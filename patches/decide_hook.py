#!/usr/bin/env python3
"""The army-decision hook (AI decision comparison with remake main, owner 2026-10-30): an observation-only build of the seed
exe that logs, for every own army the original's army phase FUN_0044f31c decides, every input of its branch.

    python3 patches/decide_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed decidehook.exe"

Disassembly of F31C (pinned seed build), per army ESI with record EBX = 0x47c1ec + 0x290*ESI and moves > 0:
FUN_0044e670 writes the home city to [esp]; FUN_0044ece4 the city target [esp+2], its score [esp+8] and distance [esp+0xc];
FUN_0044ee60 the army target [esp+4], its score [esp+6] and distance [esp+0xa]. Then:
  army > 100 and (supplies [ebx+0xa] > 0 or morale [ebx+0xe] > 59 or army distance < 9), unless city > 100 and city
    distance < moves and army distance > 2*moves:                            walk to the army target (0x44F409)
  city > 100 and (supplies > 0 or city distance < 20):                       walk to the city target (0x44F43F)
  FUN_0044a698(army) / 500 >= supplies, or no city target:                   walk to the home city (0x44F47C)
  else FUN_0044e84c (0x44F485), then army > 70: walk to the army target (0x44F4A3), else city > 85: to the city (0x44F4C7).
After any of them, FUN_0044aab4 / FUN_0044ebe8 (not logged here).

Probes, each a `jmp stub` over one instruction the stub runs before jumping back:
  1  0x44F3B8  `cmp word [esp+6],0x64` (6 bytes, the 6th becomes a NOP): the inputs, right after FUN_0044ee60 returns.
  2  0x44F450  `mov ecx,0x1f4`: EAX = FUN_0044a698(army), the resupply test's numerator (reached only on that path).
Each stub saves and restores EFLAGS and all general registers (pushfd/pushad). A 48-byte record: +0 kind, +4 EBX (the army
record), +8..+0x14 the frame dwords [esp+0], [esp+4], [esp+8], [esp+0xc] (probe 2: +8 = EAX), +0x18..+0x24 the army record
dwords at +0, +4, +8, +0xc, +0x28 nation, +0x2C sequence. Log: CTL 0x565000 (+0 count, +4 'DEC1', +8 capacity), BUF 0x565100.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

MAGIC = 0x31434544                      # 'DEC1'
DST = "Imperial Conquest 2 fast rollingsave seed decidehook.exe"
REC, CAP = 48, 32768
P1, P2 = 0x44F3B8, 0x44F450
EXPECT = {P1: bytes.fromhex("66837c240664"), P2: bytes.fromhex("b9f4010000")}
ARMIES, ARMY_REC = 0x47C1EC, 0x290
u32 = W.u32
FB = 36                                  # F31C's esp = the stub's esp + 36 after pushfd/pushad


def put(slot):
    return b"\x89\x41" + bytes([slot])   # mov [ecx+slot], eax


def log_body(kind):
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)
    b += b"\x81\xF9" + u32(CAP)
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([REC])
    b += b"\x81\xC1" + u32(W.BUF)
    b += b"\xC7\x01" + u32(kind)
    b += b"\x8B\x54\x24\x10"                                         # mov edx, [esp+0x10] (saved EBX)
    b += b"\x89\x51\x04"                                             # mov [ecx+4], edx
    if kind == 1:
        for i, off in enumerate((0, 4, 8, 12)):
            b += b"\x8B\x44\x24" + bytes([FB + off]) + put(8 + 4 * i)  # mov eax, [esp+FB+off]
    else:
        b += b"\x8B\x44\x24\x1C" + put(8)                            # mov eax, [esp+0x1c] (saved EAX)
    for i, off in enumerate((0, 4, 8, 12)):
        b += b"\x8B\x42" + bytes([off]) + put(0x18 + 4 * i)          # mov eax, [edx+off]
    b += b"\x0F\xBF\x05" + u32(W.NATION) + put(0x28)
    b += b"\xA1" + u32(W.CTL) + put(0x2C)                            # sequence = count
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def stub(va, kind, replaced, back):
    body = bytearray(b"\x9C\x60") + log_body(kind) + b"\x61\x9D" + replaced
    body += b"\xE9" + W.rel32(va + len(body), back)
    return bytes(body)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    for va, want in EXPECT.items():
        if bytes(b[W.off(va):W.off(va) + len(want)]) != want:
            raise SystemExit("0x%X holds %s, not %s" % (va, bytes(b[W.off(va):W.off(va) + len(want)]).hex(), want.hex()))
    hdr = 0x1F8 + 8 * 40
    if bytes(b[hdr:hdr + 6]) != b".patch":
        raise SystemExit(".patch is not the 9th section")
    vsize = W.BUF + CAP * REC - W.PATCH_VA
    struct.pack_into("<I", b, hdr + 8, vsize)
    struct.pack_into("<I", b, hdr + 16, W.RAW_SIZE)
    struct.pack_into("<I", b, hdr + 36, struct.unpack_from("<I", b, hdr + 36)[0] | 0x80000000)
    struct.pack_into("<I", b, 0x118 + 56, (W.PATCH_VA - W.BASE + vsize + 0xFFF) & ~0xFFF)
    b += b"\xCC" * (W.CTL - W.PATCH_VA - W.SEED_PATCH_SIZE) + bytes(W.RAW_SIZE - (W.CTL - W.PATCH_VA))
    raw = lambda va: W.PATCH_RAW + (va - W.PATCH_VA)
    b[raw(W.CTL + 4):raw(W.CTL + 8)] = u32(MAGIC)
    b[raw(W.CTL + 8):raw(W.CTL + 12)] = u32(CAP)
    va, out = W.CAVES, {}
    for site, kind in ((P1, 1), (P2, 2)):
        want = EXPECT[site]
        code = stub(va, kind, want, site + len(want))
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + len(want)] = b"\xE9" + W.rel32(site, va) + b"\x90" * (len(want) - 5)
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("caves overflow")
    return out


def words(d):
    lo, hi = struct.unpack("<hh", struct.pack("<I", d & 0xFFFFFFFF))
    return lo, hi


def decode(buf, n):
    out = []
    for i in range(n):
        kind, rec, f0, f4, f8, fc, a0, a4, a8, ac, nation, seq = struct.unpack_from("<12I", buf, i * REC)
        army = (rec - ARMIES) // ARMY_REC
        x, y = words(a0)
        owner, moves = words(a4)
        _, supplies = words(a8)
        _, morale = words(ac)
        r = {"seq": seq, "nation": words(nation)[0], "army": army, "x": x, "y": y, "owner": owner, "moves": moves,
             "supplies": supplies, "morale": morale}
        if kind == 1:
            home, city = words(f0)
            target, army_score = words(f4)
            city_score, army_dist = words(f8)
            city_dist, _ = words(fc)
            r.update(kind="inputs", home=home, city=city, city_score=city_score, city_dist=city_dist, target=target,
                     army_score=army_score, army_dist=army_dist)
        else:
            r.update(kind="resupply", a698=struct.unpack("<i", struct.pack("<I", f0))[0])
        out.append(r)
    return out


def branch(r, a698=None):
    """F31C's choice from the logged inputs (the walks themselves are FUN_0044dba8's business)."""
    a, c, mv, sup = r["army_score"], r["city_score"], r["moves"], r["supplies"]
    if a > 100 and (sup > 0 or r["morale"] > 59 or r["army_dist"] < 9):
        if not (c > 100 and r["city_dist"] < mv and r["army_dist"] > 2 * mv):
            return "army>100"
    if c > 100 and (sup > 0 or r["city_dist"] < 20):
        return "city>100"
    if a698 is None:
        raise ValueError("resupply test reached without the a698 record")
    if a698 // 500 >= sup or r["city"] == -1:          # idiv truncates; a698 is non-negative
        return "resupply"
    if a > 70:
        return "e84c+army>70"
    if c > 85:
        return "e84c+city>85"
    return "e84c"


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
