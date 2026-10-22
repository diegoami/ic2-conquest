#!/usr/bin/env python3
"""run-exp-sav-aboard107: a natural embark, for the aboard-link invariants of issue #107.

    python3 runs/experiments/sav-inert107/aboard.py

From saves/fleet-port-antium-0734.SAV (seed build, seed 12345): army 0 (101,45) embarks on fleet 2 (101,46); memory
dumps of army 0, fleet 2 and the two map cells before and after; Save As; End turn; the autosave is kept.
Logs: runs/experiments/data/run-exp-sav-aboard107/aboard-<stamp>.jsonl (tracked). Saves: artifacts/run-exp-sav-aboard107/
<stamp>/ (unique names, never deleted; CLAUDE.md rule 6).
"""
import hashlib
import json
import shutil
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness import driver  # noqa: E402

STAMP = time.strftime("%Y%m%d-%H%M%S")
DATA = ROOT / "runs/experiments/data/run-exp-sav-aboard107"
ART = ROOT / "artifacts/run-exp-sav-aboard107" / STAMP
SRC = ROOT / "saves/fleet-port-antium-0734.SAV"
ARMY, FLEET = 0, 2


def state(g):
    a = struct.unpack("<8h", g.mem(0x47C1EC + 656 * ARMY, 16))
    f = struct.unpack("<13h", g.mem(0x49C26C + 26 * FLEET, 26))
    cell = lambda x, y: struct.unpack("<h", g.mem(0x45E870 + 2 * (x * 140 + y), 2))[0]
    return dict(army=dict(zip(("x", "y", "owner", "moves", "cell", "supplies", "money", "morale"), a)),
                fleet=dict(zip(("x", "y", "route_x", "route_y", "owner", "countdown", "moves", "supplies", "money",
                                "ships", "condition", "army", "cell"), f)),
                map_at_army_start=cell(101, 45), map_at_fleet=cell(f[0], f[1]), fleets=g.i16(0x4A0326), armies=g.i16(0x4A0324))


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    fh = open(DATA / f"aboard-{STAMP}.jsonl", "x")

    def log(step, **kw):
        rec = dict(t=time.strftime("%H:%M:%S"), step=step, **kw)
        fh.write(json.dumps(rec) + "\n"); fh.flush(); print(json.dumps(rec)[:400], flush=True)

    def keep(src, name):
        dst = ART / name
        shutil.copyfile(src, dst)
        log("kept", file=name, sha256=hashlib.sha256(dst.read_bytes()).hexdigest())

    g = driver.Game(log=lambda *a: None)
    log("start", exe=driver.EXE, stamp=STAMP)
    g.load(SRC, seed=12345)
    log("loaded", save=SRC.name, seed_line=g.seed_line, state=state(g))
    texts = g.embark(ARMY, FLEET)
    log("embark", texts=texts, state=state(g))
    keep(g.save_as(f"AB_{STAMP}_aboard.SAV"), "AB_aboard_saveas.SAV")
    log("end_turn", texts=str(g.end_turn(strict_confirm=True)), state=state(g))
    line = (driver.G / "AUTOSAVE.LOG").read_text().splitlines()[-1]
    keep(driver.G / line.split()[1], "AB_aboard_next_autosave.SAV")
    g.kill()
    log("done")


if __name__ == "__main__":
    main()
