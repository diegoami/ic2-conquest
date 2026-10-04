#!/usr/bin/env python3
"""Resumable trial runner of the battle sweep (battles plan §3.2, B4/B5): one fresh lab-build process per battle, L1 edits from FLD-RG,
both sides on Computer general, every half-round save kept.

A cell is `<attacker>-<defender>-<size>`: types li|hi|ar|lc|hc, size half (one unit of std/2), one (one unit of std) or three (three units
of std); std = LI 15000, HI 6000, Ar 3500, LC 7000, HC 2500; quality 6, army morale 65 on both sides (battles.md §4 B5). The attacker is
Rome's army 0 (the human seat, Computer general on), the defender Gaul's army 10, which stands next to it in FLD-RG; the armies' positions
are never edited. Example: `hi-hi-one`.

    python3 runs/experiments/battles/trials.py run hi-hi-one --seeds 1-3 [--reps 2] [--redo-errors] [--stop-on-error]
    python3 runs/experiments/battles/trials.py table              # sweep-table-<stamp>.csv from trials.jsonl
    python3 runs/experiments/battles/trials.py compare TRIAL_A TRIAL_B   # byte comparison of two trials' series and post-battle saves

`result` in a row is derived from the post-battle save (who survived); the "Battle ended" box's own text is the screenshot
`<trial>_battle-ended.png` (OCR of its table is garbled and kept as `result_text_ocr` only).

Output (CLAUDE.md rule 6): `trials.jsonl` in the TRACKED folder runs/experiments/data/run-exp-battle-sweep/ is APPEND-ONLY, one line per
trial attempt (status ok or error; an error records the exception, the open windows and a screenshot name; nothing is retried silently:
an errored trial is skipped by a resumed run unless --redo-errors is given, and then a NEW line is appended). A trial already `ok` is
skipped. Saves stay in artifacts/run-exp-battle-sweep/ (git-ignored; SHA-256 in SAVES.sha256), copied under names that never overwrite.
`--rep N` repeats a (cell, seed) in a new process, for the same-seed-twice byte comparison. Stale wine processes are killed by pid.
"""
import csv
import json
import re
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import stage  # noqa: E402
from harness.driver import DriverError, Game  # noqa: E402
from state import battle, sav  # noqa: E402

TYPES = ("li", "hi", "ar", "lc", "hc")
SIZES = {"half": (1, 0.5), "one": (1, 1.0), "three": (3, 1.0)}      # (units, fraction of one standard battalion)
Q, MORALE = 6, 65
RESULTS = {"attacker": "Rome defeats Gaul", "defender": "Gaul defeats Rome", "none": "neither army destroyed", "both": "both armies destroyed"}
COLUMNS = ["trial", "cell", "attacker", "defender", "size", "seed", "rep", "exe", "status", "half_rounds", "winner", "end_turn_clicks",
           "att_troops_before", "att_troops_after", "att_loss", "def_troops_before", "def_troops_after", "def_loss",
           "att_destroyed", "def_destroyed", "att_promotions", "def_promotions", "end_condition", "result", "dialog",
           "seconds", "start_save", "series_first", "series_last", "post_save", "post_sha12", "series_sha12", "halflog", "loss_rows", "unambiguous_rows"]


def parse_cell(cell):
    m = re.fullmatch(r"(%s)-(%s)-(%s)" % ("|".join(TYPES), "|".join(TYPES), "|".join(SIZES)), cell)
    if not m:
        raise ValueError("cell %r is not <type>-<type>-<half|one|three>" % cell)
    return m.groups()


def cell_ops(cell):
    """The L1 edits of a cell (stage.py): both armies' units (all of one type, quality 6) and morale 65. Positions are never edited."""
    a, d, size = parse_cell(cell)
    n, f = SIZES[size]
    return [("units", C.ROME_ARMY, stage.uniform(a, n, f, Q)), ("morale", C.ROME_ARMY, MORALE),
            ("units", C.GAUL_ARMY, stage.uniform(d, n, f, Q)), ("morale", C.GAUL_ARMY, MORALE)]


def trial_id(cell, seed, rep):
    return f"{cell}_s{seed}_r{rep}"


