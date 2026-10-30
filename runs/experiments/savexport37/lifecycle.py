#!/usr/bin/env python3.12
"""Research #37 Q3 (2026-10-31): what the original writes when it creates, launches, removes and relocates army and fleet
records, measured by executing the original routines on the #187 RAM snapshot (runs/experiments/navigation187/core.py).

Each control fills the record(s) the routine will write with a canary byte pattern, runs the routine, and reports which
byte offsets it wrote (changed from the canary) and which it left as residue. Presentation is stubbed (news line, string
helpers, sound). No game is run.

  ctor        FUN_00449f08(nation 1, point, &index): the army constructor every new army goes through
  fleet_order FUN_0044a004(nation 1, city, ships): the build order (human TBuildFleet_OK and AI FUN_00450768)
  launch      FUN_0044a050(fleet): the round tick's launch of a finished build
  compaction  FUN_0044adb0(): tombstones at chosen indices, an army aboard a fleet as the last army; the resulting
              table order and the fleet's carrier link

    python3.12 runs/experiments/savexport37/lifecycle.py --version v1
"""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
import core as C  # noqa: E402
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE  # noqa: E402
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-savexport37"
ARMIES, AREC, FLEETS, FREC = 0x47C1EC, 0x290, 0x49C26C, 0x1A
NCOUNT, FCOUNT = 0x4A0324, 0x4A0326
STUB = {0x449240: "news_line", 0x405B00: "str_copy", 0x405BC8: "str_cat", 0x405C98: "str_upper", 0x45BF28: "sound"}
CANARY = 0xA5


def run(ram, entry, eax=0, edx=0, ecx=0):
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

    def hook(uc, addr, size, data):
        if addr in STUB:
            sp = uc.reg_read(UC_X86_REG_ESP)
            uc.reg_write(UC_X86_REG_ESP, sp + 4)
            uc.reg_write(UC_X86_REG_EIP, struct.unpack("<I", uc.mem_read(sp, 4))[0])
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(entry, 0x600000, count=5_000_000)
    assert u.reg_read(UC_X86_REG_EIP) == 0x600000, hex(u.reg_read(UC_X86_REG_EIP))
    return bytearray(u.mem_read(C.ORIGIN, C.SIZE)), bytes(u.mem_read(0x700000, 16))


def written(before, after, base, size):
    return [i for i in range(size) if after[base - C.ORIGIN + i] != before[base - C.ORIGIN + i]]


def ranges(offs):
    out, start, prev = [], None, None
    for o in offs:
        if start is None:
            start = prev = o
        elif o == prev + 1:
            prev = o
        else:
            out.append([start, prev]); start = prev = o
    if start is not None:
        out.append([start, prev])
    return [f"+{a:#05x}" if a == b else f"+{a:#05x}..+{b:#05x}" for a, b in out]


def ctor():
    r = bytearray(C.RAM)
    C.put(r, 0x4A0320, 1)
    n = C.short(r, NCOUNT)
    base = ARMIES + n * AREC
    r[base - C.ORIGIN:base - C.ORIGIN + AREC] = bytes([CANARY]) * AREC
    p = tuple(C.xy(r, ARMIES + 3 * AREC))                           # next to Carthage's army 3, a land cell
    out, idx = run(r, 0x449F08, eax=1, edx=C.point((p[0] + 2, p[1])), ecx=0x700000)
    w = written(r, out, base, AREC)
    rec = {"index": struct.unpack("<h", idx[:2])[0], "count_before": n, "count_after": C.short(out, NCOUNT),
           "bytes_written": len(w), "written": ranges(w),
           "values": {"x,y": C.xy(out, base), "owner": C.short(out, base + 4), "moves": C.short(out, base + 6),
                      "cell(+8)": C.short(out, base + 8), "supplies(+0xA)": C.short(out, base + 0xA),
                      "money(+0xC)": C.short(out, base + 0xC), "morale(+0xE)": C.short(out, base + 0xE)},
           "map_marker": C.cell(out, tuple(C.xy(out, base)))}
    return rec


