"""#230 batch 1: single strategic orders from the Rome 270 BC start (BASE.SAV), each followed by one End turn.

Rome at the start: armies 0 (100,37; next to Arretium 81) and 1 (120,53; next to Heraclea 120 and mercenary
offer 25); treasury 2,200; tax 10; at war with Gaul, trade with Illyria, peace cooldown with Macedonia; four
queued recruits at Rome (85); recruit list Luceria (110), Rome. Recruit amounts follow the dialogs' clamp
(battalion/5 .. battalion): li 3,000-15,000, hi 1,200-6,000, ar 700-3,500, lc 1,400-7,000, hc 500-2,500.
"""
from pathlib import Path

BASE = str(Path.home() / "ic2-work/fixtures/BASE.SAV")


def case(id, note, *actions, start=BASE):
    return {"id": id, "note": note, "start": start, "actions": list(actions)}


MIN = {"li": 3000, "hi": 1200, "ar": 700, "lc": 1400, "hc": 500}
MAX = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}

CASES = [
    case("tax-0", "tax 0", {"op": "set_tax", "percent": 0}),
    case("tax-25", "tax 25", {"op": "set_tax", "percent": 25}),
    case("tax-40", "tax 40 (maximum)", {"op": "set_tax", "percent": 40}),
    case("move-plain-1", "army 0 one plain tile west", {"op": "move", "army": 0, "x": 99, "y": 37}),
    case("move-forest", "army 0 into forest (101,38)", {"op": "move", "army": 0, "x": 101, "y": 38}),
    case("move-mountain", "army 0 into mountains (101,37)", {"op": "move", "army": 0, "x": 101, "y": 37}),
    case("move-river", "army 0 onto a river (101,36)", {"op": "move", "army": 0, "x": 101, "y": 36}),
    case("move-far", "army 0 toward (90,50), beyond its moves", {"op": "move", "army": 0, "x": 90, "y": 50}),
    case("move-sea", "army 1 onto sea (122,54)", {"op": "move", "army": 1, "x": 122, "y": 54}),
    case("move-own-city", "army 0 onto Arretium (99,36)", {"op": "move", "army": 0, "x": 99, "y": 36}),
    case("move-twice", "army 1 two moves in a row", {"op": "move", "army": 1, "x": 118, "y": 52},
         {"op": "move", "army": 1, "x": 116, "y": 50}),
] + [
    case(f"recruit-{t}-min", f"recruit {MIN[t]} {t} at Rome", {"op": "recruit", "city": 85, "type": t, "troops": MIN[t]}) for t in MIN
] + [
    case(f"recruit-{t}-max", f"recruit {MAX[t]} {t} at Rome", {"op": "recruit", "city": 85, "type": t, "troops": MAX[t]}) for t in MAX
] + [
    case("recruit-luceria", "recruit 2,000 hi at Luceria", {"op": "recruit", "city": 110, "type": "hi", "troops": 2000}),
    case("recruit-two", "two recruits at Rome", {"op": "recruit", "city": 85, "type": "li", "troops": 4000},
         {"op": "recruit", "city": 85, "type": "lc", "troops": 2000}),
    case("rel-war-carthage", "declare war on Carthage", {"op": "relation", "nation": 1, "kind": "war"}),
    case("rel-war-illyria", "declare war on Illyria (trade partner)", {"op": "relation", "nation": 9, "kind": "war"}),
    case("rel-peace-gaul", "propose peace to Gaul (at war)", {"op": "relation", "nation": 6, "kind": "peace"}),
    case("rel-trade-carthage", "propose trade to Carthage", {"op": "relation", "nation": 1, "kind": "trade"}),
    case("rel-trade-bithynia", "propose trade to Bithynia", {"op": "relation", "nation": 11, "kind": "trade"}),
    case("rel-ally-carthage", "propose alliance to Carthage", {"op": "relation", "nation": 1, "kind": "ally"}),
    case("rel-ally-illyria", "propose alliance to Illyria (trade partner)", {"op": "relation", "nation": 9, "kind": "ally"}),
    case("rel-war-macedonia", "declare war on Macedonia (peace cooldown -8)", {"op": "relation", "nation": 4, "kind": "war"}),
    case("fortify-pisae-10", "fortify Pisae 10 points", {"op": "fortify", "city": 71, "points": 10}),
    case("fortify-rome-5", "fortify Rome 5 points", {"op": "fortify", "city": 85, "points": 5}),
    case("fortify-arretium-25", "fortify Arretium 25 points", {"op": "fortify", "city": 81, "points": 25}),
    case("fortify-caere-50", "fortify Caere 50 points (to 100)", {"op": "fortify", "city": 82, "points": 50}),
    case("buy-arretium-20", "army 0 buys 20 tons at Arretium", {"op": "buy_supply", "army": 0, "city": 81, "tons": 20}),
    case("buy-heraclea-50", "army 1 buys 50 tons at Heraclea", {"op": "buy_supply", "army": 1, "city": 120, "tons": 50}),
    case("disband-army-0", "disband army 0 (next to Arretium)", {"op": "disband_army", "army": 0}),
    case("split-army-1unit", "split unit row 0 off army 0", {"op": "split_army", "army": 0, "units": [0]}),
    case("split-army-2units", "split unit rows 0 and 1 off army 0", {"op": "split_army", "army": 0, "units": [0, 1]}),
    case("split-then-join", "split row 0 off army 0, then Join army 0 with it",
         {"op": "split_army", "army": 0, "units": [0]}, {"op": "join_armies", "army": 0, "partner": 14}),
    case("fleet-10", "build a fleet of 10 ships", {"op": "build_fleet", "ships": 10}),
    case("fleet-25", "build a fleet of 25 ships", {"op": "build_fleet", "ships": 25}),
    case("fleet-two", "two Build fleet orders of 10", {"op": "build_fleet", "ships": 10}, {"op": "build_fleet", "ships": 10}),
    case("disband-slot-0", "disband queued recruit slot 0 (li 5,500)", {"op": "disband_slot", "slot": 0}),
    case("disband-slot-3", "disband queued recruit slot 3 (hc 1,000)", {"op": "disband_slot", "slot": 3}),
    case("recruit-then-disband", "recruit 1,200 hi at Rome, then disband it (slot 4)",
         {"op": "recruit", "city": 85, "type": "hi", "troops": 1200}, {"op": "disband_slot", "slot": 4}),
    case("hire-merc-25", "army 1 hires mercenary offer 25 (li 3,868)", {"op": "hire_mercenary", "army": 1, "pool": 25}),
    case("tax-then-recruit", "tax 30, then recruit 3,000 li at Luceria", {"op": "set_tax", "percent": 30},
         {"op": "recruit", "city": 110, "type": "li", "troops": 3000}),
]
