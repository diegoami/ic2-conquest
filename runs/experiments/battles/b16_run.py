#!/usr/bin/env python3
"""B16 runner: the post-battle "Offer of peace" (TBattlePols), normal seed build (battles plan §7), docs/tasks/battles-b16-peace.md.

    export IC2_WORK=~/ic2-work-b16 DISPLAY_IC2=:640        # a private game folder and display are REQUIRED (b16_common.py)
    python3 runs/experiments/battles/b16_run.py survey loss 1-10     # D-LOSS: Rome's army 0 weakened (L1), seeds 1-10, box answered No
    python3 runs/experiments/battles/b16_run.py survey win 1-10      # D-WIN: Gaul's army 10 weakened (L1)
    python3 runs/experiments/battles/b16_run.py pair loss 3 [--turns 4]   # the same save + seed twice: Yes in one, No in the other, then N turns
    python3 runs/experiments/battles/b16_run.py trial loss 3 yes|no|capture [--turns N]   # one run

A trial = one fresh process of the NORMAL build (`... fast rollingsave seed.exe`: RandSeed from SEED.TXT at program start), `Game.load(start, seed)`,
Rome's army 0 attacks Gaul's army 10 at (85,28) with Computer general on (both sides), and `play_battle(on_dialog=..., pre_answer=...)`.
The state BEFORE the answer is read from game memory at the moment the box is up, before the click (`snapshot`): RandSeed, the map, the nation, army,
fleet tables, the battle block and header (0x45E030..0x4A0B80); the box's text and controls are recorded with it. A box that does not open gets the
same snapshot right after the Battle ended box closed. Every record is one line appended to trials-b16.jsonl (CLAUDE.md rule 6: append-only,
errors are results, nothing is retried silently); snapshots (binary, gzip) go to artifacts/run-exp-battle-peace/snaps/ with their SHA-256 in SAVES.sha256.

L1 cells (synthetic, labelled): `loss` = FLD-RG with Rome's army 0 replaced by one 3,000 LI battalion (quality 6); `win` = FLD-RG with Gaul's army 10
replaced by one 3,000 LI battalion. Nothing else is edited; positions never.
"""
import gzip
import hashlib
import json
import os
import re
import struct
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b16_common as B  # noqa: E402  (checks IC2_WORK / DISPLAY_IC2 first)
import common as C  # noqa: E402
import stage  # noqa: E402
from state import sav  # noqa: E402

D = B.D
SNAP_BASE, SNAP_END = 0x45E030, 0x4A0B80
REGIONS = {"randseed": (0x45E030, 4), "map": (D.MAP, 320 * 140 * 2), "nations": (D.NATIONS, 16 * D.NATION_LEN), "armies": (D.ARMIES, 200 * D.ARMY_LEN),
           "fleets": (D.FLEETS, 0x4A0344 - D.FLEETS - 0), "battle_block": (D.BATTLE_SLOTS, 2096), "battle_header": (0x4A0B74, 0xC)}
CELLS = {
    "loss": {"ops": [("units", C.ROME_ARMY, [("li", 3000, 6)])], "note": "D-LOSS: Rome's army 0 = one 3,000 LI battalion (L1 synthetic); Gaul's army 10 as in FLD-RG"},
    "win": {"ops": [("units", C.GAUL_ARMY, [("li", 3000, 6)])], "note": "D-WIN: Gaul's army 10 = one 3,000 LI battalion (L1 synthetic); Rome's army 0 as in FLD-RG"},
}
TRIALS = "trials-b16.jsonl"
WINNER_TEXT = re.compile(r"(\w+)'?s?\s+army\s+defeats", re.I)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def stage_start(cell, ops_extra=()):
    src = B.ART / C.FLD_RG_NAME
    if not src.exists():
        raise D.DriverError("fixture %s missing" % src)
    ops = list(CELLS[cell.split("+")[0]]["ops"]) + list(ops_extra)
    tmp = B.ART / "start" / ("_tmp_%d_%s.SAV" % (os.getpid(), re.sub(r"\W", "_", cell)))
    tmp.parent.mkdir(parents=True, exist_ok=True)
    stage.edit(src, tmp, ops)
    kept = C.keep(tmp, "%s_start.SAV" % re.sub(r"[^\w+=.-]", "_", cell), B.ART / "start")
    tmp.unlink()
    return kept


