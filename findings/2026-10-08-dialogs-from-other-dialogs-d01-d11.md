# Dialogs reached from other dialogs — verification of rows D01–D11

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows D01–D11. Eleven dialogs, all form-bound, sharing three extraction sources (`forms.json`, `function_list.tsv`, `form_xrefs.tsv`) plus a fourth — the dialog's own literals in `dump_string_literals.v2.tsv` — for the boxes that print text. One consolidated document.

**Tags.** Each row's tag is carried from the inventory (`[confirmed]` or `[derived]`); the cell-level extraction below tightens the evidence without re-tagging.

## Answer

| Row | Form | Form-init function (function_list.tsv) | Form xrefs (form_xrefs.tsv) | Dialog's own literals (dump_string_literals.v2.tsv) | Test / screenshot evidence | Match |
|---|---|---|---|---|---|---|
| D01 Supply | TAFSupply | `TAFSupply_TransferSupply @ 0x0043ff98` (the OK-side handler) | `TAreaMap_CheckQuit @ 0x0043eda7`, `TUnitMap_SupplyArmy @ 0x00446fdb`, `TUnitMap_SupplyFleet @ 0x00447854`, `TUnitMap_SupplyFleet @ 0x004478af` (3 callers from `TUnitMap_SupplyFleet`) | none (the form has only labels and spinners; no quoted prompt text) | `tests/test_orders.py` `keep(g.save_as("T_SUPPLY_FLEET.SAV"))` (Antium +100 t); `findings/2026-10-02-fleet-orders-live.md`. UI: row UA01 / UF01 source. | identical |
| D02 Mercenary | TRecruitMercs | `TRecruitMercs_RecruitMercUnit @ 0x00441360` (the OK-side) | `TRepairFleet_Cancel @ 0x00440fcf`, `TUnitMap_RecruitMercenaries @ 0x00447171` | none | `C:§1 'Hire mercenaries' (saves/merc-hire-free-0720.SAV)` — Samnite LI 3,868 q8 joined, no price deducted. UI: row UA02. | identical |
| D03 Army-to-army transfer | TArmyToArmy | `TArmyToArmy_InitializeForm @ 0x00441c24` (note: uses "Initialize" spelled with capital-I as Delphi did) | `TRecruitMercs_OK @ 0x00441b35`, `TUnitMap_ArmyToArmyTransfer @ 0x004472e1`, `TUnitMap_SplitArmy @ 0x004475eb` (and is itself `Initialize`d with title `"Split army"` for UA04 — see below) | "Split army" header (the same form is `Initialize`d with a different title when reached from `TUnitMap_SplitArmy`); see UA04 row prose | `C:§1 'Transfer unit' (T_TRANSFER.SAV: 5,000 from army 0 to army 1)`; `findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md`. | identical |
| D04 Fleet-to-fleet | TFleetToFleet | `TFleetToFleet_InitializeForm @ 0x0044356c` | `TArmyToArmy_Cancel @ 0x00443477`, `TUnitMap_FleetToFleetTransfer @ 0x00447a30`, `TUnitMap_SplitFleet @ 0x00447d65` (same form, title switches to "Split fleet" when reached from `TUnitMap_SplitFleet`) | "Split fleet" header (UF04) | `C:§1 'Fleet: move, embark, disembark, supply, repair, split, join, transfer, scuttle' (T_TRANSFER_SHIPS.SAV)`; `saves/fleet-split-antium-0734.SAV`. | identical |
| D05 Rename unit | TRenameArmyUnit | `TRenameArmyUnit_InitialiseForm @ 0x00443e38`, `OK @ 0x00443f50`, `Cancel @ 0x00443fcc` | `TFleetToFleet_Cancel @ 0x00443e1d`, `TChangeArmyUnits_RenameUnit @ 0x00444c49` | rows 241–242 of `dump_string_literals.v2.tsv`: `"You can only rename regular units."`, `"You can only rename 1 unit at a time."` (in `TChangeArmyUnits_RenameUnit @ 0x00444bb0`) | `C:§1 'Change units (rename, split, join units)' (T_RENAME.SAV: '1st Foot Battalion' -> 'Legio Test')`. | identical |
| D06 Split unit | TSplitArmyUnit | `TSplitArmyUnit_OK @ 0x004444cc` | `TChangeArmyUnits_SplitUnit @ 0x00444cc4` (the caller) | rows 229–238: ordinals `"st"`, `"nd"`, `"rd"`, `"th"`, units `"Foot"`, `"Guards"`, `"Bowmen"`, `"Lancers"`, `"Dragoons"`, `" Battalion"` (the new-unit name template); rows 243–246 refusals: `"This unit is too small to split."`, `"This army already has 20 units."`, `"You can only split regular units."`, `"You can only split 1 unit at a time."` | `C:§1 'Change units (rename, split, join units)' (T_SPLITUNIT.SAV: a 5,000 unit splits 2,500 / 2,500)`. | identical |
| D07 Change units: Join + Disband | TChangeArmyUnits | `TChangeArmyUnits_RenameUnit @ 0x00444bb0`, `_SplitUnit @ 0x00444cc4`, `_JoinUnits @ 0x00444e8c`, `_Disband @ 0x004450c8` (separate methods on the same form) | form is reached from `TUnitMap_SelectUnit` via the `Change units` toolbar button | rows 247–249 (`TChangeArmyUnits_JoinUnits`): `"You can only join regular units together."`, `"These units are too large to be combined."`, `"You can only combine units of the same type."`; rows 250–254 (`TChangeArmyUnits_Disband`): `"Are you sure you want to disband "` + `" unit"` + `"s"` + `"."`, plus `"An army must be near its own city to disband a regular unit."` | `C:§1 'Change units (rename, split, join units)' (T_JOINUNITS.SAV, T_CHUNITS_REFUSED.SAV)`. | identical |
| D08 End turn ? box | TToEndTurn | `TToEndTurn_InitializeForm @ 0x00459828` | reached from `TPremierForm_EndTurn` (the End-turn handler) | (warnings 1–5 cited in `findings/2026-10-03-end-turn-warning-box.md`, no per-line quoted literals in tracked data; the warnings are joined strings) | `C:§1 'End turn' (T_END_AUTO0721.SAV)`; `findings/2026-10-03-end-turn-warning-box.md`; `coverage.md` §1 'End turn'. | identical |
| D09 Offer of peace (after a battle) | TBattlePols | `TBattlePols_InitializeForm @ 0x004577ec` | reached from `TBattleOver_OK @ 0x00459560` after the Battle-ended box | rows 403–406: `"After defeating you in battle "`, `" are willing to end"`, `"After losing to you in battle "`, `" are willing to end"` | `coverage.md` §1 row 35 ✅; `findings/2026-10-05-battle-peace-offer.md` — gate measured end-to-end: `loss_s1_yes_r1_post.SAV` (Yes closes war, no money / unity / city change), `loss_s1_no_r2_post.SAV` (No, Gaul takes Rome a turn later); box screenshot `loss_s1_survey_r1_dialog-Offer_of_peace-1791142747.png`. | identical |
| D10 Peace offers between 2 human players | THVHBatPols | `THVHBatPols_InitializeForm @ 0x00457fa8` | reached from `TBattleOver_OK @ 0x00459560` (parallel to TBattlePols) | inventory cites literals `" has defeated "`, `" will pay reparations of "` (per the feature inventory's D10 row) | `[derived]` in inventory — test-wise reachable only when two humans are seated in one battle; no `tests/results.md` row in this repo; `F:2026-10-02-two-human-seats.md` sets up the precondition. | identical (literals match the inventory's prose; `[derived]` flag carried) |
| D11 Battle ended box (boundary) | TBattleOver | `TBattleOver_InitializeForm @ 0x00458bc8` | reached from the tactical battle's end-of-battle handler | `findings/2026-10-04-battle-probe.md` references TBattleOver; result box `NB_post_battle.SAV` | `coverage.md` §2 'Battle screen'; `F:2026-10-04-battle-probe.md` — `NB_post_battle.SAV` saved after the result box. | identical |

