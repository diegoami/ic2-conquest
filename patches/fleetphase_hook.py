#!/usr/bin/env python3
"""The fleet-phase hook (#174, owner 2026-10-31): an observation-only build of the seed exe that logs, for every own
launched fleet the AI fleet phase FUN_0044f608 handles, every input of its branch.

    python3 patches/fleetphase_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed fleetphasehook.exe"

FUN_0044f608 (pinned seed build), per fleet EBP (record ESI = 0x49c26c + 26*EBP) with owner = current nation and
countdown -1: supply pass FUN_0044e5dc; port pick FUN_0044e9a8 -> [esp+4]; then
  route_x >= 0                       -> FUN_0044e1fc(fleet, stored route)          (0x44F667)
  else moves > 0: FUN_0044f4f8 -> target [esp+2], score [esp]
       score > 100                   -> FUN_0044e1fc(fleet, target fleet position)  (0x44F69A)
       else port >= 0                -> FUN_0044e1fc(fleet, port city position)     (0x44F6BE)

Probes (`jmp stub` over one 5-byte instruction the stub runs itself, pushfd/pushad around the log):
  1  0x44F65B  `cmp word [esi+4],-1`: fleet (EBP), port [esp+4], route dword [esi+4], position dword [esi], moves|supplies
               dword [esi+0xC].
  2  0x44F682  `cmp word [esp],0x64`: fleet, score [esp], target [esp+2].
A 40-byte record: +0 kind, +4..+0x14 five values, +0x18 nation, +0x1C week, +0x20 reserved, +0x24 sequence. Log: CTL
0x565000 (+0 count, +4 'FLT1', +8 capacity), BUF 0x565100 (patches/walk_hook.py layout).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

MAGIC = 0x31544C46                      # 'FLT1'
DST = "Imperial Conquest 2 fast rollingsave seed fleetphasehook.exe"
P1, P2 = 0x44F65B, 0x44F682
EXPECT = {P1: bytes.fromhex("66837e04ff"), P2: bytes.fromhex("66833c2464")}
WEEK = 0x4A0330
u32 = W.u32
FB = 36


def body(kind):
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)
    b += b"\x81\xF9" + u32(W.CAP)
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([W.REC])
    b += b"\x81\xC1" + u32(W.BUF)
    b += b"\xC7\x01" + u32(kind)
    b += b"\x8B\x44\x24\x08\x89\x41\x04"                                 # fleet (saved EBP)
    if kind == 1:
        b += b"\x0F\xBF\x44\x24" + bytes([FB + 4]) + b"\x89\x41\x08"     # port [F+4]
        b += b"\x8B\x54\x24\x04"                                         # mov edx, [esp+4] (saved ESI): the record
        b += b"\x8B\x42\x04\x89\x41\x0C"                                 # route dword
        b += b"\x8B\x02\x89\x41\x10"                                     # position dword
        b += b"\x8B\x42\x0C\x89\x41\x14"                                 # moves|supplies
    else:
        b += b"\x0F\xBF\x44\x24" + bytes([FB]) + b"\x89\x41\x08"         # score [F+0]
        b += b"\x0F\xBF\x44\x24" + bytes([FB + 2]) + b"\x89\x41\x0C"     # target [F+2]
    b += b"\x0F\xBF\x05" + u32(W.NATION) + b"\x89\x41\x18"
    b += b"\x0F\xBF\x05" + u32(WEEK) + b"\x89\x41\x1C"
    b += b"\xA1" + u32(W.CTL) + b"\x89\x41\x24"
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    for site, want in EXPECT.items():
        if bytes(b[W.off(site):W.off(site) + 5]) != want:
            raise SystemExit("0x%X holds %s" % (site, bytes(b[W.off(site):W.off(site) + 5]).hex()))
    hdr = 0x1F8 + 8 * 40
    if bytes(b[hdr:hdr + 6]) != b".patch":
        raise SystemExit(".patch is not the 9th section")
    vsize = W.BUF + W.CAP * W.REC - W.PATCH_VA
    struct.pack_into("<I", b, hdr + 8, vsize)
    struct.pack_into("<I", b, hdr + 16, W.RAW_SIZE)
    struct.pack_into("<I", b, hdr + 36, struct.unpack_from("<I", b, hdr + 36)[0] | 0x80000000)
    struct.pack_into("<I", b, 0x118 + 56, (W.PATCH_VA - W.BASE + vsize + 0xFFF) & ~0xFFF)
    b += b"\xCC" * (W.CTL - W.PATCH_VA - W.SEED_PATCH_SIZE) + bytes(W.RAW_SIZE - (W.CTL - W.PATCH_VA))
    raw = lambda va: W.PATCH_RAW + (va - W.PATCH_VA)
    b[raw(W.CTL + 4):raw(W.CTL + 8)] = u32(MAGIC)
    b[raw(W.CTL + 8):raw(W.CTL + 12)] = u32(W.CAP)
    va, out = W.CAVES, {}
    for site, kind in ((P1, 1), (P2, 2)):
        code = bytearray(b"\x9C\x60") + body(kind) + b"\x61\x9D" + EXPECT[site]
        code += b"\xE9" + W.rel32(va + len(code), site + 5)
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + 5] = b"\xE9" + W.rel32(site, va)
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("cave overflow")
    return out


def words(d):
    return struct.unpack("<hh", struct.pack("<I", d & 0xFFFFFFFF))


def decode(buf, n):
    out = []
    for i in range(n):
        kind, fleet, a, b_, c, d, nation, week, _, seq = struct.unpack_from("<10i", buf, i * W.REC)
        r = {"seq": seq, "nation": nation, "week": week, "fleet": fleet}
        if kind == 1:
            rx, ry = words(b_)
            x, y = words(c)
            moves, supplies = words(d)
            r.update(kind="fleet", port=struct.unpack("<h", struct.pack("<H", a & 0xFFFF))[0], route=[rx, ry], pos=[x, y],
                     moves=moves, supplies=supplies)
        else:
            r.update(kind="hunt", score=a, target=b_)
        out.append(r)
    return out


def branch(fleet, hunt):
    """F608's choice from the logged inputs."""
    if fleet["route"][0] >= 0:
        return "stored-route", fleet["route"]
    if fleet["moves"] <= 0:
        return "none", None
    if hunt and hunt["score"] > 100:
        return "hunt", hunt["target"]
    if fleet["port"] >= 0:
        return "port", fleet["port"]
    return "none", None


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
