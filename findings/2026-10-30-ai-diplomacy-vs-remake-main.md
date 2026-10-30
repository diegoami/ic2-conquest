# AI diplomacy, original vs remake main: one rule gap (the trade-swap pass), everything else is the rolls

**Tag:** [confirmed]. Every AI relation write of the original was logged with its caller and compared with remake main's
decisions on the same states, 16 New Game starts × 5 rounds. The one rule difference was checked with a scratch patch.
**Owner request:** 2026-10-30, "Diplomacy decisions", the next comparison after the AI army decisions
(`2026-10-30-ai-decisions-vs-remake-main.md`, whose §5 left diplomacy open).
**Remake compared:** main `05b02936` (T249), not released.

## Method

- **Original:** `patches/diplo_hook.py`, an observation-only build with four probes.
  1. **The relation setter `FUN_00449b40`** (entry): every relation write between two nations, with a, b, the new state,
     the relation before and the caller (its 22 call sites, research `decompiled-war-cascade-and-peace-paths.md` §1).
  2. **The AI diplomacy phase `FUN_0044fb7c`'s war candidate** (0x44FD22): the candidate, its power ratio, the busy
     flags and the trade counts.
  3. and 4. **Its two rolls:** `Random(10)` for war (0x44FD2F) and `Random(20)` for the alliance search (0x44FD61). The
     stub makes the original call and logs the result.
  - Runs: 16 starts × 5 End turns, seed 12345, the human seat giving no orders. The hooked autosaves are
    **byte-identical to the plain build in 80 of 80 turns**, and identical to the army comparison's run, so both
    comparisons use the same states.
- **Remake:** each round replayed from the original's autosave before it (`RemakeAdapter aiprobe ... ailog= events=`):
  its AI decision lines and its diplomacy, peace and battle domain events (new `events=` option).
- **Comparison** (`runs/experiments/diplo/compare.py`):
  - Per seat, both sides become actions: trade (loop 1 at 0x44FD0C or loop 3 at 0x44FEEF), swap (the 0x44FF7E +
    0x44FF8F pair), alliance (0x44FE5A), war (0x44FD47) and treaty (`FUN_00450c68` after an AI–AI instant battle). The
    treaty's own side effects (the sues branch's −10s, the ally loop) follow from it and are not compared.
  - Each round is walked in seat order. The first seat whose actions differ is classified as:
    - **draw**: a war or alliance on one side only, with the war target being the original's own candidate, so only
      the roll can differ;
    - **battle**: a treaty on one side only (`Random(5) < 2` after a battle, itself random);
    - **deterministic**: anything else.
  - Every later difference in that round is "after divergence".

## Result: 1,280 seat-turns

| | Remake main `05b02936` | Main + one-pass swap (§1, diagnostic) |
|---|---|---|
| seats the same | 1,088 | 1,132 |
| first divergence: **deterministic** | **10** | **0** |
| first divergence: draw (war or alliance roll) | 21 | 25 |
| first divergence: battle (treaty roll) | 19 | 19 |
| after the round's first divergence | 142 | 104 |
| **war candidates**, seats before divergence | — | **833 of 833 equal** (82 with a candidate) |

**Outside §1, every difference starts with a chance roll.**
- The war-target search (busy flags, neighbour, power ratio), the trade loops and the alliance candidate agree whenever
  the state agrees.
- The war candidate was compared with a log-only line in the diagnostic build (`BestWarTarget` per seat; no behaviour
  change).
- **Roll rates agree:**
  - war: the original rolled 107 times with a candidate and hit 8; the remake declared war in 11 of its 107 seat-turns
    with a candidate (expected 10%);
  - treaties: 27 in the original against 31 in the remake (86 remake battles);
  - alliance search: the original hit 23 of 666 rolls (expected 5%).

  The two games use different generators, so these differ draw by draw. That is not a rule difference.

## 1. The trade-swap loop is one pass in the original; the remake searches again after every swap

`FUN_0044fb7c`'s last loop (0x44FF04–0x44FFAC):

