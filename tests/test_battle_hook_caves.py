#!/usr/bin/env python3
"""B11 offline test: the hook's caves preserve every register, EFLAGS, ESP and the stack, as a direct call (or the original entry bytes) would
(docs/tasks/battles-b11-hook.md, Design 1-2). Needs the x86 emulator `unicorn` (`pip install unicorn`; capstone is used for a disassembly dump when present).

    python3 -m tests.test_battle_hook_caves [--trials N]       # also runnable with pytest

For each cave, N random states (all eight registers, the arithmetic flags and DF, a random stack) are run twice from the same address: once
the way the unhooked game runs (a direct `call Random`; the original entry bytes; the original `mov byte [flag],0`) and once through the hook's
cave. The end states must be equal in: EAX, EBX, ECX, EDX, ESI, EDI, EBP, ESP, EFLAGS, RandSeed, the whole stack from ESP up, and every byte of
guest memory outside the hook's own control block and buffer (and outside the stack area below ESP, which is dead space for both runs). The records the
cave wrote are checked too. Writes outside CTL..BUF+records are detected by comparing the memory images.
"""
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "patches"))
import battle_hook as H  # noqa: E402
from state import hook_log as L  # noqa: E402

try:
    from unicorn import UC_ARCH_X86, UC_MODE_32, Uc, UcError
    from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDI, UC_X86_REG_EDX,
                                   UC_X86_REG_EFLAGS, UC_X86_REG_ESI, UC_X86_REG_ESP)
    HAVE_UNICORN = True
except ImportError:           # pragma: no cover
    HAVE_UNICORN = False

REGS = (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP, UC_X86_REG_ESP,
        UC_X86_REG_EFLAGS) if HAVE_UNICORN else ()
# Delphi RTL Random (System.Random), the 22 bytes at 0x40284C: seed = seed * 0x08088405 + 1; return high dword of range * seed
RANDOM_BYTES = bytes.fromhex("691530E04500" "05840808" "42" "891530E04500" "F7E2" "89D0" "C3")
STACK_TOP, STACK_SIZE = 0xA10000, 0x10000
LOW, HIGH = 0x400000, 0x866000                       # the exe's image, up to the end of the hook buffer
ARITH = 0x8D5 | 0x400                                  # CF PF AF ZF SF OF + DF
SITE = 0x43801A                                        # an address of the battle module used as the call site


def new_machine(seed_state):
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(LOW, HIGH - LOW)
    uc.mem_map(STACK_TOP - STACK_SIZE, STACK_SIZE + 0x1000)
    uc.mem_write(H.RANDOM, RANDOM_BYTES)
    caves = H.build_caves()
    for va, data in caves.values():
        uc.mem_write(va, data)
    uc.mem_write(H.CTL + 12, struct.pack("<II", H.BUF_RECORDS, H.MAGIC))
    return uc, caves


def random_state(rng):
    regs = {r: rng.getrandbits(32) for r in REGS[:7]}
    regs[UC_X86_REG_ESP] = STACK_TOP - 4 * rng.randrange(8, 0x200)
    regs[UC_X86_REG_EFLAGS] = 0x202 | (rng.getrandbits(32) & ARITH)
    stack = rng.randbytes(0x400)
    return regs, stack, rng.getrandbits(32)


def prepare(uc, state, code_at, code, mem_extra=()):
    regs, stack, seed = state
    uc.mem_write(code_at, code)
    uc.mem_write(H.RAND_SEED, struct.pack("<I", seed))
    uc.mem_write(H.COUNTER_HR, struct.pack("<H", rng_small(seed)))        # half-round counter (u16) at 0x4A0B7A
    uc.mem_write(H.SIDE, struct.pack("<H", (seed >> 16) & 1))             # side to move (u16) at 0x4A0B78
    uc.mem_write(H.FLAG, bytes([1]))                                      # battle flag at 0x4A0B7C
    sp = regs[UC_X86_REG_ESP]
    uc.mem_write(sp, stack[:0x100])                          # live stack contents above ESP
    for r, v in regs.items():
        uc.reg_write(r, v)


def rng_small(seed):
    return seed & 0x7FFF


