"""Per owner: the nation-button glyph's colours by role (background 180 px, outline 104 px, fill 40 px, margin 76 px = transparent
for owners 5-14), the capital map icon's (run-exp-city-marker-colours analyse_cities.json, variant 4), the unit recolour dwords of
FUN_00448aa4 (nation record +0x424/+0x428/+0x42C, read from saves/run0-start-AUTO0720-seed12345.SAV), and the 2026-09-29 table.
python3 compare_roles.py <out_dir>"""
import json, struct, collections, sys
from pathlib import Path
out = Path(sys.argv[1]); R = Path(__file__).resolve().parents[4]
cities = json.loads((R / "runs/experiments/data/run-exp-city-marker-colours/analyse_cities.json").read_text())["comparison"]
b = (R / "saves/run0-start-AUTO0720-seed12345.SAV").read_bytes()
na = struct.unpack_from("<h", b, 100956)[0]; nf = struct.unpack_from("<h", b, 100956 + 2 + na * 656)[0]
nb = 100956 + 2 + na * 656 + 2 + nf * 26
rgb = lambda t: f"{t & 0xff:02x}{(t >> 8) & 0xff:02x}{(t >> 16) & 0xff:02x}"
rows = []
for g in json.loads((out / "glyphs.json").read_text()):
    o = g["owner"]
    bmp = (out / f"glyph_{g['name']}.bmp").read_bytes()
    off, = struct.unpack_from("<I", bmp, 10); w, h, _, bpp = struct.unpack_from("<iiHH", bmp, 18)
    pal = [bmp[54 + 4 * i:54 + 4 * i + 3][::-1].hex() for i in range(16)]
    st = (w * bpp + 31) // 32 * 4
    gp = lambda x, y: pal[(bmp[off + (h - 1 - y) * st + x // 2] >> 4) if x % 2 == 0 else (bmp[off + (h - 1 - y) * st + x // 2] & 15)]
    c = collections.Counter(gp(x, y) for y in range(20) for x in range(20))
    by = {n: col for col, n in c.items()}
    glyph = {"bg": by.get(180), "outline": by.get(104), "fill": by.get(40), "margin": by.get(76), "transparent": g["transparent_bottom_left"]["rgb"]}
    cc = cities[o]
    unit = [rgb(v) for v in struct.unpack_from("<3I", b, nb + o * 1172 + 0x424)]
    rows.append({"owner": o, "nation": cc["nation"], "glyph": glyph,
                 "capital_icon": {"bg": cc["city_bg"], "outline": cc["city_outline"], "fill": cc["city_fill"]},
                 "unit_recolour": {"bg": unit[0], "outline": unit[1], "fill": unit[2]},
                 "table_2026_09_29": {"outline": cc["old_outline"], "fg": cc["old_fg"]},
                 "glyph_eq_capital": (glyph["bg"], glyph["outline"], glyph["fill"]) == (cc["city_bg"], cc["city_outline"], cc["city_fill"]),
                 "glyph_eq_unit": [glyph["bg"], glyph["outline"], glyph["fill"]] == unit,
                 "table_eq_glyph": (cc["old_outline"], cc["old_fg"]) == (glyph["outline"], glyph["fill"]),
                 "table_eq_margin_outline": (cc["old_outline"], cc["old_fg"]) == (glyph["margin"], glyph["outline"])})
(out / "compare_roles.json").write_text(json.dumps(rows, indent=1))
for r in rows:
    g = r["glyph"]
    print(f"{r['owner']:2d} {r['nation']:10s} glyph {g['bg']} {g['outline']} {g['fill']} margin {g['margin']} | =capital {r['glyph_eq_capital']} =unit {r['glyph_eq_unit']} | table {r['table_2026_09_29']['outline']},{r['table_2026_09_29']['fg']} =glyph {r['table_eq_glyph']} =(margin,outline) {r['table_eq_margin_outline']}")
