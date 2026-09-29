# A city can recruit from fortification 75, or as the capital, or with a unit already queued there

**Status:** draft finding from `ic2-conquest`, awaiting promotion to the research repo's `docs/reports/`.

**Question** ([imperial_conquest_2#515](https://github.com/diegoami/imperial_conquest_2/issues/515)): which cities does the *Army recruits* dialog offer, and what fortification level does a city need to recruit?

**Answer** (read from the code, and matched on a save):
- An own city is listed under *Cities to recruit at* when **any one** of these holds:
  1. its fortification is **75 or more**. For a city with a fortification order in progress (a stored value above 100), the part already built, `fort mod 100`, must be 75 or more;
  2. it is the nation's **capital** (nation record `+0x444`);
  3. it **already holds one of the nation's recruitment slots** (a queued unit with troops > 0 whose city word is this city).
- The player's rule in `strategies/rome-v1.md` ("only towns with high-level fortifications can recruit") is right, and the level is **75**.

## Method

- **Build:** `Imperial Conquest 2 fast rollingsave seed.exe` (this repository's `patches/seed_patch.py` on top of `patch_exe.py`), SHA-256 `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`.
- **Code:** capstone disassembly of the original `Imperial Conquest 2.exe` (SHA-256 `9d753d5d…ba31`) around the *Army recruits* city-list fill, which precedes `TArmyRecruits_RecruitUnit` (`0x454E78`).
- **Save:** a new game as Rome, seed 12345: `BASE.SAV` = `AUTO0720.SAV`, SHA-256 `050bc354f1cbbe37…`, 270 BC Spring week 1 (run `tests`, see `tests/results.md`).

## Observations

The loop over the nation's cities (`si` = city index; the city table is at `0x479590`, stride 34, fortification at `+0x1A`):

```text
0x454540  for each of the nation's 40 recruitment slots (+0x2E4):
              if slot.troops > 0 and slot.city == si: listed = 1
0x45457C  if listed: goto add
0x45458C  cx = city[si].fort
0x454594  if cx > 74 and cx <= 100: goto add            ; finished fortification 75..100
0x4545B4  if cx > 100 and cx mod 100 > 74: goto add     ; order in progress, built part 75+
0x4545E9  if si == nation.capital (+0x444): goto add
          else: skip
add:      name = city[si].name; if the city is any nation's capital (0x44B8D0), upper-case it
```

On `BASE.SAV`, Rome's 25 cities have fortifications from 30 to 78. The dialog lists exactly two, `Luceria` (fort 77) and `ROME` (78, and the capital). Arretium (72), the next highest, is absent. Nobody has a slot outside Rome yet.

## Inferences

- **A recruiting city stays a recruiting city while it holds a queued unit**, even if its fortification later falls below 75 (siege erosion lowers fortification win or lose). Mobilizing or disbanding its last slot ends that.
- **Fortification is the lever for recruiting near the front.** It costs `population (thousands) × points` talents and builds about 10 points per turn (research: `decompiled-unit-map-orders-and-record-fields.md`, `city-population-growth.md`). For Rome, taking Arretium from 72 to 75 costs 33 × 3 = 99 talents.
- A captured city is recruitable at once only if its fortification is already 75 or more. Siege erosion (`fort × def/atk`, at least ×3/4) usually takes it below that.

## What this does not establish

- Whether the same gate applies to the AI (the AI recruits through its own code, not this dialog).
- The maximum troops per order (the dialog's ▲ buttons); not probed yet.
- Whether a pending fortification's built part is really what the tick raises (the code reads `fort mod 100` here; the tick's increment was derived in the research, not read here).

## Reproduction

```text
setup/setup.sh
python3 -c "from harness.driver import Game; g=Game(); g.new_game(0, seed=12345); g.open_recruit()"
# screenshot: the list shows Luceria, ROME
python3 -c "from state.sav import *; s=load('BASE.SAV'); print([c['name'] for c in s['cities'] if can_recruit_at(s,0,c)])"
```
