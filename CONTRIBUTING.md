# Contributing / maintaining this skill

This is the maintainer loop for the `drawio` skill — how to refine it and
get the changes back into Claude. It is not user-facing; `SKILL.md` is the
reference for *using* the skill.

## Two separate things: refining vs. installing

These are independent, and conflating them wastes time:

- **Working copy** — this folder, living in a directory you edit and commit.
  Refinement (editing Python, running tests/validator/preview) happens here.
  The skill does **not** need to be "installed" for this; you're just running
  Python against a folder.
- **Installed skill** — what Claude actually invokes (auto-loads `SKILL.md`,
  or `/drawio` in Cowork). Installed by uploading a packaged archive through
  the UI.

**Editing the working copy does not update the installed skill.** After a
change is done, you re-package and re-upload to refresh the installed copy.
Pure development needs only the folder.

## The refine loop

From the skill root:

```bash
.venv/bin/python -m pytest                         # all checks
python examples/build_three_tier_web.py            # build the example
python scripts/validate.py three-tier-web.drawio   # must be 0 violations
python scripts/preview.py three-tier-web.drawio    # inline visual (matplotlib)
```

**Validation gate:** never consider a change to `scripts/validate.py`, the
helpers, or the example "done" until `pytest` is green *and* the example
re-builds and validates with zero violations. The
`test_three_tier_example_validates_clean` test enforces the latter, but run the
build directly too when you touch geometry.

## End of a phase: regenerate the renders

```bash
python scripts/render_examples.py
```

Rebuilds every `examples/build_*.py`, validates each result, and writes
`renders/<diagram>-light.png` and `renders/<diagram>-dark.png`. **These PNGs
are what gets reviewed for sign-off**, so regenerate them as the last step of
a phase — a stale render is worse than none, because it is reviewed as if it
were current.

The renders are committed. For a diagramming skill they are the product, so
the repo records what each phase actually looked like; a diff that changes
geometry should show a changed picture.

Three things worth knowing:

- **Both themes, every time.** The skill stopped authoring dark colours in
  1.3.0, but draw.io still inverts them on export and its choices still have
  to be looked at. Light-only review misses that entirely.
- **A diagram with violations is reported and not rendered.** Reviewing a
  picture of a layout the validator already rejected wastes the review.
- **A clean validate is not the bar.** Every genuinely interesting defect
  found in this project — a blank icon plate, an arrow struck through a
  caption, unreadable dark labels — was found by looking at a render, not by
  a check. The renders exist for the problems no check can see yet.

## Environment notes (esp. in a Cowork / VM sandbox)

- `scripts/preview.py` needs `matplotlib` (`pip install matplotlib`). It
  renders the exact geometry the validator sees, so it's reliable for
  routing/lane/label placement.
- `scripts/preview.py` does **not** wrap box text the way draw.io does. Long
  box descriptions overflow in the preview but wrap fine in real draw.io.
  Do not trim box text based on a preview overflow alone — size the box for
  the wrapped text (≈ `width / 6` chars per line at fontSize 10–11) instead.
- `scripts/render_png.py` needs the draw.io Desktop CLI on `PATH`. Inside an
  isolated VM (Cowork runs shell/code in a VM separate from the host OS) the
  host-installed `drawio` binary is typically not reachable, so `render_png.py`
  will report "drawio CLI not found." Use `preview.py` for inline checks and
  open the `.drawio` in draw.io Desktop on the host for pixel-accurate output.

## Tunable knobs

Geometric thresholds (interior buffer, orthogonal tolerance, minimum overlap
length, title-band height, label-width estimation) are documented module
constants at the top of `scripts/validate.py`. Tune there in one place; the
function signatures default to them.

## Packaging

**Before packaging, bump the version.** Update the `version:` field in
`SKILL.md`'s frontmatter and add a matching `CHANGELOG.md` entry. The
Customize → Skills UI reads the displayed version from that frontmatter
field — *not* from the archive filename or the CHANGELOG — so if you forget,
an upload that's really new will still show the old version. The frontmatter
`version:` is the single source of truth; the top CHANGELOG entry mirrors it.
Use semver: patch for tuning/fixes/docs, minor for new checks or helpers,
major for breaking changes to the conventions, helper signatures, or CLI.

**Filename: always export the canonical `drawio.skill`** — do not put the
version in the filename. The version lives in the frontmatter; versioned
filenames just produce a pile of stale archives. Overwrite the same
`drawio.skill` each release.

The archive must contain the `drawio/` folder at its root (not nested under a
wrapper folder). Two ways:

Portable (any environment) — zip the folder from its parent directory:

```bash
cd <parent-of-drawio>
zip -r drawio.skill drawio -x '*/__pycache__/*' '*/.pytest_cache/*'
```

Canonical (if you have the skill-creator skill) — its `package_skill.py`
validates frontmatter and emits a `.skill` file (a zip with a `.skill`
extension):

```bash
python <skill-creator>/scripts/package_skill.py /path/to/drawio /output/dir
```

