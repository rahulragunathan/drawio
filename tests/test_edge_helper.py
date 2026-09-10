"""Tests for `edge()`'s line-jump handling in the template.

Line jumps are on by default, which makes two things easy to break silently
and worth pinning down:

- the default itself. `jump="gap"` is what stops a crossing from reading as a
  junction; flipping it back to off is invisible in every test that only
  checks a diagram validates, because the validator does not look at
  jumpStyle at all.
- the alias forms. `jump=True` / `jump=False` predate the style argument and
  are still spelled that way in older generators, so they have to keep
  meaning "gap" and "off".

The helpers are loaded out of the real template rather than re-vendored, the
same way tests/test_icons.py does it.
"""

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate import parse_style  # noqa: E402


def load_template_helpers():
    """Exec the template's helper section, stopping at the diagram marker."""
    src = (SKILL_ROOT / "assets" / "build_template.py").read_text()
    head = src.split("# === YOUR DIAGRAM GOES HERE ===")[0]
    ns: dict = {}
    exec(compile(head, "build_template.py", "exec"), ns)  # noqa: S102
    return ns


def edge_style(**kwargs):
    """Emit one edge and return its parsed style dict."""
    helpers = load_template_helpers()
    helpers["edge"]("srcId", "dstId", **kwargs)
    cells = helpers["root"].findall("mxCell")
    edges = [c for c in cells if c.get("edge") == "1"]
    assert len(edges) == 1
    return parse_style(edges[-1].get("style"))


def test_jump_defaults_to_gap():
    # The default is the whole point: an edge that crosses another has to read
    # as crossing it, not joining it.
    assert edge_style().get("jumpStyle") == "gap"


def test_jump_accepts_each_drawio_style():
    for style in ("gap", "line", "arc", "sharp"):
        assert edge_style(jump=style).get("jumpStyle") == style


def test_jump_none_and_false_emit_no_jump_style_at_all():
    # Not "jumpStyle=none" — draw.io's own default is none, so the token is
    # noise in the file and churns the diff against a Desktop round-trip.
    for off in (False, None, "none"):
        assert "jumpStyle" not in edge_style(jump=off)


def test_jump_true_is_still_an_alias_for_gap():
    assert edge_style(jump=True).get("jumpStyle") == "gap"


def test_unknown_jump_style_raises():
    # draw.io silently ignores a jumpStyle it does not know, so a typo would
    # otherwise show up as "the jumps just aren't there" with nothing to find.
    with pytest.raises(ValueError, match="jump must be one of"):
        edge_style(jump="gapp")


def test_dotted_edge_in_the_example_uses_line_not_gap():
    """The worked case for the dashed/dotted rule.

    A gap is an absence of ink. On dashPattern=1 4 it is indistinguishable
    from the pattern, so the hop disappears — and this edge is the one
    draw.io hops, being declared after the arrow it crosses.
    """
    src = (SKILL_ROOT / "examples" / "build_three_tier_web.py").read_text()

    assert 'jump="line"' in src
    assert "jump=True" not in src


def test_every_dotted_or_dashed_edge_that_hops_is_not_left_on_gap(tmp_path):
    """Guard the rule across the whole bundled example.

    draw.io hops the edge drawn *later*, so a dashed edge only needs "line"
    when it is the later one at some crossing. Reconstruct the routes with
    the validator's own geometry and check exactly those.
    """
    from validate import edge_polyline, parse_drawio, segments

    script = SKILL_ROOT / "examples" / "build_three_tier_web.py"
    subprocess.run(
        [sys.executable, str(script)], cwd=tmp_path, check=True, capture_output=True
    )
    path = tmp_path / "three-tier-web.drawio"
    assert path.exists(), "the example generator wrote nothing"

    boxes, edges = parse_drawio(str(path))
    styles = {
        c.get("id"): parse_style(c.get("style") or "")
        for c in ET.parse(path).getroot().iter("mxCell")
    }
    lines = [(e, edge_polyline(e, boxes)) for e in edges]

    def crosses(p1, p2):
        for (ax1, ay1), (ax2, ay2) in segments(p1):
            for (bx1, by1), (bx2, by2) in segments(p2):
                if ay1 == ay2 and bx1 == bx2:
                    if min(ax1, ax2) < bx1 < max(ax1, ax2) and min(
                        by1, by2
                    ) < ay1 < max(by1, by2):
                        return True
                if ax1 == ax2 and by1 == by2:
                    if min(ay1, ay2) < by1 < max(ay1, ay2) and min(
                        bx1, bx2
                    ) < ax1 < max(bx1, bx2):
                        return True
        return False

    offenders = []
    for i, (_e1, p1) in enumerate(lines):
        for e2, p2 in lines[i + 1 :]:
            if not crosses(p1, p2):
                continue
            later = styles.get(e2.cell_id, {})  # document order == draw order
            if later.get("dashed") == "1" and later.get("jumpStyle") == "gap":
                offenders.append(e2.label or e2.cell_id)

    assert offenders == [], (
        f"dashed/dotted edges hop on an invisible gap: {offenders} — "
        'these need jump="line"'
    )
