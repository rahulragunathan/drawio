# ROADMAP

**What's next.** This file holds only work that has not happened yet, at index level. It does
not describe what shipped or how the code works today.

| Looking for | Read |
|-------------|------|
| Detail on an open bug | [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |
| Detail on a candidate enhancement | [ENHANCEMENTS.md](ENHANCEMENTS.md) |
| Detail on an open question | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) |
| What already shipped | [CHANGELOG.md](../CHANGELOG.md) |
| How the code works now | [README.md](../README.md), [ARCHITECTURE.md](ARCHITECTURE.md), [CLAUDE.md](../CLAUDE.md) |
| Ideas considered and dropped | "Decisions taken and not taken" in [CLAUDE.md](../CLAUDE.md) |

The tables below are **pointers, not summaries** — ID, title, rating, link. Nothing is
described twice.

An item's whole life is a move: it enters here and its supporting file together, and on
completion is deleted from both, with the record written into CHANGELOG `[Unreleased]`. An
item dropped rather than built moves to "Decisions taken and not taken". IDs are never
reused. Nothing here looks backward — completed phases are CHANGELOG releases.

**Last Updated**: 2026-09-01 (1.4.0 released; external code review planned next)

## Status

The skill is stable at 1.4.0 and in real use. The validator, the icon catalog and the two
worked examples are settled. The 1.4.0 phase adopted the documented docs layout — `docs/`,
an architecture diagram, and these roadmap files — and its drift check surfaced the entries
below. They are the first three, not the full picture.

### Phases

No phase is in flight. An external code review of the whole codebase is planned next;
its findings land in the three files below.

## Known Issues

Most severe first. Severity definitions and full detail in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

| ID | Issue | Severity |
|----|-------|----------|
| [KI-01](KNOWN_ISSUES.md#ki-01) | The icon catalog publishes keys the generator helpers reject | Medium |

## Enhancements

Highest priority first. Priority definitions and full detail in [ENHANCEMENTS.md](ENHANCEMENTS.md).

| ID | Enhancement | Priority | Effort |
|----|-------------|----------|--------|
| [ENH-01](ENHANCEMENTS.md#enh-01) | One verify gate that runs lint, tests, and a live example build | Medium | ~2 hours |
| [ENH-02](ENHANCEMENTS.md#enh-02) | Catch a stale architecture render before it is reviewed | Low | ~1 hour |

## Open Questions

Decisions first, then verification gaps, then accepted risks. Kind definitions and the
reasoning behind each in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

| ID | Question | Kind |
|----|----------|------|
| [UNK-01](OPEN_QUESTIONS.md#unk-01) | Should the missing v1.3.0 tag be backfilled? | Decision |
