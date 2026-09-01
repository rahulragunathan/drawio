"""Tests for scripts/package_skill.py.

The archive is what actually gets uploaded, so what it contains matters more
than that the command ran. These assert the shape of the result, not the
mechanics of zipping.
"""

import sys
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import package_skill  # noqa: E402


def _build(tmp_path):
    out = tmp_path / "drawio.skill"
    package_skill.build_package(SKILL_ROOT, out)
    with zipfile.ZipFile(out) as z:
        return out, z.namelist()


def test_the_archive_is_rooted_at_the_skill_folder(tmp_path):
    # Claude expects drawio/SKILL.md at the archive root, not SKILL.md loose
    # or nested under a wrapper directory.
    _out, names = _build(tmp_path)

    assert "drawio/SKILL.md" in names
    assert all(n.startswith("drawio/") for n in names)


def test_no_hidden_files_or_directories_are_packaged(tmp_path):
    # .venv and .git are the obvious ones, but .gitignore, .DS_Store and the
    # tool caches are just as unwanted in an upload.
    _out, names = _build(tmp_path)

    hidden = [n for n in names if any(part.startswith(".") for part in n.split("/"))]
    assert hidden == []


def test_review_artifacts_are_not_packaged(tmp_path):
    # renders/ exists for phase sign-off and is ~500KB of PNGs.
    _out, names = _build(tmp_path)

    assert not any(n.startswith("drawio/renders/") for n in names)


def test_the_skill_itself_is_complete(tmp_path):
    _out, names = _build(tmp_path)

    for required in (
        "drawio/SKILL.md",
        "drawio/LICENSE",
        "drawio/scripts/validate.py",
        "drawio/assets/build_template.py",
        "drawio/assets/icon_names.txt.gz",
        "drawio/references/icons.md",
        "drawio/examples/build_aws_vpc_pipeline.py",
        "drawio/examples/snowflake.svg",
    ):
        assert required in names, required


def test_maintainer_docs_are_not_packaged(tmp_path):
    # docs/ is the maintainer's material — architecture, roadmap, the
    # contributing loop. A user installing the skill reads SKILL.md.
    _out, names = _build(tmp_path)

    assert not any(n.startswith("drawio/docs/") for n in names)
