"""rulebot-2 (owner 2026-11-04): a defensive rule bot. "Its purpose is to defend, not to attack", and it should also
"attack invading armies, if odds in favour, and reconquer core towns, whose allegiance is to them".

`decide(state)` returns the orders for the current nation (state["current_nation"]), without End turn; `end_turn(state)`
returns the End turn action, with "peace": true (a human-AI war ends only when the human accepts the AI's post-battle
peace offer, docs/rules-digest.md §7, so accepting it is the defensive bot's way to make peace). Like rulebot-1 it reads only
what a player sees and is deterministic: the same state gives the same orders, in both games.

The rules, from docs/rules-digest.md:
1. **Tax** 15 % (unity loses tax/2 a quarter; below 400 the leader is overthrown, as Seleucid's was at turn 26).
2. **Recruit** heavy infantry (field weight 100) at the capital, with treasury >= 1,000 and fewer than 40 queued units.
3. **Mobilize** a slot once its readiness reaches 24, the cap (quality 6, "average"), one per turn. **Desperate**
   (the enemy armies within THREAT tiles of the capital outweigh our own armies there, owner 2026-11-05: "mobilize when
   they are average, not when available, unless you are desperate"): every slot from readiness 16 (quality 4, the
   player's earliest), highest slot index first so the earlier indices do not shift.
4. **Each own army** with moves, in record order, does the first that applies:
   a. **supply** below 40 % supply (owner 2026-11-05: "do the supply fix, otherwise they will get creamed"): buy from
      the adjacent own city with the most stock; with no stocked city adjacent, march to the nearest own city holding
      at least SUPPLY_MIN tons (or the army's whole need), as the original's AI walks to its resupply city;
   b. **counter-attack**: an army of a nation at war, adjacent to this army, whose field strength ours exceeds by ODDS
      (field strength = sum(weight x troops/100) / 80 x morale; weights LI 20, HI 100, Ar 40, LC 60, HC 120);
   c. **reconquer**: an adjacent core city (allegiance = us, owner at war with us) whose estimated siege defence is
      below our siege strength (sum(troops, archers x3) div 80 x morale);
   d. **intercept**: the nearest invading army (at war, within THREAT tiles of an own city) we beat by ODDS: march to it;
   e. **retake**: the nearest core city held by an enemy that we would take: march to it;
   f. **garrison**: march back next to the capital (HOME = 1, so a garrison can buy supply there; it was 3 until
      2026-11-05, which left the Seleucid game's 80,016-man army 2 tiles from any city at 0 % supply for 100 turns).
   It never declares war and never targets a nation it is not at war with.
5. **Each own launched fleet** next to an own city, carrying no army (owner 2026-11-05: "same as fleet, make them supplied
   and repaired"): below half its capacity (8 x ships) it takes tons from the adjacent own city with the most stock; below
   condition FLEET_REPAIR_BELOW it is repaired to 100 when the treasury keeps TREASURY_RESERVE after the cost
   (ships x points / 5). rulebot-2 does not sail its fleets, so they are served where they lie.
6. **Mercenary pay** (owner 2026-11-05: "just pay mercenaries"): regulars are paid from the treasury with no balance check
   and never desert; a mercenary unit (unit marker != 0) is paid `(troops div 200) x price x quality div 5` a quarter
   from its army's purse and deserts when the purse is at 0 (research upkeep-payment-and-desertion.md). An own army with
   mercenaries, next to an own city, whose purse holds less than two quarters' pay gets talents from the treasury, in
   hundreds, up to four quarters' pay (purse cap 1,000), when the treasury keeps TREASURY_RESERVE. rulebot-2 hires none,
   but a handed-over nation inherits its AI's (the Seleucid game's army 10: 11,216 Kardackians, purse 598 -> 263).
"""
from planner import path as P
from state.sav import cell

NAME = "rulebot-2"
LAND = set(range(2, 12))
WEIGHT = {"li": 20, "hi": 100, "ar": 40, "lc": 60, "hc": 120}
ODDS = 1.3          # counter-attack only with at least 30 % more field strength
THREAT = 6          # an enemy army within this many tiles of an own city is an invader
HOME = 1            # garrison armies stand next to the capital (3 until 2026-11-05)
SUPPLY_MIN = 100    # a city worth marching to for supply holds at least this many tons (or the army's whole need)
DESPERATE_READY = 16  # readiness from which a desperate nation mobilizes (quality 4, the player's earliest)
FLEET_REPAIR_BELOW = 80   # repair a docked fleet below this condition (storms sink a fleet below 40)
TREASURY_RESERVE = 1000   # a repair or a mercenary payment must leave at least this much in the treasury
PRICE = {"li": 1, "hi": 2, "ar": 1, "lc": 3, "hc": 4}   # quarterly price per 200 troops (DAT unit table +0x24)
PURSE_CAP = 1000
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


