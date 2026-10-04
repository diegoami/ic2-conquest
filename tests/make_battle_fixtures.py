#!/usr/bin/env python3
"""B1 fixtures (battles plan §4 B1), built NATURAL on the normal seed build (seed 12345) and built TWICE, byte compare:

  FLD-RG   `1_rome_270_winter_11.sav` (research request's start save, turn 0743, Rome's turn): Rome's army 0 walked to (86,28), next to Gaul's
           army 10 at (85,28), moves left (6 of 8 used). The battle starts when army 0 clicks (85,28): the sweep's L1 start state.
  FLD-R0G  army 0 alone: the same save (army 0 is the only army walked; army 13 stays at (93,28)) - NOT BUILT, it would be identical.
  SIE-FEL / SIE-TAU (siege approaches) and terrain fixtures (B9): not Stage 1, not built.

    python3 -m tests.make_battle_fixtures           # needs the game; writes artifacts/run-exp-battle-sweep/FLD-RG_*.SAV (git-ignored) + the
                                                    #   tracked report fixtures-build-<stamp>.json (SHA-256, byte comparison, pre-state of both armies)
Exit 1 if the two builds are not byte-identical. The fixtures are NEVER committed (rule 1 / plan §9.5): release run-exp-battle-sweep.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runs" / "experiments" / "battles"))
import common as C  # noqa: E402
from harness.driver import DriverError, Game  # noqa: E402
from state import battle, sav  # noqa: E402


def start_save():
    dst = C.ART / C.START_NAME
    if not dst.exists():
        old = C.ROOT / "artifacts" / "run-exp-battle-probe" / C.START_NAME
        if old.exists():
            C.keep(old, folder=C.ART)
        else:
            subprocess.run(["gh", "release", "download", "run-1-rome", "--repo", "diegoami/imp_conquest_fixtures", "--pattern", C.START_NAME,
                            "--dir", str(C.ART)], check=True)
    return dst


def build_once(start, tag, log):
    g = Game(exe=C.NORMAL_EXE)
    try:
        t0 = time.time()
        texts = g.load(start, seed=12345)
        log("loaded", tag=tag, seconds=round(time.time() - t0, 1), boxes=texts, calendar=g.calendar())
        for leg in C.LEGS:
            pos, boxes = g.move(C.ROME_ARMY, *leg)
            log("move", tag=tag, to=leg, now=tuple(pos), boxes=boxes)
        if tuple(g.army_pos(C.ROME_ARMY)) != C.STAGE_TILE:
            raise DriverError("army 0 is at %s, not %s" % (g.army_pos(C.ROME_ARMY), C.STAGE_TILE))
        st = {"army0": g.army_state(0), "army10": g.army_state(10)}
        log("pre_attack_state", tag=tag, army0=st["army0"], army10=st["army10"])
        p = g.save_as(f"FLD-RG_build_{tag}.SAV")
        return Path(p).read_bytes(), st
    finally:
        C.kill_stale(g)


def main():
    log = C.Log("fixtures-build")
    start = start_save()
    log("start_save", file=start.name, sha256=C.sha(start))
    blobs, states = [], []
    for tag in ("a", "b"):
        b, st = build_once(start, tag, log)
        blobs.append(b)
        states.append(st)
    same = blobs[0] == blobs[1]
    diff = [i for i in range(min(map(len, blobs))) if blobs[0][i] != blobs[1][i]]
    final = C.ART / C.FLD_RG_NAME
    final.parent.mkdir(parents=True, exist_ok=True)
    kept = C.keep(C.D.G / "FLD-RG_build_a.SAV", C.FLD_RG_NAME)
    C.keep(C.D.G / "FLD-RG_build_b.SAV", "FLD-RG_build_b.SAV")
    s = sav.load(str(kept))
    rep = {"fixture": "FLD-RG", "file": kept.name, "sha256": C.sha(kept), "byte_identical_two_builds": same, "sizes": [len(x) for x in blobs],
           "differing_bytes": len(diff) + abs(len(blobs[0]) - len(blobs[1])), "first_differing_offsets": diff[:10],
           "turn": s["turn"], "battle_flag": s["battle_flag"], "current_nation": s["current_nation"],
           "army0": {k: v for k, v in states[0]["army0"].items() if k != "units"} | {"by_type": battle.by_type(states[0]["army0"])},
           "army10": {k: v for k, v in states[0]["army10"].items() if k != "units"} | {"by_type": battle.by_type(states[0]["army10"])},
           "units_army0": states[0]["army0"]["units"], "units_army10": states[0]["army10"]["units"],
           "FLD-R0G": "not built: identical to FLD-RG (army 0 is alone in both)", "SIE-FEL/SIE-TAU/terrain": "not built (not Stage 1)"}
    (C.DATA / f"fixtures-build-{C.STAMP}.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps({k: rep[k] for k in ("file", "sha256", "byte_identical_two_builds", "differing_bytes")}, indent=1))
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
