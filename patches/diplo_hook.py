#!/usr/bin/env python3
"""The relation-setter hook (diplomacy comparison with remake main, owner 2026-10-30): an observation-only build of the seed
exe that logs every call of FUN_00449b40, the setter every relation write between two nations goes through (22 callers:
the AI diplomacy phase FUN_0044fb7c, the treaty FUN_00450c68 after an instant battle, the human Politics screen, the
offer roll, elimination and others; research decompiled-war-cascade-and-peace-paths.md §1).

    python3 patches/diplo_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed diplohook.exe"

Entry of FUN_00449b40 (pinned seed build): AX = nation a, DX = nation b, CX = the new state (0 peace, 1 trade, 2 alliance,
3 war; the setter itself maps 0 over a trade/alliance/war to the cooldown -8/-24/-18). The first 6 bytes
(`push ebp; mov ebp,esp; add esp,-12`) become `jmp stub; nop`: the stub logs, then runs those three instructions and
jumps back to 0x449B46. The cascade's direct stores inside the setter (allies and enemies of b) are not separate calls;
they show in the relation matrix.

Three more probes in the AI diplomacy phase FUN_0044fb7c:
  2  0x44FD22  `cmp word [esp+8],-1` (6 bytes): the war candidate. Logs [esp+8] (the candidate, -1 = none), EBP (its
               power ratio), the frame dwords [esp] (busy bytes at +1/+2) and [esp+4] (the trade counts at +4/+6).
  3  0x44FD2F  `call Random` (Random(10), the war roll): the stub makes the call itself, then logs EAX (the draw).
  4  0x44FD61  `call Random` (Random(20), the alliance-search roll): the same.

A 40-byte record: +0 kind (1), +4 a, +8 b, +0xC state, +0x10 rel[a][b] before the call, +0x14 the return address (the
caller), +0x18 the current nation (0x4A0320), +0x1C the week word 0x4A0330, +0x20 reserved, +0x24 sequence. Kind 2: +4 candidate, +8 ratio, +0xC [esp], +0x10
[esp+4]; kinds 3/4: +4 the draw; +0x18 nation, +0x1C week as for kind 1. Log: CTL
0x565000 (+0 count, +4 'DIP1', +8 capacity), BUF 0x565100, the layout of patches/walk_hook.py. The stub saves and restores
EFLAGS and all general registers (pushfd/pushad).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

MAGIC = 0x31504944                      # 'DIP1'
DST = "Imperial Conquest 2 fast rollingsave seed diplohook.exe"
SITE = 0x449B40
EXPECT = bytes.fromhex("558bec83c4f4")
REL = 0x474696                          # rel[a][b] = REL + a*0x494 + b*2
WEEK = 0x4A0330
u32 = W.u32
CALLERS = {0x44682D: "4467xx", 0x446916: "4468xx", 0x446B00: "446Axx", 0x44C149: "44C1xx", 0x44C450: "44C4xx",
           0x44C68B: "44C6xx", 0x44C9FF: "44C9xx", 0x44FD0C: "ai_diplomacy", 0x44FD47: "ai_diplomacy",
           0x44FE5A: "ai_diplomacy", 0x44FEEF: "ai_diplomacy", 0x44FF7E: "ai_diplomacy", 0x44FF8F: "ai_diplomacy",
           0x450D72: "treaty", 0x450F3F: "treaty", 0x450FBF: "treaty", 0x450FE8: "treaty", 0x45106C: "treaty",
           0x451095: "treaty", 0x451FB5: "451Bxx", 0x4532B8: "politics_ok", 0x453338: "politics_ok"}


P2, P3, P4 = 0x44FD22, 0x44FD2F, 0x44FD61
EXPECT2 = bytes.fromhex("66837c2408ff")
RANDOM = 0x40284C
FB = 36                                  # FB7C's esp = the stub's esp + 36 after pushfd/pushad


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


def body_candidate():
    b, jae = head(2)
    b += b"\x0F\xBF\x44\x24" + bytes([FB + 8]) + b"\x89\x41\x04"     # movsx eax, word [F+8]: candidate
    b += b"\x8B\x44\x24\x08\x89\x41\x08"                              # mov eax, [esp+8] (saved EBP): ratio
    b += b"\x8B\x44\x24" + bytes([FB]) + b"\x89\x41\x0C"              # [F+0]
    b += b"\x8B\x44\x24" + bytes([FB + 4]) + b"\x89\x41\x10"          # [F+4]
    return tail(b, jae)


def body_draw(kind):
    b, jae = head(kind)
    b += b"\x8B\x44\x24\x1C\x89\x41\x04"                              # mov eax, [esp+0x1c] (saved EAX): the draw
    return tail(b, jae)


def log_body():
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)                                    # mov ecx, [count]
    b += b"\x81\xF9" + u32(W.CAP)
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([W.REC])
    b += b"\x81\xC1" + u32(W.BUF)                                    # ecx = record
    b += b"\xC7\x01" + u32(1)
    b += b"\x0F\xBF\x44\x24\x1C\x89\x41\x04"                         # movsx eax, word [esp+0x1c] (saved EAX): a
    b += b"\x0F\xBF\x54\x24\x14\x89\x51\x08"                         # movsx edx, word [esp+0x14] (saved EDX): b
    b += b"\x0F\xBF\x5C\x24\x18\x89\x59\x0C"                         # movsx ebx, word [esp+0x18] (saved ECX): state
    b += b"\x69\xC0\x94\x04\x00\x00"                                 # imul eax, eax, 0x494
    b += b"\x8D\x04\x50"                                             # lea eax, [eax + edx*2]
    b += b"\x0F\xBF\x80" + u32(REL) + b"\x89\x41\x10"                # movsx eax, word [eax+REL]: rel[a][b] before
    b += b"\x8B\x44\x24\x24\x89\x41\x14"                             # mov eax, [esp+0x24] (return address)
    b += b"\x0F\xBF\x05" + u32(W.NATION) + b"\x89\x41\x18"
    b += b"\x0F\xBF\x05" + u32(WEEK) + b"\x89\x41\x1C"
    b += b"\xA1" + u32(W.CTL) + b"\x89\x41\x24"                      # sequence = count
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    if bytes(b[W.off(SITE):W.off(SITE) + 6]) != EXPECT:
        raise SystemExit("0x%X holds %s" % (SITE, bytes(b[W.off(SITE):W.off(SITE) + 6]).hex()))
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
    for site, want in ((P2, EXPECT2), (P3, b"\xE8" + W.rel32(P3, RANDOM)), (P4, b"\xE8" + W.rel32(P4, RANDOM))):
        if bytes(b[W.off(site):W.off(site) + len(want)]) != want:
            raise SystemExit("0x%X holds %s" % (site, bytes(b[W.off(site):W.off(site) + len(want)]).hex()))
    va, out = W.CAVES, {}

    def place(site, code, length):
        nonlocal va
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + length] = b"\xE9" + W.rel32(site, va) + b"\x90" * (length - 5)
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15

    body = bytearray(b"\x9C\x60") + log_body() + b"\x61\x9D" + EXPECT
    body += b"\xE9" + W.rel32(va + len(body), SITE + 6)
    place(SITE, bytes(body), 6)
    body = bytearray(b"\x9C\x60") + body_candidate() + b"\x61\x9D" + EXPECT2
    body += b"\xE9" + W.rel32(va + len(body), P2 + 6)
    place(P2, bytes(body), 6)
    for site, kind in ((P3, 3), (P4, 4)):
        body = bytearray(b"\xE8" + W.rel32(va, RANDOM))                    # the original call, made from the stub
        body += b"\x9C\x60" + body_draw(kind) + b"\x61\x9D"
        body += b"\xE9" + W.rel32(va + len(body), site + 5)
        place(site, bytes(body), 5)
    if va > W.CTL:
        raise SystemExit("cave overflow")
    return out


def decode(buf, n):
    out = []
    for i in range(n):
        kind, a, b_, state, before, ret, nation, week, _, seq = struct.unpack_from("<10i", buf, i * W.REC)
        if kind == 1:
            site = (ret & 0xFFFFFFFF) - 5
            out.append({"seq": seq, "kind": "write", "a": a, "b": b_, "state": state, "before": before,
                        "caller": CALLERS.get(site, hex(site)), "site": hex(site), "nation": nation, "week": week})
        elif kind == 2:
            f0, f4 = state & 0xFFFFFFFF, before & 0xFFFFFFFF
            out.append({"seq": seq, "kind": "war_candidate", "candidate": struct.unpack("<h", struct.pack("<H", a & 0xFFFF))[0],
                        "ratio": b_, "busy_self": (f0 >> 8) & 0xFF, "busy_other": (f0 >> 16) & 0xFF,
                        "trades_self": struct.unpack("<h", struct.pack("<H", f4 & 0xFFFF))[0],
                        "trades_other": struct.unpack("<h", struct.pack("<H", f4 >> 16))[0], "nation": nation, "week": week})
        else:
            out.append({"seq": seq, "kind": "war_roll" if kind == 3 else "alliance_roll", "draw": a,
                        "hit": a == 0, "nation": nation, "week": week})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
