#!/usr/bin/env python3
"""Offline .drawio preview renderer (approximate; needs matplotlib).

Unlike render_png.py (which calls the draw.io Desktop CLI for a
pixel-accurate export), this renders a preview using only matplotlib —
no external binary required. It reuses validate.py's geometry functions
(edge_polyline, edge_label_center) so the preview shows EXACTLY the
geometry the validator reasons about. That makes it the fastest way to
eyeball routing, lane spacing, and label placement while iterating,
including in sandboxes or VMs where the draw.io CLI isn't installed.

Caveats: text wrapping, font metrics, and rounded-corner rendering are
approximations of draw.io's. Trust it for layout (box positions, edge
routes, label anchors); open the .drawio in draw.io for final fidelity.

Usage:
    python scripts/preview.py <file.drawio> [out.png]

Requires: matplotlib (pip install matplotlib).
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Rectangle
except ImportError:
    sys.exit("preview.py needs matplotlib. Install it with: pip install matplotlib")

sys.path.insert(0, str(Path(__file__).parent))
from validate import (  # noqa: E402
    edge_label_center,
    edge_polyline,
    parse_drawio,
    parse_style,
)


# Drawn in place of any colour matplotlib cannot parse.
FALLBACK_COLOUR = "#b0b0b0"


def light(value: str) -> str:
    """Return a colour matplotlib can draw, or a neutral grey.

    The preview is a layout check, not a colour proof, so an unusable value
    must never abort the render. draw.io accepts things matplotlib does not —
    `default`, gradient values, and colour functions — and a hand-edited file
    can contain anything. A wrong-coloured box still shows the geometry; a
    traceback shows nothing.
    """
    if not value:
        return FALLBACK_COLOUR
    value = value.strip()
    try:
        mcolors.to_rgba(value)
    except (ValueError, TypeError):
        return FALLBACK_COLOUR
    return value


def strip_html(s: str) -> str:
    s = s.replace("</div>", "\n").replace("<div>", "\n")
    s = s.replace("<br>", "\n").replace("<br/>", "\n")
    s = re.sub(r"<[^>]+>", "", s)
    for k, v in {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
    }.items():
        s = s.replace(k, v)
    return re.sub(r"\n+", "\n", s).strip()


def cell_styles(path):
    root = ET.parse(path).getroot()
    out = {}
    for cell in root.findall(".//mxCell"):
        cid = cell.get("id")
        if cid in ("0", "1"):
            continue
        out[cid] = (parse_style(cell.get("style") or ""), cell.get("value") or "")
    return out


def render(path, out_png):
    boxes, edges = parse_drawio(path)
    styles = cell_styles(path)
    gm = ET.parse(path).getroot().find(".//mxGraphModel")
    W = float(gm.get("pageWidth", 1280))
    H = float(gm.get("pageHeight", 820))

    fig, ax = plt.subplots(figsize=(W / 100, H / 100), dpi=130)
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)  # draw.io y grows downward
    ax.set_aspect("equal")
    ax.axis("off")

    # 1) Containers first (z-order bottom)
    for cid, box in boxes.items():
        if not box.is_container:
            continue
        sd, val = styles.get(cid, ({}, ""))
        ax.add_patch(
            Rectangle(
                (box.x, box.y),
                box.w,
                box.h,
                facecolor=light(sd.get("fillColor", "#ffffff")),
                edgecolor=light(sd.get("strokeColor", "#333333")),
                linewidth=1.6,
                linestyle=(0, (6, 4)),
                zorder=1,
            )
        )
        ax.text(
            box.x + 10,
            box.y + 16,
            strip_html(val).split("\n")[0],
            fontsize=9,
            style="italic",
            color=light(sd.get("strokeColor", "#333333")),
            ha="left",
            va="center",
            zorder=2,
        )

    # 2) Solid boxes
    for cid, box in boxes.items():
        if box.is_container:
            continue
        sd, val = styles.get(cid, ({}, ""))
        fill = light(sd.get("fillColor", "#cccccc"))
        box_ls = (0, (5, 3)) if sd.get("dashed") == "1" else "-"
        ax.add_patch(
            FancyBboxPatch(
                (box.x + 2, box.y + 2),
                box.w - 4,
                box.h - 4,
                boxstyle="round,pad=2,rounding_size=6",
                facecolor=fill,
                edgecolor=light(sd.get("strokeColor")) or fill,
                linewidth=1.2,
                linestyle=box_ls,
                zorder=3,
            )
        )
        lines = strip_html(val).split("\n")
        if len(lines) > 6:
            lines = lines[:6] + ["…"]
        ax.text(
            box.x + box.w / 2,
            box.y + box.h / 2,
            "\n".join(lines),
            fontsize=7.5,
            color=light(sd.get("fontColor", "#ffffff")),
            ha="center",
            va="center",
            zorder=4,
        )

    # 3) Edges
    for e in edges:
        poly = edge_polyline(e, boxes)
        if len(poly) < 2:
            continue
        sd, _ = styles.get(e.cell_id, ({}, ""))
        color = light(sd.get("strokeColor", "#333333"))
        lw = float(sd.get("strokeWidth", 2)) * 0.7
        ls = "-"
        if sd.get("dashed") == "1":
            ls = ":" if sd.get("dashPattern", "").startswith("1") else (0, (5, 3))
        ax.plot(
            [p[0] for p in poly],
            [p[1] for p in poly],
            color=color,
            linewidth=lw,
            linestyle=ls,
            zorder=5,
            solid_capstyle="round",
        )
        ax.annotate(
            "",
            xy=poly[-1],
            xytext=poly[-2],
            arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, shrinkA=0, shrinkB=0),
            zorder=5,
        )
        if e.label.strip():
            cx, cy = edge_label_center(e, poly)
            ax.text(
                cx,
                cy,
                strip_html(e.label),
                fontsize=6.5,
                color=color,
                ha="center",
                va="center",
                zorder=6,
                bbox=dict(
                    boxstyle="square,pad=0.15", facecolor="white", edgecolor="none"
                ),
            )

    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"Wrote {out_png}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python preview.py <file.drawio> [out.png]")
        sys.exit(2)
    src = sys.argv[1]
    out = (
        sys.argv[2] if len(sys.argv) > 2 else str(Path(src).with_suffix(".preview.png"))
    )
    render(src, out)


if __name__ == "__main__":
    main()
