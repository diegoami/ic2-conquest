"""Pick one relation radio in the open International Relations dialog, press OK, shoot any box: rel.py <row> <col> <name> <what>."""
import sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import m  # noqa: E402

row, col, name, what = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
g = m.attach()
if not g.find_windows("^International Relations$"):
    g.tool("relations", pause=2)
w = g.find_windows("^International Relations$")[0]
g.raise_window(w[0])
cs = g.controls("International Relations")
radios = sorted((c for c in cs if c["cls"] == "TRadioButton"), key=lambda c: (c["y"], c["x"]))
for _ in range(2):
    g.click_control(radios[row * 4 + col], pause=0.5)
if len(sys.argv) > 5:
    m.snap(g, sys.argv[5], "7 Diplomacy", "International Relations with the new choice ticked, before OK", window=w)
g.click_control(g.control(cs, text="OK"), pause=1.5)
ps = g.message_boxes()
if not ps and g.find_windows("^International Relations$"):
    g.click_control(g.control(cs, text="OK"), pause=1.5)
    ps = g.message_boxes()
print("boxes", ps)
if ps:
    print(g.read_popup(ps[0]))
    m.snap(g, name, "7 Diplomacy", what, window=ps[0])
    g.dismiss_popups()
    time.sleep(1)
if g.find_windows("^International Relations$"):
    g.click_control(g.control(cs, text="Cancel"), pause=1.5)
print("open", bool(g.find_windows("^International Relations$")))
