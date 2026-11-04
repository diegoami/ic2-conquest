#!/usr/bin/env python3
"""Offline tests of the long-game tooling (owner 2026-11-04: "test the tooling before running more games, so not in the game
itself"): difftest.late_starts, difftest.save_corpus, difftest.handover, difftest.campaign --resume, difftest.longgame and
difftest.anchored --retry-errors. No Wine, no game, no network: gh, rclone, the original session, the remake and the
campaign subprocess are replaced by stand-ins; game folders are built in a temp dir from a tracked save
(saves/det-AUTO0721-seed12345.SAV).

    python3 -m tests.test_longgame_tooling        (exit 1 on a failure)

Each test names the bug it guards against where there was one (2026-11-04 session).
"""
import json
import shutil
import struct
import sys
import tarfile
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from state.sav import NATIONS, load  # noqa: E402

SAV = ROOT / "saves/det-AUTO0721-seed12345.SAV"


def game_dir(tmp, name="g-rulebot1-150t", complete=(1, 2), extra_checkpoints=(), seeds=True, remake=False):
    """A campaign folder: original/ checkpoints (t00-start, tKK-a00/a01 per complete turn, plus `extra_checkpoints`),
    a receipt with randseed_after for every checkpoint, turns.jsonl rows for the complete turns."""
    g = Path(tmp) / name
    o = g / "original"
    o.mkdir(parents=True)
    names = ["t00-start"] + [f"t{k:02d}-a{j:02d}" for k in complete for j in (0, 1)] + list(extra_checkpoints)
    rec = [{"kind": "start"}]
    for i, n in enumerate(names):
        shutil.copy(SAV, o / f"{n}.SAV")
        if seeds:
            rec.append({"kind": "randseed_after", "checkpoint": n, "value": 1000 + i})
    (o / "receipt.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rec))
    (g / "turns.jsonl").write_text("".join(json.dumps({"turn": k, "orders_same": True, "differences": 0}) + "\n" for k in complete))
    if remake:
        for k in [0] + list(complete):
            d = g / "remake" / f"t{k:02d}"
            d.mkdir(parents=True)
            shutil.copy(SAV, d / "a001.SAV")
            (d / "a001.native").write_text("native")
    return g


# ---- late_starts --------------------------------------------------------------------------------------------------

def test_catalogue_counts_completed_turns_only():
    # bug: a pack published mid-game listed the turn in progress (its last checkpoint is a mid-turn state)
    from difftest.late_starts import catalogue
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        g = game_dir(tmp, complete=(1, 2), extra_checkpoints=("t03-a00",))
        c = catalogue(g.resolve())
        assert [s["start_of_turn"] for s in c] == [1, 2, 3], c


def test_catalogue_three_digit_turns():
    # bug: t[0-9][0-9] / name[1:3] missed t100-a00.SAV in the 150-turn games
    from difftest.late_starts import catalogue
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        g = game_dir(tmp, complete=(99, 100, 101))
        c = catalogue(g.resolve())
        assert [s["start_of_turn"] for s in c] == [1, 100, 101, 102], [s["start_of_turn"] for s in c]
        assert c[-1]["checkpoint"].endswith("t101-a01.SAV") and c[-1]["randseed_after"] is not None


def test_catalogue_randseed_after_matches_checkpoint():
    from difftest.late_starts import catalogue
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        g = game_dir(tmp, complete=(1,))
        c = catalogue(g.resolve())
        assert c[0]["randseed_after"] == 1000 and c[1]["randseed_after"] == 1002, c   # t00-start, t01-a01


# ---- save_corpus --------------------------------------------------------------------------------------------------

def corpus_sandbox(tmp):
    import difftest.save_corpus as C
    calls = []
    saved = (C.STAGE, C.INDEX, C.gh, C.rclone)
    C.STAGE = Path(tmp) / "stage"
    C.INDEX = Path(tmp) / "index.jsonl"
    C.gh = lambda *a, check=True: calls.append(("gh",) + a) or types.SimpleNamespace(returncode=1 if a[:2] == ("release", "view") else 0)
    C.rclone = lambda *a, check=True: calls.append(("rclone",) + a) or types.SimpleNamespace(returncode=0)
    return C, calls, saved


def restore(C, saved):
    C.STAGE, C.INDEX, C.gh, C.rclone = saved


def test_publish_limits_starts_to_the_pack_and_excludes_anchored():
    # bug: the index listed starts beyond the pack (read after packing while the game ran)
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        C, calls, saved = corpus_sandbox(tmp)
        try:
            g = game_dir(tmp, complete=(1, 2, 3), extra_checkpoints=("t04-a00",))
            (g / "anchored-turnseed").mkdir()
            (g / "anchored-turnseed" / "big.txt").write_text("x")
            (g.parent / "g.log").write_text("log")
            C.publish(g)
            e = [json.loads(l) for l in C.INDEX.read_text().splitlines()][0]
            assert e["asset"] == "g-rulebot1-150t-t003.tar.gz" and e["last_turn"] == 3, e
            assert [s["start_of_turn"] for s in e["starts"]] == [1, 2, 3, 4], e["starts"]
            assert all(s["checkpoint"].startswith("g-rulebot1-150t/original/") for s in e["starts"])
            names = tarfile.open(C.STAGE / e["asset"]).getnames()
            assert not any("anchored" in n for n in names), names
            assert any(n.endswith("original/t03-a01.SAV") for n in names)
            kinds = [c[:3] for c in calls]
            assert ("gh", "release", "create") in kinds and ("gh", "release", "upload") in kinds, calls
            assert sum(1 for c in calls if c[0] == "rclone" and c[1] == "copy") == 2, calls     # pack + index
        finally:
            restore(C, saved)


def test_publish_never_replaces_a_pack():
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        C, calls, saved = corpus_sandbox(tmp)
        try:
            g = game_dir(tmp, complete=(1,))
            C.publish(g)
            try:
                C.publish(g)
                raise AssertionError("second publish of the same turn did not refuse")
            except SystemExit as e:
                assert "never replaced" in str(e)
        finally:
            restore(C, saved)


def test_entries_skip_note_lines_and_fetch_prefers_drive():
    # bug: `list` crashed on the index's note lines
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        C, calls, saved = corpus_sandbox(tmp)
        try:
            g = game_dir(tmp, complete=(1,))
            C.publish(g)
            with open(C.INDEX, "a") as f:
                f.write(json.dumps({"note": "x"}) + "\n")
            assert len(C.entries()) == 1
            calls.clear()
            pack = C.STAGE / "g-rulebot1-150t-t001.tar.gz"
            into = Path(tmp) / "fetched"
            into.mkdir()
            shutil.copy(pack, into / pack.name)       # what the (stand-in) rclone copy would leave
            C.fetch("g-rulebot1-150t", into)
            assert calls and calls[0][0] == "rclone" and not any(c[0] == "gh" for c in calls), calls
            assert (into / "g-rulebot1-150t" / "original" / "t01-a01.SAV").exists()
        finally:
            restore(C, saved)


# ---- handover -----------------------------------------------------------------------------------------------------

def test_handover_moves_only_the_human_flags():
    from difftest.handover import handover, nation_table, HUMAN
    from state.sav import NATION_LEN
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        dst = Path(tmp) / "h.SAV"
        info = handover(SAV, dst)
        a, b = SAV.read_bytes(), dst.read_bytes()
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        t = nation_table(bytearray(a))
        assert all((i - t) % NATION_LEN == HUMAN for i in diff) and len(diff) == 2, diff     # old off, new on
        s, d = load(SAV), load(dst)
        heir = max((n["cities_count"], -i, i) for i, n in enumerate(s["nations"]) if n["unity"] > 0 and n["capital"] >= 0
                   and not n["human"])[2]
        assert [NATIONS[i] for i, n in enumerate(d["nations"]) if n["human"]] == [NATIONS[heir]] == [info["to"]], info


def test_handover_named_heir():
    from difftest.handover import handover
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        info = handover(SAV, Path(tmp) / "h.SAV", to="Carthage")
        assert info["to"] == "Carthage" and [n["name"] for n in load(Path(tmp) / "h.SAV")["nations"] if n["human"]], info


# ---- campaign --resume ----------------------------------------------------------------------------------------------

def run_resume(g, original_only):
    import difftest.campaign as K
    import difftest.original as O
    made = {}

    class FakeSession:
        def __init__(self, start, out, seed, tag, log=print, resume_randseed=None, start_randseed=None):
            made.update(start=Path(start), out=Path(out), resume_randseed=resume_randseed)
    saved = O.OriginalSession
    O.OriginalSession = FakeSession
    try:
        a = types.SimpleNamespace(seed=12345, original_only=original_only)
        return K.resume(g, a, g / "remake", "TAG", lambda *x: None), made
    finally:
        O.OriginalSession = saved


def test_resume_reloads_last_complete_turn_with_its_seed_and_moves_the_partial_turn_aside():
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        g = game_dir(tmp, complete=(1, 2), extra_checkpoints=("t03-a00",), remake=True)
        (g / "remake" / "t03").mkdir()
        (o, so, native, sr, done, first), made = run_resume(g, original_only=False)
        assert done == 2 and made["start"].name == "t02-a01.SAV", (done, made)
        assert made["resume_randseed"] == 1004, made                         # randseed_after of t02-a01 (index 4)
        assert not (g / "original" / "t03-a00.SAV").exists() and not (g / "remake" / "t03").exists()
        aside = next(g.glob("superseded-*"))
        assert {p.name for p in aside.iterdir()} == {"original-t03-a00.SAV", "remake-t03"}, list(aside.iterdir())
        assert native.name == "a001.native" and native.parent.name == "t02"
        r = [json.loads(l) for l in (g / "resumes.jsonl").read_text().splitlines()]
        assert r[-1]["after_turn"] == 2 and r[-1]["randseed"] == 1004


def test_resume_original_only_and_refuses_without_seeds():
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        g = game_dir(tmp, complete=(1,))
        (o, so, native, sr, done, first), made = run_resume(g, original_only=True)
        assert done == 1 and native is None and sr is None
        g2 = game_dir(tmp, name="noseed", complete=(1,), seeds=False)
        try:
            run_resume(g2, original_only=True)
            raise AssertionError("resumed without randseed_after")
        except SystemExit as e:
            assert "IC2_LOG_RANDSEED" in str(e)


# ---- longgame -------------------------------------------------------------------------------------------------------

def run_longgame(base, turns=150):
    import difftest.longgame as LG
    log = {"run_part": [], "anchored": []}
    saved = (LG.run_part, LG.anchored, LG.corpus)

    def fake_run_part(b, part, start, n, seed, pin):
        log["run_part"].append((part.name, Path(start).name, n, seed, part.exists()))
    LG.run_part = fake_run_part
    LG.anchored = lambda b, part, pin: log["anchored"].append(part.name)
    LG.corpus = lambda b, part: None
    try:
        try:
            LG.main([str(SAV), str(base), "--turns", str(turns)])
        except (AttributeError, TypeError):
            pass     # the fake run_part writes no summary for the new part: main stops after scheduling it
    finally:
        LG.run_part, LG.anchored, LG.corpus = saved
    return log


def test_longgame_hands_over_after_game_over_and_ignores_the_start_file():
    # bugs: relative_to on a relative checkpoint path; the -h* glob matched the handover start save
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        base = game_dir(tmp, name="rome-rulebot1-150t", complete=tuple(range(1, 49)))
        (base / "summary.json").write_text(json.dumps({"game_over": {"turn": 48, "text": "conquered"}}))
        rel = base.relative_to(ROOT)
        log = run_longgame(rel)
        assert log["run_part"] and log["run_part"][0][:4] == ("rome-rulebot1-150t-h1", "rome-rulebot1-150t-h1-start.SAV", 102,
                                                              1000 + 1 + 2 * 46 + 1), log    # randseed_after of t47-a01
        h = [json.loads(l) for l in (base.parent / "rome-rulebot1-150t.handovers.jsonl").read_text().splitlines()]
        assert h[0]["from_checkpoint"].endswith("t47-a01.SAV") and h[0]["to"] and h[0]["from"], h
        assert (base.parent / "rome-rulebot1-150t-h1-start.SAV").exists()
        # second run: the start file exists (no h1 directory yet) and must not be taken for a part, nor rewritten
        mtime = (base.parent / "rome-rulebot1-150t-h1-start.SAV").stat().st_mtime
        log2 = run_longgame(rel)
        assert log2["run_part"][0][0] == "rome-rulebot1-150t-h1", log2
        assert (base.parent / "rome-rulebot1-150t-h1-start.SAV").stat().st_mtime == mtime


def test_longgame_resumes_an_unfinished_part_with_its_handover():
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        base = game_dir(tmp, name="rome-rulebot1-150t", complete=tuple(range(1, 49)))
        (base / "summary.json").write_text(json.dumps({"game_over": {"turn": 48, "text": "conquered"}}))
        h1 = game_dir(tmp, name="rome-rulebot1-150t-h1", complete=tuple(range(1, 28)))     # interrupted at 27
        (base.parent / "rome-rulebot1-150t.handovers.jsonl").write_text(json.dumps(
            {"part": h1.name, "start": str(base.parent / "rome-rulebot1-150t-h1-start.SAV"), "randseed": 77}) + "\n")
        log = run_longgame(base.relative_to(ROOT))
        assert log["run_part"][0] == ("rome-rulebot1-150t-h1", "rome-rulebot1-150t-h1-start.SAV", 102, 77, True), log
        assert log["anchored"][0] == "rome-rulebot1-150t", log


# ---- anchored --retry-errors ------------------------------------------------------------------------------------------

def test_anchored_retry_errors_replays_only_failed_turns_into_new_folders():
    import difftest.anchored as AN
    with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as tmp:
        g = game_dir(tmp, complete=(1, 2, 3))
        out = g / "anchored-x"
        out.mkdir()
        rows = [{"turn": 1, "ai": {}}, {"turn": 2, "error": "Out of memory"}, {"turn": 3, "ai": {}}]
        (out / "turns.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        seen = []
        saved = AN.replay_turn
        AN.replay_turn = lambda camp, k, row, o, log, seed=None, attempt=1: seen.append((k, seed, attempt)) or {"turn": k, "ai": {}}
        try:
            AN.main([str(g), "--out", "anchored-x", "--turn-seed", "100", "--retry-errors"])
        finally:
            AN.replay_turn = saved
        assert seen == [(2, 102, 2)], seen
        last = [json.loads(l) for l in (out / "turns.jsonl").read_text().splitlines()][-1]
        assert last["turn"] == 2 and last["attempt"] == 2 and "error" not in last


TESTS = [n for n in sorted(globals()) if n.startswith("test_")]

if __name__ == "__main__":
    bad = 0
    for n in TESTS:
        try:
            globals()[n]()
            print("PASS", n)
        except Exception as e:  # noqa: BLE001
            bad += 1
            import traceback
            print("FAIL", n, type(e).__name__, e)
            traceback.print_exc(limit=3)
    sys.exit(1 if bad else 0)
