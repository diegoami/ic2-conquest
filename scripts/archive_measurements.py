#!/usr/bin/env python3
"""Archive an experiment's measurements into tracked paths (CLAUDE.md rule 6), without ever overwriting.

    python3 scripts/archive_measurements.py run-exp-<name> [--commit]

Copies the text outputs (json, jsonl, log, csv, txt) of `artifacts/<name>/` to `runs/experiments/data/<name>/` and writes `SAVES.sha256`
(the SHA-256 of every .SAV and other binary, whose files stay out of git and go to the release). A file that already exists there with
different content is NOT replaced: the new content is written beside it as `<stem>.v<N><ext>` (a growing trials.json is versioned by
its content, so the history of the batches is kept). `--commit` runs `git add` on the folder, commits and pushes the current branch.
"""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".json", ".jsonl", ".log", ".csv", ".txt"}
BINARY = {".sav", ".png", ".jpg", ".mp4", ".avi", ".mkv", ".exe", ".dat"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def archive(name):
    src, dst = ROOT / "artifacts" / name, ROOT / "runs" / "experiments" / "data" / name
    if not src.is_dir():
        sys.exit(f"no {src}")
    dst.mkdir(parents=True, exist_ok=True)
    copied, versioned, sums = 0, 0, []
    for f in sorted(src.iterdir()):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext in TEXT:
            target = dst / f.name
            if target.exists() and sha(target) != sha(f):
                existing = {sha(p) for p in dst.glob(f"{f.stem}.v*{f.suffix}")}
                if sha(f) in existing:
                    continue
                n = 2
                while (dst / f"{f.stem}.v{n}{f.suffix}").exists():
                    n += 1
                target = dst / f"{f.stem}.v{n}{f.suffix}"
                versioned += 1
            elif target.exists():
                continue
            shutil.copy2(f, target)
            copied += 1
        elif ext in BINARY:
            sums.append(f"{sha(f)}  {f.name}")
    if sums:
        sumfile = dst / "SAVES.sha256"
        old = set(sumfile.read_text().splitlines()) if sumfile.exists() else set()
        merged = sorted(old | set(sums), key=lambda l: l.split("  ", 1)[1])
        sumfile.write_text("\n".join(merged) + "\n")      # hashes are only ever added
    print(f"{name}: {copied} text files copied ({versioned} as new versions beside an older one), {len(sums)} binaries hashed")
    return dst


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    d = archive(args[0])
    if "--commit" in sys.argv:
        subprocess.run(["git", "add", str(d)], cwd=ROOT, check=True)
        r = subprocess.run(["git", "commit", "-q", "-m", f"measurements of {args[0]} (archived, rule 6)"], cwd=ROOT)
        if r.returncode == 0:
            subprocess.run(["git", "push", "-q"], cwd=ROOT, check=True)
