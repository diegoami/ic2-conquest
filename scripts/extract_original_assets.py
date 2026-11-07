#!/usr/bin/env python3
"""Portable IC2 original-resource extractor. Python 3.10+, standard library only.

Metadata is the default output. Optional media is written only to a new, explicit
private directory. This file can be copied independently of the conquest repo.
No game process, Wine, ImageMagick or installed Python package is required.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import zlib

VERSION = "1.0.1"
SCHEMA = "ic2-original-assets/1"
EXE_PIN = "9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31"
PROFILES = {EXE_PIN: "ic2-original-1996-pinned"}
MAX_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 4_000_000
MAX_NODES = 20_000
RESOURCE_TYPES = {1: "cursor", 2: "bitmap", 3: "icon", 6: "string",
                  10: "rcdata", 12: "group_cursor", 14: "group_icon"}
NATIONS = ("Rome", "Carthage", "Seleucid", "Ptolemaic", "Macedonia", "Numidia",
           "Gaul", "Greece", "Celtiberia", "Illyria", "Dacia", "Bithynia",
           "Galatia", "Armenia", "Media", "Thracia")
UNIT_TYPES = ("light_infantry", "heavy_infantry", "archers", "light_cavalry", "heavy_cavalry")
SIZES = ("small", "medium", "large")
SOUNDS = ("unit_move", "fleet_move", "battle_arrows", "battle_javelin",
          "battle_melee", "siege_failed", "city_captured", "fleet_sunk", "battle",
          "nation_conquered")


class Invalid(ValueError):
    """Malformed/truncated input, distinct from an unsupported encoding/profile."""


class Unsupported(ValueError):
    """Well-bounded input for a format that is not implemented/qualified."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def span(data, offset, size):
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise Invalid("range outside input")
    return data[offset:offset + size]


def unpack(fmt, data, offset=0):
    return struct.unpack(fmt, span(data, offset, struct.calcsize(fmt)))


def read_file(path):
    with Path(path).open("rb") as f:
        data = f.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise Invalid("input exceeds 64 MiB limit")
    return data


def pe_resources(data):
    """Return bounded PE32 resource leaves, preserving numeric vs named IDs."""
    if span(data, 0, 2) != b"MZ":
        raise Invalid("missing DOS signature")
    pe, = unpack("<I", data, 60)
    if span(data, pe, 4) != b"PE\0\0":
        raise Invalid("missing PE signature")
    _, sections, _, _, _, opt_size, _ = unpack("<HHIIIHH", data, pe + 4)
    opt = pe + 24
    span(data, opt, opt_size)
    if unpack("<H", data, opt)[0] != 0x10B:
        raise Unsupported("only PE32 optional headers are qualified")
    if opt_size < 120 or unpack("<I", data, opt + 92)[0] < 3:
        raise Invalid("resource directory missing from optional header")
    if not 0 < sections <= 96:
        raise Invalid("invalid section count")
    ranges = []
    for i in range(sections):
        entry = span(data, opt + opt_size + 40 * i, 40)
        virtual_size, rva, raw_size, raw = unpack("<IIII", entry, 8)
        span(data, raw, raw_size)
        ranges.append((rva, raw_size, raw))

    def file_offset(rva, size):
        matches = [raw + rva - start for start, length, raw in ranges
                   if start <= rva and rva - start <= length and size <= length - (rva - start)]
        if len(matches) != 1:
            raise Invalid("resource RVA has no unique file-backed section")
        span(data, matches[0], size)
        return matches[0]

    rva, length = unpack("<II", data, opt + 112)
    if not rva or not length:
        return []
    base = file_offset(rva, length)
    directory = span(data, base, length)
    leaves, seen_dirs, seen_ids = [], set(), set()

    def visit(pos, path):
        if len(path) > 2 or pos in seen_dirs or len(seen_dirs) > MAX_NODES:
            raise Invalid("resource directory cycle, alias or depth limit")
        seen_dirs.add(pos)
        _, _, _, _, named, ids = unpack("<IIHHHH", directory, pos)
        if named + ids > MAX_NODES:
            raise Invalid("too many resources")
        span(directory, pos + 16, 8 * (named + ids))
        local_ids = set()
        for i in range(named + ids):
            ident, target = unpack("<II", directory, pos + 16 + 8 * i)
            if ident & 0x80000000:
                loc = ident & 0x7FFFFFFF
                count, = unpack("<H", directory, loc)
                try:
                    ident = span(directory, loc + 2, 2 * count).decode("utf-16le")
                except UnicodeDecodeError as e:
                    raise Invalid("invalid resource name") from e
            if ident in local_ids:
                raise Invalid("duplicate resource identity")
            local_ids.add(ident)
            parts = path + [ident]
            if target & 0x80000000:
                visit(target & 0x7FFFFFFF, parts)
            else:
                if len(parts) != 3:
                    raise Invalid("resource leaf is not type/name/language")
                leaf_rva, size, codepage, reserved = unpack("<IIII", directory, target)
                offset = file_offset(leaf_rva, size)
                identity = tuple(parts)
                if identity in seen_ids or len(leaves) >= MAX_NODES:
                    raise Invalid("duplicate/too many resource leaves")
                seen_ids.add(identity)
                leaves.append({"type": parts[0], "name": parts[1], "language": parts[2],
                               "type_label": RESOURCE_TYPES.get(parts[0], "other"),
                               "offset": offset, "bytes": size, "codepage": codepage})
    visit(0, [])
    return leaves


