#!/usr/bin/env python3
"""B8 offline analysis of the icon ladder (`b8_ladder.py`, `b8-ladder-v2-*.jsonl`; the v1 files `b8-ladder-2026*.jsonl` of the 12-units-per-side run are kept but their
defender observations are mostly invalid: more than 9 defenders share cells, see README) -> `b8-thresholds-<stamp>.json` and `b8-icon-index-<stamp>.csv`.

Only units alone on their cell count. Per (type, side): troops -> size class (the grid word minus side*20 + 3*type), the class changes with their exact troop pair, monotonicity,
the comparison with the decompiled rule [R-code] `min(2, troops div (std div 3))` and with B2's earlier hypothesis `3*troops < std`; per (type, side, class) the set of
inner-26x26 tile hashes (image diff): one icon per (type, side, class), different icons for different words. The index lists one screenshot per (type, side, class)."""
import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import stage  # noqa: E402
from state import battle_block as BB  # noqa: E402


def main():
    files = sorted(C.DATA.glob("b8-ladder-v2-*.jsonl"))
    obs = defaultdict(dict)                    # (type, side) -> troops -> class
    tiles = defaultdict(set)                   # (type, side, class) -> hashes
    word_tiles = defaultdict(set)
    rep = {}
    rounds = []
    for f in files:
        for l in open(f):
            r = json.loads(l)
            if "slots" not in r or r.get("status") != "ok":
                continue
            rounds.append({"tag": r["tag"], "type": r["type"], "purpose": r["purpose"], "file": f.name, "screenshot": r["screenshot"], "save": r["saves"][:1], "n_slots": len(r["slots"])})
            cells = defaultdict(int)
            for s in r["slots"]:
                cells[(s["x"], s["y"])] += 1
            for s in r["slots"]:
                if cells[(s["x"], s["y"])] != 1:
                    continue
                k = (r["type"], s["side"])
                obs[k][s["troops"]] = s["size_class"]
                tiles[(r["type"], s["side"], s["size_class"])].add(s["tile"])
                word_tiles[s["grid_word"]].add(s["tile"])
                rep.setdefault((r["type"], s["side"], s["size_class"]), (s["troops"], r["screenshot"], r["saves"][0] if r["saves"] else "", (s["x"], s["y"])))
    out = {"files": [f.name for f in files], "rounds": len(rounds), "per_type_side": {}}
    for (typ, side), o in sorted(obs.items()):
        pts = sorted(o.items())
        changes = [{"last_below": a, "first_above": b, "from_class": c, "to_class": d} for (a, c), (b, d) in zip(pts, pts[1:]) if c != d]
        std = stage.STD[typ]
        out["per_type_side"]["%s side %d" % (typ, side)] = {
            "points": len(pts), "troops_min": pts[0][0], "troops_max": pts[-1][0], "monotone": all(c <= d for (a, c), (b, d) in zip(pts, pts[1:])),
            "class_changes": changes, "exact_one_troop": all(c["first_above"] - c["last_below"] == 1 for c in changes),
            "equals_rule_R_code_min2_troops_div_std_div_3": all(v == min(2, t // (std // 3)) for t, v in pts),
            "equals_B2_hypothesis_3troops_lt_std": all(v == (0 if t * 3 < std else 1 if t * 3 < 2 * std else 2) for t, v in pts),
            "first_troops_of_class_1_2": [c["first_above"] for c in changes]}
    out["icons"] = {"one_icon_per_type_side_class": all(len(v) == 1 for v in tiles.values()), "distinct_type_side_class_icons": len({h for v in tiles.values() for h in v}),
                    "type_side_class_combinations": len(tiles), "every_word_one_icon": all(len(v) == 1 for v in word_tiles.values()),
                    "different_words_different_icons": len({next(iter(v)) for v in word_tiles.values()}) == len(word_tiles), "words": len(word_tiles)}
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["type", "side", "size_class", "grid_word", "first_troops_of_class_rule", "example_troops", "tile_hash12", "screenshot", "save", "cell_xy"])
    for (typ, side, cls), (tr, shot, sv, xy) in sorted(rep.items()):
        t = BB.TYPES.index(typ)
        w.writerow([typ, side, cls, side * 20 + 3 * t + cls, cls * (stage.STD[typ] // 3), tr, next(iter(tiles[(typ, side, cls)])), shot, sv, "%d,%d" % xy])
    p1 = C.write_new(C.DATA, f"b8-thresholds-{C.STAMP}.json", json.dumps({**out, "rounds_list": rounds}, indent=1))
    p2 = C.write_new(C.DATA, f"b8-icon-index-{C.STAMP}.csv", buf.getvalue())
    print(p1.name, p2.name)
    print(json.dumps({k: v for k, v in out["per_type_side"].items()}, indent=0)[:3000])
    print(out["icons"])


if __name__ == "__main__":
    main()
