#!/usr/bin/env python3
"""The garrison-fallback gate hook (research's request after PR #300, gap A, 2026-11-02): an observation-only build of the
seed exe that logs, for every army F31C has just walked, the return value of FUN_0044aab4, which decides whether the garrison
fallback FUN_0044ebe8 runs.

    python3 patches/aab4_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed aab4hook.exe"

F31C (pinned seed build), after the branch's walk:
  44f4c7: call 0x44dba8          the walk
  44f4cc: mov eax, esi           ESI = the army index
  44f4ce: call 0x44aab4
  44f4d3: test al, al
  44f4d5: jne 0x44f4de           AL != 0: no fallback
  44f4d7: mov eax, esi
  44f4d9: call 0x44ebe8          the garrison fallback
Research's reading (2026-10-07-strategic-ai-turn.md §3.5): AAB4 returns recomputedFullMoves != army[+6], i.e. "the army
spent moves", not "the army changed tile".

Probe: the 7 bytes at 0x44F4CC (`mov eax,esi; call 0x44aab4`) become `jmp stub; nop; nop`. The stub runs them (the call
re-targeted), then pushfd/pushad, logs a 48-byte record and jumps back to 0x44F4D3: +0 kind 3, +4 ESI (army index), +8 EAX
(AL = AAB4's result), +0x18..+0x24 the army record dwords at +0, +4, +8, +0xc (x, y | owner, moves | . , supplies | . , morale),
+0x28 nation, +0x2C sequence. Log: CTL 0x565000 (+0 count, +4 'AAB4', +8 capacity), BUF 0x565100. Same runner as the fleet
hook: IC2_FLEET_HOOK=aab4_hook IC2_HOOK_LOG=aab4 python3 -m difftest.probes.fleetphase_hook_run OUT 1 START.SAV.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402
from decide_hook import ARMIES, ARMY_REC, words  # noqa: E402

MAGIC = 0x34424141                      # 'AAB4'
DST = "Imperial Conquest 2 fast rollingsave seed aab4hook.exe"
REC, CAP = 48, 32768
SITE, BACK, AAB4 = 0x44F4CC, 0x44F4D3, 0x44AAB4
EXPECT = bytes.fromhex("8bc6e8e1b5ffff")
u32 = W.u32


def put(slot):
    return b"\x89\x41" + bytes([slot])   # mov [ecx+slot], eax


def log_body():
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)                                    # mov ecx, [CTL]
    b += b"\x81\xF9" + u32(CAP)                                      # cmp ecx, CAP
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([REC])                                  # imul ecx, ecx, REC
    b += b"\x81\xC1" + u32(W.BUF)                                    # add ecx, BUF
    b += b"\xC7\x01" + u32(3)                                        # mov dword [ecx], 3
    b += b"\x8B\x44\x24\x1C" + put(8)                                # saved EAX (AAB4's result)
    b += b"\x8B\x54\x24\x04"                                         # mov edx, [esp+4] (saved ESI)
    b += b"\x89\x51\x04"                                             # mov [ecx+4], edx
    b += b"\x69\xD2" + u32(ARMY_REC)                                 # imul edx, edx, 0x290
    b += b"\x81\xC2" + u32(ARMIES)                                   # add edx, ARMIES
    for i, off in enumerate((0, 4, 8, 12)):
        b += b"\x8B\x42" + bytes([off]) + put(0x18 + 4 * i)          # mov eax, [edx+off]
    b += b"\x0F\xBF\x05" + u32(W.NATION) + put(0x28)
    b += b"\xA1" + u32(W.CTL) + put(0x2C)                            # sequence = count
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def stub(va):
    body = bytearray(b"\x8B\xC6")                                    # mov eax, esi
    body += b"\xE8" + W.rel32(va + len(body), AAB4)                  # call 0x44aab4
    body += b"\x9C\x60" + log_body() + b"\x61\x9D"
    body += b"\xE9" + W.rel32(va + len(body), BACK)
    return bytes(body)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    if bytes(b[W.off(SITE):W.off(SITE) + len(EXPECT)]) != EXPECT:
        raise SystemExit("0x%X holds %s, not %s" % (SITE, bytes(b[W.off(SITE):W.off(SITE) + 7]).hex(), EXPECT.hex()))
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
    code = stub(W.CAVES)
    b[raw(W.CAVES):raw(W.CAVES) + len(code)] = code
    b[W.off(SITE):W.off(SITE) + len(EXPECT)] = b"\xE9" + W.rel32(SITE, W.CAVES) + b"\x90" * (len(EXPECT) - 5)
    if W.CAVES + len(code) > W.CTL:
        raise SystemExit("caves overflow")
    return {hex(SITE): W.CAVES}


def decode(buf, n):
    out = []
    for i in range(n):
        kind, army, eax, _, _, _, a0, a4, a8, ac, nation, seq = struct.unpack_from("<12I", buf, i * REC)
        x, y = words(a0)
        owner, moves = words(a4)
        _, supplies = words(a8)
        _, morale = words(ac)
        out.append({"seq": seq, "nation": words(nation)[0], "kind": "aab4", "army": army, "aab4": eax & 0xFF,
                    "fallback": (eax & 0xFF) == 0, "x": x, "y": y, "owner": owner, "moves": moves, "supplies": supplies,
                    "morale": morale})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
