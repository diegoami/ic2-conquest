# Strategic AI: region boundaries, embarked-army resupply and fleet purse/repair rules

**Status:** draft for research intake, addressing research issues #22, #23 and
#26. Implemented in the owner's current Codex session; MiniMax review pending.
No remake implementation is included.

**Tags:** `[code]` pinned original decompile/disassembly; `[x86]` original
instructions executed under Unicorn; `[Wine, staged]` original game with named
save-field edits, not natural play or native Windows confirmation.

**Evidence:** `runs/experiments/data/run-exp-ai-oct16/`; binaries in
[release run-exp-ai-oct16](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-ai-oct16),
hashes in `SAVES.sha256`. `observations-20261016-152721.md` and its JSON give
every authoritative input/output filename and field delta. `summarize.py`
checks the hashes and post-save fields against the logs. Superseded exploratory
runs remain beside the controlled runs and are excluded from those selections.
All strategic cases below are turn **0734**, within one AI seat, without a
weekly tick: Armenia human -> Rome AI -> Bithynia human.

Source: `all_app_functions.txt`, SHA-256
`2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`.
`targeted-code-extract.txt` retains the relevant functions with original source
line numbers; `targeted-source-callers.json` records their callers. Environment,
EXE/DAT/input hashes and staging edits are tracked. The ordinary seeded EXE is
`354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`.

## Region membership and scoring (#22)

`[code]` `FUN_0044eb18` (52538) classifies packed `(x,y)` as two values, a region
index and a separate coast flag. The eight boxes read from live Wine memory at
`0x4794e8` are:

| Index | x bounds, both excluded | y bounds, both excluded |
|---|---|---|
| 0 | 58, 64 | 53, 61 |
| 1 | 86, 91 | 40, 48 |
| 2 | 82, 90 | 49, 63 |
| 3 | 99, 114 | 62, 74 |
| 4 | 149, 156 | 54, 60 |
| 5 | 150, 164 | 75, 81 |
| 6 | 163, 167 | 66, 71 |
| 7 | 190, 207 | 68, 79 |

The default index is -1. All eight tests run in index order; the last match
wins. These actual boxes have no interior overlap. The coast flag starts at 1
and becomes 0 if **any** pair `(cx,cy)` satisfies `x < cx AND y < cy`:
`(44,78), (158,75), (180,36), (171,41), (163,45), (161,47)` at `0x479528`.
Equality at either coast threshold fails that pair's test.

`[code]` "same region" in `FUN_0044eb9c` requires **both** the index and coast
flag to match, including when both indices are -1. `FUN_0044ca30`, used by army
reachability `FUN_0044cab4`, is byte-identical to `FUN_0044eb18` over its entire
132-byte extent. Movement's `FUN_0044da88` uses the same tables, tests and order,
then maps the resulting pair to its movement-region kind. Cities and unit
coordinates are passed to these classifiers; there is no separately authored
city-region map. The pinned callers of the scoring comparison are enemy-city
scoring, enemy-army scoring and homeland threat filtering. Fleet hunting
`FUN_0044f4f8` does not contain that regional score penalty; do not extend the
army/city score rule to fleets by analogy.

`[Wine]` The tables and all 334 city coordinates/names came from unchanged
`fleet-port-antium-0734.SAV`, turn 0734, in
`probe-20261016-144552-500897.jsonl`. `[x86]` `region_audit.py` executed the
original classifier on **482** distinct city/boundary/coast/fallback coordinates,
all matching the transcribed algorithm. The complete reproducible mapping is
`city-regions-20261016-145216.csv`; `region-audit-20261016-145216.json` records
the cases and hashes. The earlier CSV from a failed summary write is retained
but is not the authoritative mapping.

`[code][x86]` Enemy-city and enemy-army scorers subtract distance first, then
apply the cross-region operation **`s := s - trunc(s/2)`**, not a truncating
`s/2`. Thus 107 becomes 54 and -3 becomes -2. The original signed instruction
slices at `0x44edd1` and `0x44ef4d` agree in 20 signed test cases, including odd
negative values (`code-truth-tables-20261016-150205.json`). The city scorer then
applies its weak/near-city and capital doubling, in that order. The army scorer
caps at 1000, then adds 1000 for a weaker enemy within 7. Both choose by strict
`>` (first equal candidate retained), store the winning score as a word, and
add the winning distance back to the returned score. Initial strength division
and later modifiers are not interchangeable with the region operation.

