#!/usr/bin/env python3
"""Upload the saves and screenshots under artifacts/run-exp-battle-sweep/ that the release `run-exp-battle-sweep` does not hold yet (by file name).
Never clobbers, never deletes. If `gh release upload` is refused, prints the exact command and exits 3 (CLAUDE.md rule 1: report it, do not retry another way).
    python3 runs/experiments/battles/release_sync.py [--dry]
Writes `release-sync-<stamp>.json` (tracked) listing what was uploaded or what is pending."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

TAG = "run-exp-battle-sweep"
EXT = {".sav", ".png"}


def held():
    out = subprocess.run(["gh", "release", "view", TAG, "--json", "assets", "--jq", ".assets[].name"], capture_output=True, text=True, check=True).stdout
    return set(out.split())


def pending():
    have, seen, files = held(), set(), []
    for f in sorted(C.ART.rglob("*")):
        if f.is_file() and f.suffix.lower() in EXT and not f.name.startswith("_tmp") and f.name not in have and f.name not in seen:
            seen.add(f.name)
            files.append(f)
    return files


def main():
    files = pending()
    rec = {"tag": TAG, "pending": len(files), "uploaded": [], "refused": None}
    for i in range(0, len(files), 40):
        chunk = files[i:i + 40]
        cmd = ["gh", "release", "upload", TAG] + [str(f) for f in chunk]
        if "--dry" in sys.argv:
            continue
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            rec["refused"] = {"stderr": r.stderr[-400:], "command": "gh release upload %s <%d files from artifacts/%s/>" % (TAG, len(files) - i, C.NAME)}
            break
        rec["uploaded"] += [f.name for f in chunk]
    C.write_new(C.DATA, "release-sync-%s.json" % C.STAMP, json.dumps(rec, indent=1))
    print(json.dumps({k: (v if k != "uploaded" else len(v)) for k, v in rec.items()}))
    sys.exit(3 if rec["refused"] else 0)


if __name__ == "__main__":
    main()
