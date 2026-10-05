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


# ---- R3: processes are killed by identity (pid + start time), never by pattern or by a remembered pid alone -------------------------------
def _fake_proc(entries):
    """entries: {pid: (ppid, cmdline, environ dict[, start time])} written as a /proc-like tree (status, cmdline, environ, stat)."""
    root = Path(tempfile.mkdtemp())
    for pid, e in entries.items():
        ppid, cmd, env = e[:3]
        start = e[3] if len(e) > 3 else 1000 + pid
        _write_proc(root, pid, ppid, cmd, env, start)
    return root


def _write_proc(root, pid, ppid, cmd, env, start):
    d = root / str(pid)
    d.mkdir(exist_ok=True)
    (d / "status").write_text("Name:\tx\nPPid:\t%d\n" % ppid)
    (d / "cmdline").write_bytes(cmd.encode() + b"\0")
    (d / "environ").write_bytes(b"\0".join(("%s=%s" % kv).encode() for kv in env.items()) + b"\0")
    # field 22 = starttime; the command name holds a space and a ')' on purpose
    (d / "stat").write_text("%d (wine pre) loader) S %d 1 1 0 -1 4194560 100 0 0 0 1 1 0 0 20 0 1 0 %d 1000 100 18446744073709551615\n" % (pid, ppid, start))


MINE = {"DISPLAY": ":640", "WINEPREFIX": str(R.D.PREFIX)}


class FakeOwner:
    """A PeaceGame wired to a fake /proc whose signals are recorded instead of sent."""

    def __init__(self, root, owned, popen_pid):
        import b16_common as BC
        self.BC = BC
        self.g = BC.PeaceGame(exe="x")
        self.g.PROC = str(root)
        self.g.owned = owned
        self.signalled = []
        self.g._pidfd = lambda pid: None
        self.g._send = lambda pid, fd: self.signalled.append(pid)

        class P:
            pid = popen_pid

            def wait(self, timeout=None):
                return 0
        self.g.popen = P()

    def stop(self):
        old = self.BC.time.sleep
        self.BC.time.sleep = lambda s: None
        try:
            return self.g.stop()
        finally:
            self.BC.time.sleep = old


def test_descendants_follow_the_ppid_tree_only():
    import b16_common as BC
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE), 102: (101, "child", MINE),
                       200: (1, "Imperial Conquest 2 fast.exe", MINE), 201: (200, "child", MINE), 300: (1, "bash", {})})
    assert sorted(BC.descendants(100, root)) == [100, 101, 102], BC.descendants(100, root)


def test_proc_start_reads_field_22_even_with_a_paren_in_the_name():
    import b16_common as BC
    root = _fake_proc({100: (1, "wine", MINE, 4242)})
    assert BC.proc_start(100, root) == 4242 and BC.proc_start(999, root) is None


def test_stop_kills_only_the_launched_tree_never_a_matching_foreign_process():
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE),
                       200: (1, "Imperial Conquest 2 fast.exe", MINE), 201: (200, "Imperial Conquest 2 fast.exe", {"DISPLAY": ":640"})})
    f = FakeOwner(root, [(100, 1100), (101, 1101)], 100)
    done = f.stop()
    assert sorted(f.signalled) == [100, 101] and sorted(p for p, _ in done) == [100, 101] and 200 not in f.signalled and 201 not in f.signalled, (f.signalled, done)


def test_a_recycled_owned_pid_and_its_foreign_children_are_never_signalled():
    """Between discovery and stop() the owned child 101 exits and a FOREIGN process takes its pid (new start time) and has foreign children; the launcher 100 is intact."""
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE), 102: (101, "child", MINE)})
    f = FakeOwner(root, [(100, 1100), (101, 1101), (102, 1102)], 100)
    import shutil
    shutil.rmtree(root / "102")
    _write_proc(root, 101, 1, "foreign-editor", {"DISPLAY": ":0"}, 999999)          # pid 101 reused by a foreign process
    _write_proc(root, 150, 101, "foreign-child", {"DISPLAY": ":0"}, 999998)         # with a foreign child
    done = f.stop()
    assert sorted(f.signalled) == [100], f.signalled
    assert 101 not in f.signalled and 150 not in f.signalled and 102 not in f.signalled, f.signalled
    assert {p for p, _ in f.g.skipped} >= {101, 102}, f.g.skipped
    assert [p for p, _ in done] == [100], done


