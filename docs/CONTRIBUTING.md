# Contributing / maintaining this skill

The maintainer loop for the `drawio` skill — how to refine it and get the
changes back into Claude. It is not user-facing; [SKILL.md](../SKILL.md) is the
reference for *using* the skill, [ARCHITECTURE.md](ARCHITECTURE.md) explains how
the code fits together, and [CLAUDE.md](../CLAUDE.md) holds the invariants and
the decisions already settled.

## Two separate things: refining vs. installing

These are independent, and conflating them wastes time:

- **Working copy** — this folder, in a directory you edit and commit. Refinement
  (editing Python, running tests, the validator, the preview) happens here. The
  skill does not need to be "installed" for that; you are running Python against
  a folder.
- **Installed skill** — what Claude invokes (auto-loads `SKILL.md`, or `/drawio`
  in Cowork). Installed by uploading a packaged archive through the UI.

**Editing the working copy does not update the installed skill.** Re-package and
re-upload to refresh it. Pure development needs only the folder.

## The refine loop

From the skill root:

```bash
.venv/bin/python -m pytest                         # all checks (94 tests)
python examples/build_three_tier_web.py            # build the example
python scripts/validate.py three-tier-web.drawio   # must be 0 violations
python scripts/preview.py three-tier-web.drawio    # inline visual (matplotlib)
```

**Validation gate:** never consider a change to `scripts/validate.py`, the
helpers, or an example done until `pytest` is green *and* the example re-builds
and validates with zero violations. `test_three_tier_example_validates_clean`
and `test_aws_vpc_pipeline_example_validates_clean` enforce the latter, but run
the build directly too when you touch geometry.

## End of a phase

```bash
python docs/build_architecture.py    # only if the module structure changed
python scripts/render_examples.py    # renders/ — reviewed for sign-off
python scripts/package_skill.py      # ../drawio.skill — the uploadable archive
```

`render_examples.py` rebuilds every `examples/build_*.py`, validates each result,
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

## Packaging

**Bump the version first.** Update `version:` in `SKILL.md`'s frontmatter and add
a matching `CHANGELOG.md` entry. The Customize → Skills UI reads the displayed
version from that frontmatter field — not from the archive filename and not from
the CHANGELOG — so an upload that is really new will otherwise show the old
version. Use semver: patch for tuning, fixes and docs; minor for new checks or
helpers; major for a break in the conventions, helper signatures, or CLI.

```bash
python scripts/package_skill.py     # writes ../drawio.skill
```

It writes beside the skill folder, not inside it, so the archive never contains a
stale copy of itself. It excludes every hidden entry by rule rather than by name
— `.git`, `.venv`, `.gitignore`, `.DS_Store` and the tool caches have all leaked
into hand-built archives before — along with `renders/`, `docs/` and
`__pycache__`.

**Do not build the zip by hand.** The exclusion list is the part that goes wrong,
and `tests/test_package_skill.py` asserts the result's shape rather than that the
command ran.

**Filename: always the canonical `drawio.skill`.** No version in the filename —
the version lives in the frontmatter, and versioned filenames just produce a pile
of stale archives. Overwrite the same file each release.

`.skill` and `.zip` are interchangeable in contents; if an upload picker rejects
`.skill`, rename to `.zip`.

## Installing / refreshing in Cowork

Install through the UI, not by copying the folder to `~/.claude/skills/`:

1. Customize (left sidebar) → Skills tab → upload the packaged archive.
2. Toggle the skill on.
3. Ensure **Code execution and file creation** is enabled — the scripts need it.
4. Invoke with `/drawio`, or let Claude auto-load it from the description.

As of mid-2026 there was a reported issue where Cowork loaded only skills
installed through the Customize UI and ignored folders copied into
`~/.claude/skills/`. Prefer the UI upload until you have confirmed the file-copy
path works in your version. Claude Code, by contrast, does watch
`~/.claude/skills/` and reloads on change.

To refresh after refining: re-package, then re-upload via Customize → Skills,
replacing the previous version.

## Environment notes (esp. in a Cowork / VM sandbox)

- `scripts/preview.py` needs `matplotlib` (`pip install matplotlib`). It renders
  the exact geometry the validator sees, so it is reliable for routing, lane
  spacing and label placement.
- `preview.py` does **not** wrap box text the way draw.io does. Long box
  descriptions overflow in the preview but wrap fine in real draw.io. Do not trim
  box text on a preview overflow alone — size the box for the wrapped text
  (≈ `width / 6` chars per line at fontSize 10–11) instead.
- `scripts/render_png.py` needs the draw.io Desktop CLI on `PATH`, or the macOS
  app bundle at `/Applications/draw.io.app`, which it detects on its own. Inside
  an isolated VM (Cowork runs shell and code in a VM separate from the host OS)
  the host-installed `drawio` binary is typically not reachable, so
  `render_png.py` reports "drawio CLI not found." Use `preview.py` for inline
  checks and open the `.drawio` in draw.io Desktop on the host for
  pixel-accurate output.

## Tunable knobs

Geometric thresholds (interior buffer, orthogonal tolerance, minimum overlap
length, title-band height, label-width estimation) are documented module
constants at the top of `scripts/validate.py`. Tune there in one place; the
function signatures default to them.

## The icon catalog

`references/icons.md` is both the model-facing catalog and the machine-readable
source: `list_icons.py` parses its tables, so there is no second copy to drift.
`assets/icon_names.txt.gz` is generated — every name draw.io ships — and is what
`UNKNOWN_ICON` validates against.

```bash
python scripts/list_icons.py --search redis   # find a key (no draw.io needed)
python scripts/list_icons.py --verify         # catalog vs the installed draw.io
python scripts/list_icons.py --refresh        # regenerate icon_names.txt.gz
```

Only `--verify`, `--refresh` and `--dump-names` need draw.io installed. The
generated file is written with `mtime=0`, so an unchanged refresh leaves it
byte-identical instead of writing a fresh binary blob.

The three extraction traps that produce a plausible-but-wrong result are in
[CLAUDE.md](../CLAUDE.md) — read them before touching the extractor.

## Git

Maintainer commits, pushes and merges manually. Tooling here never touches git —
it edits files in place; you review and commit.
