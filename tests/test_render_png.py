"""Tests for scripts/render_png.py.

Covers the argument parsing (a pure function — no drawio CLI needed) and
the one piece of plumbing that matters: that an explicit --output path
reaches the CLI invocation. The subprocess call is faked at the system
boundary so the real render() code path runs without drawio installed.
"""

import subprocess
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import render_png  # noqa: E402
from render_png import parse_args  # noqa: E402


# ----------------------------------------------------------------------
# parse_args — accepted forms
# ----------------------------------------------------------------------


def test_no_args_returns_empty_paths():
    """Zero args is the glob-the-cwd mode; main() fills the paths in."""
    assert parse_args([]) == ([], None)


def test_single_input_without_output():
    assert parse_args(["a.drawio"]) == (["a.drawio"], None)


def test_multiple_inputs_without_output():
    assert parse_args(["a.drawio", "b.drawio"]) == (["a.drawio", "b.drawio"], None)


@pytest.mark.parametrize(
    "argv",
    [
        ["a.drawio", "-o", "out.png"],
        ["a.drawio", "--output", "out.png"],
        ["a.drawio", "--output=out.png"],
        ["-o", "out.png", "a.drawio"],  # flag before the input
    ],
)
def test_output_flag_forms(argv):
    paths, out = parse_args(argv)
    assert paths == ["a.drawio"]
    assert out == Path("out.png")


# ----------------------------------------------------------------------
# parse_args — rejected forms. --output names ONE destination file, so
# anything that would render several diagrams into it is an error rather
# than a silent overwrite of all but the last.
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv,expected",
    [
        (["a.drawio", "b.drawio", "-o", "out.png"], "exactly one input"),
        (["-o", "out.png"], "exactly one input"),  # would glob the cwd
        (["a.drawio", "-o"], "needs a file path"),
        (["a.drawio", "--output="], "needs a file path"),
        (["a.drawio", "-o", "x.png", "-o", "y.png"], "more than once"),
        (["a.drawio", "--frobnicate"], "unknown option"),
    ],
)
def test_rejected_invocations(argv, expected):
    with pytest.raises(ValueError, match=expected):
        parse_args(argv)


# ----------------------------------------------------------------------
# render — the explicit path must reach the CLI
# ----------------------------------------------------------------------


def _fake_run(recorder):
    def run(cmd, **kwargs):
        recorder.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    return run


def test_render_defaults_to_replacing_the_extension(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(render_png.subprocess, "run", _fake_run(calls))
    src = tmp_path / "foo.drawio"
    src.write_text("<mxfile/>")
    assert render_png.render(src, "drawio") is True
    assert str(tmp_path / "foo.png") in calls[0]
    assert str(tmp_path / "foo.drawio.png") not in calls[0]


def test_render_honours_explicit_output(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(render_png.subprocess, "run", _fake_run(calls))
    src = tmp_path / "foo.drawio"
    src.write_text("<mxfile/>")
    out = tmp_path / "docs" / "architecture.png"
    assert render_png.render(src, "drawio", out) is True
    assert str(out) in calls[0]


def test_render_creates_missing_output_directory(tmp_path, monkeypatch):
    """Naming a destination under a directory that doesn't exist yet should
    work — the drawio CLI fails rather than creating it."""
    monkeypatch.setattr(render_png.subprocess, "run", _fake_run([]))
    src = tmp_path / "foo.drawio"
    src.write_text("<mxfile/>")
    render_png.render(src, "drawio", tmp_path / "docs" / "out.png")
    assert (tmp_path / "docs").is_dir()
