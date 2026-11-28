#!/usr/bin/env python3
"""Render .drawio files to .png using the drawio Desktop CLI.

The drawio CLI ships with drawio Desktop
(https://github.com/jgraph/drawio-desktop/releases). After installing,
the `drawio` binary must be on PATH. On macOS the app bundle's binary
at /Applications/draw.io.app/Contents/MacOS/draw.io is auto-detected.

Usage:
    python render_png.py <file1.drawio> [file2.drawio ...]
    python render_png.py            # renders every .drawio in cwd
    python render_png.py <file.drawio> -o <path.png>

Output: <name>.png next to each .drawio file — the .drawio extension is
replaced, not appended, so `foo.drawio` renders to `foo.png` (drawio
Desktop itself would write `foo.drawio.png`, which needed a follow-up
`mv` on every invocation).

`-o` / `--output` overrides that destination — for repos that keep
diagram sources and rendered PNGs in different directories. It names ONE
file, so it takes exactly one input .drawio (missing parent directories
are created).
"""

import shutil
import subprocess
import sys
from pathlib import Path


CLI_CANDIDATES = ["drawio", "draw.io", "drawio-desktop"]


def find_drawio_cli() -> str | None:
    for name in CLI_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    mac_path = Path("/Applications/draw.io.app/Contents/MacOS/draw.io")
    if mac_path.exists():
        return str(mac_path)
    return None


USAGE = """Usage:
    python render_png.py <file.drawio> [more.drawio ...]
    python render_png.py                          # every .drawio in cwd
    python render_png.py <file.drawio> -o <path.png>
    python render_png.py <file.drawio> --theme dark   # dark, light, auto"""


# draw.io's own set. "auto" leaves an SVG adaptive and renders raster
# formats light.
THEMES = ("dark", "light", "auto")


def parse_args(argv: list[str]) -> tuple[list[str], Path | None, str | None]:
    """Split argv into input paths, an optional output path, and a theme.

    Raises ValueError with an actionable message on a malformed or
    ambiguous invocation. Kept separate from main() so the argument
    contract is testable without the drawio CLI installed.
    """
    paths: list[str] = []
    out_path: Path | None = None
    theme: str | None = None

    def set_theme(value: str):
        nonlocal theme
        if value not in THEMES:
            raise ValueError(
                f"unknown theme {value!r}; expected one of {', '.join(THEMES)}"
            )
        theme = value

    def set_output(value: str):
        nonlocal out_path
        if out_path is not None:
            raise ValueError("--output given more than once")
        if not value:
            raise ValueError("--output needs a file path")
        out_path = Path(value)

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("-o", "--output"):
            if i + 1 >= len(argv):
                raise ValueError("--output needs a file path")
            set_output(argv[i + 1])
            i += 2
        elif arg.startswith("--output="):
            set_output(arg.split("=", 1)[1])
            i += 1
        elif arg == "--theme":
            if i + 1 >= len(argv):
                raise ValueError(f"--theme needs one of {', '.join(THEMES)}")
            set_theme(argv[i + 1])
            i += 2
        elif arg.startswith("--theme="):
            set_theme(arg.split("=", 1)[1])
            i += 1
        elif arg.startswith("-"):
            raise ValueError(f"unknown option {arg!r}")
        else:
            paths.append(arg)
            i += 1

    # --output names a single destination file. Allowing it alongside
    # several inputs (or the glob-the-cwd default) would render each
    # diagram over the last one and silently leave only the final file.
    if out_path is not None and len(paths) != 1:
        raise ValueError(
            f"--output names one destination file, so it needs exactly one "
            f"input .drawio (got {len(paths)})"
        )
    return paths, out_path, theme


def render(
    drawio_path: Path,
    cli: str,
    out_path: Path | None = None,
    theme: str | None = None,
) -> bool:
    # Default: replace the .drawio extension rather than appending to it —
    # drawio Desktop would write foo.drawio.png, which needed a follow-up
    # `mv` on every invocation and leaked double extensions into commits.
    out_path = Path(out_path) if out_path else drawio_path.with_suffix(".png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        cli,
        "--export",
        "--format",
        "png",
        "--output",
        str(out_path),
    ]
    if theme:
        cmd += ["--theme", theme]
    cmd.append(str(drawio_path))
    print(f"  → {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    FAILED: {result.stderr.strip() or result.stdout.strip()}")
        return False
    print(f"    Wrote {out_path}")
    return True


def main():
    try:
        args, out_path, theme = parse_args(sys.argv[1:])
    except ValueError as exc:
        print(f"ERROR: {exc}\n")
        print(USAGE)
        sys.exit(2)
    if not args:
        args = sorted(str(p) for p in Path(".").glob("*.drawio"))
        if not args:
            print(USAGE)
            sys.exit(2)
    cli = find_drawio_cli()
    if cli is None:
        print("ERROR: drawio CLI not found on PATH.")
        print("Install from: https://github.com/jgraph/drawio-desktop/releases")
        sys.exit(1)
    print(f"Using drawio CLI: {cli}\n")

    ok = 0
    for path_str in args:
        p = Path(path_str)
        if not p.exists():
            print(f"  ! Skip (not found): {p}")
            continue
        print(f"Rendering {p}")
        # out_path is only ever set for a single input (parse_args enforces).
        if render(p, cli, out_path, theme):
            ok += 1
    print(f"\n{ok}/{len(args)} rendered.")
    sys.exit(0 if ok == len(args) else 1)


if __name__ == "__main__":
    main()
