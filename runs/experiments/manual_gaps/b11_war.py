#!/usr/bin/env python3
"""B11: an AI nation declaring war on the human seat. Staged: Carthage at war with nobody (its Celtiberia war ended with the -18
cooldown); Carthage's mobilisation 15, P(Carthage) 1,733 against P(Rome) 1,058 (8 x ratio 13.1 > 10), Rome its only eligible
neighbour (Numidia is its ally, Ptolemaic -10, Celtiberia -18). The code then declares with 1 in 10 per non-Winter turn.
End turns (cap given) until Carthage's relation to Rome is 3; every box is shot before it is answered; b11-war.jsonl per turn.

    python3 runs/experiments/manual_gaps/b11_war.py SEED [CAP]
"""
import struct
import sys

from mg import SAVES, DATA, start, snap, GAME_AREA
from turns import end_turns

SAVE = SAVES / "MG_B11_staged_carthage_celtiberia_-18.SAV"


def power(g, n):
    r = g.nation_rec(n)
    wealth = struct.unpack_from("<i", r, 0x430)[0]
    unity, mob = struct.unpack_from("<2h", r, 0x440)
    return {"wealth": wealth, "unity": unity, "mob": mob, "P": round(wealth / 20000 * unity / 100, 1)}


def measure(g):
    c = g.nation_state(1)
    wars = [k for k, v in c["relations"].items() if v == 3]
    return {"carthage_rel_rome": c["relations"]["Rome"], "rome_rel_carthage": g.nation_state(0)["relations"]["Carthage"],
            "carthage_wars": wars, "carthage": power(g, 1), "rome": power(g, 0), "season": g.calendar()["season"]}


if __name__ == "__main__":
    seed = int(sys.argv[1])
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    g, texts = start(SAVE, seed=seed)
    g.dismiss_popups()
    out = end_turns(g, "B11", seed, cap, measure, stop=lambda r: r["state"]["carthage_rel_rome"] == 3,
                    jsonl=DATA / "b11-war.jsonl")
    if out[-1]["state"]["carthage_rel_rome"] == 3:
        snap(g, f"MG_B11_seed{seed}_after_declaration_screen.png", "B11",
             "The human's screen at the turn start after Carthage declared war on Rome (Information panel news)", box=GAME_AREA,
             margin=0)
