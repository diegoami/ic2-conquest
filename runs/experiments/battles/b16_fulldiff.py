#!/usr/bin/env python3
"""B16 R2: what the answer changes, over the whole decoded save, per branch (Yes and No), from the state BEFORE the answer to the state AFTER it.

    python3 runs/experiments/battles/b16_fulldiff.py

BEFORE = the memory snapshot taken with the box up (`<trial>_pre.snap.gz`), AFTER = the Save As taken right after the box closed (`<trial>_post.SAV`).
The snapshot holds, at fixed game addresses, the same blocks as a save: map (0x45E870), nations (0x474670), cities (0x479590, found by searching the
save's block in the snapshot; 334 x 34 bytes, contiguous with the armies), armies (0x47C1EC), fleets (0x49C26C), mercenaries (0x49DA10) and the news ring (40 lines of 61 bytes,
located by search). A "before save" is built by laying those blocks over the post save's own bytes (so layout, sizes and the tail are the save's) and decoded with
`state/sav.py` exactly like the after save; every decoded field of cities, armies, fleets, nations (relations included), mercenaries and news is compared
(`save_diff`), and the map cell by cell. NOT in the snapshot, hence not compared before/after: the save's tail (turn order, current seat, pending offer, calendar,
battle flag) and the battle block; those are compared between the Yes and No post saves (b16_analyze.py pairs). Sanity: in the No branch the blocks laid over must
equal the post save's blocks, or the layout assumption is reported as broken.
Writes `b16-fulldiff-<stamp>.json` (every changed field of every run) and `b16-fulldiff-summary-<stamp>.md` (new files; older ones kept)."""
import gzip
import json
import os
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("IC2_WORK", "/nonexistent")
os.environ.setdefault("DISPLAY_IC2", ":640")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import b16_analyze as A  # noqa: E402
import b16_common as B  # noqa: E402
import common as C  # noqa: E402
from state import sav  # noqa: E402

BASE = 0x45E030
MAP, CITIES, ARMIES, FLEETS, NATIONS, MERCS = 0x45E870, 0x479590, 0x47C1EC, 0x49C26C, 0x474670, 0x49DA10
NEWS_N = 40


def layout(post):
    na = struct.unpack_from("<h", post, sav.ARMY_OFF)[0]
    of = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN
    nf = struct.unpack_from("<h", post, of)[0]
    nat0 = of + 2 + nf * sav.FLEET_LEN
    return {"na": na, "nf": nf, "of": of, "nat0": nat0, "mercs0": nat0 + 16 * sav.NATION_LEN}


def before_save(snap, post, news_base):
    """The post save with its blocks replaced by the snapshot's: the 'save' of the moment the box was up (except the tail, see the module doc)."""
    L = layout(post)
    b = bytearray(post)
    take = lambda addr, n: snap[addr - BASE:addr - BASE + n]
    b[0:89600] = take(MAP, 89600)
    b[sav.CITY_OFF:sav.CITY_OFF + sav.CITY_N * sav.CITY_LEN] = take(CITIES, sav.CITY_N * sav.CITY_LEN)
    b[sav.ARMY_OFF + 2:sav.ARMY_OFF + 2 + L["na"] * sav.ARMY_LEN] = take(ARMIES, L["na"] * sav.ARMY_LEN)
    b[L["of"] + 2:L["of"] + 2 + L["nf"] * sav.FLEET_LEN] = take(FLEETS, L["nf"] * sav.FLEET_LEN)
    b[L["nat0"]:L["nat0"] + 16 * sav.NATION_LEN] = take(NATIONS, 16 * sav.NATION_LEN)
    b[L["mercs0"]:L["mercs0"] + 600] = take(MERCS, 600)
    news = [snap[news_base - BASE + 61 * k:news_base - BASE + 61 * (k + 1)].split(b"\0")[0].decode("latin1") for k in range(NEWS_N)]
    return bytes(b), news


def find_news_base(snap, post_no):
    """Address of the news ring in the snapshot, found by searching the No post save's first 20 news lines (raw 61-byte records)."""
    L = layout(post_no)
    n0 = L["mercs0"] + 600
    seg = post_no[n0 + 2:n0 + 2 + 61 * 20]
    i = snap.find(seg)
    if i < 0:
        raise SystemExit("news ring not found in the snapshot")
    return BASE + i


