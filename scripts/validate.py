"""Geometric validator for draw.io diagrams.

Nine checks:
  1. CROSSING          — edge segment passes through the interior of any
                         non-source / non-target solid box, including the
                         caption band beneath a bottom-labelled icon. A
                         glyph nested inside a box is skipped: the box is
                         already checked at those coordinates.
  2. OVERLAP           — two edge segments share 8+ px on the same axis-
                         aligned line (within a 1.5 px orthogonal tolerance).
  3. TEXT_OVERLAP      — edge segment passes through the top 28 px title
                         band of any non-source / non-target dashed
                         container. A VERTICAL segment is exempt when the
                         edge's source or target box sits geometrically
                         inside that container: reaching a box inside a zone
                         means piercing the zone's full-width title band, so
                         that entry stub isn't "cutting across" the title.
                         A segment running ALONG the band still fires.
  4. LABEL_OVERLAP     — two edge labels' estimated bounding boxes
                         intersect. Width is estimated from character count
                         (~5.5 px/char at fontSize=10) plus padding; HTML
                         tags and common entities are stripped first.
  5. LABEL_BOX_OVERLAP — an edge label's estimated bounding box overlaps a
                         solid box that is neither the edge's source nor
                         target. Catches labels parked on top of unrelated
                         boxes (containers are exempt — labels live inside
                         zones legitimately).
  6. SHORT_LABELLED_EDGE — a labelled edge's total rendered length is less
                         than its own label's estimated text width, so the
                         label has nowhere to sit and renders as a caption
                         floating over the boxes at either end. Invisible to
                         LABEL_BOX_OVERLAP, which exempts the edge's own
                         endpoints. Fix by widening the gap or stacking the
                         label into narrower <div> lines.
  7. DIAGONAL          — an INTERIOR (waypoint-to-waypoint) edge segment is
                         neither horizontal nor vertical. Anchor stubs are
                         auto-squared on reconstruction (see below), so this
                         fires only when two explicit waypoints are offset on
                         both axes — draw.io would square that too, so the
                         route is non-deterministic. Add an aligning waypoint.
  8. DANGLING          — an edge's source or target id does not resolve to
                         any shape. Usually a typo or a deleted box; the
                         edge would render detached in draw.io.
  9. UNKNOWN_ICON      — a cell's stencil, resIcon/prIcon or image name is
                         not one draw.io ships, or it is a remote URL that
                         only renders where the host is reachable. A
                         mistyped stencil draws as an empty shape and
                         reports no error, so nothing else catches it.
                         Skipped when assets/icon_names.txt.gz is absent.

Severity: CROSSING, OVERLAP, TEXT_OVERLAP, LABEL_OVERLAP and DANGLING are
hard ERRORS (non-zero exit). DIAGONAL, LABEL_BOX_OVERLAP and
SHORT_LABELLED_EDGE are advisory WARNINGS — real but often-tolerable (a
route the validator can't fully verify, a label over an unrelated box that
its opaque white background usually masks, or a label estimated slightly
wider than its edge). Warnings print but do not fail the build.

Reads the .drawio XML, parses shapes and edges with their waypoints,
reconstructs each edge as an orthogonal polyline (source-anchor →
waypoints → target-anchor). The source and target *stubs* are squared into
the L-bend draw.io actually renders when an anchor doesn't line up with its
adjacent point, so the reconstruction matches the rendered route instead of
flagging phantom diagonals on every short connection stub.

Usage:
    python validate.py <file.drawio> [more.drawio ...]
    python validate.py            # validates every .drawio in cwd

Returns a list of violations as strings; exits with non-zero if any
violations are found.
"""

from __future__ import annotations

import difflib
import gzip
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


# --------------------------------------------------------------------------
# Tunable thresholds. These are calibrated for typical architecture diagrams
# authored with the bundled helpers (fontSize 10 edge labels, ~12px lane
# offsets, strokeWidth 1-3). Tighten them for denser diagrams; loosen them
# if legitimate corner-touches or intentional parallel edges trip the checks.
# --------------------------------------------------------------------------
# px inside a box edge that still counts as "interior" for the CROSSING
# check. Keeps an edge that grazes a box border from false-firing.
EDGE_BUFFER = 2.0

# px perpendicular tolerance for treating a segment as axis-aligned, and for
# treating two segments as collinear. Absorbs half-pixel anchor rounding. Two
# parallel edges must sit >ORTHO_TOL apart on the minor axis to be seen as
# distinct.
ORTHO_TOL = 1.5

# px two collinear segments must share before OVERLAP fires. Below this
# they're treated as a shared corner/waypoint, not a routing collision.
MIN_OVERLAP = 8.0

# px from a container's top edge treated as its title text band for the
# TEXT_OVERLAP check. Covers fontSize up to ~18 plus spacingTop.
TITLE_BAND_HEIGHT = 28.0

# px inset for the container title-band check.
TITLE_EDGE_BUFFER = 1.0

# Label bounding-box estimation (LABEL_OVERLAP). Width is char-count based;
# calibrated for Latin sans-serif at fontSize 10. CJK / styled HTML labels
# may need manual label_x / label_y tuning (see SKILL.md Limitations).
LABEL_PER_CHAR_PX = 5.5
LABEL_LINE_HEIGHT = 16.0
LABEL_X_PAD = 10.0
LABEL_Y_PAD = 4.0
# px on the shorter axis; an edge-label/box overlap smaller than this is
# treated as a graze (edge labels carry an opaque white background that masks
# small overlaps) and is not flagged by LABEL_BOX_OVERLAP.
LABEL_BOX_MIN_OVERLAP = 8.0

