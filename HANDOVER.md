# Handover: 2026-09-29, end of the first working session

## Where things stand

- **Branch** `claude/focused-knuth-ci59fz`. Everything is pushed; nothing is merged into `main`.
- **Run 0 has not started.** The proposal is [issue #1](https://github.com/diegoami/ic2-conquest/issues/1) and `runs/0/proposal.md`. The player answered the questions in the session (recorded at the end of `runs/0/proposal.md` and in a comment on the issue), but asked for the remaining order tests and this handover first. **Get an explicit "go" in issue #1 before turn 1.**
- **Findings** (`findings/`, three drafts) were sent to the research session "AUTOSAVE IMPERIAL_CONQUEST" (session_01VrRVit3CMpJ5PbUA8RZc51) as a one-shot scheduled message at 2026-09-29 20:15 UTC, routine `trig_013u6cRqre8gCTyrK8J35qWr`. Its text is also `findings/PROMPT-for-research-session.md`.

**Note (merged from main):** the research repo answered #515 in parallel. See `2026-09-29-which-cities-may-recruit-and-troop-amounts.md` and `2026-09-29-fortification-orders-cost-rate-and-the-100-bug.md`, cited in `strategies/rome-v1.md`. They confirm the 75 % rule, add the refusal "This city's fortification has fallen below 75%." and the dialog amounts (battalion/5 up to a full battalion), and warn: **never order fortification to exactly 100 % with a remainder** (a bug resets the town to 0 %). This repo's `findings/…fortification-75.md` adds the third condition, "a city already holding one of your queued units". Otherwise it duplicates that report.

## Bring the environment back (a new container)

```text
sudo setup/setup.sh                 # ~5 min: apt (wine32, xvfb, xdotool, ffmpeg, tesseract), pinned clones, builds, Wine prefix
mkdir -p ~/ic2-work/fixtures && cp saves/run0-start-AUTO0720-seed12345.SAV ~/ic2-work/fixtures/BASE.SAV
python3 -m tests.test_orders        # ~5 min; expect 5 PASS (tests/results.md)
```

`IC2_RELEASE_TOKEN` is set in the environment, but the proxy refuses release calls (HTTP 403). Keep run artifacts in `artifacts/run-0/<season>/` and post the `gh release create` command at the end.

## Order driver status (`harness/driver.py`, layouts in `coverage.md` §2)

| Order | State |
|---|---|
| new game, open/load (with seed), save as, move, attack (siege), recruit, end turn | ✅ automated save-diff tests (`tests/test_orders.py`) |
| supply army, hire mercenaries, fortify, mobilize, relations (trade) | ✅ driven by hand this session and checked on saves (`saves/README.md`). `Game.supply/hire_mercs/fortify/mobilize/relation` are written, but **not yet run as methods**: add a test for each to `tests/test_orders.py` and run it before turn 1 |
| join armies, split, transfer, change units, disband, taxation, build fleet, fleet orders, field battle | ⬜ Split's dialog is mapped. Join needs two adjacent armies (turn 2 of the plan: make it the test). The Taxation toolbar button (129,58) opened nothing on its first try, so look again |

**Driver lessons** (all built in; keep them):
- Hover before a click.
- Prefer the toolbar to menus.
- Raise a dialog (`xdotool windowraise`) before clicking in it, because dialogs can end up under the main window.
- The first click into an inactive window may only activate it, so verify every effect and retry at most twice.
- File dialogs keep the last name, so clear the field.
- **Never click End turn twice** unless the first click provably did nothing: a queued second click ends the next turn too (seen once).

## Open questions found this session

1. **Silent trade no-ops:** proposing trade to Media, Thracia, Bithynia, Armenia or Galatia gave no box and no change. Six other nations refused with "You cannot trade with X." Is it a click problem (save a screenshot per attempt) or a silent AI refusal? Bithynia even offered trade at turn start.
2. **Mercenary hire cost 0.** The research predicted `(troops × price div 1000) × quality` from the purse (24 here). Check the quarterly pay at the first quarter (end of turn 0725), and write a finding.
3. **Auto-resupply after a human move** (research: code only) is still unobserved.
4. A tactical battle inside the AI phase has not yet been played under a fixed seed. Check that turns stay byte-repeatable through one.

## Next steps, in order

1. Add tests for supply, mercenaries, fortify, mobilize, relation (and join, over two turns) and run them. Update `tests/results.md` and `coverage.md`.
2. Taxation driver. Set 20 % if the player agrees (see the proposal addendum).
3. **Experiment the player asked about** (not done, out of budget): from the run-0 start, join the armies (0721), walk to Gaul's army, attack, and play the battle with *Computer general* under 3–5 seeds. This measures the odds of "defeat the Gallic army first", Rome's priority rule. Use the results for P1's `k`.
4. With the player's go in issue #1: play run 0 per the README (turn files, metrics, seasonal checkpoints, per-season video, debrief).

## Files worth knowing

`CLAUDE.md` (rules, condensed) · `docs/rules-digest.md` (the rules, with sources) · `docs/sav-layout-notes.md` · `state/sav.py` (`can_recruit_at`, `siege_strength`, `siege_defence`, `consumption`) · `planner/path.py` · `saves/README.md`.