def snapshot(uc):
    s = {r: uc.reg_read(r) for r in REGS}
    sp = s[UC_X86_REG_ESP]
    s["stack"] = bytes(uc.mem_read(sp, STACK_TOP - sp))
    s["seed"] = bytes(uc.mem_read(H.RAND_SEED, 4))
    # the image outside the hook's control block and buffer (the stack area is handled above; below ESP is dead)
    s["image_low"] = bytes(uc.mem_read(LOW, H.CTL - LOW))
    return s


def run(uc, begin, until):
    uc.emu_start(begin, until, count=100000)
    uc.mem_write(begin, bytes(16))                       # the code at the site differs by design (hook vs original): not part of the comparison
    uc.mem_write(until, bytes(16))


def compare(a, b, what, extra=None):
    bad = [("reg 0x%x" % r) for r in REGS if a[r] != b[r]]
    for k in ("stack", "seed", "image_low"):
        if a[k] != b[k]:
            bad.append(k)
    return ["%s: %s" % (what, x) for x in bad]


def fresh(state):
    uc, caves = new_machine(state)
    return uc, caves


def test_random_cave(trials=300):
    assert HAVE_UNICORN, "pip install unicorn"
    rng = random.Random(1234)
    fails, buffers = [], 0
    for t in range(trials):
        state = random_state(rng)
        ucA, _ = fresh(state)
        ucB, caves = fresh(state)
        direct = b"\xE8" + H.rel32(SITE, H.RANDOM)
        hooked = b"\xE8" + H.rel32(SITE, caves["random"][0])
        stop = SITE + 5
        # the page after the call site holds a harmless instruction; execution is stopped there
        for uc, code in ((ucA, direct), (ucB, hooked)):
            prepare(uc, state, SITE, code + b"\xF4")
            run(uc, SITE, stop)
        a, b = snapshot(ucA), snapshot(ucB)
        fails += compare(a, b, "random cave trial %d" % t)
        # the record it wrote
        ctl, recs = L.read_process(lambda addr, n: bytes(ucB.mem_read(addr, n)))
        r = recs[0] if recs else None
        regs, stack, seed = state
        ok = (r is not None and ctl["index"] == 1 and not ctl["overflow"] and r["kind"] == "random" and r["site"] == SITE
              and r["eax"] == regs[UC_X86_REG_EAX] and r["edx"] == regs[UC_X86_REG_EDX] and r["ecx"] == regs[UC_X86_REG_ECX]
              and r["seed_before"] == seed and r["seed_after"] == L.lcg(seed) and r["result"] == a[UC_X86_REG_EAX]
              and r["ebp"] == regs[UC_X86_REG_EBP] and r["counter"] == rng_small(seed) and r["side"] == (seed >> 16) & 1 and r["flag"] == 1)
        if not ok:
            fails.append("random cave trial %d: record %r" % (t, r))
        buffers += 1
    return fails, buffers


def test_marker_caves(trials=300):
    assert HAVE_UNICORN
    rng = random.Random(99)
    fails, n = [], 0
    for name, entry, displaced in H.MARKERS:
        for t in range(trials):
            state = random_state(rng)
            ucA, _ = fresh(state)
            ucB, caves = fresh(state)
            after = entry + len(displaced)
            orig = displaced + b"\xF4"
            hooked = b"\xE9" + H.rel32(entry, caves["marker_" + name][0]) + b"\x90" * (len(displaced) - 5)
            prepare(ucA, state, entry, orig)
            run(ucA, entry, after)
            prepare(ucB, state, entry, hooked)
            ucB.mem_write(after, b"\xF4")
            run(ucB, entry, after)
            a, b = snapshot(ucA), snapshot(ucB)
            fails += compare(a, b, "marker %s trial %d" % (name, t))
            ctl, recs = L.read_process(lambda addr, n_: bytes(ucB.mem_read(addr, n_)))
            regs = state[0]
            r = recs[0] if recs else None
            if not (r and r["kind"] == "marker" and r["site"] == entry and r["eax"] == regs[UC_X86_REG_EAX] and r["edx"] == regs[UC_X86_REG_EDX]
                    and r["ecx"] == regs[UC_X86_REG_ECX] and r["seed_before"] == r["seed_after"] == state[2]):
                fails.append("marker %s trial %d: record %r" % (name, t, r))
            n += 1
    return fails, n