# px between a glyph's bottom edge and the caption rendered beneath it.
CAPTION_BAND_PAD = 2.0

# px slack when deciding whether a box sits inside a container (TEXT_OVERLAP
# entry exemption). Absorbs half-pixel authoring arithmetic on a box flush
# with a zone edge.
CONTAINMENT_MARGIN = 1.0

# Severity tiers. Hard errors fail the build (non-zero exit); warnings are
# advisory — they surface a real but often-tolerable issue (a route the
# validator can't fully verify, a label sitting over an unrelated box that
# its white background usually masks, or a label estimated slightly wider
# than its own edge) without blocking.
ERROR_CHECKS = {"CROSSING", "OVERLAP", "TEXT_OVERLAP", "LABEL_OVERLAP", "DANGLING"}
WARNING_CHECKS = {
    "DIAGONAL",
    "LABEL_BOX_OVERLAP",
    "SHORT_LABELLED_EDGE",
    "UNKNOWN_ICON",
}


def violation_severity(violation: str) -> str:
    """Return 'error' or 'warning' for a violation string, keyed on its
    prefix (the text before the first ':')."""
    prefix = violation.split(":", 1)[0]
    return "warning" if prefix in WARNING_CHECKS else "error"


@dataclass
class Box:
    cell_id: str
    label: str
    x: float
    y: float
    w: float
    h: float
    is_container: bool
    # Set for cells that carry a vendor glyph (a stencil shape or an image).
    parent_id: str = "1"
    is_icon: bool = False
    # An icon nested inside another shape. It sits within a box that is
    # already an obstacle, so it must not be treated as a second one.
    is_decoration: bool = False
    # True when the label renders BELOW the shape rather than inside it,
    # which is the draw.io default for vendor icons.
    label_below: bool = False
    style: dict = field(default_factory=dict)

    @property
    def x2(self):
        return self.x + self.w

    @property
    def y2(self):
        return self.y + self.h

    def anchor(self, ex: float, ey: float) -> tuple[float, float]:
        """Compute absolute (x,y) of an exit/entry point given relative
        coords ex, ey in [0,1] on the box edges."""
        return (self.x + ex * self.w, self.y + ey * self.h)

    def obstacle_rect(self) -> tuple[float, float, float, float]:
        """The rect an edge must not run through: the shape, plus its caption
        band when the label sits below it.

        Anchors and containment deliberately keep using the SHAPE rect
        (x, y, x2, y2). A caption is ink, not geometry you connect to — an
        entryY=1 anchor must land on the glyph's bottom edge, not somewhere
        in the text beneath it.
        """
        if not (self.label_below and self.label.strip()):
            return (self.x, self.y, self.x2, self.y2)
        cx1, cy1, cx2, cy2 = caption_rect(self)
        return (min(self.x, cx1), self.y, max(self.x2, cx2), max(self.y2, cy2))

    def contains_point(self, x: float, y: float, margin: float = 0) -> bool:
        return (
            self.x - margin <= x <= self.x2 + margin
            and self.y - margin <= y <= self.y2 + margin
        )


def caption_rect(box: Box) -> tuple[float, float, float, float]:
    """The band a bottom-positioned label occupies, below the shape.

    Sized with the same estimator as an edge label, so a caption and a label
    are measured by one rule. Centred on the shape because draw.io centres a
    bottom label — and a caption is routinely WIDER than the 48px glyph it
    belongs to, which is exactly why the shape's own bounding box is not
    enough to keep arrows off the text.
    """
    lines = normalise_label(box.label) or [""]
    w = max(len(ln) for ln in lines) * LABEL_PER_CHAR_PX + 2 * LABEL_X_PAD
    h = len(lines) * LABEL_LINE_HEIGHT + 2 * LABEL_Y_PAD
    cx = box.x + box.w / 2
    top = box.y2 + CAPTION_BAND_PAD
    return (cx - w / 2, top, cx + w / 2, top + h)


@dataclass
class Edge:
    cell_id: str
    src: str
    dst: str
    exitX: float | None
    exitY: float | None
    entryX: float | None
    entryY: float | None
    waypoints: list[tuple[float, float]]
    label: str
    color: str
    label_offset: tuple[float, float] = (0.0, 0.0)
    # Fixed endpoints from geometry (mxPoint as="sourcePoint"/"targetPoint").
    # draw.io Desktop writes these when an edge is anchored to a coordinate
    # instead of a cell — a normal hand-tuning artifact, not a broken edge.
    src_point: tuple[float, float] | None = None
    dst_point: tuple[float, float] | None = None


