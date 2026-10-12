#!/usr/bin/env python3
"""Offline test (no Wine) of harness/preserve.sh, the rule-6 helpers of harness/new_game.sh (review R1, R4): a rerun with the same
output name keeps the earlier output's bytes; a `superseded-<stamp>` folder that already exists with the same AUTO name is not reused or
overwritten; a failed preservation returns non-zero (new_game.sh then aborts before launching the game).
Run: python3 -m tests.test_new_game_sh_keeps_saves   (exit 1 on a failure)."""
import os
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
        # round 4 R3: a failure to move is injected (a stub `mv` first on PATH), so this holds for any UID (root included)
        (g / "AUTO0721.SAV").write_bytes(b"live-C")
        stub = t / "stubbin"; stub.mkdir(); (stub / "mv").write_text("#!/bin/sh\nexit 1\n"); (stub / "mv").chmod(0o755)
        r = subprocess.run(["bash", "-c", f". '{SH}'; supersede_autos '{g}'"], capture_output=True, text=True,
                           env={**os.environ, "PATH": f"{stub}:{os.environ['PATH']}"})
        assert r.returncode != 0 and "cannot move" in r.stderr and (g / "AUTO0721.SAV").read_bytes() == b"live-C", r
        (g / "AUTO0721.SAV").unlink()
        # round 4 R1: a listing that fails is NOT "nothing to preserve" (injected, so it does not depend on the UID)
        (g / "AUTO0722.SAV").write_bytes(b"live-D")
        r = bash(f"preserve_ls() {{ return 2; }}; supersede_autos '{g}'")
        assert r.returncode != 0 and "cannot list" in r.stderr and (g / "AUTO0722.SAV").read_bytes() == b"live-D", r
        # ... while a successful listing of an empty folder is success
        e = t / "empty"; e.mkdir()
        assert bash(f"supersede_autos '{e}'").returncode == 0
        # a missing game folder is a failure too
        assert bash(f"supersede_autos '{t / 'nope'}'").returncode != 0
        # the caller: run harness/new_game.sh with the game launch stubbed (fake wine/xdotool/wineserver, temp game folder)
        for fail in (True, False):
            w = t / f"w{int(fail)}"; G = w / "G"; G.mkdir(parents=True); bindir = w / "bin"; bindir.mkdir()
            (G / "AUTO0720.SAV").write_bytes(b"measured")
            (w / "env.sh").write_text(f'export IC2_WORK="{w}"\nG="{G}"\nW="{bindir}/wine"\n')
            (bindir / "wine").write_text(f'#!/bin/sh\necho launched >> "{w}/wine.called"\necho log > AUTOSAVE.LOG\necho new > AUTO0720.SAV\n')
            (bindir / "xdotool").write_text("#!/bin/sh\nexit 0\n")
            (bindir / "wineserver").write_text("#!/bin/sh\nexit 0\n")
            if fail: (bindir / "mv").write_text("#!/bin/sh\nexit 1\n")
            for f in bindir.iterdir(): f.chmod(0o755)
            r = subprocess.run(["bash", str(ROOT / "harness" / "new_game.sh"), "0", "out.SAV"], capture_output=True, text=True, timeout=120,
                               env={**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}", "IC2_ENV_SH": str(w / "env.sh"),
                                    "WINESERVER": str(bindir / "wineserver")})
            launched = (w / "wine.called").exists()
            if fail:
                assert r.returncode != 0 and not launched, ("launch happened or exit 0 although preservation failed", r)
                assert (G / "AUTO0720.SAV").read_bytes() == b"measured"
            else:
                assert r.returncode == 0 and launched, ("no launch although preservation succeeded", r)
                kept = [p.read_bytes() for d in G.glob("superseded-*") for p in d.iterdir()]
                assert kept == [b"measured"], kept
    print("test_new_game_sh_keeps_saves: all checks passed")


if __name__ == "__main__":
    main()
