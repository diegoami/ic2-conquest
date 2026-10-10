"""The environment that produced a run's screenshots, OCR and saves (owner, 2026-10-10).

Text rendering depends on the host: the game's Information panel asks for "Book Antiqua", which no computer has, so Wine draws
whatever font it matches (DejaVu Sans with the old font set, Liberation Sans once fonts-liberation was installed); screenshots,
OCR and some window geometry differ with the Wine version too. `fingerprint(prefix)` records the Wine version, the exe and its
SHA-256, the Xvfb screen, the fonts that matter and a short hash of the prefix's font registry, so evidence says what made it.
Why: runs/experiments/data/run-exp-machine-move/RESULTS.md sections 4-5. Stdlib only. Every probe is best-effort: a failure is
recorded as {"error": ...} and never raises. Only font names are read from the registry (user.reg also holds other settings).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

WINE = "/usr/lib/wine/wine"
FONT_SECTIONS = ("Software\\\\Wine\\\\Fonts\\\\External Fonts", "Software\\\\Wine\\\\Fonts\\\\Replacements")
PROBE_TIMEOUT = 0.8  # s per command (a slow fc-list or xdpyinfo must not slow a start)
BUDGET = 0.9         # s for the whole fingerprint, enforced: probes run in parallel threads and a probe unfinished at the deadline is an error
_cache = {}          # per process: (prefix, exe path, display) -> fingerprint
_keyed = {}          # sinks registered with a key (one per key)
_sinks = []          # runner callbacks: fn(record dict), called by record_start on every start
_logged = set()      # (prefix, exe, display, pid) whose line self.log already got: once per game process
_deadline = [None]
_exe_hashes = {}     # (path, mtime_ns, size) -> sha256 hex


def _run(*args, env=None, timeout=PROBE_TIMEOUT):
    if _deadline[0] is not None:
        left = _deadline[0] - time.monotonic()
        if left <= 0:
            raise TimeoutError("fingerprint time budget spent")
        timeout = min(timeout, left)
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env, check=True)
    return r.stdout.strip()


def sanitize(msg):
    """An error text without absolute paths or the home directory (user.reg's location, the exe's): they say nothing about the
    environment and must not reach logs."""
    msg = msg.replace(str(Path.home()), "~")
    return re.sub(r"(?<![\w.])/[^\s'\"]*", "<path>", msg)


def _probe(fn):
    try:
        return fn()
    except Exception as e:          # best-effort: the error is the record
        return {"error": sanitize(f"{type(e).__name__}: {e}")[:200]}


def exe_sha256(path):
    """SHA-256 of the exe, cached per path + mtime + size (read once per change, not once per start)."""
    p = Path(path)
    st = p.stat()
    key = (str(p), st.st_mtime_ns, st.st_size)
    if key not in _exe_hashes:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        _exe_hashes[key] = h.hexdigest()
    return _exe_hashes[key]


def registry_font_names(text):
    """Sorted font names from user.reg text: the External Fonts value names and the Replacements `name=replacement` pairs
    (both are font names). Nothing else is read out of the registry; External Fonts' values (file paths) are dropped."""
    names, section = [], None
    for line in text.splitlines():
        if line.startswith("["):
            m = re.match(r"\[(.*?)\]", line)
            section = m.group(1) if m else None
            continue
        if section not in FONT_SECTIONS or not line.startswith('"'):
            continue
        m = re.match(r'"((?:[^"\\]|\\.)*)"\s*=\s*(.*)$', line)
        if not m:
            continue
        if section.endswith("External Fonts"):
            names.append("E:" + m.group(1))
        else:
            names.append("R:" + m.group(1) + "=" + m.group(2).strip().strip('"'))
    return sorted(names)


def registry_fonts_hash(user_reg):
    names = registry_font_names(Path(user_reg).read_text(errors="replace"))
    return {"sha256_12": hashlib.sha256("\n".join(names).encode()).hexdigest()[:12], "count": len(names)}


def _fc_match(family):
    return _run("fc-match", "-f", "%{family}", family).split(",")[0]       # "DejaVu Sans"


def _fonts(r):
    """The fonts part, from the results of the parallel probes `r` (fc_book, fc_ms, fc_list: a value or {"error": ...})."""
    d = {"Book Antiqua": r["fc_book"], "MS Sans Serif": r["fc_ms"]}
    lst = r["fc_list"]
    if isinstance(lst, dict):
        d["liberation_count"] = d["tahoma_wine"] = lst
    else:
        d["liberation_count"] = sum("liberation" in x.lower() for x in lst)
        d["tahoma_wine"] = any("/wine/" in x.lower() and "tahoma" in x.lower() for x in lst)
    return d


def _xvfb_size(display):
    out = _run("xdpyinfo", env=dict(os.environ, DISPLAY=display))
    m = re.search(r"dimensions:\s+(\d+x\d+)", out)
    if not m:
        raise RuntimeError("no dimensions in xdpyinfo output")
    return m.group(1)


def _parallel(probes):
    """Run every probe in its own daemon thread under one shared deadline (BUDGET s from now): the whole set returns by then
    whatever the probes do, even when all hang or fail. A probe unfinished at the deadline is recorded as an error (its thread is
    abandoned: it is a daemon and its subprocess has its own timeout)."""
    deadline = time.monotonic() + BUDGET
    _deadline[0] = deadline
    out = {}

    def work(name, fn):
        out[name] = _probe(fn)

    threads = {n: threading.Thread(target=work, args=(n, f), daemon=True) for n, f in probes.items()}
    for t in threads.values():
        t.start()
    for t in threads.values():
        t.join(max(0.0, deadline - time.monotonic()))
    _deadline[0] = None
    return {n: dict(out[n]) if isinstance(out.get(n), dict) else out[n] if n in out
            else {"error": "TimeoutError: probe did not finish within the fingerprint budget"} for n in probes}


