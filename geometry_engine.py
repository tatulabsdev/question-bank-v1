"""
TryIT Question Engine — Geometry Engine
==========================================
For paper folding and embedded figures, we flip who does the drawing.
Instead of asking an LLM to freehand a figure and then checking if it
happens to be right, CODE constructs the figure first (exact reflection
math for folding, exact subset-of-segments construction for embedding),
so correctness is guaranteed by how it's built, not verified after the
fact. The LLM's only job afterward is to write the question stem and
explanations around a scenario we already know the answer to.

Both generators return a dict with:
  - "correct_answer": int (0-3) — fixed by construction, never decided by an LLM
  - "diagram_meta": structured coordinate data (the source of truth)
  - "diagram_svg" / "option_svgs": SVG strings rendered FROM that same data
  - "scenario_text": a plain-language description for the LLM prompt
"""

import random
import math

CANVAS = 100


# ──────────────────────────────────────────────────────────
# PAPER FOLDING
# ──────────────────────────────────────────────────────────
def _reflect_vertical(p):
    return (CANVAS - p[0], p[1])


def _reflect_horizontal(p):
    return (p[0], CANVAS - p[1])


def _reflect_diagonal(p):
    return (p[1], p[0])


def _points_close(a, b, tol=2.0):
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol


def _dedupe_close(points, tol=2.0):
    out = []
    for p in points:
        if not any(_points_close(p, q, tol) for q in out):
            out.append(p)
    return out


def generate_paper_fold_geometry(num_folds: int = 2, rng: random.Random = None) -> dict:
    rng = rng or random.Random()
    fold_types = rng.sample(["vertical", "horizontal"], k=min(num_folds, 2))
    if num_folds > 2:
        fold_types = fold_types + ["vertical"]  # simple extension: re-fold same axis again

    # Punch point safely inside the remaining folded region, away from
    # fold lines/edges so reflections don't accidentally coincide.
    margin = 12
    half = CANVAS / (2 if len(fold_types) >= 1 else 1)
    px = rng.uniform(margin, half - margin) if "vertical" in fold_types else rng.uniform(margin, CANVAS - margin)
    py = rng.uniform(margin, half - margin) if "horizontal" in fold_types else rng.uniform(margin, CANVAS - margin)
    punch = (round(px, 1), round(py, 1))

    # Correct holes = orbit of punch point under every combination of the
    # actual folds used (this IS the physical unfolding, computed exactly).
    correct_holes = [punch]
    for fold in fold_types:
        reflector = _reflect_vertical if fold == "vertical" else _reflect_horizontal
        correct_holes = correct_holes + [reflector(p) for p in correct_holes]
    correct_holes = _dedupe_close(correct_holes)

    # Decoys — each a clearly DIFFERENT, deterministic wrong transform,
    # verified below to actually differ from the correct set.
    decoys = []

    # Decoy: "forgot one fold" — only reflects across the first fold, ignores the rest
    only_first = [punch]
    if fold_types:
        reflector = _reflect_vertical if fold_types[0] == "vertical" else _reflect_horizontal
        only_first = only_first + [reflector(p) for p in only_first]
    decoys.append(_dedupe_close(only_first))

    # Decoy: "wrong axis" — reflects across the diagonal instead of the actual fold axes
    wrong_axis = [punch] + [_reflect_diagonal(punch)]
    for fold in fold_types[1:]:
        reflector = _reflect_vertical if fold == "vertical" else _reflect_horizontal
        wrong_axis = wrong_axis + [reflector(p) for p in wrong_axis]
    decoys.append(_dedupe_close(wrong_axis))

    # Decoy: correct hole count, but one hole shifted (plausible-looking slip)
    shifted = list(correct_holes)
    if shifted:
        idx = rng.randrange(len(shifted))
        sx, sy = shifted[idx]
        shifted[idx] = (round(min(max(sx + rng.choice([-18, 18]), 2), CANVAS - 2), 1),
                        round(min(max(sy + rng.choice([-18, 18]), 2), CANVAS - 2), 1)) 
    decoys.append(shifted)

    # Safety check: every decoy must differ from the correct set. If a decoy
    # collapsed onto the correct answer (rare edge case with symmetric punch
    # points), nudge it so the option set stays meaningfully wrong.
    def _sets_match(a, b, tol=3.0):
        if len(a) != len(b):
            return False
        used = [False] * len(b)
        for pa in a:
            found = False
            for i, pb in enumerate(b):
                if not used[i] and _points_close(pa, pb, tol):
                    used[i] = True
                    found = True
                    break
            if not found:
                return False
        return True

    for i, d in enumerate(decoys):
        if _sets_match(d, correct_holes):
            decoys[i] = [(round(x + 20, 1), round(y + 5, 1)) for x, y in d]

    options = [correct_holes, decoys[0], decoys[1], decoys[2]]
    rng.shuffle(options)
    correct_index = options.index(correct_holes)

    scenario_text = (
        f"A square sheet of paper is folded {', then folded '.join(fold_types)} "
        f"(fold {len(fold_types)} time(s)), and a hole is punched through all "
        f"folded layers at one point. Ask the student to identify which "
        f"unfolding pattern (option) shows where the holes will appear when "
        f"the paper is fully unfolded."
    )

    return {
        "correct_answer": correct_index,
        "scenario_text": scenario_text,
        "diagram_meta": {
            "fold_sequence": fold_types,
            "punch_point": punch,
            "option_holes": options,
        },
        "diagram_svg": render_fold_before_svg(fold_types, punch),
        "option_svgs": [render_hole_pattern_svg(pts) for pts in options],
    }


