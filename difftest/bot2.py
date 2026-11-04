"""rulebot-2 (owner 2026-11-04): a defensive rule bot. "Its purpose is to defend, not to attack", and it should also
"attack invading armies, if odds in favour, and reconquer core towns, whose allegiance is to them".

`decide(state)` returns the orders for the current nation (state["current_nation"]), without End turn; `end_turn(state)`
returns the End turn action, with "peace": true (a human-AI war ends only when the human accepts the AI's post-battle
peace offer, docs/rules-digest.md §7, so accepting it is the defensive bot's way to make peace). Like rulebot-1 it reads only
what a player sees and is deterministic: the same state gives the same orders, in both games.

The rules, from docs/rules-digest.md:
1. **Tax** 15 % (unity loses tax/2 a quarter; below 400 the leader is overthrown, as Seleucid's was at turn 26).
2. **Recruit** heavy infantry (field weight 100) at the capital, with treasury >= 1,000 and fewer than 40 queued units.
3. **Mobilize** every ready slot (readiness 24, the cap) into the field.
4. **Each own army** with moves, in record order, does the first that applies:
   a. **supply**, as rulebot-1 (below 40 % supply, next to an own city);
   b. **counter-attack**: an army of a nation at war, adjacent to this army, whose field strength ours exceeds by ODDS
      (field strength = sum(weight x troops/100) / 80 x morale; weights LI 20, HI 100, Ar 40, LC 60, HC 120);
   c. **reconquer**: an adjacent core city (allegiance = us, owner at war with us) whose estimated siege defence is
      below our siege strength (sum(troops, archers x3) div 80 x morale);
   d. **intercept**: the nearest invading army (at war, within THREAT tiles of an own city) we beat by ODDS: march to it;
   e. **retake**: the nearest core city held by an enemy that we would take: march to it;
   f. **garrison**: march back to the capital when farther than HOME tiles.
   It never declares war and never targets a nation it is not at war with.
"""
from state.sav import cell

