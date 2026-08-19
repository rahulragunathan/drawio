# drawio skill

A Claude skill for generating draw.io architecture diagrams with explicit, validated routing.

The full reference is in `SKILL.md`. This README is a 30-second tour.

## Layout

```
drawio/
├── SKILL.md                          ← Read this first
├── README.md                         ← This file
├── CONTRIBUTING.md                   ← Maintainer loop (refine / package / install)
├── CHANGELOG.md                      ← Version history
├── pytest.ini
├── scripts/
│   ├── validate.py                   ← Geometric validator (7 checks)
│   ├── preview.py                    ← Offline matplotlib preview (no CLI needed)
│   └── render_png.py                 ← drawio Desktop CLI wrapper (pixel-accurate)
├── assets/
│   └── build_template.py             ← Minimal starter to copy
├── examples/
│   └── build_three_tier_web.py       ← Worked example, validates clean
└── tests/
    ├── test_validate.py              ← One test per validator check
    └── fixtures/
        └── builders.py               ← Minimal fixture generators
```

## Quick start

```bash
# Build the bundled example and validate it.
python examples/build_three_tier_web.py
python scripts/validate.py three-tier-web.drawio

# Open the result at https://app.diagrams.net (no auth) or in draw.io Desktop.

# Run the test suite.
python -m pytest
```

## Authoring your own diagram

```bash
cp assets/build_template.py my-diagram.py
# Edit the constants, containers, boxes, and edges.
python my-diagram.py
python scripts/validate.py my-diagram.drawio
python scripts/render_png.py my-diagram.drawio   # → my-diagram.png; then look at it
```

The eight validator checks (CROSSING, OVERLAP, TEXT_OVERLAP, LABEL_OVERLAP, LABEL_BOX_OVERLAP, SHORT_LABELLED_EDGE, DIAGONAL, DANGLING) and the locked conventions for arrow colour, multi-line labels, corridor reservation, and future-state styling are all documented in `SKILL.md`.
