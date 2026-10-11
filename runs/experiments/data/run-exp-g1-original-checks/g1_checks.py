"""Original-side checks 2, 3, 5, 6, 7, 8, 9, 10 of the v0.5.0 gap analysis (rows_g1.md "Original-side checks needed"; issue #78).
Usage: python3 g1_checks.py <case> [args]. One fresh Wine process per case. Cases:
  G2_merc    Balance sheet with a mercenary unit on the payroll (L1-staged merc unit; control: the same save without it)
  G2_fleet   Balance sheet "Fleet" line with a fleet under construction (natural: Build fleet) and with a finished fleet (PORT save)
  G2_debt    Debt limit display rounding at several wealth values (L1-staged wealth)
  G2_depose  Deposition test at the start of the human's turn: unrounded or rounded Debt limit (L1-staged treasury, then End turn)
  G3_cap     Trade refusals (L1-staged relations): own 3-partner cap, target with 3 partners, controls
Staging is L1 and labelled: only named save fields are patched (stage.py ops and g1_lib helpers), army positions never."""
import sys, os
from g1_lib import *
import g1_lib

hook_environment()
g = Game()


def partner_unit_name(n): return f"{n} Battalion"


try:
    if CASE == "G2_merc":
        g.load(START, seed=12345)
        log("loaded", save=START.name, seed_line=g.seed_line, army0=g.army_state(0))
        balance_sheet(g, "control_no_merc"); save(g, "control_loaded.SAV")
        variants = {"li": ("merc_li3000_q6", add_unit(0, 11, "li", 3000, 6, "Gallic Foot  Battalion")),
                    "hc": ("merc_hc2400_q9", add_unit(0, 35, "hc", 2400, 9, "Egyptian Dragoons  Battalion")),
                    "hi": ("merc_hi4000_q8", add_unit(0, 11, "hi", 4000, 8, "Gallic Guards  Battalion"))}
        for tag, extra in [variants[sys.argv[2]]]:
            src = staged(START, [], tag, extra)
            g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            log("alive", pid=g.pid, proc=Path(f"/proc/{g.pid}").exists(), windows=windows(g))
            log("opened_staged", tag=tag, save=src.name, army0_slots=[(k, struct.unpack_from("<4h", g.army_rec(0), 16 + 32 * k)) for k in range(20)
                                                                       if struct.unpack_from("<h", g.army_rec(0), 16 + 32 * k + 4)[0] > 0])
            balance_sheet(g, tag)
    elif CASE == "G2_fleet":
        g.load(START, seed=12345)
        log("loaded", save=START.name, seed_line=g.seed_line)
        balance_sheet(g, "before_build")
        log("fleets_before", fleets=[g.fleet_state(i) for i in range(g.i16(0x4A0326))])
        texts = g.build_fleet(2)
        log("build_fleet", texts=texts, notices=g.build_fleet_notices, root=shot(g, "after_build"),
            fleets=[(i, g.fleet_state(i), g.fleet_rec(i).hex()) for i in range(g.i16(0x4A0326))])
        balance_sheet(g, "fleet_under_construction"); save(g, "under_construction.SAV")
        g.open(PORT); g.wait(g.loaded, 20, "loaded"); time.sleep(1)
        log("opened", save=PORT.name, fleets=[(i, g.fleet_state(i), g.fleet_rec(i).hex()) for i in range(g.i16(0x4A0326))])
        balance_sheet(g, "port_save_finished_fleets")
    elif CASE == "G2_debt":
        wealths = [2_577_000, 2_400_000, 2_499_999, 2_500_500, 3_000_000, 6_000_000, 9_999_999, 10_000_000, 12_000_000]
        first = True
        for w in wealths:
            src = staged(START, [], f"wealth{w}", set_wealth(0, w))
            if first: g.load(src, seed=12345); first = False
            else: g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(1)
            rd, mem = balance_sheet(g, f"wealth{w}")
            log("debt_summary", wealth=w, displayed=rd["debt_limit"]["value"], unrounded=w // 500, memory_formula=mem["debt_limit_displayed"])
    elif CASE == "G2_depose":
        # treasury relative to the debt line of wealth 2,577,000: unrounded 5154 (deposed below -5154), displayed/rounded 5000 (deposed below -5000)
        tag, treasury = sys.argv[2], int(sys.argv[3])
        src = staged(START, [("treasury", 0, treasury)], tag, set_wealth(0, 2_577_000))
        g.load(src, seed=12345)
        log("loaded", tag=tag, treasury_staged=treasury, memory=balance_from_memory(g))
        balance_sheet(g, tag + "_before")
        try:
            name, texts = g.end_turn()
            log("end_turn_ok", autosave=name, texts=texts, memory_after=balance_from_memory(g), turn=g.turn_number(), root=shot(g, tag + "_after_end_turn"))
        except drv.GameOver as e:
            log("game_over", text=e.text, windows=windows(g), root=shot(g, tag + "_game_over"), memory=balance_from_memory(g))
        except DriverError as e:
            log("end_turn_error", error=repr(e), boxes=boxes(g), windows=windows(g))
    elif CASE == "G3_cap":
        variant = sys.argv[2]            # natural_target3 | own3

        def relations_dialog():
            g.dismiss_popups()
            for _ in range(3):
                g.tool("relations", pause=1.5)
                if g.find_windows("^International Relations$"): break
            w = g.find_windows("^International Relations$"); g.raise_window(w[0][0])
            for _ in range(8):
                try: cs = g.controls("International Relations"); break
                except DriverError: time.sleep(1)
            radios = sorted((c for c in cs if c["cls"] == "TRadioButton"), key=lambda c: (c["y"], c["x"]))
            if len(radios) != 64: raise DriverError("expected 64 radios, found %d" % len(radios))
            return w[0][0], cs, radios

        rel = lambda a, b: g.i16(drv.NATIONS + a * drv.NATION_LEN + 0x26 + 2 * b)
        row = lambda a: [rel(a, k) for k in range(16)]

        def propose(tag, nation, ok):
            wid, cs, radios = relations_dialog()
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
            log("propose", tag=tag, nation=nation, press="OK" if ok else "Cancel", clicks=res, dismissed=dismissed, before=before, after=after,
                dialog_closed=not g.find_windows("^International Relations$"), rome_row=row(0), target_row=row(nation))

        if variant == "natural_target3":
            g.load(START, seed=12345); log("loaded", save=START.name, seed_line=g.seed_line, rome_relations=row(0))
            for nm, nat in (("carthage", 1), ("greece", 7)):         # each already trades with three nations in this save (see the finding)
                log("target_trade_partners", target=nm, partners=[k for k in range(16) if rel(nat, k) == 1])
                propose(f"refuse_{nm}", nat, False)
            log("target_trade_partners", target="numidia", partners=[k for k in range(16) if rel(5, k) == 1])
            propose("control_numidia", 5, True); save(g, "after_control.SAV")
        elif variant == "own3":
            for tag, ops in (("own3", [("relation", 0, 1, 1), ("relation", 0, 8, 1)]), ("own2_control", [("relation", 0, 1, 1)])):
                src = staged(START, ops, tag)
                if tag == "own3": g.load(src, seed=12345)
                else: g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(1)
                log("loaded", tag=tag, rome_relations=row(0), partners=[k for k in range(16) if rel(0, k) == 1], numidia_partners=[k for k in range(16) if rel(5, k) == 1])
                propose(tag + "_numidia", 5, tag != "own3")
        else: raise SystemExit("variant")
    elif CASE in ("G5", "G6"):
        which = sys.argv[2]
        g.exe = {"patched": drv.EXE, "original": "Imperial Conquest 2.exe"}[which]
        ids = lambda: set(sh("xdotool", "search", "--onlyvisible", "--name", "", check=False).split())
        snap = lambda: {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in G.iterdir() if p.is_file()}
        changed = lambda a, b: sorted(n for n in b if a.get(n) != b[n])
        if CASE == "G5":
            X = G / f"g1_G5_{STAMP}_X_{which}.SAV"; shutil.copy2(START, X); _hash = hashlib.sha256(X.read_bytes()).hexdigest()
            log("X", file=X.name, sha256=_hash, copy_kept=keep(X, "X_original_before_anything.SAV"), exe=g.exe)
            if which == "patched": g.set_seed(12345)
            g.start(); g.open(X); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            log("opened_X", title=[w[1] for w in g.find_windows("^Imperial Conquest 2 ")], root=shot(g, "after_open_X"))
            s0 = snap(); before_ids = ids()
            g.menu("file", drv.FILE_ITEMS["save"]); time.sleep(4)
            new_ids = ids() - before_ids
            s1 = snap()
            log("save_after_open", new_windows=sorted(new_ids), boxes=boxes(g), windows=windows(g), files_changed=changed(s0, s1), root=shot(g, "after_save_menu"))
            if X.name in changed(s0, s1):
                log("X_after_save", sha256_after=sha(X), same_as_before=(sha(X) == _hash), size_before=s0[X.name][0], size_after=s1[X.name][0], copy_kept=keep(X, "X_after_save.SAV"))
            for w in sorted(new_ids): sh("xdotool", "key", "--window", w, "Escape", check=False)
            time.sleep(1)
            # Save as: the default name
            before_ids = ids(); g.menu("file", drv.FILE_ITEMS["save_as"]); time.sleep(2); nid = ids() - before_ids
            log("save_as_dialog", new_windows=sorted(nid), root=shot(g, "save_as_default_name"))
            g.key("Escape"); time.sleep(1)
            log("after_escape", new_windows=sorted(ids() - before_ids), windows=windows(g))
            # File > New, then File > Save
            s2 = snap()
            g.menu("file", drv.FILE_ITEMS["new"]); time.sleep(2)
            log("new_confirm", boxes=boxes(g), windows=windows(g))
            g._answer_confirm([p for p in g.popups() if p[1] == "Confirm"][0][0], yes=True)
            g.wait(lambda: g.find_windows("^Imperial Conquest 2$"), 10, "new game form"); time.sleep(1)
            log("new_game_form", root=shot(g, "new_game_form"))
            n_auto = len((G / "AUTOSAVE.LOG").read_text().splitlines()) if (G / "AUTOSAVE.LOG").exists() else 0
            g.click(*[117, 117], pause=0.5); g.click(344, 194)
            if which == "patched": g.wait(lambda: (G / "AUTOSAVE.LOG").exists() and len((G / "AUTOSAVE.LOG").read_text().splitlines()) > n_auto, 120, "new-game autosave")
            else: time.sleep(10)
            time.sleep(3); texts = g.dismiss_popups()
            s3 = snap()
            log("new_game_started", texts=texts, files_changed=changed(s2, s3), title=[w[1] for w in g.find_windows("^Imperial Conquest 2 ")], root=shot(g, "after_new_game"),
                autosave_log_tail=(G / "AUTOSAVE.LOG").read_text().splitlines()[-2:] if (G / "AUTOSAVE.LOG").exists() else None)
            before_ids = ids(); g.menu("file", drv.FILE_ITEMS["save"]); time.sleep(4)
            new_ids = ids() - before_ids; s4 = snap()
            log("save_after_new", new_windows=sorted(new_ids), boxes=boxes(g), windows=windows(g), files_changed=changed(s3, s4), root=shot(g, "after_save_after_new"))
            for n in changed(s3, s4):
                if n.upper().endswith(".SAV"): log("changed_file", name=n, size=s4[n][0], copy_kept=keep(G / n, "after_new_save_" + n))
            for w in sorted(new_ids): sh("xdotool", "key", "--window", w, "Escape", check=False)
        else:       # G6
            variant = sys.argv[3]       # game | nogame_menu | nogame_sysclose
            alive = lambda: subprocess.run(["pgrep", "-f", "^Imperial Conquest"], capture_output=True).returncode == 0
            def sysclose():
                r = sh(WINE, str(WORK / "win_close.exe"), "Imperial Conquest 2", check=False); log("sysclose", out=r.strip()); time.sleep(3)
            def box_step(tag, answer):
                bx = boxes(g); log("box", tag=tag, boxes=bx, windows=windows(g), alive=alive())
                conf = [p for p in g.popups() if p[1] == "Confirm"]
                if conf:
                    cs = g.controls("Confirm"); log("box_controls", tag=tag, controls=[(c["cls"], c["text"]) for c in cs])
                    if answer:
                        for _ in range(3):
                            g.click_control(next(c for c in cs if c["text"].replace("&", "") == answer), pause=1.5)
                            if not [p for p in g.popups() if p[1] == "Confirm"] or not alive(): break
                            time.sleep(1)
                        time.sleep(1.5)
                        log("after_answer", tag=tag, answer=answer, boxes=boxes(g), windows=windows(g) if alive() else None, alive=alive(), root=shot(g, tag + "_after_" + answer) if alive() else None)
            if variant == "game":
                if which == "patched": g.load(START, seed=12345)
                else: g.start(); g.open(START)
                log("loaded", alive=alive(), tax=g.i16(drv.NATIONS + 0x44a))
                sysclose(); box_step("A1_sysclose_unmodified", "No")
                texts = g.taxation(25); log("modified", note="tax set to 25 through the Taxation dialog", texts=texts, tax=g.i16(drv.NATIONS + 0x44a))
                g.menu("file", drv.FILE_ITEMS["close"]); time.sleep(2); box_step("A2_file_close_modified", "Cancel")
                g.menu("file", drv.FILE_ITEMS["close"]); time.sleep(2); box_step("A3_file_close_modified_no", "No")
                sysclose(); box_step("A4_sysclose_yes", "Yes")
                for _ in range(20):
                    if not alive(): break
                    time.sleep(0.5)
                log("final", alive=alive())
            else:
                g.start(); log("started_no_game", alive=alive(), windows=windows(g), root=shot(g, "no_game_started"))
                if variant == "nogame_menu": g.menu("file", drv.FILE_ITEMS["close"]); time.sleep(4)
                else: sysclose(); time.sleep(1)
                log("after_close_no_game", alive=alive(), boxes=boxes(g) if alive() else None, windows=windows(g) if alive() else None, root=shot(g, "no_game_after_close") if alive() else None)
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
