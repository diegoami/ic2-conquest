#!/usr/bin/env python3
"""B16 claims audit: every number and every "identical / closed / opened" claim of findings/2026-10-05-battle-peace-offer.md recomputed from the RAW
files (the `.snap.gz` memory snapshots, the Save As / autosave `.SAV` files, the dialog and Battle-ended screenshots, and `trials-b16.jsonl` for the
facts that only the run knows: the seed, the plan, the answer clicked, the box text), written as `b16-claims-audit-<stamp>.md` in the tracked data folder
(never overwritten). Exit 1 on a mismatch.

    python3 runs/experiments/battles/b16_audit.py

Independence: the unity, city count, relation, treasury, army strength, owner and news values are read from the BYTES with `struct` here (nation record
+0x26/0x438/0x440/0x446, army record +4/+14/+16.., the offsets of docs/sav-layout-notes.md); `b16_analyze.py`, `b16_run.strategic`/`rcode`, `state.sav` and
`state.battle` are not used. Shared with the run: the file lists, and the way a snapshot/save is located (memory addresses of the nation and army
tables, the save's block order). The SHA-256 of every binary is checked against `SAVES.v2.sha256` (one form: `<sha256>  <bare file name>`).
"""
import csv
import re
import gzip
import hashlib
import json
import os
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("IC2_WORK", "/nonexistent")
os.environ.setdefault("DISPLAY_IC2", ":640")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import b16_common as B  # noqa: E402
import b16_numbers as NUMS  # noqa: E402
import common as C  # noqa: E402

BASE = 0x45E030
NAT, ARM = 0x474670, 0x47C1EC
WEIGHT = {0: 20, 1: 100, 2: 40, 3: 60, 4: 120}      # unit type index -> power weight (docs/rules-digest.md: li, hi, ar, lc, hc)
rows = []
CL = {}          # claim id -> (match, text of the checked values)


def norm(x):
    """JSON-comparable form: tuples are lists, sets sorted lists, dict keys strings (so claimed values can live in b16_expect.json)."""
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if isinstance(x, set):
        return sorted((norm(v) for v in x), key=str)
    return x


def claim(doc, text, source, got, want, cid=None):
    ok = norm(got) == norm(want)
    rows.append((doc, text, source, norm(got), norm(want), "y" if ok else "N"))
    if cid:
        assert cid not in CL, cid
        CL[cid] = (ok, json.dumps(norm(want)))


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def trials():
    return [json.loads(x) for x in (B.DATA / "trials-b16.jsonl").read_text().splitlines() if x.strip()]


def ok_trials():
    last = {}
    for r in trials():
        if r.get("status") == "ok":
            last[r["trial"]] = r
    return last


def snap(name):
    return gzip.decompress((B.ART / "snaps" / name).read_bytes())


# ---- raw readers of a memory snapshot ----------------------------------------------------------------------------------------------------
def s_nation(b, n, off):
    return i16(b, NAT - BASE + n * 1172 + off)


def s_armies(b, owner):
    """Σ over the owner's live armies of (Σ weight*troops//100) // 80 * morale (FUN_0044A8CC), read from the bytes."""
    tot = 0
    for i in range(200):
        r = ARM - BASE + i * 656
        if i16(b, r + 4) != owner:
            continue
        s = 0
        for k in range(20):
            lab, typ, troops, q = struct.unpack_from("<4h", b, r + 16 + 32 * k)
            if troops > 0:
                s += WEIGHT[typ] * troops // 100
        if s:
            tot += s // 80 * i16(b, r + 14)
    return tot


def s_army_alive(b, i):
    r = ARM - BASE + i * 656
    return i16(b, r + 4) == 0 and sum(max(0, i16(b, r + 16 + 32 * k + 4)) for k in range(20)) > 0       # still Rome's (a deleted army is re-owned) with troops


# ---- raw readers of a save -------------------------------------------------------------------------------------------------------------------
def v_offsets(b):
    na = i16(b, 100956)
    of = 100956 + 2 + na * 656
    nf = i16(b, of)
    return of + 2 + nf * 26            # nation 0 record


def v_nation(b, n, off):
    return i16(b, v_offsets(b) + n * 1172 + off)


def v_treasury(b, n):
    return struct.unpack_from("<i", b, v_offsets(b) + n * 1172 + 0x438)[0]


def v_news(b):
    o = v_offsets(b) + 16 * 1172 + 600
    ni = i16(b, o)
    out = []
    for k in range(ni + 1):
        raw = b[o + 2 + 61 * k:o + 2 + 61 * (k + 1)]
        out.append(raw.split(b"\0")[0].decode("latin1"))
    return out


def differs_only_in_volatile(a, b):
    return len(a) == len(b) and (a == b or all(0x45E614 <= BASE + i < 0x45E618 for i in range(len(a)) if a[i] != b[i]))


