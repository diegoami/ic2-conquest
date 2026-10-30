#!/usr/bin/env python3.12
"""Research #37 Q1(b) (2026-10-31): do the 31 INERT nation bytes stay untouched through battle, siege, elimination and
treaty paths? The atlas (2026-10-21-original-sav-semantic-atlas.md) found no reader statically and in one Wine round; its
stated gap is untraversed states. This executes those paths in emulation on the #187 RAM snapshot.

All 16 nation records get a canary in +0x450..+0x46A, +0x46D, +0x491..+0x493 (31 × 16 = 496 bytes). A Unicorn memory hook
over the nation table reports every read or write that overlaps those bytes, with the instruction address. As a positive
control the same hook counts accesses to the live unity word +0x440 (and +0x490, the human flag next to the holes).
Presentation calls are stubbed (sound, map redraw, news line and its string helpers); the routines and their RNG run
unmodified.

Paths:
  treaty_honourable / treaty_sues  FUN_00450c68(winner, loser), both branches (`score(W) >= score(L) and armies(W) >= armies(L)`)
  battle                           FUN_0044aee4(attacker, defender): instant AI-vs-AI battle, loss, destruction, Random(5) treaty roll
  siege_elimination                FUN_0044b27c(army, city) on the last city of a nation: capture FUN_0044bb18 and
                                   elimination FUN_0044c528
  ai_round                         FUN_0044fa20 for every seat in turn order (diplomacy, economy, armies, fleets), current seat first

    python3.12 runs/experiments/savexport37/q1canary.py --version v1
"""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
import core as C  # noqa: E402
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE  # noqa: E402
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-savexport37"
NAT, NREC = 0x474670, 0x494
HOLES = list(range(0x450, 0x46B)) + [0x46D] + [0x491, 0x492, 0x493]
CONTROL = {0x440: "unity", 0x441: "unity", 0x490: "human"}
ARMIES, AREC = 0x47C1EC, 0x290
CITIES, CREC = 0x479590, 34
STUB = {0x45BF28: "sound", 0x445B38: "redraw", 0x449240: "news_line", 0x405B00: "str_copy", 0x405BC8: "str_cat",
        0x405C98: "str_upper", 0x45C084: "set_turn_title", 0x45BED4: "disable_nation_menu", 0x45BA6C: "refresh_forms"}


def canary(r):
    for n in range(16):
        for o in HOLES:
            r[NAT + n * NREC + o - C.ORIGIN] = 0x5A ^ (o & 0xFF) ^ n


def run(ram, entry, eax=0, edx=0, ecx=0, extra_stubs=None, budget=400_000_000):
    u = Uc(UC_ARCH_X86, UC_MODE_32)
    u.mem_map(0x400000, 0x300000)
    u.mem_map(0x700000, 0x110000)
    for va, rp, rs in C.SECTIONS:
        if rs:
            u.mem_write(va, C.EXE[rp:rp + rs])
    u.mem_write(C.ORIGIN, bytes(ram))
    esp = 0x80F000
    u.mem_write(esp, struct.pack("<I", 0x600000))
    for reg, v in ((UC_X86_REG_EAX, eax), (UC_X86_REG_EDX, edx), (UC_X86_REG_ECX, ecx), (UC_X86_REG_ESP, esp)):
        u.reg_write(reg, v)
    stubs = dict(STUB, **(extra_stubs or {}))
    hits, control, calls = [], {"unity": 0, "human": 0}, {}
    pc = [0]

    def code(uc, addr, size, data):
        pc[0] = addr
        if addr in stubs:
            calls[stubs[addr]] = calls.get(stubs[addr], 0) + 1
            sp = uc.reg_read(UC_X86_REG_ESP)
            uc.reg_write(UC_X86_REG_ESP, sp + 4)
            uc.reg_write(UC_X86_REG_EIP, struct.unpack("<I", uc.mem_read(sp, 4))[0])

    def mem(uc, access, addr, size, value, data):
        rel = addr - NAT
        n, off = rel // NREC, rel % NREC
        span = range(off, off + size)
        if any(o in HOLES for o in span):
            hits.append({"pc": hex(pc[0]), "kind": "write" if access == UC_HOOK_MEM_WRITE else "read", "nation": n,
                         "offset": hex(off), "size": size})
        for o in span:
            if o in CONTROL:
                control[CONTROL[o]] += 1
                break
    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, mem, begin=NAT, end=NAT + 16 * NREC - 1)
    u.emu_start(entry, 0x600000, count=budget)
    assert u.reg_read(UC_X86_REG_EIP) == 0x600000, hex(u.reg_read(UC_X86_REG_EIP))
    out = bytearray(u.mem_read(C.ORIGIN, C.SIZE))
    unchanged = all(out[NAT + n * NREC + o - C.ORIGIN] == ram[NAT + n * NREC + o - C.ORIGIN] for n in range(16) for o in HOLES)
    return out, {"hole_accesses": hits, "control_accesses": control, "stub_calls": calls, "canary_bytes_unchanged": unchanged}


