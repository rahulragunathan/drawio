# drawio skill — working notes (auto-loaded)

This repo is one Claude skill: a generator template plus a geometric validator
for `.drawio` architecture diagrams. `SKILL.md` is the model-facing reference
and the product. Everything else supports it.

Global shell, git, and process rules live in `~/.claude/CLAUDE.md`. They are not
restated here.

## Where things are written down

| Question | File |
|----------|------|
| How do I use the skill? | [SKILL.md](SKILL.md) |
| What is this repo, in 30 seconds? | [README.md](README.md) |
| How is the code put together? | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| How do I refine, package, and install it? | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| What shipped, and when? | [CHANGELOG.md](CHANGELOG.md) |
| What is still open? | [docs/ROADMAP.md](docs/ROADMAP.md) |

## Rules specific to this repo

- **Stdlib only in the shipped code.** `validate.py`, `render_png.py`,
  `list_icons.py`, `package_skill.py` and `assets/build_template.py` must import
  nothing outside the standard library. The skill is a self-contained drop into
  `~/.claude/skills/`; a third-party import would have to be installed on every
  machine before a diagram could be built. `preview.py` is the one exception and
  is documented as such.
- **The version lives in `SKILL.md` frontmatter.** The Skills UI reads it from
  there — not from the archive filename or the CHANGELOG. The top CHANGELOG
  entry mirrors it.
- **Never hand-build the `.skill` archive.** Run `scripts/package_skill.py`.
  Hand-built zips have shipped `.gitignore` and tool caches.
- **A clean validate is not the bar.** Every genuinely interesting defect found
  in this project — a blank icon plate, an arrow struck through a caption,
  unreadable dark labels — was found by looking at a render. Regenerate
  `renders/` at the end of a phase and look at both themes.
- **`references/icons.md` is machine-readable.** `list_icons.py` parses its
  tables. Keep the table shape; there is no second copy of the catalog.

## Validator invariants — do not undo these

Each one was learned from a failure and is easy to break while "simplifying".
`tests/test_validate.py` guards them.

- **Stub-squaring is essential.** `edge_polyline` squares each edge's
  source/target stub into the L-bend draw.io's `orthogonalEdgeStyle` renders.
  Without it every short connection stub false-fires `DIAGONAL`. `DIAGONAL`
  therefore flags only interior waypoint-to-waypoint diagonals — routes draw.io
  would also square, so genuinely non-deterministic ones.
- **`TEXT_OVERLAP` exempts vertical entry into a container, and only that.** A
  container's title band spans its full width, so an arrow reaching a box inside
  a zone must pierce it. The exemption needs a *vertical* segment and an
  endpoint geometrically inside the container. Widening it to "any segment of an
  edge with an endpoint inside" loses the real check;
  `build_text_overlap_inside` guards that.
- **Container detection keys on `dashed=1` plus `verticalAlign=top`, nothing
  else.** Requiring a particular `strokeWidth` silently reclassified containers
  as solid boxes and produced false `CROSSING`. Future-state shapes are dashed
  too but use `verticalAlign=middle`, so they do not match.
- **The source/target exemption covers the shape, not the caption.** An edge
  ends on its own box's boundary, so that is exempt from `CROSSING`. A caption
  under an icon is not — a line through it reads as a strikethrough.
- **`is_decoration` is a conjunction:** an icon *and* a child of a vertex.
  Exempting every child loses a real `CROSSING` on a box nested in a swimlane;
  exempting every icon wrongly exempts an `icon_node()`, which is the shape.
- **Measure an overlap against the rect you hit-tested.** `LABEL_BOX_OVERLAP`
  once hit-tested `obstacle_rect()` and measured the bare shape, so every
  caption-band hit computed a negative height and was discarded as a graze. The
  check existed and could not fire.
- **Label size is read from the style, never assumed.** The estimator is
  `0.55 x fontSize` per character. Hard-coding fontSize 10 under-measured every
  label at another size, and a test asserting the default size could not see it.
- **Label-overlap checks ignore grazes below 8 px.** Edge labels carry an opaque
  white plate, so a few pixels are masked and read fine. Do not drop the
  threshold to zero.

## Icon extraction — three traps

Each produces a plausible result while being wrong. Assert against all three
when touching `list_icons.py`.

- Asset paths inside `app.asar` are prefixed `drawio/src/main/webapp/`.
  Filtering on the style-relative `img/lib/` prefix matches nothing.
- The archive's data section starts at `8 + field1`, not `16 + json_length`.
  The JSON directory is padded, so the naive formula reads every file up to
  three bytes early — which regex scanning tolerates, so it looks like it works.
- The wrapper shapes that actually render vendor icons
  (`mxgraph.aws4.resourceIcon`, `mxgraph.kubernetes.icon2`, four others) live
  only in draw.io's JavaScript, in no stencil file. Extracting stencil XML alone
  yields ~9,000 names while missing every AWS and Kubernetes icon.

`gcp3` is a category set of 45 broad names; per-product GCP icons live in
`gcp2`, so some catalog entries carry a fully qualified `mxgraph.gcp2.*` name.

## Decisions taken and not taken

- **No pip-installable helper library.** The helpers stay vendored inline in
  `assets/build_template.py` and each example. A skill has to be a
  self-contained folder, the helpers are short, and each generator grows its own
  variants of `box()`. If one repo copies them across many diagrams, factor a
  local module *in that repo* — not here.
- **No hand-authored dark colours.** Dropped in 1.3.0 after measuring a real
  dark export. draw.io inverts colours for its own dark theme, and an explicit
  colour on a label opts that label out of the inversion — so exactly the labels
  given a dark variant became unreadable. `ld()`, the `*_DARK` constants and the
  `light-dark()` label wrapper are gone. Diagrams that still contain
  `light-dark()` render fine; it is draw.io's own function.
- **No auto-layout.** The skill exists because Lucid, Mermaid and Graphviz
  auto-route and lose lane reservation, source-coloured arrows, per-flow line
  styles, and label positions that survive a Desktop round-trip. Adding a layout
  engine would remove the reason to use this.
- **Severity tiers stay.** `DIAGONAL`, `LABEL_BOX_OVERLAP` and
  `SHORT_LABELLED_EDGE` warn rather than fail. All three rest on estimates — a
  route the validator cannot fully verify, or a character-count label width —
  and were calibrated against real diagrams that looked good and tripped them.
- **`preview.py` does not unwrap `light-dark(l,d)`.** `light()` returns neutral
  grey for any colour matplotlib cannot parse, so a pre-1.3.0 diagram previews
  in grey rather than failing. Render the PNG for a faithful picture of an
  older file.
- **`renders/` is committed, and excluded from the package.** For a diagramming
  skill the pictures are the product, so the repo records what each phase looked
  like and a geometry change shows a changed picture. Users installing the skill
  do not need 500 KB of PNGs.
