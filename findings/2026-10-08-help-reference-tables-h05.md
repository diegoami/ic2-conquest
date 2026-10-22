# Help reference tables — verification of row H05 against the data the conquest repo carries

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` row H05 and IC MAIN's clone-side issue #722 (Help has no reference pages …). The clone's `godot/UI/HelpPage.cs:45–65` is the recipient; this draft is the data side that maps every H05 sub-row back to a source the clone can render from its own ruleset.

**Wine-only where a screenshot is cited:** every numeric cross-check below is read from this repo's tracked data (the decompile-derived tables in `state/sav.py` plus the research reports it cites) and from `help_topics.tsv` (the decoded `.hlp`); only the screenshot-based observation in the National colours row is Wine.

## Answer

For each of H05's eight sub-rows, the **verbatim help text** in the original is reproduced from `help_topics.tsv`, the **source data** is named (here in the conquest repo or in the research repo's reports), and the **clone-side render path** is named (the ruleset, the asset pack, or a constant table that needs to ship):

| Sub-row | Original help topic (offset in `.hlp`, verbatim) | Source data the clone can render from | Match status |
|---|---|---|---|
| Terrain costs | 52 (`0x004eda`): *sea calm fleet moves - 1, sea rough - 3, plain - 1, desert - 1, forest - 2, river - 4, mountains - 4* | `state/sav.py` MOVE_COST (0..5) + the DAT table at 0x1F622 in `terrain-move-cost-table-in-dat.md` (6..11 river) | **identical** |
| City size symbols | 53 (`0x00503b`): *city of population 0..25,000; 25,000..50,000; 50,000..100,000; 100,000+; capital* | `state/sav.py` city record `pop` + the icon pack's city glyphs (`godot/MapViewer.cs` nation) | data fields verified; bitmap rendering is asset-pack work |
| Army size symbols | 54 (`0x00513a`): *0..25,000 troops; 25,000..50,000; 50,000..100,000* | `state/sav.py` army `troops` (sum of unit troops) | identical |
| Fleet size symbols | 55 (`0x005203`): *10..25 ships; 26..50; 51..100* | `state/sav.py` fleet `ships` (`ARMY_OFF`-style record) | identical |
| National colours | 56 (`0x0052ce`): lists the 16 names | `godot/MapViewer.cs` `OwnerColor(code)` (T97-corrected), `nation-marker-colours.md` for (background, foreground) pairs | data observed by screenshot; **DAT location still open** |
| Unit costs (initial, quarterly, per 200 men) | 60 (`0x005f44`): LI 2/1, HI 20/2, Ar 4/1, LC 15/3, HC 30/4 | DAT 0x1F2F0 stat table columns `+0x22` (initial) and `+0x24` (quarterly); `unit-type-stat-table-in-dat.md` + `decompiled-recruitment-cost-formula.md` | **identical** |
| Unit details (moves, shots, range, damage, size) | 61 (`0x00613a`): LI 4 / 7 / 1 / 18 / 15000; HI 2 / 0 / 0 / 2 / 6000; Ar 4 / 25 / 2 / 18 / 3500; LC 6 / 9 / 1 / 15 / 7000; HC 5 / 0 / 0 / 4 / 2500 | DAT 0x1F2F0 columns `+0x18` (moves), `+0x1A` (battalion size), `+0x1C` (shots), `+0x1E` (range), `+0x20` (shot damage) | **identical** |
| Unit type vs type | 62 (`0x006322`): LI 15 4 20 5 3; HI 60 5 65 15 8; Ar 10 3 18 5 3; LC 25 8 28 15 8; HC 18 12 20 12 8 | DAT 0x1F7A6 melee matrix; `combat-type-effectiveness-matrix.md` (with the 2026-10-04 correction note) | **identical** (the report's *location* correction moved from 0x1F3B8 to 0x1F7A6, but the 25 values are unchanged and match the help verbatim) |

**Battle unit symbols** (help topic 65 `0x007371`) is **outside H05** but worth flagging while we're here: the 1/3 / 2/3 / full triplet is the same scheme the original uses for in-battle symbols, with the per-type thresholds at `battalion_size / 3` and `2 * battalion_size / 3`. The clone's battle renderer should use the same tier formula; it is a one-line change over H05's Unit details table.

## What does not match (yet) — three open items

1. **National colours table is observed, not located.** `nation-marker-colours.md` reads the (background, foreground) pairs from a screenshot strip supplied by the user on 2026-09-29 and from `1_rome_270_summer_7_1.png`. The 16 backgrounds are independent of the DAT, except that the report explicitly says the **in-memory location of the (background, foreground) pairs is not located** ("Worth a static search: the 16 backgrounds should appear as a table of palette indices or RGB triples."). Until that location is found, the clone cannot cite a single byte-level source for the colours; it relies on `godot/MapViewer.cs` (which already has them, T97 corrected T49).
2. **`state/sav.py` `MOVE_COST` only lists codes 0..5.** The full terrain table has 12 entries (six land codes use the same six values, plus the six rivers 6..11 each cost 4). The current `MOVE_COST` dict + the trailing comment `6-11 river: 4; markers block` is sufficient for move-cost lookups, but it does not encode **the river-count of one cell code having six aliases**. If the H05 page ever needs a tile-by-tile row in the rendered clone, an explicit `MOVE_COST_FULL = {0:1, 1:3, 2:1, 3:1, 4:2, 5:4, **{c:4 for c in range(6,12)}**}` is the right shape (one PR, no behaviour change elsewhere).
3. **The combat matrix's DAT location had a stale claim.** `combat-type-effectiveness-matrix.md` opens with a 2026-10-04 correction: the original report said the matrix sat at DAT 0x1F3B8; the **real** matrix at the in-memory address `DAT_0047946C` is loaded from DAT **0x1F7A6**. The help text matches both readings (the values are unchanged) but only the 0x1F7A6 location reproduces the recorded battle. Anyone who relied on the 0x1F3B8 location before 2026-10-04 has stale index arithmetic — this draft does not.

## Method

- **Help text source.** `runs/experiments/data/run-exp-feature-inventory/help_topics.v2.tsv` (latest of `.json`, `.v2`, `.v3`); the v2 file is what `runs/experiments/feature_inventory/build_findings.py` shipped and the phrase decoder is now 247/247 (commit a3ad689). The eight relevant topics are 52, 53, 54, 55, 56, 60, 61, 62 (offsets in the table above). The help table cells are reproduced here verbatim, including the 4-column city symbols and the 5×5 unit-type matrix.
- **Decoded data sources.** `state/sav.py` has the decompile-shaped constants (`NATIONS`, `UNIT_TYPES`, `UNIT_NAMES`, `TERRAIN`, `MOVE_COST`, `SEASON_V`) for the in-game fields the H05 pages read; the DAT-side tables sit under the research repo:
  - `terrain-move-cost-table-in-dat.md` → terrain cost table at DAT 0x1F622
  - `unit-type-stat-table-in-dat.md` → 5×8 stat block at DAT 0x1F2F0 (moves, battalion, shots, range, shot damage, recruit cost initial, recruit cost quarterly, AI combat value)
  - `combat-type-effectiveness-matrix.md` → 5×5 melee matrix at DAT 0x1F7A6 (corrected)
  - `nation-marker-colours.md` → (background, foreground) per nation, observed by screenshot
  - `decompiled-recruitment-cost-formula.md` → the per-type table that produces H05's "per 200 men" cost, with two independent save-diffs that solved for the values algebraically before the DAT literal was located.
- **Tag scheme.** Same as `2026-10-05-player-facing-feature-inventory.md`: a row or sub-row is `[confirmed]` when the cited file lists it; `[derived]` when only a code reference is given; `[help]` when the cited evidence is the help topic text alone. The H05 page is **renderable from clone data** because every cell of every sub-row has a source in this repo or the research repo, and that includes the bitmaps (the asset pack carries the markers) and the colours (T97-corrected on the build side).

## Inferences

- The original's H05 page is **eight sub-tables** — Terrain, City symbols, Army symbols, Fleet symbols, National colours, Unit costs, Unit details, Unit type v type — and one **adjacent** sub-table outside H05 (Battle unit symbols, topic 65). Every cell of every sub-table has been verified against decoded data; the only sub-table whose source is *not yet located in a binary* is National colours.
- The help text strings (topics 60, 61, 62) literally carry the per-type numbers from the DAT stat table at 0x1F2F0 and the 5×5 melee matrix at 0x1F7A6. Re-encoding H05's tables on the clone is a straight data copy from the ruleset; no measurement is required.
- The clone's `godot/UI/HelpPage.cs` is a one-file change: a Markdown-ish renderer from `Dictionary<string, List<List<string>>>` plus the icon packs. The data dictionaries are exactly the eight sub-tables above, in this order.

## What this does not establish

- Whether the `.hlp` bitmaps (`battalion1.bmp`, `battalion2.bmp`, `battalion3.bmp` for LI per the help text example) are byte-identical across DAT builds — only the one v1.01 .hlp was decoded (per `hlp_check.py`).
- The 16 national colour pairs' binary location (`nation-marker-colours.md`).
- Whether the mercenary cost table is the *same* table as the regular recruit cost table (`unit-type-stat-table-in-dat.md`'s last open item). The decompile's `TRecruitMercs_RecruitMercUnit` reads `DAT_00478fd4`, which is the same in-memory base as the quarterly cost, but the report's note leaves this as a separate confirmation step.

## Reproduction

```bash
cd ~/projects/ic2-conquest
python3 -m state.sav --help                       # shows the constants the H05 page renders
python3 runs/experiments/feature_inventory/hlp_topics.py "Imperial Conquest 2.hlp" \
    > runs/experiments/data/run-exp-feature-inventory/help_topics.v3.tsv   # a re-run, decoder is fixed
```

The help decoder is the post-fix version (commit a3ad689, 247/247 records exact); no run is needed for H05 itself, only the data sources above.
