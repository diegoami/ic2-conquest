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

        calls = []
        real = E._run
        with mock.patch.object(E, "_run", lambda *x, **k: calls.append(x) or real(*x, **k)):
            E._cache.clear()
            first = E.fingerprint(prefix, exe="g.exe", display=":9")
            n = len(calls)
            assert n >= 4, n
            assert E.fingerprint(prefix, exe="g.exe", display=":9") is first and len(calls) == n   # cached: no probe ran again
            other = E.fingerprint(prefix, exe="g.exe", display=":10")                              # R5: another display, fresh
            assert len(calls) > n and other is not first
            n = len(calls)
            (prefix / "drive_c" / "IC2" / "h.exe").write_bytes(b"other")
            third = E.fingerprint(prefix, exe="h.exe", display=":9")                               # R5: another exe, fresh
            assert len(calls) > n and third["exe"]["sha256"] != first["exe"]["sha256"]
        ok += 1; print("PASS cached per (prefix, exe, display): no probe on a repeat, fresh for another exe or display")

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

    # R4: an error text carries no absolute path or home directory
    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run()):
        prefix = make_prefix(tmp)
        (prefix / "user.reg").unlink()
        err = fp(prefix)["prefix_fonts"]["error"]
        assert tmp not in err and str(Path.home()) not in err and "<path>" in err, err
        assert "/" not in E.sanitize(f"x {Path.home()}/a/b and /etc/y: z"), E.sanitize("x")
        ok += 1; print("PASS error text sanitised:", err)

    # R3: a slow probe is bounded and recorded as an error; the whole fingerprint stays under the budget
    import os, stat, time
    with tempfile.TemporaryDirectory() as tmp:
        slow = Path(tmp) / "slowwine"
        slow.write_text("#!/bin/sh\nsleep 5\n")
        slow.chmod(slow.stat().st_mode | stat.S_IEXEC)
        prefix = make_prefix(Path(tmp) / "p")
        with mock.patch.object(E, "WINE", str(slow)), mock.patch.object(E, "PROBE_TIMEOUT", 0.3):
            E._cache.clear()
            t = time.time()
            f = E.fingerprint(prefix, exe="g.exe", display=":9")
            took = time.time() - t
        assert took < 2.5 and "error" in f["wine"] and "Timeout" in f["wine"]["error"], (took, f["wine"])
        assert tmp not in f["wine"]["error"]
        with mock.patch.object(E, "BUDGET", 0.0):
            f = fp(prefix)
        assert "budget" in f["wine"]["error"] and "budget" in f["fonts"]["Book Antiqua"]["error"], f
        ok += 1; print("PASS slow probe bounded (%.2f s) and recorded; spent budget skips probes" % took)

    # R1: the record reaches environment.jsonl, a runner's sink (its own log), and self.log once per process
    from harness import driver
    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run()):
        prefix = make_prefix(Path(tmp) / "p")
        jsonl = Path(tmp) / "environment.jsonl"
        got, logged = [], []
        E._sinks.clear(); E._logged.clear(); E._cache.clear()
        E.add_sink(got.append)
        E.record_start(prefix, "g.exe", ":9", prefix / "drive_c" / "IC2", 4242, jsonl, logged.append)
        E.record_start(prefix, "g.exe", ":9", prefix / "drive_c" / "IC2", 4243, jsonl, logged.append)
        lines = [json.loads(x) for x in jsonl.read_text().splitlines()]
        assert [r["pid"] for r in lines] == [4242, 4243] and lines[0]["step"] == "environment", lines     # every start, append only
        assert lines[0]["argv0"] and lines[0]["cwd"] and lines[0]["environment"]["wine"] == "wine-10.0 (fake)", lines[0]
        assert len(got) == 2 and len(logged) == 1 and logged[0].startswith("environment {"), (got, logged)
        assert E.sink_line(got[0]).startswith("environment {") and '"step"' not in E.sink_line(got[0])
        ok += 1; print("PASS record in environment.jsonl (each start), sink (runner log), self.log (once)")

        # R2: every start override is wrapped, nested super().start() records once
        class Plain(driver.Game):
            def start(self):
                self.pid = 1
        class Hooked(Plain):
            def start(self):
                super().start()
        for cls in (Plain, Hooked):
            g = cls.__new__(cls)
            g.exe, g.pid, g.log = "g.exe", None, logged.append
            seen = []
            g.record_environment = lambda: seen.append(g.pid)
            g.start()
            assert seen == [1], (cls, seen)
        ok += 1; print("PASS Game subclasses' start() overrides record once, after the game runs")

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
