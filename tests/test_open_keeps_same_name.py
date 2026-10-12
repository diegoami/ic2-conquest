#!/usr/bin/env python3
"""Offline test (no Wine) of Game.open's copy step (rule 6): a different file of the same name in the game folder is moved to
`superseded-<stamp>/`, never overwritten; an identical one is left alone (no folder); a missing one is copied.
Run: python3 -m tests.test_open_keeps_same_name   (exit 1 on a failure)."""
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import harness.driver as D  # noqa: E402


class Stub(D.Game):
    def __init__(self):
        pass

    def open_file_dialog(self, name):
        pass

    def wait(self, *a):
        return True

    def loaded(self):
        return True

    def dismiss_popups(self, strict=True):
        return []


def main():
    old_g, old_sleep = D.G, D.time.sleep
    D.time.sleep = lambda s: None
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as srcd:
        D.G = Path(tmp)
        try:
            src = Path(srcd) / "X.SAV"
            g = Stub()
            src.write_bytes(b"one"); g.open(src)
            assert (D.G / "X.SAV").read_bytes() == b"one" and not list(D.G.glob("superseded-*")), "plain copy"
            g.open(src)
            assert not list(D.G.glob("superseded-*")), "identical file moved"
            src.write_bytes(b"two"); g.open(src)
            assert (D.G / "X.SAV").read_bytes() == b"two"
            kept = [p.read_bytes() for d in D.G.glob("superseded-*") for p in d.iterdir()]
            assert kept == [b"one"], kept
            src.write_bytes(b"three"); g.open(src)
            assert sorted(p.read_bytes() for d in D.G.glob("superseded-*") for p in d.iterdir()) == [b"one", b"two"]
        finally:
            D.G, D.time.sleep = old_g, old_sleep
    print("test_open_keeps_same_name: all checks passed")


if __name__ == "__main__":
    main()
