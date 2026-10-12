#!/usr/bin/env python3
"""Upload to release run-exp-g3-original-checks what it does not hold yet from artifacts/run-exp-g3-original-checks/ (creates the release
first if missing). Never deletes, never clobbers. If a release call is refused, prints the exact command and exits 3 (CLAUDE.md rule 1:
report it, never retry another way). Writes release-sync-<stamp>.json beside this script (rule 6)."""
import json, shlex, subprocess, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[4]
TAG = "run-exp-g3-original-checks"
ART = R / "artifacts" / TAG
D = Path(__file__).resolve().parent


def run(*a):
    return subprocess.run(a, capture_output=True, text=True, cwd=R)


have = run("gh", "release", "view", TAG, "--json", "assets", "--jq", ".assets[].name")
exists = have.returncode == 0
held = set(have.stdout.split()) if exists else set()
pending = sorted(p for p in ART.iterdir() if p.is_file() and p.name not in held)
rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "release_existed": exists, "pending": [p.name for p in pending], "uploaded": [], "refused": None}
for i in range(0, len(pending), 40):
    chunk = [str(p) for p in pending[i:i + 40]]
    if not exists:
        cmd = ["gh", "release", "create", TAG, "--title", TAG, "--notes", "Saves and screenshots of the G3 original-side checks (issue #80); SHA-256 in runs/experiments/data/run-exp-g3-original-checks/SAVES.sha256"] + chunk
        exists = True
    else:
        cmd = ["gh", "release", "upload", TAG] + chunk
    r = run(*cmd)
    if r.returncode:
        rec["refused"] = {"command": cmd, "command_shell": shlex.join(cmd), "cwd": str(R), "stderr": r.stderr[-600:]}
        print("REFUSED:", r.stderr[-600:], "\nexact command (run from %s):\n%s" % (R, shlex.join(cmd)))
        break
    rec["uploaded"] += [Path(c).name for c in chunk]
(D / f"release-sync-{time.strftime('%Y%m%d-%H%M%S')}.json").write_text(json.dumps(rec, indent=1))
print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in rec.items()}))
sys.exit(3 if rec["refused"] else 0)
