"""Render findings/2026-10-05-information-window-fields-and-bands.md from findings_rows.py, the code tables, band_edges/band_samples and the audit
and coverage summaries (latest versions under the tracked data folder). Writes the findings file (a draft: this repo's findings/ is versioned by git).
    python3 build_findings.py"""
import re, os, sys, csv, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, ROOT
import findings_rows as FR
import panel_model as M
from harness import decompile  # iw_lib puts the repo root on sys.path
decompile.check()
DUMP = decompile.DUMP
lines = open(DUMP, encoding='latin-1').read().split('\n')
start = {}
for i, l in enumerate(lines):
    m = re.match(r'// ==== (TInformation_Show\w+) @ ([0-9a-f]+) ====', l)
    if m: start[m.group(1)] = (i + 1, m.group(2))
def cite(fn, anchor):
    s = start[fn][0]
    for i in range(s, s + 260):
        if lines[i - 1].startswith('// ==== ') and i != s: break
        if anchor.strip('"') in lines[i - 1]: return i
    return None
def latest(pat):
    fs = glob.glob(DATA + pat)
    return sorted(fs, key=lambda p: (len(p), p))[-1]
def read(pat): return open(latest(pat), encoding='utf-8').read()
def rowline(r):
    n = cite(r['fn'], r['anchor'])
    code = 'F:%s %s' % (n, '(' + r['fn'].replace('TInformation_', '') + ')') if n else r['fn']
    return '| %s | %s | %s | %s | %s | %s | %s | [R-code] %s%s |' % (r['id'], r['line'], r['caption'], r['source'], r['formula'], r['fmt'], r['cond'], code, ('; [O] `%s`' % r['seen']) if r['id'] != 'H1' else '')
HDR = '| id | line | caption | source field | formula | format | shown when | evidence |\n|---|---|---|---|---|---|---|---|\n'
def table(panels):
    return HDR + '\n'.join(rowline(r) for r in FR.ROWS if r['panel'] in panels) + '\n'
# ---- band tables ----
edges = list(csv.DictReader(open(latest('band_edges*.tsv')), delimiter='\t'))
samples = list(csv.DictReader(open(latest('band_samples3*.tsv')), delimiter='\t'))
def sample(fld, v):
    for s in samples:
        if s['field'] == fld and int(s['value']) == v and s['status'] == 'OK': return s
def edge_rows(fld, fmt=None):
    out = []
    for e in edges:
        if e['field'] != fld: continue
        a, b = map(int, e['edge(last value of the lower word|first value of the higher word)'].split('|'))
        sa, sb = sample(fld, a), sample(fld, b)
        if e['status'] == 'confirmed':
            ev = '**confirmed**: %d `%s` (%s), %d `%s` (%s)' % (a, sa['png'], sa['save'], b, sb['png'], sb['save'])
        else:
            ev = '[derived] ' + e['status'].replace('derived ', '')
        out.append('| %d | %d | %s | %s | %s |' % (a, b, e['word_below'] or '(blank)', e['word_above'] or '(blank)', ev))
    return '| last value below | first value above | word below | word above | status |\n|---|---|---|---|---|\n' + '\n'.join(out) + '\n'
def words(fn, lo, hi):
    out, cur, s = [], None, lo
    for v in range(lo, hi + 1):
        w = fn(v)
        if cur is None: cur, s = w, v
        elif w != cur: out.append((s, v - 1, cur)); cur, s = w, v
    out.append((s, hi, cur)); return out
def wtable(fn, lo, hi):
    return '| from | to | word |\n|---|---|---|\n' + '\n'.join('| %d | %d | %s |' % (a, b, w if w else '(blank)') for a, b, w in words(fn, lo, hi)) + '\n'
