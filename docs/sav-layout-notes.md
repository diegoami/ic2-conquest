# SAV layout notes (for the Python parser)

Condensed from the research repo `diegoami/imperial-conquest-2-research` at commit `60475a30`. Sources, all in `docs/reports/`:

- decompiled-sav-file-layout.md
- impconq2-full-save-analysis.md
- army-records-and-roman-roster.md
- fleet-owner-field-confirmed.md
- nation-tax-base-and-city-economy-fields.md
- mercenary-pool-record.md

Corrections from later reports are folded in, and each one is cited where it applies.

**Tags.** **[C]** means confirmed by the save/load code (`FUN_004484D0` save, `FUN_004487C4` load) and/or checked on saves. **[D]** means derived. **[?]** means unknown.

**Conventions.**

- Every multi-byte field is little-endian.
- A field is a **signed int16** unless it is marked otherwise.
- The sentinel `0xFFFF` is `-1`.
- Offsets are in bytes.
- `A` is the army count and `F` the fleet count.

**Whole-file check** **[C: 54 of 54 saves]** (news-log-format-and-messages.md, upkeep-payment-and-desertion.md):

```text
len(file) = 100956 + 2 + A*656 + 2 + F*26 + 18752 + 600 + 2 + (newsIndex+1)*61 + 55     (battle flag 0)
```

This was also re-checked for this note on the 54 fixture saves in `imp_conquest_fixtures`: 0 mismatches **[P]**.

## Block sequence

| # | Block | Offset | Size | Notes |
|---:|---|---|---|---|
| 1 | Map grid | 0 | 89,600 | 320 × 140 int16, column-major |
| 2 | City table | 89,600 (`0x15E00`) | 11,356 = 334 × 34 | Ends at 100,956 (`0x18A5C`) |
| 3 | Army count `A` | 100,956 | 2 | int16. Max 198 armies in memory (`< 0xC6`) |
| 4 | Army records | 100,958 (`0x18A5E`) | A × 656 | |
| 5 | Fleet count `F` | `off_f = 100958 + A*656` | 2 | int16 |
| 6 | Fleet records | `off_f + 2` | F × 26 | |
| 7 | Nation table | `off_n = off_f + 2 + F*26` | 18,752 = 16 × 1,172 | Record index = nation code |
| 8 | Mercenary pool | `off_m = off_n + 18752` | 600 = 50 × 12 | Fixed size |
| 9 | News index | `off_m + 600` | 2 | int16 `newsIndex` (−1 empty … 39 full) |
| 10 | News slots | `off_m + 602` | (newsIndex+1) × 61 | Variable size |
| 11 | Trailer | `off_t = off_m + 602 + (newsIndex+1)*61` | 55 | Normally `len − 55` |
| 12 | Battle block | `off_t + 55` | 2,105 | Present only if the battle flag is set |

Notes on the blocks:

- **Block 2:** the city table is the same layout as the DAT's city table.
- **Block 3:** the army count includes tombstones.
- **Block 8:** see decompiled-sav-file-layout.md and mercenary-pool-record.md.
- **Block 10:** see news-log-format-and-messages.md.
- **Block 12:** the battle block is `2+2+2+1+2+1760+336` bytes. It is never present in a normal save (decompiled-sav-file-layout.md). The battle-lab build writes such saves (2026-09-28-battle-minigame-headless-feasibility.md). A robust parser takes the trailer at `off_t`, not at `len − 55`.

**Reconciliation with `state/queues.py`.**

