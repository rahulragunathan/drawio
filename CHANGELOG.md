# Changelog

All notable changes to the `drawio` skill are recorded here. Versioning
follows [semver](https://semver.org/): patch = tuning / fixes / docs, minor =
additive features (new check or helper), major = breaking changes to the
locked conventions, helper signatures, or the validator CLI contract.

The authoritative version is the `version:` field in `SKILL.md` frontmatter
(the Customize → Skills UI reads it from there). Keep this changelog's top
entry in sync with it before packaging. See `CONTRIBUTING.md` → Packaging.

## 1.2.0 — 2026-08-01

From an agent's first production use of the skill (a SupernoteExport
architecture diagram: 3 dashed zones, 13 boxes, 14 edges). Additive — existing
generators keep working, though a diagram with a too-short labelled edge will
now surface a new warning.

### Validator (`scripts/validate.py`)

- **`TEXT_OVERLAP` no longer blocks the documented bottom-service-band
  pattern.** A container's title band spans its full width, so any arrow
  dropping into a box *inside* a zone had to cross it — and the container is
  never the edge's own source/target (the box inside it is). The skill
  recommended a layout its own validator rejected. A **vertical** segment is
  now exempt when the edge's source or target box sits geometrically inside
  that container (`box_inside` / `edge_endpoint_inside`; point-anchored
  endpoints count too). The exemption is deliberately narrow — a segment
  running *along* the band still fires, even between two boxes inside the
  zone, because that one really does sit on the title text.
- **New `SHORT_LABELLED_EDGE` check (warning).** Fires when a labelled edge's
  total rendered length is shorter than its own label's estimated text width.
  The failure — a 40 px edge carrying a 13-character label — rendered as a
  stub arrow with a floating caption yet validated clean: each overhang was
  below `LABEL_BOX_OVERLAP`'s 8 px threshold, and both boxes were the edge's
  own endpoints, which that check exempts. Reuses the existing ~5.5 px/char
  estimator (padding excluded — the question is whether the ink fits).
- **`normalise_label` now treats `<div>` as a line break, not a no-op.**
  Only `</div>` broke the line, so the skill's own locked multi-line
  convention (`Verify<div>Token</div>`) was measured as one 11-char line
  instead of two ≤6-char lines — roughly double its true width, and one line
  too short. Fixes width/height estimates for every label-geometry check.
  Blank lines left by tag boundaries are dropped.

### Rendering (`scripts/render_png.py`)

- **`foo.drawio` now renders to `foo.png`, not `foo.drawio.png`.** The
  extension is replaced rather than appended, removing the follow-up `mv`
  that every invocation needed (and the double extensions that leaked into
  committed filenames).
- **New `-o` / `--output` flag** for repos that keep diagram sources and
  rendered PNGs in different directories (`render_png.py d.drawio -o
  docs/architecture.png`). Missing parent directories are created. It names
  one destination file, so it requires exactly one input — combining it with
  several inputs or the glob-the-cwd default is a usage error (exit 2)
  rather than a silent render of each diagram over the last. Argument
  parsing is factored into a testable `parse_args()`.

### Example

- The example's `API Gateway → Auth Service` label is stacked into two
  `<div>` lines: the gap there is 40 px and "Verify Token" needs ~66 px, so
  the new check caught a genuine instance in the bundled example on its first
  run.

### Docs (SKILL.md)

- Bottom-service-band bullet now states that the band **can** be a dashed
  container, and how to enter it (from above/below, never along the title).
- `TEXT_OVERLAP` and the new `SHORT_LABELLED_EDGE` rows added/updated in the
  checks table.
- Rendering the PNG **and looking at it** is now step 6 of the workflow
  proper, not an optional extra; a new Limitation states that a clean
  validate says nothing about whether labels have *room*.
- Routing strategy: writing the corridor allocation into the generator's
  comments is now an explicit recommendation (it makes later layout edits
  mechanical), not just something the example happens to model.
- "Why no Python library?" notes that a host repo's formatter will reflow the
  vendored helpers from ~80 to ~200 lines — expected; don't fight it and
  don't diff against the template for drift.
- `preview.py`'s `matplotlib` dependency flagged as not shared by the rest of
  the skill, so in a project venv `render_png.py` is usually the available
  path.

### Tests

- New fixtures `build_container_entry` (entering a zone must not fire),
  `build_text_overlap_inside` (running along the band still fires),
  `build_short_labelled_edge`, plus parametrised `normalise_label` cases.
- New `tests/test_render_png.py` — the `parse_args` contract (accepted forms
  and every rejected one) plus render plumbing, with `subprocess.run` faked
  at the system boundary so the real `render()` path runs without the drawio
  CLI installed. Suite is now 34 tests.

