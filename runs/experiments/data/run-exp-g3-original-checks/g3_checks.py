"""Original-side checks 1 (a-f), 2, 3, 5, 6 of the v0.5.0 gap analysis (rows_g3.md "Original-side checks needed"; issue #80).
Usage: python3 g3_checks.py <case> [args]. One fresh Wine process per case (seed 12345, fast rollingsave seed exe). Cases:
  Q1ab    rebellion: control, own-allegiance city at loyalty 2 (Capua, Venusia, Pisae), Rome-held Greek-allegiance city (Heraclea), week 11
  Q1c     rebirth: Greece unity 0, 9 Greek-allegiance cities at loyalty 5 (and the 7-city control)
  Q1d     mercenary desertion: purse 100 control and purse 0, one and two mercenary units
  Q1e     winter famine: 15 cities at stock 0, 10 at full stock, four winter rounds
  Q1f     AI deposition: all AI nations at treasury -50,000, repeated quarter rounds in one process
  Q2      natural quarter: six rounds from the start save, Balance sheet before the quarter round
  Q3      news line order (destroys vs treaty block) from memory and the News window
  Q5      rough sea
  Q6      offers from a peace-only start
Staging is L1 and labelled in each log's `staged` line: only named save fields are patched (stage.py ops and g3_lib helpers); positions never."""
import sys
from g3_lib import *
import g3_lib

hook_environment()
g = Game()
W11 = set_calendar(week=11)
FIRST = [True]


def go(tag, src, turns=1):
    r = round_(g, tag, src, FIRST[0], turns); FIRST[0] = False; return r


def predict_rebel(b, c):
    """The remake's/decompile's rule for an own-allegiance non-capital city: (c) the last army within 9 tiles (Chebyshev) of a nation at war with the owner;
    else (d) the neighbour (mask) with unity > 0 and best cities - 2 x distance(capital), ties to the lowest index. For owner != allegiance: (a)/(b)."""
    ct = b["cities"][c]; owner, alleg = ct[3], ct[4]; N = b["nations"]
    if owner != alleg:
        return {"rule": "b" if N[alleg]["unity"] > 0 else "a", "to": alleg if N[alleg]["unity"] > 0 else None}
    pick = -1
    for a in b["armies"]:
        if a["owner"] >= 0 and max(abs(a["x"] - ct[1]), abs(a["y"] - ct[2])) < 10 and N[owner]["relations"].get(sav.NATIONS[a["owner"]]) == 3: pick = a["owner"]
    if pick >= 0: return {"rule": "c", "to": pick}
    best, pick = -1000, -1
    for n in range(16):
        if sav.NATIONS[n] in N[owner]["neighbours"] and N[n]["unity"] > 0:
            cap = b["cities"][N[n]["capital"]]; s = N[n]["cities_count"] - 2 * max(abs(ct[1] - cap[1]), abs(ct[2] - cap[2]))
            if s > best: best, pick = s, n
    return {"rule": "d", "to": pick, "score": best}


def rome_cities(b): return sorted(b["nations"][0]["city_list"])


try:
    if CASE == "Q1ab":
        variants = sys.argv[2:] or ["ctl", "capua", "venusia", "pisae", "heraclea"]
        LOY = {"capua": 100, "venusia": 115, "pisae": 71, "heraclea": 120, "ariminum": 87, "arretium": 81, "pisae_gaul_dead": 71}
        for v in variants:
            ops = [("city", LOY[v], {"loyalty": 2})] if v in LOY else []
            if v == "pisae_gaul_dead": ops.append(("unity", 6, 0))      # L1: Gaul unity 0 (its armies stay): (c) ignores the war nation's unity, (d) skips it
            src = staged(START, ops, f"q1ab_{v}", W11)
            before, afters, diffs = go(f"q1ab_{v}", src)
            if v in LOY: log("prediction", tag=v, city=LOY[v], name=before["cities"][LOY[v]][0], predicted=predict_rebel(before, LOY[v]), observed_owner=afters[0]["cities"][LOY[v]][3], observed_loyalty=afters[0]["cities"][LOY[v]][5])
    elif CASE == "Q1c":
        NINE = [111, 116, 119, 122, 120, 123, 97, 100, 101]
        for v, ids in (("nine", NINE), ("seven_control", NINE[:7])):
            ops = [("unity", 7, 0)]
            for c in ids: ops += [("city", c, {"allegiance": 7, "loyalty": 5})]
            src = staged(START, ops, f"q1c_{v}", W11)
            go(f"q1c_{v}", src)
    elif CASE == "Q1d":
        a = lambda t: add_unit(0, 11, "li", 3000, 6, "Gallic Foot  Battalion")
        two = chain(add_unit(0, 11, "li", 3000, 6, "Gallic Foot  Battalion"), add_unit(0, 14, "ar", 2000, 7, "Cretan Bowmen Battalion"))
        one = chain(add_unit(0, 11, "li", 3000, 6, "Gallic Foot  Battalion"))
        for v, ex, purse in (("one_purse100_control", one, 100), ("one_purse0", one, 0), ("two_purse100_control", two, 100), ("two_purse0", two, 0)):
            src = staged(START, [("money", 0, purse)], f"q1d_{v}", chain(W11, ex))
            go(f"q1d_{v}", src)
    elif CASE == "Q1e":
        b0 = sav.load(START); ids = sorted(b0["nations"][0]["city_list"]); ctl = [c for i, c in enumerate(ids) if i % 5 in (0, 2)]; test = [c for c in ids if c not in ctl]
        log("groups", test_stock0=test, control_full=ctl, n_test=len(test), n_control=len(ctl))
        src = staged(START, [], "q1e_winter", chain(set_calendar(week=1, season=3), set_cities(test, "supplies", 0), set_city_stock_to_pop_cap(ctl)))
        before, afters, diffs = go("q1e_winter", src, turns=4)
        prev = before
        for t, aft in enumerate(afters):
            rows = []
            for c in range(334):
                p, q = prev["cities"][c], aft["cities"][c]
                rows.append({"id": c, "group": "test" if c in test else "ctl" if c in ctl else "other", "owner_before": p[3], "stock_before": p[6], "stock_after": q[6], "loy_before": p[5], "loy_after": q[5]})
            log("famine_round", round=t + 1, rows=rows)
            prev = aft
    else:
        raise SystemExit("unknown case " + CASE)
    log("done")
except Exception as e:
    log("error", error=repr(e))
    try: log("error_state", shot=shot(g, "error"), boxes=boxes(g))
    except Exception: pass
    raise
finally:
    g.kill()
