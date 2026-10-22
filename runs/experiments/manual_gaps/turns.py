"""End-turn loop shared by B10 and B11: every box that `end_turn` would dismiss is shot first (crop to the box), each autosave is
kept as MG_<tag>_seed<s>_AUTOnnnn.SAV, and a per-turn record is appended to a jsonl."""
import json
import time

from harness.driver import G
from mg import snap, keep_save, DATA, log


def shoot_boxes(g, tag, seed, counter):
    """Wrap g.dismiss_popups so that each box is shot before it is answered."""
    orig = g.dismiss_popups

    def wrapped(*a, **kw):
        for w in g.message_boxes():
            counter[0] += 1
            try:
                t = g.turn_number()
            except Exception:
                t = 0
            try:
                snap(g, f"MG_{tag}_seed{seed}_t{t:04d}_box{counter[0]:03d}.png", tag,
                     "Box shown during End turn (auto-shot before OK)", window=w, delay=0.3)
            except SystemExit:
                pass
        return orig(*a, **kw)
    g.dismiss_popups = wrapped


def end_turns(g, tag, seed, n, measure, stop=None, jsonl=None):
    counter = [0]
    shoot_boxes(g, tag, seed, counter)
    out = []
    rec0 = {"tag": tag, "seed": seed, "turn": g.turn_number(), "state": measure(g), "phase": "start"}
    out.append(rec0)
    with jsonl.open("a") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), **rec0}) + "\n")
    for k in range(n):
        name, texts = g.end_turn(peace=False)
        try:
            keep_save(G / name, f"MG_{tag}_seed{seed}_{name}")
        except SystemExit:
            pass
        rec = {"tag": tag, "seed": seed, "k": k + 1, "autosave": name, "turn": g.turn_number(),
               "calendar": g.calendar(), "boxes": texts, "state": measure(g)}
        out.append(rec)
        with jsonl.open("a") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), **rec}) + "\n")
        print(json.dumps(rec)[:600])
        if stop and stop(rec):
            break
    log(f"{tag}_done", seed=seed, turns=len(out) - 1)
    return out
