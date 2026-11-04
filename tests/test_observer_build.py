#!/usr/bin/env python3
"""Offline tests of patches/observer_build.py (owner 2026-11-04: tooling is tested before games): the observation build is
built in memory from the seed exe, its bytes are checked against the seed build, and P1–P3 are run under Unicorn with the
callees they reach (FUN_0044fa20, the rollingsave cave) replaced by recording stubs. No Wine.

    python3.12 -m tests.test_observer_build     (exit 1 on a failure; needs unicorn)
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "patches"))
import observer_build as OB  # noqa: E402
import walk_hook as W  # noqa: E402
from harness.driver import G  # noqa: E402

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE  # noqa: E402
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP, UC_X86_REG_EIP  # noqa: E402

SENTINEL = 0x00100000            # a return address outside the image: reaching it ends the run


def built():
    src = bytearray((G / W.SRC).read_bytes())
    b = bytearray(src)
    OB.build(b)
    return bytes(src), bytes(b)


def load(img):
    """Map the PE's sections at their virtual addresses, plus a stack."""
    pe = struct.unpack_from("<I", img, 0x3C)[0]
    nsec = struct.unpack_from("<H", img, pe + 6)[0]
    opt = struct.unpack_from("<H", img, pe + 20)[0]
    size = struct.unpack_from("<I", img, pe + 24 + 56)[0]
    mu = Uc(UC_ARCH_X86, UC_MODE_32)
    mu.mem_map(W.BASE, (size + 0xFFF) & ~0xFFF)
    sh = pe + 24 + opt
    for i in range(nsec):
        vsize, va, rsize, raw = struct.unpack_from("<IIII", img, sh + 40 * i + 8)
        mu.mem_write(W.BASE + va, img[raw:raw + min(rsize, vsize or rsize)])
    mu.mem_map(SENTINEL, 0x1000)
    mu.mem_write(SENTINEL, b"\xF4")              # hlt
    mu.mem_map(0x00200000, 0x10000)              # stack
    return mu


def run(mu, start, stubs, sp=0x0020F000, steps=500):
    """Run from `start` with [esp] = SENTINEL; addresses in `stubs` (va -> fn(mu)) are intercepted: fn runs, then a ret."""
    mu.reg_write(UC_X86_REG_ESP, sp)
    mu.mem_write(sp, struct.pack("<I", SENTINEL))
    trace = []

    def hook(uc, addr, size, data):
        trace.append(addr)
        if addr in stubs:
            stubs[addr](uc)
            esp = uc.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
            uc.reg_write(UC_X86_REG_ESP, esp + 4)
            uc.reg_write(UC_X86_REG_EIP, ret)
        elif addr == SENTINEL or (stubs.get("stop") and addr in stubs["stop"]):
            uc.emu_stop()
    mu.hook_add(UC_HOOK_CODE, hook)
    mu.emu_start(start, SENTINEL + 1, count=steps)
    return trace


def poke(mu, va, fmt, v):
    mu.mem_write(va, struct.pack(fmt, v))


# ---- bytes -----------------------------------------------------------------------------------------------------------

def test_only_the_three_sites_and_the_patch_section_change():
    src, b = built()
    head = 0x400
    diffs = [i for i in range(head, len(src)) if src[i] != b[i]]
    sites = set()
    for site, want, _ in (OB.P1, OB.P2, OB.P3):
        sites |= set(range(W.off(site), W.off(site) + len(want)))
    outside = [i for i in diffs if i not in sites]
    assert not outside, [hex(i) for i in outside[:10]]
    assert len(b) == W.PATCH_RAW + W.RAW_SIZE
    assert b[W.PATCH_RAW + (OB.OBS - W.PATCH_VA)] == 0, "OBS must start off"


def test_seed_cave_and_autosave_hook_untouched():
    src, b = built()
    a, z = W.off(OB.AUTOSAVE_CAVE), W.PATCH_RAW + W.SEED_PATCH_SIZE
    assert src[W.PATCH_RAW:z] == b[W.PATCH_RAW:z]
    assert src[W.off(0x45217A):W.off(0x45217A) + 5] == b[W.off(0x45217A):W.off(0x45217A) + 5]


