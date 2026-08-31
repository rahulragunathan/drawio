"""Tests for scripts/render_examples.py.

The rendering itself needs draw.io, so what is pinned here is the contract
around it: the tool must say plainly when it cannot run, and must refuse to
render a diagram the validator rejected.
"""

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import render_examples  # noqa: E402


def test_missing_drawio_reports_and_fails(monkeypatch, capsys):
    monkeypatch.setattr(render_examples, "find_drawio_cli", lambda: None)

    code = render_examples.main()

    out = capsys.readouterr().out
    assert code == 1
    assert "drawio CLI not found" in out
    assert "releases" in out, "tell the reader where to get it"


def test_a_diagram_with_violations_is_not_rendered(monkeypatch, capsys, tmp_path):
    # Reviewing a picture of a layout the validator already rejected wastes
    # the review, so a failing diagram must be reported instead.
    rendered = []
    monkeypatch.setattr(render_examples, "find_drawio_cli", lambda: "drawio")
    monkeypatch.setattr(render_examples, "validate", lambda p: ["CROSSING: bad"])
    monkeypatch.setattr(
        render_examples,
        "render",
        lambda *a, **k: rendered.append(a) or True,
    )

    def fake_build(script, workdir):
        d = Path(workdir) / "sample.drawio"
        d.write_text("<mxfile/>")
        return [d]

    monkeypatch.setattr(render_examples, "build", fake_build)

    code = render_examples.main()

    assert code == 1
    assert rendered == [], "must not render a diagram that failed validation"
    assert "error(s)" in capsys.readouterr().out


def test_warnings_do_not_block_a_render(monkeypatch, capsys, tmp_path):
    # validate.py exits 0 on warnings. Blocking here would mean this tool
    # disagrees with the validator about whether a diagram is acceptable.
    rendered = []
    monkeypatch.setattr(render_examples, "find_drawio_cli", lambda: "drawio")
    monkeypatch.setattr(
        render_examples,
        "validate",
        lambda p: ["DIAGONAL: edge 'x' has a diagonal segment"],
    )
    monkeypatch.setattr(
        render_examples, "render", lambda *a, **k: rendered.append(a) or True
    )

    def fake_build(script, workdir):
        d = Path(workdir) / "sample.drawio"
        d.write_text("<mxfile/>")
        return [d]

    monkeypatch.setattr(render_examples, "build", fake_build)

    code = render_examples.main()

    assert code == 0, "a warning is advisory; it must not block the render"
    # Two themes per diagram, across however many examples the repo has.
    assert rendered and len(rendered) % len(render_examples.THEMES) == 0
    assert "DIAGONAL" in capsys.readouterr().out, "but the warning must be shown"


def test_a_failed_render_is_not_reported_as_success(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(render_examples, "find_drawio_cli", lambda: "drawio")
    monkeypatch.setattr(render_examples, "validate", lambda p: [])
    monkeypatch.setattr(render_examples, "render", lambda *a, **k: False)

    def fake_build(script, workdir):
        d = Path(workdir) / "sample.drawio"
        d.write_text("<mxfile/>")
        return [d]

    monkeypatch.setattr(render_examples, "build", fake_build)

    code = render_examples.main()

    assert code == 1
    assert "rendered 2 themes" not in capsys.readouterr().out
