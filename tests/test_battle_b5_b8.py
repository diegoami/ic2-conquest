"""Offline tests of the B5 tabulation and the B8 ladder planner (no game)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
import b5_analyze as A  # noqa: E402
import b8_ladder as L  # noqa: E402


def test_ladder_has_the_named_rungs_and_caps():
    for t, std in (("li", 15000), ("hi", 6000), ("ar", 3500), ("lc", 7000), ("hc", 2500)):
        v = L.ladder(t)
        assert v == sorted(set(v)) and v[0] == 100 and v[-1] == 32767 and max(v) <= 32767
        for f in (0.25, 0.5, 1):
            assert round(std * f) in v
        assert min(32767, 2 * std) in v


def test_predicted_thresholds_are_the_first_troop_count_of_each_class():
    assert L.predicted("hi") == (2000, 4000) and L.predicted("li") == (5000, 10000)
    assert L.predicted("ar") == (1166, 2332) and L.predicted("hc") == (833, 1666) and L.predicted("lc") == (2333, 4666)   # [R-code]
    assert L.hypothesis_b2("ar") == (1167, 2334)           # the earlier B2 hypothesis differs by 1-2 troops


def test_probes_close_a_bracket_to_one_troop():
    obs = {1000: 0, 2000: 1, 4000: 1, 6000: 2}           # HI: classes change inside (1000, 2000) and (4000, 6000)
    p = L.next_probes("hi", obs)
    assert 1999 in p and 2000 not in p and 3999 not in p and 4000 not in p and len(p) <= L.MAXU      # 2000 and 4000 are observed already
    obs.update({1999: 0, 5999: 2, 4001: 2})
    assert L.brackets(obs)[1] == [(1999, 2000), (4000, 4001)] and L.next_probes("hi", obs) == []


def test_spread_is_inside_and_distinct():
    for lo, hi, n in ((0, 10, 3), (0, 5, 12), (100, 100, 3), (0, 100000, 5)):
        s = L.spread(lo, hi, n)
        assert all(lo < x < hi for x in s) and len(s) == len(set(s)) <= max(n, 0) + (hi - lo - 1 if hi - lo - 1 <= n else 0)


def test_target_rank_by_distance_troops():
    def row(hr, slots):
        return {"half_round": hr, "slots": slots}
    sl = lambda slot, side, x, y, tr, tg, typ="hi": {"slot": slot, "side": side, "type": typ, "x": x, "y": y, "troops": tr, "target": tg}
    prev = row(5, [sl(0, 0, 0, 0, 100, -1), sl(20, 1, 0, 2, 500, -1), sl(21, 1, 5, 5, 50, -1)])
    cur = row(6, [sl(0, 0, 0, 1, 100, 20), sl(20, 1, 0, 2, 500, -1), sl(21, 1, 5, 5, 50, -1)])
    ev = A.targets_events([prev, cur])
    assert len(ev) == 1 and ev[0]["is_nearest"] and ev[0]["enemies_strictly_nearer"] == 0 and not ev[0]["is_weakest"] and ev[0]["enemies_strictly_weaker"] == 1
    cur2 = row(6, [sl(0, 0, 0, 1, 100, 21), sl(20, 1, 0, 2, 500, -1), sl(21, 1, 5, 5, 50, -1)])
    ev = A.targets_events([prev, cur2])
    assert not ev[0]["is_nearest"] and ev[0]["enemies_strictly_nearer"] == 1 and ev[0]["is_weakest"]
    assert ev[0]['prev_is_nearest'] is False or 'prev_is_nearest' in ev[0]      # the previous-snapshot columns exist when the enemy stood there
    one_enemy = row(6, [sl(0, 0, 0, 1, 100, 20), sl(20, 1, 0, 2, 500, -1)])
    assert A.targets_events([row(5, [sl(0, 0, 0, 0, 100, -1), sl(20, 1, 0, 2, 500, -1)]), one_enemy]) == []


def _blk(slots):
    from state import battle_block as BB
    full = []
    for k in range(40):
        d = slots.get(k)
        full.append({"slot": k, "side": 0 if k < 20 else 1, "alive": bool(d), "troops": d["troops"] if d else 0, "ammo": d.get("ammo", 0) if d else 0,
                     "target": d.get("target", -1) if d else -1})
    return {"slots": full}


def test_attribute_uses_words_8_and_9():
    from state import battle_block as BB
    a = _blk({0: {"troops": 100, "target": 20}, 20: {"troops": 100}})
    b = _blk({0: {"troops": 90, "target": -1}, 20: {"troops": 80}})
    r = BB.attribute(a, b)
    assert r["losses"] == 2 and r["fixed"] == 2 and r["rows"][20]["links"] == [(0, 20)] and r["rows"][0]["kind"] == "melee"
    # one archer shoots (ammo falls) at one of two enemies that both lost troops: the shooter is known, the target is not
    a = _blk({0: {"troops": 100, "ammo": 25}, 20: {"troops": 100}, 21: {"troops": 100}})
    b = _blk({0: {"troops": 100, "ammo": 21}, 20: {"troops": 90}, 21: {"troops": 95}})
    r = BB.attribute(a, b)
    assert r["by_kind"]["shooting"] == 2 and r["fixed"] == 0 and r["rows"][20]["actors"] == [0]
    # a single loser with a single shooter is fixed
    b2 = _blk({0: {"troops": 100, "ammo": 21}, 20: {"troops": 90}, 21: {"troops": 100}})
    assert BB.attribute(a, b2)["fixed"] == 1
    # a link to an own-side slot (the placeholder target 0 of an attacker at BATTLE01) is not a melee link
    a = _blk({0: {"troops": 100, "target": 0}, 1: {"troops": 100, "target": 0}})
    assert BB.attribute(a, _blk({0: {"troops": 90}, 1: {"troops": 100}}))["rows"][0]["kind"] == "unknown"


if __name__ == "__main__":
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
