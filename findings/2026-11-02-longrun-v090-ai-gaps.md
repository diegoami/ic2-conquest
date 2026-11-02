# Long runs against remake v0.9.0: two AI army gaps that repeat every turn (capital armies walked away; sieges by the mercenary-run branch dropped)

**Tag:** [confirmed: Wine hook + remake AI log]. Seed build in Wine; remake `aiprobe` decision and walk logs.
**Task:** owner request 2026-11-02, "parallel long runs with the original and the remake" (anchored + free-running, 4 starts × 40 turns).
**Status:** promoted by research PR #165 (merge `a0b21c5`) as `docs/reports/2026-11-02-longrun-v090-ai-gaps.md`.
Research checked `AiTurn.cs:330-351` and `AiMilitaryPhase.cs:433-440` at 88c1989b, the hook inputs and branches, and that
the hooked and plain saves are identical; it did not rerun Wine or the remake. Research added a code reading for gap A that is
not hooked: the original decides on the fallback with `FUN_0044aab4`, which returns `recomputedFullMoves != army[+6]`
(the army spent moves), not a change of tile (`2026-10-07-strategic-ai-turn.md` §3.5). A swing out and back has spent moves,
so EBE8 never runs; T156 compares tiles. A hook at 0x44aab4 on `t01-a04` would confirm it. The `fleetstarts/*.SAV` files
and the hook and probe saves are now in release `run-exp-longrun-v090` (`gaul-t30end.SAV`, `gaul-t39end.SAV`,
`rome-t16end.SAV`, `hooks-and-probes-saves.tar.gz`).
**Remake compared:** tag v0.9.0, `88c1989b`. Gap A is older: the Rome game's turn 5 moves the four capital armies on
`8e2d9053` and `e20a6488` to the same tiles, and on v0.8.4 `d9cc71bc` to other tiles next to them (gap B: checked on
`88c1989b` only).

## Method

`difftest/campaign.py` plays the rule bot (rulebot-1) as the human for 40 turns in both games; the original is one
process (seed 12345). `difftest/anchored.py` then replays **every turn** in the remake from the **original's own save**
at the start of that turn, with the original's orders, and compares the end of the turn. No difference carries over
between turns. `runs/experiments/longrun-v090/classify.py` sorts each turn's differences by kind; `stays.py` lists the
AI units that end the original's turn on their starting tile but are elsewhere in the remake.

| Game | Turns | Human phase (our orders) | AI phase: structural turns |
|---|---|---|---|
| Rome | 40 | 40 × draws only | 39 |
| Carthage | 40 | 40 × draws only | 38 |
| Gaul | 40 | 40 × draws only | 39 |
| Seleucid | 25 (stops at turn 26 in every run: driver, below) | 25 × draws only | 23 |

"Draws only" = troop sizes, recruit types, supplies, treasury, storm tiles. The structural AI rows are mostly the two
gaps below; the rest (relations, city captures, battle outcomes) are not attributed here.

`stays.py` over the four games (data: `runs/experiments/data/run-exp-longrun-v090/stays-v2.txt`):

| Unit next to | Rows | Cases |
|---|---|---|
| its own capital (army) | 410 | Macedonia (Pella), Media (Ecbatana), Thracia (Byzantium), Ptolemaic (Alexandria), Seleucid (Antioch): every turn they are idle |
| an enemy city (army) | 17 | Carthage–Castulo, Seleucid–Astacus, Seleucid–Synnada, Ptolemaic–Sidon, Galatia–Cius (random) |
| another nation's city (army) | 3 | Armenia–Van (same as gap A) |
| own port (fleet) | 5 | Ptolemaic–Alexandria (port tile), Carthage–Utica, Leptis Magna (random hunt draw): gap C |

## Gap A: an army whose walk ends where it started gets a second march (garrison fallback) in the remake

