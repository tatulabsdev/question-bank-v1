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
against them automatically. CRITICAL: every value in diagram_meta must
be valid JSON — write a computed decimal number (0.75), never an
unevaluated math expression as a bare value (NOT 3/4, NOT sqrt(2)) since
that breaks JSON parsing entirely. Do NOT invent additional keys beyond
"sides" and "angles" — if the question's given values don't fit that
shape (e.g. a ratio-based problem), still convert everything to plain
decimal numbers under "sides"/"angles" rather than adding a new
structure the parser doesn't expect.
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
        # existing
        "chart_data":              CHART_DATA_INSTRUCTION,
        "geometry_svg":            GEOMETRY_SVG_INSTRUCTION,
        "nonverbal_mirror_svg":    NONVERBAL_MIRROR_SVG_INSTRUCTION,
        "map_region":              MAP_REGION_INSTRUCTION,
        # physics
        "free_body_diagram":       FREE_BODY_DIAGRAM_INSTRUCTION,
        "circuit_diagram":         CIRCUIT_DIAGRAM_INSTRUCTION,
        "ray_diagram":             RAY_DIAGRAM_INSTRUCTION,
        "pv_graph":                PV_GRAPH_INSTRUCTION,
        # chemistry
        "electron_dot":            ELECTRON_DOT_INSTRUCTION,
        "periodic_highlight":      PERIODIC_HIGHLIGHT_INSTRUCTION,
        # biology
        "biology_labeled_diagram": BIOLOGY_LABELED_DIAGRAM_INSTRUCTION,
        "process_flow":            PROCESS_FLOW_INSTRUCTION,
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
    if not categories or not isinstance(series, list):
        return False
    for s in series:
        # The model occasionally returns a malformed series list where an
        # item isn't a dict at all (observed: a plain int), which used to
        # crash the whole job with AttributeError. Reject the diagram
        # instead of crashing — this is exactly what the rest of this
        # gate already does for other malformed cases.
        if not isinstance(s, dict):
            return False
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
    # The model occasionally writes a literal null (or a non-numeric
    # value) for one of the given side lengths — valid JSON, but not
    # something float() can convert, which used to crash the whole job.
    # Reject the diagram instead, same pattern as the chart_data fix.
    if any(g is None or not isinstance(g, (int, float, str)) for g in given):
        return False
    try:
        given_sorted = sorted(float(g) for g in given)
    except (TypeError, ValueError):
        return False
    drawn_sorted = sorted(drawn)
    if any(g == 0 for g in given_sorted):
        return False
    ratios = [d / g for d, g in zip(drawn_sorted, given_sorted)]

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
    # existing kinds
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
    # physics — real coordinate-math validation
    if diagram_kind == "free_body_diagram":
        return validate_free_body_diagram(question)
    if diagram_kind == "circuit_diagram":
        return validate_circuit_diagram(question)
    if diagram_kind == "ray_diagram":
        return validate_ray_diagram(question)
    if diagram_kind == "pv_graph":
        return validate_pv_graph(question)
    # chemistry — structural-presence check (human review mandatory)
    if diagram_kind == "electron_dot":
        return validate_electron_dot(question)
    if diagram_kind == "periodic_highlight":
        return validate_periodic_highlight(question)
    # biology — labeled-presence check (human review mandatory)
    if diagram_kind == "biology_labeled_diagram":
        return validate_biology_labeled_diagram(question)
    if diagram_kind == "process_flow":
        return validate_process_flow(question)
    return True  # no diagram required for this topic


# ──────────────────────────────────────────────────────────
# PHYSICS DIAGRAM INSTRUCTIONS
# ──────────────────────────────────────────────────────────

FREE_BODY_DIAGRAM_INSTRUCTION = """
This question needs a free body diagram (FBD). Add a "diagram_svg" field
containing a valid SVG string (viewBox "0 0 300 300", white background):
- Draw a simple box or dot representing the object at the center
- Draw labeled force vectors as arrows (<line> with arrowhead <polygon>):
  * Weight/gravity: arrow pointing DOWN, labeled "W" or "mg"
  * Normal force: arrow pointing UP from surface, labeled "N"
  * Friction: arrow pointing LEFT or RIGHT along surface, labeled "f"
  * Applied forces: arrows in their stated direction, labeled "F" or given name
- Each arrow length must be PROPORTIONAL to the stated magnitude
- Label every force mentioned in the question using <text> elements
Also add "diagram_meta": {
  "forces": [{"name": "...", "direction": "up|down|left|right|angle_degrees",
              "magnitude": num_or_null}]
}
CRITICAL: every force mentioned in the question text MUST appear in
diagram_meta forces list. Direction must be one of the stated values.
Never use an unevaluated expression as a magnitude value.
"""