def base(current=1):
    r = bytearray(C.RAM)
    canary(r)
    C.put(r, 0x4A0320, current)
    for n in range(16):
        r[NAT + n * NREC + 0x490 - C.ORIGIN] = 0                      # every seat AI: no human dialogs on these paths
    return r


def war(r, a, b):
    C.put(r, NAT + a * NREC + 0x26 + b * 2, 3)
    C.put(r, NAT + b * NREC + 0x26 + a * 2, 3)


def treaty(sues):
    r = base()
    w, l = (1, 8) if sues else (8, 1)            # Carthage vs Celtiberia; the branch depends on scores and army counts
    war(r, w, l)
    out, rep = run(r, 0x450C68, eax=w, edx=l)
    rep["relation_after"] = C.short(out, NAT + w * NREC + 0x26 + l * 2)
    return rep


def battle():
    r = base()
    a, d = 2, 10                                  # Carthage army 2 and Celtiberia army 10 in the snapshot
    war(r, C.short(r, ARMIES + a * AREC + 4), C.short(r, ARMIES + d * AREC + 4))
    p = C.xy(r, ARMIES + d * AREC)
    C.put(r, ARMIES + a * AREC, p[0] + 1); C.put(r, ARMIES + a * AREC + 2, p[1])
    out, rep = run(r, 0x44AEE4, eax=a, edx=d)
    rep["owners_after"] = [C.short(out, ARMIES + a * AREC + 4), C.short(out, ARMIES + d * AREC + 4)]
    return rep


def siege_elimination():
    r = base()
    a = 2
    att = C.short(r, ARMIES + a * AREC + 4)
    # the victim: Numidia (5) keeps one city, the target; all its others go to the attacker
    victim = 5
    own = [i for i in range(334) if C.short(r, CITIES + i * CREC + 0x12) == victim]
    target = own[0]
    for i in own[1:]:
        C.put(r, CITIES + i * CREC + 0x12, att)
    C.put(r, NAT + victim * NREC + 0x446, 1)                           # the victim's city count and list: just the target
    C.put(r, NAT + victim * NREC + 0x48, target)
    C.put(r, NAT + victim * NREC + 0x4A, -1)
    war(r, att, victim)
    cx, cy = C.xy(r, CITIES + target * CREC + 0xE)
    C.put(r, ARMIES + a * AREC, cx + 1); C.put(r, ARMIES + a * AREC + 2, cy)
    out, rep = run(r, 0x44B27C, eax=a, edx=target)
    rep["city_owner_after"] = C.short(out, CITIES + target * CREC + 0x12)
    rep["victim_unity_after"] = C.short(out, NAT + victim * NREC + 0x440)
    return rep


def ai_round():
    r = base()
    rep_all = {"hole_accesses": [], "control_accesses": {"unity": 0, "human": 0}, "seats": 0}
    cur = r
    for seat in range(16):
        C.put(cur, 0x4A0320, seat)
        cur, rep = run(cur, 0x44FA20)
        rep_all["hole_accesses"] += rep["hole_accesses"]
        for k, v in rep["control_accesses"].items():
            rep_all["control_accesses"][k] += v
        rep_all["seats"] += 1
    rep_all["canary_bytes_unchanged"] = all(cur[NAT + n * NREC + o - C.ORIGIN] == r[NAT + n * NREC + o - C.ORIGIN]
                                            for n in range(16) for o in HOLES)
    return rep_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"q1canary-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    paths = {"treaty_honourable": lambda: treaty(False), "treaty_sues": lambda: treaty(True), "battle": battle,
             "siege_elimination": siege_elimination, "ai_round": ai_round}
    res = {}
    for name, f in paths.items():
        if a.only and name not in a.only.split(","):
            continue
        try:
            res[name] = f()
        except Exception as e:                                  # recorded, not hidden
            res[name] = {"error": repr(e)}
        print(name, {k: (len(v) if k == "hole_accesses" else v) for k, v in res[name].items()})
    out.write_text(json.dumps({"ram": "#187 snapshot (private)", "holes": "+0x450..+0x46A, +0x46D, +0x491..+0x493",
                               "paths": res}, indent=1))


if __name__ == "__main__":
    main()
