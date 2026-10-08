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
