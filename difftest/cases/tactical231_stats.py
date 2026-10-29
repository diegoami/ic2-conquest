"""#231 many-seed pre-registration (written 2026-10-29 before any trial).

Combat losses come from different random generators in the two games, so they are compared as distributions:
each case is played once per seed in each game (original: startup RandSeed = seed; remake: the battle's draw
stream = seed). Metrics: each live slot's troops lost and final morale after the script. Test as in
difftest/stats.py: permutation test on the difference of means, Holm over all metrics here, ALPHA 0.05.

- melee30: heavy infantry 3,000 (quality 7) attacks the adjacent heavy infantry 3,000 (quality 7); the attacker
  ends its half-round (the melee is fought), then the defender ends its half-round. Seeds 1-30.
- archery30: archers 1,000 (quality 7) shoot a heavy infantry unit 2,000 at distance 2, three volleys over three
  attacker half-rounds (the defender passes in between). Seeds 1-30.
"""
ALPHA = 0.05
CASES = [
    {"id": "melee30", "note": "hi 3,000 attacks adjacent hi 3,000; both end",
     "attacker": [("hi", 3000, 7), ("li", 2000, 6)], "defender": [("hi", 3000, 7), ("li", 2000, 6)],
     "positions": {0: (3, 3), 1: (2, 2), 20: (4, 3), 21: (10, 9)}, "script": ["attack 0 20", "end", "end"],
     "slots": [0, 20], "seeds": list(range(1, 31))},
    {"id": "archery30", "note": "archers 1,000 shoot hi 2,000 at distance 2, three volleys",
     "attacker": [("ar", 1000, 7), ("hi", 2000, 7)], "defender": [("hi", 2000, 7), ("li", 1000, 6)],
     "positions": {0: (3, 3), 1: (2, 2), 20: (5, 3), 21: (12, 10)},
     "script": ["shoot 0 20", "end", "end", "shoot 0 20", "end", "end", "shoot 0 20"], "slots": [0, 20],
     "seeds": list(range(1, 31))},
]
SCENARIOS = [{"id": c["id"]} for c in CASES]
