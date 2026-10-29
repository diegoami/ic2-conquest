#!/usr/bin/env python3
"""The AI-fleet hook (imperial_conquest_2#1409, delegated by research 2026-10-30): an observation-only build of the seed exe that logs,
in memory, what the original's AI fleet move `FUN_0044e1fc` (fleet index in EAX, target point in EDX) does on each call.

    python3 patches/fleet_hook.py <game folder>    # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed fleethook.exe"

Disassembly (pinned seed build): the target is the dword [esp] of E1FC's frame, the route point the word pair [esp+4]; EBX points to
the fleet record (x, y at +0, moves at +0xC), ESI is the fleet index. Five probes:

  1  0x44E245  `call 0x44CB40` (the direct-line test) re-pointed to a stub that makes the call, then logs AL: the branch.
  2  0x44E287  after `call 0x44D174` (the route finder): `cmp word [esp+4],-1; jle` becomes `jmp stub`: log the returned point.
  3  0x44E2BB  after `call 0x44CEC8` (the no-progress fallback): `cmp word [esp+4],-1; je` the same way: log the fallback point.
  4  0x44E2FD  `call 0x44E1FC` (the recursion) re-pointed to a stub that logs and then jumps to E1FC.
  5  0x44E302  `mov edx,[ebx]; mov eax,[esp]` (the start of the arrival/contact part, after the moves and the recursion):
               `jmp stub`: log the position and moves after this call's walking.

Each stub saves and restores EFLAGS and all general registers (pushfd/pushad), then runs the replaced instructions unchanged: an
observation, not a change. A 40-byte record: +0 kind (1-5), +4 AL (kind 1) or 0, +8 target dword, +0xC fleet, +0x10 point dword
([esp+4]: D174's or CEC8's result; stale before the D174 branch writes it), +0x14 fleet x (lo) / y (hi), +0x18 moves, +0x1C
E1FC's return address, +0x20 current nation, +0x24 sequence. The log lives in the grown `.patch` section (CTL 0x565000: +0 count,
+4 magic 'FLT1', +8 capacity; BUF 0x565100), exactly like patches/walk_hook.py.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

MAGIC = 0x31544C46                      # 'FLT1'
DST = "Imperial Conquest 2 fast rollingsave seed fleethook.exe"
P1, P2, P3, P4, P5 = 0x44E245, 0x44E287, 0x44E2BB, 0x44E2FD, 0x44E302
EXPECT = {P1: bytes.fromhex("e8f6e8ffff"), P2: bytes.fromhex("66837c2404ff7e0b"), P3: bytes.fromhex("66837c2404ff740b"),
          P4: bytes.fromhex("e8fafeffff"), P5: bytes.fromhex("8b138b0424")}
CALL_SITES = {0x44E2FD: "recursion"}   # key: call address = return address - 5; others print as the hex return address
u32 = W.u32


def log_body(kind, d):
    """pushfd/pushad already done; E1FC's frame starts at [esp+d]. Writes one record and bumps the count."""
    body = bytearray()
    body += b"\x8B\x0D" + u32(W.CTL)                        # mov ecx, [CTL]
    body += b"\x81\xF9" + u32(W.CAP)                        # cmp ecx, CAP
    jae_at = len(body); body += b"\x0F\x83\0\0\0\0"         # jae skip
    body += b"\x89\xCA"                                     # mov edx, ecx (sequence)
    body += b"\x6B\xC9" + bytes([W.REC])                    # imul ecx, ecx, REC
    body += b"\x81\xC1" + u32(W.BUF)                        # add ecx, BUF
    body += b"\xC7\x01" + u32(kind)                         # mov dword [ecx], kind
    body += (b"\x0F\xB6\x44\x24\x1C" if kind == 1 else b"\x31\xC0")   # movzx eax, byte [esp+0x1C] (saved AL) / xor eax, eax
    body += b"\x89\x41\x04"                                 # mov [ecx+4], eax
    body += b"\x8B\x44\x24" + bytes([d]) + b"\x89\x41\x08"  # mov eax, [esp+d]: target
    body += b"\x8B\x44\x24\x04"                             # mov eax, [esp+4] = saved ESI (pushad order: EDI, ESI, EBP, ESP, EBX, ...)
    body += b"\x89\x41\x0C"                                 # mov [ecx+0xC], eax: fleet index
    body += b"\x8B\x44\x24" + bytes([d + 4]) + b"\x89\x41\x10"   # mov eax, [esp+d+4]: point
    body += b"\x8B\x03\x89\x41\x14"                         # mov eax, [ebx]; mov [ecx+0x14], eax
    body += b"\x0F\xBF\x43\x0C\x89\x41\x18"                 # movsx eax, word [ebx+0xC]; mov [ecx+0x18], eax
    body += b"\x8B\x44\x24" + bytes([d + 24]) + b"\x89\x41\x1C"  # mov eax, [esp+d+24]: E1FC's return address
    body += b"\x0F\xBF\x05" + u32(W.NATION) + b"\x89\x41\x20"
    body += b"\x89\x51\x24"                                 # mov [ecx+0x24], edx
    body += b"\xFF\x05" + u32(W.CTL)                        # inc dword [CTL]
    body[jae_at + 2:jae_at + 6] = struct.pack("<i", len(body) - (jae_at + 6))
    return bytes(body)


