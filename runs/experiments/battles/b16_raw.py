#!/usr/bin/env python3
"""B16 raw facts: every measured value of the finding, computed here from RAW inputs only, and the renderer that turns the finding's skeleton into the finding.

INPUTS (each one is raw, or a run record written by the runner at run time; nothing an analyser wrote is read here):
  raw       artifacts/run-exp-battle-peace/snaps/*.snap.gz     memory snapshots of the game taken with the box up (written by the runner from /proc/<pid>/mem)
  raw       artifacts/run-exp-battle-peace/**/*.SAV            start saves, Save As after the answer, End-turn autosaves (written by the game)
  raw       artifacts/run-exp-battle-peace/shots/*.png         screenshots (existence and bytes)
  run record runs/experiments/data/run-exp-battle-peace/trials-b16.jsonl   one line per run, appended by the runner (seed, plan, the answer clicked, read-backs, box text OCR)
  run record runs/experiments/data/run-exp-battle-peace/hooklog-*.csv      the exchange hook's records, dumped by the runner from the game's memory
  raw       harness/driver.py                                   the driver constants
NOT read: b16-fulldiff-*, b16-repeat-*, b16-pairs-*, b16-survey-table-*, b16-hook-table-*, b16-facts-* (analyser or generator outputs). The only place that
opens an analyser file is `compare_with_analyser` in b16_audit.py, which COMPARES it with the values computed here and never uses it.

`values()` returns ({name: formatted value}, {name: source}); `render(skeleton)` replaces every `%%name%%` (or `%%name:c%%` for thousands commas, `%%table:<id>%%`
for a table) by the value. The finding is `render(findings/b16-finding.skeleton.md)`: a number that is not computed here cannot appear in it
(`literal_numbers` lists what a skeleton states literally, each one a reference or a rule quoted from the report)."""
import gzip
import json
import os
import re
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
from state import sav  # noqa: E402

BASE = 0x45E030
NAT, ARM, CITY, FLT, MERC = 0x474670, 0x47C1EC, 0x479590, 0x49C26C, 0x49DA10
MAP = 0x45E870
WEIGHT = {0: 20, 1: 100, 2: 40, 3: 60, 4: 120}
VOLATILE = (0x45E614, 0x45E618)
REGIONS = {"randseed": (0x45E030, 4), "map": (0x45E870, 89600), "nations": (0x474670, 18752), "armies": (0x47C1EC, 200 * 656), "fleets_news": (0x49C26C, 0x4A0344 - 0x49C26C),
           "battle_block": (0x4A0344, 2096), "battle_header": (0x4A0B74, 12)}
EXT = "win+own12=6,strong12=6,unity6=600,weak2=500,weak13=500"
CITYWORD = 0x446
SKELETON = Path(__file__).resolve().parents[3] / "findings" / "b16-finding.skeleton.md"
FINDING = Path(__file__).resolve().parents[3] / "findings" / "2026-10-05-battle-peace-offer.md"
_cache = {}


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def c(n):
    return "{:,}".format(n)


def trials():
    if "trials" not in _cache:
        last, err = {}, 0
        for x in (B.DATA / "trials-b16.jsonl").read_text().splitlines():
            if x.strip():
                r = json.loads(x)
                if r.get("status") == "ok":
                    last[r["trial"]] = r
                else:
                    err += 1
        _cache["trials"] = (last, err)
    return _cache["trials"]


def snap(name):
    if name not in _cache:
        _cache[name] = gzip.decompress((B.ART / "snaps" / name).read_bytes())
    return _cache[name]


def rd(path):
    p = Path(path)
    if p not in _cache:
        _cache[p] = p.read_bytes()
    return _cache[p]


def boxed(r):
    """The box opened: the dialog screenshot taken with it up exists (the file, not the record's flag)."""
    d = r.get("dialogs")
    return bool(d) and bool(d[0].get("shot")) and (B.ART / "shots" / d[0]["shot"]).exists()


# ---- snapshot readers ------------------------------------------------------------------------------------------------------------------
def s_nation(b, n, off):
    return i16(b, NAT - BASE + n * 1172 + off)


