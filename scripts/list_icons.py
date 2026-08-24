#!/usr/bin/env python3
"""Icon catalog tooling for the drawio skill.

Reads the stencil and image names that draw.io ships, so the validator can
tell a typo'd shape name from a real one. Stdlib only, like the rest of the
skill.

Nothing in the skill's normal workflow needs this script or a draw.io
install: the generated name list is committed under assets/. This tool
exists to regenerate that list against a newer draw.io release.
"""

from __future__ import annotations

import json
import re
import struct
from collections.abc import Callable
from pathlib import Path


def read_asar(path: Path) -> dict[str, Callable[[], bytes]]:
    """Enumerate an Electron asar archive as {path: read_bytes_callable}.

    draw.io ships its whole webapp — stencils, icons, JS — in one asar. The
    format is a Chromium Pickle header followed by a JSON directory and then
    the concatenated file data:

        uint32  always 4 (size of the next field)
        uint32  size of the rest of the pickle
        uint32  size of the JSON string pickle
        uint32  length of the JSON string
        <JSON directory, padded to a 4-byte boundary>
        <file data>

    The data section starts at ``8 + field1``. It does NOT start at
    ``16 + json_length``: the JSON is padded for alignment, so that formula
    lands up to three bytes early and shifts every single file read. The
    corruption is easy to miss because it damages only the head of each
    file, which regex-based scanning tolerates.

    Values are callables so that enumerating an archive stays cheap; a
    147 MB bundle is not read into memory to answer "which files exist".
    """
    with open(path, "rb") as fh:
        _, rest_of_pickle, _, json_len = struct.unpack("<IIII", fh.read(16))
        directory = json.loads(fh.read(json_len).decode("utf8"))
    data_base = 8 + rest_of_pickle

    entries: dict[str, Callable[[], bytes]] = {}

    def _walk(node: dict, prefix: str = "") -> None:
        for name, meta in node.get("files", {}).items():
            if "files" in meta:
                _walk(meta, prefix + name + "/")
            else:
                offset = data_base + int(meta["offset"])
                size = int(meta["size"])
                entries[prefix + name] = _reader(path, offset, size)

    _walk(directory)
    return entries


def _reader(archive: Path, offset: int, size: int) -> Callable[[], bytes]:
    """Bind one file's location into a zero-argument reader."""

    def read() -> bytes:
        with open(archive, "rb") as fh:
            fh.seek(offset)
            return fh.read(size)

    return read


# draw.io's webapp is nested inside the archive; style strings reference
# assets relative to the webapp root, so this prefix is stripped when
# emitting image names. Filtering on the style-relative path instead
# silently matches nothing.
WEBAPP_PREFIX = "drawio/src/main/webapp/"

_SHAPES_LIB_RE = re.compile(rb'<shapes[^>]*\sname="([^"]+)"')
_SHAPE_NAME_RE = re.compile(rb'<shape[^>]*\sname="([^"]+)"')


def stencil_names(entries: dict[str, Callable[[], bytes]]) -> set[str]:
    """Shape names defined in the bundled stencil XML.

    Each stencil file declares a library (``<shapes name="mxgraph.aws4">``)
    and its shapes. draw.io matches shape names case-insensitively with
    spaces normalised to underscores, so "API Gateway" is referenced in a
    style as ``mxgraph.aws4.api_gateway``; the names are normalised here to
    match what a style string actually carries.
    """
    names: set[str] = set()
    for path, read in entries.items():
        if "/stencils/" not in path or not path.endswith(".xml"):
            continue
        blob = read()
        lib_match = _SHAPES_LIB_RE.search(blob)
        if lib_match is None:
            continue
        library = lib_match.group(1).decode("utf8", "replace")
        for raw in _SHAPE_NAME_RE.findall(blob):
            shape = raw.decode("utf8", "replace")
            if shape == library:
                continue
            names.add(f"{library}.{shape.lower().replace(' ', '_')}")
    return names


