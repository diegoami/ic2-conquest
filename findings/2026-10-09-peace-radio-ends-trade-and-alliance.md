# The original's Peace radio ends a trade (−8) or an alliance (−24) on both sides at OK, with no box and no news; Cancel discards. The remake's engine does the same for a trade, but its app offers Make Peace only at war

**Status:** promoted 2026-10-09 into imperial-conquest-2-research at `06f5a5e` (by ic2-research, from `e091835`); this draft is kept for history, the research repo is canonical. Research notes it is the first in-play confirmation of `FUN_00449B40`'s cooldown table (trade → −8, alliance → −24, symmetric). It does original-side check 1 of the v0.5.0 gap analysis (research `1935df5` / `4ff65e8`, row NEW-g1-2 and S02), at the player's request. NEW-g1-2's severity ("blocks a normal game") was conditional on this check, and the condition holds.

**Tags:**
- `[confirmed]` (Wine): read from game memory and the saves.
- **L1:** the ally case is staged and labelled.

## Answer

- **Peace on a trade partner** `[confirmed]`: at the start `run0-start-AUTO0720-seed12345.SAV`, Rome trades with Illyria (relation 1 both ways). Peace radio on Illyria, OK:
  - the relation becomes **−8 on both sides at once**;
  - no box opens, and no news line follows (`A_20261009-175015_AUTO0721.SAV`);
  - the −8 is still there after the End turn.
  - Saves: `A_20261009-175015_A_before.SAV` → `A_20261009-175015_A_after.SAV`.
- **Peace on an ally** `[confirmed]`, L1: with Rome–Illyria set to 2 (allied) both ways in the start save (`D_20261009-175644_start_rome_illyria_allied.SAV`), Peace radio on Illyria, OK:
  - the relation becomes **−24 on both sides**;
  - no box, no news line (`D_20261009-175644_AUTO0721.SAV`), and the −24 holds after End turn.
  - Save after: `D_20261009-175644_D_after.SAV`.
- **No natural alliance at this start:** Alliance proposed to each of the 15 nations was refused every time: "X does not want to ally with your nation." (`peace_radio-C-*.jsonl`).
- **Cancel discards** `[confirmed]`: clicking the Peace radio on Illyria and then Cancel leaves the relation at 1 (`B_20261009-175604_B_after_cancel.SAV`; screenshot `B_20261009-175604_peace_clicked.png`).
  - A radio click alone commits nothing: the dialog commits at OK.
  - In the first run the Cancel click only activated the window (a known driver pitfall); the second run's third click closed the dialog.
- **The remake** (v0.5.0, CLI): `make-peace macedonia` on a trade partner also gives **−8 both ways**, kept after `end` (`cli/check1_peace_on_trade.txt`, `check1_before.sav` → `check1_after_trade_peace.sav` → `check1_after_end.sav`). The engine matches.
  - **But the app enables Make Peace only at war** (`godot/Screens/DiplomacyGridViewModel.cs:69`, `CanMakePeace: isWar`, code reading).
  - So **in the Godot app a player cannot end a trade or an alliance**, which the original allows. With 3 trade partners, no new trade can be made. The ally case was not run on the remake.
- **For the gap analysis:**
  - NEW-g1-2's condition holds: `differs`, `blocks a normal game`, no longer conditional.
  - S02's "OK commits, Cancel discards" is confirmed on the original side. The remake's screen commits each click at once (rows_g1 S02).

## Evidence

- **Data:** `runs/experiments/data/run-exp-peace-radio/` (`peace_radio.py`, `peace_radio-{A,B,C,D}-*.jsonl`, `SAVES.sha256`, `README.md`).
- **Release:** [`run-exp-peace-radio`](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-peace-radio).
- **The remake's side:** `runs/experiments/data/run-exp-gap-v050/cli/check1_peace_on_trade.txt`; the `check1_*.sav` saves are added to release `run-exp-gap-v050`.

## Not established

- **A natural alliance** (none formed at this start); the ally case is staged.
- **The remake's value after ending an alliance**, not run. The −24 is the original's.
- **The Godot screen itself:** its Make Peace gating is code reading.
- **The desktop original:** Wine only.
