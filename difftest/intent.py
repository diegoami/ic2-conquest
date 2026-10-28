"""Did an order do what the case asked? (#230)

`check(action, before, after)` compares two parsed saves of the same game around one action and returns
(status, detail): "met", "not-met" (the state changed, but not as asked: on the original side this usually means
the adapter set a dialog wrongly, as recruit once did), "no-change" (nothing changed: the order was refused or
ignored) or "unchecked" (the op has no amount to check). Run on both sides; a case whose original side is
"not-met" is a harness problem, never a game difference.
"""
from difftest.compare import project


def _changed(before, after):
    pa, pb = project(before), project(after)
    return [k for k in set(pa) | set(pb) if pa.get(k) != pb.get(k)] or (before["map"] != after["map"] and ["map"]) or []


def check(a, before, after):
    if not _changed(before, after):
        return "no-change", "the state did not change"
    op, me = a["op"], before["current_nation"]
    nb, na = before["nations"][me], after["nations"][me]
    if op == "set_tax":
        return ("met" if na["tax"] == a["percent"] else "not-met"), f"tax {nb['tax']} -> {na['tax']}"
    if op == "recruit":
        new = [x for x in na["recruit_slots"] if x not in nb["recruit_slots"]]
        ok = len(new) == 1 and new[0]["type"] == a["type"] and new[0]["troops"] == a["troops"] and new[0]["city"] == a["city"]
        return ("met" if ok else "not-met"), f"new slots {new}"
    if op == "fortify":
        cb, ca = before["cities"][a["city"]], after["cities"][a["city"]]
        got = ca["fort_pending"] - cb["fort_pending"]
        return ("met" if got == a["points"] else "not-met"), f"pending points {cb['fort_pending']} -> {ca['fort_pending']}"
    if op == "buy_supply":
        # Capped by the army's need (troops / 100 + 1, driver.supply) and the city's stock: both games gave
        # 45 of 50 asked at Heraclea (#230 buy-heraclea-50).
        army = before["armies"][a["army"]]
        sb, sa = army["supplies"], after["armies"][a["army"]]["supplies"]
        want = max(0, min(a["tons"], army["troops"] // 100 + 1 - sb, before["cities"][a["city"]]["supplies"]))
        return ("met" if sa - sb == want else "not-met"), f"army supplies {sb} -> {sa} (expected +{want})"
    if op == "build_fleet":
        new = after["fleets"][len(before["fleets"]):]
        ok = len(new) == 1 and new[0]["building"] and new[0]["ships"] == a["ships"]
        return ("met" if ok else "not-met"), f"new fleets {[(f['ships'], f.get('build_city')) for f in new]}"
    if op == "split_army":
        moved = sorted((u["type"], u["troops"], u["quality"]) for k, u in enumerate(before["armies"][a["army"]]["units"]) if k in a["units"])
        new = after["armies"][-1]
        ok = len(after["armies"]) == len(before["armies"]) + 1 and sorted((u["type"], u["troops"], u["quality"]) for u in new["units"]) == moved
        return ("met" if ok else "not-met"), f"armies {len(before['armies'])} -> {len(after['armies'])}"
    if op == "disband_slot":
        return ("met" if len(na["recruit_slots"]) == len(nb["recruit_slots"]) - 1 else "not-met"), \
            f"slots {len(nb['recruit_slots'])} -> {len(na['recruit_slots'])}"
    if op == "relation":
        from state.sav import NATIONS
        want = {"war": 3, "trade": 1, "ally": 2}.get(a["kind"])
        got = na["relations"][NATIONS[a["nation"]]]
        if want is None:
            return ("met" if got <= 0 else "not-met"), f"relation {nb['relations'][NATIONS[a['nation']]]} -> {got}"
        return ("met" if got == want else "not-met"), f"relation {nb['relations'][NATIONS[a['nation']]]} -> {got}"
    return "unchecked", ""
