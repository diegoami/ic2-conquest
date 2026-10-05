#!/usr/bin/env python3
"""B16 analysis, from trials-b16.jsonl and the kept binaries (CLAUDE.md rule 6: every output is a NEW tracked file, nothing overwritten).

    python3 runs/experiments/battles/b16_analyze.py table            # per-run table (D-LOSS / D-WIN): box, text, buttons, strategic state, [R-code] tests
    python3 runs/experiments/battles/b16_analyze.py pairs            # Yes/No pairs: the state before the answer, byte for byte, and the 4-turn diffs
    python3 runs/experiments/battles/b16_analyze.py snapdiff A B     # offsets that differ between two pre-answer snapshots

The pre-answer comparison reads the two `.snap.gz` files (raw game memory 0x45E030..0x4A0B80 at the moment the box was up, before the click)
and compares the BYTES, not the recorded hashes; the dialog screenshots are compared by SHA-256 of the PNG files.
"""
import csv
import gzip
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b16_common as B  # noqa: E402
import common as C  # noqa: E402
from state import sav  # noqa: E402

D = B.D
SNAP_BASE = 0x45E030


def trials():
    f = B.DATA / "trials-b16.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def latest_ok(label_filter=None):
    """{trial id: last ok record}."""
    out = {}
    for r in trials():
        if r.get("status") == "ok":
            out[r["trial"]] = r
    return out


def snap_bytes(name):
    return gzip.decompress((B.ART / "snaps" / name).read_bytes())


def diff_offsets(a, b, limit=40):
    """Byte offsets (as addresses) where two equal-length buffers differ: runs, not single bytes."""
    runs, i, n = [], 0, min(len(a), len(b))
    while i < n:
        if a[i] != b[i]:
            j = i
            while j + 1 < n and a[j + 1] != b[j + 1]:
                j += 1
            runs.append((hex(SNAP_BASE + i), j - i + 1))
            i = j + 1
        else:
            i += 1
    return {"len_a": len(a), "len_b": len(b), "differing_bytes": sum(r[1] for r in runs), "runs": runs[:limit], "runs_total": len(runs)}


def png_sha(name):
    p = B.ART / "shots" / name if name else None
    return C.sha(p) if p and p.exists() else None


def rows_table(recs):
    out = []
    for r in recs:
        rc = r.get("rcode") or {}
        d = (r.get("dialogs") or [{}])[0] if r.get("dialogs") else {}
        out.append({
            "trial": r["trial"], "cell": r["cell"], "seed": r["seed"], "answer_plan": r["answer_plan"], "build": r["build"], "box_opened": r.get("box_opened"),
            "winner": {0: "Rome", 6: "Gaul"}.get(rc.get("winner")), "loser_unity": rc.get("unity_L"), "loser_cities": rc.get("cities_L"),
            "armies_W": rc.get("armies_W"), "armies_L": rc.get("armies_L"), "armies_W_lt_L": rc.get("armies_W_lt_L"),
            "unity_gt_500": rc.get("unity_L_gt_500"), "cities_gt_7": rc.get("cities_L_gt_7"), "preconditions_pass": rc.get("preconditions_pass"),
            "box_title": r.get("box_title"), "buttons": "/".join(r.get("box_buttons") or []), "answered": r.get("answered"),
            "clicks": (r.get("answer_click") or {}).get("clicks"), "closed": (r.get("answer_click") or {}).get("closed"),
            "box_text": (r.get("box_text") or "").replace("\n", " "), "dialog_shot": d.get("shot"), "battle_ended_shot": r.get("battle_ended_shot"),
            "pre_sha12": (r.get("pre_sha256") or "")[:12], "randseed_loaded": r.get("randseed_loaded"), "post_save": r.get("post_save"),
            "pre_snap": r.get("pre_snap"), "seconds_load": r.get("load_seconds"), "start_save": r.get("start_save")})
    return out


def cmd_table():
    recs = [r for r in latest_ok().values() if r["answer_plan"] == "capture"]
    rows = rows_table(sorted(recs, key=lambda r: (r["cell"], r["seed"], r["trial"])))
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    p = C.write_new(B.DATA, "b16-survey-table-%s.csv" % C.STAMP, buf.getvalue())
    print(p, len(rows), "rows")


