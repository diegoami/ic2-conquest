# ic2-conquest: rules for Claude sessions

Purpose: find strategies that dominate the map in the original *Imperial Conquest 2* (1996) and prove it with per-turn saves, logs and plans; secondarily, exercise every mechanic (`coverage.md`). Read `README.md`, then the active strategy in `strategies/`.

## Hard rules

1. **No EXE, DAT, screenshot or video in git.** Saves: the player allowed (2026-09-29) **selected** small saves in `saves/`, each listed in `saves/README.md` with why it is interesting for play or research. All other saves, screenshots and videos go in a GitHub release `run-<id>` (or `artifacts/run-<id>/`) and are cited by bare filename.
   - Releases: the bot creates the run's release itself, **at the first batch and uploads to it after every batch, not only at the end of a run** (rule 6; `gh release create run-<id> <files>` the first time, `gh release upload run-<id> <files>` after each later batch; from the gitignored `artifacts/run-<id>/`, one folder per season while the run goes on; for an experiment, `run-exp-<name>`). Use `IC2_RELEASE_TOKEN` only for release calls, as `Authorization: Bearer`; never print, log or write it. If the call fails (an earlier session's proxy answered "Creating, editing, or deleting releases is not permitted for this session type", HTTP 403), keep the artifacts and post the exact `gh release create …` command for the player; do not retry in another way.
2. **Never write to another repository.** Rule discoveries go to `findings/` here, in the research repo's report format, with the saves cited. The player promotes them.
3. **The player's words in a strategy file are never edited.** The bot writes only in its own sections ("Bot validation", "Trials").
4. **No run starts before the player approves it** in the run's GitHub issue.
5. **Every claim of progress cites a save**: run, file and turn (e.g. "run 0, `AUTO0731.SAV`, turn 0731").
6. **Measurements are kept, committed and pushed as they are made, and never deleted** (adopted 2026-10-04 from game-archaeologist `lessons.md` L207 and `method/research-protocol.md` §2, adapted to rule 1).
   - Where: every output a finding or a PR may cite (trial tables, probe logs, timings, OCR or tooltip dumps, tables, static extracts) is written under a **tracked** path the task owns: `runs/experiments/data/run-exp-<name>/` for experiments, `runs/<id>/` for runs; never only under `artifacts/`, `rendered/` or a temp folder. New runners (the battles plan) write their text outputs straight to the tracked path.
   - Archiving: a script may write to the git-ignored `artifacts/run-exp-<name>/` while it runs, but after each batch the session runs `python3 scripts/archive_measurements.py run-exp-<name> --commit`, which copies the text outputs to the tracked path without overwriting (a changed file is kept as `<stem>.v<N><ext>` beside the old one) and adds the binaries' hashes.
   - Binaries (saves, screenshots, video) stay out of git (rule 1): their SHA-256 go in `SAVES.sha256` beside the data, and they are uploaded to the release `run-exp-<name>` / `run-<id>` as the batches finish.
   - Cadence: **commit and push after each batch of trials or probes and at least every 30 minutes**, so a stopped session loses nothing.
   - **Never delete or overwrite a measured output**: a re-run writes new files beside the old ones and the finding names the ones it cites (a resumable runner appends or versions; it does not rewrite history).
   - Every brief for a task that measures (an experiment, a probe, a driver task that times things, a plan handed to an implementer) must carry this rule.

## Environment

- **Model quota:** quota-tracker on `localhost:8765` says which providers have quota left (`docs/environment.md`); check it before choosing a model (L50 under Code map).

- `setup/setup.sh` (root, Ubuntu 24.04): installs Wine (32-bit prefix), Xvfb, xdotool, imagemagick, ffmpeg, tesseract; clones the pinned research and fixtures repos (`setup/pins.txt`) under `/home/user/diegoami`; builds the executables into `$IC2_WORK/build` and the game folder `$IC2_WORK/prefix/drive_c/IC2` (`IC2_WORK` defaults to `~/ic2-work`, outside git).
- The bot plays **`Imperial Conquest 2 fast rollingsave seed.exe`**: instant battles; every human turn writes `AUTOnnnn.SAV` + an `AUTOSAVE.LOG` line; `RandSeed` comes from `SEED.TXT` beside the exe at **program start and New Game only** (loading does not reseed: `findings/2026-09-29-loading-a-save-does-not-reseed.md`). So a repeatable turn = restart the game with the seed, open the save, issue the orders (`Game.load`).
- `nnnn` = `(300 − yearBC) × 24 + season × 6 + (week − 1) / 2`; 0720 = 270 BC Spring week 1.

