"""Does the unit-map army icon differ by the marker's size band (2026-10-08)? Each variant is loaded, tile (120,53) (Rome
army 1) is brought into the unit map without selecting anything, the pointer is parked on the bare root window, the screen
is captured and the 32x32 tile cropped. Variants: the run-exp-army-marker-band AFTER saves (word and troops agree), and
copies with only the map word patched (same troops), to tell whether the icon follows the stored word or the troops.
python3 probe_icon.py <band_dir> <out_dir>"""
import hashlib, json, shutil, struct, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, "/home/diego/projects/ic2-conquest")
from tests.test_orders import fresh_save, load
from harness.driver import sh
band, out = Path(sys.argv[1]), Path(sys.argv[2])
OFF = 120 * 280 + 53 * 2
VARIANTS = {   # name: (source save, patched word or None)
    "w200_t24999": ("t24999_AFTER.SAV", None), "w216_t25000": ("t25000_AFTER.SAV", None),
    "w232_t50000": ("t50000_AFTER.SAV", None),
    "w216_t24999": ("t24999_AFTER.SAV", 216), "w232_t24999": ("t24999_AFTER.SAV", 232),
    "w200_t50000": ("t50000_AFTER.SAV", 200),
}
res = {}
for name, (src, word) in VARIANTS.items():
    data = bytearray((band / src).read_bytes())
    if word is not None:
        struct.pack_into("<h", data, OFF, word)
    p = out / f"{name}.SAV"; p.write_bytes(bytes(data))
    g = fresh_save(p)
    cx, cy = g.show(120, 53)
    nx, ny = g.neutral_point(); sh("xdotool", "mousemove", str(nx), str(ny)); time.sleep(1.0)
    full = out / f"{name}_screen.png"; g.shot(full)
    tile = out / f"{name}_tile.png"
    subprocess.run(["convert", str(full), "-crop", f"32x32+{cx - 16}+{cy - 16}", "+repage", str(tile)], check=True)
    rgb = subprocess.run(["convert", str(tile), "rgb:-"], capture_output=True, check=True).stdout
    a1 = next(a for a in load(p)["armies"] if a["id"] == 1)
    res[name] = {"word": struct.unpack_from("<h", p.read_bytes(), OFF)[0], "troops": a1["troops"], "mem_word": g.cell(120, 53),
                 "tile_xy": [cx, cy], "tile_rgb_sha256": hashlib.sha256(rgb).hexdigest()[:16]}
    print(name, json.dumps(res[name]), flush=True)
(out / "probe_icon.json").write_text(json.dumps(res, indent=1))
