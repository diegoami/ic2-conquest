#!/usr/bin/env python3
"""What are the OpenCode runs doing? One plain line per run, running first.

    opencode_status.py [--root rendered] [--hours 24] [--all]

Reads the run dirs that opencode_watched.py keeps under <root>/<kind><n>-<token>/run-<k>/ (state.json, progress.jsonl,
result.json; the progress comes from OpenCode's session database, read-only). A run whose watcher process is gone without a
result is shown as DIED. Ended runs older than --hours are left out unless --all. Example lines:

  PR 66 review · gpt-5.6-luna · running 4m · 12 steps · now: read findings/x.md · todo 2/3 (check the diff)
  PR 66 review · gpt-5.6-luna · STOPPED (process: idle-timeout) · no progress for 600s · session ses_... · resume: python3 scripts/external_review.py --resume <dir>
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opencode_watched as ow  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def runs(root):
    """Every run dir under root (a dir with a state.json), at most two levels down."""
    root = Path(root)
    return sorted({p.parent for pat in ("*/state.json", "*/*/state.json") for p in root.glob(pat)})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(REPO / "rendered"), help="where the run dirs are (default: the main checkout's rendered/)")
    ap.add_argument("--hours", type=float, default=24, help="show ended runs from the last N hours")
    ap.add_argument("--all", action="store_true", help="show every ended run")
    a = ap.parse_args()
    now = time.time()
    rows = []
    for rd in runs(a.root):
        try:
            line = ow.describe(rd, now)
        except Exception as e:                             # one odd run dir must not hide the others
            line = f"{rd.name} · unreadable run dir ({type(e).__name__}: {e})"
        st = ow.read_json(rd / "state.json")
        st = st if isinstance(st, dict) else {}
        if not line:
            continue
        running = " · running " in line
        if not running and not a.all and now - st.get("updated", 0) > a.hours * 3600:
            continue
        rows.append((0 if running else 1, -st.get("updated", 0), line))
    for _, _, line in sorted(rows):
        print(line)
    if not rows:
        print("no OpenCode runs" + ("" if a.all else f" running or ended in the last {a.hours:g} h") + f" under {a.root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