def snapshot(g):
    """Raw game memory 0x45E030..0x4A0B80 at this moment (bytes), read in one go."""
    b = g.mem(SNAP_BASE, SNAP_END - SNAP_BASE)
    if len(b) != SNAP_END - SNAP_BASE:
        raise D.DriverError("snapshot: read %d of %d bytes" % (len(b), SNAP_END - SNAP_BASE))
    return b


def region_hashes(b):
    return {k: sha_bytes(b[a - SNAP_BASE:a - SNAP_BASE + n]) for k, (a, n) in REGIONS.items()}


def strategic(b):
    """The state the [R-code] condition names, parsed from a snapshot's bytes (not from an analyser's output of a save): nations 0 and 6 (unity,
    cities, treasury, relation 0-6), every live army of both with its field strength (Σ weight×troops/100 // 80 × morale, `sav.field_strength`),
    and the per-nation sums armies(n)."""
    nat = lambda n: sav.parse_nation(b[D.NATIONS - SNAP_BASE + n * D.NATION_LEN:D.NATIONS - SNAP_BASE + (n + 1) * D.NATION_LEN], n)
    out = {"nations": {}, "armies": []}
    for n in (0, 6):
        N = nat(n)
        out["nations"][n] = {"name": N["name"], "unity": N["unity"], "cities": N["cities_count"], "city_list_len": len(N["city_list"]),
                             "treasury": N["treasury"], "rel_rome_gaul": N["relations"].get("Gaul" if n == 0 else "Rome")}
    tot = {0: 0, 6: 0}
    for i in range(200):
        r = b[D.ARMIES - SNAP_BASE + i * D.ARMY_LEN:D.ARMIES - SNAP_BASE + (i + 1) * D.ARMY_LEN]
        a = sav.parse_army(r, i)
        if a["troops"] > 0 and a["owner"] in (0, 6):
            fs = sav.field_strength(a)
            tot[a["owner"]] += fs
            out["armies"].append({"id": i, "owner": a["owner"], "xy": [a["x"], a["y"]], "troops": a["troops"], "morale": a["morale"], "strength": fs,
                                  "units": [(u["type"], u["troops"], u["quality"]) for u in a["units"]]})
    out["armies_sum"] = tot
    a0 = [a for a in out["armies"] if a["id"] == C.ROME_ARMY]
    out["winner"] = 0 if a0 else 6          # the loser's army is deleted by the Battle ended OK: Rome's army 0 alive = Rome won
    return out


def rcode(st):
    """[R-code] preconditions for the box (decompiled report §9 item 6; war-cascade §2.3): human-AI battle (always here), armies(W) < armies(L),
    unity(L) > 500, cities(L) > 7, then Random(5) < 2. Evaluated on the state read from memory after the write-back (the game's own order: the OK's
    write-back, then the sums). Returns the three tests and whether all pass (the draw itself is not observable without the B11 hook)."""
    W = st["winner"]
    L = 6 if W == 0 else 0
    t = {"winner": W, "loser": L, "armies_W": st["armies_sum"][W], "armies_L": st["armies_sum"][L],
         "unity_L": st["nations"][L]["unity"], "cities_L": st["nations"][L]["cities"]}
    t["armies_W_lt_L"] = t["armies_W"] < t["armies_L"]
    t["unity_L_gt_500"] = t["unity_L"] > 500
    t["cities_L_gt_7"] = t["cities_L"] > 7
    t["preconditions_pass"] = t["armies_W_lt_L"] and t["unity_L_gt_500"] and t["cities_L_gt_7"]
    return t


