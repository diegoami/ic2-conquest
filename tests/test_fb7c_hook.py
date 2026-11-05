#!/usr/bin/env python3
"""Offline tests of patches/fb7c_hook.py (#195 own-capital stays): the build changes only the three sites and the patch
section; each probe runs under Unicorn on the real exe, logs its record, and the game continues exactly as unpatched
(the re-run `cmp` still drives the `jle`). No Wine.

    python3.12 -m tests.test_fb7c_hook     (exit 1 on a failure; needs unicorn)
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "patches"))
import fb7c_hook as H  # noqa: E402
import walk_hook as W  # noqa: E402
from tests.test_observer_build import load, poke, run  # noqa: E402
from harness.driver import G  # noqa: E402

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI  # noqa: E402

SP = 0x0020F000


def built():
    src = bytearray((G / W.SRC).read_bytes())
    b = bytearray(src)
    H.build(b)
    return bytes(src), bytes(b)


def rec(mu, i=0):
    return H.decode(mu.mem_read(W.BUF + i * W.REC, W.REC), 1)[0]


def setup(b):
    mu = load(b)
    poke(mu, W.CTL, "<I", 0)
    poke(mu, W.NATION, "<h", 13)
    return mu


def test_only_the_three_sites_and_the_patch_section_change():
    src, b = built()
    sites = set()
    for site, (_, want, _) in H.SITES.items():
        sites |= set(range(W.off(site), W.off(site) + len(bytes.fromhex(want))))
    outside = [i for i in range(0x400, W.PATCH_RAW + W.SEED_PATCH_SIZE) if src[i] != b[i] and i not in sites]
    assert not outside, [hex(i) for i in outside[:10]]


def target_probe(target):
    _, b = built()
    mu = setup(b)
    # run() puts its return address at [sp]; the probe reads the word at the original [esp+8]
    poke(mu, SP + 8, "<h", target)
    trace = run(mu, 0x44FD22, {"stop": {0x44FD2A, 0x44FD51}}, sp=SP)
    return mu, trace[-1]


def test_war_target_probe_logs_and_keeps_the_branch():
    mu, last = target_probe(5)
    assert last == 0x44FD2A, hex(last)                      # a target: on to the Random(10) roll, as unpatched
    assert rec(mu) == {**rec(mu), "kind": "war_target", "nation": 13, "nation_arg": 5}, rec(mu)
    mu, last = target_probe(-1)
    assert last == 0x44FD51, hex(last)                      # no target: the jle skips the roll, as unpatched
    assert rec(mu)["nation_arg"] == -1


def test_war_declared_probe():
    _, b = built()
    mu = setup(b)
    poke(mu, SP + 8, "<h", 7)
    trace = run(mu, 0x44FD38, {"stop": {0x44FD41}}, sp=SP)
    assert trace[-1] == 0x44FD41, hex(trace[-1])
    assert mu.reg_read(UC_X86_REG_ECX) & 0xFFFF == 3 and mu.reg_read(UC_X86_REG_EDX) & 0xFFFF == 7
    assert rec(mu)["kind"] == "war_declared" and rec(mu)["nation_arg"] == 7, rec(mu)


def test_alliance_probe():
    _, b = built()
    mu = setup(b)
    mu.reg_write(UC_X86_REG_ESI, 4)
    trace = run(mu, 0x44FE4E, {"stop": {0x44FE54}}, sp=SP)
    assert trace[-1] == 0x44FE54, hex(trace[-1])
    assert mu.reg_read(UC_X86_REG_ECX) & 0xFFFF == 2 and mu.reg_read(UC_X86_REG_EDX) == 4
    assert rec(mu)["kind"] == "alliance" and rec(mu)["nation_arg"] == 4, rec(mu)


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
