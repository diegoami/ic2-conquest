"""Shared pieces of the B16 runs (battles plan B16, docs/tasks/battles-b16-peace.md; adapted from the B11 branch's b11_common.py, which is not in main yet).

Everything is isolated from other sessions: the run uses ITS OWN game folder (`IC2_WORK`, a copy of the prefix) and ITS OWN X display
(`DISPLAY_IC2`), both required in the environment (no default, so a forgotten variable cannot land on :99 or on the shared prefix), and it
kills only the processes it started, by pid. Text outputs go straight to the TRACKED folder runs/experiments/data/run-exp-battle-peace/
(CLAUDE.md rule 6; never overwritten: `common.write_new`, append-only jsonl); binaries stay in artifacts/run-exp-battle-peace/ (git-ignored),
SHA-256 in SAVES.sha256, uploaded to the release as per-batch tar.gz archives with a tracked manifest.
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

for _v in ("IC2_WORK", "DISPLAY_IC2"):
    if not os.environ.get(_v):
        sys.exit("b16: set %s (a private game folder and a private X display; never the shared ones)" % _v)
if os.environ["DISPLAY_IC2"] in (":99", ":453", ":0") or os.environ["DISPLAY_IC2"] in [":%d" % n for n in range(576, 582)]:
    sys.exit("b16: DISPLAY_IC2 must be your own display (not :99, :453, :0 or :576-:581)")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import harness.driver as D  # noqa: E402

NAME = "run-exp-battle-peace"
C.NAME = NAME
C.ART = C.ROOT / "artifacts" / NAME
C.DATA = C.ROOT / "runs" / "experiments" / "data" / NAME
ART, DATA = C.ART, C.DATA
HOOK_EXE = "Imperial Conquest 2 lab hook s%d.exe"
PLAIN_EXE = "Imperial Conquest 2 lab s%d.exe"
DISPLAY = os.environ["DISPLAY_IC2"]


def start_xvfb():
    """Start this run's Xvfb on DISPLAY_IC2 unless it already runs there; returns its pid (None if it was already up). Only this pid is ever killed."""
    lock = Path("/tmp/.X%s-lock" % DISPLAY.lstrip(":"))
    if lock.exists():
        try:
            pid = int(lock.read_text().strip())
            os.kill(pid, 0)
            return None
        except (ValueError, ProcessLookupError, PermissionError):
            lock.unlink(missing_ok=True)
    p = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1280x1024x24", "-nolisten", "tcp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    time.sleep(2)
    return p.pid


def my_game_pids():
    """pids whose command line starts with 'Imperial Conquest' AND whose environment has this run's DISPLAY (never another session's game)."""
    out = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            cmd = (d / "cmdline").read_bytes()
            if not cmd.startswith(b"Imperial Conquest"):
                continue
            env = (d / "environ").read_bytes().split(b"\0")
            if ("DISPLAY=%s" % DISPLAY).encode() in env and ("WINEPREFIX=%s" % D.PREFIX).encode() in env:
                out.append(int(d.name))
        except (OSError, PermissionError):
            continue
    return out


def kill_mine(g=None):
    """Kill this run's game processes by pid, then this prefix's wineserver (WINEPREFIX is private). Returns the pids killed."""
    pids = my_game_pids()
    for p in pids:
        try:
            os.kill(p, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if g is not None:
        try:
            g.kill()
        except Exception:       # noqa: BLE001
            pass
    return pids


C.kill_stale = kill_mine          # the shared helpers (`trials.run_all`, `common`) call this name: never a pattern kill here


class PeaceGame(D.Game):
    """Game whose pid is chosen by display and prefix (never another session's game)."""

    def start(self):
        super().start()
        mine = my_game_pids()
        if not mine:
            raise D.DriverError("no game process on display %s" % DISPLAY)
        self.pid = mine[0]
