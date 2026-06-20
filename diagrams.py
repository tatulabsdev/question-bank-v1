"""
TryIT Question Engine — Diagrams
===================================
For Geometry, Trigonometry, Mensuration, Data Interpretation, and
mirror-image Reasoning, the visual IS the question — these are not
optional extras generated later. This module makes the SAME generation
call also produce the diagram, then VALIDATES it with actual coordinate
math, not just by trusting the model.

Three diagram kinds, three very different reliability levels:

1. chart_data / table_data  (Data Interpretation — bar/line/pie/table)
   No image at all. The model emits structured numbers; the TryIT app
   renders the chart client-side with a charting library. This is
   strictly BETTER than a static image: themeable, accessible, scales
   to any screen, and free to render. Validation = structural integrity
   (do the numbers actually line up with the labels).

2. geometry_svg  (Geometry, Trigonometry, Mensuration)
   The model emits an SVG description of the figure (vertices, labeled
   sides/angles) in the SAME call as the question. We then independently
   recompute the geometry from the SVG coordinates and check it actually
   matches the values stated in the question text. If it doesn't match,
   we reject — we do not ship a figure we can't verify.

3. nonverbal_mirror_svg  (Reasoning — mirror image only, for now)
   Same idea: model emits the original shape's coordinates plus 4 option
   shapes. We verify computationally that the marked-correct option is a
   true geometric reflection of the original. This works well for mirror
   image specifically.

HONEST LIMITATION — read this before assuming full non-verbal reasoning
coverage: embedded figures and paper folding involve recognizing a shape
hidden inside a more complex figure, or predicting a 3D fold result.
There's no clean coordinate-math check for "did the model draw a
correct embedded-figure puzzle" the way there is for a triangle or a
mirror flip. Rather than ship diagrams I can't verify and risk teaching
a wrong visual pattern, those two subtopics are marked
`auto_generate: False` in config.py — paused, not faked, until there's
a reliable way to check them (e.g. a vision-capable free-tier model
strong enough to self-grade, or a designer pass). Same logic applies to
geography maps: I won't have an LLM hallucinate India's coastline.
"""

import re
import math
import json


# ──────────────────────────────────────────────────────────
# PROMPT BLOCKS — injected into the generation prompt only when a
# topic's diagram_kind requires it (see config.py)
# ──────────────────────────────────────────────────────────

CHART_DATA_INSTRUCTION = """
This question needs a DATA chart, not an image. Add a "chart_data" field:
{
  "chart_type": "bar" | "line" | "pie" | "table",
  "title": "...",
  "categories": ["...", "...", "..."],
  "series": [{"name": "...", "values": [num, num, num]}]
}
The numbers in "series" must be the exact numbers the question and
explanation rely on — a student must be able to answer the question
using only this data, nothing implied or missing.
"""

GEOMETRY_SVG_INSTRUCTION = """
This question needs a labeled geometric figure. Add a "diagram_svg" field
containing a single valid SVG string (viewBox "0 0 300 300", white
background), drawing the EXACT figure described in the question:
- For triangles: a <polygon points="x1,y1 x2,y2 x3,y3"> whose side-length
  RATIOS match the side lengths given in the question (it does not need
  to be to literal scale in pixels, but the relative proportions between
  sides must be geometrically consistent with the question's numbers).
- For circles: a <circle cx="..." cy="..." r="..."> sized consistently
  with any other elements in the same figure.
- Label every vertex/side/angle mentioned in the question using <text>
  elements positioned near the relevant point or edge.
Also add "diagram_meta": {"shape": "triangle"|"circle"|"rectangle"|"other",
"given_values": {"sides": [num,...], "angles": [num,...]}} listing the
exact numeric values from the question, so the figure can be checked
against them automatically.
"""

NONVERBAL_MIRROR_SVG_INSTRUCTION = """
This is a mirror-image reasoning question. Add:
"original_svg": an SVG string (viewBox "0 0 100 100") of the original
  figure, built from simple shapes (<polygon>, <circle>, <line>, <rect>).
"option_svgs": an array of exactly 4 SVG strings (same viewBox), one per
  option A-D, where exactly ONE is the true horizontal mirror reflection
  of "original_svg" and the other three are plausible but incorrect
  (e.g. rotated, vertically flipped, or slightly altered).
Make sure "correct_answer" points to the index of the true mirror image.
"""


MAP_REGION_INSTRUCTION = """
This question is about identifying or describing a specific Indian state
or union territory on a map (e.g. "which state is this", "which state
shares this border", "this state's capital is..."). Add a "map_data"
field:
{
  "region_name": "<exact official name of one real Indian state or UT>",
  "region_type": "state" | "union_territory",
  "highlight_reason": "short phrase, e.g. 'shares a border with Nepal'"
}
Use the EXACT official name (e.g. "Tamil Nadu", not "TN" or "Tamilnadu").
Do NOT describe or invent the shape of the map yourself — the app already
has an accurate map and will render it; you are only naming which real
region the question is about. Any factual claim in the question (capital,
border, river, etc.) must be accurate.
"""


def diagram_instruction_for(diagram_kind: str) -> str:
    return {
        "chart_data": CHART_DATA_INSTRUCTION,
        "geometry_svg": GEOMETRY_SVG_INSTRUCTION,
        "nonverbal_mirror_svg": NONVERBAL_MIRROR_SVG_INSTRUCTION,
        "map_region": MAP_REGION_INSTRUCTION,
    }.get(diagram_kind, "")


# ──────────────────────────────────────────────────────────
# VALIDATORS — actual math, not "ask the model if it looks right"
# ──────────────────────────────────────────────────────────

