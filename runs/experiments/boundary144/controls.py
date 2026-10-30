#!/usr/bin/env python3.12
"""Research #144 (remake #1640), delegated 2026-10-30: the boundaries and ties of FUN_0044ebe8 (garrison fallback) and
FUN_0044e84c (mercenary run), on controlled synthetic states.

Unicorn on the pinned EXE with the #187 RAM snapshot (runs/experiments/navigation187/core.py: unmodified helpers, read-only
RAM check, no RNG). Each control runs the routine with EAX = the army and stops at the entry of FUN_0044dba8, the walk it
starts: the walk's army (EAX) and destination (EDX) are the routine's choice. Nothing after that call runs, so no state
changes and no presentation code is reached. Inputs are written into the snapshot copy only:

- Current nation 1 (Carthage, 0x4A0320); the deciding army is record 3, owner 1. Every other army owned by 1 is moved to
  (300,10), far from everything.
- City records (0x479590 + 34*i: +0xE x, +0x10 y, +0x12 owner) are moved: every city not used by a control goes to
  (319,139); the capital (474AB4[1]) stays where it is unless a control says otherwise.
- Mercenary pool records 201..250 (0x49D0A4 + 12*k: +0 x, +2 y, +8 the live word, > -1 = live): every one not used by a
  control is set dead (+8 = -1).

    python3.12 runs/experiments/boundary144/controls.py --version v1 --names <ids.json>                 # layout v1
    python3.12 runs/experiments/boundary144/controls.py --version v2 --names <ids.json> --layout land   # land strip
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "runs/experiments/navigation187"))
import core as C  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-boundary144"
NATION, ARMY = 1, 3
ARMIES, AREC = 0x47C1EC, 0x290
CITIES, CREC, NCITIES = 0x479590, 34, 334
POOL, PREC, SLOTS = 0x49D0A4, 12, range(201, 251)
CAPITAL = 0x474AB4 + NATION * 0x494
REL = 0x474696                          # relation row: REL + a*0x494 + b*2
FAR_CITY, FAR_ARMY = (319, 139), (300, 10)
EBE8, E84C, DBA8 = 0x44EBE8, 0x44E84C, 0x44DBA8


def base():
    r = bytearray(C.RAM)
    C.put(r, 0x4A0320, NATION)
    for i in range(C.short(r, 0x4A0324)):
        a = ARMIES + i * AREC
        if C.short(r, a + 4) == NATION and i != ARMY:
            C.put(r, a, FAR_ARMY[0]); C.put(r, a + 2, FAR_ARMY[1])
    cap = C.short(r, CAPITAL)
    for i in range(NCITIES):
        if i != cap:
            set_city(r, i, FAR_CITY)
    for k in SLOTS:
        C.put(r, POOL + k * PREC + 8, -1)
    return r


def set_city(r, i, p, owner=None):
    c = CITIES + i * CREC
    C.put(r, c + 0xE, p[0]); C.put(r, c + 0x10, p[1])
    if owner is not None:
        C.put(r, c + 0x12, owner)


def set_army(r, p):
    a = ARMIES + ARMY * AREC
    C.put(r, a, p[0]); C.put(r, a + 2, p[1])


def set_offer(r, k, p, live=100):
    C.put(r, POOL + k * PREC, p[0]); C.put(r, POOL + k * PREC + 2, p[1]); C.put(r, POOL + k * PREC + 8, live)


def city_xy(r, i):
    return tuple(C.xy(r, CITIES + i * CREC + 0xE))


def choose(r, entry):
    out = C.run(entry, eax=ARMY, ram=r, stop=(DBA8,))
    walks = [t for t in out["trace"] if t["function"] == hex(DBA8)]
    if not walks:
        return None
    e = walks[-1]["edx"]
    return [e & 0xFFFF, (e >> 16) & 0xFFFF]


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def ebe8_rows(names, layout):
    """layout "v1": the capital where it is, the nearest city 1 beyond the army. layout "land" (v2): the free land strip
    (60..77, 20) and column (68, 20..31) of the snapshot's map, the capital moved to (60,20), the nearest city 3 beyond the
    army, tie cities 2 either side: the same states the native probe uses, where the #925 walker test can pass."""
    rows = []
    r0 = base()
    cap = C.short(r0, CAPITAL)
    if layout == "land":
        set_city(r0, cap, (60, 20))
    capxy = city_xy(r0, cap)
    gap = 3 if layout == "land" else 1
    x_city = 40                                           # any non-capital record used as "the nearest city"
    for d in (9, 10, 11):
        r = bytearray(r0)
        army = (capxy[0] + d, capxy[1])
        set_army(r, army)
        set_city(r, x_city, (army[0] + gap, army[1]))    # gap from the army, d + gap from the capital
        got = choose(r, EBE8)
        rows.append({"control": f"ebe8 capital distance {d}", "army": army, "capital": list(capxy),
                     "army_to_capital": cheb(army, capxy), "nearest_city": [army[0] + gap, army[1]],
                     "destination": got, "branch": "capital" if got == list(capxy) else
                     "nearest city" if got == [army[0] + gap, army[1]] else "other"})
    # absent capital: 474AB4[1] = -1 (the routine has no guard; it reads the record before the table)
    r = bytearray(r0)
    army = (capxy[0] + (8 if layout == "land" else 20), capxy[1])
    set_army(r, army)
    set_city(r, x_city, (army[0] + gap, army[1]))
    C.put(r, CAPITAL, -1)
    rows.append({"control": "ebe8 capital index -1, deciding army 20 from the old capital", "army": army,
                 "record_minus_1_xy": list(C.xy(r, CITIES - CREC + 0xE)), "destination": choose(r, EBE8)})
    # ties: two cities 1 from the army (the capital far), records i < j whose native ids order the other way
    i, j = tie_pair(names)
    if layout == "land":
        army, a_xy, b_xy, cap_xy, other_xy = (68, 20), (66, 20), (70, 20), (68, 31), (68, 30)
    else:
        army, a_xy, b_xy, cap_xy, other_xy = (61, 40), (60, 40), (62, 40), (61, 50), (61, 49)
    for label, (pi, pj) in (("as staged", (a_xy, b_xy)), ("positions swapped", (b_xy, a_xy))):
        r = bytearray(r0)
        set_army(r, army)
        C.put(r, CAPITAL, cap)
        # an own army near the capital so the nearest-city branch is taken
        set_city(r, cap, cap_xy)
        set_army_xy_of_other(r, other_xy)
        set_city(r, i, pi); set_city(r, j, pj)
        got = choose(r, EBE8)
        rows.append({"control": f"ebe8 tie, {label}", "army": army, "record_i": i, "id_i": names.get(i), "xy_i": list(pi),
                     "record_j": j, "id_j": names.get(j), "xy_j": list(pj), "destination": got,
                     "chosen_record": i if got == list(pi) else j if got == list(pj) else None})
    return rows


