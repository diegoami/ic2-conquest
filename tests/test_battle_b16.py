#!/usr/bin/env python3
"""Offline tests of the B16 tooling (`runs/experiments/battles/b16_run.py`, `b16_analyze.py`, `stage.py` ncities). No Wine, no X.
Run: python3 -m tests.test_battle_b16   (exit 1 on a failure).

  - `strategic` / `rcode` on a synthetic game-memory snapshot built from the tracked start save: unity, cities, per-nation army strength and the three
    [R-code] tests come out as the save's own values; a doctored winner/loser flips the tests as the report's condition says.
  - `stage.apply(("ncities", n, v))` changes only nation n's +0x446 word.
  - `diff_offsets` finds exactly the bytes that differ; `save_diff` reports a relation edit as exactly two fields.
  - A trial record's `pre_answer` identity: two equal snapshots compare equal byte for byte, one flipped byte is found at its address.
"""
import gzip
import os
import struct
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("IC2_WORK", tempfile.mkdtemp())
os.environ.setdefault("DISPLAY_IC2", ":640")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
import b16_analyze as A  # noqa: E402
import b16_run as R  # noqa: E402
import stage  # noqa: E402
from state import sav  # noqa: E402

SRC = ROOT / "saves" / "run0-start-AUTO0720-seed12345.SAV"
D = R.D


def memory_from(b):
    """A fake 0x45E030..0x4A0B80 snapshot holding the save's nation and army tables at the game's addresses."""
    snap = bytearray(R.SNAP_END - R.SNAP_BASE)
    o = stage._offsets(b)
    for n in range(16):
        a = o["nation0"] + n * sav.NATION_LEN
        snap[D.NATIONS - R.SNAP_BASE + n * D.NATION_LEN:D.NATIONS - R.SNAP_BASE + (n + 1) * D.NATION_LEN] = b[a:a + sav.NATION_LEN]
    for i in range(o["na"]):
        a = o["army0"] + i * sav.ARMY_LEN
        snap[D.ARMIES - R.SNAP_BASE + i * D.ARMY_LEN:D.ARMIES - R.SNAP_BASE + (i + 1) * D.ARMY_LEN] = b[a:a + sav.ARMY_LEN]
    return bytes(snap)


def test_strategic_reads_the_saves_own_values():
    b = SRC.read_bytes()
    s = sav.load(str(SRC))
    st = R.strategic(memory_from(b))
    for n in (0, 6):
        N = s["nations"][n]
        assert st["nations"][n]["unity"] == N["unity"] and st["nations"][n]["cities"] == N["cities_count"], (n, st["nations"][n])
    want = {n: sum(sav.field_strength(a) for a in s["armies"] if a["owner"] == n and a["troops"] > 0) for n in (0, 6)}
    assert st["armies_sum"] == want, (st["armies_sum"], want)


def test_rcode_tests():
    st = {"winner": 6, "armies_sum": {0: 30000, 6: 12000}, "nations": {0: {"unity": 856, "cities": 30}, 6: {"unity": 400, "cities": 23}}}
    r = R.rcode(st)
    assert r["loser"] == 0 and r["armies_W_lt_L"] and r["unity_L_gt_500"] and r["cities_L_gt_7"] and r["preconditions_pass"], r
    st["nations"][0]["unity"] = 500                      # strictly above 500
    assert not R.rcode(st)["unity_L_gt_500"] and not R.rcode(st)["preconditions_pass"]
    st["nations"][0].update({"unity": 856, "cities": 7})
    assert not R.rcode(st)["cities_L_gt_7"]
    st["nations"][0]["cities"] = 8
    st["armies_sum"] = {0: 12000, 6: 12000}              # not strictly weaker
    assert not R.rcode(st)["armies_W_lt_L"]
    st = {"winner": 0, "armies_sum": {0: 44000, 6: 0}, "nations": {0: {"unity": 881, "cities": 30}, 6: {"unity": 377, "cities": 23}}}
    r = R.rcode(st)
    assert r["loser"] == 6 and not r["preconditions_pass"], r


def test_ncities_edits_only_its_word():
    b0 = bytearray(SRC.read_bytes())
    b1 = stage.apply(bytearray(b0), [("ncities", 0, 7)])
    diff = [i for i in range(len(b0)) if b0[i] != b1[i]]
    base = stage._offsets(b0)["nation0"] + 0x446
    assert diff and all(base <= i < base + 2 for i in diff), diff
    assert sav.parse(bytes(b1))["nations"][0]["cities_count"] == 7


def test_owner_edits_only_the_owner_word():
    b0 = bytearray(SRC.read_bytes())
    b1 = stage.apply(bytearray(b0), [("owner", 1, 6)])
    diff = [i for i in range(len(b0)) if b0[i] != b1[i]]
    base = stage._army(b0, 1) + 4
    assert diff and all(base <= i < base + 2 for i in diff), diff
    assert sav.parse(bytes(b1))["armies"][1]["owner"] == 6


