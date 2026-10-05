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
    """A PeaceGame wired to a fake /proc: a "pidfd" is the tuple ("fd", pid, start time read from the fake /proc at the moment it is opened), so a signal through it
    names the process that existed when it was opened; signals are recorded instead of sent. `discover(pids)` adopts the given pids as the game would at start."""

    def __init__(self, root, popen_pid):
        import b16_common as BC
        self.BC = BC
        self.g = BC.PeaceGame(exe="x")
        self.g.PROC = str(root)
        self.signalled = []
        self.g._pidfd = lambda pid: ("fd", pid, BC.proc_start(pid, str(root)))
        self.g._send = lambda pid, fd: self.signalled.append(fd if fd is not None else ("pid", pid, BC.proc_start(pid, str(root))))
        self.g._close = lambda fd: None

        class P:
            pid = popen_pid

            def wait(self, timeout=None):
                return 0
        self.g.popen = P()

    def discover(self, pids):
        self.g.owned = [self.g._own(p) for p in pids]

    def stop(self):
        old = self.BC.time.sleep
        self.BC.time.sleep = lambda s: None
        try:
            return self.g.stop()
        finally:
            self.BC.time.sleep = old

    def pids(self):
        return sorted({x[1] for x in self.signalled})


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
    f = FakeOwner(root, 100)
    f.discover([100, 101])
    done = f.stop()
    assert f.pids() == [100, 101] and sorted(p for p, _ in done) == [100, 101], (f.signalled, done)


def test_a_recycled_owned_pid_and_its_foreign_children_are_never_signalled():
    """Between discovery and stop() the owned child 101 exits and a FOREIGN process takes its pid (new start time) and has foreign children. The foreign process is not
    walked, and no signal names it or its children (a signal through 101's pidfd names the ORIGINAL process, whose start time is the discovered one)."""
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE), 102: (101, "child", MINE)})
    f = FakeOwner(root, 100)
    f.discover([100, 101, 102])
    import shutil
    shutil.rmtree(root / "102")
    _write_proc(root, 101, 1, "foreign-editor", {"DISPLAY": ":0"}, 999999)
    _write_proc(root, 150, 101, "foreign-child", {"DISPLAY": ":0"}, 999998)
    f.stop()
    assert 150 not in f.pids() and all(x[2] in (1100, 1101, 1102) for x in f.signalled), f.signalled
    # stop() walks nothing since the narrow review (R2), so there is no walk to skip: the signals above are the whole check


def test_a_recycled_launcher_pid_pulls_no_foreign_tree_into_cleanup():
    """The launcher pid 100 is replaced by a foreign process with foreign children; the owned child 101 is gone. No signal names a foreign process."""
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE)})
    f = FakeOwner(root, 100)
    f.discover([100, 101])
    import shutil
    shutil.rmtree(root / "101")
    _write_proc(root, 100, 1, "foreign-service", {"DISPLAY": ":0"}, 777777)
    _write_proc(root, 160, 100, "foreign-child", {"DISPLAY": ":0"}, 777778)
    _write_proc(root, 161, 160, "foreign-grandchild", {"DISPLAY": ":0"}, 777779)
    f.stop()
    assert all(x[2] in (1100, 1101) for x in f.signalled) and not ({160, 161} & set(f.pids())), f.signalled
    # stop() walks nothing since the narrow review (R2), so there is no walk to skip: the signals above are the whole check


