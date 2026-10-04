#!/usr/bin/env python3
"""Tests of `runs/experiments/battles/stage.py` (L1 edits) and `state/battle.py` (reader and diff). Offline by default:

    python3 -m tests.test_battle_stage          # offline: a no-op edit is byte-identical, each edit changes only its own field, the diff
                                                #   reads saved pairs (synthetic edits of a tracked save, and the B0 pair if its saves are present)
    python3 -m tests.test_battle_stage live     # needs the game: the edited save is opened and army 0's record is read back from memory
"""
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
import stage  # noqa: E402
from state import battle, sav  # noqa: E402

SRC = ROOT / "saves" / "run0-start-AUTO0720-seed12345.SAV"
B0_PAIR = (ROOT / "artifacts" / "run-exp-battle-probe" / "NB_pre_attack-20261004-081149.SAV",
           ROOT / "artifacts" / "run-exp-battle-probe" / "NB_post_battle.SAV")


def tmp():
    return Path(tempfile.mkdtemp())


def changed(a, b):
    """Byte offsets where two equal-length buffers differ."""
    assert len(a) == len(b), (len(a), len(b))
    return [i for i in range(len(a)) if a[i] != b[i]]


def edited(ops):
    return stage.apply(bytearray(SRC.read_bytes()), ops)


def within(offs, lo, hi):
    return all(lo <= o < hi for o in offs)


def test_noop_is_byte_identical():
    d = tmp() / "o.sav"
    stage.edit(SRC, d)
    assert d.read_bytes() == SRC.read_bytes()


def test_rewriting_current_values_is_byte_identical():
    s = sav.load(str(SRC))
    a0 = s["armies"][0]
    ops = [("units", 0, [(u["type"], u["troops"], u["quality"], u["merc"], u["name"]) for u in a0["units"]]),
           ("morale", 0, a0["morale"]), ("supplies", 0, a0["supplies"]), ("money", 0, a0["money"]), ("moves", 0, a0["moves"]),
           ("treasury", 0, s["nations"][0]["treasury"]), ("unity", 0, s["nations"][0]["unity"]),
           ("relation", 0, 6, s["nations"][0]["relations"]["Gaul"]), ("city", 0, {"loyalty": s["cities"][0]["loyalty"]})]
    assert bytes(edited(ops)) == SRC.read_bytes()


def test_each_edit_changes_only_its_own_field():
    raw = SRC.read_bytes()
    a0 = stage._army(bytearray(raw), 0)
    n0, n6 = stage._nation(bytearray(raw), 0), stage._nation(bytearray(raw), 6)
    cases = [("morale", [("morale", 0, 65)], a0 + 14, a0 + 16), ("supplies", [("supplies", 0, 123)], a0 + 10, a0 + 12),
             ("money", [("money", 0, 77)], a0 + 12, a0 + 14), ("moves", [("moves", 0, 5)], a0 + 6, a0 + 8),
             ("treasury", [("treasury", 0, 4242)], n0 + 0x438, n0 + 0x43C), ("unity", [("unity", 0, 321)], n0 + 0x440, n0 + 0x442),
             ("city", [("city", 3, {"loyalty": 11, "fort": 9})], sav.CITY_OFF + 3 * 34 + 22, sav.CITY_OFF + 3 * 34 + 28)]
    for name, ops, lo, hi in cases:
        offs = changed(raw, bytes(edited(ops)))
        assert offs and within(offs, lo, hi), (name, offs[:5], lo, hi)
    offs = changed(raw, bytes(edited([("relation", 0, 6, 3)])))
    ok = [(n0 + 0x26 + 12, n0 + 0x26 + 14), (n6 + 0x26 + 0, n6 + 0x26 + 2)]
    assert all(any(lo <= o < hi for lo, hi in ok) for o in offs), offs
    # an army edit never touches the position (x, y at +0, +2) or any other army
    b = edited([("units", 0, [("hi", 6000, 6)]), ("morale", 0, 65), ("supplies", 0, 9), ("money", 0, 9), ("moves", 0, 9)])
    offs = changed(raw, bytes(b))
    assert within(offs, a0 + 6, a0 + sav.ARMY_LEN) and not any(a0 <= o < a0 + 6 for o in offs), offs[:5]
    s0, s1 = sav.load(str(SRC)), sav.parse(bytes(b))
    assert s0["armies"][1:] == s1["armies"][1:] and s0["map"] == s1["map"] and (s1["armies"][0]["x"], s1["armies"][0]["y"]) == (s0["armies"][0]["x"], s0["armies"][0]["y"])


def test_set_units_values_and_empty_slots():
    s = sav.parse(bytes(edited([("units", 0, [("hi", 6000, 6), ("lc", 7000, 7, 11, "Gallic Riders")])])))
    u = s["armies"][0]["units"]
    assert [(x["type"], x["troops"], x["quality"], x["merc"]) for x in u] == [("hi", 6000, 6, 0), ("lc", 7000, 7, 11)], u
    assert u[1]["name"] == "Gallic Riders" and u[0]["name"].endswith("Battalion"), u


