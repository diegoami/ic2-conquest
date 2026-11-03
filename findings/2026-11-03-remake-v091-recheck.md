# Recheck on remake v0.9.1 (0d9d4729): the garrison fallback's walk now besieges Sidon; no other anchored turn changes

**Tag:** [confirmed: remake replay against the stored original games]. Wine only (the original side is the stored runs).
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
against the stored original runs; `run-exp-recheck-0d9d4729/report-v1.md`): unchanged 113, FIXED 11, REGRESSED 11, CHANGED 4,
row for row identical to the v0.9.0 recheck (`run-exp-recheck-88c1989b`). The 11 "regressions" are the one storm draw
explained there; v0.9.1 changes no registered test.

## 4. A new long game on v0.9.1

RESULTS_PENDING (Ptolemaic, rulebot-1, 40 turns, seed 12345; `run-exp-longrun-v091`).

## Harness

`end_turn` now raises `GameOver(text, autosave=line)` when End of Game opens after the autosave line (the human
overthrown), and `difftest.campaign` stops cleanly after that turn (`summary.json` → `game_over`). Checked on Wine from
the turn-26 start (`turn26-repro/wine-v2-gameover`: GameOver 6.4 s after End turn). The campaign's frozen battle window
(`2026-11-02-seleucid-turn26-overthrow.md`) is a different screen and is not handled by this.

## Open

- D3 (#1732), code only.
- The Ptolemaic port tile (3 fleet rows) and the hunt-score distributions.
- Why individual battles happen in one game only (army side).
