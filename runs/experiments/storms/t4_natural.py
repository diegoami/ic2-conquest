#!/usr/bin/env python3
"""T4 natural loss: nothing edited. Carthage's and Ptolemaic's fleets stay where they are (calm sea, away from their cities) while both
humans only End turn, from the two-human start (T1_0720_s13_Carthage.SAV, Carthage's seat at 0720), until a fleet is lost at sea
("A fleet belonging to X is lost at sea.") or MAX_ROUNDS end turns have been made. Every autosave is kept and read: condition, ships,
supplies of both fleets at each seat's turn start, and the news lines about fleets.

    python3 runs/experiments/storms/t4_natural.py SEED [MAX_END_TURNS]
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import G, Game  # noqa: E402
from state import sav  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-storms"
START = ROOT / "artifacts" / "run-exp-fleet-battles" / "T1_0720_s13_Carthage.SAV"
NAMES = {1: "Carthage", 3: "Ptolemaic"}


def row(s, label):
    fl = {NAMES[f["owner"]]: (f["ships"], f["condition"], f["supplies"], (f["x"], f["y"])) for f in s["fleets"] if f["owner"] in NAMES}
    return {"save": label, "turn": s["turn"], "seat": s["seat_index"], "season": s["season"], "fleets": fl,
            "news": [n for n in s["news"][-80:] if "fleet" in n.lower() and ("storm" in n.lower() or "lost at sea" in n.lower())]}


def main(seed, max_ends=30):
    g = Game()
    log = []
    try:
        g.load(START, seed=seed)
        log.append(row(sav.load(str(START)), START.name))
        for i in range(max_ends):
            name, texts = g.end_turn(timeout=300)
            s = sav.load(str(G / name))
            dst = OUT / f"NAT_seed{seed}_{i + 1:02d}_{s['turn']:04d}_seat{s['seat_index']:02d}.SAV"
            shutil.copy(G / name, dst)
            r = row(s, dst.name) | {"end_turn_texts": texts}
            log.append(r)
            print(r["save"], r["turn"], r["fleets"], r["news"][-2:], flush=True)
            (OUT / f"t4_natural_seed{seed}.json").write_text(json.dumps(log, indent=1, default=str))
            if len(r["fleets"]) < 2:        # one of the two tracked fleets is gone (a "lost at sea" line may be an AI fleet's)
                break
    finally:
        g.kill()


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 30)
