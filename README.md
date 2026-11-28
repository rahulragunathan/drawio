# drawio plugin

A Claude Code plugin whose `create-diagram` skill generates draw.io architecture diagrams with explicit,
validated routing — and, optionally, real vendor logos.

Auto-layout tools route for you and lose the things that make a dense diagram
readable: reserved corridors, source-coloured arrows, label positions that
survive a round-trip. The skill makes you write the coordinates, then checks
the result geometrically, so arrows do not cross boxes and labels do not sit on
top of each other.

The full reference is in [`skills/create-diagram/SKILL.md`](skills/create-diagram/SKILL.md).
This README is a 30-second tour.

## Install

Add the marketplace on your claude.ai account: Customize → Plugins → Add marketplace,
`rahulragunathan/drawio`, with **Sync automatically** on. Then install `drawio`. It reaches
Claude Code, Cowork and cloud sessions, loads as `/drawio:create-diagram`, and updates itself
after each release.

Without a claude.ai account (an API key setup), use the command line, then turn auto-update
on for the marketplace in `/plugin`:

```bash
claude plugin marketplace add rahulragunathan/drawio
claude plugin install drawio@drawio
```

## Layout

```text
drawio/
├── .claude-plugin/
│   ├── plugin.json                   ← The plugin, and the one version source
│   └── marketplace.json              ← This repo as a one-plugin marketplace
├── skills/create-diagram/            ← The skill that installs
│   ├── SKILL.md                      ← Read this first
│   ├── scripts/
│   │   ├── validate.py               ← Geometric validator (9 checks)
│   │   ├── preview.py                ← Offline matplotlib preview (no CLI needed)
│   │   ├── render_png.py             ← drawio Desktop CLI wrapper (pixel-accurate)
│   │   └── list_icons.py             ← Search the icon catalog; refresh it in a checkout
│   ├── assets/
│   │   ├── build_template.py         ← Minimal starter to copy
│   │   └── icon_names.txt.gz         ← Every icon name draw.io ships (generated)
│   ├── references/
│   │   └── icons.md                  ← 128 curated vendor icons, with brand colours
│   └── examples/
│       ├── build_three_tier_web.py   ← Worked example, validates clean
│       ├── build_aws_vpc_pipeline.py ← Worked example with vendor icons
│       └── snowflake.svg             ← A logo draw.io does not ship
├── tools/
│   └── render_examples.py            ← Rebuild every example → renders/, light + dark
├── README.md · AGENTS.md · CHANGELOG.md · LICENSE
├── pytest.ini · ruff.toml · requirements*.txt
├── renders/                          ← Current PNGs of both examples, light + dark
├── docs/                             ← Maintainer docs
│   ├── ARCHITECTURE.md               ← How the pieces fit, with a generated diagram
│   ├── build_architecture.py         ← Its generator; source + render sit beside it
│   ├── CONTRIBUTING.md               ← Maintainer loop (refine / release)
│   ├── PHASE_RECORD.md               ← The phase in flight
│   ├── ROADMAP.md                    ← What is still open (index)
│   └── KNOWN_ISSUES.md · ENHANCEMENTS.md · OPEN_QUESTIONS.md
└── tests/
    ├── test_validate.py              ← One test per validator check
    ├── test_plugin.py                ← Manifests, layout, skill-folder paths
    ├── test_icons.py · test_list_icons.py · test_preview.py
    ├── test_render_png.py · test_render_examples.py
    └── fixtures/
        └── builders.py               ← Minimal fixture generators
```

## Quick start

```bash
# From a checkout: build a bundled example and validate it.
python skills/create-diagram/examples/build_aws_vpc_pipeline.py
python skills/create-diagram/scripts/validate.py aws-vpc-pipeline.drawio

# Open the result at https://app.diagrams.net (no auth) or in draw.io Desktop.

# Run the test suite.
python -m pytest
```

## Authoring your own diagram

In a session, `/drawio:create-diagram` does this for you. By hand, from a checkout:

```bash
cp skills/create-diagram/assets/build_template.py my-diagram.py
# Edit the constants, containers, boxes, and edges.
python skills/create-diagram/scripts/list_icons.py --search lambda    # find a vendor icon, if you want one
python my-diagram.py
python skills/create-diagram/scripts/validate.py my-diagram.drawio
python skills/create-diagram/scripts/render_png.py my-diagram.drawio  # → my-diagram.png; then look at it
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
are documented in the skill's `SKILL.md`.

## Icons

Diagrams can carry real vendor logos from draw.io's own stencil library — AWS,
Azure, GCP, Kubernetes, Cisco — or any logo you supply as an SVG. No download
and no draw.io install is needed to *generate* a diagram: the artwork lives in
draw.io itself, and the names it accepts ship with the skill in
`skills/create-diagram/assets/icon_names.txt.gz`, extracted from a draw.io Desktop build (Apache-2.0).
No draw.io artwork is redistributed here.

## Licence

MIT — see [LICENSE](LICENSE).

`skills/create-diagram/assets/icon_names.txt.gz` is a list of icon *names* extracted from a draw.io
Desktop build ([drawio-desktop](https://github.com/jgraph/drawio-desktop),
Apache-2.0). It contains no draw.io artwork: the skill references stencils by
name and draw.io draws them. The one embedded logo, `skills/create-diagram/examples/snowflake.svg`,
was drawn for the example.