def render_fold_before_svg(fold_types, punch_point) -> str:
    lines = ""
    if "vertical" in fold_types:
        lines += f'<line x1="{CANVAS/2}" y1="0" x2="{CANVAS/2}" y2="{CANVAS}" stroke="gray" stroke-dasharray="3,3"/>'
    if "horizontal" in fold_types:
        lines += f'<line x1="0" y1="{CANVAS/2}" x2="{CANVAS}" y2="{CANVAS/2}" stroke="gray" stroke-dasharray="3,3"/>'
    px, py = punch_point
    return (f'<svg viewBox="0 0 {CANVAS} {CANVAS}">'
            f'<rect x="0" y="0" width="{CANVAS}" height="{CANVAS}" fill="white" stroke="black"/>'
            f'{lines}<circle cx="{px}" cy="{py}" r="3" fill="black"/></svg>')


def render_hole_pattern_svg(points) -> str:
    circles = "".join(f'<circle cx="{x}" cy="{y}" r="3" fill="black"/>' for x, y in points)
    return (f'<svg viewBox="0 0 {CANVAS} {CANVAS}">'
            f'<rect x="0" y="0" width="{CANVAS}" height="{CANVAS}" fill="white" stroke="black"/>'
            f'{circles}</svg>')


def validate_paper_fold_geometry(data: dict) -> bool:
    """Self-check: recompute the correct hole set from the stored fold
    sequence + punch point, and confirm it matches the option marked
    correct. Mostly a defense against a future code change breaking the
    generator silently — the construction is already correct by design."""
    meta = data.get("diagram_meta", {})
    fold_types = meta.get("fold_sequence", [])
    punch = tuple(meta.get("punch_point", (0, 0)))
    options = meta.get("option_holes", [])
    correct_idx = data.get("correct_answer")
    if not options or correct_idx is None or not (0 <= correct_idx < len(options)):
        return False

    recomputed = [punch]
    for fold in fold_types:
        reflector = _reflect_vertical if fold == "vertical" else _reflect_horizontal
        recomputed = recomputed + [reflector(p) for p in recomputed]
    recomputed = _dedupe_close(recomputed)

    claimed = [tuple(p) for p in options[correct_idx]]
    if len(recomputed) != len(claimed):
        return False
    used = [False] * len(claimed)
    for p in recomputed:
        found = False
        for i, q in enumerate(claimed):
            if not used[i] and _points_close(p, q, 3.0):
                used[i] = True
                found = True
                break
        if not found:
            return False
    return True


# ──────────────────────────────────────────────────────────
# EMBEDDED FIGURES
# ──────────────────────────────────────────────────────────
def _segment_close(seg_a, seg_b, tol=3.0):
    (a1, a2), (b1, b2) = seg_a, seg_b
    direct = _points_close(a1, b1, tol) and _points_close(a2, b2, tol)
    reversed_ = _points_close(a1, b2, tol) and _points_close(a2, b1, tol)
    return direct or reversed_


def _triangle_segments(points):
    return [(points[i], points[(i + 1) % 3]) for i in range(3)]


