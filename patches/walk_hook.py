#!/usr/bin/env python3
"""The AI-walk hook (research #97, delegated 2026-10-30): an observation-only build of the seed exe that logs, in memory, what the
original's AI army move `FUN_0044dba8` reads when it decides whether to walk again.

    python3 patches/walk_hook.py <game folder>     # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed walkhook.exe"

Disassembly of FUN_0044dba8 (pinned seed build): the intermediate point is the word [ebp-0xa]; only the FUN_0044db38 branch writes it.
The direct-line branch (FUN_0044cb40 returns non-zero) skips the write, but the no-progress fallback (0x44DC4D) and the recursion
(0x44DC8C) both test `cmp word [ebp-0xa],-1; jle`. Three probes:

  A  0x44DC06  `call 0x44CB40` is re-pointed to a stub that makes the same call, then logs: AL (the direct-line result), the army
               ([ebp-2]), the target ([ebp-6], x in the low word, y in the high), [ebp-0xa] at entry (the word the direct path will
               test: stale), the army's x, y and moves ([ebx], [ebx+6]), the return address of FUN_0044dba8 ([ebp+4]: which of the 9
               call sites, or 0x44DCA6 for the recursion) and the current nation. It then returns with every register as the call left it.
  B  0x44DC8C  the recursion test (`cmp word [ebp-0xa],-1`, 5 bytes) becomes `jmp stub`: log the same fields (reached only when the
               target is more than 1 away and moves are left), then `cmp word [ebp-0xa],-1; jle 0x44DCA6; jmp 0x44DC93`.
  C  0x44DC4D  the no-progress test, the same way: then `cmp word [ebp-0xa],-1; jle 0x44DC75; jmp 0x44DC54`.

Each stub saves and restores EFLAGS and all general registers (pushfd/pushad), so the game runs the same instructions on the same
values: an observation, not a change. A 40-byte record: +0 kind (1 A, 2 B, 3 C), +4 AL (A) or 0, +8 target dword, +0xC army,
+0x10 [ebp-0xa] (sign-extended), +0x14 army x (lo) / y (hi), +0x18 moves, +0x1C return address, +0x20 nation, +0x24 sequence.
The log lives in the grown `.patch` section: CTL 0x565000 (+0 count, +4 magic 'WLK1', +8 capacity), BUF 0x565100.
"""
import struct
import sys
from pathlib import Path

BASE = 0x400000
CODE_VA, CODE_RAW = 0x401000, 0x400
PATCH_VA, PATCH_RAW, SEED_PATCH_SIZE = 0x564000, 0x11CC00, 0x600
CAVES = 0x564600
CTL, BUF = 0x565000, 0x565100
RAW_SIZE = 0x1200
REC, CAP = 40, 65536
MAGIC = 0x314B4C57                      # 'WLK1'
NATION = 0x4A0320
SRC = "Imperial Conquest 2 fast rollingsave seed.exe"
DST = "Imperial Conquest 2 fast rollingsave seed walkhook.exe"
CALL_SITES = {0x44E913: "e913", 0x44EC7D: "ec7d", 0x44ECD6: "ecd6", 0x44F2E7: "intercept_capital", 0x44F2F9: "intercept_army",
              0x44F409: "f409", 0x44F43F: "f43f", 0x44F47C: "f47c", 0x44F4A3: "f4a3", 0x44DCA1: "recursion"}

PROBE_A, PROBE_B, PROBE_C = 0x44DC06, 0x44DC8C, 0x44DC4D
EXPECT = {PROBE_A: bytes.fromhex("e835efffff"), PROBE_B: bytes.fromhex("66837df6ff7e13"), PROBE_C: bytes.fromhex("66837df6ff7e21")}


def off(va):
    return va - CODE_VA + CODE_RAW


def rel32(src, target):
    return struct.pack("<i", target - (src + 5))


def u32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def log_body(kind):
    """pushfd/pushad already done; esp+0x1C is the saved EAX. Writes one record and bumps the count."""
    body = bytearray()
    body += b"\x8B\x0D" + u32(CTL)                          # mov ecx, [CTL]
    body += b"\x81\xF9" + u32(CAP)                          # cmp ecx, CAP
    jae_at = len(body); body += b"\x0F\x83\0\0\0\0"         # jae skip
    body += b"\x89\xCA"                                     # mov edx, ecx (sequence)
    body += b"\x6B\xC9" + bytes([REC])                      # imul ecx, ecx, REC
    body += b"\x81\xC1" + u32(BUF)                          # add ecx, BUF
    body += b"\xC7\x01" + u32(kind)                         # mov dword [ecx], kind
    if kind == 1:
        body += b"\x0F\xB6\x44\x24\x1C"                     # movzx eax, byte [esp+0x1C] (saved AL)
    else:
        body += b"\x31\xC0"                                 # xor eax, eax
    body += b"\x89\x41\x04"                                 # mov [ecx+4], eax
    body += b"\x8B\x45\xFA\x89\x41\x08"                     # mov eax, [ebp-6]; mov [ecx+8], eax
    body += b"\x0F\xBF\x45\xFE\x89\x41\x0C"                 # movsx eax, word [ebp-2]; mov [ecx+0xC], eax
    body += b"\x0F\xBF\x45\xF6\x89\x41\x10"                 # movsx eax, word [ebp-0xa]; mov [ecx+0x10], eax
    body += b"\x8B\x03\x89\x41\x14"                         # mov eax, [ebx]; mov [ecx+0x14], eax
    body += b"\x0F\xBF\x43\x06\x89\x41\x18"                 # movsx eax, word [ebx+6]; mov [ecx+0x18], eax
    body += b"\x8B\x45\x04\x89\x41\x1C"                     # mov eax, [ebp+4]; mov [ecx+0x1C], eax
    body += b"\x0F\xBF\x05" + u32(NATION) + b"\x89\x41\x20"  # movsx eax, word [NATION]; mov [ecx+0x20], eax
    body += b"\x89\x51\x24"                                 # mov [ecx+0x24], edx
    body += b"\xFF\x05" + u32(CTL)                          # inc dword [CTL]
    body[jae_at + 2:jae_at + 6] = struct.pack("<i", len(body) - (jae_at + 6))
    return body


