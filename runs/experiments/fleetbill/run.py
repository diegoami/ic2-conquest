#!/usr/bin/env python3
"""run-exp-fleet-bill: does the quarterly bill charge a fleet under construction? (manual #133, item 12 of research PR #57)

    python3 runs/experiments/fleetbill/run.py

From M133_session1_AUTO0725.SAV (Rome, 270 BC Spring week 11: its End turn runs the quarterly tick), seed 12345, two
branches: A ends the turn; B orders a 50-ship fleet, then ends the turn. Code (FUN_00451B40) bills 3 x ships only for a
launched fleet (countdown -1); if so, B's treasury after the tick = A's - 500 (the build cost) exactly, else 150 lower.
Logs: runs/experiments/data/run-exp-fleet-bill/ (tracked); saves: artifacts/run-exp-fleet-bill/<stamp>/ (unique names,
never deleted; CLAUDE.md rule 6).
"""
import hashlib, json, shutil, struct, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from harness import driver  # noqa: E402
import sav_atlas_coverage as cov  # noqa: E402

STAMP = time.strftime("%Y%m%d-%H%M%S")
DATA = ROOT / "runs/experiments/data/run-exp-fleet-bill"
ART = ROOT / "artifacts/run-exp-fleet-bill" / STAMP
SRC = ROOT / "artifacts/run-exp-manual133/saves/M133_session1_AUTO0725.SAV"
TREASURY = 0x474670 + 0x438          # Rome's treasury (i32)


def rome(path):
    b = Path(path).read_bytes()
    blocks, facts = cov.frame(b)
    pos = {r: o for r, o, _ in blocks}
    n0, f0 = pos["nation"], pos.get("fleet", 0)
    fleets = [struct.unpack_from("<13h", b, f0 + 26 * j) for j in range(facts["fleets"])]
    own = [dict(ships=f[9], countdown=f[5]) for f in fleets if f[4] == 0]
    return dict(treasury=struct.unpack_from("<i", b, n0 + 0x438)[0], fleets=own,
                calendar=dict(zip(("week", "year_bc", "season"), (facts.get("week"), facts.get("year_bc"), facts.get("season")))))


def main():
    DATA.mkdir(parents=True, exist_ok=True); ART.mkdir(parents=True, exist_ok=True)
    fh = open(DATA / f"run-{STAMP}.jsonl", "x")

    def log(step, **kw):
        rec = dict(t=time.strftime("%H:%M:%S"), step=step, **kw)
        fh.write(json.dumps(rec, default=str) + "\n"); fh.flush(); print(json.dumps(rec, default=str)[:400], flush=True)

    log("start", exe=driver.EXE, src=SRC.name, src_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(), src_rome=rome(SRC))
    g = driver.Game(log=lambda *a: None)
    for tag, ships in (("A_nofleet", 0), ("B_fleet50", 50)):
        g.load(SRC, seed=12345)
        log("loaded", tag=tag, seed_line=g.seed_line, treasury=g.i32(TREASURY) if hasattr(g, "i32") else struct.unpack("<i", g.mem(TREASURY, 4))[0])
        if ships:
            texts = g.build_fleet(ships)
            log("build_fleet", tag=tag, ships=ships, texts=texts, treasury=struct.unpack("<i", g.mem(TREASURY, 4))[0])
        log("end_turn", tag=tag, texts=str(g.end_turn(strict_confirm=True)))
        line = (driver.G / "AUTOSAVE.LOG").read_text().splitlines()[-1]
        dst = ART / f"FB_{tag}_after_quarter.SAV"
        shutil.copyfile(driver.G / line.split()[1], dst)
        log("kept", tag=tag, file=dst.name, sha256=hashlib.sha256(dst.read_bytes()).hexdigest(), rome=rome(dst))
    g.kill()
    log("done")


if __name__ == "__main__":
    main()
