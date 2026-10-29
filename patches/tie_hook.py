#!/usr/bin/env python3
"""The enemy-pick hook (research #117 follow-up, owner 2026-10-30): an observation-only build of the seed exe that logs every
candidate the AI's enemy-army pick `FUN_0044ee60` scores, so ties broken by table order can be counted in real AI turns.

    python3 patches/tie_hook.py <game folder>     # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed tiehook.exe"

Disassembly (pinned seed build): the actor is [ebp-2], the candidate index [ebp-0xE], its distance [ebp-0x1C]; the final score
is in EDI at 0x44EF79; the current best score is the word at [[ebp-0xC]] and the best index the word at [[ebp-8]]. Probes:

  1  0x44EF79  `mov eax,[ebp-0xc]; movsx eax,word [eax]` (6 bytes) becomes `jmp stub; nop`: log the candidate, then run the
               two instructions and jump back to 0x44EF7F (the `cmp edi, eax` that keeps only a strictly greater score).
  2  0x44EFB1  `mov eax,[ebp+8]; mov ax,word [eax]` (6 bytes), the loop's exit: log the chosen index and its score.

Each stub saves and restores EFLAGS and all general registers (pushfd/pushad), then runs the replaced instructions unchanged.
A 40-byte record: +0 kind (1 candidate, 2 chosen), +4 actor, +8 candidate (1) or chosen index (2), +0xC score (EDI for 1,
the best score for 2), +0x10 distance, +0x14 best score before this candidate, +0x18 best index before it, +0x1C the return
address of FUN_0044ee60, +0x20 current nation, +0x24 sequence. Log: CTL 0x565000 (+0 count, +4 'TIE1', +8 capacity),
BUF 0x565100, the layout of patches/walk_hook.py.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

MAGIC = 0x31454954                      # 'TIE1'
DST = "Imperial Conquest 2 fast rollingsave seed tiehook.exe"
P1, P2 = 0x44EF79, 0x44EFB1
EXPECT = {P1: bytes.fromhex("8b45f40fbf00"), P2: bytes.fromhex("8b4508668b00")}
u32 = W.u32


def log_body(kind):
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)                           # mov ecx, [CTL]
    b += b"\x81\xF9" + u32(W.CAP)                           # cmp ecx, CAP
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x89\xCA"                                        # mov edx, ecx
    b += b"\x6B\xC9" + bytes([W.REC])                       # imul ecx, ecx, REC
    b += b"\x81\xC1" + u32(W.BUF)                           # add ecx, BUF
    b += b"\xC7\x01" + u32(kind)
    b += b"\x0F\xBF\x45\xFE\x89\x41\x04"                    # movsx eax, word [ebp-2]: actor
    if kind == 1:
        b += b"\x0F\xBF\x45\xF2\x89\x41\x08"                # movsx eax, word [ebp-0xe]: candidate
        b += b"\x8B\x04\x24\x89\x41\x0C"                    # mov eax, [esp] (saved EDI = the score); mov [ecx+0xc], eax
        b += b"\x8B\x45\xE4\x89\x41\x10"                    # mov eax, [ebp-0x1c]: distance
    else:
        b += b"\x8B\x45\xF8\x0F\xBF\x00\x89\x41\x08"        # mov eax,[ebp-8]; movsx eax, word [eax]: chosen
        b += b"\x8B\x45\xF4\x0F\xBF\x00\x89\x41\x0C"        # best score
        b += b"\x8B\x45\x08\x0F\xBF\x00\x89\x41\x10"        # best distance ([[ebp+8]])
    b += b"\x8B\x45\xF4\x0F\xBF\x00\x89\x41\x14"            # best score so far
    b += b"\x8B\x45\xF8\x0F\xBF\x00\x89\x41\x18"            # best index so far
    b += b"\x8B\x45\x04\x89\x41\x1C"                        # return address
    b += b"\x0F\xBF\x05" + u32(W.NATION) + b"\x89\x41\x20"
    b += b"\x89\x51\x24"
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
    for site, kind, back in ((P1, 1, 0x44EF7F), (P2, 2, 0x44EFB7)):
        code = stub(va, kind, EXPECT[site], back)
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + 6] = b"\xE9" + W.rel32(site, va) + b"\x90"
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("caves overflow")
    return out


def decode(buf, n):
    out = []
    for i in range(n):
        kind, actor, cand, score, dist, best, besti, ret, nation, seq = struct.unpack_from("<Iiiiiiiiii", buf, i * W.REC)
        out.append({"seq": seq, "kind": {1: "candidate", 2: "chosen"}.get(kind, kind), "actor": actor, "index": cand,
                    "score": score, "distance": dist, "best_before": best, "best_index_before": besti, "ret": hex(ret & 0xFFFFFFFF),
                    "nation": nation})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    b = bytearray((folder / W.SRC).read_bytes())
    print(build(b))
    (folder / DST).write_bytes(bytes(b))
