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
    elif CASE == "Q1c_dead":
        # Greece really eliminated (as the game leaves a dead nation: unity 0, capital -1, no city): its 21 cities go to Macedonia (owner + both city lists + counts, L1)
        b0 = sav.load(START); greek = list(b0["nations"][7]["city_list"])
        NINE = [111, 116, 119, 122, 120, 123, 97, 100, 101]
        for v, ids in (("nine_dead", NINE), ("seven_dead_control", NINE[:7]), ("nine_dead_again", NINE)):
            ops = []
            for c in ids: ops += [("city", c, {"allegiance": 7, "loyalty": 5})]
            src = staged(START, ops, f"q1c_{v}", chain(W11, give_cities(7, 4, greek, kill_frm=True)))
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
    elif CASE == "Q1f":
        n_rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        ctl = [1, 4]            # Carthage (treasury 11,000) and Macedonia (275) keep their natural treasuries: in-save controls (never below the debt line)
        ops = [("treasury", n, -50000) for n in range(1, 16) if n not in ctl]
        variant = sys.argv[3] if len(sys.argv) > 3 else "base"
        if variant == "unity":      # all debtors at unity 400 (so a deposition's unity effect shows), Carthage solvent at unity 350 (< 400: the code deposes it with the same 1/9 although solvent), Macedonia solvent at unity 800
            ops += [("unity", n, 400) for n in range(1, 16) if n not in ctl] + [("unity", 1, 350), ("unity", 4, 800)]
        src = staged(START, ops, "q1f_debt50000" + ("_" + variant if variant != "base" else ""), W11)
        for i in range(n_rounds): go(f"q1f_r{i + 1:02d}", src)        # the same staged save opened again in the same process: the RNG goes on, so each opening is an independent trial
    elif CASE == "Q2":
        g.load(START, seed=12345)
        log("loaded", save=START.name, seed_line=g.seed_line)
        prev = snap(g)
        for t in range(6):
            if t in (0, 5): balance_sheet(g, f"before_round{t + 1}")
            prev = snap(g)
            name, texts = g.end_turn(); time.sleep(2)
            kept = keep_auto(name, g.turn_number(), f"round{t + 1}")
            after = snap(g); d = diff(prev, after)
            log("round_done", round=t + 1, tag=f"q2_round{t + 1}", autosave=name, kept=kept, texts=texts, cal=after["cal"], turn=g.turn_number(), news_new=new_news(prev, after), news_all=after["news"],
                rome_before=nat_brief(prev["nations"][0]), rome_after=nat_brief(after["nations"][0]), diff=d, root=shot(g, f"q2_round{t + 1}"))
            if t == 5: balance_sheet(g, "after_round6")
    elif CASE == "Q2b":
        # the quarter boundary on a staged week-11 save (no AI capture of a Roman city first, unlike the natural run): Balance sheet before, End turn, Balance sheet after; the same save opened again (RNG goes on)
        src = staged(START, [], "q2b_week11", W11)
        for i in range(int(sys.argv[2]) if len(sys.argv) > 2 else 3):
            if i == 0: g.load(src, seed=12345)
            else: g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            balance_sheet(g, f"q2b_{i + 1}_before")
            prev = snap(g)
            name, texts = g.end_turn(); time.sleep(2)
            kept = keep_auto(name, g.turn_number(), f"q2b_{i + 1}")
            after = snap(g); d = diff(prev, after)
            log("round_done", round=i + 1, tag=f"q2b_{i + 1}", autosave=name, kept=kept, texts=texts, cal=after["cal"], turn=g.turn_number(), news_new=new_news(prev, after), news_all=after["news"],
                rome_before=nat_brief(prev["nations"][0]), rome_after=nat_brief(after["nations"][0]), diff=d, root=shot(g, f"q2b_{i + 1}_after"))
            balance_sheet(g, f"q2b_{i + 1}_after")
    elif CASE == "Q3":
        g.load(START, seed=12345)
        nm = news_mem(g)
        log("news_start", lines=nm, destroys=[i for i, t in enumerate(nm) if " destroys army of " in t], sues=[i for i, t in enumerate(nm) if " sues " in t and "for peace" in t], windows=windows(g), root=shot(g, "start"))
        g.dismiss_popups()
        before = {w[0] for w in g.find_windows(".")}
        g.tool("news", pause=2.5)
        new = [w for w in g.find_windows(".") if w[0] not in before]
        log("news_tool", new_windows=[(w[0], w[1], w[4], w[5]) for w in new], windows=windows(g), root=shot(g, "news_tool"))
        for w in new[:2]:
            if w[4] > 100:
                f, o = ocr_window(g, "news_window", w[0]); log("news_window_ocr", title=w[1], image=f, ocr=o)
        info = [w for w in g.find_windows("^Information$")]
        for w in info[:1]:
            f, o = ocr_window(g, "information_window", w[0]); log("information_window_ocr", image=f, ocr=o)
    elif CASE == "Q6":
        n = int(sys.argv[2]); ops = [("relation", 0, k, 0) for k in range(1, 16)]
        src = staged(START, ops, "q6_peace_only")        # Rome at peace (0) with all 15 nations; everything else as the start save (spring week 1)
        for i in range(n):
            rec = light_round(g, f"q6_t{i + 1:03d}", src, i == 0)
            if rec.get("game_over"): break
    elif CASE == "Q5":
        sub = sys.argv[2]
        fst = lambda: (g.fleet_state(2), g.fleet_rec(2).hex())
        if sub == "move":
            first = True
            for tag, ex in (("rough", set_map(100, 47, 1)), ("calm_control", None), ("rough_again", set_map(100, 47, 1))):
                src = staged(PORT, [], f"q5_move_{tag}", ex)
                if first: g.load(src, seed=12345); first = False
                else: g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
                before = dict(state=fst(), moves=g.fleet_moves(2), target_cell=g.cell(100, 47), fleet_cell=g.cell(101, 46))
                pos, texts = g.move_fleet(2, 100, 47)
                info = [w for w in g.find_windows("^Information$")]
                io = ocr_window(g, f"{tag}_info", info[0][0]) if info else None
                log("fleet_move", tag=tag, before=before, pos_after=pos, texts=texts, state_after=fst(), moves_after=g.fleet_moves(2), target_cell_after=g.cell(100, 47),
                    origin_cell_after=g.cell(101, 46), info_ocr=io, root=shot(g, f"{tag}_after_move"))
        elif sub == "storm":
            n = int(sys.argv[3])
            srcs = {"rough": staged(PORT, [], "q5_storm_rough", set_fleet(2, cond=40, supplies=500, cell=1)),
                    "calm": staged(PORT, [], "q5_storm_calm", set_fleet(2, cond=40, supplies=500, cell=0))}
            first = True
            for k in range(n):
                for tag in (("rough", "calm") if k % 2 == 0 else ("calm", "rough")):
                    light_round(g, f"q5_storm_{tag}_{k + 1:02d}", srcs[tag], first); first = False
        else: raise SystemExit("sub")
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
