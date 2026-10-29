#!/usr/bin/env python3
"""The army-step hook (research #42, delegated 2026-10-30): an observation-only build of the seed exe that logs every call of the
army step FUN_0044d420, so a walk's crossed tiles are seen in play, not only its endpoint.

    python3 patches/step_hook.py <game folder>     # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed stephook.exe"

FUN_0044d420 is a nested step of the army walker FUN_0044d734 and receives the walker's frame pointer P as its stack argument
([esp+4] at entry). The walker keeps the army index at word [P-6], its line cursor at [P-2]/[P-4] (x, y: the cell the step
is about to take, or the army's own cell at the start) and the target at dword [P-0xa].

Probe: the 6-byte prologue at 0x44D420 (`push ebp; mov ebp,esp; add esp,-0xc`) becomes `jmp stub; nop`. The stub saves EFLAGS
and every register, writes a 32-byte record, restores them, runs the same prologue and jumps to 0x44D426. Record: +0 army,
+2 army x, +4 army y, +6 moves (the army record before the step), +8 cursor x, +0xA cursor y, +0xC target dword, +0x10 return
address (the walker's call site), +0x14 current nation, +0x18 sequence. Log: CTL 0x565000 (+0 count, +4 'STP1', +8 capacity),
BUF 0x565100.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402  (shares the section layout and helpers)

REC, CAP = 32, 131072
MAGIC = 0x31505453                      # 'STP1'
SRC = W.SRC
DST = "Imperial Conquest 2 fast rollingsave seed stephook.exe"
SITE = 0x44D420
EXPECT = bytes.fromhex("558bec83c4f4")
ARMIES = 0x47C1EC


def stub(va):
    u32 = W.u32
    body = bytearray(b"\x9C\x60")                          # pushfd; pushad   (then [esp+0x24] = ret, [esp+0x28] = P)
    body += b"\x8B\x0D" + u32(W.CTL)                       # mov ecx, [CTL]
    body += b"\x81\xF9" + u32(CAP)                         # cmp ecx, CAP
    jae_at = len(body); body += b"\x0F\x83\0\0\0\0"
    body += b"\x89\xCF"                                    # mov edi, ecx (sequence)
    body += b"\xC1\xE1\x05"                                # shl ecx, 5 (x32)
    body += b"\x81\xC1" + u32(W.BUF)                       # add ecx, BUF
    body += b"\x8B\x74\x24\x28"                            # mov esi, [esp+0x28]  (P)
    body += b"\x0F\xBF\x46\xFA"                            # movsx eax, word [esi-6]  (army)
    body += b"\x66\x89\x01"                                # mov [ecx], ax
    body += b"\x69\xC0" + u32(0x290)                       # imul eax, eax, 0x290
    body += b"\x8B\x90" + u32(ARMIES) + b"\x89\x51\x02"    # mov edx, [eax+ARMIES]; mov [ecx+2], edx  (x, y)
    body += b"\x66\x8B\x90" + u32(ARMIES + 6) + b"\x66\x89\x51\x06"   # mov dx, [eax+ARMIES+6]; mov [ecx+6], dx (moves)
    body += b"\x66\x8B\x46\xFE\x66\x89\x41\x08"            # mov ax, [esi-2]; mov [ecx+8], ax  (cursor x)
    body += b"\x66\x8B\x46\xFC\x66\x89\x41\x0A"            # mov ax, [esi-4]; mov [ecx+0xA], ax (cursor y)
    body += b"\x8B\x46\xF6\x89\x41\x0C"                    # mov eax, [esi-0xa]; mov [ecx+0xC], eax (target)
    body += b"\x8B\x44\x24\x24\x89\x41\x10"                # mov eax, [esp+0x24]; mov [ecx+0x10], eax (return address)
    body += b"\x0F\xBF\x05" + u32(W.NATION) + b"\x89\x41\x14"
    body += b"\x89\x79\x18"                                # mov [ecx+0x18], edi
    body += b"\xFF\x05" + u32(W.CTL)
    body[jae_at + 2:jae_at + 6] = struct.pack("<i", len(body) - (jae_at + 6))
    body += b"\x61\x9D"                                    # popad; popfd
    body += EXPECT                                         # the displaced prologue
    body += b"\xE9" + W.rel32(va + len(body), SITE + 6)    # jmp 0x44D426
    return bytes(body)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    if bytes(b[W.off(SITE):W.off(SITE) + 6]) != EXPECT:
        raise SystemExit("0x%X does not hold the expected prologue" % SITE)
    hdr = 0x1F8 + 8 * 40
    vsize = W.BUF + CAP * REC - W.PATCH_VA
    struct.pack_into("<I", b, hdr + 8, vsize)
    struct.pack_into("<I", b, hdr + 16, W.RAW_SIZE)
    struct.pack_into("<I", b, hdr + 36, struct.unpack_from("<I", b, hdr + 36)[0] | 0x80000000)
    struct.pack_into("<I", b, 0x118 + 56, (W.PATCH_VA - W.BASE + vsize + 0xFFF) & ~0xFFF)
    b += b"\xCC" * (W.CTL - W.PATCH_VA - W.SEED_PATCH_SIZE) + bytes(W.RAW_SIZE - (W.CTL - W.PATCH_VA))
    raw = lambda va: W.PATCH_RAW + (va - W.PATCH_VA)
    b[raw(W.CTL + 4):raw(W.CTL + 8)] = W.u32(MAGIC)
    b[raw(W.CTL + 8):raw(W.CTL + 12)] = W.u32(CAP)
    code = stub(W.CAVES)
    b[raw(W.CAVES):raw(W.CAVES) + len(code)] = code
    b[W.off(SITE):W.off(SITE) + 6] = b"\xE9" + W.rel32(SITE, W.CAVES) + b"\x90"
    return W.CAVES


def decode(buf, n):
    out = []
    for i in range(n):
        army, x, y, moves, cx, cy, tgt, ret, nation, seq = struct.unpack_from("<hhhhhhIIiI", buf, i * REC)
        out.append({"seq": seq, "army": army, "x": x, "y": y, "moves": moves, "cursor": [cx, cy],
                    "target": [struct.unpack("<h", W.u32(tgt)[:2])[0], struct.unpack("<h", W.u32(tgt)[2:])[0]],
                    "call_site": hex(ret - 5), "nation": nation})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    b = bytearray((folder / SRC).read_bytes())
    build(b)
    (folder / DST).write_bytes(bytes(b))
    print("wrote", folder / DST)
