#!/usr/bin/env python3
"""Research #42 part 2 (delegated 2026-10-30): fleet movement controls on the pinned unpatched original EXE in Unicorn (the method of
runs/experiments/terrain42/original_steps.py). Never launches the game.

    python3.12 runs/experiments/fleet42/fleet_controls.py --exe EXE --dat DAT --output OUT.json

Three entry points, each on a synthetic all-calm-sea map with fleet 0 (the current nation's, 30 ships, launched, empty):
- the fleet walker FUN_0044e094(fleet, target): step rules (rough sea 1 costs 3, calm 0 costs 1; laterals; markers; land);
- the human fleet handler TUnitMap_MoveHumanFleet (0x446E24) on a fake unit-map object whose +0x224 word is the fleet: it
  calls the walker, and again if the fleet is still short of the target with moves left; its UI calls
  (TUnitMap_UpdateUMSelection 0x446EF4, TUnitMap_EndUMSelection 0x446EAC) are stubbed;
- the AI fleet routine FUN_0044e1fc(fleet, target): every entry is counted (its recursion).
Only presentation and those UI calls are stubbed. Every coordinate store into the fleet record is logged (the path).
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_EIP

MAP, FLEETS, FLEET_LEN, CUR_NATION, HUMAN0 = 0x45E870, 0x49C26C, 26, 0x4A0320, 0x474B00
FLEET_COUNT = None                       # not needed by these routines' paths here
STUBS = {0x445B38: "redraw", 0x45BF28: "sound", 0x446EF4: "UpdateUMSelection", 0x446EAC: "EndUMSelection"}
EXE_SHA = "9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31"
SEA, ROUGH, LAND = 0, 1, 2


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
    assert sha(exe) == EXE_SHA
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
    assert costs[:2] == [1, 3], costs

    def run(entry, goal, moves, cells=None, start=(10, 10), human=True):
        u = Uc(UC_ARCH_X86, UC_MODE_32)
        u.mem_map(0x400000, 0x300000)
        u.mem_map(0x800000, 0x20000)
        for va, rp, rs in secs:
            if rs:
                u.mem_write(va, exe[rp:rp + rs])
        u.mem_write(0x4792E4, terrain)
        u.mem_write(MAP, struct.pack("<h", SEA) * (320 * 140))
        u.mem_write(CUR_NATION, struct.pack("<h", 0))
        u.mem_write(HUMAN0, bytes([int(human)]))
        rec = struct.pack("<13h", start[0], start[1], -1, -1, 0, -1, moves, 50, 0, 30, 90, -1, SEA)
        u.mem_write(FLEETS, rec)
        u.mem_write(MAP + 2 * (start[0] * 140 + start[1]), struct.pack("<h", 300))
        for (x, y), code in (cells or {}).items():
            u.mem_write(MAP + 2 * (x * 140 + y), struct.pack("<h", code))
        path, entries, stubbed, trail = [], [], [], []

        steps = []

        def hook(uc, addr, size, data):
            trail.append(addr)
            del trail[:-40]
            if addr == 0x44DD70:                                  # the fleet step: position before each step
                steps.append(list(struct.unpack("<2h", uc.mem_read(FLEETS, 4))) + [struct.unpack("<h", uc.mem_read(FLEETS + 12, 2))[0]])
            if addr == 0x44E1FC:
                entries.append(list(struct.unpack("<2h", uc.mem_read(FLEETS, 4))) + [struct.unpack("<h", uc.mem_read(FLEETS + 12, 2))[0]])
            if addr in STUBS:
                stubbed.append(STUBS[addr])
                esp = uc.reg_read(UC_X86_REG_ESP)
                ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
                uc.reg_write(UC_X86_REG_ESP, esp + 4)
                uc.reg_write(UC_X86_REG_EIP, ret)
        u.hook_add(UC_HOOK_CODE, hook)

        def write(uc, access, addr, size, value, data):
            if addr in (FLEETS, FLEETS + 2):
                path.append(("x" if addr == FLEETS else "y", value & 0xFFFF))
        u.hook_add(UC_HOOK_MEM_WRITE, write)
        esp = 0x81F000
        u.mem_write(esp, struct.pack("<I", 0x600000))
        u.reg_write(UC_X86_REG_ESP, esp)
        target = goal[0] | (goal[1] << 16)
        if entry == 0x446E24:
            obj = 0x810000
            u.mem_write(obj, bytes(0x400))
            u.mem_write(obj + 0x224, struct.pack("<h", 0))
            u.reg_write(UC_X86_REG_EAX, obj)
        else:
            u.reg_write(UC_X86_REG_EAX, 0)
        u.reg_write(UC_X86_REG_EDX, target)
        u.reg_write(UC_X86_REG_ECX, 0)
        try:
            u.emu_start(entry, 0x600000, count=2000000)
        except Exception as e:
            return {"error": str(e), "last_addresses": [hex(t) for t in trail[-12:]], "routine_entries": entries,
                    "partial_cells": [p for p in path]}
        assert u.reg_read(UC_X86_REG_EIP) == 0x600000, hex(u.reg_read(UC_X86_REG_EIP))
        x, y = struct.unpack("<2h", u.mem_read(FLEETS, 4))
        mv = struct.unpack("<h", u.mem_read(FLEETS + 12, 2))[0]
        # rebuild visited cells from the coordinate stores
        cur, visited = list(start), []
        for f, v in path:
            cur[0 if f == "x" else 1] = v if v < 32768 else v - 65536
            if not visited or visited[-1] != tuple(cur):
                visited.append(tuple(cur))
        cells = [s_[:2] for s_ in steps] + [[x, y]]
        dedup = [c for k, c in enumerate(cells) if k == 0 or c != cells[k - 1]]
        return {"final": [x, y], "moves_left": mv, "cells": dedup, "step_calls": len(steps), "routine_entries": entries,
                "stubbed": sorted(set(stubbed))}

    W = 0x44E094
    cases = [
        ("walk-calm-3", W, (10, 7), 8, None),
        ("walk-rough-on-line-laterals-calm", W, (10, 6), 8, {(10, 9): ROUGH}),
        ("walk-rough-on-line-east-rough", W, (10, 6), 8, {(10, 9): ROUGH, (11, 9): ROUGH}),
        ("walk-rough-on-line-east-marker", W, (10, 6), 8, {(10, 9): ROUGH, (11, 9): 301}),
        ("walk-rough-all-three", W, (10, 6), 8, {(10, 9): ROUGH, (11, 9): ROUGH, (9, 9): ROUGH}),
        ("terminal-rough-cost3-moves3", W, (10, 9), 3, {(10, 9): ROUGH}),
        ("terminal-rough-cost3-moves2", W, (10, 9), 2, {(10, 9): ROUGH}),
        ("terminal-rough-cost3-moves4", W, (10, 9), 4, {(10, 9): ROUGH}),
        ("island-on-line", W, (10, 6), 8, {(10, 9): LAND}),
        ("wall-of-land", W, (10, 6), 8, {(9, 9): LAND, (10, 9): LAND, (11, 9): LAND}),
        ("long-wall-short-walk", W, (10, 2), 12, {(x, 8): LAND for x in range(6, 14)}),
    ]
    out = {"exe_sha256": sha(exe), "dat_sha256": sha(dat), "runner_sha256": sha(Path(__file__).read_bytes()),
           "terrain_costs": costs, "evidence": "Unicorn, original instructions; presentation and unit-map UI calls stubbed",
           "walker": [], "human_handler_vs_walker": [], "ai_routine": []}
    for name, entry, goal, mv, cells in cases:
        out["walker"].append({"name": name, "goal": list(goal), "moves": mv, "cells_set": {f"{x},{y}": c for (x, y), c in (cells or {}).items()},
                              **run(entry, goal, mv, cells)})
    # human handler vs one walker call, on cases where one walk may end short with moves left
    for name, goal, mv, cells in (("wall-of-land", (10, 6), 8, {(9, 9): LAND, (10, 9): LAND, (11, 9): LAND}),
                                  ("long-wall", (10, 2), 12, {(x, 8): LAND for x in range(6, 14)}),
                                  ("island-on-line", (10, 6), 8, {(10, 9): LAND}),
                                  ("calm-straight", (10, 4), 8, None)):
        out["human_handler_vs_walker"].append({"name": name, "goal": list(goal), "moves": mv,
                                               "walker_once": run(W, goal, mv, cells), "human_handler": run(0x446E24, goal, mv, cells)})
    # search: random small obstacle maps where the human handler's second walk changes the result
    import random
    rnd = random.Random(42)
    found = []
    for trial in range(400):
        cells = {}
        for _ in range(rnd.randint(3, 9)):
            cells[(rnd.randint(7, 16), rnd.randint(3, 9))] = rnd.choice([LAND, LAND, ROUGH])
        cells.pop((10, 10), None)
        goal = (rnd.randint(5, 18), rnd.randint(1, 5))
        if goal in cells:
            continue
        once, handler = run(W, goal, 10, cells), run(0x446E24, goal, 10, cells)
        if once["final"] != handler["final"]:
            found.append({"trial": trial, "goal": list(goal), "moves": 10, "cells_set": {f"{x},{y}": c for (x, y), c in cells.items()},
                          "walker_once": once, "human_handler": handler})
    out["human_handler_search"] = {"trials": 400, "seed": 42, "differing": len(found), "examples": found[:6]}

    # AI fleet routine: direct-path recursion
    for name, goal, mv, cells in (("ai-calm-far", (10, 2), 8, None), ("ai-wall", (10, 2), 12, {(x, 8): LAND for x in range(6, 14)}),
                                  ("ai-island", (10, 6), 8, {(10, 9): LAND})):
        out["ai_routine"].append({"name": name, "goal": list(goal), "moves": mv, **run(0x44E1FC, goal, mv, cells, human=False)})
    with a.output.open("x") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    for r in out["walker"]:
        print(f"walker {r['name']:36} -> {r['final']} left {r['moves_left']} via {r['cells']}")
    for r in out["human_handler_vs_walker"]:
        print(f"human  {r['name']:20} once {r['walker_once']['final']} left {r['walker_once']['moves_left']}  handler {r['human_handler']['final']} left {r['human_handler']['moves_left']}")
    print(f"search: {out['human_handler_search']['differing']} of 400 random maps where the handler's second walk changes the result")
    for ex in out["human_handler_search"]["examples"][:3]:
        print(f"   goal {ex['goal']} once {ex['walker_once']['final']} left {ex['walker_once']['moves_left']} via {ex['walker_once']['cells']} | handler {ex['human_handler']['final']} left {ex['human_handler']['moves_left']}")
    for r in out["ai_routine"]:
        if "error" in r:
            print(f"ai     {r['name']:20} ERROR {r['error']} after {r['last_addresses'][-6:]} entries {r['routine_entries']}")
        else:
            print(f"ai     {r['name']:20} -> {r['final']} left {r['moves_left']} entries {len(r['routine_entries'])} {r['routine_entries']}")


if __name__ == "__main__":
    main()