# A shape reference is always library-qualified: at least one dot after the
# "mxgraph." prefix. Requiring that trailing segment keeps bare library names
# out of the set.
_JS_SHAPE_RE = re.compile(rb'["\'](mxgraph\.[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+)["\']')


def js_shape_names(entries: dict[str, Callable[[], bytes]]) -> set[str]:
    """Shape names registered in draw.io's JavaScript rather than in a stencil.

    The wrapper shapes that carry vendor icons — mxgraph.aws4.resourceIcon,
    mxgraph.kubernetes.icon2, mxgraph.gcp2.hexIcon — are defined in code and
    appear in no stencil XML. They are registered via prototype constants, so
    a `registerShape("...")` pattern misses them; sweeping every quoted
    mxgraph literal is what actually finds them.

    Omitting this source makes UNKNOWN_ICON fire on every AWS and Kubernetes
    icon the skill emits.
    """
    names: set[str] = set()
    for path, read in entries.items():
        if not path.endswith(".js"):
            continue
        for raw in _JS_SHAPE_RE.findall(read()):
            names.add(raw.decode("utf8", "replace"))
    return names


def image_names(entries: dict[str, Callable[[], bytes]]) -> set[str]:
    """Bundled icon image paths, as a style string references them.

    Modern Azure, mscae, ibm and sap are not stencils at all: draw.io builds
    those palettes from SVG files and the style carries a relative path
    (image=img/lib/azure2/...). Only img/lib is icon artwork; the webapp's
    own chrome images are not addressable this way.
    """
    prefix = WEBAPP_PREFIX + "img/lib/"
    return {
        path[len(WEBAPP_PREFIX) :]
        for path in entries
        if path.startswith(prefix) and path.endswith(".svg")
    }


def all_names(entries: dict[str, Callable[[], bytes]]) -> set[str]:
    """Every legitimate icon reference draw.io can resolve.

    The union of all three sources. UNKNOWN_ICON validates against this, not
    against the curated catalog: an icon dragged from the draw.io sidebar is
    perfectly valid and must not warn just because it is not one of the ~140
    names the reference doc lists.
    """
    return stencil_names(entries) | js_shape_names(entries) | image_names(entries)


# ---------------------------------------------------------------------------
# Families. Each entry says how a catalog name becomes a style fragment.
#   kind    — "stencil" (drawing instructions in the app) or "image" (an SVG
#             file the app ships; not recolourable).
#   prefix  — what a bare catalog name is qualified with.
#   wrapper — the shape that renders the glyph, when the family uses one.
#   key     — the style key the wrapper reads the glyph name from.
#   bare    — True when that key takes an unqualified name (Kubernetes) rather
#             than a fully qualified one (AWS).
# ---------------------------------------------------------------------------
FAMILIES: dict[str, dict] = {
    "aws": {
        "kind": "stencil",
        "prefix": "mxgraph.aws4.",
        "wrapper": "mxgraph.aws4.resourceIcon",
        "key": "resIcon",
        "bare": False,
        "recolourable": False,
    },
    "gcp": {
        "kind": "stencil",
        "prefix": "mxgraph.gcp3.",
        "wrapper": None,
        "key": None,
        "bare": False,
        "recolourable": True,
    },
    "k8s": {
        "kind": "stencil",
        "prefix": "mxgraph.kubernetes.",
        "wrapper": "mxgraph.kubernetes.icon2",
        "key": "prIcon",
        "bare": True,
        "recolourable": True,
    },
    "azure": {
        "kind": "image",
        "prefix": "img/lib/azure2/",
        "wrapper": None,
        "key": None,
        "bare": False,
        "recolourable": False,
    },
    "cisco": {
        "kind": "stencil",
        "prefix": "mxgraph.cisco19.",
        "wrapper": None,
        "key": None,
        "bare": False,
        "recolourable": True,
    },
    "net": {
        "kind": "stencil",
        "prefix": "mxgraph.networks.",
        "wrapper": None,
        "key": None,
        "bare": False,
        "recolourable": True,
    },
}

