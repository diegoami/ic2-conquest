"""Open menu <x> item <y>, shoot the box that appears (named <name>), answer No: menuprompt.py <menu_x> <item_y> <name> <chapter> <what>."""
import sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import m  # noqa: E402

mx, iy, name, chapter, what = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
g = m.attach()
g.reset_ui()
g.click(mx, 36, pause=0.8)
g.click(mx + 20, iy, pause=1.5)
ps = []
for _ in range(8):
    ps = g.message_boxes() or [w for w in g.popups() if w[4] > 1]
    if ps:
        break
    time.sleep(0.5)
print(ps)
if ps:
    time.sleep(0.6)
    print(g.read_popup(ps[0]))
    m.snap(g, name, chapter, what, window=ps[0], delay=0.2)
    try:
        for c in g.controls(ps[0][1]):
            print(c["cls"], c["text"])
    except Exception as e:
        print(e)
    if ps[0][1] == "Confirm":
        print("closed", g._answer_confirm(ps[0][0], yes=False))
