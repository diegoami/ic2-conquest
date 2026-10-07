#!/usr/bin/env python3
"""A01 run-length measurement (canonical, PIL-free): the byte-flag in TAreaMap_PaintForm is an ImageList index, so the
two toggle states are two image sets of the same tile bitmap. The two sets differ in their run-length profile: a
uniform/political map has long runs of identical grey per row; a per-tile-shaded terrain map has short runs.

usage: a01_runs.py [BEFORE.png AFTER.png]

Reads two PNGs (default: the b8 screenshots under artifacts/run-exp-cosmetic-gaps/), converts to a single grey
channel per pixel (one byte per pixel), then for every 4th row of the bitmap crop (x=8+34 304x150, the map area
below the Y row of speed buttons) prints the mean / median / max / sample count of identical-grey-pixel runs.

Exits non-zero when the byte-1 mean is not at least 1.5x the byte-0 mean: the finding's
[confirmed by measurement] annotation depends on this distinction holding for the cited screenshots."""
import os, struct, zlib, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'artifacts', 'run-exp-cosmetic-gaps'))

# ----- PNG ---- decode to a single grey byte per pixel (ctype 0 gray, 2 RGB, 3 palette, 4 RGBA) -----
def _decode_png(path):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos, chunks = 8, []
    while pos < len(data):
        L, T = struct.unpack('>I4s', data[pos:pos + 8]); pos += 8
        body = data[pos:pos + L]; pos += L + 4
        chunks.append((T, body))
    ihdr = next(b for t, b in chunks if t == b'IHDR')
    W, H, depth, ctype, *_ = struct.unpack('>IIBBBBB', ihdr)
    assert depth == 8, 'only 8-bit PNGs supported (got %d-bit)' % depth
    raw = zlib.decompress(b''.join(b for t, b in chunks if t == b'IDAT'))
    bpp = {0: 1, 2: 3, 3: 1, 4: 2}[ctype]
    rows = []
    prev = bytes(W * bpp)
    p = 0
    for y in range(H):
        ftype = raw[p]; p += 1
        row = bytearray(raw[p:p + W * bpp]); p += W * bpp
        if ftype == 1:
            for x in range(bpp, len(row)): row[x] = (row[x] + row[x - bpp]) & 0xFF
        elif ftype == 2:
            for x in range(len(row)): row[x] = (row[x] + prev[x]) & 0xFF
        elif ftype == 3:
            for x in range(len(row)):
                a = row[x - bpp] if x >= bpp else 0
                b = prev[x]
                row[x] = (row[x] + (a + b) // 2) & 0xFF
        elif ftype == 4:
            for x in range(len(row)):
                a = row[x - bpp] if x >= bpp else 0     # left (reconstructed: same row, bpp bytes to the left)
                b = prev[x]                              # above (already reconstructed: previous row's byte)
                c = prev[x - bpp] if x >= bpp else 0     # upper-left (previous row, bpp to the left)
                p = a + b - c                            # initial prediction
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                if pa <= pb and pa <= pc: pr = a
                elif pb <= pc: pr = b
                else: pr = c                            # Paeth's SELECTOR is the predictor value a/b/c
                row[x] = (row[x] + pr) & 0xFF
        rows.append(bytes(row)); prev = rows[-1]
    if ctype == 0:
        return W, H, b''.join(rows)
    if ctype == 2:
        grey = bytearray(W * H)
        for y, row in enumerate(rows):
            o = y * W
            for x in range(W):
                r, g, b = row[3 * x], row[3 * x + 1], row[3 * x + 2]
                grey[o + x] = (r * 299 + g * 587 + b * 114) // 1000
        return W, H, bytes(grey)
    if ctype == 3:
        plte = next(b for t, b in chunks if t == b'PLTE')
        out = bytearray(W * H)
        for y, row in enumerate(rows):
            for x in range(W):
                out[y * W + x] = plte[row[x] * 3]
        return W, H, bytes(out)
    if ctype == 4:
        grey = bytearray(W * H)
        for y, row in enumerate(rows):
            o = y * W
            for x in range(W):
                r, g, b = row[4 * x], row[4 * x + 1], row[4 * x + 2]
                grey[o + x] = (r * 299 + g * 587 + b * 114) // 1000
        return W, H, bytes(grey)
    raise ValueError('unsupported color type %d' % ctype)

# ----- measure the map-face crop's identical-grey-pixel runs -----
def measure(path, l=8, t=34, w=304, h=150, step=4):
    """Return (mean, median, max, n_runs) of identical-grey-byte runs across every step-th row of the crop."""
    W, H, pix = _decode_png(path)
    runs = []
    for y0 in range(0, h, step):
        row = pix[(t + y0) * W + l: (t + y0) * W + l + w]
        run = 1
        for x in range(1, w):
            if row[x] == row[x - 1]:
                run += 1
            else:
                runs.append(run); run = 1
        runs.append(run)
    return statistics.mean(runs), statistics.median(runs), max(runs), len(runs)

def main():
    args = sys.argv[1:]
    a = args[0] if args else os.path.join(ART, 'CG_T3_b8_area_before.png')          # byte 1
    b = args[1] if len(args) > 1 else os.path.join(ART, 'CG_T3_b8_area_after_one.png') # byte 0
    for f in (a, b):
        if not os.path.exists(f):
            sys.exit('missing screenshot %s' % f)
    ma, meda, mxa, na = measure(a)
    mb, medb, mxb, nb = measure(b)
    ratio = ma / mb
    print('byte 1: mean=%.2fpx median=%d max=%d n=%d   (%s)' % (ma, meda, mxa, na, a))
    print('byte 0: mean=%.2fpx median=%d max=%d n=%d   (%s)' % (mb, medb, mxb, nb, b))
    print('ratio byte1/byte0: %.2fx' % ratio)
    if ratio < 1.5:
        sys.exit('run-length ratio below 1.5x — the measurement no longer distinguishes the two states')
    if not (ma > mb):
        sys.exit('byte-1 mean is not greater than byte-0 mean')

if __name__ == '__main__':
    main()