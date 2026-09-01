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

Nothing is open. Settled questions leave this file: into the code plus a CHANGELOG entry
if they changed anything, into KNOWN_ISSUES or ENHANCEMENTS if they became work, or into
"Decisions taken and not taken" in [CLAUDE.md](../CLAUDE.md) if the answer was to do
nothing.