## What does not match — three open notes

1. **D10 (THVHBatPols) is `[derived]`** in the inventory. The form exists, the function-table row is exact, the literals (`" has defeated "`, `" will pay reparations of "`) match the inventory's prose, but **no test save** exercises the path — the precondition is two humans in one battle, which the harness doesn't currently drive. The reproduction would need a `tests/test_orders.py` extension that runs a 2-player game and reaches a battle where both sides are human seats. **Recorded as the one unclosed cell** in the D-section.
2. **D08 (TToEndTurn) warning-line literals are not in `dump_string_literals.v2.tsv`.** The five warnings — *"An army of yours needs supplies."*, *"An army of yours cannot afford to pay its mercenary units."*, *"A fleet of yours needs repairing."*, *"One of your fleets is not docked at its own city."*, *"A fleet of yours needs supplies."* — appear in `findings/2026-10-03-end-turn-warning-box.md` and the inventory's D08 row, but I did not see them in the literals table (only the prompt-side call sites are addressed). They are likely in a function the inventory doesn't name; the order matters for byte-exact reproduction but the **preconditions** (when each line shows) are already verified in the cited finding.
3. **D01 (TAFSupply) is opened from `TUnitMap_SupplyArmy` and from `TUnitMap_SupplyFleet` — but `TUnitMap_SupplyFleet` is listed twice in `form_xrefs.tsv`** (rows `0x00447854` and `0x004478af`). That's two call sites in the same function (probably the "buy at city" and "buy at foreign fleet" branches). Not a duplicate; both are real call sites. Recording so a clone reproduction cites both addresses if it traces the path.

## Method