def read_trials():
    f = C.DATA / "trials.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def append_trial(rec):
    """Append-only: one line, flushed and synced."""
    C.DATA.mkdir(parents=True, exist_ok=True)
    with open(C.DATA / "trials.jsonl", "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
        f.flush()
        import os
        os.fsync(f.fileno())


def pending(cells, seeds, reps, redo_errors=False):
    """(cell, seed, rep) not yet ok; an errored one only with redo_errors. Returns (todo, skipped_ok, skipped_error)."""
    status = {}
    for r in read_trials():
        if "trial" in r and r.get("status") in ("ok", "error"):
            status[r["trial"]] = "ok" if status.get(r["trial"]) == "ok" or r["status"] == "ok" else "error"
    todo, ok, err = [], [], []
    for cell in cells:
        for seed in seeds:
            for rep in reps:
                t = trial_id(cell, seed, rep)
                (ok if status.get(t) == "ok" else err if status.get(t) == "error" and not redo_errors else todo).append((cell, seed, rep))
    return todo, ok, err


def stage_start(cell):
    """The cell's start save (FLD-RG with the cell's L1 edits), written once to artifacts/…/start/; an existing identical file is reused."""
    src = C.ART / C.FLD_RG_NAME
    if not src.exists():
        raise DriverError("fixture %s missing: run python3 -m tests.make_battle_fixtures" % src)
    tmp = C.ART / "start" / ("_tmp_%s.SAV" % cell)
    tmp.parent.mkdir(parents=True, exist_ok=True)
    stage.edit(src, tmp, cell_ops(cell))
    kept = C.keep(tmp, f"{cell}_start.SAV", C.ART / "start")
    tmp.unlink()
    return kept


def wait_battle(g, log, limit=40):
    t0 = time.time()
    seen = []
    while time.time() - t0 < limit:
        if g.in_battle() and g.find_windows(" v "):
            return round(time.time() - t0, 2)
        names = [w[1] for w in g.popups()]
        if names and names != seen:
            log("popup_before_battle", names=names, texts=[g.read_popup(p) for p in g.popups()])
            seen = names
        time.sleep(0.5)
    raise DriverError("battle window did not open in %d s" % limit)


def run_trial(g, cell, seed, rep, log):
    """One whole battle from a fresh process. Raises on any failure (the caller records it). Returns the trial record."""
    a_type, d_type, size = parse_cell(cell)
    tid = trial_id(cell, seed, rep)
    tag = tid
    exe = C.LAB_EXE % seed
    start = stage_start(cell)
    expect = cell_ops(cell)
    for f in C.D.G.glob("BATTLE*.SAV"):                 # a stray from an earlier process is kept, not lost
        C.keep(f, f"stray_{tid}_{f.name}")
        f.unlink()
    t0 = time.time()
    rec = {"trial": tid, "cell": cell, "attacker": a_type, "defender": d_type, "size": size, "seed": seed, "rep": rep, "exe": exe,
           "start_save": start.name, "start_sha256": C.sha(start), "level": "L1 from FLD-RG (labelled synthetic)", "build": "lab"}
    g.exe = exe
    g.start()
    log("process_started", trial=tid, exe=exe, pid=g.pid, seconds=round(time.time() - t0, 1))
    boxes = g.open(start)
    rec["open_boxes"] = boxes
    t_loaded = time.time() - t0
    # the game's own memory must show the edited state (read back) and the geometry: never trust the file alone
    a0, a10 = g.army_state(C.ROME_ARMY), g.army_state(C.GAUL_ARMY)
    want = {C.ROME_ARMY: expect[0][2], C.GAUL_ARMY: expect[2][2]}
    for i, a in ((C.ROME_ARMY, a0), (C.GAUL_ARMY, a10)):
        got = [(u["type"], u["troops"], u["quality"]) for u in a["units"]]
        if got != [(t, n, q) for t, n, q in want[i]] or a["morale"] != MORALE:
            raise DriverError("army %d read back %s morale %d, expected %s morale %d" % (i, got, a["morale"], want[i], MORALE))
    if (a0["x"], a0["y"]) != C.STAGE_TILE or (a10["x"], a10["y"]) != C.GAUL_TILE or a0["moves"] <= 0:
        raise DriverError("geometry: army 0 at %s moves %s, army 10 at %s" % ((a0["x"], a0["y"]), a0["moves"], (a10["x"], a10["y"])))
    log("loaded", trial=tid, seconds=round(t_loaded, 1), boxes=boxes, army0=battle.by_type(a0), army10=battle.by_type(a10))
    g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
    t_click = time.time()
    g.click_tile(*C.GAUL_TILE, pause=0.0)
    dt = wait_battle(g, log)
    t_open = time.time()
    log("battle_open", trial=tid, seconds_from_click=dt, title=g.find_windows(" v ")[0][1])
    shots = C.ART / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    res = g.play_battle(shot=shots / f"{tag}_battle-ended.png", on_dialog="capture")
    for d in res["dialogs"]:           # the driver writes dialog screenshots to IC2_WORK/shots: keep them with the saves, never overwritten
        if d.get("shot") and Path(d["shot"]).exists():
            d["shot"] = C.keep(d["shot"], f"{tag}_{Path(d['shot']).name}", shots).name
    t_over = time.time()
    log("battle_played", trial=tid, end_turn_clicks=res["end_turn_clicks"], ended=res["battle_ended_text"], dialogs=[
        {k: d[k] for k in ("title", "text", "answer", "shot")} for d in res["dialogs"]])
    post = g.save_as(f"{tag}_post.SAV")
    t_saved = time.time()
    kept_post = C.keep(post, f"{tag}_post.SAV")
    series = []
    for f in sorted(C.D.G.glob("BATTLE*.SAV")):
        series.append(C.keep(f, f"{tag}_{f.name}").name)
        f.unlink()
    pre_s, post_s = sav.load(str(start)), sav.load(str(kept_post))
    ids, nats = [C.ROME_ARMY, C.GAUL_ARMY], [0, 6]
    d = battle.diff(battle.snapshot(pre_s, ids, nats), battle.snapshot(post_s, ids, nats), C.ROME_ARMY, C.GAUL_ARMY)
    att, dfn = d["attacker"], d["defender"]
    loser = dfn if d["winner"] == "attacker" else att if d["winner"] == "defender" else None
    import hashlib
    rec.update({
        "status": "ok", "half_rounds": len(series), "series": series, "post_save": kept_post.name, "post_sha256": C.sha(kept_post),
        "series_sha12": hashlib.sha256("".join(C.sha(C.ART / s) for s in series).encode()).hexdigest()[:12],
        "winner": d["winner"], "end_turn_clicks": res["end_turn_clicks"], "result_text_ocr": res["battle_ended_text"],
        "result": RESULTS[d["winner"]],
        "battle_ended_shot": f"{tag}_battle-ended.png" if (shots / f"{tag}_battle-ended.png").exists() else None,
        "dialogs": res["dialogs"], "dialog": ";".join(x["title"] for x in res["dialogs"]),
        "end_condition": "none (nobody destroyed)" if loser is None else "loser destroyed (annihilation, rout or surrender: not distinguished at strategic level)" if loser["destroyed"] else "loser survived",
        "attacker_result": {k: att[k] for k in ("troops_before", "troops_after", "loss", "destroyed", "type_loss", "promotions", "morale", "money")},
        "defender_result": {k: dfn[k] for k in ("troops_before", "troops_after", "loss", "destroyed", "type_loss", "promotions", "morale", "money")},
        "units": {"attacker": att["units"], "defender": dfn["units"]}, "nations": d["nations"], "news": d["news"], "taken": d["taken"],
        "seconds": round(t_saved - t0, 1),
        "timing": {"loaded": round(t_loaded, 1), "click_to_battle": dt, "battle_open_to_over": round(t_over - t_open, 1),
                   "post_save": round(t_saved - t_over, 1)}})
    try:       # the per-half-round log (B2/B4); a decoding failure is recorded, it never loses the trial
        import halflog
        p, summ = halflog.write_halflog(tid, series)
        rec["halflog"], rec["halflog_summary"] = p.name, summ
    except Exception as e:      # noqa: BLE001
        rec["halflog_error"] = f"{type(e).__name__}: {e}"
    if res["dialogs"]:
        rec["dialog_note"] = "an Offer of peace (or other) box appeared after the battle and was DECLINED (never Yes)"
    log("trial_done", trial=tid, seconds=rec["seconds"], half_rounds=len(series), winner=d["winner"], post_sha12=rec["post_sha256"][:12])
    return rec


def row(rec):
    if rec.get("status") != "ok":
        return {"trial": rec.get("trial"), "cell": rec.get("cell"), "status": rec.get("status")}
    a, d = rec["attacker_result"], rec["defender_result"]
    return {"trial": rec["trial"], "cell": rec["cell"], "attacker": rec["attacker"], "defender": rec["defender"], "size": rec["size"],
            "seed": rec["seed"], "rep": rec["rep"], "exe": rec["exe"], "status": "ok", "half_rounds": rec["half_rounds"],
            "winner": rec["winner"], "end_turn_clicks": rec["end_turn_clicks"], "att_troops_before": a["troops_before"],
            "att_troops_after": a["troops_after"], "att_loss": a["loss"], "def_troops_before": d["troops_before"],
            "def_troops_after": d["troops_after"], "def_loss": d["loss"], "att_destroyed": a["destroyed"], "def_destroyed": d["destroyed"],
            "att_promotions": len(a["promotions"]), "def_promotions": len(d["promotions"]), "end_condition": rec["end_condition"].split(" (")[0],
            "result": rec.get("result") or RESULTS[rec["winner"]], "dialog": rec.get("dialog", ""), "seconds": rec["seconds"],
            "start_save": rec["start_save"], "series_first": rec["series"][0] if rec["series"] else "",
            "series_last": rec["series"][-1] if rec["series"] else "", "post_save": rec["post_save"],
            "post_sha12": rec["post_sha256"][:12], "series_sha12": rec["series_sha12"], "halflog": rec.get("halflog", ""),
            "loss_rows": rec.get("halflog_summary", {}).get("loss_rows", ""), "unambiguous_rows": rec.get("halflog_summary", {}).get("unambiguous_rows", "")}


def write_table():
    """sweep-table-<stamp>.csv from the LAST ok record of every trial id (a new file each time, never overwritten)."""
    last = {}
    for r in read_trials():
        if r.get("status") == "ok":
            last[r["trial"]] = r
    out = C.DATA / f"sweep-table-{C.STAMP}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, COLUMNS)
        w.writeheader()
        for r in last.values():
            w.writerow(row(r))
    return out, len(last)


def compare(ta, tb):
    """Byte comparison of two ok trials: the half-round series (aligned by position, same length required, n > 0) and the post-battle saves.
    Reads the files the trial records name (the new ones), not whatever matches a pattern."""
    rs = {r["trial"]: r for r in read_trials() if r.get("status") == "ok"}
    a, b = rs[ta], rs[tb]
    rd = lambda n: (C.ART / n).read_bytes()
    pairs = list(zip(a["series"], b["series"]))
    diff = [(x, y) for x, y in pairs if rd(x) != rd(y)]
    same_len = len(a["series"]) == len(b["series"])
    return {"a": ta, "b": tb, "series_a": len(a["series"]), "series_b": len(b["series"]), "aligned": len(pairs), "differing_files": len(diff),
            "series_identical": same_len and len(pairs) > 0 and not diff, "post_identical": rd(a["post_save"]) == rd(b["post_save"]),
            "differing_examples": diff[:3]}


def parse_seeds(s):
    out = []
    for part in s.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def run_all(cells, seeds, reps, redo_errors=False, stop_on_error=False, make_game=Game, log=None, shot=True):
    log = log or C.Log("trials-run")
    todo, ok, err = pending(cells, seeds, reps, redo_errors)
    log("plan", todo=[trial_id(*t) for t in todo], skipped_ok=[trial_id(*t) for t in ok], skipped_error=[trial_id(*t) for t in err])
    n_ok = n_err = 0
    for cell, seed, rep in todo:
        tid = trial_id(cell, seed, rep)
        g = make_game()
        attempt = sum(1 for r in read_trials() if r.get("trial") == tid) + 1
        C.kill_stale(g)
        try:
            rec = run_trial(g, cell, seed, rep, log)
            rec["attempt"] = attempt
            n_ok += 1
        except Exception as e:      # noqa: BLE001 - an error is a result: recorded, never retried silently
            rec = {"trial": tid, "cell": cell, "seed": seed, "rep": rep, "status": "error", "attempt": attempt, "error": f"{type(e).__name__}: {e}",
                   "traceback": traceback.format_exc()[-1500:]}
            try:
                rec["windows"] = [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")]
                if shot:
                    p = C.ART / f"error_{tid}_{time.strftime('%H%M%S')}.png"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    g.shot(p)
                    rec["screenshot"] = p.name
            except Exception:       # noqa: BLE001
                pass
            n_err += 1
            log("trial_error", trial=tid, error=rec["error"])
        finally:
            rec["stamp"] = C.STAMP
            rec["pids_killed"] = C.kill_stale(g)
        append_trial(rec)
        if rec["status"] == "error" and stop_on_error:
            break
    log("run_done", ok=n_ok, errors=n_err)
    return n_ok, n_err


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("run", "table", "compare"):
        sys.exit(__doc__)
    if args[0] == "table":
        out, n = write_table()
        print(out, n, "trials")
    elif args[0] == "compare":
        res = compare(args[1], args[2])
        out = C.DATA / f"compare-{args[1]}-{args[2]}-{C.STAMP}.json"
        out.write_text(json.dumps(res, indent=1))
        print(json.dumps(res, indent=1))
    else:
        cells = [a for a in args[1:] if not a.startswith("--") and re.fullmatch(r"[a-z]{2}-[a-z]{2}-[a-z]+", a)]
        for c in cells:
            parse_cell(c)
        seeds = parse_seeds(args[args.index("--seeds") + 1]) if "--seeds" in args else [1, 2, 3]
        nreps = int(args[args.index("--reps") + 1]) if "--reps" in args else 1
        n_ok, n_err = run_all(cells, seeds, list(range(1, nreps + 1)), "--redo-errors" in args, "--stop-on-error" in args)
        sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
