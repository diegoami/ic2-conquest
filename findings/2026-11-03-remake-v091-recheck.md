# Recheck on remake v0.9.1 (0d9d4729): the garrison fallback's walk now besieges Sidon; no other anchored turn changes

**Tag:** [confirmed: remake replay against the stored original games; Wine hook + remake code for section 4]. Wine only.
**Status:** promoted by research PR #181 (merge `597b996`) as `docs/reports/2026-11-03-remake-v091-recheck.md`. The IC-main
report `2026-11-02-remake-fixes-gaps-ab.md` gained a v0.9.1 section and the no-command-fallback fix. Research verified the
remake code at `0d9d4729` (both fallback paths, `mayMarch`), AAB4's formula in the disassembly (0x44AAB4–0x44AB0B), hook
seq 4–10 with its control, the probe lines, the anchored-diff and stays files and the recheck counts. Correction applied:
the recheck summary is `report-v1.json` (the `.md` is not archived). Not re-checked by research: the row-for-row match with
v0.9.0, `classify.py`, the GameOver change; "spent moves earlier" for the 8 moves is our reading.
**Task:** owner 2026-11-03, "Now we have version 0.9.1 and some fixes, continue with your tasks". Remake `v0.9.1` = main
`0d9d4729` = `11f713e2` + 4 commits. One changes the engine: `e1772c52` (fix 1729, PR #1731), the walk end check for both
garrison construction paths (`AiMilitaryPhase.AddMarchCandidate`'s no-tree-command fallback and `AiTurn.RunGarrisonFallback`).
It answers the gap-B row left in `2026-11-02-remake-11f713e2-recheck.md`. D3 (#1732) is not fixed in v0.9.1 (docs only, `2f120cf3`).

## 1. Anchored replay of the four long games

`python3 -m difftest.anchored <game> --pin 0d9d4729 --out anchored-0d9d4729` for Rome, Carthage, Gaul (40 turns) and Seleucid
(25): 145 turns, no remake error. `stays.py --anchored=anchored-0d9d4729` → `stays-0d9d4729-v1.txt`.

| Unit next to | v0.9.0 `88c1989b` | `11f713e2` | v0.9.1 `0d9d4729` |
|---|---|---|---|
| its own capital (army, gap A) | 410 | 4 | **4** (the four war declarations, attributed in `2026-11-03-diplomacy-longrun.md`) |
| an enemy city (army, gap B) | 17 | 1 | **0** |
| another city (army) | 6 | 0 | 0 |
| own port (fleet) | 5 | 4 | 4 (3 × the Ptolemaic port tile, 1 × the random hunt at Utica) |

**Per-turn difference counts** against the `11f713e2` replay (`anchored-0d9d4729-vs-11f713e2-v1.txt`): 144 of 145 turns
are unchanged in all four counts (human fields, human map cells, AI fields, AI map cells). The one changed turn is Seleucid
turn 10, whose AI differences drop from 28 fields / 7 map cells to 22 / 5. Totals: AI fields 6,485 → 6,479, AI map cells
63,657 → 63,655. So the fix touches only the measured case in this sample.

## 2. The Sidon case, AI probe

`probes/0d9d4729-seleucid-rulebot1-40t-t10` (start `seleucid-rulebot1-40t/original/t09-a02.SAV`, seed 12345, no human
orders): Ptolemaic army 6 at (221,70) gets "garrison fallback (221, 71)", then "original walk end contact army-6 at
(221, 71)" and `battle.besiege-city`; it stays on (221,70) with its moves spent, and Sidon (city 263, Seleucid) is
besieged (`BattleResolved` army-6 vs sidon). The original's hook run (`hooks-gapb-v2`, seq 111–119) did the same: EBE8 →
DBA8 from 0x44ECD6 → D734 → B27C from 0x44D949. Army 5's fallback to its own capital Alexandria (190,94) still has no
contact (F6D8 branch in the original).

## 3. Registry recheck

`python3 -m difftest.recheck 0d9d4729 --version v1` (order sweeps, stats scenarios, 5-turn campaigns, remake side replayed
against the stored original runs; `run-exp-recheck-0d9d4729/report-v1.json`): unchanged 113, FIXED 11, REGRESSED 11, CHANGED 4,
row for row identical to the v0.9.0 recheck (`run-exp-recheck-88c1989b`). The 11 "regressions" are the one storm draw
explained there; v0.9.1 changes no registered test.

## 4. A new long game on v0.9.1: one new gap, the no-command fallback has no AAB4 gate

Ptolemaic, rulebot-1 as the human, 40 turns, seed 12345, free-running and anchored (`run-exp-longrun-v091`; runner
`runs/experiments/longrun-v090/run_all.sh` with `NAME=run-exp-longrun-v091 PIN=0d9d4729`). 40 turns played, no
game over, no remake error. Saves are in release `run-exp-longrun-v091`.
- **Anchored totals** (40 turns): AI fields 1,808, AI map cells 14,181; human 26 / 110.
- **`classify.py`** (`classify-v1.txt`): 20 AI turns with only draws, 20 structural turns, 141 nation-turns with a
  relations difference (mostly the quarterly thaw), 15 with a position difference.
- **`stays.py`** (`stays-v1.txt`): **one row**. Turn 1, Galatia army 12, 19,300 troops at (200,45), stays in the
  original; in the remake it walks to (198,46). Iconium (197,47), Galatia's own city, is 3 tiles away.

**The original** (hook `patches/gapb_hook.py`, run `hooks-gapb-galatia-v1`, start `starts/ptolemaic-t00start.SAV` = the
campaign's `t00-start`, watched armies 12 and 6; hooked autosave byte-identical to the plain build). In this round
Galatia's seat comes first (seat order 12, 2, 15, 7, 10, 4, 14, 13, 0, 11, 1, 6, 8, 9, 5). The mid-round move refill
comes later, before Illyria's seat. So army 12 still has the 8 moves the save gives it:
1. E41C supply pass, then F6D8 (city 233, not at war);
2. E84C mercenary run, with no walk;
3. **AAB4 = 1** (seq 9–10).

`FUN_0044aab4` recomputes the full allowance: 10 − min(troops / 20,000, 5), or 9 − … when supplies × troops / 10,000 < 10.
For 19,300 troops and 73 supplies that is 10. It returns 1 when that differs from the army's moves (8). So F31C does not
call EBE8, and the army stays on (200,45).

**The remake** (`probes/0d9d4729-ptolemaic-t01`, the same start, no human orders): the target tree gives army-12 no
command, and "garrison fallback (197, 47) with army-12: 3 tiles away" walks it to (198,46).

**The cause:** fix 1723 (`AiTurn.cs:336–354`, `afterTile.Moves == SupplyMoraleRule.MovesForActionCheck`) gates only the
fallback that follows an executed command. The remake's other fallback, for an army the tree gives no command
(`AiMilitaryPhase.cs:487–503`, "the army that never got a command at all"), runs on `mayMarch` alone. In the original
both cases go through the same F31C call to AAB4. The fix is the same full-allowance test on that path, under Classical
Faithful navigation.

It shows only when an army has fewer than its full moves at its seat. Here that is because the seat comes before the
mid-round refill and the army had spent moves earlier. One row in 40 turns. None in the other four games, where every
fallback row was gap A after a command.

## Harness

`end_turn` now raises `GameOver(text, autosave=line)` when End of Game opens after the autosave line (the human
overthrown), and `difftest.campaign` stops cleanly after that turn (`summary.json` → `game_over`). Checked on Wine from
the turn-26 start (`turn26-repro/wine-v2-gameover`: GameOver 6.4 s after End turn). The campaign's frozen battle window
(`2026-11-02-seleucid-turn26-overthrow.md`) is a different screen and is not handled by this.

## Open

- The no-command fallback's AAB4 gate (section 4): for IC main.
- D3 (#1732), code only.
- The other 14 position nation-turns of the Ptolemaic game (not stay-versus-move; not attributed).
- The Ptolemaic port tile (3 fleet rows) and the hunt-score distributions.
- Why individual battles happen in one game only (army side).