NAME = "rulebot-2"
LAND = set(range(2, 12))
WEIGHT = {"li": 20, "hi": 100, "ar": 40, "lc": 60, "hc": 120}
ODDS = 1.3          # counter-attack only with at least 30 % more field strength
THREAT = 6          # an enemy army within this many tiles of an own city is an invader
HOME = 3            # garrison armies stay within this many tiles of the capital
RETAKE_RANGE = 15   # core cities farther than this are left alone


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def field_strength(army):
    return sum(WEIGHT[u["type"]] * u["troops"] // 100 for u in army["units"]) / 80 * army["morale"]


def siege_strength(army):
    return sum(u["troops"] * (3 if u["type"] == "ar" else 1) for u in army["units"]) // 80 * army["morale"]


def city_defence(s, c, attacker):
    """Siege defence of city c against `attacker` (docs/rules-digest.md, Siege): loyalty x150 + fort x250 + pop x200,
    x5/3 for a capital with loyalty > 59, x4/5 if owner != allegiance, + the owner's queued troops at the city / 2,
    x9/10 if the attacker is the city's allegiance nation."""
    d = c["loyalty"] * 150 + c["fort"] * 250 + c["pop"] * 200
    if any(n["capital"] == c["id"] for n in s["nations"]) and c["loyalty"] > 59:
        d = d * 5 // 3
    if c["owner"] != c["allegiance"]:
        d = d * 4 // 5
    if 0 <= c["owner"] < 16:
        d += sum(r["troops"] for r in s["nations"][c["owner"]]["recruit_slots"] if r["city"] == c["id"]) // 2
    if c["allegiance"] == attacker:
        d = d * 9 // 10
    return d


def approach(s, pos, target):
    """The land tile next to `target` nearest `pos` (rulebot-1's choice), or None."""
    tiles = [(target[0] + dx, target[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    tiles = [t for t in tiles if 0 <= t[0] < 320 and 0 <= t[1] < 140 and cell(s, *t) in LAND]
    return min(tiles, key=lambda t: (cheb(pos, t), t)) if tiles else None


def decide(s):
    me = s["current_nation"]
    n = s["nations"][me]
    out = []
    if n["tax"] != 15:
        out.append({"op": "set_tax", "percent": 15})
    if n["treasury"] >= 1000 and len(n["recruit_slots"]) < 40 and n["capital"] >= 0:
        out.append({"op": "recruit", "city": n["capital"], "type": "hi", "troops": 1200})
    for i, r in enumerate(n["recruit_slots"]):
        if r["state"] >= 24:
            out.append({"op": "mobilize", "slot": i})
            break                                   # one per turn: slot indices shift after a mobilization
    names = [x["name"] for x in s["nations"]]
    at_war = {j for j, x in enumerate(s["nations"]) if j != me and n["relations"].get(names[j]) == 3}
    own = [c for c in s["cities"] if c["owner"] == me]
    capital = next((c for c in s["cities"] if c["id"] == n["capital"]), None)
    enemies = [a for a in s["armies"] if a["owner"] in at_war and a["troops"] > 0 and not a["embarked"]]
    invaders = [a for a in enemies if any(cheb((a["x"], a["y"]), (c["x"], c["y"])) <= THREAT for c in own)]
    lost_core = [c for c in s["cities"] if c["allegiance"] == me and c["owner"] in at_war]
    for a in s["armies"]:
        if a["owner"] != me or a["troops"] <= 0 or a["moves"] <= 0 or a["embarked"]:
            continue
        pos = (a["x"], a["y"])
        if a["supply_pct"] < 40:                                                    # a. supply
            near = [c for c in own if cheb(pos, (c["x"], c["y"])) == 1]
            need = a["troops"] // 100 + 1 - a["supplies"]
            if near and need >= 10:
                c = min(near, key=lambda c: c["id"])
                tons = min(need, c["supplies"]) // 10 * 10
                if tons >= 10:
                    out.append({"op": "buy_supply", "army": a["id"], "city": c["id"], "tons": tons})
                    continue
        mine = field_strength(a)
        adj = [e for e in enemies if cheb(pos, (e["x"], e["y"])) == 1 and mine >= ODDS * field_strength(e)]
        if adj:                                                                     # b. counter-attack
            out.append({"op": "attack_army", "army": a["id"], "target": min(adj, key=lambda e: e["id"])["id"]})
            continue
        siege = siege_strength(a)
        take = [c for c in lost_core if cheb(pos, (c["x"], c["y"])) == 1 and siege > city_defence(s, c, me)]
        if take:                                                                    # c. reconquer
            out.append({"op": "besiege", "army": a["id"], "city": min(take, key=lambda c: c["id"])["id"]})
            continue
        beatable = [e for e in invaders if mine >= ODDS * field_strength(e)]
        if beatable:                                                                # d. intercept
            e = min(beatable, key=lambda e: (cheb(pos, (e["x"], e["y"])), e["id"]))
            t = approach(s, pos, (e["x"], e["y"]))
            if t and t != pos:
                out.append({"op": "move", "army": a["id"], "x": t[0], "y": t[1]})
                continue
        targets = [c for c in lost_core if cheb(pos, (c["x"], c["y"])) <= RETAKE_RANGE and siege > city_defence(s, c, me)]
        if targets:                                                                 # e. retake
            c = min(targets, key=lambda c: (cheb(pos, (c["x"], c["y"])), c["id"]))
            t = approach(s, pos, (c["x"], c["y"]))
            if t and t != pos:
                out.append({"op": "move", "army": a["id"], "x": t[0], "y": t[1]})
                continue
        if capital and cheb(pos, (capital["x"], capital["y"])) > HOME:              # f. garrison
            t = approach(s, pos, (capital["x"], capital["y"]))
            if t and t != pos:
                out.append({"op": "move", "army": a["id"], "x": t[0], "y": t[1]})
    return out


def end_turn(s):
    return {"op": "end_turn", "peace": True}
