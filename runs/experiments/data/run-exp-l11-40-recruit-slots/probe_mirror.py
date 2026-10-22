"""L11 40-slot mirror probe: Rome slot 0 empty, slots 1-39 occupied (city 85).
Slot-39-only gate (R46 reading) -> refused; whole-queue gate -> accepted (into which slot?).
python3 probe_mirror.py <out_dir>"""
import json, struct, sys
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import BASE, fresh_save, load, _make_patched_save_full_slots
from harness.driver import DriverError

out = Path(sys.argv[1])
NATION_LEN, SLOT_BASE, ARMY_COUNT_OFF, ARMY_LEN = 1172, 0x2E4, 100956, 656
pre = _make_patched_save_full_slots(BASE, nation_index=0, city_id=85, n_slots=40, state=12, typ=1, troops=3200)
data = bytearray(pre.read_bytes())
na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
nf = struct.unpack_from("<h", data, ARMY_COUNT_OFF + 2 + na * ARMY_LEN)[0]
slot0 = ARMY_COUNT_OFF + 2 + na * ARMY_LEN + 2 + nf * 26 + SLOT_BASE
struct.pack_into("<4h", data, slot0, 0, 0, 0, 0)   # empty slot 0
pre.write_bytes(bytes(data))
(out / "MIRROR_PRE.SAV").write_bytes(bytes(data))

def slots(s):
    return {sl["slot"]: [sl["state"], sl["type"], sl["troops"], sl["city"]] for sl in s["nations"][0]["recruit_slots"]}

g = fresh_save(pre)
before = slots(load(g.save_as("MIRROR_BEFORE.SAV")))
try:
    texts = g.recruit(city_row=1, unit_type="hi", thousands=2)
    err = None
except DriverError as e:
    texts, err = [], str(e)
p = g.save_as("MIRROR_AFTER.SAV")
after = slots(load(p))
for n in ("MIRROR_BEFORE.SAV", "MIRROR_AFTER.SAV"):
    (out / n).write_bytes(Path(p).with_name(n).read_bytes())
res = {"occupied_before": sorted(before), "occupied_after": sorted(after),
       "new_slots": {k: v for k, v in after.items() if k not in before},
       "changed": {k: [before[k], after[k]] for k in before if k in after and before[k] != after[k]},
       "popups": texts, "driver_error": err}
(out / "probe_mirror.json").write_text(json.dumps(res, indent=1))
print(json.dumps({k: res[k] for k in ("new_slots", "changed", "popups", "driver_error")}), len(before), len(after))
pre.unlink(missing_ok=True)
