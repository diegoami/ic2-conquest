# Experiment: can Rome beat Gaul's field army early?

From the run-0 start (`BASE.SAV`, Rome, a fresh seed): join armies 0 and 1,
march the joined army to Gaul's army, attack it and play the battle with
*Computer general*. Then record both sides' composition before and after, the
winner and the losses.

```bash
python3 runs/experiments/gallic-army.py 12345 999 777 42
```

Writes `results.json` here.

## Result (2026-10-01, Wine 9.0, build SHA-256 `354d8265…532f`)

Rome's joined army is 45,700 (li 8,900, hi 30,700, lc 2,400, hc 3,700). It
reaches Gaul's army on the third turn (0723) in every seed and destroys it,
losing 9,400–13,800 troops:

| seed | Gaul before | Rome after | Rome lost | winner |
|---|---:|---:|---:|---|
| 12345 | 43,153 | 36,298 | 9,402 | Rome |
| 999 | 43,169 | 32,305 | 13,395 | Rome |
| 777 | 43,133 | 35,274 | 10,426 | Rome |
| 42 | 43,153 | 31,883 | 13,817 | Rome |

Gaul's army is destroyed in all four seeds; Rome never loses. So the
"defeat the Gallic army first" priority is safe at this force ratio
(45,700 : ~43,150), with 20–30 % losses. Gaul's exact composition varies a
little per seed (its AI turn is seeded); Rome's does not.

## Repeatability

A turn containing a tactical battle is **byte-repeatable** under a fixed seed:
two runs of seed 12345 produced identical `AUTO0724.SAV` (the autosave after
the battle turn).

## How the battle is driven

`Game.attack` clicks the adjacent enemy army, waits for the battle window (it
opens about 3 s later) and calls `Game.play_battle`, which clicks *Computer
general on* and then *End turn*. The battle toolbar's x is derived from its
tooltips (End turn ~114, Computer general ~165 vs `coverage.md`'s 110/158).
**The Computer general toggle must be on during the placement phase**, or the
battle stalls waiting for human input; hence the wait before clicking.
