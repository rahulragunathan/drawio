"""Tests for scripts/list_icons.py.

The asar reader is exercised against a synthetic archive built in tmp_path,
not against the 147 MB draw.io bundle: the format is what needs pinning down,
and a real install must never be a precondition for the suite. The
install-dependent CLI modes are tested only for their graceful-degradation
path, which is the behaviour that matters on a machine without draw.io.
"""

import json
import struct
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import list_icons  # noqa: E402


def _build_asar(path: Path, files: dict[str, bytes]) -> Path:
    """Write a minimal but format-faithful Electron asar archive.

    Four little-endian uint32 fields, then the JSON directory padded to a
    4-byte boundary, then the concatenated file data. The padding is the
    part that matters: the data section starts at 8 + field1, NOT at
    16 + json_length, and getting that wrong shifts every file by a few
    bytes (see the reader's docstring).
    """
    blob = b""
    tree: dict = {"files": {}}
    for name, data in files.items():
        node = tree
        parts = name.split("/")
        for part in parts[:-1]:
            node = node["files"].setdefault(part, {"files": {}})
        node["files"][parts[-1]] = {"size": len(data), "offset": str(len(blob))}
        blob += data

    js = json.dumps(tree).encode("utf8")
    pad = (4 - len(js) % 4) % 4
    padded = len(js) + pad
    header = struct.pack("<IIII", 4, 8 + padded, 4 + padded, len(js))
    path.write_bytes(header + js + b"\0" * pad + blob)
    return path


def test_asar_reader_reads_file_contents_at_the_correct_offset(tmp_path):
    # Deliberately sized so the JSON directory needs padding: an off-by-three
    # base offset would return the tail of the previous file.
    archive = _build_asar(
        tmp_path / "test.asar",
        {
            "a/first.xml": b"<shapes name='lib'><shape name='One'/></shapes>",
            "a/b/second.svg": b"<svg>second</svg>",
            "third.js": b'var x = "mxgraph.aws4.resourceIcon";',
        },
    )

    entries = list_icons.read_asar(archive)

    assert set(entries) == {"a/first.xml", "a/b/second.svg", "third.js"}
    assert entries["a/b/second.svg"]() == b"<svg>second</svg>"
    assert entries["third.js"]() == b'var x = "mxgraph.aws4.resourceIcon";'


def test_stencil_names_are_qualified_lowercased_and_underscored(tmp_path):
    archive = _build_asar(
        tmp_path / "s.asar",
        {
            "drawio/src/main/webapp/stencils/aws4.xml": (
                b'<shapes name="mxgraph.aws4">'
                b'<shape name="Lambda"/><shape name="API Gateway"/>'
                b"</shapes>"
            ),
        },
    )

    names = list_icons.stencil_names(list_icons.read_asar(archive))

    assert names == {"mxgraph.aws4.lambda", "mxgraph.aws4.api_gateway"}


def test_js_shape_names_catch_wrappers_absent_from_the_stencil_xml(tmp_path):
    # resourceIcon and icon2 are registered in JavaScript, not declared in any
    # stencil file. Miss them and the validator warns on every AWS and
    # Kubernetes icon, which is the failure this sweep exists to prevent.
    archive = _build_asar(
        tmp_path / "j.asar",
        {
            "drawio/src/main/webapp/js/app.min.js": (
                b"mxShapeAws4ResourceIcon.prototype.cst="
                b'{RESOURCE_ICON:"mxgraph.aws4.resourceIcon"};'
                b"x(\"mxgraph.kubernetes.icon2\");y('mxgraph.gcp2.hexIcon');"
                b'var notashape="mxgraph.aws4";'
            ),
        },
    )

    names = list_icons.js_shape_names(list_icons.read_asar(archive))

    assert "mxgraph.aws4.resourceIcon" in names
    assert "mxgraph.kubernetes.icon2" in names
    assert "mxgraph.gcp2.hexIcon" in names
    # A bare library name is not a shape reference.
    assert "mxgraph.aws4" not in names


def test_image_names_are_relative_to_the_webapp_root(tmp_path):
    webapp = "drawio/src/main/webapp/"
    archive = _build_asar(
        tmp_path / "i.asar",
        {
            webapp + "img/lib/azure2/compute/Function_Apps.svg": b"<svg/>",
            webapp + "images/drawlogo.svg": b"<svg/>",
        },
    )

    names = list_icons.image_names(list_icons.read_asar(archive))

    # Style strings say image=img/lib/..., so that is what must be stored.
    assert names == {"img/lib/azure2/compute/Function_Apps.svg"}


def test_refresh_without_drawio_exits_two_and_names_the_path(
    tmp_path, capsys, monkeypatch
):
    missing = tmp_path / "nowhere" / "draw.io.app"
    monkeypatch.setenv("DRAWIO_APP", str(missing))

    code = list_icons.main(["--refresh"])

    out = capsys.readouterr().out + capsys.readouterr().err
    assert code == 2
    assert str(missing) in out
    # The message must say the skill still works without the app, or a reader
    # reasonably concludes the install is a prerequisite.
    assert "does not need" in out.lower() or "never needs" in out.lower()


def test_search_works_without_drawio_installed(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("DRAWIO_APP", str(tmp_path / "nowhere"))

    code = list_icons.main(["--search", "lambda"])

    assert code == 0
    assert "aws-lambda" in capsys.readouterr().out


def test_a_flag_missing_its_value_reports_usage(capsys):
    # Indexing one past the flag with no bounds check gives an IndexError
    # traceback, which tells the reader nothing about what they typed wrong.
    code = list_icons.main(["--search"])

    assert code == 2
    assert "--search" in capsys.readouterr().out