def test_the_parent_replaced_between_verification_and_traversal_adopts_nothing():
    """The regression of the final review: a parent that passed its identity check is replaced by a foreign process BEFORE its children are listed (the `_between` hook);
    neither the replacement nor its children are signalled, and the walk is dropped."""
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE)})
    f = FakeOwner(root, 100)
    f.discover([100, 101])
    import shutil
    shutil.rmtree(root / "101")
    swapped = []

    def swap(pid):
        if pid == 100 and not swapped:
            swapped.append(1)
            _write_proc(root, 100, 1, "foreign-service", {"DISPLAY": ":0"}, 777777)       # replaced after verification, before the listing
            _write_proc(root, 170, 100, "foreign-child", {"DISPLAY": ":0"}, 777778)
    f.g._between = swap
    f.g.owned += f.g._walk(f.g.owned[0])          # children are adopted only at discovery (stop() walks nothing since the narrow review)
    f.stop()
    assert swapped and 170 not in f.pids(), (swapped, f.signalled)
    assert all(x[2] in (1100, 1101) for x in f.signalled), f.signalled                   # only the originals (through their pidfds) were named
    assert any("replaced while its children were listed" in why for _, why in f.g.skipped), f.g.skipped


def test_a_process_swapped_while_its_pidfd_is_opened_is_not_adopted():
    """A new child of a verified parent whose identity changes while its pidfd is being opened is not adopted and not signalled."""
    root = _fake_proc({100: (1, "wine", MINE)})
    f = FakeOwner(root, 100)
    f.discover([100])
    _write_proc(root, 101, 100, "child", {"DISPLAY": ":640"}, 1101)
    orig = f.g._pidfd

    def swap(pid):
        if pid == 101:
            _write_proc(root, 101, 1, "foreign", {"DISPLAY": ":0"}, 5555555)       # replaced exactly while its pidfd is opened
        return orig(pid)
    f.g._pidfd = swap
    f.g.owned += f.g._walk(f.g.owned[0])
    f.stop()
    assert f.pids() == [100] and (101, "identity changed while being adopted") in f.g.skipped, (f.signalled, f.g.skipped)


def test_a_parent_recycled_while_its_child_is_adopted_hands_over_no_child():
    """Narrow review R1: the parent passes its checks, then is recycled (new start time) while a child is being adopted; the child still names the old pid as its
    parent. The child is not adopted and not signalled."""
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "foreign-child", {"DISPLAY": ":0"})})
    f = FakeOwner(root, 100)
    f.discover([100])
    orig = f.g._pidfd

    def recycle_parent(pid):
        if pid == 101:
            _write_proc(root, 100, 1, "foreign-service", {"DISPLAY": ":0"}, 888888)      # the parent pid now names another process
        return orig(pid)
    f.g._pidfd = recycle_parent
    f.g.owned += f.g._walk(f.g.owned[0])
    f.stop()
    assert 101 not in f.pids() and (101, "identity changed while being adopted") in f.g.skipped, (f.signalled, f.g.skipped)


def test_without_a_pidfd_nothing_is_signalled_by_a_bare_pid_except_our_unreaped_launcher():
    """Narrow review round 2: a handle with no pidfd is never signalled by pid (the pid may be recycled between any check and the kill). Only the launcher, our own
    unreaped child, is killed, through Popen.kill()."""
    root = _fake_proc({100: (1, "wine", MINE), 101: (100, "Imperial Conquest 2 fast.exe", MINE)})
    f = FakeOwner(root, 100)
    f.g._pidfd = lambda pid: None                     # no pidfd support
    killed = []
    f.g.popen.kill = lambda: killed.append(100)
    f.discover([100, 101])
    f.stop()
    assert f.signalled == [] and killed == [100], (f.signalled, killed)
    assert (101, "no pidfd: not signalled (a bare pid may have been recycled)") in f.g.skipped, f.g.skipped


def test_start_refuses_without_pidfd_support():
    """The player's decision on PR #45: without pidfd support the runner refuses to start (cleanup could not stop the game safely), launching nothing."""
    import b16_common as BC
    g = BC.PeaceGame(exe="x")
    launched = []
    old_popen, had = BC.subprocess.Popen, hasattr(BC.os, "pidfd_open")
    saved = getattr(BC.os, "pidfd_open", None)
    BC.subprocess.Popen = lambda *a, **k: launched.append(a)
    if had:
        del BC.os.pidfd_open
    try:
        try:
            g.start()
            raise AssertionError("start() did not refuse")
        except BC.D.DriverError as e:
            assert "no pidfd support" in str(e), e
        assert launched == [], launched
    finally:
        BC.subprocess.Popen = old_popen
        if had:
            BC.os.pidfd_open = saved


