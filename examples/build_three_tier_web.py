"""Three-tier web application architecture (generic reference example).

Demonstrates every locked convention from SKILL.md on a canonical
three-tier web app: external clients on the left, application services
in the middle, data tier on the right.

Conventions exercised:
- Arrow colour matches the SOURCE box (or its stroke if the fill is
  too light to read as a line).
- Future-state shape = grey/dashed; future-state arrows = grey/dashed
  with NO 'Future' label (the legend carries the meaning).
- Solid / dashed / dotted line styles each used at least once.
- Multi-line edge label authored with <div> tags (round-trip stable).
- Reserved corridors: horizontal lanes y=272/284/296 (and y=425 for the
  lower flow) plus a vertical sub-channel at x=888/892/896 in the gap
  between the application and data containers.
- labelBackgroundColor=#ffffff on every labelled edge (set in edge()).
- Edges emitted AFTER boxes so labels render on top.
- Subheadings via sub() — italicised, explicit font-size.
- Description body via desc() — sentence case, non-bold, explicit
  font-size.
- edge() options: a bidirectional Web<->DB Read/Write edge (edge 7 — the
  exception; almost everything else is one-way), and a jump=gap hop where
  the Read lane crosses the Gateway->Web arrow (edge 6).
- Lean legend: only the future-state convention, which a reader can't infer.

Run from the skill root:
    python examples/build_three_tier_web.py
    python scripts/validate.py three-tier-web.drawio
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom


# --- Source-based palette: each arrow takes its source box's colour ---
# The goal is clear contrast in both themes, not a particular palette. draw.io
# One colour per category. draw.io inverts colours for its own dark theme, and
# it does that better than setting a dark variant by hand did.
COLOR_PRIMARY_BLUE = "#0078d4"  # External clients / primary infrastructure
COLOR_FUTURE_GREY = "#9e9e9e"  # Future-state / out-of-scope
COLOR_CONFIG_GOLD = "#bf8f00"  # Configuration / repository
COLOR_ORCH_PURPLE = "#5b3fbf"  # Background worker / orchestrator
COLOR_FRONTEND_GREEN = "#34a853"  # User-facing application service
COLOR_DATASTORE_NAVY = "#003c71"  # Datastore / index
COLOR_GATEWAY_ORANGE = "#d04a02"  # Gateway / auth tier

COLOR_WORKER_PURPLE = "#8e7cc3"  # pale worker fill ...
# Green and orange read in both themes; left single-colour.


W, H = 1320, 680
mxfile = ET.Element("mxfile", host="app.diagrams.net", type="device", version="24.0.0")
diagram = ET.SubElement(
    mxfile, "diagram", name="Three-Tier Web Architecture", id="three-tier-web"
)
graph = ET.SubElement(
    diagram,
    "mxGraphModel",
    dx="1200",
    dy="700",
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


def container(
    x,
    y,
    w,
    h,
    title,
    stroke,
    fill="#ffffff",
    fontColor=None,
    fontSize=14,
):
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
    """Italicised Title Case subheading, non-bold, with explicit
    font-size for drawio round-trip stability."""
    return (
        f"<span style='font-style:italic;font-weight:normal;"
        f"font-size:{size}px'>{text}</span>"
    )


def desc(text, size=11):
    """Sentence-case description body, non-bold, with explicit font-size."""
    return f"<span style='font-weight:normal;font-size:{size}px'>{text}</span>"


# ----- Title bar -----
box(
    40,
    20,
    W - 80,
    46,
    "Three-Tier Web Architecture (Reference Example)",
    fill="#1f3864",
    fontSize=18,
)


# ----- Containers (rendered first so boxes layer on top) -----
# Zones are pale fills with a matching stroke and title colour.
container(
    40,
    92,
    320,
    496,
    "External Clients",
    stroke="#3a6ea5",
    fill="#eaf3fb",
    fontColor="#1f3864",
)
container(
    380,
    92,
    500,
    496,
    "Application Tier",
    stroke="#5b3fbf",
    fill="#f3f0ff",
)
container(
    900,
    92,
    340,
    496,
    "Data Tier",
    stroke="#003c71",
    fill="#e7f0fb",
)


# ----- External clients -----
browser = box(
    70,
    140,
    260,
    80,
    "<b>Browser / Mobile App</b><br>" + sub("User-Facing Clients"),
    fill=COLOR_PRIMARY_BLUE,  # dark text on the lighter blue
    bold=False,
)

# CDN as future state — grey/dashed shape. Following the reference
# diagrams' style, a brief context sentence is fine here: draw.io wraps
# it inside the box. The legend still carries the "grey/dashed = future"
# meaning, so the sentence adds context rather than restating "future".
cdn_future = box(
    70,
    248,
    260,
    96,
    "<b>CDN</b><br>"
    + sub("Edge Caching", size=10)
    + "<br>"
    + desc(
        "Future: geographic edge distribution beyond the initial single-region deploy.",
        size=10,
    ),
    fill="#e0e0e0",
    stroke=COLOR_FUTURE_GREY,
    fontColor="#616161",
    fontSize=11,
    bold=False,
    dashed=True,
)

config = box(
    70,
    360,
    260,
    200,
    "<b>Configuration (Git Repo)</b><br><br>"
    + desc(
        "• Service routing rules<br>"
        "• Feature flags<br>"
        "• Connection strings<br>"
        "• Rate-limit policies<br>"
        "• Secret references"
    ),
    fill="#fff4d6",
    stroke=COLOR_CONFIG_GOLD,
    fontColor="#7f6000",
    fontSize=11,
    valign="top",
    halign="left",
    spacingTop=10,
    spacingLeft=10,
    bold=False,
)


# ----- Application tier (two rows, ~100px routing band between) -----
api_gw = box(
    410,
    140,
    200,
    80,
    "<b>API Gateway</b><br>" + sub("Entry Point"),
    fill=COLOR_GATEWAY_ORANGE,
    fontSize=12,
    bold=False,
)
auth = box(
    650,
    140,
    210,
    80,
    "<b>Auth Service</b><br>" + sub("Token Verification"),
    fill=COLOR_GATEWAY_ORANGE,
    fontSize=12,
    bold=False,
)
web = box(
    410,
    320,
    200,
    80,
    "<b>Web Service</b><br>" + sub("Business Logic"),
    fill=COLOR_FRONTEND_GREEN,
    fontSize=12,
    bold=False,
)
worker = box(
    650,
    320,
    210,
    80,
    "<b>Background Worker</b><br>" + sub("Async Jobs"),
    fill=COLOR_WORKER_PURPLE,
    stroke=COLOR_ORCH_PURPLE,
    fontSize=12,
    bold=False,
)


# ----- Data tier -----
primary_db = box(
    920,
    140,
    290,
    104,
    "<b>Primary Database</b><br>"
    + sub("Source of Truth")
    + "<br>"
    + desc("Transactional reads and writes"),
    fill=COLOR_DATASTORE_NAVY,
    fontSize=12,
    bold=False,
)
cache = box(
    920,
    272,
    290,
    72,
    "<b>Cache</b><br>" + sub("Hot Reads"),
    fill=COLOR_DATASTORE_NAVY,
    fontSize=12,
    bold=False,
)
queue = box(
    920,
    372,
    290,
    72,
    "<b>Message Queue</b><br>" + sub("Async Jobs"),
    fill=COLOR_DATASTORE_NAVY,
    fontSize=12,
    bold=False,
)
# Analytics sink as future state — grey/dashed, brief context sentence.
analytics_future = box(
    920,
    472,
    290,
    84,
    "<b>Analytics Sink</b><br>"
    + sub("Reporting Warehouse", size=10)
    + "<br>"
    + desc("Future: out-of-scope reporting pipeline for v1.", size=10),
    fill="#e0e0e0",
    stroke=COLOR_FUTURE_GREY,
    fontColor="#616161",
    fontSize=11,
    bold=False,
    dashed=True,
)


# ============================================================
# Edges — colours match the SOURCE box.
# Routing band lanes (clear of all boxes): y=272 / 284 / 296.
# Right sub-channel (gap between app & data containers): x=888/892/896.
# Future-state edges use grey/dashed (no "Future" label).
# ============================================================

# 1. Browser -> API Gateway (source = blue). One-way, like most arrows.
edge(
    browser,
    api_gw,
    exitX=1,
    exitY=0.5,
    entryX=0,
    entryY=0.5,
    color=COLOR_PRIMARY_BLUE,
    label="HTTPS",
    label_bg="#eaf3fb",
)

# 2. CDN (future) -> Browser — grey/dashed, no label.
edge(
    cdn_future,
    browser,
    exitX=0.5,
    exitY=0,
    entryX=0.5,
    entryY=1,
    color=COLOR_FUTURE_GREY,
    style="dashed",
)

# 3. Config -> API Gateway (source = gold). Dashed = configuration mount.
#    Route up the sub-channel at x=372 (gap between External & App).
edge(
    config,
    api_gw,
    exitX=1,
    exitY=0.05,
    entryX=0,
    entryY=0.75,
    color=COLOR_CONFIG_GOLD,
    style="dashed",
    label="Load Config",
    label_bg="#eaf3fb",
    waypoints=[(372, 370), (372, 200)],
)

# 4. API Gateway -> Auth Service (source = orange).
#    The gap here is only 40px, so "Verify Token" is stacked into two <div>
#    lines to fit — a single line (~66px) would overhang both boxes and read
#    as a floating caption (SHORT_LABELLED_EDGE).
edge(
    api_gw,
    auth,
    exitX=1,
    exitY=0.5,
    entryX=0,
    entryY=0.5,
    color=COLOR_GATEWAY_ORANGE,
    label="Verify<div>Token</div>",
    label_bg="#f3f0ff",
)

# 5. API Gateway -> Web Service (source = orange, dominant flow, width=3).
#    Multi-line label authored with <div> tags for round-trip stability.
edge(
    api_gw,
    web,
    exitX=0.5,
    exitY=1,
    entryX=0.5,
    entryY=0,
    color=COLOR_GATEWAY_ORANGE,
    width=3,
    label="Route<div>Request</div>",
    label_bg="#f3f0ff",
    # Lifted toward API Gateway so it reads as leaving the gateway rather
    # than floating mid-gap, and placed left of the x=510 line to stay clear
    # of the Read/Write label.
    label_x=-32,
    label_y=-20,
)

# 6. Web -> Cache (source = green). Dotted = out-of-band lookup.
#    Lane y=296, sub-channel x=896. jump=True: this lane crosses the
#    API Gateway -> Web vertical (edge 5) at x~510; the gap hop reads
#    cleaner than rerouting (perpendicular crossings are valid anyway).
edge(
    web,
    cache,
    exitX=0.45,
    exitY=0,
    entryX=0,
    entryY=0.5,
    color=COLOR_FRONTEND_GREEN,
    style="dotted",
    jump=True,
    label="Read",
    label_bg="#f3f0ff",
    waypoints=[(500, 296), (896, 296), (896, 308)],
)

# 7. Web <-> Primary DB (source = green, dominant flow, width=3).
#    Lane y=284, sub-channel x=892. Label lifted above the lane.
#    bidirectional=True is the EXCEPTION, not the rule — used here only
#    because data genuinely flows both ways (reads out, writes in). Almost
#    every other edge stays one-way.
edge(
    web,
    primary_db,
    exitX=0.55,
    exitY=0,
    entryX=0,
    entryY=0.6,
    color=COLOR_FRONTEND_GREEN,
    width=3,
    bidirectional=True,
    label="Read/Write",
    label_bg="#f3f0ff",
    waypoints=[(520, 284), (892, 284), (892, 202)],
    # The longest segment's midpoint (x=706) lands over the Background
    # Worker, so the label reads as the worker's. Pulled back to where the
    # line leaves Web Service, which is what it describes.
    #
    # label_y sits it flush on its own y=284 lane. It cannot drop further:
    # the dotted Read lane is only 12px below at y=296, and a label wide
    # enough to reach it would mask a line belonging to a different edge.
    label_x=-140,
    label_y=-14,
)

# 8. Web -> Message Queue (source = green). Lane y=425 (below the row),
#    sub-channel x=896, enter queue at y=401.
edge(
    web,
    queue,
    exitX=0.5,
    exitY=1,
    entryX=0,
    entryY=0.4,
    color=COLOR_FRONTEND_GREEN,
    label="Enqueue Job",
    label_bg="#f3f0ff",
    waypoints=[(510, 425), (896, 425), (896, 401)],
)

# 9. Background Worker -> Message Queue (source = purple). Dotted = pull.
#    Short hop down the x=890 channel; enter queue at y=419.
edge(
    worker,
    queue,
    exitX=1,
    exitY=0.75,
    entryX=0,
    entryY=0.65,
    color=COLOR_ORCH_PURPLE,
    style="dotted",
    label="Consume",
    label_bg="#f3f0ff",
    waypoints=[(890, 380), (890, 419)],
)

# 10. Background Worker -> Primary DB (source = purple). Lane y=272
#     (top lane), sub-channel x=888. Label lifted above the lane.
edge(
    worker,
    primary_db,
    exitX=0.5,
    exitY=0,
    entryX=0,
    entryY=0.72,
    color=COLOR_ORCH_PURPLE,
    label="Write Result",
    label_bg="#f3f0ff",
    waypoints=[(755, 272), (888, 272), (888, 215)],
    label_x=0,
    label_y=-14,
)

# 11. Primary DB -> Analytics Sink (source = navy). Dashed = future,
#     no "Future" label. Side channel at x=1250 (right of the data boxes,
#     which end at x=1210, and clear of the "Replicate" label so it
#     doesn't sit on the Message Queue box).
edge(
    primary_db,
    analytics_future,
    exitX=1,
    exitY=0.9,
    entryX=1,
    entryY=0.5,
    color=COLOR_DATASTORE_NAVY,
    style="dashed",
    label="Replicate",
    label_bg="#e7f0fb",
    waypoints=[(1250, 234), (1250, 514)],
)


# ----- Legend (lean) -----
# Colour + labels carry the meaning; the only convention a reader can't infer
# is the future-state styling, so that's all the legend states. (Drop the
# legend entirely if a diagram has no future-state shapes.)
legend_text = "<b>Legend:</b> Grey / dashed shape = future state"
box(
    40,
    616,
    W - 80,
    28,
    legend_text,
    fill="#ffffff",
    stroke="#cccccc",
    fontColor="#444444",
    fontSize=10,
    bold=False,
    valign="middle",
    halign="left",
    spacingLeft=10,
)


xml_bytes = ET.tostring(mxfile, encoding="utf-8")
pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ")
out_path = "./three-tier-web.drawio"
with open(out_path, "w") as f:
    f.write(pretty)
print(f"Wrote {out_path}")
print(f"Cells: {_next[0] - 2}")
