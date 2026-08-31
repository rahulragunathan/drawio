"""Minimal starter for a drawio diagram generator.

Copy this file, rename it (e.g. `build_my_diagram.py`), and populate the
section between the helper definitions and the XML write at the bottom.

Conventions encoded here (read SKILL.md for the full rationale):
- Arrow colour matches the SOURCE box's fill (or its stroke if fill is too light).
- Future state = grey/dashed shape + grey/dashed arrow with NO "Future" label
  (legend covers it).
- Edge labels carry `labelBackgroundColor=#ffffff` so they read over crossings.
- Edges are emitted AFTER boxes so labels render on top.
- Subheadings via sub() — italicised Title Case with explicit font-size.
- Descriptions via desc() — sentence case with explicit font-size, non-bold.
- Multi-line edge labels use <div> tags, NOT \\n (drawio Desktop round-trip).

After running this generator, run:
    python scripts/validate.py <output.drawio>
to check for CROSSING / OVERLAP / TEXT_OVERLAP / LABEL_OVERLAP /
LABEL_BOX_OVERLAP / SHORT_LABELLED_EDGE / DIAGONAL / DANGLING violations.
Then render the PNG and LOOK at it — a clean validate says nothing about
whether labels have room or whether either theme is legible:
    python scripts/render_png.py <output.drawio>   # foo.drawio -> foo.png

Reserve routing corridors before writing any edges, and record the
allocation here (e.g. "y=225 lane — pipeline fan-in; x=850 channel — app
-> data"). Later layout edits then become mechanical.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom


# --------------------------------------------------------------------------
# Source-based colour palette. Each arrow takes its source box's colour.
# Categories below are illustrative — substitute your own semantic groups.
#
# Goal: clear contrast and legibility — not a particular palette. Pick colours
# that separate categories and let a reader follow flow at a glance.
#
# Emit one colour per thing and let draw.io handle its own dark theme: its
# export inverts colours automatically, and doing so by hand produced a WORSE
# dark render than leaving it alone (an explicit colour opts a label out of
# that inversion, pinning dark text onto a dark canvas).
#
# COLOR_ORCH_PURPLE is a stroke colour rather than a fill: the matching pale
# fill #8e7cc3 is too light to read as a line.
# --------------------------------------------------------------------------
COLOR_PRIMARY_BLUE = "#0078d4"  # Primary cloud / SaaS infrastructure
COLOR_FUTURE_GREY = "#9e9e9e"  # Future-state / out-of-scope (use dashed)
COLOR_CONFIG_GOLD = "#bf8f00"  # Configuration / repository source
COLOR_ORCH_PURPLE = "#5b3fbf"  # Orchestrator / pipeline (stroke, not fill)
COLOR_FRONTEND_GREEN = "#34a853"  # User-facing / frontend
COLOR_DATASTORE_NAVY = "#003c71"  # Datastore / index
COLOR_GATEWAY_ORANGE = "#d04a02"  # Gateway / service mesh
COLOR_CONSUMER_PURPLE = "#9c27b0"  # External consumer / subscriber

# --------------------------------------------------------------------------
# Canvas dimensions. Adjust to fit your content.
# --------------------------------------------------------------------------
W, H = 1560, 870


# --------------------------------------------------------------------------
# XML scaffolding.
# --------------------------------------------------------------------------
mxfile = ET.Element("mxfile", host="app.diagrams.net", type="device", version="24.0.0")
diagram = ET.SubElement(mxfile, "diagram", name="My Diagram", id="my-diagram")
graph = ET.SubElement(
    diagram,
    "mxGraphModel",
    dx="1422",
    dy="757",
    grid="0",
    gridSize="10",
    guides="1",
    tooltips="1",
    connect="1",
    arrows="1",
    fold="1",
    page="1",
    pageScale="1",
    pageWidth=str(W),
    pageHeight=str(H),
    math="0",
    shadow="0",
)
root = ET.SubElement(graph, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")
_next = [2]


def cell_id():
    cid = str(_next[0])
    _next[0] += 1
    return cid


# --------------------------------------------------------------------------
# Primitives.
# --------------------------------------------------------------------------
def container(x, y, w, h, title, stroke, fill="#ffffff", fontColor=None, fontSize=14):
    """Dashed-edge zone group. Emit BEFORE the boxes that sit inside it."""
    cid = cell_id()
    fillC = fill
    strokeC = stroke
    fontC = fontColor or stroke
    style = (
        f"rounded=0;whiteSpace=wrap;html=1;"
        f"fillColor={fillC};strokeColor={strokeC};strokeWidth=2;"
        f"dashed=1;verticalAlign=top;align=left;"
        f"fontColor={fontC};fontSize={fontSize};"
        f"fontStyle=1;spacingTop=8;spacingLeft=12;"
    )
    c = ET.SubElement(
        root, "mxCell", id=cid, value=title, style=style, vertex="1", parent="1"
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


def box(
    x,
    y,
    w,
    h,
    text,
    fill,
    stroke=None,
    fontColor="#ffffff",
    fontSize=12,
    bold=True,
    valign="middle",
    halign="center",
    spacingTop=0,
    spacingLeft=0,
    dashed=False,
):
    """Solid rectangle. Supports HTML in `text` (with &lt;b&gt; etc.).

    Pass dashed=True for a future-state / out-of-scope shape (grey fill +
    grey stroke + dashed border) — matches the 'grey/dashed shape = future'
    convention and the legend. verticalAlign stays 'middle' so the validator
    won't mistake a dashed box for a container.

    """
    cid = cell_id()
    fillC = fill
    strokeC = stroke or fill
    fontC = fontColor
    style = (
        f"rounded=1;whiteSpace=wrap;html=1;"
        f"fillColor={fillC};strokeColor={strokeC};strokeWidth=1;"
        f"{'dashed=1;' if dashed else ''}"
        f"fontColor={fontC};fontSize={fontSize};"
        f"fontStyle={1 if bold else 0};arcSize=10;"
        f"verticalAlign={valign};align={halign};"
        f"spacingTop={spacingTop};spacingLeft={spacingLeft};"
    )
    c = ET.SubElement(
        root,
        "mxCell",
        id=cid,
        value=text.replace("\n", "<br>"),
        style=style,
        vertex="1",
        parent="1",
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


def edge(
    src,
    dst,
    color=COLOR_ORCH_PURPLE,
    width=2,
    style="solid",
    label=None,
    waypoints=None,
    exitX=None,
    exitY=None,
    entryX=None,
    entryY=None,
    label_x=None,
    label_y=None,
    jump=False,
    bidirectional=False,
    end_arrow=True,
    label_bg="#ffffff",
):
    """Orthogonal edge with optional waypoints and label offset.

    jump=True         — add jumpStyle=gap so this edge hops crossed lines
                        instead of being rerouted (cheap crossing fix).
    bidirectional=True— arrowheads on both ends (request/response, R/W).
    end_arrow=False   — no end arrowhead (connector / bus / merge line).
    label_bg          — the plate drawn behind the label. It masks the line
                        running underneath, so do not remove it; recolour it
                        to match the zone the label sits over, or a white
                        plate reads as a sticker on a tinted background.
    Prefer verb-first labels ('Call OCR', 'Reads index') and stacked <div>
    words in tight channels.

    The label carries no explicit font colour. draw.io inverts colours for its
    own dark theme, and an explicit <font color> opts the label OUT of that,
    which is how it ends up as dark text on a dark canvas."""
    if (exitX is None) != (exitY is None):
        raise ValueError(
            "exitX and exitY must be given together — half a pair emits "
            "'exitY=None' into the style, which is not a coordinate"
        )
    if (entryX is None) != (entryY is None):
        raise ValueError(
            "entryX and entryY must be given together — half a pair emits "
            "'entryY=None' into the style, which is not a coordinate"
        )
    cid = cell_id()
    dash = ""
    if style == "dashed":
        dash = "dashed=1;"
    elif style == "dotted":
        dash = "dashed=1;dashPattern=1 4;"
    exit_str = (
        f"exitX={exitX};exitY={exitY};exitDx=0;exitDy=0;" if exitX is not None else ""
    )
    entry_str = (
        f"entryX={entryX};entryY={entryY};entryDx=0;entryDy=0;"
        if entryX is not None
        else ""
    )
    strokeC = color
    end_str = "endArrow=classic;endFill=1;" if end_arrow else "endArrow=none;"
    start_str = "startArrow=classic;startFill=1;" if bidirectional else ""
    style_str = (
        f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=0;"
        f"jettySize=auto;html=1;{exit_str}{entry_str}"
        f"strokeColor={strokeC};strokeWidth={width};"
        f"{dash}{'jumpStyle=gap;' if jump else ''}{start_str}{end_str}"
        f"startSize=2;endSize=2;fontSize=12;"
        f"fontColor={strokeC};labelBackgroundColor={label_bg};"
    )
    value = label or ""
    c = ET.SubElement(
        root,
        "mxCell",
        id=cid,
        value=value,
        style=style_str,
        edge="1",
        parent="1",
        source=src,
        target=dst,
    )
    geom = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
    if waypoints:
        arr = ET.SubElement(geom, "Array", **{"as": "points"})
        for x, y in waypoints:
            ET.SubElement(arr, "mxPoint", x=str(x), y=str(y))
    if label and (label_x is not None or label_y is not None):
        ET.SubElement(
            geom,
            "mxPoint",
            x=str(label_x or 0),
            y=str(label_y or 0),
            **{"as": "offset"},
        )
    return cid


# --------------------------------------------------------------------------
# Vendor icons.
#
# Names and fill colours come from references/icons.md in the skill; pass a
# key as "<family>:<name>", e.g. "aws:lambda". `list_icons.py --search redis`
# finds one. Any of draw.io's ~11,500 names works, not just the curated list.
#
# Two placements:
#   icon_box()  — glyph inside a labelled card. The card keeps the exact
#                 geometry, anchors and routing behaviour of a plain box().
#   icon_node() — bare glyph with its name underneath, the vendor-docs look.
#
# For a logo draw.io has no stencil for (Snowflake, a client's mark), pass
# svg_icon("path/to/logo.svg") in place of the key.
# --------------------------------------------------------------------------
ICON_NODE_SIZE = 48  # icon_node() glyph edge, px
ICON_BOX_SIZE = 28  # icon_box() child glyph edge, px
ICON_BOX_INSET = 10  # px from the card's left edge to the glyph
ICON_TEXT_GAP = 8  # px between glyph and the card's text

# kind, name prefix, wrapper shape, wrapper's glyph key, key takes a bare name
ICON_FAMILIES = {
    "aws": ("stencil", "mxgraph.aws4.", "mxgraph.aws4.resourceIcon", "resIcon", False),
    "gcp": ("stencil", "mxgraph.gcp3.", None, None, False),
    "k8s": (
        "stencil",
        "mxgraph.kubernetes.",
        "mxgraph.kubernetes.icon2",
        "prIcon",
        True,
    ),
    "azure": ("image", "img/lib/azure2/", None, None, False),
    "cisco": ("stencil", "mxgraph.cisco19.", None, None, False),
    "net": ("stencil", "mxgraph.networks.", None, None, False),
}


class Svg(str):
    """An embedded SVG data URI, as returned by svg_icon()."""


class Raw:
    """A stencil or image name used verbatim, as returned by raw_icon()."""

    def __init__(self, shape=None, image=None):
        self.shape, self.image = shape, image


def raw_icon(shape=None, image=None):
    """Use a draw.io name directly, bypassing the curated catalog.

    references/icons.md lists ~130 icons, but draw.io ships ~11,500. This
    reaches the rest — an IBM, SAP or Veeam stencil, or any bundled image
    path — without inventing a family entry for a one-off.

        raw_icon(shape="mxgraph.veeam.vbr")
        raw_icon(image="img/lib/ibm/analytics/analytics.svg")

    UNKNOWN_ICON still verifies the name, so a typo here is caught.
    """
    if (shape is None) == (image is None):
        raise ValueError("raw_icon() takes exactly one of shape= or image=")
    return Raw(shape=shape, image=image)


def svg_icon(path):
    """Embed a local SVG so the diagram carries its own artwork.

    draw.io wants "data:image/svg+xml,<base64>" — a comma, then raw base64.
    NOT ";base64,": a style string is ";"-delimited, so that spelling ends
    the token early and the icon renders blank. Verified by rendering both.
    """
    import base64

    data = (
        Path(path).read_bytes() if isinstance(path, Path) else open(path, "rb").read()
    )
    return Svg("data:image/svg+xml," + base64.b64encode(data).decode())


def icon_style(icon, placement="node", fill=None, font_color="#232F3E", font_size=11):
    """Build the style for one glyph.

    Knows the stencil-vs-image split so the emitters do not have to. Image
    families (Azure, and any embedded SVG) ship as fixed-colour SVG files, so
    `fill` does not apply to them.
    """
    common = "sketch=0;outlineConnect=0;dashed=0;html=1;aspect=fixed;"
    if placement == "node":
        label = (
            f"labelPosition=center;verticalLabelPosition=bottom;"
            f"align=center;verticalAlign=top;fontSize={font_size};"
            f"fontStyle=0;fontColor={font_color};"
        )
    else:
        # Inside a card: the card owns the text, so this cell must never
        # acquire a caption, and must not be draggable out of its parent.
        label = (
            "labelPosition=center;verticalLabelPosition=middle;"
            "verticalAlign=middle;align=center;pointerEvents=0;"
            "movable=0;resizable=0;rotatable=0;editable=0;connectable=0;"
            "drawioSkillRole=icon;"
        )

    if isinstance(icon, Raw):
        if icon.image:
            return (
                f"shape=image;imageAspect=0;points=[];{common}{label}"
                f"image={icon.image};"
            )
        paint = f"fillColor={fill};" if fill else ""
        return f"{common}{label}{paint}shape={icon.shape};"

    if isinstance(icon, Svg) or str(icon).startswith("data:"):
        return f"shape=image;imageAspect=0;points=[];{common}{label}image={icon};"

    family, _, name = str(icon).partition(":")
    kind, prefix, wrapper, glyph_key, bare = ICON_FAMILIES[family]
    if kind == "image":
        return (
            f"shape=image;imageAspect=0;points=[];{common}{label}image={prefix}{name};"
        )

    qualified = name if "." in name else prefix + name
    paint = f"fillColor={fill};" if fill else ""
    if wrapper:
        # A tile wrapper draws a white glyph on a coloured plate, so it reads
        # on either canvas; strokeColor is the glyph itself.
        return (
            f"{common}{label}strokeColor=#ffffff;{paint}"
            f"shape={wrapper};{glyph_key}={name if bare else qualified};"
        )
    return f"{common}{label}{paint}shape={qualified};"


def icon_node(x, y, label, icon, size=ICON_NODE_SIZE, **kw):
    """Bare vendor glyph with its name rendered underneath.

    Never pass a dashed style here: dashed + verticalAlign=top is exactly the
    validator's container signature, and the glyph would be read as a zone.
    Grey the fill for a future-state icon instead.
    """
    cid = cell_id()
    c = ET.SubElement(
        root,
        "mxCell",
        id=cid,
        value=label,
        style=icon_style(icon, "node", **kw),
        vertex="1",
        parent="1",
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


def icon_box(
    x,
    y,
    w,
    h,
    text,
    fill,
    icon,
    icon_size=ICON_BOX_SIZE,
    icon_inset=ICON_BOX_INSET,
    icon_fill=None,
    **kw,
):
    """Labelled card with a vendor glyph inside it, text to the right.

    The card is an ordinary box() — same geometry, anchors and routing — so
    icons cost nothing in layout terms. The glyph is a child cell, because a
    stencil is a registered shape and cannot be fed to image=; being a child
    is also what keeps it attached when the card is moved in Desktop.

    Text is left-aligned: centring it would run under the glyph.
    """
    kw.setdefault("halign", "left")
    kw.setdefault("spacingLeft", icon_inset + icon_size + ICON_TEXT_GAP)
    parent = box(x, y, w, h, text, fill, **kw)
    child = cell_id()
    c = ET.SubElement(
        root,
        "mxCell",
        id=child,
        value="",
        style=icon_style(icon, "box", fill=icon_fill),
        vertex="1",
        parent=parent,
    )
    ET.SubElement(
        c,
        "mxGeometry",
        x=str(icon_inset),
        y=str((h - icon_size) / 2),
        width=str(icon_size),
        height=str(icon_size),
        **{"as": "geometry"},
    )
    return parent


def sub(text, size=11):
    """Italicised Title Case subheading, non-bold. Explicit font-size keeps
    XML stable across drawio Desktop re-saves."""
    return (
        f"<span style='font-style:italic;font-weight:normal;"
        f"font-size:{size}px'>{text}</span>"
    )


def desc(text, size=11):
    """Sentence-case description body, non-bold. Explicit font-size."""
    return f"<span style='font-weight:normal;font-size:{size}px'>{text}</span>"


# --------------------------------------------------------------------------
# === YOUR DIAGRAM GOES HERE ===
#
# Pattern:
#   1. Title bar (a `box` near y=20).
#   2. Containers (dashed zones) — emit FIRST so boxes layer on top.
#   3. Boxes inside each zone.
#   4. Edges (with source-coloured arrows, waypoints, label offsets).
#   5. Legend strip (a `box` near the bottom).
#
# Look at examples/build_three_tier_web.py for a fully-worked reference
# that exercises every locked convention and validates clean.
# --------------------------------------------------------------------------

box(
    40,
    20,
    W - 80,
    50,
    "Replace this with your diagram title",
    fill="#1f3864",
    fontSize=18,
)

# Example container
container(
    40,
    100,
    320,
    720,
    "Source Systems",
    stroke="#3a6ea5",
    fill="#eaf3fb",
    fontColor="#1f3864",
)

# Example box inside the container
src = box(
    70,
    160,
    260,
    70,
    "<b>Example Source</b><br>" + sub("Subheading"),
    fill=COLOR_PRIMARY_BLUE,
    bold=False,
)

# Add more boxes, then edges, then a legend...


# --------------------------------------------------------------------------
# Write out.
# --------------------------------------------------------------------------
xml_bytes = ET.tostring(mxfile, encoding="utf-8")
pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ")
out_path = "./my-diagram.drawio"
with open(out_path, "w") as f:
    f.write(pretty)
print(f"Wrote {out_path}")
print(f"Cells: {_next[0] - 2}")
