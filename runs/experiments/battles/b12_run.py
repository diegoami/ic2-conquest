#!/usr/bin/env python3
"""B12 trial runner (docs/tasks/battles-b7-b12.md): one battle per fresh process on the HOOKED lab exe of the seed, Rome driven by a scripted plan (`p-hold`, `p-focus`,
`p-cav`: b12_plans.py) or by Computer general (`cg`, the pair's baseline: `Game.play_battle`), Gaul always by Computer general.

    export IC2_WORK=~/ic2-work-b7 DISPLAY_IC2=:710 B12_WORKER=-w1          # a private game folder and display are REQUIRED
    python3 runs/experiments/battles/b12_run.py run cg,p-hold,p-focus mix-rg --seeds 1-30 [--rep 1] [--batch b12]
    python3 runs/experiments/battles/b12_run.py run --pairs-file F          # lines "plan cell seed"

Same start save, exe and seed for a plan run and its `cg` run. **At battle open (placement phase, nothing clicked yet) every trial records the pairing proof**: the SHA-256 of the
battle block read from game memory, RandSeed, and the hook buffer's records so far (count and SHA-256 of their (kind, site, seed_before, seed_after, result) tuples); the pair
comparison (`b12_pairs.py`) requires them equal. At the end: the hook buffer is read and checked (seed chain, `b11_run.analyze`), the post-battle save kept, the result diffed.

Outputs (CLAUDE.md rule 6): `trials-b12.jsonl` (append-only, one line per attempt, errors included), `hooklog-<trial>.csv`, `hookcheck-<trial>.json`, `orders-<trial>.jsonl` (every
order record of the plan, with the block read-back summary) and the run's `.log`/`.jsonl`, all in the TRACKED data folder, never overwritten; saves, screenshots and raw buffers in
artifacts/run-exp-battle-orders/ (SHA-256 in SAVES.sha256, release archives).
"""
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b7_common as O  # noqa: E402
import b11_run as R  # noqa: E402
import b12_plans as P  # noqa: E402
import common as C  # noqa: E402
import trials as T  # noqa: E402
from harness.driver import DriverError  # noqa: E402
from state import battle, battle_block as BB, sav  # noqa: E402

JSONL = "trials-b12.jsonl"
R.JSONL = JSONL
WALL_LIMIT = 25 * 60          # seconds of play per battle
SHOTS = C.ART / "shots"


def tag_of(plan, cell, seed, rep):
    return "%s_%s_s%d_r%d" % (cell, plan, seed, rep)


