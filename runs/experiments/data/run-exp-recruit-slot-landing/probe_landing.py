"""Where an accepted Recruit unit lands in Rome's queue (nation +0x2E4, 40 x <4h> state,type,troops,city).
Each case: BASE with Rome's 40 slots cleared and the listed slots set to (12, hi, 3200, city 85); then the
same order (Recruit unit, Rome = city_row 1, heavy infantry, thousands=2) `orders` times, saving after each.
python3 probe_landing.py <out_dir> [case ...]"""
import json, shutil, struct, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import BASE, fresh_save, load
from harness.driver import DriverError

CASES = {
    "c1_empty": ([], 1),
    "c2_gap_slot1": ([0, 2, 3, 4, 5], 1),
    "c3_gap_slot0": (list(range(1, 39)), 3),   # 3rd order: slot 39 should be taken by then -> R46
}
NATION_LEN, SLOT_BASE, ARMY_COUNT_OFF, ARMY_LEN = 1172, 0x2E4, 100956, 656
out = Path(sys.argv[1])

def make_pre(occupied):
    data = bytearray(BASE.read_bytes())
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    nf = struct.unpack_from("<h", data, ARMY_COUNT_OFF + 2 + na * ARMY_LEN)[0]
    base = ARMY_COUNT_OFF + 2 + na * ARMY_LEN + 2 + nf * 26 + SLOT_BASE
    for k in range(40):
        struct.pack_into("<4h", data, base + 8 * k, *((12, 1, 3200, 85) if k in occupied else (0, 0, 0, 0)))
    fd, name = tempfile.mkstemp(suffix=".SAV", prefix="tmp_land_"); p = Path(name); p.write_bytes(bytes(data))
    return p

def state(s):
    n = s["nations"][0]
    return {"slots": {sl["slot"]: [sl["state"], sl["type"], sl["troops"], sl["city"]] for sl in n["recruit_slots"]},
            "treasury": n["treasury"], "mob": n["mobilization"]}

results = {}
for case in (sys.argv[2:] or CASES):
    occ, orders = CASES[case]
    pre = make_pre(occ)
    shutil.copy(pre, out / f"{case}_PRE.SAV")
    g = fresh_save(pre)
    p = g.save_as(f"{case.upper()}_0.SAV"); shutil.copy(p, out / f"{case}_0.SAV")
    states = [state(load(p))]
    steps = []
    for k in range(1, orders + 1):
        try:
            texts, err = g.recruit(city_row=1, unit_type="hi", thousands=2), None
        except DriverError as e:
            texts, err = [], str(e)
        p = g.save_as(f"{case.upper()}_{k}.SAV"); shutil.copy(p, out / f"{case}_{k}.SAV")
        st = state(load(p)); prev = states[-1]; states.append(st)
        steps.append({"order": k, "popups": texts, "driver_error": err,
                      "new_slots": {s: v for s, v in st["slots"].items() if s not in prev["slots"]},
                      "changed_slots": {s: [prev["slots"][s], v] for s, v in st["slots"].items() if s in prev["slots"] and prev["slots"][s] != v},
                      "treasury": [prev["treasury"], st["treasury"]], "mob": [prev["mob"], st["mob"]],
                      "byte_identical": (out / f"{case}_{k-1}.SAV").read_bytes() == (out / f"{case}_{k}.SAV").read_bytes()})
    results[case] = {"occupied_pre": occ, "steps": steps}
    print(case, json.dumps(steps), flush=True)
    pre.unlink(missing_ok=True)
(out / ("probe_landing_" + "_".join(results) + ".json")).write_text(json.dumps(results, indent=1))
