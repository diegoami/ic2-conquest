"""End turn once, shooting every box that appears (prefix given), until the autosave line appears: endturn.py <prefix>."""
import sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import m  # noqa: E402

prefix = sys.argv[1]
g = m.attach()
log = m.driver.G / "AUTOSAVE.LOG"
n = len(log.read_text().splitlines())
g.tool("end_turn", pause=0.5)
k, t0, seen = 0, time.time(), set()
while time.time() - t0 < 120:
    if len(log.read_text().splitlines()) > n:
        time.sleep(2)
        if not g.popups():
            break
    if g.in_battle() and g.find_windows(" v "):
        print("battle", g.find_windows(" v ")[0][1])
        r = g.play_battle(on_dialog="capture")
        print("battle result", r.get("battle_ended_text"), [d.get("title") for d in r.get("dialogs", [])])
        continue
    for w in g.popups():
        if " v " in w[1] or w[1] == "Battle ended":
            continue
        if w[0] in seen or w[4] <= 1:
            continue
        time.sleep(0.8)
        k += 1
        txt = g.read_popup(w)
        print("box", w, txt)
        m.snap(g, "%s_box%02d.png" % (prefix, k), "8 Turn", "Box during End turn (%s): %s" % (w[1], txt[:80]), window=w, delay=0.2)
        seen.add(w[0])
        if w[1] in ("Information", "Confirm", "Warning", "Error", ""):
            g.dismiss_popups(max_n=1)
        elif w[1] == "Offer of peace":
            g.answer_battle_peace(False)
        elif w[1] == "End turn ?":
            cs = g.controls("End turn ?")
            g.click_control(g.control(cs, text="End turn"), pause=1.5)
    time.sleep(0.5)
print("turn", g.turn_number(), log.read_text().splitlines()[-1])
m.log("end_turn", turn=g.turn_number(), boxes=k)
