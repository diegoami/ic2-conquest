# City-versus-army decision: city eligibility changes the retained branch

**Tag:** [confirmed, partial: same retained private original/native boundary,
input/projection gates, candidate arithmetic and public score-fed controls].
**Tasks:** [conquest #187](https://github.com/diegoami/ic2-conquest/issues/187),
[Main T212/#1394](https://github.com/diegoami/imperial_conquest_2/issues/1394).
**Follow-ups:** [#1417 city policy](https://github.com/diegoami/imperial_conquest_2/issues/1417),
[#1418 exact-100 boundary](https://github.com/diegoami/imperial_conquest_2/issues/1418).
Promoted by [Research PR75](https://github.com/diegoami/imperial-conquest-2-research/pull/75)
at `2c2a18370c4d9c6be49692fdc7f830fee6912323`.
Use the [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/2c2a18370c4d9c6be49692fdc7f830fee6912323/docs/reports/2026-10-24-city-army-selection187.md)
and [safe receipt](https://github.com/diegoami/imperial-conquest-2-research/blob/2c2a18370c4d9c6be49692fdc7f830fee6912323/docs/data/city198-intake-v1.json).
Research freshly reproduces the original/scorer/projection/component evidence,
complete retained native v3 scalar, and all 32 original/native grid rows without
normalization. It confirms the signed JLE boundaries and corrects its older
strategic report/rules. No fresh game, native rebuild, production patch,
scope/label change, full-turn or Windows acceptance is claimed.

## Answer to Main's bounded question

The reported AttackCity choice comes from **city eligibility**, not incorrect
imported city inputs or the final branch predicate on this state. The original
keeps a stronger distant city as its best city target. The native city's
existing direct-walk filter rejects that city, leaving a nearby alternative.
That nearby alternative changes the city-versus-army decision.

The filter is explicitly documented as a **designed** policy (#925/#907), so
this is an attributed original-policy difference, not an undisclosed importer
bug. Current T212 changes only the enemy-army selector/routing slice. Main needs
an explicit faithful-city scope decision or a narrower acceptance claim; the
same enemy target/waypoint alone does not establish full military branch parity.

## Same-state evidence

Pin: [T212 draft PR1415](https://github.com/diegoami/imperial_conquest_2/pull/1415),
head `0c4944542d32d1e6d2d9982f78fdfcddaabaddea`. Only an archived copy is built
inside conquest; no other checkout is written. Original EXE SHA256 starts
`9d753d5d`, listing starts `2018c205`. The retained private pre-command state is
reused without a game, new owner save or Windows access.

| Result | Original | Native production at the pin |
|---|---|---|
| Best city: index / score / distance | 287 / 495 / 28 | 253 / 330 / 6 |
| Best enemy army: index / score / distance | 24 / 828 / 28 | 24 / 828 / 28 |
| Final tree branch | AttackArmy | AttackCity |
| Native military proposal for actor | — | City approach, not an executed attack |

Original ECE4, EE60 and E670 run unchanged. Both a branch supplied with those
scores and the complete original scorer-to-F31C sequence choose the army and
match the recorded enemy destination. Complete captured game RAM stays unchanged
and no original RNG call occurs. These executions stop before movement/contact.

The original city is too distant to trigger the nearby-city preference. The
native alternative is within this turn's budget, while the enemy army is beyond
twice that budget, so the native branch chooses the city. Supplying **only the
original city result** to production DecideFromScores restores AttackArmy; the
native enemy result is already equal.

## Import and input attribution

Exact original RAM-to-diagnostic-container byte identity passes for map, cities,
armies, fleets, nations (including queues/relations) and mercenaries. Turn order,
active seat/calendar and decoded JSON also match. The reused news/UI metadata
is excluded from the scorers. This is a diagnostic projection, not Save As or
Windows round-trip acceptance.

The native importer then passes **2,908 field checks** covering units/order/
quality/labels, actor and other army resources/morale, city ownership/allegiance/
fortification/population/loyalty/supply, nation capitals/control/queues/relations
and fleets. All **44,800** terrain/occupancy cells pass the relevant land-code/
passability/marker checks. Do not interpret those counters as every memory field.

Original and native assault strength agree. Raw and attacker-allegiance-adjusted
city defense agree for all **40 hostile-city candidates**. Import projection,
fortification decoding, changed relations or strength arithmetic therefore do
not explain the winner difference on this state.

## Eligibility versus scoring

The original winner is accepted by CAB4 and rejected by native IsReachable.
Thirty-six original-eligible city candidates are rejected by the native filter.
The selected nearby native city is among the remaining candidates.

A source-shaped diagnostic of the native formula uses production assault/city-
defense helpers and first reproduces its production winner/score. Changing only
that diagnostic's eligibility to the original CAB4 eligibility restores the
original city **287 / 495 / 28** and AttackArmy. This is a labelled counterfactual
model, not a patched production run or an accepted corrected command.

There is a secondary scoring difference: shipped `cityRegionById` is empty,
explicitly designed, so its halving never fires. Actual original candidate
arithmetic is observed at `0044EE16`. Five candidate scores differ under the
empty native geography; substituting the original region-and-coordinate-side
comparison in the diagnostic reproduces **all 40** observed candidate scores.
This does not change the winner after eligibility alignment in this retained
state. No new city name, coordinate list or owner state is published.

Main #1417 holds the policy/scope follow-up: evaluate original-policy CAB4 city
eligibility plus EB9C geography separately from the designed/Improved filter.
Do not remove the Improved policy, alter the walker, or silently widen T212.
Research has promoted this bounded evidence; Main still owns an explicit
policy/scope decision and production acceptance.

## Independent exact-100 branch discrepancy

Although branch predicates do not cause the retained-state discrepancy, source
inspection found a separate boundary error. The original includes exactly 100
in two weak-target branches; the native implementation uses strict `< 100` with
shipped threshold 100. Thirty-two **public synthetic score-fed** original/native
branch controls produce seven differences, all at exactly 100.

Examples use moves 7, supplies 0, morale 80 and enemy distance 28:

| Army score | City score / distance | Original | Native |
|---|---|---|---|
| 99 | 100 / 6 | MoveToResupplyCity | AttackCity |
| 100 | 99 / 28 | MoveToResupplyCity | AttackArmy |
| 100 | 100 / 6 | MoveToResupplyCity | AttackArmy |

At `0044F3B8`, the army-score compare is followed by **JLE** at F3BE. At
`0044F413`, the city-score compare is followed by **JLE** at F419. The separate
better-buy predicate at F3D6 still requires city score **> 100**. Raising one
shared city threshold to 101 would change that other predicate too; preserve
the distinct inclusivity rather than fixing one by breaking another.

These are conditioned branch inputs, not proof that every tuple naturally
occurs in a campaign. They execute original branch instructions with unchanged
game RAM and zero RNG, stopping before destination execution. Native production
DecideFromScores consumes the same public actor/score inputs. The private state
uses scores 828 and 495/330, so this boundary error is independent of that case.
Main #1418 tracks the original-policy correction and provenance/test update.

## Evidence, validation and limits

Public ledgers live under `runs/experiments/data/run-exp-city-army187/`:
`original-scalar-v1.json`, `native-scalar-v3.json`, `projection-gate-v1.json`,
`component-gate-v1.json`, `branch-grid-original-v2.json`,
`branch-grid-native-v2.json`, `source-ledger-v1.json` and `summary-v1.json`.
Runners are in `runs/experiments/city-army187/`.

Private evidence: the retained pre-command diagnostic `before.SAV`, decoded
state and RAM; per-city component observations; scorer/branch/proposal traces.
All owner paths, private hashes and full states/traces remain private. The
public synthetic grid uses a separate generated `generated-before.SAV`.
Neither container is an original Save As. No raw owner archive is published.

The initial synthetic grid container had an inconsistent seat/turn-order trailer;
native import correctly refused it. That log/container and the original v1 grid
remain. Fresh v2 corrects only the diagnostic trailer; all 32 original branch
rows reproduce exactly. No measurement was overwritten. Native scalar v1/v2
also remain beside v3's stronger terrain/projection/component gates.

The public audit, Python compilation, native builds and diff check pass; no
external reviewer is claimed. This is one retained state plus bounded branch
controls, not full-turn parity, multi-campaign fidelity, accepted corrected AI
orders or native Windows acceptance. Main owns implementation and acceptance;
the current owner request is answered without asking for another save/screen.
