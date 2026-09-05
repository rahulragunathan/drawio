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
| ------- | ------- |
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

**Source:** found during the 1.4.0 documentation drift check.

---

<a id="enh-03"></a>

## ENH-03 — Mark a container explicitly instead of inferring it from its style

**Priority:** Medium · **Effort:** ~3 hours
**Where:** [scripts/validate.py:403-405](../scripts/validate.py#L403-L405) · [assets/build_template.py](../assets/build_template.py) · **Regression net:** `tests/test_validate.py`

### What it is

Have `container()` stamp a role into the style — `drawioSkillRole=zone`, matching the
`drawioSkillRole=icon` marker the icon helpers already emit — and have the parser prefer
that marker, falling back to the current `dashed=1` + `verticalAlign=top` inference for
files the skill did not generate.

### Why it matters

Container detection currently reads presentation as meaning:

```python
is_container = (
    style_d.get("dashed") == "1" and style_d.get("verticalAlign") == "top"
)
```

Being classified as a container has real consequences — the shape is skipped entirely by
`CROSSING`, and only its top 28 px are checked at all. So any dashed, top-aligned vertex
that is *not* a zone becomes a hole in the diagram: an arrow can pass straight through its
body and nothing fires. A note box, an annotation, or a shape styled that way by hand all
qualify.

The precedent is already in the codebase. `icon_style()` emits `drawioSkillRole=icon` for
exactly this reason, and `is_icon` checks it first before falling back to style sniffing.

### Notes for the work

Keep the inference as the fallback — hand-authored and Desktop-round-tripped files have no
marker, and dropping it would reclassify every existing diagram. The marker only has to win
where present.

[CLAUDE.md](../CLAUDE.md) records that container detection deliberately does **not** require
a particular `strokeWidth`; that decision stands and is not what this changes. Update that
note when the marker lands, and add a fixture for a dashed top-aligned shape carrying no
marker (still a container) and one carrying `drawioSkillRole=box` (not a container).

**Source:** gpt-5.6-sol — repo review, 1.4.0

---

<a id="enh-04"></a>

## ENH-04 — Refuse to package a file that resolves outside the skill root

**Priority:** Medium · **Effort:** ~1 hour
**Where:** [scripts/package_skill.py:58-62](../scripts/package_skill.py#L58-L62), `build_package` · **Regression net:** `tests/test_package_skill.py`

### What it is

Resolve every candidate path and skip (or refuse) anything whose real location is not under
`skill_root`, so the archive can only ever contain the skill's own files.

### Why it matters

```python
files = sorted(
    p
    for p in skill_root.rglob("*")
    if p.is_file() and is_packaged(p.relative_to(skill_root))
)
```

`rglob` yields symlinks, `is_file()` follows them, and `ZipFile.write()` then archives the
*target's* bytes under the link's in-repo name. `is_packaged()` filters on the path as it
appears in the repo, so a link whose name looks ordinary passes.

The archive is the one artifact that leaves this machine and gets uploaded, which is what
makes an unchecked "read whatever this points at" step worth closing. This is hardening, not
a live bug: nothing in the repo does this today, and `.venv` — the one symlink present — is
already excluded for being hidden.

### Notes for the work

`Path.resolve()` then `is_relative_to(skill_root.resolve())` is the whole check. Decide
whether an out-of-tree link is skipped silently or fails the build; failing is easier to
justify for a distribution artifact, and it cannot be triggered by accident.

Test with a `tmp_path` skill tree containing a symlink to a file outside it, asserting the
target's content never appears in the archive. Note that `skill_root` itself is resolved at
the top of the function already, so compare against the resolved root.

**Source:** gpt-5.6-sol — repo review, 1.4.0

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

**Source:** found during the 1.4.0 documentation drift check.

---

<a id="enh-05"></a>

## ENH-05 — Sanity-check an icon-name refresh before it overwrites the catalog

**Priority:** Low · **Effort:** ~1 hour
**Where:** [scripts/list_icons.py:45-62](../scripts/list_icons.py#L45-L62), `read_asar` · **Regression net:** `tests/test_list_icons.py`

### What it is

Validate the asar header and the per-file offsets before reading, and refuse to write
`assets/icon_names.txt.gz` when a refresh produces implausibly few names.

### Why it matters

`read_asar` trusts the archive completely:

```python
_, rest_of_pickle, _, json_len = struct.unpack("<IIII", fh.read(16))
directory = json.loads(fh.read(json_len).decode("utf8"))
data_base = 8 + rest_of_pickle
```

No field is range-checked and no entry's `offset + size` is checked against the file length,
so a truncated or partially-downloaded `app.asar` yields short reads rather than an error.
The names simply come out incomplete, `--refresh` writes the smaller list, and from then on
`UNKNOWN_ICON` warns about perfectly valid stencils — a slow, confusing failure that looks
like a catalog problem rather than a bad refresh.

The input is a local, trusted app bundle (or `$DRAWIO_APP`), so this is about corruption
rather than attack. The offset arithmetic itself is correct and must stay as it is;
[CLAUDE.md](../CLAUDE.md) records why `8 + field1` is the right formula.

### Notes for the work

The cheap, high-value half is the count guard: `--refresh` can read how many names the
current file holds, so refuse to shrink it by more than a small margin without an explicit
`--force`. draw.io releases add names far more often than they remove them.

Bounds-checking each entry against the archive size is a few lines on top, and turns a
silent truncation into a clear error naming the offending entry.

**Source:** gpt-5.6-sol — repo review, 1.4.0

---

<a id="enh-06"></a>

## ENH-06 — Root the archive at the skill's declared name, not the directory's

**Priority:** Low · **Effort:** ~30 minutes
**Where:** [scripts/package_skill.py:53](../scripts/package_skill.py#L53), `build_package` · **Regression net:** `tests/test_package_skill.py`

### What it is

Take the archive's root prefix from the `name:` field in `SKILL.md`'s frontmatter rather
than from whatever the checkout directory happens to be called.

### Why it matters

```python
prefix = skill_root.name
```

Clone the repository as `drawio-skill/`, or build from a worktree, and the archive is rooted
at that name instead of `drawio/`. [SKILL.md](../SKILL.md) and
[CONTRIBUTING.md](CONTRIBUTING.md) both state the archive is rooted at `drawio/`, and the
skill's identity comes from its frontmatter `name:`, not from a local directory name.

`main()`'s completeness check already hedges on this — it accepts either `drawio/SKILL.md`
or `f"{SKILL_ROOT.name}/SKILL.md"` — which is the shape of a contract that was never pinned
down.

### Notes for the work

Parse the frontmatter `name:` with a couple of lines of string handling; the file is the
skill's own and stdlib-only parsing is the constraint. Fail loudly when the field is missing
rather than falling back to the directory name — the silent fallback is the thing being
removed.

`test_the_archive_is_rooted_at_the_skill_folder` currently passes for the wrong reason: the
checkout happens to be called `drawio`. Give it a `tmp_path` tree with a different directory
name so it tests the contract rather than the coincidence.

**Source:** gemini-3.1-pro-high — repo review, 1.4.0