def _segment_in_list(seg, seg_list, tol=3.0):
    return any(_segment_close(seg, other, tol) for other in seg_list)


def generate_embedded_figure_geometry(rng: random.Random = None) -> dict:
    rng = rng or random.Random()
    margin = 15

    target = [
        (rng.uniform(margin, CANVAS - margin), rng.uniform(margin, CANVAS - margin))
        for _ in range(3)
    ]
    target_segments = _triangle_segments(target)

    # Noise segments: random lines that clutter the figure visually but
    # are NOT part of the target — generated independently, so they won't
    # coincide with the target's edges except by astronomical coincidence
    # (and we double-check below regardless).
    noise_segments = []
    for _ in range(6):
        p1 = (rng.uniform(0, CANVAS), rng.uniform(0, CANVAS))
        p2 = (rng.uniform(0, CANVAS), rng.uniform(0, CANVAS))
        noise_segments.append((p1, p2))

    figure_segments = target_segments + noise_segments

    # Decoys: other triangles, deterministically distinct in shape from
    # the target (scaled/skewed), then verified to NOT be embedded.
    decoy_triangles = []
    transforms = [
        lambda p: (p[0] * 0.6 + 20, p[1] * 0.6 + 20),               # shrink + shift
        lambda p: (CANVAS - p[0], p[1]),                              # horizontal flip
        lambda p: (p[1], p[0]),                                       # swap axes
    ]
    for t in transforms:
        candidate = [t(p) for p in target]
        # clamp into canvas
        candidate = [(min(max(x, 5), CANVAS - 5), min(max(y, 5), CANVAS - 5)) for x, y in candidate]
        decoy_triangles.append(candidate)

    # Guarantee decoys are genuinely not embedded — if a transform
    # accidentally reproduces an embedded triangle (essentially
    # impossible with continuous random coordinates, but checked
    # anyway), perturb it until it isn't.
    def is_embedded(triangle):
        segs = _triangle_segments(triangle)
        return all(_segment_in_list(s, figure_segments) for s in segs)

    for i, tri in enumerate(decoy_triangles):
        attempts = 0
        while is_embedded(tri) and attempts < 5:
            tri = [(x + 7, y - 7) for x, y in tri]
            attempts += 1
        decoy_triangles[i] = tri

    options = [target] + decoy_triangles
    rng.shuffle(options)
    correct_index = options.index(target)

    scenario_text = (
        "A complex figure is made of several overlapping straight lines. "
        "Exactly one of the four simple triangles shown as options is "
        "hidden (embedded) within the complex figure's lines. Ask the "
        "student to identify which one."
    )

    return {
        "correct_answer": correct_index,
        "scenario_text": scenario_text,
        "diagram_meta": {
            "figure_segments": figure_segments,
            "option_triangles": options,
        },
        "diagram_svg": render_figure_svg(figure_segments),
        "option_svgs": [render_triangle_svg(tri) for tri in options],
    }


def render_figure_svg(segments) -> str:
    lines = "".join(
        f'<line x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}" stroke="black"/>'
        for p1, p2 in segments
    )
    return f'<svg viewBox="0 0 {CANVAS} {CANVAS}">{lines}</svg>'


def render_triangle_svg(points) -> str:
    pts_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (f'<svg viewBox="0 0 {CANVAS} {CANVAS}">'
            f'<polygon points="{pts_str}" fill="none" stroke="black"/></svg>')


def validate_embedded_figure_geometry(data: dict) -> bool:
    """Self-check: confirm the option marked correct really is a subset
    of the figure's segments, and at least the OTHER three are not."""
    meta = data.get("diagram_meta", {})
    figure_segments = [tuple(map(tuple, seg)) for seg in meta.get("figure_segments", [])]
    options = meta.get("option_triangles", [])
    correct_idx = data.get("correct_answer")
    if not figure_segments or not options or correct_idx is None:
        return False
    if not (0 <= correct_idx < len(options)):
        return False

    correct_segs = _triangle_segments([tuple(p) for p in options[correct_idx]])
    if not all(_segment_in_list(s, figure_segments) for s in correct_segs):
        return False

    for i, opt in enumerate(options):
        if i == correct_idx:
            continue
        segs = _triangle_segments([tuple(p) for p in opt])
        if all(_segment_in_list(s, figure_segments) for s in segs):
            return False  # a decoy is ALSO embedded — ambiguous question, reject
    return True
