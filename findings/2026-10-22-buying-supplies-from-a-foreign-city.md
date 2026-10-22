# Buying supplies from a foreign city at peace: 1 talent per 5 tons from the army's purse to the city's owner, capped by capacity and by the purse

2026-10-22. **[confirmed]** (code + two plays, Wine). `docs/rules-digest.md` §2 had it as **[C code; no save yet]**;
run `run-exp-manual-gaps`, item B9.

## Answer

- **The dialog.** Supply army next to a foreign city at peace (and no own city) is a different layout from the own-city one:
  "Supplies at Agrigentum", "Army's supplies"; **10s / 100s** arrows; "Supplies amount", "Supplies cost"; a **Buy supplies**
  button (the catalogue's "Transfer"); "Army's money"; OK. There is no "National balance" row: the treasury is not involved.
- **Play** (seed build `354d8265…`, seed 12345, Rome's army 1 moved next to Agrigentum, Carthage, relation peace; turn 0720):

  | Case | Army before (troops, supplies, purse) | 10s clicks | Shown amount / cost | Army after | Agrigentum stock | Carthage treasury | Rome treasury |
  |---|---|---:|---|---|---:|---:|---:|
  | capacity cap (`MG_B9_before_buy.SAV` → `MG_B9_after_buy.SAV`) | 22,000, 176, 100 | 5 | **45 / 9** | supplies 221, purse **91** | 197 → 152 | 11,000 → **11,009** | 2,200 (unchanged) |
  | purse cap (`MG_B9b_staged_army1_purse5_supplies0.SAV`, purse 5, supplies 0 staged) | 22,000, 0, 5 | 5 | 25 / 5 | supplies 25, purse **0** | 197 → 172 | 11,000 → **11,005** | 2,200 |

  - Five 10s clicks asked for 50 tons; the amount stopped at **45 = troops div 100 + 1 − supplies** (221 − 176) in the first
    case and at **25 = purse × 5** in the second.
  - The cost is **amount div 5** talents, taken from the **army's purse** and added to the **selling city's owner's**
    treasury; the city's stock falls by the amount. The buyer's treasury does not move.
  - The decoded diff of the first case (`B9-buy-supplies-diff.txt`) has only these fields plus Rome's map view.

## What this does not establish

- One city, one seller; an amount not a multiple of 5 was not tried, so the rounding of `amount div 5` is the code's, not seen.
- The 100s arrow and the stock cap (a city with less stock than asked) were not exercised.
- The army's position is staged (moved by a save edit next to Agrigentum, map marker kept consistent); the second case also
  edits the purse and supplies. The purchase itself is natural play.

## Evidence

- `runs/experiments/data/run-exp-manual-gaps/`: `B9-buy-supplies-diff.txt`, `run-log.jsonl` (`B9_buy`, `B9b_buy`: memory
  before and after), `staged-edits.jsonl`, `shots.csv`; screenshots `MG_B9_supply_army_foreign_city_open.png`,
  `MG_B9_supply_army_foreign_city_5x10s.png`, `MG_B9_supply_army_foreign_city_after_buy.png`,
  `MG_B9b_supply_army_purse5_5x10s.png`, `MG_B9b_supply_army_purse5_after_buy.png`.
- Saves (Drive `IC2/artifacts/run-exp-manual-gaps/saves/`): `MG_B9_staged_rome_army1_at_107_67_agrigentum.SAV`
  (`4032493126b6…`, from `run0-start-AUTO0720-seed12345.SAV` `050bc354f1cb…`), `MG_B9_before_buy.SAV` (`6b89237fe38d…`),
  `MG_B9_after_buy.SAV` (`7a31b543b064…`), `MG_B9b_staged_army1_purse5_supplies0.SAV` (`9eec73ac5bf9…`).