def load_icon_names() -> set[str]:
    """Every icon name draw.io can resolve, from the committed list.

    Returns an empty set when the file is missing, which disables
    UNKNOWN_ICON rather than failing: validate.py must keep working as a
    standalone copy, and a missing catalog is not a diagram defect.
    """
    names_file = Path(__file__).resolve().parent.parent / "assets" / "icon_names.txt.gz"
    try:
        with gzip.open(names_file, "rt", encoding="utf8") as fh:
            return {ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")}
    except OSError:
        return set()


def icon_references(style_d: dict[str, str]) -> list[tuple[str, str]]:
    """The icon names a style refers to, as (kind, name) pairs.

    kind is "name" for something checkable against the catalog, or "remote"
    for an http(s) image, which renders now but breaks wherever the host is
    unreachable. Embedded data: URIs are self-contained and yield nothing.
    """
    out: list[tuple[str, str]] = []
    shape = style_d.get("shape", "")
    if shape.startswith("mxgraph."):
        out.append(("name", shape))
    res = style_d.get("resIcon")
    if res:
        out.append(("name", res))
    pr = style_d.get("prIcon")
    if pr:
        # AWS qualifies this value; Kubernetes leaves it bare, in which case
        # it belongs to the library named by shape=.
        if "." in pr:
            out.append(("name", pr))
        elif shape.startswith("mxgraph."):
            out.append(("name", shape.rsplit(".", 1)[0] + "." + pr))
    image = style_d.get("image", "")
    if image.startswith(("http://", "https://")):
        out.append(("remote", image))
    elif image and not image.startswith("data:"):
        out.append(("name", image))
    return out


def parse_style(style: str) -> dict[str, str]:
    out = {}
    for piece in style.split(";"):
        if "=" in piece:
            k, v = piece.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _absolute_origin(cid, raw, seen=None):
    """Sum a cell's ancestors' offsets to get its absolute position.

    A child cell's mxGeometry is relative to its parent's origin, which is
    how draw.io keeps a glyph attached to the box it decorates. Reading it
    as absolute turns a glyph at (10, 16) inside a box at (400, 300) into a
    phantom obstacle near the canvas origin, and every edge that legitimately
    passes through that corner starts reporting CROSSING.
    """
    seen = seen or set()
    parent = raw[cid]["parent"]
    if parent in ("0", "1", None) or parent not in raw or parent in seen:
        return 0.0, 0.0
    seen.add(parent)
    px, py = _absolute_origin(parent, raw, seen)
    return raw[parent]["x"] + px, raw[parent]["y"] + py


def parse_drawio(path: str) -> tuple[dict[str, Box], list[Edge]]:
    tree = ET.parse(path)
    root = tree.getroot()
    boxes: dict[str, Box] = {}
    edges: list[Edge] = []

    # Pass 1: collect raw vertex geometry so parents can be resolved
    # regardless of the order cells appear in the file.
    raw: dict[str, dict] = {}
    edge_ids = {c.get("id") for c in root.findall(".//mxCell") if c.get("edge") == "1"}
    for cell in root.findall(".//mxCell"):
        cid = cell.get("id")
        if cid in ("0", "1") or cell.get("vertex") != "1":
            continue
        geom = cell.find("mxGeometry")
        if geom is None:
            continue
        raw[cid] = {
            "parent": cell.get("parent"),
            "x": float(geom.get("x", 0)),
            "y": float(geom.get("y", 0)),
        }

    for cell in root.findall(".//mxCell"):
        cid = cell.get("id")
        if cid in ("0", "1"):
            continue
        style = cell.get("style") or ""
        style_d = parse_style(style)
        geom = cell.find("mxGeometry")
        if cell.get("vertex") == "1" and geom is not None:
            parent_id = cell.get("parent") or "1"
            # A vertex parented to an EDGE is a label cell, which draw.io
            # Desktop writes on round-trip. Its geometry is a fractional
            # position along the edge, not a rectangle on the canvas, so it
            # cannot be placed and must not become an obstacle.
            if geom.get("relative") == "1" or parent_id in edge_ids:
                continue
            ox, oy = _absolute_origin(cid, raw)
            x = float(geom.get("x", 0)) + ox
            y = float(geom.get("y", 0)) + oy
            w = float(geom.get("width", 0))
            h = float(geom.get("height", 0))
            # A container is a dashed-edge zone with its title pinned to
            # the top. We key on dashed + top-aligned title only; strokeWidth
            # is NOT required (a container styled with strokeWidth 1 or 3 is
            # still a container, and requiring "2" silently reclassified it
            # as a solid box → false CROSSING). Future-state *shapes* may be
            # dashed too, but they use verticalAlign=middle, so they don't
            # match here.
            is_container = (
                style_d.get("dashed") == "1" and style_d.get("verticalAlign") == "top"
            )
            # Not truncated: the label now feeds geometry (an icon caption
            # band is sized from it). Message sites truncate for display.
            label = cell.get("value") or ""
            is_icon = (
                style_d.get("drawioSkillRole") == "icon"
                or style_d.get("shape", "").startswith("mxgraph.")
                or "image" in style_d
            )
            boxes[cid] = Box(
                cid,
                label,
                x,
                y,
                w,
                h,
                is_container,
                parent_id=parent_id,
                is_icon=is_icon,
                # A decoration is an icon that lives INSIDE another shape. It
                # is deliberately a conjunction: "child of a vertex" alone
                # would exempt a real box dropped into a swimlane and lose a
                # genuine CROSSING, while "is an icon" alone would exempt an
                # icon_node(), which IS the shape.
                is_decoration=is_icon and parent_id in raw,
                label_below=style_d.get("verticalLabelPosition") == "bottom",
                style=style_d,
            )
        elif cell.get("edge") == "1":
            ex = style_d.get("exitX")
            ey = style_d.get("exitY")
            entryX = style_d.get("entryX")
            entryY = style_d.get("entryY")
            waypoints = []
            label_offset = (0.0, 0.0)
            src_point = dst_point = None
            if geom is not None:
                arr = geom.find("Array")
                if arr is not None:
                    for pt in arr.findall("mxPoint"):
                        waypoints.append((float(pt.get("x")), float(pt.get("y"))))
                # Top-level mxPoints: label offset and fixed source/target
                # endpoints (point-anchored edges from draw.io Desktop).
                for pt in geom.findall("mxPoint"):
                    role = pt.get("as")
                    if role == "offset":
                        label_offset = (float(pt.get("x", 0)), float(pt.get("y", 0)))
                    elif role == "sourcePoint":
                        src_point = (float(pt.get("x", 0)), float(pt.get("y", 0)))
                    elif role == "targetPoint":
                        dst_point = (float(pt.get("x", 0)), float(pt.get("y", 0)))
            edges.append(
                Edge(
                    cid,
                    cell.get("source"),
                    cell.get("target"),
                    float(ex) if ex else None,
                    float(ey) if ey else None,
                    float(entryX) if entryX else None,
                    float(entryY) if entryY else None,
                    waypoints,
                    cell.get("value") or "",
                    style_d.get("strokeColor", ""),
                    label_offset,
                    src_point,
                    dst_point,
                )
            )
    return boxes, edges


def _anchor_travels_horizontally(ex: float | None, ey: float | None) -> bool | None:
    """Which way does an edge leave/meet a box at anchor (ex, ey)?

    draw.io's orthogonalEdgeStyle exits perpendicular to the box edge the
    anchor sits on: an anchor on a left/right edge (ex == 0 or 1) travels
    horizontally first; one on a top/bottom edge (ey == 0 or 1) travels
    vertically first. Returns True (horizontal), False (vertical), or None
    when it can't be determined (no anchor, or an interior point).
    """
    if ex is None or ey is None:
        return None
    if ex in (0.0, 1.0):
        return True
    if ey in (0.0, 1.0):
        return False
    return None


def _square_front(pts, horizontal):
    """If the first segment is diagonal, insert the L-bend corner draw.io
    actually renders, so the reconstructed stub matches the real route."""
    if horizontal is None or len(pts) < 2:
        return pts
    a, nxt = pts[0], pts[1]
    if segment_is_orthogonal(a, nxt):
        return pts
    corner = (nxt[0], a[1]) if horizontal else (a[0], nxt[1])
    return [a, corner, *pts[1:]]


def _square_back(pts, horizontal):
    """Same as _square_front, for the final (target-anchor) stub."""
    if horizontal is None or len(pts) < 2:
        return pts
    prev, b = pts[-2], pts[-1]
    if segment_is_orthogonal(prev, b):
        return pts
    corner = (prev[0], b[1]) if horizontal else (b[0], prev[1])
    return [*pts[:-1], corner, b]


def edge_polyline(edge: Edge, boxes: dict[str, Box]) -> list[tuple[float, float]]:
    """Reconstruct the rendered polyline: source-anchor → waypoints →
    target-anchor, with the source and target *stubs* squared into the
    orthogonal L-bend draw.io draws when an anchor doesn't line up with its
    adjacent point. Interior waypoint-to-waypoint segments are left as
    authored — a diagonal there is a real non-determinism (DIAGONAL check).
    """
    src = boxes.get(edge.src)
    dst = boxes.get(edge.dst)
    # Resolve each endpoint to a coordinate: a connected cell's anchor/centre,
    # or — for a point-anchored edge — its fixed sourcePoint/targetPoint.
    if src is not None:
        a = (
            src.anchor(edge.exitX, edge.exitY)
            if edge.exitX is not None and edge.exitY is not None
            else (src.x + src.w / 2, src.y + src.h / 2)
        )
    else:
        a = edge.src_point
    if dst is not None:
        b = (
            dst.anchor(edge.entryX, edge.entryY)
            if edge.entryX is not None and edge.entryY is not None
            else (dst.x + dst.w / 2, dst.y + dst.h / 2)
        )
    else:
        b = edge.dst_point
    if a is None or b is None:
        return []
    pts = [a, *edge.waypoints, b]
    pts = _square_front(pts, _anchor_travels_horizontally(edge.exitX, edge.exitY))
    pts = _square_back(pts, _anchor_travels_horizontally(edge.entryX, edge.entryY))
    return pts


def edge_label_center(
    edge: Edge, poly: list[tuple[float, float]]
) -> tuple[float, float]:
    """Estimate the absolute position of the edge label.

    draw.io places labels at the polyline's geometric center (midpoint of
    its longest segment, roughly). We approximate by taking the midpoint
    of the longest axis-aligned segment, then applying the label_offset.
    """
    if not poly or len(poly) < 2:
        return (0.0, 0.0)
    # Find longest segment
    longest = None
    longest_len = -1.0
    for i in range(len(poly) - 1):
        a, b = poly[i], poly[i + 1]
        seg_len = abs(b[0] - a[0]) + abs(b[1] - a[1])
        if seg_len > longest_len:
            longest_len = seg_len
            longest = (a, b)
    a, b = longest
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return (mid[0] + edge.label_offset[0], mid[1] + edge.label_offset[1])


_LABEL_ENTITIES = {
    "&nbsp;": " ",
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
}


def normalise_label(label: str) -> list[str]:
    """Split a label into plain-text lines for measurement.

    Treats <div>..</div> and <br> as line separators, strips remaining
    HTML tags, then decodes common entities. Returns one string per line.

    Both <div> and </div> break the line: draw.io renders a <div> as a
    block, so 'Verify<div>Token</div>' is two lines, not one. (Treating
    the opening tag as a no-op measured the skill's own locked multi-line
    convention as a single double-width line.) Blank lines left behind by
    the tag boundaries are dropped so they don't inflate the line count.
    """
    s = label.replace("</div>", "\n").replace("<div>", "\n")
    s = s.replace("<br/>", "\n").replace("<br>", "\n")
    out_lines = []
    for ln in s.split("\n"):
        cleaned = ln
        while "<" in cleaned and ">" in cleaned:
            lt = cleaned.find("<")
            gt = cleaned.find(">", lt)
            if gt == -1:
                break
            cleaned = cleaned[:lt] + cleaned[gt + 1 :]
        for k, v in _LABEL_ENTITIES.items():
            cleaned = cleaned.replace(k, v)
        out_lines.append(cleaned)
    stripped = [ln for ln in out_lines if ln.strip()]
    return stripped or out_lines[:1]


def short_label(value: str, n: int = 25) -> str:
    """A readable one-line snippet of a cell's label for messages.

    Uses normalise_label so labels that start with an HTML tag (e.g.
    '<b>Pipeline...') render as their text, not as an empty string.
    """
    text = " ".join(normalise_label(value)).strip()
    return text[:n]


def endpoint_label(boxes: dict, cell_id) -> str:
    """Readable label for an edge endpoint, tolerating a point-anchored
    end (no cell) — returns '(point)' rather than raising."""
    b = boxes.get(cell_id)
    return short_label(b.label) if b is not None else "(point)"


def label_bbox(
    center: tuple[float, float],
    label: str,
    per_char_px: float = LABEL_PER_CHAR_PX,
    line_height: float = LABEL_LINE_HEIGHT,
    x_pad: float = LABEL_X_PAD,
    y_pad: float = LABEL_Y_PAD,
) -> tuple[float, float, float, float]:
    """Estimate a label's bounding box (x1, y1, x2, y2) centred on `center`.

    Width is char-count based (5.5 px/char @ font 10); height is line-count
    based. HTML tags and common entities are stripped before measuring.
    """
    plain_lines = normalise_label(label) or [""]
    max_chars = max((len(ln) for ln in plain_lines), default=0)
    w = max_chars * per_char_px + 2 * x_pad
    h = len(plain_lines) * line_height + 2 * y_pad
    cx, cy = center
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def rects_overlap(
    r1: tuple[float, float, float, float], r2: tuple[float, float, float, float]
) -> bool:
    """Return True if two (x1, y1, x2, y2) rectangles intersect."""
    x1a, y1a, x1b, y1b = r1
    x2a, y2a, x2b, y2b = r2
    return not (x1b < x2a or x2b < x1a or y1b < y2a or y2b < y1a)


def labels_overlap(
    c1: tuple[float, float],
    label1: str,
    c2: tuple[float, float],
    label2: str,
    per_char_px: float = LABEL_PER_CHAR_PX,
    line_height: float = LABEL_LINE_HEIGHT,
    x_pad: float = LABEL_X_PAD,
    y_pad: float = LABEL_Y_PAD,
) -> bool:
    """Return True if two label bounding boxes overlap."""
    if not label1.strip() or not label2.strip():
        return False
    b1 = label_bbox(c1, label1, per_char_px, line_height, x_pad, y_pad)
    b2 = label_bbox(c2, label2, per_char_px, line_height, x_pad, y_pad)
    return rects_overlap(b1, b2)


def segments(polyline: list[tuple[float, float]]):
    """Yield (a, b) segment tuples."""
    for i in range(len(polyline) - 1):
        yield polyline[i], polyline[i + 1]


def segment_is_orthogonal(
    a: tuple[float, float], b: tuple[float, float], ortho_tol: float = ORTHO_TOL
) -> bool:
    """Return True if the segment is horizontal or vertical (within
    ortho_tol). A False here means the segment is diagonal — the validator
    can't reason about draw.io's real orthogonal route for it."""
    return abs(a[0] - b[0]) <= ortho_tol or abs(a[1] - b[1]) <= ortho_tol


def segment_crosses_box(
    a: tuple[float, float],
    b: tuple[float, float],
    box: Box,
    edge_buffer: float = EDGE_BUFFER,
    ortho_tol: float = ORTHO_TOL,
) -> bool:
    """Return True if the segment from a to b passes through the box's ink.

    That means the shape plus, for a bottom-labelled icon, its caption band —
    see Box.obstacle_rect().
    """
    return segment_crosses_rect(a, b, box.obstacle_rect(), edge_buffer, ortho_tol)


def segment_crosses_rect(
    a: tuple[float, float],
    b: tuple[float, float],
    rect: tuple[float, float, float, float],
    edge_buffer: float = EDGE_BUFFER,
    ortho_tol: float = ORTHO_TOL,
) -> bool:
    """Return True if the segment from a to b passes through the
    interior of the rect. Treats near-orthogonal segments (delta ≤
    ortho_tol on the minor axis) as orthogonal — this catches cases
    where source/target anchor y values differ by half a pixel because
    of integer-vs-fractional box-midline arithmetic."""
    ax, ay = a
    bx, by = b
    rx1, ry1, rx2, ry2 = rect
    x_min = rx1 + edge_buffer
    x_max = rx2 - edge_buffer
    y_min = ry1 + edge_buffer
    y_max = ry2 - edge_buffer
    if x_min >= x_max or y_min >= y_max:
        return False
    # Horizontal segment (allow small y delta)
    if abs(ay - by) <= ortho_tol:
        y_avg = (ay + by) / 2
        if not (y_min <= y_avg <= y_max):
            return False
        seg_x1, seg_x2 = sorted((ax, bx))
        return seg_x1 < x_max and seg_x2 > x_min
    # Vertical segment (allow small x delta)
    if abs(ax - bx) <= ortho_tol:
        x_avg = (ax + bx) / 2
        if not (x_min <= x_avg <= x_max):
            return False
        seg_y1, seg_y2 = sorted((ay, by))
        return seg_y1 < y_max and seg_y2 > y_min
    return False


def segments_overlap(
    s1: tuple, s2: tuple, min_overlap: float = MIN_OVERLAP, ortho_tol: float = ORTHO_TOL
) -> bool:
    """Return True if two near-orthogonal segments lie on the same line
    (within ortho_tol) and overlap for at least `min_overlap` units."""
    (a1, b1), (a2, b2) = s1, s2
    # Both horizontal (y nearly constant within each, and roughly equal)
    if (
        abs(a1[1] - b1[1]) <= ortho_tol
        and abs(a2[1] - b2[1]) <= ortho_tol
        and abs(((a1[1] + b1[1]) / 2) - ((a2[1] + b2[1]) / 2)) <= ortho_tol
    ):
        x1, x2 = sorted((a1[0], b1[0]))
        x3, x4 = sorted((a2[0], b2[0]))
        overlap = min(x2, x4) - max(x1, x3)
        return overlap >= min_overlap
    # Both vertical
    if (
        abs(a1[0] - b1[0]) <= ortho_tol
        and abs(a2[0] - b2[0]) <= ortho_tol
        and abs(((a1[0] + b1[0]) / 2) - ((a2[0] + b2[0]) / 2)) <= ortho_tol
    ):
        y1, y2 = sorted((a1[1], b1[1]))
        y3, y4 = sorted((a2[1], b2[1]))
        overlap = min(y2, y4) - max(y1, y3)
        return overlap >= min_overlap
    return False


def segment_is_vertical(
    a: tuple[float, float], b: tuple[float, float], ortho_tol: float = ORTHO_TOL
) -> bool:
    """Return True if the segment runs vertically (within ortho_tol)."""
    return abs(a[0] - b[0]) <= ortho_tol and abs(a[1] - b[1]) > ortho_tol


def polyline_length(polyline: list[tuple[float, float]]) -> float:
    """Total rendered length of an orthogonal polyline (manhattan sum)."""
    return sum(abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in segments(polyline))


def label_text_width(label: str, per_char_px: float = LABEL_PER_CHAR_PX) -> float:
    """Estimated width of a label's widest text line, WITHOUT the padding
    label_bbox adds. Used by SHORT_LABELLED_EDGE, where the question is
    whether the ink fits on the edge — the padding is breathing room, not
    something the edge has to span."""
    plain_lines = normalise_label(label) or [""]
    return max((len(ln) for ln in plain_lines), default=0) * per_char_px


def box_inside(inner: Box, outer: Box, margin: float = CONTAINMENT_MARGIN) -> bool:
    """Return True if `inner` sits geometrically within `outer`'s bounds.

    draw.io zones are drawn as siblings (both parent="1") and nest only
    visually, so containment is a geometric question, not a parent-id one.
    """
    return (
        inner.x >= outer.x - margin
        and inner.x2 <= outer.x2 + margin
        and inner.y >= outer.y - margin
        and inner.y2 <= outer.y2 + margin
    )


def edge_endpoint_inside(edge: Edge, boxes: dict[str, Box], container: Box) -> bool:
    """Return True if either end of `edge` lives inside `container` — a
    connected box within its bounds, or a point-anchored endpoint that
    falls inside it. The container itself doesn't count as its own
    endpoint (that case is already exempted by the src/dst id check)."""
    for cell_id, point in ((edge.src, edge.src_point), (edge.dst, edge.dst_point)):
        endpoint = boxes.get(cell_id)
        if endpoint is not None:
            if endpoint is not container and box_inside(endpoint, container):
                return True
        elif point is not None and container.contains_point(*point):
            return True
    return False


def segment_crosses_container_title(
    a: tuple[float, float],
    b: tuple[float, float],
    box: Box,
    title_band_height: float = TITLE_BAND_HEIGHT,
    edge_buffer: float = TITLE_EDGE_BUFFER,
    ortho_tol: float = ORTHO_TOL,
) -> bool:
    """Return True if the segment crosses the title text band of a
    container box. Containers have their title rendered at the top
    with spacingTop=8 plus ~font-size px. A 28px band from box.y
    covers fontSize up to ~18 plus its top spacing.

    A horizontal segment running across the container's title band
    is the most common failure (an arrow running across the title
    text of a non-source/non-target container). A vertical segment
    that just dips through the band is also flagged.
    """
    ax, ay = a
    bx, by = b
    x_min = box.x + edge_buffer
    x_max = box.x2 - edge_buffer
    y_min = box.y + edge_buffer
    y_max = box.y + title_band_height
    if x_min >= x_max:
        return False
    # Horizontal segment
    if abs(ay - by) <= ortho_tol:
        y_avg = (ay + by) / 2
        if not (y_min <= y_avg <= y_max):
            return False
        seg_x1, seg_x2 = sorted((ax, bx))
        return seg_x1 < x_max and seg_x2 > x_min
    # Vertical segment dipping through the band
    if abs(ax - bx) <= ortho_tol:
        x_avg = (ax + bx) / 2
        if not (x_min <= x_avg <= x_max):
            return False
        seg_y1, seg_y2 = sorted((ay, by))
        return seg_y1 < y_max and seg_y2 > y_min
    return False


def validate(path: str) -> list[str]:
    boxes, edges = parse_drawio(path)
    violations: list[str] = []

    # 0. Dangling edges — source or target id doesn't resolve to a shape.
    # Check before building polylines, since edge_polyline silently returns
    # [] for these (they'd otherwise vanish without a diagnostic).
    for e in edges:
        # An endpoint is fine if it resolves to a cell OR is pinned to a
        # fixed coordinate (sourcePoint/targetPoint — a normal draw.io Desktop
        # hand-tuning artifact). Only a truly unresolvable endpoint is dangling.
        missing = []
        if e.src not in boxes and e.src_point is None:
            missing.append("source")
        if e.dst not in boxes and e.dst_point is None:
            missing.append("target")
        if missing:
            violations.append(
                f"DANGLING: edge '{short_label(e.label)}' references missing "
                f"{' and '.join(missing)} "
                f"(source={e.src!r}, target={e.dst!r})"
            )

    # 1b. Unknown icon names. Run before the geometry work: this is a name
    # check, and it must reach cells whose geometry says nothing useful. A
    # mistyped stencil renders as an empty shape with no error anywhere, so
    # nothing else in the loop can catch it.
    icon_universe = load_icon_names()
    lowered = {n.lower(): n for n in icon_universe}
    for box in boxes.values():
        for kind, ref in icon_references(box.style):
            if kind == "remote":
                # Independent of the catalog: a remote URL is not offline-safe
                # whether or not we can check names.
                violations.append(
                    f"UNKNOWN_ICON: cell '{short_label(box.label)}' loads a "
                    f"remote image {ref!r}; the diagram is not offline-safe "
                    f"— embed the SVG instead"
                )
                continue
            if not icon_universe:
                continue
            if ref in icon_universe or ref.lower() in lowered:
                continue
            near = difflib.get_close_matches(ref, icon_universe, n=1, cutoff=0.8)
            hint = f" — did you mean {near[0]!r}?" if near else ""
            violations.append(
                f"UNKNOWN_ICON: cell '{short_label(box.label)}' uses "
                f"{ref!r}, which is not in the bundled icon catalog{hint}"
            )

    # Pre-compute polylines
    edge_lines = {}
    for e in edges:
        poly = edge_polyline(e, boxes)
        if len(poly) >= 2:
            edge_lines[e.cell_id] = (e, poly)

    # 1. Edge segments crossing non-source/non-target/non-container boxes.
    # Note: we no longer skip "title" or "legend" boxes by hard-coded
    # canvas coordinates; if an edge segment crosses your title bar or
    # legend strip, that's a genuine routing problem worth flagging.
    for _eid, (edge, poly) in edge_lines.items():
        for a, b in segments(poly):
            for bid, box in boxes.items():
                if box.is_container:
                    continue
                # A glyph inside a box is not a second obstacle: the box it
                # decorates is already checked at the same coordinates, so
                # flagging both reports one routing problem twice.
                if box.is_decoration:
                    continue
                if bid == edge.src or bid == edge.dst:
                    continue
                if segment_crosses_box(a, b, box):
                    src_label = endpoint_label(boxes, edge.src)
                    dst_label = endpoint_label(boxes, edge.dst)
                    box_label = short_label(box.label)
                    violations.append(
                        f"CROSSING: edge '{edge.label}' "
                        f"({src_label} → {dst_label}) "
                        f"segment {a}→{b} passes through box '{box_label}'"
                    )

    # 1b. Edge segments crossing container title bands.
    # A container's title band spans its full width, so an arrow dropping
    # into a box INSIDE the zone (the documented bottom-service-band
    # pattern) must pierce it. That vertical entry stub is exempt; a
    # segment running ALONG the band still sits on the title text and
    # fires, whether or not its endpoints live in the zone.
    for _eid, (edge, poly) in edge_lines.items():
        for a, b in segments(poly):
            for bid, box in boxes.items():
                if not box.is_container:
                    continue
                if bid == edge.src or bid == edge.dst:
                    continue
                if segment_is_vertical(a, b) and edge_endpoint_inside(edge, boxes, box):
                    continue
                if segment_crosses_container_title(a, b, box):
                    src_label = endpoint_label(boxes, edge.src)
                    dst_label = endpoint_label(boxes, edge.dst)
                    box_label = short_label(box.label)
                    violations.append(
                        f"TEXT_OVERLAP: edge '{edge.label}' "
                        f"({src_label} → {dst_label}) "
                        f"segment {a}→{b} crosses title of container '{box_label}'"
                    )

    # 2. Pairs of edges with overlapping segments
    seen_pairs = set()
    edge_ids = list(edge_lines.keys())
    for i, e1id in enumerate(edge_ids):
        for e2id in edge_ids[i + 1 :]:
            e1, poly1 = edge_lines[e1id]
            e2, poly2 = edge_lines[e2id]
            for s1 in segments(poly1):
                for s2 in segments(poly2):
                    if segments_overlap(s1, s2):
                        key = tuple(sorted((e1id, e2id)))
                        if key in seen_pairs:
                            continue
                        seen_pairs.add(key)
                        violations.append(
                            f"OVERLAP: edge '{e1.label}' overlaps with "
                            f"edge '{e2.label}' (segments {s1} and {s2})"
                        )

    # 2b. Diagonal (non-orthogonal) segments — the reconstructed route is
    # not axis-aligned, so draw.io's real orthogonal auto-route is unchecked.
    for _eid, (edge, poly) in edge_lines.items():
        for a, b in segments(poly):
            if a == b:
                continue
            if not segment_is_orthogonal(a, b):
                src_label = endpoint_label(boxes, edge.src)
                dst_label = endpoint_label(boxes, edge.dst)
                violations.append(
                    f"DIAGONAL: edge '{edge.label}' "
                    f"({src_label} → {dst_label}) has non-orthogonal "
                    f"segment {a}→{b}; add waypoints or exit/entry anchors "
                    f"so the route is orthogonal and checkable"
                )
                break  # one report per edge is enough to act on

    # 3. Pairs of edge labels with overlapping bounding boxes
    label_seen = set()
    for i, e1id in enumerate(edge_ids):
        for e2id in edge_ids[i + 1 :]:
            e1, poly1 = edge_lines[e1id]
            e2, poly2 = edge_lines[e2id]
            if not e1.label.strip() or not e2.label.strip():
                continue
            c1 = edge_label_center(e1, poly1)
            c2 = edge_label_center(e2, poly2)
            b1 = label_bbox(c1, e1.label)
            b2 = label_bbox(c2, e2.label)
            if rects_overlap(b1, b2):
                ov_x = min(b1[2], b2[2]) - max(b1[0], b2[0])
                ov_y = min(b1[3], b2[3]) - max(b1[1], b2[1])
                if min(ov_x, ov_y) < LABEL_BOX_MIN_OVERLAP:
                    continue  # a graze — masked by the labels' white bg
                key = tuple(sorted((e1id, e2id)))
                if key in label_seen:
                    continue
                label_seen.add(key)
                violations.append(
                    f"LABEL_OVERLAP: label '{e1.label}' at {c1} "
                    f"overlaps with label '{e2.label}' at {c2} "
                    f"by {ov_x:.0f}x{ov_y:.0f}px"
                )

    # 4. Edge labels overlapping a non-source/non-target solid box.
    # Containers are exempt — labels legitimately sit inside zone
    # containers. The edge's own endpoints are exempt too, since a label
    # naturally rests near the boxes it connects.
    for _eid, (edge, poly) in edge_lines.items():
        if not edge.label.strip():
            continue
        c = edge_label_center(edge, poly)
        lb = label_bbox(c, edge.label)
        for bid, box in boxes.items():
            if box.is_container:
                continue
            if box.is_decoration:
                continue
            if bid == edge.src or bid == edge.dst:
                continue
            if rects_overlap(lb, box.obstacle_rect()):
                ov_x = min(lb[2], box.x2) - max(lb[0], box.x)
                ov_y = min(lb[3], box.y2) - max(lb[1], box.y)
                if min(ov_x, ov_y) < LABEL_BOX_MIN_OVERLAP:
                    continue  # a graze — masked by the label's white bg
                box_label = short_label(box.label)
                violations.append(
                    f"LABEL_BOX_OVERLAP: label '{edge.label}' at {c} "
                    f"overlaps box '{box_label}' "
                    f"by {ov_x:.0f}x{ov_y:.0f}px"
                )

    # 5. Labelled edges shorter than their own label. The label has nowhere
    # to live, so it renders as a caption floating over the boxes at either
    # end — a failure LABEL_BOX_OVERLAP can't see, since it exempts the
    # edge's own endpoints (and each overhang alone is often a sub-8 px
    # graze anyway).
    for _eid, (edge, poly) in edge_lines.items():
        if not edge.label.strip():
            continue
        text_w = label_text_width(edge.label)
        route_len = polyline_length(poly)
        if route_len < text_w:
            src_label = endpoint_label(boxes, edge.src)
            dst_label = endpoint_label(boxes, edge.dst)
            violations.append(
                f"SHORT_LABELLED_EDGE: edge '{edge.label}' "
                f"({src_label} → {dst_label}) is {route_len:.0f}px long but "
                f"its label needs ~{text_w:.0f}px; widen the gap or stack "
                f"the label into narrower <div> lines"
            )

    return violations


def main():
    from pathlib import Path

    paths = sys.argv[1:]
    if not paths:
        paths = sorted(str(p) for p in Path(".").glob("*.drawio"))
        if not paths:
            print("Usage: python validate.py <file.drawio> [more.drawio ...]")
            print("       python validate.py     # validate every .drawio in cwd")
            sys.exit(2)
    total_err = 0
    total_warn = 0
    for p in paths:
        print(f"\n=== {p} ===")
        v = validate(p)
        if not v:
            print("  ✓ no violations")
            continue
        for line in v:
            if violation_severity(line) == "error":
                print("  ✗", line)
                total_err += 1
            else:
                print("  ⚠", line)
                total_warn += 1
    print(f"\nErrors: {total_err}   Warnings: {total_warn}")
    # Warnings are advisory; only hard errors fail the build.
    sys.exit(1 if total_err else 0)


if __name__ == "__main__":
    main()
