#!/usr/bin/env python3
"""Offline test (no Wine) of g4_lib.give_cities (review round 3, R2 negative control): the byte-change assertion runs at BOTH
the sender and the receiver (the round-2 fix had `snapshot=None` at the receiver, which disabled the assertion precisely
where the original recruit-queue overrun occurred when a full 334-city receiver absorbed one city). This test builds a
save buffer where nation A (receiver) has a full 334-city list and nation B (sender) has a small list, calls give_cities
(B, A, [one_city]), and asserts the byte at A's +0x2e4 (the start of the recruit-queue slot 0 state word) is unchanged
after the call: the bounded put does not overrun.
Run: python3 -m tests.test_give_cities   (exit 1 on a failure)."""
import importlib.util
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "runs/experiments/data/run-exp-g4-followups/g4_lib.py"
SCRIPTS = ROOT / "runs" / "experiments" / "battles"


def main():
    sys.argv = ["x", "TESTCASE"]
    sys.path.insert(0, str(LIB.parent))
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("g4_lib_under_test", LIB); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
    import stage  # noqa: E402
    import state.sav as sv  # noqa: E402
    with tempfile.TemporaryDirectory() as tmp:
        L.ART = Path(tmp); L.D = Path(tmp); L.LOG = Path(tmp) / "log.jsonl"
        # build a save buffer where nation A (1, Carthage, the receiver) has a full 334-city list and nation B (0, Rome, the sender)
        # has a small list. We pick one of Rome's actual cities as the moved city, fill A's list with that city + 333 other ids,
        # so the city move stays consistent (Rome's list must contain the moved city and A's list must include it before the call).
        b = bytearray(L.START.read_bytes())
        rome_cities = [c for c in range(sv.CITY_N) if struct.unpack_from("<h", b, sv.CITY_OFF + c * sv.CITY_LEN + 18)[0] == 0]
        if not rome_cities:
            raise SystemExit("start save has no Rome city")
        moved_city = rome_cities[0]
        # Build a 334-entry list for A (1) that includes moved_city, plus 333 other ids, no terminator (full list).
        o_a = stage._nation(b, 1) + 0x48
        ids = [moved_city] + [c for c in range(sv.CITY_N) if c != moved_city][:333]
        assert len(ids) == 334
        for k, cid in enumerate(ids):
            struct.pack_into("<h", b, o_a + 2 * k, cid)
        # Count word matches the full list.
        struct.pack_into("<h", b, stage._nation(b, 1) + 0x446, 334)
        # Make sure every city id in A's list points to A (1) in the city owner field, so give_cities' ownership edits stay consistent.
        for cid in ids:
            struct.pack_into("<h", b, sv.CITY_OFF + cid * sv.CITY_LEN + 18, 1)
        # Capture the byte at A's +0x2e4 (the recruit-queue slot 0 state word) before the call.
        a_off = stage._nation(b, 1)
        byte_before = b[a_off + 0x2e4]
        # Call give_cities: sender B (Rome, 0) gives one city to receiver A (1). The receiver's list is already full;
        # the bounded put must not write a terminator at +0x2e4 (the original buggy loop did).
        op = L.give_cities(0, 1, [moved_city])
        op(b)
        byte_after = b[a_off + 0x2e4]
        assert byte_before == byte_after, f"receiver +0x2e4 changed: {byte_before} -> {byte_after}; the bounded put overran into the recruit slot"
        # also confirm the receiver's list still ends with the 334th entry (no terminator at +0x2e4)
        last = struct.unpack_from("<h", b, o_a + 2 * 333)[0]
        assert last == ids[333] and last >= 0, f"receiver's 334th entry corrupt: {last}"
    print("test_give_cities: all checks passed")


if __name__ == "__main__":
    main()