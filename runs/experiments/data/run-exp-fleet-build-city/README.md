# run-exp-fleet-build-city

Original-side check of the v0.5.0 gap analysis: rows_g1 NEW-g1-3 (at which city the original builds a fleet) and rows_g2 check 8 (whether a coastal city with a fleet under construction is still free).

- `build_city.py`: from `saves/run0-start-AUTO0720-seed12345.SAV` (Rome), seed 12345, the seed exe. It orders Build fleet (10 ships) repeatedly in the same turn and logs each box, the new fleet record's build city (read from memory) and the treasury. At the start it also lists Rome's cities with their Chebyshev distance to the capital and whether sea touches them (3×3).
- Logs `build_city-<stamp>.jsonl`. The four runs:
  - `182810`: crashed at its start on a script bug (`g.nation`).
  - `182837`: the second order met the N02 notice ("A fleet of 10 ships will be ready in 24 weeks at Caere."), which the driver then took for a refusal.
  - `183011`: five orders, after the driver fix; the sixth timed out.
  - `183238`: the cited run, six orders.
- **Driver fix, the same day:** `Game.build_fleet` now reads and dismisses N02 notices (shown before the dialog, one per own fleet under construction) and waits up to 20 s for the dialog.
- **Order 7 of the cited run:** neither the dialog nor a box appeared within 20 s (`20261009-183238_timeout_order7.png`). Not explained.
- **Binaries:** release `run-exp-fleet-build-city`; SHA-256 in `SAVES.sha256`.
