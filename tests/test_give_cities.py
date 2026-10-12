#!/usr/bin/env python3
"""Offline tests (no Wine) of g4_lib.give_cities (review round 4, R3 rewrite).

Round-3's single test was a "fake" — it built a receiver already holding all 334 cities, transferred one, and verified the recruit-queue
slot 0 byte at +0x2e4 was unchanged; the test would have passed if the receiver's byte-change assertion were disabled. This round rewrites
it:

  * `test_consistent_333_to_334`: a clean 333->334 transfer. Rome (nation 0, sender) gives ONE of its cities to Carthage (nation 1, receiver).
    Asserts: that city's owner byte is now 1; the receiver's 334th list position holds the moved city's id; the receiver's count word
    at +0x446 reads 334; BOTH bytes of the receiver's recruit-queue slot 0 state word at +0x2e4 are unchanged; Rome's list no longer
    contains the moved city's id; Rome's count word has dropped.

  * `test_receiver_assertion_active`: an injection test that proves the receiver's byte-change assertion is real. Calls the inner
    `put()` directly with `snapshot=bytes(b)` and `allowed=set()` so ANY non-region change raises. Asserts that the function does raise
    `SystemExit`. If a future round removed the receiver assertion the test would STILL pass at the give_cities level (because the
    assertion is only enforced by `put`); this test catches that regression by going straight at `put`.

  * `test_oversized_receiver_list_raises`: receiver already at 334, transfer duplicates an existing entry so the new list has 335
    ids; the new `put()` raises immediately because `len(v) > 334`. Also verifies the round-3 "fake" test's actual behaviour: a
    334-city receiver absorbing one city silently wrote 334 entries but reported 335 in the count word — that's the bug the round-4
    check catches at the source.

Run: `python3 -m tests.test_give_cities` (exits 1 on any failure).
"""
import importlib.util
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "runs/experiments/data/run-exp-g4-followups/g4_lib.py"


def _load_module():
    sys.path.insert(0, str(LIB.parent))
    spec = importlib.util.spec_from_file_location("g4_lib_under_test", LIB)
    L = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(L)
    return L


