#!/usr/bin/env python3
"""Gap-B call-order hook (research issue #168, owner-routed 2026-11-02): an observation-only build of the seed exe that logs, in
order, the entry of each function on the AI army path and the siege, with the caller's return address and the acting army's
moves, plus the moves of two watched armies at every event.

    python3 patches/gapb_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed gapbhook.exe"
    IC2_FLEET_HOOK=gapb_hook IC2_HOOK_LOG=gapb IC2_GAPB_WATCH=2,5 python3 -m difftest.probes.fleetphase_hook_run OUT 1 START.SAV

Entry probes (the prologue bytes, whole non-relative instructions, are moved into the stub and run after the log):
  FA20 one AI seat          F31C army phase            E41C supply pass (army)     E84C mercenary run (army)
  DBA8 walk (army, target)  D734 line walk + end check (army, target)              B27C siege (army, city)
  AEE4 attack army (army, enemy army)                  F6D8 non-war city (city, army)                      EBE8 garrison fallback (army)
  AAB4 fallback gate (army)
plus the AAB4 return at F31C's call site 0x44F4CC (as patches/aab4_hook.py), kind "aab4ret" with AL.
Record (48 bytes): +0 kind, +4 return address (the caller), +8 EAX, +0xC EDX, +0x10 ECX, +0x14/+0x18 the army record dwords +0
(x | y) and +4 (owner | moves) of the army index in AX when 0 <= AX < 200 (else 0xFFFFFFFF), +0x1C/+0x20 the +4 dword
(owner | moves) of the two watched armies, +0x24 nation 0x4A0320, +0x28 sequence, +0x2C AL (aab4ret only).
For F6D8 the army is EDX (the record fields then read EDX). Log: CTL 0x565000 (+0 count, +4 'GAPB', +8 capacity), BUF 0x565100.
"""
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402
from decide_hook import ARMIES, ARMY_REC, words  # noqa: E402

MAGIC = 0x42504147                      # 'GAPB'
DST = "Imperial Conquest 2 fast rollingsave seed gapbhook.exe"
REC, CAP = 48, 32768
WATCH = [int(x) for x in os.environ.get("IC2_GAPB_WATCH", "2,5").split(",")][:2]
# kind: (va, prologue bytes moved into the stub, register holding the army: "eax" or "edx")
ENTRIES = {
    1: (0x44FA20, "0fbf0520034a00", "eax"),
    2: (0x44F31C, "5356575583c4f0", "eax"),
    3: (0x44E41C, "5356575583c4f0", "eax"),
    4: (0x44E84C, "5356575551", "eax"),
    5: (0x44DBA8, "558bec83c4f0", "eax"),
    6: (0x44D734, "558bec83c4e8", "eax"),
    7: (0x44B27C, "558bec83c4b8", "eax"),
    8: (0x44AEE4, "5356575583c4ac", "eax"),
    9: (0x44F6D8, "535657558bea", "edx"),
    10: (0x44EBE8, "5356575551", "eax"),
    11: (0x44AAB4, "5356578bd8", "eax"),
}
NAMES = {1: "FA20 seat", 2: "F31C armies", 3: "E41C supply", 4: "E84C merc run", 5: "DBA8 walk", 6: "D734 line walk",
         7: "B27C SIEGE", 8: "AEE4 attack army", 9: "F6D8 non-war city", 10: "EBE8 fallback", 11: "AAB4 gate", 12: "aab4ret"}
AAB4_SITE, AAB4_BACK, AAB4 = 0x44F4CC, 0x44F4D3, 0x44AAB4
AAB4_EXPECT = bytes.fromhex("8bc6e8e1b5ffff")
u32 = W.u32


def put(slot):
    return b"\x89\x41" + bytes([slot])   # mov [ecx+slot], eax