audit = read('claims_audit3_summary*.txt'); cov = read('coverage_summary*.txt')
bn = re.search(r'band samples (\d+)', audit).group(1)
conf = sum(1 for e in edges if e['status'] == 'confirmed')
doc = '''# The Information window: every field, its formula, and the number-to-word bands

**Status:** draft finding from `ic2-conquest` (branch `experiment/info-window`), awaiting promotion. Task: `docs/tasks/info-window.md`. For the clone's v0.5.0 task T140 (imperial_conquest_2 #728, bug #718, foreign-nation panel #614). **Wine-only where a run is cited:** the runs are the original `Imperial Conquest 2.exe` (the normal build) under Wine 9.0 on Xvfb `:730`, own copy of the game folder, crafted copies of fixture saves only (L1 edits through `runs/experiments/info_window/stage.py`). Tags: `[R-code]` read from the decompile, `[O]` observed in play (a save and a screenshot, bare file names, in the release `run-exp-info-window`), `[D]` derived, never presented as observed. Code citations `F:<n>` are line numbers of `all_app_functions.txt` in the ReTools folder (function and address in the row).

## Answer

- **Priority (a), the number-to-word bands.** Every word comes from the DAT, not from the exe: the tables are BSS filled by the DAT loader `FUN_004481a0` in a fixed read order, so their DAT offsets are computed, not searched (quality `0x1F6CA`, unity/loyalty `0x1F738`, relations `0x1F800`). Unity and loyalty share one 11-byte table and differ only in the divisor (unity `div 100`, loyalty `div 10`, both truncating); morale is the same table read from entry 4 with index `(m - 51) sar 2`; quality is an index (no band). Sections "Band tables" give every threshold with its words; **%d of %d edges are confirmed on both sides in play** and the rest are [derived] with the reason.
- **Priority (b), the fortification bracket** is the sum of `troops` over **all** of the controlling nation's recruit slots at that city **whatever their state**, shown only when positive, on foreign cities too (row C07). The rules digest's "the queue is the garrison" is right; the help's "conscripts currently being trained" is too narrow (a state-24 trained unit counts: `61%% (3,000)` for a state-0 1,000 and a state-24 2,000 at one city).
- **Priority (c), Regulars cost / Mercenary pay** (rows A10, A11): per unit slot `s = i16(trunc(troops / 200) x price[type])` (the product is stored in a signed 16-bit `short`, F:41084; i16 = wrap to signed 16 bits), then regulars (label 0) `Regulars cost = sum s` and mercenaries (label not 0) `Mercenary pay = sum trunc((s x quality) / 5)` (F:41086, 41089); the two sums are 32-bit and not narrowed; with the DAT prices (1-4) the narrowing never changes a result, and it is documented so a clone with other prices copies it; price is the unit-type table's quarterly price (`DAT_00478FD4`, record `+0x24`); plain integers, own army only. Recomputed for every own army captured (staged morale, units, qualities, troops 199/399/200 for the `div 200` truncation, regular and mercenary slots) with 0 mismatches in `claims_audit_lines*.tsv`.
- **Priority (d), the fleet's Sea word** (row F08) is `calm` when the fleet's `+0x18` field is 0, otherwise `rough`. No rule on the panel decides it: the field is the map code under the fleet, cleared and re-rolled by the weekly weather overlay and copied from the destination cell by every fleet step (see the row).
- **Priority (e), the foreign-nation panel** (rows N01-N12): exact formats are in the nation table; **"peace" really shows blank** (relation 0, and any value `<= 0`, prints nothing; the word `peace` exists in the DAT table but is never printed); the nation's Population is the stored `+0x430` field, **3000 x the sum of its cities' populations in thousands** (so Rome shows 2,577,000 while its city panels add to 859,000); Mobilized and Treasury are blank for a foreign nation.
- **Coverage:** %s
- **Claims audit:** %s (`runs/experiments/info_window/audit.py`: every captured panel line recomputed from the code model and compared with the OCR of its screenshot; every band row compared as expected word versus seen word).

## Method

- **Code read.** The seven routines `TInformation_ShowNationStatus` 0x0043BA7C, `ShowCityDetails` 0x0043BE5C, `ShowArmyDetails` 0x0043C33C, `ShowFleetDetails` 0x0043C890, `ShowCityUnits` 0x0043CC40, `ShowArmyUnits` 0x0043CDD8, `ShowFleetUnits` 0x0043CF0C and the helpers they call were read from `all_app_functions.txt` (`show_fn.py` of the inventory task). `TInformation_PaintForm` (0x0043B394) draws each 61-byte line by splitting it at its **first `-`**: the left part at x, the right part 100 pixels to the right; so every `Caption -value` string below is a two-column row, and a line without a `-` is one string. A line that starts with `   (` is drawn red (the conquered-nation row).
- **Tables from the DAT.** `FUN_004481a0` (ReTools `scratch/datload.txt`) reads the DAT sequentially: the map `0x15E00`, the cities `0x2C5C`, 15 armies, 2 fleets, 16 nations, then the tables at `0x00478FB0`, ... (read sizes and addresses in `panel_model.LOADER`). The running sum of the read sizes puts `DAT_0047938C` at DAT offset `0x1F6CA`, which is where the first `not ready` is (a cross-check of the loader read against the file, `code_word_tables.tsv`). `panel_model.py` rebuilds the memory image (unfilled bytes are 0) and implements every panel, citing the decompile lines; it reproduces what the game does when an index runs past a table (loyalty -10 prints `ite`, from the end of the previous table).
- **Staging.** For every band, saves were crafted with the value on each side of every edge (`batch_a*.py`, one value per city, nation, army or fleet, so one save carries many edges), opened on the normal build, the object clicked (left click for the details panel, right click for the unit list or the mercenary list) and the Information window cropped (`import -crop`, 330 x 730) and OCR'd (tesseract). Every panel line is compared row by row, exactly, with the model (`rowcompare.py`, `audit.py`). The statuses the audit can assign: `OK`, `OK-ordinal` (the OCR reads the 1 of `1st` as `l`), `CLIPPED-right` / `CLIPPED-left` (only for a list row whose pixel extent is individually evidenced to touch the window edge, `row_extents.tsv`, with at least 25 visible glyphs and a strictly shorter exact prefix/suffix; partial evidence, no band evidence), `CORRECTED-OCR` (a glyph misread, each row listed with a reason and eye check in `ocr_corrections.v2.tsv`), `NOT-MODELLED-OUTPUT` (real game output the model does not produce, listed per row in `game_output_differences.v2.tsv`; never counted as a successful comparison), `SCROLLBAR-ARTIFACT` (the scroll-bar arrows read as text, each listed in `scrollbar_artifacts.tsv`), `EXCLUDED-listed` (`capture_exclusions*.tsv`), and the failing `MISMATCH`, `MISSING`, `EXTRA`, `NOT-MODELLED` (a capture kind with no model and no listed exclusion). Short rows, headers and fully visible rows must match exactly. Words were also **checked by eye** on contact sheets of the cropped word lines (loyalty, unity, morale, tribute, sea) and on the scrolled unit lists (quality): no disagreement with the OCR.
- **One caveat found on the way.** After File > Open the nation panel is not refreshed when the same nation is chosen again (it showed the previous save's values); batch a7 captured it that way, four shots are listed in `capture_exclusions.tsv` and were re-captured in batch a7b after choosing another nation first. Six first-run nation shots (batch a3, rows 9-14 clicked at the wrong menu pitch) are excluded by the audit because their panel names another nation than the one staged; they stay in `captures.tsv`.
- **Rule 6.** Text outputs under `runs/experiments/data/run-exp-info-window/` (never overwritten; versions as `.vN`), binaries in the release `run-exp-info-window` as per-batch tar.gz with `MANIFEST-<batch>.txt` and `SAVES.sha256`.

## The nation panel (N03 of the inventory)

''' % (conf, len(edges), cov.strip().replace('\n', ' '), audit.strip().replace('\n', ' ')) + table({'N'}) + '''
Notes: the relations row of nation `n` lists nation `m`'s name and **nation n's own relation value toward m** (`n`'s record, `+0x26 + 2m`); the conquered test uses nation m's unity (0) and m's `+0x44E`. A conquered nation's menu item is greyed, so its own panel cannot be opened (screenshot `t4_menu.png`, in the release manifest, checked by eye; it is a menu shot, not a panel capture in `captures.tsv`).

## The city panel (UM02), left click on any city tile, own or foreign

''' + table({'C'}) + '''
## The army panel (UM03 own, UM04 foreign), left click on an army

''' + table({'A'}) + '''
**Foreign army** (the same routine; every `own` condition is false): lines 1-4 (Moves, Supply, Morale, Money) show only their captions, Terrain and the five type lines and Total troops are shown, and No. of units, Regulars cost and Mercenary pay do not exist (the last line index is `b + 6`). A left click on a foreign army does not select it (`SEL_ARMY` stays -1) and a right click on it prints nothing new: the left-click panel stays [O] `A5_foreign_army2_left.png`, `A5_foreign_army2_right.png`, `A5_foreign_army7_left.png`, `A5_foreign_army4_left.png`.

## The fleet panel (UM05), left click on a fleet marker

''' + table({'F'}) + '''
**Foreign fleet:** Fleet of, Ships, Capacity and Sea are shown; Moves, Repair, Supply and Money are blank [O] `A5_f5a_fleet0_left.png`, `A5_f5b_fleet1_left.png`. A foreign fleet that carries an army shows that army as a foreign army (composition only) under `Army` [O] `A5_f5c_fleet0_left.png`. **What decides Sea:** `FUN_00451304` (weather overlay, `F:54272`) zeroes `+0x18` of every fleet each week, clears and re-rolls the code-1 cells (rough sea) around 20 DAT centres, and sets `+0x18 = 1` for a fleet whose marker a new patch lands on (`F:54264`); every fleet step (`FUN_0044DD70`, `F:51965-51972`) stores the destination cell's code into `+0x18` (a fleet can only enter cells with code 0 or 1); a new fleet starts at 0 (`F:48794`). The panel only tests `+0x18 == 0`. [R-code][O] values 0 (`calm`), 1, 2, -1 (`rough`) in `A5_f5a_fleet2_left.png`, `A5_f5a_fleet0_left.png`, `A5_f5b_fleet0_left.png`, `A5_f5a_fleet1_left.png`. See also decompiled-map-code1-overlay.md and decompiled-weather-events.md of the research repository.

## The unit lists (UM06, UM07), right click

''' + table({'U1', 'U2', 'U3'}) + '''
Helpers (not captions): `FUN_00405B00` strcpy and `FUN_00405BC8` strcat build every line; `FUN_004028C4` + `FUN_00402978` turn a number into its decimal text (no separators; a negative keeps `-`); the three thousands formatters are `FUN_00448E74` (a 14-character field: blank, sign, blank, then the digits with `,` every three, left-aligned), `FUN_00448F18` (trailing blanks cut), `FUN_00448F3C` (left part cut: `1,500`, or `- 1,500` for a negative: the minus, a blank, the digits [O] `A7_nation00_treasury0.png`), `FUN_00448F9C` (12 characters copied from index 3: no sign, trailing blanks kept); `FUN_004498D8`, `FUN_00449920`, `FUN_00449970` find the city, army or fleet at the clicked tile (the army and fleet must have an owner >= 0); `FUN_0044A698` total troops (1 if 0), `FUN_0044A66C` highest used slot + 1, `FUN_0044B8D0` is-a-capital, `FUN_004498B0` tribute x pop / max pop.

## Band tables

Words are the DAT strings (11-byte entries; the relation entries are 6 bytes). An edge is **confirmed** only when both sides were captured in play with the expected word seen; the screenshot and save of each side are cited. `[derived]` edges are the ones that were not or could not be staged, with the reason.

### Unity (nation panel), `trunc(unity / 100)` into the table at `DAT_004793FC`

''' + wtable(M.unity_word, 0, 1199) + '\n' + edge_rows('unity') + '''
Unity 0 is not a word: the nation is conquered (row N12). Unity is kept within 300-990 by the game's own quarterly update (nation-tax-base / city-population-growth reports), so the blank at 1000 and above is not reachable in play [D]; it was staged only to read the code's edge (`A3_nation_13_Armenia.v2.png` blank at 1000, `A3_nation_14_Media.v2.png` blank at 1100).

### Loyalty (city panel), `trunc(loyalty / 10)` into the same table

''' + wtable(M.loyalty_word, 0, 109) + '\n' + edge_rows('loyalty') + '''
Saves hold 38-96 (702 saves, 4,000+ city records); a negative loyalty is read before the table (-10..-19 prints `ite`, the tail of `elite` of the quality table; -20.. prints other bytes): staged only at -10 and -9 [O] `A1_city_071_Pisae.png` (`ite`), `A1_city_080_Tarquinii.png` (`very low`); edges below -10 are [D].

### Morale (own army panel), index `((m - 51), or (m - 48) when that is negative) sar 2` into the table at `DAT_00479428` (= the unity table from entry 4)

''' + wtable(M.morale_word, 40, 80) + '\n' + edge_rows('morale') + '''
Saves hold 51-73 (the research report supply-driven-morale-and-fleet-attrition.md says 51-70 and "five 4-wide tiers"; the code has a sixth tier, `excellent` 71-74, and saves such as `fleet-split-antium-0734.SAV` (army 3, morale 73) are in it). Below 51 the `m - 48` branch applies: 48-50 are index 0 (`very low`; 50 staged [O] `A4_army_00_left.png`); 40-47 read the unity table's entries 3 to 1 before the morale table's start, which are also `very low` [D] (not staged); below about 36 the index leaves the table [D]. 75 and above prints nothing [O] (75 staged, `A4_army_13_left.png`).

### Quality of a unit (unit lists, mercenary lists), the field `0..9` is the table index (`DAT_0047938C`)

''' + wtable(lambda q: M.quality_word(q), 0, 11) + '\n' + edge_rows('quality') + '''
Indexes 0-3 print the same word (`not ready`: the mobilized quality is `state / 4`, a unit under 16 weeks of training); 10 and 11 print nothing [O] `A6_army0_right_scrolled.png`. The word is checked space-free in the audit because the OCR sometimes drops a blank inside a row; the shot was checked by eye.

### Tribute of a FOREIGN city (found on the way), the city's `+0x20` field as an unsigned 16-bit

''' + edge_rows('tribute_word_foreign') + '''
Above 10000 no word is chosen and the talents number text (row C08's) stays: 10001 prints `10001`, 20000 prints `20000`, 40000 prints `-25536`, 65535 prints `-1` [O] `A2_city_026_Helice.png`, `A2_city_030_Akra Leuke.png`, `A2_city_033_Icosium.png`, `A2_city_035_Cissa.png`.

### Relations (nation panel), `DAT_004794C8 + 6 x value` only when `value > 0`

| value | word |
|---|---|
| <= 0 | (blank) |
| 1 | trade |
| 2 | ally |
| 3 | war |
| 4, 5 | (blank) |
| 6, 7, 100 | other memory (one stray character, `5` `[` `,` seen) |

''' + edge_rows('relation') + '''
The DAT table also holds `peace` at value 0, which the code never prints. Values stored in saves are -18..3 (the negatives are other state of the diplomacy matrix); only 0-3 are meaningful.

### Sea (fleet panel)

| `+0x18` | word |
|---|---|
| 0 | calm |
| anything else | rough |

''' + edge_rows('sea') + '''
### Other branches that are not words

- **Fortification** `raw <= 100`: `raw%%`; `raw >= 101`: `raw mod 100%%  (under construction)`: staged 0, 50, 99, 100, 101, 150, 199, 200, 250 [O] `A1_city_*` (100 prints `100%%`, 101 prints `1%%  (under construction)`).

## Where the sources disagree

- **Help topic "Cities" versus the code (bracket).** The help says the number in brackets after the fortification is "the number of conscripts currently being trained at that city". The code (C07) sums every slot of the controller's queue at that city whatever its state, trained ones included, and does it for foreign cities as well. [R-code][O] `A2_city_090_Alba Fucens.png` (state 0 + state 24 = `(3,000)`). The digest line "the queue is the garrison" matches the code.
- **Help topic "Nations" versus the code.** The help lists "tribute payed" and "trade earned" among the details of the own nation; `ShowNationStatus` prints neither (the inventory's N03 already noted the screenshots do not show them). [R-code][O] `A7b_nation00_treasury1.png` (Rome as current nation: Mobilized and Treasury present) and `A8_cur1_nation00.png` (Rome seen from Carthage: neither).
- **Research report `supply-driven-morale-and-fleet-attrition.md`** says the morale field is bounded 51-70, exactly five 4-wide tiers; the code has six tiers and saves reach 73 (see Morale above).
- **Research report `rome-city-recruitment-and-nations.md`** lists the loyalty adjective thresholds as "not decoded"; they are in the Loyalty table above.
- **Inventory rows UM04 and UM05** were [derived]; they are now observed (foreign army: composition, terrain and total only; fleet panel: fields and Sea).
- **Nation-tax-base report names `+0x430` "wealth"**; the panel prints it as **Population**. [O] the panels of the unmodified BASE.SAV nations show Rome `2,577,000` (`A8_cur1_nation00.png`) and Carthage `4,821,000` (`A8_cur1_nation01.png`). [D] those equal 3000 x the sum of the cities' `pop` fields of that save (Rome 859, Carthage 1607, computed with `state/sav.py` from `BASE.SAV`, not a capture), which is the report's formula.

## What this does not establish

- **Model-versus-game output not reproduced (1 row, `NOT-MODELLED-OUTPUT`):** a nation Population of 2,147,483,647 (`A3_nation_07_Greece.png`, panel line 4) prints junk glyphs after the digits; the code explains the overrun (`FUN_00448F9C` copies 12 characters of a 14-character field without a terminator) but the junk is stale stack content the model cannot know; the value is unreachable (10^9 or more). The relation-100 stray `,` after Dacia, once listed as a disagreement, is now modelled: the index runs into the city table loaded from the save (byte `0x2C`), and the row compares OK apart from an OCR misread of the comma.
- Edges outside the values the game produces (loyalty below 0 or above 109, unity 1000 and above, morale below 48 and above 75, relation values above 5, quality -1 and 10 and above) are the code's reading of other memory and are [derived]; the ones staged are marked confirmed only where both sides were seen.
- OCR was the reader; the by-eye check covered contact sheets of the cropped word lines and the 23 corrected rows, not every one of the 1,500 panel lines. 29 clipped list rows are partial evidence only (their last word is cut by the window); the quality words are evidenced by the scrolled / short lists.
- `Population` of a nation of 10^9 or more prints junk after the digits; not a reachable value.
- Carthage as current nation was re-captured with a verified refresh (`A8_cur1_nation01.png`: Mobilized 12%, Treasury 7,777 talents); the first attempt (`A7_cur1_nation01.png`) showed a stale Rome panel and is excluded.
- A nation panel whose `Capital` is -1, a city with `max_pop` 0 (division by zero in `ShowCityDetails`) and a city whose allegiance is -1 were not staged.
- The panel is rebuilt only on a click or a menu choice; whether the game redraws it after an order or an end of turn was not studied.
- Wine 9.0 only; no real Windows run.
- The news-log, battle `BattleUnitMoves` and the other Information-window uses are out of this task.

## Evidence index

`runs/experiments/data/run-exp-info-window/`: `captures.tsv` (every capture: save, target, staged values, screenshot, SHA-256, OCR), `claims_audit_*` (the audit), `band_samples.tsv`, `band_edges.tsv`, `code_word_tables.tsv`, `coverage_report.tsv` and `coverage_summary.txt`, `MANIFEST-*.txt`, `SAVES.sha256`, `capture_exclusions.tsv`. Scripts in `runs/experiments/info_window/`. Binaries: release `run-exp-info-window`.
'''
doc = doc.replace('%%', '%')
out = ROOT + '/findings/2026-10-05-information-window-fields-and-bands.md'
open(out, 'w', encoding='utf-8').write(doc)
print(out, len(doc))
