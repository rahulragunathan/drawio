---
name: drawio
version: 1.2.0
description: Use this skill whenever the user wants to generate, validate, or modify architecture diagrams as draw.io (.drawio / diagrams.net) XML files. Trigger on any mention of .drawio, draw.io, diagrams.net, or requests for architecture diagrams where routing control matters — for example, when auto-layout tools (Lucid, Mermaid, Graphviz) have produced arrows that cross boxes, overlap labels, or pile into a single corridor. The skill emits explicit waypoints, anchor coordinates, and label offsets so routing is deterministic, then runs an eight-check geometric validator (CROSSING, OVERLAP, TEXT_OVERLAP, LABEL_OVERLAP, LABEL_BOX_OVERLAP, SHORT_LABELLED_EDGE, DIAGONAL, DANGLING). Use this skill even if the user only says 'architecture diagram' or 'system diagram' without naming draw.io — it produces .drawio output that opens at app.diagrams.net without auth and round-trips through draw.io Desktop without diff churn. Also use it when validating, fixing, or PNG-rendering an existing .drawio file.
license: MIT
---

# drawio

Build .drawio architecture diagrams with deterministic orthogonal routing, then run a geometric validator that catches the failure modes auto-layout tools leave behind.

## Why a generator + validator instead of a layout engine

Lucid, Mermaid, and Graphviz all auto-route. They optimise for "no segment crosses a box" globally but lose: lane reservation, source-coloured arrows, multi-line labels with `<div>` round-trip, distinct line styles per semantic flow, and label positions that survive a draw.io Desktop round-trip without diff churn.

This skill encodes those decisions explicitly. You write the coordinates; the validator catches the geometric failure modes that *always* trip up reviewers; the output opens at app.diagrams.net without auth and at draw.io Desktop without diff churn.

## What's in the skill

| Path | Purpose |
| --- | --- |
| `scripts/validate.py` | Geometric validator. Eight checks: CROSSING, OVERLAP, TEXT_OVERLAP, LABEL_OVERLAP, LABEL_BOX_OVERLAP, SHORT_LABELLED_EDGE, DIAGONAL, DANGLING. Run on any `.drawio` file. |
| `scripts/render_png.py` | Renders `.drawio` → `.png` via the draw.io Desktop CLI (`foo.drawio` → `foo.png`; `-o path.png` to send it elsewhere). Needs `drawio` on PATH (macOS auto-detects the app bundle). Pixel-accurate. |
| `scripts/preview.py` | Offline preview renderer. Reuses `validate.py`'s geometry, so it shows exactly what the validator sees. Approximate text wrapping — trust it for layout, not final fidelity. **Needs `matplotlib`**, which the rest of the skill does not — in a project venv without it, reach for `render_png.py` instead (the draw.io CLI is a system binary, not a venv dependency). |
| `assets/build_template.py` | Minimal starter generator. Copy, rename, customise. Vendors the helpers (`container`, `box`, `edge`, `sub`, `desc`) inline. |
| `examples/build_three_tier_web.py` | Comprehensive worked example: three-tier web app, 11 solid boxes, 11 edges, every locked convention exercised. Validates clean. |
| `tests/test_validate.py` | Pytest suite — one minimal fixture per validator check, guards for each exemption, plus a regression test on the bundled example. |
| `tests/fixtures/builders.py` | Fixture builders that produce minimal `.drawio` files exhibiting exactly one violation type each. |

## Workflow