def test_stop_signals_only_the_handles_from_discovery():
    """Narrow review R2: a child that appears after discovery is neither adopted nor signalled by stop()."""
    root = _fake_proc({100: (1, "wine", MINE)})
    f = FakeOwner(root, 100)
    f.discover([100])
    _write_proc(root, 101, 100, "Imperial Conquest 2 fast.exe", MINE, 1101)
    f.stop()
    assert f.pids() == [100], f.signalled


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


def _skeleton():
    return (ROOT / "findings" / "b16-finding.skeleton.md").read_text()


def test_skeleton_lint_is_clean_and_catches_a_literal_number():
    import b16_raw as RR
    assert RR.lint_skeleton(_skeleton()) == []
    assert RR.literal_numbers("a literal 12 and %%box_w%% and %%lit:rule6%%") == ["12"]


@_need_raw
def test_hardcoding_a_value_marker_is_caught():
    """The bypass: `%%box_w%%` replaced by its rendered value 406 (and `%%box_h%%` by 360) renders identically, so only the lint can catch it."""
    import b16_audit as AU
    import b16_raw as RR
    sk = _skeleton()
    for name, value in (("box_w", "406"), ("box_h", "360")):
        mutated = sk.replace("%%" + name + "%%", value)
        ok, _ = AU.check_finding(None, mutated)
        assert ok, "the rendering is identical, which is the point of the bypass"
        errs = RR.lint_skeleton(mutated)
        assert errs and all("literal number %s" % value in e for e in errs), errs
        # the original bug: a prose line describing the marker syntax with a bare double percent made the old lint pair markers across lines and swallow text
        # (numbers included); put such a line in front of every 4th line and require the hardcoded value to be found in each variant
        lines = mutated.split("\n")
        for pos in range(0, len(lines), 4):
            variant = "\n".join(lines[:pos] + ["the markers are `%%`-delimited"] + lines[pos:])
            errs = RR.lint_skeleton(variant)
            assert any("literal number %s" % value in e for e in errs), (pos, errs[:3])


@_need_raw
def test_hardcoding_a_table_is_caught():
    """A table pasted into the skeleton in place of its marker (every row a literal) and a single hardcoded cell are both literal numbers on table-row lines."""
    import b16_raw as RR
    sk = _skeleton()
    mutated = sk.replace("%%table:gate%%", RR.table_md("gate"))
    errs = RR.lint_skeleton(mutated)
    assert errs and any("literal number 501" in e for e in errs), errs[:3]
    row = "| `loss+unity0=526` | 501 | 30 | 32743 | 12992 | **open** | **open** | **open** |"
    assert RR.lint_skeleton(sk + "\n" + row) and any("literal number 501" in e for e in RR.lint_skeleton(sk + "\n" + row))


def test_a_stray_double_percent_is_an_error_and_cannot_swallow_text():
    import b16_raw as RR
    sk = _skeleton()
    errs = RR.lint_skeleton(sk + "\nsee the %%-delimited markers, then 406 x %%box_h%%\n")
    assert any("stray or unknown" in e for e in errs) and any("literal number 406" in e for e in errs), errs
    try:
        RR.render("a %% b %%box_w%%")
    except ValueError as e:
        assert "stray" in str(e)
    else:
        raise AssertionError("render accepted a stray double percent")
    errs = RR.lint_skeleton("%%box_w%% x %%lit:nope%%")
    assert any("stray or unknown" in e for e in errs), errs          # an unregistered lit key is not a marker


@_need_raw
def test_freezing_every_marker_in_turn_is_caught():
    import b16_audit as AU
    total, uncaught = AU.sweep_freeze()
    assert total > 250 and uncaught == [], (total, uncaught[:5])


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


