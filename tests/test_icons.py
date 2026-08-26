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


def load_template_helpers():
    """Exec the template's helper section, stopping at the diagram marker.

    build_template.py is meant to be copied, not imported — it writes a file
    when run — so the helpers are loaded by executing only the part above
    "YOUR DIAGRAM GOES HERE". That keeps these tests on the real template
    code rather than a re-vendored copy that could drift from it.
    """
    src = (SKILL_ROOT / "assets" / "build_template.py").read_text()
    head = src.split("# === YOUR DIAGRAM GOES HERE ===")[0]
    ns: dict = {}
    exec(compile(head, "build_template.py", "exec"), ns)  # noqa: S102
    return ns


def test_icon_style_renders_an_aws_tile_through_its_wrapper():
    style = load_template_helpers()["icon_style"]("aws:lambda", fill="#ED7100")

    assert "shape=mxgraph.aws4.resourceIcon;" in style
    assert "resIcon=mxgraph.aws4.lambda;" in style
    assert "fillColor=#ED7100;" in style
    # Never dashed + top-aligned together: that pair is the validator's
    # container signature and would reclassify the icon as a zone.
    assert not ("dashed=1;" in style and "verticalAlign=top;" in style)


def test_icon_style_uses_a_bare_pricon_for_kubernetes():
    style = load_template_helpers()["icon_style"]("k8s:pod")

    assert "shape=mxgraph.kubernetes.icon2;" in style
    assert "prIcon=pod;" in style


def test_icon_style_emits_an_image_shape_for_azure():
    style = load_template_helpers()["icon_style"]("azure:compute/Function_Apps.svg")

    # Must be "shape=image", never a bare "image;" token: parse_style drops
    # tokens without "=", so the bare form loses the shape marker entirely.
    assert "shape=image;" in style
    assert "image=img/lib/azure2/compute/Function_Apps.svg;" in style


def test_svg_icon_embeds_base64_with_no_semicolon_in_the_payload(tmp_path):
    helpers = load_template_helpers()
    svg = tmp_path / "logo.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')

    style = helpers["icon_style"](helpers["svg_icon"](svg))

    # Verified by rendering: draw.io accepts "data:image/svg+xml,<base64>".
    # The ";base64," spelling renders blank, because ";" ends the style token.
    assert "image=data:image/svg+xml," in style
    assert ";base64," not in style
    payload = style.split("image=data:image/svg+xml,")[1].split(";")[0]
    assert payload and ";" not in payload
