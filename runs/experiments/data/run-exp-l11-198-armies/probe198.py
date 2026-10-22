import sys, struct, subprocess
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import *
from tests.test_orders import _make_patched_save_with_n_armies
from harness.driver import ARMIES
total = int(sys.argv[1]); out = sys.argv[2]
s0 = load(BASE); n_other = sum(1 for a in s0["armies"] if a["owner"] != 0)
pre = _make_patched_save_with_n_armies(BASE, n_rome_target=total - n_other)
print("SAV count", struct.unpack_from("<h", pre.read_bytes(), 100956)[0])
g = fresh_save(pre)
print("windows at load", [w[1] for w in g.find_windows(".")])
print("count", g.i16(ARMY_COUNT))
for i in (0, 1, 13, 14, 196, 197, 198):
    print(i, struct.unpack_from("<4h", g.mem(ARMIES + 656*i, 8)))
ax, ay = g.army_pos(0); g.select_army(0, ax, ay)
if not g.army_x: g.calibrate_army_toolbar()
g.click(g.army_x["split"], ARMY_TOOLBAR_Y, pause=1.5)
print("count after click", g.i16(ARMY_COUNT))
print("windows after", [w[1] for w in g.find_windows(".")])
subprocess.run(["import", "-window", "root", out], env={"DISPLAY": ":99"})
