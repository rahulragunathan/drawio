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
from xml.dom import minidom


# --------------------------------------------------------------------------
# Source-based colour palette. Each arrow takes its source box's colour.
# Categories below are illustrative — substitute your own semantic groups.
#
# Goal: clear contrast and legibility — not a particular palette. draw.io
# Desktop is usually viewed/exported in dark mode, where pale fills and
# near-black text wash out, so emit colours via light-dark(light, dark) (see
# ld() and the *_DARK constants) WHERE a colour wouldn't read in both themes.
# The dark value is a higher-contrast variant — usually a brighter/lighter
# tint of the same hue (bright accents work too, if you prefer them). Colours
# that already contrast in both themes (green, orange) stay single-colour.
# --------------------------------------------------------------------------
COLOR_PRIMARY_BLUE   = "#0078d4"  # Primary cloud / SaaS infrastructure
COLOR_FUTURE_GREY    = "#9e9e9e"  # Future-state / out-of-scope (use dashed)
COLOR_CONFIG_GOLD    = "#bf8f00"  # Configuration / repository source
COLOR_ORCH_PURPLE    = "#5b3fbf"  # Orchestrator / pipeline (stroke colour;
                                  # the lighter fill #8e7cc3 is too pale
                                  # to read clearly as a line colour)
COLOR_FRONTEND_GREEN = "#34a853"  # User-facing / frontend
COLOR_DATASTORE_NAVY = "#003c71"  # Datastore / index
COLOR_GATEWAY_ORANGE = "#d04a02"  # Gateway / service mesh
COLOR_CONSUMER_PURPLE = "#9c27b0"  # External consumer / subscriber

# Dark-mode contrast variants (pass as fill_dark / stroke_dark / color_dark).
# Lighter/brighter tints of the same hue — calm but legible on dark.
COLOR_PRIMARY_BLUE_DARK    = "#4da3ff"  # lighter blue
COLOR_CONFIG_GOLD_DARK     = "#ffd966"  # lighter gold
COLOR_ORCH_PURPLE_DARK     = "#b59dff"  # lighter purple
COLOR_WORKER_PURPLE        = "#8e7cc3"  # pale worker fill ...
COLOR_WORKER_PURPLE_DARK   = "#cbbcff"  # ... lighter lavender (use dark text)
COLOR_DATASTORE_NAVY_DARK  = "#7fb3e6"  # light steel-blue
COLOR_CONSUMER_PURPLE_DARK = "#d18cff"  # lighter violet
# Green (#34a853) and orange (#d04a02) read in both themes; leave them
# single-colour unless a specific diagram needs otherwise.


# --------------------------------------------------------------------------
# Canvas dimensions. Adjust to fit your content.
# --------------------------------------------------------------------------
W, H = 1560, 870


# --------------------------------------------------------------------------
# XML scaffolding.
# --------------------------------------------------------------------------
mxfile = ET.Element("mxfile", host="app.diagrams.net",
                    type="device", version="24.0.0")
diagram = ET.SubElement(mxfile, "diagram",
                        name="My Diagram", id="my-diagram")
graph = ET.SubElement(diagram, "mxGraphModel",
                      dx="1422", dy="757", grid="0", gridSize="10",
                      guides="1", tooltips="1", connect="1", arrows="1",
                      fold="1", page="1", pageScale="1",
                      pageWidth=str(W), pageHeight=str(H),
                      math="0", shadow="0")