def test_a_recycled_launcher_pid_pulls_no_foreign_tree_into_cleanup():
    """The launcher pid 100 is replaced by a foreign process (new start time) with foreign children; the owned child 101 is gone. Nothing is signalled."""
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE)})
    f = FakeOwner(root, [(100, 1100), (101, 1101)], 100)
    import shutil
    shutil.rmtree(root / "101")
    _write_proc(root, 100, 1, "foreign-service", {"DISPLAY": ":0"}, 777777)
    _write_proc(root, 160, 100, "foreign-child", {"DISPLAY": ":0"}, 777778)
    _write_proc(root, 161, 160, "foreign-grandchild", {"DISPLAY": ":0"}, 777779)
    done = f.stop()
    assert f.signalled == [] and done == [] and {p for p, _ in f.g.skipped} >= {100, 101}, (f.signalled, done, f.g.skipped)


def test_identity_is_rechecked_after_the_pidfd_is_opened():
    """A process whose start time changes between traversal and the signal (replaced while the pidfd is being opened) is skipped."""
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "child", MINE)})
    f = FakeOwner(root, [(100, 1100)], 100)
    orig = f.g._pidfd

    def swap(pid):
        if pid == 101:
            _write_proc(root, 101, 1, "foreign", {"DISPLAY": ":0"}, 5555555)       # replaced exactly while its pidfd is opened
        return orig(pid)
    f.g._pidfd = swap
    f.stop()
    assert f.signalled == [100] and (101, "identity changed before the signal") in f.g.skipped, (f.signalled, f.g.skipped)


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


# ---- R1/R2: the audit uses raw data only; the finding is the rendering of the skeleton -------------------------------------------------------
ART = ROOT / "artifacts" / "run-exp-battle-peace"


def _need_raw(fn):
    def w():
        if not (ART / "snaps").exists():
            print("SKIP %s: the raw artifacts are not on this machine" % fn.__name__)
            return
        fn()
    w.__name__ = fn.__name__
    return w


def _strip_docstring(src):
    import re as _re
    return _re.sub(r'^(#!.*\n)?"""(.|\n)*?"""', "", src, count=1)


def test_inventory_skips_file_spans_and_dates_but_counts_words_and_hex():
    import b16_numbers as N
    t = N.line_tokens("- see `b16-pairs-20261005-150654.json` on 2026-10-05: four runs, 0x45951C, 12,992 and 33 %, cell `loss+unity0=526`.")
    assert sorted(t) == sorted(["4", "0x45951c", "12992", "33"]), t


def test_audit_reads_only_raw_inputs():
    """The audit and b16_raw name no analyser output outside `compare_with_analyser` (their docstrings list what is not read)."""
    import re as _re
    banned = _re.compile(r"b16-(fulldiff|repeat|pairs|survey|hook-table|facts)|b16_expect|b16_number_map|b16_analyze|b16_fulldiff|summary-")
    audit = _strip_docstring((ROOT / "runs/experiments/battles/b16_audit.py").read_text())
    i = audit.index("def compare_with_analyser")
    j = audit.index("def sha(")
    body_ok, outside = audit[i:j], audit[:i] + audit[j:]
    assert banned.search(body_ok), "compare_with_analyser should name the analyser files"
    assert not banned.search(outside), banned.search(outside).group(0)
    raw = _strip_docstring((ROOT / "runs/experiments/battles/b16_raw.py").read_text())
    assert not banned.search(raw), banned.search(raw).group(0)
    for src, name in ((outside, "audit"), (raw, "raw")):
        for m in _re.finditer(r"(?:glob|read_text|read_bytes|open)\(([^)]*)\)", src):
            assert not banned.search(m.group(1)), (name, m.group(0))


