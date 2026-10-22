#!/usr/bin/env python3
"""Offline test (no saves) for scripts/sav_export_policy_check.py.

Reuses the synthetic SAV of tests.test_sav_atlas_invariants and checks the gate-2 policy rules: a clean save
passes; a dirty name tail and empty-slot residue fail a from-scratch export but are only reported when the
export has a source; INERT bytes must be zero without a source and equal to the source's with one.

Run: python3 -m tests.test_sav_export_policy_check   (exit 1 on a failure).
"""
import importlib.util
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.test_sav_atlas_invariants import build  # noqa: E402

NATION0 = 89600 + 34 * 334 + 2 + 656 + 2            # cities, army count, one army, fleet count


def main():
    spec = importlib.util.spec_from_file_location("pol_under_test", ROOT / "scripts" / "sav_export_policy_check.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

    def res(b, src=None):
        return {r: (ok, req) for r, ok, _d, req in m.policy(b, src)}

    good = build()
    tail = bytearray(good); tail[89600 + 6] = 0x41                    # "Alba\0\0A": a byte after the NUL
    slot = bytearray(good); slot[89600 + 34 * 334 + 2 + 16 + 32 * 3 + 10] = 7   # residue in empty slot 3
    inert = bytearray(good); inert[NATION0 + 0x450] = 1
    alleg = bytearray(good); struct.pack_into("<h", alleg, 89600 + 0x14, -1)  # city 0 without allegiance
    cases = [("clean save passes every rule", all(ok for ok, _ in res(good).values())),
             ("dirty tail fails a from-scratch export", res(bytes(tail))["text_tails_canonical"] == (False, True)),
             ("dirty tail with a source is reported only", res(bytes(tail), good)["text_tails_canonical"] == (False, False)),
             ("empty-slot residue fails a from-scratch export", res(bytes(slot))["empty_slots_zero"] == (False, True)),
             ("INERT byte set without a source fails", not res(bytes(inert))["inert_bytes_carried_or_zero"][0]),
             ("INERT byte carried from the source passes", res(bytes(inert), bytes(inert))["inert_bytes_carried_or_zero"][0]),
             ("INERT byte differing from the source fails", not res(bytes(inert), good)["inert_bytes_carried_or_zero"][0]),
             ("allegiance -1 fails, with a source too", res(bytes(alleg), bytes(alleg))["city_allegiance_in_range"] == (False, True))]
    fails = 0
    for name, ok in cases:
        print(("ok   " if ok else "FAIL ") + name)
        fails += not ok
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