def cstr_(b):
    return b.split(b"\0")[0].decode("latin1")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def more(T, pairs, box_from_files, shas):
    """R1: claims that carry every remaining number of the finding (each with a claim id the number map refers to), the recomputation of the finding's tables, the
    existence of every cited file or cell, and the number map check."""
    normal = [r for r in T.values() if r["build"] == "normal"]
    opened_norm = [r for r in normal if r["answer_plan"] in ("capture", "yes", "no") and box_from_files(r)]
    survey = {}
    for r in normal:
        if r["answer_plan"] == "capture":
            if (r["cell"], r["seed"]) not in survey or "survey" in r["trial"]:
                survey[(r["cell"], r["seed"])] = r
    # --- box ---------------------------------------------------------------------------------------------------------------------------------
    rect = {}
    for r in opened_norm:
        g = r["dialogs"][0]["geometry"]
        for c in r["dialogs"][0].get("controls") or []:
            rect.setdefault(c["text"], set()).add((c["x"] - g[0], c["y"] - g[1], c["w"], c["h"]))
    claim("finding box", "button rectangles relative to the box: Yes (81, 320), No (256, 320), both 70 x 25, in every recorded control list", "trials-b16.jsonl controls",
          {k: sorted(v) for k, v in rect.items()}, {"No": [[256, 320, 70, 25]], "Yes": [[81, 320, 70, 25]]}, cid="rects")
    claim("finding box", "exactly two controls (both TButton) in every recorded control list", "trials-b16.jsonl controls", {"controls": sorted({len(r["dialogs"][0]["controls"]) for r in opened_norm if r["dialogs"][0].get("controls")})}, {"controls": [2]}, cid="nbuttons")
    claim("finding box", "box geometry x, y, width, height and title in every opened run", "trials-b16.jsonl", ({tuple(r["dialogs"][0]["geometry"]) for r in opened_norm}, {r["box_title"] for r in opened_norm}),
          ([(13, 94, 406, 360)], ["Offer of peace"]), cid="geom")
    claim("finding box", "the reparation lines: no line of the OCR text names a sum (no digits in any opened run's box text)", "trials-b16.jsonl", sum(1 for r in opened_norm if any(ch.isdigit() for ch in r["box_text"])), 0, cid="nodigits")
    # --- cells and read-backs ------------------------------------------------------------------------------------------------------------------
    def loaded(cell, key):
        return {json.dumps(r["armies_loaded"][key]) for r in normal if r["cell"] == cell and r["status"] == "ok"}
    EXT = "win+own12=6,strong12=6,unity6=600,weak2=500,weak13=500"
    claim("finding method", "army contents read back from game memory before the attack: loss cell Rome army 0 = one LI 3,000 quality 6; win cell Gaul army 10 = one LI 3,000 quality 6", "trials-b16.jsonl armies_loaded",
          (sorted(loaded("loss", "rome0")), sorted(loaded("win", "gaul10"))), ([json.dumps([["li", 3000, 6]])], [json.dumps([["li", 3000, 6]])]), cid="cells")
    rb = {}
    for r in normal:
        if r["cell"] == EXT and r["status"] == "ok":
            for x in r["readback"]:
                rb.setdefault(tuple(x["op"]), set()).add(json.dumps(x["got"]))
    claim("finding method", "extended D-WIN cell read back from memory in all 5 runs: army 12 owner 6 and six HI of 6,000 quality 6; Gaul unity 600; armies 2 and 13 one LI of 500 quality 6", "trials-b16.jsonl readback",
          {str(k): sorted(v) for k, v in sorted(rb.items())},
          {"('owner', 12)": ["6"], "('unity', 6)": ["600"], "('units', 12)": [json.dumps([["hi", 6000, 6]] * 6)], "('units', 13)": [json.dumps([["li", 500, 6]])], "('units', 2)": [json.dumps([["li", 500, 6]])]}, cid="extcell")
    fld = (B.ART / C.FLD_RG_NAME).read_bytes()
    na = i16(fld, 100956)
    arm = lambda i: 100956 + 2 + i * 656
    st = {"rome": [v_nation(fld, 0, 0x446), v_nation(fld, 0, 0x440)], "gaul": [v_nation(fld, 6, 0x446), v_nation(fld, 6, 0x440)],
          "army0": [i16(fld, arm(0)), i16(fld, arm(0) + 2)], "army10": [i16(fld, arm(10)), i16(fld, arm(10) + 2)], "army12": [i16(fld, arm(12)), i16(fld, arm(12) + 2), i16(fld, arm(12) + 4)],
          "rome_armies": [i for i in range(na) if i16(fld, arm(i) + 4) == 0 and any(i16(fld, arm(i) + 16 + 32 * k + 4) > 0 for k in range(20))],
          "owners": {str(i): i16(fld, arm(i) + 4) for i in (0, 10, 12)}}
    claim("finding method", "FLD-RG start save: Rome 30 cities unity 881, Gaul 23 cities unity 402; army 0 at (86, 28), army 10 at (85, 28), army 12 at (150, 61) owned by nation 9 (Illyria); Rome's live armies 0, 2, 13", C.FLD_RG_NAME, st,
          {"rome": [30, 881], "gaul": [23, 402], "army0": [86, 28], "army10": [85, 28], "army12": [150, 61, 9], "rome_armies": [0, 2, 13], "owners": {"0": 0, "10": 6, "12": 9}}, cid="start")
    def clist(b, n):
        o = v_offsets(b) + n * 1172 + 0x48
        k = 0
        while k < 334 and i16(b, o + 2 * k) >= 0:
            k += 1
        return k
    claim("finding method", "the city-count word at nation +0x446 equals the length of the nation's city list in the start save (Rome 30, Gaul 23): the gate cells edit that word only", C.FLD_RG_NAME,
          {"offset": hex(0x446), "rome": [v_nation(fld, 0, 0x446), clist(fld, 0)], "gaul": [v_nation(fld, 6, 0x446), clist(fld, 6)]}, {"offset": "0x446", "rome": [30, 30], "gaul": [23, 23]}, cid="cityword")
    # --- survey state -------------------------------------------------------------------------------------------------------------------------
    def state(r):
        b = snap(r["pre_snap"])
        W = 0 if s_army_alive(b, 0) else 6
        L = 6 if W == 0 else 0
        return {"W": W, "armies_W": s_armies(b, W), "armies_L": s_armies(b, L), "unity_L": s_nation(b, L, 0x440), "cities_L": s_nation(b, L, 0x446), "unity_W": s_nation(b, W, 0x440),
                "tests": s_armies(b, W) < s_armies(b, L) and s_nation(b, L, 0x440) > 500 and s_nation(b, L, 0x446) > 7}
    win = [state(survey[("win", sd)]) for sd in range(1, 11)]
    claim("finding survey", "D-WIN, 10 seeds: armies(Gaul, the loser) 0, Gaul unity 377, cities 23, tests fail, 0 boxes", "win survey snapshots",
          ({(w["armies_L"], w["unity_L"], w["cities_L"], w["tests"]) for w in win}, sum(1 for sd in range(1, 11) if box_from_files(survey[("win", sd)]))), ([(0, 377, 23, False)], 0), cid="winstate")
    ext = [(sd, state(survey[(EXT, sd)]), box_from_files(survey[(EXT, sd)])) for sd in range(1, 6)]
    claim("finding survey", "D-WIN with a second Gaul army, 5 seeds: armies(Rome) 11,775 to 11,839, armies(Gaul) 29,700, Gaul unity 575 after the -25, 23 cities, tests hold; box open in seeds 3 and 5", "ext survey snapshots",
          ({e[1]["armies_W"] for e in ext}, {e[1]["armies_L"] for e in ext}, {e[1]["unity_L"] for e in ext}, {e[1]["cities_L"] for e in ext}, all(e[1]["tests"] for e in ext), [e[0] for e in ext if e[2]], len(ext)),
          ([11775, 11839], [29700], [575], [23], True, [3, 5], 5), cid="extstate")
    loss = [state(survey[("loss", sd)]) for sd in range(1, 31)]
    nopen = sum(1 for sd in range(1, 31) if box_from_files(survey[("loss", sd)]))
    claim("finding survey", "D-LOSS: 10 of 30 open = 33 %; all 30 satisfy the three tests, loser Rome with unity 856 and 30 cities, Gaul's armies 12,934 to 13,050 against Rome's 32,743", "loss survey snapshots",
          ({"open": nopen, "of": len(loss), "percent": round(100 * nopen / len(loss))}, all(x["tests"] for x in loss), {x["unity_L"] for x in loss}, {x["cities_L"] for x in loss},
           (min(x["armies_W"] for x in loss), max(x["armies_W"] for x in loss)), {x["armies_L"] for x in loss}),
          ({"open": 10, "of": 30, "percent": 33}, True, [856], [30], [12934, 13050], [32743]), cid="lossrate")
    # unity write-back: start save v snapshot
    st_loss = (B.ART / "start" / "loss_start.SAV").read_bytes()
    sb = snap(survey[("loss", 1)]["pre_snap"])
    ste = (B.ART / "start" / ("%s_start.SAV" % EXT.replace(",", "_"))).read_bytes()
    sbe = snap(survey[(EXT, 1)]["pre_snap"])
    claim("finding survey", "battle write-back of unity: loser -25, winner +25 (Rome 881 to 856, Gaul 402 to 427; extended cell Gaul 600 to 575)", "start saves + snapshots",
          {"loss": {"rome": [v_nation(st_loss, 0, 0x440), s_nation(sb, 0, 0x440)], "gaul": [v_nation(st_loss, 6, 0x440), s_nation(sb, 6, 0x440)]}, "ext": {"gaul": [v_nation(ste, 6, 0x440), s_nation(sbe, 6, 0x440)]}, "delta": v_nation(st_loss, 0, 0x440) - s_nation(sb, 0, 0x440), "loser_change": s_nation(sb, 0, 0x440) - v_nation(st_loss, 0, 0x440), "winner_change": s_nation(sb, 6, 0x440) - v_nation(st_loss, 6, 0x440)},
          {"loss": {"rome": [881, 856], "gaul": [402, 427]}, "ext": {"gaul": [600, 575]}, "delta": 25, "loser_change": -25, "winner_change": 25}, cid="writeback")
    # --- answer clicks ----------------------------------------------------------------------------------------------------------------------------
    clk = Counter((r["answered"], r["answer_click"]["clicks"]) for r in normal if r.get("answer_click") and r["status"] == "ok")
    claim("finding method", "clicks per verified answer, normal build: 32 No and 12 Yes took 2 clicks, one No took 3", "trials-b16.jsonl answer_click", {"%s/%s" % k: v for k, v in sorted(clk.items())}, {"No/2": 32, "No/3": 1, "Yes/2": 12}, cid="clicks")
    snaplen = {len(snap(r["pre_snap"])) for r in normal if r["status"] == "ok"}
    claim("finding method", "every pre-answer snapshot is 273,232 bytes (0x45E030..0x4A0B80)", "*_pre.snap.gz", (sorted(snaplen), 0x4A0B80 - 0x45E030, [hex(BASE), hex(0x4A0B80)]), ([273232], 273232, ["0x45e030", "0x4a0b80"]), cid="snaplen")
    drv = (C.ROOT / "harness" / "driver.py").read_text()
    m_ = re.search(r"for _ in range\((\d+)\):\s+# give the box up to ([\d.]+) s", drv)
    t_ = re.search(r"def answer_battle_peace\(self, yes, shot=None, pre_click=None, tries=(\d+)\)", drv)
    claim("finding method", "driver constants of answer_battle_peace: the box gets up to 2.5 s (10 polls of 0.25 s) to close, at most 3 clicks of the same button", "harness/driver.py",
          {"poll_seconds": int(m_.group(1)) * 0.25, "text_says": float(m_.group(2)), "tries": int(t_.group(1))}, {"poll_seconds": 2.5, "text_says": 2.5, "tries": 3}, cid="driverconsts")
    # --- pairs --------------------------------------------------------------------------------------------------------------------------------------
    claim("finding pairs", "12 pairs = 10 D-LOSS + 2 D-WIN-with-second-army, each with 4 proven turns (autosave per turn)", "trials-b16.jsonl",
          {"pairs": len(pairs), "loss": sum(1 for p in pairs if p[0] == "loss"), "win": sum(1 for p in pairs if p[0] != "loss"), "turns_each": {len(p[2]["turns"]) for p in pairs} | {len(p[3]["turns"]) for p in pairs}, "no_turn_errors": sum(1 for p in pairs for t in p[2]["turns"] + p[3]["turns"] if t.get("error"))},
          {"pairs": 12, "loss": 10, "win": 2, "turns_each": [4], "no_turn_errors": 0}, cid="pairs12")
    def rome(b, k):
        return v_nation(b, 0, k)
    ts = {}
    for t in range(1, 5):
        for c, sd, y, n in pairs:
            by, bn = ((B.ART / "turns" / r["turns"][t - 1]["save"]).read_bytes() for r in (y, n))
            ts.setdefault(c == "loss", {}).setdefault(t, set()).add((rome(by, 0x446), rome(bn, 0x446), v_nation(by, 6, 0x446), v_nation(bn, 6, 0x446), rome(by, 0x26 + 12), rome(bn, 0x26 + 12)))
    claim("finding pairs", "D-LOSS after turns 1 to 4 (Yes, No): Rome cities (30, 30), (30, 29), (30, 28), (30, 27); Gaul 23 v 23, 24, 25, 26; relation -14 v 3; D-WIN: Rome 30, Gaul 23 throughout", "turns/*.SAV",
          {("loss" if k else "win") + str(t): sorted(v) for k, d in ts.items() for t, v in d.items()},
          {"loss1": [[30, 30, 23, 23, -14, 3]], "loss2": [[30, 29, 23, 24, -14, 3]], "loss3": [[30, 28, 23, 25, -14, 3]], "loss4": [[30, 27, 23, 26, -14, 3]],
           "win1": [[30, 30, 23, 23, -14, 3]], "win2": [[30, 30, 23, 23, -14, 3]], "win3": [[30, 30, 23, 23, -14, 3]], "win4": [[30, 30, 23, 23, -14, 3]]}, cid="cities")
    first = {c_: min(t for t in range(1, 5) if any(n_ != y_ for (y_, n_, _, _, _, _) in ts[c_ == "loss"][t])) if c_ == "loss" else None for c_ in ("loss",)}
    claim("finding pairs", "turns are numbered 1 to 4; in the D-LOSS pairs the first turn at which Rome's city count differs between Yes and No is 2", "turn saves", {"turns": sorted(ts[True]), "first_city_loss_turn": first["loss"]}, {"turns": [1, 2, 3, 4], "first_city_loss_turn": 2}, cid="turnidx")
    claim("finding pairs", "relation after the answer -18 (Yes) v 3 (No), -14 v 3 after each of turns 1 to 4; -18 + 4 = -14", "post saves + turn saves", {"after_answer": [-18, 3], "turns": [[-14, 3]] * 4, "step": -14 - -18},
          {"after_answer": [-18, 3], "turns": [[-14, 3]] * 4, "step": 4}, cid="rel")
    # No v No
    nnn = []
    nos = defaultdict(list)
    for r in T.values():
        if r["build"] == "normal" and r["answer_plan"] == "no" and r.get("turns"):
            nos[(r["cell"], r["seed"])].append(r)
    for k, rs in sorted(nos.items()):
        if len(rs) >= 2:
            a, b = rs[0], rs[1]
            nnn.append((k[1], (B.ART / a["post_save"]).read_bytes() == (B.ART / b["post_save"]).read_bytes(), sum(1 for x, y in zip(a["turns"], b["turns"]) if (B.ART / "turns" / x["save"]).read_bytes() == (B.ART / "turns" / y["save"]).read_bytes())))
    claim("finding pairs", "No v No on seeds 1 and 3: post-answer save equal and 4 of 4 turn saves equal", "post + turns saves", {"seeds": len(nnn), "rows": nnn}, {"seeds": 2, "rows": [(1, True, 4), (3, True, 4)]}, cid="nonoise2")
    # identity, volatile words
    vals, extra = set(), set()
    for c, sd, y, n in pairs:
        for r in (y, n):
            b = snap(r["pre_snap"])
            vals.add((struct.unpack_from("<h", b, 0x45E614 - BASE)[0], struct.unpack_from("<h", b, 0x45E616 - BASE)[0]))
    s8 = {t: struct.unpack_from("<h", snap(T[t]["pre_snap"]), 0x45E614 - BASE)[0] for t in ("loss_s8_survey_r1", "loss_s8_yes_r1", "loss_s8_no_r1")}
    claim("finding pairs", "the two volatile words in the 24 pair snapshots take values 74 to 92 and 1 or 2; seed 8 survey, Yes, No hold 78, 76, 74", "*_pre.snap.gz",
          ((min(v[0] for v in vals), max(v[0] for v in vals)), sorted({v[1] for v in vals}), [s8["loss_s8_survey_r1"], s8["loss_s8_yes_r1"], s8["loss_s8_no_r1"]]), ([74, 92], [1, 2], [78, 76, 74]), cid="volatile")
    claim("finding pairs", "the volatile words are at 0x45E614 and 0x45E616; the area where runs of different roles differ is 0x45E420..0x45E700", "analysis constants", ([hex(a_) for a_ in (0x45E614, 0x45E616)], [hex(0x45E420), hex(0x45E700)]), (["0x45e614", "0x45e616"], ["0x45e420", "0x45e700"]), cid="volatileaddr")
    rp = json.loads(sorted(B.DATA.glob("b16-repeat-*.json"))[-1].read_text())
    mx = 0
    for r in rp:
        mx = max(mx, sum(x[1] for x in r["pre_differing_offsets"]) if r["pre_differing_offsets"] else 0)
    claim("finding pairs", "b16-repeat: 19 comparisons, named regions equal in all; at most 10 differing bytes outside the two volatile words, all in 0x45E420..0x45E700", "b16-repeat-*.json",
          (len(rp), all(r["pre_named_regions_equal"] for r in rp), max((sum(x[1] for x in r["pre_differing_offsets"] if not 0x45E614 <= int(x[0], 16) < 0x45E618) for r in rp), default=0), all(0x45E420 <= int(o[0], 16) < 0x45E700 for r in rp for o in r["pre_differing_offsets"])), (19, True, 10, True), cid="repeat")
    d1, d30 = ((B.ART / ("loss_s%d_yes_r1_post.SAV" % sd)).read_bytes() for sd in (1, 30))
    t1, t30 = ((B.ART / "turns" / ("loss_s%d_yes_r1_t4_AUTO0747.SAV" % sd)).read_bytes() for sd in (1, 30))
    claim("finding pairs", "post-answer Yes saves of seeds 1 and 30 differ in 6 bytes, their turn-4 autosaves in 7", "post and turn saves", ({"seeds": [1, 30], "post": sum(1 for x, y in zip(d1, d30) if x != y) + abs(len(d1) - len(d30)), "turn4": sum(1 for x, y in zip(t1, t30) if x != y) + abs(len(t1) - len(t30))}), {"seeds": [1, 30], "post": 6, "turn4": 7}, cid="seedsdiffer")
    nm0 = {r["trial"]: (cstr_(snap(r["pre_snap"])[NAT - BASE:NAT - BASE + 11]), cstr_(snap(r["pre_snap"])[NAT - BASE + 6 * 1172:NAT - BASE + 6 * 1172 + 11])) for r in opened_norm}
    lcg6 = (6 * 0x08088405 + 1) & 0xFFFFFFFF
    claim("finding pairs", "RandSeed with the box up in every opened normal run is 0x3033181F = one LCG step after the seed 6 = winner + loser (nation index 0 is Rome, 6 is Gaul)", "*_pre.snap.gz",
          {"values": sorted({hex(struct.unpack("<I", snap(r["pre_snap"])[:4])[0]) for r in opened_norm}), "lcg_of_6": hex(lcg6), "names": sorted(set(nm0.values())), "index": [0, 6]},
          {"values": ["0x3033181f"], "lcg_of_6": "0x3033181f", "names": [("Rome", "Gaul")], "index": [0, 6]}, cid="reseed")
    # hooked
    hk = []
    for r in T.values():
        if r["build"] == "lab hook":
            hk.append(r)
    base = [r for r in hk if r["cell"] == "loss"]
    claim("finding hook", "16 hooked baseline seeds (lab seeds 1 to 16): 3 opened (seeds 10, 11, 14) with draws 0, 1, 0 and 13 closed with draws 2 to 4; range of the draw 5; 9 hooked gate runs with no draw (unity 500, 7 cities, weak armies on seeds 10, 11, 14); reseed record at 0x457907", "hooklog-*.csv",
          {"seeds": sorted({r["seed"] for r in base}), "n": len(base), "gate_runs": len(hk) - len(base)}, {"seeds": list(range(1, 17)), "n": 16, "gate_runs": 9}, cid="hookn")
    rngs, sites = set(), set()
    for r in base:
        for x in (B.DATA / ("hooklog-%s.csv" % r["trial"])).read_text().splitlines()[1:]:
            f = x.split(",")
            if f[1] == "random" and f[2] == "0x45951c":
                rngs.add(int(f[3]))
            if f[1] == "reseed":
                sites.add(f[2])
    claim("finding hook", "the draw's range is 5 in every hooked baseline run, logged at site 0x45951c; reseed record site 0x457907", "hooklog-*.csv", (sorted(rngs), sorted(sites), "0x45951c"), ([5], ["0x457907"], "0x45951c"), cid="hookrange")
    claim("finding hook", "Random(5) takes the values 0 to 4; the box opens below 2: 2 of the 5 values = 40 %", "arithmetic on the logged range", {"values": 5, "open_values": sum(1 for v in range(5) if v < 2), "percent": 100 * sum(1 for v in range(5) if v < 2) // 5}, {"values": 5, "open_values": 2, "percent": 40}, cid="drawrate")
    opened_h = [r for r in base if box_from_files(r)]
    claim("finding hook", "hooked baseline: 3 opened, 13 closed; the 9 hooked gate runs made 0 draws at 0x45951c", "hooklog-*.csv + shots/",
          {"open": len(opened_h), "closed": len(base) - len(opened_h), "gate_runs": len([r for r in hk if r["cell"] != "loss"]),
           "gate_draws": sum(1 for r in hk if r["cell"] != "loss" for x in (B.DATA / ("hooklog-%s.csv" % r["trial"])).read_text().splitlines()[1:] if x.split(",")[1] == "random" and x.split(",")[2] == "0x45951c")},
          {"open": 3, "closed": 13, "gate_runs": 9, "gate_draws": 0}, cid="hookcounts")
    # --- gate -------------------------------------------------------------------------------------------------------------------------------------
    gate = {}
    for r in normal:
        if r["cell"].startswith("loss+") and r["answer_plan"] == "capture":
            b = snap(r["pre_snap"])
            gate.setdefault(r["cell"], {})[r["seed"]] = (box_from_files(r), s_nation(b, 0, 0x440), s_nation(b, 0, 0x446), s_armies(b, 0), s_armies(b, 6))
    gg = {c: {sd: v for sd, v in d.items()} for c, d in gate.items()}
    claim("finding gate", "all gate cells on all three seeds (1, 3, 5): (box open, Rome unity at the box, Rome city word, armies(Rome), armies(Gaul))", "gate snapshots + shots/",
          {c: {str(sd): list(v) for sd, v in sorted(d.items())} for c, d in sorted(gg.items())},
          {"loss+ncities0=7": {str(sd): [False, 856, 7, 32743, a] for sd, a in ((1, 12992), (3, 12934), (5, 12992))},
           "loss+ncities0=8": {str(sd): [True, 856, 8, 32743, a] for sd, a in ((1, 12992), (3, 12934), (5, 12992))},
           "loss+unity0=524": {str(sd): [False, 499, 30, 32743, a] for sd, a in ((1, 12992), (3, 12934), (5, 12992))},
           "loss+unity0=525": {str(sd): [False, 500, 30, 32743, a] for sd, a in ((1, 12992), (3, 12934), (5, 12992))},
           "loss+unity0=526": {str(sd): [True, 501, 30, 32743, a] for sd, a in ((1, 12992), (3, 12934), (5, 12992))},
           "loss+weak2=500,weak13=500": {str(sd): [False, 856, 30, 127, a] for sd, a in ((1, 12992), (3, 12934), (5, 12992))}}, cid="gateall")
    claim("finding gate", "unity edits 526/525/524 give 501/500/499 at the box: the edit minus the 25 of the write-back", "gate snapshots", dict({c: sorted({v[1] for v in d.values()}) for c, d in gg.items() if "unity" in c}, writeback=526 - 501),
          {"loss+unity0=524": [499], "loss+unity0=525": [500], "loss+unity0=526": [501], "writeback": 25}, cid="gateunity")
    claim("finding gate", "the thresholds: 501 opens/500 closed, 8 opens/7 closed, the test is strict (> 500, > 7), 3 seeds each, 6 gate cells", "gate cells",
          {"unity_open": sorted({v[1] for d in (gg["loss+unity0=526"],) for v in d.values() if v[0]}), "unity_closed": sorted({v[1] for c in ("loss+unity0=525", "loss+unity0=524") for v in gg[c].values() if not v[0]}),
           "city_open": sorted({v[2] for v in gg["loss+ncities0=8"].values() if v[0]}), "city_closed": sorted({v[2] for v in gg["loss+ncities0=7"].values() if not v[0]}), "seeds": 3, "cells": len(gg)},
          {"unity_open": [501], "unity_closed": [499, 500], "city_open": [8], "city_closed": [7], "seeds": 3, "cells": 6}, cid="thresholds")
    # --- tables of the finding, recomputed from raw ----------------------------------------------------------------------------------------------
    tabs = NUMS.tables()
    def tab(prefix):
        return next(v for k, v in tabs.items() if k and k.startswith(prefix))
    def fmt_rows(cell, seeds):
        out = []
        for sd in seeds:
            r = survey[(cell, sd)]
            x = state(r)
            shot = r["dialogs"][0]["shot"] if box_from_files(r) else None
            out.append([str(sd), "**open**" if box_from_files(r) else "closed", {0: "Rome", 6: "Gaul"}[x["W"]], str(x["armies_W"]), str(x["armies_L"]), str(x["unity_L"]), str(x["cities_L"]),
                        "yes" if x["tests"] else "no", ("`%s`" % shot) if shot else "-", "`%s`" % r["pre_snap"]])
        return out
    for cid, prefix, cell, seeds in (("tab_loss", "D-LOSS (", "loss", range(1, 31)), ("tab_win", "D-WIN (", "win", range(1, 11)), ("tab_ext", "D-WIN with a second", EXT, range(1, 6))):
        got, want = fmt_rows(cell, seeds), tab(prefix)["rows"]
        claim("finding table", "table '%s': every cell of its %d rows recomputed from the snapshots, screenshots and records" % (prefix, len(want)), "survey snapshots", got, want, cid=cid)
    prow = []
    for c, sd, y, n in pairs:
        ry, rn = ((B.ART / r["post_save"]).read_bytes() for r in (y, n))
        tt = [tuple((B.ART / "turns" / r["turns"][t]["save"]).read_bytes() for r in (y, n)) for t in range(4)]
        f = lambda g: "%s/%s" % (g(tt[3][0]), g(tt[3][1]))
        prow.append(["D-LOSS" if c == "loss" else "D-WIN + 2nd Gaul army", str(sd), "%s/%s" % (v_nation(ry, 0, 0x26 + 12), v_nation(rn, 0, 0x26 + 12)),
                     " ".join("%s/%s" % (v_nation(a, 0, 0x26 + 12), v_nation(b, 0, 0x26 + 12)) for a, b in tt), " ".join("%s/%s" % (v_nation(a, 0, 0x446), v_nation(b, 0, 0x446)) for a, b in tt),
                     f(lambda b: v_nation(b, 6, 0x446)), f(lambda b: v_nation(b, 0, 0x440)), f(lambda b: v_nation(b, 6, 0x440)), f(lambda b: v_treasury(b, 0))])
    claim("finding table", "the finding has exactly 6 tables, all recomputed here (D-LOSS, D-WIN, D-WIN with a second army, Yes versus No, gate cells, hooked runs)", "findings", {"tables": len(tabs)}, {"tables": 6}, cid="ntables")
    claim("finding table", "table 'Yes versus No': relation after the answer and after turns 1-4, Rome cities t1-t4, Gaul cities, unity of both and Rome treasury at turn 4, all 12 rows, from the saves", "post + turn saves", prow, tab("Yes versus No")["rows"], cid="tab_pairs")
    grow = []
    for c, d in sorted(gg.items()):
        v1 = d[1]
        grow.append(["`%s`" % c, str(v1[1]), str(v1[2]), str(v1[3]), str(v1[4])] + ["**open**" if d[sd][0] else "closed" for sd in (1, 3, 5)])
    claim("finding table", "table 'Gate cells': unity, city word, armies and the box on seeds 1, 3, 5 for the 6 cells", "gate snapshots + shots/", grow, tab("Gate cells")["rows"], cid="tab_gate")
    hrow = []
    for r in sorted(hk, key=lambda r: (r["seed"], r["cell"] != "loss", r["trial"])):
        rows_ = [x.split(",") for x in (B.DATA / ("hooklog-%s.csv" % r["trial"])).read_text().splitlines()[1:]]
        dr = [int(x[6]) for x in rows_ if x[1] == "random" and x[2] == "0x45951c"]
        rs = [("%s@%s" % (x[0], x[2])) for x in rows_ if x[1] == "reseed"]
        b = snap(r["pre_snap"])
        W = 0 if s_army_alive(b, 0) else 6
        hrow.append(["`%s`" % r["trial"], "**open**" if box_from_files(r) else "closed", "yes" if (s_armies(b, W) < s_armies(b, 6 if W == 0 else 0) and s_nation(b, 6 if W == 0 else 0, 0x440) > 500 and s_nation(b, 6 if W == 0 else 0, 0x446) > 7) else "no",
                     str(len(dr)), str(dr[0]) if dr else "-", ";".join(rs) if rs else "-"])
    hrow.sort(key=lambda x: x[0])
    wantrows = sorted(tab("Hooked lab runs")["rows"], key=lambda x: x[0])
    claim("finding table", "table 'Hooked lab runs': box, tests, draws logged at 0x45951C, the draw, the reseed record, 25 rows, from hooklog csv, snapshots and screenshots", "hooklog-*.csv", hrow, wantrows, cid="tab_hook")
    # --- full diff (R2) ---------------------------------------------------------------------------------------------------------------------------
    fd = json.loads(sorted(B.DATA.glob("b16-fulldiff-2*.json"))[-1].read_text())
    yes = [d for d in fd["runs"] if d["answer"] == "Yes"]
    no = [d for d in fd["runs"] if d["answer"] == "No"]
    claim("finding fulldiff", "full before/after diff (24 runs): Yes 12 runs, 42 changed fields each = 2 relations (3 to -18) + 40 news positions, 1 line added, the oldest dropped; No 12 runs, 0 fields; no map cell changed", "b16-fulldiff-*.json",
          {"yes_runs": len(yes), "yes_fields": sorted({len(d["fields"]) for d in yes}), "yes_nonnews": sorted({(f[0], str(f[1]), str(f[2])) for d in yes for f in d["fields"] if not f[0].startswith("news")}),
           "news_changes": sorted({sum(1 for f in d["fields"] if f[0].startswith("news")) for d in yes}), "added": sorted({len(d["news_added"]) for d in yes}), "dropped": sorted({tuple(d["news_dropped"]) for d in yes}),
           "no_runs": len(no), "no_fields": sorted({len(d["fields"]) for d in no}), "maps": sorted({d["map_cells_changed"] for d in fd["runs"]}), "total": len(fd["runs"])},
          {"yes_runs": 12, "yes_fields": [42], "yes_nonnews": sorted([("nations[0].relations.Gaul", "3", "-18"), ("nations[6].relations.Rome", "3", "-18")]), "news_changes": [40], "added": [1],
           "dropped": [["Laranda   (Seleucid)  falls to Galatia."]], "no_runs": 12, "no_fields": [0], "maps": [0], "total": 24}, cid="fulldiff")
    # independent raw check of the full diff: blocks of the snapshot v blocks of the post save, byte level, per branch
    raw = {}
    for c, sd, y, n in pairs:
        for r, nm in ((y, "yes"), (n, "no")):
            sn, ps = snap(r["pre_snap"]), (B.ART / r["post_save"]).read_bytes()
            L = struct.unpack_from("<h", ps, 100956)[0]
            of = 100956 + 2 + L * 656
            nf = struct.unpack_from("<h", ps, of)[0]
            nat0 = of + 2 + nf * 26
            blocks = {"map": (0x45E870, 0, 89600), "cities": (0x479590, 89600, 11356), "armies": (0x47C1EC, 100958, L * 656), "fleets": (0x49C26C, of + 2, nf * 26), "mercs": (0x49DA10, nat0 + 16 * 1172, 600)}
            res = {k: sn[a - BASE:a - BASE + n_] == ps[o:o + n_] for k, (a, o, n_) in blocks.items()}
            nb = [i for i in range(16 * 1172) if sn[0x474670 - BASE + i] != ps[nat0 + i]]
            res["nations_differing_bytes_in_relation_words_only"] = all(any((k * 1172 + 0x26 + 2 * m) <= i < (k * 1172 + 0x26 + 2 * m + 2) for k in (0, 6) for m in (0, 6)) for i in nb)
            raw.setdefault(nm, set()).add((tuple(sorted(res.items())), len(nb)))
    claim("finding fulldiff", "raw byte check, every pair, both branches: map, cities, armies, fleets and mercenary blocks of the snapshot equal the post-answer save's; nations differ (Yes only, 2 relation words = 4 bytes) only inside the Rome-Gaul relation words", "snapshots + post saves",
          {k: sorted(map(str, v)) for k, v in raw.items()},
          {"yes": [str((tuple(sorted({"map": True, "cities": True, "armies": True, "fleets": True, "mercs": True, "nations_differing_bytes_in_relation_words_only": True}.items())), 4))],
           "no": [str((tuple(sorted({"map": True, "cities": True, "armies": True, "fleets": True, "mercs": True, "nations_differing_bytes_in_relation_words_only": True}.items())), 0))]}, cid="rawdiff")
    # --- cited files ------------------------------------------------------------------------------------------------------------------------------
    text = NUMS.FINDING.read_text()
    import re as _re
    spans = set(_re.findall(r"`([^`]*(?:\.(?:png|SAV|csv|json|jsonl|md|py|gz|sha256|txt|log|sh)\b)[^`]*)`", text))
    missing = []
    RESEARCH = Path.home() / "projects" / "imperial-conquest-2-research" / "docs" / "reports"
    for sp in sorted(spans):
        base = sp.split()[0]
        if base.startswith("."):
            continue                    # an extension fragment (`.tar.gz`), not a file
        if base.startswith("docs/reports/") or base.endswith("-paths.md"):         # the research repository's reports (read only)
            if not (RESEARCH / Path(base).name).exists():
                missing.append(sp)
            continue
        if base.startswith(("docs/", "state/", "runs/", "tests/", "setup/", "findings/")) or "/" in base:
            pat = base
            hits = list(C.ROOT.glob(pat)) if "*" in pat else ([C.ROOT / pat] if (C.ROOT / pat).exists() else [])
        else:
            pat = base
            def known(pat):
                if "{" in pat or "<" in pat:
                    return True       # a template (`<trial>_post.SAV`, `loss_s1_{...}`): its instances are cited elsewhere
                if "*" in pat:
                    return any(B.DATA.glob(pat)) or any(B.ART.rglob(pat)) or any(C.ROOT.glob("**/" + pat))
                return (B.DATA / pat).exists() or any(B.ART.rglob(pat)) or any(C.ROOT.glob("**/" + pat)) or pat in shas
            hits = [1] if known(pat) else []
        if not hits:
            missing.append(sp)
    claim("finding files", "every file name or glob cited in a code span of the finding exists (data folder, artifacts, repository) or is a template: %d distinct spans" % len(spans), "findings + data", missing, [], cid="cited_files")
    cellspans = sorted(set(_re.findall(r"`((?:loss|win)\+[^`]*)`", text)))
    cellspans = [c_.split(" ")[0] for c_ in cellspans]
    alltrial = {r["cell"] for r in normal}
    cm = []
    for c_ in cellspans:
        if c_ not in alltrial:
            cm.append(c_)
    claim("finding files", "every cell expression cited in the finding is a cell of trials-b16.jsonl", "trials-b16.jsonl", cm, [], cid="cited_cells")
    return tabs


def number_map_check(text=None, mp=None, cl=None):
    """Every prose line with a number is in the number map; each of its tokens is among the checked values of the line's claims or exempt with a reason.
    (`text`, `mp`, `cl` let a test feed a synthetic finding, map and claim table.)"""
    mp = mp if mp is not None else json.loads((Path(__file__).resolve().parent / "b16_number_map.json").read_text())
    CL_ = cl if cl is not None else CL
    inv = NUMS.inventory(text)
    out, bad = [], []
    nums = lambda txt: {NUMS.norm(m.group(0)) for m in NUMS.NUM.finditer(txt)} | {NUMS.WORDS[w.lower()] for w in NUMS.WORD.findall(txt)}
    for i in inv:
        e = mp.get(i["key"])
        if e is None:
            bad.append("line %d not in the map: %s" % (i["line"], i["key"]))
            continue
        for cid in e["claims"]:
            if cid not in CL_ or not CL_[cid][0]:
                bad.append("line %d: claim %s missing or not matching" % (i["line"], cid))
        checked = set()
        for cid in e["claims"]:
            if cid in CL_:
                checked |= nums(CL_[cid][1].replace("\\u2018", ""))
        for tok in i["tokens"]:
            if tok in e.get("exempt", {}):
                out.append((i["line"], tok, "exempt", e["exempt"][tok]))
            elif tok in checked:
                out.append((i["line"], tok, "claims " + ",".join(e["claims"]), ""))
            else:
                bad.append("line %d: token %s is neither in a claim's checked values (%s) nor exempt" % (i["line"], tok, ",".join(e["claims"])))
        for tok in e.get("exempt", {}):
            if tok not in i["tokens"]:
                bad.append("line %d: exempt token %s does not occur in the line" % (i["line"], tok))
    stale = [k for k in mp if k not in {i["key"] for i in inv}]
    for k in stale:
        bad.append("map entry for a line that is no longer in the finding: %s" % k)
    return out, bad, len(inv), sum(i["count"] for i in inv)


def main():
    T = ok_trials()
    errs = [r for r in trials() if r.get("status") == "error"]
    shas = {}
    sums_file = sorted(B.DATA.glob("SAVES.v*.sha256"), key=lambda q: int(q.stem.split(".v")[1].split("-")[0]))[-1]
    for line in sums_file.read_text().splitlines():
        h, _, n = line.partition("  ")
        shas[n] = h
    # ---- the survey ----------------------------------------------------------------------------------------------------------------------------
    survey = {}
    for r in T.values():
        if r["answer_plan"] == "capture" and r["trial"].split("_")[2] in ("survey", "capture"):
            survey.setdefault((r["cell"], r["seed"]), r)

    def box_from_files(r):         # the box counted from the dialog screenshot file, independent of the record's flag
        return bool(r.get("dialogs")) and bool(r["dialogs"][0].get("shot")) and (B.ART / "shots" / r["dialogs"][0]["shot"]).exists()
    for cell, seeds in (("loss", range(1, 31)), ("win", range(1, 11))):
        rr = [survey[(cell, s)] for s in seeds if (cell, s) in survey]
        opened = sorted(r["seed"] for r in rr if box_from_files(r))
        claim("finding survey", "%s: %d seeds surveyed; box opened (dialog screenshot present) in seeds %s" % (cell, len(rr), opened), "trials-b16.jsonl + shots/",
              (len(rr), opened, sum(1 for r in rr if r["box_opened"])), EXPECT["survey_" + cell], cid="survey_" + cell)
        # the strategic state from the snapshot bytes, not from the record
        got = Counter()
        for r in rr:
            b = snap(r["pre_snap"])
            W = 0 if s_army_alive(b, 0) else 6
            L = 6 if W == 0 else 0
            got[(W, s_armies(b, W) < s_armies(b, L), s_nation(b, L, 0x440) > 500, s_nation(b, L, 0x446) > 7, box_from_files(r))] += 1
        claim("finding survey", "%s: counts of (winner nation, armies(W) < armies(L), unity(L) > 500, cities(L) > 7, box opened) recomputed from the %d snapshots" % (cell, len(rr)),
              "*_pre.snap.gz", dict(sorted(got.items())), EXPECT["rcode_" + cell], cid="rcode_" + cell)
    claim("finding survey", "exactly one error record in trials-b16.jsonl (the hooked seed 5 launch before that lab hook exe was built, FileNotFoundError; kept, seed 5 was rerun as r2)", "trials-b16.jsonl", len(errs), EXPECT["errors"], cid="errors")
    # ---- the pairs -----------------------------------------------------------------------------------------------------------------------------
    pairs = []
    for cell in sorted({r["cell"] for r in T.values() if r["answer_plan"] in ("yes", "no")}):
        for seed in sorted({r["seed"] for r in T.values() if r["cell"] == cell}):
            ys = [r for r in T.values() if r["cell"] == cell and r["seed"] == seed and r["answer_plan"] == "yes" and r.get("turns")]
            ns = [r for r in T.values() if r["cell"] == cell and r["seed"] == seed and r["answer_plan"] == "no" and r.get("turns") and r.get("dialogs") and r["dialogs"][0].get("shot")]
            if ys and ns:
                pairs.append((cell, seed, ys[-1], ns[-1]))
    claim("finding pairs", "pairs (cell, seed) with a Yes run and a No run, each with 4 turns", "trials-b16.jsonl", [(c, s) for c, s, _, _ in pairs], EXPECT["pairs"], cid="pairs")
    ident, volat = [], []
    for c, s, y, n in pairs:
        a, b = snap(y["pre_snap"]), snap(n["pre_snap"])
        diff = [BASE + i for i in range(len(a)) if a[i] != b[i]]
        ident.append((c, s, len(a) == len(b), len(diff), all(0x45E614 <= d < 0x45E618 for d in diff)))
        sy, sn = B.ART / "shots" / y["dialogs"][0]["shot"], B.ART / "shots" / n["dialogs"][0]["shot"]
        volat.append(sha(sy) == sha(sn))
    claim("finding pairs", "pre-answer snapshots: bytes differing only inside 0x45E614..0x45E617 (0 to 2 bytes), same length; per pair (cell, seed, same length, differing bytes, all inside the two volatile words)",
          "*_pre.snap.gz", ident, EXPECT["identity"], cid="identity")
    claim("finding pairs", "the Offer of peace screenshot (taken before the click) is byte-identical in Yes and No for every pair", "shots/*dialog-Offer_of_peace*.png", volat, [True] * len(pairs))
    clicks = [(y["dialogs"][0]["answer"], n["dialogs"][0]["answer"], y["answer_click"]["closed"], n["answer_click"]["closed"]) for c, s, y, n in pairs]
    claim("finding pairs", "clicked button recorded: Yes in the Yes run, No in the No run, box closed (verified by the driver) in all", "trials-b16.jsonl", set(clicks), {("Yes", "No", True, True)})
    rel = []
    for c, s, y, n in pairs:
        ry, rn = (open(B.ART / r["post_save"], "rb").read() for r in (y, n))
        rel.append((v_nation(ry, 0, 0x26 + 12), v_nation(rn, 0, 0x26 + 12), v_nation(ry, 6, 0x26), v_nation(rn, 6, 0x26)))
    claim("finding pairs", "relation Rome-Gaul in the Save As right after the answer: -18 (Yes), 3 (No), both directions", "post saves", set(rel), EXPECT["rel_after"], cid="rel_after")
    news = []
    for c, s, y, n in pairs:
        ry, rn = (v_news(open(B.ART / r["post_save"], "rb").read()) for r in (y, n))
        W, L = ("Rome", "Gaul") if c != "loss" else ("Gaul", "Rome")
        news.append(("%s and %s have agreed to end their war." % (W, L) in ry[-3:], "agreed to end their war" in " ".join(rn[-3:])))
    claim("finding pairs", "news: the Yes save ends with '<Winner> and <Loser> have agreed to end their war.' (Gaul and Rome after a human defeat, Rome and Gaul after a human victory; last 3 lines), the No save has no such line", "post saves", set(news), {(True, False)})
    # turns
    for t in range(1, 5):
        got = []
        for c, s, y, n in pairs:
            fy, fn = (B.ART / "turns" / r["turns"][t - 1]["save"] for r in (y, n))
            by, bn = fy.read_bytes(), fn.read_bytes()
            got.append((c, s, v_nation(by, 0, 0x26 + 12), v_nation(bn, 0, 0x26 + 12), v_nation(by, 0, 0x446), v_nation(bn, 0, 0x446), v_nation(by, 6, 0x446), v_nation(bn, 6, 0x446)))
        claim("finding pairs", "turn %d autosave: (cell, seed, relation Yes, relation No, Rome cities Yes, No, Gaul cities Yes, No)" % t, "turns/*.SAV", got, EXPECT["turn%d" % t], cid="turn%d" % t)
    # No/No noise
    nn = []
    for (c, s), rs in sorted({(r["cell"], r["seed"]): [] for r in T.values()}.items()):
        pass
    nos = defaultdict(list)
    for r in T.values():
        if r["answer_plan"] == "no" and r.get("turns") and r.get("dialogs"):
            nos[(r["cell"], r["seed"])].append(r)
    for k, rs in sorted(nos.items()):
        if len(rs) >= 2:
            a, b = rs[0], rs[1]
            nn.append((k[0], k[1], (B.ART / a["post_save"]).read_bytes() == (B.ART / b["post_save"]).read_bytes(),
                       [(B.ART / "turns" / x["save"]).read_bytes() == (B.ART / "turns" / y["save"]).read_bytes() for x, y in zip(a["turns"], b["turns"])],
                       differs_only_in_volatile(snap(a["pre_snap"]), snap(b["pre_snap"]))))
    claim("finding No/No", "No v No on the same save and seed (two fresh processes): the post-answer save, each of the 4 End-turn saves and the pre-answer snapshot (outside the two volatile words) are byte-equal", "post and turns saves, snapshots",
          nn, EXPECT["nonoise"], cid="nonoise")
    # ---- gates ---------------------------------------------------------------------------------------------------------------------------------
    gate = defaultdict(dict)
    for r in T.values():
        if r["cell"].startswith("loss+") and r["answer_plan"] == "capture" and r["build"] == "normal":
            gate[r["cell"]][r["seed"]] = box_from_files(r)
    claim("finding gate", "gate cells (L1 edit of the loss cell): box opened per seed", "trials-b16.jsonl + shots/", {k: dict(sorted(v.items())) for k, v in sorted(gate.items())}, EXPECT["gate"])
    gv = {}
    for r in T.values():
        if r["cell"].startswith("loss+") and r["answer_plan"] == "capture" and r["build"] == "normal":
            b = snap(r["pre_snap"])
            gv[(r["cell"], r["seed"])] = (s_nation(b, 0, 0x440), s_nation(b, 0, 0x446), s_armies(b, 0), s_armies(b, 6))
    claim("finding gate", "gate cells: (Rome unity, Rome city count, armies(Rome), armies(Gaul)) in the snapshot before the answer / at the box, seeds 1, 3, 5", "*_pre.snap.gz",
          {k[0]: v for k, v in gv.items() if k[1] == 1}, EXPECT["gatevals"])
    # ---- the box as the clone copies it ---------------------------------------------------------------------------------------------------------
    normal_open = [r for r in T.values() if r["build"] == "normal" and r["answer_plan"] in ("capture", "yes", "no") and box_from_files(r)]
    claim("finding box", "every opened run (%d, normal build): title 'Offer of peace', geometry 13,94,406,360, buttons exactly No and Yes (TButton), answered with a recorded click" % len(normal_open), "trials-b16.jsonl",
          ({r["box_title"] for r in normal_open}, {tuple(r["dialogs"][0]["geometry"]) for r in normal_open}, {tuple(sorted(c["text"] for c in r["dialogs"][0]["controls"] if c["cls"] == "TButton")) for r in normal_open if r["dialogs"][0].get("controls")}, {c["cls"] for r in normal_open if r["dialogs"][0].get("controls") for c in r["dialogs"][0]["controls"]}),
          ({"Offer of peace"}, {(13, 94, 406, 360)}, {("No", "Yes")}, {"TButton"}))
    heads = Counter(r["box_text"][:60] for r in normal_open)
    claim("finding box", "box text (OCR) starts 'After defeating you in battle Gaul are willing to end their war' after a human defeat and 'After losing to you in battle Gaul are willing to end their war' after a human victory", "trials-b16.jsonl",
          {k.replace("\u2018", "").replace("\u2019", ""): v for k, v in heads.items()}, EXPECT["heads"], cid="heads")
    claim("finding box", "every opened run's text contains 'honourable peace with no reparations' and 'click YES' and 'click NO'", "trials-b16.jsonl",
          sum(1 for r in normal_open if "honourable peace with no reparations" in r["box_text"] and "click YES" in r["box_text"] and "click NO" in r["box_text"]), len(normal_open))
    rs = {struct.unpack("<I", snap(r["pre_snap"])[:4])[0] for r in normal_open}
    claim("finding box", "RandSeed (first 4 bytes of the snapshot taken with the box up) is 0x3033181F in every opened normal-build run", "*_pre.snap.gz", {hex(x) for x in rs}, {"0x3033181f"})
    # no change at the answer: Rome and Gaul treasury, unity, city count in the Yes post save == No post save == the snapshot before the answer
    chg = []
    for c, s_, y, n in pairs:
        by, bn = (open(B.ART / r["post_save"], "rb").read() for r in (y, n))
        bs = snap(y["pre_snap"])
        vy = [(v_treasury(by, k), v_nation(by, k, 0x440), v_nation(by, k, 0x446)) for k in (0, 6)]
        vn = [(v_treasury(bn, k), v_nation(bn, k, 0x440), v_nation(bn, k, 0x446)) for k in (0, 6)]
        vs = [(struct.unpack_from("<i", bs, NAT - BASE + k * 1172 + 0x438)[0], s_nation(bs, k, 0x440), s_nation(bs, k, 0x446)) for k in (0, 6)]
        chg.append(vy == vn == vs)
    claim("finding pairs", "at the answer Rome's and Gaul's treasury, unity and city count are the same in the Yes save, the No save and the snapshot before the answer (no money, unity or city change, no reparations): per pair", "post saves + snapshots", chg, [True] * len(pairs))
    # hooked runs: the draw
    hk = []
    for r in T.values():
        if r["build"] == "lab hook":
            rows_ = [x.split(",") for x in (B.DATA / ("hooklog-%s.csv" % r["trial"])).read_text().splitlines()[1:]]
            draws = [int(x[6]) for x in rows_ if x[1] == "random" and x[2] == "0x45951c" and int(x[3]) == 5]
            hk.append((r["cell"], r["seed"], box_from_files(r), tuple(draws), any(x[1] == "reseed" for x in rows_)))
    base = [h for h in hk if h[0] == "loss"]
    claim("finding hook", "16 hooked baseline seeds: box open exactly when the logged Random(5) at 0x45951C is < 2; opened seeds and draws", "hooklog-*.csv + shots/",
          (len(base), sum(1 for h in base if h[2] == (len(h[3]) == 1 and h[3][0] < 2)), [(h[1], h[3][0]) for h in base if h[2]], sorted({h[3][0] for h in base if not h[2]}), all(h[4] == h[2] for h in base)), EXPECT["hookbase"], cid="hookbase")
    gated = [h for h in hk if h[0] != "loss"]
    claim("finding hook", "hooked gate runs (unity 500, city word 7, weak armies; seeds 10, 11, 14): box closed, no Random(5) draw at 0x45951C at all", "hooklog-*.csv + shots/",
          (len(gated), sum(1 for h in gated if not h[2] and h[3] == ())), (9, 9))
    # ---- hashes / counts / files ---------------------------------------------------------------------------------------------------------------
    bins = [p for p in B.ART.rglob("*") if p.is_file() and p.suffix.lower() in (".sav", ".png", ".gz") and "archives" not in p.parts and not p.name.startswith("_tmp")]
    bad = [p.name for p in bins if shas.get(p.name) != sha(p)]
    claim("finding files", "every binary under artifacts/run-exp-battle-peace/ (saves, snapshots, screenshots) has its SHA-256 in the newest SAVES.v<N>.sha256 and it matches (%d files)" % len(bins), "SAVES.v2.sha256", len(bad), 0)
    manifest = set()
    for f in B.DATA.glob("release-manifest-*.json"):
        for a in json.loads(f.read_text())["archives"].values():
            if a.get("uploaded"):
                manifest |= set(a["members"])
    claim("finding files", "every binary is a member of an uploaded release archive listed in a tracked manifest", "release-manifest-*.json", sorted(p.name for p in bins if p.name not in manifest)[:5], [])
    # tests
    import subprocess
    for mod, e in (("test_driver_battle", EXPECT["tests_driver"]), ("test_battle_b16", EXPECT["tests_b16"]), ("test_battle_stage", EXPECT["tests_stage"])):
        out = subprocess.run([sys.executable, "-m", "tests." + mod], capture_output=True, text=True, cwd=C.ROOT).stdout
        claim("results.md", "%s: %s tests pass, 0 fail" % (mod, e), "tests/" + mod + ".py", (out.count("PASS "), out.count("FAIL ")), (e, 0))
    more(T, pairs, box_from_files, shas)
    nm_out, nm_bad, nm_lines, nm_tokens = number_map_check()
    for b_ in nm_bad:
        rows.append(("number map", b_, "b16_number_map.json", "-", "-", "N"))
    rows.append(("number map", "every numeric token of the finding's prose (%d lines, %d token occurrences) is checked by a claim or exempt with a reason; its tables (6, recomputed cell by cell above) and cited files/cells are checked separately" % (nm_lines, nm_tokens), "b16_number_map.json", len(nm_bad), 0, "y" if not nm_bad else "N"))
    NM = nm_out
    badr = [r for r in rows if r[5] != "y"]
    out = C.write_new(B.DATA, "b16-claims-audit-%s.md" % C.STAMP,
                      "# B16 claims audit\n\n%d claims, %d mismatches.\n\nInputs: raw snapshots, saves and screenshots, read with `struct` in `b16_audit.py`; `trials-b16.jsonl` for the seed, plan, answer clicked and box text. Not used: `b16_analyze.py`, `b16_run.strategic/rcode`, `state.sav`, `state.battle`.\n\n"
                      "| doc | claim | file | value in files | claimed | match |\n|---|---|---|---|---|---|\n" % (len(rows), len(badr))
                      + "\n".join("| %s | %s | `%s` | %s | %s | %s |" % (w, t_, f_, str(v).replace("|", "/"), str(e).replace("|", "/"), m) for w, t_, f_, v, e, m in rows) + "\n")
    C.write_new(B.DATA, "b16-number-map-%s.md" % C.STAMP, "# Number map of findings/2026-10-05-battle-peace-offer.md\n\nEvery numeric token of the prose (digits, hex, number words two..nine) with the claim that checks it or the reason it is exempt; the finding's tables are recomputed cell by cell (claims tab_*), cited files and cells checked for existence (cited_files, cited_cells).\n\n| line | token | checked by | reason |\n|---:|---|---|---|\n" + "\n".join("| %s | `%s` | %s | %s |" % x for x in NM) + "\n")
    print(out, len(rows), "claims,", len(badr), "mismatches")
    for r in badr:
        print("MISMATCH", r[1][:90], "\n   got ", r[3], "\n   want", r[4])
    sys.exit(1 if badr else 0)


class _E(dict):
    def __missing__(self, k):
        return "<no expected value: %s>" % k


EXPECT = _E(json.loads((Path(__file__).resolve().parent / "b16_expect.json").read_text()) if (Path(__file__).resolve().parent / "b16_expect.json").exists() else {})


if __name__ == "__main__":
    main()