Both produce an archive with `drawio/SKILL.md`, `drawio/scripts/...`, etc. at
the root. `.skill` and `.zip` are interchangeable in contents; if an upload
picker rejects `.skill`, rename to `.zip`.

## Installing / refreshing in Cowork

Install through the UI, not by copying the folder to `~/.claude/skills/`:

1. Customize (left sidebar) → Skills tab → upload the packaged archive.
2. Toggle the skill on.
3. Ensure **Code execution and file creation** is enabled — the scripts need it.
4. Invoke with `/drawio` (Cowork) or let Claude auto-load it from the description.

As of mid-2026 there was a reported issue where Cowork loaded only skills
installed through the Customize UI and ignored folders copied into
`~/.claude/skills/`. Prefer the UI upload until you've confirmed the
file-copy path works in your version. (Claude Code, by contrast, does watch
`~/.claude/skills/` and reloads on change.)

To refresh after refining: re-package the folder, re-upload via Customize →
Skills, replacing the previous version.

## Git

Maintainer commits, pushes, and merges manually. Tooling here never touches
git — it edits files in place; you review and commit.

## Conventions that are settled (do not re-litigate)

See `SKILL.md` for the full list. The load-bearing ones:

- Arrow colour matches the source box (or its stroke if the fill is too pale).
- Future-state = grey/dashed shape and arrow; no `Future` label on arrows.
- Multi-line edge labels use `<div>`, never `\n` (round-trip stability).
- Edges emitted after boxes; `labelBackgroundColor=#ffffff` on labelled edges.
- Helpers stay vendored inline per generator script — not extracted to a
  pip-installable library.
- Reserve horizontal lanes and vertical sub-channels for parallel flows;
  offset shared corridors by ≥5 px on the perpendicular axis.

## Design notes (why the validator works the way it does)

Hard-won lessons that are easy to accidentally undo. Read before changing
`scripts/validate.py`.

- **Stub-squaring is essential, not optional.** `edge_polyline` squares each
  edge's source/target *stub* (anchor → first/last point) into the L-bend
  draw.io's `orthogonalEdgeStyle` actually renders. Without it, every short
  diagonal connection stub draw.io squares invisibly would false-fire
  `DIAGONAL`. `DIAGONAL` therefore flags only *interior* (waypoint-to-
  waypoint) diagonals, which draw.io would also square — i.e. genuinely
  non-deterministic routes. Don't "simplify" edge_polyline back to a straight
  anchor→waypoint reconstruction.
- **Severity tiers exist because some checks are inherently advisory.**
  `DIAGONAL`, `LABEL_BOX_OVERLAP` and `SHORT_LABELLED_EDGE` are warnings
  (print, don't fail the build); the rest are hard errors. This was
  calibrated against real production diagrams that looked good but tripped
  those checks — all three rest on estimates (a route the validator can't
  fully verify, or a char-count label width) rather than exact geometry.
- **`TEXT_OVERLAP` exempts vertical entry into a container.** A container's
  title band spans its full width, so an arrow reaching a box *inside* a
  zone must pierce it — and the container is never that edge's own
  source/target, so the plain rule made the documented bottom-service-band
  pattern unbuildable. The exemption is intentionally narrow: **vertical**
  segments only, and only when an endpoint sits geometrically inside the
  container (`edge_endpoint_inside`). A segment running *along* the band
  still fires, since that one really does sit on the title text. Widening
  this to "any segment of an edge with an endpoint inside" would lose a
  genuine check — `build_text_overlap_inside` guards against exactly that.
- **Edge labels carry an opaque white background** (`labelBackgroundColor=
  #ffffff`), so a label overlapping a box or another label by a few px is
  masked and reads fine. That's why `LABEL_OVERLAP` and `LABEL_BOX_OVERLAP`
  ignore overlaps below `LABEL_BOX_MIN_OVERLAP` (8 px on the shorter axis).
  Don't drop the threshold to zero.
- **Container detection keys on `dashed=1` + `verticalAlign=top` only.** It
  deliberately does NOT require a specific `strokeWidth` — doing so silently
  reclassified containers with a different stroke as solid boxes, producing
  false `CROSSING`. Future-state *shapes* are also dashed but use
  `verticalAlign=middle`, so they don't match.
- **The skill emits one colour per thing and does not theme for dark mode.**
  It used to, via `light-dark()`. Removed in 1.3.0 after measuring: draw.io
  inverts colours for its own dark theme, and the manual handling produced a
  WORSE dark render, because an explicit `<font color>` on an edge label opts
  that label out of the inversion and pins dark text onto a dark canvas.
  `preview.py` still unwraps `light-dark(l,d)` so diagrams authored before
  the change keep working. `validate.py` ignores colour entirely, so contrast
  remains an eyeball check on a real render.
- **Width estimation is char-count based** (`LABEL_PER_CHAR_PX = 5.5`,
  Latin sans-serif at fontSize 10). CJK / heavily-styled HTML labels are
  approximate — see SKILL.md Limitations. Tune the module constants at the
  top of `validate.py` in one place; function signatures default to them.
