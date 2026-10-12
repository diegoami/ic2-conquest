#!/usr/bin/env python3
"""Offline test (no Wine) for archive_measurements.py `__pycache__` filters.

The fix prevents the --commit gate from refusing to commit when a stale
`runs/experiments/data/<name>/__pycache__/` directory exists at the destination
(it is gitignored, but the bytes came from a runner that imported g*_lib in
place before a previous archive created the folder). The script must (a) never
copy `__pycache__/` from the source walk and (b) exclude any `__pycache__/`
paths from the `git check-ignore` list passed before the commit.

These tests exercise the production code: `M.archive()` with a temporary ROOT
for the source filter and `M._files_for_check_ignore()` for the destination
gate. They fail when either production filter is removed.

Run: python3 -m tests.test_archive_pycache   (exit 1 on a failure).
"""
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT_PKG = Path(__file__).resolve().parent.parent
SCRIPT = ROOT_PKG / "scripts" / "archive_measurements.py"


def _archive_module():
    spec = importlib.util.spec_from_file_location("archive_under_test", SCRIPT)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _init_git(tmp):
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@x"], cwd=tmp, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp, check=True, capture_output=True)


def main():
    sys.argv = ["x"]
    M = _archive_module()

    # 1. The production `archive()` does not copy a TEXT-extension file from
    #    `__pycache__/` at the source — a `.pyc` would be skipped by the
    #    extension filter alone, so we put a `.jsonl` inside `__pycache__/`
    #    to exercise the production filter directly.
    with tempfile.TemporaryDirectory() as tmp:
        name = "run-exp-pycache-source"
        (Path(tmp) / "artifacts" / name).mkdir(parents=True)
        dst_root = Path(tmp) / "runs" / "experiments" / "data" / name
        dst_root.mkdir(parents=True)
        (Path(tmp) / "artifacts" / name / "result.jsonl").write_text("entry\n")
        cached = Path(tmp) / "artifacts" / name / "__pycache__"
        cached.mkdir()
        (cached / "stale.jsonl").write_text("entry inside __pycache__\n")
        saved = M.ROOT
        M.ROOT = Path(tmp)
        try:
            M.archive(name)
        finally:
            M.ROOT = saved
        assert (dst_root / "result.jsonl").exists(), "regular src file not archived"
        assert not (dst_root / "__pycache__").exists(), (
            "__pycache__/ at src was archived despite the production filter"
        )
        assert not (dst_root / "__pycache__" / "stale.jsonl").exists(), (
            "TEXT file inside __pycache__/ at src leaked through archive()"
        )

    # 2. The production `_files_for_check_ignore()` excludes `__pycache__/`
    #    from the destination list passed to `git check-ignore`.
    with tempfile.TemporaryDirectory() as tmp:
        _init_git(tmp)
        (Path(tmp) / ".gitignore").write_text("__pycache__/\n")
        dst = Path(tmp) / "runs" / "experiments" / "data" / "run-exp-pycache-dst"
        dst.mkdir(parents=True)
        (dst / "result.jsonl").write_text("entry\n")
        cached = dst / "__pycache__"
        cached.mkdir()
        (cached / "stale.pyc").write_text("x")
        # The destination has a `__pycache__/stale.pyc` that IS ignored
        r0 = subprocess.run(
            ["git", "check-ignore", "-v", str(cached / "stale.pyc")],
            cwd=tmp, capture_output=True, text=True,
        )
        assert r0.returncode == 0, ("setup: stale.pyc should be ignored", r0.stdout, r0.stderr)
        files = M._files_for_check_ignore(dst)
        assert all("__pycache__" not in f for f in files), ("filter leak", files)
        assert any(f.endswith("result.jsonl") for f in files), files
        # The kept set passes `git check-ignore` (returncode 1 = none ignored)
        r1 = subprocess.run(["git", "check-ignore", *files], cwd=tmp, capture_output=True, text=True)
        assert r1.returncode == 1, (
            "filter kept set still has an ignored file", r1.stdout, r1.stderr, files
        )

    print("test_archive_pycache: all checks passed")


if __name__ == "__main__":
    main()
