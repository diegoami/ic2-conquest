#!/usr/bin/env python3
"""B5 offline tabulation of the sweep (battles plan §4 B5). Reads the tracked `trials.jsonl` and the per-half-round logs `halfrounds-*.jsonl`
(no game, no saves) and writes NEW files (common.write_new, never overwritten) under the tracked data folder:

  b5-pairings-<stamp>.csv     one line per (attacker, defender, attacker size, defender size, seed): winner, half-rounds, losses, promotions, peace offer
  b5-placement-<stamp>.csv    per trial and slot: type, side, position in the first file (half-round 1: Gaul placed, Rome parked) and the second
                              (Rome placed), and which side acted in half-rounds 2-5 (initiative, [D] from the diff)
  b5-targets-<stamp>.csv      every half-round in which a unit's `target` field named a new enemy slot while two or more enemies stood: the
                              rank of the chosen enemy by distance, by troops and by type (observations of the AI general, NOT rules)
  b5-promotions-<stamp>.csv   per unit: quality before / after, troops before / after, destroyed
  b5-summary-<stamp>.json     the aggregates every finding sentence cites (counts per type, per end condition, per size, peace offers, timings,
                              seed-pairing check, loser's state at the last saved half-round)
    python3 runs/experiments/battles/b5_analyze.py [--trials-prefix ...]
Trials used: the last `ok` record of each trial id with rep 1 (`hi-hi-one` reps 2-4 are the B4 repeats, counted in `replays` only). All numbers
are [O] observed from block fields and result records, actions are [D]; lab, L1; 3 seeds per cell describe how a battle unfolds, not odds.
"""
import csv
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import trials as T  # noqa: E402

CHEB = lambda p, q: max(abs(p[0] - q[0]), abs(p[1] - q[1]))


def halflog_rows(rec):
    name = rec.get("halflog")
    if not name:
        bf = T.backfill_halflog(rec)
        name = bf[0] if bf else None
    if not name:
        return []
    return [json.loads(x) for x in (C.DATA / name).read_text().splitlines() if x.strip()]


def attribution(rec):
    """Old (BB.diff, adjacency/ammo candidates) v new (BB.attribute, words 8 and 9 [R-code]) share of fixed loss rows over a trial's series files."""
    from state import battle_block as BB
    files = [C.ART / n for n in rec["series"]]
    out = {"losses": 0, "old_unambiguous": 0, "new_fixed": 0, "kinds": Counter()}
    prev = None
    for f in files:
        b = BB.from_save(f)
        if prev is not None:
            d, n = BB.diff(prev, b), BB.attribute(prev, b)
            out["losses"] += d["losses"]
            out["old_unambiguous"] += d["unambiguous"]
            out["new_fixed"] += n["fixed"]
            assert n["losses"] == d["losses"], "loss row counts differ"
            out["kinds"].update(n["by_kind"])
        prev = b
    return out


def b0_attribution():
    import glob
    from state import battle_block as BB
    probe = C.ROOT / "artifacts" / "run-exp-battle-probe"
    out = {"losses": 0, "old_unambiguous": 0, "new_fixed": 0, "kinds": Counter()}
    for tag in ("gate2_a", "gate2_s2a"):
        prev = None
        for f in sorted(glob.glob(str(probe / f"{tag}_BATTLE[0-9][0-9].SAV"))):
            b = BB.from_save(f)
            if prev is not None:
                d, n = BB.diff(prev, b), BB.attribute(prev, b)
                out["losses"] += d["losses"]
                out["old_unambiguous"] += d["unambiguous"]
                out["new_fixed"] += n["fixed"]
                out["kinds"].update(n["by_kind"])
            prev = b
    return out


def csv_text(cols, rows):
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, cols)
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return buf.getvalue()


def last_ok():
    last = {}
    for r in T.read_trials():
        if r.get("status") == "ok":
            last[r["trial"]] = r
    return last


def sizes_of(cell):
    a, d, size = T.parse_cell(cell)
    sa, _, sd = size.partition("-")
    return sa, sd or sa


