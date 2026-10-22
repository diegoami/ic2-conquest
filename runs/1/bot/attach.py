"""Run 1 debug helper: attach to the running game and print Rome's queue, Roman armies and the open windows.

    python3 runs/1/bot/attach.py
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from turn import RunGame  # noqa: E402


def attach():
    g = RunGame()
    g.__dict__["_pid"] = int(subprocess.check_output(["pgrep", "-f", "^Imperial Conquest"]).split()[0])
    return g


if __name__ == "__main__":
    g = attach()
    r = g.rome()
    print("turn", g.turn_number(), "treasury", r["treasury"], "mob", r["mobilization"])
    for q in r["recruit_slots"]:
        print("  slot", q)
    for i, a in g.roman_armies().items():
        print("  army", i, a["x"], a["y"], a["troops"], a["supplies"], a["moves"], [(u["type"], u["troops"], u["quality"]) for u in a["units"]])
    print([w[1:] for w in g.find_windows(".")])