- `MAP=89600`, `CITY=11356`, and the army count as a u16 at `MAP+CITY` all match.
- So do 656-byte armies, the fleet count, 26-byte fleets, 16 nations × 1,172 and the recruitment block at nation `+0x2E4`, 40 × 8 bytes of `<4h`.
- **Signedness:** read the counts as int16. The counts are small, so the result is the same as u16.
- **Tombstones:** mid-turn saves can contain tombstoned records (owner −1) inside the army and fleet tables. They are counted in `A` and `F` and must be skipped, not treated as corruption (battle-replayed-rout-mechanic-and-combat-constants.md).
- `dat_queues()` (DAT nation table at `0x1B100`, stride `0x41F`, recruitment at `+0x2C9`) also matches (2026-09-29-new-game-recruitment-queues-come-from-the-dat.md).

## 1. Map grid (0 … 89,599)

**Layout.** The word for tile `(x, y)` is at `2 * (x*140 + y)`, for `x ∈ [0,320)` and `y ∈ [0,140)` **[C]** (map-layout.md). The in-memory column stride is `0x118` = 280 bytes (decompiled-elimination-cleanup.md).

**Terrain codes** **[C]** (terrain-move-cost-table-in-dat.md, decompiled-map-code1-overlay.md):

| Code | Terrain | Move cost |
|---:|---|---:|
| 0 | calm sea | 1 |
| 1 | rough sea (weekly weather overlay; never present in the DAT) | 3 |
| 2 | plain | 1 |
| 3 | desert | 1 |
| 4 | forest | 2 |
| 5 | mountains | 4 |
| 6–11 | river (six shapes) | 4 |

**Overlay markers** **[C]** (decompiled-unit-map-orders-and-record-fields.md, rivers-and-map-markers.md):

- **City:** `20 + owner + 16*variant`, with variant 0–4, so codes 20–99.
- **Army:** `owner + (troops<25000 ? 200 : troops<50000 ? 216 : 232)`, so codes 200–247.
- **Fleet:** `owner + (ships<25 ? 300 : ships<50 ? 316 : 332)`, so codes 300–347.
- **Owner:** `(code − 200) % 16` for an army and `(code − 300) % 16` for a fleet.

**Terrain under a marker.** The terrain beneath an army or fleet marker is stored in that record's covered-cell field (army `+8`, fleet `+24`). An embarked army has no marker.

## 2. City record (334 × 34 bytes, from 89,600)

Base for city `i`: `89600 + 34*i`. The same layout is at DAT `0x15E00`, and in memory at `0x00479590`, stride `0x22`.

| Off | Hex | Type | Field | Source |
|---:|---:|---|---|---|
| 0 | 0x00 | char[14] | Name, NUL-padded | [D] name length; the longest city name is 13 characters (news-log-format-and-messages.md); names parse cleanly [P] |
| 14 | 0x0E | i16 | x | [C] decompiled-quarterly-rebellion.md |
| 16 | 0x10 | i16 | y | [C] same |
| 18 | 0x12 | i16 | owner (nation code) | [C] rome-city-recruitment-and-nations.md, rome-tax-increase-and-sidon-capture.md |
| 20 | 0x14 | i16 | allegiance (nation code) | [C] same. Changes only via the loaders |
| 22 | 0x16 | i16 | loyalty (0–99) | [C] tier string `names[loyalty/10]` (decompiled-unit-map-orders-and-record-fields.md) |
| 24 | 0x18 | i16 | supplies, tons (cap `pop*10`) | [C] controlled-army-supply-transfer.md, city-population-growth.md |
| 26 | 0x1A | i16 | fortification (see below) | [C] decompiled-unit-map-orders-and-record-fields.md |
| 28 | 0x1C | i16 | population, thousands | [C] nation-tax-base-and-city-economy-fields.md |
| 30 | 0x1E | i16 | maximum population, thousands | [C] same |
| 32 | 0x20 | i16 | tribute, talents | [C] same |

**Fortification encoding.** A value of 100 or less is the fortification percentage. A value above 100 means an order is in progress: `pendingPoints*100 + current`.

**Derived values** **[C]**:

