# Strategic fidelity pilot: target eligibility and resupply choices differ

**Tag:** [confirmed, partial: eleven generated strategic inputs, original Wine,
matched decision-state original instructions and pinned production-native code].
**Status:** draft for Research intake. [Conquest #171](https://github.com/diegoami/ic2-conquest/issues/171)
tracks broader coverage; no production correction or complete strategic parity.
Remake pin: `55d96876a98ba3bb7142ca7c1ecc0d1b61095c18`.

## Answer

The games make different strategic choices even when the local decision inputs
match. In this pilot the principal measured differences are **which targets the
remake excludes before scoring**, and **how it chooses resupply cities**.

Eleven byte-distinct inputs cover six human starts (Rome, Carthage, Seleucid,
Ptolemaic, Numidia, Gaul), war/peace, Carthage–Numidia war, two supply situations
and a threatened Seleucid capital. Each original run advances **0720 → 0721**.
They yield **112 captured original army target-tree states**, involving eleven
AI nations. The corresponding native import/projection gates pass **290,524
checks** over units, armies, cities, fleets, nations, relations and recruits.

| Local comparison on those original states | Agreement |
|---|---:|
| Target-tree branch kind, using each engine's own scorers | 58/112 |
| Enemy-city target, including no-target outcomes | 61/112 |
| Enemy-army target, including no-target outcomes | 57/112 |
| Raw resupply-city selector | 14/112 |
| Branch plus primary destination, where fully compared | 9/109 |
| Native branch kind **fed the actual original scores** | **112/112** |

Three mercenary-run continuations are excluded from the primary-destination
denominator. This compares the local tree and its primary destination, not the
entire native greedy proposal/command-selection loop. These sampled original
states are not independent campaigns or an estimate of general failure rates.

## Target eligibility: the #1388 family extends beyond its owner battle

Every differing selected combat target is rejected by the production remake's
direct-walk eligibility test:

- **51/51** differing enemy-city selections exclude the original's winning city.
- **55/55** differing enemy-army selections exclude the original's winning army.

Those are separate, potentially overlapping selector observations, not 106
independent bugs. The original scorer is executed unchanged from measured RAM;
its selected target passed its original eligibility path. Production
`AiArmyTargetTree.IsReachable` is then evaluated on the imported same state for
that exact target. Its rejection is recorded explicitly, not inferred from a
later endpoint or aggregate casualty count.

Giving production `DecideFromScores` the original scored targets, scores and
distances restores **all 112 observed branch kinds**. Thus the branch differences
in this sample are explained upstream by selection/scoring inputs. This does
not prove all branch thresholds or mercenary continuations faithful. No missing
target is repaired by substituting a draw, changing troop power or declaring
every target reachable.

[#1388](https://github.com/diegoami/imperial_conquest_2/issues/1388)'s previous
private control already isolates the original region/coast/fleet eligibility
and intermediate-routing wrapper. It remains a prior reference, not a new
owner run here. A faithful correction still needs eligibility **and** routing;
the existing target-only negative control remains valid.

## New isolated resupply result, and a correction to earlier research prose

Original `FUN_0044E670` uses **`floor(troops/1000)`**, and an own city is an
eligible supply candidate when its stock is **greater** than that quantity.
This quotient is a city-choice threshold; automatic transfer quantities have
separate rules.
It minimizes adjusted distance: **subtract 20 for a capital**, favoring it.
Production `ScoreResupplyCity` uses **`troops/100`**, keeps own cities whose
stock is **below** that quantity, and subtracts a capital penalty from the
negative-distance score it maximizes, disfavoring capitals.

These are verified with actual original instructions, not solely a decompiler
reading. The original x86 at `0x44E6B8` loads divisor `0x3E8`; `0x44E6E8..EC`
accepts own stock above the quotient; `0x44E784` subtracts 20 before the minimum
comparison. The tracked disassembly preserves the measured instruction listing.

Six controlled variants start from the captured Macedonian decision: army
29,800 troops at `(145,40)`, Pella city144 at `(143,41)`, Thessalonica city152
at `(146,42)`. Both cities are distance2. Only own-city supply stocks and, in
one variant, the Macedonian capital pointer change. Other own stocks are zero.
There is no new game run, relocation or combat-stat adjustment in these controls.

| Same-input control | Original selector | Native raw selector |
|---|---|---|
| Both stocks30, capital Pella | Pella144 | Thessalonica152 |
| Both stocks30, capital Thessalonica | Thessalonica152 | Pella144 |
| Pella0, Thessalonica29 | Pella144, nearest-own fallback | Thessalonica152 |
| Pella0, Thessalonica30 | Thessalonica152 | Thessalonica152 |
| Pella0, Thessalonica297 | Thessalonica152 | Thessalonica152 |
| Pella0, Thessalonica298 | Thessalonica152 | City159 |

All six pass the full native input gate. Original instructions call no Random
routine and preserve game RAM in these selectors. The swapped-capital pair
isolates preference direction; the 29/30 and 297/298 boundaries isolate the
stock/divisor differences and include positive agreement controls.

**Research correction requested:**
`docs/reports/2026-10-07-strategic-ai-turn.md` §3.3 currently describes the own-city
rule as stock below `troops/100`. That statement is contradicted by this bounded
x86/control evidence and should be corrected during intake. Describe the original
capital term as a lower-is-better distance adjustment, rather than suggesting
the native penalty is the same rule. The original's foreign +20 is likewise a
distance cost; its conversion into a maximized score needs sign care. Foreign
preference was not independently isolated by these six controls.

Production `ResolveResupplyCity` also adds a separately documented reachable-city
policy. Raw selection and resolved destination are reported separately; an
intentional policy difference is not automatically a newly proven defect.

## Scenarios and control quality

`case-manifest-v1/v2/v3.json` retain the complete declaration history. The first
Rome–Gaul war edit was a no-op because the Numidian start already had that war.
Its native result is retained as an exact duplicate-input control; it is not
counted as another distinct scenario. Manifestv2 adds a peace counterfactual.

The first shortage input is naturally replenished before target choice:
Ptolemaic 0 money/0 supply becomes **500 money/564 supply** at the captured
decision. A separately declared isolation case moves that generated army to
`(187,104)`, six cells from every city. It reaches the decision with **0/0**,
the same 56,400 troops, morale64 and eight moves. Thus the pilot includes both
automatic replenishment and a genuinely depleted decision input. Neither is
an owner #1355/#1388 input.

The capital-threat case has an observed Seleucid homeland-intercept call
(`0x44F2F9`, original army4, destination `(227,67)`), in addition to ordinary
army-tree observations. Full matched homeland-dispatch decisions are not yet
implemented by this comparator.

Validation:

- Original observer covers 22 guarded call sites and passes **792** CPU
  register/flags/stack/game-RAM and capacity controls before live use.
- Two same-seed observer/plain pairs (Roman start and capital threat) have
  **byte-identical complete before and after SAVs**. These repeats are controls,
  not independent strategic scenarios.
- All 11 observed original cases complete one End turn; two plain controls
  make 13 original runs. No human tactical battle order was issued.
- Native normal End-turn observations cover the 11 distinct inputs plus the
  retained duplicate. Disabling native observations leaves the Roman final
  native state identical. No native case remains in a tactical battle.
- **102** replayed first destination calls match actual observed original
  calls. Mercenary-first/continuation limitations remain explicit.
- Corrupted expected troop and relation inputs both fail the gate before
  emitting any comparable rows. Original and native helpers are not modified
  to make expected results pass.
- **349** archived Engine/Data/data Git blobs match the remake pin. Builds and
  diagnostics run inside this checkout; no other repository was written.

## Evidence and how far to extend the conclusion

Runners: `runs/experiments/strategic-fidelity/`.
Tracked evidence: `runs/experiments/data/run-exp-strategic-fidelity/`:
`summary-v2.json`, `decision-ledger-v2.jsonl`, `case-summary-v2.csv`, per-case
original/native/eligibility/from-scores rows, source pin, instruction listing,
control outputs, immutable manifests and hashes. `summary-v1` retains the first
ten-case result; it is not the final expanded denominator.

Original save references are `SF-<case>-hook-v1-before.SAV` and
`SF-<case>-hook-v1-after.SAV`, turn0720→0721; the two controls use `plain-v1`.
For example `SF-N-rome-hook-v1-after.SAV` and
`SF-L-ptolemaic-isolated-hook-v1-after.SAV`. A decision row names its original
snapshot ordinal. RAM-to-SAV projections are synthetic diagnostic containers,
**not original Save As files**; news/UI metadata are retained and excluded from
the relevant decision-input gate.

Generated evidence is on [Drive](https://drive.google.com/drive/folders/1gNiyzqi7RbgV0U4AJ5xwiYeDzK58H8-i),
with archive/member hashes tracked. Batch01 has the first ten cases and the
initial compiled tool. Batch02 adds isolated scarcity and `tools-v7`, including
the original-score counterfactual mode. Batch03 adds two required native terrain
sidecars omitted from batch01's JSON-only allowlist. The initial failed recovery
and both older bundles are preserved. Recovering all three bundles into a new
tree verifies **499 member hashes** and reproduces eleven retained compiled-tool
rows byte-for-byte. Each archive is retained independently.
No original EXE/DAT, Wine prefix/runtime, credentials or owner1355/1388 material
is in the bundles. Generated RAM captures stay off Git. Local hashes and remote
size/parent metadata are verified; no remote-download digest check is claimed.

Ordinary whole-turn outcomes differ, but the engines' random streams and action
histories are not aligned. Recruitment, diplomacy, economy, fleet orders and
contact outcomes have observation coverage; complete same-input decision/RNG
comparisons for those families are still missing. Native decision logs contain
proposals; accepted command timelines are kept separately. Do not call every
proposal an executed action or every final-state difference a rule defect.

The useful next work is to correct/reconcile the validated selector rules and
navigation boundary, then instrument the remaining strategic families and add
boundary/terrain controls, all16starts and short continuations. These samples
do not establish every feature, multi-seed campaign equivalence, an optimal AI,
production acceptance or native Windows compatibility. Native Computer Use
remains stopped; the paused battle queue and optional Improved general remain
separate.