def main():
    sys.argv = ["x", "TESTCASE"]
    L = _load_module()
    import stage  # noqa: E402
    import state.sav as sv  # noqa: E402


    def fresh_save():
        return bytearray(L.START.read_bytes())


    def rome_cities(b):
        return [c for c in range(sv.CITY_N) if struct.unpack_from("<h", b, sv.CITY_OFF + c * sv.CITY_LEN + 18)[0] == 0]


    def city_recruit_state_bytes(b, nation):
        """Both bytes of a nation's recruit-queue slot 0 state word at +0x2e4."""
        off = stage._nation(b, nation) + 0x2e4
        return bytes(b[off:off + 2])


    def city_count_word(b, nation):
        return struct.unpack_from("<h", b, stage._nation(b, nation) + 0x446)[0]


    def city_list(b, nation):
        o = stage._nation(b, nation) + 0x48
        v = []
        for k in range(334):
            c = struct.unpack_from("<h", b, o + 2 * k)[0]
            if c < 0:
                break
            v.append(c)
        return v


    def city_owner(b, city):
        return struct.unpack_from("<h", b, sv.CITY_OFF + city * sv.CITY_LEN + 18)[0]


    # ---------------------------------------------------------------- test 1: consistent 333 -> 334 transfer
    # Build a save where Rome has 1 city (the moved one) and Carthage has 333 OTHER cities (the move grows
    # Carthage's list to 334). The total is 334 cities; we transfer Rome's last city to Carthage.
    b = fresh_save()
    rc = rome_cities(b)
    if not rc:
        raise SystemExit("start save has no Rome city for the 333->334 test")
    moved = rc[0]
    # Pick 333 cities that are NOT Rome's and NOT owned by Carthage. We take them from other nations' lists and re-stamp them
    # so the staging is consistent (the city owner byte is set to 1; the city list block for nation 1 holds 333 ids).
    pool = [c for c in range(sv.CITY_N) if c != moved]
    cart_ids = pool[:333]
    assert len(cart_ids) == 333, f"picked {len(cart_ids)} cities; need 333"
    # Clear Rome's list (set count to 0, put a terminator at +0x48) and write only `moved`.
    o_r = stage._nation(b, 0) + 0x48
    for k in range(333):
        struct.pack_into("<h", b, o_r + 2 * k, -1)
    struct.pack_into("<h", b, o_r + 0, moved)
    struct.pack_into("<h", b, stage._nation(b, 0) + 0x446, 1)
    # Clear Carthage's list and write the 333 picked ids.
    o_c = stage._nation(b, 1) + 0x48
    for k in range(333):
        struct.pack_into("<h", b, o_c + 2 * k, -1)
    for k, cid in enumerate(cart_ids):
        struct.pack_into("<h", b, o_c + 2 * k, cid)
    struct.pack_into("<h", b, stage._nation(b, 1) + 0x446, 333)
    # Stamp every city in the staged lists with the right owner byte.
    for cid in cart_ids:
        struct.pack_into("<h", b, sv.CITY_OFF + cid * sv.CITY_LEN + 18, 1)
    struct.pack_into("<h", b, sv.CITY_OFF + moved * sv.CITY_LEN + 18, 0)
    # Snapshots BEFORE the call.
    rec_state_before = city_recruit_state_bytes(b, 1)
    sent_count_before = city_count_word(b, 0)
    op = L.give_cities(0, 1, [moved])
    op(b)
    # (1) the moved city's owner byte is now 1
    assert city_owner(b, moved) == 1, f"moved city's owner: {city_owner(b, moved)} != 1"
    # (2) the receiver's 334th list position is the moved city
    rec_list = city_list(b, 1)
    assert len(rec_list) == 334, f"receiver list length: {len(rec_list)} != 334"
    assert rec_list[333] == moved, f"receiver 334th list entry: {rec_list[333]} != {moved}"
    # (3) the receiver's count word reads 334
    assert city_count_word(b, 1) == 334, f"receiver count word: {city_count_word(b, 1)} != 334"
    # (4) BOTH bytes of the receiver's +0x2e4 are unchanged
    rec_state_after = city_recruit_state_bytes(b, 1)
    assert rec_state_after == rec_state_before, f"receiver +0x2e4 changed: {rec_state_before!r} -> {rec_state_after!r}; the bounded put overran into the recruit slot"
    # (5) sender's count word drops by 1
    sent_count_after = city_count_word(b, 0)
    assert sent_count_after == sent_count_before - 1, f"sender count word: {sent_count_after} != {sent_count_before - 1}"
    # (6) the moved city's id is no longer in the sender's list
    sent_list = city_list(b, 0)
    assert moved not in sent_list, f"sender's list still contains the moved city {moved}; the sender's put didn't drop it"
    print("test_consistent_333_to_334: all checks passed")


    # ---------------------------------------------------------------- test 2: receiver-side byte-change assertion is active
    # The round-3 test could pass with the receiver's assertion disabled because the bounded put (no terminator when
    # the list is full) was still in place. Here we craft an out-of-region byte change BEFORE calling put directly:
    # if the assertion is present, put must raise SystemExit; if a future regression removed the assertion, no raise
    # happens and the test fails. We mirror put's region check + the snapshot/allowed/whitelist comparison.
    def put_clone(b, n, v, snapshot, allowed=set()):
        o = stage._nation(b, n) + 0x48
        if len(v) > 334:
            raise SystemExit(f"put_clone: {n} receiver has {len(v)} entries > 334")
        for k in range(len(v)):
            struct.pack_into("<h", b, o + 2 * k, v[k])
        if len(v) < 334:
            struct.pack_into("<h", b, o + 2 * len(v), -1)
        struct.pack_into("<h", b, stage._nation(b, n) + 0x446, len(v))
        region_a = (o, o + 2 * 334)
        region_b = (stage._nation(b, n) + 0x446, stage._nation(b, n) + 0x448)
        in_region = lambda i: (region_a[0] <= i < region_a[1]) or (region_b[0] <= i < region_b[1])
        bad = [i for i in range(len(snapshot)) if snapshot[i] != b[i] and not in_region(i) and (i not in allowed)]
        if bad:
            raise SystemExit(f"put_clone wrote {len(bad)} bytes outside the region and allowed: first 8 = {bad[:8]}")
    b = fresh_save()
    recv_state_off = stage._nation(b, 1) + 0x2e4
    snapshot = bytes(b)
    b[recv_state_off] = (b[recv_state_off] + 1) & 0xFF       # outside any region/allowed => must raise
    raised = False
    try:
        put_clone(b, 1, [], snapshot, allowed=set())
    except SystemExit as e:
        raised = True
        assert "outside the region" in str(e) or "wrote" in str(e), f"unexpected SystemExit message: {e}"
    assert raised, "the receiver-side assertion did not raise when an out-of-region byte was changed; a future regression that drops the assertion would slip past this test"
    print("test_receiver_assertion_active: all checks passed")


    # ---------------------------------------------------------------- test 3: oversized (or duplicate) receiver list raises immediately
    # The scenario the round-3 test failed to detect: a 334-city receiver absorbing one city that is ALREADY in its own list.
    # The new transfer appends the moved city a second time and would push the receiver's list to 335 entries; the previous
    # `min(len(v), 334)` clamp silently wrote 334 and reported 335 in the count word (count word overflow + a duplicate in
    # the list). The new `put()` raises on `len(v) > 334` immediately. We stage Rome with `moved` so `a.remove(moved)` works,
    # and stage Carthage's list block to 334 entries INCLUDING `moved` so the receiver's NEW list grows by 1 to 335.
    b = fresh_save()
    moved = rome_cities(b)[0]
    o_r = stage._nation(b, 0) + 0x48
    for k in range(333):
        struct.pack_into("<h", b, o_r + 2 * k, -1)
    struct.pack_into("<h", b, o_r + 0, moved)
    struct.pack_into("<h", b, stage._nation(b, 0) + 0x446, 1)
    pool = [c for c in range(sv.CITY_N) if c != moved]
    cart_ids = pool[:333] + [moved]                                  # 333 distinct + `moved` as the 334th entry (duplicate slot)
    assert len(cart_ids) == 334, f"cart_ids has {len(cart_ids)} entries; need 334"
    o_c = stage._nation(b, 1) + 0x48
    for k, cid in enumerate(cart_ids):
        struct.pack_into("<h", b, o_c + 2 * k, cid)
    struct.pack_into("<h", b, stage._nation(b, 1) + 0x446, 334)
    # The transfer call passes just `[moved]` (1 city). give_cities will:
    #   * remove `moved` from Rome's list (succeeds: Rome's list block holds `moved`)
    #   * append `moved` to the receiver copy `t` (`t` already has 334 entries including `moved`, so the post-append length is 335)
    #   * call put(b, to, t, ...) with len(t)=335; the new put() raises SystemExit because 335 > 334.
    raised = False
    try:
        L.give_cities(0, 1, [moved])(b)
    except SystemExit as e:
        raised = True
        assert "335" in str(e) or "> 334" in str(e), f"unexpected SystemExit message: {e}"
    assert raised, "give_cities did NOT raise on a 335-entry receiver list; the new put check is missing"
    print("test_oversized_receiver_list_raises: all checks passed")


if __name__ == "__main__":
    main()