def flat(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(o, (list, tuple)) and not (len(o) > 0 and all(isinstance(x, int) for x in o) and len(o) > 64):
        for i, v in enumerate(o):
            yield from flat(v, "%s[%d]" % (path, i))
    else:
        yield path, o


def save_diff(pa, pb):
    """Structured diff of two saves (every parsed field of cities, armies, fleets, nations, mercenaries, news, calendar, tail; the map by cell count)
    plus the raw differing byte count. Returns {raw_bytes_differing, size_a, size_b, fields: [(path, a, b)], map_cells}."""
    ba, bb = Path(pa).read_bytes(), Path(pb).read_bytes()
    sa, sb = sav.parse(ba), sav.parse(bb)
    fa, fb = dict(flat({k: v for k, v in sa.items() if k != "map"})), dict(flat({k: v for k, v in sb.items() if k != "map"}))
    fields = [(k, fa.get(k), fb.get(k)) for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)]
    return {"size_a": len(ba), "size_b": len(bb), "raw_bytes_differing": sum(1 for x, y in zip(ba, bb) if x != y) + abs(len(ba) - len(bb)),
            "map_cells_differing": sum(1 for x, y in zip(sa["map"], sb["map"]) if x != y), "fields": fields}


VOLATILE = [(0x45E614, 0x45E618)]      # two words that vary from run to run for the SAME save, seed and answer (see the finding): not game state


def _only_volatile(a, b):
    if len(a) != len(b):
        return False
    return all(any(lo <= SNAP_BASE + i < hi for lo, hi in VOLATILE) for i in range(len(a)) if a[i] != b[i])


def pair_compare(ry, rn):
    keys = ["start_sha256", "seed_line", "randseed_loaded", "state_at_load", "randseed_battle_open", "end_turn_clicks", "battle_ended_text",
            "box_opened", "box_title", "box_text", "box_buttons", "pre_regions", "strategic_pre", "rcode"]
    same = {k: ry.get(k) == rn.get(k) for k in keys if k != "box_buttons"}
    same["box_buttons"] = sorted(ry.get("box_buttons") or []) == sorted(rn.get("box_buttons") or [])
    dy, dn = ry["dialogs"][0], rn["dialogs"][0]
    same["dialog_geometry"] = dy["geometry"] == dn["geometry"]
    same["dialog_controls"] = sorted(map(json.dumps, dy["controls"])) == sorted(map(json.dumps, dn["controls"]))
    same["dialog_shot_png_bytes"] = png_sha(dy.get("shot")) == png_sha(dn.get("shot")) and png_sha(dy.get("shot")) is not None
    ay, an = snap_bytes(ry["pre_snap"]), snap_bytes(rn["pre_snap"])
    same["pre_snapshot_bytes_outside_volatile"] = ay == an or _only_volatile(ay, an)
    out = {"yes": ry["trial"], "no": rn["trial"], "seed": ry["seed"], "cell": ry["cell"], "same": same, "pre_identical": all(same.values()),
           "pre_strictly_identical": ay == an, "battle_title_at_open": [ry["battle_title"], rn["battle_title"]],
           "snapshot_diff": None if ay == an else diff_offsets(ay, an)}
    return out


