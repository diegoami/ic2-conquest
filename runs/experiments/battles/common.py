"""Shared pieces of the battle experiments after B0 (paths, logging, versioned copies, the FLD-RG geometry, killing stale wine by pid).

Text outputs go to the TRACKED folder `runs/experiments/data/run-exp-battle-sweep/` (CLAUDE.md rule 6: append-only, a re-run writes new
files beside the old, committed and pushed after each batch); saves, screenshots and exes stay in `artifacts/run-exp-battle-sweep/`
(never in git; SHA-256 in SAVES.sha256, uploaded to the release `run-exp-battle-sweep`).
"""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import harness.driver as D  # noqa: E402

NAME = "run-exp-battle-sweep"
ART = ROOT / "artifacts" / NAME                       # binaries (git-ignored)
DATA = ROOT / "runs" / "experiments" / "data" / NAME  # text measurements (tracked)
START_NAME = "1_rome_270_winter_11.sav"
FLD_RG_NAME = "FLD-RG_0743_rome_army0_at_86_28.SAV"
NORMAL_EXE = "Imperial Conquest 2 fast rollingsave seed.exe"
LAB_EXE = "Imperial Conquest 2 lab s%d.exe"
ROME_ARMY, GAUL_ARMY = 0, 10
STAGE_TILE, GAUL_TILE = (86, 28), (85, 28)
LEGS = [(90, 25), (87, 27), STAGE_TILE]               # straight legs of the 6-move path (planner.path.path_adjacent)
BATTLE_Y = 112
# This save opens the unit map 1143 x 903 px, clipped by the 1280 x 1024 screen: 29 x 27 tiles in view, not the driver's 13 x 13.
D.VIEW_COLS, D.VIEW_ROWS = 29, 27
STAMP = time.strftime("%Y%m%d-%H%M%S")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ocr(path):
    return " ".join(subprocess.run(["tesseract", str(path), "-", "--psm", "6"], capture_output=True, text=True).stdout.split())


def record_sha(path, folder=None):
    """Append `<sha256>  <name>` to the tracked SAVES.sha256 (once per distinct name + hash)."""
    DATA.mkdir(parents=True, exist_ok=True)
    f = DATA / "SAVES.sha256"
    line = f"{sha(path)}  {Path(path).name}"
    if not f.exists() or line not in f.read_text().splitlines():
        with open(f, "a") as fh:
            fh.write(line + "\n")
    return line.split()[0]


def keep(src, name=None, folder=None):
    """Copy `src` into the artifacts folder under `name` (default its own); NEVER overwrite: an existing file with other content gets a
    `-<stamp>` suffix, an identical one is reused. Returns the Path of the kept copy; its SHA-256 goes to SAVES.sha256."""
    src = Path(src)
    folder = folder or ART
    folder.mkdir(parents=True, exist_ok=True)
    dst = folder / (name or src.name)
    n = 0
    while dst.exists() and sha(dst) != sha(src):
        n += 1
        dst = dst.with_name(f"{Path(name or src.name).stem}-{STAMP}{'' if n == 1 else '-%d' % n}{dst.suffix}")
    if not dst.exists():
        shutil.copy(src, dst)
    record_sha(dst)
    return dst


def unique_path(folder, name):
    """A path in `folder` for `name` that does not exist yet: `name`, else `<stem>-<stamp>`, `<stem>-<stamp>-2`, ... (a loop, so any number of
    writes in the same second all survive)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    p, n = folder / name, 0
    while p.exists():
        n += 1
        p = folder / f"{Path(name).stem}-{STAMP}{'' if n == 1 else '-%d' % n}{Path(name).suffix}"
    return p


def write_new(folder, name, data):
    """THE writer of measured outputs: creates a file that did not exist (exclusive create, retried on a name race), never overwrites; `data` is
    str or bytes. Returns the Path written. (Append-only logs/jsonl are the only other writers: they open "a".)"""
    for _ in range(1000):
        p = unique_path(folder, name)
        try:
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            continue
        with os.fdopen(fd, "wb") as f:
            f.write(data.encode() if isinstance(data, str) else data)
        return p
    raise RuntimeError("no free name for " + name)


def battle_end_turn(g, wid=None):
    """ONE battle End turn click with proof it advanced (`Game.end_turn_proven`: flag, title, BATTLEnn count or half-round counter moves within
    8 s). After a File > Save As the battle window is inactive and a click may only activate it, so the window is raised and focused FIRST (not a
    retry). No retry of any kind: with no sign of progress DriverError propagates, because the click may still be queued (a second click could then
    end two half-rounds)."""
    if wid is None:
        w = g.find_windows(" v ")
        wid = w[0][0] if w else None
    if wid is not None:
        D.sh("xdotool", "windowraise", str(wid), check=False)
        D.sh("xdotool", "windowfocus", str(wid), check=False)
        time.sleep(0.3)
    g.end_turn_proven(lambda: g.click(g.battle_x.get("end_turn", D.BATTLE_TOOLS["end_turn"]), D.BATTLE_TOOLBAR_Y, pause=1.0))


def shot(g, name, window="root", folder=None):
    """Screenshot through `keep`: taken to a temp name, then kept under `name` (versioned if the name exists with other content, never overwritten)
    and its SHA-256 recorded in SAVES.sha256. Returns the kept Path."""
    folder = folder or ART
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / f"_tmp_shot_{os.getpid()}.png"
    g.shot(tmp, window=window)
    try:
        return keep(tmp, name, folder)
    finally:
        tmp.unlink(missing_ok=True)


class Log:
    """Timestamped events to a text log and a jsonl file in the tracked folder (new files per run, never overwritten)."""

    def __init__(self, tag, folder=None):
        self.folder = folder or DATA
        self.folder.mkdir(parents=True, exist_ok=True)
        self.tag, self.t0 = tag, time.time()
        self.txt = write_new(self.folder, f"{tag}-{STAMP}.log", b"")        # exclusive create: a second run in the same second gets a new name, never appends to an old file
        self.jl = write_new(self.folder, f"{tag}-{STAMP}.jsonl", b"")
        from harness import environment       # every game start of this run is recorded as an `environment` event (harness/environment.py)
        environment.add_sink(lambda rec: self("environment", **{k: v for k, v in rec.items() if k != "step"}), key="battles.Log")

    def __call__(self, event, **kw):
        t = round(time.time() - self.t0, 2)
        with open(self.jl, "a") as f:
            f.write(json.dumps({"t": t, "event": event, **kw}, default=str) + "\n")
        line = f"[{t:7.2f}] {event} " + " ".join(f"{k}={v!r}" for k, v in kw.items())
        with open(self.txt, "a") as f:
            f.write(line + "\n")
        print(line, flush=True)


def kill_stale(g=None):
    """Kill the game's wine processes BY PID (never a pattern that could match a waiter of our own script): the pids of every process whose
    command line starts with 'Imperial Conquest' (the game and its lab/normal builds), then wineserver -k for the prefix."""
    pids = []
    try:
        out = subprocess.run(["pgrep", "-f", "^Imperial Conquest"], capture_output=True, text=True).stdout.split()
        pids = [int(p) for p in out if int(p) != os.getpid()]
    except Exception:       # noqa: BLE001
        pass
    for p in pids:
        try:
            os.kill(p, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if g is not None:
        try:
            g.kill()
        except Exception:   # noqa: BLE001
            pass
    return pids


def count_battle_saves():
    return len(list(D.G.glob("BATTLE*.SAV")))
