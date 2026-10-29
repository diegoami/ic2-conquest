#!/usr/bin/env python3
"""Research #98 (delegated 2026-10-30): controls for the army walker FUN_0044d734's distance-1 tail, on the pinned unpatched
original EXE run in Unicorn (the method of runs/experiments/terrain42/original_steps.py). Never launches the game.

    python3.12 runs/experiments/walker98/tail_controls.py --exe EXE --dat DAT --output OUT.json

The tail (decompile :51629-51657): after its line loop, if the army is exactly 1 from the target, the walker reads the target
cell: terrain 2..11 -> walk into it again only if its cost < the army's moves (strict); a city marker 20..99 -> siege
(FUN_0044b27c) if the city's owner is at war with the current nation and moves > 0, else FUN_0044f6d8 if not at war; an army
marker 200..247 -> attack (FUN_0044aee4) if its owner is at war and moves > 0; anything else -> nothing.

Each case builds a synthetic all-plain map, puts the current nation's army 0 at `start` with `moves`, sets one target cell, a
city record or an enemy army record there when the case needs it, the relation, and the current seat's human flag. Only
presentation (redraw 0x445B38, sound 0x45BF28) is stubbed; the three contact routines are intercepted at their entry and
recorded (not run): a control of which branch the tail takes, not of the battle, siege or supply that follows.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_EIP

MAP, ARMIES, ARMY_LEN, ARMY_COUNT = 0x45E870, 0x47C1EC, 0x290, 0x4A0324
CITIES, CITY_LEN, RELATIONS, NATION_STRIDE = 0x479590, 0x22, 0x474696, 0x24A * 2
CUR_NATION, HUMAN0 = 0x4A0320, 0x474B00
CONTACT = {0x44AEE4: "attack", 0x44B27C: "siege", 0x44F6D8: "city_non_war"}
STEP = 0x44D420
EXE_SHA = "9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", type=Path, required=True)
    ap.add_argument("--dat", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise SystemExit("output exists; choose a new name")
    exe, dat = a.exe.read_bytes(), a.dat.read_bytes()
    assert sha(exe) == EXE_SHA, sha(exe)
    pe = struct.unpack_from("<I", exe, 0x3C)[0]
    n, opt = struct.unpack_from("<H", exe, pe + 6)[0], struct.unpack_from("<H", exe, pe + 20)[0]
    ib = struct.unpack_from("<I", exe, pe + 24 + 28)[0]
    secs = []
    for k in range(n):
        o = pe + 24 + opt + 40 * k
        vs, va, rs, rp = struct.unpack_from("<4I", exe, o + 8)
        secs.append((ib + va, rp, rs))
    terrain = dat[0x1F622:0x1F622 + 12 * 14]
    costs = [struct.unpack_from("<h", terrain, 14 * k + 12)[0] for k in range(12)]
    assert costs == [1, 3, 1, 1, 2, 4, 4, 4, 4, 4, 4, 4], costs

    def run(start, goal, moves, target_code, human, relation=0, city_owner=None, enemy_army_owner=None, extra=None):
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(0x400000, 0x300000)
        u.mem_map(0x800000, 0x10000)
        for va, rp, rs in secs:
            if rs:
                u.mem_write(va, exe[rp:rp + rs])
        u.mem_write(0x4792E4, terrain)
        u.mem_write(MAP, struct.pack("<h", 2) * (320 * 140))
        u.mem_write(CUR_NATION, struct.pack("<h", 0))
        u.mem_write(HUMAN0, bytes([int(human)]))
        u.mem_write(RELATIONS, struct.pack("<h", 0) * 16)                     # nation 0's row
        u.mem_write(RELATIONS + 2 * 1, struct.pack("<h", relation))             # nation 0 -> nation 1
        armies = 1
        rec = bytearray(ARMY_LEN)
        struct.pack_into("<8h", rec, 0, start[0], start[1], 0, moves, 2, 100, 100, 70)
        struct.pack_into("<4h", rec, 16, 0, 1, 3000, 6)
        u.mem_write(ARMIES, bytes(rec))
        u.mem_write(MAP + 2 * (start[0] * 140 + start[1]), struct.pack("<h", 200))
        if enemy_army_owner is not None:
            e = bytearray(ARMY_LEN)
            struct.pack_into("<8h", e, 0, goal[0], goal[1], enemy_army_owner, 8, 2, 100, 100, 70)
            struct.pack_into("<4h", e, 16, 0, 1, 3000, 6)
            u.mem_write(ARMIES + ARMY_LEN, bytes(e))
            armies = 2
        u.mem_write(ARMY_COUNT, struct.pack("<h", armies))
        u.mem_write(CITIES, bytes(CITY_LEN * 334))
        if city_owner is not None:
            c = bytearray(CITY_LEN)
            c[:5] = b"Testa"
            struct.pack_into("<10h", c, 14, goal[0], goal[1], city_owner, city_owner, 80, 100, 50, 20, 25, 5)
            u.mem_write(CITIES, bytes(c))
        u.mem_write(MAP + 2 * (goal[0] * 140 + goal[1]), struct.pack("<h", target_code))
        for (x, y), code in (extra or {}).items():
            u.mem_write(MAP + 2 * (x * 140 + y), struct.pack("<h", code))
        reached, steps = [], 0

        def hook(uc, addr, size, data):
            nonlocal steps
            if addr == STEP:
                steps += 1
            if addr in (0x445B38, 0x45BF28) or addr in CONTACT:
                if addr in CONTACT:
                    reached.append(CONTACT[addr])
                esp = uc.reg_read(UC_X86_REG_ESP)
                ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
                uc.reg_write(UC_X86_REG_ESP, esp + 4)
                uc.reg_write(UC_X86_REG_EIP, ret)
        u.hook_add(UC_HOOK_CODE, hook)
        esp = 0x80F000
        u.mem_write(esp, struct.pack("<I", 0x600000))
        u.reg_write(UC_X86_REG_ESP, esp)
        u.reg_write(UC_X86_REG_EAX, 0)
        u.reg_write(UC_X86_REG_EDX, goal[0] | (goal[1] << 16))
        u.reg_write(UC_X86_REG_ECX, 0)
        u.emu_start(0x44D734, 0x600000, count=500000)
        assert u.reg_read(UC_X86_REG_EIP) == 0x600000, hex(u.reg_read(UC_X86_REG_EIP))
        x, y, _, mv = struct.unpack("<4h", u.mem_read(ARMIES, 8))
        return {"final": [x, y], "moves_left": mv, "contact": reached, "step_calls": steps}

    P, F, M, R, S = 2, 4, 5, 6, 0                  # plain, forest (2), mountains (4), river (4), sea
    cases = []

    def case(name, start, goal, moves, code, **kw):
        cases.append((name, start, goal, moves, code, kw))

    # terrain target 1 away (start (10,10), goal (10,9))
    for code, cname, cost in ((P, "plain", 1), (F, "forest", 2), (M, "mountains", 4), (R, "river", 4)):
        for mv in sorted({cost - 1, cost, cost + 1} - {0, -1}):
            case(f"adjacent-{cname}-moves{mv}", (10, 10), (10, 9), mv, code)
    case("adjacent-sea-moves8", (10, 10), (10, 9), 8, S)
    # terrain target at the end of a 2-tile walk: after the first plain step the army has moves-1 left
    for code, cname, cost in ((F, "forest", 2), (M, "mountains", 4)):
        for mv in (cost, cost + 1, cost + 2):
            case(f"walk2-{cname}-moves{mv}", (10, 10), (10, 8), mv, code)
    # city markers
    case("city-own-moves8", (10, 10), (10, 9), 8, 20, city_owner=0)
    case("city-peace-moves8", (10, 10), (10, 9), 8, 21, city_owner=1, relation=0)
    case("city-war-moves8", (10, 10), (10, 9), 8, 21, city_owner=1, relation=3)
    case("city-war-moves0", (10, 10), (10, 9), 0, 21, city_owner=1, relation=3)
    case("city-war-walk2-moves1", (10, 10), (10, 8), 1, 21, city_owner=1, relation=3)
    # army markers
    case("army-war-moves8", (10, 10), (10, 9), 8, 203, enemy_army_owner=1, relation=3)
    case("army-peace-moves8", (10, 10), (10, 9), 8, 203, enemy_army_owner=1, relation=0)
    case("army-war-moves0", (10, 10), (10, 9), 0, 203, enemy_army_owner=1, relation=3)
    case("army-war-walk2-moves1", (10, 10), (10, 8), 1, 203, enemy_army_owner=1, relation=3)

    out = {"exe_sha256": sha(exe), "dat_sha256": sha(dat), "runner_sha256": sha(Path(__file__).read_bytes()),
           "terrain_costs": costs, "evidence": "Unicorn, original instructions; presentation stubbed; contact routines intercepted at entry",
           "cases": []}
    for name, start, goal, moves, code, kw in cases:
        row = {"name": name, "start": list(start), "goal": list(goal), "moves": moves, "target_code": code, **{k: v for k, v in kw.items()}}
        for human in (False, True):
            row["human" if human else "ai"] = run(start, goal, moves, code, human, **kw)
        out["cases"].append(row)
    with a.output.open("x") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    for r in out["cases"]:
        print(f"{r['name']:28} ai {r['ai']['final']} left {r['ai']['moves_left']:2} {r['ai']['contact']}   "
              f"human {r['human']['final']} left {r['human']['moves_left']:2} {r['human']['contact']}")


if __name__ == "__main__":
    main()
