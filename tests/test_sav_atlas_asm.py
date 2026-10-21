#!/usr/bin/env python3
"""Offline test (no Wine, no EXE) for scripts/sav_atlas_asm.py.

Feeds hand-encoded x86 sequences through `scan` and checks the field and the
access kind for each tracking rule: a literal displacement, a register
pointer moved by `add`, the record -1 rule for an indexed label below a base,
a StrCopy destination, a TStream read, a `rep movsd` block, the push/pop
shadow, the callee-saved carry after a `jmp`, and a volatile register dropped
by a call. Needs capstone (`pip install capstone`).

Run: python3 -m tests.test_sav_atlas_asm   (exit 1 on a failure).
"""
import importlib.util
import struct
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
VA = 0x440000


def _module():
    spec = importlib.util.spec_from_file_location("sav_atlas_asm_under_test", SCRIPTS / "sav_atlas_asm.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def d32(v):
    return struct.pack("<I", v & 0xFFFFFFFF)


def call(at, target):
    return b"\xE8" + struct.pack("<i", target - (VA + at + 5))


def build(parts):
    """Concatenate byte strings; a callable part gets its own offset (for call rel32)."""
    out = b""
    for p in parts:
        out += p(len(out)) if callable(p) else p
    return out


CASES = [  # name, code parts, expected set of (kind, field) among the hits (subset), forbidden set
    ("literal scalar write", [b"\x66\xC7\x05" + d32(0x4A0320) + b"\x05\x00"],
     {("write", "TRAILER.current_nation")}, set()),
    ("register pointer + add", [b"\xBE" + d32(0x49C26C), b"\x66\x89\x46\x08", b"\x83\xC6\x1A", b"\x66\x8B\x46\x0A"],
     {("write", "FLEET.owner"), ("read", "FLEET.countdown")}, set()),
    ("record -1 below base", [b"\x8D\x1C\x5D" + d32(0x49C252), b"\x66\x89\x43\x08"],
     {("write", "FLEET.owner")}, {("write", "SLOT.name")}),
    ("strcopy destination", [b"\xB8" + d32(0x47467B), lambda o: call(o, 0x405B00)],
     {("write", "NATION.leader")}, set()),
    ("stream read block", [b"\xBA" + d32(0x479590), b"\xB9" + d32(0x2C5C), b"\xFF\x16"],
     {("write", "CITY.name"), ("write", "CITY.tribute")}, set()),
    ("rep movsd block", [b"\xBF" + d32(0x49C26C), b"\xB9" + d32(6), b"\xF3\xA5"],
     {("write", "FLEET.x"), ("write", "FLEET.army")}, {("write", "FLEET.cell")}),
    ("push/pop shadow", [b"\xBE" + d32(0x4A0324), b"\x56", b"\xBE" + d32(0x47C1EC), b"\x5E", b"\x66\xFF\x0E"],
     {("write", "ARMYCOUNT.A")}, {("write", "ARMY.x")}),
    ("callee-saved carry after jmp", [b"\xBB" + d32(0x474670), b"\xEB\x02", b"\x90\x90",
                                      b"\xC6\x83" + d32(0x490) + b"\x00"],
     {("write", "NATION.human")}, set()),
    ("volatile dropped by a call", [b"\xB8" + d32(0x474670), lambda o: call(o, 0x402744),
                                    b"\xC6\x80" + d32(0x490) + b"\x00"],
     {("escape", "NATION.name")}, {("write", "NATION.human")}),
]


def main():
    m = _module()
    m._ROWS[:] = m.cov.load_map()
    scal = {}
    for addr, (r, w) in m.scalar_fields(m._ROWS).items():
        m.SCALAR_ARRAYS.append((r["field_id"], addr, w))
        for k in range(w):
            scal[addr + k] = (r["field_id"], k)
    fails = []
    for name, parts, want, forbid in CASES:
        code = build(parts) + b"\xC3"
        hits = m.scan(VA, code, {VA}, scal)
        got = {(h["kind"], f) for h in hits for f in h["fields"]}
        ok = want <= got and not (forbid & got)
        print(("ok   " if ok else "FAIL ") + f"{name}: {sorted(got) if not ok else sorted(want)}")
        if not ok:
            fails.append(name)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
