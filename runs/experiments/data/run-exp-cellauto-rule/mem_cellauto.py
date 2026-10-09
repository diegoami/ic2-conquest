"""Wine, read-only memory: the CellAuto form (global 0x4A0B9C, set by Application.CreateForm in TAboutIC_Cancell 0x456ca0): its colour
fields +0x1C0..+0x1CC, rule table +0x688 (10 words), Image1 (+0x1BC) -> Picture (+0xAC) -> Graphic (+4), at three moments: window open,
after a Save click before N, after N. Log: mem_cellauto-<stamp>.jsonl (tracked). python3 mem_cellauto.py"""
import json, struct, sys, time
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest"); sys.path.insert(0, str(R))
from harness.driver import Game
STAMP = time.strftime("%Y%m%d-%H%M%S")
LOG = R / f"runs/experiments/data/run-exp-cellauto-rule/mem_cellauto-{STAMP}.jsonl"
u32 = lambda a: struct.unpack("<I", g.mem(a, 4))[0]
def state(tag):
    f = u32(0x4A0B9C); img = u32(f + 0x1BC); pic = u32(img + 0xAC); gr = u32(pic + 4)
    d = {"tag": tag, "form": hex(f), "image1": hex(img), "picture": hex(pic), "graphic": hex(gr),
         "colours": [hex(u32(f + 0x1C0 + 4 * k)) for k in range(4)], "table": list(struct.unpack("<10h", g.mem(f + 0x688, 20))),
         "graphic_class": None}
    if gr:
        vmt = u32(gr); name_ptr = u32(vmt - 44)          # Delphi 2 vmtClassName = -44
        n = g.mem(name_ptr, 1)[0]; d["graphic_class"] = g.mem(name_ptr + 1, n).decode()
    d["t"] = time.strftime("%H:%M:%S"); print(d)
    with LOG.open("a") as fh: fh.write(json.dumps(d) + "\n")
g = Game(); g.load(R / "saves/run0-start-AUTO0720-seed12345.SAV", seed=12345)
g.reset_ui(); g.click(304, 36, pause=1.0); g.click(382, 109, pause=1.5)
cs = g.controls("About Imperial Conquest 2"); g.click_control(g.control(cs, text="CAncell"), pause=1.5)
state("open"); g.click(650, 341, pause=0.8); g.click(537, 341, pause=2.0); state("after Save before N")
g.click(509, 341, pause=3.0); state("after N")
g.kill()
