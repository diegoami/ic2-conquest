#!/usr/bin/env python3
"""harness/environment.py and scripts/environment_check.py: fake commands, a fake user.reg. No Wine, no display.

python3 -m tests.test_environment
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from harness import environment as E  # noqa: E402
import environment_check as C  # noqa: E402

EXT = "[Software\\\\Wine\\\\Fonts\\\\External Fonts] 1\n"
REG = ("WINE REGISTRY Version 2\n\n"
       "[Software\\\\Wine\\\\Fonts] 1\n\"Foo\"=\"bar\"\n\n"
       + EXT + "#time=1\n"
       "\"DejaVu Sans (TrueType)\"=\"Z:\\\\usr\\\\share\\\\fonts\\\\dejavu.ttf\"\n"
       "\"@Droid Sans Fallback (TrueType)\"=\"Z:\\\\usr\\\\share\\\\fonts\\\\droid.ttf\"\n\n"
       "[Software\\\\Wine\\\\Fonts\\\\Replacements] 1\n\"MS Sans Serif\"=\"Tahoma\"\n\n"
       "[Software\\\\Wine\\\\Other] 1\n\"Secret\"=\"never-read\"\n")
FILES = "/usr/share/fonts/truetype/wine/tahoma.ttf\n/usr/share/fonts/dejavu/DejaVuSans.ttf\n"


def fake_run(files=FILES, match="DejaVu Sans", fail=()):
    def run(*args, env=None, timeout=10):
        if args[0] in fail:
            raise FileNotFoundError(args[0])
        if args[0] == "fc-match":
            return match
        if args[0] == "fc-list":
            return files.strip()
        if args[0] == "xdpyinfo":
            return "  dimensions:    1280x1024 pixels (338x270 millimeters)"
        return "wine-10.0 (fake)"
    return run


def make_prefix(tmp, reg=REG):
    p = Path(tmp)
    (p / "drive_c" / "IC2").mkdir(parents=True)
    (p / "drive_c" / "IC2" / "g.exe").write_bytes(b"exe")
    (p / "user.reg").write_text(reg)
    return p


def fp(prefix):
    E._cache.clear()
    return E.fingerprint(prefix, exe="g.exe", display=":9")


def main():
    ok = 0
    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run()):
        prefix = make_prefix(tmp)
        f = fp(prefix)
        assert f["wine"] == "wine-10.0 (fake)", f
        assert f["exe"]["name"] == "g.exe" and len(f["exe"]["sha256"]) == 64, f
        assert f["xvfb_screen"] == "1280x1024", f
        assert f["fonts"] == {"Book Antiqua": "DejaVu Sans", "MS Sans Serif": "DejaVu Sans", "liberation_count": 0,
                              "tahoma_wine": True}, f
        assert f["prefix_fonts"]["count"] == 3, f
        names = E.registry_font_names(REG)
        assert names == ["E:@Droid Sans Fallback (TrueType)", "E:DejaVu Sans (TrueType)", "R:MS Sans Serif=Tahoma"], names
        assert "never-read" not in json.dumps(f) and "usr" not in json.dumps(f["prefix_fonts"])
        ok += 1; print("PASS fields and registry font names")

        assert E.fingerprint(prefix, exe="g.exe") is E._cache[str(prefix)]        # cached per process
        assert fp(prefix) == f
        ok += 1; print("PASS cached and stable")

        added = REG.replace(EXT, EXT + "\"Liberation Sans (TrueType)\"=\"Z:\\\\y.ttf\"\n")
        (prefix / "user.reg").write_text(added)
        g = fp(prefix)
        assert g["prefix_fonts"]["sha256_12"] != f["prefix_fonts"]["sha256_12"] and g["prefix_fonts"]["count"] == 4, g
        ok += 1; print("PASS hash changes when a font is added")

        (prefix / "user.reg").write_text(REG)
        assert fp(prefix)["prefix_fonts"] == f["prefix_fonts"]
        ok += 1; print("PASS hash stable for the same names")

    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run(fail=("fc-match", "fc-list", "xdpyinfo"))):
        prefix = make_prefix(tmp)
        (prefix / "user.reg").unlink()
        f = fp(prefix)             # must not raise
        assert "error" in f["fonts"]["Book Antiqua"] and "error" in f["xvfb_screen"] and "error" in f["prefix_fonts"], f
        assert "error" in f["fonts"]["liberation_count"], f
        assert f["wine"] == "wine-10.0 (fake)" and len(f["exe"]["sha256"]) == 64      # the other probes still ran
        ok += 1; print("PASS failing probes are recorded, not raised")

    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run()):
        base = fp(make_prefix(tmp))
    assert C.diff(base, base) == []
    lib = FILES + "/usr/share/fonts/liberation/LiberationSans-Regular.ttf\n"
    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run(files=lib, match="Liberation Sans")):
        now = fp(make_prefix(tmp))
    lines = C.diff(base, now)
    text = "\n".join(lines)
    assert any('"Book Antiqua"' in x and "'DejaVu Sans'" in x and "'Liberation Sans'" in x for x in lines), text
    assert any("Liberation fonts" in x and "0" in x and "1" in x for x in lines), text
    assert len(lines) == 3, text           # also the MS Sans Serif match
    ok += 1; print("PASS baseline diff in plain words:\n  " + text.replace("\n", "\n  "))

    print(f"{ok} passed")


if __name__ == "__main__":
    main()
