"""Click the battle End turn (proven) until the battle ends; then shoot Battle ended and any post-battle box (peace offer -> No)."""
import sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import m  # noqa: E402

g = m.attach(exe="Imperial Conquest 2.exe")
t0 = time.time()
while time.time() - t0 < 900:
    if not g.in_battle() or g.find_windows("Battle ended"):
        break
    w = g.find_windows(" v ")
    if w:
        g.raise_window(w[0][0])
    try:
        g.end_turn_proven(lambda: g.click(106, 112, pause=1.0), timeout=15)
    except Exception as e:
        print(e)
        time.sleep(5)
    time.sleep(2)
print("ended", g.in_battle())
w = g.wait(lambda: g.find_windows("Battle ended"), 60, "Battle ended")
m.snap(g, "M06_21_orig_battle_ended.png", "6 Combat", "Original exe: the Battle ended window (who defeats whom, troops at start and finish by type, money and supplies captured)", window=w[0], delay=1)
print(g.read_popup(w[0]))
cs = g.controls("Battle ended")
g.click_control(g.control(cs, text="OK"), pause=2)
for _ in range(20):
    ps = g._post_battle_windows()
    if ps:
        p = ps[0]
        print("post", p, g.read_popup(p))
        m.snap(g, "M06_22_orig_after_battle_box.png", "6 Combat", "Box after the battle: " + p[1], window=p, delay=0.8)
        if p[1] == "Offer of peace":
            g.answer_battle_peace(False)
        else:
            g.dismiss_popups()
        break
    time.sleep(1)
time.sleep(2)
m.sh("xdotool", "mousemove", "1000", "900")
m.snap(g, "M06_23_orig_map_after_battle.png", "6 Combat", "Back on the map after the field battle: the news log reports the outcome", box=(0, 26, 772, 975), margin=0, delay=1)