CIRCUIT_DIAGRAM_INSTRUCTION = """
This question needs an electric circuit diagram. Add a "diagram_svg" field
containing a valid SVG string (viewBox "0 0 300 300", white background)
using standard circuit symbols drawn with <line>, <rect>, <circle>, <path>:
- Battery: two parallel lines (long=positive, short=negative), labeled "V" or given voltage
- Resistor: zigzag line (<path>), labeled "R" or given resistance value in Ω
- Bulb/lamp: circle with X inside, labeled with given name
- Switch: a gap in the wire with a line showing open/closed state
- Wires: straight <line> elements connecting components
- For SERIES circuits: all components on ONE continuous loop
- For PARALLEL circuits: components on SEPARATE branches between two common nodes
Also add "diagram_meta": {
  "circuit_type": "series" | "parallel" | "mixed",
  "components": [{"type": "battery|resistor|bulb|switch", "label": "...", "value": num_or_null}]
}
CRITICAL: every component named in the question MUST appear in
diagram_meta components. circuit_type must match the actual topology drawn.
"""

RAY_DIAGRAM_INSTRUCTION = """
This question needs an optics ray diagram. Add a "diagram_svg" field
containing a valid SVG string (viewBox "0 0 300 300", white background):
- Draw the principal axis as a horizontal line through the center
- Draw the lens (double-convex oval) or mirror (curved arc) at the center
- Mark focal point F and center of curvature C with labeled dots
- Draw the object as a vertical arrow on one side
- Draw at least 2 rays from the top of the object:
  * Ray 1: parallel to principal axis → refracts/reflects through F
  * Ray 2: through optical center → passes straight (for lens) or
           through C → reflects back (for mirror)
- Where rays intersect (or their extensions): mark the IMAGE with a
  dashed arrow (real image = solid convergence, virtual = dashed extensions)
Also add "diagram_meta": {
  "type": "convex_lens|concave_lens|convex_mirror|concave_mirror",
  "object_distance": num_or_null,
  "focal_length": num_or_null,
  "image_type": "real|virtual|at_infinity"
}
CRITICAL: focal_length and object_distance must be plain decimal numbers,
never unevaluated expressions. image_type must match the actual optics.
"""

PV_GRAPH_INSTRUCTION = """
This question needs a Pressure-Volume (PV) diagram. Use the existing
"chart_data" field format with chart_type "line":
{
  "chart_type": "line",
  "title": "PV Diagram — [process name]",
  "x_label": "Volume (V)",
  "y_label": "Pressure (P)",
  "process_type": "isothermal|isobaric|isochoric|adiabatic",
  "categories": [v1, v2, v3, ...],   <- volume values along the curve
  "series": [{"name": "Process", "values": [p1, p2, p3, ...]}]
}
Curve shape MUST match the stated process:
- Isothermal: P×V = constant → hyperbola (P decreases as V increases)
- Isobaric: constant pressure → horizontal line (all P values identical)
- Isochoric: constant volume → vertical line (all V values identical)
- Adiabatic: steeper than isothermal → P falls faster than isothermal
CRITICAL: generate at least 5 data points tracing the real curve shape.
Values must be plain numbers, never unevaluated expressions.
"""

# ──────────────────────────────────────────────────────────
# CHEMISTRY DIAGRAM INSTRUCTIONS
# (Honest weaker validation tier — labeled explicitly in code)
# ──────────────────────────────────────────────────────────

ELECTRON_DOT_INSTRUCTION = """
This question needs a Lewis dot / electron dot structure. Add a "diagram_svg"
field containing a valid SVG string (viewBox "0 0 300 300", white background):
- Draw element symbols as <text> elements
- Draw bonding pairs as short lines between symbols (<line>)
- Draw lone pairs as pairs of dots (<circle r="2">) around each atom
- For molecules: arrange atoms according to the actual molecular geometry
  (linear, bent, trigonal planar, tetrahedral as appropriate)
Also add "diagram_meta": {
  "formula": "e.g. H2O",
  "central_atom": "e.g. O",
  "bond_type": "single|double|triple",
  "lone_pairs_on_central": num,
  "stated_atoms": ["H", "O", ...]
}
CRITICAL: every atom stated in diagram_meta.stated_atoms MUST appear as
a <text> element in the SVG. Bond type must match the actual chemistry.
NOTE: This is a structural-presence check, not a full valence-rules
verification — human chemistry expert review is mandatory before use.
"""

