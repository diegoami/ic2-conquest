"""Wine: open the CA window, click Save once before any N, then list windows and every file under drive_c and the Wine user dirs changed
since the click. Log: save_before_n-<stamp>.jsonl (tracked). python3 probe_save_before_n.py"""
import json, sys, time, hashlib
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R))
from harness.driver import Game, G
STAMP = time.strftime("%Y%m%d-%H%M%S")
LOG = R / f"runs/experiments/data/run-exp-cellauto-rule/save_before_n-{STAMP}.jsonl"
ART = R / "artifacts/run-exp-cellauto-rule"
def log(**kw):
    kw["t"] = time.strftime("%H:%M:%S"); print(kw)
    with LOG.open("a") as f: f.write(json.dumps(kw) + "\n")
g = Game(); g.load(R / "saves/run0-start-AUTO0720-seed12345.SAV", seed=12345)
g.reset_ui(); g.click(304, 36, pause=1.0); g.click(382, 109, pause=1.5)
cs = g.controls("About Imperial Conquest 2"); g.click_control(g.control(cs, text="CAncell"), pause=1.5)
g.click(650, 341, pause=0.8)          # the panel, away from the buttons: activates the window
t0 = time.time() - 1
g.click(537, 341, pause=3.0)
ws = [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")]
log(step="after_save_click", windows=ws)
p = ART / f"save_before_n_{STAMP}.png"; g.shot(p); log(step="shot", file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
changed = [str(q) for q in G.parent.parent.rglob("*") if q.is_file() and q.stat().st_mtime > t0]
log(step="changed_files", files=changed)
for w in g.popups():
    if w[1] not in ("Cellular Automata", "About Imperial Conquest 2"):
        log(step="popup", window=list(w[1:]), text=g.read_popup(w) if hasattr(g, "read_popup") else None)
g.kill(); log(step="done")