def log_body(kind, reg):
    """After pushfd/pushad: [esp] = EDI ESI EBP ESP EBX EDX ECX EAX (+0..+0x1C), [esp+0x20] = EFLAGS, [esp+0x24] = the return
    address of the probed function (entry probes) or F31C's own frame (the aab4ret probe, which logs 0 there)."""
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)                                    # mov ecx, [CTL]
    b += b"\x81\xF9" + u32(CAP)                                      # cmp ecx, CAP
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([REC])                                  # imul ecx, ecx, REC
    b += b"\x81\xC1" + u32(W.BUF)                                    # add ecx, BUF
    b += b"\xC7\x01" + u32(kind)                                     # mov dword [ecx], kind
    if kind == 12:
        b += b"\x31\xC0" + put(4)                                    # xor eax, eax; [ecx+4] = 0
    else:
        b += b"\x8B\x44\x24\x24" + put(4)                            # mov eax, [esp+0x24]: return address
    b += b"\x8B\x44\x24\x1C" + put(8)                                # saved EAX
    b += b"\x8B\x44\x24\x14" + put(0x0C)                             # saved EDX
    b += b"\x8B\x44\x24\x18" + put(0x10)                             # saved ECX
    b += b"\x0F\xBF\x44\x24" + (b"\x1C" if reg == "eax" else b"\x14")  # movsx eax, word [esp+0x1C|0x14]
    b += b"\x83\xF8\x00"                                             # cmp eax, 0
    jl = len(b); b += b"\x7C\x00"
    b += b"\x3D" + u32(200)                                          # cmp eax, 200
    jge = len(b); b += b"\x7D\x00"
    b += b"\x69\xC0" + u32(ARMY_REC)                                 # imul eax, eax, 0x290
    b += b"\x05" + u32(ARMIES)                                       # add eax, ARMIES
    b += b"\x8B\x10\x89\x51\x14"                                     # mov edx, [eax]; mov [ecx+0x14], edx
    b += b"\x8B\x50\x04\x89\x51\x18"                                 # mov edx, [eax+4]; mov [ecx+0x18], edx
    skip = len(b); b += b"\xEB\x00"
    bad = len(b)
    b += b"\xC7\x41\x14" + u32(0xFFFFFFFF) + b"\xC7\x41\x18" + u32(0xFFFFFFFF)
    done = len(b)
    b[jl + 1] = bad - (jl + 2); b[jge + 1] = bad - (jge + 2); b[skip + 1] = done - (skip + 2)
    for i, a in enumerate(WATCH):
        b += b"\xA1" + u32(ARMIES + ARMY_REC * a + 4) + put(0x1C + 4 * i)
    b += b"\x0F\xBF\x05" + u32(W.NATION) + put(0x24)
    b += b"\xA1" + u32(W.CTL) + put(0x28)                            # sequence = count
    if kind == 12:
        b += b"\x0F\xB6\x44\x24\x1C" + put(0x2C)                     # movzx eax, byte [esp+0x1C]: AL
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    sites = {k: (va, bytes.fromhex(p), reg) for k, (va, p, reg) in ENTRIES.items()}
    for k, (va, want, _) in sites.items():
        if len(want) < 5 or bytes(b[W.off(va):W.off(va) + len(want)]) != want:
            raise SystemExit("0x%X holds %s, not %s" % (va, bytes(b[W.off(va):W.off(va) + 8]).hex(), want.hex()))
    if bytes(b[W.off(AAB4_SITE):W.off(AAB4_SITE) + 7]) != AAB4_EXPECT:
        raise SystemExit("0x44F4CC changed")
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
    for k, (site, want, reg) in sites.items():
        code = bytearray(b"\x9C\x60") + log_body(k, reg) + b"\x61\x9D" + want
        code += b"\xE9" + W.rel32(va + len(code), site + len(want))
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + len(want)] = b"\xE9" + W.rel32(site, va) + b"\x90" * (len(want) - 5)
        out[NAMES[k]] = hex(va)
        va = (va + len(code) + 15) & ~15
    code = bytearray(b"\x8B\xC6") + b"\xE8" + W.rel32(va + 2, AAB4)  # mov eax, esi; call 0x44aab4
    code += b"\x9C\x60" + log_body(12, "eax") + b"\x61\x9D"
    code += b"\xE9" + W.rel32(va + len(code), AAB4_BACK)
    b[raw(va):raw(va) + len(code)] = code
    b[W.off(AAB4_SITE):W.off(AAB4_SITE) + 7] = b"\xE9" + W.rel32(AAB4_SITE, va) + b"\x90\x90"
    out["aab4ret"] = hex(va)
    va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("caves overflow: %#x" % va)
    return out


def decode(buf, n):
    out = []
    for i in range(n):
        kind, ret, eax, edx, ecx, a0, a4, w1, w2, nation, seq, al = struct.unpack_from("<12I", buf, i * REC)
        r = {"seq": seq, "nation": words(nation)[0], "kind": NAMES.get(kind, kind), "ret": hex(ret),
             "eax": eax & 0xFFFF, "edx": edx, "ecx": ecx}
        if a0 != 0xFFFFFFFF:
            x, y = words(a0)
            owner, moves = words(a4)
            r.update(x=x, y=y, owner=owner, moves=moves)
        r["watch"] = {str(WATCH[0]): words(w1)[1], str(WATCH[1]): words(w2)[1]}
        if kind == 12:
            r["aab4"] = al & 0xFF
        out.append(r)
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
