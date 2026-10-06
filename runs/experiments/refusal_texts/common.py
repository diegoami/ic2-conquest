"""Shared helpers: rule 6 (never overwrite a measured output; a re-run writes a new versioned file beside the old one)."""
import os, re
DATA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'run-exp-refusal-texts'))

def versions(path):
    """All existing versions of path (base file first, then .v2, .v3 ...), as [(n, path)]."""
    d, b = os.path.split(path); stem, ext = os.path.splitext(b); out = []
    if os.path.exists(path): out.append((1, path))
    if os.path.isdir(d):
        for f in os.listdir(d):
            m = re.fullmatch(re.escape(stem) + r'\.v(\d+)' + re.escape(ext), f)
            if m: out.append((int(m.group(1)), os.path.join(d, f)))
    return sorted(out)

def new_path(path):
    v = versions(path)
    if not v: return path
    d, b = os.path.split(path); stem, ext = os.path.splitext(b)
    return os.path.join(d, '%s.v%d%s' % (stem, v[-1][0] + 1, ext))

def write_new(path, data, binary=False):
    """Write to a path that does not exist yet (the next free version); opening with 'x' refuses to overwrite. Returns the path used."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    p = new_path(path)
    with open(p, 'xb' if binary else 'x', **({} if binary else {'encoding': 'utf-8'})) as f: f.write(data)
    return p

def latest(path):
    """The newest version of a tracked output (what a downstream check reads)."""
    v = versions(path)
    if not v: raise FileNotFoundError(path)
    return v[-1][1]
