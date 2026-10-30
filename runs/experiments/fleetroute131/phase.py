#!/usr/bin/env python3.12
"""Research #131 parts 1-2: the stored fleet route's lifetime inside the fleet phase FUN_0044f608, and the phase's order and
selection, run as unmodified original instructions under Unicorn (no helper, Random, movement or contact routine replaced;
the run stops before naval combat FUN_0044b5d0, as fleet174 did).

    python3.12 runs/experiments/fleetroute131/phase.py --version v1

Inputs: the fleet174 synthetic phase inputs (artifacts/run-exp-fleet-actions174/inputs-v1/<case>/input.ram, private), replayed
as they are, and new cases derived from them (declared in CASES below). Every write to any fleet's route words (+4..+7), every
E1FC call with its call site, every Random draw and every write to fleet 0's position/moves and to the cargo army are logged.
Outputs: runs/experiments/data/run-exp-fleetroute131/phase-<version>.json (exclusive create). RAM stays private.
"""
import argparse
import json
import struct
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "fleet174-actions"))
from common import machine, RAM_BASE, RAM_SIZE  # noqa: E402  (pinned EXE, hash-checked there)
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE  # noqa: E402
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EDX, UC_X86_REG_ESP, UC_X86_REG_EIP  # noqa: E402

ROOT = HERE.parents[2]
INPUTS = ROOT / "artifacts/run-exp-fleet-actions174/inputs-v1"
DATA = ROOT / "runs/experiments/data/run-exp-fleetroute131"
FLEET, ARMY, MAP = 0x49c26c, 0x47c1ec, 0x45e870
SITES = {0x44f66c: "stored-route (0x44F667)", 0x44f69f: "hunt (0x44F69A)", 0x44f6c3: "port (0x44F6BE)"}


def s16(v):
    v &= 0xffff
    return v - 0x10000 if v & 0x8000 else v


def rd(ram, a):
    return struct.unpack_from("<h", ram, a - RAM_BASE)[0]


def put(ram, a, v):
    struct.pack_into("<h", ram, a - RAM_BASE, v)


def cell(ram, x, y):
    return rd(ram, MAP + 2 * (x * 140 + y))


def fleet(ram, f):
    return [rd(ram, FLEET + 26 * f + 2 * k) for k in range(13)]


def derive(base, **edits):
    """A new input from a fleet174 input: fleet0 fields by offset, extra fleets, relations, the cargo army."""
    r = bytearray((INPUTS / base / "input.ram").read_bytes())
    for off, v in edits.get("fleet0", {}).items():
        put(r, FLEET + off, v)
    for f, fields in edits.get("fleets", {}).items():
        for off, v in fields.items():
            put(r, FLEET + 26 * f + off, v)
    if "nfleets" in edits:
        put(r, 0x4a0326, edits["nfleets"])
    for (a, b), v in edits.get("relations", {}).items():
        put(r, 0x474670 + a * 0x494 + 0x26 + 2 * b, v)
    for off, v in edits.get("army3", {}).items():
        put(r, ARMY + 3 * 656 + off, v)
    for (x, y), v in edits.get("cells", {}).items():
        put(r, MAP + 2 * (x * 140 + y), v)
    return r


