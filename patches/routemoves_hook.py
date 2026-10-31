#!/usr/bin/env python3
"""The route-moves hook (research #159, owner 2026-10-31): does the original write a ferry route for an army with 0 moves?
An observation-only build of the seed exe that logs every AI march FUN_0044dba8 (with its caller and the army's moves) and
every ferry-route write of FUN_0044d9a8 (with the army's moves AT the write), plus the fleet phase's branch inputs.

    python3 patches/routemoves_hook.py <game folder>   # reads "... seed.exe", writes "... seed routemoveshook.exe"

Static trace (pinned seed build), F31C's continuation to the write:
  F31C 0x44F485 call E84C; 0x44F48A army score > 70 -> 0x44F4A3 call DBA8(army, army target)
                           else 0x44F4AA city score > 85 -> 0x44F4C7 call DBA8(army, city)      (no moves test)
  DBA8 0x44DBC5 si := moves (+6); 0x44DBC9 aboard test (+8); 0x44DC06 CB40(position, target), the direct-line test;
       not direct -> DB38; moves compared only after DB38 returns (0x44DC43)
  DB38 classifies both points (FUN_0044da88) and calls D9A8 when they differ (0x44DB8B); its locals are the two points, the
       class results and the out pointer: no moves
  D9A8 the nearest own fleet with owner, +0x16 == -1, +0xA == -1 and fleet moves +0xC > 0; at distance 1 the army embarks
       (FUN_0044b79c), otherwise CD08 writes the route (0x44DA6F)                                        (fleet gates only)
Probes (`jmp stub` over whole position-independent instructions the stub runs itself, pushfd/pushad around the log):
  1  0x44F65B  fleetphase_hook probe 1 (F608: fleet, port, route, position, moves).
  2  0x44F682  fleetphase_hook probe 2 (F608: hunt score and target).
  3  0x44DBA8  DBA8 entry, `push ebp; mov ebp,esp; add esp,-0x10` (6 bytes): army (AX), target (EDX), caller, the army's
               dwords +4 (owner | moves) and +8 (cell | supplies).
  4  0x44DA74  after D9A8's `call FUN_0044cd08`, `mov eax,[ebp-8]; mov eax,[eax]`: EBX (13*fleet), the route dword, the army
               index DBA8 keeps at its [ebp-2] (D9A8's [ebp+8] is DBA8's frame), that army's dword +4 (owner | moves), and
               DBA8's [ebp-6] (its target) before D9A8 replaces it.
A 40-byte record: +0 kind, +4..+0x14 five values, +0x18 nation, +0x1C week, +0x20 reserved, +0x24 sequence. Log: CTL 0x565000
(+0 count, +4 'RTM1', +8 capacity), BUF 0x565100 (patches/walk_hook.py layout).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import econ2_hook as E  # noqa: E402
import fleetphase_hook as FP  # noqa: E402
import walk_hook as W  # noqa: E402

MAGIC = 0x314D5452                      # 'RTM1'
DST = "Imperial Conquest 2 fast rollingsave seed routemoveshook.exe"
u32 = W.u32
# DBA8's return addresses (its 11 call sites, from a scan for E8 rel32 calls; DB38's only caller is 0x44DC26 in DBA8 and
# D9A8's only caller is 0x44DB8B in DB38, so D9A8's [ebp+8] is always DBA8's frame)
CALLERS = {0x44DCA6: "dba8-self", 0x44E918: "e84c-run", 0x44EC82: "ebe8-capital", 0x44ECDB: "ebe8-nearest",
           0x44F2EC: "efc8-a", 0x44F2FE: "efc8-b", 0x44F40E: "f31c-army>100", 0x44F444: "f31c-city>100",
           0x44F481: "f31c-resupply", 0x44F4A8: "f31c-e84c-army>70", 0x44F4CC: "f31c-e84c-city>85"}


def frame_army():              # eax := DBA8's army word at [[saved EBP]+8 - 2] (D9A8's [ebp+8] is DBA8's ebp)
    return b"\x8B\x54\x24" + bytes([E.R["ebp"]]) + b"\x8B\x52\x08" + b"\x0F\xBF\x42\xFE"


def frame_army_field(off):     # eax := dword at army[frame army] + off
    return frame_army() + b"\x69\xC0" + u32(E.ARMY_SIZE) + b"\x8B\x80" + u32(E.ARMY + off)


def frame_target():            # eax := DBA8's [ebp-6] dword
    return b"\x8B\x54\x24" + bytes([E.R["ebp"]]) + b"\x8B\x52\x08" + b"\x8B\x42\xFA"


def route_dword():             # eax := [saved EBX*2 + 0x49C270]
    return b"\x8B\x54\x24" + bytes([E.R["ebx"]]) + b"\x8B\x04\x55" + u32(0x49C270)


E_SITES = {
    0x44DBA8: (3, "558bec83c4f0", [E.reg16("eax"), E.reg("edx"), E.stack(0), E.army_field("eax", 4), E.army_field("eax", 8)]),
    0x44DA74: (4, "8b45f88b00", [E.reg("ebx"), route_dword(), frame_army(), frame_army_field(4), frame_target()]),
}


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    sites = {FP.P1: (1, FP.EXPECT[FP.P1].hex(), None), FP.P2: (2, FP.EXPECT[FP.P2].hex(), None)}
    sites.update(E_SITES)
    for site, (_, want, _) in sites.items():
        want = bytes.fromhex(want)
        if bytes(b[W.off(site):W.off(site) + len(want)]) != want:
            raise SystemExit("0x%X holds %s" % (site, bytes(b[W.off(site):W.off(site) + len(want)]).hex()))
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
    for site, (kind, want, values) in sites.items():
        want = bytes.fromhex(want)
        body = FP.body(kind) if values is None else E.body(kind, values)
        code = bytearray(b"\x9C\x60") + body + b"\x61\x9D" + want
        code += b"\xE9" + W.rel32(va + len(code), site + len(want))
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + len(want)] = b"\xE9" + W.rel32(site, va) + b"\x90" * (len(want) - 5)
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("cave overflow")
    return out


def decode(buf, n):
    out = []
    for i in range(n):
        kind = struct.unpack_from("<i", buf, i * W.REC)[0]
        if kind in (1, 2):
            out += FP.decode(buf[i * W.REC:(i + 1) * W.REC], 1)
            continue
        _, a, b_, c, d, e, nation, week, _, seq = struct.unpack_from("<10i", buf, i * W.REC)
        r = {"seq": seq, "nation": nation, "week": week}
        if kind == 3:
            owner, moves = E.words(d)
            cell, supplies = E.words(e)
            caller = c & 0xFFFFFFFF
            r.update(kind="dba8", army=a, target=E.words(b_), caller=CALLERS.get(caller, hex(caller)), moves=moves,
                     cell=cell, owner=owner)
        else:
            owner, moves = E.words(d)
            r.update(kind="route-write", fleet=(a & 0xFFFFFFFF) // 13, route=E.words(b_), army=c, army_moves=moves,
                     army_owner=owner, dba8_target=E.words(e))
        out.append(r)
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
