# Changelog

All notable changes to the `drawio` skill are recorded here. Versioning
follows [semver](https://semver.org/): patch = tuning / fixes / docs, minor =
additive features (new check or helper), major = breaking changes to the
locked conventions, helper signatures, or the validator CLI contract.

The authoritative version is the `version:` field in `SKILL.md` frontmatter
(the Customize → Skills UI reads it from there). Keep this changelog's top
entry in sync with it before packaging. See
[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) → Packaging.

## [Unreleased]

## [1.4.2] - 2026-09-01 — Documentation standards refresh

### Fixed

- **`docs/ARCHITECTURE.md` stated the icon catalog's size and key format wrongly.**
  It said "~130 `family:name` keys"; the catalog holds 128 entries and spells them
  with a hyphen (`aws-lambda`), the mismatch with the helpers' colon form that
  KI-01 tracks.
- **`docs/ARCHITECTURE.md` and `docs/CONTRIBUTING.md` no longer require the
  draw.io CLI on `PATH`.** `render_png.py` also finds the macOS app bundle at
  `/Applications/draw.io.app` on its own.
- **Two `docs/ENHANCEMENTS.md` entries rendered their `Source:` line as a
  heading.** They ran straight into the `---` rule with no blank line, which
  Markdown reads as a setext heading. ENH-03's cited line range and code excerpt
  now match `validate.py` as it stands.

### Changed

- **Removed text that stood in two places.** `docs/OPEN_QUESTIONS.md` repeated its
  own header paragraph as its empty state; `docs/ROADMAP.md` gave the queue in
  both Status and Phases; the reason `renders/` is committed stood in three files
  and now stands only in `CLAUDE.md`.
- **`docs/ROADMAP.md`'s Status is an index again**, not a summary of the four open
  High issues that the table below it already lists.
- **`docs/CONTRIBUTING.md` describes the present.** Its dark-theme review step no
  longer explains itself through the 1.3.0 removal, which is history and belongs
  in this file.

## [1.4.1] - 2026-09-01 — External review intake

### Fixed

- **`docs/ARCHITECTURE.md` no longer claims `render_png.py` reuses the
  validator's geometry.** It does not import `validate.py` at all — it hands the
  file to the draw.io CLI, which parses it itself. Only `preview.py` shares the
  validator's geometry. The module diagram carried the same false edge and has
  been regenerated without it.
- **`docs/ARCHITECTURE.md` no longer requires the draw.io CLI on `PATH` for
  `list_icons.py --refresh`.** That path reads `app.asar` out of the app bundle
  directly (or `$DRAWIO_APP`) and never looks at `PATH`.
- Catalog size in the module diagram: `~130` → 128, matching the other docs.
- **Release 1.3.0 is tagged.** It shipped on 2026-08-31 without one, leaving
  `git describe` and every "what changed since 1.3.0" diff with no anchor. The
  tag was backfilled at `796f084` — the release's last commit, where the
  `SKILL.md` frontmatter and the CHANGELOG's top entry both read 1.3.0. Settles
  UNK-01.

## [1.4.0] - 2026-09-01 — Documentation standards and packaging

### Added

- **`scripts/package_skill.py`** — builds `../drawio.skill` from the folder.
  It roots the archive at `drawio/` and drops every hidden entry by rule rather
  than by name, so `.gitignore` and tool caches stop leaking into uploads the
  way they did from hand-built zips.
- **`LICENSE`** — MIT, matching the `license:` field in `SKILL.md` frontmatter.
- **`CLAUDE.md`** — the repo's own conventions, the validator invariants that
  are easy to undo while simplifying, the three icon-extraction traps, and the
  decisions already taken and not taken.
- **`docs/ARCHITECTURE.md`**, with the module diagram the skill draws of itself.
  Its generator, `.drawio` source and render are all committed, so the picture
  can be checked against the code rather than trusted.
- **`docs/ROADMAP.md`** and its supporting `KNOWN_ISSUES.md`,
  `ENHANCEMENTS.md`, `OPEN_QUESTIONS.md`.

### Changed

- **`CONTRIBUTING.md` moved to `docs/`.** The repo root now holds only
  `README.md`, `CLAUDE.md`, `CHANGELOG.md`, `LICENSE` and the skill's own
  `SKILL.md`. The design notes and settled conventions moved out of it and into
  `CLAUDE.md`, where rationale belongs.
- **`docs/` is excluded from the package.** It is maintainer material;
  a user installing the skill reads `SKILL.md`.
- **Release headings follow Keep a Changelog** (`## [x.y.z] - date — name`).
  Only the headings changed; every released entry's text is untouched.

### Fixed

- **The icon catalog's own example no longer raises.** `references/icons.md`
  opened with `icon="aws-lambda"`, which the helpers reject — they take
  `aws:lambda`. The snippet and SKILL.md's "Choosing an icon" section now state
  the two spellings and the swap between them. The underlying mismatch is
  tracked as KI-01.
- **Test count corrected** in `SKILL.md` and `docs/CONTRIBUTING.md`: 88 → 94.
- **`render_png.py --theme` is documented** in SKILL.md's tool table.
- **Catalog size stated exactly** (128 entries) instead of "~130".
- Stale paths after the move: `.gitignore`, `README.md`, `SKILL.md` and the
  CHANGELOG preamble all pointed at the old `CONTRIBUTING.md` location.

### Removed

- **`archive/`** — prior-art feedback kept for maintainers. Tracked outside the
  repo; it is history, not part of the skill.
- **Hand-zip packaging instructions** from `SKILL.md` and `docs/CONTRIBUTING.md`.
  They contradicted the rule that the archive is never built by hand, which is
  the failure they caused.

## [1.3.0] - 2026-08-31 — Vendor logos and a ninth check

Vendor logos, a ninth check, and the removal of dark-mode support.

### Icons

- **`icon_box(...)`** — a vendor glyph inside a labelled card. The card keeps
  the exact geometry, anchors and routing of a plain `box()`, so icons cost
  nothing in layout terms. The default placement.
- **`icon_node(...)`** — bare glyph with its name underneath, the vendor-docs
  look. Its caption is wider than the glyph, so an edge leaving the bottom
  crosses its own label; `icon_box()` avoids that entirely.
- **`svg_icon(path)`** — embeds a local SVG as a base64 data URI for a logo
  draw.io does not ship. The form is `data:image/svg+xml,<base64>`; the
  `;base64,` spelling renders blank, because `;` ends the style token.
- **`raw_icon(...)`** — escape hatch for a name not in the catalog.
- **`references/icons.md`** — ~130 curated icons across AWS, Azure, GCP,
  Kubernetes, Cisco and generic network shapes, with brand colours. It is also
  the machine-readable source, so there is no second copy to drift.
- **`scripts/list_icons.py`** — browse, verify, or refresh the catalog. Only
  the refresh modes need draw.io installed.

### Validator

- **New check: `UNKNOWN_ICON`** (warning). Verifies stencil, `resIcon`/`prIcon`
  and image names against the ~11,500 names draw.io ships, with a did-you-mean.
  A mistyped stencil renders as an empty shape and reports nothing, so no other
  check can catch it. Skipped when the name list is absent.
- **Child cells are positioned against their parent.** A glyph at (10, 16)
  inside a box at (400, 300) was becoming a phantom obstacle near the canvas
  origin. This also fixes a pre-existing bug: draw.io Desktop writes
  `edgeLabel` child cells on round-trip, which were parsed as absolute boxes.
- **CROSSING now covers an icon's caption band**, including against the edge's
  own endpoints. A caption is text, not a connection surface.
- **A glyph inside a card is no longer a second obstacle**, so one routing
  problem reports once.
- **Label measurement scales with `fontSize`** instead of assuming 10.
- **Edge labels moved from fontSize 10 to 12.**
- **A malformed anchor no longer kills the parser**; the generators refuse half
  an anchor pair by name.

### Removed: dark-mode support

`ld()`, the eight `*_DARK` constants, all 35 `*_dark` parameters, and the
`<font color="light-dark(...)">` wrapper on edge labels are gone.

Measured against a real dark export, the manual handling made things **worse**:
draw.io inverts colours for its own dark theme, and an explicit colour on a
label opts it out of that inversion — so exactly the labels given a dark variant
were the ones that became unreadable. Stripping every `light-dark()` and
re-exporting produced a strictly better dark render.

Existing diagrams are unaffected: `light-dark()` is draw.io's own function and
still renders. `preview.py` greys any colour matplotlib cannot parse rather than
failing on it.

### Tooling

- **`scripts/render_examples.py`** — rebuilds every example, validates it, and
  writes `renders/<name>-{light,dark}.png`. A diagram with errors is reported
  and not rendered. Warnings do not block, matching `validate.py`'s contract.
- **`render_png.py` gains `--theme`** (dark / light / auto).
- **`preview.py`** draws icons as labelled placeholders and puts a bottom
  caption below its shape; `light()` falls back to grey instead of raising.
- **`ruff.toml`** pins six rule families. Without a config, ruff enabled 400+
  rules and the result depended on the installed version.

### Conventions

- Edge labels are **Title Case**; literal protocol and command tokens keep their
  real casing (HTTPS, PUT, COPY).
- Stack a label when it does not fit, not by taste: `SHORT_LABELLED_EDGE`
  reports the exact pixels.
- `edge()` gains **`label_bg`** so a label's plate can match the zone behind it.
  A white plate on a tinted container reads as a sticker.
- Never dash an `icon_node()`: `dashed=1` + `verticalAlign=top` is the
  validator's container signature.
- Always give a wrapper icon its brand colour, or it renders as a blank plate.

### Example

- **`examples/build_aws_vpc_pipeline.py`** — an AWS pipeline with a VPC nested
  inside a cloud zone, and one embedded SVG. Validates clean.

### Tests

34 → 88.

## [1.2.0] - 2026-08-01 — Validator fixes from first production use

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

## [1.1.1] - 2026-06-06 — Point-anchored edges and colour guidance

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

## [1.1.0] - 2026-06-06 — Dark-mode helpers and layout guidance

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
  blind spots and Desktop round-trip artifacts. `docs/CONTRIBUTING.md` design
  notes updated.

## [1.0.0] - 2026-06-06 — First stable release

First stable release. (Versions 0.1.x–0.2.x were pre-stable iteration; the
counter was reset here. The design rationale from those iterations is
preserved in `SKILL.md` and `CLAUDE.md`, not in this
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

## Reference

- [Unreleased](https://github.com/rahulragunathan/drawio/compare/v1.4.2...HEAD)
- [1.4.2](https://github.com/rahulragunathan/drawio/compare/v1.4.1...v1.4.2)
- [1.4.1](https://github.com/rahulragunathan/drawio/compare/v1.4.0...v1.4.1)
- [1.4.0](https://github.com/rahulragunathan/drawio/compare/v1.3.0...v1.4.0)
- [1.3.0](https://github.com/rahulragunathan/drawio/compare/v1.2.0...v1.3.0)
- [1.2.0](https://github.com/rahulragunathan/drawio/releases/tag/v1.2.0)

Releases before 1.2.0 were never tagged, so they have no compare link. 1.3.0's
tag was backfilled after the fact — see the entry above.