def s_armies(b, owner):
    tot = 0
    for i in range(200):
        r = ARM - BASE + i * 656
        if i16(b, r + 4) != owner:
            continue
        s = sum(WEIGHT[struct.unpack_from("<4h", b, r + 16 + 32 * k)[1]] * struct.unpack_from("<4h", b, r + 16 + 32 * k)[2] // 100 for k in range(20) if struct.unpack_from("<4h", b, r + 16 + 32 * k)[2] > 0)
        if s:
            tot += s // 80 * i16(b, r + 14)
    return tot


def s_rome_alive(b):
    r = ARM - BASE
    return i16(b, r + 4) == 0 and sum(max(0, i16(b, r + 16 + 32 * k + 4)) for k in range(20)) > 0


def state(r):
    b = snap(r["pre_snap"])
    W = 0 if s_rome_alive(b) else 6
    L = 6 if W == 0 else 0
    return {"W": W, "armies_W": s_armies(b, W), "armies_L": s_armies(b, L), "unity_L": s_nation(b, L, 0x440), "cities_L": s_nation(b, L, 0x446),
            "tests": s_armies(b, W) < s_armies(b, L) and s_nation(b, L, 0x440) > 500 and s_nation(b, L, 0x446) > 7}


# ---- save readers ----------------------------------------------------------------------------------------------------------------------
def layout(b):
    na = i16(b, sav.ARMY_OFF)
    of = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN
    nf = i16(b, of)
    nat0 = of + 2 + nf * sav.FLEET_LEN
    return {"na": na, "nf": nf, "of": of, "nat0": nat0, "mercs0": nat0 + 16 * sav.NATION_LEN}


def v_nation(b, n, off):
    return i16(b, layout(b)["nat0"] + n * 1172 + off)


def v_treasury(b, n):
    return struct.unpack_from("<i", b, layout(b)["nat0"] + n * 1172 + 0x438)[0]


def v_news(b):
    o = layout(b)["mercs0"] + 600
    ni = i16(b, o)
    return [b[o + 2 + 61 * k:o + 2 + 61 * (k + 1)].split(b"\0")[0].decode("latin1") for k in range(ni + 1)]


def flat(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            yield from flat(v, "%s[%d]" % (path, i))
    else:
        yield path, o


def decoded_diff(sp, sq):
    fa = dict(flat({k: v for k, v in sp.items() if k not in ("map", "tail_off")}))
    fb = dict(flat({k: v for k, v in sq.items() if k not in ("map", "tail_off")}))
    return [(k, fa.get(k), fb.get(k)) for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)]


def before_save(sn, post, news_base):
    """The post save with the snapshot's blocks laid over it (the 'save' of the moment the box was up, except the tail), and the news ring decoded from the snapshot."""
    L = layout(post)
    b = bytearray(post)
    take = lambda a, n: sn[a - BASE:a - BASE + n]
    b[0:89600] = take(MAP, 89600)
    b[sav.CITY_OFF:sav.CITY_OFF + sav.CITY_N * sav.CITY_LEN] = take(CITY, sav.CITY_N * sav.CITY_LEN)
    b[sav.ARMY_OFF + 2:sav.ARMY_OFF + 2 + L["na"] * sav.ARMY_LEN] = take(ARM, L["na"] * sav.ARMY_LEN)
    b[L["of"] + 2:L["of"] + 2 + L["nf"] * sav.FLEET_LEN] = take(FLT, L["nf"] * sav.FLEET_LEN)
    b[L["nat0"]:L["nat0"] + 16 * sav.NATION_LEN] = take(NAT, 16 * sav.NATION_LEN)
    b[L["mercs0"]:L["mercs0"] + 600] = take(MERC, 600)
    news = [sn[news_base - BASE + 61 * k:news_base - BASE + 61 * (k + 1)].split(b"\0")[0].decode("latin1") for k in range(40)]
    return bytes(b), news


def pairs_of(T):
    """(cell, seed, yes record, no record): the last ok Yes run and the last ok No run with turns and a box screenshot, per (cell, seed)."""
    pick = {}
    for r in T.values():
        if r["build"] == "normal" and r["answer_plan"] in ("yes", "no") and r.get("turns") and boxed(r):
            pick[(r["cell"], r["seed"], r["answer_plan"])] = r
    return [(c_, s_, pick[(c_, s_, "yes")], pick[(c_, s_, "no")]) for (c_, s_, a) in sorted(pick) if a == "yes" and (c_, s_, "no") in pick]


def fulldiff_raw(T=None, pairs=None):
    """The whole before/after diff per run, from the snapshot (box up) and the post-answer save, decoded with state/sav.py and compared field by field; news included."""
    T = T or trials()[0]
    pairs = pairs if pairs is not None else pairs_of(T)
    no0 = next(n for _, _, _, n in pairs)
    seg_save = rd(B.ART / no0["post_save"])
    L = layout(seg_save)
    seg = seg_save[L["mercs0"] + 600 + 2:L["mercs0"] + 600 + 2 + 61 * 20]
    i = snap(no0["pre_snap"]).find(seg)
    news_base = BASE + i
    out = []
    for _, sd, y, n in pairs:
        for r in (y, n):
            post = rd(B.ART / r["post_save"])
            pre, news_pre = before_save(snap(r["pre_snap"]), post, news_base)
            sp, sq = sav.parse(pre), sav.parse(post)
            sp["news"] = news_pre
            d = decoded_diff(sp, sq)
            cb, ca = Counter(news_pre), Counter(sq["news"])
            out.append({"trial": r["trial"], "answer": r["answer_plan"], "cell": r["cell"], "fields": d, "map": sum(1 for a, b in zip(sp["map"], sq["map"]) if a != b),
                        "added": sorted((ca - cb).elements()), "dropped": sorted((cb - ca).elements())})
    return {"news_base": news_base, "runs": out}


def repeat_raw(T=None):
    """Same cell, same seed, same answer class, different process: named regions of the box-up snapshots and the bytes outside the two volatile words."""
    T = T or trials()[0]
    groups = defaultdict(list)
    for r in T.values():
        if r["build"] == "normal" and (r.get("dialogs") or r.get("box_opened") is False):
            groups[(r["cell"], r["seed"], "yes" if r["answer_plan"] == "yes" else "no")].append(r)
    res = []
    for k, rs in sorted(groups.items()):
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = snap(rs[i]["pre_snap"]), snap(rs[j]["pre_snap"])
                reg = all(a[x - BASE:x - BASE + n] == b[x - BASE:x - BASE + n] for x, n in REGIONS.values())
                diff = [BASE + t for t in range(len(a)) if a[t] != b[t]] if a != b else []
                res.append({"a": rs[i]["trial"], "b": rs[j]["trial"], "regions_equal": reg, "differing": len(diff), "outside_volatile": [d for d in diff if not VOLATILE[0] <= d < VOLATILE[1]]})
    return res


def clist(b, n):
    o = layout(b)["nat0"] + n * 1172 + 0x48
    k = 0
    while k < 334 and i16(b, o + 2 * k) >= 0:
        k += 1
    return k


def values():
    """({name: str}, {name: source})."""
    if "values" in _cache:
        return _cache["values"]
    T, nerr = trials()
    V, S = {}, {}

    def put(src, **kw):
        for k, v in kw.items():
            assert k not in V, k
            V[k] = v if isinstance(v, str) else str(v)
            S[k] = src
    normal = [r for r in T.values() if r["build"] == "normal"]
    survey = {}
    for r in normal:
        if r["answer_plan"] == "capture" and ((r["cell"], r["seed"]) not in survey or "survey" in r["trial"]):
            survey[(r["cell"], r["seed"])] = r
    opened = [r for r in normal if r["answer_plan"] in ("capture", "yes", "no") and boxed(r)]
    # box
    g = {tuple(r["dialogs"][0]["geometry"]) for r in opened}
    ctl = {(x["text"], x["x"] - r["dialogs"][0]["geometry"][0], x["y"] - r["dialogs"][0]["geometry"][1], x["w"], x["h"]) for r in opened for x in (r["dialogs"][0].get("controls") or [])}
    assert len(g) == 1 and len(ctl) == 2, (g, ctl)
    gx, gy, gw, gh = next(iter(g))
    yes = next(x for x in ctl if x[0] == "Yes")
    no = next(x for x in ctl if x[0] == "No")
    put("trials-b16.jsonl dialogs (geometry and controls of every opened run)", box_x=gx, box_y=gy, box_w=gw, box_h=gh, btn_w=yes[3], btn_h=yes[4], yes_rx=yes[1], yes_ry=yes[2],
        no_rx=no[1], no_ry=no[2], ncontrols=len(ctl), btn_same_size=(yes[3:] == no[3:]))
    # start save and cells
    rb_keys = {tuple(x["op"]) for r in normal if r["cell"] == EXT for x in r["readback"]}
    fld = rd(B.ART / C.FLD_RG_NAME)
    na = i16(fld, sav.ARMY_OFF)
    arm = lambda i: sav.ARMY_OFF + 2 + i * 656
    nm = lambda n: rd(B.ART / C.FLD_RG_NAME)[layout(fld)["nat0"] + n * 1172:layout(fld)["nat0"] + n * 1172 + 11].split(b"\0")[0].decode()
    put("FLD-RG start save (raw bytes)", rome_cities=v_nation(fld, 0, 0x446), rome_unity=v_nation(fld, 0, 0x440), gaul_cities=v_nation(fld, 6, 0x446), gaul_unity=v_nation(fld, 6, 0x440),
        army0_x=i16(fld, arm(0)), army0_y=i16(fld, arm(0) + 2), army10_x=i16(fld, arm(10)), army10_y=i16(fld, arm(10) + 2), army12_x=i16(fld, arm(12)), army12_y=i16(fld, arm(12) + 2),
        army12_owner=i16(fld, arm(12) + 4), army12_owner_name=nm(i16(fld, arm(12) + 4)),
        rome_army=[i for i in range(na) if (i16(fld, arm(i)), i16(fld, arm(i) + 2)) == (86, 28)][0], gaul_army=[i for i in range(na) if (i16(fld, arm(i)), i16(fld, arm(i) + 2)) == (85, 28)][0],
        ext_army=[k[1] for k in rb_keys if k[0] == "owner"][0], cityword_off="0x%X" % CITYWORD,
        rome_other="%d and %d" % tuple(i for i in range(1, na) if i16(fld, arm(i) + 4) == 0 and any(i16(fld, arm(i) + 16 + 32 * k + 4) > 0 for k in range(20))),
        cityword_ok=(v_nation(fld, 0, 0x446) == clist(fld, 0) and v_nation(fld, 6, 0x446) == clist(fld, 6)))
    ld = lambda cell, key: {json.dumps(r["armies_loaded"][key]) for r in normal if r["cell"] == cell}
    a, b_ = ld("loss", "rome0"), ld("win", "gaul10")
    assert len(a) == 1 and len(b_) == 1
    la, lb = json.loads(next(iter(a)))[0], json.loads(next(iter(b_)))[0]
    put("trials-b16.jsonl armies_loaded (read back from game memory before the attack)", cell_type=la[0].upper(), cell_troops=c(la[1]), cell_q=la[2], win_cell_same=(la == lb))
    rb = defaultdict(set)
    for r in normal:
        if r["cell"] == EXT:
            for x in r["readback"]:
                rb[tuple(x["op"])].add(json.dumps(x["got"]))
    u12, u2, u13 = (json.loads(next(iter(rb[("units", k)]))) for k in (12, 2, 13))
    put("trials-b16.jsonl readback (extended D-WIN cell, read from game memory before each of its 5 runs)", ext_owner=json.loads(next(iter(rb[("owner", 12)]))), ext_nunits=len(u12),
        ext_unit_type=u12[0][0].upper(), ext_unit_troops=c(u12[0][1]), ext_gaul_unity=json.loads(next(iter(rb[("unity", 6)]))), ext_weak=c(u2[0][1]), ext_weak_same=(u2 == u13),
        ext_readbacks_consistent=all(len(v) == 1 for v in rb.values()))
    # survey
    loss = [state(survey[("loss", s)]) for s in range(1, 31)]
    lo = [s for s in range(1, 31) if boxed(survey[("loss", s)])]
    put("snapshots of the 30 D-LOSS survey runs, dialog screenshots", loss_n=30, loss_open=len(lo), loss_open_seeds=", ".join(map(str, lo)), loss_pct=round(100 * len(lo) / 30),
        loss_tests_all=all(x["tests"] for x in loss), loss_unity=next(iter({x["unity_L"] for x in loss})), loss_cities=next(iter({x["cities_L"] for x in loss})),
        loss_armW="%s to %s" % (c(min(x["armies_W"] for x in loss)), c(max(x["armies_W"] for x in loss))), loss_armL=c(next(iter({x["armies_L"] for x in loss}))))
    win = [state(survey[("win", s)]) for s in range(1, 11)]
    put("snapshots of the 10 D-WIN survey runs", win_n=10, win_open=sum(1 for s in range(1, 11) if boxed(survey[("win", s)])), win_armL=next(iter({x["armies_L"] for x in win})),
        win_unity=next(iter({x["unity_L"] for x in win})), win_cities=next(iter({x["cities_L"] for x in win})), win_tests_any=any(x["tests"] for x in win))
    ext = [(s, state(survey[(EXT, s)]), boxed(survey[(EXT, s)])) for s in range(1, 6)]
    eo = [e[0] for e in ext if e[2]]
    put("snapshots of the 5 extended D-WIN survey runs", ext_n=5, ext_open=len(eo), ext_open_seeds=" and ".join(map(str, eo)),
        ext_armW="%s to %s" % (c(min(e[1]["armies_W"] for e in ext)), c(max(e[1]["armies_W"] for e in ext))), ext_armL=c(next(iter({e[1]["armies_L"] for e in ext}))),
        ext_unity=next(iter({e[1]["unity_L"] for e in ext})), ext_cities=next(iter({e[1]["cities_L"] for e in ext})), ext_tests_all=all(e[1]["tests"] for e in ext))
    stl = rd(B.ART / "start" / "loss_start.SAV")
    ste = rd(B.ART / "start" / ("%s_start.SAV" % EXT.replace(",", "_")))
    sb, sbe = snap(survey[("loss", 1)]["pre_snap"]), snap(survey[(EXT, 1)]["pre_snap"])
    put("start saves v snapshots with the box up", wb_loser=s_nation(sb, 0, 0x440) - v_nation(stl, 0, 0x440), wb_winner="+%d" % (s_nation(sb, 6, 0x440) - v_nation(stl, 6, 0x440)),
        rome_after=s_nation(sb, 0, 0x440), gaul_after=s_nation(sb, 6, 0x440), ext_gaul_after=s_nation(sbe, 6, 0x440), ext_gaul_before=v_nation(ste, 6, 0x440))
    # clicks
    clk = Counter((r["answered"], r["answer_click"]["clicks"]) for r in normal if r.get("answer_click"))
    put("trials-b16.jsonl answer_click (normal build)", clicks_no2=clk[("No", 2)], clicks_yes2=clk[("Yes", 2)], clicks_no3=clk[("No", 3)], click_n=Counter(k[1] for k in clk.elements()).most_common(1)[0][0], click_n3=max(k[1] for k in clk), clicks_other=sum(v for k, v in clk.items() if k not in (("No", 2), ("Yes", 2), ("No", 3))))
    drv = (C.ROOT / "harness" / "driver.py").read_text()
    m_ = re.search(r"for _ in range\((\d+)\):\s+# give the box up to ([\d.]+) s", drv)
    t_ = re.search(r"def answer_battle_peace\(self, yes, shot=None, pre_click=None, tries=(\d+)\)", drv)
    put("harness/driver.py", poll_s=int(m_.group(1)) * 0.25, tries=int(t_.group(1)))
    lens = {len(snap(r["pre_snap"])) for r in normal}
    put("the pre-answer snapshots", snap_len=c(next(iter(lens))), snap_lens_equal=(len(lens) == 1))
    put("trials-b16.jsonl", errors_n=nerr)
    # pairs
    pairs = pairs_of(T)
    put("trials-b16.jsonl", npairs=len(pairs), npairs_loss=sum(1 for p in pairs if p[0] == "loss"), npairs_win=sum(1 for p in pairs if p[0] != "loss"),
        nturns=next(iter({len(r["turns"]) for p in pairs for r in p[2:]})), turn_errors=sum(1 for p in pairs for r in p[2:] for t in r["turns"] if t.get("error")))
    ts = lambda r, t: rd(B.ART / "turns" / r["turns"][t]["save"])
    rel = lambda b: v_nation(b, 0, 0x26 + 12)
    ry0 = {rel(rd(B.ART / p[2]["post_save"])) for p in pairs}
    rn0 = {rel(rd(B.ART / p[3]["post_save"])) for p in pairs}
    ryg = {v_nation(rd(B.ART / p[2]["post_save"]), 6, 0x26) for p in pairs}
    ty = [{rel(ts(p[2], t)) for p in pairs} for t in range(4)]
    tn = [{rel(ts(p[3], t)) for p in pairs} for t in range(4)]
    one = lambda s: str(next(iter(s))) if len(s) == 1 else "VARIES"
    put("post-answer saves and End-turn autosaves (raw)", rel_yes_ans=one(ry0), rel_yes_ans_gaul=one(ryg), rel_no_ans=one(rn0), rel_yes_t1=one(ty[0]), rel_yes_all=one(ty[0] | ty[1] | ty[2] | ty[3]),
        rel_no_all=one(tn[0] | tn[1] | tn[2] | tn[3]), rel_step=int(one(ty[0])) - int(one(ry0)) if "VARIES" not in (one(ty[0]), one(ry0)) else "VARIES")
    cl = lambda sel, who, t, which: {v_nation(ts(p[which], t), who, 0x446) for p in pairs if sel(p)}
    L_ = lambda p: p[0] == "loss"
    W_ = lambda p: p[0] != "loss"
    put("End-turn autosaves (raw)", loss_no_rome=", ".join(one(cl(L_, 0, t, 3)) for t in range(4)), loss_no_gaul=", ".join(one(cl(L_, 6, t, 3)) for t in range(4)),
        loss_yes_rome=one(set().union(*[cl(L_, 0, t, 2) for t in range(4)])), loss_yes_gaul=one(set().union(*[cl(L_, 6, t, 2) for t in range(4)])),
        win_rome=one(set().union(*[cl(W_, 0, t, w) for t in range(4) for w in (2, 3)])), win_gaul=one(set().union(*[cl(W_, 6, t, w) for t in range(4) for w in (2, 3)])),
        first_city_turn=min(t + 1 for t in range(4) if any(v_nation(ts(p[2], t), 0, 0x446) != v_nation(ts(p[3], t), 0, 0x446) for p in pairs if L_(p))),
        loss_no_gaul_first=one(cl(L_, 6, 0, 3)), loss_no_gaul_last=one(cl(L_, 6, 3, 3)))
    # no v no
    nos = defaultdict(list)
    for r in T.values():
        if r["build"] == "normal" and r["answer_plan"] == "no" and r.get("turns"):
            nos[(r["cell"], r["seed"])].append(r)
    nn = [(k[1], rd(B.ART / a["post_save"]) == rd(B.ART / b["post_save"]), sum(1 for x, y in zip(a["turns"], b["turns"]) if rd(B.ART / "turns" / x["save"]) == rd(B.ART / "turns" / y["save"])), len(a["turns"]))
          for k, rs in sorted(nos.items()) if len(rs) >= 2 for a, b in [(rs[0], rs[1])]]
    put("post and turn saves of repeated No runs", nn_n=len(nn), nn_seeds=" and ".join(str(x[0]) for x in nn), nn_post_equal=all(x[1] for x in nn), nn_turns_equal=all(x[2] == x[3] for x in nn), nn_turns=nn[0][3])
    # full diff
    fd = fulldiff_raw(T, pairs)
    yr = [d for d in fd["runs"] if d["answer"] == "yes"]
    nr = [d for d in fd["runs"] if d["answer"] == "no"]
    ynn = lambda d: [f for f in d["fields"] if not f[0].startswith("news")]
    put("full before/after diff computed in b16_raw.fulldiff_raw (snapshot v post save, state/sav.py)", fd_runs=len(fd["runs"]), fd_yes_runs=len(yr), fd_no_runs=len(nr), fd_yes_fields=one({len(d["fields"]) for d in yr}),
        fd_yes_rel=one({len(ynn(d)) for d in yr}), fd_yes_news=one({len(d["fields"]) - len(ynn(d)) for d in yr}), fd_added=one({len(d["added"]) for d in yr}), fd_dropped_n=one({len(d["dropped"]) for d in yr}),
        fd_dropped=one({d["dropped"][0] for d in yr}), fd_no_fields=one({len(d["fields"]) for d in nr}), fd_map=one({d["map"] for d in fd["runs"]}),
        fd_rel_paths=" and ".join(sorted({f[0] for d in yr for f in ynn(d)})), fd_rel_before=one({str(f[1]) for d in yr for f in ynn(d)}), fd_rel_after=one({str(f[2]) for d in yr for f in ynn(d)}),
        fd_added_win=one({d["added"][0] for d in yr if d["cell"] != "loss"}), fd_added_loss=one({d["added"][0] for d in yr if d["cell"] == "loss"}))
    # volatile words, identity
    vals = [(struct.unpack_from("<h", snap(r["pre_snap"]), 0x45E614 - BASE)[0], struct.unpack_from("<h", snap(r["pre_snap"]), 0x45E616 - BASE)[0]) for p in pairs for r in p[2:]]
    s8 = [struct.unpack_from("<h", snap(T[t]["pre_snap"]), 0x45E614 - BASE)[0] for t in ("loss_s8_survey_r1", "loss_s8_yes_r1", "loss_s8_no_r1")]
    idn = []
    for _, _, y, n in pairs:
        a, b = snap(y["pre_snap"]), snap(n["pre_snap"])
        d = [BASE + t for t in range(len(a)) if a[t] != b[t]] if a != b else []
        idn.append((len(d), all(VOLATILE[0] <= x < VOLATILE[1] for x in d), all(a[x - BASE:x - BASE + n_] == b[x - BASE:x - BASE + n_] for x, n_ in REGIONS.values()),
                    rd(B.ART / "shots" / y["dialogs"][0]["shot"]) == rd(B.ART / "shots" / n["dialogs"][0]["shot"])))
    rp = repeat_raw(T)
    put("pre-answer snapshots, pairs and repeated runs (raw)", id_max_bytes=max(x[0] for x in idn), id_all_volatile=all(x[1] for x in idn), id_regions_equal=all(x[2] for x in idn),
        id_png_equal=all(x[3] for x in idn), vol_a="0x%X" % VOLATILE[0], vol_b="0x%X" % (VOLATILE[0] + 2), vol_min=min(v[0] for v in vals), vol_max=max(v[0] for v in vals),
        vol_other=" or ".join(str(x) for x in sorted({v[1] for v in vals})), s8_vals="%d, %d and %d" % tuple(s8), rep_n=len(rp), rep_regions_equal=all(x["regions_equal"] for x in rp),
        rep_extra=max(len(x["outside_volatile"]) for x in rp), rep_lo="0x%X" % min(o for x in rp for o in x["outside_volatile"]), rep_hi="0x%X" % max(o for x in rp for o in x["outside_volatile"]),
        snap_lo="0x%X" % BASE, snap_hi="0x4A0B80")
    d1, d30 = rd(B.ART / "loss_s1_yes_r1_post.SAV"), rd(B.ART / "loss_s30_yes_r1_post.SAV")
    t1, t30 = rd(B.ART / "turns" / "loss_s1_yes_r1_t4_AUTO0747.SAV"), rd(B.ART / "turns" / "loss_s30_yes_r1_t4_AUTO0747.SAV")
    put("post and turn-4 saves of seeds 1 and 30 (raw)", sd_seeds="1 and 30", sd_post=sum(1 for x, y in zip(d1, d30) if x != y) + abs(len(d1) - len(d30)), sd_turn=sum(1 for x, y in zip(t1, t30) if x != y) + abs(len(t1) - len(t30)))
    # reseed
    lcg6 = (6 * 0x08088405 + 1) & 0xFFFFFFFF
    rs = {struct.unpack("<I", snap(r["pre_snap"])[:4])[0] for r in opened}
    nmz = lambda b, n: b[NAT - BASE + n * 1172:NAT - BASE + n * 1172 + 11].split(b"\0")[0].decode()
    put("snapshots of every opened run", rs_value="0x%X" % next(iter(rs)), rs_unique=(len(rs) == 1), rs_lcg6="0x%X" % lcg6, rs_n=len(opened), rome_idx=[i for i in range(16) if nmz(sb, i) == "Rome"][0], gaul_idx=[i for i in range(16) if nmz(sb, i) == "Gaul"][0])
    # gate (normal build)
    gate = defaultdict(dict)
    for r in normal:
        if r["cell"].startswith("loss+") and r["answer_plan"] == "capture":
            b = snap(r["pre_snap"])
            gate[r["cell"]][r["seed"]] = (boxed(r), s_nation(b, 0, 0x440), s_nation(b, 0, 0x446), s_armies(b, 0), s_armies(b, 6))
    allo = lambda c_: all(v[0] for v in gate[c_].values())
    allc = lambda c_: not any(v[0] for v in gate[c_].values())
    uni = lambda c_: next(iter({v[1] for v in gate[c_].values()}))
    edit_of = lambda c_: int(c_.rsplit("=", 1)[1])
    put("gate-cell snapshots and dialog screenshots (normal build, seeds 1, 3, 5)", g_unity_open=uni("loss+unity0=526"), g_unity_c1=uni("loss+unity0=525"), g_unity_c2=uni("loss+unity0=524"),
        g_edit_open=edit_of("loss+unity0=526"), g_edit_c1=edit_of("loss+unity0=525"), g_edit_c2=edit_of("loss+unity0=524"),
        g_ok=(allo("loss+unity0=526") and allc("loss+unity0=525") and allc("loss+unity0=524") and allo("loss+ncities0=8") and allc("loss+ncities0=7") and allc("loss+weak2=500,weak13=500")),
        g_city_open=next(iter({v[2] for v in gate["loss+ncities0=8"].values()})), g_city_closed=next(iter({v[2] for v in gate["loss+ncities0=7"].values()})),
        g_weakL=next(iter({v[3] for v in gate["loss+weak2=500,weak13=500"].values()})), g_weakW="%s to %s" % (c(min(v[4] for v in gate["loss+weak2=500,weak13=500"].values())), c(max(v[4] for v in gate["loss+weak2=500,weak13=500"].values()))),
        g_seeds=len(gate["loss+unity0=526"]), g_cells=len(gate), g_before=uni("loss+unity0=525") - (s_nation(sb, 0, 0x440) - v_nation(stl, 0, 0x440)))
    # hooked
    hk = [r for r in T.values() if r["build"] == "lab hook"]
    hb = [r for r in hk if r["cell"] == "loss"]
    hcsv = lambda r: [x.split(",") for x in (B.DATA / ("hooklog-%s.csv" % r["trial"])).read_text().splitlines()[1:]]
    draw = lambda r: [int(x[6]) for x in hcsv(r) if x[1] == "random" and x[2] == "0x45951c"]
    rng = {int(x[3]) for r in hb for x in hcsv(r) if x[1] == "random" and x[2] == "0x45951c"}
    ho = [r for r in hb if boxed(r)]
    hc = [r for r in hb if not boxed(r)]
    put("hooklog-*.csv (run records of the hooked lab runs) and dialog screenshots", hook_n=len(hb), hook_seeds="%d to %d" % (min(r["seed"] for r in hb), max(r["seed"] for r in hb)), hook_open=len(ho),
        hook_open_seeds=", ".join(str(r["seed"]) for r in sorted(ho, key=lambda r: r["seed"])), hook_open_draws=", ".join(str(draw(r)[0]) for r in sorted(ho, key=lambda r: r["seed"])), hook_closed=len(hc),
        hook_closed_draws="%d to %d" % (min(draw(r)[0] for r in hc), max(draw(r)[0] for r in hc)), hook_rule=all((boxed(r)) == (len(draw(r)) == 1 and draw(r)[0] < 2) for r in hb),
        hook_gate_runs=len(hk) - len(hb), hook_gate_draws=sum(len(draw(r)) for r in hk if r["cell"] != "loss"), hook_gate_open=sum(1 for r in hk if r["cell"] != "loss" and boxed(r)),
        draw_range=next(iter(rng)) if len(rng) == 1 else "VARIES", draw_open=sum(1 for v in range(5) if v < 2), draw_pct=100 * sum(1 for v in range(5) if v < 2) // 5,
        reseed_site=next(iter({x[2] for r in hb for x in hcsv(r) if x[1] == "reseed"})), reseed_only_open=all(any(x[1] == "reseed" for x in hcsv(r)) == boxed(r) for r in hb), draw_site="0x45951c")
    _cache["values"] = (V, S)
    return V, S


def table_rows(name):
    T, _ = trials()
    normal = [r for r in T.values() if r["build"] == "normal"]
    survey = {}
    for r in normal:
        if r["answer_plan"] == "capture" and ((r["cell"], r["seed"]) not in survey or "survey" in r["trial"]):
            survey[(r["cell"], r["seed"])] = r
    if name in ("loss", "win", "ext"):
        cell, seeds = {"loss": ("loss", range(1, 31)), "win": ("win", range(1, 11)), "ext": (EXT, range(1, 6))}[name]
        hdr = ["seed", "box", "winner", "armies(W)", "armies(L)", "unity(L)", "cities(L)", "tests pass", "dialog screenshot", "pre-answer snapshot"]
        rows = []
        for s in seeds:
            r = survey[(cell, s)]
            x = state(r)
            shot = r["dialogs"][0]["shot"] if boxed(r) else None
            rows.append([str(s), "**open**" if boxed(r) else "closed", {0: "Rome", 6: "Gaul"}[x["W"]], str(x["armies_W"]), str(x["armies_L"]), str(x["unity_L"]), str(x["cities_L"]),
                         "yes" if x["tests"] else "no", ("`%s`" % shot) if shot else "-", "`%s`" % r["pre_snap"]])
        return hdr, rows, "|---:|:---:|---|---:|---:|---:|---:|:---:|---|---|"
    pairs = pairs_of(T)
    if name == "pairs":
        hdr = ["cell", "seed", "rel after answer", "rel after turn 1..4", "Rome cities t1..t4", "Gaul cities t4", "Rome unity t4", "Gaul unity t4", "Rome treasury t4"]
        rows = []
        for c_, sd, y, n in pairs:
            ry, rn = (rd(B.ART / r["post_save"]) for r in (y, n))
            tt = [tuple(rd(B.ART / "turns" / r["turns"][t]["save"]) for r in (y, n)) for t in range(4)]
            f = lambda g: "%s/%s" % (g(tt[3][0]), g(tt[3][1]))
            rows.append(["D-LOSS" if c_ == "loss" else "D-WIN + 2nd Gaul army", str(sd), "%s/%s" % (v_nation(ry, 0, 0x26 + 12), v_nation(rn, 0, 0x26 + 12)),
                         " ".join("%s/%s" % (v_nation(a, 0, 0x26 + 12), v_nation(b, 0, 0x26 + 12)) for a, b in tt), " ".join("%s/%s" % (v_nation(a, 0, 0x446), v_nation(b, 0, 0x446)) for a, b in tt),
                         f(lambda b: v_nation(b, 6, 0x446)), f(lambda b: v_nation(b, 0, 0x440)), f(lambda b: v_nation(b, 6, 0x440)), f(lambda b: v_treasury(b, 0))])
        return hdr, rows, "|---|---:|---|---|---|---|---|---|---|"
    if name == "gate":
        gate = defaultdict(dict)
        for r in normal:
            if r["cell"].startswith("loss+") and r["answer_plan"] == "capture":
                b = snap(r["pre_snap"])
                gate[r["cell"]][r["seed"]] = (boxed(r), s_nation(b, 0, 0x440), s_nation(b, 0, 0x446), s_armies(b, 0), s_armies(b, 6))
        hdr = ["cell (edit)", "Rome unity at the box (after the -25)", "Rome cities word", "armies(Rome)", "armies(Gaul)", "seed 1", "seed 3", "seed 5"]
        rows = [["`%s`" % c_, str(d[1][1]), str(d[1][2]), str(d[1][3]), str(d[1][4])] + ["**open**" if d[s][0] else "closed" for s in (1, 3, 5)] for c_, d in sorted(gate.items())]
        return hdr, rows, "|---|---:|---:|---:|---:|:---:|:---:|:---:|"
    if name == "hook":
        hdr = ["trial", "box", "tests pass", "draws at 0x45951C", "draw result", "reseed record"]
        rows = []
        for r in sorted([r for r in T.values() if r["build"] == "lab hook"], key=lambda r: (r["seed"], r["cell"] != "loss", r["trial"])):
            rs_ = [x.split(",") for x in (B.DATA / ("hooklog-%s.csv" % r["trial"])).read_text().splitlines()[1:]]
            dr = [int(x[6]) for x in rs_ if x[1] == "random" and x[2] == "0x45951c"]
            rows.append(["`%s`" % r["trial"], "**open**" if boxed(r) else "closed", "yes" if state(r)["tests"] else "no", str(len(dr)), str(dr[0]) if dr else "-",
                         ";".join("%s@%s" % (x[0], x[2]) for x in rs_ if x[1] == "reseed") or "-"])
        rows.sort(key=lambda x: x[0])
        return hdr, rows, "|---|:---:|:---:|---:|---:|---|"
    raise KeyError(name)


def table_md(name):
    hdr, rows, sep = table_rows(name)
    return "\n".join(["| " + " | ".join(hdr) + " |", sep] + ["| " + " | ".join(r) + " |" for r in rows])


PROTECTED = ("army12_owner_name", "cell_type", "ext_unit_type", "fd_added_loss", "fd_added_win", "fd_dropped")
TABLES = ("loss", "win", "ext", "pairs", "gate", "hook")
MARKER = re.compile(r"%%(?:([A-Za-z_][A-Za-z0-9_]*)|lit:([A-Za-z0-9_]+)|table:([a-z]+))%%")


def _valid(m):
    """A marker is valid if it names a computed value, a registered literal (LIT) or a table id."""
    name, lit, tab = m.groups()
    if lit is not None:
        return lit in LIT
    if tab is not None:
        return tab in TABLES
    return True          # a value name; `values()` decides whether it exists (see `placeholders` and the audit claim)


def render(skeleton):
    V, _ = values()

    def sub(m):
        name, lit, tab = m.groups()
        if tab is not None:
            return table_md(tab)
        if lit is not None:
            return LIT[lit][0]
        return V[name]
    out = MARKER.sub(sub, skeleton)
    if "%%" in out:
        raise ValueError("stray or unknown %% in the skeleton: " + out[out.index("%%") - 40:out.index("%%") + 40])
    return out


def placeholders(skeleton):
    """Names of the value markers (not `lit:` or `table:`) in the skeleton."""
    return [m.group(1) for m in MARKER.finditer(skeleton) if m.group(1)]


LIT = {"rep_sec": ("§9 item 6", "section reference of the decompiled report"), "rep_sec2": ("§2.3", "section reference of the decompiled report"), "plan7": ("§7", "section of docs/proposals/battles.md"),
       "rule6": ("rule 6", "CLAUDE.md rule number"), "thaw": ("(+1, and +3 with a 1-in-3 chance, the rule is the report's, not measured here)", "the quarterly thaw rule quoted from the report"),
       "ally8": ("ally relations to -8", "the ally-loop rule quoted from the report"), "w2": ("two fresh processes", "the design of a pair (a Yes run and a No run)"),
       "t3": ("the three tests", "the three tests the report names"), "two_nations": ("both nations", "wording"), "weak_edit": ("weak2=500,weak13=500", "the edit expression of the gate cell (the cell is checked to exist in trials-b16.jsonl)"),
       "reclick": ("reclick=False", "the driver argument named in the sentence"),
       "ally_cond": ("rel[W][k] == 2 and rel[L][k] == 3", "the ally-loop condition quoted from the report")}


def lint_skeleton(skeleton):
    """Errors of the skeleton, line by line: (a) any `%%` that is not part of a VALID marker (a value name, `lit:KEY` with KEY in LIT, `table:ID` with ID in TABLES);
    (b) any numeric token left after the valid markers are removed, in prose, headings AND table rows (a frozen value, a pasted table). Returns [] when clean."""
    errs = []
    V, _ = values()
    for n, line in enumerate(skeleton.split("\n"), 1):
        rest = MARKER.sub(lambda m: " " if _valid(m) else m.group(0), line)
        for name in PROTECTED:           # a computed text value (a name, a unit type, a news line) frozen into the prose
            if re.search(r"(?<![\w])" + re.escape(V[name]) + r"(?![\w])", rest):
                errs.append("line %d: the computed value of %s (%r) is written literally" % (n, name, V[name]))
        if re.search(r"\b(True|False)\b", rest):
            errs.append("line %d: a literal True/False outside a marker (the invariants are computed)" % n)
        if "%%" in rest:
            errs.append("line %d: stray or unknown %%%% marker: %s" % (n, rest[max(0, rest.index("%%") - 30):rest.index("%%") + 30]))
        for t in NUMS.lint_tokens(rest):
            errs.append("line %d: literal number %s outside a marker" % (n, t))
    return errs


def literal_numbers(skeleton):
    """The numeric tokens the skeleton states literally (line by line, valid markers removed first; see `lint_skeleton`)."""
    out = []
    for line in skeleton.split("\n"):
        out += NUMS.lint_tokens(MARKER.sub(lambda m: " " if _valid(m) else m.group(0), line))
    return sorted(set(out))
