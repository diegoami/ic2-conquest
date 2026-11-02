# Diplomacy in the long runs: the remake's AI diplomacy follows the original's code; war declarations and relation differences come from rolls and battles

**Tag:** [confirmed: code (both games) + Wine hook]. Wine only.
**Status:** promoted by research PR #178 (merge `6945db3`) as `docs/reports/2026-11-03-diplomacy-longrun.md`. The recheck
report's four war declarations now point to it as attributed. Research's intake notes:
1. **D3 is a remake departure from a documented rule.** Research's §1a pseudocode already has it as the `else if`: a nation
   that passes the war-candidate test is not offered a trade in the same iteration.
2. **The busy flag is confirmed.** `FUN_0044faa0` is called at 0x44FC21 and stored at 0x44FC55, *inside* loop 1, after the
   0 ≤ rel < 3 gates that jump to 0x44FD11. §1a had it before the loop and now carries a correction note.

Research did not re-check the §3 per-row chains, the 157 ±2 cooldown pairs or the 35-turn mask stability.
**Task:** owner 2026-11-03: "do war declarations and relations", and "can you decompile that in both games". Remake main `11f713e2`.

## 1. The code, side by side

**Original:** `FUN_0044fb7c`, the AI diplomacy phase, with its helpers (Ghidra dump, `all_app_functions.txt`):
- `FUN_0044faa0(n)` returns three things: n is at war (any relation 3); n is **protected** (an ally whose cities plus n's
  exceed the seat's); and n's trade count.
- `FUN_0044fb50` counts wars, `FUN_004499c0` counts trades, and `FUN_00449b40` is the relation setter. When it sets 0
  (peace), it writes a cooldown instead: −8 after a trade, −24 after an alliance, −18 after a war.

**Remake:** `AiOwnDiplomacyRule`, `AiDiplomacyPhase`, `AiMilitaryPhase.ProposeOwnWarDeclaration`, `OriginalTradeSwapPass`,
`QuarterlyThawSystem`, `AiDepositionHandler`; constants from `data/rulesets/classical-faithful.json`.

| Step | Original | Remake | Same? |
|---|---|---|---|
| busy | at war, or mobilization > 40, or winter (season 3) | `IsBusy`, threshold 40 | yes |
| power | treasury / 20,000 × unity / 100 | `Power`, 20,000 / 100 | yes |
| war candidate | not busy; relation 0–2; alive; neighbour mask bit; not protected; 8·P(me)/max(1, P(k)) > best, best starting at 10 | `BestWarTarget`: the same tests, 10 / 8 | yes |
| neighbour mask | nation record `+0x46`, never changes in play (35 turns checked) | the DAT mask; the importer reads each save's own | yes |
| war roll | `Random(10) == 0` | 1 in 10 (`warDeclareRollDenominator`), a per-nation, per-turn stream | same chance, different stream |
| alliance | not busy and no war this turn, `Random(20) == 0`; first neighbour j (relation 0–1, not protected) with an AI m at war with j, wars(m) < 2, cities(j) < cities(me) + cities(m) | `FindAlliancePartner`, 1 in 20, same order | yes (the roll comes before the search in the original, after it in the remake) |
| alliance pulls in wars | setter(…, 2) calls `FUN_00449a44`: the new ally joins its partner's wars | the same (Ptolemaic, below) | yes |
| trades | loop 1 and loop 3: relation 0, both under 3 trades, partner not human | `EligibleTradePartners`, cap 3 | see D3 |
| swap pass | one pass: a richer candidate at peace replaces a trade partner (−8) | `OriginalTradeSwapPass` (fixed since 2026-10-31) | yes |
| quarterly thaw | `FUN_00451b40`: each cooldown v → v + 1, or min(0, v + 3) on `Random(3) == 0`; only columns 0–7 of each row | `QuarterlyThawSystem`: 1, 3, 1 in 3, `faithfulThawColumnBug` true, limit 8 | yes, including the bug |
| deposition | `FUN_0044c8f0` when an AI nation is in debt or below 400 unity and `Random(9) == 0`; clears its cooldowns −5…−1 to peace | `AiDepositionHandler`, `InDebt`, 1 in 9 | yes |
| post-battle treaty | `FUN_00450c68`: peace, or the loser sues (ends its trades and alliances at −10 and pays); then each ally of one side that is at war with the other ends that alliance (−8), and, if not a neighbour and not human, that war too (−8) | the same effects (Illyria, below) | yes |

**Code-level differences found by reading (none of them observed in play):**
- **D3:** in loop 1, the nation that becomes the new best war candidate is skipped for a trade (`goto LAB_0044fd11`). The
  remake offers trades to every eligible nation. This only matters when a 3-trade cap binds.
- **Edge case:** if no nation stands at peace, trade or alliance with the seat, loop 1 never sets the "busy" flag, and the
  alliance test then reads it uninitialised.

## 2. Measured: AI diplomacy decisions from the same states

- **Hook:** `patches/diplo_hook.py` logs every relation write with its caller, plus E84C's war candidate and its rolls.
- **Starts:** 7 states from the long runs, 3 rounds each:
  - the four war-declaration turns: Carthage game before turns 34 and 36, Gaul game before turn 36, Seleucid game before
    turn 18;
  - mid-game: Rome, Carthage and Gaul games before turn 21.
- **Remake:** `11f713e2` replays each round from the original's own autosave.
- **Comparer:** `runs/experiments/diplo/compare.py`, now with the quarterly bookkeeping writes set apart.
- **Data:** `run-exp-diplo-longrun`. The hooked autosaves are byte-identical to the plain build in 21 of 21 rounds.

| Seat turns | v1 | v2 (thaw and deposition writes apart) |
|---|---|---|
| same | 322 | **326** |
| draw (only a war or alliance roll differs) | 1 | 3 |
| after a divergence | 3 | 1 |
| **deterministic** | 4 | **0** |

The four v1 "deterministic" seats were all Illyria's seat, the one that runs the week tick. In each, the AI's own actions
were identical, and only the original's quarterly writes differed: the thaw (setter called at 0x451FB5) and two
depositions (0x44C9FF: Galatia in `carthage-t33end` round 3, Armenia in `carthage-t35end` round 1). The remake doesn't log
those writes as AI actions. Both are rolls in both games: thaw 1 in 3, deposition 1 in 9.

## 3. The long-run differences, explained

**Relations** (anchored replays on `11f713e2`, 145 turns):
- 53 turns differ in at least one relation status, mostly trades.
- 157 cooldown pairs differ by exactly ±2 (80 / 76 / 1 × +4), all on season-start turns. That's the thaw's 1-in-3 +3
  landing in one game and not the other.

**The four remake-only war declarations:**

| Game, turn | Remake event | Chain |
|---|---|---|
| Carthage, 34 | Macedonia declares war on Illyria | In the remake's round, Illyria destroys Rome's army; the treaty's ally loop (Gaul was at war with Rome) ends Illyria–Gaul (−8); Illyria is no longer protected, becomes Macedonia's candidate (ratio 32), and the roll hits. In the original no battle took place, so Illyria stays protected and Macedonia has no candidate (hook: −1). |
| Gaul, 36 | Macedonia declares war on Illyria | Rome destroys Illyria's army; Illyria sues for peace and ends all its alliances; unprotected; the roll hits. |
| Carthage, 36 | Ptolemaic at war with Numidia and Carthage | Ptolemaic's alliance roll hits (ally Celtiberia); the alliance pulls Ptolemaic into Celtiberia's wars. Numidia is not a neighbour of Ptolemaic in either game. The original's hooked run from the same state also allies with Celtiberia, in another round. |
| Seleucid, 18 | Media at war with Seleucid | Media's alliance roll hits (ally Ptolemaic, at war with Seleucid). |

Every step follows the original's rules. The differences enter through rolls (war 1 in 10, alliance 1 in 20) and through
battles that happen in one game's round only. Which battles happen depends on army moves and outcomes, and the army side
is covered by the long-run AI-gap findings (one gap left: the garrison fallback's walk). Remake-only wars like these
therefore don't call for a diplomacy fix.

## Open

- D3 and the uninitialised busy flag (code only).
- Whether the roll distributions match (they're equal by construction; not measured).
- Why individual battles happen in one game only (army-side, not attributed here).