def stub_a(va):
    body = bytearray(b"\xE8" + rel32(va, 0x44CB40))         # call FUN_0044cb40 (same registers as the original call)
    body += b"\x9C\x60"                                     # pushfd; pushad
    body += log_body(1)
    body += b"\x61\x9D\xC3"                                 # popad; popfd; ret
    return bytes(body)


def stub_cmp(va, kind, jle_to, back_to):
    body = bytearray(b"\x9C\x60")
    body += log_body(kind)
    body += b"\x61\x9D"
    body += b"\x66\x83\x7D\xF6\xFF"                         # cmp word [ebp-0xa], -1
    body += b"\x0F\x8E" + struct.pack("<i", jle_to - (va + len(body) + 6))   # jle jle_to
    body += b"\xE9" + rel32(va + len(body), back_to)        # jmp back_to
    return bytes(body)


def build(b):
    if len(b) != PATCH_RAW + SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d (the seed exe has %d)" % (len(b), PATCH_RAW + SEED_PATCH_SIZE))
    if any(x != 0xCC for x in b[PATCH_RAW + (CAVES - PATCH_VA):PATCH_RAW + SEED_PATCH_SIZE]):
        raise SystemExit("the .patch space from 0x%X is not free" % CAVES)
    for va, want in EXPECT.items():
        if bytes(b[off(va):off(va) + len(want)]) != want:
            raise SystemExit("0x%X holds %s, not %s" % (va, bytes(b[off(va):off(va) + len(want)]).hex(), want.hex()))
    hdr = 0x1F8 + 8 * 40
    if bytes(b[hdr:hdr + 6]) != b".patch":
        raise SystemExit(".patch is not the 9th section")
    vsize = BUF + CAP * REC - PATCH_VA
    struct.pack_into("<I", b, hdr + 8, vsize)
    struct.pack_into("<I", b, hdr + 16, RAW_SIZE)
    struct.pack_into("<I", b, hdr + 36, struct.unpack_from("<I", b, hdr + 36)[0] | 0x80000000)
    struct.pack_into("<I", b, 0x118 + 56, (PATCH_VA - BASE + vsize + 0xFFF) & ~0xFFF)
    b += b"\xCC" * (CTL - PATCH_VA - SEED_PATCH_SIZE) + bytes(RAW_SIZE - (CTL - PATCH_VA))
    raw = lambda va: PATCH_RAW + (va - PATCH_VA)
    b[raw(CTL + 4):raw(CTL + 8)] = u32(MAGIC)
    b[raw(CTL + 8):raw(CTL + 12)] = u32(CAP)
    va, out = CAVES, {}
    for name, make, site in (("A", stub_a, PROBE_A),
                             ("B", lambda v: stub_cmp(v, 2, 0x44DCA6, 0x44DC93), PROBE_B),
                             ("C", lambda v: stub_cmp(v, 3, 0x44DC75, 0x44DC54), PROBE_C)):
        code = make(va)
        b[raw(va):raw(va) + len(code)] = code
        if name == "A":
            b[off(site):off(site) + 5] = b"\xE8" + rel32(site, va)
        else:
            b[off(site):off(site) + 7] = b"\xE9" + rel32(site, va) + b"\x90\x90"
        out[name] = va
        va = (va + len(code) + 15) & ~15
    if va > CTL:
        raise SystemExit("caves overflow into the control block")
    return out


def decode(buf, n):
    out = []
    kinds = {1: "A_direct_check", 2: "B_recursion_test", 3: "C_no_progress_test"}
    for i in range(n):
        kind, al, target, army, word, xy, moves, ret, nation, seq = struct.unpack_from("<IIIiiIiIiI", buf, i * REC)
        out.append({"seq": seq, "kind": kinds.get(kind, kind), "direct": al if kind == 1 else None, "army": army,
                    "target": [struct.unpack("<h", u32(target)[:2])[0], struct.unpack("<h", u32(target)[2:])[0]],
                    "word": word, "x": struct.unpack("<h", u32(xy)[:2])[0], "y": struct.unpack("<h", u32(xy)[2:])[0],
                    "moves": moves, "caller": CALL_SITES.get(ret - 5, hex(ret)), "nation": nation})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    b = bytearray((folder / SRC).read_bytes())
    caves = build(b)
    (folder / DST).write_bytes(bytes(b))
    print("wrote", folder / DST, {k: hex(v) for k, v in caves.items()})
