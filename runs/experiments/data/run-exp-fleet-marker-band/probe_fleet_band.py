"""Fleet map marker by ship band (research: FUN_0044a878, owner + 300 / 316 / 332 for ships < 25 / < 50 / more), and the
fleet icon on the unit map (2026-10-08).
Part A, live boundaries: saves/fleet-split-antium-0734.SAV, Rome fleets 2 at (101,46) and 5 at (101,47), ships patched
(content scan, +18) to (a, b); Join fleets on fleet 2; read the survivor's map word at (101,46) (save and memory).
Part B, icons: the Part A AFTER saves plus copies with only the map word patched; each is loaded, the unit map is put at a
fixed origin by an Area map click on (101,46) (pinned scroll), the pointer parked, the screen captured and the tile cropped.
python3 probe_fleet_band.py <out_dir>"""
import hashlib, json, shutil, struct, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import fresh_save, load, _make_patched_fleet_split_save
from harness.driver import sh, AREA_ORIGIN
out = Path(sys.argv[1])
OFF = 101 * 280 + 46 * 2
JOINS = {"s24": (12, 12), "s25": (12, 13), "s49": (24, 25), "s50": (25, 25)}
word = lambda p: struct.unpack_from("<h", Path(p).read_bytes(), OFF)[0]
res = {"A": {}, "B": {}}
for name, (a, b) in JOINS.items():
    pre = _make_patched_fleet_split_save(a, b); shutil.copy(pre, out / f"{name}_PRE.SAV")
    g = fresh_save(pre)
    p0 = g.save_as(f"{name.upper()}_BEFORE.SAV"); shutil.copy(p0, out / f"{name}_BEFORE.SAV")
    texts = g.join_fleets(2)
    p1 = g.save_as(f"{name.upper()}_AFTER.SAV"); shutil.copy(p1, out / f"{name}_AFTER.SAV")
    f2 = [f for f in load(out / f"{name}_AFTER.SAV")["fleets"] if f["owner"] == 0]
    r = {"ships": [a, b], "popups": texts, "rome_fleets_after": [(f["id"], f["x"], f["y"], f["ships"]) for f in f2],
         "word_101_46": [word(out / f"{name}_{k}.SAV") for k in ("PRE", "BEFORE", "AFTER")], "mem_word": g.cell(101, 46)}
    res["A"][name] = r; print("A", name, json.dumps(r), flush=True)
    pre.unlink(missing_ok=True)
VARIANTS = {"w300_s24": ("s24", None), "w316_s25": ("s25", None), "w316_s49": ("s49", None), "w332_s50": ("s50", None),
            "w316_s24": ("s24", 316), "w332_s24": ("s24", 332), "w300_s50": ("s50", 300)}
for name, (src, w) in VARIANTS.items():
    data = bytearray((out / f"{src}_AFTER.SAV").read_bytes())
    if w is not None:
        struct.pack_into("<h", data, OFF, w)
    p = out / f"{name}.SAV"; p.write_bytes(bytes(data))
    g = fresh_save(p)
    g.reset_ui(); g.click(AREA_ORIGIN[0] + 101, AREA_ORIGIN[1] + 46, pause=1.0)     # pinned scroll: same origin every time
    cx, cy = g.show(101, 46)
    nx, ny = g.neutral_point(); sh("xdotool", "mousemove", str(nx), str(ny)); time.sleep(1.0)
    full = out / f"{name}_screen.png"; g.shot(full)
    tile = out / f"{name}_tile.png"
    subprocess.run(["convert", str(full), "-crop", f"32x32+{cx - 16}+{cy - 16}", "+repage", str(tile)], check=True)
    rgb = subprocess.run(["convert", str(tile), "rgb:-"], capture_output=True, check=True).stdout
    scr = subprocess.run(["convert", str(full), "rgb:-"], capture_output=True, check=True).stdout
    r = {"word": word(p), "mem_word": g.cell(101, 46), "view_origin": list(g.view_origin()), "tile_xy": [cx, cy],
         "tile_rgb_sha256": hashlib.sha256(rgb).hexdigest()[:16], "screen_rgb_sha256": hashlib.sha256(scr).hexdigest()[:16]}
    res["B"][name] = r; print("B", name, json.dumps(r), flush=True)
(out / "probe_fleet_band.json").write_text(json.dumps(res, indent=1))
