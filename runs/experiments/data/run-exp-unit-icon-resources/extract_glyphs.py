"""The main form's 16 nation buttons (TPremierForm sb_<Nation>): class, events, NumGlyphs/Layout/Margin, and the Glyph.Data bitmap
(4-byte length + BMP), decoded read-only: size, depth, palette (RGB), pixel counts per index, the bottom-left (transparent) colour.
Writes glyph_<name>.bmp / .png and glyphs.json. python3 extract_glyphs.py <exe> <out_dir>"""
import collections, hashlib, json, re, struct, subprocess, sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R / "runs/experiments/feature_inventory"))
import extract_forms as EF
_orig = EF.value
def value(r):
    if r.d[r.p] == 10:
        r.p += 1; n = r.i(4, "<I"); v = bytes(r.d[r.p:r.p + n]); r.p += n; return {"bytes": v}
    return _orig(r)
EF.value = value
NAMES = ['Rome', 'Carthage', 'Seleucid', 'Ptolemaic', 'Macedonia', 'Numidia', 'Gaul', 'Greece', 'Celtiberia', 'Illyria', 'Dacia',
         'Bithynia', 'Galatia', 'Armenia', 'Media', 'Thracia']
exe, out = Path(sys.argv[1]), Path(sys.argv[2])
d = exe.read_bytes()
found = {}
for m in re.finditer(rb"TPF0", d):
    s = m.start()
    if d[s + 4] == 0 or d[s + 5:s + 6] != b"T":
        continue
    try:
        o = EF.obj(EF.P(d, s + 4))
    except Exception:
        continue
    def walk(n):
        if n["name"] in {f"sb_{x}" for x in NAMES}:
            found[n["name"]] = (o["class"], n)
        for c in n["children"]:
            walk(c)
    walk(o)
res = []
for k, nat in enumerate(NAMES):
    form, n = found[f"sb_{nat}"]
    blob = n["props"]["Glyph.Data"]["bytes"]
    ln = struct.unpack_from("<I", blob, 0)[0]; bmp = blob[4:4 + ln]
    off, = struct.unpack_from("<I", bmp, 10); w, h, _, bpp = struct.unpack_from("<iiHH", bmp, 18)
    ncol = struct.unpack_from("<I", bmp, 46)[0] or (1 << bpp)
    pal = [bmp[54 + 4 * i:54 + 4 * i + 3][::-1].hex() for i in range(ncol)]
    stride = (w * bpp + 31) // 32 * 4
    def idx(x, y):                       # y from the top
        row = off + (abs(h) - 1 - y) * stride if h > 0 else off + y * stride
        if bpp == 8: return bmp[row + x]
        byte = bmp[row + x // 2]; return (byte >> 4) if x % 2 == 0 else (byte & 15)
    cnt = collections.Counter(idx(x, y) for y in range(abs(h)) for x in range(w))
    bl = idx(0, abs(h) - 1)
    p = out / f"glyph_{n['name']}.bmp"; p.write_bytes(bmp)
    subprocess.run(["convert", str(p), str(p.with_suffix(".png"))], check=True)
    res.append({"owner": k, "name": n["name"], "class": n["class"], "form": form,
                "props": {kk: vv for kk, vv in n["props"].items() if kk != "Glyph.Data"},
                "bmp": {"w": w, "h": h, "bpp": bpp, "palette_size": ncol}, "sha256": hashlib.sha256(bmp).hexdigest(),
                "transparent_bottom_left": {"index": bl, "rgb": pal[bl]},
                "pixels": {pal[i]: c for i, c in cnt.most_common()}, "pixels_by_index": {str(i): c for i, c in cnt.most_common()}})
(out / "glyphs.json").write_text(json.dumps(res, indent=1, default=str))
for r in res:
    print(r["owner"], r["name"], r["class"], r["bmp"], "transp", r["transparent_bottom_left"]["rgb"], r["pixels"],
          {k: v for k, v in r["props"].items() if k in ("NumGlyphs", "Layout", "Margin", "OnClick")})
