#!/usr/bin/env python3
"""The capital-defence hook (research #123, delegated 2026-10-30): an observation-only build of the seed exe that logs the AI
capital defence FUN_0044efc8 (the homeland intercept): every threat put on its list, every listed threat a responder
compares, and every threat it accepts as the nearest.

    python3 patches/capdef_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed capdefhook.exe"

Disassembly (pinned seed build), frame words of FUN_0044efc8: [esp] the record index of the loop, [esp+2] the threat count,
[esp+6] the responder's distance to the capital, [esp+8] the best distance so far, [esp+0xA] the best threat. Probes, each
one 5-byte instruction replaced by `jmp stub` (the stub runs it, then jumps back):

  1  0x44F0A5  `movsx eax, word [esp+2]`: a threat is appended. Logs its record and the count before it (a count of 9
               means it overwrites the uncounted tenth slot: the list keeps the first 9 threats in table order).
  2  0x44F226  `cmp ax, [esp+8]`: a responder compares a listed threat. Logs the responder, the threat (SI), its distance
               (AX), the best so far, the threat's owner, the current nation's relation to that owner, and the responder's
               distance to the capital.
  3  0x44F273  `mov [esp+8], ax`: the threat is accepted as the nearest so far.

Each stub saves and restores EFLAGS and all general registers (pushfd/pushad). A 40-byte record: +0 kind, +4 a, +8 b, +0xC c,
+0x10 d, +0x14 e, +0x18 f, +0x1C g, +0x20 nation, +0x24 sequence (meanings in decode()). Log: CTL 0x565000 (+0 count,
+4 'CAP1', +8 capacity), BUF 0x565100, the layout of patches/walk_hook.py.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

MAGIC = 0x31504143                      # 'CAP1'
DST = "Imperial Conquest 2 fast rollingsave seed capdefhook.exe"
P1, P2, P3 = 0x44F0A5, 0x44F226, 0x44F273
EXPECT = {P1: bytes.fromhex("0fbf442402"), P2: bytes.fromhex("663b442408"), P3: bytes.fromhex("6689442408")}
u32 = W.u32
FB = 36                                  # E FC8's esp = the stub's esp + 36 after pushfd/pushad


def fw(off):
    """movsx eax, word [esp + FB + off]"""
    return b"\x0F\xBF\x44\x24" + bytes([FB + off])


def put(slot):
    return b"\x89\x41" + bytes([slot])   # mov [ecx+slot], eax


def log_body(kind):
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)
    b += b"\x81\xF9" + u32(W.CAP)
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x89\xCA"
    b += b"\x6B\xC9" + bytes([W.REC])
    b += b"\x81\xC1" + u32(W.BUF)
    b += b"\xC7\x01" + u32(kind)
    if kind == 1:
        b += fw(0) + put(4) + fw(2) + put(8)                         # threat record, count before
    else:
        b += fw(0) + put(4)                                          # responder
        b += b"\x0F\xBF\x44\x24\x04" + put(8)                        # movsx eax, word [esp+4] (saved ESI): the threat
        b += b"\x0F\xBF\x44\x24\x1C" + put(12)                       # movsx eax, word [esp+0x1c] (saved AX): its distance
        b += fw(8) + put(16)                                         # best so far
        b += b"\x0F\xBF\x44\x24\x04"                                 # threat index
        b += b"\x69\xC0\x90\x02\x00\x00"                             # imul eax, eax, 0x290
        b += b"\x0F\xBF\x80" + u32(0x47C1F0) + put(20)               # movsx eax, word [eax+0x47c1f0]: owner
        b += b"\x0F\xBF\x15" + u32(W.NATION)                         # movsx edx, word [nation]
        b += b"\x69\xD2\x94\x04\x00\x00"                             # imul edx, edx, 0x494
        b += b"\x8D\x14\x42"                                         # lea edx, [edx + eax*2]
        b += b"\x0F\xBF\x82" + u32(0x474696) + put(24)               # movsx eax, word [edx+0x474696]: relation
        b += fw(6) + put(28)                                         # responder's distance to the capital
    b += b"\x0F\xBF\x05" + u32(W.NATION) + put(0x20)
    b += b"\x8B\x0D" + u32(W.CTL)                                    # reload ecx: the base of this record
    b += b"\x6B\xC9" + bytes([W.REC]) + b"\x81\xC1" + u32(W.BUF)
    b += b"\x8B\x15" + u32(W.CTL) + b"\x89\x51\x24"                  # sequence = count
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
    for site, kind in ((P1, 1), (P2, 2), (P3, 3)):
        code = stub(va, kind, EXPECT[site], site + 5)
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + 5] = b"\xE9" + W.rel32(site, va)
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("caves overflow")
    return out


def decode(buf, n):
    out = []
    for i in range(n):
        kind, a, b_, c, d, e, f, g, nation, seq = struct.unpack_from("<10i", buf, i * W.REC)
        if kind == 1:
            out.append({"seq": seq, "kind": "threat", "nation": nation, "threat": a, "count_before": b_})
        else:
            out.append({"seq": seq, "kind": "compare" if kind == 2 else "accept", "nation": nation, "responder": a,
                        "threat": b_, "distance": c, "best_before": d, "threat_owner": e, "relation": f,
                        "responder_to_capital": g})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