def targets_events(rows):
    """Every (half-round, slot) whose target changed to an enemy slot while >= 2 enemies were alive: [D] ranks of the chosen one."""
    ev = []
    for prev, cur in zip(rows, rows[1:]):
        by = {s["slot"]: s for s in cur["slots"]}
        pb = {s["slot"]: s for s in prev["slots"]}
        for s in cur["slots"]:
            p = pb.get(s["slot"])
            if not p or s["target"] == p["target"] or s["target"] < 0 or s["target"] not in by:
                continue
            enemies = [e for e in cur["slots"] if e["side"] != s["side"]]
            if len(enemies) < 2:
                continue
            ch = by[s["target"]]
            dist = lambda e: CHEB((s["x"], s["y"]), (e["x"], e["y"]))
            d_ch = dist(ch)
            nearer = sum(1 for e in enemies if dist(e) < d_ch)
            tied = sum(1 for e in enemies if e is not ch and dist(e) == d_ch)
            weaker = sum(1 for e in enemies if e["troops"] < ch["troops"])
            ev.append({"half_round": cur["half_round"], "side": s["side"], "slot": s["slot"], "type": s["type"], "target": ch["slot"], "target_type": ch["type"],
                       "enemies_alive": len(enemies), "distance": d_ch, "enemies_strictly_nearer": nearer, "enemies_tied_distance": tied,
                       "enemies_strictly_weaker": weaker, "is_nearest": nearer == 0, "is_unique_nearest": nearer == 0 and tied == 0,
                       "is_weakest": weaker == 0, "enemy_types": "".join(sorted(e["type"] for e in enemies)),
                       "ranged_shooter": s["type"] in ("li", "ar", "lc")})
    return ev


