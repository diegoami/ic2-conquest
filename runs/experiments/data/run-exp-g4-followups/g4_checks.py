"""g4 follow-up original-side checks (issue #83), one case per check letter. Usage: python3 g4_checks.py <case> [args]. One fresh Wine process per case
(seed 12345, fast rollingsave seed exe, Xvfb :99). Staging is L1 (named save fields; length asserted; exclusive creation) and named in each log's `staged` line.
Cases: F  (save flag 0x4a0334 around Open / Save as / File > New, memory poller), C, B, A, D, G, H, I, K, J, L, E (see the finding)."""
import sys
from g4_lib import *
import g4_lib

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
        X = G / f"g4_F_{STAMP}_X.SAV"; shutil.copy2(START, X); log("X", file=X.name, sha256=sha(X), copy_kept=keep(X, "X_original_before_anything.SAV"))
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
