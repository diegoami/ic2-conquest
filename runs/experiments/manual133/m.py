"""Manual screenshots (issue #133): helpers to attach to the running game and record shots.

Each python call is a new process, so `attach()` rebuilds a Game around the running wine process.
`snap(g, name, chapter, what, ...)` shoots the root window (optionally cropped to a window or a box), refuses to
overwrite an existing PNG (rule 6), and appends a row to shots.csv and the run log jsonl (tracked).
"""
import csv, hashlib, json, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from harness import driver  # noqa: E402
from harness.driver import Game, sh  # noqa: E402,F401

SHOTS = Path("/home/user/ic2-conquest/artifacts/run-exp-manual133/shots")
DATA = REPO / "runs/experiments/data/run-exp-manual133"
CSV = DATA / "shots.csv"
LOG = DATA / "run-log.jsonl"
STATE = DATA / "state.json"      # current save / exe, so a later process knows what is loaded
FIELDS = ["file", "chapter", "what", "source_save", "turn", "exe", "sha256"]


def log(event, **kw):
    DATA.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **kw}) + "\n")


def state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def set_state(**kw):
    s = state()
    s.update(kw)
    STATE.write_text(json.dumps(s, indent=1))


def attach(exe=None):
    g = Game(exe=exe or state().get("exe", driver.EXE), log=lambda *a: None)
    out = subprocess.run(["pgrep", "-f", "^Imperial Conquest"], capture_output=True, text=True).stdout.split()
    g.pid = int(out[0]) if out else None
    return g


def start(save, seed=12345, exe=None):
    exe = exe or driver.EXE
    g = Game(exe=exe, log=lambda *a: None)
    src = str(REPO / "saves" / save) if "/" not in save else save
    texts = g.load(src, seed=seed)
    set_state(save=Path(save).name, exe=exe)
    log("load", save=save, exe=exe, seed=seed, popups=texts, turn=g.turn_number())
    return g, texts


def snap(g, name, chapter, what, window=None, box=None, margin=6, save=None, turn=None, delay=0.8):
    """Shoot. window: a (wid,name,x,y,w,h) tuple or a title regex (crop to it plus margin); box: (x,y,w,h) crop."""
    time.sleep(delay)
    path = SHOTS / name
    if path.exists():
        raise SystemExit(f"{path} exists: pick a new name (never overwrite)")
    if isinstance(window, str):
        ws = g.find_windows(window)
        if not ws:
            raise SystemExit(f"no window {window!r}")
        window = ws[0]
    if window is not None:
        _, _, x, y, w, h = window
        box = (x, y, w, h)
    raw = SHOTS / ("_raw_" + name)
    g.shot(str(raw))
    if box is not None:
        x, y, w, h = box
        x0, y0 = max(0, x - margin), max(0, y - margin)
        subprocess.run(["convert", str(raw), "-crop", f"{w + 2 * margin}x{h + 2 * margin}+{x0}+{y0}", "+repage", str(path)],
                       check=True)
        raw.unlink()
    else:
        raw.rename(path)
    st = state()
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        t = turn if turn is not None else g.turn_number()
    except Exception:
        t = ""
    row = {"file": name, "chapter": chapter, "what": what, "source_save": save or st.get("save", ""),
           "turn": t, "exe": Path(st.get("exe", driver.EXE)).name, "sha256": sha}
    new = not CSV.exists()
    with CSV.open("a", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            wr.writeheader()
        wr.writerow(row)
    log("shot", **row, box=box)
    print("shot", path)
    return path


def wins(g, pattern="."):
    for w in g.find_windows(pattern):
        print(w)


def ctl(g, title):
    for c in g.controls(title):
        print(c)
