#!/usr/bin/env python3
"""Offline test (no Wine) of g1_lib.staged (review R3, round 3): repeated tags and opposite-sign treasuries (the runner's tag uses
abs(treasury)) never replace an earlier staged save: each call writes a new file (`.vN` suffix), the earlier bytes survive, every file is hashed.
Run: python3 -m tests.test_g1_staged_unique   (exit 1 on a failure)."""
import importlib.util
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "runs/experiments/data/run-exp-g1-original-checks/g1_lib.py"


def main():
    sys.argv = ["x", "TESTCASE"]
    sys.path.insert(0, str(LIB.parent))
    spec = importlib.util.spec_from_file_location("g1_lib_under_test", LIB); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
    with tempfile.TemporaryDirectory() as tmp:
        L.ART = Path(tmp); L.D = Path(tmp); L.LOG = Path(tmp) / "log.jsonl"
        a = L.staged(L.START, [("treasury", 0, -5100)], "test5100")
        b = L.staged(L.START, [("treasury", 0, 5100)], "test5100")        # same tag, opposite sign: abs() collides
        c = L.staged(L.START, [("treasury", 0, -5100)], "test5100")       # repeated identical call
        names = [a.name, b.name, c.name]
        assert len(set(names)) == 3, names
        assert a.read_bytes() != b.read_bytes(), "opposite-sign treasuries must differ"
        assert a.read_bytes() == c.read_bytes()
        assert [p.name for p in sorted(Path(tmp).glob("*.SAV"))] == sorted(names)
        hashes = (Path(tmp) / "SAVES.sha256").read_text().splitlines()
        assert len(hashes) == 3 and {h.split("  ")[1] for h in hashes} == set(names), hashes
    print("test_g1_staged_unique: all checks passed")


if __name__ == "__main__":
    main()
