"""Battle result reader and diff (battles plan §3.4): what a battle did to the strategic armies and nations, read from two saves (a
pre-attack save and a post-battle Save As) or from game memory (`Game.army_state` / `Game.nation_state`).

    from state import battle
    before, after = battle.snapshot(sav.load(pre), [0, 10], [0, 6]), battle.snapshot(sav.load(post), [0, 10], [0, 6])
    d = battle.diff(before, after, attacker=0, defender=10)

`by_type` is the per-type troop total of an army. (It replaces the dict comprehension
`{u["type"]: u["troops"] for u in army["units"]}` of `runs/experiments/gallic-army.py`, which kept only the LAST unit of each type.)
"""
from . import sav

UNIT_FIELDS = ("slot", "type", "troops", "quality", "merc", "name")


def by_type(army):
    """Troops per unit type (all five keys), summed over every unit of the army; {} for None (a destroyed army)."""
    if not army:
        return {}
    out = {t: 0 for t in sav.UNIT_TYPES}
    for u in army["units"]:
        out[u["type"]] += u["troops"]
    return out


def army_view(a):
    """The reader's record of one army: position, owner, morale, supplies, money, moves, every unit (slot, type, troops, quality, merc label)."""
    return {"id": a["id"], "x": a["x"], "y": a["y"], "owner": a["owner"], "moves": a["moves"], "morale": a["morale"],
            "supplies": a["supplies"], "money": a["money"], "troops": a["troops"], "units": [dict(u) for u in a["units"]],
            "by_type": by_type(a)}


def nation_view(n):
    return {"id": n["id"], "name": n["name"], "unity": n["unity"], "treasury": n["treasury"], "wealth": n["wealth"],
            "cities": n["cities_count"], "relations": dict(n["relations"]), "human": n["human"]}


def snapshot(s, armies, nations):
    """From a parsed save: the listed armies (an id whose record is a tombstone or empty reads as None) and nations, plus the news and the turn."""
    arm = {}
    for i in armies:
        a = s["armies"][i] if i < len(s["armies"]) else None
        arm[i] = army_view(a) if a and a["owner"] >= 0 and a["troops"] > 0 else None
    return {"turn": s["turn"], "battle_flag": s["battle_flag"], "armies": arm,
            "nations": {n: nation_view(s["nations"][n]) for n in nations}, "news": list(s["news"])}


def new_news(before, after):
    """News lines in `after` that are not in `before` (the log is a window of 40: match the longest suffix of the old list with a prefix of the new)."""
    for k in range(min(len(before), len(after)), -1, -1):
        if k == 0 or before[len(before) - k:] == after[:k]:
            return after[k:]
    return list(after)


def _match_units(bu, au):
    """Pair units of the before list with units of the after list. Slots are packed (a dead unit is swapped out), so the slot index is
    not an identity: the key is (name, type), duplicates are paired in slot order. Returns [(before_unit, after_unit_or_None)]."""
    pool = {}
    for u in au:
        pool.setdefault((u["name"], u["type"]), []).append(u)
    pairs = []
    for u in bu:
        lst = pool.get((u["name"], u["type"]), [])
        pairs.append((u, lst.pop(0) if lst else None))
    return pairs


def army_diff(b, a):
    """One army before/after: units (loss, promotion), per-type totals and losses, morale/supplies/money deltas. `a` None = destroyed."""
    units = []
    for u0, u1 in _match_units(b["units"], a["units"] if a else []):
        t1 = u1["troops"] if u1 else 0
        units.append({"name": u0["name"], "type": u0["type"], "troops_before": u0["troops"], "troops_after": t1, "loss": u0["troops"] - t1,
                      "destroyed": u1 is None, "quality_before": u0["quality"], "quality_after": u1["quality"] if u1 else None,
                      "promoted": bool(u1 and u1["quality"] > u0["quality"]), "merc": u0["merc"]})
    tb, ta = by_type(b), by_type(a)
    return {"id": b["id"], "destroyed": a is None, "troops_before": b["troops"], "troops_after": a["troops"] if a else 0,
            "loss": b["troops"] - (a["troops"] if a else 0), "units": units,
            "type_before": tb, "type_after": ta, "type_loss": {t: tb[t] - ta.get(t, 0) for t in tb},
            "promotions": [u["name"] for u in units if u["promoted"]],
            "morale": (b["morale"], a["morale"] if a else None), "supplies": (b["supplies"], a["supplies"] if a else None),
            "money": (b["money"], a["money"] if a else None), "position": ((b["x"], b["y"]), (a["x"], a["y"]) if a else None)}


def diff(before, after, attacker, defender):
    """What the battle did: the two armies' diffs, the winner ("attacker", "defender", "none" if both survive, "both" if both are gone),
    each side's money/supplies change, the nations' unity/treasury/relation changes and the new news lines."""
    ad = army_diff(before["armies"][attacker], after["armies"][attacker])
    dd = army_diff(before["armies"][defender], after["armies"][defender])
    win = "both" if ad["destroyed"] and dd["destroyed"] else "defender" if ad["destroyed"] else "attacker" if dd["destroyed"] else "none"
    nat = {}
    for n, b in before["nations"].items():
        a = after["nations"][n]
        nat[n] = {"unity": (b["unity"], a["unity"]), "treasury": (b["treasury"], a["treasury"]),
                  "relations_changed": {k: (v, a["relations"][k]) for k, v in b["relations"].items() if a["relations"][k] != v}}
    return {"winner": win, "attacker": ad, "defender": dd, "nations": nat, "news": new_news(before["news"], after["news"]),
            "taken": {"attacker_money": ad["money"][1] - ad["money"][0] if not ad["destroyed"] else None,
                      "defender_money": dd["money"][1] - dd["money"][0] if not dd["destroyed"] else None,
                      "attacker_supplies": ad["supplies"][1] - ad["supplies"][0] if not ad["destroyed"] else None,
                      "defender_supplies": dd["supplies"][1] - dd["supplies"][0] if not dd["destroyed"] else None}}
