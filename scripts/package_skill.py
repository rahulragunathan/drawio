#!/usr/bin/env python3
"""Build the uploadable `.skill` archive.

A `.skill` file is a zip with a different extension, rooted at the skill
folder: Claude expects `drawio/SKILL.md` at the archive root, not `SKILL.md`
loose and not nested under a wrapper directory.

Run it at the end of a phase, alongside `render_examples.py`, so the packaged
skill matches the commit rather than whatever was last built by hand:

    python scripts/package_skill.py

Writes `../drawio.skill` — beside the skill folder, not inside it, so the
archive never contains a stale copy of itself.
"""

from __future__ import annotations

import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent

# Directories that exist for development or review and have no business in an
# upload. Hidden entries (.git, .venv, .gitignore, .DS_Store, tool caches) are
# excluded by rule rather than by name — see is_packaged().
#
# archive/ is prior-art feedback kept for maintainers: history, not part of
# the skill a user installs. It shipped in packages up to 1.3.0.
EXCLUDED_DIRS = {"renders", "__pycache__", "archive"}


def is_packaged(rel: Path) -> bool:
    """Should this path go into the archive?

    Anything hidden is out. A dotted name is either machine state (.venv,
    .git, tool caches) or repo plumbing (.gitignore) — neither is part of the
    skill, and both have leaked into hand-built archives before.
    """
    parts = rel.parts
    if any(part.startswith(".") for part in parts):
        return False
    return not any(part in EXCLUDED_DIRS for part in parts)


def build_package(skill_root: Path, out_path: Path) -> list[str]:
    """Write the archive and return the entry names it contains."""
    skill_root = Path(skill_root).resolve()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = skill_root.name

    names: list[str] = []
    # Sorted so an unchanged skill produces a byte-comparable archive rather
    # than one that varies with filesystem ordering.
    files = sorted(
        p
        for p in skill_root.rglob("*")
        if p.is_file() and is_packaged(p.relative_to(skill_root))
    )
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            name = f"{prefix}/{path.relative_to(skill_root).as_posix()}"
            z.write(path, name)
            names.append(name)
    return names


def main() -> int:
    out = SKILL_ROOT.parent / f"{SKILL_ROOT.name}.skill"
    names = build_package(SKILL_ROOT, out)
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out.name} ({len(names)} files, {size_kb:.0f}K)")
    if "drawio/SKILL.md" not in names and f"{SKILL_ROOT.name}/SKILL.md" not in names:
        print("ERROR: SKILL.md is missing from the archive")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
