#!/usr/bin/env python3
"""B8 layout screenshots (battles plan §4 B8): the whole battle screen at the placement phase, at a move phase and at the end; every toolbar button's tooltip;
the unit information shown on a click; the "Battle ended" result box; the surrender box (opened, answered **No**, never Yes); any post-battle box (the Offer of
peace is captured and declined by `Game.play_battle(on_dialog="capture")`).

    python3 runs/experiments/battles/b8_layout.py

Natural FLD-RG (Rome's army 0, nine units, against Gaul's army 10, five units) on the lab seed-1 exe, Computer general OFF until the last step. Every screenshot goes
through `common.shot` (versioned, SHA-256 in SAVES.sha256, artifacts/ then the release); every observation (windows, tooltips, controls, the block read from memory
before and after each step) is appended to the tracked `b8-layout-<stamp>.jsonl`. Nothing is retried; the only End turn click is proven (`common.battle_end_turn`);
if the surrender box shows no "No" control the run stops without clicking anything else.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import trials as T  # noqa: E402
from harness.driver import DriverError, Game  # noqa: E402
from state import battle_block as BB  # noqa: E402

TAG = "b8_layout"


def main():
    log = C.Log("b8-layout")
    out = C.write_new(C.DATA, f"b8-layout-{C.STAMP}.jsonl", b"")

    def rec(event, **kw):
        with open(out, "a") as f:
            f.write(json.dumps({"event": event, **kw}, default=str) + "\n")
        log(event, **{k: v for k, v in kw.items() if k != "block"})

    shots = C.ART / "shots"
    g = Game(exe=C.LAB_EXE % 1)
    C.kill_stale(g)
    for f in C.D.G.glob("BATTLE*.SAV"):
        C.keep(f, f"stray_{TAG}_{f.name}")
        f.unlink()
    status = "error"
    try:
        g.start()
        g.open(C.ART / C.FLD_RG_NAME)
        g.select_army(C.ROME_ARMY, *C.STAGE_TILE)
        g.click_tile(*C.GAUL_TILE, pause=0.0)
        T.wait_battle(g, log)
        time.sleep(2.5)
        win = g.find_windows(" v ")[0]
        wid = win[0]
        rec("battle_open", title=win[1], geometry=win[2:], armies={"attacker": len(g.army_state(0)["units"]), "defender": len(g.army_state(10)["units"])})
        # 1. placement: whole screen and the battle window
        st0 = g.battle_state()
        a = C.shot(g, f"{TAG}_placement_root.png", folder=shots)
        b = C.shot(g, f"{TAG}_placement_window.png", window=str(wid), folder=shots)
        rec("placement", root=a.name, window=b.name, half_round=st0["half_round"], y1=st0["y1"], occupied=[(s["slot"], s["side"], s["type"], s["troops"], s["x"], s["y"]) for s in st0["slots"] if s["alive"]],
            windows=[w[1] for w in g.find_windows()])
        # 2. toolbar tooltips: hover along the strip; one root screenshot the first time each tooltip name shows
        import subprocess
        seen = {}
        g.click  # noqa: B018 (hover only below: xdotool mousemove, never a click)
        for x in range(5, 260, 3):
            subprocess.run(["xdotool", "mousemove", str(x), str(C.BATTLE_Y)])
            time.sleep(0.7)
            names = sorted({w[1] for w in g.find_windows(".")} - {w[1] for w in g.find_windows(".") if w[1].startswith("Imperial") or w[1] in ("Area map", "Unit map", "Information") or " v " in w[1]})
            for n in names:
                if n not in seen:
                    seen[n] = {"x_first": x, "x_last": x}
                    seen[n]["shot"] = C.shot(g, f"{TAG}_tooltip_{len(seen):02d}.png", folder=shots).name
                    rec("tooltip", name=n, x=x, shot=seen[n]["shot"])
                else:
                    seen[n]["x_last"] = x
        rec("tooltips", tooltips=seen)
        # 3. unit information on a click: a Gaul unit's tile (no order can be given to an enemy unit at placement), effect read from memory
        gs = next(s for s in st0["slots"] if s["alive"] and s["side"] == 1)
        tx, ty = 0 + gs["x"] * 32 + 16, 28 + gs["y"] * 32 + 16          # tile origin in the window; the window's screen position is win[2:4]
        sx, sy = win[2] + tx, win[3] + ty
        before = g.battle_state()
        w_before = {w[1] for w in g.find_windows()}
        g.click(sx, sy, pause=1.5)
        after = g.battle_state()
        c = C.shot(g, f"{TAG}_unit_info_click_gaul_slot{gs['slot']}.png", folder=shots)
        texts = [g.read_popup(p) for p in g.popups()]
        panel = [t for t in texts if "Troops" in t and "army" in t]            # the Information panel names the army and shows Troops
        rec("unit_info_click", slot=gs["slot"], screen=(sx, sy), shot=c.name, new_windows=sorted({w[1] for w in g.find_windows()} - w_before),
            block_unchanged=BB.encode_block(before) == BB.encode_block(after), popups=texts, panel_shown=bool(panel), panel_text=panel[:1])
        if not panel:      # nothing is claimed from a click that opened no panel: stop, the files stay
            raise DriverError("unit info click at %s showed no Information panel (texts %r)" % ((sx, sy), texts))
        # 4. the surrender box: open it, answer No
        sur = next((n for n in seen if "urrender" in n), None)
        if sur:
            x = (seen[sur]["x_first"] + seen[sur]["x_last"]) // 2
            before = BB.encode_block(g.battle_state())
            g.click(x, C.BATTLE_Y, pause=1.5)
            pops = g.popups()
            shot = C.shot(g, f"{TAG}_surrender_box_root.png", folder=shots)
            info = []
            answered = None
            for p in pops:
                cs = g.controls(p[1])
                info.append({"title": p[1], "text": g.read_popup(p), "controls": [c_["text"] for c_ in cs]})
                no = [c_ for c_ in cs if c_["text"].replace("&", "").strip().lower() == "no"]
                if no:
                    g.click_control(no[0], pause=1.0)
                    answered = "No"
            rec("surrender_box", tooltip=sur, x=x, shot=shot.name, boxes=info, answered=answered)
            if pops and answered != "No":
                raise DriverError("surrender box without a No control: stopping, nothing else clicked")
            rec("after_surrender_no", still_in_battle=g.in_battle(), block_unchanged=BB.encode_block(g.battle_state()) == before, windows=[w[1] for w in g.find_windows()])
        else:
            rec("surrender_button_not_found", tooltips=list(seen))
        # 5. a move phase: ONE proven End turn click with Computer general off; whole screen after it
        C.battle_end_turn(g, wid)
        time.sleep(2)
        st1 = g.battle_state()
        d = C.shot(g, f"{TAG}_move_phase_root.png", folder=shots)
        e = C.shot(g, f"{TAG}_move_phase_window.png", window=str(wid), folder=shots)
        rec("move_phase", root=d.name, window=e.name, half_round=st1["half_round"], title=[w[1] for w in g.find_windows(" v ")])
        # 6. the end: Computer general on, End turn (proven), result box, post-battle boxes captured and declined
        tmp_end = shots / f"_tmp_end_{TAG}.png"
        res = g.play_battle(shot=tmp_end, on_dialog="capture")
        endshot = None
        if tmp_end.exists():
            endshot = C.keep(tmp_end, f"{TAG}_battle-ended.png", shots).name
            tmp_end.unlink()
        for dlg in res["dialogs"]:
            if dlg.get("shot") and Path(dlg["shot"]).exists():
                dlg["shot"] = C.keep(dlg["shot"], f"{TAG}_{Path(dlg['shot']).name}", shots).name
        rec("battle_end", end_turn_clicks=res["end_turn_clicks"], result_box_shot=endshot, ocr=res["battle_ended_text"], dialogs=res["dialogs"])
        f_ = C.shot(g, f"{TAG}_after_battle_root.png", folder=shots)
        rec("after_battle", root=f_.name, windows=[w[1] for w in g.find_windows()])
        status = "ok"
    except Exception as e:      # noqa: BLE001
        rec("error", error=f"{type(e).__name__}: {e}")
        try:
            C.shot(g, f"error_{TAG}.png", folder=shots)
        except Exception:       # noqa: BLE001
            pass
    finally:
        for f in C.D.G.glob("BATTLE*.SAV"):
            C.keep(f, f"{TAG}_{f.name}", C.ART / "crafted_b8")
            f.unlink()
        C.kill_stale(g)
    rec("done", status=status)
    print(out)


if __name__ == "__main__":
    main()
