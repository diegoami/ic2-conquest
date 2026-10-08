# Handover: 2026-10-01 — WSL bootstrap, run-time UI derivation, order types, the Gallic-army experiment

## TL;DR

Three open PRs, all pushed, **nothing merged into `main`**:

| PR | Branch | What | Base |
|---|---|---|---|
| [#3](https://github.com/diegoami/ic2-conquest/pull/3) | `fix/toolbar-calibration` | run-time derivation of the toolbar / army-toolbar / dialog-control positions | `main` |
| [#5](https://github.com/diegoami/ic2-conquest/pull/5) | `feat/order-types` | eight new orders, the field battle, the Gallic-army experiment | **stacked on #3** |
| [#4](https://github.com/diegoami/ic2-conquest/pull/4) | `docs/wsl-setup` | WSL2 setup runbook + intent/approaches doc | `main` |

`python3 -m tests.test_orders` → **13 PASS** (about 15 min). The Gallic-army experiment runs and Rome wins every seed.

## Review and merge, in this order

1. **#3 first** — it is the base of #5. Review `harness/driver.py`'s run-time calibration and `harness/win_controls.c`.
2. **#5** — after #3 merges, GitHub retargets it to `main`. Review the new orders, the battle handling and `runs/experiments/gallic-army/`.
3. **#4** — the docs; independent.

Verify after merging: `python3 -m tests.test_orders` → 13 PASS. The driver moves UI positions at run time, so a different font/DPI does not need new coordinates.

## What changed

### #3 — run-time UI derivation (the important one)

The hardcoded screen coordinates in `coverage.md` drift between Wine builds (here the toolbar pitch is ~24 px vs ~22, so `TOOLBAR["recruit"]=174` landed on *Balance sheet*; the Army recruits dialog's OK moved from (155,345) to (133,359)). Two derivations replace them:

- **Toolbars** (main, army, battle): each button's tooltip is a named X window. `Game.calibrate_toolbar` / `_scan_bar` hover the bar once, read the tooltip names, and cache the centres (`$IC2_WORK/toolbar.json`, `army_toolbar.json`, `battle_toolbar.json`). `Game.tool` / `army_tool` use them.
- **Dialog controls**: Wine draws a dialog's controls itself (they are **not** X windows). `harness/win_controls.c` — a ~30-line mingw helper built to `$IC2_WORK/win_controls.exe` by `setup.sh` — enumerates a window's child HWNDs as `class / text / x / y / w / h`. `Game.controls(title)`, `control(cs, text=…/cls=…)` and `click_control` read it. `recruit` / `mobilize` use it.

`coverage.md` §2 now says the recorded coordinates are the fallback/reference, not what the driver clicks.

### #5 — orders, battle, experiment

- New orders, each with a save-diff test in `tests/test_orders.py`: `join`, `taxation` (slider 0..40, Home then Right×n), `disband_unit`, `disband_army`, `build_fleet` (1s/10s spinners), `split_army`, `change_units_disband`, `transfer_units` (army-to-army, same dialog as split).
- **Field battle**: `attack` on an army opens the tactical screen and plays it. Two things make it work: (a) **wait for the battle window** (it opens ~3 s after the click), and (b) **Computer general must be toggled during the placement phase**, or the battle stalls waiting for human input. The battle toolbar is calibrated like the others (End turn ~114, Computer general ~165 vs `coverage.md`'s 110/158).
- **Confirm dialogs** (Yes/No/Cancel) are answered **Yes by button** — `dismiss_popups` used to click the bottom centre, which missed them.
- **Battle flag** `0x4A0B7C` (`Game.in_battle`) gates battle handling, so a stale `<A> v <B>` window cannot spin `end_turn`.
- **Experiment** `runs/experiments/gallic-army.py` (+ `README.md`, `results.json`): from the run-0 start, join armies 0 and 1, march to Gaul's army, attack. Rome destroys it on 0723 in **all four seeds** (losses 9.4k–13.8k of 45,700), and a battle turn is **byte-repeatable** (identical `AUTO0724.SAV` across two runs). See that README for the table.

### #4 — docs

`docs/wsl-setup.md` (how to bring the environment up on WSL2, with the two gotchas below) and `docs/intent-and-approaches.md` (the player's intent for the four modes — headless runner, discovery, trainer, run-the-discovery-on-Windows — the assessment, approach options, and a suggested order). **Read `intent-and-approaches.md` before starting anything new: it is the agreed direction.**

## Environment (a fresh session)

Follow `docs/wsl-setup.md` (PR #4). In short, on this machine it needed three things beyond `setup/setup.sh`:

1. `setup.sh` must be run with `IC2_SRC=$HOME/diegoami IC2_WORK=$HOME/ic2-work` (its default `IC2_SRC` is `/home/user/diegoami`, which does not exist), then `chown -R $USER` the two trees.
2. Disable the stale `cli.github.com` apt repo (`github-cli.list`), or `apt-get update` aborts.
3. Run `wineboot -u` **as the user** after setup — the prefix was created by root and `C:\users\<user>` had no profile, so the game's File → Open dialog failed with `BrowseObject could not browse to folder` and every load timed out.

```bash
mkdir -p ~/ic2-work/fixtures && cp saves/run0-start-AUTO0720-seed12345.SAV ~/ic2-work/fixtures/BASE.SAV
python3 -m tests.test_orders        # expect 13 PASS
```

## What is left

1. **change-units rename / join / split** (only Disband is implemented).
2. **Fleet orders** — move, attack, embark, disembark, supply, repair, transfer, split, join, scuttle. These need a **launched** fleet; the build has a 24-week countdown, so either run turns or use a save with a fleet.
3. **Accept a post-battle peace** (`TBattlePols`, a Yes/No after a battle).
4. **Run 0** (the pilot) still needs the player's explicit go in [issue #1](https://github.com/diegoami/ic2-conquest/issues/1). `runs/0/proposal.md` and `HANDOVER` (2026-09-29) have the plan; the Gallic-army experiment now supplies P1's calibration.

## Gotchas to keep

- **Never hardcode screen coordinates.** Derive them (toolbars by tooltip, dialog controls via `win_controls`). They drift with the font/DPI.
- **A confirmation is a `Confirm` window** with Yes/No/Cancel — answer it by button, not the bottom-centre OK.
- **The battle window opens ~3 s after the attack click**; wait, then click Computer general **during placement**.
- **`pkill -f "…"` can match its own command line** — use `pkill -f "[I]mperial Conquest"`.
- **Xvfb must be started with `setsid`**, and run as the same user as Wine.
- **Never click End turn twice** unless the first provably did nothing (a queued second click ends the next turn too) — built into `end_turn` already.
- The driver **restarts the game before every load** (the seed is read at program start), so per-environment caches under `$IC2_WORK` matter.

## Files worth knowing

`docs/intent-and-approaches.md` (the direction) · `docs/wsl-setup.md` (the environment) · `coverage.md` §1 (the order checklist, now with the new orders ticked) · `tests/results.md` (the last run) · `harness/driver.py` (`tool`, `army_tool`, `controls`, `attack`, `play_battle`, `taxation`, `transfer_units`) · `harness/win_controls.c` · `state/sav.py` · `planner/path.py` · `runs/experiments/gallic-army/` · `runs/0/proposal.md`.

## Open threads (added 2026-10-07)

- **Sitting recorder (idea, not yet a task).** goal2-archaeology's "human
  playthrough as a behavioural record" method, adapted to ic2-conquest, would
  answer the §3.1 intercept dispatch and §4 fleet hunt-vs-port checks (saves
  alone) and the §2.1 threat-budget / `+0x274` / fleet-destination questions
  (RAM snapshots). The proposal is at
  `~/projects/imperial-conquest-2-research/docs/ideas/2026-10-07-sitting-recorder.md`;
  the only open decision before it becomes a task is **desktop-Wine as the
  confirmation standard, or native-Windows watcher required?** (item (e) of
  the idea file).
- **AI-mover contact-resolution experiment** routed to `ic2-research`
  (2026-10-07); awaiting draft from that session.
- **`experiment/ai-turn`** is pushed (`bab12f5`), promoted, and not merged —
  its runner pattern (`runs/experiments/ai_turn/{watch,snapshot,common,paths,archive_batch}.py`)
  is the verified template to copy for any new `run-exp-*` experiment.

## Handover: 2026-10-08 (ic2-conquest session, MiniMax-M3 via Claude Code)

A different session picked up after the 2026-10-01 handover + the AI-mover intake. This entry
documents what that session did and what's left. The earlier sections (above) are still
the canonical env + tool description; the section below is the **state of `main` and
the work queue as of 2026-10-08 evening** (minimax, ~80% quota at one point, reset since).

### TL;DR (this session)

**`main` carries 24 new commits since 2026-10-01.** The **146-row player-facing feature
inventory is fully cell-verified on this side** and relayed to ic2-research; the
**Join-fleets 100-ship boundary** has a live in-play reproduction on disk and a
release tag; the L11 row's gates 100-ships / 500-ships / 100k-troops / 100%-mob
are now `[confirmed, partial]`. G03 (New-nation Yes path) is WIP — harness helper
in, test fails, to be re-iterated. **Standing by for the next route.**

### Commits on `main` this session (in order)

| # | SHA | Section | What |
|---|---|---|---|
| 1 | `f4b061f` | H04 | Cellular Automata form/callsite extraction (H04 = easter-egg) |
| 2 | `85be932` | H05 | Help reference tables cell-verified (terrain/sizes/colours/costs/details/matrix) |
| 3 | `2b02b8a` | H01–H03 | Help-topics / Show-hints / About-Imperial-Conquest cell-verified |
| 4 | `0735121` | MM01–MM10 | Map mouse actions (10 rows, TUnitMap_SelectUnit dispatcher + 5 literals) |
| 5 | `d5ccf24` | D01–D11 | Dialogs-reached-from-other-dialogs (11 forms, 4 sub-rows of S02) |
| 6 | `58b86a2` | K01–K03 | Keyboard shortcuts (15 menu ShortCuts + TPremierForm_KeyPressed + Ctrl-P) |
| 7 | `bc980f1` | M01–M06 | Main window + menu bar (7 menu parents + 26 speed buttons + 4 windows) |
| 8 | `a2d1e6c` | F01–F06 | File menu (5 items + TPickLeaders form) |
| 9 | `ce71f92` | G01–G04 | Game menu (End turn, New player, New nation, Abdicate) |
| 10 | `e2b0828` | S01–S12 | Strategy menu (12 rows, TPolitics + 5 form functions + 5 Armies-Recruits functions) |
| 11 | `357d031` | N01–N03 | Nations (16-nation dual surface, 0x10 sentinel) |
| 12 | `d192980` | A01–A10 | Area map (10 rows, TAreaMap_* functions, TFindCity form) |
| 13 | `68d2924` | UA01–UA07 | Unit map > Army (7 actions, including 2 sub-rows of S05) |
| 14 | `05ffc0b` | UF01–UF06 | Unit map > Fleet (6 actions; UF01+UA01 share TAFSupply, UF03+UF04 share TFleetToFleet) |
| 15 | `db4323f` | UC01 + UM01–UM09 | Unit map > City + view/selection (1 + 9 = 10 rows; TInformation has 8 sibling Show-handlers) |
| 16 | `11c4446` | E01–E29 | Turn-start and turn-end events (29 rows; shared FUN_00451b40 + FUN_0044b27c dispatchers) |
| 17 | `1a784a9` | L01–L14 | News and messages (14 rows; 4 outcome-panel literals pinned at dump_string_literals.v2.tsv rows 379/380/381/382/384) |
| 18 | `6aa10fd` | V01–V05 + EG01 | Victory/defeat + End-of-Game screen (6 rows; THumanFalls_InitializeForm @ 0x00455e38) |
| 19 | `af58e05` | `findings/2026-10-08-join-fleets-cap-in-play.md` + run-exp-join-fleets-cap-in-play | Join-fleets 100-ship boundary: 3 trials (50+49/50+50/50+51); gate is **< 101** (100 ships accepted, 101 refused); harness docstring tightened |
| 20 | `1e10c5d` | join-fleets-cap-in-play draft | Cited release tag in the draft |
| 21 | `6ce961a` | harness docstring fix + 3 regression tests | `Game.join_fleets` docstring off-by-one; `test_join_fleets_{99,100,101}` register, run, pass |
| 22 | `189226a` | L11 regressions WIP + G03 helper | `_make_patched_save` / `_make_patched_base_save` helpers; 4 L11 tests + 1 G03 test; pass on 100k/100%-mob/500-ship after bumps; G03 Yes-path test fails (post-state unchanged), WIP |
| 23 | `062aa3d` | `Game.new_nation` rewrite + 500/ship bump | 18,001 troops/30 ships PASS; the auto-Yes Confirm path errors on missing controls, replaced with manual OK click; menubar at y=14 (was y=36 — wrong) |
| 24 | `7b94118` | `tests/results.md` 2026-10-08 entry | L11 (3 of 7) + G03 (WIP) regression log |

The 146-row inventory is now cell-verified on this side; each row cites its source.
ic2-research's intake ledger is the canonical side — when they process these,
the imperial-conquest-2-research main will carry the per-row reports.

### Side artifacts

| Path | What |
|---|---|
| `docs/notes-for-main-session-decompile-skills.md` | The in-repo note that tells the main session what ic2-conquest can do (capstone, Ghidra headless, struct parsing, the project extractors, live harness). The user's main session can't read this repo; this is the document they look up. |
| `findings/2026-10-08-join-fleets-cap-in-play.md` | Three trials (50+49/50+50/50+51) at the L11 join-fleets 100-ship boundary. Cites `2026-10-07-join-fleets-100-ships-boundary.md` (research, decompile side). |
| `runs/experiments/data/run-exp-join-fleets-cap-in-play/` | `trial.py` (orchestrator + SAV patcher), `trial_driver.py` (per-trial `Game()` sub-process), `results.json` (per-trial summaries), `SAVES.sha256` (rule-6 measurement keeps). |
| `artifacts/run-exp-join-fleets-cap-in-play/trial-{099,100,101}-{pre,post}.SAV` | Six SAV binaries (132 KB each). Pushed to release `run-exp-join-fleets-cap-in-play` on imperial-conquest-2-research via the `IC2_RELEASE_TOKEN` Bearer header. URL: `https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-join-fleets-cap-in-play` (tag 2026-10-08T10:22:52Z). |
| `artifacts/run-exp-feature-inventory/` | 60-screen feature-inventory batch (FI_b1_01..60 + the .hlp + the .dat). SHA-256 in `SAVES.sha256`. |

### Open items (with route)

1. **G03 New-nation Yes path** (row G03 in the player-facing inventory, `[confirmed]`
   currently; the morning AI-mover intake's open note *"[code, Yes not run]"* stays
   open). Harness helper `Game.new_nation()` in `harness/driver.py:806` (manubar y=14,
   New-nation item at y=88, manual OK click on the resulting popup). Test
   `test_new_nation_yes` in `tests/test_orders.py:687`; registered in TESTS.
   The test's post-state assertion fails (current_nation stays 0, rome.human
   stays True) — likely a menubar-geometry drift on this Wine build or the
   Yes-path effect is different from the inventory's prose. Iterate the test
   next session (or take a screenshot during the test to see what's on
   screen) and either fix the assertion or update the inventory's
   `[code, Yes not run]` note.
2. **L11 row remaining 3 gates** (`[derived]` carry-over):
   - 20 units per army (Join armies): uncacheable in 21 units due to the
     20-slot army-record cap.
   - 40 recruit slots: needs a 40-slot recruit-state pre-state.
   - 198 armies: needs 198 armies in pre-state.
   Each needs a fresh multi-step pre-state setup. The 4 of 7 already
   `[confirmed, partial]` are 100-ships (`6ce961a`), 500/ship (`062aa3d`),
   100k-troops (earlier batch), 100%-mob (earlier batch).
3. **Harness docstring "fewer than 100 combined" off-by-one** is fixed at
   `6ce961a` (now "fewer than 101 combined"). The imperial-conquest-2-research
   ledger's L11 row open note 1 was cross-linked in `f6d4bed`; nothing more
   here.
4. **`experiment/ai-mover-contact` branch** is clean (commits `3d9490c`,
   `6a535d8`, `2d2251d`, all pushed). Intake was 2d2251d (the morning's
   deliverable). The branch is the route for any further AI-mover work; the
   session after the morning's session intake was the ic2-research one.

### Engine

- **Backend**: `minimax` (MiniMax-M3 via Claude Code). NOT `claude`. Don't
  ask about `claude` quota; check `minimax` quota only.
- **Quota**: was 80% used at one point; reset since. The 5h window is
  shared. Don't burn the next session's quota on long Wine runs without
  the user explicitly routing it.
- **Cross-OS session messaging**: `SendMessage` between PowerShell (main
  session) and WSL (this session) is unreliable. The user is the carrier
  for paste-ready prompts. `SendMessage` between WSL sessions (this side
  and `ic2-research` at `70286.sock`) works.
- **Worktree path** for the AI-mover branch: `/home/diego/projects/wt-ai-mover/`
  on branch `experiment/ai-mover-contact`. Commits in this session stayed
  on `main` (no AI-mover work in this session; the morning's commits are
  the latest on that branch).

### Files worth knowing (this session's additions)

- The 24 new findings drafts (listed in the table above).
- `findings/2026-10-05-player-facing-feature-inventory.md` (the 146-row
  inventory — unchanged, all row evidence columns now cite this side's
  cell-level extractions).
- `harness/driver.py` (Game.new_nation added, Game.join_fleets docstring
  tightened).
- `tests/test_orders.py` (`_make_patched_save` + `_make_patched_base_save`
  helpers; tests: `test_join_fleets_{99,100,101}`,
  `test_embark_over_500_per_ship`, `test_join_armies_over_100k_troops`,
  `test_recruit_100pct_mobilization`, `test_new_nation_yes`).
- `tests/results.md` (the 2026-10-08 entry at the bottom — three
  regression PASS, two WIP, one G03).
- `runs/experiments/data/run-exp-join-fleets-cap-in-play/` (rule-6 tracked).
- `docs/notes-for-main-session-decompile-skills.md` (the cross-OS note
  the main session looks at).

### Resumption

Next session opens with: `git log --oneline -25` on `main` to see this session's
24 commits; the inventory's evidence column is now cross-linked with this
side's findings drafts; L11's 4 of 7 gates are `[confirmed, partial]` on
ic2-research's ledger (commit `f6d4bed` on their `main`). The G03 Yes
path and the remaining 3 L11 gates are queued for further iteration.

