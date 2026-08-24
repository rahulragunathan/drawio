"""Tests for scripts/validate.py.

Each test builds a minimal .drawio fixture into tmp_path that exhibits
exactly one violation type (or zero), then asserts the validator
flags only that type. The set comparison guards against accidental
co-firing — if a CROSSING fixture also trips OVERLAP or LABEL_OVERLAP,
the fixture is no longer minimal and the test fails loudly.
"""

import subprocess
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(SKILL_ROOT / "tests" / "fixtures"))

from builders import (  # noqa: E402
    build_clean,
    build_container_entry,
    build_crossing,
    build_dangling,
    build_diagonal,
    build_label_overlap,
    build_overlap,
    build_point_anchored,
    build_short_labelled_edge,
    build_stub_clean,
    build_text_overlap,
    build_text_overlap_inside,
)
from validate import normalise_label, validate  # noqa: E402


def _types(violations):
    """Extract the violation-type prefixes (CROSSING, OVERLAP, ...)."""
    return {line.split(":", 1)[0] for line in violations}


@pytest.mark.parametrize(
    "label,expected",
    [
        # The locked multi-line convention: <div> opens a block, so it breaks
        # the line just as </div> closes it. Measuring 'Verify<div>Token</div>'
        # as one 11-char line overstates its width by ~2x.
        ("Verify<div>Token</div>", ["Verify", "Token"]),
        ("<div>Route</div><div>Request</div>", ["Route", "Request"]),
        ("Plain label", ["Plain label"]),
        ("Read<br>Write", ["Read", "Write"]),
        ("<b>Bold</b>&nbsp;text", ["Bold text"]),
    ],
)
def test_normalise_label_splits_lines(label, expected):
    assert normalise_label(label) == expected


def test_clean_fixture_has_no_violations(tmp_path):
    p = tmp_path / "clean.drawio"
    build_clean(p)
    v = validate(str(p))
    assert v == [], f"expected zero violations, got: {v}"


def test_stub_clean_fixture_has_no_violations(tmp_path):
    """Misaligned anchors with no waypoints must NOT fire DIAGONAL — the
    anchor stub is squared into an orthogonal L-bend (matching draw.io)."""
    p = tmp_path / "stub_clean.drawio"
    build_stub_clean(p)
    v = validate(str(p))
    assert v == [], f"expected zero violations after stub-squaring, got: {v}"


def test_point_anchored_fixture_has_no_violations(tmp_path):
    """An edge pinned to a fixed targetPoint (no target cell) must NOT fire
    DANGLING — it's a normal draw.io Desktop hand-tuning artifact."""
    p = tmp_path / "point_anchored.drawio"
    build_point_anchored(p)
    v = validate(str(p))
    assert v == [], f"expected zero violations for point-anchored edge, got: {v}"


def test_crossing_fixture_fires_only_crossing(tmp_path):
    p = tmp_path / "crossing.drawio"
    build_crossing(p)
    v = validate(str(p))
    assert v, "expected at least one CROSSING violation"
    assert _types(v) == {"CROSSING"}, (
        f"expected only CROSSING violations, got: {sorted(_types(v))} with details: {v}"
    )


def test_overlap_fixture_fires_only_overlap(tmp_path):
    p = tmp_path / "overlap.drawio"
    build_overlap(p)
    v = validate(str(p))
    assert v, "expected at least one OVERLAP violation"
    assert _types(v) == {"OVERLAP"}, (
        f"expected only OVERLAP violations, got: {sorted(_types(v))} with details: {v}"
    )


def test_text_overlap_fixture_fires_only_text_overlap(tmp_path):
    p = tmp_path / "text_overlap.drawio"
    build_text_overlap(p)
    v = validate(str(p))
    assert v, "expected at least one TEXT_OVERLAP violation"
    assert _types(v) == {"TEXT_OVERLAP"}, (
        f"expected only TEXT_OVERLAP violations, got: {sorted(_types(v))} "
        f"with details: {v}"
    )


def test_container_entry_fixture_has_no_violations(tmp_path):
    """An edge dropping into a box inside a container must NOT fire
    TEXT_OVERLAP — the bottom-service-band pattern requires piercing the
    container's full-width title band to reach the box."""
    p = tmp_path / "container_entry.drawio"
    build_container_entry(p)
    v = validate(str(p))
    assert v == [], f"expected zero violations entering a container, got: {v}"


def test_text_overlap_inside_fixture_still_fires(tmp_path):
    """The entry exemption covers vertical entry stubs only — a segment
    running ALONG the title band still fires, even between two boxes that
    both live inside the container."""
    p = tmp_path / "text_overlap_inside.drawio"
    build_text_overlap_inside(p)
    v = validate(str(p))
    assert v, "expected at least one TEXT_OVERLAP violation"
    assert _types(v) == {"TEXT_OVERLAP"}, (
        f"expected only TEXT_OVERLAP violations, got: {sorted(_types(v))} "
        f"with details: {v}"
    )


def test_short_labelled_edge_fixture_fires_only_short_labelled_edge(tmp_path):
    p = tmp_path / "short_labelled_edge.drawio"
    build_short_labelled_edge(p)
    v = validate(str(p))
    assert v, "expected at least one SHORT_LABELLED_EDGE violation"
    assert _types(v) == {"SHORT_LABELLED_EDGE"}, (
        f"expected only SHORT_LABELLED_EDGE violations, got: "
        f"{sorted(_types(v))} with details: {v}"
    )


def test_label_overlap_fixture_fires_only_label_overlap(tmp_path):
    p = tmp_path / "label_overlap.drawio"
    build_label_overlap(p)
    v = validate(str(p))
    assert v, "expected at least one LABEL_OVERLAP violation"
    assert _types(v) == {"LABEL_OVERLAP"}, (
        f"expected only LABEL_OVERLAP violations, got: {sorted(_types(v))} "
        f"with details: {v}"
    )


def test_diagonal_fixture_fires_only_diagonal(tmp_path):
    p = tmp_path / "diagonal.drawio"
    build_diagonal(p)
    v = validate(str(p))
    assert v, "expected at least one DIAGONAL violation"
    assert _types(v) == {"DIAGONAL"}, (
        f"expected only DIAGONAL violations, got: {sorted(_types(v))} with details: {v}"
    )


def test_dangling_fixture_fires_only_dangling(tmp_path):
    p = tmp_path / "dangling.drawio"
    build_dangling(p)
    v = validate(str(p))
    assert v, "expected at least one DANGLING violation"
    assert _types(v) == {"DANGLING"}, (
        f"expected only DANGLING violations, got: {sorted(_types(v))} with details: {v}"
    )


def test_three_tier_example_validates_clean(tmp_path):
    """End-to-end regression: the bundled example builds and validates."""
    example = SKILL_ROOT / "examples" / "build_three_tier_web.py"
    result = subprocess.run(
        [sys.executable, str(example)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"example build failed: {result.stderr}"
    out = tmp_path / "three-tier-web.drawio"
    assert out.exists(), "example did not produce three-tier-web.drawio"
    v = validate(str(out))
    assert v == [], f"three-tier example should validate clean, got: {v}"