def test_bad_inputs_rejected_and_positions_not_an_operation():
    for ops in ([("units", 0, [("xx", 1, 6)])], [("units", 0, [("hi", 40000, 6)])], [("x", 0, 5)], [("units", 999, [])], [("city", 999, {})]):
        try:
            edited(ops)
        except ValueError:
            continue
        raise AssertionError(ops)


def test_uniform_sizes():
    assert stage.uniform("hi") == [("hi", 6000, 6)] and stage.uniform("li", 1, 0.5) == [("li", 7500, 6)] and stage.uniform("lc", 3)[2][1] == 7000


# ---- state/battle.py -----------------------------------------------------------------------------------------------------------
def test_by_type_sums_every_unit_of_a_type():
    a = {"units": [{"type": "li", "troops": 14400}, {"type": "hi", "troops": 5900}, {"type": "li", "troops": 14500}, {"type": "li", "troops": 6900}, {"type": "hi", "troops": 5000}]}
    assert battle.by_type(a) == {"li": 35800, "hi": 10900, "ar": 0, "lc": 0, "hc": 0} and battle.by_type(None) == {}


def test_diff_on_a_synthetic_pair():
    pre = edited([("units", 0, [("hi", 6000, 6), ("hi", 6000, 6), ("li", 5000, 6)]), ("morale", 0, 60), ("money", 0, 100)])
    post = bytearray(pre)
    b = stage.apply(bytearray(pre), [("units", 0, [("hi", 5000, 7, 0, "1st Guards  Battalion"), ("li", 3000, 6, 0, "3rd Foot  Battalion")]), ("money", 0, 160), ("unity", 0, 800)])
    s0, s1 = sav.parse(bytes(pre)), sav.parse(bytes(b))
    x, y = battle.snapshot(s0, [0, 1], [0, 6]), battle.snapshot(s1, [0, 1], [0, 6])
    d = battle.diff(x, y, 0, 1)
    a = d["attacker"]
    assert d["winner"] in ("none", "defender", "attacker", "both")
    assert a["loss"] == 17000 - 8000 and a["type_loss"] == {"li": 2000, "hi": 7000, "ar": 0, "lc": 0, "hc": 0}, a
    assert [u["destroyed"] for u in a["units"]] == [False, True, False], a["units"]
    assert a["promotions"] and a["money"] == (100, 160) and d["nations"][0]["unity"][1] == 800, d


def test_new_news():
    assert battle.new_news(["a", "b"], ["a", "b", "c"]) == ["c"]
    assert battle.new_news(["a", "b", "c"], ["b", "c", "d"]) == ["d"] and battle.new_news([], ["x"]) == ["x"] and battle.new_news(["a"], ["a"]) == []


def test_b0_pair_if_present():
    if not all(p.exists() for p in B0_PAIR):
        print("   (B0 pair not on this machine: synthetic tests only)")
        return
    d = battle.diff(*[battle.snapshot(sav.load(str(p)), [0, 10], [0, 6]) for p in B0_PAIR], 0, 10)
    g = d["defender"]
    assert d["winner"] == "defender" and (g["troops_before"], g["troops_after"]) == (46700, 17239), g
    assert g["type_before"]["li"] == 35800 and g["type_before"]["hi"] == 10900, "per-type totals sum every unit (the gallic bug kept the last)"
    assert d["taken"]["defender_money"] == 156 and d["news"] == ["Gaul destroys army of Rome."], d


def live():
    """Open an edited save in the game and read army 0's record back from memory."""
    sys.path.insert(0, str(ROOT))
    from harness.driver import Game
    d = tmp() / "STAGE_LIVE.SAV"
    stage.edit(SRC, d, [("units", 0, [("hi", 6000, 6), ("lc", 7000, 7)]), ("morale", 0, 65), ("supplies", 0, 321), ("money", 0, 77), ("unity", 0, 555)])
    g = Game()
    try:
        g.load(d, seed=1)
        a, n = g.army_state(0), g.nation_state(0)
        assert [(u["type"], u["troops"], u["quality"]) for u in a["units"]] == [("hi", 6000, 6), ("lc", 7000, 7)], a["units"]
        assert (a["morale"], a["supplies"], a["money"], n["unity"]) == (65, 321, 77, 555), (a["morale"], a["supplies"], a["money"], n["unity"])
        print("PASS live: the game reads back the edited army 0 and Rome's unity")
    finally:
        g.kill()


if __name__ == "__main__":
    if "live" in sys.argv:
        live()
        sys.exit(0)
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as e:      # noqa: BLE001
                fails += 1
                print("FAIL", name, type(e).__name__, e)
    sys.exit(1 if fails else 0)
