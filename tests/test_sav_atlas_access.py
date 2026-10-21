#!/usr/bin/env python3
"""Offline test (no Wine, no private source) for scripts/sav_atlas_access.py.

Feeds synthetic lines written in the decompiler's style through `scan` and
checks the field, the access kind and the two ambiguity rules: a label just
below a table base is record -1 only when indexed, and an index multiplier
picks the table whose stride it divides.

Run: python3 -m tests.test_sav_atlas_access   (exit 1 on a failure).
"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _module():
    spec = importlib.util.spec_from_file_location("sav_atlas_access_under_test", SCRIPTS / "sav_atlas_access.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


CASES = [  # line, expected (kind, fields) of the first hit, or None for no hit
    ("  x = (&DAT_0047c1f0)[i * 0x148];", ("read", ["ARMY.owner"])),
    ("  y = (&DAT_0047c1ec)[i * 0x148 + 2];", ("read", ["ARMY.owner"])),
    ("  *(short *)(&DAT_0049c25a + iVar1) = p;", ("write", ["FLEET.owner"])),
    ("  *(undefined2 *)(&DAT_0049c25c + iVar1) = 0x18;", ("write", ["FLEET.countdown"])),
    ("  DAT_004a031c = 3;", None),
    ("  DAT_004a0320 = 5;", ("write", ["TRAILER.current_nation"])),
    ("  if (DAT_004a0320 == 5) {", ("read", ["TRAILER.current_nation"])),
    ("  v = *(undefined4 *)((int)&DAT_0049c26c + i * 0x1a);", ("read", ["FLEET.x", "FLEET.y"])),
    ("  (&DAT_00474aa8)[n * 0x125] = (&DAT_00474aa8)[n * 0x125] + 1;", ("write", ["NATION.treasury"])),
    ("  puVar3 = &DAT_0049c26c;", ("escape", ["FLEET.x"])),
    ("  FUN_0044cd08(p, (undefined4 *)((int)&DAT_0049c270 + i * 0x1a));", ("escape", ["FLEET.route_x"])),
    ("  c = (&DAT_004a0a24)[x * 0xc + y];", ("read", ["BATTLE.grid"])),
    ("  (&DAT_004a034c)[s * 0x16] = 0;", ("write", ["BSLOT.troops"])),
    ("  (&DAT_004a0348)[s * 0x16] = 0;", ("write", ["BSLOT.label"])),
    ("  *(char *)(&DAT_00474b00 + n * 0x494) = 1;", ("write", ["NATION.human"])),
]


def main():
    m = _module()
    rows = m.cov.load_map()
    fails = []
    for line, want in CASES:
        hits, _ = m.scan(["// ==== FUN_00400000 @ 00400000 ====", line], rows)
        got = (hits[0]["kind"], hits[0]["fields"]) if hits else None
        ok = got == want
        print(("ok   " if ok else "FAIL ") + f"{line.strip()} -> {got}")
        if not ok:
            fails.append(line)
    hits, _ = m.scan(["// ==== FUN_00400000 @ 00400000 ====", "  puVar3 = &DAT_0049c26c;",
                      "  FUN_0044cd08(p, (undefined4 *)((int)&DAT_0049c270 + i * 0x1a));"], rows)
    ok = [h.get("escape") for h in hits] == ["seed", "arg"]
    print(("ok   " if ok else "FAIL ") + "escape subtypes seed / arg")
    if not ok:
        fails.append("escape subtypes")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
