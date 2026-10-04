#!/usr/bin/env python3
"""Claims audit (PR #36 review): every number and every "identical / verified / 0 violations" claim of findings/2026-10-04-tactical-battle-sweep.md,
the battles.md bot section and tests/results.md, recomputed from the TRACKED file it cites, written as a table `claims-audit-<stamp>.md`
in the tracked data folder (never overwritten). Exit 1 if any claim does not match.

    python3 runs/experiments/battles/claims_audit.py
"""
import csv
import glob
import json
import statistics as st
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

D = C.DATA


def latest(pat):
    return sorted(D.glob(pat))[-1]


def jl(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def main():
    trials = [r for r in jl(D / "trials.jsonl") if r.get("status") == "ok"]
    ana = json.loads(latest("b2-analysis-*.json").read_text())
    anaf = latest("b2-analysis-*.json").name
    ver = json.loads(sorted(D.glob("b2-verify-*093834.json"))[0].read_text())
    rows = []

    def claim(where, text, file, value, expected):
        rows.append((where, text, file, value, expected, "y" if value == expected else "**n**"))

    ok = lambda f: [r for r in trials if f(r)]
    sec = [r["seconds"] for r in trials]
    claim("finding", "12 B4 trials ok", "trials.jsonl", len(trials), 12)
    claim("finding", "mean 53.4 s per battle", "trials.jsonl", round(st.mean(sec), 1), 53.4)
    claim("finding", "range 48.4 to 58.5 s", "trials.jsonl", (min(sec), max(sec)), (48.4, 58.5))
    for s, e in ((1, 55.9), (2, 49.1), (3, 55.3)):
        claim("finding", f"seed {s} mean {e} s", "trials.jsonl", round(st.mean(r["seconds"] for r in trials if r["seed"] == s), 1), e)
    for k, e in (("loaded", 19.3), ("click_to_battle", 6.3), ("battle_open_to_over", 18.2), ("post_save", 8.1)):
        claim("finding", f"mean timing {k} {e} s", "trials.jsonl", round(st.mean(r["timing"][k] for r in trials), 1), e)
    claim("finding", "0 End turn clicks in all 12", "trials.jsonl", sum(r["end_turn_clicks"] for r in trials), 0)
    for s, hr, gaul, peace, sha in ((1, 19, 2958, "Offer of peace", "1043d0aaccf3"), (2, 18, 2831, "", "3e4a5b00b6de"), (3, 15, 4196, "Offer of peace", "0e99a9b52809")):
        rs = ok(lambda r: r["seed"] == s)
        claim("finding", f"seed {s}: {hr} half-rounds, Gaul {gaul}, dialog {peace!r}, post sha {sha}, 4 runs", "trials.jsonl",
              (sorted({r["half_rounds"] for r in rs}), sorted({r["defender_result"]["troops_after"] for r in rs}), sorted({r.get("dialog", "") for r in rs}),
               sorted({r["post_sha256"][:12] for r in rs}), len(rs)), ([hr], [gaul], [peace], [sha], 4))
        claim("finding", f"seed {s}: attacker destroyed, Gaul wins in all 4", "trials.jsonl", sorted({(r["winner"], r["attacker_result"]["destroyed"]) for r in rs}), [("defender", True)])
    for s in (1, 2, 3):
        res = []
        for f in D.glob(f"compare-hi-hi-one_s{s}_r1-hi-hi-one_s{s}_r[234]-*.json"):
            c = json.loads(f.read_text())
            res.append((c["b"][-2:], c["series_identical"], c["post_identical"], c["aligned"] > 0))
        claim("finding", f"seed {s}: r1 byte-identical to r2, r3, r4 (series and post)", "compare-hi-hi-one_s%d_r1-*.json" % s, sorted(set(res)),
              [(f"r{k}", True, True, True) for k in (2, 3, 4)])
    claim("finding", "Offer of peace in 2 of 3 seeds", "trials.jsonl", len({r["seed"] for r in trials if r.get("dialog") == "Offer of peace"}), 2)
    # verify
    claim("finding", "memory = Save As block in 3 of 3 phases", "b2-verify-20261004-093834.json", [p["memory_equals_save_block"] for p in ver["phases"]], [True] * 3)
    claim("finding", "slot positions <-> screen 168 of 168 in 3 phases", "b2-verify-20261004-093834.json", [p["screen_cells_agreeing"] for p in ver["phases"]], [168] * 3)
    claim("finding", "half-round counter 2 at placement, 3, 5 after End turn clicks", "b2-verify-20261004-093834.json", [p["half_round"] for p in ver["phases"]], [2, 3, 5])
    claim("finding", "header +2 = 10 (defender army), +0 = 0", "b2-verify-20261004-093834.json", {(p["attacker_army"], p["defender_army"]) for p in ver["phases"]}, {(0, 10)})
    claim("finding", "AI side re-sorted: slot order differs from the army's", "b2-verify-20261004-093834.json", (ver["side1"]["same_order"], ver["side1"]["same_set"]), (False, True))
    claim("finding", "slot label = strategic label for every unit", "b2-verify-20261004-093834.json", ver["merc_label_equals_strategic_label_for_every_unit"], True)
    # analysis
    g = ana["per_group"]
    claim("finding", "241 decoded files (33 B0 + 208 trials)", anaf, (ana["files_decoded"], g["B0 natural FLD-RG series (gate2_a, gate2_s2a)"]["files"], g["B4 1-v-1 trials"]["files"]), (241, 33, 208))
    claim("finding", "0 inconsistent grid files / 0 sprite violations in the 241", anaf, (ana["grid_inconsistent_files"], ana["sprite_rule_violations"]), (0, 0))
    claim("finding", "B0 natural battles: 125 loss rows, 14 unambiguous", anaf, (g["B0 natural FLD-RG series (gate2_a, gate2_s2a)"]["loss_rows"], g["B0 natural FLD-RG series (gate2_a, gate2_s2a)"]["unambiguous"]), (125, 14))
    claim("finding", "B4 1-v-1: 272 of 272 unambiguous", anaf, (g["B4 1-v-1 trials"]["loss_rows"], g["B4 1-v-1 trials"]["unambiguous"]), (272, 272))
    claim("finding", "aggregate 286 of 397", anaf, (ana["loss_rows_unambiguous"]["unambiguous"], ana["loss_rows_unambiguous"]["loss_rows"]), (286, 397))
    hl1 = jl(D / "halfrounds-hi-hi-one_s1_r1.jsonl")
    claim("finding", "seed 1: 26 of 26 loss rows unambiguous", "halfrounds-hi-hi-one_s1_r1.jsonl", (sum(r.get("since_previous", {}).get("losses", 0) for r in hl1), sum(r.get("since_previous", {}).get("unambiguous", 0) for r in hl1)), (26, 26))
    claim("finding", "x2 rule holds on 241 files", anaf, (ana["x2_rule"]["files_checked"], ana["x2_rule"]["violations"]), (241, 0))
    a = ana["all_battle_saves"]
    n = lambda k: a[k]["files"]
    claim("finding", "763 saves = 345 B0 + 192 B3 + 226 trials/other", anaf, (ana["all_battle_saves_total"], n("B0 probe series (artifacts/run-exp-battle-probe)"), n("B3 crafted/resumed series"), n("B4 trials and other sweep series")), (763, 345, 192, 226))
    claim("finding", "571 saves with 0 violations (B0 + trials); 14 B3 files violate", anaf,
          (a["B0 probe series (artifacts/run-exp-battle-probe)"]["sprite_violations"] + a["B4 trials and other sweep series"]["sprite_violations"], a["B3 crafted/resumed series"]["grid_inconsistent"], a["B3 crafted/resumed series"]["sprite_violations"]), (0, 14, 14))
    r = ana["size_class_troop_range"]
    claim("finding", "HI ranges 250-1866 / 2024-3964 / 4083-6000", anaf, [r["hi"][c] for c in "012"], [[250, 1866], [2024, 3964], [4083, 6000]])
    claim("finding", "Ar ranges 181-789 / 1215-2046 / 2881-3411", anaf, [r["ar"][c] for c in "012"], [[181, 789], [1215, 2046], [2881, 3411]])
    claim("finding", "LI ranges 853-4728 / 5147-9669 / 10318-14500", anaf, [r["li"][c] for c in "012"], [[853, 4728], [5147, 9669], [10318, 14500]])
    claim("finding", "LC 1912 / 2426-4421 (no class 2); HC 227-801 / 1269-1574 / 1935-2337", anaf, ([r["lc"][c] for c in "01"], "2" in r["lc"], [r["hc"][c] for c in "012"]), ([[1912, 1912], [2426, 4421]], False, [[227, 801], [1269, 1574], [1935, 2337]]))
    claim("finding", "ammo at first file: HI 0, HC 0, LI 7, LC 9, Ar 25", anaf, {t: sorted(v) for t, v in ana["ammo_at_first_file"].items()}, {"hi": ["0"], "hc": ["0"], "li": ["7"], "lc": ["9"], "ar": ["25"]})
    # morale / placement / b3
    last = jl(D / "halfrounds-hi-hi-one_s1_r3.jsonl")
    claim("finding", "morale Rome 65 -> 31, Gaul 88 -> 99 (s1_r3)", "halfrounds-hi-hi-one_s1_r3.jsonl", ([s_["morale"] for s_ in last[0]["slots"]], [s_["morale"] for s_ in last[-1]["slots"]]), ([65, 88], [31, 99]))
    pos = {s: [x for x in jl(D / f"halfrounds-hi-hi-one_s{s}_r1.jsonl")[0]["slots"] if x["side"] == 1][0] for s in (1, 2, 3)}
    claim("finding", "Gaul HI first placed on row 9 at x 4 / 10 / 7", "halfrounds-hi-hi-one_s{1,2,3}_r1.jsonl", [(pos[s]["x"], pos[s]["y"]) for s in (1, 2, 3)], [(4, 9), (10, 9), (7, 9)])
    b3 = {}
    for f in sorted(D.glob("b3-crafted-*.jsonl")):
        for r_ in jl(f):
            if r_.get("status") == "ok" and "post_battle" in r_:
                b3[r_["scenario"]] = r_
    claim("finding", "14 crafted resumes", "b3-crafted-*.jsonl", len(b3), 14)
    for sc, hrs, gaul in (("c0_control", 16, 3533), ("c2_troops", 11, 5330), ("c4_slot_only", 11, 5330), ("c3_adjacent", 16, 3533), ("c5_stale_grid", 16, 3533), ("c6_same_cell", 16, 3533),
                          ("d0_control", 13, 3285), ("d3_adjacent", 11, 3285), ("d5_stale_grid", 13, 3285), ("d6_same_cell", 11, 3285), ("d8_far", 15, 3285)):
        claim("finding", f"B3 {sc}: {hrs} half-rounds, Gaul keeps {gaul}", "b3-crafted-*.jsonl", (b3[sc]["half_rounds"], b3[sc]["post_battle"]["defender"]["troops_after"]), (hrs, gaul))
    claim("finding", "c7: Rome wins, keeps 3,876; state 2 -> 5", "b3-crafted-*.jsonl", (b3["c7_type"]["post_battle"]["winner"], b3["c7_type"]["post_battle"]["attacker"]["troops_after"], [x for x in b3["c7_type"]["memory_v_file"] if x[0] == "slot0.state"]), ("attacker", 3876, [["slot0.state", 2, 5]]))
    claim("finding", "c1 no-op: file identical to source; series and post identical to c0", "b3-crafted-*.jsonl", (b3["c1_noop"]["identical_to_source"], b3["c1_noop"]["post_sha256"] == b3["c0_control"]["post_sha256"]), (True, True))
    claim("finding", "c3/c5/c6 post-battle identical to c0 (placement phase)", "b3-crafted-*.jsonl", {b3[x]["post_sha256"][:12] for x in ("c0_control", "c3_adjacent", "c5_stale_grid", "c6_same_cell")}, {"db4f576949bf"})
    claim("finding", "d0..d8 five end in one post-battle save", "b3-crafted-*.jsonl", len({b3[x]["post_sha256"] for x in ("d0_control", "d3_adjacent", "d5_stale_grid", "d6_same_cell", "d8_far")}), 1)
    claim("finding", "resume counter +1 (2->3, 3->4) / +2 (4->6)", "b3-crafted-*.jsonl", ([x for x in b3["c0_control"]["memory_v_file"] if x[0] == "half_round"], [x for x in b3["d0_control"]["memory_v_file"] if x[0] == "half_round"], [x for x in b3["e0_x2"]["memory_v_file"] if x[0] == "half_round"]),
          ([["half_round", 2, 3]], [["half_round", 3, 4]], [["half_round", 4, 6]]))
    claim("finding", "e0: x2 file 1, memory 0 after resume", "b3-crafted-*.jsonl", [x for x in b3["e0_x2"]["memory_v_file"] if x[0] == "x2"], [["x2", 1, 0]])
    # sha / screenshots / release
    sums = (D / "SAVES.sha256").read_text().splitlines()
    claim("finding", "53 screenshots hashed in SAVES.sha256", "SAVES.sha256", sum(1 for x in sums if x.strip().endswith(".png")), 53)
    claim("finding", "FLD-RG sha 39edecd1... twice byte-identical", "fixtures-build-20261004-091421.json", (json.loads((D / "fixtures-build-20261004-091421.json").read_text())["byte_identical_two_builds"], json.loads((D / "fixtures-build-20261004-091421.json").read_text())["sha256"][:8]), (True, "39edecd1"))
    rel = int(subprocess.run(["gh", "release", "view", "run-exp-battle-sweep", "--json", "assets", "-q", ".assets|length"], capture_output=True, text=True).stdout.strip() or -1)
    claim("PR body", "release holds >= 521 assets (PR body says 520 at the time; now stated as 'about 520+')", "release run-exp-battle-sweep", rel >= 521, True)
    # test counts
    for mod, e in (("test_driver_battle", 17), ("test_battle_stage", 16), ("test_battle_trials", 7)):
        out = subprocess.run([sys.executable, "-m", f"tests.{mod}"], capture_output=True, text=True, cwd=C.ROOT).stdout
        claim("results.md", f"{mod}: {e} tests pass", "tests/" + mod + ".py", out.count("\nPASS ") + out.startswith("PASS "), e)
    # sweep table
    t = latest("sweep-table-*.csv")
    tr = list(csv.DictReader(t.open()))
    claim("finding", "latest sweep table: 12 rows, build lab, level L1, halflog+counts filled", t.name, (len(tr), {x["build"] for x in tr}, all(x["halflog"] and x["loss_rows"] for x in tr)), (12, {"lab"}, True))
    bad = [r_ for r_ in rows if r_[5] != "y"]
    out = C.write_new(D, f"claims-audit-{C.STAMP}.md", "# Claims audit (PR #36)\n\nEvery claim recomputed from the tracked file it cites: %d claims, %d mismatches.\n\n"
                      "| doc | claim | file | value in file | claimed | match |\n|---|---|---|---|---|---|\n" % (len(rows), len(bad))
                      + "\n".join("| %s | %s | `%s` | %s | %s | %s |" % (w, t_, f_, str(v).replace("|", "/"), str(e).replace("|", "/"), m) for w, t_, f_, v, e, m in rows) + "\n")
    print(out, len(rows), "claims,", len(bad), "mismatches")
    for r_ in bad:
        print("MISMATCH", r_)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