## 1.1.1 — 2026-06-06

Patch from examining the four final DocumentIQ diagrams in the spec folder.

### Validator (`scripts/validate.py`)

- **Point-anchored edges no longer false-fire `DANGLING`.** draw.io Desktop
  writes an edge endpoint as a fixed `sourcePoint`/`targetPoint` (instead of a
  connected cell) after hand-tuning — a normal artifact. The validator now
  parses those points, uses them in `edge_polyline`, and only reports
  `DANGLING` when an endpoint resolves to neither a cell nor a point. Cleared
  all spurious DANGLING errors across the four hand-tuned finals. Messages
  also tolerate a point endpoint (shown as `(point)`).

### Docs — colour guidance reframed

- The colour section is now **"Colour: contrast and clarity"**: the goal is
  legibility/contrast, *not* a dark/neon scheme. `light-dark()` is presented
  as the mechanism for keeping contrast across themes; dark variants are
  higher-contrast tints of the same hue (neon optional), and a single colour
  is fine when it already contrasts. Palette tables, helper comments, and the
  example's accents were retuned from neon (hot pink / magenta / cyan) to
  calmer same-hue tints (lighter blue / steel-blue / lavender). Behaviour
  unchanged; example still validates clean.

### Tests

- Added `build_point_anchored` fixture + test (a fixed-`targetPoint` edge must
  not fire DANGLING). Suite is now 10 tests.

## 1.1.0 — 2026-06-06

Additive release from lessons hand-refining the DocumentIQ diagrams in
draw.io Desktop. All helper changes are backward-compatible (new optional
args); existing generators keep working unchanged.

### Helpers (template + example)

- **`ld(light, dark=None)`** — builds draw.io's `light-dark()` colour.
- **`box()` / `container()`** gain `fill_dark`, `stroke_dark`,
  `fontColor_dark` for dark-mode-safe colours.
- **`edge()`** gains `color_dark` (themes stroke and auto-wraps the label in
  a `light-dark()` font), `jump=True` (`jumpStyle=gap` over crossings),
  `bidirectional=True` (arrowheads both ends), and `end_arrow=False`
  (connector / bus lines). Default edge style now includes
  `startSize=2;endSize=2`.
- Added `*_DARK` palette constants.

### Preview

- **`scripts/preview.py`** extracts the light value from `light-dark(l,d)`
  before handing colours to matplotlib, so themed diagrams still preview.
  (Preview remains light-mode only by design.)

### Example

- `build_three_tier_web.py` converted to the dark-mode palette via the new
  args; demonstrates a bidirectional edge, a `jump` hop, and a lean legend
  (future-state only). Still validates clean.

### Docs (SKILL.md)

- New **"Designing for dark mode"** section (light-dark mechanics, `*_dark`
  args, dark palette, preview caveat); **"Layout & semantics"** (managed
  services vs compute zones, bottom service band, balance pass, single-row
  numbered pipelines); **"Edge styles beyond colour"** (jump / bidirectional
  / connector). Locked conventions now cover dark colours, verb-first
  theme-aware labels, and lean legends. Limitations note colour/semantic
  blind spots and Desktop round-trip artifacts. `CONTRIBUTING.md` design
  notes updated.

## 1.0.0 — 2026-06-06

First stable release. (Versions 0.1.x–0.2.x were pre-stable iteration; the
counter was reset here. The design rationale from those iterations is
preserved in `SKILL.md` and `CONTRIBUTING.md` → Design notes, not in this
history.)

Capabilities at 1.0.0:

- **Generator** — `assets/build_template.py` (copy-and-edit starter) and the
  worked `examples/build_three_tier_web.py`, with vendored inline helpers:
  `container`, `box` (incl. `dashed=` for future-state shapes), `edge`,
  `sub`, `desc`.
- **Validator** (`scripts/validate.py`) — seven geometric checks, split by
  severity:
  - Errors (fail the build): `CROSSING`, `OVERLAP`, `TEXT_OVERLAP`,
    `LABEL_OVERLAP`, `DANGLING`.
  - Warnings (advisory, print only): `DIAGONAL` (interior non-orthogonal
    segment; anchor stubs are auto-squared to match draw.io), and
    `LABEL_BOX_OVERLAP` (label over an unrelated box).
  - Label-overlap checks ignore sub-8 px grazes (labels carry an opaque
    white background). Geometric thresholds are documented module constants.
- **Preview / render** — `scripts/preview.py` (offline matplotlib, reuses
  the validator's geometry incl. dashed boxes) and `scripts/render_png.py`
  (pixel-accurate via the draw.io Desktop CLI).
- **Tests** — nine pytest cases: a clean fixture, one per failure mode, a
  stub-squaring regression guard, and an end-to-end build+validate of the
  bundled example.
