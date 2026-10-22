"""L11 20-units-per-army gate on Join armies (TUnitMap_JoinArmies :46982-46984: FUN_0044a66c(kept) + FUN_0044a66c(partner) < 0x15,
FUN_0044a66c = index of the last occupied slot + 1). FLEET_PORT: army 0 (Rome, (101,45)) is selected = kept; army 12 (Rome, (102,45))
and army 13 (Rome, (102,44)) are both adjacent; FUN_00449d64 keeps the LAST adjacent match, so both get the partner
layout (names tell which merged). Each army's 20 slots are cleared, then the listed slots get a regular unit (label 0, heavy inf, 1,000 men,
quality 7, name "S<army>-<slot>"), so totals stay far below 100,000 and every unit is traceable.
python3 probe_join20.py <out_dir> [case ...]"""
import json, shutil, struct, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import fresh_save, load
from harness.driver import DriverError

FLEET_PORT = (Path(__file__).resolve().parents[4] / "saves/fleet-port-antium-0734.SAV")
CASES = {   # case: (kept army 0 slots, partner slots for armies 12 and 13)
    "c1_10_10": (list(range(10)), list(range(10))),
    "c2_10_11": (list(range(10)), list(range(11))),
    "c3_gap_value21": ([0, 15], list(range(5))),
    "c4_gap_value20": ([0, 9], list(range(10))),
    "c5_partner_slot0_empty": (list(range(5)), [1, 2, 3]),
}
ARMY_COUNT_OFF, ARMY_LEN = 100956, 656
out = Path(sys.argv[1])

def army_off(data, x, y, owner):
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    for i in range(na):
        off = ARMY_COUNT_OFF + 2 + i * ARMY_LEN
        if struct.unpack_from("<3h", data, off) == (x, y, owner):
            return off
    raise RuntimeError(f"no army at {(x, y, owner)}")

def make_pre(kept, partner):
    data = bytearray(FLEET_PORT.read_bytes())
    for (x, y, aid), slots in (((101, 45, 0), kept), ((102, 45, 12), partner), ((102, 44, 13), partner)):
        off = army_off(data, x, y, 0)
        for k in range(20):
            so = off + 16 + 32 * k
            data[so:so + 32] = bytes(32)
            if k in slots:
                struct.pack_into("<4h", data, so, 0, 1, 1000, 7)
                name = f"S{aid}-{k}".encode()
                data[so + 8:so + 8 + len(name)] = name
    fd, name = tempfile.mkstemp(suffix=".SAV", prefix="tmp_join20_"); p = Path(name); p.write_bytes(bytes(data))
    return p

def armies(s):
    return {a["id"]: {"xy": [a["x"], a["y"]], "moves": a["moves"], "troops": a["troops"],
                      "slots": {u["slot"]: u["name"] for u in a["units"]}}
            for a in s["armies"] if a["owner"] == 0 and a["id"] in (0, 12, 13)}

results = {}
for case in (sys.argv[2:] or CASES):
    kept, partner = CASES[case]
    pre = make_pre(kept, partner)
    shutil.copy(pre, out / f"{case}_PRE.SAV")
    g = fresh_save(pre)
    p0 = g.save_as(f"{case.upper()}_BEFORE.SAV"); shutil.copy(p0, out / f"{case}_BEFORE.SAV")
    try:
        texts, err = g.join(0), None
    except DriverError as e:
        texts, err = [], str(e)
    p1 = g.save_as(f"{case.upper()}_AFTER.SAV"); shutil.copy(p1, out / f"{case}_AFTER.SAV")
    b, a = load(out / f"{case}_BEFORE.SAV"), load(out / f"{case}_AFTER.SAV")
    r = {"kept_slots": kept, "partner_slots": partner,
         "gate_value": (max(kept) + 1 if kept else 0) + (max(partner) + 1 if partner else 0),
         "units": len(kept) + len(partner), "popups": texts, "driver_error": err,
         "before": armies(b), "after": armies(a), "rome_armies": [len([x for x in s["armies"] if x["owner"] == 0]) for s in (b, a)],
         "byte_identical": (out / f"{case}_BEFORE.SAV").read_bytes() == (out / f"{case}_AFTER.SAV").read_bytes()}
    results[case] = r
    print(case, json.dumps({k: r[k] for k in ("gate_value", "units", "popups", "driver_error", "after", "rome_armies", "byte_identical")}), flush=True)
    pre.unlink(missing_ok=True)
(out / ("probe_join20_" + "_".join(results) + ".json")).write_text(json.dumps(results, indent=1))
