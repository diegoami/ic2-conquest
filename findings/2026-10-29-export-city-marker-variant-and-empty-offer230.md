# Converting a save through the remake changes three conquered cities' marker variant and the empty offer's type

**Status:** promoted by research PR #93 (merge `403db0d`), 2026-10-29, with the cause of the marker change established
(below). The empty offer's type change is still unexplained.
**Tag:** [confirmed, partial] for the bytes; the marker cause [confirmed] by research. One start save, under Wine.
**Task:** conquest [#230](https://github.com/diegoami/ic2-conquest/issues/230) (tracker #228); remake **v0.8.4**
(`d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`).

## Answer

`saves/fleet-port-antium-0734.SAV` (Rome, Autumn week 5, 270 BC) was imported into the remake
(`OriginalSaveImporter`) and exported straight back (`OriginalSaveExporter`), with no order in between. Compared with
the original's own save, the same parser (`state/sav.py`) finds two differences:

1. **Three city marker cells.** A city's marker word is 20 + owner + 16 × variant
   (`findings/2026-10-09-city-marker-colours.md`). The owner part is unchanged; the export writes the variant one
   higher:

   | City (index) | Tile | Owner (allegiance) | Population | Original word | Exported word |
   |---|---|---|---|---|---|
   | Bordeaux (27) | (47,29) | Celtiberia (Gaul) | 26 / 27 | 28 (variant 0) | 44 (variant 1) |
   | Tarquinii (80) | (98,39) | Gaul (Rome) | 26 / 27 | 26 (variant 0) | 42 (variant 1) |
   | Tarrentum (123) | (124,52) | Gaul (Greece) | 51 / 56 | 42 (variant 1) | 58 (variant 2) |

   All three are conquered cities (owner ≠ allegiance). Every other city marker matches, including other conquered
   ones. **Cause (research, PR #93, from `2026-10-07-city-marker-variants.md`):** the original refreshes a city's tier
   only when the city changes owner, never as it grows. In `embark/original/a000.SAV` these three are exactly the
   only stale tiers (Bordeaux and Tarquinii at population 26 should be tier 1, Tarrentum at 51 tier 2). The export
   has none, because the conversion recomputes the tier from the current population. So the remake's export is
   "correct" by the tier rule, and the original's save carries a tier its own rule would no longer give.
2. **The empty pending offer's type.** With no offer pending (sender −1), the original's tail holds type 1 and the
   export writes 0.

The Rome 270 BC start (`BASE.SAV`) round-trips exactly in both respects (`run-exp-diff084-tooling`, checkpoint
`a000`: 0 differences), so these come from this save's later state.

## Effect on the comparisons

Every case of #230 batch 3 that starts from this save shows both differences at its start (`a000`) and unchanged
after the orders. The sweep now sets aside a difference already present at the start (`difftest/sweep.py`); it does
not count it against the order. Whether the remake also draws these cities with a different icon in play was not
checked: this finding is about the save conversion, not the display.

## Evidence

Run `run-exp-diff084-orders-b3` (turn 0734): `embark/original/a000.SAV` vs `embark/remake/a000.SAV`; the same in
every case of the batch that starts from `fleet-port-antium-0734.SAV` or `fleet-split-antium-0734.SAV`. Data:
`runs/experiments/data/run-exp-diff084-orders-b3/` (`results-rejudged-*.jsonl`, `details.start_baseline`).