def fingerprint(prefix, exe=None, display=None, game_dir=None, refresh=False):
    """The environment as a plain JSON-able dict. Cached per process by (prefix, exe path, display) unless `refresh`; the whole
    probe set is bounded by BUDGET seconds."""
    prefix = Path(prefix)
    exe = exe or os.environ.get("IC2_EXE", "Imperial Conquest 2 fast rollingsave seed.exe")
    display = display or os.environ.get("DISPLAY_IC2", ":99")
    game_dir = Path(game_dir) if game_dir else prefix / "drive_c" / "IC2"
    key = (str(prefix), str(game_dir / exe), display)
    if not refresh and key in _cache:
        return _cache[key]
    probes = {"wine": lambda: _run(WINE, "--version"),
              "exe": lambda: exe_sha256(game_dir / exe),
              "xvfb": lambda: _xvfb_size(display),
              "fc_book": lambda: _fc_match("Book Antiqua"),
              "fc_ms": lambda: _fc_match("MS Sans Serif"),
              "fc_list": lambda: _run("fc-list", "--format", "%{file}\n").splitlines(),
              "reg": lambda: registry_fonts_hash(prefix / "user.reg")}
    r = _parallel(probes)
    fp = {"wine": r["wine"], "exe": {"name": exe, "sha256": r["exe"]}, "xvfb_screen": r["xvfb"], "fonts": _fonts(r),
          "prefix_fonts": r["reg"]}
    _cache[key] = fp
    return fp


def add_sink(fn, key=None):
    """Register fn(record) to be called after every Game start with the environment record: how a runner puts it in its own log.
    With a `key` the sink replaces the earlier one of that key (a runner that opens a new log per run keeps one sink)."""
    if key is not None:
        _keyed.pop(key, None)
        _keyed[key] = fn
    elif fn not in _sinks:
        _sinks.append(fn)
    return fn


def record_start(prefix, exe, display, game_dir, pid, jsonl, log):
    """What Game.record_environment does: fingerprint, one log line per process, one jsonl line per start (append only), sinks."""
    fp = fingerprint(prefix, exe, display, game_dir)
    key = (str(prefix), str(exe), display, pid)       # per game process: a restart in the same Python process logs again
    if key not in _logged:
        _logged.add(key)
        try:
            log(log_line(fp))
        except Exception:
            pass
    rec = {"step": "environment", "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "pid": pid, "argv0": sys.argv[0] if sys.argv else "",
           "cwd": os.getcwd(), "environment": fp}
    try:
        with open(jsonl, "a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    except Exception:
        pass
    try:       # the tracked copy: environment.jsonl in the runner's own data folder, append only
        folder = _override[0] or (data_folder(sys.argv[0]) if sys.argv and sys.argv[0] else None)
        if folder is not None:
            Path(folder).mkdir(parents=True, exist_ok=True)
            with open(Path(folder) / "environment.jsonl", "a") as f:
                f.write(json.dumps(rec, sort_keys=True) + "\n")
    except Exception:
        pass
    for sink in list(_sinks) + list(_keyed.values()):
        try:
            sink(rec)
        except Exception:
            pass
    return fp


REPO = Path(__file__).resolve().parent.parent
# runs/experiments/<dir> whose tracked data folder is not run-exp-<dir with _ as ->
DATA_FOLDERS = {"battles": "run-exp-battle-sweep", "fleet-battles": "run-exp-naval-battle", "unit-map-mouse": "run-exp-unitmap-mouse"}
_override = [None]


def data_folder(script, repo=None):
    """The TRACKED folder where the runner `script` keeps its outputs (CLAUDE.md rule 6), or None when the script is not under runs/:
    runs/experiments/data/run-exp-<n>/x.py -> that folder; runs/experiments/<dir>/x.py -> runs/experiments/data/run-exp-<dir>/
    (`_` as `-`, exceptions in DATA_FOLDERS); runs/experiments/x.py -> runs/experiments/<x>/; runs/<id>/x.py -> runs/<id>/."""
    repo = Path(repo) if repo else REPO
    try:
        parts = (Path(script).resolve().relative_to((repo / "runs").resolve())).parts
    except (ValueError, OSError):
        return None
    if not parts or len(parts) < 2:
        return None
    base = repo / "runs"
    if parts[0] != "experiments":
        return base / parts[0]
    rest = parts[1:]
    if rest[0] == "data":
        return base / "experiments" / "data" / rest[1] if len(rest) > 2 and rest[1].startswith("run-exp-") else None
    if len(rest) == 1:
        return base / "experiments" / Path(rest[0]).stem
    return base / "experiments" / "data" / DATA_FOLDERS.get(rest[0], "run-exp-" + rest[0].replace("_", "-"))


def set_data_folder(folder):
    """A runner whose tracked data folder differs from data_folder()'s guess says so here (it must be a tracked folder, not artifacts/)."""
    _override[0] = Path(folder)


def sink_line(rec):
    """The record as one `environment {json}` text line, for runners whose log is text."""
    return "environment " + json.dumps({k: v for k, v in rec.items() if k != "step"}, separators=(",", ":"), sort_keys=True)


def log_line(fp):
    return "environment " + json.dumps(fp, separators=(",", ":"), sort_keys=True)
