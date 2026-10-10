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
from harness import driver  # noqa: E402

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
        assert "error" in f["wine"] and "error" in f["fonts"]["Book Antiqua"], f
        # the worst case: every probe hangs (commands and file reads alike): the whole fingerprint is back under 1 s
        def hang(*a, **k):
            time.sleep(5)
        with mock.patch.object(E, "_run", hang), mock.patch.object(E, "exe_sha256", hang), mock.patch.object(E, "registry_fonts_hash", hang):
            E._cache.clear()
            t = time.time()
            f = E.fingerprint(prefix, exe="g.exe", display=":9")
            worst = time.time() - t
        assert worst < 1.0 and "error" in f["wine"] and "error" in f["exe"]["sha256"] and "error" in f["prefix_fonts"] \
            and "error" in f["fonts"]["liberation_count"], (worst, f)
        ok += 1; print("PASS all probes hanging: fingerprint back in %.2f s (< 1 s)" % worst)
        ok += 1; print("PASS slow probe bounded (%.2f s) and recorded; spent budget skips probes" % took)

    # R1: the record reaches environment.jsonl, a runner's sink (its own log), and self.log once per process
    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run()):
        prefix = make_prefix(Path(tmp) / "p")
        jsonl = Path(tmp) / "environment.jsonl"
        got, logged = [], []
        E._sinks.clear(); E._keyed.clear(); E._logged.clear(); E._cache.clear()
        E.add_sink(got.append)
        E.record_start(prefix, "g.exe", ":9", prefix / "drive_c" / "IC2", 4242, jsonl, logged.append)
        E.record_start(prefix, "g.exe", ":9", prefix / "drive_c" / "IC2", 4243, jsonl, logged.append)
        lines = [json.loads(x) for x in jsonl.read_text().splitlines()]
        assert [r["pid"] for r in lines] == [4242, 4243] and lines[0]["step"] == "environment", lines     # every start, append only
        assert lines[0]["argv0"] and lines[0]["cwd"] and lines[0]["environment"]["wine"] == "wine-10.0 (fake)", lines[0]
        assert len(got) == 2 and len(logged) == 2 and logged[0].startswith("environment {"), (got, logged)   # one line per game process
        assert E.sink_line(got[0]).startswith("environment {") and '"step"' not in E.sink_line(got[0])
        ok += 1; print("PASS record in environment.jsonl (each start), sink (runner log), self.log (once per game process)")

        # R2: any start records, by pid assignment: an override, a nested super().start(), a start replaced by assignment
        class Plain(driver.Game):
            def start(self):
                self.pid = 1
        class Hooked(Plain):
            def start(self):
                super().start()
        def patched(self):
            self.pid = 1
        for cls, start in ((driver.Game, patched), (Plain, None), (Hooked, None)):
            saved = driver.Game.start
            if start:
                driver.Game.start = start            # what a finished data script does: `Game.start = start`
            try:
                with mock.patch.object(driver.Game, "_is_game_process", staticmethod(lambda pid: True)):
                    g = cls.__new__(cls)
                    g.exe, g.log = "g.exe", logged.append
                    g.__dict__["_pid"] = None
                    seen = []
                    g.record_environment = lambda: seen.append(g.pid)
                    g.start()
                    assert seen == [1], (cls, seen)
                    g.pid = None; g.start()
                    assert seen == [1, 1], (cls, seen)          # a restart records again
            finally:
                driver.Game.start = saved
        with mock.patch.object(driver.Game, "_is_game_process", staticmethod(lambda pid: False)):
            g = Plain.__new__(Plain); g.__dict__["_pid"] = None
            seen = []
            g.record_environment = lambda: seen.append(1)
            g.start()
            assert seen == [], "a fake pid (no game process) must not write the durable record"
        ok += 1; print("PASS every start records (override, nested, monkeypatched by assignment); fake pids do not")

    # R2 (round 3): two restarts in one Python process, through the real Game.pid hook: every game process logs and reaches the sinks

    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run()), \
            mock.patch.object(driver, "WORK", Path(tmp)), mock.patch.object(driver, "PREFIX", make_prefix(Path(tmp) / "p")), \
            mock.patch.object(driver.Game, "_is_game_process", staticmethod(lambda pid: True)):
        E._sinks.clear(); E._keyed.clear(); E._logged.clear(); E._cache.clear()
        sunk, lines = [], []
        E.add_sink(sunk.append)
        g = driver.Game.__new__(driver.Game)
        g.exe, g.log, g.environment = "g.exe", lines.append, None
        g.__dict__["_pid"] = None
        for pid in (101, None, 102):
            g.pid = pid
        assert [r["pid"] for r in sunk] == [101, 102], sunk
        assert len([x for x in lines if x.startswith("environment {")]) == 2, lines
        assert [json.loads(x)["pid"] for x in (Path(tmp) / "environment.jsonl").read_text().splitlines()] == [101, 102]
        ok += 1; print("PASS two restarts in one process: self.log, sink, and environment.jsonl each get both")
        E._sinks.clear(); E._keyed.clear()

    # round 5: the tracked data folder of a runner, by script location
    repo = Path("/r")
    cases = {"/r/runs/experiments/data/run-exp-peace-radio/peace_radio.py": "/r/runs/experiments/data/run-exp-peace-radio",
             "/r/runs/experiments/pair2/trials.py": "/r/runs/experiments/data/run-exp-pair2",
             "/r/runs/experiments/feature_inventory/explore_lib.py": "/r/runs/experiments/data/run-exp-feature-inventory",
             "/r/runs/experiments/end_of_game/run_two.py": "/r/runs/experiments/data/run-exp-end-of-game",
             "/r/runs/experiments/fleet-battles/trials.py": "/r/runs/experiments/data/run-exp-naval-battle",
             "/r/runs/experiments/battles/b0_probe.py": "/r/runs/experiments/data/run-exp-battle-sweep",
             "/r/runs/experiments/unit-map-mouse/common.py": "/r/runs/experiments/data/run-exp-unitmap-mouse",
             "/r/runs/experiments/gallic-army.py": "/r/runs/experiments/gallic-army",
             "/r/runs/run0/play.py": "/r/runs/run0",
             "/r/tests/test_orders.py": None, "/r/scripts/x.py": None, "/elsewhere/runs/experiments/pair2/t.py": None,
             "/r/runs/experiments/data/loose.py": None}
    for script, want in cases.items():
        got = E.data_folder(script, repo)
        assert (str(got) if got else None) == want, (script, got, want)
    ok += 1; print("PASS data_folder: tracked folder chosen by script location (%d cases)" % len(cases))

    # the default sink: a record lands in the runner's tracked environment.jsonl (append only), the override wins, tests/ get none
    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run()):
        prefix = make_prefix(Path(tmp) / "p")
        fake_repo = Path(tmp) / "repo"
        script = fake_repo / "runs" / "experiments" / "pair2" / "trials.py"
        script.parent.mkdir(parents=True)
        script.write_text("")
        E._sinks.clear(); E._keyed.clear(); E._logged.clear(); E._cache.clear()
        args = (prefix, "g.exe", ":9", prefix / "drive_c" / "IC2")
        with mock.patch.object(E, "REPO", fake_repo), mock.patch.object(sys, "argv", [str(script)]):
            E.record_start(*args, 1, Path(tmp) / "m.jsonl", lambda x: None)
            E.record_start(*args, 2, Path(tmp) / "m.jsonl", lambda x: None)
            tracked = fake_repo / "runs" / "experiments" / "data" / "run-exp-pair2" / "environment.jsonl"
            assert [json.loads(x)["pid"] for x in tracked.read_text().splitlines()] == [1, 2]
            E.set_data_folder(fake_repo / "runs" / "experiments" / "data" / "run-exp-other")
            E.record_start(*args, 3, Path(tmp) / "m.jsonl", lambda x: None)
            E._override[0] = None
            assert (fake_repo / "runs" / "experiments" / "data" / "run-exp-other" / "environment.jsonl").exists()
            assert len(tracked.read_text().splitlines()) == 2
        with mock.patch.object(E, "REPO", fake_repo), mock.patch.object(sys, "argv", [str(fake_repo / "tests" / "t.py")]):
            before = sorted(fake_repo.rglob("environment.jsonl"))
            E.record_start(*args, 4, Path(tmp) / "m.jsonl", lambda x: None)
            assert sorted(fake_repo.rglob("environment.jsonl")) == before
        ok += 1; print("PASS default sink: tracked environment.jsonl per runner (append), override honoured, tests/ none")

    # R1 (b): a runner library that owns a log gets the record there (battles.common.Log; keyed, so a new Log replaces the old sink)
    sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
    import common as BC
    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(E, "_run", fake_run()):
        prefix = make_prefix(Path(tmp) / "p")
        E._sinks.clear(); E._keyed.clear(); E._logged.clear(); E._cache.clear()
        old = BC.Log("t1", Path(tmp) / "d")
        new = BC.Log("t2", Path(tmp) / "d")
        E.record_start(prefix, "g.exe", ":9", prefix / "drive_c" / "IC2", 7, Path(tmp) / "e.jsonl", lambda x: None)
        ev = [json.loads(x) for x in new.jl.read_text().splitlines()]
        assert [e["event"] for e in ev] == ["environment"] and ev[0]["pid"] == 7 and "wine" in ev[0]["environment"], ev
        assert old.jl.read_text() == "", "the replaced Log must not get the record"
        ok += 1; print("PASS battles.common.Log gets the environment event (keyed sink)")
        E._keyed.clear()

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