def read_trials():
    f = C.DATA / JSONL
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def append_trial(rec):
    C.DATA.mkdir(parents=True, exist_ok=True)
    with open(C.DATA / JSONL, "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())


def records_sha(recs):
    return hashlib.sha256(json.dumps([(r["kind"], r["site"], r["seed_before"], r["seed_after"], r["result"]) for r in recs]).encode()).hexdigest()


def open_proof(g):
    """The pairing proof read right after the battle window opened: block, RandSeed, hook records so far."""
    st = g.battle_state()
    raw = BB.encode_block(st)
    c, recs = g.hook_read()
    return {"block_sha256": hashlib.sha256(raw).hexdigest(), "half_round": st["half_round"], "y1": st["y1"], "side_to_move": st["x2"],
            "seed_mem": int.from_bytes(g.mem(O.D.RAND_SEED, 4), "little"), "hook_records": len(recs), "hook_records_sha256": records_sha(recs),
            "hook_last_seed_after": recs[-1]["seed_after"] if recs else None,
            "rome_units": [(s["slot"], s["type"], s["troops"], s["quality"], s["morale"], s["x"], s["y"]) for s in st["slots"][:20] if s["alive"]],
            "gaul_units": [(s["slot"], s["type"], s["troops"], s["quality"], s["morale"], s["x"], s["y"]) for s in st["slots"][20:] if s["alive"]]}


def run_trial(g, plan, cell, seed, rep, log, batch):
    tag = tag_of(plan, cell, seed, rep)
    exe = O.HOOK_EXE % seed
    start, expect = R.stage_start(cell)
    for f in O.D.G.glob("BATTLE*.SAV"):
        C.keep(f, "stray_%s_%s" % (tag, f.name))
        f.unlink()
    t0 = time.time()
    rec = {"trial": tag, "batch": batch, "plan": plan, "cell": cell, "seed": seed, "rep": rep, "exe": exe, "exe_sha256": C.sha(O.D.G / exe), "start_save": start.name,
           "start_sha256": C.sha(start)}
    g.exe = exe
    g.start()
    log("process_started", trial=tag, exe=exe, pid=g.pid)
    rec["open_boxes"] = g.open(start)
    a0, a10 = g.army_state(C.ROME_ARMY), g.army_state(C.GAUL_ARMY)
    if expect:
        want = {C.ROME_ARMY: expect[0][2], C.GAUL_ARMY: expect[2][2]}
        for i, a in ((C.ROME_ARMY, a0), (C.GAUL_ARMY, a10)):
            got = [(u["type"], u["troops"], u["quality"]) for u in a["units"]]
            if got != [(t, n, q) for t, n, q in want[i]] or a["morale"] != T.MORALE:
                raise DriverError("army %d read back %s morale %d, expected %s" % (i, got, a["morale"], want[i]))
    if (a0["x"], a0["y"]) != C.STAGE_TILE or (a10["x"], a10["y"]) != C.GAUL_TILE or a0["moves"] <= 0:
        raise DriverError("geometry: army 0 at %s moves %s, army 10 at %s" % ((a0["x"], a0["y"]), a0["moves"], (a10["x"], a10["y"])))
    c, _ = g.hook_read()
    if not c["magic_ok"] or c["index"] != 0:
        raise DriverError("hook buffer not clean before the battle: %r" % c)
    g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
    g.click_tile(*C.GAUL_TILE, pause=0.0)
    T.wait_battle(g, log)
    time.sleep(2.5)
    t_open = time.time()
    rec["open"] = open_proof(g)
    log("battle_open", trial=tag, block=rec["open"]["block_sha256"][:12], seed_mem=rec["open"]["seed_mem"], hook_records=rec["open"]["hook_records"])
    SHOTS.mkdir(parents=True, exist_ok=True)
    tmp_end = SHOTS / ("_tmp_end_%s.png" % tag)
    orders = []
    try:
        if plan == "cg":
            res = g.play_battle(shot=tmp_end, on_dialog="capture")
            rec["end_turn_clicks"] = res["end_turn_clicks"]
        else:
            pl = P.PLANS[plan](g, log=lambda *a, **k: None)
            orders = pl.orders
            deadline = time.time() + WALL_LIMIT
            _half = pl.half_round
            pl.half_round = lambda: (_ for _ in ()).throw(DriverError("wall limit %d s" % WALL_LIMIT)) if time.time() > deadline else _half()
            pl.play()
            res = g.battle_finish(shot=tmp_end, on_dialog="capture")
            rec["end_turn_clicks"] = sum(1 for o in orders if o["order"] == "end_turn")
            rec["blocked_moves"] = pl.blocked
    finally:
        if plan != "cg":
            C.write_new(C.DATA, "orders-%s.jsonl" % tag, "".join(json.dumps(o, default=str) + "\n" for o in orders))
    ended = None
    if tmp_end.exists():
        ended = C.keep(tmp_end, "%s_battle-ended.png" % tag, SHOTS).name
        tmp_end.unlink()
    for d in res["dialogs"]:
        if d.get("shot") and Path(d["shot"]).exists():
            d["shot"] = C.keep(d["shot"], "%s_%s" % (tag, Path(d["shot"]).name), SHOTS).name
    t_over = time.time()
    flag_after = g.mem(O.D.BATTLE_FLAG, 1)[0]
    c1, recs1 = g.hook_read()
    post = g.save_as("%s_post.SAV" % tag)
    kept_post = C.keep(post, "%s_post.SAV" % tag)
    series = []
    for f in sorted(O.D.G.glob("BATTLE*.SAV")):
        k = C.keep(f, "%s_%s" % (tag, f.name))
        series.append({"name": k.name, "sha256": C.sha(k), "orig": f.name})
        f.unlink()
    final_seed = int.from_bytes(g.mem(O.D.RAND_SEED, 4), "little")
    pre_s, post_s = sav.load(str(start)), sav.load(str(kept_post))
    d = battle.diff(battle.snapshot(pre_s, [C.ROME_ARMY, C.GAUL_ARMY], [0, 6]), battle.snapshot(post_s, [C.ROME_ARMY, C.GAUL_ARMY], [0, 6]), C.ROME_ARMY, C.GAUL_ARMY)
    rec.update({"status": "ok", "half_rounds": len(series), "series": series, "post_save": kept_post.name, "post_sha256": C.sha(kept_post), "winner": d["winner"],
                "battle_ended_shot": ended, "battle_ended_text": res.get("battle_ended_text"), "dialogs": res["dialogs"], "dialog": ";".join(x["title"] for x in res["dialogs"]),
                "flag_after_battle_ended": flag_after, "att_loss": d["attacker"]["loss"], "def_loss": d["defender"]["loss"], "att_troops_before": d["attacker"]["troops_before"],
                "att_troops_after": d["attacker"]["troops_after"], "def_troops_before": d["defender"]["troops_before"], "def_troops_after": d["defender"]["troops_after"],
                "seconds": round(time.time() - t0, 1), "battle_seconds": round(t_over - t_open, 1), "final_seed_memory": final_seed, "orders": len(orders)})
    c2, recs2 = g.hook_read()
    chk = R.analyze(recs2, c2, seed, final_seed)
    csvp = C.write_new(C.DATA, "hooklog-%s.csv" % tag, R.log_csv(recs2))
    chkp = C.write_new(C.DATA, "hookcheck-%s.json" % tag, json.dumps(chk, indent=1, default=str))
    raw = bytes(g.mem(R.H.BUF, len(recs2) * R.H.REC)) if recs2 else b""
    rec.update({"hooklog": csvp.name, "hookcheck": chkp.name, "hook_pass": chk["pass"], "hook_records": chk["records"], "hook_overflow": chk["overflow"], "hook_reentered": chk["reentered"],
                "hook_chain_breaks": chk["chain_break_count"], "hook_raw_sha256": hashlib.sha256(raw).hexdigest(), "hook_read_1_is_prefix": [r["seq"] for r in recs1] == [r["seq"] for r in recs2[:len(recs1)]]})
    rawf = C.ART / "hookbuf"
    rawf.mkdir(parents=True, exist_ok=True)
    if not (rawf / ("%s.bin" % tag)).exists():
        (rawf / ("%s.bin" % tag)).write_bytes(raw)
    log("trial_done", trial=tag, seconds=rec["seconds"], half_rounds=len(series), winner=d["winner"], hook_pass=rec["hook_pass"], orders=len(orders))
    return rec


def run_all(plans, cells, seeds, rep=1, batch="b12", redo_errors=False, pairs=None, log=None):
    log = log or C.Log("b12-run" + os.environ.get("B12_WORKER", ""))
    todo = list(pairs) if pairs else [(p, c, s) for c in cells for s in seeds for p in plans]
    done = {}
    for r in read_trials():
        done[r["trial"]] = "ok" if done.get(r["trial"]) == "ok" or r.get("status") == "ok" else "error"
    xv = O.B.start_xvfb()
    log("xvfb", pid=xv, display=O.B.DISPLAY)
    n_ok = n_err = 0
    for plan, cell, seed in todo:
        tag = tag_of(plan, cell, seed, rep)
        if done.get(tag) == "ok" or (done.get(tag) == "error" and not redo_errors):
            log("skip", trial=tag, status=done.get(tag))
            continue
        g = O.OGame()
        g.CHANGE_TIMEOUT = 1.5
        attempt = sum(1 for r in read_trials() if r.get("trial") == tag) + 1
        O.B.kill_mine(g)
        try:
            rec = run_trial(g, plan, cell, seed, rep, log, batch)
            rec["attempt"] = attempt
            n_ok += 1
        except Exception as e:      # noqa: BLE001
            rec = {"trial": tag, "batch": batch, "plan": plan, "cell": cell, "seed": seed, "rep": rep, "status": "error", "attempt": attempt, "error": "%s: %s" % (type(e).__name__, e),
                   "traceback": traceback.format_exc()[-1500:]}
            try:
                rec["windows"] = [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")]
                rec["screenshot"] = C.shot(g, "error_%s_%s.png" % (tag, time.strftime("%H%M%S"))).name
            except Exception:       # noqa: BLE001
                pass
            n_err += 1
            log("trial_error", trial=tag, error=rec["error"])
        finally:
            rec["stamp"] = C.STAMP
            rec["worker"] = os.environ.get("B12_WORKER", "")
            rec["pids_killed"] = O.B.kill_mine(g)
        append_trial(rec)
    log("run_done", ok=n_ok, errors=n_err)
    return n_ok, n_err


def main():
    a = sys.argv[1:]
    if not a or a[0] != "run":
        sys.exit(__doc__)
    opt = lambda n, d=None: a[a.index(n) + 1] if n in a else d
    rest = [x for i, x in enumerate(a[1:], 1) if not x.startswith("--") and a[i - 1] not in ("--seeds", "--rep", "--batch", "--pairs-file")]
    pairs = None
    if "--pairs-file" in a:
        pairs = [(ln.split()[0], ln.split()[1], int(ln.split()[2])) for ln in Path(opt("--pairs-file")).read_text().splitlines() if ln.strip()]
        plans = cells = None
    else:
        plans = rest[0].split(",")
        cells = rest[1:]
    seeds = T.parse_seeds(opt("--seeds", "1")) if "--seeds" in a else [1]
    n_ok, n_err = run_all(plans, cells, seeds, int(opt("--rep", 1)), opt("--batch", "b12"), "--redo-errors" in a, pairs)
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