**Original** (hook `patches/decide_hook.py`, run `hooks-decide-v1/t01-a04`, from the Rome game's save before turn 2):
Macedonia army 8 at (144,42), next to Pella (143,41), at peace: F31C inputs `city = -1` → branch **resupply**. The turn
ends with the army at **(144,42), 2 moves left**; in the Rome game it stays there from turn 2 to turn 40 (every
`original/tNN-*.SAV`). The walk itself is the out-and-back swing measured on 2026-10-30
(`2026-10-30-ai-decisions-vs-remake-main.md`: out to (147,44) and back).

**Remake** (`probes/capital-armies-t05`, aiprobe from the Rome save before turn 5): the same branch
(`MoveToResupplyCity`); the walk returns to (144,42) (2 walks, 6 of 9 moves, 3 left). Because the army's tile is
unchanged, `AiTurn` (`88c1989b` src/IC2.Engine/Ai/AiTurn.cs:330–351, T156) runs `RunGarrisonFallback`: a march toward
the capital (143,41). The army ends at **(146,44), 3 tiles from the capital, moves -1**. The log says
"garrison fallback moved army-8 to (143, 41)": that is the target, not where the army ended.

The same happens to Media army 10 (307,58) → (309,60), Thracia army 6 (169,38) → (167,38), Ptolemaic army 7
(191,95) → (192,97), Seleucid at Antioch (221,60) → (223,62) and Armenia army 1 at Van (256,47) → (257,44)
(`probes/carthage-rulebot1-40t-t36`: mercenary run, walk back to (256,47), then the fallback toward (262,34)).

**Hook of the fallback's gate (revision 2026-11-02, research's request):** `patches/aab4_hook.py` logs, after each walk
in F31C, the result of `FUN_0044aab4` (0x44F4CE). AL = 0 → `FUN_0044ebe8` (the garrison fallback) runs. Run
`hooks-aab4-v2` from the games' own saves (`aab4starts/rome-t01end.SAV`, `rome-t03end.SAV`, `rome-t06end.SAV`,
`carthage-t35end.SAV`); 38 walks, the hooked autosaves byte-identical to the plain build (4 of 4).

| Army after its walk | Moves left | AAB4 | Fallback |
|---|---|---|---|
| Macedonia 8 at (144,42), Media's capital army at (307,58), Thracia 6 at (169,38): back on the start tile (Thracia on turns 4, 7 and 36; on turn 2 it walked there from (169,37)) | 2 | 1 | no |
| Ptolemaic 7 at (191,95) (start tile) | 2 | 1 | no |
| Armenia 1 at (256,47) (start tile; Carthage game turn 36) | 3 | 1 | no |
| Carthage 2 at (37,62), Seleucid 5 at (178,41): the gap-B armies, start tile | 0 | 1 | no |
| Celtiberia 2 at (41,47): did not move | 8 | **0** | **yes** |
| the 20 other walks (to other tiles) | 0–8 | 1 | no |

