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
