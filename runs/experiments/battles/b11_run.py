#!/usr/bin/env python3
"""B11 trial runner: one whole battle per fresh process on the HOOKED lab exe (variant `hook`) or the unhooked lab exe (`plain`), the same L1 staging as
the B5 sweep (`trials.py`: FLD-RG with the cell's edits; `MIX-RG` = FLD-RG with no edit, Rome's army 0 against Gaul's army 10, the B0 battle).

    export IC2_WORK=~/ic2-work-b11 DISPLAY_IC2=:577          # a private game folder and display are REQUIRED (b11_common.py)
    python3 runs/experiments/battles/b11_run.py run hook hi-hi-one mix-rg --seeds 1-3 [--rep 1]
    python3 runs/experiments/battles/b11_run.py run plain hi-hi-one mix-rg --seeds 1-3
    python3 runs/experiments/battles/b11_run.py compare                 # inertness: hooked vs unhooked (and vs the B5 hashes), one file in the data folder

Output (rule 6): `trials-b11.jsonl` (append-only, one line per attempt, error lines included), `hooklog-<trial>.csv` (every record of the buffer, per battle),
`hookcheck-<trial>.json` (the chain/boundary/formula checks of that log), the run's `.log`/`.jsonl` (common.Log). Saves in artifacts/run-exp-battle-hook/ (SHA-256
in SAVES.sha256, never overwritten). A trial that is `ok` is skipped by a resumed run; an errored one only with --redo-errors (a new line is appended).
"""
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_common as B  # noqa: E402
import common as C  # noqa: E402
import stage  # noqa: E402
import trials as T  # noqa: E402
from harness.driver import DriverError  # noqa: E402
from state import battle, hook_log as L, sav  # noqa: E402

sys.path.insert(0, str(C.ROOT / "patches"))
import battle_hook as H  # noqa: E402

MIX = "mix-rg"
JSONL = "trials-b11.jsonl"


def parse_cell(cell):
    """`<att>-<def>-<size>` or, for the size matrix, `<att>-<def>-<att size>-<def size>` (e.g. `hi-li-half-three`): the same cells the B5 sweep (PR #40) ran. The
    B5 trials.py is not in main yet, so its two small extensions (the size matrix) are repeated here, not imported."""
    m = re.fullmatch(r"(%s)-(%s)-((?:%s)(?:-(?:%s))?)" % ("|".join(T.TYPES), "|".join(T.TYPES), "|".join(T.SIZES), "|".join(T.SIZES)), cell)
    if not m:
        raise ValueError("cell %r is not <type>-<type>-<size>[-<size>]" % cell)
    return m.groups()


def cell_ops(cell):
    """The L1 edits of a cell (stage.py): both armies' units (all of one type, quality 6) and morale 65; positions are never edited."""
    a, d, size = parse_cell(cell)
    sa, _, sd = size.partition("-")
    (na, fa), (nd, fd) = T.SIZES[sa], T.SIZES[sd or sa]
    return [("units", C.ROME_ARMY, stage.uniform(a, na, fa, T.Q)), ("morale", C.ROME_ARMY, T.MORALE),
            ("units", C.GAUL_ARMY, stage.uniform(d, nd, fd, T.Q)), ("morale", C.GAUL_ARMY, T.MORALE)]


def trial_tag(cell, seed, rep, variant):
    return "%s_s%d_r%d_%s" % (cell, seed, rep, variant)