def main():
    last = last_ok()
    recs = [r for r in last.values() if r["rep"] == 1]
    replays = [r["trial"] for r in last.values() if r["rep"] != 1]
    attr_total = {"1 unit per side": Counter(), "3 units per side": Counter(), "mixed sizes (size matrix)": Counter()}
    kinds_total = Counter()
    x2_v_actor = Counter()
    pair_rows, place_rows, target_rows, promo_rows = [], [], [], []
    peace = Counter()
    summary = {"trials": len(recs), "replays_not_counted": len(replays)}
    end_stats = defaultdict(list)
    first_gaul_x = defaultdict(dict)       # (defender type, defender size) -> {seed: {attacker type: tuple of Gaul x at half-round 1}}
    init_seq = Counter()
    for r in sorted(recs, key=lambda r: (r["attacker"], r["defender"], r["size"], r["seed"])):
        sa, sd = sizes_of(r["cell"])
        a, d = r["attacker_result"], r["defender_result"]
        rows = halflog_rows(r)
        at = attribution(r)
        grp = "3 units per side" if (sa == "three" and sd == "three") else "mixed sizes (size matrix)" if sa != sd else "1 unit per side"
        for k in ("losses", "old_unambiguous", "new_fixed"):
            attr_total[grp][k] += at[k]
        kinds_total.update(at["kinds"])
        offer = "Offer of peace" in r.get("dialog", "")
        peace[(sa, sd, "offer" if offer else "none")] += 1
        promos = [(side, u) for side in ("attacker", "defender") for u in r["units"][side] if u["promoted"]]
        pair_rows.append({"cell": r["cell"], "attacker": r["attacker"], "defender": r["defender"], "att_size": sa, "def_size": sd, "seed": r["seed"], "trial": r["trial"],
                          "half_rounds": r["half_rounds"], "loss_rows": at["losses"], "old_unambiguous": at["old_unambiguous"], "attributed_fixed": at["new_fixed"], "winner": r["winner"], "att_before": a["troops_before"], "att_after": a["troops_after"],
                          "def_before": d["troops_before"], "def_after": d["troops_after"], "att_destroyed": a["destroyed"], "def_destroyed": d["destroyed"],
                          "promotions": len(promos), "offer_of_peace": offer, "end_turn_clicks": r["end_turn_clicks"], "seconds": r["seconds"],
                          "def_money_taken": r.get("taken", {}).get("defender_money"), "def_supplies_taken": r.get("taken", {}).get("defender_supplies"),
                          "att_money_taken": r.get("taken", {}).get("attacker_money"), "att_supplies_taken": r.get("taken", {}).get("attacker_supplies"),
                          "news": "; ".join(r.get("news", []))})
        for side in ("attacker", "defender"):
            for u in r["units"][side]:
                promo_rows.append({"trial": r["trial"], "cell": r["cell"], "side": side, **{k: u.get(k) for k in ("name", "type", "troops_before", "troops_after", "loss", "destroyed", "quality_before", "quality_after", "promoted")}})
        if not rows:
            continue
        # placement: the first two files; initiative: who acted in diffs 2..5 (file index 1..4)
        for k, row in enumerate(rows[:2]):
            for s in row["slots"]:
                place_rows.append({"trial": r["trial"], "cell": r["cell"], "seed": r["seed"], "file_index": k, "half_round": row["half_round"], "slot": s["slot"], "side": s["side"],
                                   "type": s["type"], "x": s["x"], "y": s["y"], "troops": s["troops"], "morale": s["morale"], "state": s["state"]})
        for row in rows[1:]:
            act = row.get("since_previous", {}).get("acting_sides_D", [])
            if len(act) == 1:
                x2_v_actor["agree" if row["x2"] == act[0] else "disagree"] += 1
        seq = "".join(("A" if x == [0] else "G" if x == [1] else "B" if x else "-") for x in [row.get("since_previous", {}).get("acting_sides_D", []) for row in rows[1:6]])
        init_seq[(r["attacker"], seq)] += 1
        gx = tuple(sorted((s["x"], s["y"]) for s in rows[0]["slots"] if s["side"] == 1))
        first_gaul_x[(r["defender"], sd, r["cell"].split("-")[2])].setdefault(r["seed"], {})[r["attacker"] + "-" + sa] = gx
        for e in targets_events(rows):
            target_rows.append({"trial": r["trial"], "cell": r["cell"], "seed": r["seed"], **e})
        # the loser at the last saved half-round (the last file is the state BEFORE the final half-round: the end itself is not in the series)
        loser = {"attacker": 0, "defender": 1}.get(r["winner"] and ("defender" if r["winner"] == "attacker" else "attacker"))
        if loser is not None:
            ls = [s for s in rows[-1]["slots"] if s["side"] == loser]
            end_stats[r["winner"]].append({"trial": r["trial"], "loser_units_alive_last_file": len(ls), "loser_troops_last_file": sum(s["troops"] for s in ls),
                                           "loser_start_troops": (a if loser == 0 else d)["troops_before"],
                                           "loser_morale_min_last_file": min((s["morale"] for s in ls), default=None), "half_rounds": r["half_rounds"]})
    # aggregates
    wins = defaultdict(Counter)
    for p in pair_rows:
        wins[(p["attacker"], p["defender"], p["att_size"], p["def_size"])][p["winner"]] += 1
    summary["winner_per_cell_3_seeds"] = {"%s>%s %s/%s" % k: dict(v) for k, v in sorted(wins.items())}
    summary["attacker_wins_by_size_pair"] = {"%s/%s" % (sa, sd): sum(1 for p in pair_rows if (p["att_size"], p["def_size"]) == (sa, sd) and p["winner"] == "attacker")
                                              for sa, sd in sorted({(p["att_size"], p["def_size"]) for p in pair_rows})}
    summary["trials_per_size_pair"] = dict(Counter("%s/%s" % (p["att_size"], p["def_size"]) for p in pair_rows))
    summary["winner_counts"] = dict(Counter(p["winner"] for p in pair_rows))
    summary["half_rounds"] = {"min": min((p["half_rounds"] for p in pair_rows), default=None), "max": max((p["half_rounds"] for p in pair_rows), default=None),
                              "mean": round(sum(p["half_rounds"] for p in pair_rows) / max(1, len(pair_rows)), 2),
                              "over_99_flag": [p["trial"] for p in pair_rows if p["half_rounds"] >= 99]}
    summary["offer_of_peace"] = {"rows_with_offer": sum(1 for p in pair_rows if p["offer_of_peace"]), "rows": len(pair_rows),
                                 "by_size_pair": {"%s/%s %s" % k: v for k, v in sorted(peace.items())},
                                 "by_winner": {w: sum(1 for p in pair_rows if p["offer_of_peace"] and p["winner"] == w) for w in ("attacker", "defender", "none", "both")}}
    summary["end_condition_counts"] = dict(Counter(("both destroyed" if p["att_destroyed"] and p["def_destroyed"] else "attacker destroyed" if p["att_destroyed"]
                                                    else "defender destroyed" if p["def_destroyed"] else "nobody destroyed") for p in pair_rows))
    summary["end_clicks"] = dict(Counter(p["end_turn_clicks"] for p in pair_rows))
    summary["loser_state_at_last_saved_half_round"] = {w: v for w, v in end_stats.items()}
    summary["promotions_total"] = sum(p["promotions"] for p in pair_rows)
    summary["promotions_by_type"] = dict(Counter(u["type"] for u in promo_rows if u["promoted"]))
    summary["promotions_by_winner_side"] = dict(Counter((u["side"]) for u in promo_rows if u["promoted"]))
    summary["money_supplies_taken"] = {"rows_with_defender_money": sum(1 for p in pair_rows if p["def_money_taken"]), "rows_with_defender_supplies": sum(1 for p in pair_rows if p["def_supplies_taken"]),
                                       "rows_with_attacker_money": sum(1 for p in pair_rows if p["att_money_taken"]), "rows_with_attacker_supplies": sum(1 for p in pair_rows if p["att_supplies_taken"])}
    summary["seconds_per_battle"] = {"mean": round(sum(p["seconds"] for p in pair_rows) / max(1, len(pair_rows)), 1), "min": min((p["seconds"] for p in pair_rows), default=None), "max": max((p["seconds"] for p in pair_rows), default=None)}
    # placement
    gy = Counter((s["type"], s["y"]) for s in place_rows if s["side"] == 1 and s["file_index"] == 0)
    summary["placement_defender_first_file_row_by_type"] = {"%s y=%d" % k: v for k, v in sorted(gy.items())}
    ay0 = Counter((s["type"], s["y"]) for s in place_rows if s["side"] == 0 and s["file_index"] == 0)
    ay1 = Counter((s["type"], s["y"]) for s in place_rows if s["side"] == 0 and s["file_index"] == 1)
    summary["placement_attacker_first_file_row_by_type"] = {"%s y=%d" % k: v for k, v in sorted(ay0.items())}
    summary["placement_attacker_second_file_row_by_type"] = {"%s y=%d" % k: v for k, v in sorted(ay1.items())}
    xs = defaultdict(Counter)
    for s in place_rows:
        if s["side"] == 0 and s["file_index"] == 1:
            xs[s["type"]][s["x"]] += 1
    summary["placement_attacker_second_file_x_by_type"] = {t: dict(sorted(c.items())) for t, c in sorted(xs.items())}
    summary["initiative_sequence_files_2_to_6_A_attacker_G_defender_B_both_dash_none"] = {"%s %s" % k: v for k, v in sorted(init_seq.items())}
    # seed pairing: does the same seed give the same Gaul placement across cells with the same defender army? [O]
    pairing = {}
    for key, per_seed in first_gaul_x.items():
        for seed, per_att in per_seed.items():
            pairing["%s %s seed %s" % (key[0], key[1], seed)] = {"cells": len(per_att), "distinct_gaul_placements": len({v for v in per_att.values()})}
    summary["seed_pairing_gaul_placement_by_defender_army_and_seed"] = pairing
    # targets
    summary["targets"] = {"events": len(target_rows), "nearest": sum(1 for t in target_rows if t["is_nearest"]), "unique_nearest": sum(1 for t in target_rows if t["is_unique_nearest"]),
                          "weakest": sum(1 for t in target_rows if t["is_weakest"]),
                          "by_attacker_type": {k: dict(Counter("nearest" if t["is_nearest"] else "not nearest" for t in target_rows if t["type"] == k)) for k in sorted({t["type"] for t in target_rows})}}
    pcols = ["cell", "attacker", "defender", "att_size", "def_size", "seed", "trial", "half_rounds", "loss_rows", "old_unambiguous", "attributed_fixed", "winner", "att_before", "att_after", "def_before", "def_after", "att_destroyed", "def_destroyed",
             "promotions", "offer_of_peace", "end_turn_clicks", "seconds", "def_money_taken", "def_supplies_taken", "att_money_taken", "att_supplies_taken", "news"]
    out = {}
    out["pairings"] = C.write_new(C.DATA, f"b5-pairings-{C.STAMP}.csv", csv_text(pcols, pair_rows))
    out["placement"] = C.write_new(C.DATA, f"b5-placement-{C.STAMP}.csv", csv_text(["trial", "cell", "seed", "file_index", "half_round", "slot", "side", "type", "x", "y", "troops", "morale", "state"], place_rows))
    out["targets"] = C.write_new(C.DATA, f"b5-targets-{C.STAMP}.csv", csv_text(["trial", "cell", "seed", "half_round", "side", "slot", "type", "target", "target_type", "enemies_alive", "distance", "enemies_strictly_nearer", "enemies_tied_distance", "enemies_strictly_weaker", "is_nearest", "is_unique_nearest", "is_weakest", "enemy_types", "ranged_shooter"], target_rows))
    out["promotions"] = C.write_new(C.DATA, f"b5-promotions-{C.STAMP}.csv", csv_text(["trial", "cell", "side", "name", "type", "troops_before", "troops_after", "loss", "destroyed", "quality_before", "quality_after", "promoted"], promo_rows))
    summary["header_x2_v_acting_side"] = {"note": "x2 = the side to move at the snapshot [R-code 0x4A0B78]; compared with the side whose units moved/shot/acquired a target in the diff into that file (only diffs with exactly one acting side)", **dict(x2_v_actor)}
    b0a = b0_attribution()
    summary["attribution_R_code_words_8_9"] = {"B0 natural 14-unit battles (gate2_a, gate2_s2a)": {**{k: b0a[k] for k in ("losses", "old_unambiguous", "new_fixed")}, "kinds": dict(b0a["kinds"])},
                                               "sweep by group": {g: dict(c) for g, c in attr_total.items()}, "sweep kinds": dict(kinds_total)}
    summary["inputs"] = {"trials_jsonl_lines": len(T.read_trials()), "files": {k: v.name for k, v in out.items()}}
    out["summary"] = C.write_new(C.DATA, f"b5-summary-{C.STAMP}.json", json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: v.name for k, v in out.items()}))
    print(json.dumps({k: summary[k] for k in ("trials", "winner_counts", "half_rounds", "offer_of_peace", "end_condition_counts", "targets", "initiative_sequence_files_2_to_6_A_attacker_G_defender_B_both_dash_none")}, indent=1, default=str))


if __name__ == "__main__":
    main()
