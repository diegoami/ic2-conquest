#!/usr/bin/env python3
"""Offline test (no EXE, DAT or saves) for scripts/sav_atlas_init.py.

Checks the DAT layout arithmetic: the loader's reads sum to the size of the
pinned DAT (140,706 bytes), the 16 nation records are 1,055 bytes each from DAT
0x1B100 (the offset research found independently), and the tail tables sit
where the loader puts them.

Run: python3 -m tests.test_sav_atlas_init   (exit 1 on a failure).
"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


def main():
    spec = importlib.util.spec_from_file_location("sav_atlas_init_under_test", SCRIPTS / "sav_atlas_init.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    offs, total = m.dat_offsets()
    nation = sum(e[2] for e in m.DAT_LAYOUT if e[0].startswith("nation."))
    checks = [
        ("reads sum to the DAT size", total == 140706),
        ("nation record in the DAT is 1,055 bytes", nation == 1055),
        ("nation 0 starts at DAT 0x1B100", offs["nation.name"][0] == 0x1B100),
        ("nation 15 starts 15 records later", offs["nation.name"][15] == 0x1B100 + 15 * 1055),
        ("15 armies and 2 fleets", len(offs["army"]) == 15 and len(offs["fleet"]) == 2),
        ("leader table is 16 x 12 x 26 bytes", next(e[2] for e in m.DAT_LAYOUT if e[0] == "leader_names") == 16 * 12 * 26),
        ("news block is 40 x 61 bytes and ends the DAT", offs["news"][0] + 40 * 61 == total),
        ("merc pool is 201 templates + 50 live slots", next(e[2] for e in m.DAT_LAYOUT if e[0] == "merc_pool") == 251 * 12),
    ]
    fails = 0
    for name, ok in checks:
        print(("ok   " if ok else "FAIL ") + name)
        fails += not ok
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
