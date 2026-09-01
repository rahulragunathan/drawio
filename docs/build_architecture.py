"""Generate docs/architecture.drawio — the module map in docs/ARCHITECTURE.md.

The skill draws its own architecture diagram. Regenerate whenever the module
structure changes, then validate and render:

    python docs/build_architecture.py
    python scripts/validate.py docs/architecture.drawio
    python scripts/render_png.py docs/architecture.drawio

The helpers below are vendored from assets/build_template.py, unchanged, per
the skill's own convention. Only the five this diagram uses are copied.

Reserved corridors
------------------
    x=395  channel — authoring -> validate.py (right of the authoring zone)
    x=410  channel — icons.md -> the generator (15 px clear of x=395)
    x=885  channel — render_examples.py -> validate.py (inside the check zone)
    x=915  channel — icon_names.txt.gz -> validate.py (between the top zones,
           entering 20 px below the 'Validates' edge so the two do not merge)
    y=505  lane    — render_examples.py -> renders/ (below the top zones)
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom


# --------------------------------------------------------------------------
# One colour per layer. Arrows take their source box's colour.
# --------------------------------------------------------------------------
COLOR_AUTHOR = "#0078d4"  # Authoring: template and generator scripts
COLOR_CHECK = "#5b3fbf"  # Checking and rendering tools
COLOR_DIST = "#d04a02"  # Packaging and review artifacts
COLOR_CATALOG = "#003c71"  # Icon catalog and its generated name list

# The vendored edge() defaults to COLOR_ORCH_PURPLE. Kept as an alias so the
# helper stays byte-identical to the template rather than being edited here.
COLOR_ORCH_PURPLE = COLOR_CHECK

W, H = 1520, 810

mxfile = ET.Element("mxfile", host="app.diagrams.net", type="device", version="24.0.0")
diagram = ET.SubElement(
    mxfile, "diagram", name="drawio Skill Architecture", id="drawio-architecture"
)
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
# Primitives, vendored from assets/build_template.py.
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
# Diagram.
# --------------------------------------------------------------------------
box(
    40,
    20,
    W - 80,
    46,
    "drawio Skill — Module Architecture",
    fill="#1f3864",
    fontSize=18,
)

# --- Zones ---------------------------------------------------------------
container(40, 100, 340, 380, "Authoring", stroke=COLOR_AUTHOR, fill="#eaf3fb")
container(
    430, 100, 470, 380, "Checking and Rendering", stroke=COLOR_CHECK, fill="#f2effa"
)
container(
    950, 100, 530, 380, "Distribution and Review", stroke=COLOR_DIST, fill="#fdf0e9"
)
container(40, 540, 1440, 230, "Icon Catalog", stroke=COLOR_CATALOG, fill="#eaeff5")

# --- Authoring -----------------------------------------------------------
template = box(
    70,
    150,
    280,
    60,
    "<b>assets/build_template.py</b><br>" + desc("Starter with vendored helpers"),
    fill=COLOR_AUTHOR,
    bold=False,
)
generator = box(
    70,
    250,
    280,
    60,
    "<b>build_&lt;name&gt;.py</b><br>" + desc("Your generator: coordinates and edges"),
    fill=COLOR_AUTHOR,
    bold=False,
)
artifact = box(
    70,
    350,
    280,
    60,
    "<b>&lt;name&gt;.drawio</b><br>" + desc("Plain mxGraph XML"),
    fill=COLOR_AUTHOR,
    bold=False,
)

# --- Checking and rendering ----------------------------------------------
validator = box(
    460,
    150,
    410,
    68,
    "<b>scripts/validate.py</b><br>"
    + desc("Geometry engine. Nine checks, five of them errors"),
    fill=COLOR_CHECK,
    bold=False,
)
preview = box(
    460,
    280,
    190,
    60,
    "<b>scripts/preview.py</b><br>" + desc("matplotlib"),
    fill=COLOR_CHECK,
    bold=False,
)
render_png = box(
    680,
    280,
    190,
    60,
    "<b>scripts/render_png.py</b><br>" + desc("draw.io CLI"),
    fill=COLOR_CHECK,
    bold=False,
)
render_examples = box(
    595,
    390,
    275,
    60,
    "<b>scripts/render_examples.py</b><br>" + desc("Rebuilds every example"),
    fill=COLOR_CHECK,
    bold=False,
)

# --- Distribution and review ---------------------------------------------
renders = box(
    980,
    150,
    210,
    68,
    "<b>renders/</b><br>" + desc("Light and dark PNGs, reviewed for sign-off"),
    fill=COLOR_DIST,
    bold=False,
)
packager = box(
    1240,
    150,
    210,
    68,
    "<b>scripts/package_skill.py</b><br>" + desc("Excludes hidden entries"),
    fill=COLOR_DIST,
    bold=False,
)
archive = box(
    1240,
    290,
    210,
    60,
    "<b>../drawio.skill</b><br>" + desc("The upload"),
    fill=COLOR_DIST,
    bold=False,
)

# --- Icon catalog --------------------------------------------------------
catalog = box(
    450,
    590,
    250,
    52,
    "<b>references/icons.md</b><br>" + desc("~130 curated icons"),
    fill=COLOR_CATALOG,
    bold=False,
)
asar = box(
    90,
    690,
    250,
    56,
    "<b>draw.io Desktop</b><br>" + desc("app.asar, ~11,500 names"),
    fill=COLOR_CATALOG,
    bold=False,
)
lister = box(
    450,
    690,
    250,
    56,
    "<b>scripts/list_icons.py</b><br>" + desc("Search, verify, refresh"),
    fill=COLOR_CATALOG,
    bold=False,
)
names = box(
    810,
    690,
    250,
    56,
    "<b>assets/icon_names.txt.gz</b><br>" + desc("Generated; do not edit"),
    fill=COLOR_CATALOG,
    bold=False,
)

# --- Edges ---------------------------------------------------------------
# Authoring chain, straight down inside its own zone.
edge(template, generator, color=COLOR_AUTHOR, label="Copy")
edge(generator, artifact, color=COLOR_AUTHOR, label="Run")

# x=395 channel — the generated file goes to the validator.
edge(
    artifact,
    validator,
    color=COLOR_AUTHOR,
    label="Validate",
    exitX=1,
    exitY=0.5,
    entryX=0,
    entryY=0.5,
    waypoints=[(395, 380), (395, 184)],
)

# Both renderers import the validator's geometry, so a preview shows exactly
# what the checks see.
edge(
    preview,
    validator,
    color=COLOR_CHECK,
    label="Imports",
    exitX=0.5,
    exitY=0,
    entryX=0.25,
    entryY=1,
)
edge(
    render_png,
    validator,
    color=COLOR_CHECK,
    label="Imports",
    exitX=0.5,
    exitY=0,
    entryX=0.77,
    entryY=1,
)
edge(
    render_examples,
    render_png,
    color=COLOR_CHECK,
    label="Renders",
    exitX=0.65,
    exitY=0,
    entryX=0.5,
    entryY=1,
)
# x=885 channel — up the right-hand side of the check zone.
edge(
    render_examples,
    validator,
    color=COLOR_CHECK,
    label="Validates",
    exitX=1,
    exitY=0.5,
    entryX=1,
    entryY=0.5,
    waypoints=[(885, 420), (885, 184)],
    label_x=25,
)
# y=505 lane — below the top zones, into the review renders from underneath.
edge(
    render_examples,
    renders,
    color=COLOR_CHECK,
    label="Writes PNGs",
    exitX=0.5,
    exitY=1,
    entryX=0.5,
    entryY=1,
    waypoints=[(735, 505), (1085, 505)],
)
edge(packager, archive, color=COLOR_DIST, label="Builds")

# x=410 channel — the catalog is read while authoring. Vertical entry through
# the band's title is what TEXT_OVERLAP exempts.
edge(
    catalog,
    generator,
    color=COLOR_CATALOG,
    label="Pick An Icon",
    exitX=0,
    exitY=0.5,
    entryX=1,
    entryY=0.5,
    waypoints=[(410, 616), (410, 280)],
)
edge(asar, lister, color=COLOR_CATALOG, label="Extracts Names")
edge(lister, names, color=COLOR_CATALOG, label="Writes")
# x=915 channel — between the two right-hand zones, into the validator's side.
edge(
    names,
    validator,
    color=COLOR_CATALOG,
    label="Verifies Names",
    exitX=0.5,
    exitY=0,
    entryX=1,
    entryY=0.8,
    waypoints=[(935, 500), (915, 500), (915, 204)],
    label_x=30,
)


xml_bytes = ET.tostring(mxfile, encoding="utf-8")
pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ")
out_path = "docs/architecture.drawio"
with open(out_path, "w") as f:
    f.write(pretty)
print(f"Wrote {out_path}")
print(f"Cells: {_next[0] - 2}")
