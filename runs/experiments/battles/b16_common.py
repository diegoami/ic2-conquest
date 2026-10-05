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


def proc_env(pid, proc="/proc"):
    try:
        return (Path(proc) / str(pid) / "environ").read_bytes().split(b"\0")
    except OSError:
        return []


def proc_cmd(pid, proc="/proc"):
    try:
        return (Path(proc) / str(pid) / "cmdline").read_bytes()
    except OSError:
        return b""


def proc_ppid(pid, proc="/proc"):
    """The parent pid from /proc/<pid>/status (`PPid:`), or None."""
    try:
        for line in (Path(proc) / str(pid) / "status").read_text().splitlines():
            if line.startswith("PPid:"):
                return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return None


def descendants(root, proc="/proc"):
    """`root` and every process below it in the PPid tree (children, grandchildren, ...), found through /proc/<pid>/status. A process that has been re-parented
    away (a daemon such as wineserver) is not below `root` and is never returned."""
    kids = {}
    for d in Path(proc).iterdir():
        if d.name.isdigit():
            pp = proc_ppid(int(d.name), proc)
            if pp is not None:
                kids.setdefault(pp, []).append(int(d.name))
    out, todo = [], [root]
    while todo:
        p = todo.pop()
        if p in out:
            continue
        out.append(p)
        todo += kids.get(p, [])
    return out


def occupants(display=None, prefix=None, proc="/proc"):
    """Pids that already use this run's X display or Wine prefix (any process whose environment has DISPLAY=<display> or WINEPREFIX=<prefix> and whose command
    line is the game or a wine binary). Used ONLY to refuse to start: they are never adopted and never killed."""
    display = display or DISPLAY
    prefix = prefix or str(D.PREFIX)
    out = []
    for d in Path(proc).iterdir():
        if not d.name.isdigit():
            continue
        env, cmd = proc_env(d.name, proc), proc_cmd(d.name, proc)
        if not cmd:
            continue
        mine = ("DISPLAY=%s" % display).encode() in env or ("WINEPREFIX=%s" % prefix).encode() in env
        if mine and (cmd.startswith(b"Imperial Conquest") or b"wine" in cmd.split(b"\0")[0].lower()):
            out.append(int(d.name))
    return out


class PeaceGame(D.Game):
    """Game whose process is the one THIS object launched: `start()` refuses an occupied display or prefix (no adoption), launches with Popen, remembers that pid,
    finds the game process among its descendants (PPid tree), and `stop()` kills exactly those pids. No kill or adoption by command-line pattern, and no prefix-wide wine server kill."""

    PROC = "/proc"          # the process table to read (a test points it at a fake tree)

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.popen = None
        self.owned = []

    def start(self):
        busy = occupants(proc=self.PROC)
        if busy:
            raise D.DriverError("display %s or prefix %s already has game/wine processes %s: refusing to start (they are not ours and are not adopted or killed)"
                                % (DISPLAY, D.PREFIX, busy))
        self.popen = subprocess.Popen([D.WINE, self.exe], cwd=D.G, env=D.ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        self.wait(lambda: self.find_windows("^Imperial Conquest 2$"), 40, "main window")
        time.sleep(3)
        self.owned = descendants(self.popen.pid, self.PROC)
        game = [p for p in self.owned if proc_cmd(p, self.PROC).startswith(b"Imperial Conquest")]
        if not game:
            raise D.DriverError("no game process below the launched pid %d (tree %s)" % (self.popen.pid, self.owned))
        self.pid = game[0]

    def stop(self):
        """Kill the processes this object launched (the Popen pid and its descendants as of now and as of the start), nothing else; returns the pids signalled.
        The wine server daemon re-parents itself and ends by itself a few seconds after its last client."""
        pids = set(self.owned)
        if self.popen is not None:
            pids |= set(descendants(self.popen.pid, self.PROC))
        done = []
        for p in sorted(pids, reverse=True):
            try:
                os.kill(p, signal.SIGKILL)
                done.append(p)
            except (ProcessLookupError, PermissionError):
                pass
        if self.popen is not None:
            try:
                self.popen.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        self.popen, self.owned, self.pid = None, [], None
        time.sleep(4)          # let the wine server notice that its clients are gone before the next start checks the prefix
        return done

    def kill(self):
        return self.stop()

    def hook_read(self):
        from state import hook_log
        return hook_log.read_process(self.mem)