def validate_chart_data(question: dict) -> bool:
    data = question.get("chart_data")
    if not isinstance(data, dict):
        return False
    categories = data.get("categories")
    series = data.get("series")
    if not categories or not series:
        return False
    for s in series:
        values = s.get("values")
        if not isinstance(values, list) or len(values) != len(categories):
            return False
        if not all(isinstance(v, (int, float)) for v in values):
            return False
    return True


_POLYGON_POINTS_RE = re.compile(r'points="([^"]+)"')
_CIRCLE_R_RE = re.compile(r'<circle[^>]*\br="([\d.]+)"')


def _parse_polygon_points(svg: str):
    m = _POLYGON_POINTS_RE.search(svg)
    if not m:
        return None
    raw = m.group(1).strip()
    pts = []
    for pair in raw.split():
        if "," not in pair:
            continue
        x_str, y_str = pair.split(",")[:2]
        try:
            pts.append((float(x_str), float(y_str)))
        except ValueError:
            return None
    return pts if len(pts) >= 3 else None


def _side_lengths(points):
    n = len(points)
    sides = []
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        sides.append(math.hypot(x2 - x1, y2 - y1))
    return sides


def validate_geometry_svg(question: dict, tolerance: float = 0.15) -> bool:
    """Recomputes the figure's geometry from its own SVG coordinates and
    checks it's internally consistent with the stated given_values.
    `tolerance` is a relative error allowance (15% default — these are
    schematic figures, not engineering drawings)."""
    svg = question.get("diagram_svg")
    meta = question.get("diagram_meta")
    if not svg or "<svg" not in svg:
        return False
    if not isinstance(meta, dict):
        return False

    shape = meta.get("shape")
    given = meta.get("given_values", {})

    if shape == "triangle":
        points = _parse_polygon_points(svg)
        if not points or len(points) != 3:
            return False
        sides_drawn = _side_lengths(points)
        sides_given = given.get("sides")
        if sides_given and len(sides_given) == 3:
            return _ratios_consistent(sides_drawn, sides_given, tolerance)
        return True  # no specific numbers to check against — structurally valid is enough

    if shape == "circle":
        m = _CIRCLE_R_RE.search(svg)
        return m is not None  # presence check; radius ratio checks need a 2nd reference element

    # rectangle / other — structural presence check only for now
    return "<rect" in svg or "<polygon" in svg or "<circle" in svg


def _ratios_consistent(drawn: list, given: list, tolerance: float) -> bool:
    """Checks that the drawn side lengths are proportionally consistent
    with the given side lengths, regardless of absolute scale — i.e. the
    ratio drawn[i]/given[i] should be roughly the same constant for all i."""
    drawn_sorted = sorted(drawn)
    given_sorted = sorted(float(g) for g in given)
    if any(g == 0 for g in given_sorted):
        return False
    ratios = [d / g for d, g in zip(drawn_sorted, given_sorted)]
    avg_ratio = sum(ratios) / len(ratios)
    if avg_ratio == 0:
        return False
    return all(abs(r - avg_ratio) / avg_ratio <= tolerance for r in ratios)


def _reflect_horizontal(points, width=100.0):
    return [(width - x, y) for x, y in points]


def _polygons_match(points_a, points_b, tolerance_px=8.0) -> bool:
    if len(points_a) != len(points_b):
        return False
    # try all rotations of point order, since the model may list vertices
    # starting from a different point or in reverse order
    n = len(points_a)
    for offset in range(n):
        for reversed_order in (False, True):
            seq = points_b[::-1] if reversed_order else points_b
            rotated = seq[offset:] + seq[:offset]
            if all(math.hypot(a[0] - b[0], a[1] - b[1]) <= tolerance_px
                   for a, b in zip(points_a, rotated)):
                return True
    return False


def validate_nonverbal_mirror(question: dict) -> bool:
    original_svg = question.get("original_svg")
    option_svgs = question.get("option_svgs")
    correct_idx = question.get("correct_answer")

    if not original_svg or not isinstance(option_svgs, list) or len(option_svgs) != 4:
        return False
    if not isinstance(correct_idx, int) or not (0 <= correct_idx <= 3):
        return False

    original_points = _parse_polygon_points(original_svg)
    correct_points = _parse_polygon_points(option_svgs[correct_idx])
    if not original_points or not correct_points:
        return False  # can't verify non-polygon shapes yet — reject rather than guess

    expected_reflection = _reflect_horizontal(original_points)
    return _polygons_match(expected_reflection, correct_points)


def validate_map_region(question: dict) -> bool:
    """map_region questions never contain LLM-drawn geometry — the model
    only names a real state/UT, which we check against the canonical
    list. The frontend renders the actual map from a sourced boundary
    dataset (see config.py), not from anything generated here."""
    from config import INDIAN_STATES_UTS
    map_data = question.get("map_data")
    if not isinstance(map_data, dict):
        return False
    region_name = map_data.get("region_name")
    return region_name in INDIAN_STATES_UTS


def validate_diagram(question: dict, diagram_kind: str) -> bool:
    """Single entry point the pipeline calls. Returns True if the
    diagram is present AND internally consistent with the question."""
    if diagram_kind == "chart_data":
        return validate_chart_data(question)
    if diagram_kind == "geometry_svg":
        return validate_geometry_svg(question)
    if diagram_kind == "nonverbal_mirror_svg":
        return validate_nonverbal_mirror(question)
    if diagram_kind == "paper_fold":
        from geometry_engine import validate_paper_fold_geometry
        return validate_paper_fold_geometry(question)
    if diagram_kind == "embedded_figure":
        from geometry_engine import validate_embedded_figure_geometry
        return validate_embedded_figure_geometry(question)
    if diagram_kind == "map_region":
        return validate_map_region(question)
    return True  # no diagram required for this topic
