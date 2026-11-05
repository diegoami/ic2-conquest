#!/usr/bin/env python3
"""The D734 end-check hook (#195 C22/C23, 2026-11-05): an observation-only build of the seed exe that logs every entry of the
AI walk's end check FUN_0044d734 and the three actions its tail can take.

    python3 patches/d734tail_hook.py <game folder>   # reads "... seed.exe", writes "... seed d734hook.exe"

FUN_0044d734 (pinned seed build) walks the line to the target; when the army ends one tile from it (FUN_00449018 == 1) the
tail reads the target tile's unit-map code: a land code 2..11 with a cheaper cost than the moves recurses one step
(0x44D8E5); a city (20..99) of a nation at war is besieged (FUN_0044b27c, 0x44D949) if moves > 0; any other city (own,
allied, at peace) gets the army's resupply FUN_0044f6d8 (0x44D935, row C23); an army (200..247) of a nation at war is
attacked (FUN_0044aee4, 0x44D99B) if moves > 0. Callers: FUN_0044dba8 (0x44DC16, 0x44DC3A, 0x44DC6C), itself (0x44D8E5)
and 0x446DB1 / 0x446DEA.

Probes (pushfd/pushad around the log, so the game runs the same instructions on the same values):
  1  0x44D737  entry, `add esp,-0x18; push ebx; push esi` (5 bytes, re-run in the cave): AX army, EDX target dword, the
               army's position dword (+0), its +4 dword (moves in the high word), [ebp+4] (D734's return) and, in +0x20,
               [[ebp]+4] (the return address of the frame above: FUN_0044dba8's caller when D734 was called from it).
  2  0x44D935  `call 0x44f6d8` (F6D8 resupply; AX city, DX army)
  3  0x44D949  `call 0x44b27c` (siege; AX army, DX city)
  4  0x44D99B  `call 0x44aee4` (attack; AX army, DX target army)
     For 2-4 the call is moved to the cave (rel32 relocated) after the log: EAX, EDX, the army's position, its +0xA dword
     (supplies | money, before the action), [ebp+4], and [[ebp]+4] in +0x20.
A 40-byte record (patches/walk_hook.py layout): +0 kind, +4..+0x14 five values, +0x18 nation, +0x1C week, +0x20 the outer
return address, +0x24 sequence. Log: CTL 0x565000 (+0 count, +4 'D734', +8 capacity), BUF 0x565100.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import econ2_hook as E  # noqa: E402
import walk_hook as W  # noqa: E402

MAGIC = 0x34373344                      # 'D734'
DST = "Imperial Conquest 2 fast rollingsave seed d734hook.exe"
RET1 = b"\x8B\x44\x24" + bytes([E.R["ebp"]]) + b"\x8B\x40\x04"                 # eax := [saved ebp + 4]
RET2 = b"\x8B\x44\x24" + bytes([E.R["ebp"]]) + b"\x8B\x00\x8B\x40\x04"         # eax := [[saved ebp] + 4]

# site: (kind, replaced bytes, call target or None (re-run the bytes), army register, [values])
SITES = {
    0x44D737: (1, "83c4e85356", None, "eax", lambda a: [E.reg("eax"), E.reg("edx"), E.army_field(a, 0), E.army_field(a, 4), RET1]),
    0x44D935: (2, "e89e1d0000", 0x44F6D8, "edx", lambda a: [E.reg("eax"), E.reg("edx"), E.army_field(a, 0), E.army_field(a, 0xA), RET1]),
    0x44D949: (3, "e82ed9ffff", 0x44B27C, "eax", lambda a: [E.reg("eax"), E.reg("edx"), E.army_field(a, 0), E.army_field(a, 0xA), RET1]),
    0x44D99B: (4, "e844d5ffff", 0x44AEE4, "eax", lambda a: [E.reg("eax"), E.reg("edx"), E.army_field(a, 0), E.army_field(a, 0xA), RET1]),
}
KINDS = {1: "entry", 2: "resupply", 3: "siege", 4: "attack"}


def body(kind, values):
    b = bytearray(E.body(kind, values))
    # E.body ends with "inc dword [CTL]" (6 bytes) after the count is stored; insert the outer return address before it,
    # while ECX still points at the record. The skip jump (log full) targets the end and stays valid: it jumps over the
    # whole tail, so its displacement grows by the inserted length.
    extra = RET2 + b"\x89\x41\x20"
    tail = len(b) - 6
    b[tail:tail] = extra
    jae = 12                                 # after "mov ecx,[CTL]" (6) and "cmp ecx,CAP" (6)
    disp = struct.unpack_from("<i", b, jae + 2)[0] + len(extra)
    struct.pack_into("<i", b, jae + 2, disp)
    return bytes(b)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    for site, (_, want, _, _, _) in SITES.items():
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
    b[raw(W.CTL + 4):raw(W.CTL + 8)] = E.u32(MAGIC)
    b[raw(W.CTL + 8):raw(W.CTL + 12)] = E.u32(W.CAP)
    va, out = W.CAVES, {}
    for site, (kind, want, target, army, values) in SITES.items():
        want = bytes.fromhex(want)
        code = bytearray(b"\x9C\x60") + body(kind, values(army)) + b"\x61\x9D"
        if target is None:
            code += want
        else:
            code += b"\xE8" + W.rel32(va + len(code), target)
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
        kind, a, d, pos, f4, ret1, nation, week, ret2, seq = struct.unpack_from("<10i", buf, i * W.REC)
        lo = lambda v: struct.unpack("<h", struct.pack("<H", v & 0xFFFF))[0]
        r = {"seq": seq, "nation": nation, "week": week, "kind": KINDS.get(kind, kind), "ret": ret1 & 0xFFFFFFFF,
             "ret_outer": ret2 & 0xFFFFFFFF, "army_pos": E.words(pos)}
        if kind == 1:
            r.update(army=lo(a), target=E.words(d), moves=E.words(f4)[1])
        else:
            s, m = E.words(f4)
            r.update(ax=lo(a), dx=lo(d), supplies=s, money=m)
            if kind == 2:
                r.update(city=lo(a), army=lo(d))
            elif kind == 3:
                r.update(army=lo(a), city=lo(d))
            else:
                r.update(army=lo(a), target_army=lo(d))
        out.append(r)
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
