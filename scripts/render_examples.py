#!/usr/bin/env python3
"""Regenerate every example's renders into renders/, light and dark.

Run at the end of a phase: the PNGs are what gets reviewed for sign-off, and
a stale one is worse than none. A clean validate says nothing about whether a
diagram is legible, so the render is the part a human actually judges.

Both themes are produced even though the skill no longer authors dark
colours — draw.io inverts them on export, and its choices still have to be
looked at.

    python scripts/render_examples.py

Needs the draw.io Desktop CLI. Every example is validated first; a diagram
with violations is reported and not rendered, because reviewing a picture of
a broken layout wastes the review.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from render_png import find_drawio_cli, render  # noqa: E402
from validate import validate  # noqa: E402


EXAMPLES_DIR = SKILL_ROOT / "examples"
RENDERS_DIR = SKILL_ROOT / "renders"
THEMES = ("light", "dark")


def build(script: Path, workdir: Path) -> list[Path]:
    """Run one generator and return the .drawio files it wrote."""
    subprocess.run(
        [sys.executable, str(script)],
        cwd=workdir,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(workdir.glob("*.drawio"))


def main() -> int:
    cli = find_drawio_cli()
    if cli is None:
        print("ERROR: drawio CLI not found on PATH.")
        print("Install from: https://github.com/jgraph/drawio-desktop/releases")
        return 1

    scripts = sorted(EXAMPLES_DIR.glob("build_*.py"))
    if not scripts:
        print(f"No examples found in {EXAMPLES_DIR}")
        return 1

    RENDERS_DIR.mkdir(exist_ok=True)
    failed: list[str] = []
    written = 0

    for script in scripts:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            try:
                diagrams = build(script, workdir)
            except subprocess.CalledProcessError as exc:
                print(f"✗ {script.name}: generator failed\n{exc.stderr}")
                failed.append(script.name)
                continue

            for diagram in diagrams:
                violations = validate(str(diagram))
                if violations:
                    print(f"✗ {diagram.name}: {len(violations)} violation(s)")
                    for v in violations:
                        print(f"    {v}")
                    failed.append(diagram.name)
                    continue

                for theme in THEMES:
                    out = RENDERS_DIR / f"{diagram.stem}-{theme}.png"
                    # render() narrates each CLI invocation; that detail is
                    # noise here, where the point is a short reviewable list.
                    with contextlib.redirect_stdout(io.StringIO()):
                        ok = render(diagram, cli, out, theme=theme)
                    if ok:
                        written += 1
                    else:
                        failed.append(f"{diagram.name} ({theme})")
                print(
                    f"✓ {diagram.stem}: validated clean, rendered {len(THEMES)} themes"
                )

    print(f"\n{written} PNG(s) in {RENDERS_DIR.relative_to(SKILL_ROOT)}/")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
