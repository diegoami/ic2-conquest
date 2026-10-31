#!/usr/bin/env python3
"""The fleet-route hook (#174 fleet-0 attribution, owner 2026-10-31): patches/fleetphase_hook.py's two fleet-phase probes plus
the two writers of a fleet's stored route that the army phase uses (findings/2026-10-30-fleet-route-lifetime131.md §1), in
one observation-only build of the seed exe.

    python3 patches/fleetroute_hook.py <game folder>   # reads "... seed.exe", writes "... seed fleetroutehook.exe"

Probes (`jmp stub` over 5 bytes of position-independent instructions the stub runs itself, pushfd/pushad around the log):
  1  0x44F65B  fleetphase_hook probe 1 (F608: fleet, port, route, position, moves).
  2  0x44F682  fleetphase_hook probe 2 (F608: hunt score and target).
  3  0x44DA74  `mov eax,[ebp-8]; mov eax,[eax]`, right after FUN_0044d9a8's `call FUN_0044cd08` (0x44DA6F), which wrote the
               route of fleet EBX/13 through `lea eax,[ebx*2+0x49c270]`: the ferry rendezvous. Logs EBX (13*fleet), the
               route dword, D9A8's [ebp-4] (CD08's EAX, the army's point) and [ebp+8] (its caller's frame pointer).
  4  0x44DBF7  `sub word [ebx+6],2`, right after FUN_0044dba8's aboard-branch `call FUN_0044cd08` (0x44DBF2), which wrote
               the route of fleet ESI/13 (the carrier): the landing cell. Logs ESI (13*fleet), the route dword, EBX (the army
               record 0x47C1EC + 0x290*army) and DBA8's target [ebp-6].
A 40-byte record: +0 kind, +4..+0x14 five values, +0x18 nation, +0x1C week, +0x20 reserved, +0x24 sequence. Log: CTL 0x565000
(+0 count, +4 'FRT1', +8 capacity), BUF 0x565100 (patches/walk_hook.py layout).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fleetphase_hook as FP  # noqa: E402
import walk_hook as W  # noqa: E402

MAGIC = 0x31545246                      # 'FRT1'
DST = "Imperial Conquest 2 fast rollingsave seed fleetroutehook.exe"
P3, P4 = 0x44DA74, 0x44DBF7
EXPECT = dict(FP.EXPECT)
EXPECT.update({P3: bytes.fromhex("8b45f88b00"), P4: bytes.fromhex("66836b0602")})
ARMY_BASE, ARMY_SIZE = 0x47C1EC, 0x290
u32 = W.u32
# pushad order: [esp+0] EDI, +4 ESI, +8 EBP, +0xC ESP, +0x10 EBX, +0x14 EDX, +0x18 ECX, +0x1C EAX, +0x20 EFLAGS
S_ESI, S_EBP, S_EBX = 4, 8, 0x10


def body(kind):
    if kind in (1, 2):
        return FP.body(kind)
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)
    b += b"\x81\xF9" + u32(W.CAP)
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([W.REC])
    b += b"\x81\xC1" + u32(W.BUF)
    b += b"\xC7\x01" + u32(kind)
    if kind == 3:
        b += b"\x8B\x54\x24" + bytes([S_EBX])                 # mov edx, saved EBX (13*fleet)
        b += b"\x89\x51\x04"                                  # +4
        b += b"\x8B\x04\x55" + u32(0x49C270) + b"\x89\x41\x08"  # route dword [edx*2+0x49c270] -> +8
        b += b"\x8B\x54\x24" + bytes([S_EBP])                 # mov edx, saved EBP
        b += b"\x8B\x42\xFC\x89\x41\x0C"                      # [ebp-4] -> +0xC
        b += b"\x8B\x42\x08\x89\x41\x10"                      # [ebp+8] -> +0x10
    else:
        b += b"\x8B\x54\x24" + bytes([S_ESI])                 # mov edx, saved ESI (13*fleet)
        b += b"\x89\x51\x04"
        b += b"\x8B\x04\x55" + u32(0x49C270) + b"\x89\x41\x08"  # route dword -> +8
        b += b"\x8B\x44\x24" + bytes([S_EBX]) + b"\x89\x41\x0C"  # army record pointer -> +0xC
        b += b"\x8B\x54\x24" + bytes([S_EBP])
        b += b"\x8B\x42\xFA\x89\x41\x10"                      # [ebp-6] target dword -> +0x10
    b += b"\x0F\xBF\x05" + u32(W.NATION) + b"\x89\x41\x18"
    b += b"\x0F\xBF\x05" + u32(FP.WEEK) + b"\x89\x41\x1C"
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
    for site, kind in ((FP.P1, 1), (FP.P2, 2), (P3, 3), (P4, 4)):
        code = bytearray(b"\x9C\x60") + body(kind) + b"\x61\x9D" + EXPECT[site]
        code += b"\xE9" + W.rel32(va + len(code), site + 5)
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + 5] = b"\xE9" + W.rel32(site, va)
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
        _, a, rt, c, d, _, nation, week, _, seq = struct.unpack_from("<10i", buf, i * W.REC)
        rx, ry = FP.words(rt)
        r = {"seq": seq, "nation": nation, "week": week, "fleet": a // 13, "route": [rx, ry]}
        if kind == 3:
            px, py = FP.words(c)
            r.update(kind="rendezvous", army_point=[px, py], caller_frame=d & 0xFFFFFFFF)
        else:
            tx, ty = FP.words(d)
            r.update(kind="aboard", army=((c & 0xFFFFFFFF) - ARMY_BASE) // ARMY_SIZE, target=[tx, ty])
        out.append(r)
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
