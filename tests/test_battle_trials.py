#!/usr/bin/env python3
"""Offline dry run of the battle trial runner (`runs/experiments/battles/trials.py`) against a fake Game (no Wine, no X, no real kill).
Run: python3 -m tests.test_battle_trials   (exit 1 on a failure).

Checked: cells and L1 edits; one process per trial with the right lab exe and a kill by pid after each; trials.jsonl append-only with one line per
attempt; the sweep row and table; resumability (an ok trial is not run again; an errored trial is recorded and NOT retried unless
--redo-errors, which appends a new line); same seed twice compares identical and seed 1 v 2 differs; `keep` never overwrites.
"""
import json
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
import common as C  # noqa: E402
import trials as T  # noqa: E402
import stage  # noqa: E402
import harness.driver as D  # noqa: E402
from state import sav  # noqa: E402

SRC = ROOT / "saves" / "run0-start-AUTO0720-seed12345.SAV"


def fld_bytes():
    """A stand-in for FLD-RG: the tracked start save with army 0 at (86,28) with 2 moves and army 10 as Gaul's at (85,28) (raw edits, test only)."""
    b = bytearray(SRC.read_bytes())
    a0, a10 = stage._army(b, 0), stage._army(b, 10)
    struct.pack_into("<4h", b, a0, 86, 28, 0, 2)
    struct.pack_into("<4h", b, a10, 85, 28, 6, 0)
    return bytes(b)


class FakeGame:
    killed = []

    def __init__(self, fail_seed=None, offer=False):
        self.fail_seed, self.offer = fail_seed, offer
        self.exe, self.pid, self.opened, self.starts = None, 4242, None, 0

    def kill(self):
        FakeGame.killed.append(self.pid)

    def start(self):
        self.starts += 1

    def open(self, path):
        self.opened = Path(path)
        if self.fail_seed is not None and f"s{self.fail_seed}" in self.exe.replace(" lab s", "s"):
            raise D.DriverError("timeout waiting for map windows")
        return ["@ Bithynia wants to trade with Rome."]

    def army_state(self, i):
        return sav.parse(self.opened.read_bytes())["armies"][i]

    def select_army(self, i, x, y):
        pass

    def click_tile(self, x, y, pause=0):
        pass

    def in_battle(self):
        return True

    def find_windows(self, pat=".", visible=True):
        return [(1, "Rome  v  Gaul          Rome to place units.", 5, 99, 448, 414)]

    def popups(self):
        return []

    def shot(self, p, window="root"):
        pass

    def play_battle(self, shot=None, strict=False, on_dialog=None, max_clicks=120):
        seed = int(self.exe.split(" s")[-1].split(".")[0])
        for k in range(1, 4):
            (D.G / ("BATTLE%02d.SAV" % k)).write_bytes(self.opened.read_bytes() + bytes([seed, k]))
        d = [{"title": "Offer of peace", "text": "t", "answer": "No", "shot": "x.png"}] if self.offer else []
        return {"end_turn_clicks": 1, "battle_ended_text": "Gaul's army defeats Rome's army.", "dialogs": d}

    def save_as(self, name):
        b = bytearray(self.opened.read_bytes())
        stage.apply(b, [("units", 0, []), ("units", 10, [("hi", 1000 * (int(self.exe.split(" s")[-1].split(".")[0]) + 4), 6)])])
        p = D.G / name
        p.write_bytes(bytes(b))
        return p


def setup():
    root = Path(tempfile.mkdtemp())
    C.ART, C.DATA, D.G = root / "art", root / "data", root / "G"
    for d in (C.ART, C.DATA, D.G):
        d.mkdir()
    (C.ART / C.FLD_RG_NAME).write_bytes(fld_bytes())
    FakeGame.killed = []
    C.kill_stale = lambda g=None: ([g.kill()] if g else []) and [1]       # never pkill on a test machine; the fake records the kill
    D.time.sleep = lambda s: None
    return root


def lines():
    f = C.DATA / "trials.jsonl"
    return [json.loads(x) for x in f.read_text().splitlines()]