# ---- P1 --------------------------------------------------------------------------------------------------------------

def any_human(obs, human=None):
    _, b = built()
    mu = load(b)
    poke(mu, OB.OBS, "<B", obs)
    for n in range(16):
        poke(mu, 0x474B00 + 0x494 * n, "<B", 1 if n == human else 0)
    run(mu, 0x449050, {})
    return mu.reg_read(UC_X86_REG_EAX) & 0xFF


def test_p1_any_human():
    assert any_human(0) == 0, "no human, OBS off: 0 (the original ends the game)"
    assert any_human(1) == 1, "no human, OBS on: 1 (the observer keeps it going)"
    assert any_human(0, human=5) == 1, "a human, OBS off: 1 (unchanged)"


# ---- P2 --------------------------------------------------------------------------------------------------------------

def dispatcher_seat(obs, index_after, battle=0):
    """Run P2 from 0x451FE8 with FUN_0044fa20 stubbed to set the seat index; report whether the autosave cave was called
    (and with which EAX) and where execution went."""
    _, b = built()
    mu = load(b)
    poke(mu, OB.OBS, "<B", obs)
    poke(mu, OB.FORM, "<I", 0x12345678)
    poke(mu, OB.BATTLE_FLAG, "<B", battle)
    poke(mu, OB.OFFER, "<h", 3)
    called = {}
    stubs = {OB.FA20: lambda uc: poke(uc, OB.SEAT_INDEX, "<h", index_after),
             OB.AUTOSAVE_CAVE: lambda uc: called.update(eax=uc.reg_read(UC_X86_REG_EAX),
                                                         offer=struct.unpack("<h", uc.mem_read(OB.OFFER, 2))[0]),
             "stop": {0x451FED}}
    trace = run(mu, 0x451FE8, stubs)
    dispatcher_seat.offer = called.get("offer")
    return called.get("eax"), trace[-1]


def test_p2_pauses_only_at_the_round_boundary_with_obs():
    eax, last = dispatcher_seat(obs=1, index_after=0)
    assert eax == 0x12345678 and last == SENTINEL, (hex(eax or 0), hex(last))     # cave called, then ret from dispatcher
    assert dispatcher_seat.offer == -1, dispatcher_seat.offer                     # no stale offer box at the pause
    eax, last = dispatcher_seat(obs=1, index_after=7)
    assert eax is None and last == 0x451FED, hex(last)                             # mid-round: back into the loop
    eax, last = dispatcher_seat(obs=0, index_after=0)
    assert eax is None and last == 0x451FED, hex(last)                             # OBS off: unchanged
    eax, last = dispatcher_seat(obs=1, index_after=0, battle=1)
    assert eax is None and last == 0x451FED, hex(last)                             # a battle pending: no pause


# ---- P3 --------------------------------------------------------------------------------------------------------------

def end_turn_advance(obs):
    _, b = built()
    mu = load(b)
    poke(mu, OB.OBS, "<B", obs)
    poke(mu, OB.SEAT_INDEX, "<h", 5)
    trace = run(mu, 0x45B100, {"stop": {OB.DISPATCH_CALL, 0x45B107}})
    return trace[-1], struct.unpack("<h", mu.mem_read(OB.SEAT_INDEX, 2))[0]


def test_p3_end_turn_skips_the_seat_advance_with_obs():
    last, idx = end_turn_advance(1)
    assert last == OB.DISPATCH_CALL and idx == 5, (hex(last), idx)
    last, idx = end_turn_advance(0)
    assert last == 0x45B107, hex(last)     # the original advance continues


TESTS = [n for n in sorted(globals()) if n.startswith("test_")]

if __name__ == "__main__":
    bad = 0
    for n in TESTS:
        try:
            globals()[n]()
            print("PASS", n)
        except Exception as e:  # noqa: BLE001
            bad += 1
            import traceback
            print("FAIL", n, type(e).__name__, e)
            traceback.print_exc(limit=4)
    sys.exit(1 if bad else 0)
