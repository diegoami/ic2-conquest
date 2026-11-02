# Recheck on remake main 11f713e2 (fixes 1723, 1724): gaps A and B fixed; the garrison fallback's walk still misses the siege

**Tag:** [confirmed: Wine hook + remake replay]. Wine only.
**Task:** owner 2026-11-02, "there is a new head for the remake". Remake main `11f713e2` = v0.9.0 + 6 commits, including
`9588fe3e` (fix 1723: spent-move swings without the extra fallback, gap A) and `11f713e2` (fix 1724: Faithful walk end
contacts before the fallback, gap B). It answers `docs/reports/2026-11-02-remake-fixes-gaps-ab.md` (research PR #171).

## Method

`difftest/anchored.py --pin 11f713e2 --out anchored-11f713e2` replays every turn of the four stored original games (Rome,
Carthage, Gaul 40 turns; Seleucid 25), each from the original's own save. 145 turns, no remake error.
`runs/experiments/longrun-v090/stays.py --anchored=anchored-11f713e2` lists the units the original leaves on their tile and the
remake moves (`stays-11f713e2-v1.txt`; v0.9.0: `stays-v2.txt`).

| Unit next to | v0.9.0 `88c1989b` | `11f713e2` | The rows left |
|---|---|---|---|
| its own capital (army, gap A) | 410 | **4** | all 4 are diplomacy (below) |
| an enemy city (army, gap B) | 17 | **1** | Ptolemaic at Sidon: the fallback's walk (below) |
| another city (army) | 6 | 0 | |
| own port (fleet) | 5 | 4 | 3 × the Ptolemaic port tile; 1 × the random hunt at Utica (both unchanged) |

## The 4 capital rows are diplomacy, not gap A

In each of these turns the remake's nation declares a war the original doesn't, and its army then acts for that war:

| Game, turn | Nation | Relation in that turn (original, remake) |
|---|---|---|
| Carthage, 34 | Macedonia | Illyria (0, 3) |
| Carthage, 36 | Ptolemaic | Carthage (0, 3), Numidia (1, 3) |
| Gaul, 36 | Macedonia | Illyria (−2, 3) |
| Seleucid, 18 | Media | Seleucid (1, 3) |

The AI probe with no human orders (`probes/11f713e2-carthage-rulebot1-40t-t34`, `-seleucid-rulebot1-40t-t18`) keeps Macedonia 8
at (144,42) and Media's army at (307,58): the swing with no extra fallback, as in the original. Gap A is fixed. Whether these
war declarations are random draws or a rule difference is not attributed here.

## The gap-B row left: the garrison fallback's walk besieges in the original

**Seleucid game, turn 10:** Ptolemaic army 6 at (221,70), next to Sidon (221,71), city 263, at war with Seleucid. City score
84, below 85, so neither continuation applies.
- **Original** (hook `patches/gapb_hook.py`, run `hooks-gapb-v2`, start `gapbstarts/seleucid-t09end.SAV`, seq 111–119;
  hooked autosave byte-identical to the plain build):
  1. E41C, then E84C (called from 0x44F485), with no walk;
  2. AAB4 = 0, moves unspent (9);
  3. **EBE8** (the garrison fallback, from 0x44F4D9) calls the walk DBA8 **from 0x44ECD6**, target (221,71);
  4. `D734` (from 0x44DC16), then the siege **`B27C` from 0x44D949**, city 263, with 9 moves.
  
  The army stays on (221,70) and Sidon is besieged.
- **Remake `11f713e2`** (`probes/11f713e2-seleucid-rulebot1-40t-t10`): army-6 gets no tree command. "garrison fallback
  (221, 71)" moves it to (222,71), and the log reports `siege gates: 1 adjacent, 0 tree-selected`. No siege.

So D734's end check also runs at the end of the fallback's walk (EBE8 → DBA8 at 0x44ECD6). Fix 1724 resolves walk-end
contacts for the measured continuation and `city>100` walks only. The fallback is a third measured caller that needs the
same end check. In the same run, Ptolemaic army 5 at Alexandria (AAB4 = 0, EBE8 to its own capital) ends in `F6D8` (the
not-at-war city branch), with no siege.

**Still not observed:** the E84C run walk (0x44E913), and 0x44F409 / 0x44F47C ending next to an enemy city.

## Seleucid turn 26 (harness, open)

The game stops at turn 26 in every run. The watch build, which has no `no_delay`, stops identically, and its turns 1–25
match the fast build line for line, so `no_delay` is not the cause. At the freeze (`seleucid-rulebot1-40t-r6`,
`IC2_FREEZE_DIAG=1`):
- **CPU:** all 4 threads idle, 0 ticks in 3 s.
- **Backtrace:** the main thread waits in `win32u`, called from 0x00424A8E ← 0x00424521 ← 0x0045C3AD (the application's
  message loop). No game routine or patch code is on the stack.
- **Windows:** the X tree has no hidden dialog. The battle window "Ptolemaic v Seleucid — Seleucid to move units" exists
  but was never painted.
- **Battle flag:** 0x4A0B7C reads 0.

So the game is idle and waiting for input, with a battle window that isn't working. Whether the cause is Wine or the
original's own path for a battle the human defends at the start of their turn is not established; native Windows would
tell. Data: `seleucid-rulebot1-40t-r6/original/t26-a01-freeze-*.txt`.
