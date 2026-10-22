#!/usr/bin/env python3
"""run-exp-sav-fleetmoves107: does a new fleet keep its table index's leftover `moves`? (conquest issue #107)

    python3 runs/experiments/sav-inert107/fleetmoves.py craft   # T5 inputs into artifacts/run-exp-sav-fleetmoves107/inputs
    python3 runs/experiments/sav-inert107/fleetmoves.py T4|T5

T4  natural path from saves/fleet-split-antium-0734.SAV: memory dumps of the fleet table around Scuttle fleet 2,
    End turn (compaction), Build fleet (10 ships); Save As; End turn.
T5  crafted: fleet 3 (under construction) given to Rome with countdown 2 and moves 17; control with moves 0; End turn.

Logs: runs/experiments/data/run-exp-sav-fleetmoves107/<test>-<stamp>.jsonl (tracked). Saves: artifacts/run-exp-sav-fleetmoves107/
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
sys.path.insert(0, str(ROOT / "scripts"))
import sav_atlas_coverage as cov  # noqa: E402

STAMP = time.strftime("%Y%m%d-%H%M%S")
DATA = ROOT / "runs/experiments/data/run-exp-sav-fleetmoves107"
BASE = ROOT / "artifacts/run-exp-sav-fleetmoves107"
SRC = ROOT / "saves/fleet-split-antium-0734.SAV"
FLEET_BASE, FLEET_LEN, FLEET_COUNT = 0x49C26C, 26, 0x4A0326
NAMES = ("x", "y", "route_x", "route_y", "owner", "countdown", "moves", "supplies", "money", "ships", "city_or_cond",
         "army", "cell")
SEED = 12345


def craft():
    out = BASE / "inputs"
    out.mkdir(parents=True, exist_ok=True)
    b = SRC.read_bytes()
    f0 = {r: o for r, o, _ in cov.frame(b)[0]}["fleet"]
    o = f0 + FLEET_LEN * 3
    assert struct.unpack_from("<h", b, o + 10)[0] > 0, "fleet 3 must be under construction"
    for moves, name in ((17, "T5S_0734_fleet3_moves17.SAV"), (0, "T5C_0734_fleet3_moves0.SAV")):
        c = bytearray(b)
        struct.pack_into("<hhh", c, o + 8, 0, 2, moves)          # owner Rome, countdown 2, moves
        cov.frame(bytes(c))
        with open(out / name, "xb") as fh:
            fh.write(bytes(c))
        print(name, hashlib.sha256(bytes(c)).hexdigest())


def table(g, extra=2):
    """The fleet table from game memory, F records plus `extra` beyond the count."""
    n = g.i16(FLEET_COUNT)
    raw = g.mem(FLEET_BASE, FLEET_LEN * (n + extra))
    return n, [dict(zip(NAMES, struct.unpack_from("<13h", raw, FLEET_LEN * k)), index=k, beyond_count=k >= n)
               for k in range(n + extra)]


def main():
    if sys.argv[1] == "craft":
        return craft()
    from harness import driver
    test = sys.argv[1]
    DATA.mkdir(parents=True, exist_ok=True)
    art = BASE / STAMP
    art.mkdir(parents=True, exist_ok=True)
    fh = open(DATA / f"{test}-{STAMP}.jsonl", "x")

    def log(step, **kw):
        rec = dict(t=time.strftime("%H:%M:%S"), step=step, **kw)
        fh.write(json.dumps(rec) + "\n"); fh.flush(); print(json.dumps(rec)[:300], flush=True)

    def keep(src, name):
        dst = art / name
        shutil.copyfile(src, dst)
        log("kept", file=name, sha256=hashlib.sha256(dst.read_bytes()).hexdigest())

    def autosave():
        line = (driver.G / "AUTOSAVE.LOG").read_text().splitlines()[-1]
        return driver.G / line.split()[1]

    g = driver.Game(log=lambda *a: None)
    log("start", test=test, exe=driver.EXE, stamp=STAMP)
    if test == "T4":
        g.load(SRC, seed=SEED)
        log("loaded", save=SRC.name, seed_line=g.seed_line, table=table(g))
        texts = g.scuttle_fleet(2)
        log("scuttle_fleet_2", texts=texts, table=table(g))
        log("end_turn", texts=str(g.end_turn(strict_confirm=True)), table=table(g))
        keep(autosave(), "T4_after_scuttle_autosave.SAV")
        texts = g.build_fleet(10)
        log("build_fleet_10", texts=texts, notices=getattr(g, "build_fleet_notices", None), table=table(g))
        keep(g.save_as(f"T4_{STAMP}_after_build.SAV"), "T4_after_build_saveas.SAV")
        log("end_turn", texts=str(g.end_turn(strict_confirm=True)), table=table(g))
        keep(autosave(), "T4_after_build_next_autosave.SAV")
    elif test == "T5":
        for tag, name in (("T5S", "T5S_0734_fleet3_moves17.SAV"), ("T5C", "T5C_0734_fleet3_moves0.SAV")):
            g.load(BASE / "inputs" / name, seed=SEED)
            log("loaded", tag=tag, save=name, seed_line=g.seed_line, table=table(g))
            log("end_turn", tag=tag, texts=str(g.end_turn(strict_confirm=True)), table=table(g))
            keep(autosave(), f"{tag}_after_end_turn_autosave.SAV")
    g.kill()
    log("done")


if __name__ == "__main__":
    main()
