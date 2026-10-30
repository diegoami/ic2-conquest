# AI army decisions, original vs remake main: the decision tree matches; two port gaps and the #925 tiers decide the rest

**Tag:** [confirmed] for the comparison (749 decisions, each from the original's own hook on the same state the remake
imports) and for the three differences checked with a one-line patch; [code] for the off-by-ones and tie-breaks in §4.
**Owner request:** 2026-10-30, "a round of comparing the AI decisions with the remake code", option 1 (run both, then read
the code where they disagree), with remake **main** as the reference: `10d3bb81` (T248, #1637), not released.

## Method

- **Original:** a new observation-only hook, `patches/decide_hook.py`, logs every input of the army phase `FUN_0044f31c`'s
  branch for each army it decides. It reads F31C's frame after `FUN_0044ee60` returns (0x44F3B8): the home city, the city
  and army targets, their scores and distances, and the army's position, moves, supplies and morale. It also reads
  `FUN_0044a698`'s value at the resupply test (0x44F450).
  - The branch is computed from these inputs with F31C's own predicates (`decide_hook.branch`).
  - Runs: 16 New Game starts × 5 End turns, seed 12345, the human seat giving no orders. The hooked autosaves are
    byte-identical to the plain build's in **80 of 80** turns.
- **Remake:** each AI round is played from the **original's own autosave just before it**, so both games start every
  round from the same state. The remake's own `AiArmyTargetTree.DecisionRecord` log and AI lines are read through
  `RemakeAdapter aiprobe ... decisions= relations= ailog=`.
- **Pairing:** armies are matched by id; after a death, where the original swap-removes the table (#117), they are
  matched by nation and position. An army whose position at its decision already differs counts as state. So does a
  decision made after an attack earlier in the round, or after armies died (battle results are random draws).

## Result: 749 decisions

| Cause | Rows | What it is |
|---|---|---|
| **same** | **390** | Branch, city and army targets and scores equal. Includes 12 armies the remake did not log: a mercenary run without an offer or continuation, then the garrison move in both games. |
| **#925 resupply tier** | 252 | The resupply destination differs (§3) |
| diplomacy | 44 | The nation's wars changed during the round, or differ between the games at its end (§5) |
| **city > 85 target** | 21 | §1 |
| **capital defence attack** | 17 | §2 |
| state | 17 | An attack or a death earlier in the round. 16 were classified automatically; S07 round 3 Seleucid army 4 by hand (its target, Galatian army 10, dies in the original's round before Seleucid plays). |
| #925 fallback | 8 | The chosen branch gave no usable command, and the remake's garrison/emergency tier moved the army (§3) |

**Wherever the inputs are the same, the remake's decision tree takes the original's branch.** Its predicates match F31C
line by line: the army > 100 test with the supplies/morale/distance clause and the better-city override, city > 100,
`troops / 500 < supplies`, and the continuation thresholds 71 / 85. So do both scorers (`FUN_0044ece4`, `FUN_0044ee60`,
including T248's geography halving), the home-city choice `FUN_0044e670` (§3), and the capital-defence threat list
and responder tests (#123). Every difference that is left comes from the three items below, from diplomacy, or from
random battle results.

## 1. After the mercenary run, "city > 85" marches at the city target, not the resupply city

F31C, after `call FUN_0044e84c` (0x44F485):
- army score > 70 → walk to the **army target** (0x44F4A3);
- otherwise city score > 85 → 0x44F4B2 `movsx eax, word [esp+2]`, the city table position, `call FUN_0044dba8`
  (0x44F4C7).

`[esp+2]` is the **city target**: F31C passes `edx = &[esp+2]` to `FUN_0044ece4` (0x44F399). The home or resupply city is
`[esp]`, which `FUN_0044e670` writes, and only the resupply branch (0x44F47C) walks there.

The remake's `Continuation.DefendResupplyCity` marches at `decision.Resupply.City` (`AiMilitaryPhase.cs`). Research's
`2026-10-07-strategic-ai-turn.md` §3.3 calls it "defend the resupply city" too.

- **In play:** Carthage army 2 in S03, S04, S05, S09, S10, S11 and S12, rounds 3–5 (21 rows). Its home is Carthago Novo (45,68) and its city target
  Castulo (36,61). The original walks (39,64) → (37,62), toward Castulo and away from home. The remake sends it to the
  resupply city, or, when that is unusable, to the garrison and emergency moves.
- **Patch check** (`diagnostics/f4c7.patch.txt`: `decision.TargetCity` in place of `decision.Resupply?.City`): all 7
  rows where the army is not yet next to the city now aim at the original's city target. In S03 round 3 the march is
  (39,64) → (37,62), as in the original. The other 14 rows have the army already next to the city: §3's fallback
  interplay.

## 2. The capital defence's walk attacks the threat on arrival

In S01 (Rome) and S05 (Seleucid), round 1, the original dispatches one responder, and the second army gets its normal F31C
decision. The remake dispatches both:

| | Original | Remake main |
|---|---|---|
| S01 Rome | army 0 walks at the Gallic army 9 and fights it: 23,700 → 18,564 troops, army 9 destroyed (14 → 13 armies). Army 1 then decides normally: city > 100, Vindobona (119,8). | `capital defence: army-0 … army-1 toward (96, 30), threat army-9`. Army-0 attacks later, from its target tree. |
| S05 Seleucid | army 4 fights Ptolemaic army 6 (46,200 → 37,280 troops, army 6 destroyed). Army 5 decides normally: army > 100. | army-4 and army-5 both dispatched toward (226,72) |

- The capital-defence hook shows why (`capdef/`, S01 and S05, byte-identical to the plain build). Responder 0 compares and
  accepts the threat. Responder 1 never compares it, because by its turn the threat fails `FUN_0044efc8`'s alive test
  (owner ≤ −1, 0x44F207).
- The responder's walk `FUN_0044dba8(responder, threat position)` (0x44F2F9) ends in the threat's cell, and the battle
  happens inside the capital defence: army 0 has no moves left and gets no F31C decision that round.
- **Patch check** (`diagnostics/capdef-attack.patch.txt`: after the move, a responder next to its chosen threat attacks
  it):
  - S01: `army-0 attacks army-9`, then `approach target city (119, 8) with army-1`;
  - S05: `army-4 attacks army-6`, then army-5 approaches its army target.

  Both are the original's decisions.
- 17 rows in 16 starts × 5 rounds: Rome's army 1 in 14 and Seleucid army 5 in 3.

*Scope:* the patch is a check, not the original's mechanism. Whether `FUN_0044dba8` attacks on arrival everywhere (the army
target branch 0x44F409 too), and how, belongs to the march contract (research #97), not this comparison.

## 3. The #925 reachable tiers replace the original's destinations

The remake adds three designed tiers on top of the original's choices, under `classical-faithful` too. They come from the
owner's decision of 2026-10-10 on remake #925 (the "Hazards"):
- the reachable resupply city (`ResolveResupplyCity` keeps `FUN_0044e670`'s pick only if `IsUsableDestination`);
- the reachable garrison fallback (`GarrisonFallback`: the first reachable city instead of the nearest);
- the emergency move.

The original marches at its pick with `FUN_0044dba8`, and when a walk moves nothing, `FUN_0044ebe8` picks the nearest city
of any owner. An army next to that city stays put.

- **252 resupply rows.**
  - **238** have the army standing next to its home city (distance 1). The remake's walker cannot step into the city, so
    the tier rejects it and sends the army to another city. The original walks at it: BASE turn 1 Macedonia army 8 swings
    out to (147,44) and back (the no-progress fallback, #105) and ends at (144,42), next to Pella.
  - The other **14**: with the tier skipped (`diagnostics/raw-resupply.patch.txt`, all 80 rounds), the remake's own
    `ScoreResupplyCity` aims at **exactly the original's home city in 14 of 14**.
- **8 fallback rows:** a branch whose march is unusable in the remake ends in the garrison or emergency tier.
- **The 14 adjacent rows of §1:** the original's `FUN_0044ebe8` chooses the city the army is next to and nothing moves.
  The remake's tiers move it.

Whether `classical-faithful` should keep these tiers is the owner's design decision (#925), not a porting question.

## 4. Code differences not seen in these runs [code]

| Where | Original | Remake main |
|---|---|---|
| `FUN_0044ebe8`, an own army near the capital | distance **< 10** (0x44EC3F `cmp ax,0xa; jge`) | `<= GarrisonFallbackCapitalDistance` (10) |
| `FUN_0044e84c`, mercenary offer range | distance **< 20** (0x44E884 `cmp ax,0x14; jge`) | `distance > MercenaryRunOfferRange` (20) skips, so ≤ 20 |
| Ties in `FUN_0044e670`, `FUN_0044e84c`, `FUN_0044ebe8` | strict `<`: the first in table order wins | equal scores or distances break by **city id** (`CompareOrdinal`) |

Everything else in these three functions matches, including the +20 foreign / −20 capital terms and the always-replaced
foreign pick of `FUN_0044e670` (a foreign best is over 15 by construction).

## 5. Diplomacy: a separate comparison

In 29 nation-rounds the wars change within the round, at different times in the two games:
- the original ended a war in 16 (the remake did too in 5);
- the remake ended one in 10;
- the original declared one in 4, the remake in 7.

Example: S00 round 3, Carthage–Rome war in the remake only. Once a nation's wars differ, its armies' targets differ. That
is a diplomacy question (peace and war decisions, with their draws), not the army decision tree, and is not attributed
here.

## Recheck on remake main `05b02936` (T249, #1643)

The same 749 original decisions were compared with remake main `05b02936`, which ports §1 and §2:
- `remake-05b02936-v1/`, `report-05b02936-v1.json`, `attribution-05b02936-v1.json` (the original side unchanged, `orig-v1/`).

| Cause | `10d3bb81` | `05b02936` |
|---|---|---|
| same | 390 | **422** |
| capital defence attack (§2) | 17 | **0** |
| city > 85 target (§1) | 21 | **14**, all with the army already next to the city target, then the #925 garrison or emergency tier (§3) |
| #925 resupply / fallback | 252 / 8 | 250 / 8 |
| diplomacy / state | 44 / 17 | 41 / 14 |
| unattributed | 1 | 0 |

So **outside the #925 tiers, diplomacy and battle draws, every decision now matches the original.** §4 (the `<=` boundaries
and city-id ties, research #144) is not in this commit.

## What this does not establish

- **Later turns of a campaign:** every round here starts from the original's state, so the remake's own drift is not
  measured. The #232 campaigns remain the place for that.
- **Rounds beyond 5 and other seeds,** and armies aboard fleets (none decided aboard in these runs).
- **The adjacent rows' raw pick:** for the 238 adjacent rows the raw `ScoreResupplyCity` pick is not visible, since the
  march at distance 1 moves nothing either way. The 14 far rows and BASE's hand-checked cases match.
- **`FUN_0044dba8`'s attack on arrival** beyond the capital defence (§2 scope note).
- **§4**, which no row exercised.
- **Diplomacy (§5).**

## Corrects

`2026-10-30-carthage-army3-branch138.md`: army 3's resupply test values are 24600 / 500 = 49 against 246 supplies, read
after `FUN_0044e41c`. The first version read 18600 / 90 from the save. The branch is unchanged; the correction is in that
finding.

## Evidence

- Data: `runs/experiments/data/run-exp-aidecide/` (README):
  - `orig-v1/` (hook logs, inert checks)
  - `remake-10d3bb81-v3/` (remake logs)
  - `report-v2.json`, `attribution-v1.json`
  - `capdef/`, `walk-S01/`, `diagnostics/`
- Release `run-exp-aidecide` (`aidecide-saves.tar.xz`, 176 saves; hashes in `SAVES.sha256`).
- Saves cited:
  - starts `S00_Rome_AUTO0720.SAV` … `S15_thracia_AUTO0720.SAV`;
  - S01 round 1: `hooked-t01-AUTO0721.SAV` (army 9 gone, army 0 at 18,564 troops);
  - S03 rounds 3–5: `hooked-t02…t05` (Carthage army 2 at (39,64), then (37,62)).
- Code:
  - `patches/decide_hook.py`, `difftest/probes/decide_hook_run.py`;
  - `runs/experiments/aidecide/{compare,attribute}.py`;
  - `difftest/remake_adapter/AiProbe.cs` (`decisions=`, `relations=`, `ailog=`).
- Remake pin: `python3 -m difftest.pin build main` → `10d3bb81`.