def test_flag_caves(trials=200):
    assert HAVE_UNICORN
    rng = random.Random(7)
    fails, n = [], 0
    for name, site in H.FLAG_CLEAR:
        for t in range(trials):
            state = random_state(rng)
            ucA, _ = fresh(state)
            ucB, caves = fresh(state)
            after = site + 7
            prepare(ucA, state, site, H.FLAG_CLEAR_BYTES + b"\xF4")
            run(ucA, site, after)
            hooked = b"\xE9" + H.rel32(site, caves[name][0]) + b"\x90\x90"
            prepare(ucB, state, site, hooked)
            ucB.mem_write(after, b"\xF4")
            run(ucB, site, after)
            a, b = snapshot(ucA), snapshot(ucB)
            fails += compare(a, b, "flag cave %s trial %d" % (name, t))
            ctl, recs = L.read_process(lambda addr, n_: bytes(ucB.mem_read(addr, n_)))
            r = recs[0] if recs else None
            if not (r and r["kind"] == "flag_clear" and r["site"] == site and r["flag"] == 0 and ucB.mem_read(H.FLAG, 1)[0] == 0):
                fails.append("flag cave %s trial %d: record %r" % (name, t, r))
            n += 1
    return fails, n


def test_reseed_caves(trials=200):
    assert HAVE_UNICORN
    rng = random.Random(21)
    fails, n = [], 0
    for name, site, displaced in H.RESEED:
        for t in range(trials):
            state = random_state(rng)
            ucA, _ = fresh(state)
            ucB, caves = fresh(state)
            after = site + len(displaced)
            prepare(ucA, state, site, displaced + b"\xF4")
            run(ucA, site, after)
            hooked = b"\xE9" + H.rel32(site, caves[name][0]) + b"\x90" * (len(displaced) - 5)
            prepare(ucB, state, site, hooked)
            ucB.mem_write(after, b"\xF4")
            run(ucB, site, after)
            a, b = snapshot(ucA), snapshot(ucB)
            fails += compare(a, b, "reseed cave %s trial %d" % (name, t))
            ctl, recs = L.read_process(lambda addr, n_: bytes(ucB.mem_read(addr, n_)))
            r = recs[0] if recs else None
            if not (r and r["kind"] == "reseed" and r["site"] == site and r["seed_before"] == state[2] == r["seed_after"]):
                fails.append("reseed cave %s trial %d: record %r" % (name, t, r))
            n += 1
    return fails, n


def _reentry_case(kind, name, site, displaced, state):
    """Run one cave with BUSY = 1 (a cave is already working) against the unhooked code. The cave must log nothing, leave SV and the private stack untouched, set the
    REENTERED flag, and leave registers, EFLAGS, ESP, the stack and all memory exactly as the unhooked code does."""
    ucA, _ = fresh(state)
    ucB, caves = fresh(state)
    ucB.mem_write(H.BUSY, struct.pack("<I", 1))
    ucB.mem_write(H.SV, struct.pack("<I", 0xDEADBEEF))                # the outer cave's saved ESP: must survive
    priv_before = bytes(ucB.mem_read(H.CTL + 0x40, 0xC0))
    if kind == "random":
        direct, hooked, stop = b"\xE8" + H.rel32(SITE, H.RANDOM), b"\xE8" + H.rel32(SITE, caves["random"][0]), SITE + 5
        at = SITE
    else:
        after = site + len(displaced)
        direct, stop, at = displaced, after, site
        hooked = b"\xE9" + H.rel32(site, caves[name][0]) + b"\x90" * (len(displaced) - 5)
    prepare(ucA, state, at, direct + b"\xF4")
    run(ucA, at, stop)
    prepare(ucB, state, at, hooked)
    ucB.mem_write(stop, b"\xF4")
    ucB.mem_write(H.BUSY, struct.pack("<I", 1))
    run(ucB, at, stop)
    a, b = snapshot(ucA), snapshot(ucB)
    bad = compare(a, b, "re-entry %s" % name)
    ctl = L.parse_ctl(bytes(ucB.mem_read(H.CTL, 48)))
    if not ctl["reentered"] or ctl["index"] != 0 or ctl["busy"] != 1:
        bad.append("re-entry %s: control block %r" % (name, ctl))
    if struct.unpack("<I", ucB.mem_read(H.SV, 4))[0] != 0xDEADBEEF or bytes(ucB.mem_read(H.CTL + 0x40, 0xC0)) != priv_before:
        bad.append("re-entry %s: SV or the private stack was touched" % name)
    return bad


