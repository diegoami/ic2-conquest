"""Other owners' army and fleet icons by band (the player, 2026-10-09). The icon follows the stored map word
(run-exp-army-marker-icon), so one save shows every word: the 13 x 12 visible tiles of the unit map around Rome army 1 (120,53)
get the words owner + 200/216/232 (army bands) and owner + 300/316/332 (fleet bands) for owners 0..15, plus repeats of a few
words on tiles of other terrain (does the terrain under the icon change the pixels?). Rome army 1's own tile is left as is (control,
word 200 = earlier hash 347b29fc65a7e7b7). Nothing is clicked on the map after the load. Each 32 x 32 tile is cropped and hashed;
montage_<kind>.png lays them out owner x band.
python3 probe_colours.py <out_dir>"""
import hashlib, json, struct, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, "/home/diego/projects/ic2-conquest")
from tests.test_orders import fresh_save
from harness.driver import sh, UNIT_PAINT
from state import sav
R = Path("/home/diego/projects/ic2-conquest")
SRC = R / "artifacts/run-exp-army-marker-band/t24999_AFTER.SAV"
out = Path(sys.argv[1])
OX, OY, COLS, ROWS = 114, 46, 13, 12          # the view of the run-exp-army-marker-icon captures (tile (120,53) at (545,366))
CONTROL = (120, 53)
word = lambda b, x, y: struct.unpack_from("<h", b, x * 280 + y * 2)[0]
data = bytearray(SRC.read_bytes())
tiles = [(OX + c, OY + r) for r in range(ROWS) for c in range(COLS) if (OX + c, OY + r) != CONTROL]
plan = [(kind, o, b, kind_base + 16 * b + o) for kind, kind_base in (("army", 200), ("fleet", 300)) for o in range(16) for b in range(3)]
terrain = {t: word(data, *t) for t in tiles}
# repeats: Rome army 200, Gaul army 232, Carthage fleet 332 on tiles of different terrain from their first copy
extra = [("army", 0, 0, 200), ("army", 6, 2, 238), ("fleet", 1, 2, 333)] * 4
assign = {}
for t, p in zip(tiles, plan + extra):
    assign[t] = p
    struct.pack_into("<h", data, t[0] * 280 + t[1] * 2, p[3])
pre = out / "colours_PRE.SAV"; pre.write_bytes(bytes(data))
g = fresh_save(pre)
origin = g.view_origin()
cx, cy = g.show(*CONTROL)
nx, ny = g.neutral_point(); sh("xdotool", "mousemove", str(nx), str(ny)); time.sleep(1.5)
assert origin == (OX, OY) and g.view_origin() == (OX, OY), (origin, g.view_origin())
full = out / "colours_screen.png"; g.shot(full)
res = {"origin": origin, "control": {"tile": CONTROL, "word": g.cell(*CONTROL)}, "tiles": []}
def crop(x, y, name):
    px, py = UNIT_PAINT[0] + 32 * (x - OX), UNIT_PAINT[1] + 30 + 32 * (y - OY)
    p = out / "tiles" / f"{name}.png"; p.parent.mkdir(exist_ok=True)
    subprocess.run(["convert", str(full), "-crop", f"32x32+{px}+{py}", "+repage", str(p)], check=True)
    rgb = subprocess.run(["convert", str(p), "rgb:-"], capture_output=True, check=True).stdout
    px0 = rgb[3 * (1 * 32 + 1):3 * (1 * 32 + 1) + 3]            # pixel (1,1): background colour
    return p, hashlib.sha256(rgb).hexdigest()[:16], px0.hex()
res["control"]["png"], res["control"]["sha"], res["control"]["bg"] = [str(v) if i == 0 else v for i, v in enumerate(crop(*CONTROL, "control_rome_army_200"))]
seen = {}
for t, (kind, o, b, w) in assign.items():
    n = seen.get(w, 0); seen[w] = n + 1
    name = f"{kind}_o{o:02d}_b{b}_w{w}" + (f"_rep{n}" if n else "")
    p, h, bg = crop(*t, name)
    res["tiles"].append({"tile": t, "kind": kind, "owner": o, "band": b, "word": w, "repeat": n, "terrain_under": terrain[t],
                         "mem_word": g.cell(*t), "sha": h, "bg_rgb": bg, "png": p.name})
g.save_as("OC_AFTER.SAV"); import shutil; shutil.copy(Path(g.cell.__self__.__class__.__module__ and __import__("harness.driver").driver.G) / "OC_AFTER.SAV", out / "colours_AFTER.SAV")
for kind in ("army", "fleet"):
    rows = []
    for o in range(16):
        rows += [str(out / "tiles" / f"{kind}_o{o:02d}_b{b}_w{(200 if kind == 'army' else 300) + 16 * b + o}.png") for b in range(3)]
    subprocess.run(["montage", *rows, "-tile", "3x16", "-geometry", "64x64+2+2", "-filter", "point", str(out / f"montage_{kind}.png")], check=True)
(out / "probe_colours.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res["control"], default=str)); print(len(res["tiles"]), "tiles")
g.kill()