class DFMReader:
    """Bounded version of the existing feature_inventory TPF0 grammar."""
    def __init__(self, data):
        self.data, self.pos, self.nodes = data, 4, 0
        if not data.startswith(b"TPF0"):
            raise Invalid("missing TPF0 signature")

    def take(self, n):
        b = span(self.data, self.pos, n)
        self.pos += n
        return b

    def num(self, fmt):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def peek(self):
        return span(self.data, self.pos, 1)[0]

    def string(self):
        return self.take(self.num("<B")).decode("latin-1")

    def value(self, depth=0):
        self.nodes += 1
        if depth > 64 or self.nodes > MAX_NODES:
            raise Invalid("DFM nesting/node limit")
        kind = self.num("<B")
        if kind == 0:
            return None
        if kind == 1:
            values = []
            while self.peek():
                values.append(self.value(depth + 1))
            self.take(1)
            return values
        if kind in {2, 3, 4, 16}:
            return self.num({2: "<b", 3: "<h", 4: "<i", 16: "<q"}[kind])
        if kind == 5:
            self.take(10)
            return {"type": "extended"}
        if kind in {6, 7}:
            return self.string()
        if kind in {8, 9}:
            return kind == 9
        if kind == 10:
            return self.take(self.num("<I"))
        if kind == 11:
            values = []
            while True:
                v = self.string()
                if not v:
                    return values
                values.append(v)
                if len(values) > MAX_NODES:
                    raise Invalid("DFM set limit")
        if kind in {12, 13, 14}:
            self.take(4 if kind == 12 else 8)
            return {"type": "scalar", "kind": kind}
        if kind in {15, 17}:
            size = self.num("<I")
            try:
                return self.take(size * (2 if kind == 15 else 1)).decode(
                    "utf-16le" if kind == 15 else "utf-8")
            except UnicodeDecodeError as e:
                raise Invalid("invalid DFM text") from e
        raise Unsupported("DFM value type %d" % kind)

    def object(self, depth=0):
        self.nodes += 1
        if depth > 64 or self.nodes > MAX_NODES:
            raise Invalid("DFM object limit")
        if self.peek() & 0xF0 == 0xF0:
            # No inherited/inline/prefixed object layout is qualified yet.
            raise Unsupported("prefixed/inherited DFM object")
        obj = {"class": self.string(), "name": self.string(), "props": {}, "children": []}
        if not obj["class"] or not obj["name"]:
            raise Invalid("empty DFM identity")
        while self.peek():
            name = self.string()
            if name in obj["props"]:
                raise Invalid("duplicate DFM property")
            obj["props"][name] = self.value(depth)
        self.take(1)
        child_names = set()
        while self.peek():
            child = self.object(depth + 1)
            if child["name"] in child_names:
                raise Invalid("duplicate DFM child")
            child_names.add(child["name"])
            obj["children"].append(child)
        self.take(1)
        return obj

    def parse(self):
        obj = self.object()
        if self.pos != len(self.data):
            raise Invalid("unconsumed DFM resource bytes")
        return obj


