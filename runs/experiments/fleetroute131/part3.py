#!/usr/bin/env python3.12
"""Research #131 part 3: inside FUN_0044e1fc for the fleet-phase cases. Each E1FC level is traced: the direct-line test
(CB40), the land-target replacement (FUN_0044939c), the waypoint (FUN_0044d174, group 0), the no-progress fallback (CEC8) with
its move, every walk (FUN_0044e094) with the cell it ended on, the recursion and the arrival branch. Every D174 result is
checked against the research #187 portable model (runs/experiments/navigation187/model.py `waypoint`), evaluated on the
emulator's live map at the moment of the call. Same inputs and no replaced helper as phase.py.

    python3.12 runs/experiments/fleetroute131/part3.py --version v1 [--dry]
"""
import argparse
import json
import struct
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "navigation187"))
import phase as P  # noqa: E402
import model as M  # noqa: E402
from common import machine, RAM_BASE, RAM_SIZE  # noqa: E402
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE  # noqa: E402
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP  # noqa: E402

DATA = P.DATA
FLEET = P.FLEET
s16 = P.s16


def pt(v):
    return [s16(v), s16(v >> 16)]


def word2(uc, a):
    return list(struct.unpack("<2h", uc.mem_read(a, 4)))


# Extra part-3 cases (same derivation as phase.py)
CASES3 = [
    ("p3-no-progress-sea-target", "stored-one",
     dict(fleet0={4: 49, 6: 63, 12: 25}),
     "route on the adjacent sea cell (49,63): distance 1 from the start, a direct step"),
    ("p3-carried-across-coast", "cargo-positive",
     dict(fleet0={4: 47, 6: 64, 12: 25}),
     "army aboard, land route (47,64) across the coast: where the carried army ends"),
]