def test_cells():
    assert T.parse_cell("hi-hi-one") == ("hi", "hi", "one")
    ops = T.cell_ops("lc-ar-three")
    assert ops[0] == ("units", 0, [("lc", 7000, 6)] * 3) and ops[2] == ("units", 10, [("ar", 3500, 6)] * 3) and ops[1][2] == 65, ops
    assert T.cell_ops("li-hc-half")[0][2] == [("li", 7500, 6)] and T.cell_ops("li-hc-half")[2][2] == [("hc", 1250, 6)]
    assert T.parse_cell("hi-li-half-three") == ("hi", "li", "half-three")      # the size matrix: attacker half, defender three
    mo = T.cell_ops("hi-li-half-three")
    assert mo[0][2] == [("hi", 3000, 6)] and mo[2][2] == [("li", 15000, 6)] * 3, mo
    for bad in ("hi-hi", "xx-hi-one", "hi-hi-two", "hi-hi-one-two", "hi-hi-one-half-three"):
        try:
            T.parse_cell(bad)
        except ValueError:
            continue
        raise AssertionError(bad)


def test_dry_run_resume_errors_and_compare():
    setup()
    log = C.Log("t")
    log.txt, log.jl = C.DATA / "x.log", C.DATA / "x.jsonl"
    mk = lambda: FakeGame()
    n_ok, n_err = T.run_all(["hi-hi-one"], [1, 2], [1, 2], make_game=mk, log=log, shot=False)
    assert (n_ok, n_err) == (4, 0)
    ls = lines()
    assert [r["trial"] for r in ls] == ["hi-hi-one_s1_r1", "hi-hi-one_s1_r2", "hi-hi-one_s2_r1", "hi-hi-one_s2_r2"] and all(r["status"] == "ok" for r in ls)
    r = ls[0]
    assert r["half_rounds"] == 3 and r["exe"] == "Imperial Conquest 2 lab s1.exe" and r["winner"] == "defender" and r["end_turn_clicks"] == 1, r
    assert r["defender_result"]["troops_after"] == 5000 and r["attacker_result"]["destroyed"] and "level" in r
    assert len(FakeGame.killed) >= 4, "a kill after every trial"
    # the table
    out, n = T.write_table()
    rows = out.read_text().splitlines()
    assert n == 4 and len(rows) == 5 and rows[0].split(",") == T.COLUMNS, rows[:2]
    import csv as _csv
    r0 = next(_csv.DictReader(out.open()))
    assert r0["build"] == "lab" and r0["level"].startswith("L1"), (r0["build"], r0["level"])
    # resume: nothing new is run, the file is untouched
    before = (C.DATA / "trials.jsonl").read_text()
    assert T.run_all(["hi-hi-one"], [1, 2], [1, 2], make_game=mk, log=log, shot=False) == (0, 0)
    assert (C.DATA / "trials.jsonl").read_text() == before
    # compare: same seed twice identical, seed 1 v 2 differs
    same, other = T.compare("hi-hi-one_s1_r1", "hi-hi-one_s1_r2"), T.compare("hi-hi-one_s1_r1", "hi-hi-one_s2_r1")
    assert same["series_identical"] and same["post_identical"] and same["aligned"] == 3, same
    assert not other["series_identical"] and not other["post_identical"], other


def test_error_recorded_not_retried_silently():
    setup()
    log = C.Log("t")
    log.txt, log.jl = C.DATA / "x.log", C.DATA / "x.jsonl"
    mk = lambda: FakeGame(fail_seed=2)
    assert T.run_all(["hi-hi-one"], [1, 2, 3], [1], make_game=mk, log=log, shot=False) == (2, 1)
    ls = lines()
    assert [r["status"] for r in ls] == ["ok", "error", "ok"] and "timeout" in ls[1]["error"] and ls[1]["attempt"] == 1, ls[1]
    first = (C.DATA / "trials.jsonl").read_text()
    assert T.run_all(["hi-hi-one"], [1, 2, 3], [1], make_game=mk, log=log, shot=False) == (0, 0), "an errored trial is skipped on resume"
    assert (C.DATA / "trials.jsonl").read_text() == first
    assert T.run_all(["hi-hi-one"], [2], [1], redo_errors=True, make_game=lambda: FakeGame(), log=log, shot=False) == (1, 0)
    ls = lines()
    assert ls[:3] == [json.loads(x) for x in first.splitlines()] and ls[3]["status"] == "ok" and ls[3]["attempt"] == 2, "append-only: old lines untouched"