def test_reentry_when_busy(trials=60):
    """Every cave entered while BUSY: no log, REENTERED set, the unhooked behaviour (R2)."""
    assert HAVE_UNICORN
    rng = random.Random(77)
    fails, n = [], 0
    for t in range(trials):
        state = random_state(rng)
        fails += _reentry_case("random", "random", None, None, state)
        for name, entry, displaced in H.MARKERS:
            fails += _reentry_case("x", "marker_" + name, entry, displaced, state)
        for name, site in H.FLAG_CLEAR:
            fails += _reentry_case("x", name, site, H.FLAG_CLEAR_BYTES, state)
        for name, site, displaced in H.RESEED:
            fails += _reentry_case("x", name, site, displaced, state)
        n += 1
    return fails, n


def test_real_nested_entry_inside_the_recorder():
    """A genuine re-entry: while the Random cave is inside `rec_body` (BUSY = 1, on the private stack) a second call of the Random cave happens. The inner call must leave
    EAX, the other registers, EFLAGS and RandSeed as a direct `call Random` from that state does; the outer call must finish; REENTERED is set; one record only."""
    assert HAVE_UNICORN
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EIP
    rng = random.Random(5)
    for t in range(30):
        state = random_state(rng)
        uc, caves = fresh(state)
        regs, stack, seed = state
        prepare(uc, state, SITE, b"\xE8" + H.rel32(SITE, caves["random"][0]) + b"\xF4")
        trap = caves["rec_body"][0]                                # rec_body entry: every register is saved on the private stack, so the nested call may clobber them like any call
        seen = {}

        def cb(u, addr, size, _):
            if "done" in seen:
                if "after" not in seen:                              # the inner call has returned to the trap address: its end state
                    seen["after"] = {r: u.reg_read(r) for r in REGS}
                return
            seen["done"] = True
            seen["regs"] = {r: u.reg_read(r) for r in REGS}
            seen["seed"] = u.mem_read(H.RAND_SEED, 4)
            sp = u.reg_read(UC_X86_REG_ESP) - 4
            u.mem_write(sp, struct.pack("<I", addr))             # the inner "call": its return address is the trap address itself
            u.reg_write(UC_X86_REG_ESP, sp)
            seen["nested_ret_sp"] = sp + 4
            u.reg_write(UC_X86_REG_EIP, caves["random"][0])
            seen["inner_eax"] = u.reg_read(UC_X86_REG_EAX)

        # the trap is hit twice (entering, and again when the inner call returns to it): the second time is not intercepted
        h = uc.hook_add(UC_HOOK_CODE, cb, begin=trap, end=trap)
        uc.emu_start(SITE, SITE + 5, count=20000)
        uc.hook_del(h)
        # the inner call left the registers, EFLAGS and ESP as a direct `call Random` from the same state does
        ref, _ = fresh(state)
        ref.mem_write(SITE, b"\xE8" + H.rel32(SITE, H.RANDOM) + b"\xF4")
        ref.mem_write(H.RAND_SEED, bytes(seen["seed"]))
        for r in REGS:
            ref.reg_write(r, seen["regs"][r])
        ref.mem_write(seen["regs"][UC_X86_REG_ESP], bytes(0x20))
        ref.emu_start(SITE, SITE + 5, count=100)
        for r in REGS:
            assert ref.reg_read(r) == seen["after"][r], "inner call differs from a direct call in register 0x%x" % r
        ctl = L.parse_ctl(bytes(uc.mem_read(H.CTL, 48)))
        assert ctl["reentered"] == 1, ctl
        assert ctl["busy"] == 0 and ctl["index"] == 1, ctl          # the outer call finished and logged its one record
        # two draws happened (inner and outer): RandSeed advanced twice
        assert struct.unpack("<I", uc.mem_read(H.RAND_SEED, 4))[0] == L.lcg(L.lcg(seed))
        assert uc.reg_read(UC_X86_REG_ESP) == regs[UC_X86_REG_ESP]


