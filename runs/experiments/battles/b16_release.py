#!/usr/bin/env python3
"""B16: upload what release `run-exp-battle-peace` does not hold yet, as ONE per-batch tar.gz of binaries (GitHub caps a release at 1000 assets).

    python3 runs/experiments/battles/b16_release.py <label> [--dry]

Archives every file under artifacts/run-exp-battle-peace/ (saves .SAV, snapshots .snap.gz, screenshots .png; not `_tmp*`, not `archives/`) whose name is not
a member of an earlier tracked manifest. Writes tracked files (new names, never overwritten): `MANIFEST-<label>-<stamp>.txt` (sha256  name, one line per member),
`release-manifest-<stamp>.json` (archive sha256, size, members), `release-sync-<stamp>.json`. The release is created at the first batch with
`gh release create run-exp-battle-peace ...`, later batches use `gh release upload`. A refused call (HTTP 403) leaves the archive in artifacts/ and
prints the exact command; exit 3: report it, do not retry another way. IC2_RELEASE_TOKEN is read by gh from the environment; it is never printed here."""
import json
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import os  # noqa: E402
os.environ.setdefault("IC2_WORK", "/nonexistent")
os.environ.setdefault("DISPLAY_IC2", ":640")
import b16_common as B  # noqa: E402
import common as C  # noqa: E402

TAG = "run-exp-battle-peace"
EXT = {".sav", ".png", ".gz"}


def held():
    out = set()
    for f in B.DATA.glob("release-manifest-*.json"):
        for a in json.loads(f.read_text()).get("archives", {}).values():
            if a.get("uploaded"):
                out |= set(a["members"])
    return out


def pending():
    have, seen, files = held(), set(), []
    for f in sorted(B.ART.rglob("*")):
        if f.is_file() and f.suffix.lower() in EXT and not f.name.startswith("_tmp") and "archives" not in f.parts and f.name not in have and f.name not in seen:
            seen.add(f.name)
            files.append(f)
    return files


def main():
    label = next((a for a in sys.argv[1:] if not a.startswith("--")), "batch")
    files = pending()
    rec = {"tag": TAG, "label": label, "pending": len(files), "refused": None}
    if "--dry" in sys.argv or not files:
        print(json.dumps(rec))
        return
    arch_dir = B.ART / "archives"
    arch_dir.mkdir(exist_ok=True)
    p = C.write_new(arch_dir, "%s-%s.tar.gz" % (label, C.STAMP), b"")
    with tarfile.open(p, "w:gz") as t:
        for f in files:
            t.add(f, arcname=f.name)
    members = {f.name: C.sha(f) for f in files}
    C.write_new(B.DATA, "MANIFEST-%s-%s.txt" % (label, C.STAMP), "".join("%s  %s\n" % (h, n) for n, h in members.items()))
    exists = subprocess.run(["gh", "release", "view", TAG], capture_output=True, text=True).returncode == 0
    cmd = (["gh", "release", "upload", TAG, str(p)] if exists else
           ["gh", "release", "create", TAG, str(p), "--title", TAG, "--notes", "B16 the Offer of peace: saves, snapshots and screenshots in per-batch .tar.gz archives; members and SHA-256 in the tracked MANIFEST-*.txt / release-manifest-*.json (findings/2026-10-04-battle-peace-offer.md)."])
    r = subprocess.run(cmd, capture_output=True, text=True)
    arch = {p.name: {"sha256": C.sha(p), "size": p.stat().st_size, "members": members, "uploaded": r.returncode == 0}}
    if r.returncode:
        rec["refused"] = {"stderr": r.stderr[-300:], "command": "gh release %s %s artifacts/%s/archives/%s" % ("upload" if exists else "create", TAG, C.NAME, p.name)}
    rec["archives"] = arch
    C.write_new(B.DATA, "release-sync-%s.json" % C.STAMP, json.dumps(rec, indent=1))
    C.write_new(B.DATA, "release-manifest-%s.json" % C.STAMP, json.dumps({"release": TAG, "archives": arch}, indent=1))
    print(json.dumps({k: v for k, v in rec.items() if k != "archives"}), len(members), "members")
    sys.exit(3 if rec["refused"] else 0)


if __name__ == "__main__":
    main()
