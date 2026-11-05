#!/usr/bin/env python3
"""Offline tests of patches/d734tail_hook.py (#195 C22/C23): the hook build is made in memory from the seed exe, its bytes
are checked against the seed build, and each probe is run under Unicorn: the logged record, the callee reached with the
same AX/DX, and the return to the instruction after the site. No Wine.

    python3.12 -m tests.test_d734tail_hook     (exit 1 on a failure; needs unicorn)
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "patches"))
import d734tail_hook as H  # noqa: E402
import econ2_hook as E  # noqa: E402
import walk_hook as W  # noqa: E402
from tests.test_observer_build import SENTINEL, load, poke, run  # noqa: E402
from harness.driver import G  # noqa: E402

from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EDX, UC_X86_REG_ESP)  # noqa: E402

FRAME, OUTER = 0x00208000, 0x00208100
D734_RET, OUTER_RET = 0x0044DC1B, 0x0044E9AB
ARMY_N, POS, F4, FA = 7, 0x002A0031, 0x00050000, 0x01F400E1      # pos (49, 42); moves 5; supplies 225, money 500


def built():
    src = bytearray((G / W.SRC).read_bytes())
    b = bytearray(src)
    H.build(b)
    return bytes(src), bytes(b)


def setup(b, eax, edx):
    mu = load(b)
    poke(mu, W.CTL, "<I", 0)
    base = E.ARMY + ARMY_N * E.ARMY_SIZE
    poke(mu, base, "<I", POS)
    poke(mu, base + 4, "<I", F4)
    poke(mu, base + 0xA, "<I", FA)
    poke(mu, FRAME, "<I", OUTER)                 # [ebp] = the outer frame
    poke(mu, FRAME + 4, "<I", D734_RET)          # [ebp+4] = D734's return
    poke(mu, OUTER + 4, "<I", OUTER_RET)         # [[ebp]+4]
    poke(mu, W.NATION, "<h", 3)
    mu.reg_write(UC_X86_REG_EAX, eax)
    mu.reg_write(UC_X86_REG_EDX, edx)
    mu.reg_write(UC_X86_REG_EBP, FRAME)
    return mu


def record(mu, i=0):
    return struct.unpack("<10i", mu.mem_read(W.BUF + i * W.REC, W.REC))


def test_only_the_four_sites_and_the_patch_section_change():
    src, b = built()
    diffs = [i for i in range(0x400, len(src)) if src[i] != b[i]]
    sites = set()
    for site, (_, want, _, _, _) in H.SITES.items():
        sites |= set(range(W.off(site), W.off(site) + len(bytes.fromhex(want))))
    outside = [i for i in diffs if i not in sites and i < W.PATCH_RAW + W.SEED_PATCH_SIZE]
    assert not outside, [hex(i) for i in outside[:10]]
    assert src[W.PATCH_RAW:W.PATCH_RAW + W.SEED_PATCH_SIZE] == b[W.PATCH_RAW:W.PATCH_RAW + W.SEED_PATCH_SIZE]


def tail(site, callee, eax, edx):
    _, b = built()
    mu = setup(b, eax, edx)
    got = {}
    stubs = {callee: lambda uc: got.update(ax=uc.reg_read(UC_X86_REG_EAX) & 0xFFFF, dx=uc.reg_read(UC_X86_REG_EDX) & 0xFFFF,
                                           ebp=uc.reg_read(UC_X86_REG_EBP)),
             "stop": {site + 5}}
    sp = 0x0020F000
    trace = run(mu, site, stubs, sp=sp)
    return mu, got, trace, sp


def check_tail(kind, site, callee, eax, edx):
    mu, got, trace, sp = tail(site, callee, eax, edx)
    assert trace[-1] == site + 5, hex(trace[-1])
    assert got == {"ax": eax & 0xFFFF, "dx": edx & 0xFFFF, "ebp": FRAME}, got
    assert mu.reg_read(UC_X86_REG_ESP) == sp, "the stack is balanced after the relocated call"
    assert struct.unpack("<I", mu.mem_read(W.CTL, 4))[0] == 1
    k, a, d, pos, fa, ret, nation, week, outer, seq = record(mu)
    assert (k, a, d, pos, fa, ret, nation, outer, seq) == (kind, eax, edx, POS, FA, D734_RET, 3, OUTER_RET, 0), \
        (k, a, d, hex(pos), hex(fa), hex(ret), nation, hex(outer), seq)
    r = H.decode(mu.mem_read(W.BUF, W.REC), 1)[0]
    return r


def test_resupply_tail():
    r = check_tail(2, 0x44D935, 0x44F6D8, eax=214, edx=ARMY_N)
    assert r["kind"] == "resupply" and r["city"] == 214 and r["army"] == ARMY_N and r["supplies"] == 225 and r["money"] == 500, r


def test_siege_tail():
    r = check_tail(3, 0x44D949, 0x44B27C, eax=ARMY_N, edx=90)
    assert r["kind"] == "siege" and r["city"] == 90 and r["army"] == ARMY_N, r


def test_attack_tail():
    r = check_tail(4, 0x44D99B, 0x44AEE4, eax=ARMY_N, edx=11)
    assert r["kind"] == "attack" and r["target_army"] == 11 and r["army_pos"] == [49, 42], r


def test_entry():
    _, b = built()
    target = 0x00300040                                       # (64, 48)
    mu = setup(b, ARMY_N, target)
    sp = 0x0020F000
    trace = run(mu, 0x44D734, {"stop": {0x44D73C}}, sp=sp)
    assert trace[-1] == 0x44D73C, hex(trace[-1])
    # push ebp (4) + add esp,-0x18 + push ebx + push esi, as the original
    assert mu.reg_read(UC_X86_REG_ESP) == sp - 4 - 0x18 - 8, hex(mu.reg_read(UC_X86_REG_ESP))
    k, a, d, pos, f4, ret, nation, week, outer, seq = record(mu)
    # inside D734's frame: [ebp] = the caller's EBP (FRAME), [ebp+4] = SENTINEL (run()'s return address), [[ebp]+4] = D734_RET
    assert (k, a, d, pos, f4, ret, outer) == (1, ARMY_N, target, POS, F4, SENTINEL, D734_RET), \
        (k, a, hex(d), hex(pos), hex(f4), hex(ret), hex(outer))
    r = H.decode(mu.mem_read(W.BUF, W.REC), 1)[0]
    assert r["kind"] == "entry" and r["target"] == [64, 48] and r["moves"] == 5, r


def test_full_log_skips_and_still_runs():
    _, b = built()
    mu = setup(b, 214, ARMY_N)
    poke(mu, W.CTL, "<I", W.CAP)
    got = {}
    trace = run(mu, 0x44D935, {0x44F6D8: lambda uc: got.update(ok=1), "stop": {0x44D93A}})
    assert got == {"ok": 1} and trace[-1] == 0x44D93A
    assert struct.unpack("<I", mu.mem_read(W.CTL, 4))[0] == W.CAP


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
