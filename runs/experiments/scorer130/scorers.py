#!/usr/bin/env python3.12
"""Research #130: word storage, comparison and the final add in the AI target scorers FUN_0044ece4 (city) and FUN_0044ee60
(army), run as original instructions under Unicorn (read-only; the pinned unpatched EXE and the #187 RAM snapshot, which stay
out of git).

    python3.12 runs/experiments/scorer130/scorers.py controls --version v1   # stubbed-helper boundary controls + model check
    python3.12 runs/experiments/scorer130/scorers.py survey --version v1     # real helpers on original saves: reachable ranges

Calling convention (both): ax = army index, edx -> index word, ecx -> score word, [esp+4] -> distance word; `ret 4`.
Controls stub the helpers at their entry (value in eax, plain ret), keyed by the candidate the scorer is visiting, so any
register value can be fed. The survey runs the real helpers on RAM built from each save (map, cities, armies, fleets,
nations written over the snapshot) for every army of every nation, and checks every call against `model()`.
Outputs go to runs/experiments/data/run-exp-scorer130/ with exclusive creation (rule 6).
"""
import argparse
import glob
import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP, \
    UC_X86_REG_EBP, UC_X86_REG_EDI

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "runs/experiments/data/run-exp-scorer130"
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
from core import EXE  # noqa: E402  (the pinned unpatched EXE; core.py checks its hash)
RAM = (ROOT / "artifacts/run-exp-strategic-fidelity/original/N-rome-hook-v1/snapshots/000.ram").read_bytes()
ORIGIN = 0x45e000
CITY, ARMY, FLEET, NATION, MAP = 0x479590, 0x47c1ec, 0x49c26c, 0x474670, 0x45e870
ARMY_N, FLEET_N, CUR = 0x4a0324, 0x4a0326, 0x4a0320
ECE4, EE60 = 0x44ece4, 0x44ee60
OUT = 0x80a000          # idx, score, dist words
RET = 0x600000

pe = struct.unpack_from("<I", EXE, 0x3c)[0]
_n, _opt = struct.unpack_from("<H", EXE, pe + 6)[0], struct.unpack_from("<H", EXE, pe + 20)[0]
SECTIONS = []
for _i in range(_n):
    _o = pe + 24 + _opt + 40 * _i
    _vs, _va, _rs, _rp = struct.unpack_from("<4I", EXE, _o + 8)
    SECTIONS.append((0x400000 + _va, _rp, _rs))


def s16(v):
    v &= 0xffff
    return v - 0x10000 if v & 0x8000 else v


def s32(v):
    v &= 0xffffffff
    return v - 0x100000000 if v & 0x80000000 else v


