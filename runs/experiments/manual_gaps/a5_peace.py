#!/usr/bin/env python3
"""A5: the post-battle "Offer of peace" box. D-LOSS set-up of findings/2026-10-05-battle-peace-offer.md on the M133 game:
Rome's army 0 (one 3,000 LI battalion) moves next to Gaul's army 9 (cut to a third) and attacks it; Computer general; after the
Battle ended box the Offer of peace opens when the draw allows (about 40 % once the three tests hold). Tries seeds until it opens;
shoots the box and answers No. Results appended to a5-trials.jsonl.

    python3 runs/experiments/manual_gaps/a5_peace.py SEED [SEED ...]
"""
import json
import sys
import time

from mg import SAVES, DATA, start, snap, log, GAME_AREA, save_as

SAVE = SAVES / "MG_A5_staged_rome0_3000li_gaul9_third_0722.SAV"


def trial(seed):
    g, texts = start(SAVE, seed=seed)
    g.dismiss_popups()
    rec = {"seed": seed, "load_boxes": texts}
    pos, t = g.move(0, 99, 37)
    rec["moved_to"] = pos
    g.select_army(0, *pos)
    g.click_tile(98, 36, pause=1.5)
    rec["click_boxes"] = g.dismiss_popups()
    for _ in range(30):
        if g.in_battle() and g.find_windows(" v "):
            break
        time.sleep(0.5)
    rec["battle"] = [w[1] for w in g.find_windows(" v ")]
    if not rec["battle"]:
        rec["result"] = "no battle"
        return rec
    res = g.play_battle(on_dialog=None)
    rec["end_turn_clicks"] = res["end_turn_clicks"]
    time.sleep(3)
    box = g.find_windows("^Offer of peace$")
    rec["peace_box"] = bool(box)
    rec["army0"] = g.army_state(0)["troops"]
    rec["army9"] = g.army_state(9)["troops"]
    if box:
        snap(g, f"MG_A5_offer_of_peace_seed{seed}.png", "A5",
             "Offer of peace box after Rome lost a battle it started (Gaul offers peace); answered No", window=box[0], save=SAVE.name)
        snap(g, f"MG_A5_offer_of_peace_seed{seed}_context.png", "A5", "Context: the Offer of peace box over the game screen",
             box=GAME_AREA, margin=0, save=SAVE.name)
        r = g.answer_battle_peace(False)
        rec["answer"] = {k: r[k] for k in ("button", "clicks", "closed", "text")}
        time.sleep(1.5)
        rec["rel_rome_gaul_after"] = g.nation_state(0)["relations"]["Gaul"]
        save_as(g, f"MG_A5_after_no_seed{seed}.SAV")
    return rec


if __name__ == "__main__":
    for s in map(int, sys.argv[1:]):
        rec = trial(s)
        with (DATA / "a5-trials.jsonl").open("a") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), **rec}) + "\n")
        log("A5_trial", **rec)
        print(rec)
        if rec.get("peace_box"):
            break
