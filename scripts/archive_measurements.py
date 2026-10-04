#!/usr/bin/env python3
"""Archive an experiment's measurements into tracked paths (CLAUDE.md rule 6), without ever overwriting.

    python3 scripts/archive_measurements.py run-exp-<name> [--commit]

Copies the text outputs (json, jsonl, log, csv, txt) of `artifacts/<name>/` to `runs/experiments/data/<name>/` and writes `SAVES.sha256`
(the SHA-256 of every .SAV and other binary, whose files stay out of git and go to the release). A file that already exists there with
different content is NOT replaced: the new content is written beside it as `<stem>.v<N><ext>` (a growing trials.json is versioned by
its content, so the history of the batches is kept). Subfolders (one per season) are walked and keep their relative path. A text file
with an upper-case extension (`AUTOSAVE.LOG`) is archived with the extension lower-cased, because `.gitignore` ignores `*.LOG`.
`--trailer "<line>"` (with `--commit`) is appended to the commit message after a blank line.
`--commit` runs `git add` on the folder, refuses to commit if git would still ignore an archived file, commits and pushes the branch.
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
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        ext = f.suffix.lower()
        if ext in TEXT:
            target = dst / rel.parent / (f.stem + ext)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and sha(target) != sha(f):
                existing = {sha(p) for p in target.parent.glob(f"{f.stem}.v*{ext}")}
                if sha(f) in existing:
                    continue
                n = 2
                while (target.parent / f"{f.stem}.v{n}{ext}").exists():
                    n += 1
                target = target.parent / f"{f.stem}.v{n}{ext}"
                versioned += 1
            elif target.exists():
                continue
            shutil.copy2(f, target)
            copied += 1
        elif ext in BINARY:
            sums.append(f"{sha(f)}  {rel.as_posix()}")
    if sums:
        sumfile = dst / "SAVES.sha256"
        current = sumfile.read_text() if sumfile.exists() else ""
        old = {l for l in current.splitlines() if "  " in l}
        merged = sorted(old | set(sums), key=lambda l: (l.split("  ", 1)[1], l))   # hashes are only ever added
        text = "\n".join(merged) + "\n"
        if text != current:
            sumfile.write_text(text)
    print(f"{name}: {copied} text files copied ({versioned} as new versions beside an older one), {len(sums)} binaries hashed")
    return dst


if __name__ == "__main__":
    argv = sys.argv[1:]
    trailer = None
    if "--trailer" in argv:
        i = argv.index("--trailer")
        trailer = argv[i + 1] if i + 1 < len(argv) else sys.exit("--trailer needs a line")
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    d = archive(args[0])
    if "--commit" in sys.argv:
        subprocess.run(["git", "add", str(d)], cwd=ROOT, check=True)
        files = [str(p) for p in d.rglob("*") if p.is_file()]
        ignored = subprocess.run(["git", "check-ignore", *files], cwd=ROOT, capture_output=True, text=True).stdout.split()
        if ignored:
            sys.exit("git ignores these archived files, nothing committed: " + " ".join(ignored))
        r = subprocess.run(["git", "commit", "-q", "-m", f"measurements of {args[0]} (archived, rule 6)" + (f"\n\n{trailer}" if trailer else "")], cwd=ROOT)
        if r.returncode == 0:
            subprocess.run(["git", "push", "-q"], cwd=ROOT, check=True)
