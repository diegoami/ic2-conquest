# Faithful AI: a war declared in an AI seat mobilises recruits in the same seat in the original, not in the remake (audit #195, X1)

**Tag:** [confirmed: decompile + anchored remake replays of stored original games]. Wine only for the original side
(the stored games). No new Wine run.
**Status:** draft for research, written as a remake issue candidate.
**Task:** research #195, cross-cutting difference X1 (phase order) in `findings/2026-11-04-ai-audit195-inventory.md`;
step 2 of the 2026-11-04 night handover. The inventory had X1 as "confirmed on both sides in code; not measured". This
report measures it.

Remake pin: **v0.9.4** = `168dbc04`. Ruleset `classical-faithful`, Instant battles (anchored replays).

## The two orders

- **Original:** `FUN_0044fa20` (the AI seat) runs diplomacy `FB7C`, then the economy `FFBC`, the armies `F31C`, the
  fleets `F608` (research PR #156 confirmed this order).
  - `FFBC` sums a **threat** for the acting nation: 15,000 for each nation it is at war with (relation 3), plus the
    armies of the nations it is at war with, plus a quarter of every foreign army within 10 tiles and half of every
    enemy army within 20.
  - It sums its **strength**: 6,000 per ally, plus its own armies and half of its allies' armies.
  - When the threat exceeds the strength, it calls `FUN_004504f4(threat − strength)`, which mobilises ready recruits.
  - Because `FB7C` runs first, **a war declared in this seat already counts** for this seat's mobilisation.
- **Remake** (`src/IC2.Engine/Ai/AiTurn.cs` at `168dbc04`):
  - line 150: `AiFaithfulEconomy.Run` (threat `FaithfulThreatPerEnemyNation` × wars, `AiFaithfulEconomy.cs:252`), then
    capital defence (line 158) and the hire pass (line 187);
  - line 241: the scored loop, in which `AiDiplomacyPhase.Propose` (loop line 38) offers the war candidate.
  - A war declared in this seat therefore reaches the economy **only in the nation's next seat**.

## Measurement

`runs/experiments/audit195/x1_war_seats.py` scans the 19 stored games replayed on `168dbc04` (`anchored-168dbc04-ts`,
the 898 turns of `2026-11-04-remake-168dbc04-recheck.md`). For each turn it lists the wars (relation 3) that start during
the AI phase, in the original and in the remake:
- **234 war starts.** Most occur in one game only (109 original only, 105 remake only), as expected: the war rolls are
  draws and the turn seed is not the original's.
- **20 start in both** (the same pair in the same seat). They are 13 declarer seats, 11 of them distinct (Rome t26 and
  t29 repeat in the Rome 150-turn game).

`x1_mobilise.py` reads, for each of those seats, the declarer (from the remake's receipt, "A declares war on B") and its
ready recruits (slots at state 24), treasury and mobilisation, before the AI phase, after the original and after the
remake. In every seat the declarer was at war with no one before.

| game | turn | declarer | ready recruits before → original / remake | treasury before → original / remake | position rows |
|---|---|---|---|---|---|
| rome-rulebot1-40t (and -150t) | 29 | Ptolemaic (war on Carthage, Numidia) | 46,300 → **24,900** / 46,300 | 4,030 → 2,645 / 4,030 | Ptolemaic armies, fleets |
| macedonia-rulebot1-40t | 27 | Seleucid (war on Armenia, Media) | 78,600 → **39,400** / 78,600 | 3,961 → 3,405 / 3,961 | Seleucid armies |
| armenia-rulebot1-40t | 36 | Ptolemaic (war on Carthage, Numidia) | 46,300 → **24,900** / 46,300 | 5,036 → 5,061 / 6,576 | Ptolemaic armies, fleets |
| greece-rulebot1-40t | 8 | Carthage | 4,200 → **3,000** / 4,200 | 11,287 → 10,762 / 11,287 | none |
| the 7 other seats | | | equal in both games | | none |

- **In the original, 3 of the 11 seats mobilise in the same seat as the war.** A fourth, Greece t8, probably does too, but
  its slot change has not been decomposed.
- **The remake mobilises in none of them.** No seat shows the reverse (the remake mobilises and the original does not).

**What it moves.** Rome t29, Ptolemaic:
- Five slots at state 24 are mobilised: hc 900, hi 5,000 and li 7,500 at the capital, city 214 (190,94), and hc 2,200 and
  lc 5,800 at city 267 (223,88).
- The capital's three join the main army, which goes from 64,030 to 77,430 at (192,94). City 267's two become a new
  8,000-man army at (223,89). Mobilisation goes from 9 to 12.
- In the remake, the army stays at 64,030 and there is no second army. Its fleet also ends elsewhere: at (192,93) beside
  the army, against (218,85) in the original.

Macedonia t27, Seleucid: the same, with 16,200 men joining the main army at (211,45) and a new 23,000-man army at
(188,59) from city 206.

So these are the position rows of these seats. They were unattributed until now, and this report attributes them to X1.

## Expected and actual

- **Expected (original):** the AI economy's threat budget includes wars declared earlier in the same seat. The nation
  mobilises in the seat where it declares war.
- **Actual (remake):** the economy runs before the war candidate is chosen. Mobilisation waits for the nation's next
  seat, one round later.
- **Candidate fix:** in Faithful, run the own-diplomacy decision (war, alliance, trade) as a phase before
  `AiFaithfulEconomy.Run`, as in FA20. Or, the narrower fix: re-run the Faithful economy after a war is declared in the
  seat.

## Scope and open

- **Measured: only the economy consequence.** The inventory lists three others of the same order: the capital-defence
  radius (19 at war, 9 otherwise), the hire gate ("at war with someone") and the busy test. They are expected to differ
  the same way, but they are **not measured here**. Capital defence runs before the loop in the remake (line 158); in the
  original it runs at F31C entry, after FB7C.
- **The fleet row** in Ptolemaic t29/t36 is consistent with a fleet that follows the army it would carry. It is not
  traced.
- **Wine control (optional):** the stored games already give the original side. A staged control would need a seat
  whose war roll is forced, so it adds little.

## Evidence

- `runs/experiments/data/run-exp-audit195/x1-war-seats-v1/`: `war_seats.jsonl` (234 rows) and `mobilise.jsonl`
  (13 rows).
- The saves this reads:
  - **Original games:** releases `run-exp-longrun-v090` (`rome-rulebot1-40t-saves.tar.gz`), `run-exp-longrun-v091`
    (`macedonia-rulebot1-40t-saves.tar.gz`), `run-exp-longrun-v092` (`greece-…`) and `run-exp-longrun-v093`
    (`armenia-…`). The seats are `t29-a00.SAV` → `t29-a01.SAV` (Rome) and `t26-a01.SAV` → `t27-a00.SAV` (Macedonia).
  - **Remake replays:** release `run-exp-longrun-v093`, `recheck-168dbc04-anchored-saves.tar.gz`
    (`anchored-168dbc04-ts/tNN/a*.SAV`).
- Tooling: `runs/experiments/audit195/x1_war_seats.py`, `x1_mobilise.py`.
