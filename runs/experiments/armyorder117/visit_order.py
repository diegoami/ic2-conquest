#!/usr/bin/env python3.12
"""Research #117 part 2: does the AI army phase FUN_0044f31c decide differently when the same armies sit in a different table
order? Unicorn on the pinned unpatched EXE with the #187 live-RAM snapshot (runs/experiments/navigation187/core.py; 270 BC, 14
armies). For each nation with two armies, F31C runs twice from the same RAM: as captured, and with the two records swapped
(records exchanged whole; map markers are by position, so unchanged; fleet carried-army links repointed). Random draws run
(the stream is shared, so the visit order also decides who gets which draw). Attacks (FUN_0044aee4), sieges (FUN_0044b27c) and
the AI fleet move are logged with their arguments and skipped (they would open the battle UI). Compared per army identity:
final cell, moves, the calls logged for it, and the RNG draws consumed.

    python3.12 runs/experiments/armyorder117/visit_order.py --version v1
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
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EIP  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-armyorder117"
A, REC = 0x47c1ec, 656
SKIP = {0x44aee4: "attack_army", 0x44b27c: "siege_city"}
STUB = {0x445b38: "redraw", 0x45bf28: "sound"}            # presentation only (as runs/experiments/fleet42/fleet_controls.py)
WATCH = {0x44dba8: "army_move", 0x44f6d8: "own_city_contact", 0x4509f0: "merge_small", 0x44e41c: "army_upkeep"}


def swap(r, i, j):
    a, b = A + i * REC - C.ORIGIN, A + j * REC - C.ORIGIN
    r[a:a + REC], r[b:b + REC] = bytes(r[b:b + REC]), bytes(r[a:a + REC])
    for f in range(C.short(r, 0x4a0326)):
        p = 0x49c26c + 26 * f + 22
        v = C.short(r, p)
        if v in (i, j):
            C.put(r, p, j if v == i else i)


def run(ram, entry=0x44f31c):
    u = Uc(UC_ARCH_X86, UC_MODE_32)
    u.mem_map(0x400000, 0x300000)
    u.mem_map(0x700000, 0x110000)
    for va, rp, rs in C.SECTIONS:
        if rs:
            u.mem_write(va, C.EXE[rp:rp + rs])
    u.mem_write(C.ORIGIN, bytes(ram))
    esp = 0x80f000
    u.mem_write(esp, struct.pack("<I", 0x600000))
    u.reg_write(UC_X86_REG_ESP, esp)
    log, draws = [], [0]

    def hook(uc, addr, size, data):
        if addr == 0x40284c:
            draws[0] += 1
        if addr in WATCH:
            log.append({"call": WATCH[addr], "army": uc.reg_read(UC_X86_REG_EAX) & 0xFFFF, "edx": uc.reg_read(UC_X86_REG_EDX)})
        if addr in STUB:
            sp = uc.reg_read(UC_X86_REG_ESP)
            uc.reg_write(UC_X86_REG_ESP, sp + 4)
            uc.reg_write(UC_X86_REG_EIP, struct.unpack("<I", uc.mem_read(sp, 4))[0])
            return
        if addr in SKIP:
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            log.append({"call": SKIP[addr], "army": uc.reg_read(UC_X86_REG_EAX) & 0xFFFF, "target": uc.reg_read(UC_X86_REG_EDX) & 0xFFFF,
                        "draw_index": draws[0]})
            uc.reg_write(UC_X86_REG_ESP, sp + 4)
            uc.reg_write(UC_X86_REG_EIP, ret)
    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(entry, 0x600000, count=200_000_000)
    assert u.reg_read(UC_X86_REG_EIP) == 0x600000
    return bytearray(u.mem_read(C.ORIGIN, C.SIZE)), log, draws[0]


def state(r, i):
    p = A + i * REC
    return {"x": C.short(r, p), "y": C.short(r, p + 2), "owner": C.short(r, p + 4), "moves": C.short(r, p + 6),
            "troops": sum(C.short(r, p + 16 + 32 * k + 4) for k in range(20)), "money": C.short(r, p + 12),
            "supplies": C.short(r, p + 10)}


def small_units(r, i, n, troops):
    p = A + i * REC - C.ORIGIN
    r[p + 16:p + REC] = bytes(REC - 16)
    for k in range(n):
        struct.pack_into("<4h", r, p + 16 + 32 * k, 0, k % 2, troops, 6)
        r[p + 24 + 32 * k:p + 24 + 32 * k + 4] = f"M{i}{k}".encode().ljust(4, b"\0")   # same length: a shorter slice would shift the table


def merge_case(rows):
    """Nation 1's armies 2 (42,63) and 3, staged small (3 units of 4,000 = 12,000) and 3 placed at (45,63): FUN_004509f0 run
    directly, in the captured order and with 2 and 3 swapped."""
    base = bytearray(C.RAM)
    C.put(base, 0x4a0320, 1)
    C.place_army(base, 3, (45, 63))
    small_units(base, 2, 3, 4000)
    small_units(base, 3, 3, 4000)
    out = {}
    for name, ram in (("captured", base), ("swapped", None)):
        if ram is None:
            ram = bytearray(base)
            swap(ram, 2, 3)
        r, log, d = run(ram, 0x4509f0)
        out[name] = [dict(state(r, k), record=k, first_unit=bytes(r[A + k * REC - C.ORIGIN + 24:A + k * REC - C.ORIGIN + 28]).decode("latin1"))
                     for k in (2, 3)]
        out[name + "_draws"] = d
    rows.append({"case": "merge_small (FUN_004509f0)", "armies_before": {"record2": [42, 63], "record3": [45, 63]}, "result": out})
    print("merge captured", out["captured"])
    print("merge swapped ", out["swapped"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    out = DATA / f"visit-order-{v}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    n = C.short(C.RAM, 0x4a0324)
    rows = []
    for nation in (0, 1, 2):
        idx = [i for i in range(n) if C.short(C.RAM, A + i * REC + 4) == nation]
        i, j = idx
        base = bytearray(C.RAM)
        C.put(base, 0x4a0320, nation)
        r1, log1, d1 = run(base)
        sw = bytearray(base)
        swap(sw, i, j)
        r2, log2, d2 = run(sw)
        ident = {i: j, j: i}                                   # record i of run 1 is record j of run 2
        per = {}
        for k in (i, j):
            per[f"army{k}"] = {"captured_order": state(r1, k), "swapped_order": state(r2, ident[k])}
        rename = lambda e: dict(e, army=ident.get(e["army"], e["army"])) if "army" in e else e
        row = {"nation": nation, "armies": idx, "armies_state": per,
               "same_outcome": all(p["captured_order"] == p["swapped_order"] for p in per.values()),
               "calls_captured": log1, "calls_swapped_renamed": [rename(e) for e in log2],
               "calls_same_multiset": sorted(json.dumps(e, sort_keys=True) for e in log1 if e["call"] != "army_upkeep")
               == sorted(json.dumps(rename(e), sort_keys=True) for e in log2 if e["call"] != "army_upkeep"),
               "rng_draws": [d1, d2]}
        rows.append(row)
        print("nation", nation, "armies", idx, "same outcome", row["same_outcome"], "draws", d1, d2)
        for k, p in per.items():
            print("  ", k, p["captured_order"], "|", p["swapped_order"])
    merge_case(rows)
    out.write_text(json.dumps({"ram": "#187 snapshot (private)", "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
