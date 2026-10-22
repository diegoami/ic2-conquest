# SAV export, gate 2: what a writer must do with every field, and a checker

2026-10-22. **[confirmed for the rules marked "native", static for the rest]**
Research [#37](https://github.com/diegoami/imperial-conquest-2-research/issues/37),
conquest [#99](https://github.com/diegoami/ic2-conquest/issues/99), built on the
semantic atlas of conquest #107
([`2026-10-21-original-sav-semantic-atlas.md`](2026-10-21-original-sav-semantic-atlas.md),
increments 3–11, ledger
[`field-map-v12.csv`](../runs/experiments/data/run-exp-sav-atlas107/field-map-v12.csv)).

## The question

[`2026-10-21-sav-export37-current-gates-and-input-preflight.md`](2026-10-21-sav-export37-current-gates-and-input-preflight.md)
lists four gates before native JSON saves can be converted to original SAVs.
Gate 2 asks for:

- the UNKNOWN fields and their dependencies, or a refusal policy for the
  states the exporter does not support;
- when the historical profile applies;
- how to write new records, inactive records, text, relocated records and
  carried armies.

This finding answers gate 2. It does not touch gates 1, 3 and 4 (below).

## Answer

There are no UNKNOWN fields left: the ledger has 79 CONFIRMED, 31 CONTEXTUAL
and 3 INERT rows. The policy below says what an exporter writes for each kind
of field. `scripts/sav_export_policy_check.py` checks a candidate SAV against
it.

### 1. The 31 former UNKNOWN bytes (now INERT)

Nation `+450..46A`, `+46D`, `+491..493`. No instruction of the program
reads or writes them, except the whole-record serializer and record copies
(increment 3: machine-code index, displacement scan; increment 4: native
check, crafted values survive play and are never used).

- **Write:** carry them from the source save. Without a source, write zero.
  Every original New Game produces zero there.
- **Checker:** `inert_bytes_carried_or_zero`.

### 2. A new army

The constructor `FUN_00449F08` writes 96 of 656 bytes. The other 560 are
never read while the slot is empty (increment 5).

- **Write:** the 16-byte header, and for each live slot all five fields
  (type, label, quality, troops, name). Slots are packed: no live slot after
  an empty one. Troops ≥ 0.
- **Empty slots:** zero all 32 bytes. Not because the original does (it keeps
  whatever was at that index), but because no reader can see them, and zero
  is the one value that does not invent history.
- **Checker:** invariants `slots_packed`, `slot_troops_nonnegative`; rule
  `empty_slots_zero` (from-scratch exports).

### 3. A new fleet under construction

The order `FUN_0044A004` writes 10 of 26 bytes. **Native:** a leftover
`moves` value at the fleet's index survives launch and is usable on the
owner's next turn (increment 6, T5: 17 against 0 in the control).

- **Write:** `moves` = 0 and route x = −1 (route y is not read when x is −1).
  Countdown even 0..24, building city 0..333.
- **Checker:** rule `building_fleet_moves_0_route_x_minus1`, invariants
  `fleet_countdown`, `fleet_building_city`.

### 4. Deleted records (tombstones)

The original compacts armies (`FUN_0044ABE0`) and fleets (`FUN_0044AD7C`) by
moving the last record into the hole; the count drops and a stale copy stays
past it (increment 6, T4).

- **Write:** no tombstones. Write only live records, and the count to match.
- **Refuse:** a source state with tombstones that would be carried over. Two
  native-evidence saves hold tombstoned armies that still have troops
  (increment 5's correction); the policy does not represent them.
- **Checker:** rules `no_army_tombstones`, `no_fleet_tombstones`.

### 5. Record order and relocation

Order matters to the game: a rebellion goes to the last qualifying army in
table order, and the at-war branch to the highest-index war army in range
(increment 10; g4 (H)). Moving a record changes the indices that point at it.

- **Write:** keep the source order of armies and fleets. When a record must
  move, update every index that names it. In ledger v12 the only stored army
  indices are `FLEET.army` (the cargo) and the battle block's attacker and
  defender, which the policy refuses (point 10); no field stores a fleet
  index.
- **Not covered by the checker:** order equivalence with a source. The
  checker sees one file; the exporter's tests must compare orders.

### 6. Carried armies

**Native** (increment 9): an army aboard a fleet stands on the fleet's tile,
with cell −1; the fleet's `army` field holds the army's index; the map shows
the fleet, not the army.

- **Write:** all three together, or none.
- **Checker:** invariants `aboard_link_army_side`, `aboard_link_fleet_side`;
  rule `carried_army_on_fleet_tile`.

### 7. Text

Every reader stops at the NUL (StrCopy, StrCat, StrComp, `0x403458`;
increment 5). The bytes after it are never interpreted.

- **Write:** the name, a NUL, then zeros to the end of the buffer (city 14,
  nation name 11, leader 27, unit name 24, news 61 bytes). Latin-1.
- **Checker:** rule `text_tails_canonical` (from-scratch exports) covers
  city, nation, leader and live unit names; news text is not checked.

### 8. History and the historical profile

- **`CITY.allegiance` drives play** (defence, capture loyalty, defection,
  rebellion and revival; increments 5, 8, 10, 11, all branches observed
  natively with research's g4 follow-ups). It cannot be derived from the
  owner. **Write:** the campaign's own allegiance; for a campaign from the
  DAT scenario, the DAT value. **Refuse** a save that has no allegiance for
  its cities.
- **`wealth0`, `treasury0`, `cities0`, `conqueror` are shown only** (the
  leader-falls screen and the nation status; increment 5). **Write:** the
  campaign's own values, or the DAT profile. They change no play.
- **`NATION.cities` of an eliminated nation is stale in the original**
  (25 of 25 cases; increment 7). Write the list length, or carry the stale
  value; the checker allows both.

### 9. Derived fields

Write them from the records, never from a stale source:

- city list = the owned cities, in byte order of the names (`FUN_0044B8F4`);
  `NATION.cities` = its length for a live nation; the capital is owned;
- map markers: city (20 + owner + 16 × variant), army (200/216/232 + owner by
  troops), fleet (300/316/332 + owner by ships). An army band that the
  original has not refreshed yet is allowed (17 of 362 armies; increment 7).

**Checker:** every invariant of `scripts/sav_atlas_invariants.py`, with two
allowed drifts (`army_marker_band_current`, `city_count_eliminated`).

### 10. States outside the policy (refused)

- an open tactical battle (the battle block);
- tombstones (point 4);
- any invariant violation other than the two allowed drifts;
- a campaign with no allegiance profile.

## The checker

```
python3 scripts/sav_export_policy_check.py CANDIDATE.SAV [--source ORIGINAL.SAV] --out RECEIPT.json
```

- Without `--source` (a from-scratch export), every rule binds.
- With `--source`, the residue rules (text tails, empty slots, building-fleet
  leftovers) are reported but not required: the original writes such
  residue itself, so carrying it is faithful. INERT bytes must then equal the
  source's.
- The receipt holds rule results, counts and indices, never field values.
  Exit 1 when the candidate is refused.

Test: `python3 -m tests.test_sav_export_policy_check` (7 cases, no saves).

**Receipts** ([`export-policy-v2/`](../runs/experiments/data/run-exp-sav-atlas107/export-policy-v2/)):

| Input | Mode | Result |
|---|---|---|
| 14 public saves in `saves/` (e.g. `run0-start-AUTO0720-seed12345.SAV`, turn 0720; `fleet-split-antium-0734.SAV`, turn 0734) | identity (source = itself) | 14/14 accepted |
| the same 14 | from scratch | 14/14 refused, only for text tails and empty-slot residue, which the original keeps |
| private bundle, 3 source saves | identity | 3/3 accepted |
| private bundle, 23 native-evidence saves | identity | 21 accepted; 2 refused for tombstoned armies (`N2E68B2.SAV`, `N2R68B2.SAV`) |
| private bundle, 16 research40 saves | identity | 16 refused for the battle block |

So the policy accepts every original-written save without a battle or a
tombstone, and refuses exactly the states it does not represent.

## What gate 2 does not settle

- **Native acceptance of a from-scratch export.** No SAV written by an
  exporter has been loaded by the original yet; that is gate 4.
- **Whether the owner can spend leftover fleet moves on the launch turn**
  (increment 6). The policy writes 0, which avoids the question.
- **Order equivalence** between a native JSON save and the SAV: the JSON
  must carry an order, or the exporter must define one and say so.
- **The eliminated nation's stale count**: which value the original would
  show after the exporter writes the true length has not been run.

## Other gates (not this finding)

1. The exact twelve-input manifest: the owner's private inputs.
2. *This finding.*
3. An independent review of T185 (format-4 migration and native export
   bridge): in the remake repository, not reachable from here.
4. Native Windows round trips of the actual exports: the owner's machine.

No game was run for this finding, no SAV was written, and no owner file was
read.
