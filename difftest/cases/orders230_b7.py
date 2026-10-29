"""#230 batch 7 / research #42: human fleet moves where the original's handler walks twice (written 2026-10-30 before running).

From saves/fleet-port-antium-0734.SAV, Rome's fleet 2 (30 ships, 29 moves) at (101,46). The Unicorn search on this save's
own map (runs/experiments/fleet42/search_real_map.py, artifacts search-antium-fleet2-v1.json) predicts:
- toward (88,32): one walker call ends at (93,37) with 19 moves left; the human handler's second call reaches (88,32), 14 left.
- toward (87,47): one call (89,48), 16 left; the handler (87,47), 14 left.
Prediction: the original ends at the handler's cell; the remake (one MovementWalker.Walk) at the one-call cell.
"""
from pathlib import Path

from difftest.cases.orders230_b1 import case

PORT = str(Path(__file__).resolve().parents[2] / "saves/fleet-port-antium-0734.SAV")

CASES = [
    case("fleet-second-walk-88-32", "fleet 2 toward (88,32)", {"op": "move_fleet", "fleet": 2, "x": 88, "y": 32}, start=PORT),
    case("fleet-second-walk-87-47", "fleet 2 toward (87,47)", {"op": "move_fleet", "fleet": 2, "x": 87, "y": 47}, start=PORT),
]