1. **Copy the template.** `cp assets/build_template.py my-diagram.py`. Edit constants, containers, boxes, then edges.
2. **Build.** `python my-diagram.py`. The script writes a `.drawio` file (default: cwd).
3. **Validate.** `python scripts/validate.py my-diagram.drawio`. Fix violations (see the failure-mode table below).
4. **Open.** Drop the file at https://app.diagrams.net (no auth) or open it in draw.io Desktop. The diagram round-trips without diff churn — if you edit in Desktop and save, your generator can read the result back.
5. **(Optional) Preview inline.** `python scripts/preview.py my-diagram.drawio` renders an approximate PNG with only matplotlib (which is *not* a dependency of the rest of the skill — in a project venv you'll often find `render_png.py` is the available path) — handy when the draw.io CLI isn't available (sandboxes, VMs). It draws the exact geometry the validator checks, so it's reliable for judging routing, lane spacing, and label placement. **It does not wrap box text the way draw.io does** — long box descriptions will overflow in the preview but wrap correctly in real draw.io, so don't trim box text based on a preview overflow alone.
6. **Render the PNG and look at it.** `python scripts/render_png.py my-diagram.drawio` writes `my-diagram.png` (pixel-accurate; needs the draw.io Desktop CLI on PATH). Add `-o docs/architecture.png` when the rendered PNG is committed somewhere other than beside its source — it creates missing parent directories, and takes exactly one input. Treat this as part of the loop, not an optional extra — a clean validate says nothing about whether labels have *room*, whether column gaps are cramped, or whether either theme is legible. Looking at the render is what catches those.

## Locked conventions

These are non-negotiable; the validator, the example, and the helpers all assume them.

- **Arrow colour matches the source box** (or its stroke if the fill is too light to read as a line). This is the single rule that makes a dense diagram readable — readers can follow flow by colour without re-reading labels.
- **Future-state shape = grey/dashed; future-state arrow = grey/dashed**, NO `Future` text label. The legend strip at the bottom carries the meaning. Pass `dashed=True` to `box()` for the shape; use `style="dashed"` on `edge()` for the arrow.
- **Edges are emitted AFTER boxes** so labels render on top. (The XML order matters in draw.io.)
- **`labelBackgroundColor=#ffffff` on every labelled edge.** Set automatically by the `edge()` helper. Without it, labels become illegible where they cross other edges.
- **Multi-line edge labels use `<div>` tags, NOT `\n`.** draw.io Desktop loses `\n` on round-trip; `<div>` survives. Example: `label="Route<div>Request</div>"`.
- **Subheadings use `sub()`** — italicised Title Case with an explicit `font-size` in the span style. Without explicit `font-size`, draw.io Desktop drops back to its default and the diagram looks inconsistent.
- **Description bodies use `desc()`** — sentence case, non-bold, with explicit `font-size`. Same round-trip reason.
- **Reserve horizontal corridors and vertical sub-channels** for parallel flows. Two edges sharing a corridor must offset by at least 5 px on the perpendicular axis (OVERLAP fires below 1.5 px tolerance, but 5 px gives comfortable visual separation).
- **Choose colours for contrast and clarity**, and keep them legible in whichever theme the diagram ships in. Use `ld()` / `light-dark()` where a colour would wash out in light or dark mode; a single colour is fine when it already contrasts. See "Colour: contrast and clarity" below.
- **Edge labels are verb-first and theme-aware.** Prefer imperatives ("Call OCR", "Publish events", "Reads index") over noun fragments ("OCR call"); stack long labels into narrow `<div>` lines to fit the channel; let `edge()` colour the label to match its (dark) stroke.
- **Keep the legend lean.** Colour + labels carry the meaning. Only state what a reader can't infer — in practice just "grey/dashed shape = future state", and nothing at all if there are no future shapes. Don't enumerate line styles the diagram uses.

## Colour: contrast and clarity (and dark mode)

**The goal is clear contrast and legibility — not a particular palette.** Colours exist to separate categories and let a reader follow flow at a glance. Pick whatever reads cleanly; you do **not** need a dark/neon scheme. Two things break legibility in practice, and both are easy to avoid:

- **Low contrast against the canvas.** Pale fills (`#fff4d6`, `#eaf3fb`) and near-black label text disappear on a dark background; very light text vanishes on a light one.
- **A palette that only works in one theme.** draw.io Desktop is commonly viewed/exported in **dark mode**, so a scheme tuned only for the light canvas can fail there.

`light-dark()` is the mechanism for keeping contrast across *both* themes — it is not a mandate to go neon:

- **Use `light-dark(light, dark)` for fills, strokes, and label text** when a colour wouldn't read in both themes. The `ld()` helper builds it: `ld('#0078d4', '#4da3ff')` → `light-dark(#0078d4,#4da3ff)`. draw.io renders the first value in light mode, the second in dark. The dark value should be chosen for **contrast and clarity** — usually a brighter or lighter variant of the *same hue* (e.g. navy → light steel-blue), not a clashing neon. Saturated accents are fine if they read well, but they're a choice, not a requirement.
- **A single colour is fine when it already contrasts in the target theme.** Mid-bright colours (green `#34a853`, orange `#d04a02`, teal `#008272`) read in both themes and need no `_dark` variant. Only add one where a colour actually washes out.
- **The helpers take `*_dark` arguments.** `box()` / `container()` accept `fill_dark`, `stroke_dark`, `fontColor_dark`; `edge()` accepts `color_dark` (and `label_color_dark`). Supply a dark value only where it improves contrast; otherwise leave it single-colour.
- **Match text to its fill.** A light dark-fill needs dark `fontColor_dark` (and vice-versa); white text on a pale fill is unreadable.
- **`edge()` auto-themes the label.** When `color_dark` (or `label_color_dark`) is set, the label is wrapped in `light-dark(#000000, <dark>)` so it reads on dark and binds to its arrow colour.
- **Neither validate nor preview judges contrast.** `light-dark()` is a runtime function; `preview.py` renders the light value only and `validate.py` ignores colour entirely. A clean validate and a good preview say **nothing** about whether either theme is legible — confirm contrast by eye in a draw.io Desktop export of the theme you ship.

A starting palette. The dark column is a higher-contrast variant for the dark canvas — keep it in the same hue family for a calm result, or push it brighter if you want more pop. Substitute your own categories:

| Category | Light | Dark variant (for contrast) |
| --- | --- | --- |
| Source / primary cloud | `#0078d4` | `#4da3ff` (lighter blue) |
| Config / repo | `#bf8f00` | `#ffd966` (lighter gold) |
| Orchestrator / pipeline | `#5b3fbf` | `#b59dff` (lighter purple) |
| Worker / compute (pale fill) | `#8e7cc3` | `#cbbcff` (lighter lavender, dark text) |
| Datastore / index | `#003c71` | `#7fb3e6` (light steel-blue) |
| Downstream consumer | `#9c27b0` | `#d18cff` (lighter violet) |
| Frontend / users | `#34a853` | *(reads in both — keep single)* |
| Gateway | `#d04a02` | *(reads in both — keep single)* |
| Future-state shape | `#e0e0e0` fill, `#9e9e9e` stroke, `dashed=1` | *(grey/dashed in both themes)* |

(Bright accents like hot-pink or cyan also work if you prefer them — the rule is contrast, not restraint.)

## Layout & semantics

Content-and-composition lessons the validator can't check for you:

- **One dashed zone per trust/ownership boundary, and put each component in the zone that actually *runs* it.** The most common structural error is drawing a **managed cloud service** (Service Bus, Event Grid, AI Search, Key Vault) **inside the cluster/compute boundary** (AKS, ECS). Pull managed services into their own zone; leave the compute zone holding only things that run there (pods, workers, sidecars, jobs). A reviewer catches this instantly.
- **Bottom service band for many-to-few fan-in.** When many pipeline stages call a few shared services, lay the shared services in a horizontal band along the **bottom** and drop straight down into them, rather than fanning every arrow into one narrow side gap. Big readability win for hub-and-spoke. The band **can** be a dashed container: a container's title band spans its full width, so an arrow dropping in has to pierce it, and TEXT_OVERLAP exempts a **vertical** segment whose edge has an endpoint geometrically inside that container. Enter such a zone from above or below, not by running an arrow **along** its title band — that still fires, and rightly so.
- **Run a balance pass, then trim the page.** Spread the bottom band across the full width (align its span with the top zones), tuck boxes under otherwise-empty corners, then shrink `pageWidth`/`pageHeight` to the content. Empty quadrants read as "unfinished".
- **Linear pipelines: a single numbered row.** Number the stages (`1.`, `2.`, …) left-to-right in one row with adjacent arrows; avoid wrapping to a second row (it forces an ugly return arrow). A stage that isn't part of the per-item flow (a standalone/batch mode) is styled like a pipeline box for consistency but **left unwired** from the main chain — it gets its own labelled edge to whatever it actually talks to.

## Edge styles beyond colour

The `edge()` helper supports a few options worth reaching for:

- **`jump=True`** adds `jumpStyle=gap` — the little hop draw.io draws over a crossed line. Use it as the cheap fix when a perpendicular crossing is unavoidable (the validator already treats perpendicular edge–edge crossings as fine; the jump just makes them read better) instead of rerouting.
- **`bidirectional=True`** puts arrowheads on both ends. Use it **sparingly** — arrows are one-way by default, and direction is part of how the diagram reads. Reserve it for the rare edge where flow genuinely goes both ways (read/write to a datastore, query/response, sync). Don't reach for it just because two components talk to each other.
- **`end_arrow=False`** drops the end arrowhead — for connector / bus / merge lines where two sources join a single producer line and a directional arrow would mislead.

## The validator checks

Checks are split into two severities. **Errors** fail the build (non-zero exit); **warnings** are advisory — they surface a real but often-tolerable issue and print without blocking. The CLI prints `✗` for errors and `⚠` for warnings and exits non-zero only when an error fired.

| Check | Severity | What it flags | Common cause |
| --- | --- | --- | --- |
| `CROSSING` | error | An edge segment passes through the interior (with a 2 px buffer) of a solid box that's neither the source nor the target. | Forgot a waypoint that routes around an intermediate box. |
| `OVERLAP` | error | Two edge segments share 8+ px on the same axis-aligned line (within 1.5 px perpendicular tolerance). | Two edges share an exit anchor, or two parallel routes share the same lane/channel without offset. |
| `TEXT_OVERLAP` | error | An edge segment passes through the top 28 px title band of a dashed container that's neither source nor target. **Exempt:** a *vertical* segment on an edge whose source or target box sits geometrically inside that container — entering a zone to reach a box in it isn't cutting across its title. | Routed an arrow *along* the top of a zone container instead of through the gap above it. (Entering the zone from above or below is fine.) |
| `LABEL_OVERLAP` | error | Two edge labels' estimated bounding boxes intersect by ≥8 px on their shorter axis (width ≈ 5.5 px/char at fontSize 10; HTML tags and `&nbsp;`/`&amp;`/`&lt;`/`&gt;`/`&quot;`/`&#39;` stripped before measuring). Sub-8 px grazes are skipped — the labels' white backgrounds mask them. | Two labels default-positioned at the same segment midpoint, or a `label_y` offset that lands one label on top of another. |
| `LABEL_BOX_OVERLAP` | warning | An edge label's bounding box overlaps a solid box (neither source nor target; containers exempt) by ≥8 px on its shorter axis. | A label parked over an unrelated box, or a side-channel label whose text extends back over the boxes it's routing past. Often reads fine thanks to the label's white background — hence a warning, not an error. |
| `SHORT_LABELLED_EDGE` | warning | A labelled edge's total rendered length is shorter than its own label's estimated text width (same ~5.5 px/char estimator, padding excluded). | Two boxes placed a 40 px gap apart with a 13-character label between them. The label overhangs *both* boxes — but by less than the 8 px `LABEL_BOX_OVERLAP` threshold on each side, and both are the edge's own endpoints, so nothing else sees it. Renders as a stub arrow with a floating caption. Fix by widening the gap or stacking the label into narrower `<div>` lines. |
| `DIAGONAL` | warning | An **interior** (waypoint-to-waypoint) segment is neither horizontal nor vertical. Anchor stubs are auto-squared into the L-bend draw.io renders, so this fires only when two explicit waypoints are offset on both axes — a route draw.io would square too, making it non-deterministic. | Two waypoints placed without an aligning corner between them. Add the intermediate waypoint. |
| `DANGLING` | error | An edge's `source` or `target` id doesn't resolve to any shape. | A typo in an id, or a box deleted/renamed without updating the edge. The edge would render detached in draw.io. |

When violations fire, the message includes the involved edge labels and the offending segment coordinates (and, for overlaps, the overlap size in px) — usually enough to identify the fix without opening the diagram.

**Stub-squaring.** The validator reconstructs each edge's rendered route, squaring the source and target *stubs* (anchor → first/last point) the same way draw.io's `orthogonalEdgeStyle` does. A short diagonal between a box anchor and its neighbouring waypoint is therefore not flagged — draw.io draws it as a clean L-bend, and so does the validator. This is why you don't need to hand-align every connection stub; only genuinely ambiguous interior diagonals warn.

The geometric thresholds (interior buffer, orthogonal tolerance, minimum overlap length, title-band height, label-width estimation) are defined as documented module constants at the top of `scripts/validate.py`. Tighten them for denser diagrams or loosen them if intentional parallel edges trip the checks — it's a one-line change in one place.

## Suggested colour palette

Source-coloured arrows work best when each box belongs to one semantic category. Substitute your own categories — the constants below are illustrative. Each light constant has an optional `_DARK` variant chosen for contrast on the dark canvas (see "Colour: contrast and clarity"); pass it as `fill_dark` / `color_dark` where the base colour would wash out.

| Constant | Light | `_DARK` (for contrast) | Suggested for |
| --- | --- | --- | --- |
| `COLOR_PRIMARY_BLUE` | `#0078d4` | `#4da3ff` | External clients, primary cloud / SaaS infrastructure |
| `COLOR_FUTURE_GREY` | `#9e9e9e` | *(grey both themes)* | Future-state / out-of-scope shapes and arrows |
| `COLOR_CONFIG_GOLD` | `#bf8f00` | `#ffd966` | Configuration source, git repo, secrets |
| `COLOR_ORCH_PURPLE` | `#5b3fbf` | `#b59dff` | Orchestrator, background worker, pipeline (stroke colour — the pale `#8e7cc3` fill is too light as a line) |
| `COLOR_FRONTEND_GREEN` | `#34a853` | *(reads in both — keep)* | User-facing / frontend service |
| `COLOR_DATASTORE_NAVY` | `#003c71` | `#7fb3e6` | Datastore, index, queue, cache |
| `COLOR_GATEWAY_ORANGE` | `#d04a02` | *(reads in both — keep)* | Gateway, service mesh, auth tier |
| `COLOR_CONSUMER_PURPLE` | `#9c27b0` | `#d18cff` | External consumer / downstream subscriber |

## Routing strategy

For any diagram with more than a handful of edges, pre-allocate corridors:

1. **Horizontal lanes** between rows of boxes — y-coordinates that no box occupies. Multiple edges can share a lane if their x-ranges don't overlap; if they do overlap, offset the lanes by 5+ px (e.g. `y=265` and `y=270`).
2. **Vertical sub-channels** in the gaps between containers — x-coordinates outside every container. The three-tier example uses `x=370` (gap between External and Application zones) and `x=885/890/895` (gap between Application and Data zones).
3. **Side channels** outside the rightmost or below the bottommost container for edges that need to skip past data-tier boxes (e.g. `x=1230` in the example, for the future-state replication arrow).

**Write the corridor allocation down in the generator.** Put a comment block at the top listing the reserved lanes and channels (`y=225 lane — pipeline fan-in`, `x=850 channel — app → data`), and name the lane in each edge's own comment. This is not decoration: when you later widen a column gap or shift a row, the edit becomes mechanical because you know exactly which waypoints move. Diagrams built without it get re-derived from scratch on every layout tweak.

The example file's edge comments call out which lane and channel each edge uses — read it as a worked specification, not just a sample.

## Patterns for richer diagrams

The bundled example keeps to one clean layout, but production diagrams often use these patterns. All are supported by the existing helpers — no new code needed.

**Numbered sequential steps.** For a linear pipeline, prefix box labels with `1.`, `2.`, … and lay them out left-to-right in a **single row** (avoid wrapping to a second row — it forces an ugly return arrow). The numbers carry the sequence, so you need fewer arrows between steps. See "Layout & semantics" for the in-row-but-unwired treatment of standalone stages.

**Nested containers.** A sub-system inside a zone is just a second dashed container positioned inside the outer one's bounds (both `parent="1"` — draw.io renders the nesting visually from the geometry). The validator handles it: an edge crossing the *inner* container's title band still fires TEXT_OVERLAP.

```python
container(380, 92, 500, 496, "Application Tier", stroke="#5b3fbf")
container(410, 430, 440, 130, "Service Mesh", stroke="#5b3fbf")  # nested inside
```

**Mid-route inline labels.** On a long multi-segment route, the default label sits at the midpoint of the longest segment — which may not read well. Nudge it onto a specific segment with `label_x` / `label_y` so it sits next to the relevant hop (e.g. an "OCR Call" label beside the segment leaving the orchestrator, not floating mid-canvas).

**Future-state context sentences.** Grey/dashed future boxes can carry a short sentence of context (*why* it's deferred or *what* it will do), not just the name — draw.io wraps it inside the box. Size the box for the wrapped text (roughly `width / 6` characters per line at fontSize 10–11). Still no `Future` label on the *arrows*; the shape styling plus the legend cover that.

## Limitations

The validator is a 2D geometric check with a few known blind spots. None of these are bugs; document them in PRs if you hit one.

- **Non-rectangular containers.** The validator detects containers as `rectangle + dashed stroke`. Ellipses, swimlane shapes, and BPMN groups are treated as solid boxes and will trip CROSSING if an arrow passes through them. Use rectangular dashed containers for zones, or wrap an ellipse in a transparent dashed rectangle.
- **Intentional parallel edges.** Two edges that *should* run side by side (e.g. "request" and "response" on the same connection) need to be at least 5 px apart on the perpendicular axis. Below 1.5 px the validator merges them into one segment for OVERLAP purposes; 1.5–5 px clears the validator but is visually hard to distinguish.
- **CJK and heavily-styled HTML labels.** Width estimation uses `5.5 px/char` calibrated for Latin sans-serif at fontSize 10. Chinese/Japanese/Korean characters are wider; HTML tags are stripped before counting but `<font>`/`<b>`/inline styles aren't measured. For diagrams with mostly-CJK labels, expect occasional false negatives on LABEL_OVERLAP and tune `label_x`/`label_y` by hand.
- **Edge ordering matters for layering.** Boxes must be emitted before edges in the XML for labels to render on top. The bundled `edge()` helper relies on the caller to call `box()` first.
- **A clean validate says nothing about whether labels have *room*.** `SHORT_LABELLED_EDGE` catches the extreme case (label wider than its whole edge), but a label that technically fits in a 50 px column gap while looking cramped, or one whose estimated width is a character or two off the truth, passes silently. Render the PNG and look at it — that pass catches label-geometry problems no check sees.
- **Colour, contrast, and dark-mode legibility are invisible to the validator.** It ignores colour entirely, and `light-dark()` is a runtime function. A clean validate says nothing about whether either theme is readable — see "Colour: contrast and clarity". `preview.py` renders the light theme only.
- **Semantic correctness is a human review item.** A managed service drawn inside a cluster zone, a mislabeled flow, or the wrong trust boundary all validate fine. "Validates clean" is necessary, not sufficient — the finishing pass (theme, label wording, zone membership, balance) is done by eye in Desktop.
- **Desktop round-trip artifacts are normal.** After hand-editing in draw.io Desktop, a re-saved file picks up fractional `entryX`/`exitX` (e.g. `0.911`), explicit `entryPerimeter=0`, `sourcePoint`/`targetPoint` mxPoints, separate `edgeLabel` child cells, and `host="Electron"`. These are harmless — don't "fix" them. Treat the generator output as a clean, validated **baseline to refine in Desktop**; if you need to change it, regenerate from the script rather than diffing against the hand-tuned XML.

## Why no Python library?

This skill keeps the helpers (`container`, `box`, `edge`, `sub`, `desc`) vendored inline in `assets/build_template.py` and the example, rather than abstracting them into a `pip install`-able library. Reasons:

- Skills are meant to be self-contained drops into `~/.claude/skills/`; a `pip` dependency would defeat that.
- The helpers are ~80 lines total. The cognitive cost of copying them is lower than the cost of managing a pinned dependency that changes underneath downstream diagrams.
- Each generator script tends to grow custom variants of `box()` (e.g. with extra fontSize controls, gradient fills) that would be awkward to retrofit into a shared library.

If you find yourself copying the helpers across many diagrams in the same repo, factor *those repo-internal helpers* into a local module — but don't take the skill in that direction.

**Expect the host repo's formatter to reflow the vendored helpers.** `ruff format` / `black` at a 100-char line length will explode the compact multi-arg signatures onto one-arg-per-line, taking the helpers from ~80 lines to ~200. That's correct behaviour — run the repo's formatter and commit the result; don't fight it, and don't try to diff the copy against this skill's template to check for drift (the reflow makes that diff useless). If you want a skill update, re-copy the template and re-apply your local customisations.

## Installation

This skill follows the [Claude skill anatomy](https://docs.claude.com/en/docs/build-with-claude/skills) (SKILL.md + `scripts/` + `assets/` + `references/`).

To package the skill as a `.skill` file (a zip with a `.skill` extension) for upload to Claude, either:

- Zip the folder from its parent directory (works anywhere):

  ```bash
  cd <parent-of-drawio>
  zip -r drawio.skill drawio -x '*/__pycache__/*' '*/.pytest_cache/*'
  ```

- Or, if the `skill-creator` skill is installed, run its `package_skill.py`
  (validates frontmatter first). Its exact path depends on where skill-creator
  is installed in your environment.

Either way the archive must contain `drawio/SKILL.md`, `drawio/scripts/...`, etc. at its root (not nested under a wrapper folder). The exact upload path inside the Claude UI changes occasionally — check the current docs at https://docs.claude.com/en/docs/build-with-claude/skills for the latest. See `CONTRIBUTING.md` for the full packaging and install loop.

For local-only use with Claude Code, drop the unpacked skill folder into `~/.claude/skills/drawio/`. Restart Claude Code to pick it up.

## Running the tests

```bash
cd drawio
python -m pytest        # runs all 34 tests
```

`tests/test_render_png.py` covers `render_png.py`'s argument contract (`-o` / `--output`, and every invocation it rejects), faking `subprocess.run` at the system boundary so it runs without the draw.io CLI installed. `tests/test_validate.py` covers each validator check independently (a clean fixture plus one fixture per failure mode), the exemption guards (stub-squaring, point-anchored edges, and entering a container from above — each of which must NOT fire), a narrow-exemption guard (a segment running *along* a title band still fires even when both endpoints are inside the container), label-normalisation cases, plus a regression test that runs `examples/build_three_tier_web.py` end-to-end and asserts a clean validation. If you change `scripts/validate.py` or `scripts/render_png.py`, run the tests before committing.
