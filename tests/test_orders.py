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


def test_disband_army():
    """Disband army 0, which sits beside Arretium (its own city)."""
    g, _ = fresh("disbandarmy")
    before = len(live_armies(load(BASE), 0))
    g.disband_army(0)
    p = keep(g.save_as("T_DISBAND_ARMY.SAV"), "T_DISBAND_ARMY.SAV")
    s = load(p)
    after = len(live_armies(s, 0))
    assert after == before - 1, (before, after, [(a["id"], a["x"], a["y"]) for a in live_armies(s, 0)])
    return f"Roman armies {before} -> {after}, treasury {s['nations'][0]['treasury']}"


def test_build_fleet():
    """Build a 10-ship fleet. Cost is ships x 10 talents, and it starts a
    countdown at a free coastal city."""
    g, _ = fresh("fleet")
    s0 = load(BASE)
    before = len([f for f in s0["fleets"] if f["owner"] == 0])
    g.build_fleet(10)
    p = keep(g.save_as("T_FLEET.SAV"), "T_FLEET.SAV")
    s = load(p)
    fl = [f for f in s["fleets"] if f["owner"] == 0]
    assert len(fl) == before + 1, [(f["id"], f["building"], f["countdown"], f["ships"]) for f in fl]
    new = fl[-1]
    return f"Rome fleets {before} -> {len(fl)} (ships {new['ships']}, building {new['building']}, " \
           f"countdown {new['countdown']}); treasury {s0['nations'][0]['treasury']} -> {s['nations'][0]['treasury']}"


def test_split_army():
    """Split army 0's first unit off into a new army."""
    g, _ = fresh("split")
    s0 = load(BASE)
    before = len(live_armies(s0, 0))
    troops0 = sum(a["troops"] for a in live_armies(s0, 0))
    g.split_army(0, unit_rows=(0,))
    p = keep(g.save_as("T_SPLIT.SAV"), "T_SPLIT.SAV")
    s = load(p)
    arm = live_armies(s, 0)
    troops = sum(a["troops"] for a in arm)
    assert len(arm) == before + 1, [(a["id"], a["x"], a["y"], a["troops"]) for a in arm]
    assert troops == troops0, (troops, troops0)
    return f"Roman armies {before} -> {len(arm)} (troops {troops0} -> {troops}); " \
           f"{[(a['id'], a['x'], a['y'], a['troops']) for a in arm]}"


def test_change_units_disband():
    """Disband one unit from army 0 through the Change units dialog."""
    g, _ = fresh("changeunits")
    s0 = load(BASE)
    a0 = next(a for a in live_armies(s0, 0) if a["id"] == 0)
    g.change_units_disband(0, unit_row=0)
    p = keep(g.save_as("T_CHUNITS.SAV"), "T_CHUNITS.SAV")
    s = load(p)
    a1 = next(a for a in live_armies(s, 0) if a["id"] == 0)
    assert len(a1["units"]) == len(a0["units"]) - 1, (len(a0["units"]), len(a1["units"]), a1["units"])
    assert a1["troops"] < a0["troops"], (a0["troops"], a1["troops"])
    return f"army 0 {a0['troops']} t / {len(a0['units'])} units -> {a1['troops']} t / {len(a1['units'])} units"


def test_transfer_units():
    """Two turns to put armies 0 and 1 adjacent, then transfer a unit from army 0
    to army 1. Troops move between them; the total is unchanged."""
    import struct
    g, _ = fresh("transfer")
    g.move(1, 113, 45)
    g.end_turn()
    g.move(1, 104, 36)
    g.move(0, 103, 36)

    def mem(i):                         # (units, troops) of the running army
        rec = g.army_rec(i)
        us = [struct.unpack_from("<4h", rec, 16 + 32 * k) for k in range(20)]
        us = [u for u in us if u[2] > 0]
        return len(us), sum(u[2] for u in us)

    u0, t0 = mem(0)
    u1, t1 = mem(1)
    g.transfer_units(0, unit_row=0)
    p = keep(g.save_as("T_TRANSFER.SAV"), "T_TRANSFER.SAV")
    s = load(p)
    a0 = next(a for a in live_armies(s, 0) if a["id"] == 0)
    a1 = next(a for a in live_armies(s, 0) if a["id"] == 1)
    assert len(a0["units"]) == u0 - 1 and len(a1["units"]) == u1 + 1, \
        (u0, len(a0["units"]), u1, len(a1["units"]))
    assert a0["troops"] + a1["troops"] == t0 + t1, (a0["troops"], a1["troops"], t0, t1)
    return f"army0 {t0}t/{u0}u -> {a0['troops']}t/{len(a0['units'])}u; " \
           f"army1 {t1}t/{u1}u -> {a1['troops']}t/{len(a1['units'])}u"


TESTS = ["move", "recruit", "end_turn", "scripted_turn_repeats", "attack", "join",
         "taxation", "disband_unit", "disband_army", "build_fleet", "split_army",
         "change_units_disband", "transfer_units"]

if __name__ == "__main__":
    names = sys.argv[1:] or TESTS
    for n in names:
        t = time.time()
        try:
            r = globals()["test_" + n]()
            print(f"PASS {n} ({time.time() - t:.0f}s): {r}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {n} ({time.time() - t:.0f}s): {type(e).__name__}: {e}", flush=True)