- The city's contribution to the tax base is `tribute*pop/maxPop`.
- A capital is any nation's `+0x444`.
- The "(N)" troop count beside fortification in the UI is the sum of the owner's recruitment-slot troops at this city. It is not stored in the city record (city-units-army-transfer-and-mercenaries.md).

## 3. Army record (656 bytes)

Base for army `a`: `100958 + 656*a`. In memory it is at `0x0047C1EC`, stride `0x290`.

| Off | Type | Field | Source |
|---:|---|---|---|
| 0 | i16 | x | [C] army-records-and-roman-roster.md |
| 2 | i16 | y | [C] same |
| 4 | i16 | owner nation code. **−1 = tombstone** (deleted; compacted later by moving the last record into the hole) | [C] same; decompiled-elimination-cleanup.md |
| 6 | i16 **signed** | moves remaining this turn (see below) | [C] army-moves-field-signed-and-the-ffff-underflow.md |
| 8 | i16 | covered map cell = terrain code under the marker. **−1 = aboard a fleet** | [C] decompiled-unit-map-orders-and-record-fields.md (corrects the old "morale" label) |
| 10 | i16 | supplies, tons | [C] controlled-army-supply-transfer.md |
| 12 | i16 | money (the army purse), capped at 1,000 by the dialogs | [C] army-records-and-roman-roster.md, decompiled-unit-map-orders-and-record-fields.md |
| 14 | i16 | morale, strategic, 51–70 in normal play | [C] supply-driven-morale-and-fleet-attrition.md (corrects "unknown" and "experience") |
| 16 | 20 × 32 | unit slots; slot `k` is at `16 + 32*k` | [C] army-records-and-roman-roster.md |

**Moves (`+6`).**

- The weekly value is `10 − min(5, troops div 20000)`, and one less when supply is below 10 %.
- `0xFFFF` is −1 from an underflow bug in the original; it is not a sentinel.

**Morale (`+14`).**

- The panel's tier is `(v−51)>>2`.
- A new army starts at 59.
- A computer-controlled side gets `+3` when it enters a battle.

**Unit slot (32 bytes, at `army + 16 + 32*k`):**

| Off | Type | Field | Source |
|---:|---|---|---|
| 0 | i16 | origin label: **0 = regular**; 1–51 = mercenary, and an index into the ethnic name table | [C] decompiled-mobilization-and-mercenary-restock.md, decompiled-mercenary-offer-list-and-position.md |
| 2 | i16 | unit type: 0 light infantry, 1 heavy infantry, 2 archers, 3 light cavalry, 4 heavy cavalry | [C] army-records-and-roman-roster.md, rome-city-recruitment-and-nations.md |
| 4 | i16 | troops. **≤ 0 = empty slot** (the name may remain) | [C] army-records-and-roman-roster.md, upkeep-payment-and-desertion.md |
| 6 | i16 | quality: 4 very poor, 5 poor, 6 average, 7 good, 8 very good, 9 elite (0–3 never seen on a live unit) | [C] army-records-and-roman-roster.md, decompiled-mobilization-and-mercenary-restock.md |
| 8 | char[24] | name, NUL-terminated | [C] army-records-and-roman-roster.md |

**Mercenary label names** are at DAT `0x1F8C6`, 52 entries of 20 bytes: `0 Regular`, `11 Gallic`, `35 Egyptian`, and so on (decompiled-mercenary-offer-list-and-position.md).

**Regular unit names** follow `"<ordinal> <Foot|Guards|Bowmen|Lancers|Dragoons>  Battalion"`. Double spaces are real and are present in the saves **[P]** (ptolemy-run-ui-inventory-and-leader-draw.md).

**Slots are packed.** Removing a unit swaps the last occupied slot into the hole, and new units go at the last occupied slot + 1, so treat `troops > 0` as occupied (upkeep-payment-and-desertion.md, decompiled-mobilization-and-mercenary-restock.md).

**Derived values** **[C]**:

- Total troops `T = Σ troops` over all 20 slots. The code floors it at 1.
- The supply percentage is `supplies*10000 div T`.
- Automatic supply capacity is `T div 100`; the dialog capacity is `T div 100 + 1`.
- Quarterly regular cost is `Σ(troops div 200)*price[type]` over slots with label 0.
- Quarterly mercenary pay is `Σ((troops div 200)*price*quality) div 5` over slots with label ≠ 0 (decompiled-unit-map-orders-and-record-fields.md, supply-capacity-rounding.md).

## 4. Fleet record (26 bytes)

Base for fleet `f`: `off_f + 2 + 26*f`. In memory it is at `0x0049C26C`, stride `0x1A`.

| Off | Type | Field | Source |
|---:|---|---|---|
| 0 | i16 | x. **(0,0) = under construction** (not on the map) | [C] fleet-order-at-caere.md, decompiled-unit-map-orders-and-record-fields.md |
| 2 | i16 | y | [C] same |
| 4 | i16 | reset to −1 at the top of every fleet's turn; meaning unknown [?] | [C] supply-driven-morale-and-fleet-attrition.md |
| 6 | i16 | unknown [?]. Position-shaped (0, 77, 65 …); not morale | supply-driven-morale-and-fleet-attrition.md, fleet-owner-field-confirmed.md |
| 8 | i16 | owner nation code. **−1 = tombstone** | [C] fleet-owner-field-confirmed.md, decompiled-elimination-cleanup.md |
| 10 | i16 | construction countdown (see below) | [C] decompiled-unit-map-orders-and-record-fields.md |
| 12 | i16 | moves | [C] same |
| 14 | i16 | supplies, tons (capacity `ships*8`) | [C] same, supply-capacity-rounding.md |
| 16 | i16 | money (purse) | [C] decompiled-unit-map-orders-and-record-fields.md |
| 18 | i16 | ships | [C] fleet-order-at-caere.md |
| 20 | i16 | **dual**: build-city index while under construction (`+10 ≥ 0`); **condition %** (0–100) once launched | [C] decompiled-unit-map-orders-and-record-fields.md (corrects the `CityIndex` label in fleet-order-at-caere.md and field-recruitment-uniform-attrition-and-fleet-drift.md) |
| 22 | i16 | index of the carried army. **−1 = none** | [C] same |
| 24 | i16 | covered map cell. **1 = on rough sea** (storm damage is tripled) | [C] decompiled-map-code1-overlay.md |

**Construction countdown (`+10`).**

- It is 24 when the fleet is ordered and falls by 2 per turn.
- **−1 = launched and on the map.**
- On launch the fleet gets condition 100, supplies 50, money 0 and a covered cell of 0.

**Observed** **[P]**: under-construction fleets read `+4 = −1` in `1_rome_270_winter_7.sav`. fleet-order-at-caere.md saw 0 on an order saved before any tick.

## 5. Nation record (16 × 1,172 bytes)

Base for nation `n`: `off_n + 1172*n`. The SAV writes the whole in-memory record (at `0x00474670`, stride `0x494`), so the SAV offsets equal the in-memory offsets **[C]** (nation-tax-base-and-city-economy-fields.md, decompiled-diplomacy-peace-terms-and-instant-battles.md).

**Nation codes:**

| Code | Nation | Code | Nation |
|---:|---|---:|---|
| 0 | Rome | 8 | Celtiberia |
| 1 | Carthage | 9 | Illyria |
| 2 | Seleucid | 10 | Dacia |
| 3 | Ptolemaic | 11 | Bithynia |
| 4 | Macedonia | 12 | Galatia |
| 5 | Numidia | 13 | Armenia |
| 6 | Gaul | 14 | Media |
| 7 | Greece | 15 | Thracia |

Source: rome-city-recruitment-and-nations.md.

