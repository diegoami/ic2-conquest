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
from pathlib import Path

WINE = "/usr/lib/wine/wine"
FONT_SECTIONS = ("Software\\\\Wine\\\\Fonts\\\\External Fonts", "Software\\\\Wine\\\\Fonts\\\\Replacements")
_cache = {}          # per process: prefix -> fingerprint
_exe_hashes = {}     # (path, mtime_ns, size) -> sha256 hex


def _run(*args, env=None, timeout=10):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env, check=True)
    return r.stdout.strip()


def _probe(fn):
    try:
        return fn()
    except Exception as e:          # best-effort: the error is the record
        return {"error": f"{type(e).__name__}: {e}"[:200]}


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


def _fonts():
    d = {"Book Antiqua": _probe(lambda: _fc_match("Book Antiqua")),
         "MS Sans Serif": _probe(lambda: _fc_match("MS Sans Serif"))}
    lst = _probe(lambda: _run("fc-list", "--format", "%{file}\n").splitlines())
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


def fingerprint(prefix, exe=None, display=None, refresh=False):
    """The environment as a plain JSON-able dict. Cached per process and prefix unless `refresh`."""
    prefix = Path(prefix)
    if not refresh and str(prefix) in _cache:
        return _cache[str(prefix)]
    exe = exe or os.environ.get("IC2_EXE", "Imperial Conquest 2 fast rollingsave seed.exe")
    display = display or os.environ.get("DISPLAY_IC2", ":99")
    fp = {"wine": _probe(lambda: _run(WINE, "--version")),
          "exe": {"name": exe, "sha256": _probe(lambda: exe_sha256(prefix / "drive_c" / "IC2" / exe))},
          "xvfb_screen": _probe(lambda: _xvfb_size(display)),
          "fonts": _fonts(),
          "prefix_fonts": _probe(lambda: registry_fonts_hash(prefix / "user.reg"))}
    _cache[str(prefix)] = fp
    return fp


def log_line(fp):
    return "environment " + json.dumps(fp, separators=(",", ":"), sort_keys=True)
