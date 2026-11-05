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
| the 7 other seats | | | ready recruits equal; but see §Follow-up: 4 of them raise new slots in the original | | none |

- **In the original, 3 of the 11 seats mobilise ready recruits in the same seat as the war.** The follow-up below
  extends this to **8 of 11** seats once raised slots are counted (research intake PR #207).
- **The remake mobilises or raises in none of them.** No seat shows the reverse (the remake mobilises and the original does not).

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

## Follow-up (2026-11-05, research PR #207): the 11 seats decomposed

**Correction.** Research noted that "the 7 other seats [are] equal" holds for ready recruits only. The mobilisation level
(`+0x442`) ends higher in the original in 8 of the 11 seats.

**The function.** `FUN_004504f4(gap)` has two parts:
- **(a) Mobilise.** It mobilises ready slots (state 24) through `FUN_0044a4e0` until the gap is covered. It does so only
  if an own army is within 6 tiles of a ready slot's city, or if there are 4 or more ready slots.
- **(b) Raise.** It raises up to 8 new slots (`FUN_004501f4`) in empty slots. It does so while the recruits do not cover
  the gap, the level is below 100, and the treasury test (or the first 3 slots) passes. Each raised slot costs treasury
  and adds `troops × 1000 / wealth + 1` to the level.

**Callers (decompile).** `FUN_004501f4` is called only by `FUN_004504f4`, and `FUN_004504f4` only by `FFBC`.
`FUN_0044a4e0`'s other caller is the human's recruit dialog (`TArmyRecruits_MobilizeUnits`). So in an AI seat, every
mobilised or raised slot comes from `FFBC`'s gap call.

**The decomposition.** `runs/experiments/audit195/x1_decompose.py` writes `x1-war-seats-v1/decompose.jsonl`. Slots are
matched as a multiset of (type, troops, city). In each row below, values before the arrow are the state before the AI
phase; after it, the original's end and then the remake's.

| seat | declarer | (a) mobilised | (b) raised | level | treasury |
|---|---|---|---|---|---|
| Rome t29 | Ptolemaic | 5 slots, 21,400 | hc 2,100, lc 6,700, li 9,100 at 214 | 9 → 12 / 9 | 4,030 → 2,645 / 4,030 |
| Armenia t36 | Ptolemaic | the same 5 slots | hi 4,500, lc 7,000, li 5,100 at 214 | 6 → 6 / 3 | 5,036 → 5,061 / 6,576 |
| Macedonia t27 | Seleucid | 8 slots, 39,200 | ar 2,900 at 292 | 15 → 16 / 15 | 3,961 → 3,405 / 3,961 |
| Greece t8 | Carthage | hc 1,200 at 72 | lc 7,000 at 70 | 12 → 14 / 12 | 11,287 → 10,762 / 11,287 |
| Gaul t7 | Carthage | — | hi 4,200 at 70 | 12 → 13 / 12 | 11,233 → 10,813 / 11,233 |
| Macedonia t12 | Carthage | — | ar 2,000, li 11,000 at 72 | 12 → 13 / 9 | 12,444 → 14,468 / 14,683 |
| Media t5 | Carthage | — | hi 6,000 at 70 | 15 → 17 / 15 | 10,114 → 9,352 / 9,952 |
| Media t1 | Greece | — | 5 slots at 166: hi 2,600, 2,800, 3,900; li 6,300, 10,000 | 0 → 13 / 0 | 920 → −134 / 948 |
| Rome t26 (Armenia), Gaul t31 (Seleucid), Numidia t30 (Macedonia) | | — | — | equal | equal |

**Result.**
- In 8 of the 11 seats, the original runs `FUN_004504f4` in the seat that declared the war. The remake runs it in none of
  the 11, because its economy runs before the war is declared.
- In the 3 remaining seats, neither game mobilises or raises. In those seats the gap with the new war is not positive, or
  the gates fail.
- **Attribution: 8 seats.** The 3 seats with position rows are attributed to X1 (above). The other 5 have no position rows
  in the seat: their raised slots are still recruits, not armies.
- **Assumption.** The war-free threat must be equal in both games, i.e. the remake's Faithful economy reproduces `FFBC`
  without the new war. Every case has the same start state, and no seat shows the remake running the gap call.

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
  (13 rows), `decompose.jsonl` (13 rows).
- The saves this reads:
  - **Original games:** releases `run-exp-longrun-v090` (`rome-rulebot1-40t-saves.tar.gz`), `run-exp-longrun-v091`
    (`macedonia-rulebot1-40t-saves.tar.gz`), `run-exp-longrun-v092` (`greece-…`) and `run-exp-longrun-v093`
    (`armenia-…`). The seats are `t29-a00.SAV` → `t29-a01.SAV` (Rome) and `t26-a01.SAV` → `t27-a00.SAV` (Macedonia).
  - **Remake replays:** release `run-exp-longrun-v093`, `recheck-168dbc04-anchored-saves.tar.gz`
    (`anchored-168dbc04-ts/tNN/a*.SAV`).
- Tooling: `runs/experiments/audit195/x1_war_seats.py`, `x1_mobilise.py`, `x1_decompose.py`.
