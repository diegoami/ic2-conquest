#!/usr/bin/env python3
"""E1FC hook (owner 2026-11-03, item 2 "gap C"): an observation-only build of the seed exe that logs, inside the AI fleet route
FUN_0044e1fc(fleet, target), the sea tile its land target is replaced with and the result of the path step FUN_0044d174, which
decides whether the fleet walks at all (`cmp word [esp+4],-1; jle 0x44E29A` skips FUN_0044e094).

    python3 patches/e1fc_hook.py <game folder>   # reads "Imperial Conquest 2 fast rollingsave seed.exe", writes "... seed e1fchook.exe"
    IC2_FLEET_HOOK=e1fc_hook IC2_HOOK_LOG=e1fc python3 -m difftest.probes.fleetphase_hook_run OUT TURNS START.SAV [...]

E1FC's frame: ESI = the fleet index, EBX = its record (x, y at +0; moves at +0xC), BP = its moves at entry, [esp] = the target,
[esp+4] = local_14 (the replaced target, then D174's result). Two probes, both after E1FC's frame is set up (so they do not write
where E1FC's own locals lie; each saves and restores EFLAGS and every general register):
  1  0x44E275  after `call 0x44939c` (the land target replaced by a sea tile): `lea eax,[esp+4]; push eax` (5 bytes) move into
               the stub; logs [esp+4], the replaced target
  2  0x44E287  after `call 0x44d174`: `cmp word [esp+4],-1` (6 bytes) moves into the stub, which returns to the `jle` at
               0x44E28D with the flags of that cmp; logs [esp+4], D174's result (x low word; -1 = no walk)
Record (40 bytes): +0 kind, +4 fleet index (ESI), +8 the fleet's x|y ([EBX]), +0xC its moves now ([EBX+0xC]), +0x10 BP (moves at
E1FC's entry), +0x14 the target ([esp]), +0x18 the logged value ([esp+4]), +0x1C nation 0x4A0320, +0x20 sequence, +0x24 0.
Log: CTL 0x565000 (+0 count, +4 'E1FC', +8 capacity), BUF 0x565100.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402
from decide_hook import words  # noqa: E402

MAGIC = 0x43463145                      # 'E1FC'
DST = "Imperial Conquest 2 fast rollingsave seed e1fchook.exe"
REC, CAP = 40, 32768
SITES = {1: (0x44E275, bytes.fromhex("8d44240450"), 0x44E27A),
         2: (0x44E287, bytes.fromhex("66837c2404ff"), 0x44E28D)}
NAMES = {1: "replaced target", 2: "D174 result"}
u32 = W.u32


def put(slot):
    return b"\x89\x41" + bytes([slot])   # mov [ecx+slot], eax


def log_body(kind):
    """After pushfd/pushad: [esp] = EDI ESI EBP ESP EBX EDX ECX EAX (+0..+0x1C), [esp+0x20] = EFLAGS, [esp+0x24] = E1FC's
    [esp] (the target), [esp+0x28] = E1FC's [esp+4]."""
    b = bytearray()
    b += b"\x8B\x0D" + u32(W.CTL)                                    # mov ecx, [CTL]
    b += b"\x81\xF9" + u32(CAP)                                      # cmp ecx, CAP
    jae = len(b); b += b"\x0F\x83\0\0\0\0"
    b += b"\x6B\xC9" + bytes([REC])                                  # imul ecx, ecx, REC
    b += b"\x81\xC1" + u32(W.BUF)                                    # add ecx, BUF
    b += b"\xC7\x01" + u32(kind)                                     # mov dword [ecx], kind
    b += b"\x8B\x44\x24\x04" + put(4)                                # saved ESI: fleet index
    b += b"\x8B\x44\x24\x10\x8B\x00" + put(8)                        # mov eax,[saved EBX]; mov eax,[eax]: x|y
    b += b"\x8B\x44\x24\x10\x0F\xBF\x40\x0C" + put(0x0C)             # movsx eax, word [EBX+0xC]: moves now
    b += b"\x0F\xBF\x44\x24\x08" + put(0x10)                         # movsx eax, word [saved EBP]: BP, moves at entry
    b += b"\x8B\x44\x24\x24" + put(0x14)                             # the target
    b += b"\x8B\x44\x24\x28" + put(0x18)                             # [esp+4] of E1FC
    b += b"\x0F\xBF\x05" + u32(W.NATION) + put(0x1C)
    b += b"\xA1" + u32(W.CTL) + put(0x20)                            # sequence = count
    b += b"\x31\xC0" + put(0x24)
    b += b"\xFF\x05" + u32(W.CTL)
    b[jae + 2:jae + 6] = struct.pack("<i", len(b) - (jae + 6))
    return bytes(b)


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d" % len(b))
    for site, want, _ in SITES.values():
        if bytes(b[W.off(site):W.off(site) + len(want)]) != want:
            raise SystemExit("0x%X holds %s, not %s" % (site, bytes(b[W.off(site):W.off(site) + 8]).hex(), want.hex()))
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
    for kind, (site, want, back) in SITES.items():
        code = bytearray(b"\x9C\x60") + log_body(kind) + b"\x61\x9D" + want
        code += b"\xE9" + W.rel32(va + len(code), back)
        b[raw(va):raw(va) + len(code)] = code
        b[W.off(site):W.off(site) + len(want)] = b"\xE9" + W.rel32(site, va) + b"\x90" * (len(want) - 5)
        out[NAMES[kind]] = hex(va)
        va = (va + len(code) + 15) & ~15
    if va > W.CTL:
        raise SystemExit("caves overflow: %#x" % va)
    return out


def decode(buf, n):
    out = []
    for i in range(n):
        kind, fleet, xy, moves, bp, target, val, nation, seq, _ = struct.unpack_from("<10I", buf, i * REC)
        v = words(val)
        out.append({"seq": seq, "nation": words(nation)[0], "kind": NAMES.get(kind, kind), "fleet": words(fleet)[0],
                    "pos": list(words(xy)), "moves": words(moves)[0], "moves_at_entry": words(bp)[0],
                    "target": list(words(target)), "value": None if v[0] == -1 else list(v)})
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