`[Wine, staged]` Equal 30,000-foot armies with morale 90 were placed on a declared
synthetic plain corridor. Outstanding Roman queue troops and mercenary offers
were cleared; only one AI seat ran. The scorer observer preserves the original
call ABI and its registers/flags, checked against direct calls in 160 emulator
comparisons. All **seven** plain/observed post-save pairs are byte-identical.

| Controlled case | Original army-scorer result | Saved evidence |
|---|---|---|
| one target, same region, distance 3 | 110 | `reg_same_only_observed-20261016-151025-546199-post.SAV` |
| same-strength target across region boundary, distance 3 | 57 = 54 + 3 | `reg_cross_only_observed-20261016-151025-546199-post.SAV` |
| both index -1, matching coast flags, distance 3 | 110 | `reg_fallback_same_observed-20261016-151025-546199-post.SAV` |
| both index -1, different coast flags, distance 3 | 57 | `reg_fallback_cross_observed-20261016-151025-546199-post.SAV` |
| equal targets on opposite sides of box 0 | same-region target wins with either table index | `reg_same_right_observed-20261016-150204-535849-post.SAV`, `reg_same_left_observed-20261016-150204-535849-post.SAV` |
| target at x=58 exactly, versus interior x=62; actor x=60 | interior target wins, score 110, distance 2 | `reg_boundary_observed-20261016-150204-535849-post.SAV` |

These are observed **scorer outputs**; the final AI action also depends on its
city score and decision tree. They do not prove every scorer's complete formula
through play. In particular the negative-score rounding and city modifiers
remain code/x86 evidence, and synthetic corridor coordinates are not a natural
island crossing.

## Automatic resupply reaches embarked armies (#23)

`[code]` `FUN_0044f31c` calls `FUN_0044e41c` for every own army before testing
whether it has moves (52925-52928). Neither caller nor city loop tests the
covered-cell/embarked flag. The loop uses the **army record's coordinates**;
it does not follow the fleet link. For each city in table order, Chebyshev
distance must be < 5. Own cities need positive stock; foreign non-war cities
also need a positive purse captured at entry to the city loop. The supplies
and purse routine is `FUN_0044f6d8` (53077).

`[Wine, staged]` In the matched `aboard` / `land` cases a 30,000-foot army starts
with 50 tons, purse 500 and no moves. Its fleet has 720 tons (full), purse 100,
condition 100 and no moves. Other Roman armies were removed. All city stocks
except Antium were zero. The embarked army's covered cell is -1 and the carrier
links to army 0. The land control is on an adjacent land tile with the same
city distance.

- Both receive **250 tons**: army 50 -> 300; Antium 330 -> 80; carrier supply,
  carrier purse, army purse and treasury unchanged. Saves:
  `aboard-20261016-145017-521550-post.SAV` and
  `land-20261016-145017-521550-post.SAV`, turn 0734.
- Embarked distance 4 still receives 250 tons; distance 5 receives none:
  `a_dist4-20261016-145017-521550-post.SAV` /
  `a_dist5-20261016-145017-521550-post.SAV`.
- Empty-stock and hostile-city controls leave the army at 50 tons and preserve
  city stock: `a_empty-20261016-145017-521550-post.SAV` /
  `a_hostile-20261016-150546-540049-post.SAV`. The war control also recruits;
  its treasury change is **not** attributed to resupply.
- With army purse 0 and treasury 1, the army receives **500**, leaving treasury
  **-499**. Treasury 0 blocks the grant while still allowing free supply:
  `a_positive-20261016-145017-521550-post.SAV` /
  `a_zero-20261016-145017-521550-post.SAV`.
- A synthetic earlier supplying city fills the army before Antium. It receives
  one 500 grant, then purse 500 blocks another; Antium retains all 330 tons:
  `a_repeat-20261016-145017-521550-post.SAV`.

