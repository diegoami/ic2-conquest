"""#230 batch 4: walks blocked by an own city on the line, found by the #232 campaign (rome-rulebot1-5t, turn 1:
army 1 ordered from (120,53) to (99,32) ended at (115,49) in the original and (118,52) in the remake, whose reply
was "spending 2 of 8 moves"). Written 2026-10-29 before these cases ran.

On the exact diagonal from (120,53), the second tile (118,51) is Venusia, Rome's own city (a marker blocks).
"""
from difftest.cases.orders230_b1 import case

CASES = [
    case("walk-city-on-line", "army 1 from (120,53) toward (99,32): Venusia (118,51) is on the line",
         {"op": "move", "army": 1, "x": 99, "y": 32}),
    case("walk-city-on-line-near", "army 1 toward (116,49): the same line, a target within its moves",
         {"op": "move", "army": 1, "x": 116, "y": 49}),
    case("walk-line-clear", "army 1 toward (120,45): a line with no marker (control)",
         {"op": "move", "army": 1, "x": 120, "y": 45}),
    # walk-line-clear's target (120,45) turned out to be SEA (the command gap of move-sea), so it is no control.
    # Added after it ran: a land line with no marker.
    case("walk-line-clear-land", "army 1 north to (120,48): a clear land line (control)",
         {"op": "move", "army": 1, "x": 120, "y": 48}),
]
