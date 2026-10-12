#!/usr/bin/env python3
"""Offline test (no Wine) of harness/preserve.sh, the rule-6 helpers of harness/new_game.sh (review R1, R4): a rerun with the same
output name keeps the earlier output's bytes; a `superseded-<stamp>` folder that already exists with the same AUTO name is not reused or
overwritten; a failed preservation returns non-zero (new_game.sh then aborts before launching the game).
Run: python3 -m tests.test_new_game_sh_keeps_saves   (exit 1 on a failure)."""
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SH = ROOT / "harness" / "preserve.sh"


def bash(script):
    return subprocess.run(["bash", "-c", f". '{SH}'; {script}"], capture_output=True, text=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp); g = t / "G"; out = t / "out"; g.mkdir()
        # R1: same output name twice
        (g / "AUTO0720.SAV").write_bytes(b"first")
        r = bash(f"copy_out_unique '{g}' '{out}' x.SAV"); assert r.returncode == 0, r
        (g / "AUTO0720.SAV").write_bytes(b"second")
        r = bash(f"copy_out_unique '{g}' '{out}' x.SAV"); assert r.returncode == 0, r
        assert (out / "x.SAV").read_bytes() == b"first", "earlier output overwritten"
        assert (out / "x.SAV.1").read_bytes() == b"second", "rerun output not kept"
        # R4: a superseded folder of the same second already exists and holds the same AUTO basename
        stamp = "20260101-000000"
        fake = "date() { echo 20260101-000000; };"
        (g / "superseded-20260101-000000").mkdir(); (g / "superseded-20260101-000000" / "AUTO0720.SAV").write_bytes(b"archived-A")
        (g / "AUTO0720.SAV").write_bytes(b"live-B")
        r = bash(f"{fake} supersede_autos '{g}'"); assert r.returncode == 0, r
        assert (g / "superseded-20260101-000000" / "AUTO0720.SAV").read_bytes() == b"archived-A", "archived save overwritten"
        moved = [p.read_bytes() for d in g.glob("superseded-*") if d.name != "superseded-20260101-000000" for p in d.iterdir()]
        assert moved == [b"live-B"], moved
        assert not list(g.glob("AUTO*")), "AUTO* left in the game folder"
        # nothing to move: no folder, success
        before = sorted(p.name for p in g.iterdir())
        assert bash(f"supersede_autos '{g}'").returncode == 0 and sorted(p.name for p in g.iterdir()) == before
        # a failure stops the launch: mv -n cannot move a file into a read-only folder -> non-zero
        (g / "AUTO0721.SAV").write_bytes(b"live-C")
        r = bash(f"mkdir() {{ command mkdir \"$@\"; chmod a-w \"${{@: -1}}\"; }}; supersede_autos '{g}'")
        import os
        if os.geteuid() != 0:
            assert r.returncode != 0 and (g / "AUTO0721.SAV").read_bytes() == b"live-C", r
            for d in g.glob("superseded-*"): d.chmod(0o755)
        # round 4 R1: a listing that fails is NOT "nothing to preserve" (injected, so it does not depend on the UID)
        (g / "AUTO0722.SAV").write_bytes(b"live-D")
        r = bash(f"preserve_ls() {{ return 2; }}; supersede_autos '{g}'")
        assert r.returncode != 0 and "cannot list" in r.stderr and (g / "AUTO0722.SAV").read_bytes() == b"live-D", r
        # ... while a successful listing of an empty folder is success
        e = t / "empty"; e.mkdir()
        assert bash(f"supersede_autos '{e}'").returncode == 0
        # a missing game folder is a failure too
        assert bash(f"supersede_autos '{t / 'nope'}'").returncode != 0
        # new_game.sh aborts on that failure before launching (static check of the wiring)
        text = (ROOT / "harness" / "new_game.sh").read_text()
        assert text.index("supersede_autos") < text.index("$W ") and "exit 1" in text.split("supersede_autos")[1].split("\n")[0]
    print("test_new_game_sh_keeps_saves: all checks passed")


if __name__ == "__main__":
    main()
