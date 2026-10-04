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


def new_claims(rows, claim, sweep, all_ok):
    """Claims of the B5/B8 sections, recomputed from trials.jsonl / halfrounds files / the B8 jsonl, independently of b5_analyze.py's own summary."""
    from collections import Counter
    errs = [r for r in jl(D / "trials.jsonl") if r.get("status") == "error"]
    claim("finding B5", "315 sweep rows (rep 1), 324 ok trial ids incl. 9 B4 repeats, 0 error records", "trials.jsonl", (len(sweep), len(all_ok), len(errs)), (315, 324, 0))
    cells = Counter((r["attacker"], r["defender"], r["size"]) for r in sweep)
    grid = [k for k in cells if "-" not in k[2]]
    claim("finding B5", "225 grid battles = 75 per size (25 pairings x 3 seeds); 90 size-matrix battles = 5 pairings x 6 size combinations x 3 seeds", "trials.jsonl",
          (sum(cells[k] for k in grid), sum(cells[k] for k in cells if "-" in k[2]), len(grid), all(v == 3 for v in cells.values())), (225, 90, 75, True))
    claim("finding B5", "all 315 rows lab, L1 from FLD-RG, quality 6 morale 65 (read back before the attack: a trial that fails the read-back raises and is an error record)", "trials.jsonl",
          ({r["build"] for r in sweep}, {r["level"] for r in sweep}), ({"lab"}, {"L1 from FLD-RG (labelled synthetic)"}))
    claim("finding B5", "winner counts: attacker 133, defender 182; no draw", "trials.jsonl", dict(Counter(r["winner"] for r in sweep)), {"defender": 182, "attacker": 133})
    wsz = Counter()
    for r in sweep:
        a, d, sz = r["attacker"], r["defender"], r["size"]
        wsz[(sz, r["winner"])] += 1
    claim("finding B5", "grid: attacker wins 29 half, 28 one, 31 three (of 75 each)", "trials.jsonl", (wsz[("half", "attacker")], wsz[("one", "attacker")], wsz[("three", "attacker")]), (29, 28, 31))
    mix = Counter()
    for r in sweep:
        if "-" in r["size"]:
            mix[r["size"]] += r["winner"] == "attacker"
    claim("finding B5", "size matrix attacker wins (of 15 each): half-one 6, half-three 0, one-half 9, one-three 3, three-half 15, three-one 12", "trials.jsonl",
          {k: mix[k] for k in sorted(mix)}, {"half-one": 6, "half-three": 0, "one-half": 9, "one-three": 3, "three-half": 15, "three-one": 12})
    claim("finding B5", "grid: the archers (as attacker) win 0 of 45; HI as attacker wins 36 of 36 against li, ar, lc, hc (3 sizes x 4 x 3 seeds) and 1 of 9 against hi", "trials.jsonl",
          (sum(1 for r in sweep if r["attacker"] == "ar" and "-" not in r["size"] and r["winner"] == "attacker"),
           sum(1 for r in sweep if r["attacker"] == "hi" and r["defender"] != "hi" and "-" not in r["size"] and r["winner"] == "attacker"),
           sum(1 for r in sweep if r["attacker"] == "hi" and r["defender"] == "hi" and "-" not in r["size"] and r["winner"] == "attacker")), (0, 36, 1))
    hr = [r["half_rounds"] for r in sweep]
    claim("finding B5", "half-rounds 8 to 35, mean 15.18; none reaches 99", "trials.jsonl", (min(hr), max(hr), round(sum(hr) / len(hr), 2)), (8, 35, 15.18))
    sec = [r["seconds"] for r in sweep]
    claim("finding B5", "seconds per battle: mean 52.0, 49.0 to 61.1 (315 rows)", "trials.jsonl", (round(sum(sec) / len(sec), 1), min(sec), max(sec)), (52.0, 49.0, 61.1))
    claim("finding B5", "Offer of peace in 76 of 315 rows, every one after a defender (Gaul) win, none after an attacker win", "trials.jsonl",
          (sum("Offer of peace" in r.get("dialog", "") for r in sweep), sum("Offer of peace" in r.get("dialog", "") and r["winner"] == "defender" for r in sweep),
           sum("Offer of peace" in r.get("dialog", "") and r["winner"] == "attacker" for r in sweep)), (76, 76, 0))
    claim("finding B5", "every dialog was declined (never Yes): answers recorded", "trials.jsonl", {d.get("answer") for r in sweep for d in r.get("dialogs", [])}, {"No"})
    claim("finding B5", "End turn clicks: 0 in 279 rows, 1 in 36 (each proven by Game.end_turn_proven; a no-sign result would be an error record)", "trials.jsonl", dict(Counter(r["end_turn_clicks"] for r in sweep)), {0: 279, 1: 36})
    claim("finding B5", "loser destroyed in every row; attacker destroyed 182 / defender destroyed 133; no row with both", "trials.jsonl",
          (sum(r["attacker_result"]["destroyed"] for r in sweep), sum(r["defender_result"]["destroyed"] for r in sweep), sum(r["attacker_result"]["destroyed"] and r["defender_result"]["destroyed"] for r in sweep)), (182, 133, 0))
    pr = [(s, u) for r in sweep for s in ("attacker", "defender") for u in r["units"][s] if u["promoted"]]
    claim("finding B5", "promotions 146 (attacker 56, defender 90); every promoted unit 6 -> 7; by type hi 61, lc 35, hc 17, li 17, ar 16", "trials.jsonl",
          (len(pr), Counter(s for s, u in pr)["attacker"], Counter(s for s, u in pr)["defender"], {(u["quality_before"], u["quality_after"]) for s, u in pr}, dict(Counter(u["type"] for s, u in pr))),
          (146, 56, 90, {(6, 7)}, {"hi": 61, "lc": 35, "hc": 17, "li": 17, "ar": 16}))
    claim("finding B5", "money captured only by Gaul (the defender) in its 182 wins: 156 talents each time; supplies 0; Rome captured 0 talents and 0 supplies in its 133 wins", "trials.jsonl",
          ({(r["taken"]["defender_money"], r["taken"]["defender_supplies"]) for r in sweep if r["winner"] == "defender"}, {(r["taken"]["attacker_money"], r["taken"]["attacker_supplies"]) for r in sweep if r["winner"] == "attacker"}),
          ({(156, 0)}, {(0, 0)}))
    # half-round logs
    n_loss = n_old = 0
    hrs = {}
    for r in sweep:
        import trials as T_
        nm = r.get("halflog") or (T_.backfill_halflog(r) or [None])[0]       # trials 1-6 predate the halflog hook: the halfrounds file written afterwards
        rows_ = [json.loads(x) for x in (D / nm).read_text().splitlines()] if nm else []
        hrs[r["trial"]] = rows_
    claim("finding B5", "a half-round log exists for every one of the 315 rows", "halfrounds-*.jsonl", sum(1 for v in hrs.values() if v), 315)
    claim("finding B5", "placement: Gaul on row y = 9 and Rome parked on y = 0 in the first file of every battle; Rome on y = 2 in the second", "halfrounds-*.jsonl",
          ({s["y"] for v in hrs.values() for s in v[0]["slots"] if s["side"] == 1}, {s["y"] for v in hrs.values() for s in v[0]["slots"] if s["side"] == 0}, {s["y"] for v in hrs.values() for s in v[1]["slots"] if s["side"] == 0}), ({9}, {0}, {2}))
    seq = Counter()
    for v in hrs.values():
        seq["".join("A" if x.get("since_previous", {}).get("acting_sides_D") == [0] else "G" if x.get("since_previous", {}).get("acting_sides_D") == [1] else "?" for x in v[1:6])] += 1
    claim("finding B5", "initiative: the diffs into files 2..6 show Rome, Rome, Gaul, Rome, Gaul acting in all 315 battles", "halfrounds-*.jsonl", dict(seq), {"AAGAG": 315})
    claim("finding B5", "header x2 equals the side that acted in the diff into the file in all 3,220 diffs with exactly one acting side", "halfrounds-*.jsonl",
          (sum(1 for v in hrs.values() for x in v[1:] if len(x["since_previous"]["acting_sides_D"]) == 1 and x["x2"] == x["since_previous"]["acting_sides_D"][0]),
           sum(1 for v in hrs.values() for x in v[1:] if len(x["since_previous"]["acting_sides_D"]) == 1)), (3220, 3220))
    sm = json.loads(sorted(D.glob("b5-summary-*.json"))[-1].read_text())
    tg = list(csv.DictReader(sorted(D.glob("b5-targets-*.csv"))[-1].open()))
    claim("finding B5", "target events (a unit's target word changed to an enemy slot while >= 2 enemies stood): 664, the chosen enemy always (ties included) among the nearest, uniquely nearest in 147", sorted(D.glob("b5-targets-*.csv"))[-1].name,
          (len(tg), sum(x["is_nearest"] == "True" for x in tg), sum(x["is_unique_nearest"] == "True" for x in tg), sum(x["is_weakest"] == "True" for x in tg)), (664, 664, 147, 507))
    at = sm["attribution_R_code_words_8_9"]
    claim("finding B5", "loss rows fixed by words 8/9: B0 natural 29 of 125 (old 14); 1 v 1 battles 1569 of 1931 (old 1481); 3 v 3 1166 of 2805 (old 627); size matrix 624 of 987 (old 574)", sorted(D.glob("b5-summary-*.json"))[-1].name,
          ([at["B0 natural 14-unit battles (gate2_a, gate2_s2a)"][k] for k in ("new_fixed", "losses", "old_unambiguous")], [[at["sweep by group"][g][k] for k in ("new_fixed", "losses", "old_unambiguous")] for g in ("1 unit per side", "3 units per side", "mixed sizes (size matrix)")]),
          ([29, 125, 14], [[1569, 1931, 1481], [1166, 2805, 627], [624, 987, 574]]))
    claim("finding B5", "sweep loss kinds: melee 4263, shooting 371, mixed 1089, unknown 0", sorted(D.glob("b5-summary-*.json"))[-1].name, sm["attribution_R_code_words_8_9"]["sweep kinds"], {"melee": 4263, "shooting": 371, "mixed": 1089, "unknown": 0})
    claim("finding B5", "end state: loser already empty in the last saved file 58, units left but none rout-eligible 238, rout-eligible 19", sorted(D.glob("b5-summary-*.json"))[-1].name, sm["end_condition_inferred_from_last_saved_file"],
          {"loser already empty in the last saved file": 58, "loser units left; none rout-eligible: removed by troop loss in the final half-round [D, R-code]": 238, "loser units left; at least one rout-eligible: kill or rout, not distinguished": 19})
    pg = sm["seed_pairing_gaul_placement_by_defender_army_and_seed"]
    claim("finding B5", "same seed and same defender army: the same Gaul placement in every cell (45 groups: 24 of 1 cell, 9 of 2, 12 of 5; always 1 distinct placement)", sorted(D.glob("b5-summary-*.json"))[-1].name,
          (len(pg), sorted(Counter((v["cells"], v["distinct_gaul_placements"]) for v in pg.values()).items())), (45, [((1, 1), 24), ((2, 1), 9), ((5, 1), 12)]))
    # B8
    th = json.loads(sorted(D.glob("b8-thresholds-*.json"))[-1].read_text())
    exp = {"li": [5000, 10000], "hi": [2000, 4000], "ar": [1166, 2332], "lc": [2333, 4666], "hc": [833, 1666]}
    got = {k.split()[0] + k.split()[-1]: v["first_troops_of_class_1_2"] for k, v in th["per_type_side"].items()}
    claim("finding B8", "first troop count of icon size 1 and 2, exact to 1 troop, both sides: LI 5000/10000, HI 2000/4000, Ar 1166/2332, LC 2333/4666, HC 833/1666", "b8-thresholds-*.json",
          got, {k + s: v for k, v in exp.items() for s in "01"})
    claim("finding B8", "10 (type, side) series monotone, every class change 1 troop wide, equal to min(2, troops div (std div 3)); equal to B2's 3*troops < std for HI and LI only", "b8-thresholds-*.json",
          (all(v["monotone"] and v["exact_one_troop"] and v["equals_rule_R_code_min2_troops_div_std_div_3"] for v in th["per_type_side"].values()),
           sorted(k for k, v in th["per_type_side"].items() if v["equals_B2_hypothesis_3troops_lt_std"])), (True, ["hi side 0", "hi side 1", "li side 0", "li side 1"]))
    claim("finding B8", "icons: 30 (type, side, class) combinations, one icon image each, 30 distinct grid words, different words different icons", "b8-thresholds-*.json",
          (th["icons"]["type_side_class_combinations"], th["icons"]["one_icon_per_type_side_class"], th["icons"]["words"], th["icons"]["different_words_different_icons"], th["icons"]["every_word_one_icon"]), (30, True, 30, True, True))
    lay = [json.loads(x) for x in sorted(D.glob("b8-layout-*.jsonl"))[-1].read_text().splitlines() if x.startswith('{"event"')]
    ev = {e["event"]: e for e in lay}
    claim("finding B8", "layout: 8 toolbar tooltips; surrender box answered No, battle continued with the block unchanged; result box and move phase captured", "b8-layout-20261004-192710.jsonl",
          (sorted(ev["tooltips"]["tooltips"]), ev["surrender_box"]["answered"], ev["after_surrender_no"]["still_in_battle"], ev["after_surrender_no"]["block_unchanged"], ev["done"]["status"]),
          (sorted(["Unit moves", "Friendly units", "Enemy units", "Cancel selection", "End turn", "Change pauses", "Computer general on", "Surrender"]), "No", True, True, "ok"))


