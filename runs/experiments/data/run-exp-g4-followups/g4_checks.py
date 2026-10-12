"""g4 follow-up original-side checks (issue #83), one case per check letter. Usage: python3 g4_checks.py <case> [args]. One fresh Wine process per case
(seed 12345, fast rollingsave seed exe, Xvfb :99). Staging is L1 (named save fields; length asserted; exclusive creation) and named in each log's `staged` line.
Cases: F  (save flag 0x4a0334 around Open / Save as / File > New, memory poller), C, B, A, D, G, H, I, K, J, L, E (see the finding)."""
import os, sys
if len(sys.argv) > 1 and sys.argv[1] == "E": os.environ["DISPLAY_IC2"] = ":98"        # check E runs on its own display with a window manager (the default :99 has none)
from g4_lib import *
from g4_lib import _hash_line
import g4_lib
from versioned import next_free as _next_free      # R1 round-4: save copies and the xfwm4 log use exclusive creation; a repeated stamp allocates the next free version instead of overwriting.

hook_environment()
g = Game()
W11 = set_calendar(week=11)
FIRST = [True]


def go(tag, src, turns=1):
    r = round_(g, tag, src, FIRST[0], turns); FIRST[0] = False; return r


def new_game_form_and_start(g, tag):
    """File > New already confirmed Yes: read the form's controls (Game.controls), tick Rome (single tick box in Rome's row), OK, wait for the form to close."""
    g.wait(lambda: g.find_windows("^Imperial Conquest 2$"), 10, "new game form"); time.sleep(1)
    cs = g.controls("Human and computer leaders"); log("new_game_form_controls", tag=tag, n_controls=len(cs))
    ticks = sorted((c for c in cs if "check" in c["cls"].lower()), key=lambda c: (c["y"], c["x"]))
    oks = [c for c in cs if c["text"].replace("&", "").strip().upper() == "OK"]
    panel = [c for c in cs if c["cls"] == "TPanel" and c["text"].strip() == "Rome"]
    if not ticks or len(oks) != 1 or len(panel) != 1: raise SystemExit("new game form: unexpected controls")
    in_row = [c for c in ticks if panel[0]["y"] <= c["y"] + c["h"] // 2 < panel[0]["y"] + panel[0]["h"]]
    if len(in_row) != 1: raise SystemExit("new game form: not exactly one tick in Rome's row")
    g.click_control(in_row[0], pause=0.5); g.click_control(oks[0])
    g.wait(lambda: not g.find_windows("Human and computer leaders"), 15, "new game form closed")


def predict_rebel(b, c):
    """The decompile's rule for a non-capital city at loyalty < 30 (FUN_0044c204): owner != allegiance -> (b) back to the allegiance nation when it has unity > 0, else (a) rebirth;
    owner == allegiance: (c) the LAST army (highest index) within Chebyshev < 10 of the city whose owner is at war (relation 3) with the city's owner, else (d) the neighbour (mask)
    with unity > 0 and the best cities - 2 x distance(capital), ties to the lowest index. `b` is a snap()."""
    ct = b["cities"][c]; owner, alleg = ct[3], ct[4]; N = b["nations"]
    if owner != alleg: return {"rule": "b" if N[alleg]["unity"] > 0 else "a", "to": alleg if N[alleg]["unity"] > 0 else None}
    pick, cand = -1, []
    for a in b["armies"]:
        if a["owner"] >= 0 and max(abs(a["x"] - ct[1]), abs(a["y"] - ct[2])) < 10 and N[owner]["relations"].get(sav.NATIONS[a["owner"]]) == 3: pick = a["owner"]; cand.append((a["id"], a["owner"]))
    if pick >= 0: return {"rule": "c", "to": pick, "war_armies_in_index_order": cand}
    best, pick = -1000, -1
    for n in range(16):
        if sav.NATIONS[n] in N[owner]["neighbours"] and N[n]["unity"] > 0:
            cap = b["cities"][N[n]["capital"]]; sc = N[n]["cities_count"] - 2 * max(abs(ct[1] - cap[1]), abs(ct[2] - cap[2]))
            if sc > best: best, pick = sc, n
    return {"rule": "d", "to": pick, "score": best}


def mobilize_rome(tag, unit_row=2):
    """Strategy > Recruit unit: pick the Rome row of the city list, click unit row `unit_row` (the ready state-17 heavy infantry of the start save), press Mobilize; log what changed
    (new armies with positions, changed old armies, queue troops, boxes). Controls come from the dialog."""
    g.open_recruit(); cs = g.controls("Army recruits"); w = g.find_windows("^Army recruits$")[0][0]; g.raise_window(w); time.sleep(0.5)
    cities = g.control(cs, cls="TListBox", index=0); units = g.control(cs, cls="TListBox", index=1)
    rows_found = None
    for r in range(3):
        g.click_list_row(cities, r, pause=0.6); f, o = ocr_window(g, f"{tag}_cityrow{r}", w); log("row", tag=tag, row=r, image=f, ocr=o)
        if "units at rome" in o.lower(): rows_found = r; break
    f, o = ocr_window(g, f"{tag}_units", w); log("units_list", tag=tag, image=f, ocr=o, city_row=rows_found)
    g.click_list_row(units, unit_row, pause=0.5)
    n_arm = g.i16(0x4A0324); sl = [g.i16(drv.NATIONS + 0x2e8 + 8 * k) for k in range(8)]
    old = {i: g.army_rec(i) for i in range(n_arm)}
    g.click_control(g.control(cs, text="Mobilize"), pause=2.0)
    bx = boxes(g); texts = g.dismiss_popups()
    n2 = g.i16(0x4A0324); new = [g.army_state(i) for i in range(n_arm, n2)]
    changed = [i for i in range(n_arm) if g.army_rec(i) != old[i]]
    log("mobilize_pressed", tag=tag, armies_before=n_arm, armies_after=n2, new_armies=[(a["id"], a["x"], a["y"], a["owner"], [(u["type"], u["troops"], u["quality"], u["name"]) for u in a["units"]]) for a in new],
        changed_old_armies=[(i, g.army_pos(i), [(u["type"], u["troops"], u["name"]) for u in g.army_state(i)["units"]]) for i in changed], slot_troops_before=sl,
        slot_troops_after=[g.i16(drv.NATIONS + 0x2e8 + 8 * k) for k in range(8)], boxes=bx, dismissed=texts)
    if g.find_windows("^Army recruits$"):
        try: g.close_controls("Army recruits", cs)
        except Exception as e: log("close_error", error=repr(e))


def depose_trial(tag, src, first, check_names=True):
    """Open staged `src` (first: fresh process), End turn once; report whether the "End of Game" window (the human leader deposed) opened, keep the autosave and the
    box image/OCR, close the box with OK from its controls. One trial = one log line `depose_trial`."""
    if first: g.load(src, seed=12345)
    else:
        g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
    me = g.i16(drv.CUR_NATION); base = drv.NATIONS + me * drv.NATION_LEN
    mem = lambda: {"unity": g.i16(base + 0x440), "cities_word": g.i16(base + 0x446), "treasury": struct.unpack("<i", g.mem(base + 0x438, 4))[0], "wealth": struct.unpack("<i", g.mem(base + 0x430, 4))[0],
                   "year_bc": g.i16(0x4A0332), "season": g.i16(0x4A032E), "week": g.i16(0x4A0330), "list_len": len([c for c in range(334) if struct.unpack("<h", g.mem(0x479590 + c * 34 + 18, 2))[0] == me])}
    rec = {"tag": tag, "save": Path(src).name, "pid": g.pid, "before": mem(), "turn_before": g.turn_number()}
    deposed, text, kept = False, None, None
    try:
        name, texts = g.end_turn(); time.sleep(2)
        kept = keep_auto(name, g.turn_number(), tag); rec["texts"] = texts
        deposed = bool(g.find_windows("^End of Game$"))
    except drv.GameOver as e:
        deposed = True; text = e.text; rec["game_over_exception"] = True
    if deposed:
        w = g.find_windows("^End of Game$")
        if w:
            g.raise_window(w[0][0]); f, o = ocr_window(g, f"{tag}_end_of_game", w[0][0]); rec["end_of_game_image"] = f; rec["end_of_game_ocr"] = o
            cs = g.controls("End of Game"); rec["end_of_game_controls"] = [(c["cls"], c["text"]) for c in cs]
            for _ in range(3):
                g.click_control(g.control(cs, text="OK"), pause=1.5)
                if not g.find_windows("^End of Game$"): break
            rec["end_of_game_closed"] = not g.find_windows("^End of Game$")
    rec.update(deposed=deposed, game_over_text=text, kept=kept, after=mem() if Path(f"/proc/{g.pid}").exists() else None, cal_after=g.calendar(), boxes=boxes(g), pid_alive=Path(f"/proc/{g.pid}").exists())
    log("depose_trial", **rec)
    return deposed


try:
    if CASE == "F":
        # Check F: where File > New clears the save flag (byte 0x4a0334). Static: static_flag_xrefs.txt. Dynamic: a 10 ms poller of the byte in ONE Wine process
        # (patched exe, seed 12345) with time-stamped UI events: fresh start (flag 0, no game) -> File > Open (positive control: the poller must see 0 -> 1)
        # -> File > New, answer No (control: the flag must not change) -> File > New, answer Yes (the clear must show up BEFORE the leaders form is ticked)
        # -> tick Rome + OK -> game running (flag stays 0) -> File > Save (opens Save as: flag 0 means "no default file").
        FLAG = 0x4A0334
        # R1 round-4: exclusive-creation save copy (next_free allocates a `.v2.SAV` etc. on collision, the previous file is preserved; the
        # unconditional shutil.copy2 would truncate an existing destination). The ART name `..._X.SAV` is shared with the log's `X_original_before_anything.SAV` kept copy below.
        X = G / f"g4_F_{STAMP}_X.SAV"; X = _next_free(X); shutil.copy2(START, X); log("X", file=X.name, sha256=sha(X), copy_kept=keep(X, "X_original_before_anything.SAV"))
        g.set_seed(12345); g.start()
        P = Poller(g.pid, FLAG).start(); time.sleep(0.5)
        P.mark("fresh_start_no_game"); log("flag_fresh", flag=g.mem(FLAG, 1)[0], loaded=g.loaded())
        g.open(X); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
        P.mark("after_open"); log("flag_after_open", flag=g.mem(FLAG, 1)[0], root=shot(g, "after_open"))
        # File > New, answer No
        g.menu("file", drv.FILE_ITEMS["new"]); time.sleep(2)
        conf = [p for p in g.popups() if p[1] == "Confirm"]
        P.mark("new_confirm_box_open"); log("new_confirm_no", boxes=boxes(g), n_confirm=len(conf), flag=g.mem(FLAG, 1)[0])
        if not conf: raise SystemExit("no Confirm box after File > New")
        g._answer_confirm(conf[0][0], yes=False); time.sleep(1.5)
        P.mark("after_answer_no"); log("flag_after_no", flag=g.mem(FLAG, 1)[0], windows=windows(g), still_loaded=g.loaded())
        # File > New, answer Yes
        sup = g.supersede_autosaves(); log("autosaves_superseded", folder=str(sup) if sup else None, files=sorted(p.name for p in sup.iterdir()) if sup else [])
        n_auto = len((G / "AUTOSAVE.LOG").read_text().splitlines()) if (G / "AUTOSAVE.LOG").exists() else 0
        g.menu("file", drv.FILE_ITEMS["new"]); time.sleep(2)
        conf = [p for p in g.popups() if p[1] == "Confirm"]
        P.mark("new_confirm_box_open_2"); log("new_confirm_yes", boxes=boxes(g), flag=g.mem(FLAG, 1)[0])
        if not conf: raise SystemExit("no Confirm box (2)")
        P.mark("answer_yes_click"); g._answer_confirm(conf[0][0], yes=True)
        P.mark("after_answer_yes")
        g.wait(lambda: g.find_windows("^Imperial Conquest 2$"), 10, "new game form"); P.mark("leaders_form_visible"); time.sleep(1)
        log("flag_form_open", flag=g.mem(FLAG, 1)[0], root=shot(g, "leaders_form"))
        new_game_form_and_start(g, "F"); P.mark("form_closed")
        g.wait(lambda: (G / "AUTOSAVE.LOG").exists() and len((G / "AUTOSAVE.LOG").read_text().splitlines()) > n_auto, 120, "new-game autosave")
        time.sleep(3); texts = g.dismiss_popups(); P.mark("new_game_running")
        for a in sorted(G.glob("AUTO*.SAV")): keep_auto(a.name, g.turn_number(), "newgame")
        log("flag_new_game_running", flag=g.mem(FLAG, 1)[0], popups=texts, root=shot(g, "after_new_game"))
        before_ids = set(sh("xdotool", "search", "--onlyvisible", "--name", "", check=False).split())
        g.menu("file", drv.FILE_ITEMS["save"]); time.sleep(3)
        new_ids = set(sh("xdotool", "search", "--onlyvisible", "--name", "", check=False).split()) - before_ids
        P.mark("after_save_menu"); log("save_after_new", new_windows=sorted(new_ids), flag=g.mem(FLAG, 1)[0], root=shot(g, "after_save_menu"))
        for w in sorted(new_ids): sh("xdotool", "key", "--window", w, "Escape", check=False)
        time.sleep(1)
        log("poller", **P.stop())
    elif CASE == "C":
        # Check C: the three other deposition disjuncts of FUN_00452034 (lines 55030-55038), human Rome, one End turn each from a staged spring-week-1 start:
        #   year 250 BC (0x4a0332 == 250), unity < 400, cities word > 333, with a control at the neighbouring value for each and a positive control (treasury -5200 at
        #   wealth 2,577,000, the g1 case) in the same process. Order = argv[2:] (cases listed below), default the whole list.
        WEALTH = set_wealth(0, 2_577_000)
        everything = {
            "pos_treasury_m5200": ([("treasury", 0, -5200)], WEALTH),
            "unity399": ([("unity", 0, 399)], None), "unity400_ctl": ([("unity", 0, 400)], None),
            "year250": ([], set_calendar(year=250)), "year251_ctl": ([], set_calendar(year=251)),
            "year251_roll": ([], chain(set_calendar(year=251, season=3, week=11))), "year252_roll_ctl": ([], chain(set_calendar(year=252, season=3, week=11))),
            "cities334_word": ([("ncities", 0, 334)], None), "cities333_word_ctl": ([("ncities", 0, 333)], None),
        }
        order = sys.argv[2:] or list(everything)
        for i, tag in enumerate(order):
            ops, ex = everything[tag]
            src = staged(START, ops, tag, ex)
            depose_trial(tag, src, i == 0)
    elif CASE == "C_real":
        # Check C, cities > 333 reached by an actual conquest staging: every other nation's cities go to Rome (L1 `give_cities`: owner words and both city lists and
        # count words consistent; the nations given up are dead: unity 0, capital -1). Control in the same process: Numidia keeps its capital city (Rome owns 333).
        b0 = sav.load(START)
        def conquer(keep_nation=None):
            fs = []
            for n in range(1, 16):
                ids = list(b0["nations"][n]["city_list"])
                if n == keep_nation:
                    cap = b0["nations"][n]["capital"]; ids = [c for c in ids if c != cap]
                    fs.append(give_cities(n, 0, ids, kill_frm=False))
                else: fs.append(give_cities(n, 0, ids, kill_frm=True))
            return chain(*fs)
        for i, (tag, ex) in enumerate((("pos_unity399", None), ("cities333_real_ctl", conquer(5)), ("cities334_real", conquer(None)))):
            ops = [("unity", 0, 399)] if tag == "pos_unity399" else []
            src = staged(START, ops, tag, ex)
            depose_trial(tag, src, i == 0)
    elif CASE == "B":
        # Check B: the trade refusal for an allied or at-war target, from the International Relations dialog (radio click = TPolitics_MakeTrade, boxes appear at the click).
        # Cases in ONE process (first the natural start save, then staged copies, File > Open): every case records the boxes at the radio click; the accepting
        # controls press OK and read Rome's relation afterwards. Galatia (5 trade partners? no: 0 partners, Rome peace) isolates the Rome-side relation from the
        # target's own partner count; Carthage (3 partners) with a pending trade offer from Carthage tests the offer exemption in the code (bVar1).
        def propose(tag, nation, ok):
            wid, cs, radios = relations_dialog(g)
            before = shot(g, f"{tag}_dialog_before", window=str(wid))
            res = []
            for k in range(2):         # a click into an inactive window may only activate it; a radio click is idempotent
                g.click_control(radios[nation * 4 + 1], pause=1.5)
                bx = boxes(g); res.append({"click": k + 1, "boxes": bx})
                if bx: break
            dismissed = g.dismiss_popups()
            after = shot(g, f"{tag}_dialog_after_click", window=str(wid))
            if ok:
                for _ in range(3):
                    g.click_control(g.control(cs, text="OK"), pause=1.5)
                    res.append({"ok_boxes": boxes(g)}); dismissed += g.dismiss_popups()
                    if not g.find_windows("^International Relations$"): break
            else:
                for _ in range(3):
                    g.click_control(g.control(cs, text="Cancel"), pause=1.0)
                    if not g.find_windows("^International Relations$"): break
            log("propose", tag=tag, nation=nation, press="OK" if ok else "Cancel", clicks=res, dismissed=dismissed, before=before, after=after, dialog_closed=not g.find_windows("^International Relations$"),
                rome_rel_to_target=rel(g, 0, nation), target_partners=[k for k in range(16) if rel(g, nation, k) == 1], rome_partners=[k for k in range(16) if rel(g, 0, k) == 1], rome_row=[rel(g, 0, k) for k in range(16)])
        g.load(START, seed=12345); log("loaded", save=START.name, seed_line=g.seed_line)
        propose("natural_gaul_war_3partners", 6, False)
        propose("natural_macedonia_cooldown_m8", 4, False)
        cases = [("galatia_peace_ctl", 12, [], None, True), ("galatia_war3", 12, [("relation", 0, 12, 3)], None, False), ("galatia_ally2", 12, [("relation", 0, 12, 2)], None, False),
                 ("galatia_cooldown_m8", 12, [("relation", 0, 12, -8)], None, False), ("carthage_full_no_offer", 1, [], None, False),
                 ("carthage_full_offer_from_carthage", 1, [], set_offer(1, 1), True), ("carthage_full_offer_from_seleucid", 1, [], set_offer(2, 1), False)]
        for tag, nat, ops, ex, ok in cases:
            src = staged(START, ops, tag, ex)
            g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            log("loaded", tag=tag, rome_row=[rel(g, 0, k) for k in range(16)], offer=(g.i16(0x49f008), g.i16(0x49f00a)), target=nat, target_partners=[k for k in range(16) if rel(g, nat, k) == 1])
            propose(tag, nat, ok)
    elif CASE == "A":
        # Check A: a mercenary hired IN PLAY (army 1 beside Heraclea, the offers of that city), read on the Balance sheet. One process: Balance sheet before (control: no
        # mercenary line), the hire dialog photographed and closed, then hire_mercs twice (each call picks the first row), Balance sheet after each, and the saved game.
        g.load(START, seed=12345); log("loaded", save=START.name, seed_line=g.seed_line)
        army = lambda: g.army_state(1)
        slots = lambda: [(u["slot"], u["type"], u["troops"], u["quality"], u["merc"], u["name"]) for u in army()["units"]]
        log("army1_before", state=army(), slots=slots(), treasury=struct.unpack("<i", g.mem(drv.NATIONS + 0x438, 4))[0])
        balance_sheet(g, "before_hire_control")
        w = g.army_tool(1, "mercs", "Recruit mercenary unit")
        f, o = ocr_window(g, "hire_dialog", w[0]); cs = g.controls("Recruit mercenary unit")
        log("hire_dialog", image=f, ocr=o, controls=[(c["cls"], c["text"], c["x"], c["y"], c["w"], c["h"]) for c in cs])
        g.close_controls("Recruit mercenary unit", cs, text="OK")
        for k in (1, 2):
            n, texts = g.hire_mercs(1, rows=(0,))
            log("hired", call=k, new_units=n, texts=texts, slots=slots(), state=army(), treasury=struct.unpack("<i", g.mem(drv.NATIONS + 0x438, 4))[0], root=shot(g, f"after_hire{k}"))
            rd, mem = balance_sheet(g, f"after_hire{k}")
            log("hire_summary", call=k, mercenary_line_ocr=rd["expenditure"]["mercenary_units"]["value"], mercenary_line_memory=mem["mercenary_units"], total_ocr=rd["expenditure"]["total"]["value"],
                expenditure_memory=mem["expenditure_total_if_all_five"])
            save(g, f"after_hire{k}.SAV")
    elif CASE == "D":
        # Check D: the other mobilise branches (FUN_0044a4e0 -> FUN_0044a120 / FUN_00449f08 / FUN_004492c0).
        #  D1 no free tile: Rome's ready queued unit (state 17, heavy infantry 4000 at Rome) mobilised through Army recruits; the 8 map words around Rome (101,43) are
        #     staged (L1) to sea (0) except the variant's free tiles (words 2..11 = free land, FUN_004492c0 keeps the LAST such tile in scan order x -1..1 outer, y -1..1 inner).
        #     Variants: ctl (unstaged), none_free, one_free_100_42, two_free_100_42_and_102_44 (the later one must win), all in ONE process.
        def pad_nothing(): return None
        def mob(tag):
            g.open_recruit(); cs = g.controls("Army recruits"); w = g.find_windows("^Army recruits$")[0][0]; g.raise_window(w); time.sleep(0.5)
            cities = g.control(cs, cls="TListBox", index=0); units = g.control(cs, cls="TListBox", index=1)
            rows_found = None
            for r in range(3):
                g.click_list_row(cities, r, pause=0.6); f, o = ocr_window(g, f"{tag}_cityrow{r}", w); log("row", tag=tag, row=r, image=f, ocr=o)
                if "units at rome" in o.lower(): rows_found = r; break
            f, o = ocr_window(g, f"{tag}_units", w); log("units_list", tag=tag, image=f, ocr=o, city_row=rows_found)
            g.click_list_row(units, 2, pause=0.5)
            n_arm = g.i16(0x4A0324); sl = [g.i16(drv.NATIONS + 0x2e8 + 8 * k) for k in range(8)]
            old = {i: g.army_rec(i) for i in range(n_arm)}
            g.click_control(g.control(cs, text="Mobilize"), pause=2.0)
            bx = boxes(g); texts = g.dismiss_popups()
            n2 = g.i16(0x4A0324); new = [g.army_state(i) for i in range(n_arm, n2)]
            changed = [i for i in range(n_arm) if g.army_rec(i) != old[i]]
            log("mobilize_pressed", tag=tag, armies_before=n_arm, armies_after=n2, new_armies=[(a["id"], a["x"], a["y"], a["owner"], [(u["type"], u["troops"], u["quality"], u["name"]) for u in a["units"]]) for a in new],
                changed_old_armies=[(i, [(u["type"], u["troops"], u["name"]) for u in g.army_state(i)["units"]]) for i in changed], slot_troops_before=sl,
                slot_troops_after=[g.i16(drv.NATIONS + 0x2e8 + 8 * k) for k in range(8)], boxes=bx, dismissed=texts, rome_armies=[(i, g.army_pos(i)) for i in range(n2) if g.army_state(i)["owner"] == 0])
            if g.find_windows("^Army recruits$"):
                try: g.close_controls("Army recruits", cs)
                except Exception as e: log("close_error", error=repr(e))
        RX, RY = 101, 43
        ring = [(RX + dx, RY + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
        def sea_except(free):
            fs = [set_map(x, y, 0) for x, y in ring if (x, y) not in free]
            f = chain(*fs); f.__doc__ = f"map words of Rome's 8 neighbours := 0 (sea) except {sorted(free)} (kept as they are)"; return f
        variants = [("ctl", None), ("none_free", sea_except(set())), ("one_free_100_42", sea_except({(100, 42)})), ("two_free_100_42_and_102_44", sea_except({(100, 42), (102, 44)}))]
        for i, (tag, ex) in enumerate(variants):
            src = staged(START, [], "d1_" + tag, ex)
            if i == 0: g.load(src, seed=12345)
            else: g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            log("loaded", tag=tag, armies=g.i16(0x4A0324), ring={f"{x},{y}": g.cell(x, y) for x, y in ring}, rome_slots=[tuple(struct.unpack("<4h", g.mem(drv.NATIONS + 0x2e4 + 8 * k, 8))) for k in range(4)])
            mob("d1_" + tag)
    elif CASE == "D2":
        # Check D, the distance branches of FUN_0044a120: a HUMAN nation mobilises into an own army only at distance exactly 1 (sVar1 == 1); an AI nation (human flag 0,
        # byte at 0x474b00 + nation * 0x494) also at distance < 6. Human arms (Rome, ready queued unit state 17 at Rome) with army 0 moved BY PLAY to a chosen distance; AI arms
        # (Thracia: Byzantium (170,38) with its own army 6 at distance 4; Carthage: Carthago with army 3 at distance 1, the positive control that the AI path ran at all): the AI
        # mobilises a queue unit whose state is 24 (FUN_004504f4), so the staged queue state (L1) is 24, one End turn, then the diff of the armies.
        RX, RY = 101, 43
        def mob(tag):
            g.open_recruit(); cs = g.controls("Army recruits"); w = g.find_windows("^Army recruits$")[0][0]; g.raise_window(w); time.sleep(0.5)
            cities = g.control(cs, cls="TListBox", index=0); units = g.control(cs, cls="TListBox", index=1)
            rows_found = None
            for r in range(3):
                g.click_list_row(cities, r, pause=0.6); f, o = ocr_window(g, f"{tag}_cityrow{r}", w); log("row", tag=tag, row=r, image=f, ocr=o)
                if "units at rome" in o.lower(): rows_found = r; break
            f, o = ocr_window(g, f"{tag}_units", w); log("units_list", tag=tag, image=f, ocr=o, city_row=rows_found)
            g.click_list_row(units, 2, pause=0.5)
            n_arm = g.i16(0x4A0324); sl = [g.i16(drv.NATIONS + 0x2e8 + 8 * k) for k in range(8)]
            old = {i: g.army_rec(i) for i in range(n_arm)}
            g.click_control(g.control(cs, text="Mobilize"), pause=2.0)
            bx = boxes(g); texts = g.dismiss_popups()
            n2 = g.i16(0x4A0324); new = [g.army_state(i) for i in range(n_arm, n2)]
            changed = [i for i in range(n_arm) if g.army_rec(i) != old[i]]
            log("mobilize_pressed", tag=tag, armies_before=n_arm, armies_after=n2, new_armies=[(a["id"], a["x"], a["y"], a["owner"], [(u["type"], u["troops"], u["quality"], u["name"]) for u in a["units"]]) for a in new],
                changed_old_armies=[(i, g.army_pos(i), [(u["type"], u["troops"], u["name"]) for u in g.army_state(i)["units"]]) for i in changed], slot_troops_before=sl,
                slot_troops_after=[g.i16(drv.NATIONS + 0x2e8 + 8 * k) for k in range(8)], boxes=bx, dismissed=texts)
            if g.find_windows("^Army recruits$"):
                try: g.close_controls("Army recruits", cs)
                except Exception as e: log("close_error", error=repr(e))
        cheb = lambda x, y: max(abs(x - RX), abs(y - RY))
        first = True
        for tag, want in (("human_dist6_natural", None), ("human_dist4", 4), ("human_dist1", 1), ("human_dist0_city", 0)):
            if first: g.load(START, seed=12345); first = False
            else: g.open(START); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            moved = None
            if want is not None:
                cands = [(x, y) for x in range(RX - 5, RX + 6) for y in range(RY - 5, RY + 6) if cheb(x, y) == want and g.cell(x, y) in (2, 3, 4, 84)]
                cands.sort(key=lambda c: max(abs(c[0] - 100), abs(c[1] - 37)))
                for (x, y) in cands[:6]:
                    pos, texts = g.move(0, x, y); log("move_try", tag=tag, target=(x, y), pos=pos, texts=texts)
                    if cheb(*pos) == want: moved = pos; break
                if moved is None: log("move_failed", tag=tag, want=want); continue
            log("army0", tag=tag, pos=g.army_pos(0), cheb=cheb(*g.army_pos(0)), armies=g.i16(0x4A0324))
            mob(tag)
        # AI arms: staged queue state 24, one End turn each (the same process, File > Open between)
        def ai_arm(tag, nation, slots, watch):
            src = staged(START, [], tag, chain(*[set_queue(nation, s_, state=24) for s_ in slots]) if slots else None)
            g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            before = snap(g)
            name, texts = g.end_turn(); time.sleep(2); kept = keep_auto(name, g.turn_number(), tag)
            after = snap(g)
            q = lambda sn: [tuple(struct.unpack_from("<4h", g.mem(drv.NATIONS + nation * drv.NATION_LEN + 0x2e4 + 8 * k, 8))) for k in range(8)]
            log("ai_arm", tag=tag, nation=nation, staged_slots=slots, texts=texts, kept=kept, queue_after=q(after), armies_before=len(before["armies"]), armies_after=len(after["armies"]),
                watch=[{"army": a, "before": [(u["type"], u["troops"], u["name"]) for u in before["armies"][a]["units"]], "after": [(u["type"], u["troops"], u["name"]) for u in after["armies"][a]["units"]],
                        "pos_before": (before["armies"][a]["x"], before["armies"][a]["y"]), "pos_after": (after["armies"][a]["x"], after["armies"][a]["y"])} for a in watch],
                new_armies=[(a["id"], a["owner"], a["x"], a["y"], [(u["type"], u["troops"]) for u in a["units"]]) for a in after["armies"][len(before["armies"]):]], diff_armies=diff(before, after)["armies"])
        ai_arm("ai_carthage_dist1_state24", 1, [1], [3, 2])
        ai_arm("ai_thracia_dist4_state24", 15, [1], [6])
        ai_arm("ai_thracia_dist4_state24_allslots", 15, [0, 1, 2], [6])
        ai_arm("ai_thracia_dist4_natural_ctl", 15, [], [6])
    elif CASE == "G":
        # Check G: the storm roll AWAY from an own city (FUN_004514ec 54553-54591: no own city marker in the 3x3 -> roll x 2 + 1, not halved). Rome's fleet 2 of the Antium
        # port save stands next to Antium (the g3 arm: halved). Here it is first MOVED BY PLAY to open sea (97,46) (no city in its 3x3) and the game's own Save As is the base of
        # the "away" arms; "near" arms use the port save itself. Four arms x pairs in ONE process: fleet 2 staged (L1: condition, supplies 500, covered-cell word 0 calm / 1 rough),
        # one End turn each, arms in a rotating order. Independent draws of one RNG stream (this configuration is run once; a rerun from the same start would replay a prefix).
        n_pairs = int(sys.argv[2]) if len(sys.argv) > 2 else 6; conds = [int(c) for c in sys.argv[3].split(",")] if len(sys.argv) > 3 else [80, 60]
        # The first attempt (g4_checks-G-20261012-110607.jsonl, stopped by us, kept) lost every "away" trial: Rome is at war with Carthage and Gaul in this save and the news of each away round reads
        # "Carthage sinks fleet of Rome." before the storm pass could act. The arms below stage peace (relation 0, L1, both directions) with Carthage (1) and Gaul (6) in the base save for ALL arms.
        PEACE = [("relation", 0, 1, 0), ("relation", 0, 6, 0)]
        PORTP = staged(PORT, PEACE, "g_port_peace")
        g.load(PORTP, seed=12345); log("loaded", save=PORTP.name, fleet2=g.fleet_state(2), rome_row=[rel(g, 0, k) for k in range(16)], ring={f"{x},{y}": g.cell(x, y) for x in range(100, 103) for y in range(45, 48)})
        pos, texts = g.move_fleet(2, 97, 46)
        log("fleet_moved", pos=pos, texts=texts, fleet2=g.fleet_state(2), ring={f"{x},{y}": g.cell(x, y) for x in range(96, 99) for y in range(45, 48)}, root=shot(g, "fleet_away"))
        if tuple(pos) != (97, 46): raise SystemExit("fleet 2 did not reach (97,46): " + repr(pos))
        away_base = ART / save(g, "away_base.SAV")
        order = [("near", "calm"), ("near", "rough"), ("away", "calm"), ("away", "rough")]
        base = {"near": PORTP, "away": away_base}
        for cond in conds:
            for k in range(n_pairs):
                arms = order[k % 4:] + order[:k % 4]
                for where, cell in arms:
                    tag = f"g_{where}_{cell}_c{cond}_{k + 1:02d}"
                    src = staged(base[where], [], tag, set_fleet(2, cond=cond, supplies=500, cell=1 if cell == "rough" else 0), stem="b")
                    rec = light_round(g, tag, src, False)
                    kept = rec.get("kept")
                    log("storm_trial", tag=tag, where=where, cell=cell, cond=cond, k=k + 1, fleet2_before=[struct.unpack_from("<13h", bytes.fromhex(rec["fleets_before"][2]))] if "fleets_before" in rec else None,
                        fleet2_after=struct.unpack_from("<13h", bytes.fromhex(rec["fleets_after"][2])) if rec.get("fleets_after") else None, cal_before=rec.get("cal_before"),
                        autosave_news=sav.parse((ART / kept).read_bytes())["news"] if kept else None, kept=kept)
    elif CASE == "D3":
        # Check D, human arms at distance 1 and 0 (the army cannot get there in one turn: army 0 has 8 moves): army 0 is moved BY PLAY to (100,40) in turn 1 (spring week 1), the turn
        # is ended, and in turn 2 it is moved to a tile at the wanted distance from Rome (101,43) before Mobilize. Rome's ready unit (queue state 17) is still ready in turn 2.
        RX, RY = 101, 43
        cheb = lambda x, y: max(abs(x - RX), abs(y - RY))
        first = True
        for tag, want in (("human_dist1_turn2", 1), ("human_dist0_turn2", 0), ("human_dist2_turn2", 2)):
            if first: g.load(START, seed=12345); first = False
            else: g.open(START); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            pos, texts = g.move(0, 100, 40); log("turn1_move", tag=tag, pos=pos, texts=texts, moves_left=g.army_state(0)["moves"])
            name, texts = g.end_turn(); time.sleep(2); keep_auto(name, g.turn_number(), tag + "_t1")
            log("turn2_start", tag=tag, army0=g.army_state(0)["moves"], pos=g.army_pos(0), queue=[tuple(struct.unpack("<4h", g.mem(drv.NATIONS + 0x2e4 + 8 * k, 8))) for k in range(4)], cal=g.calendar(), texts=texts)
            cands = [(x, y) for x in range(RX - 3, RX + 4) for y in range(RY - 3, RY + 4) if cheb(x, y) == want and g.cell(x, y) in (2, 3, 4, 84, 200)]
            cands.sort(key=lambda c: max(abs(c[0] - 100), abs(c[1] - 40)))
            reached = None
            for (x, y) in cands[:5]:
                pos, texts = g.move(0, x, y); log("move_try", tag=tag, target=(x, y), pos=pos, texts=texts)
                if cheb(*pos) == want: reached = pos; break
            if reached is None: log("move_failed", tag=tag, want=want, pos=g.army_pos(0)); continue
            log("army0", tag=tag, pos=g.army_pos(0), cheb=cheb(*g.army_pos(0)), armies=g.i16(0x4A0324))
            mobilize_rome(tag)
    elif CASE == "H":
        # Check H: rebellion of a Roman city (Arretium, 81, owner = allegiance = Rome, loyalty staged 2, week 11) with TWO armies of two different nations at war with Rome within
        # 9 tiles. The start save has only Gaul's army 9 near a Roman city (Arretium: 8 tiles); Rome's own army 0 stands next to Arretium (distance 1). A second war nation is made by
        # L1: army 0's owner word := Dacia (10) (or Gaul), army 9's owner word := Dacia in the other arm, the map marker words of the two tiles := 200 + owner (the engine's own marker
        # rule, FUN_00449f08), and relation Rome-Dacia := 3 (both directions). The rule keeps the LAST qualifying army (highest index): arm "idx9_dacia" must give Dacia, arm "idx0_dacia" Gaul.
        # The control (no army staged) is the g3 case: Gaul.
        base = [("city", 81, {"loyalty": 2})]
        arms = [("h_ctl_gaul_only", base, None),
                ("h_idx0_gaul_idx9_dacia", base + [("owner", 9, 10), ("owner", 0, 6), ("relation", 0, 10, 3)], chain(set_map(93, 28, 210), set_map(100, 37, 206))),
                ("h_idx0_dacia_idx9_gaul", base + [("owner", 0, 10), ("relation", 0, 10, 3)], set_map(100, 37, 210))]
        for tag, ops, ex in arms:
            src = staged(START, ops, tag, chain(W11, ex) if ex else W11)
            before, afters, diffs = go(tag, src)
            log("prediction", tag=tag, city=81, predicted=predict_rebel(before, 81), observed_owner=afters[0]["cities"][81][3], observed_loyalty=afters[0]["cities"][81][5],
                new_news=[t for t in afters[0]["news"] if "defects" in t or "falls" in t][-3:])
    elif CASE == "I":
        # Check I: the AI nations' quarter income. The staged week-11 start save (no staging beyond the week) is opened n times in ONE process and one End turn each (independent
        # RNG draws). The before state is the staged file, the after state the kept autosave (Rome's next turn start); analysis_I.py recomputes every nation's treasury from the code
        # (FUN_00451b40 54741-54889) and compares. The unit price table is read from memory here.
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        src = staged(START, [], "i_week11", W11)
        for i in range(n):
            if i == 0: g.load(src, seed=12345)
            else: g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            if i == 0: log("unit_prices", prices=[struct.unpack("<hh", g.mem(0x478fd2 + t * 40, 4)) for t in range(5)], note="(0x478fd2, 0x478fd4) + 40 t: short pair; 0x478fd4 is the regular-unit price the quarter upkeep uses")
            b0 = snap(g); name, texts = g.end_turn(); time.sleep(2); kept = keep_auto(name, g.turn_number(), f"i_{i + 1}")
            b1 = snap(g)
            log("quarter_round", opening=i + 1, staged=src.name, kept=kept, texts=texts, news_new=new_news(b0, b1), autosave_news=sav.parse((ART / kept).read_bytes())["news"],
                nations_before={sav.NATIONS[k]: nat_brief(b0["nations"][k]) for k in range(16)}, nations_after={sav.NATIONS[k]: nat_brief(b1["nations"][k]) for k in range(16)})
    elif CASE == "J":
        # Check J: where do the -8 relations of a (re)born or dead Greece come from? The AI seat's partner swap (FUN_0044fb7c, last loop 53423-53444: a trade partner k of the AI nation
        # whose tax base is below that of a candidate with relation 0 is dropped through the relation setter with 0, which turns a trade (1) into the cooldown -8, and the candidate
        # becomes a partner) is the code-side candidate. Arms (one process, week 11, one End turn each): control (no staging), Greece dead with 0, 7, 9 disloyal Greek-allegiance
        # Roman cities (rebirth needs more than 7), Greece alive at unity 0 with 9. The relation matrices of every nation before (the staged file) and after (the kept autosave) are compared
        # by analysis_J.py against the swap rule.
        b0s = sav.load(START); greek = list(b0s["nations"][7]["city_list"])
        NINE = [111, 116, 119, 122, 120, 123, 97, 100, 101]
        def arm(tag, ids, dead):
            ops = []
            for c in ids: ops += [("city", c, {"allegiance": 7, "loyalty": 5})]
            if not dead and ids: ops += [("unity", 7, 0)]
            return tag, ops, chain(W11, give_cities(7, 4, greek, kill_frm=True)) if dead else W11
        arms = [arm("j_control_nostage", [], False), arm("j_dead_0", [], True), arm("j_dead_7", NINE[:7], True), arm("j_dead_9", NINE, True), arm("j_alive_unity0_9", NINE, False), arm("j_control_nostage_again", [], False)]
        for tag, ops, ex in arms:
            src = staged(START, ops, tag, ex)
            before, afters, diffs = go(tag, src)
            log("j_summary", tag=tag, greece_rel_before=before["nations"][7]["relations"], greece_rel_after=afters[0]["nations"][7]["relations"], tax_base_after={sav.NATIONS[k]: afters[0]["nations"][k]["tax_base"] for k in range(16)},
                unity_after={sav.NATIONS[k]: afters[0]["nations"][k]["unity"] for k in range(16)})
    elif CASE == "D4":
        # Check D, AI branch with the AI's own gating satisfied. The AI mobilises queued state-24 units only when its war threat exceeds its strength (FUN_0044ffbc: +15000 per war
        # relation, +armies of war nations ...; FUN_004504f4 is called with the deficit) and, inside it, only if a ready unit has an own army within distance < 6 of its city or at least 4
        # units are ready. L1 staging: the AI nation at war (relation 3, both directions) with eight other nations, one queue slot's state := 24. Arms (one process, one End turn each):
        #   thracia_dist4: Byzantium, own army 6 at distance 4 (the < 6 branch: merge into army 6 expected)   carthage_dist1: army 3 at distance 1 (positive control: merge by either branch)
        #   galatia_dist8: Ancyra, own army 12 at distance 8 (>= 6: a NEW army at a free tile expected)       thracia_dist4_nowars: the same slot without the wars (gating control: nothing).
        def wars(n, others): return [("relation", n, k, 3) for k in others]
        def arm(tag, nation, slot, others, watch, city_name):
            ops = wars(nation, others) if others else []
            src = staged(START, ops, tag, set_queue(nation, slot, state=24))
            g.open(src) if not FIRST[0] else g.load(src, seed=12345)
            FIRST[0] = False
            g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            before = snap(g)
            name, texts = g.end_turn(); time.sleep(2); kept = keep_auto(name, g.turn_number(), tag)
            after = snap(g)
            qrow = lambda: [tuple(struct.unpack_from("<4h", g.mem(drv.NATIONS + nation * drv.NATION_LEN + 0x2e4 + 8 * k, 8))) for k in range(6)]
            log("ai_arm", tag=tag, nation=nation, city=city_name, staged_slot=slot, wars_with=others, texts=texts, kept=kept, queue_after=qrow(), armies_before=len(before["armies"]), armies_after=len(after["armies"]),
                watch=[{"army": a, "owner": after["armies"][a]["owner"], "before": [(u["type"], u["troops"], u["name"]) for u in before["armies"][a]["units"]], "after": [(u["type"], u["troops"], u["name"]) for u in after["armies"][a]["units"]],
                        "pos_before": (before["armies"][a]["x"], before["armies"][a]["y"]), "pos_after": (after["armies"][a]["x"], after["armies"][a]["y"])} for a in watch],
                new_armies=[(a["id"], a["owner"], a["x"], a["y"], [(u["type"], u["troops"], u["name"]) for u in a["units"]]) for a in after["armies"][len(before["armies"]):]],
                relations_after={sav.NATIONS[k]: after["nations"][nation]["relations"].get(sav.NATIONS[k]) for k in range(16) if k != nation})
        everyone = lambda n: [k for k in range(16) if k != n][:8]
        arm("d4_thracia_dist4_wars8", 15, 1, [k for k in range(16) if k != 15][:8], [6], "Byzantium (192)")
        arm("d4_carthage_dist1_wars8", 1, 1, [k for k in range(16) if k != 1][:8], [3], "Carthago (72)")
        arm("d4_galatia_dist8_wars8", 12, 1, [k for k in range(16) if k != 12][:8], [12], "Ancyra (218)")
        arm("d4_thracia_dist4_nowars_ctl", 15, 1, [], [6], "Byzantium (192)")
    elif CASE == "K":
        # Check K: trade/alliance offer eligibility at each roll (FUN_00452034 54975-55030). n rounds, each = File > Open of the same staged save (same state, the RNG goes on: independent
        # draws) + End turn, autosave kept; analysis_K.py recomputes, from each kept autosave (the state at the roll), which proposers were eligible for which offer and compares
        # the observed proposer/type and the frequency. Variants: nat (start save unstaged: Rome trades with Illyria, at war with Gaul), p3 (Rome also trades with Carthage and Seleucid:
        # three partners, so the tax-base threshold applies), nowar (peace with Gaul: Rome at war with nobody, so the alliance branch is open).
        variant, n = sys.argv[2], int(sys.argv[3])
        ops = {"nat": [], "p3": [("relation", 0, 1, 1), ("relation", 0, 2, 1)], "nowar": [("relation", 0, 6, 0)]}[variant]
        src = staged(START, ops, "k_" + variant)
        for i in range(n):
            rec = light_round(g, f"k_{variant}_t{i + 1:03d}", src, i == 0)
            if rec.get("game_over"): break
    elif CASE == "D5":
        # Check D, the AI's "four ready units" branch: Galatia (Ancyra (192,38), own army 12 at distance 8 >= 6) with FOUR queue slots at state 24 and eight wars: no army within 6,
        # so FUN_0044a4e0 falls to FUN_00449f08 (a NEW army at a free tile) if the AI calls it at all (FUN_004504f4 calls it when >= 4 units are ready). Control (same process): the same with three.
        def wars(n, others): return [("relation", n, k, 3) for k in others]
        for i, (tag, slots) in enumerate((("d5_galatia_4ready", [0, 1, 2, 3]), ("d5_galatia_3ready_ctl", [0, 1, 2]))):
            src = staged(START, wars(12, [k for k in range(16) if k != 12][:8]), tag, chain(*[set_queue(12, s_, state=24) for s_ in slots]))
            if i == 0: g.load(src, seed=12345)
            else: g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            before = snap(g); name, texts = g.end_turn(); time.sleep(2); kept = keep_auto(name, g.turn_number(), tag); after = snap(g)
            log("ai_arm", tag=tag, nation=12, staged_slots=slots, texts=texts, kept=kept, queue_after=[tuple(struct.unpack_from("<4h", g.mem(drv.NATIONS + 12 * drv.NATION_LEN + 0x2e4 + 8 * k, 8))) for k in range(10)],
                armies_before=len(before["armies"]), armies_after=len(after["armies"]),
                watch=[{"army": 12, "before": [(u["type"], u["troops"], u["name"]) for u in before["armies"][12]["units"]], "after": [(u["type"], u["troops"], u["name"]) for u in after["armies"][12]["units"]],
                        "pos_before": (before["armies"][12]["x"], before["armies"][12]["y"]), "pos_after": (after["armies"][12]["x"], after["armies"][12]["y"])}],
                new_armies=[(a["id"], a["owner"], a["x"], a["y"], [(u["type"], u["troops"], u["name"]) for u in a["units"]]) for a in after["armies"][len(before["armies"]):]])
    elif CASE == "L_probe":
        # Check L, step 1: the 20 fixed storm centres of the weather (FUN_00451304: DAT_00479540, 20 x (x, y) shorts) read from memory after loading the Antium port save, with the
        # distance of each to Rome's fleet 2 and the map words of the 3 x 3 around it (a cell is painted only with no city marker 20..99 in its 3 x 3).
        g.load(PORT, seed=12345)
        cen = [struct.unpack("<hh", g.mem(0x479540 + 4 * k, 4)) for k in range(20)]
        f2 = g.fleet_state(2)
        log("centres", centres=cen, fleet2=f2, rows=[{"k": k, "x": x, "y": y, "dist_to_fleet2": max(abs(x - f2["x"]), abs(y - f2["y"])), "word": g.cell(x, y),
                                                      "ring": [g.cell(min(319, max(0, x + dx)), min(139, max(0, y + dy))) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]} for k, (x, y) in enumerate(cen)])
    elif CASE == "L":
        # Check L: a rough-sea cell painted by the game's own weather (FUN_00451304: 20 fixed storm centres, one painted box per firing centre; a fleet standing in a painted box has its
        # covered-cell word set to 1). Rome's fleet 2 of the Antium port save (supplies staged 500, L1, so the long run does not starve it; peace staged with Carthage and Gaul as in G,
        # because Carthage sinks fleets at sea) is moved BY PLAY to the centre 5 at (100,56), then End turn rounds are played naturally (up to n). After every round the fleet record, the
        # number of rough cells (map word 1 on sea), the rough cells within 1 tile of the fleet and the covered-cell word are logged and the autosave kept. When the covered word reads 1
        # at a turn start, the NEXT round's storm roll is the one the weather made rough (the covered word is read by the storm pass before the weather call rewrites it, FUN_004514ec).
        # When a rough cell is adjacent to the fleet at a turn start, one move onto it is made and its cost and the Information window text are logged (once).
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 40; tx, ty = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (100, 56)
        src = staged(PORT, [("relation", 0, 1, 0), ("relation", 0, 6, 0)], "l_peace_supplies500", set_fleet(2, supplies=500))
        g.load(src, seed=12345)
        def rough_cells():
            mp = g.mem(drv.MAP, 320 * 140 * 2); return [(i // 140, i % 140) for i in range(320 * 140) if mp[2 * i] == 1 and mp[2 * i + 1] == 0]
        def fstate():
            r = g.fleet_rec(2); f = struct.unpack_from("<13h", r); return {"x": f[0], "y": f[1], "moves": f[6], "supplies": f[7], "ships": f[9], "cond": f[10], "cell": f[12], "raw": r.hex()}
        log("start", fleet2=fstate(), rough=len(rough_cells()), cal=g.calendar())
        pos, texts = g.move_fleet(2, tx, ty); log("fleet_moved", target=(tx, ty), pos=pos, texts=texts, fleet2=fstate(), root=shot(g, "fleet_at_centre"))
        tested, covered_rounds = False, 0
        for r in range(1, n + 1):
            before = fstate(); cal0 = g.calendar()
            name, texts = g.end_turn(); time.sleep(2); kept = keep_auto(name, g.turn_number(), f"l_r{r:02d}")
            after = fstate(); rc = rough_cells(); fx, fy = after["x"], after["y"]
            near = [c for c in rc if max(abs(c[0] - fx), abs(c[1] - fy)) <= 1]
            news = [t for t in sav.parse((ART / kept).read_bytes())["news"] if "fleet belonging" in t]
            log("l_round", round=r, cal_before=cal0, cal_after=g.calendar(), before=before, after=after, rough_total=len(rc), rough_within1=near, covered_flag_now=after["cell"], storm_news=news, texts=texts, kept=kept, rough_cells=(rc if r <= 3 else None), rough_cells_note="full list only for rounds 1-3: the weather world is the same whatever the fleet does (the two first runs had identical rough counts), so a later run can place the fleet where the weather will paint")
            if after["cell"] == 1: covered_rounds += 1
            if near and not tested and after["cell"] == 0:
                tx2, ty2 = near[0]; tested = True; mv0 = after["moves"]
                pos, texts = g.move_fleet(2, tx2, ty2); a2 = fstate()
                info = [w for w in g.find_windows("^Information$")]; io = ocr_window(g, "rough_move_info", info[0][0]) if info else None
                log("rough_move", target=(tx2, ty2), word_at_target_before=1, pos=pos, moves_before=mv0, moves_after=a2["moves"], cost=mv0 - a2["moves"], covered_after=a2["cell"], info_ocr=io, texts=texts, root=shot(g, "rough_move"))
            if g.find_windows("^End of Game$") or after["ships"] <= 0: break
            if covered_rounds >= 3 and tested: break
    elif CASE == "E":
        # Check E: a REAL X-button click on the main window's title bar, under xfwm4 (installed, no root needed) on a separate Xvfb display :98 (the other runs use :99 without a window manager).
        # The quit prompt is the one g1 G6 reached with a posted WM_SYSCOMMAND. Control in the same display: with no game loaded the click ends the process at once, no box.
        # Menu clicks of the driver use absolute coordinates with the client at (0,0): here the main window's client origin is read (xwininfo) and added to the menu clicks only.
        wm_log = lambda **kw: log("e_" + str(kw.pop("step", "wm")), **kw)
        def alive(): return subprocess.run(["pgrep", "-f", "^Imperial Conquest"], capture_output=True).returncode == 0
        env98 = dict(os.environ, DISPLAY=":98")
        if subprocess.run(["pgrep", "-fx", "Xvfb :98 -screen 0 1280x1024x24"], capture_output=True).returncode:
            subprocess.Popen(["setsid", "Xvfb", ":98", "-screen", "0", "1280x1024x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(2)
        if subprocess.run(["pgrep", "-x", "xfwm4"], capture_output=True).returncode == 0: subprocess.run(["pkill", "-x", "xfwm4"]); time.sleep(1)
        # R1 round-4: exclusive creation (the previous `open(path, "w")` truncated an existing file at the same second-resolution stamp); allocate the next free version first.
        wm_log_path = _next_free(ART / f"E_{STAMP}_xfwm4.out")
        wm_out = open(wm_log_path, "w")      # the "w" truncate is safe once _next_free has chosen the destination
        wm = subprocess.Popen(["setsid", "xfwm4", "--compositor=off"], env=env98, stdout=wm_out, stderr=subprocess.STDOUT); time.sleep(10)      # a game started within a few seconds of the window manager was not decorated in the first attempts
        chk = subprocess.run(["xprop", "-root", "_NET_SUPPORTING_WM_CHECK"], env=env98, capture_output=True, text=True).stdout
        wm_log(display=":98", xfwm4_pid=wm.pid, xfwm4_alive=wm.poll() is None, supporting_wm_check=chk.strip())
        def xinfo(wid, *a): return subprocess.run(["xwininfo", "-id", str(wid)] + list(a), env=env98, capture_output=True, text=True).stdout
        def main_win():
            w = [x for x in g.find_windows("^Imperial Conquest 2") if x[4] > 100]      # the 1 x 1 helper windows of Wine carry the same name
            return w[0][0] if w else None
        def geom(wid):
            t = xinfo(wid); import re as _re
            ax, ay = (int(_re.search(r"Absolute upper-left X:\s+(-?\d+)", t).group(1)), int(_re.search(r"Absolute upper-left Y:\s+(-?\d+)", t).group(1)))
            wd, ht = (int(_re.search(r"Width: (\d+)", t).group(1)), int(_re.search(r"Height: (\d+)", t).group(1)))
            ext = subprocess.run(["xprop", "-id", str(wid), "_NET_FRAME_EXTENTS"], env=env98, capture_output=True, text=True).stdout.strip()
            return {"client_x": ax, "client_y": ay, "w": wd, "h": ht, "frame_extents": ext}
        def sh_x(*a): return subprocess.run(list(a), env=env98, capture_output=True, text=True).stdout
        OFF = [0, 0]
        def menu_wm(name, item):
            g.reset_ui(); g.click(OFF[0] + drv.MENU[name], OFF[1] + 36, pause=0.8); g.click(OFF[0] + drv.MENU[name] + 20, OFF[1] + drv.MENU_ITEM_Y(item), pause=1.2)
        def close_info_boxes():
            out = []
            for _ in range(5):
                bx = [p_ for p_ in g.popups() if p_[1] == "Information" and p_[4] < 600 and p_[5] < 300]
                if not bx: break
                sh_x("xdotool", "windowfocus", str(bx[0][0])); time.sleep(0.5); sh_x("xdotool", "key", "--window", str(bx[0][0]), "Return"); time.sleep(1.2); out.append((bx[0][0], bx[0][1]))
            return out
        g.menu = menu_wm; g.reset_ui = lambda: g.key("Escape")      # the maximised window leaves no bare root point for the driver's reset_ui
        def frame_of(wid):
            """the decorated frame: walk up xwininfo -tree parents until the child of root"""
            t = sh_x("xwininfo", "-id", str(wid), "-tree")
            import re as _re
            m = _re.search(r"Parent window id: (0x[0-9a-f]+)", t); return m.group(1) if m else None
        E_SEQ = [0]                                                          # R2 round-2: every E direct image/log writer gets a unique name via this counter; a name collision is raised, never silently overwritten
        def _e_png(kind, tag):
            """return a fresh ART / E_{STAMP}_{tag}_{kind}_{seq:03d}.png (raises if the name already exists; the helper that calls it can change the tag to keep names unique)."""
            E_SEQ[0] += 1; seq = E_SEQ[0]
            p = ART / f"E_{STAMP}_{tag}_{kind}_{seq:03d}.png"
            if p.exists(): raise SystemExit(f"{p} exists: E's direct image names must be unique (R2)")
            return p, seq
        def click_x_button(tag):
            wid = main_win(); fr = frame_of(wid)
            fg = geom(fr) if fr else None; cg = geom(wid)
            png, seq = _e_png("titlebar", tag)
            sh_x("import", "-window", "root", "-crop", f"{fg['w']}x{max(40, cg['client_y'] - fg['client_y'] + 4)}+{fg['client_x']}+{fg['client_y']}", str(png)); _hash_line(png)
            wm_log(tag=tag, frame=fr, frame_geom=fg, client_geom=cg, titlebar_image=png.name, seq=seq)
            return fg, cg, png
        g.set_seed(12345); g.start()
        wid = main_win(); cg0 = geom(wid); wm_log(step="started", main_window=wid, client=cg0, tree=sh_x("xwininfo", "-root", "-tree")[:1500], root=shot(g, "started"))
        OFF[0], OFF[1] = cg0["client_x"], cg0["client_y"]
        fg, cg, png = click_x_button("nogame")
        if len(sys.argv) < 4:
            wm_log(step="probe_only", note="pass <dx from the frame's right edge> <dy from the frame's top> of the close button to click it")
        else:
            dx, dy = int(sys.argv[2]), int(sys.argv[3])
            def real_click(tag):
                fg, cg, png = click_x_button(tag)                                # R2 round-2: each call now gets its own titlebar_<seq>.png; a repeated tag no longer overwrites
                x, y = fg["client_x"] + fg["w"] - dx, fg["client_y"] + dy
                sh_x("xdotool", "mousemove", str(x), str(y)); time.sleep(0.5)
                snap_png, seq = _e_png("before_click", tag)
                sh_x("import", "-window", "root", "-crop", f"{fg['w']}x{cg['client_y'] - fg['client_y'] + 4}+{fg['client_x']}+{fg['client_y']}", str(snap_png)); _hash_line(snap_png)
                sh_x("xdotool", "click", "1"); wm_log(tag=tag, clicked_at=(x, y), image=snap_png.name, seq=seq)
                return (x, y)
            # control: no game loaded -> the real click ends the process at once, no box
            real_click("nogame")
            for _ in range(20):
                if not alive(): break
                time.sleep(0.5)
            wm_log(step="after_click_nogame", alive=alive(), boxes=boxes(g) if alive() else None)
            # a game loaded -> the real click raises the quit prompt
            g.set_seed(12345); g.start(); wid = main_win(); cg1 = geom(wid); OFF[0], OFF[1] = cg1["client_x"], cg1["client_y"]
            # R1 round-4: exclusive-creation save copy (the unconditional shutil.copy2 would truncate an existing destination).
            X = G / f"g4_E_{STAMP}_X.SAV"; X = _next_free(X); shutil.copy2(START, X); wm_log(step="X", file=X.name, sha256=sha(X), copy_kept=keep(X, "X_original_before_anything.SAV"))
            g.open(X); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            wm_log(step="loaded", loaded=g.loaded(), windows=windows(g), root=shot(g, "loaded"), dismissed_before=close_info_boxes())      # the start save opens with the offer box "Bithynia wants to trade with Rome."
            try:
                for k, answer in ((1, "No"), (2, "Yes")):
                    real_click(f"game_click{k}"); tl = []
                    for _ in range(30):      # watch 3 s at 0.1 s for a transient box or the exit
                        tl.append((round(time.time() % 1000, 1), alive(), [p_[1] for p_ in g.popups()] if alive() else None)); time.sleep(0.1)
                    wm_log(step="click_timeline", click=k, timeline=tl[::3])
                    bx = boxes(g); conf = [p_ for p_ in g.popups() if p_[1] == "Confirm"]
                    wm_log(step="after_click_game", click=k, alive=alive(), boxes=bx, n_confirm=len(conf))
                    if conf:
                        cs = g.controls("Confirm"); wm_log(step="box_controls", controls=[(c["cls"], c["text"]) for c in cs])
                        for _ in range(3):
                            g.click_control(next(c for c in cs if c["text"].replace("&", "") == answer), pause=1.5)
                            if not [p_ for p_ in g.popups() if p_[1] == "Confirm"] or not alive(): break
                        time.sleep(2)
                        wm_log(step="after_answer", answer=answer, alive=alive(), windows=windows(g) if alive() else None, root=shot(g, f"game_after_{answer}") if alive() else None)
                    # R3 round-5: stop the click loop when the game exits (e.g., real_click exited the process without a quit prompt — the
                    # previous behaviour tried game_click2 against a nonexistent main window and bypassed cleanup).
                    if not alive():
                        wm_log(step="game_exit_after_click", click=k, note="game exited without quit prompt; breaking click loop")
                        break
            finally:
                # R3 round-5: window-manager cleanup and final log hashing in a `finally` block so they run on every exit path
                # (game exit, raise from click_x_button, etc.). The earlier code put this AFTER the else block; if the click loop raised,
                # xfwm4 was left running and the log was never hashed.
                wm.terminate()
                # R1 round-4: hash the xfwm4 log AFTER the process has stopped and its output file descriptor is closed (the previous inline
                # hash at process start could read the file while xfwm4 was still appending).
                try:
                    wm.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    wm.kill(); wm.wait(timeout=5)
                try:
                    wm_out.close()      # closing before _hash_line ensures every buffered byte is flushed and the read sees the final contents
                except Exception:
                    pass
                _hash_line(wm_log_path)
    elif CASE == "none":
        pass
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
