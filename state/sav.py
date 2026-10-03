"""Parse an Imperial Conquest 2 save (.SAV) into plain Python / JSON.

    python3 -m state.sav AUTO0720.SAV            # JSON on stdout
    python3 -m state.sav AUTO0720.SAV --summary  # one line per nation

Layout: docs/sav-layout-notes.md (from the research repo's
decompiled-sav-file-layout.md and the field reports it cites). Offsets here
are the save's; the running game holds the same records in memory.
"""
import json
import struct
import sys

NATIONS = ["Rome", "Carthage", "Seleucid", "Ptolemaic", "Macedonia", "Numidia", "Gaul", "Greece",
           "Celtiberia", "Illyria", "Dacia", "Bithynia", "Galatia", "Armenia", "Media", "Thracia"]
UNIT_TYPES = ["li", "hi", "ar", "lc", "hc"]            # light/heavy infantry, archers, light/heavy cavalry
UNIT_NAMES = ["Lit inf", "Hvy inf", "Archers", "Lit cav", "Hvy cav"]
QUALITY = {4: "very poor", 5: "poor", 6: "average", 7: "good", 8: "very good", 9: "elite"}
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
RELATION = {0: "peace", 1: "trade", 2: "alliance", 3: "war"}
TERRAIN = {0: "sea", 1: "rough sea", 2: "plain", 3: "desert", 4: "forest", 5: "mountains"}
MOVE_COST = {0: 1, 1: 3, 2: 1, 3: 1, 4: 2, 5: 4}        # 6-11 river: 4; markers block
SEASON_V = [50, 80, 80, 20]                            # DAT 0x1F7D8

MAP_W, MAP_H = 320, 140
CITY_OFF, CITY_N, CITY_LEN = 89600, 334, 34
ARMY_OFF, ARMY_LEN, FLEET_LEN, NATION_LEN = 100956, 656, 26, 1172


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def cstr(b):
    return b.split(b"\0")[0].decode("latin1")


def terrain_name(code):
    return TERRAIN.get(code, "river" if 6 <= code <= 11 else str(code))


def move_cost(code):
    return MOVE_COST.get(code, 4 if 6 <= code <= 11 else None)


