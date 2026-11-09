#!/usr/bin/env python3
"""Research #223: scalar receipt for the original's toolbar glyphs and area-map lists.

Reads the pinned original EXE (read-only, no media written) with the accepted
extractor's parsers and writes a JSON receipt of scalars only: component paths,
hints, OnClick identifiers, published-field offsets, handler addresses, glyph
geometry, transparent-key palette index, identical-image groups, and per-index
counts for TAreaMap.PointsList / MapsList. No pixels, crops or hashes of
original content leave the process.

Usage (python3 -I, explicit inputs, receipt path must not exist):
  python3 -I scan_command_glyphs.py --exe EXE --extractor scripts/extract_original_assets.py \
      --symbols $IC2_DECOMPILE/delphi_symbols.tsv --dump $IC2_DECOMPILE/all_app_functions.txt \
      --save saves/fortify-arretium-0720.SAV --repo . --out receipt.json
"""
import argparse, collections, hashlib, importlib.util, json, os, re, struct, sys

EXE_SHA = "9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31"
DUMP_SHA = "2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8"
EXTRACTOR_SHA = "5d266a075ce1cc75ccb359f2b4a64aa5bbf82e2dca031965c729e6abd53a97f5"
# StrategicDecision / ChangePauses / UseFindCity dialog targets (VMT addresses read from the dump).
VMTS = ["0x452208", "0x4533cc", "0x453c44", "0x454138", "0x455600", "0x43d438", "0x4365bc"]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_extractor(path):
    spec = importlib.util.spec_from_file_location("extract_original_assets", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def pe_map(d):
    pe = struct.unpack_from("<I", d, 60)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    optsz = struct.unpack_from("<H", d, pe + 20)[0]
    base = struct.unpack_from("<I", d, pe + 24 + 28)[0]
    secs = []
    for i in range(nsec):
        o = pe + 24 + optsz + 40 * i
        vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
        secs.append((va, max(vs, rs), rp))

    def off(addr):
        r = addr - base
        for va, sz, rp in secs:
            if va <= r < va + sz:
                return rp + r - va
        raise ValueError("address outside image")
    return off


def class_name_at_vmt(d, off, vmt):
    """Delphi class name: the shortstring pointed to by the VMT slot at -0x1C."""
    p = struct.unpack_from("<I", d, off(vmt - 0x1C))[0]
    o = off(p)
    return d[o + 1:o + 1 + d[o]].decode("latin-1")


def field_offsets(d, name):
    """Published field table entries: <dword offset><word class index><shortstring name>."""
    pat = bytes([len(name)]) + name.encode()
    hits = []
    for m in re.finditer(re.escape(pat), d):
        p = m.start()
        fo, idx = struct.unpack_from("<IH", d, p - 6)
        if 0x100 <= fo < 0x1000 and idx < 64:
            hits.append(fo)
    return hits


def main():
    ap = argparse.ArgumentParser()
    for a in ("--exe", "--extractor", "--symbols", "--dump", "--save", "--repo", "--out"):
        ap.add_argument(a, required=True)
    args = ap.parse_args()
    if os.path.exists(args.out):
        sys.exit("receipt exists; use a new name (rule 6)")
    d = open(args.exe, "rb").read()
    dump = open(args.dump, "rb").read()
    ext_bytes = open(args.extractor, "rb").read()
    pins = {"exe_sha256": sha(d), "dump_sha256": sha(dump), "dump_lines": dump.count(b"\n"),
            "extractor_sha256": sha(ext_bytes)}
    pins["pins_match"] = (pins["exe_sha256"] == EXE_SHA and pins["dump_sha256"] == DUMP_SHA
                          and pins["extractor_sha256"] == EXTRACTOR_SHA)
    X = load_extractor(args.extractor)
    sys.path.insert(0, args.repo)
    from state import sav
    symbols = {}
    for line in open(args.symbols, encoding="latin-1"):
        a, _, n = line.rstrip("\n").partition("\t")
        if n:
            symbols[n] = a
    off = pe_map(d)
    receipt = {"schema": "ic2-assets223/1", "pins": pins, "glyphs": [], "lists": [], "dialogs": {}}
    receipt["dialogs"] = {v: class_name_at_vmt(d, off, int(v, 16)) for v in VMTS}
    groups = collections.defaultdict(list)
    save = sav.load(args.save)
    for res in X.pe_resources(d):
        blob = X.span(d, res["offset"], res["bytes"])
        if not (res["type"] == 10 and blob.startswith(b"TPF0")):
            continue
        obj = X.DFMReader(blob).parse()
        form = obj["class"]

        def walk(n, path):
            p = n["props"]
            if n["class"] == "TSpeedButton" and "Glyph.Data" in p:
                bm = X.Bitmap.read(p["Glyph.Data"][4:])
                count = p.get("NumGlyphs", 1)
                w = bm.width // count
                key_index = bm.indices[(bm.height - 1) * bm.width]
                key = bm.palette[key_index]
                frames = []
                for f in range(count):
                    px = bm.crop(f * w, 0, w, bm.height)
                    frames.append({"frame": f, "key_pixels": sum(bm.palette[v] == key for v in px),
                                   "distinct_indices": len(set(px))})
                content = sha(bytes(bm.indices) + repr(bm.palette).encode())
                groups[content].append(f"{form}.{n['name']}")
                handler = p.get("OnClick")
                fo = field_offsets(d, n["name"])
                row = {"form": form, "component": path, "hint": p.get("Hint"), "onclick": handler,
                       "handler_symbol": f"{form}_{handler}" if handler else None,
                       "handler_address": symbols.get(f"{form}_{handler}"),
                       "field_offsets_named": [hex(x) for x in fo],
                       "num_glyphs": count, "sheet": [bm.width, bm.height], "frame": [w, bm.height],
                       "bpp": bm.bpp, "palette_entries": len(bm.palette),
                       "palette_is_windows16": bm.palette == WIN16,
                       "key_palette_index": key_index, "key_rgb_hex": "%02x%02x%02x" % key,
                       "key_rgb_in_other_slots": [k for k, c in enumerate(bm.palette) if c == key and k != key_index],
                       "frames": frames, "visible_in_dfm": p.get("Visible", True),
                       "group_index": p.get("GroupIndex", 0), "allow_all_up": p.get("AllowAllUp", False),
                       "_content": content,
                       **{k: v for k, v in X.glyph_semantic(form, n["name"]).items()
                          if k in ("candidate_key", "mapping_status")}}
                receipt["glyphs"].append(row)
            if n["class"] == "TImageList" and n["name"] in ("PointsList", "MapsList") and "Bitmap" in p:
                W, H = p.get("Width", 32), p.get("Height", 32)
                col, mask, count = X.image_list(p["Bitmap"], W, H)
                cols = col.width // W
                cells = []
                for k in range(count):
                    x, y = (k % cols) * W, (k // cols) * H
                    ci, mi = col.crop(x, y, W, H), mask.crop(x, y, W, H)
                    cell = {"index": k, "mask_opaque": sum(m == 0 for m in mi),
                            "mask_transparent": sum(m == 1 for m in mi),
                            "colour_counts": {"%02x%02x%02x" % c: v for c, v in
                                              collections.Counter(col.palette[c] for c in ci).most_common()}}
                    if n["name"] == "MapsList":
                        cm = collections.Counter()
                        for yy in range(H):
                            for xx in range(W):
                                code = sav.cell(save, xx, yy)
                                cls = ("sea" if code in (0, 1) else sav.terrain_name(code) if code < 12 else "marker")
                                cm[cls + ":" + "%02x%02x%02x" % col.palette[ci[yy * W + xx]]] += 1
                        cell["terrain_vs_colour"] = dict(sorted(cm.items()))
                    cells.append(cell)
                distinct = len({sha(col.crop((k % cols) * W, (k // cols) * H, W, H)) for k in range(count)})
                receipt["lists"].append({"form": form, "component": path, "cell": [W, H],
                                         "sheet": [col.width, col.height], "count": count,
                                         "colour_bpp": col.bpp, "mask_bpp": mask.bpp,
                                         "distinct_cells": distinct,
                                         "field_offsets_named": [hex(x) for x in field_offsets(d, n["name"])],
                                         "dfm_props": {k: v for k, v in p.items() if k != "Bitmap"},
                                         "cells": cells})
            for c in n["children"]:
                walk(c, path + "/" + c["name"])
        walk(obj, obj["name"])
    # Identical-image groups by index, not by hash (no content digests in the receipt).
    ids = {}
    for g in receipt["glyphs"]:
        ids.setdefault(g["_content"], len(ids))
        g["image_group"] = ids[g["_content"]]
        del g["_content"]
    receipt["identical_glyph_images"] = [v for v in groups.values() if len(v) > 1]
    receipt["summary"] = {"glyph_sheets": len(receipt["glyphs"]),
                          "with_candidate_key": sum(bool(g["candidate_key"]) for g in receipt["glyphs"]),
                          "keys": sorted(g["candidate_key"] for g in receipt["glyphs"] if g["candidate_key"])}
    with open(args.out, "x") as fh:
        json.dump(receipt, fh, indent=1, default=str)
        fh.write("\n")
    print(json.dumps({"pins_match": pins["pins_match"], **{k: v for k, v in receipt["summary"].items() if k != "keys"}}))


WIN16 = ((0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0), (0, 0, 128), (128, 0, 128), (0, 128, 128),
         (192, 192, 192), (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255),
         (255, 0, 255), (0, 255, 255), (255, 255, 255))

if __name__ == "__main__":
    main()
