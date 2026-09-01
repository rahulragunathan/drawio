---
name: drawio
version: 1.4.2
description: Use this skill whenever the user wants to generate, validate, or modify architecture diagrams as draw.io (.drawio / diagrams.net) XML files. Trigger on any mention of .drawio, draw.io, diagrams.net, or requests for architecture diagrams where routing control matters — for example, when auto-layout tools (Lucid, Mermaid, Graphviz) have produced arrows that cross boxes, overlap labels, or pile into a single corridor. The skill emits explicit waypoints, anchor coordinates, and label offsets so routing is deterministic, then runs a nine-check geometric validator (CROSSING, OVERLAP, TEXT_OVERLAP, LABEL_OVERLAP, LABEL_BOX_OVERLAP, SHORT_LABELLED_EDGE, DIAGONAL, DANGLING, UNKNOWN_ICON). Diagrams can carry real vendor logos — AWS, Azure, GCP, Kubernetes, Cisco — from draw.io's own stencil library, or any logo you supply as an SVG. Use this skill even if the user only says 'architecture diagram' or 'system diagram' without naming draw.io — it produces .drawio output that opens at app.diagrams.net without auth and round-trips through draw.io Desktop without diff churn. Also use it when validating, fixing, or PNG-rendering an existing .drawio file.
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
| `scripts/validate.py` | Geometric validator. Nine checks: CROSSING, OVERLAP, TEXT_OVERLAP, LABEL_OVERLAP, LABEL_BOX_OVERLAP, SHORT_LABELLED_EDGE, DIAGONAL, DANGLING, UNKNOWN_ICON. Run on any `.drawio` file. |
| `scripts/render_png.py` | Renders `.drawio` → `.png` via the draw.io Desktop CLI (`foo.drawio` → `foo.png`; `-o path.png` to send it elsewhere; `--theme dark\|light\|auto`). Needs `drawio` on PATH (macOS auto-detects the app bundle). Pixel-accurate. |
| `scripts/preview.py` | Offline preview renderer. Reuses `validate.py`'s geometry, so it shows exactly what the validator sees. Approximate text wrapping — trust it for layout, not final fidelity. **Needs `matplotlib`**, which the rest of the skill does not — in a project venv without it, reach for `render_png.py` instead (the draw.io CLI is a system binary, not a venv dependency). |
| `scripts/render_examples.py` | Rebuilds every example, validates it, and writes `renders/<name>-light.png` and `-dark.png`. Run at the end of a piece of work: a render is where you see the problems no check can catch. |
| `scripts/package_skill.py` | Builds `../drawio.skill`, the uploadable archive. Run it at the end of a phase so the package matches the commit. |
| `scripts/list_icons.py` | Browse the icon catalog (`--search redis`), or refresh it against a newer draw.io (`--verify`, `--refresh`). Only the refresh modes need draw.io installed. |
| `references/icons.md` | The icon catalog: 128 curated vendor icons with brand colours. Read it to pick an icon. |
| `assets/icon_names.txt.gz` | Every icon name draw.io ships (~11,500), used by `UNKNOWN_ICON` to tell a typo from a real name. Generated; do not hand-edit. |
| `assets/build_template.py` | Minimal starter generator. Copy, rename, customise. Vendors the helpers (`container`, `box`, `edge`, `sub`, `desc`, `icon_box`, `icon_node`, `svg_icon`) inline. |
| `examples/build_three_tier_web.py` | Comprehensive worked example: three-tier web app, 11 solid boxes, 11 edges, every locked convention exercised. Validates clean. |
| `examples/build_aws_vpc_pipeline.py` | Worked example **with vendor icons**: an AWS pipeline, a VPC nested inside a cloud zone, and one embedded SVG for a logo draw.io does not ship. Validates clean. |
| `tests/test_validate.py` | Pytest suite — one minimal fixture per validator check, guards for each exemption, plus a regression test on the bundled example. |
| `tests/fixtures/builders.py` | Fixture builders that produce minimal `.drawio` files exhibiting exactly one violation type each. |

## Workflow