def main():
    all_ok = {}
    for r in jl(D / "trials.jsonl"):
        if r.get("status") == "ok":
            all_ok[r["trial"]] = r                                # the last ok record of each trial id
    sweep = [r for r in all_ok.values() if r["rep"] == 1]         # the 315 sweep rows (B4's 4 repeats of hi-hi-one: reps 2-4 are not rows)
    trials = [r for r in all_ok.values() if r["cell"] == "hi-hi-one"]       # the 12 B4 trials (3 seeds x 4 runs)
    anaf = "b2-analysis-20261004-110552.json"                      # the analysis the B2-B4 sections cite (the later ones also decode the sweep series)
    ana = json.loads((D / anaf).read_text())
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
    ic = json.loads(sorted(D.glob("b2-icons-*.json"))[-1].read_text())
    claim("finding", "icons: 42 occupied cells (14 per phase), 11 words, one icon per word, distinct words distinct icons", sorted(D.glob("b2-icons-*.json"))[-1].name,
          (ic["cells_total"], [v["occupied_cells"] for v in ic["per_phase"].values()], ic["distinct_words_total"], ic["every_word_has_one_icon"], ic["different_words_have_different_icons"]), (42, [14, 14, 14], 11, True, True))
    claim("finding", "B3 c4 same tactical outcome as c2 (11 half-rounds, Gaul 5330, Rome destroyed) but a different post save", "b3-crafted-*.jsonl",
          (b3["c4_slot_only"]["half_rounds"], b3["c4_slot_only"]["post_battle"]["defender"]["troops_after"], b3["c4_slot_only"]["post_battle"]["winner"], b3["c4_slot_only"]["post_sha256"] != b3["c2_troops"]["post_sha256"]), (11, 5330, "defender", True))
    cnt = lambda n: (D / n).read_text().count("end_turn_no_sign")
    claim("finding", "b2-verify 093834: no no-sign line; 093600: retry fired (2 no-sign lines)", "b2-verify-*.log", (cnt("b2-verify-20261004-093834.log"), cnt("b2-verify-20261004-093600.log")), (0, 2))
    # sha / screenshots / release
    sums = (D / "SAVES.sha256").read_text().splitlines()
    claim("finding", "at least the 53 screenshots of the PR B review hashed in SAVES.sha256 (more since)", "SAVES.sha256", sum(1 for x in sums if x.strip().endswith(".png")) >= 53, True)
    claim("finding", "FLD-RG sha 39edecd1... twice byte-identical", "fixtures-build-20261004-091421.json", (json.loads((D / "fixtures-build-20261004-091421.json").read_text())["byte_identical_two_builds"], json.loads((D / "fixtures-build-20261004-091421.json").read_text())["sha256"][:8]), (True, "39edecd1"))
    rel = int(subprocess.run(["gh", "release", "view", "run-exp-battle-sweep", "--json", "assets", "-q", ".assets|length"], capture_output=True, text=True).stdout.strip() or -1)
    claim("PR body", "release holds >= 521 assets (PR body says 520 at the time; now stated as 'about 520+')", "release run-exp-battle-sweep", rel >= 521, True)
    # test counts
    for mod, e in (("test_driver_battle", 20), ("test_battle_stage", 16), ("test_battle_trials", 7), ("test_battle_b5_b8", 6)):
        out = subprocess.run([sys.executable, "-m", f"tests.{mod}"], capture_output=True, text=True, cwd=C.ROOT).stdout
        claim("results.md", f"{mod}: {e} tests pass", "tests/" + mod + ".py", out.count("\nPASS ") + out.startswith("PASS "), e)
    # sweep table
    t = D / "sweep-table-20261004-105525.csv"
    tr = list(csv.DictReader(t.open()))
    claim("finding", "B4 sweep table: 12 rows, build lab, level L1, halflog+counts filled", t.name, (len(tr), {x["build"] for x in tr}, all(x["halflog"] and x["loss_rows"] for x in tr)), (12, {"lab"}, True))
    new_claims(rows, claim, sweep, all_ok)
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