def save_snap(tag, label, b):
    snaps = B.ART / "snaps"
    snaps.mkdir(parents=True, exist_ok=True)
    tmp = snaps / ("_tmp_%d.bin.gz" % os.getpid())
    with gzip.open(tmp, "wb", 6) as f:
        f.write(b)
    kept = C.keep(tmp, "%s_%s.snap.gz" % (tag, label), snaps)
    tmp.unlink()
    return kept


def append_trial(rec):
    B.DATA.mkdir(parents=True, exist_ok=True)
    with open(B.DATA / TRIALS, "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_trials():
    f = B.DATA / TRIALS
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def wait_battle(g, log, limit=40):
    t0 = time.time()
    while time.time() - t0 < limit:
        if g.in_battle() and g.find_windows(" v "):
            return round(time.time() - t0, 2)
        time.sleep(0.5)
    raise D.DriverError("battle window did not open in %d s" % limit)


def turn_reads(g):
    """Rome and Gaul from game memory: relation, treasury, unity, cities (for the per-turn table; the saves carry the rest)."""
    out = {}
    for n in (0, 6):
        N = g.nation_state(n)
        out[N["name"]] = {"treasury": N["treasury"], "unity": N["unity"], "cities": N["cities_count"],
                          "rel": N["relations"].get("Gaul" if n == 0 else "Rome"), "alive": N["alive"]}
    return out


def run_turns(g, tag, n, log, rec):
    """N End turn clicks, each proven (`end_turn(reclick=False)`: DriverError if there is no sign of the turn starting, never a second click).
    Per turn: the autosave the game wrote (copied), memory reads of Rome and Gaul, the news texts the turn raised (OCR of every box), a screenshot."""
    rows = []
    for t in range(1, n + 1):
        before = turn_reads(g)
        t0 = time.time()
        try:
            auto, texts = g.end_turn(reclick=False, strict_confirm=False)
            err = None
        except Exception as e:      # noqa: BLE001
            auto, texts, err = None, [], "%s: %s" % (type(e).__name__, e)
        row = {"turn_index": t, "before": before, "autosave": auto, "texts": texts, "error": err, "seconds": round(time.time() - t0, 1)}
        if err is None:
            row["after"] = turn_reads(g)
            row["calendar"] = g.calendar()
            f = D.G / auto
            if f.exists():
                row["save"] = C.keep(f, "%s_t%d_%s" % (tag, t, auto), B.ART / "turns").name
            row["screen"] = C.shot(g, "%s_t%d.png" % (tag, t), folder=B.ART / "shots").name
        log("turn", trial=tag, **{k: v for k, v in row.items() if k != "before"})
        rows.append(row)
        if err:
            break
    rec["turns"] = rows


def trial(cell, seed, answer, turns, log, rep=1, label=None):
    """One whole run from a fresh process. `answer`: yes | no | capture. `no` and `capture` both press No (the driver's `capture` mode: screenshot + controls + No;
    its `no` mode records neither, which a Yes/No pair needs); the plan is recorded as given. Returns the record (also appended)."""
    tag = "%s_s%d_%s_r%d" % (cell.replace("+", "-").replace("=", ""), seed, label or answer, rep)
    rec = {"trial": tag, "cell": cell, "seed": seed, "answer_plan": answer, "rep": rep, "exe": C.NORMAL_EXE, "build": "normal", "turns_plan": turns,
           "level": "L1 from FLD-RG (labelled synthetic)", "stamp": C.STAMP, "status": "started"}
    g = B.PeaceGame(exe=C.NORMAL_EXE)
    pre = {}
    try:
        base, _, extra = cell.partition("+")
        ops_extra = []
        for kv in [x for x in extra.split(",") if x]:
            k, v = kv.split("=")
            m = re.fullmatch(r"(unity|treasury|ncities)(\d+)", k)
            w = re.fullmatch(r"weak(\d+)", k)
            if m:
                ops_extra.append((m.group(1), int(m.group(2)), int(v)))
            elif re.fullmatch(r"own\d+", k):      # army N becomes nation v's (an existing army; position and map untouched)
                ops_extra.append(("owner", int(k[3:]), int(v)))
            elif re.fullmatch(r"strong\d+", k):   # army N = v heavy-infantry battalions of 6,000 (quality 6)
                ops_extra.append(("units", int(k[6:]), [("hi", 6000, 6)] * int(v)))
            elif w:                  # army N replaced by one LI battalion of v troops (quality 6): a weaker Rome elsewhere (armies(L) test)
                ops_extra.append(("units", int(w.group(1)), [("li", int(v), 6)]))
            else:
                raise ValueError("gate op %r" % kv)
        start = stage_start(cell, ops_extra)
        t0 = time.time()
        B.kill_mine(g)
        boxes = g.load(start, seed)
        rec.update({"start_save": start.name, "start_sha256": C.sha(start), "seed_line": g.seed_line, "open_boxes": boxes, "load_seconds": round(time.time() - t0, 1)})
        a0, a10 = g.army_state(C.ROME_ARMY), g.army_state(C.GAUL_ARMY)
        if (a0["x"], a0["y"]) != C.STAGE_TILE or (a10["x"], a10["y"]) != C.GAUL_TILE or a0["moves"] <= 0:
            raise D.DriverError("geometry: army 0 at %s moves %s, army 10 at %s" % ((a0["x"], a0["y"]), a0["moves"], (a10["x"], a10["y"])))
        rec["armies_loaded"] = {"rome0": [(u["type"], u["troops"], u["quality"]) for u in a0["units"]], "gaul10": [(u["type"], u["troops"], u["quality"]) for u in a10["units"]],
                                "morale": [a0["morale"], a10["morale"]]}
        rb = []
        for o in ops_extra:        # every extra L1 edit is read back from the game's memory before the attack
            if o[0] == "owner":
                got = g.army_state(o[1])["owner"]
            elif o[0] == "units":
                got = [(u["type"], u["troops"], u["quality"]) for u in g.army_state(o[1])["units"]]
                o = (o[0], o[1], [tuple(x) for x in o[2]])
            elif o[0] == "unity":
                got = g.nation_state(o[1])["unity"]
            elif o[0] == "ncities":
                got = g.nation_state(o[1])["cities_count"]
            else:
                continue
            rb.append({"op": [o[0], o[1]], "want": o[2], "got": got})
            if got != o[2]:
                raise D.DriverError("read-back mismatch for %s: want %s got %s" % (o[:2], o[2], got))
        rec["readback"] = rb
        rec["randseed_loaded"] = struct.unpack("<I", g.mem(D.RAND_SEED, 4))[0]
        rec["state_at_load"] = region_hashes(snapshot(g))
        g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
        g.click_tile(*C.GAUL_TILE, pause=0.0)
        dt = wait_battle(g, log)
        rec["battle_open_s"] = dt
        rec["battle_title"] = g.find_windows(" v ")[0][1]
        rec["randseed_battle_open"] = struct.unpack("<I", g.mem(D.RAND_SEED, 4))[0]
        shots = B.ART / "shots"
        shots.mkdir(parents=True, exist_ok=True)
        tmp_end = shots / ("_tmp_end_%d.png" % os.getpid())

        def pre_answer(info):
            b = snapshot(g)
            pre["bytes"], pre["info"] = b, info
            pre["strategic"] = strategic(b)
            log("pre_answer", trial=tag, text=info["text"], buttons=info["buttons"], geometry=info["geometry"])

        res = g.play_battle(shot=tmp_end, on_dialog={"capture": "capture", "yes": "yes", "no": "capture"}[answer], pre_answer=pre_answer)
        if tmp_end.exists():
            rec["battle_ended_shot"] = C.keep(tmp_end, "%s_battle-ended.png" % tag, shots).name
            tmp_end.unlink()
        rec["end_turn_clicks"], rec["battle_ended_text"] = res["end_turn_clicks"], res["battle_ended_text"]
        d = res["dialogs"]
        rec["box_opened"] = bool(d)
        rec["dialogs"] = []
        for x in d:
            x = dict(x)
            if x.get("shot") and Path(x["shot"]).exists():
                x["shot"] = C.keep(x["shot"], "%s_%s" % (tag, Path(x["shot"]).name), shots).name
            rec["dialogs"].append(x)
        if not d:
            b = snapshot(g)             # no box: the same read, right after the Battle ended box closed and the map is back
            pre["bytes"], pre["strategic"] = b, strategic(b)
        rec["pre_answer_when"] = "box up, before the click" if d else "no box: after the Battle ended box closed and the map returned"
        rec["pre_regions"] = region_hashes(pre["bytes"])
        rec["pre_sha256"] = sha_bytes(pre["bytes"])
        rec["pre_snap"] = save_snap(tag, "pre", pre["bytes"]).name
        rec["strategic_pre"] = pre["strategic"]
        rec["rcode"] = rcode(pre["strategic"])
        rec["box_title"] = d[0]["title"] if d else None
        rec["box_text"] = d[0]["text"] if d else None
        rec["box_buttons"] = [c["text"] for c in (d[0]["controls"] or [])] if d and d[0].get("controls") else None
        rec["answered"] = d[0]["answer"] if d else None
        rec["answer_click"] = {k: d[0].get(k) for k in ("click", "clicks", "closed")} if d else None
        if d and d[0]["title"] == "Offer of peace" and not d[0].get("closed"):
            raise D.DriverError("the Offer of peace box was not proven closed")
        if d and d[0]["title"] == "Offer of peace" and answer != "capture" and d[0]["answer"].lower() != answer:
            raise D.DriverError("answered %s, plan %s" % (d[0]["answer"], answer))
        time.sleep(1)
        rec["after_answer"] = {"windows": [(w[1], w[4], w[5]) for w in g.popups()], "randseed": struct.unpack("<I", g.mem(D.RAND_SEED, 4))[0],
                               "reads": turn_reads(g), "regions": region_hashes(snapshot(g))}
        post = g.save_as("%s_post.SAV" % tag)
        rec["post_save"] = C.keep(post, post.name).name
        rec["post_sha256"] = C.sha(post)
        if turns:
            run_turns(g, tag, turns, log, rec)
        rec["status"] = "ok"
    except Exception as e:      # noqa: BLE001 - an error is a result: recorded, never retried silently
        rec["status"] = "error"
        rec["error"] = "%s: %s" % (type(e).__name__, e)
        rec["traceback"] = traceback.format_exc()[-1500:]
        try:
            rec["windows"] = [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")]
            rec["screenshot"] = C.shot(g, "error_%s_%s.png" % (tag, time.strftime("%H%M%S")), folder=B.ART / "shots").name
        except Exception:       # noqa: BLE001
            pass
        log("trial_error", trial=tag, error=rec["error"])
    finally:
        rec["pids_killed"] = B.kill_mine(g)
    append_trial(rec)
    log("trial_done", trial=tag, status=rec["status"], box=rec.get("box_opened"), rcode=rec.get("rcode"))
    return rec


def parse_seeds(s):
    out = []
    for part in s.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def next_rep(cell, seed, label):
    return 1 + sum(1 for r in read_trials() if r.get("trial", "").startswith("%s_s%d_%s_r" % (cell.replace("+", "-").replace("=", ""), seed, label)))


def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[0] not in ("survey", "pair", "trial"):
        sys.exit(__doc__)
    turns = int(a[a.index("--turns") + 1]) if "--turns" in a else 4
    log = C.Log("b16-run-%s" % a[0], B.DATA)
    xv = B.start_xvfb()
    log("xvfb", pid=xv, display=B.DISPLAY)
    cell = a[1]
    if a[0] == "survey":
        for seed in parse_seeds(a[2]):
            r = trial(cell, seed, "capture", 0, log, rep=next_rep(cell, seed, "survey"), label="survey")
    elif a[0] == "pair":
        for seed in parse_seeds(a[2]):
            for ans in ("yes", "no"):
                trial(cell, seed, ans, turns, log, rep=next_rep(cell, seed, ans))
    else:
        trial(cell, int(a[2]), a[3], turns, log, rep=next_rep(cell, int(a[2]), a[3]))


if __name__ == "__main__":
    main()
