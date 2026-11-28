# Phase record

**The phase in flight, and nothing else.** Written at `phase-workflow` §2 step 3, preserved across
sessions, and read back at §4 for `MERGE_METHOD`. It is overwritten at each phase start, never
appended. When no phase is in flight the body is the single line `No phase in flight.`

---

## Plugins from the claude.ai account

| Key | Value |
| --- | --- |
| `ORIGIN_URL` | `git@github.com:rahulragunathan/drawio.git` |
| `ORIGIN_PUSH_URL` | `git@github.com:rahulragunathan/drawio.git` |
| `REPO` | `rahulragunathan/drawio` |
| `DEFAULT_BRANCH` | `main` |
| `PHASE_BRANCH` | `feature/plugins-from-github` |
| `MERGE_METHOD` | `squash` |
| Branched from | `origin/main` at `07c73b2` |
| Started | 2026-11-28 |

`squash` is the first allowed method in the order squash, rebase, merge. The plan lives in
`~/.claude/plans/2026-11-27-plugins-from-github-plan.md`.

One phase across three repositories, one PR each, merged in this order after one sign-off:
drawio 2.0.0, dev-skills 2.3.1, dev-setup 1.5.0. This repository's part: drawio becomes a plugin and its skill `create-diagram`.