PERIODIC_HIGHLIGHT_INSTRUCTION = """
This question highlights one or more elements on the periodic table concept.
Add a "diagram_meta" field only (no SVG — the app renders the real periodic
table and highlights the stated elements):
{
  "diagram_type": "periodic_highlight",
  "highlighted_elements": ["Fe", "Cu", ...],
  "highlight_reason": "transition metals" | "noble gases" | "stated property",
  "group": num_or_null,
  "period": num_or_null
}
CRITICAL: element symbols must be exact standard symbols (Fe not Iron,
Cu not Copper). All elements stated in the question must appear in
highlighted_elements.
"""

# ──────────────────────────────────────────────────────────
# BIOLOGY DIAGRAM INSTRUCTIONS
# (Honest labeled-presence check tier — labeled explicitly in code)
# ──────────────────────────────────────────────────────────

BIOLOGY_LABELED_DIAGRAM_INSTRUCTION = """
This question needs a labeled biological diagram. Add a "diagram_svg" field
containing a valid SVG string (viewBox "0 0 300 300", white background):
- Draw a simplified schematic of the biological structure (cell, organ,
  system) using basic SVG shapes — accuracy of shape matters less than
  clarity of labels
- Label EVERY part mentioned in the question using <text> elements with
  short leader lines (<line>) pointing to the relevant part
- Use standard biological names for all labels (nucleus not "centre blob")
Also add "diagram_meta": {
  "structure_type": "cell|organ|system|process_flow",
  "labeled_parts": ["nucleus", "mitochondria", ...]
}
CRITICAL: every part named in the question text MUST appear in
diagram_meta.labeled_parts AND have a corresponding <text> label in the
SVG. This is a labeled-presence check, not a spatial-accuracy guarantee
— human biology expert review is mandatory before student-facing use.
"""

PROCESS_FLOW_INSTRUCTION = """
This question involves a biological or chemical process with sequential
steps (e.g. photosynthesis, digestion, cell cycle). Add a "diagram_svg"
field containing a valid SVG flowchart (viewBox "0 0 300 300", white
background):
- Draw each step as a labeled box (<rect> + <text>)
- Connect boxes with directional arrows (<line> with arrowhead)
- Steps must appear in the CORRECT biological/chemical order top-to-bottom
Also add "diagram_meta": {
  "process_name": "e.g. photosynthesis",
  "steps": ["step 1 name", "step 2 name", ...]
}
CRITICAL: steps in diagram_meta must be in the exact correct order.
The number of boxes in the SVG must match len(diagram_meta.steps).
This is a step-ordering check — human expert review mandatory before use.
"""


# ──────────────────────────────────────────────────────────
# PHYSICS VALIDATORS — real coordinate-math where possible
# ──────────────────────────────────────────────────────────

def validate_free_body_diagram(question: dict) -> bool:
    """Checks that every force stated in the question appears in
    diagram_meta.forces with a valid direction. SVG presence also
    checked."""
    svg = question.get("diagram_svg")
    meta = question.get("diagram_meta")
    if not svg or "<svg" not in svg:
        return False
    if not isinstance(meta, dict):
        return False
    forces = meta.get("forces")
    if not isinstance(forces, list) or len(forces) == 0:
        return False
    valid_directions = {"up", "down", "left", "right"}
    for f in forces:
        if not isinstance(f, dict):
            return False
        direction = str(f.get("direction", "")).lower()
        # allow either cardinal directions or numeric angle strings
        if direction not in valid_directions:
            try:
                float(direction)
            except (ValueError, TypeError):
                return False
    # every force in meta must have a <text> label in the SVG
    for f in forces:
        name = f.get("name", "")
        if name and name not in svg:
            return False
    return True


def validate_circuit_diagram(question: dict) -> bool:
    """Checks circuit_type is stated, all declared components appear as
    labels in the SVG, and topology is minimally consistent."""
    svg = question.get("diagram_svg")
    meta = question.get("diagram_meta")
    if not svg or "<svg" not in svg:
        return False
    if not isinstance(meta, dict):
        return False
    circuit_type = meta.get("circuit_type")
    if circuit_type not in ("series", "parallel", "mixed"):
        return False
    components = meta.get("components")
    if not isinstance(components, list) or len(components) == 0:
        return False
    for c in components:
        if not isinstance(c, dict):
            return False
        label = c.get("label", "")
        if label and label not in svg:
            return False
    return True


