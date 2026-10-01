"""Order-driver tests: each order is issued headless through the game's UI and
checked on the save diff against a baseline loaded with the same seed.

    python3 -m tests.test_orders [name ...]     # or: pytest tests/test_orders.py

Needs setup/setup.sh done and a start save: $IC2_WORK/fixtures/BASE.SAV
(270 BC Spring week 1, Rome human; tests/make_base.sh makes it). Each test
prints its result line; tests/results.md records the last full run.
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harness.driver import G, WORK, Game  # noqa: E402
from state.sav import load, live_armies  # noqa: E402

BASE = WORK / "fixtures" / "BASE.SAV"
SEED = 12345
OUT = WORK / "tests"


def fresh(name):
    OUT.mkdir(parents=True, exist_ok=True)
    g = Game()
    popups = g.load(BASE, seed=SEED)
    return g, popups


def keep(path, name):
    dst = OUT / name
    shutil.copy(path, dst)
    return dst


def diff(a, b):
    """Byte offsets that differ, grouped into (start, length) runs."""
    x, y = Path(a).read_bytes(), Path(b).read_bytes()
    runs, i = [], 0
    n = min(len(x), len(y))
    while i < n:
        if x[i] != y[i]:
            j = i
            while j < n and x[j] != y[j]:
                j += 1
            runs.append((i, j - i))
            i = j
        else:
            i += 1
    return runs, len(x), len(y)


def baseline():
    g, _ = fresh("baseline")
    p = keep(g.save_as("T_BASE.SAV"), "T_BASE.SAV")
    return g, p


def test_move():
    g, base = baseline()
    s0 = load(base)
    a0 = s0["armies"][0]
    pos, texts = g.move(0, a0["x"] + 1, a0["y"] - 1)
    p = keep(g.save_as("T_MOVE.SAV"), "T_MOVE.SAV")
    s1 = load(p)
    a1 = s1["armies"][0]
    assert (a1["x"], a1["y"]) == pos != (a0["x"], a0["y"]), (a0, a1)
    assert a1["moves"] < a0["moves"]
    others = [(x["id"], x["x"], x["y"]) for x in s1["armies"] if x["id"] != 0]
    assert others == [(x["id"], x["x"], x["y"]) for x in s0["armies"] if x["id"] != 0]
    return f"army 0 ({a0['x']},{a0['y']}) -> ({a1['x']},{a1['y']}), moves {a0['moves']} -> {a1['moves']}, " \
           f"cell {a0['cell']} -> {a1['cell']}, diff runs {len(diff(base, p)[0])}, popups {texts}"


def test_recruit():
    g, base = baseline()
    s0 = load(base)
    texts = g.recruit(city_row=1, unit_type="hi", thousands=2)     # rows: Luceria, ROME
    p = keep(g.save_as("T_RECRUIT.SAV"), "T_RECRUIT.SAV")
    s1 = load(p)
    r0, r1 = s0["nations"][0], s1["nations"][0]
    new = [q for q in r1["recruit_slots"] if q not in r0["recruit_slots"]]
    assert len(new) == 1 and new[0]["type"] == "hi" and new[0]["city"] == 85 and new[0]["state"] == 0, new
    cost = (new[0]["troops"] // 200) * 20
    assert r0["treasury"] - r1["treasury"] == cost, (r0["treasury"], r1["treasury"], cost)
    mob = min(100, r0["mobilization"] + 1 + new[0]["troops"] * 1000 // r0["wealth"])
    assert r1["mobilization"] == mob, (r1["mobilization"], mob)
    return f"slot {new[0]}, treasury {r0['treasury']} -> {r1['treasury']} (cost {cost}), " \
           f"mobilization {r0['mobilization']} -> {r1['mobilization']}, popups {texts}"


def test_end_turn():
    g, base = baseline()
    name, texts = g.end_turn()
    p = keep(G / name, "T_END_" + name)
    s0, s1 = load(base), load(p)
    assert s1["turn"] == s0["turn"] + 1, (s0["turn"], s1["turn"])
    return f"{base.name} turn {s0['turn']} -> {name} turn {s1['turn']} ({s1['date']}); popups {texts}"


def scripted_turn(tag):
    """Phase 0's criterion: one scripted turn (a move plus a recruit), ended."""
    g, _ = fresh(tag)
    g.move(0, 101, 36)
    g.recruit(city_row=1, unit_type="hi", thousands=2)
    name, texts = g.end_turn()
    return keep(G / name, f"T_SCRIPTED_{tag}_{name}"), g.seed_line, texts


def test_scripted_turn_repeats():
    a, seed_a, ta = scripted_turn("a")
    b, seed_b, tb = scripted_turn("b")
    runs, la, lb = diff(a, b)
    assert seed_a == seed_b and not runs and la == lb, (seed_a, seed_b, runs[:5], la, lb)
    s = load(a)
    return f"{a.name} == {b.name} byte for byte ({la} B, seed {seed_a}); {s['date']}; " \
           f"army 0 at ({s['armies'][0]['x']},{s['armies'][0]['y']}), Rome queue {len(s['nations'][0]['recruit_slots'])} slots"