root = ET.SubElement(graph, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")
_next = [2]


def cell_id():
    cid = str(_next[0]); _next[0] += 1
    return cid


# --------------------------------------------------------------------------
# Primitives.
# --------------------------------------------------------------------------
def ld(light, dark=None):
    """Theme colour via draw.io's light-dark() function.

    ld('#0078D4')            -> '#0078D4'                     (single colour)
    ld('#0078D4', '#FF66B3') -> 'light-dark(#0078D4,#FF66B3)' (light / dark)

    draw.io renders the first value in light mode, the second in dark. Pass a
    dark value wherever a fill, stroke, or label would wash out on the dark
    canvas. NOTE: light-dark() is a runtime function — preview.py shows only
    the light value, so judge dark contrast in draw.io Desktop.
    """
    return f"light-dark({light},{dark})" if dark else light


def container(x, y, w, h, title, stroke, fill="#ffffff",
              fontColor=None, fontSize=14,
              fill_dark=None, stroke_dark=None, fontColor_dark=None):
    """Dashed-edge zone group. Emit BEFORE the boxes that sit inside it.
    Pass *_dark values for dark-mode-safe fills/strokes/title text."""
    cid = cell_id()
    fillC = ld(fill, fill_dark)
    strokeC = ld(stroke, stroke_dark)
    fontC = ld(fontColor or stroke, fontColor_dark or stroke_dark)
    style = (f"rounded=0;whiteSpace=wrap;html=1;"
             f"fillColor={fillC};strokeColor={strokeC};strokeWidth=2;"
             f"dashed=1;verticalAlign=top;align=left;"
             f"fontColor={fontC};fontSize={fontSize};"
             f"fontStyle=1;spacingTop=8;spacingLeft=12;")
    c = ET.SubElement(root, "mxCell", id=cid, value=title, style=style,
                      vertex="1", parent="1")
    ET.SubElement(c, "mxGeometry", x=str(x), y=str(y),
                  width=str(w), height=str(h), **{"as": "geometry"})
    return cid


def box(x, y, w, h, text, fill, stroke=None, fontColor="#ffffff",
        fontSize=12, bold=True, valign="middle", halign="center",
        spacingTop=0, spacingLeft=0, dashed=False,
        fill_dark=None, stroke_dark=None, fontColor_dark=None):
    """Solid rectangle. Supports HTML in `text` (with &lt;b&gt; etc.).

    Pass dashed=True for a future-state / out-of-scope shape (grey fill +
    grey stroke + dashed border) — matches the 'grey/dashed shape = future'
    convention and the legend. verticalAlign stays 'middle' so the validator
    won't mistake a dashed box for a container.

    Pass fill_dark / stroke_dark / fontColor_dark for dark-mode accents; they
    route through ld() into light-dark(). A box keeps its single colour if no
    dark value is given."""
    cid = cell_id()
    fillC = ld(fill, fill_dark)
    strokeC = ld(stroke or fill, stroke_dark or fill_dark)
    fontC = ld(fontColor, fontColor_dark)
    style = (f"rounded=1;whiteSpace=wrap;html=1;"
             f"fillColor={fillC};strokeColor={strokeC};strokeWidth=1;"
             f"{'dashed=1;' if dashed else ''}"
             f"fontColor={fontC};fontSize={fontSize};"
             f"fontStyle={1 if bold else 0};arcSize=10;"
             f"verticalAlign={valign};align={halign};"
             f"spacingTop={spacingTop};spacingLeft={spacingLeft};")
    c = ET.SubElement(root, "mxCell", id=cid,
                      value=text.replace("\n", "<br>"),
                      style=style, vertex="1", parent="1")
    ET.SubElement(c, "mxGeometry", x=str(x), y=str(y),
                  width=str(w), height=str(h), **{"as": "geometry"})
    return cid


def edge(src, dst, color=COLOR_ORCH_PURPLE, width=2, style="solid",
         label=None, waypoints=None,
         exitX=None, exitY=None, entryX=None, entryY=None,
         label_x=None, label_y=None,
         color_dark=None, jump=False, bidirectional=False,
         end_arrow=True, label_color_dark=None):
    """Orthogonal edge with optional waypoints and label offset.

    color_dark        — dark-mode stroke accent (light-dark via ld()).
    jump=True         — add jumpStyle=gap so this edge hops crossed lines
                        instead of being rerouted (cheap crossing fix).
    bidirectional=True— arrowheads on both ends (request/response, R/W).
    end_arrow=False   — no end arrowhead (connector / bus / merge line).
    The label is auto-wrapped in a light-dark <font> when a dark colour is
    available (label_color_dark, else color_dark), so it reads on dark and
    binds to its arrow. Prefer verb-first labels ('Call OCR', 'Reads index')
    and stacked <div> words in tight channels."""
    cid = cell_id()
    dash = ""
    if style == "dashed":   dash = "dashed=1;"
    elif style == "dotted": dash = "dashed=1;dashPattern=1 4;"
    exit_str = (f"exitX={exitX};exitY={exitY};exitDx=0;exitDy=0;"
                if exitX is not None else "")
    entry_str = (f"entryX={entryX};entryY={entryY};entryDx=0;entryDy=0;"
                 if entryX is not None else "")
    strokeC = ld(color, color_dark)
    end_str = "endArrow=classic;endFill=1;" if end_arrow else "endArrow=none;"
    start_str = "startArrow=classic;startFill=1;" if bidirectional else ""
    style_str = (
        f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=0;"
        f"jettySize=auto;html=1;{exit_str}{entry_str}"
        f"strokeColor={strokeC};strokeWidth={width};"
        f"{dash}{'jumpStyle=gap;' if jump else ''}{start_str}{end_str}"
        f"startSize=2;endSize=2;fontSize=10;"
        f"fontColor={strokeC};labelBackgroundColor=#ffffff;")
    value = label or ""
    dark_label = label_color_dark or color_dark
    if label and dark_label:
        value = f'<font color="light-dark(#000000,{dark_label})">{label}</font>'
    c = ET.SubElement(root, "mxCell", id=cid, value=value,
                      style=style_str, edge="1", parent="1",
                      source=src, target=dst)
    geom = ET.SubElement(c, "mxGeometry", relative="1",
                         **{"as": "geometry"})
    if waypoints:
        arr = ET.SubElement(geom, "Array", **{"as": "points"})
        for (x, y) in waypoints:
            ET.SubElement(arr, "mxPoint", x=str(x), y=str(y))
    if label and (label_x is not None or label_y is not None):
        ET.SubElement(geom, "mxPoint",
                      x=str(label_x or 0), y=str(label_y or 0),
                      **{"as": "offset"})
    return cid


def sub(text, size=11):
    """Italicised Title Case subheading, non-bold. Explicit font-size keeps
    XML stable across drawio Desktop re-saves."""
    return (f"<span style='font-style:italic;font-weight:normal;"
            f"font-size:{size}px'>{text}</span>")


def desc(text, size=11):
    """Sentence-case description body, non-bold. Explicit font-size."""
    return (f"<span style='font-weight:normal;font-size:{size}px'>"
            f"{text}</span>")


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

box(40, 20, W - 80, 50, "Replace this with your diagram title",
    fill="#1f3864", fontSize=18)

# Example container
container(40, 100, 320, 720, "Source Systems",
          stroke="#3a6ea5", fill="#eaf3fb", fontColor="#1f3864")

# Example box inside the container
src = box(70, 160, 260, 70,
          "<b>Example Source</b><br>" + sub("Subheading"),
          fill=COLOR_PRIMARY_BLUE, bold=False)

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
