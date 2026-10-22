"""Wine with WINEDEBUG=+seh,+file: open the CA window, mark the trace, click Save before any N, mark, then N, mark, Save, mark.
The full trace goes to artifacts/run-exp-cellauto-rule/trace-<stamp>.log (big); the lines between the marks, with seh events and
CreateFile / NtCreateFile calls, go to runs/experiments/data/run-exp-cellauto-rule/trace_excerpt-<stamp>.txt (tracked).
python3 trace_save_before_n.py"""
import re, subprocess, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R))
import harness.driver as drv
from harness.driver import Game, G
STAMP = time.strftime("%Y%m%d-%H%M%S")
TRACE = R / f"artifacts/run-exp-cellauto-rule/trace-{STAMP}.log"
OUT = R / f"runs/experiments/data/run-exp-cellauto-rule/trace_excerpt-{STAMP}.txt"
drv.ENV["WINEDEBUG"] = "+seh,+file"
_f = TRACE.open("w")
def start(self):
    self.ensure_xvfb(); self.kill()
    subprocess.Popen(["setsid", drv.WINE, self.exe], cwd=G, env=drv.ENV, stdout=_f, stderr=_f)
    self.wait(lambda: self.find_windows("^Imperial Conquest 2$"), 60, "main window")
    time.sleep(3)
    self.pid = int(subprocess.check_output(["pgrep", "-f", "^Imperial Conquest"]).split()[0])
Game.start = start
def mark(s):
    _f.flush(); time.sleep(1.0); return TRACE.stat().st_size
g = Game(); g.load(R / "saves/run0-start-AUTO0720-seed12345.SAV", seed=12345)
g.reset_ui(); g.click(304, 36, pause=1.0); g.click(382, 109, pause=1.5)
cs = g.controls("About Imperial Conquest 2"); g.click_control(g.control(cs, text="CAncell"), pause=1.5)
g.click(650, 341, pause=0.8)
m0 = mark("before"); g.click(537, 341, pause=3.0); m1 = mark("after save-before-N")
g.click(509, 341, pause=3.0); m2 = mark("after N"); g.click(537, 341, pause=3.0); m3 = mark("after save")
g.kill(); _f.close()
data = TRACE.read_bytes().decode("latin-1")
keep = lambda s: [l for l in s.splitlines() if re.search(r"seh|CreateFile|ca\d{10}|\.BMP|exception", l, re.I)]
with OUT.open("w") as o:
    for name, a, b in (("save before N", m0, m1), ("N", m1, m2), ("save after N", m2, m3)):
        seg = data[a:b]
        o.write(f"=== {name}: {len(seg.splitlines())} trace lines; kept:\n" + "\n".join(keep(seg)[:80]) + "\n")
print(OUT.read_text()[:4000])
