# drawio skill

A Claude skill for generating draw.io architecture diagrams with explicit,
validated routing — and, optionally, real vendor logos.

Auto-layout tools route for you and lose the things that make a dense diagram
readable: reserved corridors, source-coloured arrows, label positions that
survive a round-trip. This skill makes you write the coordinates, then checks
the result geometrically, so arrows do not cross boxes and labels do not sit on
top of each other.

The full reference is in `SKILL.md`. This README is a 30-second tour.

## Layout

```
drawio/
├── SKILL.md                          ← Read this first
├── README.md                         ← This file
├── CLAUDE.md                         ← Repo conventions and settled decisions
├── CHANGELOG.md                      ← Version history
├── LICENSE                           ← MIT
├── pytest.ini · ruff.toml · requirements*.txt
├── scripts/
│   ├── validate.py                   ← Geometric validator (9 checks)
│   ├── preview.py                    ← Offline matplotlib preview (no CLI needed)
│   ├── render_png.py                 ← drawio Desktop CLI wrapper (pixel-accurate)
│   ├── render_examples.py            ← Rebuild every example → renders/, light + dark
│   ├── package_skill.py              ← Build the uploadable ../drawio.skill
│   └── list_icons.py                 ← Browse / verify / refresh the icon catalog
├── assets/
│   ├── build_template.py             ← Minimal starter to copy
│   └── icon_names.txt.gz             ← Every icon name draw.io ships (generated)
├── references/
│   └── icons.md                      ← 128 curated vendor icons, with brand colours
├── examples/
│   ├── build_three_tier_web.py       ← Worked example, validates clean
│   ├── build_aws_vpc_pipeline.py     ← Worked example with vendor icons
│   └── snowflake.svg                 ← A logo draw.io does not ship
├── renders/                          ← Current PNGs of both examples, light + dark
├── docs/                             ← Maintainer docs; not shipped in the package
│   ├── ARCHITECTURE.md               ← How the pieces fit, with a generated diagram
│   ├── CONTRIBUTING.md               ← Maintainer loop (refine / package / install)
│   ├── ROADMAP.md                    ← What is still open (index)
│   └── KNOWN_ISSUES.md · ENHANCEMENTS.md · OPEN_QUESTIONS.md
└── tests/
    ├── test_validate.py              ← One test per validator check
    ├── test_icons.py · test_list_icons.py · test_preview.py
    ├── test_render_png.py · test_render_examples.py · test_package_skill.py
    └── fixtures/
        └── builders.py               ← Minimal fixture generators
```

## Quick start

```bash
# Build a bundled example and validate it.
python examples/build_aws_vpc_pipeline.py
python scripts/validate.py aws-vpc-pipeline.drawio

# Open the result at https://app.diagrams.net (no auth) or in draw.io Desktop.

# Run the test suite.
python -m pytest
```

## Authoring your own diagram

```bash
cp assets/build_template.py my-diagram.py
# Edit the constants, containers, boxes, and edges.
python scripts/list_icons.py --search lambda    # find a vendor icon, if you want one
python my-diagram.py
python scripts/validate.py my-diagram.drawio
python scripts/render_png.py my-diagram.drawio  # → my-diagram.png; then look at it
```

That last step is not optional. A clean validate says nothing about whether a
label has room, whether an icon rendered at all, or whether the diagram reads —
every interesting defect found while building this skill was found by looking at
a render, not by a check.

## What the validator checks

Nine checks: CROSSING, OVERLAP, TEXT_OVERLAP, LABEL_OVERLAP, LABEL_BOX_OVERLAP,
SHORT_LABELLED_EDGE, DIAGONAL, DANGLING, UNKNOWN_ICON. Errors fail the build;
warnings are advisory. These, and the locked conventions for arrow colour,
label casing and stacking, corridor reservation, icons and future-state styling,
are documented in `SKILL.md`.

## Icons

Diagrams can carry real vendor logos from draw.io's own stencil library — AWS,
Azure, GCP, Kubernetes, Cisco — or any logo you supply as an SVG. No download
and no draw.io install is needed to *generate* a diagram: the artwork lives in
draw.io itself, and the names it accepts ship with this skill in
`assets/icon_names.txt.gz`, extracted from a draw.io Desktop build (Apache-2.0).
No draw.io artwork is redistributed here.

## Licence

MIT — see [LICENSE](LICENSE).

`assets/icon_names.txt.gz` is a list of icon *names* extracted from a draw.io
Desktop build ([drawio-desktop](https://github.com/jgraph/drawio-desktop),
Apache-2.0). It contains no draw.io artwork: the skill references stencils by
name and draw.io draws them. The one embedded logo, `examples/snowflake.svg`,
was drawn for the example.