def diff_runs(rec, news_base):
    snap = A.snap_bytes(rec["pre_snap"])
    post = (B.ART / rec["post_save"]).read_bytes()
    pre, news_pre = before_save(snap, post, news_base)
    sp, sq = sav.parse(pre), sav.parse(post)
    sp["news"] = news_pre
    fa, fb = dict(A.flat({k: v for k, v in sp.items() if k not in ("map", "tail_off")})), dict(A.flat({k: v for k, v in sq.items() if k not in ("map", "tail_off")}))
    fields = [(k, fa.get(k), fb.get(k)) for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)]
    cb, ca = Counter(news_pre), Counter(sq["news"])
    return {"trial": rec["trial"], "answer": rec["answered"], "cell": rec["cell"], "seed": rec["seed"], "fields": fields,
            "news_added": sorted((ca - cb).elements()), "news_dropped": sorted((cb - ca).elements()),
            "map_cells_changed": sum(1 for x, y in zip(sp["map"], sq["map"]) if x != y),
            "news_lines_before": len(news_pre), "news_lines_after": len(sq["news"])}


def group(path):
    import re
    return re.sub(r"\[\d+\]", "[]", path)


def main():
    T = A.latest_ok()
    pairs = {}
    for r in T.values():
        if r["answer_plan"] in ("yes", "no") and r.get("turns") and r.get("dialogs") and r["dialogs"][0].get("shot"):
            pairs[(r["cell"], r["seed"], r["answer_plan"])] = r
    # the layout check: in a No branch (nothing written) the blocks laid over must equal the post save's blocks, for the strategic blocks the save holds
    k0 = next(k for k in sorted(pairs) if k[2] == "no")
    snap0 = A.snap_bytes(pairs[k0]["pre_snap"])
    base = find_news_base(snap0, (B.ART / pairs[k0]["post_save"]).read_bytes())
    out, summ = [], defaultdict(lambda: defaultdict(Counter))
    for k, r in sorted(pairs.items()):
        d = diff_runs(r, base)
        out.append(d)
        for p, a, b in d["fields"]:
            summ[k[2]][group(p)][k[0] + ("" if k[0] == "loss" else "")] += 1
    res = C.write_new(B.DATA, "b16-fulldiff-%s.json" % C.STAMP, json.dumps({"news_ring_address": hex(base), "runs": out}, indent=1, default=str))
    lines = ["# B16 full before/after diff per answer (b16_fulldiff.py)\n", "news ring at %s; %d runs\n" % (hex(base), len(out))]
    for ans in ("yes", "no"):
        rs = [d for d in out if d["answer"].lower() == ans]
        lines.append("\n## %s: %d runs; changed fields per run: %s; map cells changed: %s; news lines before/after: %s\n" % (
            ans.upper(), len(rs), sorted({len(d["fields"]) for d in rs}), sorted({d["map_cells_changed"] for d in rs}), sorted({(d["news_lines_before"], d["news_lines_after"]) for d in rs})))
        lines.append("  news lines added (same in every run?): %s; dropped: %s\n" % (sorted({tuple(d["news_added"]) for d in rs}), sorted({tuple(d["news_dropped"]) for d in rs})))
        lines.append("  non-news, non-relation changed fields in any run: %s\n" % sorted({p for d in rs for p, a, b in d["fields"] if not p.startswith("news") and ".relations." not in p}))
        lines.append("  relation fields: %s\n" % sorted({(p, str(a), str(b)) for d in rs for p, a, b in d["fields"] if ".relations." in p}))
        classes = Counter()
        for d in rs:
            for p, a, b in d["fields"]:
                classes[group(p)] += 1
        for p, n in sorted(classes.items()):
            lines.append("- `%s`: %d changes over %d runs\n" % (p, n, len(rs)))
    md = C.write_new(B.DATA, "b16-fulldiff-summary-%s.md" % C.STAMP, "".join(lines))
    print(res, md)
    print("".join(lines)[:3000])


if __name__ == "__main__":
    main()