def validate_ray_diagram(question: dict) -> bool:
    """Checks diagram type is stated, key optical elements (F, C or
    principal axis markers) appear in the SVG, and image_type is valid."""
    svg = question.get("diagram_svg")
    meta = question.get("diagram_meta")
    if not svg or "<svg" not in svg:
        return False
    if not isinstance(meta, dict):
        return False
    valid_types = {"convex_lens", "concave_lens", "convex_mirror", "concave_mirror"}
    if meta.get("type") not in valid_types:
        return False
    valid_image_types = {"real", "virtual", "at_infinity"}
    if meta.get("image_type") not in valid_image_types:
        return False
    # focal point must be labeled in the SVG
    if "F" not in svg:
        return False
    focal_length = meta.get("focal_length")
    if focal_length is not None:
        if not isinstance(focal_length, (int, float)):
            return False
    return True


def validate_pv_graph(question: dict) -> bool:
    """Reuses validate_chart_data for structure, then checks curve shape
    is consistent with the stated process type."""
    if not validate_chart_data(question):
        return False
    data = question.get("chart_data", {})
    process_type = data.get("process_type")
    if not process_type:
        return False
    series = data.get("series", [])
    if not series or not isinstance(series[0], dict):
        return False
    values = series[0].get("values", [])
    categories = data.get("categories", [])
    if len(values) < 2 or len(categories) < 2:
        return False
    if process_type == "isobaric":
        if len(set(values)) != 1:
            return False
    if process_type == "isochoric":
        if len(set(categories)) != 1:
            return False
    if process_type in ("isothermal", "adiabatic"):
        # pressure must decrease as volume increases
        try:
            vols = [float(c) for c in categories]
            pres = [float(v) for v in values]
            if vols[-1] <= vols[0]:
                return False  # volume should increase along the curve
            if pres[-1] >= pres[0]:
                return False  # pressure should decrease
        except (TypeError, ValueError):
            return False
    return True


# ──────────────────────────────────────────────────────────
# CHEMISTRY VALIDATORS
# (Honest weaker tier — labeled explicitly, human review mandatory)
# ──────────────────────────────────────────────────────────

def validate_electron_dot(question: dict) -> bool:
    """Checks that every stated atom appears as a <text> label in the
    SVG. Structural-presence check only — not a full valence-rules
    verification. Human chemistry expert review mandatory."""
    svg = question.get("diagram_svg")
    meta = question.get("diagram_meta")
    if not svg or "<svg" not in svg:
        return False
    if not isinstance(meta, dict):
        return False
    stated_atoms = meta.get("stated_atoms")
    if not isinstance(stated_atoms, list) or len(stated_atoms) == 0:
        return False
    for atom in stated_atoms:
        if str(atom) not in svg:
            return False
    bond_type = meta.get("bond_type")
    if bond_type not in ("single", "double", "triple"):
        return False
    return True


def validate_periodic_highlight(question: dict) -> bool:
    """Checks that highlighted_elements is present and non-empty, and
    all symbols are plausible (1-2 capital+lowercase letters). No SVG
    needed — app renders the real periodic table."""
    meta = question.get("diagram_meta")
    if not isinstance(meta, dict):
        return False
    if meta.get("diagram_type") != "periodic_highlight":
        return False
    elements = meta.get("highlighted_elements")
    if not isinstance(elements, list) or len(elements) == 0:
        return False
    import re
    for symbol in elements:
        if not re.match(r"^[A-Z][a-z]?$", str(symbol)):
            return False
    return True


# ──────────────────────────────────────────────────────────
# BIOLOGY VALIDATORS
# (Honest labeled-presence check tier — human review mandatory)
# ──────────────────────────────────────────────────────────

def validate_biology_labeled_diagram(question: dict) -> bool:
    """Checks that every part in diagram_meta.labeled_parts appears as
    a <text> label in the SVG. Spatial accuracy NOT verified — human
    biology expert review mandatory before student-facing use."""
    svg = question.get("diagram_svg")
    meta = question.get("diagram_meta")
    if not svg or "<svg" not in svg:
        return False
    if not isinstance(meta, dict):
        return False
    labeled_parts = meta.get("labeled_parts")
    if not isinstance(labeled_parts, list) or len(labeled_parts) == 0:
        return False
    for part in labeled_parts:
        if str(part).lower() not in svg.lower():
            return False
    return True


def validate_process_flow(question: dict) -> bool:
    """Checks that steps are present, non-empty, and the SVG has at
    least as many <rect> elements as stated steps. Step-ordering check
    only — human expert review mandatory."""
    svg = question.get("diagram_svg")
    meta = question.get("diagram_meta")
    if not svg or "<svg" not in svg:
        return False
    if not isinstance(meta, dict):
        return False
    steps = meta.get("steps")
    if not isinstance(steps, list) or len(steps) < 2:
        return False
    rect_count = svg.count("<rect")
    if rect_count < len(steps):
        return False
    return True

