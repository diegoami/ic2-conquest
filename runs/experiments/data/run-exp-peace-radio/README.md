# run-exp-peace-radio

The original-side check of the v0.5.0 gap analysis's row NEW-g1-2 (`rows_g1.md`): whether the original's International Relations
dialog ends a trade or an alliance when the Peace radio is set and OK pressed, and whether Cancel discards a change.

- **Runner:** `peace_radio.py A|B|C|D`, one fresh process per phase, start `saves/run0-start-AUTO0720-seed12345.SAV` (Rome human; Rome trades with Illyria), seed 12345, the seed exe. The order goes through `Game.relation`, with the relation read back from game memory on both sides. Logs: `peace_radio-<phase>-<stamp>.jsonl`.
  - A: Peace on the trade partner.
  - B: the Peace radio, then Cancel. The first B run's Cancel click only activated the window, and the dialog stayed open; the second run retries it.
  - C: an alliance proposed to every nation. All refused, so there is no save.
  - D: a staged alliance (L1: `stage.edit` `relation` 0-9 = 2), then Peace.
- **Binaries:** release `run-exp-peace-radio` (saves, autosaves, the dialog screenshots); SHA-256 in `SAVES.sha256`.
- **The remake's counterpart:** `runs/experiments/data/run-exp-gap-v050/cli/check1_peace_on_trade.txt` and the `check1_*.sav` saves (release `run-exp-gap-v050`, a later upload).
