# FUN_0044ebe8 and FUN_0044e84c: capital distance 10 and offer distance 20 are both outside; ties follow the city table and the pool table

**Tag:** [confirmed] by executing the original instructions on controlled synthetic states. Each answer is also checked
against remake main's helpers on the same states.
**Task:** research [#144](https://github.com/diegoami/imperial-conquest-2-research/issues/144) (remake #1640), delegated
2026-10-30. It follows §4 of `2026-10-30-ai-decisions-vs-remake-main.md`, which was a code reading only.
**Remake compared:** main `10d3bb81`.

## Answers

| Question | Original (executed) | Remake main `10d3bb81` (executed) |
|---|---|---|
| (a) EBE8: does an own army at capital distance exactly **10** count as "near the capital"? | **No.** 9 → nearest city; 10 and 11 → the capital (`cmp ax,0xa; jge` at 0x44EC3F, i.e. `< 10`) | **Yes.** 10 → the nearest city (`<= GarrisonFallbackCapitalDistance`) |
| (b) E84C: is an offer at distance exactly **20** taken? | **No.** 19 → taken; 20 and 21 → no walk (`cmp ax,0x14; jge` at 0x44E884, i.e. `< 20`); in a 19-vs-20 pair, 19 in both slot orders | **Yes.** 20 → taken (`distance > MercenaryRunOfferRange` skips, i.e. `<= 20`); 21 → none |
| (c1) EBE8 equal-distance nearest cities | the **city record table** (0x479590, 334 × 34 bytes): the first record wins (strict `<`) | **city id** ascending (`FirstReachableCity`, `CompareOrdinal`) |
| (c2) E84C equal-distance offers | the **mercenary pool table** (records 201–250 of 0x49D0A4, 12 bytes each): the first slot wins (strict `<`), whatever city record holds the offer | **city id** ascending, whatever the slot (`MercenaryRunDestination`) |

## The helpers and tables, from the pinned listing

**FUN_0044ebe8 (garrison fallback), argument AX = army:**
1. **Near-capital test.** For every army record (0x47C1EC + 0x290·i, count at 0x4A0324) whose owner (+4) is the current
   nation (0x4A0320): Chebyshev `FUN_00449018(army, capital) < 10` sets a flag. The capital is city `474AB4[nation]`; its
   position is `0x47959E + 34·idx`.
2. **Flag clear** → `FUN_0044dba8(army, capital)` (0x44EC7D).
3. **Flag set** → a loop over all **334 city records** in table order, with no owner or other gate. The best starts at 1000
   with strict `<`, so the first record at the minimum distance wins. Then `FUN_0044dba8(army, that city)` (0x44ECD6).

**FUN_0044e84c (mercenary run), argument AX = army:**
1. A loop over pool records 201–250: position at +0, live word at +8 (> −1).
2. Skip an offer unless `FUN_00449018(army, offer) < 20`.
3. `FUN_004498d8(offer position)` returns the city **at exactly that position**: the first such record in city-table
   order, or −1. It is not the nearest city.
4. Skip the offer when `relation(nation, that city's owner) >= 3`.
5. Keep the strict minimum distance (best starts at 1000), so the first slot at the minimum wins.
6. `FUN_0044dba8(army, offer)` (0x44E913).

The other helpers: `FUN_00449018` = max(|dx|, |dy|) (through `FUN_00448fd8`); `FUN_00448fd0` = min.

**Ambiguities, reported first:**
- **EBE8 has no capital guard.** With `474AB4[nation] = −1` it reads "city record −1", the bytes before the table. In the
  control it walks to (153,48). Remake main returns `null` (no capital) and falls to its #925 emergency tier.
- **E84C has no `FUN_004498d8 = −1` guard.** An offer not standing on a city would take its owner from record −1. Not
  exercised here: every control offer stands on a city.
- **EBE8's nearest-city loop has no eligibility gate.** A "no eligible city" control does not exist in this domain: no
  city can be 1000 away on a 320 × 140 map. This is a code reading only.

## Method

- **Original:** `runs/experiments/boundary144/controls.py`.
  - Unicorn on the pinned EXE with the #187 RAM snapshot, through `runs/experiments/navigation187/core.py`.
  - Each control writes its inputs into a copy of the snapshot, runs the routine with EAX = the army, and **stops at
    `FUN_0044dba8`'s entry**. The walk's EDX is the choice; nothing after it runs.
  - No RNG draw, the snapshot copy is unchanged by the routine (read-only check), and no presentation code is reached.
  - Synthetic base: current nation 1 (Carthage), deciding army record 3; the other own armies at (300,10); every city
    except the ones a control places at (319,139); every pool slot dead.
  - Ties use city records 1 (`olisipo`) and 3 (`ebora`), whose native ids sort the other way. The remake's city list is
    in record order (`city-record-ids.json`, matched by position, 334 of 334).
- **Layouts:**
  - **v1:** the capital in place; the nearest city 1 cell beyond the army.
  - **v2 (`--layout land`):** a free land strip of the snapshot's map, (60..77, 20) plus the column (68, 20..31). The
    capital is moved to (60,20), the nearest city sits 3 cells beyond the army, and the tie cities 2 either side.
  - The original gives the same answers in both. v2 exists because remake main's `GarrisonFallback` applies the owner's
    retained #925 reachable policy (`IsUsableDestination`) and returned `null` for every v1 state, where cities lie on
    sea or 1 cell away. On v2 that policy passes, so the literal comparison and the id tie-break are visible.
  - The v2 absent-capital row's label says "20 from the old capital"; in v2 the army stands 8 away.
- **Remake:** `difftest/remake_adapter/HelperProbe.cs` (`RemakeAdapter helperprobe <remake> BASE.SAV <out> [layout=land]`)
  builds the same states from the imported BASE.SAV and calls `GarrisonFallback` and `MercenaryRunDestination`. No turn
  is played.

## Scalar matrix (layout v2 for EBE8; E84C needs no terrain)

| Control | Inputs | Original | Remake main |
|---|---|---|---|
| EBE8 d=9 | army (69,20), capital (60,20), city (72,20) | (72,20): nearest city | (72,20) |
| EBE8 d=10 | army (70,20), city (73,20) | **(60,20): capital** | **(73,20): nearest city** |
| EBE8 d=11 | army (71,20), city (74,20) | (60,20): capital | (60,20) |
| EBE8 capital −1 | army (68,20), city (71,20) | (153,48): the bytes before the table | `null` |
| EBE8 tie | army (68,20); record 1 at (66,20), record 3 at (70,20); other own army 1 from the capital (68,31) | **(66,20): record 1** | **(70,20): `ebora`** |
| EBE8 tie, positions swapped | record 1 at (70,20), record 3 at (66,20) | **(70,20): record 1** | **(66,20): `ebora`** |
| E84C single | army (60,70), offer slot 201 on an own city at 19 / 20 / 21 | taken / **none** / none | taken / **taken** / none |
| E84C pair | 19 at (79,70), 20 at (40,70), either slot order | 19 | 19 |
| E84C tie at 5 | A (65,70), B (55,70); slots 201/202 and records 1/3 swapped independently (4 states) | **slot 201** in all 4 | **`ebora`** in all 4 |

Layout v1 gives the same original answers. Remake main's `GarrisonFallback` gives `null` in v1 for the reason above;
its E84C rows are the same as in v2.

## Literal rule vs retained policy

`GarrisonFallback` = the literal EBE8 branch plus `FirstReachableCity`, which applies the owner's #925 reachable policy. In
v2 the policy accepts every candidate, so the two differences in the table are **literal**:
- the `<=` radius;
- the id tie-break inside `FirstReachableCity`.

`MercenaryRunDestination` has no reachability step, so its two differences are literal too:
- the `<=` range;
- the id tie-break.

Nothing here touches the #925 policy itself.

## What this does not establish

- No campaign, native-Windows or in-play parity claim. These are synthetic states on one snapshot.
- Any other city or scorer tie: the enemy scorers and fleet port are separate settled contracts.
- What the original does with an offer not on a city (record −1 owner), beyond the code reading.
- No production patch.

## Evidence

- Data: `runs/experiments/data/run-exp-boundary144/`
  - `controls-v1.json`, `controls-v2.json`: the original;
  - `native-10d3bb81-v1.jsonl`, `native-10d3bb81-v2.jsonl`: remake main;
  - `city-record-ids.json`.
- Code:
  - `runs/experiments/boundary144/controls.py`;
  - `difftest/remake_adapter/HelperProbe.cs` (+ `Program.cs` dispatch).
- Private and not published: the #187 RAM snapshot and the EXE. They are referenced by path in `core.py` and are not
  copied into this repository.
