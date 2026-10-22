# Unit map > Fleet — verification of rows UF01–UF06

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows UF01–UF06. Six fleet actions: supply (UF01), repair (UF02), transfer ships (UF03), split fleet (UF04), join fleets (UF05), scuttle fleet (UF06). Most forms and functions are already cited in the D01–D11 draft; this draft pulls them together with cross-row reuse notes (UF01 + UA01 share `TAFSupply`; UF03 + UF04 share `TFleetToFleet`).

**Tags.** All six = `[confirmed]` except UF05 = `[confirmed]` *and* `[derived]` mixed (inventory has both tags for the rule-vs-help divergence). Carried from the inventory.

## Answer

### UF01 — Supply fleet (form TAFSupply)

**Same form as UA01**, instantiated against a fleet instead of an army. `TAFSupply`'s cell-level extraction is in D01 of the D01–D11 draft. Functions (function_list.tsv):

| Address | Function |
|---|---|
| `0x004477fc` | `TUnitMap_SupplyFleet` (the menu / speed-button dispatcher) |
| `0x0043ff98` | `TAFSupply_TransferSupply` (the OK-side / "Buy supplies" handler; shared with UA01) |

`form_xrefs.tsv` lists **three** `TUnitMap_SupplyFleet` references: `0x00447854`, `0x004478af`, and `0x00447854` again (listed twice — likely two branches: city-supply vs. foreign-city-supply vs. fleet-supply; recorded as a non-duplication note in the D01–D11 open items). Fleet capacity = `8 tons × ships`. Help topic 34 ("Supply fleet"). Submenu: `FI_b2_02_unit_fleet_submenu.png`. Live evidence: `T_SUPPLY_FLEET.SAV` (Antium, +100 tons).

### UF02 — Repair fleet (form TRepairFleet)

Form `TRepairFleet` (in `forms.json`). Functions:

| Address | Function |
|---|---|
| `0x004478c8` | `TUnitMap_RepairFlt` (the menu / speed-button dispatcher) |

The form has a 1s/10s spinner pair, a "Cost = ships × points / 5" line, and OK. Refusal literal *"The fleet must be next to one of its own cities and it must not be carrying an army"* `[derived]` carry-over (not in `dump_string_literals.v2.tsv`). Live evidence: `T_REPAIR_FLEET.SAV` (`97 → 100%`, `18 talents` cost). Help topic 35 ("Repair fleet"). Coverage: `coverage.md §3 'Repair'`.

### UF03 — Transfer ships (form TFleetToFleet)

Form `TFleetToFleet` (cell-level extraction in D04 of the D01–D11 draft). Functions:

| Address | Function |
|---|---|
| `0x00447a30` | `TUnitMap_FleetToFleetTransfer` (the menu / speed-button dispatcher) |
| `0x0044356c` | `TFleetToFleet_InitializeForm` (the form-init; switches title for UF04) |

`form_xrefs.tsv` lists **two** callers: `TUnitMap_FleetToFleetTransfer @ 0x00447a30` and `TUnitMap_SplitFleet @ 0x00447d65` — **two callers of the same form**, the Split-fleet caller passing the alternate title (see UF04 below). Refusal *"There are more than 100 ships in these fleets combined."* `[derived]` (not in literals). Live evidence: `T_TRANSFER_SHIPS.SAV`. Coverage: `coverage.md §3 'Transfer ships'`. Help topic 36 ("Transfer ships"). Plus `saves/fleet-split-antium-0734.SAV` for the related split path.

### UF04 — Split fleet (form TFleetToFleet, alternate title)

**Same form as UF03**, instantiated with a different title ("Split fleet"). The function-table search surfaces `TUnitMap_SplitFleet @ 0x00447cac` as the dispatcher. Form_xrefs second caller (above UF03) confirms the reuse.

The *"at least 20 ships"* precondition is `[derived]` carry-over (not pinned in literals). Live evidence: `T_SPLIT_FLEET.SAV` (`20 + 10 ships`); plus `saves/fleet-split-antium-0734.SAV` (run-0 Antium). Help topic 37 ("Split fleet").

### UF05 — Join fleets (no separate form)

`TUnitMap_JoinFleets @ 0x00447a48` (function_list.tsv). No separate form is opened; the join handler merges fleets in-memory, with three refusals (verbatim from `dump_string_literals.v2.tsv` / the inventory's row prose):

| Refusal | Where |
|---|---|
| `"There are more than 100 ships in these fleets combined."` (`[derived]`) | `[code]` carry-over |
| *"You cannot join fleets if one is carrying an army."* | inventory's row prose |
| *"The help page states the rules differently (see 'Where the sources disagree')"* | inventory's row cross-reference |

The help/code divergence on the third bullet is the inventory's noted item — the help `H:'Join fleets'` describes the rules differently from the code. The code's gate is `sum < 101` + check each fleet's `army` field (per the inventory's `X:TUnitMap_JoinFleets 0x00447a48 (the code tests sum < 101 and refuses when either fleet's army field is set)`).

Live evidence: `T_JOIN_FLEETS.SAV`. Coverage: `coverage.md §3 'Join fleets'`. Help topic 38 ("Join fleets") + cross-ref `R:decompiled-unit-map-orders-and-record-fields.md Part 2`.

### UF06 — Scuttle fleet

