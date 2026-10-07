# In-play corroboration of the strategic AI turn: the week-11 tax policy and the free AI mercenary hire

**Status:** draft finding from `ic2-conquest`, awaiting promotion. The in-play checks of
`docs/reports/2026-10-07-strategic-ai-turn.md` (research repo, as corrected at commit `7d7b613`)
named in the research pending request (2026-10-07). Checks attempted: **1 (tax) and 2 (free hire)**, per the
owner's routing; checks 3 (intercept dispatch) and 4 (fleet hunt-vs-port) were not attempted. **Wine-only.**
Natural play throughout: one fixed-seed new game, nothing staged, nothing edited, one SAV per watched turn.

**Tags.** `[derived]` = the research report's decompile reading (cited by section). `[confirmed]` = this run's
saves (bare filenames; SHA-256 in `runs/experiments/data/run-exp-ai-turn/SAVES.sha256`, binaries in release
`run-exp-ai-turn` batches b1/b2).

## Answer

- **The week-11 tax policy reproduces exactly in play** `[confirmed]`. Across two season boundaries
  (Spring and Summer 270 BC), every decidable nation row — 18 of 18, 0 mismatches — moves as the three
  sequential rules say (`§2.3`): cut `max(5, tax−6)` when `unity < 650` or `treasury > wealth/2000`; raise
  `min(40, tax+9)` when `treasury < 0`; zero when `treasury > 0 and unity < 500` (never triggered in this
  run — no nation's unity fell below 500). Examples: Armenia 8→5 = `max(5, 8−6)` (`AUTO0730.SAV`→`AUTO0731.SAV`,
  unity 681, treasury 1,129 > wealth/2000 = 537: cut only); Gaul 10→14 = cut to `max(5, 10−6)` = 5 then raise
  5+9 (treasury −2,798: both rules) (`AUTO0724.SAV`→`AUTO0725.SAV`); Galatia 14→23 = raise only, no cut trigger
  (unity 703, treasury −1,932 ≤ 684,000/2000) (`AUTO0724.SAV`→`AUTO0725.SAV`). Full tables:
  `runs/experiments/data/run-exp-ai-turn/tax_analysis.txt`.
- **Save-side placement (a correction to the report's phrasing)** `[confirmed]`. The new tax is already in the
  **week-11 save** (`AUTO0725.SAV`, `AUTO0731.SAV`); the week-11 → new-season transition shows **no** move
  (checked pair by pair, all 12 turns). So the block fires during the end-of-turn processing that leads INTO
  week 11 — consistent with the turn shape of `§1` if the weekly tick (week 9→11) runs at the seat-0 wrap
  *before* the AI seats act, so their economy phases see the counter at `0xb`. The report's "immediately before
  the quarterly tick" is one weekly tick early at save granularity: the quarterly tick (11→next season week 1)
  carries no tax write. A clone implementing "adjust at the last week's turn" should write the new tax in the
  transition that produces the week-11 state, not after it.
- **Auto-tax is computer-seat-only** `[confirmed]` (control). Rome, the human seat, held tax 10→10 and 10→10
  across both boundaries although the cut trigger held both times (treasury 2,200 > 2,577,000/2000 = 1,288;
  then 2,471 > 1,300). The slider was never touched.
- **The raise's threatened-and-broke branch fired with a positive treasury** `[confirmed, indirect]`. Greece
  (treasury 948) and Illyria (580) moved exactly cut+raise (5→14 both, `AUTO0724.SAV`→`AUTO0725.SAV`) with
  `0 ≤ treasury < 1000`: the `own ≤ threat` half of `§2.3`'s raise disjunct must have held (the threat budget
  `§2.1` is computed in memory and is not in any save). Macedonia (treasury 275, same boundary) did not move —
  consistent with its threat budget not dominating, but not proof.