| Off (hex) | Type | Field | Source |
|---:|---|---|---|
| 0x000 | char[11] | name | [C] ptolemaic-player-and-week9.md |
| 0x00B | char[27] | leader name (drawn at New Game) | [C] decompiled-diplomacy-peace-terms-and-instant-battles.md (corrects "34 bytes"); ptolemy-run-ui-inventory-and-leader-draw.md |
| 0x026 | i16[16] | relation to nation `j` (see below) | [C] decompiled-diplomacy-peace-terms-and-instant-battles.md |
| 0x046 | u16 | neighbour mask: bit `j` means borders nation `j`. Loaded from the DAT; changed only by conquest | [C] dat-neighbour-mask.md |
| 0x048 | i16[334] | the nation's city list, **0xFFFF-terminated** (668 bytes) | [C] decompiled-quarterly-rebellion.md, dat-neighbour-mask.md; parsed [P] |
| 0x2E4 | 40 × 8 | recruitment slots: `{i16 state, i16 type, i16 troops, i16 city}` | [C] decompiled-mobilization-and-mercenary-restock.md |
| 0x424 | 12 bytes | unknown [?] | [P] only |
| 0x430 | **i32** | wealth = `Σ pop × 3000` (rebuilt quarterly) | [C] nation-tax-base-and-city-economy-fields.md |
| 0x434 | **i32** | wealth (population) at game start (scorecard) | [C] decompiled-diplomacy-peace-terms-and-instant-battles.md; equals `+0x430` at start [P] |
| 0x438 | **i32** | treasury, talents (signed; can be negative) | [C] upkeep-payment-and-desertion.md |
| 0x43C | **i32** | treasury at game start (scorecard) | [C] decompiled-diplomacy-peace-terms-and-instant-battles.md; Gaul reads 315, the DAT start value [P] |
| 0x440 | i16 | unity (displayed as a word). **≤ 0 = dead or eliminated** | [C] decompiled-quarterly-rebellion.md, galatia-elimination-and-city-resupply-confirmed.md |
| 0x442 | i16 | mobilization % (0–100; 50 at nation setup) | [C] decompiled-mobilization-and-mercenary-restock.md |
| 0x444 | i16 | capital city index. **0xFFFF = eliminated** | [C] ptolemaic-player-and-week9.md, galatia-elimination-and-city-resupply-confirmed.md |
| 0x446 | i16 | city count (can be stale after elimination) | [C] same |
| 0x448 | i16 | city count at game start (scorecard) | [C] decompiled-diplomacy-peace-terms-and-instant-battles.md |
| 0x44A | i16 | tax rate % | [C] rome-tax-increase-and-sidon-capture.md |
| 0x44C | i16 | tax base (rebuilt quarterly from cities; adjusted by captures) | [C] nation-tax-base-and-city-economy-fields.md |
| 0x44E | i16 | conquered-by nation (−1 = none) | [C] decompiled-elimination-cleanup.md |
| 0x450–0x46A | — | unknown; zero in the fixtures [?] | — |
| 0x46B–0x48F | — | UI fields written at New Game [?] | [C] decompiled-diplomacy-peace-terms-and-instant-battles.md |
| 0x486, 0x488 | i16 | changed when a human seat was added (45→90, 55→186); meaning unknown [?] | ptolemaic-player-and-week9.md |
| 0x48C, 0x48E | i16 | battle-delay settings (UI) | [C] battle-quality-promotion-and-morale-array-decompiled.md |
| 0x490 | **u8** | human flag: **1 = human, 0 = computer** | [C] ptolemaic-player-and-week9.md, army-moves-field-signed-and-the-ffff-underflow.md |
| 0x491–0x493 | — | unknown or padding [?] | — |

**Relation values (`+0x026`).**

- 0 peace, 1 trade, 2 alliance, 3 war.
- A negative value is a cooldown.
- The matrix is symmetric, with a zero diagonal.

**Recruitment slots (`+0x2E4`).**

