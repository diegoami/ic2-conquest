"""Simulate the battle form's sprite build (0x436fb4: BatMapList images 0-14 through FUN_0044a6c8 with the attacker army's owner,
then again with the defender's owner) and compare with the drawn battle cells of B2's Wine screenshots (Rome v Gaul).
Colours from the save's nation records (+0x424/+0x428/+0x42C), owners from the save's army records, sprites from its battle block.
Also the ground: every empty cell against BatMapList image 15. Then print what the same templates give with Numidia's (owner 5) three dwords.
python3 check_battle_recolour.py <out_json> [<folder> <save> <png> ...]   (default: the B2 pairs)"""
import collections, json, struct, subprocess, sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R))
from state import sav, battle_block as BB
A = R / "artifacts/run-exp-battle-sweep"
PAIRS = [("B2_placement.SAV", "b2_placement_window.png"), ("B2_after_end_turn_1.SAV", "b2_after_end_turn_1_window.png"),
         ("B2_after_end_turn_2.SAV", "b2_after_end_turn_2_window.png")]
if len(sys.argv) > 2:          # other pairs: <out_json> <folder> <save> <png> [<save> <png> ...]
    A = Path(sys.argv[2]); PAIRS = list(zip(sys.argv[3::2], sys.argv[4::2]))
Y0, T = 28, 32
bmp = (R / "artifacts/run-exp-unit-icon-resources/TBattleMap_BatMapList.bmp").read_bytes()
off, = struct.unpack_from("<I", bmp, 10); w, h, _, bpp = struct.unpack_from("<iiHH", bmp, 18)
pal = [bmp[54 + 4 * i:54 + 4 * i + 3][::-1].hex() for i in range(256)]
st = (w * bpp + 31) // 32 * 4
tmpl = [[pal[bmp[off + (h - 1 - ((k // 4) * 32 + y)) * st + (k % 4) * 32 + x]] for y in range(32) for x in range(32)] for k in range(16)]          # 0-14 unit templates, 15 the ground tile
rgb = lambda t: f"{t & 0xff:02x}{(t >> 8) & 0xff:02x}{(t >> 16) & 0xff:02x}"
def colours(raw):
    p = sav.parse(raw)
    na = struct.unpack_from("<h", raw, 100956)[0]; nf = struct.unpack_from("<h", raw, 100956 + 2 + na * 656)[0]
    nb = 100956 + 2 + na * 656 + 2 + nf * 26
    return [[rgb(v) for v in struct.unpack_from("<3I", raw, nb + o * 1172 + 0x424)] for o in range(16)], p
recolour = lambda k, c: [{"800080": c[0], "ffffff": c[1], "0000ff": c[2]}.get(v, v) for v in tmpl[k]]
res = {"pairs": [], "numidia": None}
for sv, png in PAIRS:
    raw = (A / sv).read_bytes()
    cols, p = colours(raw)
    blk = BB.block_of_save(raw)
    owners = [p["armies"][blk["attacker_army"]]["owner"], p["armies"][blk["defender_army"]]["owner"]]
    shot = subprocess.run(["convert", str(A / png), "-depth", "8", "rgb:-"], capture_output=True, check=True).stdout
    W = 448
    spx = lambda x, y: shot[3 * (y * W + x):3 * (y * W + x) + 3].hex()
    cells, ground = [], []
    for gx in range(14):
        for gy in range(12):
            word = blk["grid"][BB.cell(gx, gy)]
            if word == 50:
                gm = sum(tmpl[15][y * 32 + x] != spx(gx * T + x, Y0 + 2 + gy * T + y) for y in range(32) for x in range(32)
                         if Y0 + 2 + gy * T + y < 414)
                ground.append(gm)
                continue
            side, k = divmod(word, 20)
            img = recolour(k, cols[owners[side]])
            best = min((sum(img[y * 32 + x] != spx(gx * T + dx + x, Y0 + gy * T + dy + y) for y in range(32) for x in range(32)
                            if 0 <= gx * T + dx + x < W and 0 <= Y0 + gy * T + dy + y < 414), dx, dy)
                       for dx in range(-2, 3) for dy in range(-2, 3))
            cells.append({"cell": [gx, gy], "word": word, "side": side, "owner": owners[side], "mismatch": best[0], "offset": best[1:]})
    res["pairs"].append({"save": sv, "screenshot": png, "owners": owners, "colours_of_owners": [cols[o] for o in owners], "cells": cells,
                       "ground_cells": len(ground), "ground_mismatch_counts": dict(collections.Counter(ground))})
    print(sv, "owners", owners, "cells", len(cells), "mismatches", collections.Counter(c["mismatch"] for c in cells),
          "offsets", collections.Counter(tuple(c["offset"]) for c in cells),
          "ground cells", len(ground), "ground mismatches", collections.Counter(ground))
cols, _ = colours((A / PAIRS[0][0]).read_bytes())
res["numidia"] = {"dwords": cols[5], "template_counts": [dict(collections.Counter(recolour(k, cols[5]))) for k in range(15)]}
print("Numidia dwords (bg, outline, fill):", cols[5]); print("template 4 as Numidia:", res["numidia"]["template_counts"][4])
Path(sys.argv[1]).write_text(json.dumps(res, indent=1))
