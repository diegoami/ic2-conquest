#!/usr/bin/env python3
"""A6: the End of Game window (THumanFalls) for three reasons, each from a staged save: End turn, shoot the window (crop and
context), read it, press OK, shoot the screen after.

    python3 runs/experiments/manual_gaps/a6_eog.py a|b|c
"""
import json
import sys
import time

from harness.driver import GameOver
from mg import SAVES, DATA, start, snap, log, GAME_AREA, keep_save, G

CASES = {
    "a": ("MG_A6a_staged_251bc_winter_w11.SAV", "250 BC reached (calendar staged to 251 BC Winter week 11)"),
    "b": ("MG_A6b_staged_rome_treasury_-30000.SAV", "deposition for debt (Rome's treasury staged to -30,000)"),
    "c": ("MG_A6c_staged_rome_cities_count_334.SAV", "victory (Rome's city-count word staged to 334)"),
}

if __name__ == "__main__":
    k = sys.argv[1]
    name, why = CASES[k]
    g, texts = start(SAVES / name)
    g.dismiss_popups()
    rec = {"case": k, "save": name, "why": why, "load_boxes": texts}
    try:
        rec["end_turn"] = g.end_turn()
        rec["result"] = "no End of Game window"
    except GameOver as e:
        rec["result"] = "End of Game"
        rec["ocr"] = str(e)
        time.sleep(1.5)
        w = g.find_windows("^End of Game$")[0]
        rec["geometry"] = list(w[2:])
        snap(g, f"MG_A6{k}_end_of_game_window.png", "A6", f"End of Game window: {why}", window=w)
        snap(g, f"MG_A6{k}_end_of_game_context.png", "A6", f"Context: the End of Game window over the game screen ({why})",
             box=GAME_AREA, margin=0)
        log_lines = (G / "AUTOSAVE.LOG").read_text().splitlines() if (G / "AUTOSAVE.LOG").exists() else []
        if log_lines:
            last = log_lines[-1].split()[1]
            rec["autosave"] = last
            try:
                keep_save(G / last, f"MG_A6{k}_{last}")
            except SystemExit:
                pass
        try:
            cs = g.controls("End of Game")
            rec["controls"] = [(c["cls"], c["text"]) for c in cs]
            ok = g.control(cs, text="OK")
            for _ in range(3):
                g.click_control(ok, pause=1.5)
                if not g.find_windows("^End of Game$"):
                    break
        except Exception as e:  # noqa: BLE001
            rec["ok_error"] = repr(e)
        time.sleep(8)
        rec["after_windows"] = [w[1] for w in g.find_windows(".")]
        snap(g, f"MG_A6{k}_after_ok_screen.png", "A6", f"The screen after OK on the End of Game window ({why})", box=GAME_AREA,
             margin=0)
    with (DATA / "a6-eog.jsonl").open("a") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), **rec}) + "\n")
    log("A6", **rec)
    print(rec)