- The list is compacted, with the empty slots last.
- A slot is empty if its troops ≤ 0.
- Slot state 0–24: +2 per tick, capped at 24. Quality on mobilizing is `state/4`.

**Possible colours at `+0x424`** **[P]**. Rome reads `80 00 80 00 ff ff ff 00 00 00 ff 00` and Gaul `80 00 00 00 00 ff ff 00 80 80 80 00`. The first 3 bytes match the nation icon colours in rome-city-recruitment-and-nations.md: Rome `#800080`, Gaul `#800000`. This is an unconfirmed guess that the field holds colours; 2026-09-29-nation-marker-colours.md did not locate the colour pairs.

**Derived** **[C]**:

- A nation is dead when unity ≤ 0 or the capital is `0xFFFF`.
- The displayed population is `3 × Σ city pop` (ptolemaic-player-and-week9.md).
- `+0x44C` equals `Σ (tribute*pop/maxPop) << 2` right after a quarterly tick (nation-tax-base-and-city-economy-fields.md).

## 6. Mercenary pool (50 × 12 bytes, at `off_m`)

Base for slot `s`: `off_m + 12*s`. This is the in-memory live pool at `0x0049DA10`, records 201–250 of the template table **[C]** (mercenary-pool-record.md, decompiled-mercenary-offer-list-and-position.md, decompiled-new-game-mercenary-fill.md).

| Off | Type | Field |
|---:|---|---|
| 0 | i16 | x of the offer's city tile |
| 2 | i16 | y |
| 4 | i16 | label (ethnic name index, 1–51) |
| 6 | i16 | unit type 0–4 |
| 8 | i16 | troops. **−1 (0xFFFF) = empty** |
| 10 | i16 | quality 5–9 |

- An empty slot keeps a stale `(x, y)`. Slots never filled read `(0,0,0,0,−1,0)`.
- Always test `troops >= 0` before using a slot.
- The templates are not in the SAV. They are at DAT `0x1FCD6`: 201 templates plus 50 empty live slots, 12 bytes each.

## 7. News log (at `off_m + 600`)

**[C]** (news-log-format-and-messages.md)

- **Index:** an i16 `newsIndex`, the index of the newest slot. It is −1 when the log is empty, 26 in a fresh game and 39 when full.
- **Slots:** `newsIndex + 1` slots of 61 bytes each.
- **Slot format:** a NUL-terminated single-byte string of at most 60 characters. Stale bytes after the NUL are kept.
- **Order:** slot 0 is the oldest. When the log is full, a new line shifts every slot down by one.
- **Headers:** the lines `" "` and `"Week  N      Season      YYYBC"` are ordinary entries, written at the end of each round.
- **Parsing:** the log is useful for events such as "falls to", "defects from", "destroys army of", "lost at sea", "declares war on", "sues … for peace" and "pays reparations of 2,269 talents" (the amount has a comma thousands separator).
- **Not in the log:** offer dialogs ("wants to trade") never appear here.

## 8. Trailer (55 bytes, at `off_t`)

**[C]** (news-log-format-and-messages.md, decompiled-turn-and-calendar-sequencing.md, pending-offer-block-army-split-and-naupactus.md). Values were checked for this note on `1.sav` **[P]**.

| Off | Type | Field |
|---:|---|---|
| 0 | i16[16] | turn order: the nation code at each seat position (shuffled at New Game) |
| 32 | i16 | pending offer: proposing nation (−1 = none) |
| 34 | i16 | pending offer: type (1 = trade, 2 = alliance) |
| 36 | i16 | current nation (the seat whose turn it is) |
| 38 | i16 | turn-order index of the current seat (0–15) |
| 40 | i16 | week (1, 3, 5, 7, 9, 11) |
| 42 | i16 | year BC (starts at 270, counts down) |
| 44 | i16 | season (0 Spring, 1 Summer, 2 Autumn, 3 Winter) |
| 46 | 8 bytes | main-window geometry (UI state, not the calendar) |
| 54 | u8 | battle-in-progress flag (0 in normal saves; see block 12) |

