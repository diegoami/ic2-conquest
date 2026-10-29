"""#231 first cases: staged battles (difftest/tactical.py), movement phase, both sides human, scripted commands.

Slots 0-19 are the attacker's (Rome's army 0), 20-39 the defender's (army 13, Carthage). Board 14 x 12.
"""
CASES = [
    {"id": "walk-1", "note": "each side walks one unit, then ends its half-round",
     "attacker": [("hi", 3000, 7), ("li", 3000, 6)], "defender": [("hi", 3000, 7), ("li", 3000, 6)],
     "positions": {0: (3, 3), 1: (2, 2), 20: (10, 8), 21: (11, 9)},
     "script": ["move 0 5 4", "move 1 4 4", "end", "move 20 8 7", "move 21 9 8", "end"]},
    {"id": "shoot-li", "note": "light infantry shoots an enemy in range, then the defender ends",
     "attacker": [("li", 3000, 7), ("hi", 2000, 7)], "defender": [("hi", 2000, 7), ("ar", 1000, 7)],
     "positions": {0: (3, 3), 1: (2, 2), 20: (5, 4), 21: (10, 9)},
     "script": ["shoot 0 20", "end", "end"]},
    {"id": "melee-target", "note": "a heavy infantry unit targets an adjacent enemy; the half-round's melee follows End",
     "attacker": [("hi", 3000, 7), ("li", 2000, 6)], "defender": [("hi", 3000, 7), ("li", 2000, 6)],
     "positions": {0: (3, 3), 1: (2, 2), 20: (4, 3), 21: (10, 9)},
     "script": ["attack 0 20", "end", "end"]},
]
