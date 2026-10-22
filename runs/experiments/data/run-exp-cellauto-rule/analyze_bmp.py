"""Read a ca*.BMP written by TCellAuto_SaveBMP: header fields, then compare its pixels with the model of check_cellauto.py (rule from the
file name's 10 digits; seed row 144-155) drawn at y = row. Pixels the model leaves unpainted (run ends) are reported by colour; with
--prev <bmp>, they are also compared with that earlier file's pixels (carry-over between N presses).
python3 analyze_bmp.py <bmp> [--prev <bmp>]"""
import collections, json, re, struct, sys
from pathlib import Path
sys.argv, _a = sys.argv[:1], sys.argv[1:]
import importlib.util
COL = ["ffffff", "ff0000", "0000ff", "008000"]; N, ROWS = 300, 400
def simulate(table):
    row = [0] * N
    for i in range(144, 156): row[i] = 1
    rows = [row]
    for _ in range(ROWS - 1):
        old = [0] + row + [0]
        row = [table[old[i] + old[i + 1] + old[i + 2]] for i in range(N)]
        rows.append(row)
    return rows
def painted(rows):
    """Per row: list of colour or None (the run's unpainted end)."""
    out = []
    for row in rows:
        line = [None] * N; s = 0
        for d in range(N):
            if d < N - 1 and row[d + 1] == row[s]: continue
            if d == s: line[s] = COL[row[s]]
            else:
                for x in range(s, d): line[x] = COL[row[s]]
            s = d + 1
        out.append(line)
    return out
def read(p):
    b = Path(p).read_bytes()
    fsize, _, _, off = struct.unpack_from("<IHHI", b, 2)
    hs, w, h, planes, bpp, comp, isz, xppm, yppm, used, imp = struct.unpack_from("<IiiHHIIiiII", b, 14)
    hdr = dict(magic=b[:2].decode(), file_size=fsize, actual_size=len(b), data_offset=off, header_size=hs, width=w, height=h,
               planes=planes, bpp=bpp, compression=comp, image_size=isz, xppm=xppm, yppm=yppm, clr_used=used, clr_important=imp,
               palette_entries=(off - 14 - hs) // 4, bottom_up=h > 0)
    assert bpp == 24 and comp == 0
    st = (w * 3 + 3) // 4 * 4
    px = [[b[off + (h - 1 - y if h > 0 else y) * st + 3 * x:off + (h - 1 - y if h > 0 else y) * st + 3 * x + 3][::-1].hex() for x in range(w)] for y in range(abs(h))]
    return hdr, px
bmp = _a[0]; prev = _a[_a.index("--prev") + 1] if "--prev" in _a else None
hdr, px = read(bmp)
digits = re.search(r"ca(\d{10})\.BMP$", bmp, re.I).group(1)
model = painted(simulate([int(c) for c in digits]))
mism = sum(model[y][x] is not None and model[y][x] != px[y][x] for y in range(ROWS) for x in range(N))
gaps = [(x, y) for y in range(ROWS) for x in range(N) if model[y][x] is None]
res = {"file": Path(bmp).name, "header": hdr, "rule": digits, "painted_pixels": N * ROWS - len(gaps), "painted_mismatch": mism,
       "unpainted": len(gaps), "unpainted_colours": dict(collections.Counter(px[y][x] for x, y in gaps)),
       "file_colours": dict(collections.Counter(c for r in px for c in r))}
if prev:
    _, pp = read(prev)
    res["prev"] = Path(prev).name
    res["unpainted_equal_prev"] = sum(px[y][x] == pp[y][x] for x, y in gaps)
print(json.dumps(res, indent=1))
