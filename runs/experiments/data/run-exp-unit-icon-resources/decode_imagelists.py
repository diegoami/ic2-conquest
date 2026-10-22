"""Decode the TImageList blobs written by extract_imagelists.py: Delphi 2 stream = u32 size, u32 image count, then a BMP file (the
image grid, 4 images per row of 32x32) and, after it, the mask BMP. Writes <list>.png (image grid), <list>_mask.png, and for each image
its palette indices used and their RGB colours. python3 decode_imagelists.py <out_dir>"""
import json, struct, subprocess, sys, collections
from pathlib import Path
out = Path(sys.argv[1])
meta = json.loads((out / "imagelists.json").read_text())
report = []
for l in meta["lists"]:
    name = f"{l['form']}_{l['name']}"
    b = (out / f"{name}.bin").read_bytes()
    size, count = struct.unpack_from("<II", b, 0)
    bmp = b[8:8 + size]
    assert bmp[:2] == b"BM", name
    (out / f"{name}.bmp").write_bytes(bmp)
    rest = b[8 + size:]
    mask = None
    i = rest.find(b"BM")
    if i >= 0:
        msize = struct.unpack_from("<I", rest, i + 2)[0]
        mask = rest[i:i + msize]; (out / f"{name}_mask.bmp").write_bytes(mask)
    off, = struct.unpack_from("<I", bmp, 10)
    w, h, planes, bpp = struct.unpack_from("<iiHH", bmp, 18)
    ncol = struct.unpack_from("<I", bmp, 46)[0] or (1 << bpp)
    pal = [bmp[54 + 4 * k:54 + 4 * k + 3][::-1].hex() for k in range(ncol)]          # BGRx -> RGB hex
    rows = abs(h); stride = (w * bpp + 31) // 32 * 4
    px = lambda x, y: bmp[off + (rows - 1 - y) * stride + x] if h > 0 else bmp[off + y * stride + x]
    imgs = []
    for k in range(count):
        iw, ih = l["props"].get("Width", 32), l["props"].get("Height", 32)
        gx, gy = (k % (w // iw)) * iw, (k // (w // iw)) * ih
        c = collections.Counter(px(gx + x, gy + y) for y in range(ih) for x in range(iw))
        imgs.append({"index": k, "palette_indices": {str(i): n for i, n in c.most_common()}, "rgb": {pal[i]: n for i, n in c.most_common()}})
    subprocess.run(["convert", str(out / f"{name}.bmp"), str(out / f"{name}.png")], check=True)
    report.append({"list": name, "count": count, "bmp": [w, h, bpp], "palette_size": ncol, "mask": mask is not None, "images": imgs})
    print(name, "count", count, "bmp", w, h, bpp, "mask", mask is not None)
(out / "imagelists_decoded.json").write_text(json.dumps(report, indent=1))
