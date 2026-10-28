"""Rule bots for #232: deterministic, readable rules over the player-visible state of one game.

`decide(state)` returns the actions for the nation whose turn it is (state["current_nation"]), without End turn.
The rules only read the map, cities, armies and the nation's own records, as a player sees them. They are meant
to be simple and repeatable, not strong: the same state gives the same orders, so the two games receive the same
orders for as long as their states agree.

rulebot-1:
1. Tax: set it to 20 when it is not 20.
2. Recruit: with treasury >= 1,000 and fewer than 40 queued units, recruit 1,200 heavy infantry at the capital.
3. Each own army with moves left, in record order, does one thing:
   a. supply: below 40 % supply with an own city adjacent, buy up to its need (troops / 100 + 1), in whole tens,
      from that city's stock;
   b. siege: next to a city of a nation it is at war with, besiege it (the lowest city index);
   c. march: otherwise walk toward the nearest city of a nation at war (Chebyshev distance, then city index), to the
      land tile next to it that is nearest the army.
"""
from state.sav import cell

NAME = "rulebot-1"
LAND = set(range(2, 12))            # plain, desert, forest, mountains, rivers (state/sav.py TERRAIN); markers and sea excluded


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def decide(s):
    me = s["current_nation"]
    n = s["nations"][me]
    out = []
    if n["tax"] != 20:
        out.append({"op": "set_tax", "percent": 20})
    if n["treasury"] >= 1000 and len(n["recruit_slots"]) < 40 and n["capital"] >= 0:
        out.append({"op": "recruit", "city": n["capital"], "type": "hi", "troops": 1200})
    names = [x["name"] for x in s["nations"]]
    at_war = {j for j, x in enumerate(s["nations"]) if j != me and n["relations"].get(names[j]) == 3}
    enemy_cities = [c for c in s["cities"] if c["owner"] in at_war]
    own_cities = [c for c in s["cities"] if c["owner"] == me]
    for a in s["armies"]:
        if a["owner"] != me or a["troops"] <= 0 or a["moves"] <= 0 or a["embarked"]:
            continue
        pos = (a["x"], a["y"])
        if a["supply_pct"] < 40:
            near = [c for c in own_cities if cheb(pos, (c["x"], c["y"])) == 1]
            need = a["troops"] // 100 + 1 - a["supplies"]
            if near and need >= 10:
                c = min(near, key=lambda c: c["id"])
                tons = min(need, c["supplies"]) // 10 * 10
                if tons >= 10:
                    out.append({"op": "buy_supply", "army": a["id"], "city": c["id"], "tons": tons})
                    continue
        adj = [c for c in enemy_cities if cheb(pos, (c["x"], c["y"])) == 1]
        if adj:
            out.append({"op": "besiege", "army": a["id"], "city": min(adj, key=lambda c: c["id"])["id"]})
            continue
        if not enemy_cities:
            continue
        target = min(enemy_cities, key=lambda c: (cheb(pos, (c["x"], c["y"])), c["id"]))
        tiles = [(target["x"] + dx, target["y"] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
        tiles = [t for t in tiles if 0 <= t[0] < 320 and 0 <= t[1] < 140 and cell(s, *t) in LAND]
        if tiles:
            t = min(tiles, key=lambda t: (cheb(pos, t), t))
            if t != pos:
                out.append({"op": "move", "army": a["id"], "x": t[0], "y": t[1]})
    return out
