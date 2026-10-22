"""Simulate FUN_0044a6c8 on the stored ArmiesList / FleetsList templates with each nation's three dwords (+0x424/+0x428/+0x42C of
colours_PRE.SAV) and compare with the 96 drawn icons of run-exp-owner-colours/colours_screen.png (best offset, inside a 2 px border).
python3 check_recolour.py <out_dir>"""
import collections, json, struct, subprocess, sys
from pathlib import Path
out = Path(sys.argv[1]); R = Path(__file__).resolve().parents[4]
SAVE = R / "artifacts/run-exp-owner-colours/colours_PRE.SAV"
SHOT = R / "artifacts/run-exp-owner-colours/colours_screen.png"
raw = subprocess.run(["convert", str(SHOT), "-depth", "8", "rgb:-"], capture_output=True, check=True).stdout
spx = lambda x, y: raw[3 * (y * 1280 + x):3 * (y * 1280 + x) + 3].hex()
b = SAVE.read_bytes()
na = struct.unpack_from("<h", b, 100956)[0]; nf = struct.unpack_from("<h", b, 100956 + 2 + na * 656)[0]
nb = 100956 + 2 + na * 656 + 2 + nf * 26
rgb = lambda t: f"{t & 0xff:02x}{(t >> 8) & 0xff:02x}{(t >> 16) & 0xff:02x}"
cols = [[rgb(v) for v in struct.unpack_from("<3I", b, nb + o * 1172 + 0x424)] for o in range(16)]
tiles = {t["word"]: tuple(t["tile"]) for t in json.loads((R / "runs/experiments/data/run-exp-owner-colours/probe_colours.json").read_text())["tiles"] if t["repeat"] == 0}
res = []
for kind, base, ln in (("army", 200, "ArmiesList"), ("fleet", 300, "FleetsList")):
    bmp = (out / f"TUnitMap_{ln}.bmp").read_bytes()
    off, = struct.unpack_from("<I", bmp, 10); w, h, _, bpp = struct.unpack_from("<iiHH", bmp, 18)
    pal = [bmp[54 + 4 * i:54 + 4 * i + 3][::-1].hex() for i in range(256)]
    st = (w * bpp + 31) // 32 * 4
    for band in range(3):
        gx, gy = (band % 4) * 32, (band // 4) * 32
        tmpl = [pal[bmp[off + (h - 1 - (gy + y)) * st + gx + x]] for y in range(32) for x in range(32)]
        for o in range(16):
            m = {"800080": cols[o][0], "ffffff": cols[o][1], "0000ff": cols[o][2]}
            img = [m.get(c, c) for c in tmpl]
            word = base + 16 * band + o
            tx, ty = tiles[word]
            px0, py0 = 337 + 32 * (tx - 114), 96 + 30 + 32 * (ty - 46)
            best = min((sum(img[y * 32 + x] != spx(px0 + dx + x, py0 + dy + y) for y in range(2, 30) for x in range(2, 30)), dx, dy)
                       for dx in range(-3, 4) for dy in range(-3, 4))
            res.append({"kind": kind, "band": band, "owner": o, "word": word, "inset_mismatch": best[0], "offset": best[1:]})
(out / "recolour_check.json").write_text(json.dumps({"colours": cols, "icons": res}, indent=1))
print(len(res), "icons; inset mismatches:", collections.Counter(r["inset_mismatch"] for r in res), "offsets:", collections.Counter(tuple(r["offset"]) for r in res))
