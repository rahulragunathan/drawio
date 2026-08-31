"""Tests for scripts/preview.py.

The preview is a layout check. Anything that makes it abort costs more than a
mis-drawn colour, so the colour path is the part worth pinning.
"""

import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

pytest.importorskip(
    "matplotlib", reason="preview.py is the skill's only matplotlib user"
)

import preview  # noqa: E402


@pytest.mark.parametrize(
    "value",
    [
        "light-dark(#8C4FFF,#b59dff)",  # authored before 1.3.0
        "default",  # draw.io accepts it, matplotlib does not
        "rgba(1,2,3,0.5)",
        "",
        None,
    ],
)
def test_unusable_colours_fall_back_instead_of_raising(value):
    import matplotlib.colors as mcolors

    result = preview.light(value)

    # Whatever comes back must be drawable, or the render aborts mid-figure.
    mcolors.to_rgba(result)


def test_a_usable_colour_passes_through_untouched():
    assert preview.light("#0078d4") == "#0078d4"


def _box(**kw):
    from validate import Box

    defaults = dict(
        cell_id="2", label="", x=0.0, y=0.0, w=100.0, h=60.0, is_container=False
    )
    defaults.update(kw)
    return Box(**defaults)


def test_a_normal_box_centres_its_text():
    box = _box(label="Order Handler")

    x, y, va = preview.text_anchor(box)

    assert (x, y) == (50.0, 30.0)
    assert va == "center"


def test_an_icon_node_puts_its_caption_below_the_shape():
    # draw.io renders a bottom-positioned label under the glyph. Centring it
    # would draw the caption on top of the icon and hide the real crowding.
    box = _box(label="Fargate", w=48.0, h=48.0, label_below=True)

    x, y, va = preview.text_anchor(box)

    assert x == 24.0
    assert y > box.y2, "caption must sit below the shape, not inside it"
    assert va == "top"


def test_the_glyph_placeholder_names_the_icon_it_stands_for():
    # The preview cannot draw the real stencil, so it must at least say which
    # icon belongs there — a blank plate hides a wrong or missing name.
    assert (
        preview.short_icon_name(
            {"shape": "mxgraph.aws4.resourceIcon", "resIcon": "mxgraph.aws4.lambda"}
        )
        == "lambda"
    )
    assert (
        preview.short_icon_name({"shape": "mxgraph.kubernetes.icon2", "prIcon": "pod"})
        == "pod"
    )
    assert (
        preview.short_icon_name(
            {"shape": "image", "image": "img/lib/azure2/compute/Function_Apps.svg"}
        )
        == "Function_Apps"
    )
    assert (
        preview.short_icon_name({"shape": "image", "image": "data:image/svg+xml,AAA"})
        == "svg"
    )


def test_a_box_without_a_stroke_colour_borders_itself():
    # light() never returns a falsy value, so "light(x) or fill" could never
    # reach its fallback: a box with no strokeColor got the grey used for
    # unparseable colours instead of a border matching its fill.
    assert preview.box_colours({"fillColor": "#0078d4"}) == ("#0078d4", "#0078d4")
    assert preview.box_colours({"fillColor": "#0078d4", "strokeColor": "#333333"}) == (
        "#0078d4",
        "#333333",
    )