`TUnitMap_ScuttleFleet @ 0x00447e34` (function_list.tsv). The confirmation prompt is at `dump_string_literals.v2.tsv` row 282: `"Are you sure you want to scuttle this fleet ?"` (in `TUnitMap_ScuttleFleet 0x00447e34`). The "money returns to the government and supply to the nearby city" details are `[code]` carry-over; would need capstone on the function body to enumerate.

Refusal *"Only nations with coastal cities can build fleets."* + *"You do not have a free coastal city at this time."* + *"You cannot build a fleet at this time."* are S06 literals (build-fleet form), not UF06; the scuttle-form refusals `[derived]` carry-over.

Live evidence: `T_SCUTTLE_FLEET.SAV`. Coverage: `coverage.md §3 'Scuttle fleet'`. Help topic 39 ("Scuttle fleet"). Box text read in `tests/results.md 'scuttle_fleet'`.

The Fleet submenu rows reproduced from the form capture:

| Submenu item | Speed button | OnClick |
|---|---|---|
| Supply fleet | `sb_fleetsupply` (cited via Inventory rows) | `SupplyFleet` |
| Repair fleet | `sb_fleetrepair` | `RepairFlt` |
| Transfer ships | `sb_fleetxfer` (per `mn_Fleetxfer` etc.) | `FleetToFleetTransfer` |
| Split fleet | `sb_fleetsplit` | `SplitFleet` |
| Join fleets | `sb_fleetjoin` | `JoinFleets` |
| Scuttle fleet | `sb_fleetscuttle` | `ScuttleFleet` |

(Speed buttons under `MTUnitmap` in `form_controls.tsv`; not enumerated row-by-row here because the Inventory's evidence column cites `coverage.md §2 'Unit map'` for the panel.)

## What does not match — three open notes

1. **UF02's "must be next to its own city and not carrying an army"** refusal is `[derived]` carry-over; not in `dump_string_literals.v2.tsv`. Reproducing would need capstone on `TUnitMap_RepairFlt` or `TRepairFleet_*`.
2. **UF05's *"There are more than 100 ships"* and *"carrying an army"* refusals** — the second is `[derived]` carry-over (referenced in `dump_string_literals` as the inventory's row prose), the first is `[code]` only. The help-vs-code divergence on join-fleet rules is the inventory's flagged item — the help page's wording doesn't match the actual code gates.
3. **UF06's `money/supply return` details** are `[code]` carry-over; literal pattern is in the function body, not in `dump_string_literals.v2.tsv`. The "Are you sure…?" prompt is the only pinned literal (row 282).

## Method

- **Form + function extraction.** Same toolchain. The four forms (TAFSupply [shared with UA01], TRepairFleet, TFleetToFleet, and the in-memory UF05/UF06 paths) are in `forms.json` / `function_list.tsv` / `dump_string_literals.v2.tsv`.
- **Cross-row reuse.**
  - **UF01 + UA01** share `TAFSupply` (one form, two menu items, two callers per `form_xrefs.tsv`).
  - **UF03 + UF04** share `TFleetToFleet` (two callers per `form_xrefs.tsv`).
  - **UF06** is no separate form — `TUnitMap_ScuttleFleet` runs in-memory.
- **Reproduction cells.** Six `T_*.SAV` test outputs (T_SUPPLY_FLEET, T_REPAIR_FLEET, T_TRANSFER_SHIPS, T_SPLIT_FLEET, T_JOIN_FLEETS, T_SCUTTLE_FLEET); saves/fleet-port-antium-0734.SAV + saves/fleet-split-antium-0734.SAV for the run-0 fleet traces.
- **Tag scheme.** Same as the other drafts.

## Inferences

- **`TAFSupply` and `TFleetToFleet` are the two form-reuse stars of this section.** Each is one form, two callers, alternate title. A reproduction wires them once and passes a title parameter.
- **UF05 is the only fleet-action that runs no dialog** — the join is in-memory. Refusals come from code checks (sum < 101, army field test), not from dialog texts.
- **`form_xrefs.tsv`'s three `TUnitMap_SupplyFleet` references** suggest the form captures three caller branches (own city / foreign city / fleet-to-fleet). The inventory's D01 open notes already flagged this — same carry-over here.

## What this does not establish

- UF02's full refusal literal text (`[derived]`).
- UF05's "more than 100 ships" literal text (`[code]`).
- UF06's money/supply return paths (`[code]`).

## Reproduction

```bash
cd ~/projects/ic2-conquest
grep -E "TUnitMap_(SupplyFleet|RepairFlt|FleetToFleetTransfer|SplitFleet|JoinFleets|ScuttleFleet)" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
grep -E "TUnitMap_SupplyFleet|TUnitMap_FleetToFleetTransfer|TUnitMap_SplitFleet" \
     runs/experiments/data/run-exp-feature-inventory/form_xrefs.tsv
grep -nE "TUnitMap_ScuttleFleet.*Are you sure|TRepairFleet" \
     runs/experiments/data/run-exp-feature-inventory/dump_string_literals.v2.tsv
```

The form, function and form_xrefs extracts are deterministic. Re-running `tests/test_orders.py` for the relevant tests (`supply_fleet`, `repair_fleet`, `transfer_ships`, `split_fleet`, `join_fleets`, `scuttle_fleet`) covers the live evidence.