def parse(b):
    s = {"size": len(b)}
    s["map"] = struct.unpack_from("<%dh" % (MAP_W * MAP_H), b, 0)     # (x, y) -> [x*140 + y]

    cities = []
    for i in range(CITY_N):
        o = CITY_OFF + i * CITY_LEN
        f = struct.unpack_from("<10h", b, o + 14)
        cities.append({"id": i, "name": cstr(b[o:o + 14]), "x": f[0], "y": f[1], "owner": f[2],
                       "allegiance": f[3], "loyalty": f[4], "supplies": f[5],
                       "fort": f[6] if f[6] <= 100 else f[6] % 100,
                       "fort_pending": f[6] // 100 if f[6] > 100 else 0,
                       "pop": f[7], "max_pop": f[8], "tribute": f[9]})
    s["cities"] = cities

    na = i16(b, ARMY_OFF)
    armies, o = [], ARMY_OFF + 2
    for i in range(na):
        r = b[o + i * ARMY_LEN:o + (i + 1) * ARMY_LEN]
        x, y, owner, moves, cell, sup, money, morale = struct.unpack_from("<8h", r, 0)
        units = []
        for k in range(20):
            label, typ, troops, q = struct.unpack_from("<4h", r, 16 + 32 * k)
            if troops > 0:
                units.append({"slot": k, "type": UNIT_TYPES[typ], "troops": troops, "quality": q,
                              "merc": label, "name": cstr(r[16 + 32 * k + 8:16 + 32 * k + 32])})
        troops = sum(u["troops"] for u in units)
        armies.append({"id": i, "x": x, "y": y, "owner": owner, "moves": moves, "cell": cell,
                       "embarked": cell == -1, "supplies": sup, "money": money, "morale": morale,
                       "troops": troops, "units": units,
                       "supply_pct": sup * 10000 // max(troops, 1) if troops else 0})
    s["armies"] = armies
    o += na * ARMY_LEN

    nf = i16(b, o)
    fleets, o = [], o + 2
    for i in range(nf):
        f = struct.unpack_from("<13h", b, o + i * FLEET_LEN)
        building = f[5] >= 0
        fleets.append({"id": i, "x": f[0], "y": f[1], "owner": f[4], "countdown": f[5], "building": building,
                       "moves": f[6], "supplies": f[7], "money": f[8], "ships": f[9],
                       "build_city" if building else "condition": f[10], "army": f[11], "cell": f[12]})
    s["fleets"] = fleets
    o += nf * FLEET_LEN

    nations = []
    for n in range(16):
        r = b[o + n * NATION_LEN:o + (n + 1) * NATION_LEN]
        rel = struct.unpack_from("<16h", r, 0x26)
        clist = []
        for k in range(334):
            c = i16(r, 0x48 + 2 * k)
            if c < 0:
                break
            clist.append(c)
        slots = []
        for k in range(40):
            st, typ, troops, city = struct.unpack_from("<4h", r, 0x2E4 + 8 * k)
            if troops > 0:
                slots.append({"slot": k, "state": st, "type": UNIT_TYPES[typ], "troops": troops, "city": city})
        wealth, wealth0, treasury, treasury0 = struct.unpack_from("<4i", r, 0x430)
        unity, mob, capital, ncities, ncities0, tax, taxbase, conq = struct.unpack_from("<8h", r, 0x440)
        nations.append({"id": n, "name": cstr(r[:11]), "leader": cstr(r[0xB:0x26]),
                        "relations": {NATIONS[j]: rel[j] for j in range(16) if j != n},
                        "neighbours": [NATIONS[j] for j in range(16) if (struct.unpack_from("<H", r, 0x46)[0] >> j) & 1],
                        "city_list": clist, "recruit_slots": slots,
                        "wealth": wealth, "treasury": treasury, "unity": unity, "mobilization": mob,
                        "capital": capital, "cities_count": ncities, "tax": tax, "tax_base": taxbase,
                        "conquered_by": conq, "view": [i16(r, 0x488), i16(r, 0x486)], "human": r[0x490] == 1,
                        "alive": unity > 0 and capital != -1})
    s["nations"] = nations
    o += 16 * NATION_LEN

    mercs = []
    for k in range(50):
        x, y, label, typ, troops, q = struct.unpack_from("<6h", b, o + 12 * k)
        if troops >= 0 and typ >= 0:
            mercs.append({"slot": k, "x": x, "y": y, "label": label, "type": UNIT_TYPES[typ],
                          "troops": troops, "quality": q})
    s["mercenaries"] = mercs
    o += 600

    ni = i16(b, o)
    s["news"] = [cstr(b[o + 2 + 61 * k:o + 2 + 61 * (k + 1)]) for k in range(ni + 1)]
    o += 2 + (ni + 1) * 61

    s["tail_off"] = o                # offset of the 23-short tail (turn order, current nation, week, year, season)
    t = struct.unpack_from("<23h", b, o)
    s["turn_order"] = list(t[:16])
    s["pending_offer"] = {"from": t[16], "type": t[17]}
    s["current_nation"], s["seat_index"] = t[18], t[19]
    s["week"], s["year_bc"], s["season"] = t[20], t[21], t[22]
    s["battle_flag"] = b[o + 54]
    s["turn"] = turn_number(s["year_bc"], s["season"], s["week"])
    s["date"] = f"{SEASONS[s['season']]} week {s['week']}, {s['year_bc']} BC"
    return s


def turn_number(year_bc, season, week):
    """The autosave's nnnn: 0720 is 270 BC Spring week 1."""
    return (300 - year_bc) * 24 + season * 6 + (week - 1) // 2


def load(path):
    with open(path, "rb") as f:
        return parse(f.read())


def cell(s, x, y):
    return s["map"][x * MAP_H + y]


def owned_cities(s, n):
    return [c for c in s["cities"] if c["owner"] == n]


def live_armies(s, n=None):
    return [a for a in s["armies"] if a["owner"] >= 0 and a["troops"] > 0 and (n is None or a["owner"] == n)]


def city_at(s, x, y):
    for c in s["cities"]:
        if c["x"] == x and c["y"] == y:
            return c
    return None


def can_recruit_at(s, n, city):
    """The Recruit dialog's city list (code at 0x454582, see
    findings/2026-09-29-recruiting-cities-need-fortification-75.md): own city
    with fortification >= 75 (a pending order counts its built part), or the
    capital, or a city already holding one of the nation's queued units."""
    if city["owner"] != n:
        return False
    if city["fort"] >= 75 or s["nations"][n]["capital"] == city["id"]:
        return True
    return any(sl["city"] == city["id"] for sl in s["nations"][n]["recruit_slots"])


def consumption(troops, season, embarked=False):
    """Tons per turn (supply-driven-morale-and-fleet-attrition.md)."""
    return troops // 200 if embarked else (90 - SEASON_V[season]) * troops // 20000


def siege_strength(army):
    t = sum(u["troops"] * (3 if u["type"] == "ar" else 1) for u in army["units"])
    return t // 80 * army["morale"]


def field_strength(army):
    w = {"li": 20, "hi": 100, "ar": 40, "lc": 60, "hc": 120}
    return sum(w[u["type"]] * u["troops"] // 100 for u in army["units"]) // 80 * army["morale"]


def siege_defence(s, city):
    """decompiled-city-capture-resolution.md (before the attacker-allegiance x9/10)."""
    d = city["loyalty"] * 150 + city["fort"] * 250 + city["pop"] * 200
    capital = any(n["capital"] == city["id"] for n in s["nations"] if n["alive"])
    if capital and city["loyalty"] > 59:
        d = d * 5 // 3
    if city["owner"] != city["allegiance"]:
        d = d * 4 // 5
    owner = s["nations"][city["owner"]] if city["owner"] >= 0 else None
    if owner:
        d += sum(sl["troops"] for sl in owner["recruit_slots"] if sl["city"] == city["id"]) // 2
    return d


def summary(s):
    out = [f"{s['date']} (turn {s['turn']:04d}), current {NATIONS[s['current_nation']]}"]
    for n in s["nations"]:
        if not n["alive"]:
            continue
        arm = live_armies(s, n["id"])
        out.append(f"{n['name']:11} cities {len(owned_cities(s, n['id'])):3}  armies {len(arm):2} "
                   f"troops {sum(a['troops'] for a in arm):7}  treasury {n['treasury']:6}  unity {n['unity']:4}")
    return "\n".join(out)


if __name__ == "__main__":
    st = load(sys.argv[1])
    if "--summary" in sys.argv:
        print(summary(st))
    else:
        st = dict(st)
        st.pop("map")
        json.dump(st, sys.stdout, indent=1)
