#!/usr/bin/env python3
"""B8 icon ladder (battles plan §4 B8): at what troop counts does the battle screen draw a different icon for a unit of each type, on each side?

Method (L1, labelled synthetic; the game computes the sprite itself): Rome's army 0 and Gaul's army 10 of FLD-RG are each replaced by up to 12 units of ONE type
at chosen troop counts (quality 6, morale 65; positions never edited), the lab exe attacks, and at the placement phase (BATTLE01: Gaul placed on row y = 9,
Rome parked on row y = 0) the grid words (side*20 + 3*type + size class) are read from game memory and the window is screenshotted. The grid word IS the game's own
choice of sprite (B2: one icon image per word, `b2-icons-*.json`); the image-diff of the inner 26 x 26 of each tile is made too (`b8_analyze.py`). No block edit is
needed: a block edit would not make the game recompute the sprite (B3: it does not repair the grid). The battle is not played: the process is killed after the
shots (a fresh process per round).

  python3 runs/experiments/battles/b8_ladder.py [TYPE ...] [--max-rounds 8]

Rounds per type: (1) the ladder 100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32767 plus 1/4, 1/2, 1x, 2x of the standard battalion (capped at 32767), in chunks of
12, both sides identical; (2..) per side and per class change the bracket (lo, hi) of adjacent observed troop counts is probed: first the predicted threshold pair
(T-1, T) of the std/3 and 2*std/3 hypothesis, then evenly spaced values, until every bracket is one troop wide on BOTH sides. Output: `b8-ladder-<stamp>.jsonl`
(tracked, one line per round, append-only), the BATTLE01 save and the placement screenshot of each round in artifacts/ (release), SHA-256 in SAVES.sha256.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import stage  # noqa: E402
import trials as T  # noqa: E402
from harness.driver import DriverError, Game  # noqa: E402
from state import battle_block as BB  # noqa: E402
from b2_icons import rgb, tile_hash  # noqa: E402

MAXU = 12                      # Gaul's row: x = j + 1 (<= 12 units), Rome's parked row x = j (<= 13): 12 per side fit the 14-wide grid
BASE = [100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32767]


def ladder(typ):
    std = stage.STD[typ]
    vals = set(BASE) | {min(32767, round(std * f)) for f in (0.25, 0.5, 1, 2)}
    return sorted(vals)


def predicted(typ):
    """(T1, T2) = smallest troop counts of size class 1 and 2 under the hypothesis class = 0 below std/3, 1 below 2*std/3, else 2."""
    std = stage.STD[typ]
    t1 = next(t for t in range(1, 40000) if t * 3 >= std)
    t2 = next(t for t in range(1, 40000) if t * 3 >= 2 * std)
    return t1, t2


def spread(lo, hi, n):
    """up to n distinct integers strictly between lo and hi, evenly spaced."""
    inner = hi - lo - 1
    if inner <= 0:
        return []
    if inner <= n:
        return list(range(lo + 1, hi))
    return sorted({lo + round((hi - lo) * (i + 1) / (n + 1)) for i in range(n)} - {lo, hi})


def brackets(obs):
    """obs {troops: class} of one side and type -> [(lo, hi)] of adjacent observed points with a class change and a gap > 1, plus [(lo, hi)] already exact."""
    pts = sorted(obs.items())
    open_, exact = [], []
    for (a, ca), (b, cb) in zip(pts, pts[1:]):
        if ca != cb:
            (exact if b - a == 1 else open_).append((a, b))
    return open_, exact


def next_probes(typ, obs_side):
    """The troop counts to try next for ONE side (<= MAXU): the hypothesis pair at each class change not yet observed, then evenly spaced inside each open bracket."""
    t1, t2 = predicted(typ)
    open_, exact = brackets(obs_side)
    probes = []
    for lo, hi in open_:
        for t in (t for t in (t1 - 1, t1, t2 - 1, t2) if lo < t < hi):
            if t not in obs_side and t not in probes:
                probes.append(t)
    room = MAXU - len(probes)
    if open_ and room > 0:
        per = max(1, room // len(open_))
        for lo, hi in open_:
            for t in spread(lo, hi, per):
                if t not in probes and t not in obs_side and len(probes) < MAXU:
                    probes.append(t)
    return sorted(probes)[:MAXU]


def run_round(typ, tag, att_troops, def_troops, log):
    """One battle opened at the placement phase with the given troop counts; returns the round record (read back, memory slots, grid words, tile hashes)."""
    ops = [("units", C.ROME_ARMY, [(typ, t, T.Q) for t in att_troops]), ("morale", C.ROME_ARMY, T.MORALE),
           ("units", C.GAUL_ARMY, [(typ, t, T.Q) for t in def_troops]), ("morale", C.GAUL_ARMY, T.MORALE)]
    src = C.ART / C.FLD_RG_NAME
    tmp = C.ART / "start" / f"_tmp_{tag}.SAV"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    stage.edit(src, tmp, ops)
    start = C.keep(tmp, f"{tag}_start.SAV", C.ART / "start")
    tmp.unlink()
    g = Game(exe=C.LAB_EXE % 1)
    C.kill_stale(g)
    for f in C.D.G.glob("BATTLE*.SAV"):
        C.keep(f, f"stray_{tag}_{f.name}")
        f.unlink()
    rec = {"tag": tag, "type": typ, "level": "L1 from FLD-RG (labelled synthetic)", "build": "lab s1", "start_save": start.name, "start_sha256": C.sha(start),
           "attacker_troops": att_troops, "defender_troops": def_troops}
    try:
        g.start()
        rec["open_boxes"] = g.open(start)
        want = {C.ROME_ARMY: att_troops, C.GAUL_ARMY: def_troops}
        for i, a in ((C.ROME_ARMY, g.army_state(C.ROME_ARMY)), (C.GAUL_ARMY, g.army_state(C.GAUL_ARMY))):
            got = [(u["type"], u["troops"], u["quality"]) for u in a["units"]]
            if got != [(typ, t, T.Q) for t in want[i]] or a["morale"] != T.MORALE:
                raise DriverError("army %d read back %s morale %d, expected %s" % (i, got, a["morale"], want[i]))
        a0, a10 = g.army_state(C.ROME_ARMY), g.army_state(C.GAUL_ARMY)
        if (a0["x"], a0["y"]) != C.STAGE_TILE or (a10["x"], a10["y"]) != C.GAUL_TILE or a0["moves"] <= 0:
            raise DriverError("geometry: army 0 at %s moves %s, army 10 at %s" % ((a0["x"], a0["y"]), a0["moves"], (a10["x"], a10["y"])))
        g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
        g.click_tile(*C.GAUL_TILE, pause=0.0)
        T.wait_battle(g, log)
        time.sleep(2.5)
        win = g.find_windows(" v ")[0]
        rec["title"] = win[1]
        png = C.shot(g, f"{tag}_placement.png", window=str(win[0]), folder=C.ART / "shots")
        root = C.shot(g, f"{tag}_placement_root.png", folder=C.ART / "shots")
        st = g.battle_state()
        for _ in range(40):                       # the lab build writes BATTLE01.SAV at the battle's open
            if (C.D.G / "BATTLE01.SAV").exists():
                break
            time.sleep(0.25)
        saved = []
        for f in sorted(C.D.G.glob("BATTLE*.SAV")):
            saved.append(C.keep(f, f"{tag}_{f.name}", C.ART / "crafted_b8").name)
        w, h, raw = rgb(png)
        slots = []
        for s in st["slots"]:
            if not s["alive"]:
                continue
            word = st["grid"][BB.cell(s["x"], s["y"])]
            slots.append({"slot": s["slot"], "side": s["side"], "type": s["type"], "troops": s["troops"], "x": s["x"], "y": s["y"], "grid_word": word,
                          "size_class": word - 20 * s["side"] - 3 * BB.TYPES.index(s["type"]), "tile": tile_hash(w, raw, s["x"], s["y"])})
        rec.update({"half_round": st["half_round"], "y1": st["y1"], "grid_problems": len(BB.check_grid(st)), "slots": slots, "saves": saved,
                    "screenshot": png.name, "screenshot_root": root.name, "screenshot_sha256": C.sha(png), "status": "ok"})
        # the armies must be as staged (the AI side is re-sorted but not changed): the multiset of troops per side equals the cell's
        for side, want_t in ((0, att_troops), (1, def_troops)):
            got = sorted(s["troops"] for s in slots if s["side"] == side)
            if got != sorted(want_t):
                rec["status"] = "error: side %d slot troops %s != staged %s" % (side, got, sorted(want_t))
    except Exception as e:      # noqa: BLE001
        rec["status"] = "error: %s: %s" % (type(e).__name__, e)
        try:
            C.shot(g, f"error_{tag}.png", folder=C.ART / "shots")
        except Exception:       # noqa: BLE001
            pass
    finally:
        C.kill_stale(g)
        for f in C.D.G.glob("BATTLE*.SAV"):       # strays are kept by the next round's start; not deleted here
            C.keep(f, f"after_{tag}_{f.name}", C.ART / "crafted_b8")
            f.unlink()
    return rec


def observe(rec, obs):
    for s in rec.get("slots", []):
        obs[s["side"]][s["troops"]] = s["size_class"]


def run_type(typ, out, log, max_rounds=8):
    obs = {0: {}, 1: {}}
    chunks = [ladder(typ)[i:i + MAXU] for i in range(0, len(ladder(typ)), MAXU)]
    rounds = []
    for k, ch in enumerate(chunks):                      # pass 1: the ladder, both sides identical
        rec = run_round(typ, f"b8_{typ}_r{k + 1}", ch, ch, log)
        rec["round"] = k + 1
        rec["purpose"] = "ladder"
        rounds.append(rec)
        with open(out, "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        log("round", type=typ, round=k + 1, status=rec["status"], troops=ch)
        if rec["status"] != "ok" or rec["grid_problems"]:
            return rounds, "stopped: round %d %s grid_problems=%s" % (k + 1, rec["status"], rec.get("grid_problems"))
        observe(rec, obs)
    n = len(chunks)
    while n < max_rounds:
        p0, p1 = next_probes(typ, obs[0]), next_probes(typ, obs[1])
        if not p0 and not p1:
            return rounds, "done: every class change is one troop wide on both sides"
        n += 1
        rec = run_round(typ, f"b8_{typ}_r{n}", p0 or [1], p1 or [1], log)
        rec["round"], rec["purpose"] = n, "bisect (side 0 probes %s, side 1 probes %s)" % (p0, p1)
        rounds.append(rec)
        with open(out, "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        log("round", type=typ, round=n, status=rec["status"], side0=p0, side1=p1)
        if rec["status"] != "ok" or rec["grid_problems"]:
            return rounds, "stopped: round %d %s" % (n, rec["status"])
        observe(rec, obs)
    return rounds, "max rounds reached"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    types = [a for a in args if a in T.TYPES] or list(T.TYPES)
    mr = int(sys.argv[sys.argv.index("--max-rounds") + 1]) if "--max-rounds" in sys.argv else 8
    log = C.Log("b8-ladder")
    out = C.DATA / f"b8-ladder-{C.STAMP}.jsonl"
    for typ in types:
        rounds, why = run_type(typ, out, log, mr)
        log("type_done", type=typ, rounds=len(rounds), why=why)
        with open(out, "a") as f:
            f.write(json.dumps({"type": typ, "summary": why, "rounds": len(rounds)}) + "\n")
    print(out)


if __name__ == "__main__":
    main()