```text
for i in 0..15:                       // my current partners, table order
  for s in 0..15:                     // the richer replacement, table order
    if s != me and unity(s) > 0 and rel[me][i] == trade and rel[me][s] == peace
       and wealth(i) < wealth(s) (+0x44C) and trades(s) < 3 and not human(s):
        setRelation(me, i, 0)         // 0x44FF7E: the trade ends (-8)
        setRelation(me, s, 1)         // 0x44FF8F: the new trade
```

- **Original:** one pass. A partner gained during the pass is visited as `i` only if its index is above the current `i`,
  and a dropped partner is never revisited.
- **Remake** (`AiDiplomacyPhase.ProposeOwnTradeSwap`, `AiOwnDiplomacyRule.FindTradeSwap`): each call returns the
  **first** swap from the start of the table. The seat's greedy loop calls it again after every action. So a partner
  gained by one swap can be swapped away again in the same turn, and the swaps a turn makes are not the original's.
- **In play:** 10 rounds, all round 1 or 3, where the remake swaps more, or swaps a different partner. Examples:

  | Start, round, nation | Original | Remake main |
  |---|---|---|
  | S02 r1 Thracia | Numidia → Celtiberia, Galatia → Illyria | the same two, then **Illyria → Bithynia** |
  | S02 r3 Media | Illyria → Gaul, **Bithynia → Celtiberia** | Illyria → Gaul, then **Gaul → Celtiberia** (Gaul, index 6, was already passed in the original) |
  | S07 r1 Macedonia | 3 swaps | 5 swaps |

  Every seat before them in those rounds acted identically, so the relation matrix at their turn was the same.
- **Patch check** (`diag-v2.patch.txt`, `IC2_DIAG_SWAPPASS=1`): plan the original's single pass once per seat-turn, after
  the trade loops (when no trade partner is left), and offer those swaps in order. Deterministic divergences fall from
  **10 to 0**. A first version (`diag.patch.txt`) planned before the turn's trades and was wrong (8 rows the other way);
  it is kept.

## 2. Two structural notes (no row attributed to them)

- **Order inside a seat.** The original runs diplomacy, economy, armies, then fleets, each as one step. The remake's seat
  is one greedy loop by score: war declarations first, but trades (520) and swaps (480) after army marches (around
  1,500). So a seat's own battles, and their treaties, can come before its trades. Its own comment says so
  (`AiMilitaryPhase.ProposeOwnWarDeclaration` remarks). No row here needed it: with §1 patched, nothing deterministic is
  left. It would matter when a seat's battle changes its own trade counts the same turn.
- **The post-battle treaty gate is the same:** `Random(5) < 2`, then `unity(loser) > 500`, then `+0x446 > 7`
  (0x44B1C4–0x44B20A), against the remake's `InstantBattleResolver`.

## What this does not establish

- Rounds 6+, other seeds, and diplomacy involving a human's choices (Politics screen, offers).
- Whether battle outcomes match (they are random draws; `2026-10-30-ai-decisions-vs-remake-main.md`).
- The alliance search's partner choice when both games roll a hit in the same seat: that did not happen in these runs.
  It is compared only through the "same" rows.
- No production patch: the diagnostic patches are scratch copies, never pushed.

## Evidence

- Data: `runs/experiments/data/run-exp-diplo/`
  - `orig-v2/`: hook logs and inert checks;
  - `remake-05b02936-v1/`: main;
  - `remake-diag-v1/`, `remake-diag-v2/`: the diagnostic builds;
  - `report-main-v2.json`, `report-diag-v3.json` (earlier report versions kept);
  - `diag.patch.txt`, `diag-v2.patch.txt`;
  - `aborted/`: the first run, a 1-probe hook, stopped and replaced;
  - `smoke*`: BASE checks.
- Release `run-exp-diplo` (`diplo-saves.tar.xz`, 170 saves; hashes in `SAVES.sha256`).
- Saves cited: starts `S00_Rome_AUTO0720.SAV` … `S15_thracia_AUTO0720.SAV`; the round starts are the hooked autosaves
  `hooked-tNN-AUTO07xx.SAV` per start.
- Code:
  - `patches/diplo_hook.py`, `difftest/probes/diplo_hook_run.py`;
  - `runs/experiments/diplo/compare.py`;
  - `difftest/remake_adapter/AiProbe.cs` (`events=`).
