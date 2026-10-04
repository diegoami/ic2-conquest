#!/usr/bin/env python3
"""B11 offline tests (no game, no emulator): the build refuses what it must refuse, and the log reader stops at the write index and reports the
overflow flag (docs/tasks/battles-b11-hook.md, Done when). Runs on a synthetic exe image; if the original exe is present it also checks the real scan.

    python3 -m tests.test_battle_hook_build          # also runnable with pytest
"""
import os
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "patches"))
import battle_hook as H  # noqa: E402
from state import hook_log as L  # noqa: E402

LAB = SimpleNamespace(BATTLE_START_CALL=0x45C1AE, SEED_CAVE=0x564400, TBATTLE_START=0x436FB4)


def synthetic():
    """A zero image with the 14 sites, the marker entries, the flag-clear sites and the lab's battle-start call in place."""
    b = bytearray(H.PATCH_RAW_START + H.LAB_PATCH_SIZE)
    for va in H.SITES:
        b[H.off(va):H.off(va) + 5] = b"\xE8" + H.rel32(va, H.RANDOM)
    for _, va, exp in H.MARKERS:
        b[H.off(va):H.off(va) + len(exp)] = exp
    for _, va in H.FLAG_CLEAR:
        b[H.off(va):H.off(va) + 7] = H.FLAG_CLEAR_BYTES
    for _, va, exp in H.RESEED:
        b[H.off(va):H.off(va) + len(exp)] = exp
    b[H.off(LAB.BATTLE_START_CALL):H.off(LAB.BATTLE_START_CALL) + 5] = b"\xE8" + H.rel32(LAB.BATTLE_START_CALL, LAB.SEED_CAVE)
    return b


def refuses(mutate, why):
    b = synthetic()
    mutate(b)
    try:
        H.apply(b, 1, LAB)
    except H.HookBuildError as e:
        return str(e)
    raise AssertionError("the build accepted: " + why)


def test_synthetic_builds():
    b = synthetic()
    info = H.apply(b, 1, LAB)
    assert info["scan_inside"] == sorted(H.SITES)
    rnd = info["caves"]["random"]
    for va in H.SITES:
        assert b[H.off(va)] == 0xE8 and va + 5 + struct.unpack_from("<i", b, H.off(va) + 1)[0] == rnd
    assert len(b) == H.PATCH_RAW_START + H.RAW_SIZE


def test_refuses_a_site_that_is_not_call_to_random():
    site = H.SITES[3]
    refuses(lambda b: b.__setitem__(H.off(site), 0xE9), "E9 instead of E8 at a site")
    refuses(lambda b: b.__setitem__(slice(H.off(site) + 1, H.off(site) + 5), H.rel32(site, H.RANDOM + 4)[0:4]), "an E8 to another target")
    refuses(lambda b: b.__setitem__(slice(H.off(site), H.off(site) + 5), bytes(5)), "zeros at a site")
    refuses(lambda b: b.__setitem__(slice(H.off(H.POST_SITES[1]), H.off(H.POST_SITES[1]) + 5), b"\xE8" + H.rel32(H.POST_SITES[1], H.RANDOM - 1)), "a post-battle site to the wrong place")


def test_refuses_when_scan_list_differs():
    extra = 0x43A000                                    # a 13th call inside the battle module that the hooked list lacks
    refuses(lambda b: b.__setitem__(slice(H.off(extra), H.off(extra) + 5), b"\xE8" + H.rel32(extra, H.RANDOM)), "an unhooked call inside the module")
    extra2 = 0x459000                                   # and one inside TBattleOver
    refuses(lambda b: b.__setitem__(slice(H.off(extra2), H.off(extra2) + 5), b"\xE8" + H.rel32(extra2, H.RANDOM)), "an unhooked call inside TBattleOver")
    ind = 0x43A100                                      # an indirect reference (FF 15) with the dword equal to Random
    refuses(lambda b: b.__setitem__(slice(H.off(ind), H.off(ind) + 6), b"\xFF\x15" + struct.pack("<I", H.RANDOM)), "an indirect reference inside the module")
    # a reference OUTSIDE both modules is fine (the game has 39 of them)
    b = synthetic()
    outside = 0x452000
    b[H.off(outside):H.off(outside) + 5] = b"\xE8" + H.rel32(outside, H.RANDOM)
    info = H.apply(b, 1, LAB)
    assert info["scan_outside_count"] == 1


