"""P1 strength: matchup-weighted melee power from the real melee matrix (DAT 0x1F7A6, docs/rules-digest.md §6).

For each unit u of side A, its power against side B is the troop-weighted mean over B's units d of
    M[u.type][d.type] * u.troops * (u.quality*10 + morale) div 2000 + 12
(the power term of the melee formula, morale = the army's strategic morale as a proxy for the unit's
battle-start morale). S(A vs B) is the sum over A's units. P1 asks S(Rome vs enemy) >= S(enemy vs Rome) * k.
Raw troop ratios are reported beside it.
"""
M = {"li": {"li": 15, "hi": 4, "ar": 20, "lc": 5, "hc": 3},
     "hi": {"li": 60, "hi": 5, "ar": 65, "lc": 15, "hc": 8},
     "ar": {"li": 10, "hi": 3, "ar": 18, "lc": 5, "hc": 3},
     "lc": {"li": 25, "hi": 8, "ar": 28, "lc": 15, "hc": 8},
     "hc": {"li": 18, "hi": 12, "ar": 20, "lc": 12, "hc": 8}}


def power(a, b, morale_bonus=0):
    """S(a vs b): army dicts as state.sav.parse_army returns them. A computer-played side gets +3 morale on battle entry."""
    tb = sum(u["troops"] for u in b["units"]) or 1
    m = a["morale"] + morale_bonus
    s = 0.0
    for u in a["units"]:
        for d in b["units"]:
            s += (M[u["type"]][d["type"]] * u["troops"] * (u["quality"] * 10 + m) // 2000 + 12) * d["troops"] / tb
    return round(s)


def ratio(a, b):
    pa, pb = power(a, b), power(b, a, morale_bonus=3)
    return pa, pb, (pa / pb if pb else float("inf")), (a["troops"] / b["troops"] if b["troops"] else float("inf"))


def line(a, b):
    pa, pb, r, raw = ratio(a, b)
    return "P1 army %d (%d) vs army %d (%d): S %d vs %d, ratio %.2f, raw troop ratio %.2f" % (
        a["id"], a["troops"], b["id"], b["troops"], pa, pb, r, raw)