def line(a, b):
    """The tiles of the straight walk from a to b, a excluded: the game walks a click's target along this line and stops at
    the first step it cannot afford (planner/path.py). Major-axis Bresenham, as FUN_0044d734 steps."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
    out, err = [], 2 * min(dx, dy) - max(dx, dy)
    x, y = x0, y0
    for _ in range(max(dx, dy)):
        if err >= 0:
            x, y = x + sx, y + sy
            err -= 2 * max(dx, dy)
        elif dx >= dy:
            x += sx
        else:
            y += sy
        err += 2 * min(dx, dy)
        out.append((x, y))
    return out


def legs(s, army, goal):
    """The clicks that walk the army toward `goal` this turn along the cheapest land path (2026-11-05: the old bot clicked
    the final goal, and a straight line across water left the Seleucid game's army 1 in place for 100 turns). Each click
    is the farthest tile of the turn's reach whose straight line from the previous click is land the army can still
    afford (an army keeps its remaining moves after a click). [] when there is no path or no step."""
    pos = (army["x"], army["y"])
    _, path = P.dijkstra(s, pos, lambda x, y: (x, y) == tuple(goal), max_cost=2000)
    if not path:
        return []
    reach, _ = P.turn_legs(s, path, army["moves"])
    clicks, at, left, i = [], pos, army["moves"], 0
    while i < len(reach) - 1:
        for j in range(len(reach) - 1, i, -1):
            costs = [P.passable_cost(cell(s, *u)) for u in line(at, reach[j])]
            if None not in costs and sum(costs) <= left:
                clicks.append(reach[j])
                at, left, i = reach[j], left - sum(costs), j
                break
        else:
            break
    return clicks


def march(out, s, army, goal):
    """Append this turn's clicks toward `goal` (see legs); True when there was at least one."""
    clicks = legs(s, army, goal) if goal and goal != (army["x"], army["y"]) else []
    out += [{"op": "move", "army": army["id"], "x": t[0], "y": t[1]} for t in clicks]
    return bool(clicks)


def approach(s, pos, target):
    """The land tile next to `target` nearest `pos` (rulebot-1's choice), or None."""
    tiles = [(target[0] + dx, target[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
    tiles = [t for t in tiles if 0 <= t[0] < 320 and 0 <= t[1] < 140 and cell(s, *t) in LAND]
    return min(tiles, key=lambda t: (cheb(pos, t), t)) if tiles else None


def mercenary_pay(army):
    """One quarter's pay of the army's mercenary units (unit marker != 0), as the quarterly tick bills it."""
    return sum((u["troops"] // 200) * PRICE[u["type"]] * u["quality"] // 5 for u in army["units"] if u.get("merc"))


def desperate(s, me, capital, enemies):
    """The enemy armies within THREAT tiles of the capital outweigh our own armies within THREAT tiles of it."""
    if capital is None:
        return False
    near = lambda a: cheb((a["x"], a["y"]), (capital["x"], capital["y"])) <= THREAT
    threat = sum(field_strength(e) for e in enemies if near(e))
    ours = sum(field_strength(a) for a in s["armies"] if a["owner"] == me and a["troops"] > 0 and not a["embarked"] and near(a))
    return threat > ours


def decide(s):
    me = s["current_nation"]
    n = s["nations"][me]
    out = []
    if n["tax"] != 15:
        out.append({"op": "set_tax", "percent": 15})
    if n["treasury"] >= 1000 and len(n["recruit_slots"]) < 40 and n["capital"] >= 0:
        out.append({"op": "recruit", "city": n["capital"], "type": "hi", "troops": 1200})
    names = [x["name"] for x in s["nations"]]
    at_war = {j for j, x in enumerate(s["nations"]) if j != me and n["relations"].get(names[j]) == 3}
    own = [c for c in s["cities"] if c["owner"] == me]
    capital = next((c for c in s["cities"] if c["id"] == n["capital"]), None)
    enemies = [a for a in s["armies"] if a["owner"] in at_war and a["troops"] > 0 and not a["embarked"]]
    if desperate(s, me, capital, enemies):
        ready = [i for i, r in enumerate(n["recruit_slots"]) if r["state"] >= DESPERATE_READY and r["troops"] > 0]
        out += [{"op": "mobilize", "slot": i} for i in sorted(ready, reverse=True)]
    else:
        for i, r in enumerate(n["recruit_slots"]):
            if r["state"] >= 24:
                out.append({"op": "mobilize", "slot": i})
                break                               # one per turn: slot indices shift after a mobilization
    invaders = [a for a in enemies if any(cheb((a["x"], a["y"]), (c["x"], c["y"])) <= THREAT for c in own)]
    lost_core = [c for c in s["cities"] if c["allegiance"] == me and c["owner"] in at_war]
    for a in s["armies"]:
        if a["owner"] != me or a["troops"] <= 0 or a["moves"] <= 0 or a["embarked"]:
            continue
        pos = (a["x"], a["y"])
        need = a["troops"] // 100 + 1 - a["supplies"]
        if a["supply_pct"] < 40 and need >= 10:                                     # a. supply
            near = [c for c in own if cheb(pos, (c["x"], c["y"])) == 1 and c["supplies"] >= 10]
            if near:
                c = max(near, key=lambda c: (c["supplies"], -c["id"]))
                tons = min(need, c["supplies"]) // 10 * 10
                out.append({"op": "buy_supply", "army": a["id"], "city": c["id"], "tons": tons})
                continue
            far = [c for c in own if cheb(pos, (c["x"], c["y"])) > 1 and c["supplies"] >= min(need, SUPPLY_MIN)]
            if far:
                c = min(far, key=lambda c: (cheb(pos, (c["x"], c["y"])), c["id"]))
                if march(out, s, a, approach(s, pos, (c["x"], c["y"]))):
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
            if march(out, s, a, approach(s, pos, (e["x"], e["y"]))):
                continue
        targets = [c for c in lost_core if cheb(pos, (c["x"], c["y"])) <= RETAKE_RANGE and siege > city_defence(s, c, me)]
        if targets:                                                                 # e. retake
            c = min(targets, key=lambda c: (cheb(pos, (c["x"], c["y"])), c["id"]))
            if march(out, s, a, approach(s, pos, (c["x"], c["y"]))):
                continue
        if capital and cheb(pos, (capital["x"], capital["y"])) > HOME:              # f. garrison
            march(out, s, a, approach(s, pos, (capital["x"], capital["y"])))
    treasury = n["treasury"]
    for a in s["armies"]:                                                           # 6. mercenary pay
        pay = mercenary_pay(a) if a["owner"] == me and a["troops"] > 0 and not a["embarked"] else 0
        if not pay or a["money"] >= 2 * pay or not any(cheb((a["x"], a["y"]), (c["x"], c["y"])) == 1 for c in own):
            continue
        amount = (min(PURSE_CAP, 4 * pay) - a["money"] + 99) // 100 * 100
        amount = min(amount, (PURSE_CAP - a["money"]) // 100 * 100)
        if amount >= 100 and treasury - amount >= TREASURY_RESERVE:
            out.append({"op": "fund_army", "army": a["id"], "money": amount})
            treasury -= amount
    for f in s.get("fleets", []):                                                   # 5. fleets
        if f["owner"] != me or f["ships"] <= 0 or f.get("building") or f.get("army", -1) >= 0:
            continue
        near = [c for c in own if cheb((f["x"], f["y"]), (c["x"], c["y"])) == 1]
        if not near:
            continue
        cap = 8 * f["ships"]
        stocked = [c for c in near if c["supplies"] >= 10]
        if f["supplies"] < cap // 2 and stocked:
            c = max(stocked, key=lambda c: (c["supplies"], -c["id"]))
            tons = min(cap - f["supplies"], c["supplies"]) // 10 * 10
            if tons >= 10:
                out.append({"op": "supply_fleet", "fleet": f["id"], "city": c["id"], "tons": tons})
        if f.get("condition", 100) < FLEET_REPAIR_BELOW:
            points = 100 - f["condition"]
            cost = f["ships"] * points // 5
            if treasury - cost >= TREASURY_RESERVE:
                out.append({"op": "repair_fleet", "fleet": f["id"], "points": points})
                treasury -= cost
    return out


def end_turn(s):
    return {"op": "end_turn", "peace": True}
