# run-exp-diff084-tactical-stats: battle losses over many seeds (#231)

Pre-registration: `difftest/cases/tactical231_stats.py` (written before any trial). Runner:
`python3 -m difftest.tactical stats`; analysis: `python3 -m difftest.stats analyze difftest.cases.tactical231_stats
run-exp-diff084-tactical-stats` (permutation test, Holm over 8 tests, alpha 0.05). Original: startup RandSeed =
seed; remake: the battle's draw stream = seed. 30 seeds per game per case; 120 trials, none failed.

| Case | Metric | Original | Remake | Verdict |
|---|---|---|---|---|
| `melee30`: heavy infantry 3,000 attacks adjacent heavy infantry 3,000 | attacker troops lost | 215.9 | 213.9 | consistent (p 0.93) |
| | defender troops lost | 427.9 | 400.7 | consistent (p 0.51) |
| | final morale (attacker / defender) | 71.3 / 67.7 | 71.3 / 67.7 | consistent |
| `archery30`: archers 1,000 shoot heavy infantry 2,000 at distance 2, three volleys | target troops lost | 18.1 | 17.7 | consistent (p 0.80) |
| | morale, shooter's losses | 70 / 0 | 70 / 0 | consistent |

Per trial, the boards after every command: `<case>/original-s<seed>*.jsonl` and `<case>/remake-s<seed>*.jsonl`.
