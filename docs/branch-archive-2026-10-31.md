# Old branches copied to main (2026-10-31)

Owner decision 2026-10-31: copy the content of old branches that main did not have, then delete the branches.
Files absent from main were copied as they were; a notes file whose branch version only adds lines replaces main's.
`harness/driver.py` of `experiment/ai-mover-contact` diverged both ways, so main's version stays and the branch's is kept as
`runs/experiments/ai_contact/driver-at-experiment-ai-mover-contact.py` (the experiment ran with it).

| Branch (head) | Copied |
|---|---|
| `experiment/ai-turn` (`bab12f57`) | 34 new files |
| `experiment/ai-mover-contact` (`2d2251d3`) | 95 new files |
| `experiment/battle-orders-b7-b12` (`6e9c2ea5`) | 38 new files |
| `run/unit-map-selection-rendering` (`9da03bc6`) | 10 new files |
| `docs/mark-resupply31-promoted` (`0f982e8f`) | 1 new files |
| `docs/mark-resupply33-promoted` (`be72204e`) | 4 new files |
| `docs/mark-resupply31-promoted` (`0f982e8f`) | RUN-NOTES-resupply31-promotion.md (branch version only adds lines) |
| `docs/mark-resupply33-promoted` (`be72204e`) | RUN-NOTES-resupply33-promotion.md (branch version only adds lines) |
| `docs/mark-sav-export37-partial-promoted` (`72843834`) | RUN-NOTES-sav-export37-promotion.md (branch version only adds lines) |
| `docs/tactical25-session-continuity` (`219caa41`) | docs/progress/tactical25-original-trace.md (branch version only adds lines) |

Not copied:
- `docs/pr40-review-record`, `docs/report-all-blockers`: main's `docs/model-trials.md` already holds every line of theirs.
- `chore/codex-compatibility`, `chore/session-led-workflow`, `tooling/opencode-implementer`: earlier versions of AGENTS.md, CLAUDE.md, the cloud and OpenCode docs; main has newer ones (owner: delete without copying).

The three finding drafts (`findings/2026-10-07-ai-mover-contact.md`, `2026-10-07-ai-turn-corroboration.md`, `2026-10-12-unit-map-selection-rendering.md`) were already promoted by research from these branches.

The old worktrees' git-ignored artifacts and untracked notes were moved whole to `~/ic2-work-archive/worktrees-2026-10-31/` (outside git; one file there is private).
