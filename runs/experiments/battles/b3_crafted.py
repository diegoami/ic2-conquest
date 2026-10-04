#!/usr/bin/env python3
"""B3 crafted mid-battle saves (battles plan §4 B3, synthetic L2): edit the battle block of a lab `BATTLEnn.SAV`, resume it on the lab exe
(File > Open, one process per scenario), and report what the game does with it.

    python3 runs/experiments/battles/b3_crafted.py [scenario ...]      # default: all

Source (c*): `hi-hi-one_s1_r1_BATTLE02.SAV` (lab seed 1, HI v HI one unit each, placement done: Rome slot 0 at (4,2), Gaul slot 20 at (4,9)).
Scenarios (each `stage.block_edit`, written to artifacts/run-exp-battle-sweep/crafted/<name>.SAV, never committed):
  c0_control    the source unedited                         c1_noop      a no-op block edit (must be byte-identical to c0, and resume identically)
  c2_troops     Rome slot 0 troops 6000 -> 3000 (mirrored into the army)    c3_adjacent  Rome slot 0 moved to (4,8), next to Gaul's (4,9)
  c4_slot_only  troops 3000 in the SLOT only (the army keeps 6000)          c5_stale_grid  the grid word of Gaul's cell emptied (grid inconsistent)
  c6_same_cell  both units on the same cell (4,9)           c7_type      Rome slot 0 type hi -> hc (mirrored)
  d0_control d3_adjacent d5_stale_grid d6_same_cell d8_far   the position scenarios again on BATTLE03 (placement done), see SOURCES below
For each: the file's block v the game's memory right after the resume (what the game kept, repaired or rejected), the first half-round (the lab
series' BATTLE01 of the resumed process) v the loaded state, the post-battle strategic armies, the series. Everything is appended to
b3-crafted-<stamp>.jsonl (tracked); nothing is retried silently: a scenario that fails is recorded with its error and the run goes on.
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import stage  # noqa: E402
import trials as T  # noqa: E402
from harness.driver import DriverError, Game  # noqa: E402
from state import battle, battle_block as BB, sav  # noqa: E402

SOURCE = "hi-hi-one_s1_r1_BATTLE02.SAV"
SCENARIOS = {
    "c0_control": [],
    "c1_noop": [("header", {}), ("slot", 0, {})],
    "c2_troops": [("slot", 0, {"troops": 3000})],
    "c3_adjacent": [("slot", 0, {"y": 8})],
    "c4_slot_only": [("slot", 0, {"troops": 3000}, False)],
    "c5_stale_grid": [("grid", 4, 9, BB.EMPTY)],
    "c6_same_cell": [("slot", 0, {"x": 4, "y": 9})],
    "c7_type": [("slot", 0, {"type": "hc"})],
}


# The first batch (c*) edited BATTLE02, the PLACEMENT phase (header y1 = 0): the AI re-places the units, so position edits (c3, c5, c6) were
# overwritten and the outcome was identical to the control. The second batch (d*) edits BATTLE03 (y1 = 1: placement done; Rome slot 0 at (4,4),
# Gaul slot 20 at (4,9)), where positions stick. Source file per scenario:
SOURCES = {n: "hi-hi-one_s1_r1_BATTLE03.SAV" for n in ("d0_control", "d3_adjacent", "d5_stale_grid", "d6_same_cell", "d8_far")}
SCENARIOS.update({
    "d0_control": [],
    "d3_adjacent": [("slot", 0, {"y": 8})],            # next to Gaul's (4,9)
    "d5_stale_grid": [("grid", 4, 9, BB.EMPTY)],        # the grid says Gaul's cell is empty
    "d6_same_cell": [("slot", 0, {"x": 4, "y": 9})],   # both units on one cell
    "d8_far": [("slot", 0, {"x": 13, "y": 0})],         # as far from Gaul as the grid allows
    "e0_x2": [],                                         # B0's natural FLD-RG battle, half-round 4 (header x2 = 1): is x2 read from memory right?
})
SOURCES["e0_x2"] = "gate2_a_BATTLE04.SAV"


def block_diff(a, b):
    """Fields that differ between two parsed blocks (header, every slot field, grid cells)."""
    out = []
    for f in ("attacker_army", "defender_army", "x2", "y1", "half_round"):
        if a[f] != b[f]:
            out.append((f, a[f], b[f]))
    for sa, sb in zip(a["slots"], b["slots"]):
        for f in BB.SLOT_FIELDS + ("name",):
            if sa[f] != sb[f]:
                out.append((f"slot{sa['slot']}.{f}", sa[f], sb[f]))
    out += [(f"grid[{i}]", x, y) for i, (x, y) in enumerate(zip(a["grid"], b["grid"])) if x != y]
    return out


def run_scenario(name, log):
    src = C.ART / SOURCES.get(name, SOURCE)
    if not src.exists() and (C.ROOT / "artifacts" / "run-exp-battle-probe" / src.name).exists():
        C.keep(C.ROOT / "artifacts" / "run-exp-battle-probe" / src.name)       # B0's save, copied beside ours (hash recorded)
    crafted = C.ART / "crafted"
    crafted.mkdir(parents=True, exist_ok=True)
    raw = bytearray(src.read_bytes())
    stage.block_edit(raw, SCENARIOS[name])
    tmp = crafted / f"_tmp_{name}.SAV"
    tmp.write_bytes(bytes(raw))
    kept = C.keep(tmp, f"CRAFT_{name}.SAV", crafted)
    tmp.unlink()
    written = BB.block_of_save(kept.read_bytes())
    rec = {"scenario": name, "edits": [list(map(str, e)) for e in SCENARIOS[name]], "file": kept.name, "sha256": C.sha(kept),
           "identical_to_source": kept.read_bytes() == src.read_bytes(), "source": SOURCES.get(name, SOURCE), "level": "L2 (synthetic, block edit)", "build": "lab s1"}
    g = Game(exe=C.LAB_EXE % 1)
    for f in C.D.G.glob("BATTLE*.SAV"):
        C.keep(f, f"stray_b3_{name}_{f.name}")
        f.unlink()
    try:
        t0 = time.time()
        g.start()
        shutil.copy(kept, C.D.G / kept.name)
        g.open_file_dialog(kept.name)
        g.wait(lambda: g.in_battle() and g.find_windows(" v "), 40, "battle window after the resume")
        time.sleep(2)
        rec["resume_seconds"] = round(time.time() - t0, 1)
        rec["title"] = [w[1] for w in g.find_windows(" v ")]
        loaded = g.battle_state()
        rec["memory_v_file"] = block_diff(written, loaded)
        rec["memory_equals_file"] = not rec["memory_v_file"]
        rec["army0_in_memory"] = [(u["type"], u["troops"]) for u in g.army_state(0)["units"]]
        rec["army10_in_memory"] = [(u["type"], u["troops"]) for u in g.army_state(10)["units"]]
        log("resumed", scenario=name, seconds=rec["resume_seconds"], memory_equals_file=rec["memory_equals_file"], memory_v_file=rec["memory_v_file"][:12])
        shots = C.ART / "shots"
        shots.mkdir(exist_ok=True)
        g.shot(shots / f"b3_{name}_resumed.png", window=str(g.find_windows(" v ")[0][0]))
        res = g.play_battle(shot=shots / f"b3_{name}_battle-ended.png", on_dialog="capture")
        rec["end_turn_clicks"], rec["dialogs"] = res["end_turn_clicks"], [d["title"] for d in res["dialogs"]]
        post = g.save_as(f"b3_{name}_post.SAV")
        kp = C.keep(post, f"b3_{name}_post.SAV", crafted)
        series = [C.keep(f, f"b3_{name}_{f.name}", crafted).name for f in sorted(C.D.G.glob("BATTLE*.SAV"))]
        for f in C.D.G.glob("BATTLE*.SAV"):
            f.unlink()
        rec["series"], rec["half_rounds"], rec["post_save"], rec["post_sha256"] = series, len(series), kp.name, C.sha(kp)
        first = BB.from_save(crafted / series[0]) if series else None
        if first:
            d = BB.diff(loaded, first)
            rec["first_half_round"] = {"half_round": first["half_round"], "rows": {k: v for k, v in d["slots"].items()},
                                       "unambiguous": d["unambiguous"], "ambiguous": d["ambiguous"]}
        pre = sav.load(str(kept))
        sn = battle.snapshot(pre, [0, 10], [0, 6])
        d = battle.diff(sn, battle.snapshot(sav.load(str(kp)), [0, 10], [0, 6]), 0, 10)
        rec["post_battle"] = {"winner": d["winner"], "attacker": {k: d["attacker"][k] for k in ("troops_before", "troops_after", "destroyed")},
                              "defender": {k: d["defender"][k] for k in ("troops_before", "troops_after", "destroyed")}}
        rec["status"] = "ok"
    except Exception as e:      # noqa: BLE001
        rec["status"] = "error"
        rec["error"] = f"{type(e).__name__}: {e}"
        try:
            rec["windows"] = [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")]
            g.shot(C.ART / f"error_b3_{name}.png")
        except Exception:       # noqa: BLE001
            pass
        log("error", scenario=name, error=rec["error"])
    finally:
        C.kill_stale(g)
    return rec


def main():
    names = [a for a in sys.argv[1:] if a in SCENARIOS] or list(SCENARIOS)
    log = C.Log("b3-crafted")
    out = C.DATA / f"b3-crafted-{C.STAMP}.jsonl"
    recs = {}
    for n in names:
        recs[n] = run_scenario(n, log)
        with open(out, "a") as f:
            f.write(json.dumps(recs[n], default=str) + "\n")
        log("scenario_done", scenario=n, status=recs[n]["status"], half_rounds=recs[n].get("half_rounds"), post_sha12=(recs[n].get("post_sha256") or "")[:12])
    # round trip: the no-op edit is the same file and resumes to the same series as the control
    if "c0_control" in recs and "c1_noop" in recs and all(recs[k]["status"] == "ok" for k in ("c0_control", "c1_noop")):
        a, b = recs["c0_control"], recs["c1_noop"]
        rd = lambda r, n: (C.ART / "crafted" / n).read_bytes()
        rt = {"noop_file_identical_to_source": recs["c1_noop"]["identical_to_source"], "series_a": len(a["series"]), "series_b": len(b["series"]),
              "series_identical": len(a["series"]) == len(b["series"]) > 0 and all(rd(a, x) == rd(b, y) for x, y in zip(a["series"], b["series"])),
              "post_identical": a["post_sha256"] == b["post_sha256"]}
        with open(out, "a") as f:
            f.write(json.dumps({"scenario": "roundtrip_c0_v_c1", **rt}) + "\n")
        log("roundtrip", **rt)
    print(out)


if __name__ == "__main__":
    main()
