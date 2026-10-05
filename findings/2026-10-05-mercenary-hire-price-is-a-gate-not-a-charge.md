# Hiring a mercenary offer: the price is only a minimum purse, nothing is taken from the army or the treasury

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Question 4 of `docs/tasks/v050-rule-reads.md` (clone task T113, `imperial_conquest_2` #571). **Wine-only.** Natural state, nothing edited; fixture copies only. **The task's premise (the price is taken from the army's purse) is not what the original does.**

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; code in `runs/experiments/data/run-exp-v050-rules/code_extract_q4_merc_hire.txt`). `[confirmed]` = seen in play with save pairs.

**Answer.**
- **The hire price is a gate, not a charge** `[derived]` `[confirmed]`. `TRecruitMercs_RecruitMercUnit` @ 00441360 refuses the hire when `army purse < (troops × price[type] div 1000) × quality` ("Your army has too little money to pay these mercenaries.", :43633-43639). **Nothing writes the purse or the treasury anywhere in the function** (:43618-43701): it only fills the next free unit slot of the army (:43658-43669), redraws the army marker (:43670) and empties the offer in the pool (troops word := −1, :43672). In play, two hires left the purse at 30 and the treasury at 2,270 both times (save pairs below).
- **Three different numbers, three different formulas** `[derived]` (all use the same quarterly price table `DAT_00478FD4`, read independently from the DAT file in `dat_unit_prices.tsv`: LI 1, HC 4):
  1. **Hire gate** (the minimum purse): `(troops × price div 1000) × quality` (:43633-43636), the division first.
  2. **Displayed estimate**, the dialog's "Quarterly cost" box: `(troops × price × quality) div 1000` (`TRecruitMercs_ChangeUnit` @ 00441274, :43603-43605), the division last.
  3. **Actual quarterly pay**, billed from the purse at the tick and shown on the army panel as "Mercenary pay": `((troops div 200) × price × quality) div 5` per unit (`FUN_00451B40` :54751, :54757, :54765; the panel: `TInformation_ShowArmyDetails` :41083-41090), the division by 200 first.
  The three do not agree in general. **Samnite LI 3,868 q8:** gate `(3868×1 div 1000)×8 = 3×8 =` **24**; displayed `3868×1×8 div 1000 =` **30**; pay `((3868 div 200)=19 × 1 × 8) div 5 = 152 div 5 =` **30**. **Etruscan HC 960 q9:** gate `(960×4 div 1000)×9 = 3×9 =` **27**; displayed `960×4×9 div 1000 =` **34**; pay `((960 div 200)=4 × 4 × 9) div 5 = 144 div 5 =` **28**. So the box overstates the HC's pay (34 against 28), and the Samnite's 30 = 30 is a coincidence of rounding. The army panel confirms the pay formula: army 1 holding the Samnite showed "Mercenary pay 30", and after the Etruscan too it showed **58 = 30 + 28**, not 30 + 34 = 64 (`Q4b_*_army1_panel.png`, `q4_panel_pay.tsv`) `[confirmed]` (screen reads, with the saves they were taken from).
- **A purse of 30 hired the HC although the box showed 34** (gate 27) `[confirmed]`; purse 20 was refused at the Samnite (gate 24) `[confirmed]`.
- **The first real charge is the first quarterly tick**, from the purse: a mercenary found with a purse of 0 or below leaves (`2026-10-05-army-purse-writes-and-the-1000-cap.md`, row 11).
- **When the Recruit mercenaries order is refused** (`TUnitMap_RecruitMercenaries` @ 00446FF4, in this order) `[derived]`: (0) the army is the selected army, or the army the selected fleet carries (:46871-46877), and is an own army (:46878); (1) an offer city at Chebyshev distance exactly 1 (`FUN_00449D08`, :46881), otherwise **nothing happens and no message**; (2) the 20th unit slot must be empty, else "This army already has 20 units." (:46884, :46914); (3) the army's current troops below 100,001, else "This army cannot get any bigger." (:46885, :46910); (4) the offer city's owner not at war with the nation (relation ≠ 3), else "You cannot recruit from an enemy city." (:46886-46892); (5) supplies at least 15 percent, `supplies × 10000 div troops ≥ 15`, else "No mercenaries will join an army with so few supplies." (:46893-46897); (6) **with a fleet selected**: `troops div 500 ≤ the fleet's ship-count word` (integer division, :46898-46899), else "Your fleet cannot carry any more troops." (:46904-46906); only then the dialog opens (:46900). In the dialog, per hire: the purse gate (:43633-43639); then `army troops + offer troops < 100,001`, else "An army can not contain more than 100,000 troops." (:43641-43644, :43691-43696); then, for an army aboard the fleet the dialog was opened for, `ships ≥ (troops + offer troops) div 500`, else "This fleet has too little space for these mercenaries." (:43645-43656).
- **The hired unit** keeps the offer's label (name), type, troops and quality (`Samnite` li 3,868 q8 at slot 6; `Etruscan` hc 960 q9 at slot 7) and is a mercenary slot (`+0` = the label ≠ 0), so it is paid from the purse every quarter and exempt from the mobilisation rule of disbanding (see the T136 finding).

