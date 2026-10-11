#!/usr/bin/env python3
"""Offline test (no Wine) of Game.new_game's handling of AUTO* files (rule 6): existing autosaves and AUTOSAVE.LOG are moved into a
`superseded-<stamp>/` folder, never deleted; two calls in the same second give two distinct folders; with nothing to move nothing is made.
Everything new_game calls is stubbed. Run: python3 -m tests.test_new_game_keeps_autosaves   (exit 1 on a failure)."""
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import harness.driver as D  # noqa: E402


class Stub(D.Game):
    def __init__(self):
        self.clicks = []

    def set_seed(self, seed):
        pass

    def start(self):
        assert not list(D.G.glob("AUTO*")), "AUTO* still in the game folder when the game starts"

    def menu(self, *a):
        pass

    def wait(self, fn, *a):
        if "autosave" in a[-1]:
            (D.G / "AUTOSAVE.LOG").write_text("0720 AUTO0720.SAV OK\n"); (D.G / "AUTO0720.SAV").write_bytes(b"new")
        return True

    def find_windows(self, *a):
        return [1]

    def click(self, *a, **k):
        self.clicks.append(a)

    def dismiss_popups(self):
        return []


def main():
    old_g, old_sleep = D.G, D.time.sleep
    D.time.sleep = lambda s: None
    with tempfile.TemporaryDirectory() as tmp:
        D.G = Path(tmp)
        try:
            assert Stub().supersede_autosaves() is None and not list(D.G.glob("superseded-*")), "folder made for nothing"
            (D.G / "AUTO0721.SAV").write_bytes(b"measured-1"); (D.G / "AUTO0722.SAV").write_bytes(b"measured-2")
            (D.G / "AUTOSAVE.LOG").write_text("0721 AUTO0721.SAV OK\n"); (D.G / "other.SAV").write_bytes(b"x")
            g = Stub()
            path, _ = g.new_game(row=0, seed=1)
            assert path.read_bytes() == b"new"
            kept = {p.name: p.read_bytes() for d in D.G.glob("superseded-*") for p in d.iterdir()}
            assert kept == {"AUTO0721.SAV": b"measured-1", "AUTO0722.SAV": b"measured-2", "AUTOSAVE.LOG": b"0721 AUTO0721.SAV OK\n"}, kept
            assert (D.G / "other.SAV").read_bytes() == b"x", "a non-AUTO file was touched"
            # second new game: the first game's autosaves are kept too, in a distinct folder
            g.new_game(row=0, seed=1)
            folders = sorted(D.G.glob("superseded-*"))
            assert len(folders) == 2, folders
            assert any((f / "AUTO0720.SAV").read_bytes() == b"new" for f in folders if (f / "AUTO0720.SAV").exists())
        finally:
            D.G, D.time.sleep = old_g, old_sleep
    print("test_new_game_keeps_autosaves: all checks passed")


if __name__ == "__main__":
    main()
