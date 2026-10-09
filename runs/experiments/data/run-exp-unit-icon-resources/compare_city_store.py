"""Stored city images (TUnitMap Cities1-4List, CapitalsList; image index = owner) against the Wine tile crops of
run-exp-city-marker-colours (tiles/city_v<v>_o<oo>_w<word>.png), pixel for pixel inside a 2 px border, against the screenshot cities_screen1.png at the best offset, for all 80 city words.
Also per stored capital image: pixel counts per palette index and RGB. python3 compare_city_store.py <out_dir>"""
import collections, hashlib, json, struct, subprocess, sys
from pathlib import Path
out = Path(sys.argv[1]); R = Path("/home/diego/projects/ic2-conquest")
TILES = R / "artifacts/run-exp-city-marker-colours/tiles"
LISTS = ["Cities1List", "Cities2List", "Cities3List", "Cities4List", "CapitalsList"]
res = {"per_word": [], "capitals": []}
SHOT = R / "artifacts/run-exp-city-marker-colours/cities_screen1.png"
_raw = subprocess.run(["convert", str(SHOT), "-depth", "8", "rgb:-"], capture_output=True, check=True).stdout
spx = lambda x, y: _raw[3 * (y * 1280 + x):3 * (y * 1280 + x) + 3].hex()
TILE_AT = {t["word"]: tuple(t["tile"]) for t in json.loads((R / "artifacts/run-exp-city-marker-colours/probe_cities.json").read_text())["tiles"] if t["repeat"] == 0}
for v, ln in enumerate(LISTS):
    bmp = (out / f"TUnitMap_{ln}.bmp").read_bytes()
    off, = struct.unpack_from("<I", bmp, 10); w, h, _, bpp = struct.unpack_from("<iiHH", bmp, 18)
    pal = [bmp[54 + 4 * i:54 + 4 * i + 3][::-1].hex() for i in range(256)]
    st = (w * bpp + 31) // 32 * 4
    ix = lambda x, y: bmp[off + (h - 1 - y) * st + x]
    for o in range(16):
        gx, gy = (o % 4) * 32, (o // 4) * 32
        word = 20 + o + 16 * v
        stored = [pal[ix(gx + x, gy + y)] for y in range(2, 30) for x in range(2, 30)]
        # against the screenshot itself: the probe's crops sit 1 px right of the drawn tile, so search dx, dy in -3..3
        tx, ty = TILE_AT[word]
        px0, py0 = 337 + 32 * (tx - 114), 96 + 30 + 32 * (ty - 46)
        best = min((sum(stored[(y - 2) * 28 + (x - 2)] != spx(px0 + dx + x, py0 + dy + y) for y in range(2, 30) for x in range(2, 30)), dx, dy)
                   for dx in range(-3, 4) for dy in range(-3, 4))
        full = sum(pal[ix(gx + x, gy + y)] != spx(px0 + best[1] + x, py0 + best[2] + y) for y in range(32) for x in range(32))
        res["per_word"].append({"word": word, "variant": v, "owner": o, "list": ln, "image_index": o, "inset_mismatch": best[0],
                                "offset": best[1:], "full_tile_mismatch": full,
                                "stored_inset_sha": hashlib.sha256("".join(stored).encode()).hexdigest()[:16]})
        if v == 4:
            c = collections.Counter(ix(gx + x, gy + y) for y in range(32) for x in range(32))
            res["capitals"].append({"word": word, "owner": o, "pixels_by_index": {str(k): n for k, n in c.most_common()},
                                    "pixels_rgb": {pal[k]: n for k, n in c.most_common()}})
(out / "city_store_compare.json").write_text(json.dumps(res, indent=1))
bad = [r for r in res["per_word"] if r["inset_mismatch"]]
print("words compared", len(res["per_word"]), "with inset mismatches", len(bad), bad[:3])
print("offsets", collections.Counter(tuple(r["offset"]) for r in res["per_word"]), "full-tile mismatch values", collections.Counter(r["full_tile_mismatch"] for r in res["per_word"]).most_common(5))
