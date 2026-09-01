# Enhancements

Candidate work, highest priority first. [ROADMAP.md](ROADMAP.md) carries the one-line index;
this file carries enough detail to pick an item up without digging.

Each entry has a stable ID — use it in branch names (`feature/enh-01-<slug>`) and in the
CHANGELOG entry that closes it. When an item ships, delete it from here and from the ROADMAP
index; the record lives in [CHANGELOG.md](../CHANGELOG.md). An item dropped rather than built
moves to "Decisions taken and not taken" in [CLAUDE.md](../CLAUDE.md). IDs are never reused.

## Priority

Priority is about value, not urgency. Effort is a rough estimate — a session, or days.

| Level | Means |
|-------|-------|
| **High** | Closes a gap hit during real use. |
| **Medium** | Worth doing when the area is already open. Removes a sharp edge or a duplication. |
| **Low** | Tidying. Do it while passing through. |

---

<a id="enh-01"></a>
## ENH-01 — One verify gate that runs lint, tests, and a live example build

**Priority:** Medium · **Effort:** ~2 hours
**Where:** repo root · **Regression net:** the gate is the net

### What it is

A single `verify.sh` at the repo root that runs, in order: `ruff check`, `ruff format
--check`, `pytest`, then a real build-and-validate of every `examples/build_*.py`. Non-zero
exit on the first failure.

### Why it matters

There is no CI, so the documented gate is whatever a maintainer remembers to type.
[CONTRIBUTING.md](CONTRIBUTING.md) lists four separate commands and states that a change to
`validate.py`, the helpers or an example is not done until pytest is green *and* the example
rebuilds clean. That is exactly the kind of multi-step rule that gets half-run under time
pressure.

Lint is the half that has no net at all. `ruff.toml` pins six rule families precisely so the
result does not drift with the installed ruff, and nothing runs it. Both examples are already
covered by `test_three_tier_example_validates_clean` and
`test_aws_vpc_pipeline_example_validates_clean`, so the gate's value is bundling — one
command with one exit code, rather than four a maintainer has to remember in order.

### Notes for the work

Keep it stdlib and shell only, and make it pass on a bare checkout: `preview.py` needs
matplotlib and `render_png.py` needs the draw.io CLI, so neither belongs in the gate.
`scripts/render_examples.py` walks `examples/build_*.py` and validates each result, but it
exits early when the CLI is absent — so call pytest, which already covers both examples
without one, rather than reusing that walk.

Run the gate from the relative venv path (`.venv/bin/ruff`, `.venv/bin/python -m pytest`) to
match the rest of the project's commands.

---

<a id="enh-02"></a>
## ENH-02 — Catch a stale architecture render before it is reviewed

**Priority:** Low · **Effort:** ~1 hour
**Where:** [docs/build_architecture.py](build_architecture.py) · **Regression net:** `tests/test_docs_diagram.py` (new)

### What it is

A test that runs `docs/build_architecture.py`, validates the result, and asserts the
committed `docs/architecture.drawio` matches what the generator produces now.

### Why it matters

`docs/ARCHITECTURE.md` embeds a rendered PNG, and the whole point of committing the source
and the generator beside it is that the picture can be checked rather than trusted. Nothing
enforces that today: an edit to the module structure updates the prose while the diagram
keeps showing the old shape, and a stale diagram is read as current.

This is the same argument that makes `renders/` a phase-end step, applied to the one diagram
that documents the code itself.

### Notes for the work

`test_render_examples.py` already fakes the draw.io CLI at the system boundary; reuse that
approach so the test needs no install. Compare the generated XML to the committed file as
text — the generator is deterministic, and `minidom.toprettyxml` output is stable. Only the
`.drawio` can be checked this way; the PNG needs the CLI, so leave it to the phase-end pass.