def fleet_order_and_launch():
    r = bytearray(C.RAM)
    C.put(r, 0x4A0320, 1)
    n = C.short(r, FCOUNT)
    base = FLEETS + n * FREC
    r[base - C.ORIGIN:base - C.ORIGIN + FREC] = bytes([CANARY]) * FREC
    city = next(i for i in range(334) if C.short(r, 0x479590 + i * 34 + 0x12) == 1)   # a Carthaginian city
    treasury = struct.unpack_from("<i", r, 0x474AA8 + 1 * 0x494 - C.ORIGIN)[0]
    o1, _ = run(r, 0x44A004, eax=1, edx=city, ecx=12)
    w1 = written(r, o1, base, FREC)
    order = {"index": n, "count_after": C.short(o1, FCOUNT), "bytes_written": len(w1), "written": ranges(w1),
             "values": {"owner(+8)": C.short(o1, base + 8), "countdown(+0xA)": C.short(o1, base + 0xA),
                        "ships(+0x12)": C.short(o1, base + 0x12), "build_city(+0x14)": C.short(o1, base + 0x14),
                        "carrier(+0x16)": C.short(o1, base + 0x16)},
               "treasury_change": struct.unpack_from("<i", o1, 0x474AA8 + 1 * 0x494 - C.ORIGIN)[0] - treasury}
    o2, _ = run(o1, 0x44A050, eax=n)
    w2 = written(o1, o2, base, FREC)
    launch = {"bytes_written": len(w2), "written": ranges(w2),
              "residue_still_canary": ranges([i for i in range(FREC) if o2[base - C.ORIGIN + i] == CANARY]),
              "values": {"x,y": C.xy(o2, base), "countdown(+0xA)": C.short(o2, base + 0xA), "moves(+0xC)": C.short(o2, base + 0xC),
                         "supplies(+0xE)": C.short(o2, base + 0xE), "money(+0x10)": C.short(o2, base + 0x10),
                         "condition(+0x14)": C.short(o2, base + 0x14), "carrier(+0x16)": C.short(o2, base + 0x16),
                         "+0x18": C.short(o2, base + 0x18)},
              "map_marker": C.cell(o2, tuple(C.xy(o2, base)))}
    return order, launch


def compaction():
    r = bytearray(C.RAM)
    n, nf = C.short(r, NCOUNT), C.short(r, FCOUNT)
    last = n - 1
    # the last army is aboard fleet 0: army cell -1 at the fleet's position, fleet carrier = last
    fpos = C.xy(r, FLEETS)
    C.put(r, ARMIES + last * AREC, fpos[0]); C.put(r, ARMIES + last * AREC + 2, fpos[1]); C.put(r, ARMIES + last * AREC + 8, -1)
    C.put(r, FLEETS + 0x16, last)
    tomb = [1, 4]                                                      # tombstones (owner -1)
    for i in tomb:
        C.put(r, ARMIES + i * AREC + 4, -1)
    ids = {i: bytes(r[ARMIES + i * AREC - C.ORIGIN:ARMIES + i * AREC - C.ORIGIN + 4]) for i in range(n)}
    out, _ = run(r, 0x44ADB0)
    n2 = C.short(out, NCOUNT)
    order = []
    for i in range(n2):
        rec = bytes(out[ARMIES + i * AREC - C.ORIGIN:ARMIES + i * AREC - C.ORIGIN + AREC])
        src = [j for j in range(n) if bytes(r[ARMIES + j * AREC - C.ORIGIN:ARMIES + j * AREC - C.ORIGIN + AREC]) == rec]
        order.append(src[0] if src else None)
    return {"count_before": n, "tombstones": tomb, "count_after": n2, "new_index_holds_old_index": order,
            "fleet0_carrier_before": last, "fleet0_carrier_after": C.short(out, FLEETS + 0x16),
            "vacated_slots_beyond_count_unchanged": all(out[ARMIES + i * AREC - C.ORIGIN:ARMIES + (i + 1) * AREC - C.ORIGIN]
                                                        == r[ARMIES + i * AREC - C.ORIGIN:ARMIES + (i + 1) * AREC - C.ORIGIN]
                                                        for i in range(n2, n))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"lifecycle-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    order, launch = fleet_order_and_launch()
    res = {"ram": "#187 snapshot (private)", "canary": CANARY, "ctor": ctor(), "fleet_order": order, "launch": launch,
           "compaction": compaction()}
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