- **The AI hires mercenaries for free** `[confirmed]`. Two natural observations, one of them a double hire:
  - **Gaul, `AUTO0720.SAV`→`AUTO0721.SAV`:** pool slot 13 (label 11 "Gallic", li, 11,735 troops, q7) at (98,31)
    = **Felsina, Gaul's own city**; army 9 (at war with Rome) stood at (96,30), Chebyshev 2, **money 96**. At
    t+1 the slot is empty and army 9's slot 11 holds the offer copied exactly (label 11, li, 11,735, q7, name
    "Gallic"). **Army money 96→96, Gaul treasury −2,668→−2,668: no payment anywhere in the diff.**
  - **Carthage, `AUTO0721.SAV`→`AUTO0722.SAV`:** pool slots 0 and 4 (both label 15 "Libyan": li 4,260 q6 and
    li 5,274 q7) at (83,85) = **Theveste, Carthage's own city**; army 3 (at war with Celtiberia) at (84,84),
    Chebyshev 1, **money 600**. At t+1 both slots are empty and army 3 holds both units (slots 6 and 7, names
    "Libyan"). **Money 600→600, treasury 9,366→9,366.** Two offers hired in one army-turn corroborates the
    report's *every* live offer at the city being hired in a loop (`§3.2`).
  Both hires passed the report's gates: at war, army money > 50 (96, 600), offer on a city tile within
  Chebyshev 4, city owner not at war with the hirer (own cities), a free unit slot. Against the human twin: the
  human's gate is the full computed price and the AI's is 50 talents flat (`§3.2`, and
  `2026-10-05-mercenary-hire-price-is-a-gate-not-a-charge.md`: the human's price is also only a gate).
- **The pool refreshes seasonally**: 9 further slots changed contents with no army holding the old stats
  (`merc_analysis.txt`) — the market's own refresh at the quarterly boundaries, not hires.

## Method

- **The run.** `runs/experiments/ai_turn/watch.py` on the fast rollingsave exe: `Game.new_game(row=0,
  seed=424242)` (Rome human, 15 computer seats; RandSeed from `SEED.TXT` at program start), then End turn
  repeatedly; every human turn's `AUTOnnnn.SAV` (0720–0732, Spring week 1 through Summer week 11) copied to
  `artifacts/run-exp-ai-turn/`, SHA-256 into the tracked `SAVES.sha256`, and parsed into
  `runs/experiments/data/run-exp-ai-turn/turns/AUTO*.json` (nations incl. the `+0x26` relation shorts, armies
  with unit slots and merc labels, the 50-slot pool — `snapshot.py`). Battles auto-played (Computer general,
  instant). Driver hiccups (a transient "no controls found for window 'End turn ?'" race) were recovered by
  pumping the pending turn out, never by a second End turn click; the affected turns' saves are the ones the
  log names.
- **Determinism check.** An earlier aborted attempt had collected 0720–0724 before dying; the restarted run
  (same seed, fresh process) reproduced those five snapshots **byte-identical in content** (`.v2.json` files
  beside the originals, kept per rule 6).
- **Analysis.** `analyze_tax.py` (rule table above), `analyze_merc.py` (pool-slot fate + stat match into
  armies). Both read only the tracked snapshots; outputs beside them, versioned.

## What this does not establish

- **The zero rule** (`treasury > 0 and unity < 500`) was never triggered: no watched nation's unity fell below
  500 (Gaul's 552 at Spring was the floor). Its `[derived]` status stands.
- **The raise's `own ≤ threat` condition** is corroborated only indirectly (Greece, Illyria); the threat budget
  itself lives in memory only. **Trigger values are read at turn start** (the human turn's autosave); the AI's
  own economy-phase spending before the tax block cannot be subtracted from a save (for Gaul 0720→0721 the
  treasury happened to be unchanged, so that row is clean; the deficit rows' treasuries moved by −130…−1,050
  within the following season, all staying negative).
- **The `+0x274` byte gate** on the hire remains unopened `[derived]` (report's own open list).
- **The exact intra-transition ordering** (weekly tick before the AI seats vs. the block reading the counter
  another way) is inferred from where the write lands, not disassembled.
- **Checks 3 (homeland intercept dispatch) and 4 (fleet hunt-vs-port)** were not attempted (the owner's
  routing stopped after checks 1 and 2).
- **Wine-only**: a desktop run should repeat the two hire observations before the clone treats them as
  platform-independent.

## Reproduction

```bash
source harness/env.sh
python3 runs/experiments/ai_turn/watch.py 424242 732     # ~20 min, one save per turn
python3 runs/experiments/ai_turn/analyze_tax.py
python3 runs/experiments/ai_turn/analyze_merc.py
```

Saves: release `run-exp-ai-turn`, batches b1 (the run's `AUTO0720.SAV`–`AUTO0724.SAV`, plus the aborted
attempt's own 0720–0725 autosaves preserved under `pre-run-game-folder/`) and b2 (0725–0732); hashes in
`runs/experiments/data/run-exp-ai-turn/SAVES.sha256` and `MANIFEST-b{1,2}.txt`.