So the gate is "the army spent moves", not "the army changed tile". An army whose walk ends where it started has spent
moves (AAB4 = 1), and the original never runs EBE8 for it. Only an army that did not spend moves gets the fallback.
This confirms research's code reading (`FUN_0044aab4` returns `recomputedFullMoves != army[+6]`,
`2026-10-07-strategic-ai-turn.md` §3.5). The remake's T156 tests tile equality (`AiTurn.cs:336-351`: `beforeTile.X ==
afterTile.X && beforeTile.Y == afterTile.Y`, with moves > 0), so it runs the fallback where the original does not. The
likely fix is to test spent moves (moves after the command < moves before), not the tile.

**Effect over a game:** in the free-running remake game these capital armies drift away from their capitals (Rome
game, turn 30: Macedonia's army at (146,53), Media's at (283,58) by turn 40), while the original's stay put for 40 turns.

## Gap B: the mercenary-run branch next to an enemy city besieges in the original and steps aside in the remake

**Original** (hook runs `t03-a03` and `t06-a03`, from the Rome game's saves before turns 4 and 7):

| Army | Inputs | Branch | End of the turn |
|---|---|---|---|
| Carthage army 2 at (37,62), Castulo (36,61) at war | city score 98, dist 1; army score −10000; supplies 141 > 21,878/500 | `e84c+city>85` (mercenary run) | stays at (37,62); Castulo loyalty 77 → 74; 21,878 → 20,732 troops |
| Seleucid army 5 at (178,41), Astacus (177,41) at war | city score 97, dist 1; supplies 474 > 11,224/500 | `e84c+city>85` | stays at (178,41); Astacus loyalty 52 → 50; 11,224 → 10,630 troops |

In the Rome game this repeats every turn: Castulo 80 → 77 → 74 → 71 (turns 3–5), Astacus 52 → 50 → 48 → 46 → 44
(turns 7–10), the army losing 500–700 troops a turn, until the army is gone or the score passes 100 (`city>100` attacks).

**Remake** (`probes/seleucid-siege-t08`, `probes/gaul-rulebot1-40t-t6`, `probes/seleucid-rulebot1-40t-t8`): the same
branch (`MercenaryRun`, city score 94, 95, 88). No mercenary offer is in reach, so the continuation
`MarchAtCityTarget` adds a plain march at the city (`AiMilitaryPhase.cs:433–440`, "march at the enemy-city target").
The walker cannot enter the city and moves the army to another tile next to it: Astacus (178,41) → (178,42), Synnada
(186,44) → (187,44), Sidon (221,70) → (222,71), with moves left (1, 9, 3). **No siege**: the city's loyalty and the
army's troops do not change. `siege gates: 1 adjacent, 0 tree-selected for attack city`. With a city score of 102 the
tree selects `AttackCity` and the remake besieges like the original (Galatia–Cius, Seleucid game turn 12).

Not hooked here: which original call turns the continuation into a siege (the army does not leave its tile; Carthage
kept 9 moves). The outcome is measured; the mechanism is for research.

## Gap C: AI fleets in their own port: a random hunt draw, plus one port tile (not a rule gap)

Fleet-phase hook (`patches/fleetphase_hook.py`, run `hooks-fleet-v1`, from the games' own saves; hooked autosaves
byte-identical to the plain build):

| Start | Original (F608 inputs, end) | Remake (`aiprobe`, seeds 12345, 1–5) |
|---|---|---|
| Gaul game, before turn 31: Carthage fleet 0 at Utica (93,76) | hunt score **106** → hunts to (122,80) in the hooked run; **stayed** in port in the game itself | 116 at seed 12345; 82, 117, 127, 106, 90 at seeds 1–5 (hunt when > 100) |
| Gaul game, before turn 40: Carthage fleet 0 at Leptis Magna (111,93) | score **98** → port, stays | 107; 108, 107, 116, 91, 90 |
| Rome game, before turn 17: Ptolemaic fleet 1 at (189,93), port Alexandria | no route, hunt −10000 → port branch; stays at (189,93) | port branch; ends at (188,92) |

- **The hunt score is random in both games.** The original hunted from the same state in the hooked run but not in the
  game (a different random stream), and the remake's score spreads from 82 to 127 over seeds. The hunt branch and its
  `> 100` boundary are exercised here for the first time (the 16 × 5 fleet comparison had only −10000 scores,
  `2026-10-31-ai-fleets-vs-remake-main.md`). Two samples cannot show whether the two distributions match: a seed sweep
  of the original's scorer `FUN_0044f4f8` would.
- **Port tile (open, small):** for Ptolemaic fleet 1 next to Alexandria, both choose the port branch, and the original's
  fleet stays on its tile while the remake's moves one tile, to (188,92). 3 rows (Rome game turn 17, Carthage game turn 2, Seleucid game turn 20).
  The port pick is `FUN_0044e9a8`.

## Other results of the long runs

- **Recheck of the registered difftests on 88c1989b:** 113 unchanged, 11 FIXED (walk stops at own city on the line ×4,
  fleet second walk 87-47, move-far / move-sea refusals, walk-line-clear, storm30 ×3, fleet-sail). The 11 REGRESSED
  are one random storm draw on the human fleet (condition 96 vs 97; remake seeds 1–12 give both on v0.9.0 and v0.8.4),
  so not a regression (`runs/experiments/longrun-v090/NOTES.md`).
- **Free-running games:** the remake's games diverge from turn 1 (random draws). Over 40 turns (Rome game) the remake's
  Seleucid takes all of Bithynia and Galatia by turn 20; the original's Galatia survives with 9 cities. The remake fields
  20 armies at turn 40 against the original's 9 (Greece, Illyria, Numidia raise armies only in the remake). The anchored
  replays show army counts equal turn by turn (2–5 count rows per game), so this builds up through divergent wars, not
  a per-turn rule.
- **Our harness (open):** the Seleucid game stops at turn 26 in every run (r1-r4, deterministic). After the End turn's
  autosave a window "Ptolemaic v Seleucid — Seleucid to move units" is open, so Ptolemaic attacked and the human
  defends. It blocks File > Save, and the driver's battle flag `0x4A0B7C` reads 0, so `play_battle` does not run. Two
  `end_turn` changes did not catch it and were reverted. Run r5 records the seat, the flag and screenshots, and tries
  Computer general plus End turn clicks. The Seleucid rows above use r1's 25 turns. This is a driver limitation, not a
  game difference.

## Data

`runs/experiments/data/run-exp-longrun-v090/` (turns, anchored rows, probes, hook logs); saves in release
`run-exp-longrun-v090`. Remake pin `88c1989b`, build `artifacts/diffpin-88c1989b-build`.
