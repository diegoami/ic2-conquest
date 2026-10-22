# run-exp-manual-gaps: screenshots the manual still lacks, and rules seen only in the code

Short staged runs of *Imperial Conquest 2* under Wine, approved by the owner on 2026-10-22. Items A1-A6 are screenshots for the
user manual; items B7-B11 observe rules that were known only from the decompiled code, each as a before/after save diff.

- **PNGs**: `/home/user/ic2-conquest/artifacts/run-exp-manual-gaps/shots/` (gitignored, rule 1), all prefixed `MG_`, never
  overwritten (a re-take is `_v2`). `shots.csv`: file, item, what it shows, source save, turn, exe, sha256.
- **Saves**: `/home/user/ic2-conquest/artifacts/run-exp-manual-gaps/saves/` (gitignored), prefixed `MG_`; SHA-256 in
  `SAVES.sha256`. Copied to Drive `gdrive:IC2/artifacts/run-exp-manual-gaps`. To go to release `run-exp-manual-gaps`.
- **Staged (SYNTHETIC) saves**: `runs/experiments/manual_gaps/stage.py`; every edit (offset, old, new) is in `staged-edits.jsonl`.
  The other saves are natural play from them.
- **Logs**: `run-log.jsonl` (every load, shot, measurement), `a5-trials.jsonl`, `b10-storms.jsonl`, `b11-war.jsonl`;
  save diffs `B*-diff.txt` (`diff_saves.py`: decoded map, cities, armies, fleets, nations, news, calendar).
- Environment: Xvfb 1280x1024, Wine, no window manager; the seed build `Imperial Conquest 2 fast rollingsave seed.exe`
  (SEED.TXT 12345 unless a seed is named). Only one game ran at a time.
- Scripts (`runs/experiments/manual_gaps/`): `mg.py` (start/attach/snap/keep_save, after `manual133/m.py`), `craft.py`
  (save edits, map markers kept consistent), `stage.py`, `inspect_save.py`, `diff_saves.py`, `a5_peace.py`, `b10_storms.py`,
  `b11_war.py`.

## Progress

(filled in per item below)
