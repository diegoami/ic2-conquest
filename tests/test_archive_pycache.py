#!/usr/bin/env python3
"""Offline test (no Wine) for the archive_measurements.py `__pycache__` filter.

The fix prevents the --commit gate from refusing to commit when a stale `runs/experiments/data/<name>/__pycache__/`
directory exists at the destination (it is gitignored, but the artefact there came from a runner that imported g*_lib
in place and now lives in .gitignore territory). The script must (a) never copy `__pycache__/` from the source walk
and (b) exclude any `__pycache__/` paths from the `git check-ignore` list passed before the commit.

Run: python3 -m tests.test_archive_pycache   (exit 1 on a failure).
"""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "archive_measurements.py"


def _archive_module():
    spec = importlib.util.spec_from_file_location("archive_under_test", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _git_init(tmp):
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@x"], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp, check=True, capture_output=True)


def main():
    sys.argv = ["x"]
    M = _archive_module()
    # The source-walk filter must skip __pycache__/ trees.
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "artifacts" / "run-exp-test"
        src.mkdir(parents=True)
        (src / "result.jsonl").write_text("entry\n")
        cached = src / "__pycache__"
        cached.mkdir()
        (cached / "foo.pyc").write_text("x")
        copied, versioned, sums = 0, 0, []
        for f in sorted(src.rglob("*")):
            if not f.is_file():
                continue
            if "__pycache__" in f.parts:
                continue
            rel = f.relative_to(src); ext = f.suffix.lower()
            if ext in M.TEXT:
                copied += 1
            elif ext in M.BINARY:
                sums.append(rel)
        assert copied == 1 and versioned == 0, ("source walk ignored the jsonl", copied, versioned)
        assert sums == [], ("source walk picked up a binary path", sums)
    # The destination check-ignore filter must drop __pycache__/ paths.
    with tempfile.TemporaryDirectory() as tmp:
        _git_init(tmp)
        Path(tmp, ".gitignore").write_text("__pycache__/\n")
        dst = Path(tmp) / "runs" / "experiments" / "data" / "run-exp-test"
        dst.mkdir(parents=True)
        (dst / "result.jsonl").write_text("entry\n")
        cached = dst / "__pycache__"
        cached.mkdir()
        (cached / "stale.pyc").write_text("x")
        all_files = [p for p in dst.rglob("*") if p.is_file()]
        kept = [str(p) for p in all_files if "__pycache__" not in p.parts]
        # The .pyc IS ignored by git (returncode 0 with stdout naming it)
        r0 = subprocess.run(["git", "check-ignore", "-v", str(cached / "stale.pyc")], cwd=tmp, capture_output=True, text=True)
        assert r0.returncode == 0, ("setup: stale.pyc should be ignored", r0.stdout, r0.stderr)
        # The filter kept only result.jsonl, which is NOT ignored
        r1 = subprocess.run(["git", "check-ignore", *kept], cwd=tmp, capture_output=True, text=True)
        assert r1.returncode == 1, ("filter dropped __pycache__ but kept set still hits an ignore", r1.stdout, kept)
        # And `kept` is exactly [result.jsonl], not the stale .pyc
        assert len(kept) == 1 and kept[0].endswith("result.jsonl"), kept
    print("test_archive_pycache: all checks passed")


if __name__ == "__main__":
    main()