def test_stop_on_error_and_dialog_recorded():
    setup()
    log = C.Log("t")
    log.txt, log.jl = C.DATA / "x.log", C.DATA / "x.jsonl"
    assert T.run_all(["hi-hi-one"], [1, 2, 3], [1], stop_on_error=True, make_game=lambda: FakeGame(fail_seed=1), log=log, shot=False) == (0, 1)
    assert len(lines()) == 1
    setup()
    T.run_all(["hi-hi-one"], [1], [1], make_game=lambda: FakeGame(offer=True), log=log, shot=False)
    r = lines()[0]
    assert r["dialog"] == "Offer of peace" and "DECLINED" in r["dialog_note"], r


def test_end_condition_from_both_destroyed_flags():
    c = T.END_CONDITIONS
    assert c[(False, False)].startswith("none") and c[(True, True)] == "both destroyed"
    assert c[(True, False)].endswith("attacker") and c[(False, True)].endswith("defender")


def test_every_writer_survives_a_second_call_in_the_same_stamp():
    """Rule 6: each measured-output writer, called twice in the same STAMP (same second), leaves both files."""
    import halflog
    root = setup()
    C.STAMP = "20990101-000000"
    log = C.Log("t")
    log.txt, log.jl = C.DATA / "x.log", C.DATA / "x.jsonl"
    T.run_all(["hi-hi-one"], [1, 2], [1], make_game=lambda: FakeGame(), log=log, shot=False)
    # sweep table (trials.py table), compare (trials.py compare via write_new), write_new itself, halflog
    t1, _ = T.write_table()
    t2, _ = T.write_table()
    assert t1 != t2 and t1.exists() and t2.exists() and t1.read_text() == t2.read_text()
    a = C.write_new(C.DATA, "compare-x-y-%s.json" % C.STAMP, '{"n": 1}')
    b = C.write_new(C.DATA, "compare-x-y-%s.json" % C.STAMP, '{"n": 2}')
    c = C.write_new(C.DATA, "compare-x-y-%s.json" % C.STAMP, b"3")
    assert len({a, b, c}) == 3 and a.read_text() == '{"n": 1}' and b.read_text() == '{"n": 2}' and c.read_bytes() == b"3"
    tr = {r["trial"]: r for r in T.read_trials() if r.get("status") == "ok"}["hi-hi-one_s1_r1"]
    # the fake series files hold no battle block: write the log from the REAL decoder on a synthetic block save
    from state import battle_block as BB
    raw, o = __import__("tests.test_battle_stage", fromlist=["x"]).battle_save()
    names = []
    for k in range(2):
        (C.ART / ("hl_BATTLE0%d.SAV" % (k + 1))).write_bytes(raw)
        names.append("hl_BATTLE0%d.SAV" % (k + 1))
    p1, _ = halflog.write_halflog("hl", names)
    p2, _ = halflog.write_halflog("hl", names)
    p3, _ = halflog.write_halflog("hl", names)
    assert len({p1, p2, p3}) == 3 and all(p.exists() for p in (p1, p2, p3))
    # the screenshot keeper and the SAVES.sha256 recorder
    f = root / "s.png"
    f.write_bytes(b"1")
    g = root / "s2.png"
    g.write_bytes(b"2")
    k1, k2 = C.keep(f, "shot.png"), C.keep(g, "shot.png")
    assert k1 != k2 and k1.read_bytes() == b"1" and k2.read_bytes() == b"2"


def test_keep_never_overwrites():
    root = setup()
    a, b = root / "a.SAV", root / "b.SAV"
    a.write_bytes(b"one")
    b.write_bytes(b"two")
    k1, k2, k3 = C.keep(a, "X.SAV"), C.keep(b, "X.SAV"), C.keep(a, "X.SAV")
    assert k1.name == "X.SAV" and k2.name != "X.SAV" and k1.read_bytes() == b"one" and k2.read_bytes() == b"two" and k3 == k1
    assert (C.DATA / "SAVES.sha256").read_text().count("\n") == 2


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as e:      # noqa: BLE001
                import traceback
                traceback.print_exc()
                fails += 1
                print("FAIL", name, type(e).__name__, e)
    sys.exit(1 if fails else 0)