@dataclass
class Bitmap:
    width: int
    height: int
    bpp: int
    palette: tuple
    indices: bytes             # Logical top-left rows, one byte per pixel.
    top_down: bool

    @classmethod
    def read(cls, data, dib=False):
        if not dib:
            if span(data, 0, 2) != b"BM":
                raise Invalid("missing BMP signature")
            size, = unpack("<I", data, 2)
            if size != len(data):
                raise Invalid("BMP declared length does not match blob")
            pixel_offset, = unpack("<I", data, 10)
        start = 0 if dib else 14
        hsize, width, height, planes, bpp, compression, image_size, _, _, used, _ = unpack(
            "<IiiHHIIiiII", data, start)
        if hsize != 40:
            raise Unsupported("only BITMAPINFOHEADER is supported")
        if compression != 0 or bpp not in {1, 4, 8}:
            raise Unsupported("only uncompressed 1/4/8-bpp indexed BMP is supported")
        if planes != 1 or width <= 0 or height == 0 or width * abs(height) > MAX_PIXELS:
            raise Invalid("invalid BMP geometry")
        ncolors = used or (1 << bpp)
        if not 1 <= ncolors <= (1 << bpp):
            raise Invalid("invalid BMP palette size")
        pal = span(data, start + 40, 4 * ncolors)
        palette = tuple((pal[i + 2], pal[i + 1], pal[i]) for i in range(0, len(pal), 4))
        minimum = start + 40 + len(pal)
        if dib:
            pixel_offset = minimum
        if pixel_offset < minimum:
            raise Invalid("pixel offset overlaps BMP palette/header")
        stride = ((width * bpp + 31) // 32) * 4
        required = stride * abs(height)
        if image_size not in {0, required}:
            raise Invalid("BMP pixel size mismatch")
        pixels = span(data, pixel_offset, required)
        result = bytearray()
        for y in range(abs(height)):
            physical = y if height < 0 else abs(height) - 1 - y
            row = pixels[physical * stride:(physical + 1) * stride]
            for x in range(width):
                shift = 8 - bpp - (x * bpp % 8)
                index = (row[x * bpp // 8] >> shift) & ((1 << bpp) - 1)
                if index >= len(palette):
                    raise Invalid("pixel references missing palette entry")
                result.append(index)
        return cls(width, abs(height), bpp, palette, bytes(result), height < 0)

    def crop(self, x, y, w, h):
        if min(x, y) < 0 or min(w, h) <= 0 or x + w > self.width or y + h > self.height:
            raise Invalid("sprite outside sheet")
        return bytes(v for row in range(y, y + h)
                     for v in self.indices[row * self.width + x:row * self.width + x + w])

    def describe(self):
        return {"width": self.width, "height": self.height, "bpp": self.bpp,
                "palette_entries": len(self.palette),
                "orientation": "top-down" if self.top_down else "bottom-up"}


def image_list(blob, width=32, height=32):
    size, count = unpack("<II", blob)
    color = Bitmap.read(span(blob, 8, size))
    mask = Bitmap.read(span(blob, 8 + size, len(blob) - 8 - size))
    if color.bpp != 8 or mask.bpp != 1:
        raise Unsupported("image-list colour/mask must be 8/1-bpp")
    if (color.width, color.height) != (mask.width, mask.height):
        raise Invalid("mask and colour dimensions differ")
    if (not isinstance(width, int) or not isinstance(height, int) or min(width, height) <= 0
            or color.width % width or color.height % height):
        raise Invalid("invalid image-list cell dimensions")
    if not 0 < count <= (color.width // width) * (color.height // height):
        raise Invalid("image-list count exceeds sheet capacity")
    if mask.palette != ((0, 0, 0), (255, 255, 255)):
        raise Unsupported("mask palette is not black/white in qualified order")
    return color, mask, count


def tcolor_rgb(value):
    if not 0 <= value <= 0xFFFFFF:
        raise Invalid("system/negative TColor is not an RGB colour")
    return (value & 255, value >> 8 & 255, value >> 16 & 255)


def recolour(rgb, colours):
    """Classify source pixels once; replacements may themselves be marker colours."""
    if len(colours) != 3 or any(len(c) != 3 or any(not 0 <= v <= 255 for v in c) for c in colours):
        raise Invalid("three RGB colour triples required")
    if len(rgb) % 3:
        raise Invalid("incomplete RGB pixel")
    mapping = dict(zip(((128, 0, 128), (255, 255, 255), (0, 0, 255)), colours))
    return bytes(v for i in range(0, len(rgb), 3)
                 for v in mapping.get(tuple(rgb[i:i + 3]), tuple(rgb[i:i + 3])))


def srcerase(source, destination):
    if len(source) != len(destination):
        raise Invalid("raster buffers differ")
    return bytes(s & (~d & 255) for s, d in zip(source, destination))


def masked_xor(source, mask, destination):
    """Explicit Win32 AND/XOR truth table; never assume every mask is alpha."""
    if len(source) != len(destination) or len(source) != 3 * len(mask) or any(v not in (0, 1) for v in mask):
        raise Invalid("invalid mask/compositing buffers")
    return bytes((d & (255 if mask[i // 3] else 0)) ^ s
                 for i, (s, d) in enumerate(zip(source, destination)))


def png(width, height, pixels, channels=3):
    if channels not in (3, 4) or len(pixels) != width * height * channels:
        raise Invalid("PNG buffer geometry")
    def chunk(name, value):
        return struct.pack(">I", len(value)) + name + value + struct.pack(">I", zlib.crc32(name + value))
    rows = b"".join(b"\0" + pixels[y * width * channels:(y + 1) * width * channels] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2 if channels == 3 else 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def rgb_pixels(bitmap, indices):
    return bytes(c for i in indices for c in bitmap.palette[i])


def semantic(form, name, index):
    info = {"semantic_id": None, "candidate_key": None, "mapping_status": "unresolved"}
    if form == "TUnitMap" and name == "TerrainList":
        keys = ("sea_calm", "sea_rough", "plain", "desert", "forest", "mountain")
        if index < 6:
            info.update(semantic_id=keys[index], candidate_key="terrain." + keys[index] + ".tile", mapping_status="mapped")
        elif index < 12:
            info.update(semantic_id="river_" + ("EW", "NS", "NE", "ES", "SW", "NW")[index - 6],
                        candidate_key="terrain.river.tile", mapping_status="consumer-needs-shape",
                        river_shape=("EW", "NS", "NE", "ES", "SW", "NW")[index - 6])
        elif index == 12:
            info.update(semantic_id="strategic_selection", raster_operation="SRCERASE", mapping_status="runtime-composition")
    elif form == "TUnitMap" and name in ("ArmiesList", "FleetsList") and index < 3:
        family = "army" if name == "ArmiesList" else "fleet"
        info.update(semantic_id=family + "_tier" + str(index + 1),
                    candidate_key=f"{family}.tier{index + 1}.icon", mapping_status="mapped",
                    recolour="nation-record-0x424-0x428-0x42c")
    elif form == "TUnitMap" and name in (*("Cities%dList" % i for i in range(1, 5)), "CapitalsList") and index < 16:
        key = "city.capital.icon" if name == "CapitalsList" else "city.tier" + name[6] + ".icon"
        info.update(semantic_id=name + "." + NATIONS[index], candidate_key=key,
                    owner=index, owner_name=NATIONS[index], mapping_status="consumer-needs-owner",
                    recolour="none-stored-owner-art")
    elif form == "TBattleMap" and name == "BatMapList":
        if index < 15:
            info.update(semantic_id=f"{UNIT_TYPES[index // 3]}.{SIZES[index % 3]}",
                        candidate_key=f"battle.unit.{UNIT_TYPES[index // 3]}.{SIZES[index % 3]}",
                        mapping_status="mapped", recolour="nation-record-0x424-0x428-0x42c")
        elif index in (15, 16):
            info.update(semantic_id="ground" if index == 15 else "battle_selection",
                        candidate_key="battle.ground" if index == 15 else "battle.cursor",
                        mapping_status="mapped" if index == 15 else "runtime-composition")
            if index == 16:
                info["raster_operation"] = "SRCERASE"
    return info


MAIN_COMMANDS = {"sb_Open": "open", "sb_Save": "save", "sb_Endturn": "end_turn",
                 "sb_News": "news", "sb_Pols": "relations", "sb_Tax": "taxation",
                 "sb_Balance": "balance_sheet", "sb_Newunit": "recruit_unit", "sb_Newfleet": "build_fleet"}
BATTLE_COMMANDS = {"sb_unitmoves": "unit_moves", "sb_friendlyunits": "friendly_units",
                   "sb_enemyunits": "enemy_units", "sb_cancel": "cancel_selection",
                   "sb_endturn": "end_turn", "sb_pauses": "change_pauses",
                   "sb_compgen": "computer_general", "sb_surrender": "surrender"}
AREA_COMMANDS = {"sb_areacits": "show_cities", "sb_areacap": "show_capital",
                 "sb_areaarms": "show_armies", "sb_areaflts": "show_fleets", "sb_areaalln": "show_all",
                 "sb_areali": "show_mercs_light_infantry", "sb_areahi": "show_mercs_heavy_infantry",
                 "sb_areaarch": "show_mercs_archers", "sb_arealc": "show_mercs_light_cavalry",
                 "sb_areahc": "show_mercs_heavy_cavalry", "sb_areaallm": "show_mercs_all", "sb_findcity": "find_city"}
UNIT_COMMANDS = {"sb_supplyarmy": "army_supply", "sb_recruitmercs": "army_recruit_mercenaries",
                 "sb_transferunit": "army_transfer_unit", "sb_splitarmy": "army_split", "sb_joinarmies": "army_join",
                 "sb_changeunit": "army_change_units", "sb_disbandarmy": "army_disband",
                 "sb_supplyfleet": "fleet_supply", "sb_repairfleet": "fleet_repair", "sb_transferships": "fleet_transfer_ships",
                 "sb_splitfleet": "fleet_split", "sb_joinfleets": "fleet_join", "sb_scuttle": "fleet_scuttle",
                 "sb_fortifycity": "city_fortify", "sb_cancel": "cancel_selection"}


def glyph_semantic(form, name):
    commands = {"TPremierForm": MAIN_COMMANDS, "TAreaMap": AREA_COMMANDS, "TUnitMap": UNIT_COMMANDS}.get(form, {})
    if name in commands:
        return {"candidate_key": "ui.command." + commands[name] + ".icon", "mapping_status": "candidate-component-correspondence"}
    if form == "TBattleMap" and name in BATTLE_COMMANDS:
        return {"candidate_key": "battle.toolbar." + BATTLE_COMMANDS[name], "mapping_status": "mapped"}
    if form == "TPremierForm" and name.removeprefix("sb_") in NATIONS:
        return {"owner": NATIONS.index(name[3:]), "candidate_key": None,
                "mapping_status": "consumer-needs-nation-button", "recolour": "none-stored-owner-art"}
    return {"candidate_key": None, "mapping_status": "unresolved"}


def wav_info(data):
    if span(data, 0, 4) != b"RIFF" or span(data, 8, 4) != b"WAVE":
        raise Invalid("not RIFF/WAVE")
    length, = unpack("<I", data, 4)
    if length + 8 != len(data):
        raise Invalid("RIFF length mismatch")
    pos, chunks = 12, {}
    while pos < len(data):
        tag, size = unpack("<4sI", data, pos)
        payload = span(data, pos + 8, size)
        if tag in (b"fmt ", b"data"):
            if tag in chunks:
                raise Invalid("ambiguous duplicate WAV chunk")
            chunks[tag] = payload
        pos += 8 + size
        if size & 1:
            span(data, pos, 1)
            pos += 1
    if b"fmt " not in chunks or b"data" not in chunks:
        raise Invalid("WAV needs fmt and data chunks")
    fmt = chunks[b"fmt "]
    if len(fmt) not in (16, 18) or (len(fmt) == 18 and unpack("<H", fmt, 16)[0] != 0):
        raise Unsupported("extended PCM fmt layout is not qualified")
    encoding, channels, rate, byte_rate, align, bits = unpack("<HHIIHH", fmt)
    if encoding != 1 or channels not in (1, 2) or bits not in (8, 16):
        raise Unsupported("only 8/16-bit mono/stereo integer PCM is supported")
    if not 1 <= rate <= 192000 or align != channels * bits // 8 or byte_rate != rate * align:
        raise Invalid("invalid PCM rate/alignment")
    samples = chunks[b"data"]
    if not samples or len(samples) % align:
        raise Invalid("partial/empty PCM frame")
    # Actually decode all supplied PCM values, without returning or publishing samples.
    if bits == 16:
        for _ in struct.iter_unpack("<h", samples):
            pass
    else:
        for value in samples:
            _ = (value - 128) / 128
    frames = len(samples) // align
    return {"encoding": "PCM", "channels": channels, "sample_rate": rate,
            "bits_per_sample": bits, "frames": frames, "duration_seconds": frames / rate,
            "source_bytes": len(data), "decode_validated": True}


def wav_inventory(root, media=None):
    """Root is explicit: no EXE-directory or game-working-directory assumption."""
    files, identities = [], []
    children = list(Path(root).iterdir()) if root is not None and Path(root).is_dir() else []
    for n, key in enumerate(SOUNDS, 1):
        name = "SOUND%d.WAV" % n
        matches = [p for p in children if p.name.casefold() == name.casefold()]
        row = {"sound": n, "logical_name": name, "candidate_key": "sfx." + key,
               "status": "missing", "format_provenance": "supplied-file-not-assumed-original"}
        if root is not None and not Path(root).is_dir():
            row["reason"] = "explicit-wav-root-missing-or-not-directory"
        if len(matches) > 1:
            row.update(status="unsupported", reason="ambiguous-case-duplicate")
        elif matches:
            p = matches[0]
            row["basename"] = p.name
            try:
                if p.is_symlink() or not p.is_file():
                    raise Unsupported("WAV candidate is not a regular non-symlink file")
                data = read_file(p)
                identities.append((n, sha(data)))
                row.update(wav_info(data), status="available", file=f"sound-{n:02d}.wav",
                           conversion="none-supplied-PCM-preserved")
                if media is not None:
                    media[row["file"]] = data
            except OSError as e:
                # Filesystem exception text includes private absolute filenames.
                # Receipts may be public; retain only stable non-path diagnostics.
                row.update(status="invalid", reason="wav-file-io-error",
                           io_error_class=type(e).__name__, io_errno=e.errno)
            except (Invalid, Unsupported) as e:
                row.update(status="unsupported" if isinstance(e, Unsupported) else "invalid", reason=str(e))
        files.append(row)
    return files, identities


def native_group(resource, leaves, data):
    """Rebuild a native ICO/CUR; preserve XOR/AND planes instead of guessing alpha."""
    blob = span(data, resource['offset'], resource['bytes'])
    reserved, kind, count = unpack("<HHH", blob)
    cursor = resource["type"] == 12
    if reserved or kind != (2 if cursor else 1) or not 0 < count <= 256 or len(blob) != 6 + 14 * count:
        raise Invalid("invalid icon/cursor group header")
    entries, payloads, descriptions = [], [], []
    offset = 6 + 16 * count
    for i in range(count):
        row = span(blob, 6 + i * 14, 14)
        size, ident = unpack("<IH", row, 8)
        refs = [r for r in leaves if r["type"] == (1 if cursor else 3) and r["name"] == ident
                and r["language"] == resource["language"]]
        if len(refs) != 1:
            raise Unsupported("group image has no unique same-language resource")
        image = span(data, refs[0]["offset"], refs[0]["bytes"])
        if len(image) != size:
            raise Invalid("group and leaf size disagree")
        hotspot = unpack("<HH", image) if cursor else None
        dib = image[4:] if cursor else image
        hsize, width, doubled_height, planes, bpp = unpack("<IiiHH", dib)
        if hsize != 40 or width <= 0 or not 0 < doubled_height <= 512 or doubled_height % 2 or width > 256:
            raise Unsupported("unqualified native icon/cursor image")
        height = doubled_height // 2
        if cursor:
            group_width, group_height, group_planes, group_bpp = unpack("<HHHH", row)
            if group_width != width or group_height not in (height, doubled_height) or (group_planes, group_bpp) != (planes, bpp):
                raise Invalid("cursor group/leaf geometry mismatch")
        else:
            group_width, group_height, _, _, group_planes, group_bpp = unpack("<BBBBHH", row)
            if (group_width or 256, group_height or 256) != (width, height) or (group_planes, group_bpp) != (planes, bpp):
                raise Invalid("icon group/leaf geometry mismatch")
        if planes != 1 or bpp not in (1, 4, 8) or unpack("<I", dib, 16)[0] != 0:
            raise Unsupported("only uncompressed indexed native icon/cursor images are supported")
        used = unpack("<I", dib, 32)[0] or (1 << bpp)
        if not 1 <= used <= 1 << bpp:
            raise Invalid("invalid native icon/cursor palette")
        pixel_offset = 40 + 4 * used
        color_bytes = ((width * bpp + 31) // 32) * 4 * height
        mask_bytes = ((width + 31) // 32) * 4 * height
        if len(dib) != pixel_offset + color_bytes + mask_bytes:
            raise Invalid("native icon/cursor planes truncated or trailing bytes")
        # Check every source palette reference by decoding the colour plane as a
        # normal DIB with logical height; the AND plane stays independently encoded.
        color_dib = bytearray(dib[:pixel_offset + color_bytes])
        struct.pack_into("<i", color_dib, 8, height)
        struct.pack_into("<I", color_dib, 20, color_bytes)
        Bitmap.read(bytes(color_dib), dib=True)
        if hotspot and (hotspot[0] >= width or hotspot[1] >= height):
            raise Invalid("cursor hotspot outside image")
        count_colors = 0 if bpp >= 8 else 1 << bpp
        a, b = hotspot if cursor else (planes, bpp)
        entries.append(struct.pack("<BBBBHHII", width % 256, height % 256, count_colors, 0, a, b, len(dib), offset))
        payloads.append(dib)
        descriptions.append({"image_id": ident, "width": width, "height": height, "bpp": bpp,
                             "hotspot": list(hotspot) if hotspot else None,
                             "compositing": "native-XOR-AND-planes-not-alpha"})
        offset += len(dib)
    return struct.pack("<HHH", 0, kind, count) + b"".join(entries + payloads), descriptions


def inventory(data, wav_root=None, export=False):
    digest = sha(data)
    profile = PROFILES.get(digest)
    tool_hash = sha(Path(__file__).read_bytes())
    report = {"schema": SCHEMA, "extractor_version": VERSION, "extractor_sha256": tool_hash,
              "source": {"exe_sha256": digest, "profile": profile, "status": "available" if profile else "unsupported"},
              "resources": [], "forms": [], "assets": [], "diagnostics": [], "categories": {}}
    media = {}
    try:
        leaves = pe_resources(data)
    except (Invalid, Unsupported) as e:
        report["source"].update(status="invalid" if isinstance(e, Invalid) else "unsupported", reason=str(e))
        leaves = []
    report["resources"] = leaves
    if not profile:
        report["diagnostics"].append({"status": "unsupported", "reason": "unqualified-executable-profile; no media decoded"})
    else:
        def emit(name, payload):
            if export:
                media[name] = payload

        def frame(color, indices, w, h, filename, key=None):
            rgb = rgb_pixels(color, indices)
            if key is None:
                emit(filename, png(w, h, rgb))
            else:
                rgba = bytes(c for i in range(0, len(rgb), 3)
                             for c in (*rgb[i:i + 3], 0 if tuple(rgb[i:i + 3]) == key else 255))
                emit(filename, png(w, h, rgba, 4))

        def binary_asset(resource_index, component, form, prop, payload, props):
            number = len(report["assets"])
            row = {"resource_index": resource_index, "component": component,
                   "form": form, "class": props["class"], "property": prop,
                   "bytes": len(payload), "status": "unsupported", "images": []}
            report["assets"].append(row)
            stem = "asset-%04d" % number
            try:
                if props["class"] == "TImageList" and prop == "Bitmap":
                    w, h = props["props"].get("Width", 32), props["props"].get("Height", 32)
                    color, mask, count = image_list(payload, w, h)
                    row.update(kind="image-list", status="available", color=color.describe(), mask=mask.describe(), count=count,
                               compositing="mask-and-xor; inspect raster_operation before consumer conversion")
                    for i in range(count):
                        x, y = (i % (color.width // w)) * w, (i // (color.width // w)) * h
                        filename, maskname = f"{stem}-{i:03d}.png", f"{stem}-{i:03d}-mask.png"
                        indices, bits = color.crop(x, y, w, h), mask.crop(x, y, w, h)
                        frame(color, indices, w, h, filename)
                        frame(mask, bits, w, h, maskname)
                        row["images"].append({"index": i, "width": w, "height": h,
                                              "file": filename, "mask_file": maskname,
                                              **semantic(form, props["name"], i)})
                elif props["class"] == "TSpeedButton" and prop == "Glyph.Data":
                    size, = unpack("<I", payload)
                    if size != len(payload) - 4:
                        raise Invalid("glyph length mismatch")
                    color = Bitmap.read(payload[4:])
                    count = props["props"].get("NumGlyphs", 1)
                    if not isinstance(count, int) or not 1 <= count <= 4 or color.width % count:
                        raise Invalid("invalid glyph frame count")
                    w, h = color.width // count, color.height
                    key = color.palette[color.indices[(h - 1) * color.width]]
                    row.update(kind="button-glyph", status="available", color=color.describe(), count=count,
                               transparent_rgb=list(key), compositing="TSpeedButton-bottom-left-key; stored-frames-only",
                               **glyph_semantic(form, props["name"]))
                    for i in range(count):
                        filename = f"{stem}-{i:03d}.png"
                        frame(color, color.crop(i * w, 0, w, h), w, h, filename, key)
                        row["images"].append({"index": i, "width": w, "height": h, "file": filename})
                else:
                    row["reason"] = "binary property not qualified for image conversion"
            except (Invalid, Unsupported) as e:
                row.update(status="invalid" if isinstance(e, Invalid) else "unsupported", reason=str(e))

        for i, res in enumerate(leaves):
            blob = span(data, res["offset"], res["bytes"])
            try:
                if res["type"] == 10 and blob.startswith(b"TPF0"):
                    obj = DFMReader(blob).parse()
                    report["forms"].append({"resource_index": i, "class": obj["class"], "name": obj["name"]})
                    def walk(node, path):
                        for key, value in node["props"].items():
                            if isinstance(value, bytes):
                                binary_asset(i, path, obj["class"], key, value, node)
                        for child in node["children"]:
                            walk(child, path + "/" + child["name"])
                    walk(obj, obj["name"])
                elif res["type"] == 2:
                    bmp = Bitmap.read(blob, dib=True)
                    filename = f"resource-{i:03d}.png"
                    frame(bmp, bmp.indices, bmp.width, bmp.height, filename)
                    report["assets"].append({"resource_index": i, "kind": "resource-bitmap", "status": "available",
                                             "color": bmp.describe(), "file": filename, "mapping_status": "unresolved"})
                elif res["type"] in (12, 14):
                    payload, descriptions = native_group(res, leaves, data)
                    filename = f"resource-{i:03d}." + ("cur" if res["type"] == 12 else "ico")
                    emit(filename, payload)
                    report["assets"].append({"resource_index": i, "kind": res["type_label"], "status": "partial",
                                             "file": filename, "images": descriptions,
                                             "reason": "native container recovered; consumer raster composition unverified"})
            except (Invalid, Unsupported) as e:
                report["diagnostics"].append({"resource_index": i, "status": "invalid" if isinstance(e, Invalid) else "unsupported", "reason": str(e)})

    sounds, wav_ids = wav_inventory(wav_root, media if export and profile else None)
    report["sounds"] = sounds
    counts = {kind: sum(a.get("kind") == kind and a["status"] == "available" for a in report["assets"])
              for kind in ("image-list", "button-glyph", "resource-bitmap")}
    report["summary"] = {"resource_leaves": len(leaves), "forms": len(report["forms"]), **counts,
                         "list_images": sum(a.get("count", 0) for a in report["assets"] if a.get("kind") == "image-list"),
                         "glyph_frames": sum(a.get("count", 0) for a in report["assets"] if a.get("kind") == "button-glyph"),
                         "valid_sounds": sum(s["status"] == "available" for s in sounds)}
    report["categories"] = {
        "embedded_media": "partial" if profile else "unsupported",
        "backgrounds": "no-separate-background-property-observed" if profile and len(report["forms"]) == 29 else "unresolved",
        "area_map_semantics": "partial", "native_cursor_compositing": "partial",
        "owner_city_mapping": "consumer-needs-owner", "river_mapping": "consumer-needs-six-shapes",
        "terrain_surfaces": "no-original-equivalent-established", "new_scenarios": "no-original-art-established",
        "audio": "available" if all(s["status"] == "available" for s in sounds) else "partial-or-missing"}
    identity = {"version": VERSION, "extractor_sha256": tool_hash, "schema": SCHEMA, "exe": digest, "profile": profile,
                "wav_content": wav_ids, "wav_states": sounds, "export": export,
                "conversion": "indexed-PNG-plus-separate-mask; native-icon-cursor; no-recolour"}
    report["cache_identity"] = sha(json.dumps(identity, sort_keys=True).encode())
    report["media_exported"] = export and bool(media)
    report["limits"] = ["no-game-or-native-rendering-acceptance", "no-original-UI-layout-claim",
                        "no-mask-to-alpha-assumption", "no-backend-session-or-remake-adapter",
                        "one-qualified-EXE-profile", "no-original-audio-provenance-assumed"]
    report["validation_status"] = "failed" if (
        report["source"]["status"] != "available" or report["diagnostics"]
        or any(r["status"] in ("invalid", "unsupported") for r in report["assets"] + sounds)
    ) else "passed-static"
    return report, media


def publish_new(path, data):
    """Atomic complete-file publication; link fails if destination already exists."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".asset218-", delete=False) as f:
            temp = Path(f.name)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.link(temp, path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path, help="new JSON receipt path; existing files are never overwritten")
    parser.add_argument("--wav-root", type=Path, help="explicit WAVS directory; omitted means sounds missing")
    parser.add_argument("--media-dir", type=Path, help="optional NEW private directory outside every Git checkout")
    args = parser.parse_args(argv)
    try:
        if args.metadata.exists() or args.metadata.is_symlink():
            raise FileExistsError("metadata destination already exists")
        if args.media_dir is not None:
            target = args.media_dir.resolve()
            if args.media_dir.exists() or args.media_dir.is_symlink():
                raise FileExistsError("media destination must be new")
            if any((p / ".git").exists() for p in (target, *target.parents)):
                raise Invalid("private media must be outside Git checkouts")
            if args.metadata.resolve().is_relative_to(target):
                raise Invalid("metadata receipt must be outside media directory")
        data = read_file(args.exe)
        report, media = inventory(data, args.wav_root, args.media_dir is not None)
        if args.media_dir is not None and media:
            args.media_dir.mkdir(parents=True, exist_ok=False)
            for name, payload in media.items():
                publish_new(args.media_dir / name, payload)
            # Manifest last: a partial export never masquerades as a completed cache.
            private = {**report, "files": {name: sha(payload) for name, payload in media.items()}}
            publish_new(args.media_dir / "manifest.json", (json.dumps(private, indent=2) + "\n").encode())
        publish_new(args.metadata, (json.dumps(report, indent=2) + "\n").encode())
        print(json.dumps({"metadata": str(args.metadata), "source_status": report["source"]["status"], **report["summary"]}))
        return 2 if report["validation_status"] == "failed" else 0
    except (Invalid, Unsupported, OSError) as e:
        print("extract_original_assets: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