def trace(name, ram):
    u = machine(ram)
    esp0 = 0x80f000
    u.mem_write(esp0, struct.pack("<I", 0x600000))
    u.reg_write(UC_X86_REG_ESP, esp0)
    levels, done, d174 = [], [], []
    row = dict(case=name, status="running")
    nf = P.rd(ram, 0x4a0326)

    def cur():
        return levels[-1] if levels else None

    def fpos(uc, f):
        return word2(uc, FLEET + 26 * f)

    def fmoves(uc, f):
        return s16(struct.unpack("<H", uc.mem_read(FLEET + 26 * f + 12, 2))[0])

    def hook(uc, a, size, data):
        sp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(sp, 4))[0]
        while levels and a == levels[-1]["_ret"] and sp == levels[-1]["_sp"] + 4:   # a true return from E1FC
            x = levels.pop()
            x.update(end=fpos(uc, x["fleet"]), moves_out=fmoves(uc, x["fleet"]))
            done.append(x)
        if a == 0x44b5d0:                          # naval combat from anywhere (walker contact or arrival): stop before it
            if levels:
                levels[-1]["arrival" if ret == 0x44e415 else "contact"] = f"naval combat FUN_0044b5d0 (from {ret:#x})"
            row["status"] = "stopped-before-naval-combat"
            uc.emu_stop()
            return
        if a == 0x44e1fc:
            f = uc.reg_read(UC_X86_REG_EAX) & 0xffff
            levels.append(dict(fleet=f, depth=len(levels), target=pt(uc.reg_read(UC_X86_REG_EDX)), start=fpos(uc, f),
                               moves_in=fmoves(uc, f), steps=[], _ret=ret, _sp=sp))
            return
        lv = cur()
        if lv is None:
            return
        f = lv["fleet"]
        if a == 0x44e2ce:                          # the -1 move of the no-progress branch (reached with or without a walk)
            lv["fallback_move_charged"] = True
        if a == 0x44e24a:
            lv["direct_line"] = bool(uc.reg_read(UC_X86_REG_EAX) & 0xff)
        elif a == 0x44939c and ret == 0x44e275:
            lv["replace_in"] = pt(uc.reg_read(UC_X86_REG_EAX))
        elif a == 0x44e275 and "replace_in" in lv and "replace_out" not in lv:
            lv["replace_out"] = word2(uc, sp + 4)
        elif a == 0x44d174 and ret == 0x44e287:
            origin, target = pt(uc.reg_read(UC_X86_REG_EDX)), pt(uc.reg_read(UC_X86_REG_ECX))
            lv["d174_in"] = dict(group=uc.reg_read(UC_X86_REG_EAX) & 0xffff, origin=origin, target=target)
            live = bytes(uc.mem_read(RAM_BASE, RAM_SIZE))
            try:
                m = M.waypoint(live, 0, tuple(origin), tuple(target))
                lv["model"] = dict(kind=m["kind"], point=list(m["point"]) if m["point"] else None, node=m["node"])
            except Exception as e:
                lv["model"] = dict(kind="model-undefined", error=str(e)[:200])
        elif a == 0x44e287:
            lv["d174_out"] = word2(uc, sp + 4)
        elif a == 0x44e094:
            kind = {0x44e258: "direct", 0x44e29a: "waypoint", 0x44e2ce: "fallback", 0x44e372: "arrival-sea-step"}.get(ret, hex(ret))
            lv["steps"].append(dict(walk=kind, goal=pt(uc.reg_read(UC_X86_REG_EDX)), from_=fpos(uc, f), moves=fmoves(uc, f)))
        elif a in (0x44e258, 0x44e29a, 0x44e2ce, 0x44e372) and lv["steps"] and "to" not in lv["steps"][-1]:
            if lv["steps"][-1]["walk"] == {0x44e258: "direct", 0x44e29a: "waypoint", 0x44e2ce: "fallback", 0x44e372: "arrival-sea-step"}[a]:
                lv["steps"][-1].update(to=fpos(uc, f), moves_after=fmoves(uc, f))
        elif a == 0x44e2bb:
            lv["cec8_out"] = word2(uc, sp + 4)
        elif a in (0x44b840, 0x44f7e4, 0x44b5d0) and ret in (0x44e38c, 0x44e3ce, 0x44e415):
            lv["arrival"] = {0x44b840: "landing FUN_0044b840", 0x44f7e4: "port FUN_0044f7e4", 0x44b5d0: "naval combat FUN_0044b5d0"}[a]
            if a == 0x44b5d0:
                row["status"] = "stopped-before-naval-combat"
                uc.emu_stop()

    u.hook_add(UC_HOOK_CODE, hook)
    try:
        u.emu_start(0x44f608, 0x600000, count=50_000_000)
        if row["status"] == "running":
            row["status"] = "complete"
    except Exception:
        row.update(status="error", error=traceback.format_exc()[-600:], eip=hex(u.reg_read(UC_X86_REG_EIP)))
    while levels:                                   # stopped inside a level
        x = levels.pop()
        x.update(end=fpos(u, x["fleet"]), moves_out=fmoves(u, x["fleet"]), unfinished=True)
        done.append(x)
    end = bytes(u.mem_read(RAM_BASE, RAM_SIZE))
    cargo = P.rd(ram, FLEET + 22)
    for x in done:
        x.pop("_ret", None)
        x.pop("_sp", None)
    row.update(levels=sorted(done, key=lambda x: (x["fleet"], x["depth"])),
               fleet0_after=P.fleet(end, 0), cargo_army=cargo,
               cargo_after=None if cargo < 0 else [P.rd(end, P.ARMY + 656 * cargo + 2 * k) for k in range(5)])
    row["d174_model_checks"] = [dict(fleet=x["fleet"], depth=x["depth"], original=x.get("d174_out"), model=x.get("model"),
                                     match=(x.get("model", {}).get("point") or [-1, None])[0:1] == x["d174_out"][0:1]
                                     if x.get("d174_out", [0])[0] < 0 else x.get("model", {}).get("point") == x.get("d174_out"))
                                for x in done if "d174_out" in x]
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    rows = []
    for d in sorted(P.INPUTS.iterdir()):
        if d.name == "rough-human-one":
            continue
        rows.append(dict(trace(d.name, (d / "input.ram").read_bytes()), source="fleet174 input replayed"))
    for name, base, edits, what in P.CASES + CASES3:
        r = trace(name, P.derive(base, **edits))
        r.update(source=f"derived from fleet174 {base}", isolates=what)
        rows.append(r)
    nm = sum(1 for r in rows for c in r["d174_model_checks"] if not c["match"])
    nc = sum(len(r["d174_model_checks"]) for r in rows)
    for r in rows:
        for x in r["levels"]:
            if x["fleet"] != 0:
                continue
            print(f"{r['case']:26s} d{x['depth']} tgt={x['target']} start={x['start']} mv={x['moves_in']} line={x.get('direct_line')} "
                  f"repl={x.get('replace_out')} d174={x.get('d174_out')} model={(x.get('model') or {}).get('point')} "
                  f"cec8={x.get('cec8_out')} walks={[ (s['walk'], s.get('to')) for s in x['steps']]} end={x['end']} mv={x['moves_out']} "
                  f"arr={x.get('arrival')}")
    print(f"D174 calls checked against the #187 model: {nc}, mismatches {nm}")
    if a.dry:
        return
    with open(DATA / f"part3-{a.version}.json", "x") as f:
        json.dump(dict(cases=rows, d174_checks=nc, d174_mismatches=nm), f, indent=1)


if __name__ == "__main__":
    main()
