"""Minimal fixture builders for validator tests.

Each build_*() writes a small .drawio file that exhibits exactly one
violation type (or zero, for the clean case). They share local XML
helpers rather than importing from build_template.py — the template
is meant to be copied, not imported.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom


def _new_doc():
    """Return (mxfile, root, counter) for a fresh empty drawio doc."""
    mxfile = ET.Element(
        "mxfile", host="app.diagrams.net", type="device", version="24.0.0"
    )
    diagram = ET.SubElement(mxfile, "diagram", name="fixture", id="fixture")
    graph = ET.SubElement(
        diagram,
        "mxGraphModel",
        dx="800",
        dy="600",
        grid="0",
        gridSize="10",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="1",
        pageScale="1",
        pageWidth="800",
        pageHeight="600",
        math="0",
        shadow="0",
    )
    root = ET.SubElement(graph, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    return mxfile, root, [2]


def _box(root, counter, x, y, w, h, value="", is_container=False):
    cid = str(counter[0])
    counter[0] += 1
    if is_container:
        style = (
            "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;"
            "strokeColor=#333333;strokeWidth=2;dashed=1;"
            "verticalAlign=top;align=left;fontSize=14;"
        )
    else:
        style = (
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#cccccc;"
            "strokeColor=#666666;strokeWidth=1;fontSize=12;"
        )
    c = ET.SubElement(
        root, "mxCell", id=cid, value=value, style=style, vertex="1", parent="1"
    )
    ET.SubElement(
        c,
        "mxGeometry",
        x=str(x),
        y=str(y),
        width=str(w),
        height=str(h),
        **{"as": "geometry"},
    )
    return cid


def _edge(
    root,
    counter,
    src,
    dst,
    exitX=None,
    exitY=None,
    entryX=None,
    entryY=None,
    waypoints=None,
    label="",
    label_offset=None,
    src_point=None,
    dst_point=None,
):
    """src / dst may be None to leave that end unconnected. Pass src_point /
    dst_point=(x,y) to pin an end to a fixed coordinate (point-anchored
    edge, as draw.io Desktop writes after hand-tuning)."""
    cid = str(counter[0])
    counter[0] += 1
    exit_str = (
        f"exitX={exitX};exitY={exitY};exitDx=0;exitDy=0;" if exitX is not None else ""
    )
    entry_str = (
        f"entryX={entryX};entryY={entryY};entryDx=0;entryDy=0;"
        if entryX is not None
        else ""
    )
    style = (
        f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;"
        f"{exit_str}{entry_str}"
        f"strokeColor=#333333;strokeWidth=2;endArrow=classic;"
        f"fontSize=10;labelBackgroundColor=#ffffff;"
    )
    attrs = {"id": cid, "value": label, "style": style, "edge": "1", "parent": "1"}
    if src is not None:
        attrs["source"] = src
    if dst is not None:
        attrs["target"] = dst
    c = ET.SubElement(root, "mxCell", **attrs)
    geom = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
    if src_point:
        ET.SubElement(
            geom,
            "mxPoint",
            x=str(src_point[0]),
            y=str(src_point[1]),
            **{"as": "sourcePoint"},
        )
    if dst_point:
        ET.SubElement(
            geom,
            "mxPoint",
            x=str(dst_point[0]),
            y=str(dst_point[1]),
            **{"as": "targetPoint"},
        )
    if waypoints:
        arr = ET.SubElement(geom, "Array", **{"as": "points"})
        for x, y in waypoints:
            ET.SubElement(arr, "mxPoint", x=str(x), y=str(y))
    if label_offset:
        ET.SubElement(
            geom,
            "mxPoint",
            x=str(label_offset[0]),
            y=str(label_offset[1]),
            **{"as": "offset"},
        )
    return cid


def _write(mxfile, out_path):
    xml_bytes = ET.tostring(mxfile, encoding="utf-8")
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ")
    with open(out_path, "w") as f:
        f.write(pretty)


# ----------------------------------------------------------------------
# Fixtures — each exhibits exactly ONE validator violation type, or none.
# ----------------------------------------------------------------------


def build_clean(out_path):
    """Three boxes in a row, two short edges between adjacent boxes.
    Zero violations."""
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 200, 80, 50, "A")
    b = _box(root, c, 300, 200, 80, 50, "B")
    d = _box(root, c, 500, 200, 80, 50, "C")
    _edge(root, c, a, b, exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _edge(root, c, b, d, exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _write(mxfile, out_path)


def build_crossing(out_path):
    """Single edge A→C drawn as a straight horizontal line through B.

    No waypoints — the polyline is (180, 225) → (500, 225), which
    runs through B's interior at y=225, x=(300, 380).
    Expected: one CROSSING violation, no others.
    """
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 200, 80, 50, "A")
    _box(root, c, 300, 200, 80, 50, "B")
    d = _box(root, c, 500, 200, 80, 50, "C")
    _edge(root, c, a, d, exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _write(mxfile, out_path)


def build_overlap(out_path):
    """Two edges from the same source share a horizontal corridor.

    A→B straight at y=225, x=(180, 300). A→C with waypoints that share
    (180, 225)..(220, 225) with A→B before diving below and right. The
    route is fully orthogonal (it turns back up to y=225 before entering
    C) so it trips OVERLAP without also tripping DIAGONAL.
    Expected: one OVERLAP violation, no others.
    """
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 200, 80, 50, "A")
    b = _box(root, c, 300, 200, 80, 50, "B")
    d = _box(root, c, 500, 200, 80, 50, "C")
    _edge(root, c, a, b, exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _edge(
        root,
        c,
        a,
        d,
        exitX=1,
        exitY=0.5,
        entryX=0,
        entryY=0.5,
        waypoints=[(220, 225), (220, 350), (460, 350), (460, 225)],
    )
    _write(mxfile, out_path)


def build_diagonal(out_path):
    """Single edge with an INTERIOR waypoint-to-waypoint diagonal.

    The anchors line up as orthogonal stubs (and the stubs are squared on
    reconstruction anyway), but the two interior waypoints (140,220) and
    (260,320) are offset on both axes, leaving a diagonal mid-route. Stub-
    squaring only touches the anchor stubs, so this interior diagonal
    survives and is flagged — draw.io would square it, so the route is
    non-deterministic.
    Expected: one DIAGONAL violation, no others.
    """
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 100, 80, 50, "A")
    b = _box(root, c, 100, 400, 80, 50, "B")
    _edge(
        root,
        c,
        a,
        b,
        exitX=0.5,
        exitY=1,
        entryX=0.5,
        entryY=0,
        waypoints=[(140, 220), (260, 320)],
    )
    _write(mxfile, out_path)


def build_stub_clean(out_path):
    """Misaligned anchors, no waypoints — the classic anchor-stub case.

    A exits right at (180,125); B is entered left at (400,325). The raw
    anchor→anchor line is diagonal, but draw.io squares this stub into an
    L-bend, and so does edge_polyline. The reconstructed route is therefore
    orthogonal and crosses nothing.
    Expected: ZERO violations (regression guard for stub-squaring).
    """
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 100, 80, 50, "A")
    b = _box(root, c, 400, 300, 80, 50, "B")
    _edge(root, c, a, b, exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _write(mxfile, out_path)


def build_dangling(out_path):
    """Single edge whose target id points at a box that doesn't exist.

    Expected: one DANGLING violation, no others (no polyline is built for
    a dangling edge, so no geometric checks run on it).
    """
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 200, 80, 50, "A")
    _edge(root, c, a, "9999", exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _write(mxfile, out_path)


def build_point_anchored(out_path):
    """Edge with a connected source cell but a point-anchored target (a
    fixed targetPoint, no target cell) — a normal draw.io Desktop artifact.

    The edge from A exits right at (180,225) and ends at the fixed point
    (400,225). It must NOT fire DANGLING (the target is pinned to a
    coordinate) and the route is orthogonal, so zero violations.
    Expected: zero violations (regression guard for point-anchored edges).
    """
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 200, 80, 50, "A")
    _edge(root, c, a, None, exitX=1, exitY=0.5, dst_point=(400, 225))
    _write(mxfile, out_path)


def build_text_overlap(out_path):
    """Edge segment routed across a non-src/non-dst container's title band.

    Container with title 'Container' at (100, 80, 350, 300) — title band
    occupies y=80..108. A and B sit outside the container; the edge from
    A to B is routed up over the top, running across y=90 in the
    container's x range.
    Expected: one TEXT_OVERLAP violation, no others.
    """
    mxfile, root, c = _new_doc()
    _box(root, c, 100, 80, 350, 300, "Container", is_container=True)
    a = _box(root, c, 30, 200, 60, 40, "A")
    e = _box(root, c, 500, 200, 60, 40, "B")
    _edge(
        root,
        c,
        a,
        e,
        exitX=0.5,
        exitY=0,
        entryX=0.5,
        entryY=0,
        waypoints=[(60, 90), (530, 90)],
    )
    _write(mxfile, out_path)


def build_container_entry(out_path):
    """Edge dropping straight down into a box INSIDE a bottom-band container.

    Container 'External dependencies' at (100, 300, 400, 150) — title band
    occupies y=300..328. D sits inside it; A sits above, outside. The edge
    A→D drops vertically at x=210, which necessarily pierces the container's
    full-width title band on its way in.

    This is the documented bottom-service-band pattern, so the vertical
    entry segment is exempt from TEXT_OVERLAP (the edge's target lives
    inside the container).
    Expected: ZERO violations (regression guard for the entry exemption).
    """
    mxfile, root, c = _new_doc()
    _box(root, c, 100, 300, 400, 150, "External dependencies", is_container=True)
    a = _box(root, c, 150, 100, 120, 60, "A")
    d = _box(root, c, 150, 350, 120, 60, "D")
    _edge(root, c, a, d, exitX=0.5, exitY=1, entryX=0.5, entryY=0)
    _write(mxfile, out_path)


def build_text_overlap_inside(out_path):
    """Two boxes INSIDE a container, wired by a route that runs along the
    container's title band.

    The entry exemption is deliberately narrow: it covers only the vertical
    segments that pierce the band on the way in or out. A horizontal segment
    running *along* the band still sits on top of the title text, so it must
    still fire — even though both endpoints live inside the container.
    Expected: one TEXT_OVERLAP violation, no others.
    """
    mxfile, root, c = _new_doc()
    _box(root, c, 100, 100, 400, 300, "Zone", is_container=True)
    p = _box(root, c, 150, 200, 100, 60, "P")
    q = _box(root, c, 350, 200, 100, 60, "Q")
    _edge(
        root,
        c,
        p,
        q,
        exitX=0.5,
        exitY=0,
        entryX=0.5,
        entryY=0,
        waypoints=[(200, 115), (400, 115)],
    )
    _write(mxfile, out_path)


def build_short_labelled_edge(out_path):
    """Two boxes 40 px apart joined by an edge carrying a 14-char label.

    The label ('Loads / caches', ~97 px wide including padding) is more
    than twice the rendered length of the edge it belongs to, so it renders
    as a caption floating over both boxes rather than as an edge label. Both
    boxes are the edge's own endpoints, so LABEL_BOX_OVERLAP (which exempts
    them) stays silent — this is the gap SHORT_LABELLED_EDGE fills.
    Expected: one SHORT_LABELLED_EDGE violation, no others.
    """
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 200, 80, 50, "A")
    b = _box(root, c, 220, 200, 80, 50, "B")
    _edge(
        root, c, a, b, exitX=1, exitY=0.5, entryX=0, entryY=0.5, label="Loads / caches"
    )
    _write(mxfile, out_path)


def build_label_overlap(out_path):
    """Two parallel edges with labels offset to land at the same point.

    Edge A→B has label 'Same Spot' with no offset → label centred at
    (280, 125). Edge C→D has label 'Same Spot Too' with offset
    (0, -150) → label centred at (280, 125) too. The bounding boxes
    overlap completely. Segments themselves are 150 px apart so neither
    OVERLAP nor CROSSING fires.
    Expected: one LABEL_OVERLAP violation, no others.
    """
    mxfile, root, c = _new_doc()
    a = _box(root, c, 100, 100, 60, 50, "A")
    b = _box(root, c, 400, 100, 60, 50, "B")
    d = _box(root, c, 100, 250, 60, 50, "C")
    e = _box(root, c, 400, 250, 60, 50, "D")
    _edge(root, c, a, b, exitX=1, exitY=0.5, entryX=0, entryY=0.5, label="Same Spot")
    _edge(
        root,
        c,
        d,
        e,
        exitX=1,
        exitY=0.5,
        entryX=0,
        entryY=0.5,
        label="Same Spot Too",
        label_offset=(0, -150),
    )
    _write(mxfile, out_path)


ICON_CHILD_STYLE = (
    "sketch=0;outlineConnect=0;dashed=0;html=1;aspect=fixed;"
    "pointerEvents=0;movable=0;resizable=0;rotatable=0;editable=0;"
    "connectable=0;labelPosition=center;verticalLabelPosition=middle;"
    "verticalAlign=middle;align=center;strokeColor=#ffffff;fillColor=#ED7100;"
    "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;"
    "drawioSkillRole=icon;"
)

ICON_NODE_STYLE = (
    "sketch=0;outlineConnect=0;dashed=0;html=1;aspect=fixed;pointerEvents=1;"
    "labelPosition=center;verticalLabelPosition=bottom;align=center;"
    "verticalAlign=top;fontSize=11;fontColor=#232F3E;strokeColor=#ffffff;"
    "fillColor=#ED7100;shape=mxgraph.aws4.resourceIcon;"
    "resIcon=mxgraph.aws4.lambda;"
)


def _icon_child(root, counter, parent_id, x, y, w, h, style=ICON_CHILD_STYLE):
    """A glyph cell parented to a box. Its geometry is relative to the
    parent's origin, which is how draw.io keeps the two together when the
    box is moved in Desktop."""
    cid = str(counter[0])
    counter[0] += 1
    c = ET.SubElement(
        root,
        "mxCell",
        id=cid,
        value="",
        style=style,
        vertex="1",
        parent=parent_id,
    )
    ET.SubElement(
        c,
        "mxGeometry",
        x=str(x),
        y=str(y),
        width=str(w),
        height=str(h),
        **{"as": "geometry"},
    )
    return cid


def _icon_node(root, counter, x, y, size, value, style=ICON_NODE_STYLE):
    """A standalone glyph whose caption renders below the shape."""
    cid = str(counter[0])
    counter[0] += 1
    c = ET.SubElement(
        root, "mxCell", id=cid, value=value, style=style, vertex="1", parent="1"
    )
    ET.SubElement(
        c,
        "mxGeometry",
        x=str(x),
        y=str(y),
        width=str(size),
        height=str(size),
        **{"as": "geometry"},
    )
    return cid


def build_icon_box_clean(path):
    """A labelled box with a glyph inside it, and an unrelated edge that
    runs where the glyph's geometry would land if it were read as absolute
    rather than relative to its parent."""
    mxfile, root, counter = _new_doc()
    parent = _box(root, counter, 400, 300, 200, 60, "Order Handler")
    _icon_child(root, counter, parent, 10, 16, 28, 28)
    src = _box(root, counter, 300, 15, 60, 30, "S")
    dst = _box(root, counter, 300, 400, 60, 30, "T")
    _edge(
        root,
        counter,
        src,
        dst,
        waypoints=[(24, 30), (24, 415)],
        exitX=0,
        exitY=0.5,
        entryX=0,
        entryY=0.5,
    )
    _write(mxfile, path)
    return path


def build_icon_child_duplicate_crossing(path):
    """An edge that genuinely cuts through a box carrying a glyph.

    The CROSSING is real and must be reported — once, for the box. The glyph
    sits inside that same box, so reporting it separately is a duplicate
    finding for a single routing problem.
    """
    mxfile, root, counter = _new_doc()
    src = _box(root, counter, 40, 315, 60, 30, "S")
    dst = _box(root, counter, 700, 315, 60, 30, "T")
    blocker = _box(root, counter, 400, 300, 200, 60, "Order Handler")
    _icon_child(root, counter, blocker, 10, 16, 28, 28)
    _edge(
        root,
        counter,
        src,
        dst,
        exitX=1,
        exitY=0.5,
        entryX=0,
        entryY=0.5,
    )
    _write(mxfile, path)
    return path


def build_icon_node_caption_crossing(path):
    """An edge that misses the glyph but runs straight through its caption.

    The caption renders below the 48px shape and is wider than it, so this
    is invisible to a check that only knows the shape's bounding box.
    """
    mxfile, root, counter = _new_doc()
    _icon_node(root, counter, 400, 300, 48, "Order Handler")
    src = _box(root, counter, 100, 345, 60, 30, "S")
    dst = _box(root, counter, 700, 345, 60, 30, "T")
    _edge(root, counter, src, dst, exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _write(mxfile, path)
    return path


def build_icon_node_clean(path):
    """The same glyph, with the edge routed clear of its caption."""
    mxfile, root, counter = _new_doc()
    _icon_node(root, counter, 400, 300, 48, "Order Handler")
    src = _box(root, counter, 100, 485, 60, 30, "S")
    dst = _box(root, counter, 700, 485, 60, 30, "T")
    _edge(root, counter, src, dst, exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _write(mxfile, path)
    return path


def build_swimlane_child_box(path):
    """A real box nested inside a container is still a genuine obstacle.

    Guards the conjunction in is_decoration: exempting every child of a
    vertex, rather than only icon children, would lose this CROSSING.
    """
    mxfile, root, counter = _new_doc()
    zone = _box(root, counter, 350, 250, 300, 160, "Zone", is_container=True)
    inner = str(counter[0])
    counter[0] += 1
    c = ET.SubElement(
        root,
        "mxCell",
        id=inner,
        value="Nested",
        style=(
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#cccccc;"
            "strokeColor=#666666;strokeWidth=1;fontSize=12;"
        ),
        vertex="1",
        parent=zone,
    )
    ET.SubElement(
        c,
        "mxGeometry",
        x="50",
        y="50",
        width="200",
        height="60",
        **{"as": "geometry"},
    )
    src = _box(root, counter, 100, 315, 60, 30, "S")
    dst = _box(root, counter, 700, 315, 60, 30, "T")
    _edge(root, counter, src, dst, exitX=1, exitY=0.5, entryX=0, entryY=0.5)
    _write(mxfile, path)
    return path


def _icon_only_doc(path, style, value="Widget"):
    mxfile, root, counter = _new_doc()
    _icon_node(root, counter, 400, 300, 48, value, style=style)
    _write(mxfile, path)
    return path


def build_unknown_icon(path):
    """A stencil name with a typo. draw.io renders this as an empty shape
    with no error of any kind, so nothing else in the loop catches it."""
    return _icon_only_doc(
        path,
        "sketch=0;html=1;aspect=fixed;verticalLabelPosition=bottom;"
        "verticalAlign=top;align=center;shape=mxgraph.aws4.resourceIcon;"
        "resIcon=mxgraph.aws4.lamda;",
    )


def build_remote_image_icon(path):
    """An icon pulled from the web. Renders today, blank on any machine
    that cannot reach the host."""
    return _icon_only_doc(
        path,
        "shape=image;html=1;aspect=fixed;verticalLabelPosition=bottom;"
        "verticalAlign=top;align=center;"
        "image=https://example.com/logo.svg;",
    )


def build_data_uri_icon(path):
    """An embedded SVG. Self-contained, so there is nothing to verify."""
    return _icon_only_doc(
        path,
        "shape=image;html=1;aspect=fixed;verticalLabelPosition=bottom;"
        "verticalAlign=top;align=center;"
        "image=data:image/svg+xml,PHN2Zy8+;",
    )


def build_known_icon(path):
    """A correctly named icon must not warn."""
    return _icon_only_doc(
        path,
        "sketch=0;html=1;aspect=fixed;verticalLabelPosition=bottom;"
        "verticalAlign=top;align=center;shape=mxgraph.aws4.resourceIcon;"
        "resIcon=mxgraph.aws4.lambda;",
    )
