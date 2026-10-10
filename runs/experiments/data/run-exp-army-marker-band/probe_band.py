"""Army map marker = owner + 200 / 216 / 232 by troops (< 25,000 / < 50,000 / more), docs/sav-layout-notes.md, checked at the
boundaries (2026-10-08). The merc hire calls FUN_0044a80c on the army after adding the unit (TRecruitMercs_RecruitMercUnit :43670).
Fixture saves/run0-start-AUTO0720-seed12345.SAV: army 1 (Rome) at (120,53) next to Heraclea's Samnite offer (3,868 men).
Army 1's 20 slots are replaced by regular heavy-infantry units summing to (target - 3,868); then hire_mercs(1, rows=(0,)).
python3 probe_band.py <out_dir> [case ...]"""
import json, shutil, struct, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import fresh_save, load
SRC = (Path(__file__).resolve().parents[4] / "saves/run0-start-AUTO0720-seed12345.SAV")
SAMNITE = 3868
CASES = {"t24999": 24999, "t25000": 25000, "t49999": 49999, "t50000": 50000}
ARMY_COUNT_OFF, ARMY_LEN = 100956, 656
out = Path(sys.argv[1])

def make_pre(target):
    data = bytearray(SRC.read_bytes())
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    off = next(ARMY_COUNT_OFF + 2 + i * ARMY_LEN for i in range(na)
               if struct.unpack_from("<3h", data, ARMY_COUNT_OFF + 2 + i * ARMY_LEN) == (120, 53, 0))
    base = target - SAMNITE
    parts = [base // 2, base - base // 2]
    for k in range(20):
        so = off + 16 + 32 * k
        data[so:so + 32] = bytes(32)
        if k < len(parts):
            struct.pack_into("<4h", data, so, 0, 1, parts[k], 7)
            data[so + 8:so + 12] = f"B{k}".encode().ljust(4, b"\0")
    fd, name = tempfile.mkstemp(suffix=".SAV", prefix="tmp_band_"); p = Path(name); p.write_bytes(bytes(data))
    return p

mw = lambda path: struct.unpack_from("<h", path.read_bytes(), 120 * 280 + 53 * 2)[0]
results = {}
for case in (sys.argv[2:] or CASES):
    pre = make_pre(CASES[case]); shutil.copy(pre, out / f"{case}_PRE.SAV")
    g = fresh_save(pre)
    p0 = g.save_as(f"{case.upper()}_BEFORE.SAV"); shutil.copy(p0, out / f"{case}_BEFORE.SAV")
    gained, texts = g.hire_mercs(1, rows=(0,))
    p1 = g.save_as(f"{case.upper()}_AFTER.SAV"); shutil.copy(p1, out / f"{case}_AFTER.SAV")
    tr = [next(a for a in load(out / f"{case}_{k}.SAV")["armies"] if a["id"] == 1)["troops"] for k in ("BEFORE", "AFTER")]
    r = {"target": CASES[case], "gained": gained, "popups": texts, "troops": tr,
         "map_120_53": [mw(out / f"{case}_{k}.SAV") for k in ("PRE", "BEFORE", "AFTER")]}
    results[case] = r
    print(case, json.dumps(r), flush=True)
    pre.unlink(missing_ok=True)
(out / ("probe_band_" + "_".join(results) + ".json")).write_text(json.dumps(results, indent=1))
