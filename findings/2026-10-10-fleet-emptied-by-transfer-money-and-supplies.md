# A fleet emptied by Transfer ships passes its money and supplies to the receiving fleet, with no cap

**Status:** draft from ic2-conquest (2026-10-10), answering ic2-research `docs/pending-requests.md` ef0d3e2. Not promoted.

**Tags:**
- `[P]`: played in the original under Wine (fast rollingsave seed exe, seed 12345), read from the saves and game memory.
- `[derived]`: the rule as stated.
- `[code]`: reading of the pinned decompile (`all_app_functions.txt`, line numbers below).

## Answer

**Method and environment:** one fresh Wine process per case, fast rollingsave seed exe, seed 12345. Environment: Wine 10.0 (Ubuntu 10.0~repack-12ubuntu1), fonts-wine, Book Antiqua -> DejaVu Sans; recorded after the runs in `environment-after-runs.json` (same machine, fonts and Wine unchanged since the 19:33 font experiment, `run-exp-machine-move/RESULTS.md` §5).

`saves/fleet-split-antium-0734.SAV` (turn 0734): fleet 2 at (101,46), fleet 5 at (101,47). Fleet records staged (L1, fleet records only, never x/y). Fleet 5 gives ships to fleet 2 with the ship arrows only; the supply and money arrows are untouched. Values are (owner, ships, supplies +14, money +16); Rome's treasury is 1730 in every save.

| Case | Staging | Fleet 2 before | Fleet 5 before | Fleet 2 after | Fleet 5 after | Box |
|---|---|---|---|---|---|---|
| Td0 (gives 5 of 10) | as Td1 | 0, 20, 50, 400 | 0, 10, 37, 123 | 0, 25, **50, 400** | 0, 5, **37, 123** | none |
| Td1 (gives all 10) | | 0, 20, 50, 400 | 0, 10, 37, 123 | 0, 30, **87, 523** | -1, 0, 37, 123 | none |
| Td2 (gives all 10, cap test) | | 0, 5, 40, 400 | 0, 10, 90, 123 | 0, 15, **130, 523** | -1, 0, 90, 123 | none |

Saves: `Td0_20261010-213628_before.SAV` / `_after.SAV`, `Td1_20261010-213503_before.SAV` / `_after.SAV`, `Td2_20261010-213548_before.SAV` / `_after.SAV` (release `run-exp-fleet-empty-transfer`; table `table_from_saves.md`). The Td1 dialog just before OK (`Td1_20261010-213503_dialog_before_ok.png`) shows ships 0 / 30, supply 37 / 50, money 123 / 400.

- **Money: the receiver gets the giver's money** `[P]` (Td1: 400 + 123 = 523; Td2: 400 + 123 = 523).
- **Supplies: the receiver gets the giver's supplies** `[P]` (Td1: 50 + 37 = 87; Td2: 40 + 90 = 130).
- **No cap** `[P]`: Td2's 130 supplies exceed the receiver's room, 15 ships x 8 = 120, and are kept whole. Nothing is clamped to the fleet's capacity.
- **Rome's treasury does not change** `[P]` (1730 before and after in all three cases): nothing is refunded or taken.
- **It happens only when the giver is emptied** `[P]`: a partial transfer (Td0) leaves +14 and +16 of both fleets unchanged, since the dialog's supply and money spinners were not touched.
- **The deleted giver is a tombstone** `[P]`: its record keeps owner -1, 0 ships and its old supplies and money (Td1: 37, 123), so the values are copied to the receiver, not zeroed on the giver. Nothing is lost on the player's side; the money and supplies of the tombstone are dead data.
- **No box appears** `[P]` before or after OK, in any case (`boxes_before_ok` and `popups` empty in the jsonl logs).

## Code reading `[code]`

`TFleetToFleet_OK` (`0x443b48`, dump lines 44970-45028; fleet table `0x49c26c`, 26 bytes per fleet, so `DAT_0049c27a` = +14 supplies, `DAT_0049c27c` = +16 money, `DAT_0049c27e` = +18 ships). Both dialog copies are written back first (44988-44993, 44998-45003). Then, with the giver `param_1[0x9e]` and the receiver the short at `+0x27a`:

```
45006  if ((&DAT_0049c27e)[iVar3 * 0xd] == 0) {                     // giver has 0 ships
45011    (&DAT_0049c27c)[sVar1 * 0xd] = (&DAT_0049c27c)[sVar1 * 0xd] + (&DAT_0049c27c)[iVar3 * 0xd];   // receiver money += giver money
45012    (&DAT_0049c27a)[sVar1 * 0xd] = (&DAT_0049c27a)[sVar1 * 0xd] + (&DAT_0049c27a)[iVar3 * 0xd];   // receiver supplies += giver supplies
45013    FUN_0044ad38((short)param_1[0x9e]);                          // delete the giver
```

Lines 45015-45023 are the same for the other side (the receiver emptied, its values added to the other fleet, then `FUN_0044ad38`). So the handler adds +14 and +16 to the survivor before calling `FUN_0044ad38`, as Td1 and Td2 show; research's reading that `FUN_0044ad38` itself writes neither stays true. No capacity test on the sum.

## Evidence

- **Data:** `runs/experiments/data/run-exp-fleet-empty-transfer/` (`fleet_empty_transfer.py`, `fleet_empty_transfer-<case>-<stamp>.jsonl`, `table_from_saves.md`, `SAVES.sha256`, `README.md`).
- **Release:** `run-exp-fleet-empty-transfer`.

## Not established

- **The receiver emptied side** (45015-45023, the second branch) was read, not played (Tc2 of the earlier experiment emptied fleet 2 but with 0 supplies and money).
- **Both fleets emptied at once** was not tried; with the arrows one side keeps ships.
- **A carried army** is deleted with its emptied fleet (earlier finding, Ta4); not combined with money here.
- **The desktop original.**