def test_refuses_changed_entry_bytes_and_branches_into_displaced():
    name, va, exp = H.MARKERS[0]
    refuses(lambda b: b.__setitem__(H.off(va) + 2, 0x90), "changed bytes at a routine entry")
    refuses(lambda b: b.__setitem__(slice(H.off(H.FLAG_CLEAR[1][1]), H.off(H.FLAG_CLEAR[1][1]) + 7), bytes(7)), "changed flag-clear site")
    refuses(lambda b: b.__setitem__(H.off(H.RESEED[0][1]), 0x90), "changed reseed site")
    jump_in = 0x439000                                  # a jmp into the middle of the displaced bytes of the melee entry
    tgt = H.MARKERS[1][1] + 3
    refuses(lambda b: b.__setitem__(slice(H.off(jump_in), H.off(jump_in) + 5), b"\xE9" + H.rel32(jump_in, tgt)), "a branch into displaced bytes")


def test_real_exe_scan_if_present():
    exe = Path(os.environ.get("IC2_WORK", Path.home() / "ic2-work")) / "build" / "Imperial Conquest 2.exe"
    if not exe.exists():
        print("  (the original exe is not here: the real-scan check is skipped)")
        return
    b = bytearray(exe.read_bytes())
    H.check_sites(b)
    inside, outside = H.check_scan(b)
    assert inside == sorted(H.SITES) and len(outside) == 39
    H.check_entries(b)


# ---- the log reader -----------------------------------------------------------------------------------------------------------------------------
def rec(seq, tag, seed_before, seed_after=None, eax=0, result=0):
    seed_after = seed_before if seed_after is None else seed_after
    return struct.pack("<12I", tag, seq, eax, 0, 0, seed_before, seed_after, result, 0, 1, 0, 0)


def ctl(index, overflow=0, cap=65536, magic=L.MAGIC):
    return struct.pack("<5I", index, overflow, 0, cap, magic)


def chain(n, seed=1, site=0x43801A):
    out, s = [], seed
    for i in range(n):
        s2 = L.lcg(s)
        out.append(rec(i, site + 5, s, s2, eax=10, result=(10 * s2) >> 32))
        s = s2
    return out


def test_reader_stops_at_write_index():
    buf = b"".join(chain(5))                            # five records in the buffer, but the index says three
    c, recs = L.parse(ctl(3), buf)
    assert len(recs) == 3 and c["records"] == 3 and c["overflow"] == 0
    c, recs = L.parse(ctl(0), buf)
    assert recs == [] and c["records"] == 0
    c, recs = L.parse(ctl(9), buf)                      # an index past what the buffer holds: the reader stops at the data and says so
    assert len(recs) == 5 and c["truncated_reader"] is True
    c, recs = L.parse(ctl(5, cap=4), buf)               # never past the capacity
    assert len(recs) == 4


def test_reader_reports_overflow_flag():
    c, recs = L.parse(ctl(5, overflow=1), b"".join(chain(5)))
    assert c["overflow"] == 1 and len(recs) == 5
    c, _ = L.parse(ctl(5, overflow=0), b"".join(chain(5)))
    assert c["overflow"] == 0
    c, recs = L.read_process(lambda addr, n: ctl(2, overflow=1) + bytes(12) if addr == L.CTL else b"".join(chain(2))[:n])
    assert c["overflow"] == 1 and len(recs) == 2
    # a process that is not hooked (no magic) reads as an empty log, never as garbage
    c, recs = L.read_process(lambda addr, n: bytes(n))
    assert recs == [] and c["magic_ok"] is False


def test_chain_check_finds_breaks():
    good = chain(10, seed=7)
    _, recs = L.parse(ctl(10), b"".join(good))
    assert L.chain_check(recs, start_seed=7, sites={0x43801A}) == []
    assert L.result_check(recs) == []
    dropped = good[:4] + good[5:]                        # a missing record
    _, r = L.parse(ctl(9), b"".join(dropped))
    assert L.chain_check(r, start_seed=7), "a dropped record must break the chain"
    dup = good[:4] + [good[3]] + good[4:]                # a duplicated record
    _, r = L.parse(ctl(11), b"".join(dup))
    assert L.chain_check(r, start_seed=7)
    _, r = L.parse(ctl(10), b"".join(good))
    assert L.chain_check(r, start_seed=8), "a wrong first seed breaks the boundary"
    assert L.chain_check(r, start_seed=7, sites={0x43812F}), "a site outside the module's list is reported"
    bad = good[:]
    bad[2] = rec(2, 0x43801A + 5, L.lcg(L.lcg(7)), 12345)       # seed_after is not one LCG step
    _, r = L.parse(ctl(10), b"".join(bad))
    assert L.chain_check(r, start_seed=7)


def main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    fails = 0
    for fn in fns:
        try:
            fn()
            print("ok   ", fn.__name__)
        except Exception as e:      # noqa: BLE001
            fails += 1
            print("FAIL ", fn.__name__, type(e).__name__, e)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
