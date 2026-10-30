# SAV export #37, Q3: how the original creates, removes and moves army and fleet records

**Tags:**
- [code]: decompile and disassembly of the pinned EXE;
- [confirmed in emulation]: the original routines executed on the #187 RAM snapshot.

No game was run, and no owner JSON was used.

**Task:** research [#37](https://github.com/diegoami/imperial-conquest-2-research/issues/37) Q3 (remake #1191, for T184):
- the record-ordering, relocation, carrier-link and new-record prototype rules;
- for writing native state into a SAV when the source JSON has no provenance.

It builds on the atlas (increments 5–7) and `2026-10-17-sav-export-live-regions-and-safe-rejection-policy.md` §"Army/fleet
records". Where those already hold a fact, it is cited and measured here, not re-derived.

## 1. Every path that changes the army or fleet tables [code]

| Event | Routine | What it does |
|---|---|---|
| new army | `FUN_00449f08(nation, point, &index)` | appends at index = count, only while count < **198** (0xC6) and `FUN_004492c0` finds a free cell near the point. Callers: recruitment `FUN_0044a4e0`, the AI over-capacity split `FUN_0044f8fc`, the player's `TUnitMap_SplitArmy` |
| unit into an army | `FUN_0044a4e0(nation, recruit slot)` | `FUN_0044a120` looks for an own army at the recruiting city with a free slot; otherwise it creates one there. It fills the slot (label 0, type, quality, troops), names it (`FUN_0044a218`), clears the recruit entry (`FUN_0044a610`) and sets the size-band marker (`FUN_0044a80c`) |
| AI over-capacity split | `FUN_0044f8fc(army, capacity)` | a new army (current nation) at the same position takes whole slots from the first slot where cumulative troops exceed the capacity. **A third of the supplies and of the money** go with it |
| new fleet | `FUN_0044a004(nation, city, ships)` | appends at index = count (no cap inside; the AI caller `FUN_00450768` requires count < **99** and treasury > 3,000). Charges 10 × ships |
| fleet launch | `FUN_0044a050(fleet)`, from the round tick `FUN_004514ec` | position next to the build city (`FUN_0044939c`), condition, supplies, money, marker |
| army removed | `FUN_0044ab90(army)`, 12 callers (battles, siege, merges, disband, elimination, transfer dialogs) | **tombstone**: owner = −1. If aboard (cell +8 < 0), the fleet at the army's coordinates (`FUN_00449970`, the first live match) gets carrier −1. Otherwise the map cell gets the saved underlay (+8) back. Nothing else changes |
| fleet removed | `FUN_0044ad38(fleet)`, 11 callers | **tombstone**: owner = −1. A launched fleet's map cell is set to 0 (sea). **A carried army is removed with it** (`FUN_0044ab90`) |
| fleet merge | `TUnitMap_JoinFleets` | refused if either fleet carries an army, or the ships would exceed 100. Ships, supplies and money are summed, moves set to 0, and the other fleet tombstoned |
| compaction | `FUN_0044adb0`, only from `FUN_00451fdc` | armies, then fleets, **from the last index down**. Each tombstone receives the current last record (`FUN_0044abe0`: 656 bytes; `FUN_0044ad7c`: 26 bytes), and the count drops by 1 |
| table load or new game | the loader; `TUnitMap_CheckQuit` (0x448225/0x44824F) | the counts are set (new game: 15 armies, 2 fleets) |

**When compaction runs** (`FUN_00451fdc`): once on entry, then again **before every AI seat's turn** in the loop that
plays AI seats. It never runs after the last AI seat before a human seat's turn start (`FUN_00452034`). So:
- tombstones created in the last AI seat's turn, or by the human, survive into the human's turn and its saves (the atlas
  found owner −1 army records in saves);
- they are compacted at the next End turn.

## 2. Measured prototypes [confirmed in emulation]

`runs/experiments/savexport37/lifecycle.py`, `lifecycle-v1.json`: each record is filled with a canary byte (0xA5) first,
so every unwritten byte stays visible.

- **Army constructor** (nation 1 = Carthage, AI): index 14 = the old count, count 14 → 15. **96 of 656 bytes written:**
  - `+0x00..+0x0F`:
    - x, y;
    - owner 1;
    - **moves 1** (an AI nation; 0 for a human one: `+0x490 == 0` → 1);
    - covered cell +8 = the map code it stands on;
    - supplies 0, money 0, **morale 59**;
  - `+0x12..+0x15` in each of the 20 slots: type 0, troops 0.
  - The map cell is set to 200 + owner.
  - **Residue:** every slot's `+0x10`, `+0x16..+0x2F` (label, quality, the 24-byte name).
- **Fleet order** (12 ships): index 2 = the old count. **10 of 26 bytes:**
  - owner +8, countdown +0xA = 24, ships +0x12, build city +0x14, carrier +0x16 = −1;
  - treasury −120.
- **Launch:** writes x, y (next to the build city), countdown −1, supplies +0xE = 50, money +0x10 = 0, condition +0x14 =
  100 (the build-city word is reused), +0x18 = 0, and the marker 300 + owner.
  - **Residue: route +4..+7 and moves +0xC** stay as the slot held them. The atlas observed these leftovers in Wine
    (increment 6), and the round tick later sets route_x = −1.
- **Compaction** (14 armies, tombstones at 1 and 4, the last army 13 aboard fleet 0):
  - 12 remain; slot 4 ← army 13, then slot 1 ← army 12. New order (old index per new index):
    `0, 12, 2, 3, 13, 5, 6, 7, 8, 9, 10, 11`;
  - **fleet 0's carrier 13 → 4** (`FUN_0044abe0` repoints every fleet whose carrier equals count − 1);
  - the two slots beyond the new count keep their old bytes.

## 3. Rules for writing native state without provenance

These are inferences from §1–2, labelled as such.

- **Order.** The original's table order is creation order, with removal by "last record into the gap" at compaction.
  - A compacted table, with no tombstones, is a state the original itself produces after every compaction.
  - So a native list with no owner −1 records, in the order the remake keeps (T240 already models this table), is a
    valid original table.
  - Tombstones are optional state: the original handles both.
  - The order matters for decisions: research #117 (ties, capital defence's first 9 threats).
- **Carrier link** (army aboard fleet):
  - fleet +0x16 = the army's index;
  - the army has cell +8 < 0 (no map marker) and the fleet's coordinates;
  - removal finds the fleet by coordinates (first live fleet there), so the army's x, y must equal its fleet's;
  - **a fleet carries at most one army**;
  - when an exporter reorders armies, every fleet +0x16 must be rewritten (what `FUN_0044abe0` does for one move);
  - fleets can be reordered without touching armies.
- **New army record (no lineage):**
  - write the constructor's 96 bytes as above;
  - fully write every live slot (`+0x10` label, `+0x12` type, `+0x14` troops, `+0x16` quality, `+0x18` name);
  - empty slots: type and troops 0. Their label, quality and name are residue in the original and have no effect
    (atlas increment 5: each term × troops div 200 = 0). Zero is what a never-used slot holds (BSS).
- **Unit names:** "<N><st/nd/rd/th> <Foot|Guards|Bowmen|Lancers|Dragoons> Battalion" (`FUN_0044a218`).
  - N = the lowest number from 1 that no live regular unit (label 0, troops > 0) of the same owner and type uses
    anywhere in the army table, capped at 99.
  - The suffix uses `N mod 10`, except 11–13 (`th`).
  - A native army with remake-chosen names is fine for the original (names are text only); this rule is how the
    original names a recruit.
- **New fleet record:**
  - launched: the launch's fields plus moves, route_x = −1 (as the round tick would make it) and route_y;
  - under construction: the order's 10 bytes with x, y, moves and the other words 0 (atlas: all 120 such fleets in the
    corpus hold 0 there).
  - +0x14 is the build city while building and the condition after launch.
- **Caps** the original enforces: armies < 198 on creation; fleets < 99 for the AI's builds (no cap in the human order
  routine); ships ≤ 100 per merged fleet. The fleet table is 140 records long in memory (the pool table starts at
  0x49D0A4). A native state beyond these has no original equivalent.

## What this does not establish

- **Recruitment** (`FUN_0044a4e0`) and **the AI split** (`FUN_0044f8fc`) were read, not executed: they need a ready
  recruit entry or an over-capacity embark.
- **The player's split dialog** (`TSplitArmyUnit`) beyond its constructor call.
- **Byte identity** for records without lineage: impossible by construction (residue). This is about valid original
  state.
- **Native Windows**, live game runs, owner JSON.

## Evidence

- Code: `runs/experiments/savexport37/lifecycle.py`.
- Data: `runs/experiments/data/run-exp-savexport37/lifecycle-v1.json`.
- Private, not published: the decompile dump, the EXE and the #187 RAM snapshot.
