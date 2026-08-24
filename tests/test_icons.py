"""Tests for the icon catalog itself.

These are pure-data checks against the committed name list, so they need no
draw.io install and catch a typo'd catalog entry on any machine. They guard
two silent-failure modes in particular: an extractor that looks like it
worked (thousands of names) while missing an entire source.
"""

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import list_icons  # noqa: E402


def test_every_catalog_entry_resolves_to_a_real_name():
    universe = list_icons.load_names()
    catalog = list_icons.load_catalog()
    assert catalog, "no catalog parsed from references/icons.md"

    unresolved = [
        (key, name)
        for key, entry in catalog.items()
        for name in list_icons.qualified_names(key, entry)
        if name not in universe
    ]

    assert unresolved == []


def test_committed_names_include_the_javascript_wrapper_shapes():
    # These are registered in draw.io's JS and appear in no stencil file. If
    # the JS sweep regresses, extraction still yields ~9k plausible names and
    # nothing looks broken — but every AWS and Kubernetes icon starts warning.
    universe = list_icons.load_names()

    for wrapper in ("mxgraph.aws4.resourceIcon", "mxgraph.kubernetes.icon2"):
        assert wrapper in universe


def test_committed_names_include_bundled_image_paths():
    # Image assets live under drawio/src/main/webapp/ inside the archive but
    # are referenced style-relative. Filtering on the style-relative prefix
    # matches nothing, which would silently drop every Azure icon.
    universe = list_icons.load_names()

    azure = [n for n in universe if n.startswith("img/lib/azure2/")]
    assert len(azure) > 100


def test_catalog_keys_use_a_known_family_prefix():
    for key, entry in list_icons.load_catalog().items():
        assert entry["family"] in list_icons.FAMILIES, key
        assert key.startswith(entry["family"] + "-"), key
