"""Wine: open Help > About > CAncell, then Save (no N yet), then for each seed of CA_SEEDS (comma list, default 12345): write SEED.TXT, N, Save. After each Save, find the new ca*.BMP anywhere under
drive_c, copy it to artifacts/run-exp-cellauto-rule/ under a new numbered name (never overwrite), and log name, path, size, SHA-256.
Screenshots after each step. Log: runs/experiments/data/run-exp-cellauto-rule/save_bmps-<stamp>.jsonl (tracked, rule 6).
python3 save_bmps.py"""
import hashlib, json, os, shutil, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R))
from harness.driver import Game, G
ART = R / "artifacts/run-exp-cellauto-rule"; ART.mkdir(parents=True, exist_ok=True)
STAMP = time.strftime("%Y%m%d-%H%M%S")
LOG = R / f"runs/experiments/data/run-exp-cellauto-rule/save_bmps-{STAMP}.jsonl"
DRIVE = G.parent
N_XY, SAVE_XY, X_XY = (509, 341), (537, 341), (776, 341)
def log(**kw):
    kw["t"] = time.strftime("%H:%M:%S"); print(kw)
    with LOG.open("a") as f: f.write(json.dumps(kw) + "\n")
def bmps():
    return {str(p): p.stat().st_mtime for p in DRIVE.rglob("*") if p.is_file() and p.name.lower().startswith("ca") and p.suffix.lower() == ".bmp"}
def shot(tag):
    p = ART / f"cellauto_{STAMP}_{tag}.png"; g.shot(p)
    log(step="shot", file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(tag):
    before = bmps()
    for attempt in (1, 2):            # the first click into an inactive window may only activate it (CLAUDE.md, driver pitfalls)
        g.click(*SAVE_XY, pause=2.0)
        after = bmps()
        new = [p for p, m in after.items() if before.get(p) != m]
        log(step="save_click", tag=tag, attempt=attempt, new=len(new))
        if new: break
    for p in new:
        dst = ART / f"{STAMP}_{tag}_{Path(p).name}"
        assert not dst.exists(); shutil.copy2(p, dst)
        log(step="save", tag=tag, name=Path(p).name, path=str(Path(p).relative_to(DRIVE.parent)), size=dst.stat().st_size,
            sha256=hashlib.sha256(dst.read_bytes()).hexdigest(), copy=dst.name)
    if not new:
        log(step="save", tag=tag, error="no new ca*.BMP under drive_c")
g = Game()
log(step="start", preexisting=sorted(bmps()))
g.load(R / "saves/run0-start-AUTO0720-seed12345.SAV", seed=12345)
g.reset_ui(); g.click(304, 36, pause=1.0); g.click(382, 109, pause=1.5)
ws = [w[1] for w in g.find_windows(".")]; log(step="about", windows=ws)
assert "About Imperial Conquest 2" in ws
cs = g.controls("About Imperial Conquest 2"); g.click_control(g.control(cs, text="CAncell"), pause=1.5)
ws = [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")]; log(step="cellauto", windows=ws)
assert any(w[0] == "Cellular Automata" for w in ws)
shot("0_open"); save("0_noN")
SEEDS = [int(s) for s in os.environ.get("CA_SEEDS", "12345").split(",")]
for k, seed in enumerate(SEEDS, 1):
    g.set_seed(seed)                  # the seed build's Randomize reads SEED.TXT at every call, the CA's N included
    g.click(*N_XY, pause=3.0); shot(f"{k}_N"); save(f"{k}_N_seed{seed}")
    log(step="seedlog_tail", lines=(G / "SEED.LOG").read_text().splitlines()[-2:])
g.click(*X_XY, pause=1.0)
g.kill(); log(step="done")
