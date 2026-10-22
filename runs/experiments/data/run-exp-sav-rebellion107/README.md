# run-exp-sav-rebellion107: native check of the rebellion and revival rule

The owner approved the run in the session on 2026-10-22; the proposal is in
[issue #107](https://github.com/diegoami/ic2-conquest/issues/107#issuecomment-6335762553).

**Setup.** Seed build, seed 12345, headless Wine. Script:
`runs/experiments/sav-inert107/rebellion.py` (`craft`, `run`, `analyse`).
- **Input:** research's natural week-11 save `1_rome_270_winter_11.sav`
  (release `run-exp-battle-probe`, SHA-256 `76b09ee3…`). The end of its turn
  runs the quarterly loop.
- **The crafted copy changes only loyalties:**
  - the 8 cities of allegiance Galatia (dead, all held by Seleucid) → 20;
  - Agrigentum (owner Carthage, allegiance Greece) → 5;
  - Ebora (owner = allegiance = Celtiberia) → 5;
  - Carthage's capital → 5.
- **Control:** the unmodified save.
- **Files:** step log `run-20261022-075816.jsonl`, receipt
  `analysis-20261022-075816.json`, hashes `SAVES.sha256`.

**Results (one End turn; one quarterly loop and one full round):**

- **Revival (rule confirmed).** Galatia holds all 8 cities. Its capital is
  Ancyra (218), the map marker there is owner + 84, conqueror is −1, tax is
  20 and its leader changed.
  - **Values had already moved on.** Unity 480, mobilisation 47 and
    treasury 333 differ from the starting values (450 / 50 / 0) because the
    rest of the quarterly loop and the following seats ran before the
    autosave. Mobilisation 47 is the quarterly −3.
  - **Relations (increment 10's correction confirmed).** Seleucid ↔ Galatia
    is −7, i.e. the −8 cooldown after one thaw. Media's −8 toward Galatia,
    set before the revival, is kept. Three AI nations made trade
    agreements (1) with Galatia during the round.
- **R1:** Agrigentum went from Carthage to its allegiance nation, Greece.
- **R2:** Ebora went from Celtiberia to Gaul. Celtiberia was at war only
  with Carthage, and no Carthaginian army was within 10 tiles, so the
  neighbour rule applied. Gaul scores −83 and Carthage −124 on
  `cities − 2 × distance` (computed on the input state).
- **Control:** Carthage's capital (loyalty 5) did not rebel.
- **Plain control:** one city (150) changed owner in both runs, so it was an
  event of the round itself, not of the crafted loyalties.

Saves: `gdrive:IC2/artifacts/run-exp-sav-rebellion107/` (`rclone check`: 4
matching); this container has no release token. To publish them, copy them
from Drive first, then:
`gh release create run-exp-sav-rebellion107 artifacts/run-exp-sav-rebellion107/*/*.SAV`