## Method

- **Code.** Read `TRecruitMercs_RecruitMercUnit`, `TRecruitMercs_ChangeUnit`, `TRecruitMercs_OK`, `TUnitMap_RecruitMercenaries`; the pool record's fields at `0x49D0A4 + 12 n` (`+4` label, `+6` type, `+8` troops, `+10` quality) from `decompiled-mercenary-offer-list-and-position.md`; prices from the game's DAT file (`extract_dat_prices.py` → `dat_unit_prices.tsv`, with the DAT's SHA-256: LI 1, HC 4 quarterly per 200 troops), not from the findings.
- **Play.** `runs/experiments/v050_rules/q4_merc_hire.py` on a copy of `run0-start-AUTO0720-seed12345.SAV` (Rome human, army 1 at (120,53) next to Heraclea with the Samnite offer, purse 100, supplies 176, treasury 2,200; seed 12345; own display). The purse was set with the Supply army money arrows (steps of 10; the arrows only reach multiples of 10 here, so the 24 and 27 gates are tested with 20 and 30). Each hire: army toolbar > Recruit mercenaries > select the offer (the screenshot shows the Quarterly cost) > Recruit unit. Saved before and after each step; the refusal box was read by tesseract on its crop.

## Evidence

Army 1, read from the saves (`state/sav.py`; `claims_audit.py` recomputes the gates and the differences):

| Save | Treasury | Army 1 purse | Units / troops | Offers in the pool |
|---|---|---|---|---|
| `Q4_00_start.SAV` | 2,200 | 100 | 6 / 22,000 | slot 25 Heraclea li 3,868 q8 (label 38); slot 34 Thurii hc 960 q9 (label 37) |
| `Q4_01_purse20_before_hire.SAV` (8 clicks of "10 down") | 2,280 | **20** | 6 / 22,000 | both |
| `Q4_02_after_refused_hire.SAV` (Heraclea, Samnite selected, Recruit unit) | 2,280 | 20 | 6 / 22,000: **refused** ("Your army has too little money to pay these mercenaries.", `Q4_02_heraclea_purse20_after_recruit_click.png`) | both |
| `Q4_03_purse30_before_hire.SAV` (1 click of "10 up") | 2,270 | **30** | 6 / 22,000 | both |
| `Q4_04_after_heraclea_hire.SAV` (dialog shows Quarterly cost 30; gate 24) | **2,270** | **30** | **7 / 25,868**: slot 6 `Samnite` li 3,868 q8 label 38 | slot 25 gone, slot 34 left |
| `Q4_05_before_thurii_hire.SAV` (army moved to (120,55), next to Thurii) | 2,270 | 30 | 7 / 25,868 | slot 34 |
| `Q4_06_after_thurii_hire.SAV` (dialog shows Quarterly cost 34; gate 27) | **2,270** | **30** | **8 / 26,828**: slot 7 `Etruscan` hc 960 q9 label 37 | none of the two |

- **Gate, refusal side:** purse 20 < 24: refused, no change anywhere. **Gate, hire side:** 30 ≥ 24 and 30 ≥ 27: hired. The Thurii hire passed with 30 while the box showed 34, which separates the gate (27) from the displayed number (34).
- **No charge:** purse and treasury identical before and after each hire (30 → 30, 2,270 → 2,270).
- **Displayed estimate, read from the screen**: the dialog's box showed 30 for the Samnite and 34 for the Etruscan (`Q4_02_…`, `Q4_04_…`, `Q4_06_…_offer_selected.png`, read into `q4_displayed_cost.tsv` by `q4_ocr_displayed_cost.py`), which matches formula 2 and not formula 3 (28 for the HC).
- The earlier fixture `saves/merc-hire-free-0720.SAV` (purse 100 → 100, treasury 2,200 → 2,200) is the same result at a purse far above the gate; the inventory's "free offer" was the dialog's Quarterly cost field reading 0 until a row is selected (the offer-selected screenshots show 30 and 34 once a row is selected).
- Saves and screenshots: release `run-exp-v050-rules` (`batch-q4-q6.tar.gz`), hashes in `SAVES.sha256`.

## What this does not establish

- **The first quarterly charge of these units was not run** (it needs End turns to the week-11 tick). The pay formula is `[derived]` from `FUN_00451B40`, and its panel twin was read on screen (30, then 58); the desertion rule and the tick's exactness on real quarters are the research repo's (`upkeep-payment-and-desertion.md`: 32 of 39 army-quarters exact).
- **Other unit types and qualities**: only a LI q8 and a HC q9. The gate's integer division order is read from code and matches the two numbers tested (24 vs 30, 27 vs 34); a case where the two orders differ by more was not run.
- **Purses between the gate and the displayed value** other than 30 (the arrows move in tens). The refusal is tested at 20 only.
- **A hire by a nation that is not human** is free (the AI path): `docs/rules-digest.md` §4, from the research reports; not run.
- **Wine-only**, Rome, turn 0720.

## Reproduction

```text
python3 runs/experiments/v050_rules/q4_merc_hire.py     # about 4 minutes
python3 runs/experiments/v050_rules/claims_audit.py
```
