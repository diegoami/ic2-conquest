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
from state import battle_block as BB  # noqa: E402
from collections import defaultdict  # noqa: E402

D = C.DATA


def latest(pat):
    return sorted(D.glob(pat))[-1]


def jl(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def new_claims(rows, claim, sweep, all_ok):
    """Claims of the B5/B8 sections, recomputed from trials.jsonl / halfrounds files / the B8 jsonl, independently of b5_analyze.py's own summary."""
    from collections import Counter, defaultdict
    import audit_inputs as A0
    from state import battle_block as BB
    A_facts = {r["trial"]: A0.trial_facts(r, C.ART) for r in sweep}          # winner, destroyed, promotions, money from the START and POST saves; blocks from the series
    recorded = sweep
    sweep = []
    for r in recorded:                  # the claims below use the values recomputed from the saves; `recorded` is checked against them in one claim
        f = A_facts[r["trial"]]
        r2 = dict(r, winner=f["winner"], half_rounds=len(f["blocks"]), attacker_result={"destroyed": f["att_destroyed"]}, defender_result={"destroyed": f["def_destroyed"]})
        wside = "attacker" if f["winner"] == "attacker" else "defender"
        r2["units"] = {"attacker": [], "defender": []}
        r2["units"][wside] = [{"promoted": True, "type": t, "quality_before": 6, "quality_after": q} for t, q in f["promoted"]]
        r2["taken"] = {"attacker_money": None, "attacker_supplies": None, "defender_money": None, "defender_supplies": None}
        r2["taken"][wside + "_money"], r2["taken"][wside + "_supplies"] = f["money_delta"], f["supplies_delta"]
        sweep.append(r2)
    claim("finding B5", "the winner, destroyed flags, half-round count, promotions and money recorded in trials.jsonl (written at run time by battle.diff) equal what the START and POST-BATTLE saves and the series show, for all 315 rows (the claims below use the values from the saves)", "start/post/BATTLEnn saves vs trials.jsonl",
          sum(1 for r in recorded if (r["winner"], r["half_rounds"], r["attacker_result"]["destroyed"], r["defender_result"]["destroyed"], len([u for s_ in ("attacker", "defender") for u in r["units"][s_] if u["promoted"]]),
                                        r["taken"]["defender_money"] if r["winner"] == "defender" else r["taken"]["attacker_money"]) ==
                (A_facts[r["trial"]]["winner"], len(A_facts[r["trial"]]["blocks"]), A_facts[r["trial"]]["att_destroyed"], A_facts[r["trial"]]["def_destroyed"], len(A_facts[r["trial"]]["promoted"]), A_facts[r["trial"]]["money_delta"])), 315)
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
    # ---- everything below is recomputed from the RAW saves by audit_inputs.py (not from halfrounds-*.jsonl, b5-*.csv/json or b8-thresholds-*.json) ----
    import audit_inputs as A
    F = {r["trial"]: A_facts[r["trial"]] for r in sweep}
    claim("finding B5", "a half-round log file exists for every one of the 315 rows (existence only; the contents are not used by any claim below)", "halfrounds-*.jsonl",
          sum(1 for r in sweep if (D / (r.get("halflog") or "halfrounds-%s.jsonl" % r["trial"])).exists()), 315)
    blocks = {t: f["blocks"] for t, f in F.items()}
    claim("finding B5", "placement: Gaul on row y = 9 and Rome parked on y = 0 in the first save of every battle; Rome on y = 2 in the second", "BATTLEnn saves of the 315 trials",
          ({s["y"] for v in blocks.values() for s in v[0]["slots"] if s["alive"] and s["side"] == 1}, {s["y"] for v in blocks.values() for s in v[0]["slots"] if s["alive"] and s["side"] == 0},
           {s["y"] for v in blocks.values() for s in v[1]["slots"] if s["alive"] and s["side"] == 0}), ({9}, {0}, {2}))
    seq = Counter("".join("A" if A.acting_sides(v[i], v[i + 1]) == [0] else "G" if A.acting_sides(v[i], v[i + 1]) == [1] else "?" for i in range(0, 5)) for v in blocks.values())
    claim("finding B5", "initiative: the diffs into files 2..6 show Rome, Rome, Gaul, Rome, Gaul acting in all 315 battles (acting = a unit moved, shot or took a target)", "BATTLEnn saves of the 315 trials", dict(seq), {"AAGAG": 315})
    one = [(b_["x2"], A.acting_sides(a_, b_)) for v in blocks.values() for a_, b_ in zip(v, v[1:]) if len(A.acting_sides(a_, b_)) == 1]
    claim("finding B5", "header x2 equals the side that acted in the diff into the file in all 3,220 diffs with exactly one acting side", "BATTLEnn saves of the 315 trials",
          (sum(1 for x2, act in one if x2 == act[0]), len(one)), (3220, 3220))
    cnt = Counter()
    for v in blocks.values():
        cnt.update(A.target_events(v))
    claim("finding B5", "target events: a unit's word 9 first shows an enemy slot while >= 2 enemies stood: 664; RANKS IN THE RESULTING SNAPSHOT: among the nearest in 664, uniquely nearest 147, fewest troops (ties included) 507; ranks in the PREVIOUS snapshot (664 events): nearest 602, uniquely nearest 97, fewest troops 546 (recomputed from the saves)", "BATTLEnn saves of the 315 trials",
          (cnt["events"], cnt["res_nearest"], cnt["res_unique"], cnt["res_weakest"], cnt["prev_events"], cnt["prev_nearest"], cnt["prev_unique"], cnt["prev_weakest"]), (664, 664, 147, 507, 664, 602, 97, 546))
    tgf = sorted(D.glob("b5-targets-*.csv"))[-1]
    tg = list(csv.DictReader(tgf.open()))
    claim("finding B5", "the b5-targets csv (the tabulation, an analyser output) agrees with the recomputation from the saves", tgf.name,
          (len(tg), sum(x["is_nearest"] == "True" for x in tg), sum(x["is_unique_nearest"] == "True" for x in tg), sum(x["is_weakest"] == "True" for x in tg), sum(x["prev_is_nearest"] == "True" for x in tg), sum(x["prev_is_unique_nearest"] == "True" for x in tg), sum(x["prev_is_weakest"] == "True" for x in tg)),
          (cnt["events"], cnt["res_nearest"], cnt["res_unique"], cnt["res_weakest"], cnt["prev_nearest"], cnt["prev_unique"], cnt["prev_weakest"]))
    # loss attribution: B0 natural battles and the sweep groups, from the saves; the rule is re-implemented in audit_inputs (shares only the save decoder)
    b0 = [sorted(glob.glob(str(C.ROOT / "artifacts" / "run-exp-battle-probe" / f"{t}_BATTLE[0-9][0-9].SAV"))) for t in ("gate2_a", "gate2_s2a")]
    t0 = [A.series_stats(x) for x in b0]
    claim("finding B5", "B0 natural 14-unit battles: 125 loss rows; 14 fixed by the old diff rule, 29 by words 8 and 9", "gate2_a / gate2_s2a BATTLEnn saves", (sum(x[0] for x in t0), sum(x[1] for x in t0), sum(x[2] for x in t0)), (125, 14, 29))
    grp = defaultdict(lambda: [0, 0, 0])
    kinds = Counter()
    for r in sweep:
        sa, _, sd = r["size"].partition("-")
        sd = sd or sa
        g_ = "3 v 3" if sa == sd == "three" else "mixed" if sa != sd else "1 v 1"
        st = A.series_stats([C.ART / n for n in r["series"]])
        for i in range(3):
            grp[g_][i] += st[i]
        kinds.update(st[3])
    claim("finding B5", "loss rows fixed by words 8/9 (old rule in brackets): 1 v 1 battles 1569 of 1931 (1481); 3 v 3 1166 of 2805 (627); size matrix 624 of 987 (574)", "BATTLEnn saves of the 315 trials",
          {k: (v[2], v[0], v[1]) for k, v in sorted(grp.items())}, {"1 v 1": (1569, 1931, 1481), "3 v 3": (1166, 2805, 627), "mixed": (624, 987, 574)})
    claim("finding B5", "sweep loss kinds: melee 4263, shooting 371, mixed 1089, unknown 0", "BATTLEnn saves of the 315 trials", {k: kinds[k] for k in ("melee", "shooting", "mixed", "unknown")}, {"melee": 4263, "shooting": 371, "mixed": 1089, "unknown": 0})
    es = Counter(A.end_state(f["blocks"], f["winner"]) for f in F.values())
    claim("finding B5", "end state in the last saved file: loser empty 58, units left with none rout-eligible 238, some rout-eligible 19", "BATTLEnn saves of the 315 trials", dict(es),
          {"empty": 58, "no unit rout-eligible": 238, "some rout-eligible": 19})
    pl_all = defaultdict(set)
    pl = defaultdict(set)
    ncell = defaultdict(int)
    for r in sweep:
        key = (r["defender"], r["size"].partition("-")[2] or r["size"], 3 if r["size"].partition("-")[0] == "three" else 1, r["seed"])
        pl[key].add(tuple(sorted((s["x"], s["y"]) for s in blocks[r["trial"]][0]["slots"] if s["alive"] and s["side"] == 1)))
        ncell[key] += 1
        pl_all[key[:2] + key[3:]].add(tuple(sorted((s["x"], s["y"]) for s in blocks[r["trial"]][0]["slots"] if s["alive"] and s["side"] == 1)))
    claim("finding B5", "same seed, same defender army (type, size) and same NUMBER of Rome units (1 or 3): the same Gaul placement in every cell, whatever Rome's type; with 1 v 3 units the placement differs in 30 of 45 (defender, size, seed) groups (groups of (defender type, size, Rome units, seed), by number of cells)", "BATTLEnn saves of the 315 trials",
          (len(pl), sorted(Counter((ncell[k], len(v)) for k, v in pl.items()).items())), (81, [((1, 1), 18), ((2, 1), 15), ((4, 1), 3), ((5, 1), 21), ((6, 1), 18), ((7, 1), 6)]))
    claim("finding B5", "merging 1 and 3 Rome units, (defender, size, seed) groups with more than one Gaul placement: 30 of 45", "BATTLEnn saves of the 315 trials", (len(pl_all), sum(1 for v in pl_all.values() if len(v) > 1)), (45, 30))
    # B8: thresholds and icons from the BATTLE01 saves and screenshots of the v2 ladder rounds
    rounds = [json.loads(x) for f_ in sorted(D.glob("b8-ladder-v2-*.jsonl")) for x in f_.read_text().splitlines() if '"slots"' in x]
    obs = A.b8_observations([C.ART / "crafted_b8" / r_["saves"][0] for r_ in rounds if r_.get("status") == "ok"])
    exp = {"li": [5000, 10000], "hi": [2000, 4000], "ar": [1166, 2332], "lc": [2333, 4666], "hc": [833, 1666]}
    got, mono, exact, rule, b2h = {}, True, True, True, []
    for (typ, side), o in sorted(obs.items()):
        pts = sorted(o.items())
        ch = [(a_, b_) for (a_, c1), (b_, c2) in zip(pts, pts[1:]) if c1 != c2]
        got[typ + str(side)] = [b_ for a_, b_ in ch]
        mono &= all(c1 <= c2 for (a_, c1), (b_, c2) in zip(pts, pts[1:]))
        exact &= all(b_ - a_ == 1 for a_, b_ in ch)
        rule &= all(c == min(2, t // (A.STD[typ] // 3)) for t, c in pts)
        if all(c == (0 if t * 3 < A.STD[typ] else 1 if t * 3 < 2 * A.STD[typ] else 2) for t, c in pts):
            b2h.append("%s side %d" % (typ, side))
    claim("finding B8", "first troop count of icon size 1 and 2, exact to 1 troop, both sides: LI 5000/10000, HI 2000/4000, Ar 1166/2332, LC 2333/4666, HC 833/1666 (from the BATTLE01 saves of the v2 rounds)", "b8v2_*_BATTLE01.SAV",
          got, {k + s: v for k, v in exp.items() for s in "01"})
    claim("finding B8", "10 (type, side) series monotone, every class change 1 troop wide, equal to min(2, troops div (std div 3)); equal to B2's 3*troops < std for HI and LI only", "b8v2_*_BATTLE01.SAV",
          (mono, exact, rule, sorted(b2h)), (True, True, True, ["hi side 0", "hi side 1", "li side 0", "li side 1"]))
    tiles, wt = defaultdict(set), defaultdict(set)
    for r_ in rounds:
        if r_.get("status") != "ok":
            continue
        b_ = BB.from_save(C.ART / "crafted_b8" / r_["saves"][0])
        occ = Counter((s["x"], s["y"]) for s in b_["slots"] if s["alive"])
        for s in b_["slots"]:
            if s["alive"] and occ[(s["x"], s["y"])] == 1:
                h = A.tile_hash(C.ART / "shots" / r_["screenshot"], s["x"], s["y"])
                word = b_["grid"][s["x"] * 12 + s["y"]]
                tiles[(s["type"], s["side"], word - 20 * s["side"] - 3 * A.TYPES.index(s["type"]))].add(h)
                wt[word].add(h)
    claim("finding B8", "icons (from the placement screenshots and BATTLE01 saves): 30 (type, side, size) combinations, one image each, 30 distinct grid words, different words different images", "b8v2_*_placement.png",
          (len(tiles), all(len(v) == 1 for v in tiles.values()), len(wt), len({next(iter(v)) for v in wt.values()}) == len(wt), all(len(v) == 1 for v in wt.values())), (30, True, 30, True, True))
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
    import audit_inputs as AI
    tf = {r["trial"]: AI.trial_facts(r, C.ART) for r in trials}
    trials = [dict(r, winner=tf[r["trial"]]["winner"], half_rounds=len(tf[r["trial"]]["blocks"]), post_sha256=C.sha(C.ART / r["post_save"]),
                   attacker_result={"destroyed": tf[r["trial"]]["att_destroyed"]}, defender_result={"troops_after": tf[r["trial"]]["def_troops"]}) for r in trials]       # outcome fields from the saves
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
    rd = lambda n: (C.ART / n).read_bytes()
    byid = {r["trial"]: r for r in trials}
    for s in (1, 2, 3):
        res = []
        for k in (2, 3, 4):
            x, y = byid[f"hi-hi-one_s{s}_r1"], byid[f"hi-hi-one_s{s}_r{k}"]
            res.append((f"r{k}", len(x["series"]) == len(y["series"]) > 0 and all(rd(m) == rd(n) for m, n in zip(x["series"], y["series"])), rd(x["post_save"]) == rd(y["post_save"]), True))
        claim("finding", f"seed {s}: r1 byte-identical to r2, r3, r4 (series and post)", "the BATTLEnn series and post saves of hi-hi-one_s%d_r1..r4 (byte comparison here)" % s, res, [(f"r{k}", True, True, True) for k in (2, 3, 4)])
    claim("finding", "Offer of peace in 2 of 3 seeds", "trials.jsonl", len({r["seed"] for r in trials if r.get("dialog") == "Offer of peace"}), 2)
    # verify
    claim("finding", "memory = Save As block in 3 of 3 phases", "b2-verify-20261004-093834.json", [p["memory_equals_save_block"] for p in ver["phases"]], [True] * 3)
    claim("finding", "slot positions <-> screen 168 of 168 in 3 phases", "b2-verify-20261004-093834.json", [p["screen_cells_agreeing"] for p in ver["phases"]], [168] * 3)
    claim("finding", "half-round counter 2 at placement, 3, 5 after End turn clicks", "b2-verify-20261004-093834.json", [p["half_round"] for p in ver["phases"]], [2, 3, 5])
    claim("finding", "header +2 = 10 (defender army), +0 = 0", "b2-verify-20261004-093834.json", {(p["attacker_army"], p["defender_army"]) for p in ver["phases"]}, {(0, 10)})
    claim("finding", "AI side re-sorted: slot order differs from the army's", "b2-verify-20261004-093834.json", (ver["side1"]["same_order"], ver["side1"]["same_set"]), (False, True))
    claim("finding", "slot label = strategic label for every unit", "b2-verify-20261004-093834.json", ver["merc_label_equals_strategic_label_for_every_unit"], True)
    # analysis
    b0s, t12 = AI.b2_sets(C.ART, C.ROOT / "artifacts" / "run-exp-battle-probe", trials)
    allf = [f for x in b0s + t12 for f in x]
    blk = {f: BB.from_save(f) for f in allf}
    st0 = [AI.series_stats(x) for x in b0s]
    st1 = [AI.series_stats(x) for x in t12]
    gr = [AI.grid_report(b) for b in blk.values()]
    claim("finding", "241 decoded files (33 B0 + 208 trials)", "BATTLEnn saves of B0 gate2_a, gate2_s2a and the 12 hi-hi-one trials", (len(allf), sum(len(x) for x in b0s), sum(len(x) for x in t12)), (241, 33, 208))
    claim("finding", "0 inconsistent grid files / 0 sprite violations in the 241", "the same 241 saves", (sum(g_[0] for g_ in gr), sum(g_[1] for g_ in gr)), (0, 0))
    claim("finding", "B0 natural battles: 125 loss rows, 14 unambiguous", "gate2_a, gate2_s2a saves", (sum(x[0] for x in st0), sum(x[1] for x in st0)), (125, 14))
    claim("finding", "B4 1-v-1: 272 of 272 unambiguous", "hi-hi-one trial saves", (sum(x[0] for x in st1), sum(x[1] for x in st1)), (272, 272))
    claim("finding", "aggregate 286 of 397", "the same saves", (sum(x[1] for x in st0 + st1), sum(x[0] for x in st0 + st1)), (286, 397))
    r1 = AI.series_stats([C.ART / n for n in byid["hi-hi-one_s1_r1"]["series"]])
    claim("finding", "seed 1: 26 of 26 loss rows unambiguous", "hi-hi-one_s1_r1 BATTLEnn saves", (r1[0], r1[1]), (26, 26))
    x2bad = sum(1 for b in blk.values() if not (b["x2"] == (1 if b["half_round"] % 2 == 0 else 0) if b["half_round"] >= 4 else b["x2"] == (1 if b["half_round"] == 1 else 0)))
    claim("finding", "x2 rule holds on 241 files", "the same saves", (len(blk), x2bad), (241, 0))
    probe = C.ROOT / "artifacts" / "run-exp-battle-probe"
    crafted = [f for f in (C.ART / "crafted").rglob("*BATTLE[0-9][0-9]*.SAV") if not f.name.startswith("CRAFT_")]
    sweepnames = {n for r in all_ok.values() if r["cell"] != "hi-hi-one" for n in r["series"]}
    other = [f for f in C.ART.rglob("*BATTLE[0-9][0-9]*.SAV") if "crafted" not in f.parts and "crafted_b8" not in f.parts and f.name not in sweepnames]
    b0all = list(probe.rglob("*BATTLE[0-9][0-9]*.SAV"))
    rep = lambda fs: [AI.grid_report(BB.from_save(f)) for f in fs]
    r_b0, r_b3, r_ot = rep(b0all), rep(crafted), rep(other)
    claim("finding", "763 saves = 345 B0 + 192 B3 + 226 trials/other (the 226 = 208 hi-hi-one + 17 strays + 1 copy; the sweep series, added later, are not in this set)", "artifacts BATTLEnn saves (counted here)", (len(b0all) + len(crafted) + len(other), len(b0all), len(crafted), len(other)), (763, 345, 192, 226))
    claim("finding", "571 saves with 0 violations (B0 + trials); 14 B3 files violate", "the same saves", (sum(g_[1] for g_ in r_b0 + r_ot), sum(g_[0] for g_ in r_b3), sum(g_[1] for g_ in r_b3)), (0, 14, 14))
    rng = defaultdict(lambda: defaultdict(list))
    for b in blk.values():
        for s_ in b["slots"]:
            if s_["alive"]:
                rng[s_["type"]][b["grid"][s_["x"] * 12 + s_["y"]] - 20 * s_["side"] - 3 * AI.TYPES.index(s_["type"])].append(s_["troops"])
    r = {t: {c: [min(v), max(v)] for c, v in d.items()} for t, d in rng.items()}
    claim("finding", "HI ranges 250-1866 / 2024-3964 / 4083-6000", "the 241 saves", [r["hi"][c] for c in (0, 1, 2)], [[250, 1866], [2024, 3964], [4083, 6000]])
    claim("finding", "Ar ranges 181-789 / 1215-2046 / 2881-3411", "the 241 saves", [r["ar"][c] for c in (0, 1, 2)], [[181, 789], [1215, 2046], [2881, 3411]])
    claim("finding", "LI ranges 853-4728 / 5147-9669 / 10318-14500", "the 241 saves", [r["li"][c] for c in (0, 1, 2)], [[853, 4728], [5147, 9669], [10318, 14500]])
    claim("finding", "LC 1912 / 2426-4421 (no class 2); HC 227-801 / 1269-1574 / 1935-2337", "the 241 saves", ([r["lc"][c] for c in (0, 1)], 2 in r["lc"], [r["hc"][c] for c in (0, 1, 2)]), ([[1912, 1912], [2426, 4421]], False, [[227, 801], [1269, 1574], [1935, 2337]]))
    am = defaultdict(set)
    for x in b0s + t12:
        for s_ in blk[x[0]]["slots"]:
            if s_["alive"]:
                am[s_["type"]].add(str(s_["ammo"]))
    claim("finding", "ammo at first file: HI 0, HC 0, LI 7, LC 9, Ar 25", "the first save of each of the 14 series", {t: sorted(v) for t, v in am.items()}, {"hi": ["0"], "hc": ["0"], "li": ["7"], "lc": ["9"], "ar": ["25"]})
    # morale / placement / b3
    sb = [BB.from_save(C.ART / n) for n in byid["hi-hi-one_s1_r3"]["series"]]
    claim("finding", "morale Rome 65 -> 31, Gaul 88 -> 99 (s1_r3)", "hi-hi-one_s1_r3 BATTLEnn saves (first and last)", ([s_["morale"] for s_ in sb[0]["slots"] if s_["alive"]], [s_["morale"] for s_ in sb[-1]["slots"] if s_["alive"]]), ([65, 88], [31, 99]))
    pos = {s_: [x for x in BB.from_save(C.ART / byid[f"hi-hi-one_s{s_}_r1"]["series"][0])["slots"] if x["alive"] and x["side"] == 1][0] for s_ in (1, 2, 3)}
    claim("finding", "Gaul HI first placed on row 9 at x 4 / 10 / 7", "hi-hi-one_s{1,2,3}_r1 first BATTLEnn saves", [(pos[s_]["x"], pos[s_]["y"]) for s_ in (1, 2, 3)], [(4, 9), (10, 9), (7, 9)])
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
    wt2, per_phase, cells2 = defaultdict(set), [], 0
    for png, svn in (("b2_placement_window.png", "B2_placement.SAV"), ("b2_after_end_turn_1_window.png", "B2_after_end_turn_1.SAV"), ("b2_after_end_turn_2_window.png", "B2_after_end_turn_2.SAV")):
        b_, n_ = BB.from_save(C.ART / svn), 0
        for y in range(12):
            for x in range(14):
                w_ = b_["grid"][x * 12 + y]
                if w_ != 50:
                    wt2[w_].add(AI.tile_hash(C.ART / png, x, y))
                    n_ += 1
        per_phase.append(n_)
        cells2 += n_
    claim("finding", "icons: 42 occupied cells (14 per phase), 11 words, one icon per word, distinct words distinct icons (hashes of the inner 26 x 26 of the screenshots, words from the saves)", "b2_*_window.png and B2_*.SAV",
          (cells2, per_phase, len(wt2), all(len(v) == 1 for v in wt2.values()), len({next(iter(v)) for v in wt2.values()}) == len(wt2)), (42, [14, 14, 14], 11, True, True))
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
    for mod, e in (("test_driver_battle", 22), ("test_battle_stage", 16), ("test_battle_trials", 7), ("test_battle_b5_b8", 7)):
        out = subprocess.run([sys.executable, "-m", f"tests.{mod}"], capture_output=True, text=True, cwd=C.ROOT).stdout
        claim("results.md", f"{mod}: {e} tests pass", "tests/" + mod + ".py", out.count("\nPASS ") + out.startswith("PASS "), e)
    # sweep table
    t = D / "sweep-table-20261004-105525.csv"
    tr = list(csv.DictReader(t.open()))
    claim("finding", "B4 sweep table: 12 rows, build lab, level L1, halflog+counts filled", t.name, (len(tr), {x["build"] for x in tr}, all(x["halflog"] and x["loss_rows"] for x in tr)), (12, {"lab"}, True))
    new_claims(rows, claim, sweep, all_ok)
    bad = [r_ for r_ in rows if r_[5] != "y"]
    out = C.write_new(D, f"claims-audit-{C.STAMP}.md", "# Claims audit (PR #36, #40)\n\n%d claims, %d mismatches.\n\n**Inputs.** Claims on the 315 sweep rows, the 241 B2 files, the 763 saves, the target ranks, the loss attribution, the end states, the B8 thresholds and icons, the B2 icons and the byte comparisons are recomputed here from the RAW saves and screenshots by `audit_inputs.py`, which re-implements each rule and imports none of `b5_analyze`, `b2_analyze`, `b8_analyze`, `halflog`, `BB.diff`, `BB.attribute`, `BB.check_grid`, `stage.sprite_value` or any `b5-*`/`b8-thresholds-*`/`b2-analysis-*` output (the b5-targets csv is compared with the recomputation in one claim). **Shared with the analysers:** the save decoder `state.battle_block.from_save` / `state.sav.load` (bytes to fields; checked by B2 against game memory and by the round-trip tests) and the file lists. **Recorded at run time, not recomputed:** seconds and timings, End turn click counts, the dialog titles and answers (`trials.jsonl`), the b2-verify and b3-crafted records (measurements made live), the test counts (the suites are run).\n\n"
                      "| doc | claim | file | value in file | claimed | match |\n|---|---|---|---|---|---|\n" % (len(rows), len(bad))
                      + "\n".join("| %s | %s | `%s` | %s | %s | %s |" % (w, t_, f_, str(v).replace("|", "/"), str(e).replace("|", "/"), m) for w, t_, f_, v, e, m in rows) + "\n")
    print(out, len(rows), "claims,", len(bad), "mismatches")
    for r_ in bad:
        print("MISMATCH", r_)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
