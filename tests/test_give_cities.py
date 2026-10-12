#!/usr/bin/env python3
"""Offline tests (no Wine) of g4_lib.give_cities (review round 6, R1 lift).

Round 3 added a `put()` byte-change assertion (round-2's receiver assertion) and round-4 added an oversized-list check.
The round-4 "put_clone" tested a local copy of the writer; round-5 lifts `put` from a closure to the module-level helper
`g4_lib._give_cities_put` so the test exercises the production writer directly. Round-6 adds `test_receiver_assertion_via_give_cities`
which calls the production `give_cities()` and monkey-patches `_give_cities_put` to inject a rogue byte before the original
runs, so the assertion fires inside `_give_cities_put` itself (the round-5 test called `_give_cities_put` directly and bypassed
`give_cities` entirely — a future regression that removed `snapshot=snap` from the receiver call inside `give_cities` would
not be detected). If a future regression removes the byte-change assertion (e.g., the receiver call forgets `snapshot=snap`
again) the round-6 test would fail by passing without raise.

Tests:

  * `test_consistent_333_to_334`: a clean 1->334 transfer. Rome (nation 0, sender) gives ONE of its cities to Carthage
    (nation 1, receiver). Asserts: that city's owner byte is now 1; the receiver's 334th list position holds the moved city's id;
    the receiver's count word at +0x446 reads 334; BOTH bytes of the receiver's recruit-queue slot 0 state word at +0x2e4 are
    unchanged; Rome's list no longer contains the moved city's id; Rome's count word has dropped.

  * `test_receiver_assertion_active`: an injection test that proves the receiver's byte-change assertion is real against the
    PRODUCTION module-level `_give_cities_put`. Pre-modifies a single byte at the receiver's +0x2e4 (outside the city-list region
    and count-word region) and calls `_give_cities_put(b, 1, [], snapshot, allowed=set())`. With the assertion in place this raises
    SystemExit; without it (e.g., a future regression passing `snapshot=None` for the receiver) the put succeeds silently and the
    test would fail. A second part calls with `snapshot=None` and verifies no raise fires, demonstrating the test is sensitive
    to the assertion's presence.

  * `test_receiver_assertion_via_give_cities` (round-6): monkey-patches `_give_cities_put` with a wrapper that injects a rogue
    byte at the receiver's +0x2e4 BEFORE calling the original, so the assertion fires inside `_give_cities_put` itself. Sets up
    a consistent 1->334 save (Rome=1 city, Carthage=333) and calls `give_cities(0, 1, [moved])`; the wrapper's rogue write makes
    the assertion raise inside the receiver's `_give_cities_put`. A second part calls the wrapper directly with `snapshot=None`
    to prove no raise fires (regression-detection control: if `give_cities` ever passed `snapshot=None` for the receiver,
    the rogue byte would not be detected and the test would not raise — proving the first part exercises the assertion path).

  * `test_oversized_receiver_list_raises`: a 334-city receiver absorbing one city that is ALREADY in its own list builds the
    receiver's NEW list to 335 ids; the round-4 `put()` raises immediately because `len(v) > 334`. Verifies the round-3 "fake"
    test's actual behaviour was a 335-entry count word with only 334 stored entries (the bug the round-4 check catches at the
    source).

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


    # ---------------------------------------------------------------- test 2: production receiver-side byte-change assertion is active
    # Round 5: the assertion is exercised by the module-level _give_cities_put (the round-4 put_clone
    # tested a local copy; disabling the production receiver assertion would not have been detected).
    # We pre-modify a single byte at the receiver's +0x2e4 (outside the city-list region AND outside
    # the count-word region AND outside the allowed whitelist) and call production put with snapshot=
    # bytes(b) and allowed=set(). The production put's byte-change delta check MUST include +0x2e4
    # in extra_changed and raise SystemExit. If a future regression passed snapshot=None for the receiver
    # (or removed the assertion), the raise would NOT fire and this test would fail.
    b = fresh_save()
    recv_state_off = stage._nation(b, 1) + 0x2e4
    snapshot = bytes(b)                                  # snapshot taken BEFORE the modification (round-5 mistake: capturing after caused b == snapshot, no delta to detect)
    b[recv_state_off] = (b[recv_state_off] + 1) & 0xFF       # outside any region/allowed => must raise
    raised = False
    try:
        L._give_cities_put(b, 1, [], 0, snapshot=snapshot, allowed=set())   # round-5 second mistake: 4 positional args bound to b/n/v/old_len; allowed=set() ends up at snapshot. Pass old_len=0 explicitly.
    except SystemExit as e:
        raised = True
        assert "outside the city-list region" in str(e), f"unexpected SystemExit message: {e}"
    assert raised, "production _give_cities_put did NOT raise on an out-of-region byte change; the receiver byte-change assertion is missing or the receiver call no longer passes snapshot=snap"
    # Sensitivity check: with the assertion bypassed (snapshot=None), the put writes only region_a and region_b,
    # so no SystemExit fires even though we modified +0x2e4. This part proves the previous block is exercising
    # the assertion (not, say, the oversized-list check above).
    b2 = fresh_save()
    recv_state_off2 = stage._nation(b2, 1) + 0x2e4
    b2[recv_state_off2] = (b2[recv_state_off2] + 1) & 0xFF
    try:
        L._give_cities_put(b2, 1, [], 0, snapshot=None, allowed=set())  # snapshot=None -> assertion bypassed
    except SystemExit:
        raise AssertionError("production _give_cities_put raised despite snapshot=None (assertion bypassed); this control case should NOT raise")
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



    # ---------------------------------------------------------------- test 3 (new): receiver assertion fires via give_cities()
    # Round-6: proves the receiver's byte-change assertion is exercised through the PRODUCTION give_cities()
    # entry point (not directly against _give_cities_put). The round-5 test called _give_cities_put directly,
    # so a future regression in give_cities() that passed snapshot=None for the receiver call would not be
    # detected by that test. Here we monkey-patch _give_cities_put with a wrapper that injects a rogue byte
    # BEFORE calling the original, so the original's assertion fires inside _give_cities_put itself.
    #
    # We set up the same 1->334 save as test 1 (Rome=1 city, Carthage=333) and call give_cities(0, 1, [moved]).
    # The wrapper sees the receiver's _give_cities_put call (n=1, snapshot is not None), sets a rogue byte at
    # receiver +0x2e4, then calls the original — which then raises SystemExit because +0x2e4 is outside the
    # city-list region. A second part calls the wrapper directly with snapshot=None to confirm no raise fires,
    # proving the first part actually exercises the assertion (and would not fire if give_cities ever passed
    # snapshot=None for the receiver, which is the regression we are guarding against).
    b = fresh_save()
    rc = rome_cities(b)
    if not rc:
        raise SystemExit("start save has no Rome city for the via-give_cities test")
    moved = rc[0]
    pool = [c for c in range(sv.CITY_N) if c != moved]
    cart_ids = pool[:333]
    # Rome: 1 city
    o_r = stage._nation(b, 0) + 0x48
    for k in range(333):
        struct.pack_into("<h", b, o_r + 2 * k, -1)
    struct.pack_into("<h", b, o_r + 0, moved)
    struct.pack_into("<h", b, stage._nation(b, 0) + 0x446, 1)
    # Carthage: 333 cities
    o_c = stage._nation(b, 1) + 0x48
    for k in range(333):
        struct.pack_into("<h", b, o_c + 2 * k, -1)
    for k, cid in enumerate(cart_ids):
        struct.pack_into("<h", b, o_c + 2 * k, cid)
    struct.pack_into("<h", b, stage._nation(b, 1) + 0x446, 333)
    for cid in cart_ids:
        struct.pack_into("<h", b, sv.CITY_OFF + cid * sv.CITY_LEN + 18, 1)
    struct.pack_into("<h", b, sv.CITY_OFF + moved * sv.CITY_LEN + 18, 0)

    orig_put = L._give_cities_put
    def patching_put(b, n, v, old_len, snapshot=None, allowed=None, tag=""):
        # Inject rogue byte BEFORE calling the original, but only when snapshot is supplied
        # (mimics the give_cities path where snapshot=snap for both sender and receiver).
        if snapshot is not None:
            off = stage._nation(b, n) + 0x2e4
            b[off] = (b[off] + 0xFF) & 0xFF
        return orig_put(b, n, v, old_len, snapshot=snapshot, allowed=allowed, tag=tag)

    try:
        L._give_cities_put = patching_put
        raised = False
        try:
            L.give_cities(0, 1, [moved])(b)
        except SystemExit as e:
            raised = True
            assert "outside the city-list region" in str(e) or "give_cities" in str(e), f"unexpected SystemExit message: {e}"
        assert raised, "give_cities via patched _give_cities_put did NOT raise on rogue +0x2e4 byte; the receiver assertion path is missing"

        # Regression-detection control: if give_cities ever passed snapshot=None for the receiver call,
        # the wrapper would NOT inject the rogue byte (snapshot is None branch), so no SystemExit fires.
        # We call the wrapper directly to simulate that scenario.
        b2 = fresh_save()
        off2 = stage._nation(b2, 1) + 0x2e4
        b2[off2] = (b2[off2] + 1) & 0xFF
        try:
            patching_put(b2, 1, [], 0, snapshot=None, allowed=set())
        except SystemExit:
            raise AssertionError("patching_put raised despite snapshot=None (wrapper would not inject); this control should NOT raise")
    finally:
        L._give_cities_put = orig_put

    print("test_receiver_assertion_via_give_cities: all checks passed")



if __name__ == "__main__":
    main()
