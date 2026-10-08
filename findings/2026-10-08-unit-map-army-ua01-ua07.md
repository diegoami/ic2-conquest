# Unit map > Army — verification of rows UA01–UA07

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows UA01–UA07. Seven army actions: supply (UA01), recruit mercenaries (UA02), transfer units (UA03), split army (UA04), join armies (UA05), change units (UA06), disband army (UA07). Most forms and functions already cited in the D-section draft; this draft tightens cell-level evidence for the UA section, including the **form-reuse between UA03 and UA04 (TArmyToArmy)**.

**Tags.** All seven = `[confirmed]` except UA01 = `[derived]` (inventory: *"driven, not yet checked on a save"*). Carried.

## Answer

### UA01 — Supply army (form TAFSupply)

Form `TAFSupply` (in `forms.json`; cell-level extraction in D01 of the D01–D11 draft). Functions:

| Address | Function |
|---|---|
| `0x00446f50` | `TUnitMap_SupplyArmy` (the menu / speed-button dispatcher) |
| `0x0043ff98` | `TAFSupply_TransferSupply` (the OK-side / "Buy supplies" handler) |

Form_xrefs: `TUnitMap_SupplyArmy @ 0x00446fdb` (the form-creation site). Helpers: `R:decompiled-unit-map-orders-and-record-fields.md 'Supply is bought, not moved'` + `findings/...-supply-capacity-rounding.md` carry the supply-capacity formula (`troops div 100 + 1` for armies; `8 × ships` for fleets). Help topic 26 ("Supply army"). Submenu screenshot: `SS:FI_b2_02_unit_army_submenu.png` (the Army submenu list). Refusal literals *(foreign city at war, no city, no money)* `[derived]` carry-over — none in `dump_string_literals.v2.tsv` for this form's specific refusal strings; reproduction would need capstone on the function bodies.

### UA02 — Recruit mercenaries (form TRecruitMercs)

Form `TRecruitMercs` (cell-level extraction in D02 of the D01–D11 draft). Functions:

| Address | Function |
|---|---|
| `0x00446ff4` | `TUnitMap_RecruitMercenaries` (the menu / speed-button dispatcher) |
| `0x00441360` | `TRecruitMercs_RecruitMercUnit` (the OK-side / "Recruit unit" handler) |

Form_xrefs: `TUnitMap_RecruitMercenaries @ 0x00447171`. The "free hire" observed live: `C:§1 'Hire mercenaries' (saves/merc-hire-free-0720.SAV: Samnite LI 3,868 q8 joined; no price deducted)`. Coverage: `coverage.md §1 'Hire mercenaries' ✅`. Research-side `R:decompiled-mercenary-offer-list-and-position.md` carries the offer list and adjacency logic. Help topic 27 ("Recruit mercenaries"). The mercenary quarterly price (`(troops div 200) × priceTable[type] / 5`) is per `decompiled-recruitment-cost-formula.md`; the per-type price table at DAT `0x1F622` is per `decompiled-recruitment-cost-formula.md`'s table literal.

### UA03 — Transfer unit(s) (form TArmyToArmy)

Form `TArmyToArmy` (cell-level extraction in D03 of the D01–D11 draft). Functions:

| Address | Function |
|---|---|
| `0x00447288` | `TUnitMap_ArmyToArmyTransfer` (the menu / speed-button dispatcher) |
| `0x00441c24` | `TArmyToArmy_InitializeForm` (the form-init handler; the title switches to *"Split army"* for UA04) |

Form_xrefs: `TUnitMap_ArmyToArmyTransfer @ 0x004472e1` and `TUnitMap_SplitArmy @ 0x004475eb` — **two callers of the same form**, the Split-army caller passing the alternate title (see UA04 below).

Live evidence: `C:§1 'Transfer unit / army-to-army' (T_TRANSFER.SAV: 5,000 troops from army 0 to army 1)`. Coverage: `coverage.md §1 'Transfer unit / army-to-army' ✅`. Research-side `R:army-to-army-transfer-confirmed.md` documents the form's behaviour. Help topic 28 ("Transfer unit", menu) / 29 ("Transfer units", help / speed button) — the caption difference between menu and the rest. Refusal literals *"These 2 armies combined contain more than 20 units."* / *"... more than 100,000 troops."* at `dump_string_literals.v2.tsv` rows 247 / 249 (carried from D07 in D01-D11).

### UA04 — Split army (form TArmyToArmy, alternate title)

**Same form as UA03**, instantiated with a different title ("Split army"). The function-table search surfaces `TUnitMap_SplitArmy @ 0x0044755c` as the dispatcher.