# name, base input, edits, what it isolates
CASES = [
    # --- part 1: the route is never written inside the phase
    ("route-landing-cargo", "cargo-positive", dict(fleet0={4: 47, 6: 64, 12: 25}),
     "route on a land cell (47,64) next to sea, army aboard: movement then the arrival's land branch"),
    ("route-landing-no-cargo", "stored-one", dict(fleet0={4: 47, 6: 64, 12: 25}),
     "the same land route without cargo: the arrival's land branch needs +0x16 > -1"),
    ("route-own-port", "stored-one", dict(fleet0={4: 47, 6: 63, 12: 25}),
     "route on own city 30 (47,63), code 21: the arrival's city branch, not at war -> FUN_0044f7e4"),
    ("route-inland", "stored-one", dict(fleet0={4: 41, 6: 57, 12: 25}),
     "route on an inland cell (41,57): no sea approach"),
    ("route-x-minus2", "stored-one", dict(fleet0={4: -2, 6: 66, 12: 25}),
     "x = -2: the signed test treats every negative x as absent"),
    ("route-x-minus1-y-kept", "stored-one", dict(fleet0={4: -1, 6: 66, 12: 25}),
     "x = -1 with y = 66 left over: absent; y is not read"),
    ("route-x-0-residue", "stored-one", dict(fleet0={4: 0, 6: 0, 12: 25}),
     "x = 0 (the split residue (0;0)): present, so the phase steers to (0,0)"),
    ("route-zero-moves", "stored-one", dict(fleet0={12: 0}),
     "stored route (48,66), moves 0: E1FC is still called"),
    ("route-reached", "stored-one", dict(fleet0={0: 48, 2: 66, 4: 48, 6: 66, 12: 25}, cells={(49, 62): 0, (48, 66): 333}),
     "the fleet already stands on its route cell: distance 0"),
    ("adjacent-landing-cargo", "cargo-positive",
     dict(fleet0={0: 48, 2: 64, 4: 47, 6: 64, 12: 25}, army3={0: 48, 2: 64}, cells={(49, 62): 0, (48, 64): 333}),
     "fleet at (48,64), army aboard, route on the land cell (47,64) at distance 1: the arrival's land branch"),
    ("adjacent-landing-no-cargo", "stored-one",
     dict(fleet0={0: 48, 2: 64, 4: 47, 6: 64, 12: 25}, cells={(49, 62): 0, (48, 64): 333}),
     "the same without cargo"),
    ("adjacent-own-port", "stored-one",
     dict(fleet0={0: 48, 2: 64, 4: 47, 6: 63, 12: 25}, cells={(49, 62): 0, (48, 64): 333}),
     "fleet at (48,64), route on own city 30 (47,63) at distance 1: the arrival's city branch"),
    # --- part 2: order and selection
    ("no-route-zero-moves", "stored-one", dict(fleet0={4: -1, 12: 0}),
     "no route, moves 0: prepass and port pick run, no hunt and no move"),
]
# Hunt controls: strengths below 10 make Random(4)*(base/10) = 0, so every score is fixed while the draws still happen.
_ACTOR = {4: -1, 12: 25, 18: 1, 20: 50}                       # strength 1*50/10 = 5
_TARGET = {4: -1, 6: -1, 8: 3, 10: -1, 12: 10, 18: 1, 20: 20, 22: -1, 24: 0}   # strength 2
_WAR = {(1, 3): 3, (3, 1): 3}
CASES += [
    ("hunt-tie-a", "stored-one",
     dict(fleet0=_ACTOR, nfleets=3, relations=_WAR, fleets={1: {**_TARGET, 0: 52, 2: 62}, 2: {**_TARGET, 0: 49, 2: 65}},
          cells={(52, 62): 335, (49, 65): 335}),
     "two targets, same strength 2, both at distance 3: (5*100/2 - 3)*2 = 494 each; fleet 1 (52,62) is first"),
    ("hunt-tie-b", "stored-one",
     dict(fleet0=_ACTOR, nfleets=3, relations=_WAR, fleets={1: {**_TARGET, 0: 49, 2: 65}, 2: {**_TARGET, 0: 52, 2: 62}},
          cells={(52, 62): 335, (49, 65): 335}),
     "the same two positions with the table order swapped"),
    ("hunt-protected", "stored-one",
     dict(fleet0=_ACTOR, nfleets=2, relations=_WAR, fleets={1: {**_TARGET, 0: 48, 2: 64}}, cells={(48, 64): 335, (47, 63): 23}),
     "the only target at (48,64), next to a map city cell coded for its owner (23 = 20+3) at (47,63): protected"),
    ("hunt-unprotected-2", "stored-one",
     dict(fleet0=_ACTOR, nfleets=2, relations=_WAR, fleets={1: {**_TARGET, 0: 49, 2: 65}}, cells={(49, 65): 335, (47, 63): 23}),
     "the same city code, target at (49,65), 2 from it (outside the 3x3): hunted"),
]