def cmd_pairs():
    recs = latest_ok()
    by = {}
    for r in recs.values():       # trials-b16.jsonl order = run order: the LAST ok record of a (cell, seed, answer plan) with a dialog shot and controls is paired
        if r.get("dialogs") and r["dialogs"][0].get("shot") and r["dialogs"][0].get("controls") and r["answer_plan"] in ("yes", "no"):
            by[(r["cell"], r["seed"], r["answer_plan"])] = [r]
    res = []
    for (cell, seed, ans), rs in sorted(by.items()):
        if ans != "yes":
            continue
        for ry in rs:
            for rn in by.get((cell, seed, "no"), []):
                pc = pair_compare(ry, rn)
                pc["answers"] = {"yes": ry["answered"], "no": rn["answered"]}
                pc["clicks"] = {"yes": ry["answer_click"], "no": rn["answer_click"]}
                pc["after_answer"] = {"yes": ry["after_answer"]["reads"], "no": rn["after_answer"]["reads"]}
                pc["after_answer_regions_differ"] = [k for k in ry["after_answer"]["regions"] if ry["after_answer"]["regions"][k] != rn["after_answer"]["regions"][k]]
                pc["post_save_diff"] = save_diff(B.ART / ry["post_save"], B.ART / rn["post_save"])
                pc["turns"] = []
                for ty, tn in zip(ry.get("turns", []), rn.get("turns", [])):
                    row = {"turn": ty["turn_index"], "yes": {"after": ty.get("after"), "autosave": ty.get("autosave"), "news_texts": ty.get("texts")},
                           "no": {"after": tn.get("after"), "autosave": tn.get("autosave"), "news_texts": tn.get("texts")}}
                    if ty.get("save") and tn.get("save"):
                        row["save_diff"] = save_diff(B.ART / "turns" / ty["save"], B.ART / "turns" / tn["save"])
                    pc["turns"].append(row)
                res.append(pc)
    rows = []
    for pc in res:
        def rel(x, who):
            return x[who]["rel"] if x else None
        ry, rn = pc["after_answer"]["yes"], pc["after_answer"]["no"]
        pd = pc["post_save_diff"]
        row = {"cell": pc["cell"], "seed": pc["seed"], "pre_identical": pc["pre_identical"], "answers": "%s/%s" % (pc["answers"]["yes"], pc["answers"]["no"]),
               "clicks": "%s/%s" % (pc["clicks"]["yes"]["clicks"], pc["clicks"]["no"]["clicks"]),
               "rel_after_answer_yes_no": "%s/%s" % (ry["Rome"]["rel"], rn["Rome"]["rel"]),
               "post_save_nonnews_fields": ";".join(f[0] for f in pd["fields"] if not f[0].startswith("news")),
               "post_save_raw_bytes_differing": pd["raw_bytes_differing"]}
        for t in pc["turns"]:
            n = t["turn"]
            ay, an = t["yes"]["after"], t["no"]["after"]
            if ay and an:
                row["t%d_rel" % n] = "%s/%s" % (ay["Rome"]["rel"], an["Rome"]["rel"])
                row["t%d_rome_cities" % n] = "%s/%s" % (ay["Rome"]["cities"], an["Rome"]["cities"])
                row["t%d_gaul_cities" % n] = "%s/%s" % (ay["Gaul"]["cities"], an["Gaul"]["cities"])
                row["t%d_rome_treasury" % n] = "%s/%s" % (ay["Rome"]["treasury"], an["Rome"]["treasury"])
                row["t%d_gaul_treasury" % n] = "%s/%s" % (ay["Gaul"]["treasury"], an["Gaul"]["treasury"])
                row["t%d_rome_unity" % n] = "%s/%s" % (ay["Rome"]["unity"], an["Rome"]["unity"])
                row["t%d_gaul_unity" % n] = "%s/%s" % (ay["Gaul"]["unity"], an["Gaul"]["unity"])
        rows.append(row)
    if rows:
        cols = []
        for r in rows:
            cols += [k for k in r if k not in cols]
        buf = io.StringIO(newline="")
        w = csv.DictWriter(buf, cols)
        w.writeheader()
        w.writerows(rows)
        print(C.write_new(B.DATA, "b16-pairs-summary-%s.csv" % C.STAMP, buf.getvalue()))
    p = C.write_new(B.DATA, "b16-pairs-%s.json" % C.STAMP, json.dumps(res, indent=1, default=str))
    for pc in res:
        print(pc["yes"], pc["no"], "pre_identical", pc["pre_identical"], {k: v for k, v in pc["same"].items() if not v})
    print(p)


def cmd_repeat():
    """Same cell, same seed, same answer (No and capture both press No), different process: the pre-answer snapshot bytes, the post-answer Save As
    bytes, the dialog text and every End turn autosave (the turns both runs made), byte for byte. One record per pair of runs."""
    recs = list(latest_ok().values())
    groups = {}
    for r in recs:
        if r.get("dialogs") or r.get("box_opened") is False:
            groups.setdefault((r["cell"], r["seed"], "yes" if r["answer_plan"] == "yes" else "no"), []).append(r)
    out = []
    for key, rs in sorted(groups.items()):
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = rs[i], rs[j]
                row = {"cell": key[0], "seed": key[1], "answer": key[2], "a": a["trial"], "b": b["trial"], "box_opened": (a["box_opened"], b["box_opened"]),
                       "pre_snapshot_bytes_equal": snap_bytes(a["pre_snap"]) == snap_bytes(b["pre_snap"]),
                       "pre_snapshot_equal_outside_volatile": _only_volatile(snap_bytes(a["pre_snap"]), snap_bytes(b["pre_snap"])),
                       "box_text_equal": a.get("box_text") == b.get("box_text"),
                       "post_save_bytes_equal": (B.ART / a["post_save"]).read_bytes() == (B.ART / b["post_save"]).read_bytes(),
                       "turn_saves": []}
                for ta, tb in zip(a.get("turns", []), b.get("turns", [])):
                    if ta.get("save") and tb.get("save"):
                        row["turn_saves"].append({"turn": ta["turn_index"], "a": ta["save"], "b": tb["save"],
                                                  "bytes_equal": (B.ART / "turns" / ta["save"]).read_bytes() == (B.ART / "turns" / tb["save"]).read_bytes()})
                out.append(row)
    p = C.write_new(B.DATA, "b16-repeat-%s.json" % C.STAMP, json.dumps(out, indent=1))
    for r in out:
        print(r["a"], r["b"], "pre", r["pre_snapshot_bytes_equal"], "post", r["post_save_bytes_equal"], "turns", [t["bytes_equal"] for t in r["turn_saves"]])
    print(p)


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "table":
        cmd_table()
    elif a[0] == "pairs":
        cmd_pairs()
    elif a[0] == "repeat":
        cmd_repeat()
    elif a[0] == "snapdiff":
        print(json.dumps(diff_offsets(snap_bytes(a[1]), snap_bytes(a[2])), indent=1))


if __name__ == "__main__":
    main()
