"""Mercenary hire vs a full recruitment queue and a full army (research ask B, 2026-10-08).
Fixture: saves/run0-start-AUTO0720-seed12345.SAV (Rome human; army 1 at (120,53) next to Heraclea's Samnite offer; purse 100).
Cases (Rome's 40 queue slots set first; then army 1's 20 unit slots if listed):
  c1_full_queue: 40 slots (12, hi, 3200, city 85); army 1 as in the fixture -> hire offer row 0
  c2_empty_queue: 0 slots (control)                                         -> hire offer row 0
  c3_army_20_slots: queue as in the fixture; army 1 slots 0-19 regular hi 1,000 q7 -> press Recruit mercenaries
  c4_army_gap_0_18: queue as in the fixture; army 1 slots 0 and 18 only            -> hire row 0 (lands in slot 19?)
  c5_army_only_slot19: queue as in the fixture; army 1 slot 19 only (1 unit, FUN_0044a66c = 20) -> press Recruit mercenaries
python3 probe_merc.py <out_dir> [case ...]"""
import json, shutil, struct, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import fresh_save, load
from harness.driver import DriverError

SRC = (Path(__file__).resolve().parents[4] / "saves/run0-start-AUTO0720-seed12345.SAV")
CASES = {"c1_full_queue": (40, None), "c2_empty_queue": (0, None),
         "c3_army_20_slots": (None, list(range(20))), "c4_army_gap_0_18": (None, [0, 18]),
         "c5_army_only_slot19": (None, [19])}
ARMY_COUNT_OFF, ARMY_LEN, SLOT_BASE = 100956, 656, 0x2E4
out = Path(sys.argv[1])

def make_pre(n_queue, army_slots):
    data = bytearray(SRC.read_bytes())
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    nf = struct.unpack_from("<h", data, ARMY_COUNT_OFF + 2 + na * ARMY_LEN)[0]
    if n_queue is not None:
        q = ARMY_COUNT_OFF + 2 + na * ARMY_LEN + 2 + nf * 26 + SLOT_BASE
        for k in range(40):
            struct.pack_into("<4h", data, q + 8 * k, *((12, 1, 3200, 85) if k < n_queue else (0, 0, 0, 0)))
    if army_slots is not None:
        off = next(ARMY_COUNT_OFF + 2 + i * ARMY_LEN for i in range(na)
                   if struct.unpack_from("<3h", data, ARMY_COUNT_OFF + 2 + i * ARMY_LEN) == (120, 53, 0))
        for k in range(20):
            so = off + 16 + 32 * k
            data[so:so + 32] = bytes(32)
            if k in army_slots:
                struct.pack_into("<4h", data, so, 0, 1, 1000, 7)
                data[so + 8:so + 8 + len(f"S1-{k}")] = f"S1-{k}".encode()
    fd, name = tempfile.mkstemp(suffix=".SAV", prefix="tmp_merc_"); p = Path(name); p.write_bytes(bytes(data))
    return p

def snap(s):
    a1 = next(a for a in s["armies"] if a["id"] == 1)
    n = s["nations"][0]
    return {"army1": {"purse": a1["money"], "troops": a1["troops"],
                      "slots": {u["slot"]: [u["merc"], u["type"], u["troops"], u["quality"], u["name"]] for u in a1["units"]}},
            "army2_header": next(([a["x"], a["y"], a["owner"]] for a in s["armies"] if a["id"] == 2), None),
            "n_armies": len(s["armies"]), "treasury": n["treasury"],
            "queue": {sl["slot"]: [sl["state"], sl["type"], sl["troops"], sl["city"]] for sl in n["recruit_slots"]}}

results = {}
for case in (sys.argv[2:] or CASES):
    pre = make_pre(*CASES[case]); shutil.copy(pre, out / f"{case}_PRE.SAV")
    g = fresh_save(pre)
    p0 = g.save_as(f"{case.upper()}_BEFORE.SAV"); shutil.copy(p0, out / f"{case}_BEFORE.SAV")
    try:
        gained, texts = g.hire_mercs(1, rows=(0,)); err = None
    except DriverError as e:
        gained, texts, err = None, [], str(e)
    texts = texts + g.dismiss_popups()          # an R08 box opened instead of the dialog
    p1 = g.save_as(f"{case.upper()}_AFTER.SAV"); shutil.copy(p1, out / f"{case}_AFTER.SAV")
    b, a = snap(load(out / f"{case}_BEFORE.SAV")), snap(load(out / f"{case}_AFTER.SAV"))
    r = {"gained": gained, "popups": texts, "driver_error": err, "before": b, "after": a,
         "new_army1_slots": {k: v for k, v in a["army1"]["slots"].items() if k not in b["army1"]["slots"]},
         "queue_unchanged": a["queue"] == b["queue"], "purse": [b["army1"]["purse"], a["army1"]["purse"]],
         "treasury": [b["treasury"], a["treasury"]],
         "byte_identical": (out / f"{case}_BEFORE.SAV").read_bytes() == (out / f"{case}_AFTER.SAV").read_bytes()}
    results[case] = r
    print(case, json.dumps({k: r[k] for k in ("gained", "popups", "driver_error", "new_army1_slots", "queue_unchanged", "purse", "treasury", "byte_identical")}),
          "army2", b["army2_header"], "->", a["army2_header"], "n_armies", b["n_armies"], "->", a["n_armies"], flush=True)
    pre.unlink(missing_ok=True)
(out / ("probe_merc_" + "_".join(results) + ".json")).write_text(json.dumps(results, indent=1))
