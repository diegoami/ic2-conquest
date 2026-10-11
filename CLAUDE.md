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
   - Every brief for a task that measures (an experiment, a probe, a driver task that times things, a plan handed to an implementer) must carry this rule, and say: never delete a save (even to regenerate it), and give every script's saves unique names (two scripts writing the same name left stale hashes; lesson 2026-10-09, the gap analysis).
7. **Read what a delegated run returned before you retry it, re-route it to another model, or call it a failure; never retry blind** (the owner, 2026-10-05).
   - OpenCode runs (`scripts/opencode_watched.py`, `scripts/external_review.py`): an exit or a class such as `nonzero-exit`, `cut-off` or `bad-format` looks the same for an early end and for a run that stopped and reported. The log's tail shows only the last tool output. Read the model's final message from the session record, read-only, with the session id from the run's log (`opencode session started: ses_…`): `docs/external-review.md`, "Failures and trust". Never read `auth.json` in that directory.
   - Claude agents: read the agent's final report (its hand-back) in full before acting.
   - A run that stopped and reported gets an answer to its report: amend the task, decide, or escalate. Post the report on the task's PR (or its run issue) so it is kept.
   - Treat any earlier "model X ends runs early" verdict as unconfirmed until its runs' final messages have been read.
8. **A failed subagent run is never normal: find its cause and fix it** (the owner's highest priority, 2026-10-10). This covers OpenCode runs, reviewers, implementers and Claude agents.
   - **Another model only when the provider's API does not answer** (a rate limit, a 5xx error, a quota or usage limit, a network error, or no session ever started), **and only the model the user then names** ("Choosing models", rule 7). A run that failed through a flaw in our process (a brief, permissions, timeouts, the watcher, an agent prompt) is fixed and run again on the same model, never re-routed.
   - **No run may lose its progress when it dies.** Every run records what it is doing (its session id, its state, a progress file, commits pushed as it goes), so the job can be tracked and **resumed where it stopped**, not restarted.
   - **Keep monitoring running subagents and tell the owner in plain words** what each one is doing and working on, while it runs.

## Choosing models: the user decides (the owner, 2026-10-11)

This replaces every earlier model-choice rule of this project (L50/L51, the reviewer chains and placements, issue #72 "follow quota-tracker's /recommend and nothing else"); those are kept as history in the docs, marked superseded. It holds whatever model the orchestrating session itself runs on.

1. **Before implementing anything** (a task, a fix, a plan change), ask the user ONE question with the question tool: does the main session implement it, or a subagent, and which model?
   - The main session: it implements itself, in its own git worktree (never the main checkout).
   - A subagent: the Agent tool with the model the user names (any model this session's backend offers), or an external run (e.g. OpenCode) with the model the user names.
   - Whoever implements works in its own worktree, keeps a short running-notes file there (plan, a progress line per commit, an END block before stopping), pushes after every commit, and opens the PR. When a subagent ends, the main session reads its final report before acting and posts its notes on the issue.
2. **At every review** (first review, re-review, re-check of named fixes), ask the user ONE question: which external model reviews? Run that review alone (one at a time), and relay its findings to the user in full. A PR gets one review unless the user asks for more.
3. With each question, show quota-tracker's recommendation as a **suggestion only** (`curl -s "http://localhost:8765/recommend?tier=heavy"` for heavy work, `tier=light` for small work: its `pick`/`pair` with rank, outlook and reliability). If it does not answer, ask without the suggestion.
4. The only fixed rules: the reviewer is never of the implementer's model family; DeepSeek is never used; Alibaba only when the user asks.
5. Record each choice (who, which model, the suggestion's reasons) on the issue or PR.
6. These rules never name the orchestrator's own model; they work the same on any backend.
7. A failed run is diagnosed and fixed, not silently re-routed: another model only when the provider does not answer, and the user names it (rule 8 above).

### Monitoring OpenCode sessions (and any other background agent)

8. Start every OpenCode run in the background, with stdin from a file (never an inherited pipe: `opencode run` waits for stdin's end-of-file before it creates a session). Never wait on it blind.
9. Watch it with one monitor that checks every 1-2 minutes and reports only changes:
   - the session started (`opencode session list` in the run's directory, or the run's "session ses_... started" line), and the run's exit;
   - progress: the OpenCode log's size and the session's `updated` time, the worktree's changed files, new lines in the running-notes file, and new commits pushed to the branch (`scripts/opencode_status.py` reads the reviewer runs' progress);
   - "possibly stuck" after ~10 minutes with no change; "unpushed" when a commit sits on the branch but not on origin for ~15 minutes (push it for the run and record it);
   - free memory, if the machine is short of it: run reviews and builds one at a time.
   For a Claude subagent, the progress signal is its transcript file's size plus its worktree.
10. Tell the user, in plain language, what each running agent is doing: the step it is on, what it committed, what it found (from its notes, commits and latest session messages). Never raw log lines or byte counts.
11. On a "possibly stuck" flag: check the process is alive, read its newest session messages (`opencode export <ses_...>`, or the read-only session reader in `docs/external-review.md`); a long build or test step is not stuck. A dead or 20-minute-silent run is stuck: record the cause, fix it if it is ours.
12. When a run ends, read its final message before doing anything else (rule 7 above). A run that stopped and reported a blocker gets an answer (fix the brief or the setup), not a retry on another model.
13. A run interrupted by our own limits (an idle or total timeout) is RESUMED in its own session and worktree (`opencode run --session <ses_...>` with a short "continue where you stopped" message and a longer limit; for reviews `python3 scripts/external_review.py --resume <run dir>`), not restarted from scratch.

## Working with the owner (moved from session memory, 2026-10-11)

- **Ask, don't guess** (the owner, 2026-10-02): when a decision is the owner's or a request can be read two ways, ask with the question tool, concrete options, the recommended one first. Never fill the gap with an assumption and carry on.
- **Merging** (the owner, 2026-10-04): merge a PR that has an approving review from another model family and green CI (`gh pr checks`) without asking. Read its non-blocking notes first: a proven way past what the brief's "Blocking means" names is rework, not a merge. Still ask about design decisions and escalations.
- **After a merge** (the owner, 2026-10-11, replacing "start the next item at once"): propose the next queued item and ask who implements it and with which model ("Choosing models", rule 1). Never start it unasked.
- **Current focus** (the owner, 2026-10-05): battles and bots are paused; the work is research and gap-finding for IMPERIAL CONQUEST MAIN's v0.5.0, then post-0.5.0 work not related to battles. The paused battle queue (B16, B7+B12, B6, B9, B10, B13-14, B15, then coverage gaps) resumes only when the owner says so; each paused item has resume notes in its data README.
- **New findings** (the owner, 2026-10-02): at the start and at the end of each reply, compare `findings/` on `origin/main` with the list last reported and name every new file with one line on what it is (and a reviewer's findings when it posts on a PR). No background polling, no push notifications.
- **Research** (the owner, 2026-10-05 and 2026-10-08): reading `~/projects/imperial-conquest-2-research/` is always fine (rule 2 limits writes only). Every finding that lands on main is relayed to the ic2-research session at once with the `/relay-to-research` skill, without asking. Message ic2-research otherwise only when the next step is theirs (re-running their extractors, refreshing a report, interpreting their data). The PowerShell main session (IMPERIAL CONQUEST MAIN) is reached through the owner: write a paste-ready prompt and the owner carries it (`docs/notes-for-main-session-decompile-skills.md`); it reads only promoted research reports.

## Environment

- **Model quota:** quota-tracker on `localhost:8765` says which providers have quota left (`docs/environment.md`). Its `/recommend` is shown to the user as a **suggestion only** with each model question ("Choosing models" below); it never decides.

- `setup/setup.sh` (root, Ubuntu 24.04): installs Wine (32-bit prefix), Xvfb, xdotool, imagemagick, ffmpeg, tesseract; clones the pinned research and fixtures repos (`setup/pins.txt`) under `/home/user/diegoami`; builds the executables into `$IC2_WORK/build` and the game folder `$IC2_WORK/prefix/drive_c/IC2` (`IC2_WORK` defaults to `~/ic2-work`, outside git).
- The bot plays **`Imperial Conquest 2 fast rollingsave seed.exe`**: instant battles; every human turn writes `AUTOnnnn.SAV` + an `AUTOSAVE.LOG` line; `RandSeed` comes from `SEED.TXT` beside the exe at **program start and New Game only** (loading does not reseed: `findings/2026-09-29-loading-a-save-does-not-reseed.md`). So a repeatable turn = restart the game with the seed, open the save, issue the orders (`Game.load`).
- `nnnn` = `(300 − yearBC) × 24 + season × 6 + (week − 1) / 2`; 0720 = 270 BC Spring week 1.

## Code map

- `harness/driver.py`: the order driver (`Game`): process control, read-only game memory via `/proc/<pid>/mem`, menus/toolbar, dialogs, tile targeting, orders. Layouts in `coverage.md` §2.
- `state/sav.py`: SAV → dict/JSON (layout: `docs/sav-layout-notes.md`); `state/metrics.py`: `runs/<id>/metrics.csv`, `armies.csv`, `state/nnnn.json`.
- `planner/path.py`: army paths (DAT terrain costs).
- `patches/seed_patch.py`: the seed option on top of the fixtures' `patch_exe.py`.
- `tests/test_orders.py`: each order issued headless and checked on the save diff; `tests/results.md`.
- `scripts/external_review.py`, `scripts/opencode_watched.py`, `.opencode/agents/external-reviewer.md`: the OpenCode PR reviewer in its own worktree (`docs/external-review.md`); `.claude/skills/review-pr`: a review run in a Claude session, used only when the user names a Claude model as the reviewer ("Choosing models", rule 2). **Every review brief carries a "Blocking means" section written for its task** (`docs/review-briefs/README.md`: template, one `pr<n>.md` per review passed with `--brief-file`; reviewer verdicts worth remembering go to `docs/model-trials.md`).
- **Model facts** (not a choice rule; the choice is the user's, see "Choosing models" above): model ids come from the provider's live list (`opencode models <provider>`), never from memory. The light OpenAI model is GPT-5.6 Luna on the direct route, `openai/gpt-5.6-luna`, not GPT-6 Luna (`openai/gpt-6-luna`, which draws on the main pool with Sol); never a Luna on OpenCode Go (`opencode-go/…`: a proxy returns `Bad Request` in long agent loops). **Effort** (the player, 2026-10-05): heavy models (`openai/gpt-6.1-sol`, `zai-coding-plan/glm-5.3`, Opus) at `low`, or `medium` when the task needs it, never `high`; light models (GPT-5.6 Luna, the Flash models) at `high`. The former L50/L51 choice rules (2026-10-05) are superseded by "Choosing models" (2026-10-11).
- `docs/rules-digest.md`: the researched rules, with sources. `findings/`: drafts for the research repo.

## Driver pitfalls (Wine, no window manager)

Hover before clicking; prefer toolbar buttons to menus; reset menu state before a menu; the first click into an inactive window may only activate it, so verify every order's effect (memory or save) and retry at most twice; never click End turn twice unless the first click provably did nothing.

Confirm boxes and dialogs (lessons 2026-10-08): `controls(title)` is racy for about a second after a focus change (retry, or use `_answer_confirm`); a bare cursor click can land on a sibling window, so click with `xdotool click --window`; the menu bar is at y = 36, not 14 (`coverage.md` §2); `find_windows` filters tooltips (`tooltips=True` to see them); a closed box lingers 1-2 s, so an OK loop waits for it to close and never presses Cancel; list rows go through `click_list_row`; `end_turn` answers the post-battle "Offer of peace" (`peace=False` is No).

## Runs

A run is `runs/<id>/`: `turns/nnnn.md` (intent, orders, expected vs actual, surprises), `metrics.csv`, `armies.csv`, `checkpoints/`, `debrief.md`, `viewer.md`; its binary artifacts (saves, screenshots, per-season video) go to release `run-<id>` or `artifacts/run-<id>/`. One GitHub issue per run holds the conversation: proposal before, checkpoint comments during, debrief after.
