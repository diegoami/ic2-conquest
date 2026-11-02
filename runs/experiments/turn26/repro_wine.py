#!/usr/bin/env python3
"""Seleucid turn 26, Wine side (owner 2026-11-02, the targeted Windows repro): replay ONE turn from its save.

    python3 runs/experiments/turn26/repro_wine.py SAVE RANDSEED OUT_DIR

A fresh seeded process opens SAVE (the campaign's t26-a00 checkpoint), writes RANDSEED (the value the campaign logged with
IC2_LOG_RANDSEED right before turn 26's End turn) into Delphi RandSeed 0x45E030, and clicks End turn. Loading does not
reseed, and RandSeed is the game's whole random state, so the AI seats should replay as in the campaign. Afterwards it
records the windows, the battle flag 0x4A0B7C, the seat 0x4A0320, RandSeed and a screenshot in OUT_DIR/result.json. A
freeze shows as end_turn timing out. Autosaves of the game folder are moved aside first (rule 6).
"""
import json
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from harness.driver import BATTLE_FLAG, CUR_NATION, G, DriverError, Game  # noqa: E402

RAND_SEED = 0x45E030


def main():
    save, seed, out = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=False)
    res = {"save": str(save), "randseed": seed, "steps": []}
    g = Game()
    g.move_aside(sorted(G.glob("AUTO*")))
    try:
        res["load_boxes"] = g.load(save, seed=12345)
        with open(f"/proc/{g.pid}/mem", "r+b") as f:
            f.seek(RAND_SEED)
            before = struct.unpack("<I", f.read(4))[0]
            f.seek(RAND_SEED)
            f.write(struct.pack("<I", seed))
        res["randseed_after_load"] = before
        res["randseed_written"] = struct.unpack("<I", g.mem(RAND_SEED, 4))[0]
        t0 = time.time()
        try:
            line, texts = g.end_turn(timeout=150)
            res["end_turn"] = {"autosave": line, "texts": texts, "seconds": round(time.time() - t0, 1)}
        except Exception as e:
            res["end_turn"] = {"error": f"{type(e).__name__}: {e}", "seconds": round(time.time() - t0, 1)}
        time.sleep(15)          # the campaign's battle window appeared after the autosave
        res["after"] = {"windows": [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")],
                        "battle_flag": g.in_battle(), "cur_nation": g.i16(CUR_NATION),
                        "randseed": struct.unpack("<I", g.mem(RAND_SEED, 4))[0]}
        g.shot(out / "after.png")
        res["frozen_like_campaign"] = any("Seleucid to move units" in w[0] for w in res["after"]["windows"]) \
            and not res["after"]["battle_flag"]
    finally:
        (out / "result.json").write_text(json.dumps(res, indent=1, default=str))
        print(json.dumps(res, indent=1, default=str)[:3000])
        g.kill()


if __name__ == "__main__":
    main()