def test_skeleton_literals_are_only_registered_ones():
    import b16_raw as RR
    assert RR.literal_numbers("a literal 12 and %%box_w%% and %%lit:rule6%%") == ["12"]
    assert RR.literal_numbers((ROOT / "findings" / "b16-finding.skeleton.md").read_text()) == []


@_need_raw
def test_finding_equals_the_rendering_and_an_edited_number_fails():
    """The regression Sol named: '-18 becomes -14' edited to '-18 becomes -18' in a copy of the finding must fail the audit's finding check."""
    import b16_audit as AU
    text = (ROOT / "findings" / "2026-10-05-battle-peace-offer.md").read_text()
    ok, detail = AU.check_finding(text)
    assert ok, detail
    assert "-18 becomes -14" in text, "the finding no longer states the transition"
    ok, detail = AU.check_finding(text.replace("-18 becomes -14", "-18 becomes -18", 1))
    assert not ok and "becomes" in detail, detail
    ok, detail = AU.check_finding(text.replace("10 of 30 seeds", "11 of 30 seeds", 1))
    assert not ok, detail
    ok, detail = AU.check_finding(text.replace("| 1 | **open** |", "| 1 | closed |", 1))
    assert not ok, detail


@_need_raw
def test_a_doctored_analyser_file_cannot_change_the_audit_and_is_reported():
    """The data folder is swapped for a copy whose analyser files (full diff, repeat) are doctored (a field fewer, a repeat result flipped). Everything the audit
    computes (the full diff, the repeat comparisons, all values, the rendering of the finding) must be unchanged, and the doctoring must be REPORTED by
    `compare_with_analyser`."""
    import json as _json
    import shutil
    import b16_audit as AU
    import b16_raw as RR
    base_vals, _ = RR.values()
    base_fd, base_rp = RR.fulldiff_raw(), RR.repeat_raw()
    tmp = Path(tempfile.mkdtemp())
    for f in RR.B.DATA.iterdir():
        if f.name == "trials-b16.jsonl" or f.name.startswith("hooklog-"):
            shutil.copy(f, tmp / f.name)
    afd = _json.loads(sorted(RR.B.DATA.glob("b16-fulldiff-2*.json"))[-1].read_text())
    arp = _json.loads(sorted(RR.B.DATA.glob("b16-repeat-*.json"))[-1].read_text())
    k = next(i for i, r in enumerate(afd["runs"]) if r["fields"])
    afd["runs"][k]["fields"] = afd["runs"][k]["fields"][:-1]
    afd["runs"][k]["news_dropped"] = ["doctored line"]
    arp[0]["pre_named_regions_equal"] = not arp[0]["pre_named_regions_equal"]
    (tmp / "b16-fulldiff-20261005-000000.json").write_text(_json.dumps(afd))
    (tmp / "b16-repeat-20261005-000000.json").write_text(_json.dumps(arp))
    real = RR.B.DATA
    RR.B.DATA = tmp
    RR._cache.clear()
    try:
        vals, _ = RR.values()
        fd, rp = RR.fulldiff_raw(), RR.repeat_raw()
        ok, detail = AU.check_finding()
        bad = AU.compare_with_analyser(fd, rp)
    finally:
        RR.B.DATA = real
        RR._cache.clear()
    assert vals == base_vals and fd == base_fd and rp == base_rp, "the audit's numbers moved with the doctored analyser files"
    assert ok, detail
    assert {len(r["fields"]) for r in fd["runs"] if r["answer"] == "yes"} == {42} and {len(r["fields"]) for r in fd["runs"] if r["answer"] == "no"} == {0}
    assert any("fulldiff" in b and "fields" in b for b in bad) and any("dropped" in b for b in bad) and any("repeat" in b for b in bad), bad


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