1. **Copy the template.** `cp assets/build_template.py my-diagram.py`. Edit constants, containers, boxes, then edges.
2. **Build.** `python my-diagram.py`. For a vendor logo, find its key first: `python scripts/list_icons.py --search lambda`. The script writes a `.drawio` file (default: cwd).
3. **Validate.** `python scripts/validate.py my-diagram.drawio`. Fix violations (see the failure-mode table below).
4. **Open.** Drop the file at https://app.diagrams.net (no auth) or open it in draw.io Desktop. The diagram round-trips without diff churn — if you edit in Desktop and save, your generator can read the result back.
5. **(Optional) Preview inline.** `python scripts/preview.py my-diagram.drawio` renders an approximate PNG with only matplotlib (which is *not* a dependency of the rest of the skill — in a project venv you'll often find `render_png.py` is the available path) — handy when the draw.io CLI isn't available (sandboxes, VMs). It draws the exact geometry the validator checks, so it's reliable for judging routing, lane spacing, and label placement. **It does not wrap box text the way draw.io does** — long box descriptions will overflow in the preview but wrap correctly in real draw.io, so don't trim box text based on a preview overflow alone.
6. **Render the PNG and look at it.** `python scripts/render_png.py my-diagram.drawio` writes `my-diagram.png` (pixel-accurate; needs the draw.io Desktop CLI on PATH). Add `-o docs/architecture.png` when the rendered PNG is committed somewhere other than beside its source — it creates missing parent directories, and takes exactly one input. Treat this as part of the loop, not an optional extra — a clean validate says nothing about whether labels have *room*, whether column gaps are cramped, or whether either theme is legible. Looking at the render is what catches those.

## Locked conventions

These are non-negotiable; the validator, the example, and the helpers all assume them.

- **Arrow colour matches the source box** (or its stroke if the fill is too light to read as a line). This is the single rule that makes a dense diagram readable — readers can follow flow by colour without re-reading labels.
- **Future-state shape = grey/dashed; future-state arrow = grey/dashed**, NO `Future` text label. The legend strip at the bottom carries the meaning. Pass `dashed=True` to `box()` for the shape; use `style="dashed"` on `edge()` for the arrow.
- **Edges are emitted AFTER boxes** so labels render on top. (The XML order matters in draw.io.)
- **Every labelled edge carries a background plate.** `edge()` sets one automatically; without it a label is illegible where the line runs under the text. Pass `label_bg` to match the zone the label sits over — a white plate on a tinted container reads as a sticker, while a matching one still masks the line and disappears.
- **Multi-line edge labels use `<div>` tags, NOT `\n`.** draw.io Desktop loses `\n` on round-trip; `<div>` survives. Example: `label="Route<div>Request</div>"`.
- **Subheadings use `sub()`** — italicised Title Case with an explicit `font-size` in the span style. Without explicit `font-size`, draw.io Desktop drops back to its default and the diagram looks inconsistent.
- **Description bodies use `desc()`** — sentence case, non-bold, with explicit `font-size`. Same round-trip reason.
- **Reserve horizontal corridors and vertical sub-channels** for parallel flows. Two edges sharing a corridor must offset by at least 5 px on the perpendicular axis (OVERLAP fires below 1.5 px tolerance, but 5 px gives comfortable visual separation).
- **Choose colours for contrast and clarity.** One colour per category; let draw.io handle its own dark theme. See "Colour: contrast and clarity" below.
- **Edge labels are verb-first and Title Case.** Prefer imperatives ("Call OCR", "Publish Events", "Reads Index") over noun fragments ("OCR call"). Literal protocol and command tokens keep their real casing — HTTPS, PUT, COPY — because those are names, not prose.
- **Stack a label when it does not fit, not by taste.** Two rules: (1) if the label is wider than its edge is long, stack it — `SHORT_LABELLED_EDGE` reports the exact pixels, e.g. *"is 40px long but its label needs ~66px"*; (2) on a vertical edge running through a channel, stack it so the text does not spill sideways over neighbours, which `LABEL_BOX_OVERLAP` catches. A label on a long horizontal edge needs neither.
- **A label belongs to what it describes.** The default position is the midpoint of the edge's *longest* segment, which on an L-shaped route often lands over an unrelated box. Nudge it with `label_x` / `label_y` until it reads as belonging to its own line. No check can see this — only a render can.
- **Never dash an `icon_node()`.** `dashed=1` plus `verticalAlign=top` is exactly the validator's container signature, so a dashed icon node is silently reclassified as a zone. Grey the fill for a future-state icon instead.
- **Always give a wrapper icon its brand colour.** `icon_fill` on `icon_box()`, `fill` on `icon_node()`. A tile with no fill renders as a blank white plate — valid XML, clean validate, obviously wrong on screen.
- **Keep the legend lean.** Colour + labels carry the meaning. Only state what a reader can't infer — in practice just "grey/dashed shape = future state", and nothing at all if there are no future shapes. Don't enumerate line styles the diagram uses.

## Colour: contrast and clarity

**The goal is clear contrast and legibility — not a particular palette.** Colours exist to separate categories and let a reader follow flow at a glance. Pick whatever reads cleanly.

- **Emit one colour per thing.** Do not hand-author a dark variant. draw.io inverts colours for its own dark theme, and it does that better than the skill's previous `light-dark()` handling did — measured by exporting the same diagram both ways.
- **Never set an explicit colour on an edge label.** An explicit `<font color>` opts the label out of draw.io's inversion, which is exactly how a label ends up as dark text on a dark canvas. `edge()` no longer emits one.
- **Match text to its fill.** White text on a pale fill is unreadable in any theme; that is a plain contrast question, not a theme question.
- **`validate.py` ignores colour entirely** and `preview.py` renders an approximation. A clean validate says **nothing** about whether the diagram is legible — render the PNG and look at it.

A starting palette. Substitute your own categories:

| Category | Colour |
| --- | --- |
| Source / primary cloud | `#0078d4` |
| Config / repo | `#bf8f00` |
| Orchestrator / pipeline | `#5b3fbf` |
| Datastore / index | `#003c71` |
| Downstream consumer | `#9c27b0` |
| Frontend / users | `#34a853` |
| Gateway | `#d04a02` |
| Future-state shape | `#e0e0e0` fill, `#9e9e9e` stroke, `dashed=1` |

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

## Vendor logos and icons

**Plain boxes and logo icons are both first-class.** Use plain `box()` when the
shapes are generic or vendor-neutral — "Web Service", "Message Queue", a trust
boundary. Use an icon when the diagram is about *specific named services*, where
an AWS Lambda mark says in one glyph what a label would spend three words on.
Logos are additive: `box()` and `container()` are unchanged, so a diagram without
them behaves exactly as it always did.

### The two placements

```python
# Default: glyph inside a labelled card. The card keeps the exact geometry,
# anchors and routing of a plain box(), so icons cost nothing in layout terms.
icon_box(
    620,
    160,
    220,
    64,
    "<b>Fargate</b>",
    fill=COMPUTE,
    icon="aws:fargate",
    icon_fill=COMPUTE,
)

# Alternative: bare glyph with its name underneath, the vendor-docs look.
icon_node(620, 160, "Fargate", icon="aws:fargate", fill=COMPUTE)
```

**Prefer `icon_box()`.** An `icon_node()` caption is wider than the 48 px glyph
it belongs to, so an edge leaving the glyph's bottom runs through its own label.
The validator catches it (CROSSING names the caption), but the fix is layout, and
`icon_box()` avoids the problem entirely by keeping the label inside the card.
Reach for `icon_node()` when you want the vendor-reference-architecture look and
can route edges sideways.

### Choosing an icon

The helpers take `family:name` — `aws:lambda`, `azure:compute/Function_Apps.svg`,
`gcp:bigquery`, `k8s:pod`, `cisco:l3_switch`. Six families are known: `aws`,
`azure`, `gcp`, `k8s`, `cisco`, `net`.

`python scripts/list_icons.py --search redis` finds an entry, but **it prints the
catalog's row key, not the argument.** The catalog spells the same icon with a
hyphen (`aws-lambda`); the helpers need a colon (`aws:lambda`). Swap the first
hyphen for a colon before pasting. Passing the hyphen form raises
`KeyError` — the two spellings are tracked as KI-01.

The catalog holds 128 curated entries, but **any** of draw.io's ~11,500 names
works — it is a shortlist, not a whitelist. For a name outside the curated
families, use the escape hatch:

```python
icon_box(..., icon=raw_icon(shape="mxgraph.veeam.vbr"))
icon_box(..., icon=raw_icon(image="img/lib/ibm/analytics/analytics.svg"))
```

`UNKNOWN_ICON` still verifies the name, so a typo is caught either way.

Pass the vendor's brand colour as `icon_fill`. A wrapper tile with no fill
renders as a **blank white plate** — the most common icon mistake after a
mistyped name, and one only a render will show you.

### A logo draw.io does not ship

```python
icon_box(
    40, 320, 200, 64, "<b>Snowflake</b>", fill=SNOW, icon=svg_icon("snowflake.svg")
)
```

`svg_icon()` embeds the file as a base64 data URI, so the artwork travels inside
the `.drawio`. Use it for anything outside the bundled sets — Snowflake,
Databricks, Datadog, a client's mark.

### What a logo costs

A stencil name (`shape=mxgraph.aws4.lambda`) and a bundled image path are
*references*: the artwork lives in draw.io, not in your file. That is fine
wherever the file is opened — app.diagrams.net and Desktop both ship the same
library — but a non-draw.io renderer draws nothing. `svg_icon()` has no such
dependency, and neither does a plain `box()`.

## The validator checks

Checks are split into two severities. **Errors** fail the build (non-zero exit); **warnings** are advisory — they surface a real but often-tolerable issue and print without blocking. The CLI prints `✗` for errors and `⚠` for warnings and exits non-zero only when an error fired.

| Check | Severity | What it flags | Common cause |
| --- | --- | --- | --- |
| `CROSSING` | error | An edge segment passes through the interior (with a 2 px buffer) of a solid box that's neither the source nor the target — including the caption band beneath a bottom-labelled icon. The source/target exemption covers the **shape** only: an edge crossing its *own* caption still fires, because a caption is text, not a connection surface. A glyph nested inside a card is skipped, since the card is already checked at those coordinates. | Forgot a waypoint that routes around an intermediate box; or wired two captioned `icon_node()` glyphs vertically, which strikes a line through both labels. |
| `OVERLAP` | error | Two edge segments share 8+ px on the same axis-aligned line (within 1.5 px perpendicular tolerance). | Two edges share an exit anchor, or two parallel routes share the same lane/channel without offset. |
| `TEXT_OVERLAP` | error | An edge segment passes through the top 28 px title band of a dashed container that's neither source nor target. **Exempt:** a *vertical* segment on an edge whose source or target box sits geometrically inside that container — entering a zone to reach a box in it isn't cutting across its title. | Routed an arrow *along* the top of a zone container instead of through the gap above it. (Entering the zone from above or below is fine.) |
| `LABEL_OVERLAP` | error | Two edge labels' estimated bounding boxes intersect by ≥8 px on their shorter axis (width ≈ 0.55 × the label's own fontSize per char; HTML tags and `&nbsp;`/`&amp;`/`&lt;`/`&gt;`/`&quot;`/`&#39;` stripped before measuring). Sub-8 px grazes are skipped — the labels' white backgrounds mask them. | Two labels default-positioned at the same segment midpoint, or a `label_y` offset that lands one label on top of another. |
| `LABEL_BOX_OVERLAP` | warning | An edge label's bounding box overlaps a solid box (neither source nor target; containers exempt) by ≥8 px on its shorter axis. | A label parked over an unrelated box, or a side-channel label whose text extends back over the boxes it's routing past. Often reads fine thanks to the label's white background — hence a warning, not an error. |
| `SHORT_LABELLED_EDGE` | warning | A labelled edge's total rendered length is shorter than its own label's estimated text width (same per-character estimator, scaled to the label's fontSize, padding excluded). | Two boxes placed a 40 px gap apart with a 13-character label between them. The label overhangs *both* boxes — but by less than the 8 px `LABEL_BOX_OVERLAP` threshold on each side, and both are the edge's own endpoints, so nothing else sees it. Renders as a stub arrow with a floating caption. Fix by widening the gap or stacking the label into narrower `<div>` lines. |
| `DIAGONAL` | warning | An **interior** (waypoint-to-waypoint) segment is neither horizontal nor vertical. Anchor stubs are auto-squared into the L-bend draw.io renders, so this fires only when two explicit waypoints are offset on both axes — a route draw.io would square too, making it non-deterministic. | Two waypoints placed without an aligning corner between them. Add the intermediate waypoint. |
| `DANGLING` | error | An edge's `source` or `target` id doesn't resolve to any shape. | A typo in an id, or a box deleted/renamed without updating the edge. The edge would render detached in draw.io. |
| `UNKNOWN_ICON` | warning | A cell's stencil, `resIcon`/`prIcon` or image name is not one draw.io ships, or it is a remote URL that only renders where the host is reachable. Suggests the closest real name. | A mistyped stencil name — which draw.io renders as an empty shape and reports no error for, so nothing else catches it. Skipped entirely when `assets/icon_names.txt.gz` is missing. |

When violations fire, the message includes the involved edge labels and the offending segment coordinates (and, for overlaps, the overlap size in px) — usually enough to identify the fix without opening the diagram.

**Stub-squaring.** The validator reconstructs each edge's rendered route, squaring the source and target *stubs* (anchor → first/last point) the same way draw.io's `orthogonalEdgeStyle` does. A short diagonal between a box anchor and its neighbouring waypoint is therefore not flagged — draw.io draws it as a clean L-bend, and so does the validator. This is why you don't need to hand-align every connection stub; only genuinely ambiguous interior diagonals warn.

The geometric thresholds (interior buffer, orthogonal tolerance, minimum overlap length, title-band height, label-width estimation) are defined as documented module constants at the top of `scripts/validate.py`. Tighten them for denser diagrams or loosen them if intentional parallel edges trip the checks — it's a one-line change in one place.

## Suggested colour palette

Source-coloured arrows work best when each box belongs to one semantic category. Substitute your own categories — the constants below are illustrative.

| Constant | Colour | Suggested for |
| --- | --- | --- |
| `COLOR_PRIMARY_BLUE` | `#0078d4` | External clients, primary cloud / SaaS infrastructure |
| `COLOR_FUTURE_GREY` | `#9e9e9e` | Future-state / out-of-scope shapes and arrows |
| `COLOR_CONFIG_GOLD` | `#bf8f00` | Configuration source, git repo, secrets |
| `COLOR_ORCH_PURPLE` | `#5b3fbf` | Orchestrator, background worker, pipeline (stroke colour — the pale `#8e7cc3` fill is too light as a line) |
| `COLOR_FRONTEND_GREEN` | `#34a853` | User-facing / frontend service |
| `COLOR_DATASTORE_NAVY` | `#003c71` | Datastore, index, queue, cache |
| `COLOR_GATEWAY_ORANGE` | `#d04a02` | Gateway, service mesh, auth tier |
| `COLOR_CONSUMER_PURPLE` | `#9c27b0` | External consumer / downstream subscriber |

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
- **CJK and heavily-styled HTML labels.** Width estimation uses `0.55 × fontSize` per character, calibrated for Latin sans-serif. Chinese/Japanese/Korean characters are wider; HTML tags are stripped before counting but `<font>`/`<b>`/inline styles aren't measured. For diagrams with mostly-CJK labels, expect occasional false negatives on LABEL_OVERLAP and tune `label_x`/`label_y` by hand.
- **Edge ordering matters for layering.** Boxes must be emitted before edges in the XML for labels to render on top. The bundled `edge()` helper relies on the caller to call `box()` first.
- **A clean validate says nothing about whether labels have *room*.** `SHORT_LABELLED_EDGE` catches the extreme case (label wider than its whole edge), but a label that technically fits in a 50 px column gap while looking cramped, or one whose estimated width is a character or two off the truth, passes silently. Render the PNG and look at it — that pass catches label-geometry problems no check sees.
- **Colour and contrast are invisible to the validator.** It ignores colour entirely. A clean validate says nothing about whether the diagram is readable — render the PNG and look at it.
- **Icons are references, not artwork.** A stencil name or a bundled image path resolves against the renderer: fine in draw.io (browser or Desktop), blank in anything else. `svg_icon()` embeds its bytes and has no such dependency. `UNKNOWN_ICON` verifies a name against the draw.io build the catalog was generated from, so a genuinely newer stencil warns until you run `list_icons.py --refresh`.
- **`preview.py` draws icons as placeholders, not glyphs.** It shows where an icon sits and how much space it takes, labelled with the icon's short name. It also greys any colour matplotlib cannot parse rather than failing. Render the PNG to see the real logo and the real colours.
- **A blank icon plate validates clean.** A wrapper tile with no `icon_fill` renders as an empty white square; the XML is valid and every check passes. Only a render shows it.
- **Semantic correctness is a human review item.** A managed service drawn inside a cluster zone, a mislabeled flow, or the wrong trust boundary all validate fine. "Validates clean" is necessary, not sufficient — the finishing pass (theme, label wording, zone membership, balance) is done by eye in Desktop.
- **Desktop round-trip artifacts are normal.** After hand-editing in draw.io Desktop, a re-saved file picks up fractional `entryX`/`exitX` (e.g. `0.911`), explicit `entryPerimeter=0`, `sourcePoint`/`targetPoint` mxPoints, separate `edgeLabel` child cells, and `host="Electron"`. These are harmless — don't "fix" them. Treat the generator output as a clean, validated **baseline to refine in Desktop**; if you need to change it, regenerate from the script rather than diffing against the hand-tuned XML.

## Why no Python library?

This skill keeps the helpers (`container`, `box`, `edge`, `sub`, `desc`) vendored inline in `assets/build_template.py` and the example, rather than abstracting them into a `pip install`-able library. Reasons:

- Skills are meant to be self-contained drops into `~/.claude/skills/`; a `pip` dependency would defeat that.
- The helpers are ~80 lines total. The cognitive cost of copying them is lower than the cost of managing a pinned dependency that changes underneath downstream diagrams.
- Each generator script tends to grow custom variants of `box()` (e.g. with extra fontSize controls, gradient fills) that would be awkward to retrofit into a shared library.

If you find yourself copying the helpers across many diagrams in the same repo, factor *those repo-internal helpers* into a local module — but don't take the skill in that direction.

**The vendored helpers are already `ruff format`-clean at 88 columns**, so a host repo running `ruff format` or `black` should leave them alone rather than reflowing them — which also means a copy stays diffable against this template. At a different line length you will still see churn; that's correct behaviour, so run the repo's formatter and commit the result. To pick up a skill update, re-copy the template and re-apply your local customisations.

## Installation

This skill follows the [Claude skill anatomy](https://docs.claude.com/en/docs/build-with-claude/skills) (SKILL.md + `scripts/` + `assets/` + `references/`).

To package the skill as a `.skill` file (a zip with a `.skill` extension) for upload to Claude:

```bash
python scripts/package_skill.py     # writes ../drawio.skill
```

It roots the archive at `drawio/`, so the result contains `drawio/SKILL.md`,
`drawio/scripts/...` and so on — never nested under a wrapper folder. It drops
every hidden entry (`.git`, `.venv`, `.gitignore`, tool caches) by rule rather
than by name, plus `renders/` and `docs/`.

**Do not build the zip by hand.** The exclusion list is the part that goes
wrong: hand-built archives have shipped `.gitignore` and tool caches.

Bump the `version:` field in this file's frontmatter before packaging — the
Skills UI reads the displayed version from there, not from the archive filename.
The exact upload path inside the Claude UI changes occasionally; check
https://docs.claude.com/en/docs/build-with-claude/skills for the current one.

For local-only use with Claude Code, drop the unpacked skill folder into `~/.claude/skills/drawio/`. Restart Claude Code to pick it up.

## Running the tests

```bash
cd drawio
python -m pytest        # runs all 94 tests
```

`tests/test_render_png.py` covers `render_png.py`'s argument contract (`-o` / `--output`, and every invocation it rejects), faking `subprocess.run` at the system boundary so it runs without the draw.io CLI installed. `tests/test_validate.py` covers each validator check independently (a clean fixture plus one fixture per failure mode), the exemption guards (stub-squaring, point-anchored edges, and entering a container from above — each of which must NOT fire), a narrow-exemption guard (a segment running *along* a title band still fires even when both endpoints are inside the container), label-normalisation cases, plus a regression test that runs `examples/build_three_tier_web.py` end-to-end and asserts a clean validation. If you change `scripts/validate.py` or `scripts/render_png.py`, run the tests before committing.
