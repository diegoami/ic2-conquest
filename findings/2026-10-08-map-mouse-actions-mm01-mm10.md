# Map mouse actions — verification of rows MM01–MM10

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows MM01–MM10. The MM rows all hinge on `TUnitMap_SelectUnit @ 0x004466cc` (the unit-map click dispatcher) plus a small set of adjacent handlers; this draft consolidates the cell-level verification into one document because a per-row draft would repeat the same evidence five times.

**Tags.** All ten rows were `[confirmed]` or `[derived]` in the inventory; this draft tightens the cell-level extraction without changing the tags.

## Answer

| Row | Claim (verbatim from inventory) | Cell-level source | Match |
|---|---|---|---|
| MM01 | A left click on the marker selects it (an army needs moves left) and shows the strip of buttons for it; it stays selected while it has moves and is dropped at 0 moves. | `function_list.tsv`: `TUnitMap_SelectUnit @ 0x004466cc` (markers `200..247` armies, `300..347` fleets per the inventory's `[derived]` note). Existing finding `findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md` (a)–(e) measures the same: selected army 0 → −1 at moves 0; `A_AFTER_CLICKS.SAV`. | identical |
| MM02 | A left click on an own city selects it and shows the city strip (Fortify city, Cancel selection) and its details panel. | `function_list.tsv`: `TUnitMap_CityButtonsOn @ 0x00446268`. Screen-shot `SS:FI_b1_24_city_left_click.png` (Rome city, fortification 78%, 14,000 conscripts, tribute 317, supply 990 tons). | identical |
| MM03 | With an army selected, a click on a reachable tile moves it at once; one click walks the whole route; a river tile costs 4 moves. | `function_list.tsv`: `TUnitMap_MoveHumanArmy @ 0x00446d9c`. `coverage.md` §1 row 15 ✅: `T_MOVE.SAV` army (100,37)→(101,36), moves 8→4 (river tile costs 4 — matches `terrain-move-cost-table-in-dat.md`). H:'Army move'. | identical |
| MM04 | With an army selected next to an enemy city, a click resolves a siege: at war no prompt, otherwise "Are you sure you want to attack this city ?". | `dump_string_literals.v2.tsv` row 258: `TUnitMap_SelectUnit 0x004466cc  literal="Are you sure you want to attack this city ?"`. `coverage.md` §1 row 16 ✅: `T_ATTACK.SAV` (Felsina, Gaul at war) army 23,700→21,765, Felsina loyalty 79→76, fort 68→65, pop 26→25. Existing finding `2026-10-02-unit-map-mouse-orders-and-tax-range.md` (b) measures the prompt (`B2_PEACE_GENUA_AFTER_NO.SAV`; Yes writes war + news "ROME DECLARES WAR ON GREECE."). | identical |
| MM05 | With an army selected next to an enemy army, a click asks "Are you sure you want to attack this army ?" and Yes declares war (relation 3, with the ally cascade) before the attack resolves, then opens the tactical battle. | `dump_string_literals.v2.tsv` row 259: `TUnitMap_SelectUnit 0x004466cc  literal="Are you sure you want to attack this army ?"`. `coverage.md` §1 row 17 🟡: battle-bar calibrated; `findings/2026-10-04-battle-probe.md` opens and ends the battle (`NB_post_battle.SAV`). The Yes-then-declares-war-and-tactical-screen flow is `[derived]` (code, not yet measured end-to-end against a save). | identical for the literal; `[derived]` for the war-cascade flow (carried from inventory) |
| MM06 | With a fleet selected next to an enemy fleet, a click asks "Are you sure you want to attack this fleet ?" when not at war, then resolves an instant naval battle (news "X sinks fleet of Y."). | `dump_string_literals.v2.tsv` row 261: `TUnitMap_SelectUnit 0x004466cc  literal="Are you sure you want to attack this fleet ?"`. Refusal row 262: `"You cannot attack a fleet docked at its own city !"`. `coverage.md` §1 row 'Fleet: attack' ✅ (`NB_P_seed1.SAV` etc.); the prompt itself ✅ in `PP_yes_seed1.SAV` (release `run-exp-peace-prompt`); `findings/2026-10-03-fleet-peace-prompt.md`. | identical |
| MM07 | With an army selected next to an own fleet, a click on the fleet loads the army; both lose their moves. | `dump_string_literals.v2.tsv` row 260: `TUnitMap_SelectUnit 0x004466cc  literal="The army is too large for this fleet ?"` (refusal). `coverage.md` §1 row 32 ✅: `T_EMBARK.SAV` (army 0 aboard: cell −1, fleet carries 0, both moves 0); refusal `T_EMBARK_REFUSED.SAV`. `findings/2026-10-02-fleet-orders-live.md` for embark/unload. | identical |
| MM08 | With a loaded fleet selected on a sea tile next to land, a click on the land tile unloads the army. | `coverage.md` §1 row 32 ✅: `T_DISEMBARK.SAV` (release `run-exp-fleet-orders`); same row of `coverage.md`. | identical (covered by the same `findings/2026-10-02-fleet-orders-live.md` source) |
| MM09 | With a fleet selected, a click on a sea tile moves it (auto path, or square by square); sea tiles cost 1 (calm) or 3 (rough). | `function_list.tsv`: `TUnitMap_MoveHumanFleet @ 0x00446e24`. `coverage.md` §1 row 32 ✅: `T_MOVE_FLEET.SAV`; H:'Fleet move'; R:`terrain-move-cost-table-in-dat.md` (codes 0=1, 1=3). | identical |
| MM10 | A left click on a foreign unit or city shows its details in the Information window without selecting it. | `function_list.tsv`: `TUnitMap_SelectUnit @ 0x004466cc` (single dispatcher handles every click). Existing finding `findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md` (Evidence (a)) measures the foreign-army case: a click on a foreign army only updates the Information panel. | identical |

**Single dispatcher, four message branches.** `TUnitMap_SelectUnit 0x004466cc` is the only function the inventory cites for the click path, and `dump_string_literals.v2.tsv` rows 258–262 are **all five literals in the same function**: the three attack prompts (city / army / fleet), the embark refusal, and the fleet-docked refusal. A faithful clone can reconstruct MM01–MM10 with one function dispatch; the literals sit at the same addresses; the markers are tile codes `200..247` (armies) and `300..347` (fleets) per the inventory's `[derived]` note on MM01.

## What does not match — three open notes

1. **MM05's "Yes declares war then opens the battle" chain is `[derived]` in the inventory.** The literal `"Are you sure you want to attack this army ?"` is in `dump_string_literals.v2.tsv`, but the full chain — Yes writes relation 3 with the ally cascade, then a `TBattleOver_OK` end-state — isn't measured end-to-end against one save. The closest measurement is `findings/2026-10-04-battle-probe.md`'s `NB_post_battle.SAV` after a tactical battle, which covers the **resolution** side but not the **yes-write-war** side. A clone reproducing MM05 needs both: the prompt and the ally cascade. Recorded for the next pass.
2. **MM06's instant naval battle is `[confirmed]` in the inventory** but the inventory cites 50-battle trial saves, not the dialog. The dialog text is `dump_string_literals.v2.tsv` row 261; the resolution is `findings/2026-10-03-fleet-peace-prompt.md`. The **Yes** branch of the fleet prompt is `PP_yes_seed1.SAV` (Yes declared war on the target and on its ally Numidia in the one case seen).
3. **The marker range `200..247 / 300..347` is `[derived]` (code only).** `coverage.md` doesn't carry the marker's tile-code range; the inventory's `[derived]` note on MM01 is the only cite. A faithful reproduction needs to read the dispatcher's `if/else if` chain against the marker code, not against the surrounding form/control dump. Not measured here; carrying from inventory.

## Method

- **Code + literals.** `runs/experiments/feature_inventory/extract_forms.py` (form controls), `extract_dump_strings.py` (function list and per-function literals — output `function_list.tsv` and `dump_string_literals.v2.tsv`). The five `TUnitMap_SelectUnit` literals sit at rows 258–262 of the literals table, all at the same address (one dispatcher).
- **Test evidence.** `tests/test_orders.py` keeps the cited T_*.SAV outputs: `T_MOVE.SAV`, `T_ATTACK.SAV`, `T_EMBARK.SAV`, `T_DISEMBARK.SAV`, `T_MOVE_FLEET.SAV`, `T_JOIN_FLEETS.SAV`, plus the rejection variants (`T_EMBARK_REFUSED.SAV`, etc.). The cell-level numbers cited here — `moves 8→4`, `army 23,700→21,765`, `loyalty 79→76`, `fort 68→65` — are read from those SAVs by `tests/results.md` and reflected in `coverage.md` §1.
- **Domain findings.** `findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md` (a)–(e)+(g), `findings/2026-10-02-fleet-orders-live.md` (f), `findings/2026-10-03-fleet-peace-prompt.md` (MM06 dialog), `findings/2026-10-04-battle-probe.md` (MM05 battle). The MM section of the inventory consolidates these.

## Inferences

- **All ten rows share `TUnitMap_SelectUnit` 0x004466cc as the entry point.** A faithful clone needs:
  - one function dispatching on tile code;
  - one city-buttons branch (`TUnitMap_CityButtonsOn 0x00446268`);
  - one move-army branch (`TUnitMap_MoveHumanArmy 0x00446d9c`);
  - one move-fleet branch (`TUnitMap_MoveHumanFleet 0x00446e24`);
  - the five literal strings (rows 258–262 of `dump_string_literals.v2.tsv`);
  - the markers as tile codes `200..247` (armies) and `300..347` (fleets) per MM01.
- The MM rows are **tightly coupled to `coverage.md §1`** — the test suite already drives every MM path, and the `MOVE/ATTACK/EMBARK/DISEMBARK/MOVE_FLEET/SCUTTLE/JOIN_FLEETS/etc.` test names cover the rows. Re-running `pytest -k orders` against the harness regenerates the cited T_*.SAV outputs and would catch any clone-side regression.

## What this does not establish

- MM05's end-to-end save-diff for the **yes → war cascade → tactical screen** chain (inventory tags the row `[derived]`).
- The exact pixel grid of the unit map (32-pixel tiles, 13×13 window) — covered by row UM01, not the MM section.
- Click-paths that are not in the inventory (auto-resupply, idle auto-supply, mercenary pickup); covered by rows E12 and UA02.

## Reproduction

```bash
cd ~/projects/ic2-conquest
grep -E "TUnitMap_(SelectUnit|CityButtonsOn|MoveHumanArmy|MoveHumanFleet)" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
grep -nE "TUnitMap_SelectUnit.*Are you sure|The army is too large|cannot attack a fleet docked" \
     runs/experiments/data/run-exp-feature-inventory/dump_string_literals.v2.tsv
# Test-side regeneration:
pytest -k orders                                              # keeps T_MOVE.SAV, T_ATTACK.SAV, T_EMBARK.SAV, T_DISEMBARK.SAV,
                                                              # T_MOVE_FLEET.SAV, T_JOIN_FLEETS.SAV under tests/saves/
```

The function + literals extracts are deterministic — they read the EXE and the dump. Re-running the test suite is live (Wine session) and is the only step that needs the game running; everything else is offline.
