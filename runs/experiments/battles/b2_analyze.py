#!/usr/bin/env python3
"""B2 offline analysis of the decoded battle blocks (battles plan §4 B2): over every lab `BATTLEnn.SAV` series kept so far (B0's gate series and the
B4 trials), what each field takes, how the grid sprite follows troops, how many loss rows of a half-round diff are unambiguous, who acts when.

    python3 runs/experiments/battles/b2_analyze.py      # writes b2-analysis-<stamp>.json (tracked)

Series used: B0's `gate2_a`, `gate2_s2a` (natural FLD-RG, 14 units, seeds 1 and 2) from artifacts/run-exp-battle-probe/, and every trial of
trials.jsonl (status ok) from artifacts/run-exp-battle-sweep/. All statements are [O] observed or [D] derived; Wine-only.
"""
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import stage  # noqa: E402
import trials as T  # noqa: E402
from state import battle_block as BB  # noqa: E402


def series_sets():
    sets = {}
    probe = C.ROOT / "artifacts" / "run-exp-battle-probe"
    for tag in ("gate2_a", "gate2_s2a"):
        sets[f"B0 {tag} (FLD-RG natural, 14 units)"] = sorted(glob.glob(str(probe / f"{tag}_BATTLE[0-9][0-9].SAV")))
    for r in T.read_trials():
        if r.get("status") == "ok" and r.get("series"):
            sets[r["trial"]] = [str(C.ART / n) for n in r["series"]]
    return sets


def all_files_pass():
    """Every `*BATTLE<nn>*.SAV` file under the two artifacts folders (B0's probe series, the trials' series, B3's crafted/resumed series and
    strays), decoded one by one: grid inconsistencies and sprite-rule violations, counted per group. Crafted resumes of an EDITED save
    (`crafted/b3_d5_*`, `b3_d6_*` ...) may violate the rule on purpose (the game does not repair the grid); they are listed separately."""
    groups = defaultdict(lambda: {"files": 0, "grid_inconsistent": 0, "sprite_violations": 0, "examples": []})
    for root in (C.ROOT / "artifacts" / "run-exp-battle-probe", C.ART):
        for f in sorted(root.rglob("*BATTLE[0-9][0-9]*.SAV")):
            if "crafted" in f.parts and f.name.startswith("CRAFT_"):
                continue
            g = ("B3 crafted/resumed series" if "crafted" in f.parts else "B0 probe series (artifacts/run-exp-battle-probe)" if "probe" in str(root)
                 else "B4 trials and other sweep series")
            try:
                b = BB.from_save(f)
            except Exception as e:      # noqa: BLE001
                groups[g]["examples"].append((f.name, "undecodable: %s" % e))
                continue
            if b is None:
                continue
            r = groups[g]
            r["files"] += 1
            if BB.check_grid(b):
                r["grid_inconsistent"] += 1
                if len(r["examples"]) < 5:
                    r["examples"].append((f.name, BB.check_grid(b)[:1]))
            v = sum(1 for s_ in b["slots"] if s_["alive"] and b["grid"][BB.cell(s_["x"], s_["y"])] != stage.sprite_value(s_["side"], s_["type"], s_["troops"]))
            r["sprite_violations"] += v
    return {k: v for k, v in groups.items()}


def main():
    sets = series_sets()
    out = {"series": {k: len(v) for k, v in sets.items()}, "files_decoded": 0}
    size = defaultdict(lambda: defaultdict(list))            # type -> class -> troops
    state_by_type = defaultdict(Counter)                     # (type) -> Counter of state at the FIRST file of the series
    ammo_start = defaultdict(Counter)
    hdr = []
    placed = []
    amb = {"loss_rows": 0, "unambiguous": 0}
    grid_bad = sprite_bad = 0
    acting = Counter()
    for name, files in sets.items():
        prev = None
        seq = []
        for i, f in enumerate(files):
            b = BB.from_save(f)
            out["files_decoded"] += 1
            seq.append((b["half_round"], b["x2"], b["y1"]))
            grid_bad += bool(BB.check_grid(b))
            for s in b["slots"]:
                if not s["alive"]:
                    continue
                v = b["grid"][BB.cell(s["x"], s["y"])]
                if v != stage.sprite_value(s["side"], s["type"], s["troops"]):
                    sprite_bad += 1
                size[s["type"]][v - 20 * s["side"] - 3 * BB.TYPES.index(s["type"])].append(s["troops"])
                if i == 0:
                    ammo_start[s["type"]][s["ammo"]] += 1
                if i == 1:
                    state_by_type[s["type"]][s["state"]] += 1
            if prev:
                d = BB.diff(prev, b)
                amb["loss_rows"] += d["losses"]
                amb["unambiguous"] += d["unambiguous"]
                import halflog
                acting[tuple(halflog.acting_sides(d, prev, b))] += 1
            prev = b
        hdr.append({"series": name, "half_round_x2_y1": seq})
    out["header_sequences"] = hdr
    out["grid_inconsistent_files"] = grid_bad
    out["sprite_rule_violations"] = sprite_bad
    out["size_class_troop_range"] = {t: {c: (min(v), max(v)) for c, v in sorted(cl.items())} for t, cl in size.items()}
    out["size_class_rule_D"] = "class 0 below std/3, 1 below 2*std/3, else 2; std LI 15000 HI 6000 Ar 3500 LC 7000 HC 2500 (stage.sprite_value)"
    out["ammo_at_first_file"] = {t: dict(c) for t, c in ammo_start.items()}
    out["state_at_second_file"] = {t: dict(c) for t, c in state_by_type.items()}
    out["loss_rows_unambiguous"] = amb
    out["acting_sides_per_half_round_D"] = {str(k): v for k, v in acting.items()}
    out["all_battle_saves"] = all_files_pass()
    out["all_battle_saves_total"] = sum(v["files"] for v in out["all_battle_saves"].values())
    p = C.DATA / f"b2-analysis-{C.STAMP}.json"
    p.write_text(json.dumps(out, indent=1, default=str))
    print(p)
    print(json.dumps({k: out[k] for k in ("files_decoded", "grid_inconsistent_files", "sprite_rule_violations", "all_battle_saves_total", "all_battle_saves", "loss_rows_unambiguous", "ammo_at_first_file", "state_at_second_file", "acting_sides_per_half_round_D")}, indent=1))


if __name__ == "__main__":
    main()
