#!/usr/bin/env python3
"""Observation build (owner 2026-11-04: "do we have an observation mode for this game? If not we should add one"):
the seeded fast rollingsave exe, plus a switch that lets every nation be played by the original's own AI while the game
still stops once per round, with an autosave, for the harness.

    python3 patches/observer_build.py <game folder>   # reads "... fast rollingsave seed.exe", writes "... seed observer.exe"

The original has no such mode: with no human seat left, its dispatcher ends the game (research
2026-10-05-end-of-game-screens.md §4). Here every nation stays a computer seat (human flag +0x490 = 0), so every rule that
treats humans differently (offers to humans, tactical battles, End of Game) runs its computer path. The pause is a
separate byte, OBS at 0x565000, which the harness writes (1) after loading. With OBS = 0 the build behaves exactly like
the seed build.

Three patches, each a `jmp stub` over whole instructions, the stubs in the grown .patch section at 0x564600:
- **P1, 0x449050** (FUN_00449050, "is any seat human?"): with OBS set it answers 1, so the dispatcher keeps playing
  computer seats instead of ending the game.
- **P2, 0x451FE8** (the dispatcher's `call FUN_0044fa20`, one computer seat): after the seat, with OBS set, no battle
  pending (0x4A0B7C) and the seat index (0x4A0322) wrapped to 0, the round is complete and FUN_004514ec has ticked the
  week. The stub then does what the human turn start does: clear the pending offer (0x49F008 = -1, as FUN_00452034 does
  first; without it StartTurn showed a stale "X wants to trade with Y" box at every pause, Wine check v1),
  `mov eax,[0x4A0BD0]; call <rollingsave cave 0x564200>`
  (AUTOnnnn.SAV + AUTOSAVE.LOG, then TPremierForm_StartTurn), and returns from the dispatcher. The game idles with the
  menus enabled, at the start of the round.
- **P3, 0x45B100** (TPremierForm_EndTurn's seat advance): with OBS set, End turn does not advance the seat; it calls the
  dispatcher directly (0x45B13E). Seat 0's computer player then plays first instead of being skipped.

Each End turn then plays exactly one full round (16 seats) and ends in one autosave. Tests: tests/test_observer_build.py
(byte checks and Unicorn emulation of P1–P3).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walk_hook as W  # noqa: E402

DST = "Imperial Conquest 2 fast rollingsave seed observer.exe"
OBS = W.CTL                           # 0x565000: the observer byte (0 off, 1 on)
AUTOSAVE_CAVE = 0x564200              # patch_exe.py CAVE_VA: autosave, then jmp TPremierForm_StartTurn
FORM = 0x4A0BD0                       # TPremierForm instance (StartTurn's Self, as FUN_00452034 passes it)
SEAT_INDEX, BATTLE_FLAG = 0x4A0322, 0x4A0B7C
P1 = (0x449050, bytes.fromhex("33d266b91000"), 0x449056)          # xor edx,edx; mov cx,0x10
P2 = (0x451FE8, bytes.fromhex("e833daffff"), 0x451FED)            # call 0x44fa20
P3 = (0x45B100, bytes.fromhex("0fbf0522034a00"), 0x45B107)        # movsx eax, word [0x4a0322]
FA20, DISPATCH_CALL = 0x44FA20, 0x45B13E
OFFER = 0x49F008                      # the AI's pending offer to the human seat; FUN_00452034 sets it to -1 first
u32 = W.u32


def rel(src_next, target):
    return struct.pack("<i", target - src_next)


def stubs(base):
    """The three stubs, laid out from `base`. Returns {name: (va, code)}."""
    out, va = {}, base
    # P1: cmp byte [OBS],0; je orig; mov eax,1; ret; orig: xor edx,edx; mov cx,0x10; jmp 0x449056
    c = bytearray(b"\x80\x3D" + u32(OBS) + b"\x00")
    c += b"\x74\x06" + b"\xB8\x01\x00\x00\x00" + b"\xC3"
    c += P1[1] + b"\xE9" + rel(va + len(c) + len(P1[1]) + 5, P1[2])
    out["P1"] = (va, bytes(c))
    va = (va + len(c) + 15) & ~15
    # P2: call FA20; cmp byte [OBS],0; je back; cmp word [SEAT_INDEX],0; jne back; cmp byte [BATTLE],0; jne back;
    #     mov eax,[FORM]; call AUTOSAVE_CAVE; ret; back: jmp 0x451FED
    c = bytearray(b"\xE8" + rel(va + 5, FA20))
    c += b"\x80\x3D" + u32(OBS) + b"\x00"
    j1 = len(c); c += b"\x74\x00"
    c += b"\x66\x83\x3D" + u32(SEAT_INDEX) + b"\x00"
    j2 = len(c); c += b"\x75\x00"
    c += b"\x80\x3D" + u32(BATTLE_FLAG) + b"\x00"
    j3 = len(c); c += b"\x75\x00"
    c += b"\x66\xC7\x05" + u32(OFFER) + b"\xFF\xFF"          # mov word [OFFER], -1: no offer box at the pause
    c += b"\xA1" + u32(FORM)
    c += b"\xE8" + rel(va + len(c) + 5, AUTOSAVE_CAVE)
    c += b"\xC3"
    back = len(c)
    c += b"\xE9" + rel(va + len(c) + 5, P2[2])
    for j in (j1, j2, j3):
        c[j + 1] = back - (j + 2)
    out["P2"] = (va, bytes(c))
    va = (va + len(c) + 15) & ~15
    # P3: cmp byte [OBS],0; jne dispatch; movsx eax, word [0x4a0322]; jmp 0x45B107; dispatch: jmp 0x45B13E
    c = bytearray(b"\x80\x3D" + u32(OBS) + b"\x00")
    j = len(c); c += b"\x75\x00"
    c += P3[1] + b"\xE9" + rel(va + len(c) + len(P3[1]) + 5, P3[2])
    c[j + 1] = len(c) - (j + 2)
    c += b"\xE9" + rel(va + len(c) + 5, DISPATCH_CALL)
    out["P3"] = (va, bytes(c))
    return out


def build(b):
    if len(b) != W.PATCH_RAW + W.SEED_PATCH_SIZE:
        raise SystemExit("unexpected size %d (not the seed build?)" % len(b))
    for site, want, _ in (P1, P2, P3):
        if bytes(b[W.off(site):W.off(site) + len(want)]) != want:
            raise SystemExit("0x%X holds %s, not %s" % (site, bytes(b[W.off(site):W.off(site) + 8]).hex(), want.hex()))
    hook = W.off(0x45217A)
    if b[hook] != 0xE8 or struct.unpack_from("<i", b, hook + 1)[0] + 0x45217A + 5 != AUTOSAVE_CAVE:
        raise SystemExit("0x45217A does not call the rollingsave cave at 0x564200")
    hdr = 0x1F8 + 8 * 40
    if bytes(b[hdr:hdr + 6]) != b".patch":
        raise SystemExit(".patch is not the 9th section")
    vsize = OBS + 0x10 - W.PATCH_VA
    struct.pack_into("<I", b, hdr + 8, vsize)
    struct.pack_into("<I", b, hdr + 16, W.RAW_SIZE)
    struct.pack_into("<I", b, hdr + 36, struct.unpack_from("<I", b, hdr + 36)[0] | 0x80000000)   # writable (OBS)
    struct.pack_into("<I", b, 0x118 + 56, (W.PATCH_VA - W.BASE + vsize + 0xFFF) & ~0xFFF)
    b += b"\xCC" * (W.CTL - W.PATCH_VA - W.SEED_PATCH_SIZE) + bytes(W.RAW_SIZE - (W.CTL - W.PATCH_VA))
    raw = lambda va: W.PATCH_RAW + (va - W.PATCH_VA)
    b[raw(OBS)] = 0
    out = stubs(W.CAVES)
    for name, (va, code) in out.items():
        b[raw(va):raw(va) + len(code)] = code
    for (site, want, _), name in ((P1, "P1"), (P2, "P2"), (P3, "P3")):
        b[W.off(site):W.off(site) + len(want)] = b"\xE9" + W.rel32(site, out[name][0]) + b"\x90" * (len(want) - 5)
    if max(va + len(c) for va, c in out.values()) > W.CTL:
        raise SystemExit("stubs overflow")
    return {k: hex(v[0]) for k, v in out.items()}


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    bb = bytearray((folder / W.SRC).read_bytes())
    print(build(bb))
    (folder / DST).write_bytes(bytes(bb))
