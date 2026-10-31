#!/usr/bin/env python3
"""The economy hook (#176, owner 2026-10-31): an observation-only build of the seed exe that logs the AI economy phase
FUN_0044ffbc's decisions per seat.

    python3 patches/econ_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed econhook.exe"

FUN_0044ffbc (pinned seed build): the threat sum [esp+8] and own sum [esp+4]; if own < threat, FUN_004504f4(threat - own)
deploys ready queue entries (FUN_0044a4e0) and places up to 8 new orders (FUN_004501f4: Random type, Random troops; city
from FUN_004502e0); in week 11 the tax policy rewrites +0x44A; then the fleet build, consolidation and merges.

Probes, each a `jmp stub` over whole instructions the stub runs itself (pushfd/pushad around the log):
  1  0x45011E  `mov eax,[esp+4]; cmp eax,[esp+8]` (8 bytes): own, threat, treasury +0x438,
               unity|mobilization (+0x440 dword), baseline|tax (+0x448 dword). EBX is the nation record.
  2  0x4501D6  `call 0x450768` (the fleet build; the stub makes the call): the same nation dword fields after the tax
               policy and the recruiting.
  3  0x4502D9  the 5 pops before FUN_004501f4's `ret` (the stub pops and returns): the order just written — the entry
               index [ebp-2], state|type (entry dword 0), troops|city (entry dword 4).
  4  0x44A4E0  FUN_0044a4e0's prologue `push ebp; mov ebp,esp; add esp,-12` (6 bytes): a ready entry deployed — nation
               (AX), entry (DX), the entry's two dwords, the return address (caller).
A 40-byte record: +0 kind, +4..+0x14 five values, +0x18 nation (0x4A0320), +0x1C week (0x4A0330), +0x20 reserved,
+0x24 sequence. Log: CTL 0x565000 (+0 count, +4 'ECO1', +8 capacity), BUF 0x565100 (patches/walk_hook.py layout).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

MAGIC = 0x314F4345                      # 'ECO1'
DST = "Imperial Conquest 2 fast rollingsave seed econhook.exe"
P1, P2, P3, P4 = 0x45011E, 0x4501D6, 0x4502D9, 0x44A4E0
FLEET_BUILD = 0x450768
EXPECT = {P1: bytes.fromhex("8b4424043b442408"), P3: bytes.fromhex("5f5e5b595d"), P4: bytes.fromhex("558bec83c4f4")}
WEEK = 0x4A0330
QUEUE = 0x474954                        # nation + 0x2E4: 40 entries × 8 bytes
u32 = W.u32
FB = 36


def head(kind):
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)
    b += b"\x81\xF9" + u32(W.CAP)
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([W.REC])
    b += b"\x81\xC1" + u32(W.BUF)
    b += b"\xC7\x01" + u32(kind)
    return b, jae


def tail(b, jae):
    b += b"\x0F\xBF\x05" + u32(W.NATION) + b"\x89\x41\x18"
    b += b"\x0F\xBF\x05" + u32(WEEK) + b"\x89\x41\x1C"
    b += b"\xA1" + u32(W.CTL) + b"\x89\x41\x24"
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def nation_fields(b, first_slot):
    """EDX = the nation record (saved EBX): treasury +0x438, wealth +0x430, dword +0x440, dword +0x448."""
    b += b"\x8B\x54\x24\x10"                                         # mov edx, [esp+0x10] (saved EBX)
    for i, off in enumerate((0x438, 0x430, 0x440, 0x448)):
        b += b"\x8B\x82" + u32(off) + b"\x89\x41" + bytes([first_slot + 4 * i])   # mov eax,[edx+off]; mov [ecx+slot],eax
    return b


def body1():
    b, jae = head(1)
    b += b"\x8B\x44\x24" + bytes([FB + 4]) + b"\x89\x41\x04"              # own
    b += b"\x8B\x44\x24" + bytes([FB + 8]) + b"\x89\x41\x08"              # threat
    b += b"\x8B\x54\x24\x10"                                             # mov edx, [esp+0x10] (saved EBX): the nation
    for slot, off in ((0x0C, 0x438), (0x10, 0x440), (0x14, 0x448)):       # treasury, unity|mob, base|tax
        b += b"\x8B\x82" + u32(off) + b"\x89\x41" + bytes([slot])
    return tail(b, jae)


def body2():
    b, jae = head(2)
    b = nation_fields(b, 0x04)                                           # treasury, wealth, unity|mob, base|tax
    return tail(b, jae)


def body3():
    b, jae = head(3)
    b += b"\x8B\x54\x24\x08"                                             # mov edx, [esp+8] (saved EBP)
    b += b"\x0F\xBF\x42\xFE\x89\x41\x04"                                 # movsx eax, word [edx-2]: the entry index
    b += b"\x8B\x54\x24\x1C"                                             # mov edx, [esp+0x1c] (saved EAX): the entry
    b += b"\x8B\x02\x89\x41\x08"                                         # state|type
    b += b"\x8B\x42\x04\x89\x41\x0C"                                     # troops|city
    return tail(b, jae)


def body4():
    b, jae = head(4)
    b += b"\x0F\xBF\x44\x24\x1C\x89\x41\x04"                             # nation (AX)
    b += b"\x0F\xBF\x54\x24\x14\x89\x51\x08"                             # entry (DX)
    b += b"\x69\xC0\x94\x04\x00\x00"                                     # imul eax, eax, 0x494
    b += b"\x8D\x84\xD0" + u32(QUEUE)                                    # lea eax, [eax + edx*8 + QUEUE]
    b += b"\x8B\x10\x89\x51\x0C"                                         # state|type
    b += b"\x8B\x50\x04\x89\x51\x10"                                     # troops|city
    b += b"\x8B\x44\x24\x24\x89\x41\x14"                                 # return address
    return tail(b, jae)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    for site, want in list(EXPECT.items()) + [(P2, b"\xE8" + W.rel32(P2, FLEET_BUILD))]:
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

    def place(site, code, length):
        nonlocal va
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + length] = b"\xE9" + W.rel32(site, va) + b"\x90" * (length - 5)
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15

    code = bytearray(b"\x9C\x60") + body1() + b"\x61\x9D" + EXPECT[P1]
    code += b"\xE9" + W.rel32(va + len(code), P1 + 8)
    place(P1, bytes(code), 8)
    code = bytearray(b"\x9C\x60") + body2() + b"\x61\x9D"
    code += b"\xE8" + W.rel32(va + len(code), FLEET_BUILD)
    code += b"\xE9" + W.rel32(va + len(code), P2 + 5)
    place(P2, bytes(code), 5)
    code = bytearray(b"\x9C\x60") + body3() + b"\x61\x9D" + EXPECT[P3] + b"\xC3"
    place(P3, bytes(code), 5)
    code = bytearray(b"\x9C\x60") + body4() + b"\x61\x9D" + EXPECT[P4]
    code += b"\xE9" + W.rel32(va + len(code), P4 + 6)
    place(P4, bytes(code), 6)
    if va > W.CTL:
        raise SystemExit("cave overflow")
    return out


def words(d):
    return struct.unpack("<hh", struct.pack("<I", d & 0xFFFFFFFF))


def decode(buf, n):
    out = []
    for i in range(n):
        kind, v1, v2, v3, v4, v5, nation, week, _, seq = struct.unpack_from("<10i", buf, i * W.REC)
        r = {"seq": seq, "nation": nation, "week": week}
        if kind == 1:
            unity, mob = words(v4)
            _, tax = words(v5)
            r.update(kind="budget", own=v1, threat=v2, treasury=v3, unity=unity, mobilization=mob, tax=tax)
        elif kind == 2:
            unity, mob = words(v3)
            _, tax = words(v4)
            r.update(kind="after_policy", treasury=v1, wealth=v2, unity=unity, mobilization=mob, tax=tax)
        elif kind == 3:
            state, utype = words(v2)
            troops, city = words(v3)
            r.update(kind="order", entry=v1, state=state, type=utype, troops=troops, city=city)
        else:
            state, utype = words(v3)
            troops, city = words(v4)
            r.update(kind="deploy", deploy_nation=v1, entry=v2, state=state, type=utype, troops=troops, city=city,
                     caller=hex((v5 & 0xFFFFFFFF) - 5))
        out.append(r)
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