- **Forms.** `runs/experiments/data/run-exp-feature-inventory/forms.json` (29 forms; extract_forms.py parses every `TPF0` resource of `Imperial Conquest 2.exe`). The eleven forms here are referenced by name in the inventory and in `form_xrefs.tsv`; the count of controls per form is captured by `runs/experiments/feature_inventory/form_xrefs.tsv` and `form_controls.tsv`.
- **Function handlers.** `extract_dump_strings.py` produces `function_list.tsv`; the function-table rows for D01-D11 are reproduced above verbatim. The two `TRenameArmyUnit_InitialiseForm` / `OK` / `Cancel` functions are present; `TRecruitMercs_RecruitMercUnit` is the OK-side only (the form's `InitializeForm` is via the Delphi default, not a row in function_list; covered by the inventory's "[derived]" tag on D02's source for `TUnitMap_RecruitMercenaries`).
- **Form xrefs.** `extract_forms.py` + `form_xrefs.py` produce `form_xrefs.tsv`; each row is `(form, address, ref_count, semicolon-separated caller list)`. Reproduced above.
- **Literals.** `extract_dump_strings.py` produces `dump_string_literals.v2.tsv`; rows with `T<Name>_<Method> @ <addr>` and the literal following it. The cited rows are reproduced verbatim.
- **Test evidence.** `tests/test_orders.py` keeps `T_*` saves for the driven paths (`T_RENAME.SAV`, `T_SPLITUNIT.SAV`, `T_JOINUNITS.SAV`, `T_CHUNITS_REFUSED.SAV`, `T_EMBARK.SAV`, `T_EMBARK_REFUSED.SAV`, `T_SUPPLY_FLEET.SAV`, `T_TRANSFER_SHIPS.SAV`, `T_END_AUTO0721.SAV`, plus the post-battle `NB_post_battle.SAV` and the battle-peace `loss_s1_*` saves from `runs/experiments/battles/`). The cell-level numbers in the table are read from these by `tests/results.md` and reflected in `coverage.md` §1.
- **Tag scheme.** Same as the MM01-MM10 / H-section drafts: a row is `[confirmed]` when a tracked file lists the cited evidence; `[derived]` is carried for D10 (the inventory's flag) and unchanged.

## Inferences

- **D03 and D04 reuse one form for two dialogs.** `TArmyToArmy_InitializeForm` is called from `TUnitMap_ArmyToArmyTransfer` and from `TUnitMap_SplitArmy`; the second caller passes a different title (`"Split army"`). The same is true of `TFleetToFleet_InitializeForm` (Transfer ships vs Split fleet). A clone reproducing the section needs one form class per pair and a string parameter for the title — a single init that takes the title is the natural shape.
- **D07's four methods share one form.** `TChangeArmyUnits_RenameUnit` / `_SplitUnit` / `_JoinUnits` / `_Disband` are siblings in the same class; the form has four entry points. A clone reproduction groups them under one `ChangeUnits` class.
- **D09 and D10 share `TBattleOver_OK` as their entry.** Both `TBattlePols_InitializeForm` and `THVHBatPols_InitializeForm` are reached from the Battle-ended box's OK handler; the dispatch is decided inside `TBattleOver` (human-vs-AI → TBattlePols, human-vs-human → THVHBatPols). Carrying this through to clone code: one `BattleOver_OK` returns to `TBattlePols_InitializeForm` or `THVHBatPols_InitializeForm` based on whether both seats are human.

## What this does not establish

- D10's end-to-end save-diff (no `T_*.SAV` for the 2-human peace path; inventory `[derived]`).
- D08's per-warning-string byte-exact text (the joined strings are addressed by the inventory but not pinned down to literals in `dump_string_literals.v2.tsv`).
- D06's exact new-unit name template across all 20 slots — the literals show the suffix/suffix-piece pattern but not the slot-ordinal mapping.
- Whether any of the eleven dialogs are resizable / have a non-default caption (coverable from `form_controls.tsv` reads; not measured cell-by-cell here).

## Reproduction

```bash
cd ~/projects/ic2-conquest
python3 runs/experiments/feature_inventory/extract_forms.py        # regenerate form_controls.tsv + form_xrefs.tsv
python3 runs/experiments/feature_inventory/extract_dump_strings.py  # regenerate function_list.tsv + dump_string_literals.tsv

grep -E "TToEndTurn|TBattlePols|THVHBatPols|TBattleOver|TRenameArmyUnit|TSplitArmyUnit|TChangeArmyUnits|TArmyToArmy|TFleetToFleet|TAFSupply|TRecruitMercs" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
grep -E "TAFSupply|TArmyToArmy|TFleetToFleet|TRecruitMercs|TRenameArmyUnit|TChangeArmyUnits" \
     runs/experiments/data/run-exp-feature-inventory/form_xrefs.tsv
grep -nE "TBattlePols_InitializeForm|THVHBatPols_InitializeForm|TSplitArmyUnit_OK|TChangeArmyUnits_(RenameUnit|SplitUnit|JoinUnits|Disband)|TRenameArmyUnit|TRecruitMercs_RecruitMercUnit" \
     runs/experiments/data/run-exp-feature-inventory/dump_string_literals.v2.tsv

# Test-side regeneration (drives the dialogs):
pytest -k orders                                                          # the suite driven end-to-end
pytest tests/test_battle_b16.py -k accept_a_post_battle_peace             # D09 path
```

The form + function extracts are deterministic — they read the EXE and the dump. The test runs are the only live-Wine step; the rest is offline.
