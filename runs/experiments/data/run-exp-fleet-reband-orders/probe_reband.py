"""Which orders re-band a fleet's map word (owner + 300 / 316 / 332 for ships < 25 / < 50 / more), 2026-10-08.
Pre-states: Rome fleets' ships patched (content scan on (x, y, owner 0), +18) AND their map words set to the band of the
patched ships, so a stale word cannot pass for a re-band. Then the order; then the words at every Rome fleet's tile.
python3 probe_reband.py <out_dir> [case ...]"""
import json, shutil, struct, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import fresh_save, load
SAVES = (Path(__file__).resolve().parents[4] / "saves")
PORT, SPLIT = SAVES / "fleet-port-antium-0734.SAV", SAVES / "fleet-split-antium-0734.SAV"
band = lambda ships: 300 if ships < 25 else 316 if ships < 50 else 332
CASES = {   # case: (fixture, {(x, y): ships}, order, arg)
    "sp1_split_30_by_10": (PORT, {(101, 46): 30}, "split_fleet", 10),
    "sp2_split_50_by_1": (PORT, {(101, 46): 50}, "split_fleet", 1),
    "tr1_transfer_25_24_by_1": (SPLIT, {(101, 46): 25, (101, 47): 24}, "transfer_ships", 1),
    "tr2_transfer_50_10_by_1": (SPLIT, {(101, 46): 50, (101, 47): 10}, "transfer_ships", 1),
}
out = Path(sys.argv[1])

def fleet_off(data, x, y):
    for off in range(0, len(data) - 26):
        f = struct.unpack_from("<13h", data, off)
        if f[0] == x and f[1] == y and f[4] == 0 and f[11] == -1 and f[5] < 0:
            return off
    raise RuntimeError(f"no Rome fleet at {(x, y)}")

def make_pre(src, ships):
    data = bytearray(src.read_bytes())
    for (x, y), n in ships.items():
        struct.pack_into("<h", data, fleet_off(data, x, y) + 18, n)
        struct.pack_into("<h", data, x * 280 + y * 2, band(n))
    fd, name = tempfile.mkstemp(suffix=".SAV", prefix="tmp_reband_"); p = Path(name); p.write_bytes(bytes(data))
    return p

def fleets(path):
    b = path.read_bytes()
    return [{"id": f["id"], "xy": [f["x"], f["y"]], "ships": f["ships"], "word": struct.unpack_from("<h", b, f["x"] * 280 + f["y"] * 2)[0],
             "band_of_ships": band(f["ships"])} for f in load(path)["fleets"] if f["owner"] == 0]

res = {}
for case in (sys.argv[2:] or CASES):
    src, ships, order, arg = CASES[case]
    pre = make_pre(src, ships); shutil.copy(pre, out / f"{case}_PRE.SAV")
    g = fresh_save(pre)
    p0 = g.save_as(f"{case.upper()[:20]}_B.SAV"); shutil.copy(p0, out / f"{case}_BEFORE.SAV")
    texts = getattr(g, order)(2, arg)
    p1 = g.save_as(f"{case.upper()[:20]}_A.SAV"); shutil.copy(p1, out / f"{case}_AFTER.SAV")
    a = fleets(out / f"{case}_AFTER.SAV")
    r = {"order": f"{order}(2, {arg})", "popups": texts, "before": fleets(out / f"{case}_BEFORE.SAV"), "after": a,
         "mem_words_after": {f"{f['xy'][0]},{f['xy'][1]}": g.cell(*f["xy"]) for f in a},
         "all_rebanded": all(f["word"] == f["band_of_ships"] for f in a)}
    res[case] = r; print(case, json.dumps(r), flush=True)
    pre.unlink(missing_ok=True)
(out / ("probe_reband_" + "_".join(res) + ".json")).write_text(json.dumps(res, indent=1))
