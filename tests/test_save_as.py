#!/usr/bin/env python3
"""Offline test of Game.save_as (no Wine): it refuses an existing destination and leaves it untouched (rule 6); overwrite=True replaces it.
Run: python3 -m tests.test_save_as   (exit 1 on a failure)."""
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import harness.driver as D  # noqa: E402


class Stub(D.Game):
    def __init__(self):
        self.menus = 0
        self.name = None

    def menu(self, *a):
        self.menus += 1

    def replace_field(self, name):
        self.name = name

    def key(self, k):
        (D.G / self.name).write_bytes(b"N" * 200000)

    def wait(self, fn, *a):
        assert fn()


def main():
    old = D.G
    with tempfile.TemporaryDirectory() as tmp:
        D.G = Path(tmp)
        try:
            (D.G / "A.SAV").write_bytes(b"old")
            g = Stub()
            try:
                g.save_as("A.SAV")
                raise SystemExit("FAIL: no refusal")
            except D.DriverError as e:
                assert "already exists" in str(e)
            assert (D.G / "A.SAV").read_bytes() == b"old" and g.menus == 0, "existing file touched"
            assert g.save_as("B.SAV").stat().st_size == 200000
            g.save_as("A.SAV", overwrite=True)
            assert (D.G / "A.SAV").stat().st_size == 200000
        finally:
            D.G = old
    print("test_save_as: 3 checks passed")


if __name__ == "__main__":
    main()
