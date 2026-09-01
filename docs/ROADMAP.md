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

**Last Updated**: 2026-09-01 (external repo review triaged; UNK-01 settled)

## Status

The skill is stable at 1.4.1 and in real use. The icon catalog and the two worked examples
are settled; the validator is not as settled as 1.4.0 assumed. An external review by
gpt-5.6-sol and gemini-3.1-pro-high found four High defects, all of them in how a `.drawio`
file is *read* rather than in any individual check — compressed files, multi-page files,
round-tripped labels and anchor-direction stubs. Each one makes the validator report clean
on a diagram it never actually examined, which is the failure mode the whole tool exists to
prevent.

The queue is therefore KI-02 through KI-05 first, bundled roughly as written: the two
file-reading defects together, then the three label-reading ones.

### Phases

No phase is in flight. The queue is KI-02 through KI-05.

## Known Issues

Most severe first. Severity definitions and full detail in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

| ID | Issue | Severity |
|----|-------|----------|
| [KI-02](KNOWN_ISSUES.md#ki-02) | A compressed .drawio validates as clean no matter what it contains | High |
| [KI-03](KNOWN_ISSUES.md#ki-03) | Multi-page diagrams are merged into one canvas by non-unique cell IDs | High |
| [KI-04](KNOWN_ISSUES.md#ki-04) | Stub squaring accepts a stub that leaves the anchor in the wrong direction | High |
| [KI-05](KNOWN_ISSUES.md#ki-05) | A label in a separate edgeLabel cell escapes every label check | High |
| [KI-01](KNOWN_ISSUES.md#ki-01) | The icon catalog publishes keys the generator helpers reject | Medium |
| [KI-06](KNOWN_ISSUES.md#ki-06) | Labels on `<object>` wrappers are lost | Medium |
| [KI-07](KNOWN_ISSUES.md#ki-07) | The title-band exemption applies to every vertical segment of the edge | Medium |
| [KI-08](KNOWN_ISSUES.md#ki-08) | A label's position ignores the path-relative geometry draw.io stores | Medium |
| [KI-09](KNOWN_ISSUES.md#ki-09) | Icon name matching is case-insensitive for image paths, which are not | Low |
| [KI-10](KNOWN_ISSUES.md#ki-10) | Only four exact HTML break spellings are treated as line breaks | Low |

## Enhancements

Highest priority first. Priority definitions and full detail in [ENHANCEMENTS.md](ENHANCEMENTS.md).

| ID | Enhancement | Priority | Effort |
|----|-------------|----------|--------|
| [ENH-01](ENHANCEMENTS.md#enh-01) | One verify gate that runs lint, tests, and a live example build | Medium | ~2 hours |
| [ENH-03](ENHANCEMENTS.md#enh-03) | Mark a container explicitly instead of inferring it from its style | Medium | ~3 hours |
| [ENH-04](ENHANCEMENTS.md#enh-04) | Refuse to package a file that resolves outside the skill root | Medium | ~1 hour |
| [ENH-02](ENHANCEMENTS.md#enh-02) | Catch a stale architecture render before it is reviewed | Low | ~1 hour |
| [ENH-05](ENHANCEMENTS.md#enh-05) | Sanity-check an icon-name refresh before it overwrites the catalog | Low | ~1 hour |
| [ENH-06](ENHANCEMENTS.md#enh-06) | Root the archive at the skill's declared name, not the directory's | Low | ~30 minutes |

## Open Questions

Decisions first, then verification gaps, then accepted risks. Kind definitions and the
reasoning behind each in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

None open.