@_need_raw
def test_a_valid_but_wrong_marker_swapped_into_a_clone_sentence_is_caught():
    """The R2 regression of the final review: on skeleton line 17 (clone item 2, Yes) `%%rel_yes_t1%%` replaced by `%%rel_yes_ans%%` renders 'next End turn -18 becomes -18'
    with a REGENERATED finding that equals its rendering; the lint, the placeholders and the freeze sweep accept it, the tracked bindings do not."""
    import b16_audit as AU
    import b16_raw as RR
    sk = _skeleton()
    lines = sk.split("\n")
    assert "%%rel_yes_t1%%" in lines[16] and lines[16].startswith("2. **Yes.**"), lines[16][:60]
    lines[16] = lines[16].replace("%%rel_yes_t1%%", "%%rel_yes_ans%%", 1)
    mutated = "\n".join(lines)
    rendered = RR.render(mutated)
    assert "-18 becomes -18" in rendered
    ok, _ = AU.check_finding(rendered, mutated)
    assert ok and RR.lint_skeleton(mutated) == [], "the old checks accept the substitution"
    errs = RR.check_bindings(mutated)
    assert errs and any("clone.2" in e and "rel_yes_t1" in e for e in errs), errs
    assert RR.check_bindings(sk) == []
    # a new marker-bearing sentence without a tracked binding, and a lost anchor, are errors too
    assert RR.check_bindings(sk.replace("## Method", "## For the clone: extra\n- A new sentence with %%box_w%%.\n\n## Method", 1))
    assert RR.check_bindings(sk.replace("**The reseed.**", "**The re-seed.**", 1))


@_need_raw
def test_an_asterisk_code_span_cannot_hide_numbers():
    """The R3 regression: `999 * 360` in place of the box markers is a code span with an asterisk; the lint must still read it (only registered file references are exempt)."""
    import b16_raw as RR
    sk = _skeleton()
    assert "%%box_w%% x %%box_h%%" in sk
    mutated = sk.replace("%%box_w%% x %%box_h%%", "`999 * 360`", 1)
    errs = RR.lint_skeleton(mutated)
    assert any("literal number 999" in e for e in errs) and any("literal number 360" in e for e in errs), errs
    assert RR.lint_skeleton(sk) == []
    bad = Path(tempfile.mkdtemp()) / "files.json"
    import json as _json
    reg = _json.loads((ROOT / "findings" / "b16-finding.files.json").read_text())
    reg["spans"]["999 * 360"] = {"kind": "glob", "reason": "an attempt to exempt arbitrary text"}
    reg["spans"]["nothing-*.zzz"] = {"kind": "glob", "reason": "matches nothing"}
    bad.write_text(_json.dumps(reg))
    flagged = {s for s, _ in RR.validate_registry(bad)}
    assert {"999 * 360", "nothing-*.zzz"} <= flagged, flagged
    assert RR.validate_registry() == []


def test_a_crashed_suite_with_empty_stdout_is_a_failure():
    """The R4 regression: a nonzero exit code with empty stdout (an import error) must not count as 'no failure'; a missing PASS count and a FAIL line are problems too."""
    import b16_audit as AU
    probs, counts = AU.suite_problems(1, "", "Traceback ...\nImportError: boom", 12)
    assert any("exit code 1" in p for p in probs) and any("0 PASS lines" in p for p in probs), probs
    assert AU.suite_problems(0, "PASS a\nPASS b\n", "", 2)[0] == []
    assert AU.suite_problems(0, "PASS a\n", "", 2)[0]
    assert AU.suite_problems(0, "PASS a\nFAIL b X\n", "", 2)[0]
    probs, counts = AU.suite_problems(0, "SKIP a: no raw data\nPASS a\nPASS b\n", "", 2)
    assert probs == [] and counts == {"pass": 1, "skip": 1}, (probs, counts)


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
