"""
TryIT Question Engine — SVG Sanitizer
========================================
Geometry validation in diagrams.py checks that an SVG's COORDINATES are
correct (the right triangle, the right reflection). It does NOT check
whether the SVG's MARKUP is safe to render in a browser. Those are
different problems — a geometrically perfect triangle can still carry
a <script> tag or an onload handler, since the LLM controls the raw
text for geometry_svg / nonverbal_mirror_svg.

This module is allowlist-based on purpose, not blocklist-based: rather
than trying to enumerate every dangerous pattern (always incomplete),
it only keeps elements/attributes we explicitly know are safe simple
shapes, and drops everything else — including the entire subtree of
any disallowed element, so something like
<script>...</script> inside a <g> doesn't survive by hiding deeper.

Code-generated SVGs (paper_fold, embedded_figure via geometry_engine.py)
are already safe by construction — they're run through this anyway as
defense-in-depth, in case that code ever changes to incorporate
LLM-influenced text later.
"""

import re
import xml.etree.ElementTree as ET

ALLOWED_TAGS = {"svg", "polygon", "polyline", "circle", "ellipse", "rect", "line", "text", "tspan"}

ALLOWED_ATTRS = {
    "svg":      {"viewbox", "width", "height"},
    "polygon":  {"points", "fill", "stroke", "stroke-width", "stroke-dasharray"},
    "polyline": {"points", "fill", "stroke", "stroke-width", "stroke-dasharray"},
    "circle":   {"cx", "cy", "r", "fill", "stroke", "stroke-width", "stroke-dasharray"},
    "ellipse":  {"cx", "cy", "rx", "ry", "fill", "stroke", "stroke-width"},
    "rect":     {"x", "y", "width", "height", "rx", "ry", "fill", "stroke", "stroke-width"},
    "line":     {"x1", "y1", "x2", "y2", "stroke", "stroke-width", "stroke-dasharray"},
    "text":     {"x", "y", "fill", "font-size", "text-anchor"},
    "tspan":    {"x", "y", "fill", "font-size"},
}

_NUM = r"-?\d+(\.\d+)?"
_NUMERIC_RE = re.compile(rf"^\s*{_NUM}\s*$")
_POINTS_RE = re.compile(rf"^(\s*{_NUM}\s*,\s*{_NUM}\s*)+$")
_VIEWBOX_RE = re.compile(rf"^\s*{_NUM}(\s+{_NUM}){{3}}\s*$")
_DASHARRAY_RE = re.compile(rf"^\s*{_NUM}(\s*,\s*{_NUM})*\s*$")
_COLOR_RE = re.compile(r"^(none|[a-zA-Z]{2,20}|#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})$")
_ANCHOR_RE = re.compile(r"^(start|middle|end)$")

_VALUE_VALIDATORS = {
    "viewbox": _VIEWBOX_RE, "width": _NUMERIC_RE, "height": _NUMERIC_RE,
    "points": _POINTS_RE, "cx": _NUMERIC_RE, "cy": _NUMERIC_RE, "r": _NUMERIC_RE,
    "rx": _NUMERIC_RE, "ry": _NUMERIC_RE, "x": _NUMERIC_RE, "y": _NUMERIC_RE,
    "x1": _NUMERIC_RE, "y1": _NUMERIC_RE, "x2": _NUMERIC_RE, "y2": _NUMERIC_RE,
    "stroke-width": _NUMERIC_RE, "stroke-dasharray": _DASHARRAY_RE,
    "font-size": _NUMERIC_RE, "fill": _COLOR_RE, "stroke": _COLOR_RE,
    "text-anchor": _ANCHOR_RE,
}


def _local_tag(elem_tag: str) -> str:
    """Strips any XML namespace prefix, e.g. '{http://www.w3.org/2000/svg}circle' -> 'circle'."""
    return elem_tag.split("}")[-1].lower()


def _clean_element(elem):
    """Returns a cleaned copy of elem, or None if its tag isn't allowed at
    all (the whole subtree is dropped, not just the offending element)."""
    tag = _local_tag(elem.tag)
    if tag not in ALLOWED_TAGS:
        return None

    cleaned = ET.Element(tag)
    allowed_for_tag = ALLOWED_ATTRS.get(tag, set())
    for attr_name, attr_value in elem.attrib.items():
        local_name = _local_tag(attr_name)  # attributes can carry namespaces too (e.g. xlink:href)
        if local_name not in allowed_for_tag:
            continue
        validator = _VALUE_VALIDATORS.get(local_name)
        if validator and not validator.match(attr_value.strip()):
            continue
        cleaned.set(local_name, attr_value.strip())

    if tag in ("text", "tspan") and elem.text:
        # Plain text content only — strip anything that looks like markup
        # smuggled in as text (defense in depth, ET already escapes this
        # on serialization, but reject control characters outright too).
        safe_text = re.sub(r"[<>]", "", elem.text)
        cleaned.text = safe_text[:200]  # labels don't need to be long

    for child in elem:
        cleaned_child = _clean_element(child)
        if cleaned_child is not None:
            cleaned.append(cleaned_child)

    return cleaned


def sanitize_svg(svg_string: str) -> str:
    """Returns a cleaned SVG string containing only allowlisted shape/text
    elements with allowlisted, value-validated attributes. Returns an
    empty string if the input doesn't parse as XML at all, or if nothing
    safe survives — callers should treat an empty result as "this
    diagram failed", the same as any other validation failure, not
    silently render nothing."""
    if not svg_string or "<svg" not in svg_string:
        return ""
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return ""

    if _local_tag(root.tag) != "svg":
        return ""

    cleaned_root = _clean_element(root)
    if cleaned_root is None:
        return ""
    if len(cleaned_root) == 0:
        return ""  # parsed fine, but nothing inside survived sanitization

    return ET.tostring(cleaned_root, encoding="unicode")


def sanitize_question_svgs(question: dict, diagram_kind: str) -> dict:
    """Sanitizes every SVG field a question might carry for its diagram
    kind, in place semantics (returns the same dict, mutated). Fields
    that end up empty after sanitization are left empty — the diagram
    validators in diagrams.py will then correctly reject the question
    for missing geometry, same as if the LLM hadn't produced an SVG at
    all."""
    if diagram_kind == "geometry_svg":
        if question.get("diagram_svg"):
            question["diagram_svg"] = sanitize_svg(question["diagram_svg"])

    elif diagram_kind == "nonverbal_mirror_svg":
        if question.get("original_svg"):
            question["original_svg"] = sanitize_svg(question["original_svg"])
        if isinstance(question.get("option_svgs"), list):
            question["option_svgs"] = [sanitize_svg(s) for s in question["option_svgs"]]

    elif diagram_kind in ("paper_fold", "embedded_figure"):
        if question.get("diagram_svg"):
            question["diagram_svg"] = sanitize_svg(question["diagram_svg"])
        if isinstance(question.get("option_svgs"), list):
            question["option_svgs"] = [sanitize_svg(s) for s in question["option_svgs"]]

    return question
