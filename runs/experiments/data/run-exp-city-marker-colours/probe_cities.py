"""City markers for every owner (ic2-research request for the player, 2026-10-09), drawn the way run-exp-owner-colours drew the
unit icons. City marker word = 20 + owner + 16 * variant (research 2026-10-07-city-marker-variants.md: variants 0-3 population
tiers, 4 the capital), 80 words 20..99. Screen 1: the unit-map view at origin (114,46) of t24999_AFTER.SAV; every tile except the
controls gets one word: the 80 words, then repeats of 20, 84 and 22 on plain (2) and sea (0) tiles. Controls left unpatched: Rome
army 1 (120,53, word 200) and five real Roman cities of variant 1 (word 36) at (115,48), (118,51), (120,56), (121,53), (124,52).
Screen 2: the same save moved to the view around Rome (101,43) (an Area map click), unpatched there: the real capital Rome (84) and
real variant-0 Roman cities (20). Each 32x32 tile is cropped and hashed (8-bit RGB, whole and inset 2 px).
python3 probe_cities.py <out_dir>"""
import json, shutil, struct, subprocess, sys, time, hashlib
from pathlib import Path
R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R))
from tests.test_orders import fresh_save
from harness.driver import sh, UNIT_PAINT, G
from state import sav
SRC = R / "artifacts/run-exp-army-marker-band/t24999_AFTER.SAV"
out = Path(sys.argv[1]); (out / "tiles").mkdir(parents=True, exist_ok=True)
OX, OY, COLS, ROWS = 114, 46, 13, 12
word = lambda b, x, y: struct.unpack_from("<h", b, x * 280 + y * 2)[0]
data = bytearray(SRC.read_bytes())
controls = {(120, 53)} | {(x, y) for x in range(OX, OX + COLS) for y in range(OY, OY + ROWS) if word(data, x, y) == 36}
tiles = [(OX + c, OY + r) for r in range(ROWS) for c in range(COLS) if (OX + c, OY + r) not in controls]
plan = [(o, v, 20 + o + 16 * v) for v in range(5) for o in range(16)]
terrain = {t: word(data, *t) for t in tiles}
rest = [t for t in tiles[len(plan):]]
extra_tiles = [t for t in rest if terrain[t] in (0, 2)][:12]
extra = [(0, 0, 20), (0, 4, 84), (2, 0, 22)] * 4
assign = dict(zip(tiles, plan)) | dict(zip(extra_tiles, extra))
for t, p in assign.items():
    struct.pack_into("<h", data, t[0] * 280 + t[1] * 2, p[2])
pre = out / "cities_PRE.SAV"; pre.write_bytes(bytes(data))

def rgb(png, inset=0):
    a = ["convert", str(png)] + (["-crop", f"{32 - 2 * inset}x{32 - 2 * inset}+{inset}+{inset}", "+repage"] if inset else []) + ["-depth", "8", "rgb:-"]
    return subprocess.run(a, capture_output=True, check=True).stdout

def crop(full, ox, oy, x, y, name):
    px, py = UNIT_PAINT[0] + 32 * (x - ox), UNIT_PAINT[1] + 30 + 32 * (y - oy)
    p = out / "tiles" / f"{name}.png"
    subprocess.run(["convert", str(full), "-crop", f"32x32+{px}+{py}", "+repage", str(p)], check=True)
    return {"png": p.name, "sha": hashlib.sha256(rgb(p)).hexdigest()[:16], "sha_inset2": hashlib.sha256(rgb(p, 2)).hexdigest()[:16]}

g = fresh_save(pre)
res = {"screen1": {"origin": g.view_origin()}, "tiles": [], "controls": [], "screen2": {}}
cx, cy = g.show(120, 53)
assert g.view_origin() == (OX, OY), g.view_origin()
nx, ny = g.neutral_point(); sh("xdotool", "mousemove", str(nx), str(ny)); time.sleep(1.5)
full = out / "cities_screen1.png"; g.shot(full)
seen = {}
for t, (o, v, w) in assign.items():
    n = seen.get(w, 0); seen[w] = n + 1
    name = f"city_v{v}_o{o:02d}_w{w}" + (f"_rep{n}" if n else "")
    res["tiles"].append({"tile": t, "owner": o, "variant": v, "word": w, "repeat": n, "terrain_under": terrain[t], "mem_word": g.cell(*t)}
                        | crop(full, OX, OY, *t, name))
for t in sorted(controls):
    res["controls"].append({"tile": t, "word": word(data, *t), "mem_word": g.cell(*t)} | crop(full, OX, OY, *t, f"control_{t[0]}_{t[1]}_w{word(data, *t)}"))
# screen 2: real cities around Rome, unpatched
g.show(101, 43)
ox2, oy2 = g.view_origin()
sh("xdotool", "mousemove", str(nx), str(ny)); time.sleep(1.5)
full2 = out / "cities_screen2.png"; g.shot(full2)
s = sav.load(str(pre))
vis = [c for c in s["cities"] if ox2 <= c["x"] < ox2 + COLS and oy2 <= c["y"] < oy2 + ROWS - 1]
res["screen2"] = {"origin": [ox2, oy2], "cities": [{"name": c["name"], "owner": c["owner"], "tile": [c["x"], c["y"]], "word": word(data, c["x"], c["y"]),
                                                    "mem_word": g.cell(c["x"], c["y"])} | crop(full2, ox2, oy2, c["x"], c["y"], f"real_{c['name'].replace(' ', '_')}_w{word(data, c['x'], c['y'])}")
                                                   for c in vis]}
g.save_as("CM_AFTER.SAV"); shutil.copy(G / "CM_AFTER.SAV", out / "cities_AFTER.SAV")
(out / "probe_cities.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({"n": len(res["tiles"]), "controls": len(res["controls"]), "screen2": [(c["name"], c["word"]) for c in res["screen2"]["cities"]]}))
g.kill()
