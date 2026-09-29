# Prompt for the next ic2-conquest session

---

You are continuing `diegoami/ic2-conquest`: a bot that plays the original 1996 *Imperial Conquest 2* headless under Wine, to find strategies that dominate the map and prove them with per-turn saves, plans and metrics.

**Read these first, in order:** `CLAUDE.md` (the rules), `HANDOVER.md` (where the last session stopped), then `runs/0/proposal.md` (including the player's answers at the end) and [issue #1](https://github.com/diegoami/ic2-conquest/issues/1) with its comments.

## Environment

1. Run `sudo setup/setup.sh`. It installs Wine, Xvfb, xdotool, ffmpeg and tesseract, clones the pinned research and fixtures repos, and builds `Imperial Conquest 2 fast rollingsave seed.exe` into `~/ic2-work`.
2. Copy `saves/run0-start-AUTO0720-seed12345.SAV` to `~/ic2-work/fixtures/BASE.SAV`.
3. Run `python3 -m tests.test_orders`. Expect 5 PASS before changing anything.

## Tasks, in order

1. **Finish the order driver.** `harness/driver.py` already has `supply`, `hire_mercs`, `fortify`, `mobilize` and `relation`. Each was driven by hand and checked on a save, but the methods have never run as written.
   - Add a save-diff test for each to `tests/test_orders.py` and make it pass.
   - Then drive and test **join armies**, over two turns (turn 1: army 1 → (113,45); turn 2: army 1 → (104,36), army 0 → (103,36), then join), and **taxation** (the toolbar button at (129,58) opened nothing on the first try; look again).
   - Update `tests/results.md` and `coverage.md`.
2. **Experiment: can Rome beat the Gallic field army early?**
   - From the run-0 start, carry out the plan: join the armies on 0721, march to Gaul's army (40,500 at (93,28), mostly light infantry), attack it, and play the battle with *Computer general*.
   - Run it under 3–5 seeds. Record both armies' composition before and after each battle, the winner and the losses.
   - Check that a turn containing a battle is still byte-repeatable under a fixed seed.
   - Write the results to `runs/experiments/` and summarise them in issue #1. They set P1's margin `k` and the escape rule.
3. **Open questions from the last session**, each written as a finding in `findings/` when resolved:
   - The mercenary hire deducted no money, although the research predicts `(troops × price div 1000) × quality` from the purse. Check what happens at the first quarter.
   - Trade proposals to Media, Thracia, Bithynia, Armenia and Galatia produced no box and no change.
4. **Update the run-0 plan** from the experiment. It follows the player's rules:
   - defeat armies before taking cities; escape and reinforce when Rome cannot win;
   - archers in the recruitment mix;
   - fill every trade slot;
   - propose 20 % tax.
   Post the updated turn-1/2 orders in issue #1.
5. **Then stop and wait for the player's explicit "go" in issue #1.** When it comes, play run 0 exactly as the README and `runs/0/proposal.md` describe:
   - `runs/0/turns/nnnn.md` per turn;
   - `metrics.csv` and `armies.csv`;
   - seasonal checkpoint comments, plus the Autumn week 11 winter check;
   - an ffmpeg recording per season;
   - `runs/0/debrief.md` at the end.
   Artifacts go to `artifacts/run-0/` (the proxy refuses GitHub releases). Put selected interesting saves in `saves/` with a line in `saves/README.md`.

## Hard rules (from CLAUDE.md)

- No EXE, DAT, screenshot or video in git. Only selected saves, in `saves/`.
- Never write to another repository.
- Never edit the player's words in a strategy file.
- No run before the player's approval.
- Every claim of progress cites a save.
- `IC2_RELEASE_TOKEN` is used only for release calls, and is never printed or written anywhere.
