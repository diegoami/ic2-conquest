"""Find each stored nation-button glyph (up state: the left 20x20 of the 40x20 Glyph.Data) on the Wine screenshot
(run-exp-city-marker-colours/cities_screen1.png, toolbar row), pixel for pixel, ignoring the glyph's transparent colour (its bottom-left
pixel). Reports the best position and the number of mismatching non-transparent pixels. python3 match_toolbar.py <out_dir>"""
import json, struct, subprocess, sys
from pathlib import Path
out = Path(sys.argv[1]); R = Path(__file__).resolve().parents[4]
shot = R / "artifacts/run-exp-city-marker-colours/cities_screen1.png"
W, H = 1280, 1024
raw = subprocess.run(["convert", str(shot), "-depth", "8", "rgb:-"], capture_output=True, check=True).stdout
spx = lambda x, y: raw[3 * (y * W + x):3 * (y * W + x) + 3].hex()
res = []
for g in json.loads((out / "glyphs.json").read_text()):
    bmp = (out / f"glyph_{g['name']}.bmp").read_bytes()
    off, = struct.unpack_from("<I", bmp, 10); w, h, _, bpp = struct.unpack_from("<iiHH", bmp, 18)
    pal = [bmp[54 + 4 * i:54 + 4 * i + 3][::-1].hex() for i in range(16)]
    st = (w * bpp + 31) // 32 * 4
    gp = lambda x, y: pal[(bmp[off + (h - 1 - y) * st + x // 2] >> 4) if x % 2 == 0 else (bmp[off + (h - 1 - y) * st + x // 2] & 15)]
    tr = gp(0, h - 1)
    pts = [(x, y, gp(x, y)) for y in range(20) for x in range(20) if gp(x, y) != tr]
    best = None
    for oy in range(36, 64):
        for ox in range(220, 640):
            bad = 0
            for x, y, c in pts:
                if spx(ox + x, oy + y) != c:
                    bad += 1
                    if best and bad >= best[0]:
                        break
            if best is None or bad < best[0]:
                best = (bad, ox, oy)
    res.append({"owner": g["owner"], "name": g["name"], "transparent": tr, "opaque_pixels": len(pts), "best_mismatch": best[0], "at": best[1:]})
    print(g["name"], "opaque", len(pts), "mismatch", best[0], "at", best[1:], flush=True)
(out / "toolbar_match.json").write_text(json.dumps(res, indent=1))
