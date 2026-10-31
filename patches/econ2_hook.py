#!/usr/bin/env python3
"""The economy-phase hook, part 2 (#176, owner 2026-10-31): an observation-only build of the seed exe that logs the parts of the
AI turn not covered by patches/econ_hook.py: the army phase's supply and hire pass FUN_0044e41c, the unit consolidation
FUN_00450858, the army and fleet merges FUN_004509f0 / FUN_00450b30, and the fleet order FUN_00450768 -> FUN_0044a004.

    python3 patches/econ2_hook.py <game folder>   # reads "... seed.exe", writes "... seed econ2hook.exe"

Probes (`jmp stub` over whole position-independent instructions the stub runs itself, pushfd/pushad around the log; the
decompile lines are research's 2026-10-11 merge report and all_app_functions.txt):
  1  0x44E423  E41C entry, `mov ebp,eax; movsx eax,bp` (EAX = army): army, position dword, supplies|money dword (+0xA).
  2  0x44E5D2  E41C exit, `add esp,0x10; pop ebp; pop edi` (EBP = army): army, supplies|money dword.
  3  0x44E4C7  before `call FUN_0044f6d8` (the city transfer), `mov edx,ebp; mov ax,[esp]` (6 bytes): army, city
               ([esp] word), supplies|money dword before the transfer.
  4  0x44E5AC  the hire, `mov word [ebx],0xffff` (the offer consumed; EBX = the pool record + 8): army, EBX, the offer's
               dword at [ebx-4] (mercenary id | unit type) and [ebx] (troops | quality), before the write.
  5  0x44AC3C  FUN_0044ac3c entry (remove a slot; consolidation and merges), `push ebx..push ecx`: army (AX), slot (DX), the
               caller (return address), the slot's dwords +0 (merc | type) and +4 (troops | quality).
  6  0x44ACB4  FUN_0044acb4 entry (move a slot to another army; the army merge), `push ebx; push esi; push edi; mov edi,ecx`:
               source (AX), destination (DX), slot (CX), caller.
  7  0x44AD38  FUN_0044ad38 entry (delete a fleet; the fleet merge), `push ebx; movsx eax,ax; imul eax,eax,0xd` (7 bytes):
               fleet (AX), caller, the fleet's dwords +0 (position) and +0x10 (money | ships).
  8  0x44A004  FUN_0044a004 entry (create a fleet order), `push ebx; inc word [0x4a0326]` (8 bytes): AX, DX, CX, caller.
A 40-byte record: +0 kind, +4..+0x14 five values, +0x18 nation, +0x1C week, +0x20 reserved, +0x24 sequence. Log: CTL 0x565000
(+0 count, +4 'EC21', +8 capacity), BUF 0x565100 (patches/walk_hook.py layout).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

MAGIC = 0x31324345                      # 'EC21'
DST = "Imperial Conquest 2 fast rollingsave seed econ2hook.exe"
WEEK = 0x4A0330
ARMY, ARMY_SIZE, FLEET, FLEET_SIZE = 0x47C1EC, 0x290, 0x49C26C, 0x1A
u32 = W.u32
# pushad: [esp+0] EDI, +4 ESI, +8 EBP, +0xC ESP, +0x10 EBX, +0x14 EDX, +0x18 ECX, +0x1C EAX; +0x20 EFLAGS; +0x24 the original ESP
R = {"edi": 0, "esi": 4, "ebp": 8, "ebx": 0x10, "edx": 0x14, "ecx": 0x18, "eax": 0x1C}
TOP = 0x24


def reg(r):                    # eax := saved register
    return b"\x8B\x44\x24" + bytes([R[r]])


def reg16(r):                  # eax := sign-extended low word of a saved register
    return b"\x0F\xBF\x44\x24" + bytes([R[r]])


def stack(k):                  # eax := dword at the original [esp+k]
    return b"\x8B\x44\x24" + bytes([TOP + k])


def stack16(k):
    return b"\x0F\xBF\x44\x24" + bytes([TOP + k])


def army_field(r, off):        # eax := dword at army[saved r (low word)] + off
    return reg16(r) + b"\x69\xC0" + u32(ARMY_SIZE) + b"\x8B\x80" + u32(ARMY + off)


def fleet_field(r, off):
    return reg16(r) + b"\x6B\xC0" + bytes([FLEET_SIZE]) + b"\x8B\x80" + u32(FLEET + off)


def slot_field(off):           # eax := dword at army[AX].slot[DX] + off (slots at +0x10, 0x20 each)
    return (reg16("eax") + b"\x69\xC0" + u32(ARMY_SIZE)
            + b"\x0F\xBF\x54\x24" + bytes([R["edx"]]) + b"\xC1\xE2\x05" + b"\x01\xD0"
            + b"\x8B\x80" + u32(ARMY + 0x10 + off))


def at_ebx(off):               # eax := dword at [saved EBX + off]
    return b"\x8B\x54\x24" + bytes([R["ebx"]]) + b"\x8B\x42" + struct.pack("b", off)


SITES = {
    # site: (kind, the replaced bytes, [value snippets])
    0x44E423: (1, "8be80fbfc5", [reg16("eax"), army_field("eax", 0), army_field("eax", 0xA)]),
    0x44E5D2: (2, "83c4105d5f", [reg16("ebp"), army_field("ebp", 0), army_field("ebp", 0xA)]),
    0x44E4C7: (3, "8bd5668b0424", [reg16("ebp"), stack16(0), army_field("ebp", 0xA)]),
    0x44E5AC: (4, "66c703ffff", [reg16("ebp"), reg("ebx"), at_ebx(-4), at_ebx(0)]),
    0x44AC3C: (5, "5356575551", [reg16("eax"), reg16("edx"), stack(0), slot_field(0), slot_field(4)]),
    0x44ACB4: (6, "53565 78bf9".replace(" ", ""), [reg16("eax"), reg16("edx"), reg16("ecx"), stack(0)]),
    0x44AD38: (7, "530fbfc06bc00d", [reg16("eax"), stack(0), fleet_field("eax", 0), fleet_field("eax", 0x10)]),
    0x44A004: (8, "5366ff0526034a00", [reg16("eax"), reg16("edx"), reg16("ecx"), stack(0)]),
}


def body(kind, values):
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)
    b += b"\x81\xF9" + u32(W.CAP)
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([W.REC])
    b += b"\x81\xC1" + u32(W.BUF)
    b += b"\xC7\x01" + u32(kind)
    for i, v in enumerate(values):
        b += v + b"\x89\x41" + bytes([4 + 4 * i])             # mov [ecx+4+4i], eax
    b += b"\x0F\xBF\x05" + u32(W.NATION) + b"\x89\x41\x18"
    b += b"\x0F\xBF\x05" + u32(WEEK) + b"\x89\x41\x1C"
    b += b"\xA1" + u32(W.CTL) + b"\x89\x41\x24"
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    for site, (_, want, _) in SITES.items():
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
    for site, (kind, want, values) in SITES.items():
        want = bytes.fromhex(want)
        code = bytearray(b"\x9C\x60") + body(kind, values) + b"\x61\x9D" + want
        code += b"\xE9" + W.rel32(va + len(code), site + len(want))
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + len(want)] = b"\xE9" + W.rel32(site, va) + b"\x90" * (len(want) - 5)
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("cave overflow")
    return out


def words(d):
    return list(struct.unpack("<hh", struct.pack("<I", d & 0xFFFFFFFF)))


def decode(buf, n):
    out = []
    for i in range(n):
        kind, a, b_, c, d, e, nation, week, _, seq = struct.unpack_from("<10i", buf, i * W.REC)
        r = {"seq": seq, "nation": nation, "week": week}
        if kind in (1, 2):
            s, m = words(c)
            r.update(kind="e41c-in" if kind == 1 else "e41c-out", army=a, supplies=s, money=m)
            if kind == 1:
                r["pos"] = words(b_)
        elif kind == 3:
            s, m = words(c)
            r.update(kind="transfer", army=a, city=b_, supplies=s, money=m)
        elif kind == 4:
            merc, typ = words(c)
            tr, q = words(d)
            r.update(kind="hire", army=a, offer=((b_ & 0xFFFFFFFF) - 0x49DA18) // 12, merc=merc, type=typ, troops=tr, quality=q)
        elif kind == 5:
            merc, typ = words(d)
            tr, q = words(e)
            r.update(kind="remove-slot", army=a, slot=b_, caller=c & 0xFFFFFFFF, merc=merc, type=typ, troops=tr, quality=q)
        elif kind == 6:
            r.update(kind="move-slot", src=a, dst=b_, slot=c, caller=d & 0xFFFFFFFF)
        elif kind == 7:
            mo, ships = words(e)
            r.update(kind="delete-fleet", fleet=a, caller=b_ & 0xFFFFFFFF, pos=words(c), money=mo, ships=ships)
        elif kind == 8:
            r.update(kind="fleet-order", ax=a, dx=b_, cx=c, caller=d & 0xFFFFFFFF)
        out.append(r)
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