def test_attack():
    """Two turns: march army 0 next to Felsina (Gaul), end the turn, besiege it."""
    g, _ = fresh("attack")
    s0 = load(BASE)
    felsina = next(c for c in s0["cities"] if c["name"] == "Felsina")
    g.move(0, 99, 34)
    name, texts = g.end_turn()
    s1 = load(G / name)
    a = s1["armies"][0]
    for step in [(99, 33), (99, 32)]:
        if max(abs(a["x"] - felsina["x"]), abs(a["y"] - felsina["y"])) == 1:
            break
        g.move(0, *step)
        a = {"x": g.army_pos(0)[0], "y": g.army_pos(0)[1]}
    texts = g.attack(0, felsina["x"], felsina["y"])
    p = keep(g.save_as("T_ATTACK.SAV"), "T_ATTACK.SAV")
    s2 = load(p)
    f1 = next(c for c in s1["cities"] if c["id"] == felsina["id"])
    f2 = next(c for c in s2["cities"] if c["id"] == felsina["id"])
    a1, a2 = s1["armies"][0], s2["armies"][0]
    assert a2["moves"] == 0, a2
    assert a2["troops"] < a1["troops"], (a1["troops"], a2["troops"])          # siege attrition, win or lose
    return f"army 0 {a1['troops']} -> {a2['troops']} troops; Felsina owner {f1['owner']} -> {f2['owner']}, " \
           f"loyalty {f1['loyalty']} -> {f2['loyalty']}, fort {f1['fort']} -> {f2['fort']}, pop {f1['pop']} -> {f2['pop']}; " \
           f"news tail {s2['news'][-3:]}; popups {texts}"


def test_join():
    """Two turns: army 1 walks to (113,45) on turn 1, then both close in on
    (104,36)/(103,36) on turn 2 and join into one army."""
    g, _ = fresh("join")
    s0 = load(BASE)
    before = {a["id"]: a["troops"] for a in live_armies(s0, 0)}
    g.move(1, 113, 45)
    g.end_turn()
    g.move(1, 104, 36)
    g.move(0, 103, 36)
    a0, a1 = g.army_pos(0), g.army_pos(1)
    assert max(abs(a0[0] - a1[0]), abs(a0[1] - a1[1])) == 1, ("not adjacent", a0, a1)
    texts = g.join(0)
    p = keep(g.save_as("T_JOIN.SAV"), "T_JOIN.SAV")
    s2 = load(p)
    armies = live_armies(s2, 0)
    total = sum(a["troops"] for a in armies)
    assert len(armies) == 1, [(a["id"], a["x"], a["y"], a["troops"]) for a in armies]
    assert total == sum(before.values()), (total, before)
    a = armies[0]
    return f"armies {before} -> army {a['id']} at ({a['x']},{a['y']}), {a['troops']} troops, " \
           f"{len(a['units'])} units; popups {texts}"


def test_taxation():
    """One turn: set Rome's tax to 20% through the Change tax level slider."""
    g, _ = fresh("tax")
    g.taxation(20)
    p = keep(g.save_as("T_TAX.SAV"), "T_TAX.SAV")
    s = load(p)
    r = s["nations"][0]
    assert r["tax"] == 20, ("tax", r["tax"])
    return f"Rome tax -> {r['tax']}%, treasury {r['treasury']}, unity {r['unity']}"


def test_disband_unit():
    """Recruit a unit at Rome (+1 to the queue), then disband the first queued
    unit (-1). The queue starts with four at Rome, so the count is unchanged."""
    g, _ = fresh("disband")
    before = len(load(BASE)["nations"][0]["recruit_slots"])
    g.recruit(city_row=1, unit_type="hi", thousands=2)      # 3,200 HI queued at Rome
    g.disband_unit(city_row=1, unit_row=0)                  # remove the first queued unit
    p = keep(g.save_as("T_DISBAND.SAV"), "T_DISBAND.SAV")
    r = load(p)["nations"][0]
    assert len(r["recruit_slots"]) == before, (before, r["recruit_slots"])
    return f"Rome queue {before} -> {len(r['recruit_slots'])} (recruit +1, disband -1), treasury {r['treasury']}"


TESTS = ["move", "recruit", "end_turn", "scripted_turn_repeats", "attack", "join",
         "taxation", "disband_unit"]

if __name__ == "__main__":
    names = sys.argv[1:] or TESTS
    for n in names:
        t = time.time()
        try:
            r = globals()["test_" + n]()
            print(f"PASS {n} ({time.time() - t:.0f}s): {r}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {n} ({time.time() - t:.0f}s): {type(e).__name__}: {e}", flush=True)
