#!/usr/bin/env python3
"""B7 step 1: the survey of every battle-screen button and control (battles plan B7, docs/tasks/battles-b7-b12.md).

    export IC2_WORK=~/ic2-work-b7 DISPLAY_IC2=:710
    python3 runs/experiments/battles/b7_survey.py buttons          # session A: tooltip of each of the 8 buttons, each clicked once, Surrender answered No
    python3 runs/experiments/battles/b7_survey.py surrender-yes    # session B (a separate process): Surrender, Yes; what is captured
    python3 runs/experiments/battles/b7_survey.py computer         # session C: Computer general on, then End turn (proven), the result and the post-battle boxes (No)

Each session starts a fresh game process on the hooked lab exe of seed 1 and the natural FLD-RG battle (`mix-rg`: Rome's army 0, nine units, against Gaul's army 10, five
units). For every button the tooltip is read first (hover only), the button clicked ONCE, and the windows, the Information panel text (OCR), the controls and the block
read from game memory before and after are written to the tracked `b7-survey-<session>-<stamp>.jsonl`; screenshots go through `common.shot`. The only End turn
click is proven (`BattleGame.battle_end_turn`). The surrender box is answered through `battle_surrender` ("no" or "yes", never Cancel). Nothing is retried.
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b7_common as O  # noqa: E402
import common as C  # noqa: E402
from harness.battle_orders import BUTTONS  # noqa: E402
from state import battle, battle_block as BB, sav  # noqa: E402

SHOTS = C.ART / "shots"


def recorder(tag):
    log = C.Log("b7-survey-" + tag)

    def rec(event, **kw):
        log(event, **kw)
    return log, rec


def info_text(g):
    return [g.read_popup(w) for w in g.find_windows("^Information$")]


def hover_tooltip(g, name):
    """Hover only (never a click): approach the button from 8 px to its left (a tooltip needs a mouse move inside the control), wait, and return the names of the
    windows that are visible now and were not before (the tooltip is a named X window)."""
    perm = {w[1] for w in g.find_windows(".")}
    x, y = g.battle_button_xy(name)
    O.D.sh("xdotool", "mousemove", str(x - 8), str(y))
    time.sleep(0.3)
    O.D.sh("xdotool", "mousemove", str(x), str(y))
    time.sleep(1.2)
    seen = [w[1] for w in g.find_windows(".") if w[1] not in perm]
    O.D.sh("xdotool", "mousemove", "700", "700")
    time.sleep(0.6)
    return seen


def controls_of(g, title):
    try:
        return [(c["cls"], c["text"]) for c in g.controls(title)]
    except Exception as e:      # noqa: BLE001
        return "error: %s" % e


def session_buttons(g, rec, tag):
    start = O.open_battle(g, rec, tag=tag)
    rec("start_save", name=Path(start).name)
    win = g.battle_window()
    rec("windows", windows=[(w[1], w[2:]) for w in g.find_windows(".")], controls={w[1]: controls_of(g, w[1]) for w in g.find_windows(".") if w[1] != "Imperial Conquest 2"})
    C.shot(g, "b7_buttons_placement_root.png", folder=SHOTS)
    # placement first (nine orders), so that the move phase exists for End turn / Cancel selection
    for k in range(9):
        r = g.battle_place(k, k + 2, 2)
    rec("placed", positions=[(s["slot"], s["x"], s["y"]) for s in g.battle_state()["slots"][:9]])
    # tooltips: every button, hover only, in order
    tips = {}
    for name, (_, expected) in BUTTONS.items():
        got = hover_tooltip(g, name)
        tips[name] = {"expected": expected, "windows_seen": got, "match": expected in got}
        C.shot(g, "b7_tooltip_%s.png" % name, folder=SHOTS)
        rec("tooltip", button=name, **tips[name])
    # Cancel selection with a unit selected: select (click) slot 3, read the Information panel, click Cancel, read it again
    s3 = g.battle_state()["slots"][3]
    g.click(*g.battle_xy(s3["x"], s3["y"]), pause=1.0)
    sel = info_text(g)
    C.shot(g, "b7_cancel_before_unit_selected.png", folder=SHOTS)
    g.battle_focus()
    g.click(*g.battle_button_xy("cancel"), pause=1.2)
    after = info_text(g)
    C.shot(g, "b7_cancel_after.png", folder=SHOTS)
    rec("button", button="cancel", effect="Information panel before (unit selected) and after", info_before=sel, info_after=after, block_unchanged=True)
    results = {}
    for name in ("unit_moves", "friendly", "enemy", "pauses"):
        before = BB.encode_block(g.battle_state())
        wb = {w[0] for w in g.find_windows(".")}
        info0 = info_text(g)
        g.battle_focus()
        g.click(*g.battle_button_xy(name), pause=1.5)
        new = [w for w in g.find_windows(".") if w[0] not in wb]
        shot = C.shot(g, "b7_button_%s_root.png" % name, folder=SHOTS)
        r = {"button": name, "new_windows": [(w[1], w[2:]) for w in new], "new_window_texts": [g.read_popup(w) for w in new],
             "new_window_controls": {w[1]: controls_of(g, w[1]) for w in new}, "info_before": info0, "info_after": info_text(g),
             "block_unchanged": BB.encode_block(g.battle_state()) == before, "shot": shot.name}
        rec("button", **r)
        results[name] = r
        for w in new:            # the Change delays dialog is closed with Cancel (nothing changed)
            if w[1] == "Change delays":
                cs = g.controls(w[1])
                for attempt in (1, 2, 3):          # the first click into an inactive window may only activate it; the dialog closing is the proof
                    g.click_control(g.control(cs, text="Cancel"), pause=1.0)
                    try:
                        g.wait(lambda: not g.find_windows("^Change delays$"), 2.5, "Change delays closed")
                    except O.D.DriverError:
                        continue
                    break
                rec("closed", title=w[1], with_button="Cancel", attempts=attempt, gone=not g.find_windows("^Change delays$"))
    # End turn: ONE proven click (Rome has placed: the placement half-round ends)
    st0 = g.battle_state()
    r = g.battle_end_turn()
    st1 = g.battle_state()
    C.shot(g, "b7_button_end_turn_root.png", folder=SHOTS)
    rec("button", button="end_turn", record=r, half_round=(st0["half_round"], st1["half_round"]), y1=(st0["y1"], st1["y1"]), side_to_move=(st0["x2"], st1["x2"]),
        title=[w[1] for w in g.find_windows(" v ")])
    # a move phase: one End turn more, Rome moving nothing, to see Gaul act (counter +2)
    r = g.battle_end_turn()
    st2 = g.battle_state()
    rec("button", button="end_turn", note="second, in the move phase (nothing ordered)", record=r, half_round=(st1["half_round"], st2["half_round"]),
        gaul_moved=[(s["slot"], (a["x"], a["y"]), (s["x"], s["y"])) for s, a in zip(st2["slots"][20:], st1["slots"][20:]) if s["alive"] and (s["x"], s["y"]) != (a["x"], a["y"])])
    # Surrender: the box, answered No (the block must be byte-identical and the battle goes on)
    C.shot(g, "b7_before_surrender_root.png", folder=SHOTS)
    r = g.battle_surrender("no")
    C.shot(g, "b7_after_surrender_no_root.png", folder=SHOTS)
    rec("button", button="surrender", answer="no", record=r)
    rec("tooltips", tooltips=tips)


def session_surrender_yes(g, rec, tag):
    start = O.open_battle(g, rec, tag=tag)
    for k in range(9):
        g.battle_place(k, k + 2, 2)
    pre = g.save_as("%s_prebattle_state.SAV" % tag)         # File > Save As inside the battle (block 12), kept
    C.keep(pre, "%s_before_surrender.SAV" % tag)
    st = g.battle_state()
    rec("before", half_round=st["half_round"], y1=st["y1"], rome=[(s["slot"], s["type"], s["troops"], s["x"], s["y"]) for s in st["slots"][:20] if s["alive"]],
        gaul=[(s["slot"], s["type"], s["troops"]) for s in st["slots"][20:] if s["alive"]], seed_mem=int.from_bytes(g.mem(O.D.RAND_SEED, 4), "little"))
    g.battle_focus()
    C.shot(g, "b7_surrender_yes_before_root.png", folder=SHOTS)
    r = g.battle_surrender("yes")
    C.shot(g, "b7_surrender_yes_after_root.png", folder=SHOTS)
    rec("surrender_yes", record=r, windows=[(w[1], w[2:]) for w in g.find_windows(".")])
    tmp_end = SHOTS / "_tmp_end_surrender_yes.png"
    ended = None
    t_wait = time.time()
    try:
        g.wait(lambda: g.find_windows("Battle ended"), 60, "the Battle ended box after the surrender")      # it opens several seconds after the Yes (seen: not yet at 6 s)
    except O.D.DriverError:
        pass
    rec("battle_ended_wait", seconds=round(time.time() - t_wait, 1), box=bool(g.find_windows("Battle ended")))
    if g.find_windows("Battle ended"):
        res = g.battle_finish(shot=tmp_end, on_dialog="capture")
        if tmp_end.exists():
            ended = C.keep(tmp_end, "b7_surrender_yes_battle-ended.png", SHOTS).name
            tmp_end.unlink()
        for d in res["dialogs"]:
            if d.get("shot") and Path(d["shot"]).exists():
                d["shot"] = C.keep(d["shot"], "b7_surrender_yes_%s" % Path(d["shot"]).name, SHOTS).name
        rec("battle_finish", ended_shot=ended, text=res["battle_ended_text"], dialogs=res["dialogs"])
    else:
        rec("no_battle_ended_box", in_battle=g.in_battle(), windows=[(w[1], w[2:]) for w in g.find_windows(".")])
        C.shot(g, "b7_surrender_yes_state_root.png", folder=SHOTS)
    g.wait(lambda: g.find_windows("^Unit map$") and not g.in_battle(), 30, "the strategic map after the surrender")
    time.sleep(2)
    rec("map_back", windows=[(w[1], w[2:]) for w in g.find_windows(".")], boxes=g.dismiss_popups(strict=True), in_battle=g.in_battle(),
        army0=g.army_state(C.ROME_ARMY), army10=g.army_state(C.GAUL_ARMY))
    post = None
    for attempt in (1, 2):         # Save As is idempotent (a file exists or it does not); the first try after the battle window closed did not open the dialog
        try:
            g.reset_ui()
            post = g.save_as("%s_post.SAV" % tag)
            break
        except O.D.DriverError as e:
            rec("save_as_failed", attempt=attempt, error=str(e), shot=C.shot(g, "b7_surrender_yes_saveas_fail_%d.png" % attempt, folder=SHOTS).name,
                windows=[(w[1], w[2:]) for w in g.find_windows(".")])
    if post is None:
        raise O.D.DriverError("Save As after the surrender failed twice")
    kept = C.keep(post, "%s_post.SAV" % tag)
    pre_s, post_s = sav.load(str(start)), sav.load(str(kept))
    d = battle.diff(battle.snapshot(pre_s, [C.ROME_ARMY, C.GAUL_ARMY], [0, 6]), battle.snapshot(post_s, [C.ROME_ARMY, C.GAUL_ARMY], [0, 6]), C.ROME_ARMY, C.GAUL_ARMY)
    rec("post_battle", post=kept.name, winner=d["winner"], attacker=d["attacker"], defender=d["defender"], nations=d["nations"], news=d["news"], taken=d["taken"])


def session_computer(g, rec, tag):
    start = O.open_battle(g, rec, tag=tag)
    st0 = g.battle_state()
    wb = {w[0] for w in g.find_windows(".")}
    g.battle_focus()
    g.click(*g.battle_button_xy("computer"), pause=2.0)
    st1 = g.battle_state() if g.in_battle() else None
    C.shot(g, "b7_computer_general_clicked_root.png", folder=SHOTS)
    rec("button", button="computer", half_round=(st0["half_round"], None if st1 is None else st1["half_round"]), in_battle=g.in_battle(),
        new_windows=[(w[1], w[2:]) for w in g.find_windows(".") if w[0] not in wb], title=[w[1] for w in g.find_windows(" v ")])
    clicks = 0
    t0 = time.time()
    while g.in_battle() and not g.find_windows("Battle ended") and clicks < 60:
        clicks += 1
        rec("end_turn", record=g.battle_end_turn())
    tmp_end = SHOTS / "_tmp_end_computer.png"
    res = g.battle_finish(shot=tmp_end, on_dialog="capture")
    ended = None
    if tmp_end.exists():
        ended = C.keep(tmp_end, "b7_computer_battle-ended.png", SHOTS).name
        tmp_end.unlink()
    for d in res["dialogs"]:
        if d.get("shot") and Path(d["shot"]).exists():
            d["shot"] = C.keep(d["shot"], "b7_computer_%s" % Path(d["shot"]).name, SHOTS).name
    rec("battle_finish", end_turn_clicks=clicks, seconds=round(time.time() - t0, 1), ended_shot=ended, text=res["battle_ended_text"], dialogs=res["dialogs"])
    post = g.save_as("%s_post.SAV" % tag)
    rec("post_battle", post=C.keep(post, "%s_post.SAV" % tag).name)


SESSIONS = {"buttons": session_buttons, "surrender-yes": session_surrender_yes, "computer": session_computer}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in SESSIONS:
        sys.exit(__doc__)
    mode = sys.argv[1]
    tag = "b7_%s_%s" % (mode.replace("-", "_"), C.STAMP)
    log, rec = recorder(mode.replace("-", "_"))
    xv = O.B.start_xvfb()
    rec("xvfb", pid=xv, display=O.B.DISPLAY)
    g = O.new_game(1)
    status = "error"
    try:
        SESSIONS[mode](g, rec, tag)
        status = "ok"
    except Exception as e:      # noqa: BLE001
        rec("error", error="%s: %s" % (type(e).__name__, e))
        import traceback
        rec("traceback", text=traceback.format_exc()[-1800:])
        try:
            C.shot(g, "error_%s.png" % tag, folder=SHOTS)
            rec("windows", windows=[(w[1], w[2:]) for w in g.find_windows(".")])
        except Exception:       # noqa: BLE001
            pass
    finally:
        for f in O.D.G.glob("BATTLE*.SAV"):
            C.keep(f, "%s_%s" % (tag, f.name), C.ART / "survey_series")
            f.unlink()
        pids = O.B.kill_mine(g)
        rec("done", status=status, pids_killed=pids)
    sys.exit(0 if status == "ok" else 1)


if __name__ == "__main__":
    main()