Example: `1.sav` has current nation 0 and index 7, which is week 1, 270 BC, Spring **[P]**.

**Autosaves and seat order.** `AUTOnnnn.SAV` is written at the start of a human turn, so its current nation is the human seat (2026-09-28-autosave-hook-feasibility.md). The seats at index `< idx` have already moved this round.

## 9. DAT offsets a parser may also need

These are from the DAT, not the SAV, but a parser needs them for static tables. All **[C]**.

| DAT offset | Size | Content | Source |
|---|---|---|---|
| `0x0` | 89,600 | map grid (as SAV block 1) | map-layout.md |
| `0x15E00` | 334 × 34 | city table (as SAV block 2) | map-layout.md |
| `0x1B100` | 16 × 1,055 (`0x41F`) | DAT nation record (see below) | 2026-09-29-new-game-recruitment-queues-come-from-the-dat.md, dat-neighbour-mask.md; word order verified [P] |
| `0x1F2F0` | 5 × 40 | unit-type table (see below) | unit-type-stat-table-in-dat.md |
| `0x1F3B8` | 25 × i16 | melee type matrix `M[attacker][defender]`, row-major | combat-type-effectiveness-matrix.md |
| `0x1F622` | 12 × 14 | terrain table: `char name[12]`, `i16 moveCost` | terrain-move-cost-table-in-dat.md |
| `0x1F6CA` | 10 × 11 | quality names (0–3 "not ready" … 9 "elite") | decompiled-mobilization-and-mercenary-restock.md |
| `0x1F7D8` | 4 × 10 | season table: `char name[8]`, `i16 value` (50/80/80/20) | supply-driven-morale-and-fleet-attrition.md |
| `0x1F876` | — | 20 weather sea-region centres | decompiled-map-code1-overlay.md |
| `0x1F8C6` | 52 × 20 | mercenary label names | decompiled-mercenary-offer-list-and-position.md |
| `0x1FCD6` | 251 × 12 | mercenary templates (0–200) and empty live slots (201–250) | decompiled-new-game-mercenary-fill.md |
| `0x21C1A` | 40 × 61 | news seed (new game starts at index 26) | news-log-format-and-messages.md |

**The DAT nation record** (at `0x1B100`, 16 records of `0x41F` bytes) has this layout:

| DAT offset in record | Content |
|---|---|
| `+0x000` | name, 11 bytes |
| `+0x00B` | relation row, 16 × i16 |
| `+0x02B` | neighbour mask, u16 |
| `+0x02D` | city list, 668 bytes |
| `+0x2C9` | recruitment, 40 × 8 |
| `+0x409` | wealth, i32 |
| `+0x40D` | treasury, i32 |
| `+0x411` | unity, i16 |
| `+0x413` | mobilization, i16 |
| `+0x415` | capital, i16 |
| `+0x417` | cities, i16 |
| `+0x419` | tax rate, i16 |
| `+0x41B` | tax base, i16 |
| `+0x41D` | conquered-by, i16 |

**The unit-type table** (at `0x1F2F0`, 5 records of 40 bytes): each record is `char name[16]`, `char abbrev[8]`, then 8 × i16 at `+0x18`:

| Offset | Field |
|---|---|
| `+0x18` | moves |
| `+0x1A` | standard battalion size |
| `+0x1C` | shots |
| `+0x1E` | range |
| `+0x20` | shooting vulnerability |
| `+0x22` | initial price |
| `+0x24` | quarterly price |
| `+0x26` | AI power weight |

The DAT has no army or fleet table in the SAV format. The word at DAT `0x18A5C` is not an army count (army-records-and-roman-roster.md). In practice, new-game armies come from the DAT: Rome's two starting armies are identical in three independent new games **[P]**.
