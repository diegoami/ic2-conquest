#!/usr/bin/env python3
"""Offline tests of rulebot-2 (difftest/bot2.py) and of its End turn with "peace": true through the action format, the
original's driver call, the remake runner and the campaign. Synthetic states, built from scratch (an all-land map, chosen
armies and cities), so each rule is seen alone. No Wine, no remake.

    python3 -m tests.test_bot2     (exit 1 on a failure)
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import difftest.bot2 as B  # noqa: E402
from state.sav import NATIONS  # noqa: E402

ME, FOE, NEUTRAL = 0, 6, 3          # Rome, Gaul (at war), Ptolemaic (at peace)


def nation(i, **kw):
    n = {"name": NATIONS[i], "tax": 15, "treasury": 0, "recruit_slots": [], "capital": 100 + i,
         "relations": {NATIONS[j]: 0 for j in range(16) if j != i}}
    n.update(kw)
    return n


def army(i, owner, x, y, troops=10000, kind="hi", moves=10, morale=70, supply_pct=100):
    return {"id": i, "owner": owner, "x": x, "y": y, "troops": troops, "moves": moves, "embarked": False, "morale": morale,
            "supply_pct": supply_pct, "supplies": 1000, "units": [{"type": kind, "troops": troops}]}


def city(i, x, y, owner, allegiance=None, loyalty=60, fort=10, pop=20, supplies=100):
    return {"id": i, "x": x, "y": y, "owner": owner, "allegiance": owner if allegiance is None else allegiance,
            "loyalty": loyalty, "fort": fort, "pop": pop, "supplies": supplies}


def state(armies=(), cities=(), me_kw=None):
    ns = [nation(i) for i in range(16)]
    ns[ME].update(me_kw or {})
    ns[ME]["relations"]["Gaul"] = 3
    ns[FOE]["relations"]["Rome"] = 3
    cs = [city(100 + ME, 50, 50, ME)] + list(cities)          # Rome's capital at (50,50)
    return {"current_nation": ME, "nations": ns, "cities": cs, "armies": list(armies), "map": tuple([2] * (320 * 140))}


def ops(s):
    return [(o["op"], o.get("army"), o.get("target", o.get("city")), o.get("x"), o.get("y")) for o in B.decide(s)]


def test_tax_recruit_and_one_mobilization():
    s = state(me_kw={"tax": 20, "treasury": 1500, "recruit_slots": [
        {"state": 22, "city": 100, "troops": 1200}, {"state": 24, "city": 100, "troops": 1200},
        {"state": 24, "city": 100, "troops": 1200}]})
    o = B.decide(s)
    assert o[0] == {"op": "set_tax", "percent": 15}, o
    assert {"op": "recruit", "city": 100, "type": "hi", "troops": 1200} in o
    assert [x for x in o if x["op"] == "mobilize"] == [{"op": "mobilize", "slot": 1}], o      # first ready only


def test_counter_attack_only_with_the_odds():
    weak = state([army(0, ME, 50, 52, 12000), army(1, FOE, 51, 53, 6000)])
    assert ops(weak)[0][:3] == ("attack_army", 0, 1), ops(weak)
    even = state([army(0, ME, 50, 52, 10000), army(1, FOE, 51, 53, 9000)])     # 1.11x < 1.3x: no attack
    assert not any(o[0] == "attack_army" for o in ops(even)), ops(even)


def test_never_targets_a_nation_not_at_war():
    s = state([army(0, ME, 50, 52, 50000), army(1, NEUTRAL, 51, 53, 1000)])
    assert not any(o[0] in ("attack_army", "besiege") for o in ops(s)), ops(s)
    s = state([army(0, ME, 55, 55, 50000)], [city(7, 56, 56, NEUTRAL, allegiance=ME)])   # our core, but held at peace
    assert not any(o[0] == "besiege" for o in ops(s)), ops(s)


def test_reconquer_adjacent_core_city_when_the_siege_wins():
    easy = state([army(0, ME, 55, 55, 30000)], [city(7, 56, 56, FOE, allegiance=ME, loyalty=40, fort=5, pop=10)])
    assert ops(easy)[0][:3] == ("besiege", 0, 7), ops(easy)
    hard = state([army(0, ME, 55, 55, 3000)], [city(7, 56, 56, FOE, allegiance=ME, loyalty=95, fort=90, pop=200)])
    assert not any(o[0] == "besiege" for o in ops(hard)), ops(hard)
    not_core = state([army(0, ME, 55, 55, 30000)], [city(7, 56, 56, FOE, allegiance=FOE, loyalty=40, fort=5, pop=10)])
    assert not any(o[0] == "besiege" for o in ops(not_core)), ops(not_core)                # only core towns


def test_intercept_invaders_near_own_cities_only():
    s = state([army(0, ME, 50, 51, 20000), army(1, FOE, 54, 50, 5000)])        # 4 tiles from Rome: an invader
    o = ops(s)
    assert o[0][0] == "move" and o[0][1] == 0 and max(abs(o[0][3] - 54), abs(o[0][4] - 50)) == 1, o
    far = state([army(0, ME, 50, 51, 20000), army(1, FOE, 90, 90, 5000)])      # far away: not an invader
    assert not any(x[0] == "move" for x in ops(far)), ops(far)


def test_garrison_returns_to_the_capital():
    s = state([army(0, ME, 70, 70, 5000)])
    o = ops(s)
    assert o[0][0] == "move" and max(abs(o[0][3] - 50), abs(o[0][4] - 50)) == 1, o
    home = state([army(0, ME, 52, 52, 5000)])
    assert not ops(home), ops(home)


def test_field_and_siege_strength_and_defence():
    a = army(0, ME, 0, 0, 8000, "ar", morale=80)
    assert B.field_strength(a) == 40 * 80 / 80 * 80          # sum(w x troops/100)/80 x morale = 3200/80*80
    assert B.siege_strength(a) == 8000 * 3 // 80 * 80
    s = state()
    c = city(7, 1, 1, FOE, allegiance=ME, loyalty=60, fort=10, pop=20)
    assert B.city_defence(s, c, ME) == (60 * 150 + 10 * 250 + 20 * 200) * 4 // 5 * 9 // 10


def test_end_turn_with_peace_through_the_plumbing():
    import difftest.actions as A
    import difftest.original as O
    import difftest.remake as R
    import difftest.campaign as K
    e = B.end_turn(state())
    assert e == {"op": "end_turn", "peace": True} and A.validate(e) is e
    try:
        A.validate({"op": "end_turn", "peace": "yes"})
        raise AssertionError("a non-bool peace passed")
    except A.ActionError:
        pass
    seen = {}
    g = types.SimpleNamespace(end_turn=lambda peace=False, **kw: seen.setdefault("peace", peace) and ("AUTO0721.SAV", []) or ("AUTO0721.SAV", []))
    O.perform(g, e, {})
    assert seen["peace"] is True
    calls = {}
    saved = R.subprocess.run

    class Done(Exception):
        pass

    def fake_run(cmd, **kw):
        calls["cmd"] = cmd
        raise Done
    R.subprocess.run = fake_run
    try:
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
            try:
                R.run([e], ROOT / "saves/det-AUTO0721-seed12345.SAV", Path(tmp) / "r", log=lambda *x: None)
            except Done:
                pass
    finally:
        R.subprocess.run = saved
    assert "peace=yes" in calls["cmd"], calls["cmd"]
    assert K.end_action(B, state()) == e and K.end_action(types.SimpleNamespace(), state()) == {"op": "end_turn"}


TESTS = [n for n in sorted(globals()) if n.startswith("test_")]

if __name__ == "__main__":
    bad = 0
    for n in TESTS:
        try:
            globals()[n]()
            print("PASS", n)
        except Exception as ex:  # noqa: BLE001
            bad += 1
            import traceback
            print("FAIL", n, type(ex).__name__, ex)
            traceback.print_exc(limit=3)
    sys.exit(1 if bad else 0)
