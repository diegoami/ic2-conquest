"""Rule 6 helper: write a new output beside the old ones, never over them (next free <stem>.v<N><ext>)."""
import re
from pathlib import Path


def next_free(path):
    path = Path(path)
    if not path.exists():
        return path
    n = 2
    for f in path.parent.iterdir():
        m = re.fullmatch(re.escape(path.stem) + r"\.v(\d+)" + re.escape(path.suffix), f.name)
        if m:
            n = max(n, int(m.group(1)) + 1)
    return path.with_name(f"{path.stem}.v{n}{path.suffix}")


def write_new(path, text):
    """Create the next free version of `path` (open mode 'x' refuses to overwrite); returns the path written."""
    p = next_free(path)
    with open(p, "x", encoding="utf-8") as f:
        f.write(text)
    return p
