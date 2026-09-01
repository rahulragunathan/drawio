# Open Questions

Things not yet settled, decisions first. [ROADMAP.md](ROADMAP.md) carries the one-line index;
this file carries the reasoning.

These are not work items. Each is a decision waiting to be made, a gap in what the tests
prove, or a risk knowingly carried. An entry that turns out to describe defined wrong
behavior with a known fix is a bug — move it to [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

Each entry has a stable ID. When one is settled it leaves this file: into the code plus a
CHANGELOG entry if it changed anything, into KNOWN_ISSUES or ENHANCEMENTS if it became work,
or into "Decisions taken and not taken" in [CLAUDE.md](../CLAUDE.md) if the answer was to do
nothing. IDs are never reused.

## Kind

| Kind | Means |
|------|-------|
| **Decision** | The code does something defensible, but nobody has chosen whether it is right. Asks for an answer. |
| **Verification** | The behavior is probably correct and nothing proves it. Asks for a test, or a deliberate acceptance. |
| **Risk** | Known, understood, accepted for now. Asks for nothing until circumstances change. |

---

<a id="unk-01"></a>
## UNK-01 — Should the missing v1.3.0 tag be backfilled?

**Kind:** Decision
**Where:** git history

`git tag` lists only `v1.2.0`. Release 1.3.0 was cut in CHANGELOG.md and in the `SKILL.md`
frontmatter on 2026-08-31, and four commits have landed on `main` since, but no `v1.3.0` tag
was ever pushed. The phase workflow tags in the merge cycle, so this is a gap in the one
release that predates the workflow being applied here, not a habit.

The consequence is small but real: `git describe` and any "what changed since 1.3.0" diff
have no anchor, and the next release cannot be compared against its predecessor. It also
means the CHANGELOG compare link for 1.3.0 has nothing to point at.

**What settles it:** decide whether to tag `796f084` — "Documentation pass for 1.3.0 (phase
4b)", the last commit of that release — as `v1.3.0` retroactively, or to accept the gap and
start clean tagging from the next release. Backfilling costs one command and makes the
compare links in CHANGELOG.md work; leaving it means the 1.3.0 link stays broken or absent.
