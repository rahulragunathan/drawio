# Contributing / maintaining this plugin

The maintainer loop for the `drawio` plugin and its `create-diagram` skill — how to refine it
and release it. It is not user-facing; [SKILL.md](../skills/create-diagram/SKILL.md) is the
reference for *using* the skill, [ARCHITECTURE.md](ARCHITECTURE.md) explains how
the code fits together, and [AGENTS.md](../AGENTS.md) holds the invariants and
the decisions already settled.

## Two separate things: refining vs. installing

These are independent, and conflating them wastes time:

- **Working copy** — a checkout of this repository. Refinement (editing Python, running tests,
  the validator, the preview) happens here; you are running Python against a folder.
- **Installed plugin** — what Claude invokes (`/drawio:create-diagram`). It comes from this
  repository's `main` through the marketplace on your claude.ai account, and updates itself
  after a release.

**Editing the working copy does not update the installed plugin.** A release does. To try
unreleased skill text in one Claude Code session, load the checkout directly:
`claude --plugin-dir <checkout>`.

## The refine loop

From the repository root:

```bash
.venv/bin/python -m pytest                         # all checks 
python skills/create-diagram/examples/build_three_tier_web.py   # build the example
python skills/create-diagram/scripts/validate.py three-tier-web.drawio   # must be 0 violations
python skills/create-diagram/scripts/preview.py three-tier-web.drawio    # inline visual (matplotlib)
```

**Validation gate:** never consider a change to `validate.py`, the
helpers, or an example done until `pytest` is green *and* the example re-builds
and validates with zero violations. `test_three_tier_example_validates_clean`
and `test_aws_vpc_pipeline_example_validates_clean` enforce the latter, but run
the build directly too when you touch geometry.

## End of a phase

```bash
python docs/build_architecture.py    # only if the module structure changed
python tools/render_examples.py      # renders/ — reviewed for sign-off
```

`render_examples.py` rebuilds every `examples/build_*.py` in the skill, validates each result,
and writes `renders/<diagram>-light.png` and `-dark.png`. **These PNGs are what
gets reviewed for sign-off**, so regenerate them as the last step of a phase — a
stale render is worse than none, because it is reviewed as if it were current.
The same applies to `docs/architecture.png`: regenerate, validate and re-render
it whenever the module structure moves.

Three things worth knowing:

- **Both themes, every time.** The skill authors one colour per thing and
  draw.io inverts them on export, so its choices show up only in a dark render.
  A light-only review misses them.
- **A diagram with violations is reported and not rendered.** Reviewing a
  picture of a layout the validator already rejected wastes the review.
- **A clean validate is not the bar.** Every genuinely interesting defect found
  in this project was found by looking at a render, not by a check.

Also update the roadmap files: [ROADMAP.md](ROADMAP.md) is the index, with the
detail in [KNOWN_ISSUES.md](KNOWN_ISSUES.md), [ENHANCEMENTS.md](ENHANCEMENTS.md)
and [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md). Completed work is deleted from those
and written into [CHANGELOG.md](../CHANGELOG.md) — moved, never copied.

## Releasing

**Bump the version first.** Update `version` in `.claude-plugin/plugin.json` and add a matching
`CHANGELOG.md` entry; `tests/test_plugin.py` checks they agree. The plugin updates on every
machine only when that version changes, so a release that forgets the bump reaches no one. Use
semver: patch for tuning, fixes and docs; minor for new checks or helpers; major for a break in
the conventions, helper signatures, the CLI, or the skill's name.

A release is a merge to `main`. The claude.ai marketplace syncs from it, and each signed-in
session picks the new version up. Check `claude plugin validate .claude-plugin/plugin.json`
passes before merging.

## Environment notes (esp. in a Cowork / VM sandbox)

- `preview.py` needs `matplotlib` (`pip install matplotlib`). It renders
  the exact geometry the validator sees, so it is reliable for routing, lane
  spacing and label placement.
- `preview.py` does **not** wrap box text the way draw.io does. Long box
  descriptions overflow in the preview but wrap fine in real draw.io. Do not trim
  box text on a preview overflow alone — size the box for the wrapped text
  (≈ `width / 6` chars per line at fontSize 10–11) instead.
- `render_png.py` needs the draw.io Desktop CLI on `PATH`, or the macOS
  app bundle at `/Applications/draw.io.app`, which it detects on its own. Inside
  an isolated VM (Cowork runs shell and code in a VM separate from the host OS)
  the host-installed `drawio` binary is typically not reachable, so
  `render_png.py` reports "drawio CLI not found." Use `preview.py` for inline
  checks and open the `.drawio` in draw.io Desktop on the host for
  pixel-accurate output.

## Tunable knobs

Geometric thresholds (interior buffer, orthogonal tolerance, minimum overlap
length, title-band height, label-width estimation) are documented module
constants at the top of `skills/create-diagram/scripts/validate.py`. Tune there in one place; the
function signatures default to them.

## The icon catalog

`skills/create-diagram/references/icons.md` is both the model-facing catalog and the machine-readable
source: `list_icons.py` parses its tables, so there is no second copy to drift.
`skills/create-diagram/assets/icon_names.txt.gz` is generated — every name draw.io ships — and is what
`UNKNOWN_ICON` validates against.

```bash
python skills/create-diagram/scripts/list_icons.py --search redis   # find a key (no draw.io needed)
python skills/create-diagram/scripts/list_icons.py --verify         # catalog vs the installed draw.io
python skills/create-diagram/scripts/list_icons.py --refresh        # regenerate icon_names.txt.gz
```

Only `--verify`, `--refresh` and `--dump-names` need draw.io installed. `--refresh` writes
only inside a git checkout, since an installed copy is replaced on the next sync. The generated
file is written with `mtime=0`, so an unchanged refresh leaves it byte-identical instead of
writing a fresh binary blob.

The three extraction traps that produce a plausible-but-wrong result are in
[AGENTS.md](../AGENTS.md) — read them before touching the extractor.

## Git

Maintainer commits, pushes and merges manually. Tooling here never touches git —
it edits files in place; you review and commit.
