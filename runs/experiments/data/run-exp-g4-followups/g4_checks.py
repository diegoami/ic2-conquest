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