SKILL_ROOT = Path(__file__).resolve().parent.parent
CATALOG_DOC = SKILL_ROOT / "references" / "icons.md"

# A catalog row: | Service | `key` | `name` | `#fill` |
_ROW_RE = re.compile(
    r"^\|[^|]*\|\s*`(?P<key>[a-z0-9]+-[a-z0-9.\-]+)`\s*"
    r"\|\s*`(?P<name>[^`]+)`\s*\|\s*(?P<fill>`#[0-9A-Fa-f]{6}`|[^|]*)\|"
)


def load_catalog(doc: Path | None = None) -> dict[str, dict]:
    """Parse the curated catalog out of references/icons.md.

    The reference doc is the single source of truth: it is what the model
    reads while authoring, so keeping a parallel machine-readable copy would
    only create two things to drift apart.
    """
    doc = doc or CATALOG_DOC
    catalog: dict[str, dict] = {}
    try:
        text = doc.read_text(encoding="utf8")
    except OSError:
        return catalog
    for line in text.splitlines():
        m = _ROW_RE.match(line.strip())
        if not m:
            continue
        key = m.group("key")
        family = key.split("-", 1)[0]
        if family not in FAMILIES:
            continue
        fill = m.group("fill").strip().strip("`")
        catalog[key] = {
            "family": family,
            "name": m.group("name").strip(),
            "fill": fill if fill.startswith("#") else None,
        }
    return catalog


def qualified_names(key: str, entry: dict) -> list[str]:
    """Every name this catalog entry puts into a style, for verification.

    A wrapper family contributes two: the wrapper shape itself and the glyph
    it renders. Both must exist or the icon renders blank.
    """
    fam = FAMILIES[entry["family"]]
    glyph = entry["name"]
    if fam["kind"] == "image":
        return [fam["prefix"] + glyph]
    qualified = glyph if "." in glyph else fam["prefix"] + glyph
    names = [qualified]
    if fam["wrapper"]:
        names.append(fam["wrapper"])
    return names


def find_asar(explicit: str | None = None) -> Path | None:
    """Locate draw.io Desktop's app.asar, or None when it is not installed."""
    import os

    env = explicit or os.environ.get("DRAWIO_APP")
    # An explicit override is authoritative. Falling back to the default
    # location when it misses would silently read a different install than
    # the caller asked for.
    candidates = [Path(env)] if env else [Path("/Applications/draw.io.app")]
    for app in candidates:
        asar = app / "Contents" / "Resources" / "app.asar"
        if asar.is_file():
            return asar
        if app.is_file() and app.suffix == ".asar":
            return app
    return None


NAMES_FILE = SKILL_ROOT / "assets" / "icon_names.txt.gz"

_NO_APP = """draw.io Desktop not found at {path}
(override the location with $DRAWIO_APP)

--verify, --dump-names and --refresh read the stencils bundled inside the
app, so they need a local install. Every other mode works without one, and
the skill itself never needs draw.io to build or validate a diagram — the
name list is committed under assets/."""


def _missing_app(explicit: str | None) -> str:
    import os

    shown = explicit or os.environ.get("DRAWIO_APP") or "/Applications/draw.io.app"
    return _NO_APP.format(path=shown)


def app_version(asar: Path) -> str:
    """Best-effort draw.io version, for the generated file's provenance line."""
    plist = asar.parent.parent / "Info.plist"
    try:
        text = plist.read_text(encoding="utf8", errors="replace")
        m = re.search(
            r"<key>CFBundleShortVersionString</key>\s*<string>([^<]+)</string>", text
        )
        if m:
            return m.group(1)
    except OSError:
        pass
    return "unknown"