def set_army_xy_of_other(r, p):
    """Put one other own army near the capital (used by the tie control; the deciding army is not near it)."""
    for i in range(C.short(r, 0x4A0324)):
        a = ARMIES + i * AREC
        if C.short(r, a + 4) == NATION and i != ARMY:
            C.put(r, a, p[0]); C.put(r, a + 2, p[1])
            return i
    raise SystemExit("no second own army")


def e84c_rows(names):
    rows = []
    r0 = base()
    army = (60, 70)
    set_army(r0, army)
    # an own city for each offer, so FUN_004498d8 finds a city and its owner (the nation itself) is not at war
    y1, y2 = 50, 51
    rel_self = C.short(r0, REL + NATION * 0x494 + NATION * 2)
    for d in (19, 20, 21):
        r = bytearray(r0)
        p = (army[0] + d, army[1])
        set_city(r, y1, p, owner=NATION)
        set_offer(r, 201, p)
        got = choose(r, E84C)
        rows.append({"control": f"e84c single offer at {d}", "army": army, "offer": list(p), "distance": d,
                     "destination": got, "taken": got == list(p)})
    for label, s19, s20 in (("19 in slot 201, 20 in slot 202", 201, 202), ("19 in slot 202, 20 in slot 201", 202, 201)):
        r = bytearray(r0)
        p19, p20 = (army[0] + 19, army[1]), (army[0] - 20, army[1])
        set_city(r, y1, p19, owner=NATION); set_city(r, y2, p20, owner=NATION)
        set_offer(r, s19, p19); set_offer(r, s20, p20)
        got = choose(r, E84C)
        rows.append({"control": f"e84c pair 19 vs 20, {label}", "army": army, "destination": got,
                     "chosen": 19 if got == list(p19) else 20 if got == list(p20) else None})
    # ties at distance 5: pool slot order and city record order reversed independently
    i, j = tie_pair(names)
    pa, pb = (army[0] + 5, army[1]), (army[0] - 5, army[1])
    for slot_label, (sa, sb) in (("A in slot 201, B in slot 202", (201, 202)), ("A in slot 202, B in slot 201", (202, 201))):
        for city_label, (ca, cb) in (("A on record i", (i, j)), ("A on record j", (j, i))):
            r = bytearray(r0)
            set_city(r, ca, pa, owner=NATION); set_city(r, cb, pb, owner=NATION)
            set_offer(r, sa, pa); set_offer(r, sb, pb)
            got = choose(r, E84C)
            chosen = "A" if got == list(pa) else "B" if got == list(pb) else None
            rows.append({"control": f"e84c tie at 5, {slot_label}, {city_label}", "army": army,
                         "A": list(pa), "B": list(pb), "slot_A": sa, "slot_B": sb, "record_A": ca, "id_A": names.get(ca),
                         "record_B": cb, "id_B": names.get(cb), "destination": got, "chosen": chosen,
                         "chosen_slot": sa if chosen == "A" else sb if chosen == "B" else None})
    rows.append({"control": "relation(1,1) in the snapshot", "value": rel_self})
    return rows


def tie_pair(names):
    """Two non-capital records i < j whose native (remake) city ids order the other way."""
    cap = C.short(C.RAM, CAPITAL)
    for i in range(1, NCITIES):
        for j in range(i + 1, NCITIES):
            if cap in (i, j) or i in (40, 50, 51) or j in (40, 50, 51):
                continue
            if names.get(i) and names.get(j) and names[i] > names[j]:
                return i, j
    raise SystemExit("no tie pair")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--names", required=True, help="json {record index: native city id}")
    ap.add_argument("--layout", choices=["v1", "land"], default="v1")
    a = ap.parse_args()
    names = {int(k): v for k, v in json.loads(Path(a.names).read_text()).items()}
    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / f"controls-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    rows = ebe8_rows(names, a.layout) + e84c_rows(names)
    out.write_text(json.dumps({"method": __doc__.split("\n\n")[1], "layout": a.layout, "ram": "#187 snapshot (private)", "rows": rows}, indent=1))
    for row in rows:
        print({k: v for k, v in row.items() if k not in ("record_minus_1_xy",)})


if __name__ == "__main__":
    main()
