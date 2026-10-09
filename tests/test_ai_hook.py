"""patches/ai_hook.py: each stub, run under unicorn from a simulated `call` at its site, must reach the original target with every register,
EFLAGS, ESP and the stack exactly as the call left them, and must append one correct record (or none when the buffer is full).
Needs the seed exe in the game folder (IC2_WORK) and the `unicorn` module.    python3 -m tests.test_ai_hook"""
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "patches"))
sys.path.insert(0, str(ROOT))
import ai_hook as A  # noqa: E402
from harness.driver import G  # noqa: E402

from unicorn import UC_ARCH_X86, UC_MODE_32, Uc  # noqa: E402
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDI,  # noqa: E402
                               UC_X86_REG_EDX, UC_X86_REG_EFLAGS, UC_X86_REG_ESI, UC_X86_REG_ESP)

REGS = (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESI, UC_X86_REG_EDI, UC_X86_REG_EBP)
ARITH = 0x8D5 | 0x400
STACK_TOP = 0xC10000


def image():
    src = G / A.SRC
    b = bytearray(src.read_bytes())
    caves = A.build(b)
    return b, caves


def machine(b, count, nation):
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x400000, 0xA00000 - 0x400000)
    uc.mem_map(STACK_TOP - 0x10000, 0x11000)
    uc.mem_write(A.CODE_VA, bytes(b[A.CODE_RAW:A.CODE_RAW + 0x5B400]))
    uc.mem_write(A.PATCH_VA, bytes(b[A.PATCH_RAW:A.PATCH_RAW + A.RAW_SIZE]))
    uc.mem_write(A.CTL, struct.pack("<I", count))
    uc.mem_write(A.NATION, struct.pack("<h", nation))
    return uc


def test_stub(image, site, count):
    b, caves = image
    name, sid, va, target = site
    assert b[A.off(va)] == 0xE8 and va + 5 + struct.unpack_from("<i", b, A.off(va) + 1)[0] == caves[name]
    rng = random.Random(hash((name, count)))
    for trial in range(20):
        nation = rng.randrange(-1, 16)
        uc = machine(b, count, nation)
        regs = {r: rng.getrandbits(32) for r in REGS}
        regs[UC_X86_REG_EAX] = (regs[UC_X86_REG_EAX] & 0xFFFF0000) | rng.randrange(0, 200)
        uc.mem_write(A.ARMIES, rng.randbytes(A.ARMY_LEN * 200)); uc.mem_write(A.FLEETS, rng.randbytes(A.FLEET_LEN * 200))
        esp0 = STACK_TOP - 4 * rng.randrange(16, 0x200)
        stack = bytearray(rng.randbytes(0x80))
        o = 0xA if sid in (1, 2) else 2                      # the other unit's index: valid, or negative (no copy)
        struct.pack_into("<h", stack, o, rng.choice([rng.randrange(0, 200), -1, -10000]))
        stack = bytes(stack)
        uc.mem_write(esp0, stack)
        flags = 0x202 | (rng.getrandbits(32) & ARITH)
        for r, v in regs.items():
            uc.reg_write(r, v)
        esp = esp0 - 4                                       # the call pushes its return address
        uc.mem_write(esp, struct.pack("<I", va + 5))
        uc.reg_write(UC_X86_REG_ESP, esp)
        uc.reg_write(UC_X86_REG_EFLAGS, flags)
        uc.emu_start(caves[name], target)
        for r, v in regs.items():
            assert uc.reg_read(r) == v, (name, r)
        assert uc.reg_read(UC_X86_REG_ESP) == esp
        assert uc.reg_read(UC_X86_REG_EFLAGS) & (ARITH | 0x200) == flags & (ARITH | 0x200)
        assert bytes(uc.mem_read(esp, 4)) == struct.pack("<I", va + 5)
        assert bytes(uc.mem_read(esp0, 0x80)) == stack
        n = struct.unpack("<I", bytes(uc.mem_read(A.CTL, 4)))[0]
        if count >= A.CAP:
            assert n == count
            continue
        assert n == count + 1
        rec = bytes(uc.mem_read(A.BUF + A.REC * count, A.REC))
        assert struct.unpack_from("<IIIi", rec) == (sid, regs[UC_X86_REG_EAX], regs[UC_X86_REG_EDX], nation)
        assert rec[16:40] == stack[:24]
        table, stride, other_off = (A.ARMIES, A.ARMY_LEN, 0xA) if sid in (1, 2) else (A.FLEETS, A.FLEET_LEN, 2)
        unit = struct.unpack("<h", struct.pack("<I", regs[UC_X86_REG_EAX])[:2])[0]
        exp_unit = bytes(uc.mem_read(table + stride * unit, 16)) if 0 <= table + stride * unit < 0xA00000 - 16 else None
        if exp_unit is not None:
            assert rec[40:56] == exp_unit
        other = struct.unpack_from("<h", stack, other_off)[0]
        if other < 0:
            assert rec[56:68] == bytes(12)
        else:
            assert rec[56:68] == bytes(uc.mem_read(table + stride * other, 12))


def main():
    img, fails = image(), 0
    for site in A.SITES:
        for count in (0, 7, A.CAP - 1, A.CAP):
            try:
                test_stub(img, site, count)
                print("%-18s count %-6d ok" % (site[0], count))
            except AssertionError as e:
                fails += 1
                print("%-18s count %-6d FAIL %r" % (site[0], count, e))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