def read_trials():
    f = C.DATA / JSONL
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def append_trial(rec):
    C.DATA.mkdir(parents=True, exist_ok=True)
    import os
    with open(C.DATA / JSONL, "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())


def fixture():
    dst = C.ART / C.FLD_RG_NAME
    if not dst.exists():
        raise DriverError("fixture %s missing: copy it from artifacts/run-exp-battle-sweep/ (or build it: python3 -m tests.make_battle_fixtures)" % dst)
    return dst


def stage_start(cell):
    """The cell's start save (as trials.stage_start: FLD-RG with the cell's L1 edits, kept under artifacts/.../start/), under a file lock because several
    workers may stage the same cell at the same moment (their private tmp name includes the pid)."""
    import fcntl
    (C.ART / "start").mkdir(parents=True, exist_ok=True)
    with open(C.ART / "start" / ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        if cell == MIX:
            return C.keep(fixture(), "MIX-RG_start.SAV", C.ART / "start"), None
        tmp = C.ART / "start" / ("_tmp_%s_%d.SAV" % (cell, os.getpid()))
        stage.edit(fixture(), tmp, cell_ops(cell))
        kept = C.keep(tmp, "%s_start.SAV" % cell, C.ART / "start")
        tmp.unlink()
        return kept, cell_ops(cell)


def analyze(recs, ctl, seed, final_seed_mem):
    """The checks of one hooked battle: seed chain with boundaries, formula, sites, overflow. Everything is a plain dict for the tracked output."""
    kinds = Counter(r["kind"] for r in recs)
    rnd = [r for r in recs if r["kind"] == "random"]
    breaks = L.chain_check(recs, start_seed=seed, sites=set(H.SITES))
    start_ok = bool(recs) and recs[0]["kind"] == "start" and recs[0]["seed_before"] == seed
    flag_clears = [(r["seq"], hex(r["site"]), r["counter"], r["seed_after"]) for r in recs if r["kind"] == "flag_clear"]
    first_clear = next((r["seq"] for r in recs if r["kind"] == "flag_clear"), None)
    reseeds = [(r["seq"], hex(r["site"]), r["seed_before"]) for r in recs if r["kind"] == "reseed"]
    reseed_inside = [x for x in reseeds if first_clear is None or x[0] < first_clear]            # a reseed before the flag cleared would be a finding
    reseed_after = [r for r in recs if r["kind"] == "reseed" and first_clear is not None and r["seq"] > first_clear]
    post = [r for r in recs if first_clear is not None and r["seq"] > first_clear]
    last_rand = next((r for r in reversed(recs) if r["kind"] == "random"), None)
    last_seed = recs[-1]["seed_after"] if recs else None
    # the end of the battle's draws is pinned (a) by the reseed record that follows the last post-battle site (the chain check already proved its
    # seed_before is that site's seed_after), else (b) by RandSeed read from memory right after the battle windows closed
    end_pin_reseed = bool(reseed_after) and bool(last_rand) and reseed_after[0]["seed_before"] == last_rand["seed_after"] and reseed_after[0]["seq"] > last_rand["seq"]
    end_pin_memory = bool(recs) and last_seed == final_seed_mem
    post_sites = sorted({hex(r["site"]) for r in post if r["kind"] == "random"})
    return {
        "records": len(recs), "overflow": ctl["overflow"], "reentered": ctl.get("reentered", 0), "busy_at_read": ctl.get("busy", 0), "index": ctl["index"], "capacity": ctl["capacity"], "magic_ok": ctl["magic_ok"],
        "kinds": dict(kinds), "random_by_site": {hex(k): v for k, v in sorted(Counter(r["site"] for r in rnd).items())},
        "markers_by_entry": {hex(k): v for k, v in sorted(Counter(r["site"] for r in recs if r["kind"] == "marker").items())},
        "chain_breaks": breaks[:20], "chain_break_count": len(breaks),
        "start_boundary_ok": start_ok, "start_seed_expected": seed, "first_seed_before": recs[0]["seed_before"] if recs else None,
        "flag_clear_records": flag_clears, "reseed_records": reseeds, "reseed_before_flag_clear": reseed_inside, "post_battle_random_sites": post_sites,
        "last_record_seed_after": last_seed, "final_seed_in_memory": final_seed_mem,
        "end_pin_by_reseed_record": end_pin_reseed, "end_pin_by_memory": end_pin_memory,
        "result_formula_misses": L.result_check(recs)[:20], "result_formula_miss_count": len(L.result_check(recs)),
        "sites_outside_list": sorted({hex(r["site"]) for r in rnd if r["site"] not in H.SITES}),
        "pass": (ctl["overflow"] == 0 and ctl.get("reentered", 0) == 0 and ctl["magic_ok"] and not breaks and start_ok and not L.result_check(recs) and bool(flag_clears)
                 and not reseed_inside and (end_pin_reseed or end_pin_memory)),
    }


def log_csv(recs):
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    cols = ("seq", "kind", "site", "eax", "edx", "ecx", "seed_before", "seed_after", "result", "counter", "side", "flag", "ebp")
    w.writerow(cols)
    for r in recs:
        w.writerow([r[c] if c not in ("site", "ebp") else "0x%x" % r[c] for c in cols])
    return buf.getvalue()


def run_trial(g, cell, seed, rep, variant, log):
    tag = trial_tag(cell, seed, rep, variant)
    exe = (B.HOOK_EXE if variant == "hook" else B.PLAIN_EXE) % seed
    start, expect = stage_start(cell)
    for f in C.D.G.glob("BATTLE*.SAV"):
        C.keep(f, "stray_%s_%s" % (tag, f.name))
        f.unlink()
    t0 = time.time()
    rec = {"trial": tag, "cell": cell, "variant": variant, "seed": seed, "rep": rep, "exe": exe, "exe_sha256": C.sha(C.D.G / exe),
           "start_save": start.name, "start_sha256": C.sha(start)}
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
    if variant == "hook":
        c, _ = g.hook_read()
        if not c["magic_ok"] or c["index"] != 0:
            raise DriverError("hook buffer not clean before the battle: %r" % c)
    g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
    g.click_tile(*C.GAUL_TILE, pause=0.0)
    T.wait_battle(g, log)
    t_open = time.time()
    if variant == "hook":     # an independent live look at the open battle (human placement phase): flag, header words, seed vs the buffer
        c, recs0 = g.hook_read()
        rec["at_open"] = {"flag": g.mem(C.D.BATTLE_FLAG, 1)[0], "records": len(recs0), "seed_mem": int.from_bytes(g.mem(C.D.RAND_SEED, 4), "little"),
                          "last_seed_after": recs0[-1]["seed_after"] if recs0 else None, "half_round": g.half_round_counter()}
    shots = C.ART / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    tmp_end = shots / ("_tmp_end_%s.png" % tag)
    res = g.play_battle(shot=tmp_end, on_dialog="capture")
    ended = None
    if tmp_end.exists():
        ended = C.keep(tmp_end, "%s_battle-ended.png" % tag, shots).name
        tmp_end.unlink()
    for d in res["dialogs"]:
        if d.get("shot") and Path(d["shot"]).exists():
            d["shot"] = C.keep(d["shot"], "%s_%s" % (tag, Path(d["shot"]).name), shots).name
    t_over = time.time()
    flag_after = g.mem(C.D.BATTLE_FLAG, 1)[0]
    log1 = g.hook_read() if variant == "hook" else None
    post = g.save_as("%s_post.SAV" % tag)
    kept_post = C.keep(post, "%s_post.SAV" % tag)
    series = []
    for f in sorted(C.D.G.glob("BATTLE*.SAV")):
        k = C.keep(f, "%s_%s" % (tag, f.name))
        series.append({"name": k.name, "sha256": C.sha(k), "orig": f.name})
        f.unlink()
    final_seed = int.from_bytes(g.mem(C.D.RAND_SEED, 4), "little")
    pre_s, post_s = sav.load(str(start)), sav.load(str(kept_post))
    d = battle.diff(battle.snapshot(pre_s, [C.ROME_ARMY, C.GAUL_ARMY], [0, 6]), battle.snapshot(post_s, [C.ROME_ARMY, C.GAUL_ARMY], [0, 6]), C.ROME_ARMY, C.GAUL_ARMY)
    rec.update({"status": "ok", "half_rounds": len(series), "series": series, "post_save": kept_post.name, "post_sha256": C.sha(kept_post),
                "winner": d["winner"], "end_turn_clicks": res["end_turn_clicks"], "battle_ended_shot": ended, "dialogs": res["dialogs"],
                "dialog": ";".join(x["title"] for x in res["dialogs"]), "flag_after_battle_ended": flag_after,
                "att_loss": d["attacker"]["loss"], "def_loss": d["defender"]["loss"], "seconds": round(time.time() - t0, 1),
                "battle_seconds": round(t_over - t_open, 1), "final_seed_memory": final_seed})
    if variant == "hook":
        c2, recs2 = g.hook_read()
        c1, recs1 = log1
        rec["log_read_1_records"], rec["log_read_2_records"] = len(recs1), len(recs2)
        rec["log_read_1_is_prefix"] = [r["seq"] for r in recs1] == [r["seq"] for r in recs2[:len(recs1)]]
        chk = analyze(recs2, c2, seed, final_seed)
        csvp = C.write_new(C.DATA, "hooklog-%s.csv" % tag, log_csv(recs2))
        chkp = C.write_new(C.DATA, "hookcheck-%s.json" % tag, json.dumps(chk, indent=1, default=str))
        raw = bytes(g.mem(H.BUF, len(recs2) * H.REC)) if recs2 else b""
        rec.update({"hooklog": csvp.name, "hookcheck": chkp.name, "hook_pass": chk["pass"], "hook_records": chk["records"], "hook_overflow": chk["overflow"], "hook_reentered": chk["reentered"],
                    "hook_chain_breaks": chk["chain_break_count"], "hook_raw_sha256": hashlib.sha256(raw).hexdigest()})
        rawf = C.ART / "hookbuf"           # the raw buffer (a binary: kept in the release archive; its SHA-256 is in the trial line)
        rawf.mkdir(parents=True, exist_ok=True)
        if not (rawf / ("%s.bin" % tag)).exists():
            (rawf / ("%s.bin" % tag)).write_bytes(raw)
    log("trial_done", trial=tag, seconds=rec["seconds"], half_rounds=len(series), winner=d["winner"], post_sha12=rec["post_sha256"][:12],
        hook_pass=rec.get("hook_pass"), hook_records=rec.get("hook_records"))
    return rec


def run_all(variant, cells, seeds, rep=1, redo_errors=False, stop_on_error=False, log=None, pairs=None):
    """`pairs` = [(cell, seed), ...] replaces the cells x seeds product (the batch driver gives each worker its own list)."""
    log = log or C.Log("b11-run-%s%s" % (variant, os.environ.get("B11_WORKER", "")))
    todo = list(pairs) if pairs else [(c, sd) for c in cells for sd in seeds]
    done = {}
    for r in read_trials():
        done[r["trial"]] = "ok" if done.get(r["trial"]) == "ok" or r.get("status") == "ok" else "error"
    xv = B.start_xvfb()
    log("xvfb", pid=xv, display=B.DISPLAY)
    n_ok = n_err = 0
    for cell, seed in todo:
        tag = trial_tag(cell, seed, rep, variant)
        if done.get(tag) == "ok" or (done.get(tag) == "error" and not redo_errors):
            log("skip", trial=tag, status=done.get(tag))
            continue
        g = B.HookGame()
        attempt = sum(1 for r in read_trials() if r.get("trial") == tag) + 1
        B.kill_mine(g)
        try:
            rec = run_trial(g, cell, seed, rep, variant, log)
            rec["attempt"] = attempt
            n_ok += 1
        except Exception as e:      # noqa: BLE001
            rec = {"trial": tag, "cell": cell, "variant": variant, "seed": seed, "rep": rep, "status": "error", "attempt": attempt,
                   "error": "%s: %s" % (type(e).__name__, e), "traceback": traceback.format_exc()[-1500:]}
            try:
                rec["windows"] = [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")]
                rec["screenshot"] = C.shot(g, "error_%s_%s.png" % (tag, time.strftime("%H%M%S"))).name
            except Exception:       # noqa: BLE001
                pass
            n_err += 1
            log("trial_error", trial=tag, error=rec["error"])
        finally:
            rec["stamp"] = C.STAMP
            rec["worker"] = os.environ.get("B11_WORKER", "")
            rec["pids_killed"] = B.kill_mine(g)
        append_trial(rec)
        if rec["status"] == "error" and stop_on_error:
            break
    log("run_done", ok=n_ok, errors=n_err)
    return n_ok, n_err


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("run", "compare"):
        sys.exit(__doc__)
    if a[0] == "run":
        variant = a[1]
        assert variant in ("hook", "plain")
        cells = [x for x in a[2:] if re.fullmatch(r"[a-z]{2}-[a-z]{2}-[a-z]+(-[a-z]+)?|%s" % MIX, x)]
        for c in cells:
            if c != MIX:
                parse_cell(c)
        seeds = T.parse_seeds(a[a.index("--seeds") + 1]) if "--seeds" in a else [1, 2, 3]
        rep = int(a[a.index("--rep") + 1]) if "--rep" in a else 1
        pairs = None
        if "--pairs-file" in a:                       # lines "cell seed"
            pairs = [(ln.split()[0], int(ln.split()[1])) for ln in Path(a[a.index("--pairs-file") + 1]).read_text().splitlines() if ln.strip()]
            for c, _ in pairs:
                if c != MIX:
                    parse_cell(c)
        n_ok, n_err = run_all(variant, cells, seeds, rep, "--redo-errors" in a, "--stop-on-error" in a, pairs=pairs)
        sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
