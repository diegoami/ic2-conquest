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
    assert o[0] == ("move", 0, None, 60, 60), o                      # 10 moves: this turn's leg of the 20-tile walk
    near = state([army(0, ME, 52, 52, 5000)])                     # 2 tiles out: since 2026-11-05 it closes in (HOME = 1)
    o = ops(near)
    assert o[0][0] == "move" and max(abs(o[0][3] - 50), abs(o[0][4] - 50)) == 1, o
    home = state([army(0, ME, 51, 51, 5000)])
    assert not ops(home), ops(home)


def starving(i, x, y, troops=20000):
    a = army(i, ME, x, y, troops, supply_pct=0)
    a["supplies"] = 0
    return a


def test_supply_buys_from_the_adjacent_city_with_the_most_stock():
    s = state([starving(0, 60, 60)], cities=[city(10, 61, 60, ME, supplies=0), city(11, 59, 60, ME, supplies=400),
                                             city(12, 60, 61, ME, supplies=150)])
    assert ops(s)[0] == ("buy_supply", 0, 11, None, None), ops(s)
    o = [x for x in B.decide(s) if x["op"] == "buy_supply"][0]
    assert o["tons"] == 200, o                                        # need 20000//100 + 1 - 0 = 201 -> 200


def test_supply_marches_to_a_stocked_city_when_the_neighbours_are_dry():
    s = state([starving(0, 60, 60)], cities=[city(10, 61, 60, ME, supplies=0), city(11, 70, 60, ME, supplies=500),
                                             city(12, 66, 60, ME, supplies=50)])
    o = ops(s)
    assert o[0][0] == "move" and max(abs(o[0][3] - 70), abs(o[0][4] - 60)) == 1, o     # city 12 holds too little


def test_mobilization_waits_for_average_unless_desperate():
    slots = [{"state": 16, "city": 100, "troops": 1200}, {"state": 20, "city": 100, "troops": 1200},
             {"state": 24, "city": 100, "troops": 1200}]
    calm = state(me_kw={"recruit_slots": [dict(x) for x in slots]})
    assert [x for x in B.decide(calm) if x["op"] == "mobilize"] == [{"op": "mobilize", "slot": 2}]
    siege = state([army(1, FOE, 52, 50, 30000), army(0, ME, 51, 50, 5000)], me_kw={"recruit_slots": [dict(x) for x in slots]})
    assert B.desperate(siege, ME, siege["cities"][0], [siege["armies"][0]])
    assert [x["slot"] for x in B.decide(siege) if x["op"] == "mobilize"] == [2, 1, 0], B.decide(siege)
    held = state([army(1, FOE, 52, 50, 5000), army(0, ME, 51, 50, 30000)], me_kw={"recruit_slots": [dict(x) for x in slots]})
    assert not B.desperate(held, ME, held["cities"][0], [held["armies"][0]])


def fleet(i, x, y, ships=50, supplies=0, condition=60, owner=ME, army=-1):
    return {"id": i, "owner": owner, "x": x, "y": y, "ships": ships, "supplies": supplies, "condition": condition,
            "building": False, "army": army, "moves": 20}


def test_docked_fleet_is_supplied_and_repaired():
    s = state(cities=[city(10, 61, 60, ME, supplies=300)], me_kw={"treasury": 2000})
    s["fleets"] = [fleet(3, 60, 60)]
    o = [x for x in B.decide(s) if x["op"] in ("supply_fleet", "repair_fleet")]
    assert o == [{"op": "supply_fleet", "fleet": 3, "city": 10, "tons": 300},
                 {"op": "repair_fleet", "fleet": 3, "points": 40}], o    # cost 50 x 40 / 5 = 400, 1600 left
    poor = state(cities=[city(10, 61, 60, ME, supplies=300)], me_kw={"treasury": 1300})
    poor["fleets"] = [fleet(3, 60, 60)]
    assert not [x for x in B.decide(poor) if x["op"] == "repair_fleet"]   # would leave 900 < 1000
    full = state(cities=[city(10, 61, 60, ME, supplies=300)], me_kw={"treasury": 2000})
    full["fleets"] = [fleet(3, 60, 60, supplies=300, condition=90), fleet(4, 60, 60, army=2), fleet(5, 90, 90)]
    assert not [x for x in B.decide(full) if x["op"] in ("supply_fleet", "repair_fleet")], B.decide(full)


def test_mercenaries_are_paid_from_the_treasury():
    a = army(0, ME, 51, 50, 10000)
    a["units"] = [{"type": "li", "troops": 8000, "quality": 5, "merc": 0},             # a regular: the treasury pays it
                  {"type": "li", "troops": 11216, "quality": 7, "merc": 30}]           # Kardackians: 56 x 1 x 7 // 5 = 78
    a["money"] = 100
    assert B.mercenary_pay(a) == 78
    s = state([a], me_kw={"treasury": 2000})
    assert [x for x in B.decide(s) if x["op"] == "fund_army"] == [{"op": "fund_army", "army": 0, "money": 300}], B.decide(s)
    a["money"] = 200                                                                    # two quarters' pay is there
    assert not [x for x in B.decide(state([a], me_kw={"treasury": 2000})) if x["op"] == "fund_army"]
    a["money"] = 100
    assert not [x for x in B.decide(state([a], me_kw={"treasury": 1200})) if x["op"] == "fund_army"]   # reserve
    far = dict(a, x=70, y=70)
    assert not [x for x in B.decide(state([far], me_kw={"treasury": 2000})) if x["op"] == "fund_army"]  # no city


def test_supply_fleet_action_plumbing():
    import difftest.actions as A
    import difftest.remake as R
    a = A.validate({"op": "supply_fleet", "fleet": 3, "city": 10, "tons": 300})
    assert R.command(a) == "buy-fleet-supply {fleet:3} {city:10} 300", R.command(a)
    f = A.validate({"op": "fund_army", "army": 2, "money": 300})
    assert R.command(f) == "transfer-money {army:2} 300", R.command(f)


def test_march_detours_around_water_the_straight_line_crosses():
    s = state([army(0, ME, 60, 50, 5000, moves=12)])
    m = list(s["map"])
    for y in range(40, 60):
        m[55 * 140 + y] = 0                                          # a sea strip at x = 55, rows 40..59 (the map is column-major)
    s["map"] = tuple(m)
    o = ops(s)[0]
    assert o[0] == "move", o
    t = (o[3], o[4])
    assert all(B.cell(s, *u) in B.LAND for u in B.line((60, 50), t)), t   # the clicked straight line stays on land
    assert t[1] >= 59 or t[1] <= 40 or t[0] > 55, t                      # it heads round the strip's end


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