def test_diff_offsets_and_snapshot_identity():
    a = bytes(1000)
    assert A.diff_offsets(a, a)["differing_bytes"] == 0
    c = bytearray(a)
    c[10] = 1
    c[500:503] = b"\1\1\1"
    d = A.diff_offsets(a, bytes(c))
    assert d["differing_bytes"] == 4 and d["runs"] == [(hex(R.SNAP_BASE + 10), 1), (hex(R.SNAP_BASE + 500), 3)], d


def test_save_diff_reports_a_relation_edit_as_two_fields():
    d = Path(tempfile.mkdtemp())
    b = stage.apply(bytearray(SRC.read_bytes()), [("relation", 0, 6, 0)])
    (d / "a.SAV").write_bytes(SRC.read_bytes())
    (d / "b.SAV").write_bytes(bytes(b))
    r = A.save_diff(d / "a.SAV", d / "b.SAV")
    paths = [f[0] for f in r["fields"]]
    assert r["raw_bytes_differing"] > 0 and sorted(paths) == ["nations[0].relations.Gaul", "nations[6].relations.Rome"], r


# ---- R3: processes are killed by ownership, never by pattern ----------------------------------------------------------------------------
def _fake_proc(entries):
    """entries: {pid: (ppid, cmdline, environ dict)} written as a /proc-like tree."""
    root = Path(tempfile.mkdtemp())
    for pid, (ppid, cmd, env) in entries.items():
        d = root / str(pid)
        d.mkdir()
        (d / "status").write_text("Name:\tx\nPPid:\t%d\n" % ppid)
        (d / "cmdline").write_bytes(cmd.encode() + b"\0")
        (d / "environ").write_bytes(b"\0".join(("%s=%s" % kv).encode() for kv in env.items()) + b"\0")
    return root


MINE = {"DISPLAY": ":640", "WINEPREFIX": str(R.D.PREFIX)}


def test_descendants_follow_the_ppid_tree_only():
    import b16_common as BC
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE), 102: (101, "child", MINE),
                       200: (1, "Imperial Conquest 2 fast.exe", MINE), 201: (200, "child", MINE), 300: (1, "bash", {})})
    assert sorted(BC.descendants(100, root)) == [100, 101, 102], BC.descendants(100, root)


def test_stop_kills_only_the_launched_tree_never_a_matching_foreign_process():
    import b16_common as BC
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE),
                       200: (1, "Imperial Conquest 2 fast.exe", MINE), 201: (200, "Imperial Conquest 2 fast.exe", {"DISPLAY": ":640"})})
    g = BC.PeaceGame(exe="x")
    g.PROC = str(root)
    g.owned = [100, 101]

    class P:
        pid = 100

        def wait(self, timeout=None):
            return 0
    g.popen = P()
    killed = []
    old = (BC.os.kill, BC.time.sleep)
    BC.os.kill, BC.time.sleep = (lambda pid, sig: killed.append(pid)), (lambda s: None)
    try:
        done = g.stop()
    finally:
        BC.os.kill, BC.time.sleep = old
    assert sorted(killed) == [100, 101] and sorted(done) == [100, 101] and 200 not in killed and 201 not in killed, (killed, done)


def test_start_refuses_an_occupied_display_without_launching_or_killing():
    import b16_common as BC
    root = _fake_proc({200: (1, "Imperial Conquest 2 fast.exe", MINE)})
    g = BC.PeaceGame(exe="x")
    g.PROC = str(root)
    launched, killed = [], []
    old = (BC.subprocess.Popen, BC.os.kill)
    BC.subprocess.Popen, BC.os.kill = (lambda *a, **k: launched.append(a)), (lambda pid, sig: killed.append(pid))
    try:
        try:
            g.start()
        except R.D.DriverError as e:
            assert "refusing to start" in str(e) and "200" in str(e), e
        else:
            raise AssertionError("start did not refuse")
    finally:
        BC.subprocess.Popen, BC.os.kill = old
    assert launched == [] and killed == [], (launched, killed)


def test_no_script_of_the_branch_kills_or_adopts_by_pattern():
    import re as _re
    bad = _re.compile(r"pkill|killall|pgrep|wineserver\s*-k|wineserver\", \"-k|\"-k\"\]")
    hits = []
    for f in sorted((ROOT / "runs" / "experiments" / "battles").glob("b16_*.py")) + [ROOT / "tests" / "test_battle_b16.py"]:
        for n, line in enumerate(f.read_text().splitlines(), 1):
            code = line.split("#")[0]
            if f.name != "test_battle_b16.py" and bad.search(code):
                hits.append((f.name, n, line.strip()))
    assert not hits, hits


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as e:      # noqa: BLE001
                fails += 1
                print("FAIL", name, type(e).__name__, e)
    sys.exit(1 if fails else 0)