Refusal *"You can not split an army containing only 1 unit."* `[derived]` — text isn't in `dump_string_literals.v2.tsv`; carried from inventory. Refusal *"At most 198 armies"* isn't in the literals table either; covered by `findings/...-army-to-army-transfer-confirmed.md`.

Live evidence: `C:§1 'Split army' (T_SPLIT.SAV: armies 2 -> 3)`. The "new army at an adjacent tile (one step diagonally)" + "with 0 moves and morale 59" comes from `findings/...-unit-map-mouse-orders-and-tax-range.md (e)` (`saves/mobilize-new-army-0720.SAV`-style metadata reproduced across multiple split-army tests). Help topic 30 ("Split army").

Form_xrefs: `TUnitMap_SplitArmy @ 0x004475eb`. **This is the second caller of `TArmyToArmy`; a reproduction needs to instantiate the form with the alternate caption.**

### UA05 — Join armies (no separate form)

`TUnitMap_JoinArmies @ 0x004472fc` (function-list.tsv). No separate form is opened; the join handler merges the armies in-memory and persists via the standard save path. The form_xrefs entry for `TArmyToArmy_Cancel @ 0x00443477` (per D04's entry) sits at a different address — Join armies' TUnitMap handler reaches the same address but the call graph differs.

Refusals (*"These 2 armies combined contain more than 20 units."* / *"... more than 100,000 troops."* / *"You cannot join fleets if one is carrying an army."*) — last two are fleet-join (UF05); the army-join version is the first two. `[derived]` carry-over for the literals not in `dump_string_literals.v2.tsv`.

Live evidence: `C:§1 'Join armies' (T_JOIN.SAV: 45,700 troops, 12 units)`. Coverage: `coverage.md §1 'Join armies' ✅`. Help topic 31 ("Join armies").

### UA06 — Change units (form TChangeArmyUnits)

Form `TChangeArmyUnits` (cell-level extraction in D05–D07 of the D01–D11 draft — five sibling methods on the same class). The four methods + their addresses:

| Address | Function | Sub-row |
|---|---|---|
| `0x00444bb0` | `TChangeArmyUnits_RenameUnit` | D05 (Rename unit) |
| `0x00444cc4` | `TChangeArmyUnits_SplitUnit` | D06 (Split unit) |
| `0x00444e8c` | `TChangeArmyUnits_JoinUnits` | D07 (Join units) |
| `0x004450c8` | `TChangeArmyUnits_Disband` | D07 (Disband — *units*) |
| `0x00444aa8` | `TChangeArmyUnits_FillListBox` | (helper, listed in literals rows 239–240) |

Form_xrefs: `TUnitMap_SelectUnit` routes the "Change units" toolbar button to `TChangeArmyUnits_InitializeForm`. The "Disband" sub-row was previously a UA07-specific affordance; here it's unit-level only (regular vs mercenary rules differ).

Live evidence: `C:§1 'Change units (rename, split, join units)' (T_CHUNITS.SAV, T_RENAME.SAV, T_SPLITUNIT.SAV, T_JOINUNITS.SAV, T_CHUNITS_REFUSED.SAV)`. Refusals reproduced in `dump_string_literals.v2.tsv` rows 241–254. Help topic 32 ("Change units") + sub-dialogs 33 (Rename), 34 (Split), 35 (Join + Disband).

### UA07 — Disband army

`TUnitMap_DisbandArmy @ 0x004476ac` (function-list.tsv). The confirmation prompt is at `dump_string_literals.v2.tsv` row 273: `"Are you sure you want to disband this army ?"` (in `TUnitMap_DisbandArmy 0x004476ac`). The "army's money returns to the treasury" + "supplies to the nearby city" details are code-level (`[code]` carry-over in the inventory); would need capstone on the function body to enumerate.

Refusal *"An army must be near its own city to disband."* — `[code]` carry-over; reproduction `findings/...-unit-map-mouse-orders-and-tax-range.md` already has the position-near-city check exercised on a save.

Live evidence: `C:§1 'Disband army' (T_DISBAND_ARMY.SAV: armies 2 -> 1, treasury 2,300)`. Coverage: `coverage.md §1 'Disband army' ✅`. Help topic 33 ("Disband army").

The Army submenu rows reproduced from the form capture:

| Submenu item | Speed button | OnClick |
|---|---|---|
| Supply army | `sb_armysupply` (cited via the relevant rows) | `SupplyArmy` |
| Recruit mercenaries | `sb_armymercs` | `RecruitMercenaries` |
| Transfer units | `sb_armytransfer` | `ArmyToArmyTransfer` |
| Split army | `sb_armysplit` | `SplitArmy` |
| Join armies | `sb_armyjoin` | `JoinArmies` |
| Change units | `sb_armychunits` | `ChangeUnits` (→ `TChangeArmyUnits_*` family) |
| Disband army | `sb_armydisband` | `DisbandArmy` |

(`sb_armysupply` and the rest — recorded under `MTUnitmap` in `form_controls.tsv`; not enumerated row-by-row above because the inventory's evidence column cites `coverage.md §2 'Unit map'` for the speed buttons and the rest of the data is consistent with the present draft.)

## What does not match — three open notes

1. **UA01's refusal strings** (foreign city at war / no city / no money) aren't in `dump_string_literals.v2.tsv`. `[derived]` carry-over (inventory: *"driven, not yet checked on a save"*). Reproducing the cell-level refusal text would need capstone on `TUnitMap_SupplyArmy` + `TAFSupply_TransferSupply`.
2. **UA04's refusal *"'You can not split an army containing only 1 unit.' "*** isn't in the literals table either; the literal `"At most 198 armies"` lives elsewhere or in code-only paths. `[derived]` carry-over. Same for the *"already has 20 units"* / *"not yet ready"* class of refusals carried from D06/D07.
3. **UA05's survivor-moves-zero behaviour** — the join handler zeroes the surviving army's `moves` field; the inventory's prose mentions it but the cell-level offset (the relevant `+8` field in the army record) is `[derived]`. Carried forward.

## Method

- **Form + function extraction.** Same toolchain. The four forms (TAFSupply, TRecruitMercs, TArmyToArmy, TChangeArmyUnits) and the per-form handler functions are all in `function_list.tsv`; the form_definitions live in `forms.json`.
- **Cross-row reuse.** UA03 + UA04 share `TArmyToArmy` (two callers, alternate caption) — recorded explicitly. UA06 + D05–D07 share `TChangeArmyUnits` — the cell-level extraction lives in the D01–D11 draft's D05–D07 rows.
- **`form_xrefs.tsv`** lists `TArmyToArmy`'s two callers (`ArmyToArmyTransfer @ 0x004472e1` + `SplitArmy @ 0x004475eb`) and `TAFSupply`'s four references (one for `SupplyArmy`, three for `SupplyFleet`).
- **Reproduction cells.** `saves/mobilize-new-army-0720.SAV`, `T_TRANSFER.SAV`, `T_SPLIT.SAV`, `T_JOIN.SAV`, `T_DISBAND_ARMY.SAV`, `saves/merc-hire-free-0720.SAV` — all cited.
- **Tag scheme.** Same as the other drafts.

## Inferences

- **The `StrategicDecision` + `UnitMapAction` + `ArmyToArmy` dispatcher pattern** repeats across rows: every menu button / speed button has `OnClick=<some-handler>`, the handler calls a per-action function, and the per-action function either opens a form (UA01–UA04, UA06) or runs in-memory (UA05, UA07). The seven UA rows are seven states of one shape.
- **UA03 and UA04 share a form** — `TArmyToArmy` is initialized with two different captions ("Army to army transfer" vs. "Split army"). A reproduction needs to pass the title to the form's `InitializeForm`; the inventory's prose makes the reuse explicit, and the form_xrefs.tsv captures both call sites.

## What this does not establish

- UA01's refusal literal text (`[derived]`).
- UA04's split-army precondition refusal texts (`[derived]`).
- UA05's moves-zero behaviour's exact byte offset (`[derived]`).

## Reproduction

```bash
cd ~/projects/ic2-conquest
grep -E "TAFSupply|TRecruitMercs|TArmyToArmy|TChangeArmyUnits|TUnitMap_(SupplyArmy|RecruitMercenaries|ArmyToArmyTransfer|SplitArmy|JoinArmies|DisbandArmy)" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
grep -E "TUnitMap_SupplyArmy|TUnitMap_RecruitMercenaries|TUnitMap_ArmyToArmyTransfer|TUnitMap_SplitArmy|TUnitMap_JoinArmies|TUnitMap_DisbandArmy" \
     runs/experiments/data/run-exp-feature-inventory/form_xrefs.tsv
grep -nE "TUnitMap_DisbandArmy.*Are you sure|TSplitArmyUnit_OK|TChangeArmyUnits_" \
     runs/experiments/data/run-exp-feature-inventory/dump_string_literals.v2.tsv
```

The form, function and form_xrefs extracts are deterministic. Re-running `tests/test_orders.py` for the relevant tests (`supply_army`, `transfer`, `split_army`, `join_armies`, `disband_army`, `change_units_*`) covers the live evidence.