## Code map

- `harness/driver.py`: the order driver (`Game`): process control, read-only game memory via `/proc/<pid>/mem`, menus/toolbar, dialogs, tile targeting, orders. Layouts in `coverage.md` §2.
- `state/sav.py`: SAV → dict/JSON (layout: `docs/sav-layout-notes.md`); `state/metrics.py`: `runs/<id>/metrics.csv`, `armies.csv`, `state/nnnn.json`.
- `planner/path.py`: army paths (DAT terrain costs).
- `patches/seed_patch.py`: the seed option on top of the fixtures' `patch_exe.py`.
- `tests/test_orders.py`: each order issued headless and checked on the save diff; `tests/results.md`.
- `scripts/external_review.py`, `scripts/opencode_watched.py`, `.opencode/agents/external-reviewer.md`: the OpenCode PR reviewer in its own worktree (`docs/external-review.md`); `.claude/skills/review-pr`: the Claude-side review (the fallback when the OpenCode reviewer exits 3). **Every review brief carries a "Blocking means" section written for its task** (`docs/review-briefs/README.md`: template, one `pr<n>.md` per review passed with `--brief-file`; reviewer verdicts worth remembering go to `docs/model-trials.md`).
- **Choosing a model** (harness_imperial L50/L51, adopted 2026-10-05):
  - **L50, check the quota first.** Before choosing, recommending or delegating to a model (an OpenCode reviewer, a Claude agent or subagent, an OpenRouter model), check how much quota its provider has left with quota-tracker (`docs/environment.md`). A provider whose status is `exhausted` is not used until it is usable again: take the next model of the chain whose provider has quota, pass it explicitly (`--model` for `scripts/external_review.py`, the model of an Agent call or of `opencode -m`), and say so in the run's report or the PR body ("GLM skipped: zai exhausted until 21:40; reviewed by Luna"). Where the service is not installed, go on without it and count a usage-limit error as `exhausted`. Model ids come from the provider's live list (`opencode models <provider>`), never from memory.
  - **L51, the light OpenAI model is GPT-5.6 Luna.** The light OpenAI model, and the default Luna reviewer, is GPT-5.6 Luna on the direct OpenAI route: `openai/gpt-5.6-luna`, effort `high`. It is not GPT-6 Luna (`openai/gpt-6-luna`), which draws on OpenAI's main pool with Sol; GPT-6 Luna is never the reviewer. Never use a Luna on OpenCode Go (`opencode-go/…`): a proxy behind it returns `Bad Request` in long agent loops.
  - **Effort.** Heavy models (`openai/gpt-6.1-sol`, `zai-coding-plan/glm-5.3`, Opus) run at effort `low`, or `medium` when the task needs it, never `high` (the player, 2026-10-05). Light models (GPT-5.6 Luna, the Flash models) run at `high`.
- `docs/rules-digest.md`: the researched rules, with sources. `findings/`: drafts for the research repo.

## Driver pitfalls (Wine, no window manager)

Hover before clicking; prefer toolbar buttons to menus; reset menu state before a menu; the first click into an inactive window may only activate it, so verify every order's effect (memory or save) and retry at most twice; never click End turn twice unless the first click provably did nothing.

## Runs

A run is `runs/<id>/`: `turns/nnnn.md` (intent, orders, expected vs actual, surprises), `metrics.csv`, `armies.csv`, `checkpoints/`, `debrief.md`, `viewer.md`; its binary artifacts (saves, screenshots, per-season video) go to release `run-<id>` or `artifacts/run-<id>/`. One GitHub issue per run holds the conversation: proposal before, checkpoint comments during, debrief after.
