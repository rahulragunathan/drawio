# `drawio` skill — feedback from first production use

**Context:** built the SupernoteExport architecture diagram (3 dashed zones, 13 boxes,
14 edges, plus an unzoned "external dependencies" row). Validated clean, rendered via the
draw.io Desktop CLI. Written 2026-07-17.

**Overall: the skill worked.** The diagram validated with zero violations on the *first*
run, and the routing-corridor discipline (pre-allocating lanes before writing any edges)
is what made that possible. The locked conventions — source-coloured arrows, edges after
boxes, `<div>` labels — all did what they claim. The notes below are the friction points.

---

## 1. The documented "bottom service band" pattern contradicts the TEXT_OVERLAP check

**This is the one real bug.** SKILL.md's "Layout & semantics" section says:

> **Bottom service band for many-to-few fan-in.** When many pipeline stages call a few
> shared services, lay the shared services in a horizontal band along the **bottom** and
> drop straight down into them, rather than fanning every arrow into one narrow side gap.

But TEXT_OVERLAP fires on:

> An edge segment passes through the top 28 px title band of a dashed container **that's
> neither source nor target.**

A dashed container's title band spans its **full width**. So *any* edge dropping "straight
down into" a box inside a bottom band container must cross that container's title band —
and the container is never the edge's source or target (the *box inside it* is). The
recommended pattern therefore cannot validate.

I hit this trying to wrap `supernotelib` / `mlx-vlm` / model-weights in an
`External dependencies` zone. Every arrow from the pipeline down into it errored.

**Workaround I used:** dropped the container entirely and left the three boxes as an
unzoned row, conveying "external" through fill colour and italic subtitles instead. It
looks fine, but I lost the trust-boundary framing the skill elsewhere argues for.

**Suggested fixes, in preference order:**

1. **Exempt edges whose source or target is a descendant of the container** (geometrically
   contained within its bounds). This is the semantically correct rule: an arrow entering a
   zone to reach a box inside it isn't "cutting across" the zone's title. This is a small
   change and would make the documented pattern work.
2. Failing that, exempt the portion of the title band **not occupied by the title text**.
   The band is 28px × full-width, but the text only occupies roughly
   `12px + len(title) * ~7px` from the left. An arrow dropping in at x=900 of a 1200px-wide
   zone isn't near the text.
3. At minimum, **document the conflict** in the bottom-band bullet: "note that the band
   cannot be a dashed container — see TEXT_OVERLAP — so use bare boxes or enter from the
   side."

---

## 2. Proposed new check: labelled edge shorter than its own label

**The failure the validator missed.** I placed two boxes with a 40px horizontal gap and a
labelled edge between them ("Loads / caches", ~13 chars ≈ 72px estimated width). The
validator reported **0 errors, 0 warnings**. The render was visibly broken: a stub arrow
with a label floating over both boxes, reading as an unconnected caption.

LABEL_BOX_OVERLAP is the check that should have caught it and didn't — the label
overhangs each box by less than the 8px minimum-overlap threshold on its shorter axis, so
it's skipped as a "graze". But two sub-8px grazes on *both* sides of a too-short edge is
not a graze; it's a label with nowhere to live.

**Suggested check** (warning severity):

```
SHORT_LABELLED_EDGE — a labelled edge's total rendered length is less than the
estimated width of its own label (reuse LABEL_OVERLAP's ~5.5 px/char estimator).
```

Cheap to implement, reuses machinery that already exists, and catches a failure mode that
is *invisible* to every current check. I fixed it by widening the gap 40px → 110px.

More generally: this is worth a line in "Limitations" — **a clean validate says nothing
about whether labels have room.** The skill already says this about colour; the same
caveat applies to label geometry. Rendering and *looking* at the PNG caught two problems
the validator was blind to (this one, plus cramped labels in 50px column gaps).

---

## 3. `render_png.py` emits a double extension

`render_png.py foo.drawio` writes **`foo.drawio.png`**, not `foo.png`. Every use needs a
follow-up `mv`, which is easy to forget and ends up in committed filenames.

**Suggested fix:** strip a trailing `.drawio` before appending `.png`, or add an
`--output` flag. One-liner, removes a papercut from every single invocation.

---

## 4. Vendored helpers fight a repo formatter

SKILL.md's "Why no Python library?" argues the helpers are "~80 lines total" and cheap to
copy. True — but the moment the generator lands in a repo with a configured formatter, it
stops being 80 lines. `ruff format` at line-length 100 exploded the vendored helpers from
~80 to ~200 lines by breaking every compact multi-arg signature onto its own line:

```python
# before
def container(x, y, w, h, title, stroke, fill="#ffffff", ...):

# after ruff format
def container(
    x,
    y,
    w,
    h,
    title,
    stroke,
    fill="#ffffff",
    ...
):
```

Not wrong, just noisy — and it means the copied helpers no longer look like the skill's
source, so diffing them against the template to pick up skill updates gets harder.

**Suggested:** a line in "Why no Python library?" acknowledging that a host repo's
formatter will reformat the vendored helpers, and that this is expected — don't fight it,
and don't diff against the template to check for drift.

---

## 5. Smaller notes

- **`preview.py` needs matplotlib**, which wasn't in my project venv. Not a problem — the
  draw.io Desktop CLI was on PATH so `render_png.py` worked — but worth noting in SKILL.md
  that preview's dependency is *not* in the skill's own requirements, so in a project venv
  you'll likely reach for `render_png.py` instead.
- **The "one dashed zone per trust/ownership boundary" advice was genuinely useful** and
  changed my design. My first instinct was to draw the third-party libraries inside the
  application zone; the guidance correctly pushed them out. Worth keeping prominent.
- **Reserved-corridor comments paid off.** Documenting `y=225 lane`, `x=850 channel` etc.
  at the top of the generator made the later "widen the column gaps" edit mechanical — I
  knew exactly which waypoints moved. The example's edge comments model this well; maybe
  promote it from example-only to an explicit SKILL.md recommendation.
- **Not a skill bug:** I introduced `graph = ET.SubElement(mxfile.find("diagram"), ...)`
  where the template correctly uses `ET.SubElement(diagram, ...)`. My error, not the
  skill's — noting it only so it isn't mistakenly "fixed" upstream.

---

## Summary of proposed changes

| # | Change | Type | Effort |
|---|--------|------|--------|
| 1 | Exempt edges targeting a box inside the container from TEXT_OVERLAP | validator fix | small |
| 2 | Add `SHORT_LABELLED_EDGE` warning | new check | small |
| 3 | Strip `.drawio` before appending `.png` in `render_png.py` | papercut fix | trivial |
| 4 | Note that host formatters will reflow vendored helpers | docs | trivial |
| 5 | Note that a clean validate says nothing about label room | docs | trivial |
| 6 | Note `preview.py`'s matplotlib dep isn't in project venvs | docs | trivial |

#1 and #2 are the ones with real value — #1 unblocks a pattern the skill recommends but
can't currently produce, and #2 catches a class of failure nothing else sees.
