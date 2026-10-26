# Original Supply provider order, bounded slots, row-binding quirk and staged switching

**Tag:** [confirmed, partial], stock-original Wine. Research78/82; separate from
Research85's signed-supply report. Current promoted supply findings were read
at865755e0; their multi-provider question was still unplayed.

## Exact caller and code-derived policy

`TAFSupply_FindProviders0043F468` uses the target army/fleet coordinates,
scanning x−1..x+1 outside, y−1..y+1 inside, clamping to map bounds. It collects
non-war cities first, then own fleet markers (excluding the target fleet ID):

- City slots retain **first and last** eligible city if more than two appear;
  the two retained cities are swapped when the first has less stock. Thus the
  larger stock is listed first/default; equal stock keeps scan order.
- Fleet slots retain **first, second and last** match if more than three appear.
  This is physical tile scan order, not fleet-record/state order or best stock.
- Visible rows are retained cities then retained fleets, at most2+3. Initial
  selection is row0, city if any, otherwise first fleet. It does not deduplicate
  the later row callback. Map-edge repeated scans were read, not played.

**Important callback quirk:** `TAFSupply_ChangeProvider0043FB10` maps row3 to
fleet slot2 whenever there are two cities. With two cities/two fleets, row3
therefore binds **−1**, not fleet slot1. With two cities/three retained fleets,
rows2/3/4 bind **F0/F2/F2**: F1 is unreachable and the last fleet duplicated.
This is an original defect, not a safe rule to copy automatically. One-city row3
mapping and zero-city three-fleet mapping are separately code-derived; no
universal one-row/one-provider assumption is justified.

## Runtime matrix on the unchanged classical coast

`fleet-split-antium-0734.SAV`,turn0734, private synthetic Roman army0 at existing
land(94,77), original Carthago72/Clupea76 coordinates/ownership unchanged, bilateral
peace. Fleets relocated to actual vacant sea(93,76),(93,77),(94,76),(95,76), with
recognizable stocks/purses. **No city-coordinate or terrain edits** here.

| Input | Visible/default city order | Retained fleets | Actual fleet row bindings |
|---|---|---|---|
| City stocks90/10, fleets2/5 | Carthago,Clupea |2,5,−1|2,−1|
| Same, fleets2/5/0/1 in scan order | Carthago,Clupea |2,5,1|2,1,1|
| Stocks10/90, physical IDs5/2/1/0 | Clupea,Carthago |5,2,0|5,0,0|

Each reachable row was selected through the visible original list, including
wheel-scrolling to row4. Read-only selected-row and provider-form IDs verified
binding. A10ton transfer then identifies the actual donor: valid foreign-city
rows charge2talents; free fleet rows move stock without money. Duplicate rows
both debit the same last fleet; the skipped fleet's distinct stock is untouched.
Invalid−1 in the natural control is recorded **without issuing a transfer**.
An earlier private synthetic own-city pilot pressed it and observed no supply
change; no generalized safe behavior at an invalid index is claimed.

Two additional own-city pilots reverse stock10/90 and90/10, corroborating that
city stock, not table order, determines the default. Their altered city geometry
is kept separate from the unchanged-coast controls above.

## Switching is not a staged reservation

`TAFSupply_ChangeProvider` resets selected IDs but **does not reset amount+290**.
`TAFSupply_TransferSupply0043FF98` uses the **currently selected city**, with no
second stock/room/affordability clamp. Two exact original controls:

1. CityA90,cityB10,army0tons/purse100. Stage+100 at A =>90. Select B => staged90
   remains. Close via Alt+F4 without Buy => stocks90/10,army0/100 unchanged.
2. Same action, **Buy supplies** at B, then Close => A90,B**−80**,army90/82,
   foreign treasury+18. It applies the old amount against the new provider.

This demonstrates an original exploit/negative-stock outcome, not authorization
to weaken the remake's stock invariants. Any decision to preserve safe staging
or emulate the exploit belongs in intake/owner design, explicitly separated from
an erroneous claim about original behavior.

## Evidence and remake handoff

`runs/experiments/data/run-exp-restrictions85/`:
`gui78-natural-v2_*.json` (3complete cases and per-row progress),
`gui78-switch-v3_*.json` (2cases), plus two own-city pilot rows;
`audit-gui-v1.json` reparses all5natural/switch pairs, checks row bindings and
per-row actual donor changes. Primary endpoints:
`gui78-natural-v2_natural-four-fleets_before.SAV` / `_after.SAV`;
`gui78-switch-v3_natural-staged-switch-buy-close_before.SAV` / `_after.SAV`,turn0734.
Original full files/screenshots/hashes private in ignored
`artifacts/run-exp-restrictions85/private-gui78-*/`. No release.

Runners`gui_provider_natural.py`,`gui_supply.py`,`lists.c`,`common.py` under
`runs/experiments/restrictions85/`. Offscreen-row attempt stopped without a final
measurement; its input/receipts remain. Naturalv1 display bind failed before
original launch; naturalv2 uses approved isolated runtime access.

Pinned remake4d70275a production `SupplyProviders.ForArmy` returns all2cities+
4fleets in state order; `native-gui-v3.txt` reproduces6providers. Original above
retains5rows and sorts the two cities by stock. Current`SelectProvider` drops a
staged90 to0; native model confirms that rather than original's retained90.
Thirteen audited source blobs are verified in`native-source-verified-v1.json`.
No installed Godot/native Windows acceptance.

T134's archived specification (`brief-v1/policy-T134.md`) mistakenly calls its
uncapped state-order query original-confirmed. Its explicit list/picker/default-
row presentation choices and later owner-approved army-provider/money-source
extensions remain separate design. Do not remove those extensions or reproduce
negative-index/negative-stock defects without an owner decision. First intake:
correct provenance and distinguish safe presentation from exact original rules.

## Limits

Stock unmodified original (identity private),Wine10.0 Ubuntu10.0~repack-12ubuntu1,
win32,own1280×1024Xvfb. Actual original UI, no memory writes/patch/owner desktop/
End turn. City equal-stock ties, more than2cities and clamped map-edge duplicate
scans are code-derived/unplayed. New findings do not imply fleet opening gates:
those have the separately promoted directional scan quirk and GUI79 controls.
