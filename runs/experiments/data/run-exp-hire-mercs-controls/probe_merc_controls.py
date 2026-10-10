"""Controls of the Recruit mercenary unit dialog (2026-10-08), for hire_mercs without fixed coordinates.
Fixture saves/run0-start-AUTO0720-seed12345.SAV, army 1 next to Heraclea. python3 probe_merc_controls.py"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import fresh_save
from pathlib import Path
g = fresh_save((Path(__file__).resolve().parents[4] / "saves/run0-start-AUTO0720-seed12345.SAV"))
w = g.army_tool(1, "mercs", "Recruit mercenary unit")
print("window", w[1:], flush=True)
for c in g.controls("Recruit mercenary unit"):
    print(c, flush=True)
