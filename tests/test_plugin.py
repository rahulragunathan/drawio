"""The repository is a one-plugin marketplace holding the create-diagram skill.

These pin what an installed copy needs: manifests Claude Code accepts, one
version source, and a skill that finds its own files wherever it is installed.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent
SKILL_ROOT = REPO_ROOT / "skills" / "create-diagram"
MANIFESTS = REPO_ROOT / ".claude-plugin"


def frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, "SKILL.md has no frontmatter"
    return dict(
        line.split(":", 1)
        for line in match[1].splitlines()
        if re.match(r"^[a-z]+:", line)
    )


def test_plugin_manifest():
    # Fails if the release version drifts between plugin.json and the CHANGELOG,
    # if the marketplace lists anything but this plugin at the repo root, or if a
    # second version source exists that could hide a bump from auto-update.
    plugin = json.loads((MANIFESTS / "plugin.json").read_text())
    market = json.loads((MANIFESTS / "marketplace.json").read_text())
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    latest = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)[1]

    assert plugin["name"] == "drawio"
    assert plugin["version"] == latest
    assert market["name"] == "drawio" and market["owner"]["name"]
    assert [p["name"] for p in market["plugins"]] == ["drawio"]
    assert market["plugins"][0]["source"] == "./"
    assert "version" not in market["plugins"][0]
    assert "version" not in frontmatter((SKILL_ROOT / "SKILL.md").read_text())


def test_skill_layout():
    # Fails if the skill is not named create-diagram, or a bundled file SKILL.md
    # names is missing from the skill folder.
    text = (SKILL_ROOT / "SKILL.md").read_text()
    assert frontmatter(text)["name"].strip() == "create-diagram"
    named = set(re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+)", text))
    for expected in (
        "scripts/validate.py",
        "assets/build_template.py",
        "references/icons.md",
    ):
        assert expected in named, f"SKILL.md never names {expected}"
    missing = sorted(n for n in named if not (SKILL_ROOT / n).exists())
    assert not missing, missing
    assert (SKILL_ROOT / "assets" / "icon_names.txt.gz").is_file()


@pytest.mark.parametrize("manifest", ["plugin.json", "marketplace.json"])
def test_plugin_validates(manifest):
    # Fails if Claude Code rejects either manifest.
    claude = shutil.which("claude")
    if not claude:
        pytest.skip("claude is not installed")
    result = subprocess.run(
        [claude, "plugin", "validate", str(MANIFESTS / manifest)],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