def stub_call(va, kind, callee, then_jump):
    """Entered by `call`: [esp] is the return address, so E1FC's frame is at +4 (+36 after pushfd/pushad)."""
    if then_jump:                                           # log, then tail-jump to the callee (the return address stays)
        body = bytearray(b"\x9C\x60") + log_body(kind, 40) + b"\x61\x9D"
        body += b"\xE9" + W.rel32(va + len(body), callee)
    else:                                                   # make the call, then log its AL
        body = bytearray(b"\xE8" + W.rel32(va, callee))
        body += b"\x9C\x60" + log_body(kind, 40) + b"\x61\x9D\xC3"
    return bytes(body)


def stub_jmp(va, kind, tail):
    body = bytearray(b"\x9C\x60") + log_body(kind, 36) + b"\x61\x9D"
    for ins, target in tail:
        if target is None:
            body += ins
        else:                                               # a rel32 jump: ins is its opcode bytes
            body += ins + struct.pack("<i", target - (va + len(body) + len(ins) + 4))
    return bytes(body)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    if any(x != 0xCC for x in b[W.PATCH_RAW + (W.CAVES - W.PATCH_VA):W.PATCH_RAW + W.SEED_PATCH_SIZE]):
        raise SystemExit("the .patch space from 0x%X is not free" % W.CAVES)
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
    CMP = b"\x66\x83\x7C\x24\x04\xFF"                       # cmp word [esp+4], -1
    stubs = {
        P1: lambda v: stub_call(v, 1, 0x44CB40, False),
        P2: lambda v: stub_jmp(v, 2, [(CMP, None), (b"\x0F\x8E", 0x44E29A), (b"\xE9", 0x44E28F)]),
        P3: lambda v: stub_jmp(v, 3, [(CMP, None), (b"\x0F\x84", 0x44E2CE), (b"\xE9", 0x44E2C3)]),
        P4: lambda v: stub_call(v, 4, 0x44E1FC, True),
        P5: lambda v: stub_jmp(v, 5, [(b"\x8B\x13\x8B\x04\x24", None), (b"\xE9", 0x44E307)]),
    }
    va, out = W.CAVES, {}
    for site, make in stubs.items():
        code = make(va)
        b[raw(va):raw(va) + len(code)] = code
        n = len(EXPECT[site])
        op = b"\xE8" if site in (P1, P4) else b"\xE9"
        b[W.off(site):W.off(site) + n] = op + W.rel32(site, va) + b"\x90" * (n - 5)
        out[hex(site)] = va
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("caves overflow into the control block")
    return out


KINDS = {1: "entry_direct_test", 2: "d174_point", 3: "cec8_point", 4: "recursion", 5: "after_moves"}


def decode(buf, n):
    s16 = lambda v, hi: struct.unpack("<h", u32(v)[2 * hi:2 * hi + 2])[0]
    out = []
    for i in range(n):
        kind, al, target, fleet, point, xy, moves, ret, nation, seq = struct.unpack_from("<IIIiIIiIiI", buf, i * W.REC)
        out.append({"seq": seq, "kind": KINDS.get(kind, kind), "direct": al if kind == 1 else None, "fleet": fleet,
                    "target": [s16(target, 0), s16(target, 1)], "point": [s16(point, 0), s16(point, 1)],
                    "x": s16(xy, 0), "y": s16(xy, 1), "moves": moves, "caller": CALL_SITES.get(ret - 5, hex(ret)), "nation": nation})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    b = bytearray((folder / W.SRC).read_bytes())
    caves = build(b)
    (folder / DST).write_bytes(bytes(b))
    print("wrote", folder / DST, caves)
