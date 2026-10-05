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


def proc_start(pid, proc="/proc"):
    """The process's start time in clock ticks since boot, field 22 of /proc/<pid>/stat (read after the last ')' because the command name may hold spaces), or None."""
    try:
        txt = (Path(proc) / str(pid) / "stat").read_text()
        return int(txt[txt.rindex(")") + 2:].split()[19])
    except (OSError, ValueError, IndexError):
        return None


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


class Handle:
    """An owned process: pid, start time at discovery, and the pidfd opened AT DISCOVERY (None where the kernel has none)."""

    def __init__(self, pid, start, fd):
        self.pid, self.start, self.fd = pid, start, fd

    def __repr__(self):
        return "Handle(%d, %r, fd=%r)" % (self.pid, self.start, self.fd)


def children_of(pid, proc="/proc"):
    return [int(d.name) for d in Path(proc).iterdir() if d.name.isdigit() and proc_ppid(int(d.name), proc) == pid]


class PeaceGame(D.Game):
    """Game whose process is the one THIS object launched. `start()` refuses an occupied display or prefix (no adoption), launches with Popen and takes a HANDLE
    (pid, start time from /proc/<pid>/stat field 22, and a pidfd opened at that moment, the start time being read before and after the open) of the launcher and of every
    descendant at discovery. The tree is walked only from a parent whose identity is verified before AND after its children are listed (a parent replaced in between drops
    the walk); each child is adopted only if its own identity holds across its pidfd open and its parent is still the verified parent. `stop()` signals only through the
    pidfds opened at discovery (a pidfd names the process that existed when it was opened, so a recycled pid is never hit); without pidfd support it signals by pid only
    after re-reading the start time. No kill or adoption by command-line pattern, no prefix-wide wine server kill."""

    PROC = "/proc"          # the process table to read (a test points it at a fake tree)

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.popen = None
        self.owned = []          # [Handle]
        self.skipped = []        # [(pid, why)]

    def _pidfd(self, pid):
        try:
            return os.pidfd_open(pid)
        except (AttributeError, OSError):
            return None

    def _send(self, pid, fd):
        """SIGKILL through the pidfd only; there is no bare-pid path."""
        signal.pidfd_send_signal(fd, signal.SIGKILL)

    def _close(self, fd):
        if fd is not None:
            try:
                os.close(fd)
            except (OSError, TypeError):
                pass

    def _between(self, pid):
        """Test hook: called after a parent's identity was verified and before its children are listed."""

    def _own(self, pid, parent=None):
        """A Handle for `pid` if its identity holds across the pidfd open (start time before == after) and, for a child, its parent is still `parent`; else None."""
        st = proc_start(pid, self.PROC)
        if st is None:
            return None
        fd = self._pidfd(pid)
        # a child is ours only if, AFTER its pidfd is open, it is still the same process, its parent is still `parent`'s pid, and that pid is still the verified
        # parent (same start time): a parent recycled while the child is adopted would otherwise hand us a foreign child (PR #45 narrow review, R1)
        if (proc_start(pid, self.PROC) != st or (parent is not None and (proc_ppid(pid, self.PROC) != parent.pid
                                                                          or proc_start(parent.pid, self.PROC) != parent.start))):
            self._close(fd)
            self.skipped.append((pid, "identity changed while being adopted"))
            return None
        return Handle(pid, st, fd)

    def _walk(self, parent):
        """Handles of the descendants of the VERIFIED `parent`: its identity is checked before the children are listed and again after; a change drops the walk."""
        if proc_start(parent.pid, self.PROC) != parent.start:
            self.skipped.append((parent.pid, "parent identity changed before its children were listed: not walked"))
            return []
        self._between(parent.pid)
        kids = children_of(parent.pid, self.PROC)
        if proc_start(parent.pid, self.PROC) != parent.start:
            self.skipped.append((parent.pid, "parent replaced while its children were listed: walk dropped"))
            return []
        out = []
        for k in kids:
            h = self._own(k, parent)
            if h is not None:
                out.append(h)
                out += self._walk(h)
        return out

    def start(self):
        # cleanup signals only through pidfds (never a bare pid), so a system without pidfd support could leave the game running: refuse to start there
        # (PR #45, the player's decision 2026-10-05)
        if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
            raise D.DriverError("this system has no pidfd support (os.pidfd_open / signal.pidfd_send_signal): refusing to start, because cleanup could not stop the game safely")
        busy = occupants(proc=self.PROC)
        if busy:
            raise D.DriverError("display %s or prefix %s already has game/wine processes %s: refusing to start (they are not ours and are not adopted or killed)"
                                % (DISPLAY, D.PREFIX, busy))
        self.popen = subprocess.Popen([D.WINE, self.exe], cwd=D.G, env=D.ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        root = self._own(self.popen.pid)             # our own unreaped child: its pid cannot be recycled while we hold it
        self.owned = [root] if root else []
        self.wait(lambda: self.find_windows("^Imperial Conquest 2$"), 40, "main window")
        time.sleep(3)
        if root:
            self.owned += self._walk(root)
        game = [h.pid for h in self.owned if proc_cmd(h.pid, self.PROC).startswith(b"Imperial Conquest")]
        if not game:
            raise D.DriverError("no game process below the launched pid %d (owned %s)" % (self.popen.pid, [h.pid for h in self.owned]))
        self.pid = game[0]

    def stop(self):
        """Signal ONLY the handles captured at discovery (in start()), through the pidfds opened then; nothing is walked or adopted during cleanup (PR #45 narrow
        review, R2). Returns the (pid, start) pairs signalled. Trade-off: a process the game spawns after discovery is not signalled here; the wine server then
        ends by itself after its last client, and start() refuses an occupied display or prefix, so a leftover can never be adopted by a later run."""
        handles = list(self.owned)
        done = []
        for h in sorted(handles, key=lambda x: -x.pid):
            try:
                if h.fd is None:
                    # never by a bare pid: it can be recycled between any check and the kill (PR #45 narrow review, round 2). The one safe exception is the
                    # launcher, our own unreaped child, whose pid cannot be reused while we hold it: Popen.kill() reaches exactly that process.
                    if self.popen is not None and h.pid == self.popen.pid:
                        self.popen.kill()
                        done.append((h.pid, h.start))
                    else:
                        self.skipped.append((h.pid, "no pidfd: not signalled (a bare pid may have been recycled)"))
                    continue
                self._send(h.pid, h.fd)
                done.append((h.pid, h.start))
            except (ProcessLookupError, PermissionError):
                pass
            finally:
                self._close(h.fd)
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