The direct answer is **yes, in these controlled Wine cases**. No army/fleet
stock conflation is needed to obtain the increase. This does not prove the
remake's own transported-coordinate representation or native Windows behavior.

## Fleet grant and repair thresholds (#26)

`[code]` Launched own fleets run `FUN_0044e5dc` before movement, even with zero
moves. It visits cities at distance **< 4**, not <= 4. Own-city eligibility
does not require stock; foreign cities need non-war relation, stock and an
entry purse > 0. This handler itself does not test whether the city is coastal;
the separate destination selector's coastal/path tests must not be imported
into it. `FUN_0044f7e4` (53120) performs these separate own-city operations:

1. Supply `min(ships*8 - current supply, city stock)` free.
2. If purse **< 100** and treasury **> 100**, add **100** to purse and subtract
   100 from treasury. This is an increment, not setting the purse to 100.
3. If condition **< 95**, subtract
   `trunc(((100-condition)*ships)/5)` from treasury and set condition to 100.
   There is no solvency gate or alternative flat-100 repair branch here.

The candidate supply amount is computed first; the code commits the supply/stock
writes after the purse/repair operations. These are distinct from the army's
500-based grant and from the human repair dialog.

`[Wine, staged]` With 90 ships, the observed table includes:

| Purse / treasury / condition initially | Observed result | Post save (turn 0734) |
|---|---|---|
| 99 / 101 / 100 | purse 199, treasury 1 | `f99t101-20261016-145549-528200-post.SAV` |
| 99 / 100 / 100 | purse and treasury unchanged | `f99t100-20261016-145549-528200-post.SAV` |
| purse 100 or 101, treasury 101 | no grant | `f100t101-20261016-145549-528200-post.SAV`, `f101t101-20261016-145549-528200-post.SAV` |
| 100 / 1 / 94 | condition 100, treasury -107 (cost 108) | `f94-20261016-145549-528200-post.SAV` |
| 100 / 101 / 94 | condition 100, treasury -7 (still cost 108) | `f94t101-20261016-150546-540049-post.SAV` |
| 99 / 101 / 94 | purse 199, condition 100, treasury -107 (100 + 108) | `f94grant-20261016-150546-540049-post.SAV` |
| condition 95 or 96, treasury 1 | no repair | `f95-20261016-145549-528200-post.SAV`, `f96-20261016-145549-528200-post.SAV` |
| 91 ships, condition 94, treasury 1 | condition 100, treasury -108 (cost 109) | `f94s91-20261016-150546-540049-post.SAV` |

Supply 50 -> 380 drains the available 330 tons; supply 700 -> 720 takes only
20; empty stock gives none. Isolated south-of-Antium distance 3 and 4 controls
give grant/supply versus no changes (`f_y3` / `f_y4` post saves of
`20261016-150546-540049`). The earlier westward `f_dist4` case is **not** a valid
no-provider control: Rome itself is within distance 3, and a grant still occurs.
The hostile control makes no fleet supply/grant change; war recruitment changes
treasury separately. With two own cities each stocked at 50, supply rises
50 -> 150, both city stocks become zero, and grant/repair occur only once
(`f_repeat-20261016-150546-540049-post.SAV`).

**Correction for intake:** strategic-AI report §4's "topped to 100" and "or for
a flat 100 talents when treasury is above 100" conflate the purse increment
with repair. The original code and these cases distinguish them. No other
repository was edited to apply that correction.

## Limits

All played cases are staged Wine observations. Native Windows repetition is
still needed. No natural target-choice distribution, negative-score Wine case,
full foreign-purchase matrix, general transported-coordinate synchronization
rule, or complete strategic-AI reimplementation is established here. Source
staging restores covered cells and preserves input lengths; war controls have
explicit unrelated economy activity. Exact filenames and all non-subject
fields remain inspectable in the raw logs and immutable saves. These are
record-based synthetic controls: changing city ownership does not rebuild its
nation city lists, and relocated carrier records in the early army-distance
cases do not rebuild the whole strategic overlay. No movement/pathfinding or
natural reachability claim rests on those cases; the tested resupply loop reads
the recorded coordinates, ownership, stock and links directly.
