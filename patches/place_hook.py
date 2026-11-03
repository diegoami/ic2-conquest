#!/usr/bin/env python3
"""Placement hook (owner 2026-11-03, "1 and 2": the code-only callers of FUN_0044939c in play): an observation-only build of the
seed exe that logs every call of the tile finder FUN_0044939c(xy, mode, &out) and the tile it returns.

    python3 patches/place_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed placehook.exe"
    IC2_FLEET_HOOK=place_hook IC2_HOOK_LOG=place python3 -m difftest.probes.fleetphase_hook_run OUT TURNS START.SAV [...]

FUN_0044939c scans rings r = 0, 1, ... around xy, x outer and y inner from -r to +r, and stores every tile whose terrain is in
the mode's range (mode 0: codes 0-1, sea, minus the FUN_004496bc region; mode 1: codes 2-11, land) into out, so the LAST match
of the first ring with one wins (findings/2026-11-03-ptolemaic-longrun-positions.md §4). Its callers (return addresses): 0x44A0CF (a new fleet
launches, FUN_0044a050), 0x44B86A (an AI fleet unloads its army, FUN_0044b840, mode 1), 0x44E275 (a fleet route to a land
target, FUN_0044e1fc, mode 0).

Two probes, each saving and restoring EFLAGS and every general register (pushfd/pushad), so the game runs the same instructions:
  entry 0x44939C  the prologue `push ebx; push esi; push edi; push ebp; add esp,-0x1c` (7 bytes) moves into the stub
  exit  0x4494DB  `add esp,0x1c; pop ebp; pop edi` (5 bytes) moves into the stub
Record (40 bytes): +0 kind (1 entry, 2 exit), +4 the caller's return address, +8 xy (x low word, y high), +0xC mode (DL at entry,
the saved byte [esp+4] at exit), +0x10 EBX, +0x14 ESI (the callers keep the fleet index there: B840 in EBX, E1FC in ESI), +0x18 out
(exit only: the dword written to out, -1 when nothing), +0x1C nation 0x4A0320, +0x20 sequence, +0x24 0.
Log: CTL 0x565000 (+0 count, +4 'PLC1', +8 capacity), BUF 0x565100.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402
from decide_hook import words  # noqa: E402

MAGIC = 0x31434C50                      # 'PLC1'
DST = "Imperial Conquest 2 fast rollingsave seed placehook.exe"
REC, CAP = 40, 32768
ENTRY, ENTRY_BYTES = 0x44939C, bytes.fromhex("5356575583c4e4")
EXIT, EXIT_BYTES = 0x4494DB, bytes.fromhex("83c41c5d5f")
CALLERS = {0x44A0CF: "launch (A050)", 0x44B86A: "AI disembark (B840)"}
u32 = W.u32


def put(slot):
    return b"\x89\x41" + bytes([slot])   # mov [ecx+slot], eax


def log_body(kind):
    """After pushfd/pushad: [esp] = EDI ESI EBP ESP EBX EDX ECX EAX (+0..+0x1C), [esp+0x20] = EFLAGS. Entry: [esp+0x24] is the
    caller's return address. Exit (before `add esp,0x1c`): [esp+0x24] = the saved xy ([esp] of the frame), [esp+0x28] the mode
    byte, [esp+0x2C] the out pointer, [esp+0x24+0x1C+0x10] = [esp+0x50] the caller's return address."""
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)                                    # mov ecx, [CTL]
    b += b"\x81\xF9" + u32(CAP)                                      # cmp ecx, CAP
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([REC])                                  # imul ecx, ecx, REC
    b += b"\x81\xC1" + u32(W.BUF)                                    # add ecx, BUF
    b += b"\xC7\x01" + u32(kind)                                     # mov dword [ecx], kind
    if kind == 1:
        b += b"\x8B\x44\x24\x24" + put(4)                            # return address
        b += b"\x8B\x44\x24\x1C" + put(8)                            # saved EAX: xy
        b += b"\x0F\xB6\x44\x24\x14" + put(0x0C)                     # movzx eax, byte [esp+0x14]: saved DL, the mode
        b += b"\xC7\x41\x18" + u32(0xFFFFFFFF)                       # out: not yet
    else:
        b += b"\x8B\x44\x24\x50" + put(4)                            # return address
        b += b"\x8B\x44\x24\x24" + put(8)                            # xy
        b += b"\x0F\xB6\x44\x24\x28" + put(0x0C)                     # mode byte
        b += b"\x8B\x44\x24\x2C\x8B\x00" + put(0x18)                 # mov eax, [esp+0x2C]; mov eax, [eax]: *out
    b += b"\x8B\x44\x24\x10" + put(0x10)                             # saved EBX
    b += b"\x8B\x44\x24\x04" + put(0x14)                             # saved ESI
    b += b"\x0F\xBF\x05" + u32(W.NATION) + put(0x1C)
    b += b"\xA1" + u32(W.CTL) + put(0x20)                            # sequence = count
    b += b"\x31\xC0" + put(0x24)
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    for va, want in ((ENTRY, ENTRY_BYTES), (EXIT, EXIT_BYTES)):
        if bytes(b[W.off(va):W.off(va) + len(want)]) != want:
            raise SystemExit("0x%X holds %s, not %s" % (va, bytes(b[W.off(va):W.off(va) + 8]).hex(), want.hex()))
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
    for kind, (site, want) in ((1, (ENTRY, ENTRY_BYTES)), (2, (EXIT, EXIT_BYTES))):
        code = bytearray(b"\x9C\x60") + log_body(kind) + b"\x61\x9D" + want
        code += b"\xE9" + W.rel32(va + len(code), site + len(want))
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + len(want)] = b"\xE9" + W.rel32(site, va) + b"\x90" * (len(want) - 5)
        out[kind] = hex(va)
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("caves overflow: %#x" % va)
    return out


def decode(buf, n):
    out = []
    for i in range(n):
        kind, ret, xy, mode, ebx, esi, res, nation, seq, _ = struct.unpack_from("<10I", buf, i * REC)
        x, y = words(xy)
        r = {"seq": seq, "nation": words(nation)[0], "kind": {1: "entry", 2: "exit"}.get(kind, kind), "ret": hex(ret),
             "caller": CALLERS.get(ret, "E1FC fleet route" if 0x44E1FC <= ret < 0x44E300 else "other"),
             "at": [x, y], "mode": mode & 0xFF, "ebx": words(ebx)[0], "esi": words(esi)[0]}
        if kind == 2:
            r["out"] = list(words(res)) if words(res)[0] != -1 else None     # the finder writes -1 to the low word only
        out.append(r)
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