def test_a_broken_cave_is_detected():
    """The test must be able to fail: a cave whose epilogue forgets to restore EFLAGS (`popfd` replaced by `pop eax`) is reported."""
    assert HAVE_UNICORN
    good = H.SWITCH_OUT
    try:
        H.SWITCH_OUT = b"\x61\x58\x8B\x25" + H.u32(H.SV)
        fails, _ = test_random_cave(20)
    finally:
        H.SWITCH_OUT = good
    assert len(fails) >= 20, "the broken cave was not detected (%d reports)" % len(fails)


def test_seed_cave():
    """The hooked seed cave: RandSeed := seed, one boundary record carrying that seed, then it jumps to the battle start."""
    assert HAVE_UNICORN
    uc, caves = new_machine(None)
    origin, start = 0x564800, 0x436FB4
    uc.mem_write(origin, H.seed_cave(origin, 0x1234, start))
    uc.mem_write(start, b"\xF4")
    uc.reg_write(UC_X86_REG_ESP, STACK_TOP - 0x100)
    uc.emu_start(origin, start, count=1000)
    ctl, recs = L.read_process(lambda addr, n: bytes(uc.mem_read(addr, n)))
    assert len(recs) == 1 and recs[0]["kind"] == "start" and recs[0]["seed_before"] == 0x1234 == struct.unpack("<I", uc.mem_read(H.RAND_SEED, 4))[0], recs
    assert uc.reg_read(UC_X86_REG_ESP) == STACK_TOP - 0x100


def test_overflow_never_wraps():
    """At capacity the cave sets the overflow flag, writes nothing more and still calls the real Random."""
    assert HAVE_UNICORN
    uc, caves = new_machine(None)
    uc.mem_write(H.CTL, struct.pack("<I", H.BUF_RECORDS))        # index at capacity
    uc.mem_write(H.RAND_SEED, struct.pack("<I", 5))
    uc.mem_write(SITE, b"\xE8" + H.rel32(SITE, caves["random"][0]) + b"\xF4")
    uc.reg_write(UC_X86_REG_ESP, STACK_TOP - 0x100)
    uc.reg_write(UC_X86_REG_EAX, 10)
    uc.emu_start(SITE, SITE + 5, count=1000)
    ctl = L.parse_ctl(bytes(uc.mem_read(H.CTL, 32)))
    assert ctl["overflow"] == 1 and ctl["index"] == H.BUF_RECORDS
    assert struct.unpack("<I", uc.mem_read(H.RAND_SEED, 4))[0] == L.lcg(5)      # Random still ran
    assert bytes(uc.mem_read(H.BUF + H.BUF_RECORDS * H.REC - 0x1000, 0x1000)) == bytes(0x1000)   # nothing written past the end


def main():
    trials = int(sys.argv[sys.argv.index("--trials") + 1]) if "--trials" in sys.argv else 300
    if not HAVE_UNICORN:
        print("SKIP: unicorn is not installed (pip install unicorn): the register/flag preservation test did not run")
        return 2
    allfails = []
    for fn, kw in ((test_random_cave, {"trials": trials}), (test_marker_caves, {"trials": trials}), (test_flag_caves, {"trials": max(1, trials * 2 // 3)}),
                   (test_reseed_caves, {"trials": max(1, trials * 2 // 3)}),
                   (test_reentry_when_busy, {"trials": max(1, trials // 5)})):
        fails, n = fn(**kw)
        print("%-20s %5d machine states: %s" % (fn.__name__, n, "all equal" if not fails else "%d FAILURES" % len(fails)))
        allfails += fails
    for fn in (test_seed_cave, test_overflow_never_wraps, test_real_nested_entry_inside_the_recorder, test_a_broken_cave_is_detected):
        try:
            fn()
            print("%-20s ok" % fn.__name__)
        except AssertionError as e:
            print("%-20s FAIL %s" % (fn.__name__, e))
            allfails.append(fn.__name__)
    for f in allfails[:20]:
        print(" ", f)
    return 1 if allfails else 0


if __name__ == "__main__":
    sys.exit(main())