def tdiv(a, b):
    """x86 idiv: quotient truncated toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def halve_off(x):
    """x - trunc(x/2): the region penalty (sar, then adc 0 when negative)."""
    return s32(x - tdiv(x, 2))


# ---------------------------------------------------------------- the rule (the minimal implementable model)
def cand_city(A, c):
    """FUN_0044ece4 candidate score, 32-bit. c: s (FUN_0044a98c), d (FUN_00449018 eax), same_allegiance, other_region,
    capital (FUN_0044b8d0)."""
    d = s16(c["d"])                          # kept as a word, sign-extended for use
    s = c["s"]
    if c.get("same_allegiance"):
        s = tdiv(s32(s * 9), 10)
    sc = s32(tdiv(s32(A * 110), s) - d)
    if c.get("other_region"):
        sc = halve_off(sc)
    if A > s and d < 7:
        sc = s32(sc * 2)
    if c.get("capital") and tdiv(s32(2 * s), 3) < A:
        sc = s32(sc * 2)
    return sc, d


def cand_army(A, c):
    """FUN_0044ee60 candidate score, 32-bit. c: s (FUN_0044a8cc of the target), d, other_region."""
    d = s16(c["d"])
    s = c["s"]
    sc = s32(tdiv(s32(A * 110), s) - d)
    if c.get("other_region"):
        sc = halve_off(sc)
    if sc > 1000:
        sc = 1000
    if A > s and d < 7:
        sc = s32(sc + 1000)
    return sc, d


def model(kind, A, cands, idx_before=None):
    """Original: best kept as a signed word, candidate (32-bit) wins only if > sign-extended best (strict: earlier wins ties),
    distance kept as a word, final word add. `wide`: the same with a 32-bit best and add (what the remake does)."""
    f = cand_city if kind == "city" else cand_army
    idx, best, dist = (-1 if kind == "city" else idx_before), -10000, 0
    widx, wbest, wdist = idx, -10000, 0
    scores = []
    for c in cands:
        sc, d = f(A, c)
        scores.append(sc)
        if sc > s16(best):
            idx, best, dist = c["index"], s16(sc), s16(d)
        if sc > wbest:
            widx, wbest, wdist = c["index"], sc, d
    return {"index": idx, "score": s16(best + dist), "stored_best": best, "dist": dist, "candidates": scores,
            "wide": {"index": widx, "score": wbest + wdist}}


# ---------------------------------------------------------------- emulator
class Emu:
    def __init__(self, ram):
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(0x400000, 0x300000)
        u.mem_map(0x800000, 0x10000)
        for va, rp, rs in SECTIONS:
            if rs:
                u.mem_write(va, EXE[rp:rp + rs])
        u.mem_write(ORIGIN, bytes(ram))
        self.u, self.ram = u, bytes(ram)
        self.stubs = {}
        self.rec = None
        for a in (0x44a930, 0x44a98c, 0x44a8cc, 0x449018, 0x44cab4, 0x44eb9c, 0x44b8d0,
                  0x44ed00, 0x44ed72, 0x44ed7d, 0x44ed95, 0x44edcd, 0x44edfa, 0x44ee16,
                  0x44ee7c, 0x44ef15, 0x44ef24, 0x44ef49, 0x44ef79):
            u.hook_add(UC_HOOK_CODE, self._hook, begin=a, end=a)

    def _cur(self, uc):
        """The candidate the scorer is visiting: ECE4 keeps the city index in edi, EE60 its army index at [ebp-0xe]."""
        if self.kind == "city":
            return uc.reg_read(UC_X86_REG_EDI) & 0xffff
        return s16(struct.unpack("<H", uc.mem_read(uc.reg_read(UC_X86_REG_EBP) - 0xe, 2))[0])

    def _hook(self, uc, a, size, data):
        eax = uc.reg_read(UC_X86_REG_EAX)
        if a in self.stubs:
            v = self.stubs[a](self, s16(eax))
            uc.reg_write(UC_X86_REG_EAX, v & 0xffffffff)
            sp = uc.reg_read(UC_X86_REG_ESP)
            uc.reg_write(UC_X86_REG_EIP, struct.unpack("<I", uc.mem_read(sp, 4))[0])
            uc.reg_write(UC_X86_REG_ESP, sp + 4)
            return
        r = self.rec
        if r is None:
            return
        ebp = uc.reg_read(UC_X86_REG_EBP)
        word = lambda off: s16(struct.unpack("<H", uc.mem_read(ebp + off, 2))[0])
        dword = lambda off: s32(struct.unpack("<I", uc.mem_read(ebp + off, 4))[0])
        if a in (0x44ed00, 0x44ee7c):
            r["A"] = s32(eax)
        elif a in (0x44ed72, 0x44ef15):
            r["cands"].append({"index": self._cur(uc), "d": eax & 0xffff})
        elif a in (0x44ed7d, 0x44ef24):
            r["cands"][-1]["s"] = s32(eax)
        elif a == 0x44ed95:
            r["cands"][-1]["same_allegiance"] = True
        elif a in (0x44edcd, 0x44ef49):
            r["cands"][-1]["other_region"] = bool(eax & 0xff)
        elif a == 0x44edfa:
            r["cands"][-1]["capital"] = bool(eax & 0xff)
        elif a == 0x44ee16:
            r["cands"][-1]["score"] = dword(-0x1c)
        elif a == 0x44ef79:
            r["cands"][-1]["score"] = s32(uc.reg_read(UC_X86_REG_EDI))

    def call(self, kind, army, idx_before=0x1234):
        self.kind = kind
        u = self.u
        u.mem_write(OUT, struct.pack("<3h", s16(idx_before), 0x5555 - 0x10000 if 0x5555 > 0x7fff else 0x5555, 0x6666))
        esp = 0x80f000
        u.mem_write(esp, struct.pack("<II", RET, OUT + 4))
        u.reg_write(UC_X86_REG_EAX, army)
        u.reg_write(UC_X86_REG_EDX, OUT)
        u.reg_write(UC_X86_REG_ECX, OUT + 2)
        u.reg_write(UC_X86_REG_ESP, esp)
        self.rec = {"cands": []}
        try:
            u.emu_start(ECE4 if kind == "city" else EE60, RET, count=20_000_000)
        except UcError as e:
            return {"error": str(e), "eip": hex(u.reg_read(UC_X86_REG_EIP)), "rec": self.rec}
        assert u.reg_read(UC_X86_REG_EIP) == RET and u.reg_read(UC_X86_REG_ESP) == esp + 8
        idx, score, dist = struct.unpack("<3h", u.mem_read(OUT, 6))
        assert bytes(u.mem_read(ORIGIN, len(self.ram))) == self.ram, "scorer changed game RAM"
        return {"index": idx, "score": score, "dist": dist, "eax": u.reg_read(UC_X86_REG_EAX), "rec": self.rec}


def put(ram, a, v):
    struct.pack_into("<h", ram, a - ORIGIN, v)


# ---------------------------------------------------------------- stubbed controls
N, X = 1, 5             # the scoring nation; the enemy nation


def staged(kind, k):
    """RAM where N is at war with every other nation; army 0 (owner N) scores. City: cities 1..k owned by X (allegiance X);
    army: armies 1..k owned by X, on land. The stubs decide everything else."""
    r = bytearray(RAM)
    put(r, CUR, N)
    for o in range(16):
        put(r, NATION + N * 0x494 + 0x26 + 2 * o, 0 if o == N else 3)
    put(r, ARMY + 4, N)
    put(r, ARMY + 8, 2)
    if kind == "army":
        put(r, ARMY_N, k + 1)
        for j in range(1, k + 1):
            put(r, ARMY + j * 0x290 + 4, X)
            put(r, ARMY + j * 0x290 + 8, 2)
    else:
        for i in range(334):
            put(r, CITY + i * 0x22 + 0x12, N)
            put(r, CITY + i * 0x22 + 0x14, N)
        for i in range(1, k + 1):
            put(r, CITY + i * 0x22 + 0x12, X)
            put(r, CITY + i * 0x22 + 0x14, X)
    return r


def stubs_for(kind, A, cands):
    by = {c["index"]: c for c in cands}
    st = {0x44cab4: lambda e, ax: 1 if e._cur(e.u) in by else 0,
          0x449018: lambda e, ax: by[e._cur(e.u)]["d"],
          0x44eb9c: lambda e, ax: int(by[e._cur(e.u)].get("other_region", False))}
    if kind == "city":
        st[0x44a930] = lambda e, ax: A
        st[0x44a98c] = lambda e, ax: by[ax]["s"]
        st[0x44b8d0] = lambda e, ax: int(by[ax].get("capital", False))
    else:
        st[0x44a8cc] = lambda e, ax: A if ax == 0 else by[ax]["s"]
    return st


def C(i, s, d, **kw):
    return dict(index=i, s=s, d=d, **kw)


CONTROLS = [
    # name, kind, A, candidates, what it shows
    ("city-ordinary", "city", 15000, [C(1, 22000, 10), C(2, 5000, 4)], "bounded: 65 vs 326 doubled (A>s, d<7) = 652; final 656"),
    ("city-32767", "city", 32777, [C(1, 110, 10)], "candidate 32767 stored as is; final add 32767+10 carries to -32759"),
    ("city-32768", "city", 32778, [C(1, 110, 10)], "candidate 32768 stored as -32768; final -32758"),
    ("city-65535", "city", 65545, [C(1, 110, 10)], "candidate 65535 stored as -1; final 9"),
    ("city-65536", "city", 65546, [C(1, 110, 10)], "candidate 65536 stored as 0; final 10"),
    ("city-final-no-carry", "city", 32767, [C(1, 110, 10)], "candidate 32757 + 10 = 32767: no carry"),
    ("city-final-carry", "city", 32768, [C(1, 110, 11)], "candidate 32757 + 11 = 32768: carries to -32768"),
    ("city-negative-halving", "city", 0, [C(1, 110, 7, other_region=True)], "-7 halved toward zero: -7 - (-3) = -4; final 3"),
    ("city-below-sentinel", "city", 0, [C(1, 110, 10001)], "-10001 is not > -10000: no target, index -1, score -10000"),
    ("city-just-above-sentinel", "city", 0, [C(1, 110, 9999)], "-9999 > -10000 wins; final 0"),
    ("city-two-truncated-first", "city", 40010, [C(1, 110, 10), C(2, 1000, 10)], "first 40000 kept as -25536, so the "
     "second (4391) beats it; wide keeps the first"),
    ("city-two-truncated-second", "city", 30010, [C(1, 110, 10), C(2, 80, 10)], "30000 then 41253: the second wins in both, "
     "but its stored -24283 makes the final negative"),
    ("city-tie-after-truncation", "city", 65646, [C(1, 110, 10), C(2, 6556, 10)], "first 65636 kept as 100; second 1091? "
     "no: see row"),
    ("city-distance-upper-bits", "city", 1100, [C(1, 110, 0x10003)], "distance eax 0x10003 kept as the word 3"),
    ("army-ordinary", "army", 15000, [C(1, 22000, 10), C(2, 5000, 4)], "bounded: 65 vs 326+1000 = 1326; final 1330"),
    ("army-cap", "army", 50000, [C(1, 110, 10)], "49990 capped at 1000; final 1010"),
    ("army-cap-plus-1000", "army", 50000, [C(1, 110, 3)], "capped 1000 then +1000 (A>s, d<7) = 2000; final 2003: the most "
     "a winner can hold"),
    ("army-negative-halving", "army", 0, [C(1, 110, 7, other_region=True)], "-7 -> -4; final 3"),
    ("army-no-target", "army", 0, [C(1, 110, 10001)], "no winner: index word untouched (0x1234), score -10000, dist 0"),
    ("army-two-capped-tie", "army", 50000, [C(1, 110, 10), C(2, 120, 20)], "both capped at 1000: the earlier wins"),
    ("army-negative-distance-word", "army", 0, [C(1, 110, 0x9c40)], "diagnostic: distance word 40000 = -25536 "
     "sign-extended: score +25536 -> 1000, d<7 -> +1000 if A>s (no: A=0); final 1000-25536 = -24536"),
    ("army-final-carry-diagnostic", "army", 50000, [C(1, 110, 32000)], "diagnostic: 1000 + 32000 = 33000 carries to -32536"),
]


def fix_tie():
    """The tie row: first candidate 65636 (kept as 100), second exactly 100: 100 > 100 is false, the first stays."""
    for i, c in enumerate(CONTROLS):
        if c[0] == "city-tie-after-truncation":
            # A=65646, s=110 -> 65646 - 10 = 65636; second: 65646*110/s - 10 = 100 -> s = 65646*110//110 = 65646
            CONTROLS[i] = (c[0], "city", 65646, [C(1, 110, 10), C(2, 65646, 10)],
                           "first 65636 kept as the word 100; second exactly 100 is not > 100, so the first stays "
                           "(final 110); wide also keeps the first")


fix_tie()


def run_controls(version):
    rows = []
    for name, kind, A, cands, what in CONTROLS:
        e = Emu(staged(kind, len(cands)))
        e.stubs = stubs_for(kind, A, cands)
        got = e.call(kind, 0)
        m = model(kind, A, cands, idx_before=0x1234)
        emu_scores = [c.get("score") for c in got["rec"]["cands"]]
        ok = "error" not in got and (got["index"], got["score"], got["dist"]) == (m["index"], m["score"], m["dist"]) \
            and emu_scores == m["candidates"]
        rows.append({"control": name, "scorer": kind, "A": A, "candidates": cands, "shows": what,
                     "emulated": {k: got.get(k) for k in ("index", "score", "dist", "error")}, "candidate_scores": emu_scores,
                     "model": {k: m[k] for k in ("index", "score", "stored_best", "dist")}, "wide": m["wide"],
                     "model_matches": ok, "wide_differs": (m["wide"]["index"], m["wide"]["score"]) != (m["index"], m["score"])})
        print(f"{name:32s} emu idx={got.get('index')} score={got.get('score')} dist={got.get('dist')} "
              f"model={m['index']},{m['score']} wide={m['wide']} {'OK' if ok else 'MISMATCH'}")
    # zero divisor: what the original does with s = 0 (diagnostic; reachability in the survey)
    for kind in ("city", "army"):
        e = Emu(staged(kind, 1))
        e.stubs = stubs_for(kind, 100, [C(1, 0, 10)])
        got = e.call(kind, 0)
        rows.append({"control": f"{kind}-zero-divisor", "scorer": kind, "A": 100, "candidates": [C(1, 0, 10)],
                     "shows": "s = 0: idiv by zero", "emulated": {"error": got.get("error"), "eip": got.get("eip")}})
        print(f"{kind}-zero-divisor: {got.get('error')} at {got.get('eip')}")
    write(f"controls-{version}.json", rows)


# ---------------------------------------------------------------- survey on original saves
def ram_from_sav(b):
    r = bytearray(RAM)
    r[MAP - ORIGIN:MAP - ORIGIN + 89600] = b[:89600]
    r[CITY - ORIGIN:CITY - ORIGIN + 11356] = b[89600:100956]
    a = struct.unpack_from("<h", b, 100956)[0]
    r[ARMY - ORIGIN:ARMY - ORIGIN + 198 * 656] = bytes(198 * 656)
    r[ARMY - ORIGIN:ARMY - ORIGIN + a * 656] = b[100958:100958 + a * 656]
    put(r, ARMY_N, a)
    of = 100958 + a * 656
    f = struct.unpack_from("<h", b, of)[0]
    r[FLEET - ORIGIN:FLEET - ORIGIN + f * 26] = b[of + 2:of + 2 + f * 26]
    put(r, FLEET_N, f)
    on = of + 2 + f * 26
    r[NATION - ORIGIN:NATION - ORIGIN + 16 * 1172] = b[on:on + 16 * 1172]
    return r, a


def corpus():
    pats = [str(ROOT / "saves/*.SAV"), str(ROOT / "artifacts/**/*.SAV"), str(Path.home() / "ic2-work-archive/**/*.SAV"),
            str(Path.home() / "ic2-work/**/*.SAV")]
    seen, out = set(), []
    for p in pats:
        for f in sorted(glob.glob(p, recursive=True)):
            if "/remake" in f or "remake/" in f:          # remake-written saves are not original states
                continue
            b = Path(f).read_bytes()
            h = hashlib.sha256(b).hexdigest()
            if h in seen or len(b) < 120000:
                continue
            seen.add(h)
            out.append((f, h))
    return out


def run_survey(version, limit):
    files = corpus()[:limit] if limit else corpus()
    calls = mism = 0
    agg = {k: {"max_candidate": None, "min_candidate": None, "max_winner_final": None, "truncated_winners": 0,
               "final_carries": 0, "zero_divisor": 0, "calls": 0, "calls_with_target": 0, "max_A": 0, "min_s": None,
               "max_A_over_s": 0.0, "examples": []} for k in ("city", "army")}
    for n, (f, h) in enumerate(files):
        ram, a = ram_from_sav(Path(f).read_bytes())
        if not 0 <= a <= 198:
            continue
        for i in range(a):
            owner = struct.unpack_from("<h", ram, ARMY + i * 0x290 + 4 - ORIGIN)[0]
            if owner < 0 or owner > 15:
                continue
            put(ram, CUR, owner)
            e = Emu(ram)
            for kind in ("city", "army"):
                got = e.call(kind, i)
                g = agg[kind]
                g["calls"] += 1
                calls += 1
                if "error" in got:
                    g["zero_divisor"] += 1
                    if len(g["examples"]) < 20:
                        g["examples"].append({"save": Path(f).name, "sha": h[:12], "army": i, "error": got["error"]})
                    continue
                cands = got["rec"]["cands"]
                A = got["rec"]["A"]
                m = model(kind, A, cands, idx_before=0x1234)
                if (m["index"], m["score"], m["dist"]) != (got["index"], got["score"], got["dist"]) or \
                        m["candidates"] != [c["score"] for c in cands]:
                    mism += 1
                g["max_A"] = max(g["max_A"], A)
                for c in cands:
                    sc = c["score"]
                    g["max_candidate"] = sc if g["max_candidate"] is None else max(g["max_candidate"], sc)
                    g["min_candidate"] = sc if g["min_candidate"] is None else min(g["min_candidate"], sc)
                    g["min_s"] = c["s"] if g["min_s"] is None else min(g["min_s"], c["s"])
                    if c["s"] > 0:
                        g["max_A_over_s"] = max(g["max_A_over_s"], A / c["s"])
                if m["index"] not in (-1, 0x1234) and cands:
                    g["calls_with_target"] += 1
                    win = s16(m["stored_best"]) + m["dist"]
                    g["max_winner_final"] = win if g["max_winner_final"] is None else max(g["max_winner_final"], win)
                    wsc = [c["score"] for c in cands if c["index"] == m["index"]][-1]
                    if wsc != s16(wsc):
                        g["truncated_winners"] += 1
                    if win != s16(win):
                        g["final_carries"] += 1
        if n % 100 == 0:
            print(f"{n}/{len(files)} saves, {calls} calls, {mism} model mismatches", flush=True)
    res = {"saves": len(files), "calls": calls, "model_mismatches": mism, "by_scorer": agg,
           "corpus_sha256": sorted(h for _, h in files)}
    write(f"survey-{version}.json", res)
    print(json.dumps({k: {x: v for x, v in g.items() if x != "examples"} for k, g in agg.items()}, indent=1))
    print("mismatches", mism)


def write(name, obj):
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / name, "x") as f:
        json.dump(obj, f, indent=1, default=str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["controls", "survey"])
    ap.add_argument("--version", default="v1")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    run_controls(a.version) if a.what == "controls" else run_survey(a.version, a.limit)


if __name__ == "__main__":
    sys.exit(main())