def run_case(name, ram):
    u = machine(ram)
    esp = 0x80f000
    u.mem_write(esp, struct.pack("<I", 0x600000))
    u.reg_write(UC_X86_REG_ESP, esp)
    nf = rd(ram, 0x4a0326)
    row = dict(case=name, status="running", e1fc=[], route_writes=[], draws=[], fleet0_writes=[], cargo_writes=[], calls=[])
    pend = []
    cargo = rd(ram, FLEET + 22)

    def hook(uc, a, size, data):
        if pend and a == pend[-1]["ret"]:
            p = pend.pop()
            row["draws"].append(dict(bound=p["bound"], result=uc.reg_read(UC_X86_REG_EAX), site=hex(p["ret"])))
        if a == 0x40284c:
            ret = struct.unpack("<I", uc.mem_read(uc.reg_read(UC_X86_REG_ESP), 4))[0]
            pend.append(dict(bound=uc.reg_read(UC_X86_REG_EAX), ret=ret))
        if a == 0x44e1fc:
            sp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", uc.mem_read(sp, 4))[0]
            f = uc.reg_read(UC_X86_REG_EAX) & 0xffff
            edx = uc.reg_read(UC_X86_REG_EDX)
            row["e1fc"].append(dict(fleet=f, goal=[s16(edx), s16(edx >> 16)], site=SITES.get(ret, "recursion" if ret == 0x44e302 else hex(ret)),
                                    pos=list(struct.unpack("<2h", uc.mem_read(FLEET + 26 * f, 4))),
                                    moves=s16(struct.unpack("<H", uc.mem_read(FLEET + 26 * f + 12, 2))[0])))
        if a in (0x44e5dc, 0x44e9a8, 0x44f4f8, 0x44e094, 0x44939c, 0x44d174, 0x44cec8, 0x44b840, 0x44f7e4, 0x44b79c):
            ret = struct.unpack("<I", uc.mem_read(uc.reg_read(UC_X86_REG_ESP), 4))[0]
            row["calls"].append(f"{a:#x}<-{ret:#x}")
        if a == 0x44f514:                          # hunt: the actor's strength (FUN_0044aa54, one Random(4))
            row.setdefault("hunt_terms", []).append(dict(actor_strength=uc.reg_read(UC_X86_REG_EAX), targets=[]))
        if a == 0x44f59f:                          # hunt: distance to an eligible target
            row["hunt_terms"][-1]["targets"].append(dict(d=s16(uc.reg_read(UC_X86_REG_EAX))))
        if a == 0x44f5aa:                          # hunt: that target's strength (one Random(4))
            row["hunt_terms"][-1]["targets"][-1]["s"] = uc.reg_read(UC_X86_REG_EAX)
        if a == 0x44f682:                          # back from the hunt: [esp] score word, [esp+2] target index word
            sp = uc.reg_read(UC_X86_REG_ESP)
            sc, tg, port = struct.unpack("<3h", uc.mem_read(sp, 6))
            row.setdefault("hunt", []).append(dict(score=sc, target=tg, port=port))
        if a == 0x44f65b:                          # back from the port pick: [esp+4] city index word
            row.setdefault("port_pick", []).append(s16(struct.unpack("<H", uc.mem_read(uc.reg_read(UC_X86_REG_ESP) + 4, 2))[0]))
        if a == 0x44b5d0:
            row["status"] = "stopped-before-naval-combat"
            uc.emu_stop()

    def write(uc, access, a, size, value, data):
        if FLEET <= a < FLEET + 26 * 64:
            f, off = divmod(a - FLEET, 26)
            for k in range(size):
                if 4 <= off + k <= 7:
                    row["route_writes"].append(dict(fleet=f, offset=off + k, eip=hex(uc.reg_read(UC_X86_REG_EIP))))
                    break
            if f == 0 and off in (0, 2, 12):
                row["fleet0_writes"].append(dict(field={0: "x", 2: "y", 12: "moves"}[off], value=s16(value)))
        if cargo >= 0 and ARMY + 656 * cargo <= a < ARMY + 656 * cargo + 10:
            row["cargo_writes"].append(dict(offset=a - ARMY - 656 * cargo, value=s16(value)))

    u.hook_add(UC_HOOK_CODE, hook)
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    before = [fleet(ram, f) for f in range(nf)]
    try:
        u.emu_start(0x44f608, 0x600000, count=50_000_000)
        if row["status"] == "running":
            assert u.reg_read(UC_X86_REG_EIP) == 0x600000
            row["status"] = "complete"
    except Exception:
        row.update(status="error", error=traceback.format_exc()[-800:], eip=hex(u.reg_read(UC_X86_REG_EIP)))
    end = bytes(u.mem_read(RAM_BASE, RAM_SIZE))
    after = [fleet(end, f) for f in range(nf)]
    row.update(fleets_before=before, fleets_after=after,
               routes_before=[b[2:4] for b in before], routes_after=[x[2:4] for x in after],
               route_unchanged=all(b[2:4] == x[2:4] for b, x in zip(before, after)),
               cargo_army=cargo, cargo_after=None if cargo < 0 else [rd(end, ARMY + 656 * cargo + 2 * k) for k in range(5)],
               current_nation=rd(ram, 0x4a0320))
    row["calls"] = sorted(set(row["calls"]))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1")
    ap.add_argument("--dry", action="store_true", help="print only, write nothing")
    a = ap.parse_args()
    rows = []
    for d in sorted(INPUTS.iterdir()):
        if d.name == "rough-human-one":           # a low-level human walk, not a phase input
            continue
        rows.append(dict(run_case(d.name, (d / "input.ram").read_bytes()), source="fleet174 input replayed"))
    for name, base, edits, what in CASES:
        r = run_case(name, derive(base, **edits))
        r.update(source=f"derived from fleet174 {base}", edits={k: {str(kk): vv for kk, vv in v.items()} if isinstance(v, dict) else v
                                                                 for k, v in edits.items()}, isolates=what)
        rows.append(r)
    for r in rows:
        e = [(c["site"], c["goal"]) for c in r["e1fc"] if c["fleet"] == 0][:3]
        print(f"{r['case']:28s} {r['status']:28s} route_writes={len(r['route_writes'])} unchanged={r['route_unchanged']} "
              f"draws={len(r['draws'])} e1fc0={e} f0={r['fleets_after'][0][:2]} mv={r['fleets_after'][0][6]}")
    if a.dry:
        return
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / f"phase-{a.version}.json", "x") as f:
        json.dump(rows, f, indent=1)


if __name__ == "__main__":
    main()