def load_names() -> set[str]:
    """The committed name universe. Empty when the file is absent."""
    import gzip

    try:
        with gzip.open(NAMES_FILE, "rt", encoding="utf8") as fh:
            return {ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")}
    except OSError:
        return set()


def main(argv: list[str] | None = None) -> int:
    import gzip
    import io
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    catalog = load_catalog()

    def _need_asar() -> Path | None:
        asar = find_asar()
        if asar is None:
            print(_missing_app(None))
            return None
        return asar

    if "--search" in argv:
        term = argv[argv.index("--search") + 1].lower()
        hits = sorted(
            k for k in catalog if term in k or term in catalog[k]["name"].lower()
        )
        if not hits:
            import difflib

            hits = difflib.get_close_matches(term, sorted(catalog), n=5, cutoff=0.4)
        for key in hits:
            print(f"{key:24s} {catalog[key]['name']}")
        if not hits:
            print(f"no catalog entry matches {term!r}")
        return 0

    if "--refresh" in argv:
        asar = _need_asar()
        if asar is None:
            return 2
        entries = read_asar(asar)
        names = sorted(all_names(entries))
        version = app_version(asar)
        NAMES_FILE.parent.mkdir(parents=True, exist_ok=True)
        # mtime=0 keeps the output byte-identical when the names have not
        # changed. gzip stamps the current time by default, which would make
        # every --refresh a fresh binary diff even on an unchanged catalog.
        raw = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            fh = io.TextIOWrapper(gz, encoding="utf8")
            fh.write("# Generated by scripts/list_icons.py --refresh\n")
            fh.write(f"# Source: draw.io Desktop {version}\n")
            fh.write(
                f"# {len(names)} names: stencil shapes, JS-registered "
                f"wrappers, and bundled img/lib SVG paths.\n"
            )
            for name in names:
                fh.write(name + "\n")
            fh.flush()
            fh.detach()
        NAMES_FILE.write_bytes(raw.getvalue())
        print(
            f"wrote {NAMES_FILE.relative_to(SKILL_ROOT)} "
            f"({len(names)} names, draw.io {version})"
        )
        return 0

    if "--verify" in argv:
        asar = _need_asar()
        if asar is None:
            return 2
        entries = read_asar(asar)
        universe = all_names(entries)
        print(f"draw.io {app_version(asar)}: {len(universe)} names available")
        print(f"catalog: {len(catalog)} entries")
        missing = []
        for key, entry in sorted(catalog.items()):
            for name in qualified_names(key, entry):
                if name not in universe:
                    missing.append((key, name))
        for key, name in missing:
            print(f"  MISSING  {key:24s} -> {name}")
        print(
            "all catalog entries resolve"
            if not missing
            else f"{len(missing)} unresolved name(s)"
        )
        return 1 if missing else 0

    if "--dump-names" in argv:
        asar = _need_asar()
        if asar is None:
            return 2
        entries = read_asar(asar)
        names = sorted(all_names(entries))
        if "--family" in argv:
            fam = argv[argv.index("--family") + 1]
            prefix = FAMILIES.get(fam, {}).get("prefix", fam)
            names = [n for n in names if n.startswith(prefix)]
        print("\n".join(names))
        return 0

    positional = [a for a in argv if not a.startswith("-")]
    if positional:
        key = positional[0]
        if key not in catalog:
            import difflib

            near = difflib.get_close_matches(key, sorted(catalog), n=1, cutoff=0.6)
            print(
                f"unknown catalog key {key!r}"
                + (f" — did you mean {near[0]!r}?" if near else "")
            )
            return 1
        entry = catalog[key]
        print(f"{key}  (family {entry['family']}, fill {entry['fill'] or '-'})")
        for name in qualified_names(key, entry):
            print(f"  {name}")
        return 0

    for family in sorted(FAMILIES):
        keys = sorted(k for k in catalog if catalog[k]["family"] == family)
        if not keys:
            continue
        print(f"\n{family}  ({len(keys)})")
        for key in keys:
            print(f"  {key:24s} {catalog[key]['name']}")
    if not catalog:
        print("no catalog found at references/icons.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
