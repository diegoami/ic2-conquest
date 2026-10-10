#!/usr/bin/env python3
"""The reviewer must never be told to type its worktree's path (no `git -C <worktree>`).

Why: a model that retypes a 90-character worktree path gets one character wrong sooner or later; OpenCode then auto-rejects the
path as external_directory, which ends `opencode run`, and the review is lost (harness_imperial#15, 2026-10-02: lost after 17 s).
The script already starts OpenCode inside the worktree (--dir and the process's working directory), so `-C` buys nothing; the tree
proof (first two tool calls) covers what it was for. See docs/external-review.md, "Lessons".

No game, no network, no credentials (the watcher is pointed at a missing auth.json, and the test asserts nothing was copied): a fake
`opencode` records what the watcher gives it.

    python3 -m tests.test_reviewer_prompt
"""
import atexit
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import external_review as er  # noqa: E402
import opencode_watched as ow  # noqa: E402

AGENT = ROOT / ".opencode" / "agents" / "external-reviewer.md"
SCRATCH = Path(tempfile.mkdtemp(prefix="test-reviewer-prompt-"))     # a temp dir, removed at exit: no run dir is left in the repository
atexit.register(shutil.rmtree, SCRATCH, True)
WT, BASE, HEAD = "/home/user/ic2-work/review/pr5-review-0123456789ab", "b" * 40, "a" * 40
GIT_C = re.compile(r"git\s+-C\b")

FAKE = '''#!/usr/bin/env python3
# A fake opencode. Each `run` call takes the next behaviour from plan.json (default ok): ok | 429 (provider error on stderr, exit 1,
# no session) | hang (session, then sleeps) | crash (session, exit 1) | badformat (ends ok but with no review header) | slow (3 s).
import json, os, pathlib, re, sys, time
d = pathlib.Path(os.environ["FAKE_OC_DIR"]); a = sys.argv[1:]
if a[:1] == ["models"]:
    print("provider/model")
elif a[:2] == ["debug", "agent"]:
    print(json.dumps({"name": a[2]}))
elif a[:2] == ["session", "list"]:
    t = (d / "title").read_text() if (d / "title").exists() else None
    print(json.dumps([{"id": "ses_fake", "title": t, "updated": 1}] if t else []))
elif a[:1] == ["export"]:
    hdr = (d / "hdr.txt").read_text() if (d / "hdr.txt").exists() else "PR review (x)"
    text = "tool chatter only" if (d / "badformat").exists() else hdr + "\\napprove\\nR1 a.py:1 non-blocking: x\\napprove"
    print(json.dumps({"info": {}, "messages": [{"info": {"role": "assistant", "agent": "external-reviewer", "finish": "stop"},
                                                 "parts": [{"type": "text", "text": text}]}]}))
elif a[:1] == ["run"]:
    n = int((d / "count").read_text()) + 1 if (d / "count").exists() else 1
    (d / "count").write_text(str(n))
    plan = json.loads((d / "plan.json").read_text()) if (d / "plan.json").exists() else []
    mode = plan[n - 1] if n <= len(plan) else "ok"
    (d / ("argv-%d.json" % n)).write_text(json.dumps(a))
    (d / "argv.json").write_text(json.dumps(a))
    brief = open(a[a.index("-f") + 1]).read()
    (d / "brief.txt").write_text(brief)
    m = re.search(r"exactly\\): (.+)", brief)
    if m:
        (d / "hdr.txt").write_text(m.group(1).strip())
    if mode == "badformat":
        (d / "badformat").write_text("1")
    else:
        (d / "badformat").unlink(missing_ok=True)
    if mode == "429":
        sys.stderr.write("Error: 429 Too Many Requests: rate limit exceeded\\n")
        sys.exit(1)
    if "--title" in a:
        (d / "title").write_text(a[a.index("--title") + 1])
    if mode == "hang":
        time.sleep(600)
    if mode == "crash":
        sys.stderr.write("panic: something broke\\n")
        sys.exit(1)
    if mode == "textcrash":      # the MODEL's text mentions a 429 on stdout, then the process dies: not an API failure
        print("I saw a 429 rate limit in the log", flush=True)
        sys.exit(1)
    if mode == "apicrash":       # OpenCode's own error line on stderr, as 1.18.34 prints it
        sys.stderr.write('Error: {"name": "APIError", "data": {"statusCode": 429, "message": "Too Many Requests"}}\\n')
        sys.exit(1)
    if mode == "slow":
        time.sleep(3)
'''


def agent_parts():
    text = AGENT.read_text()
    _, front, body = text.split("---", 2)
    return front, body


def test_agent_body_has_no_git_c():
    front, body = agent_parts()
    assert not GIT_C.search(body), "the agent's instructions still ask for `git -C`: %r" % GIT_C.search(body).group(0)
    assert "never type the worktree" in body and "without `-C`" in body, "the no-`-C` rule is missing from the agent body"
    for needle in ("git rev-parse --show-toplevel HEAD", "git diff --name-only", "wrong tree"):
        assert needle in body, "the tree proof is missing from the agent body: " + needle
    return "the agent body says run git as it is, never type the path, and carries the tree proof"


def test_agent_rules_only_deny_git_c():
    front, _ = agent_parts()
    rules = [ln.strip() for ln in front.splitlines() if GIT_C.search(ln)]
    allowed = [r for r in rules if not r.endswith(": deny")]
    assert not allowed, "a `git -C` rule that is not a deny: %r" % allowed
    assert any("git -C * push" in r for r in rules) and any("git -C * commit" in r for r in rules), rules
    return f"{len(rules)} `git -C` rules, all deny (push, commit, ...)"


def test_brief_template_has_no_git_c():
    for kind in ("pr", "release"):
        b = er.brief_text(kind, 5, "t", "body", BASE, HEAD, "PR review (x)", WT)
        assert not GIT_C.search(b), "the %s brief asks for `git -C`: %r" % (kind, GIT_C.search(b).group(0))
        assert "git rev-parse --show-toplevel HEAD" in b and WT in b and HEAD in b, kind
        assert ("git diff --name-only %s...HEAD" % BASE) in b, kind
    assert "must not be empty" in er.brief_text("pr", 5, "t", "b", BASE, HEAD, "h", WT)
    assert "no diff by design" in er.brief_text("release", 9, "t", "b", HEAD, HEAD, "h", WT)
    return "the PR and release briefs have the tree proof and no `git -C`"


def test_prompt_the_watcher_hands_to_opencode():
    """Run the real watcher against a fake opencode and read back the brief it was handed."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    fake = SCRATCH / "fake-opencode"
    fake.write_text(FAKE)
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    for f in ("argv.json", "title", "brief.txt"):
        (SCRATCH / f).unlink(missing_ok=True)
    brief = SCRATCH / "brief.md"
    brief.write_text(er.brief_text("pr", 5, "t", "body", BASE, HEAD, "PR review (x)", WT), encoding="utf-8")
    # OPENCODE_AUTH points at a file that does not exist: the watcher copies auth.json into its data dir, and this test
    # must not leave a copy of the real credentials in the repository tree (even a git-ignored one).
    env = {"OPENCODE_EXE": str(fake), "FAKE_OC_DIR": str(SCRATCH), "OPENCODE_AUTH": str(SCRATCH / "no-auth.json")}
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    t0 = time.time()
    try:
        r = ow.run(brief, ROOT, "provider/model", SCRATCH / "run", data_dir=SCRATCH / "data", log=lambda s: None)
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    assert not (SCRATCH / "data" / "opencode" / "auth.json").exists(), "the test copied a credential file"
    assert r["class"] == "ok", (r["class"], r["cause"])
    argv = json.loads((SCRATCH / "argv.json").read_text())
    got = (SCRATCH / "brief.txt").read_text()
    assert not GIT_C.search(" ".join(argv)), "the command line asks for `git -C`: %r" % argv
    assert not GIT_C.search(got), "the brief opencode received asks for `git -C`"
    assert "--dir" in argv and argv[argv.index("--dir") + 1] == str(ROOT), "opencode must start in the worktree (--dir)"
    assert "git rev-parse --show-toplevel HEAD" in got
    return f"opencode received a brief with no `git -C`, started with --dir <worktree> (run ok in {time.time() - t0:.0f}s)"


# ---- OpenCode resilience (2026-10-10): failure kinds, resume, progress, status -------------------------------------------
import contextlib  # noqa: E402
import sqlite3  # noqa: E402
import subprocess  # noqa: E402


@contextlib.contextmanager
def fake_opencode(name, plan):
    """A fresh scratch dir with the fake opencode and its plan; env pointed at it; the watcher's clock sped up."""
    d = SCRATCH / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    fake = d / "fake-opencode"
    fake.write_text(FAKE)
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    (d / "plan.json").write_text(json.dumps(plan))
    env = {"OPENCODE_EXE": str(fake), "FAKE_OC_DIR": str(d), "OPENCODE_AUTH": str(d / "no-auth.json")}
    saved = {k: os.environ.get(k) for k in env}
    clock = (ow.TICK, ow.PROGRESS_EVERY)
    os.environ.update(env)
    ow.TICK, ow.PROGRESS_EVERY = 0.2, 0.4
    try:
        yield d
    finally:
        ow.TICK, ow.PROGRESS_EVERY = clock
        for k, v in saved.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def chain(d, n_models=2):
    """er.run_chain over the fake: (final, stop, failures)."""
    failures = []
    final, stop = er.run_chain(["provider/model"] * n_models, "pr", 5, "t", "body", BASE, HEAD, ROOT, d / "logs", "",
                               "external-reviewer", failures, d / "data", log=lambda s: None)
    return final, stop, failures


def runs_started(d):
    return int((d / "count").read_text())


def write_brief(d):
    brief = d / "b.md"
    brief.write_text(er.brief_text("pr", 5, "t", "body", BASE, HEAD, "PR review (x)", WT), encoding="utf-8")
    return brief


def test_api_failure_falls_to_next_model():
    with fake_opencode("kind-api", ["429", "ok"]) as d:
        final, stop, failures = chain(d)
        assert final and not stop, (final, stop)
        assert failures == [("provider/model", "exited-without-session")], failures
        r1 = json.loads((d / "logs" / "run-1" / "result.json").read_text())
        assert r1["kind"] == "api" and "429" in r1["cause"], r1
        r2 = json.loads((d / "logs" / "run-2" / "result.json").read_text())
        assert r2["class"] == "ok" and r2["kind"] is None, r2
        assert runs_started(d) == 2
    for line, api in (("Error: 429 Too Many Requests", True), ("rate limit exceeded", True), ("503 Service Unavailable", True),
                      ("statusCode: 502", True), ("Error: connect ECONNRESET", True), ("usage limit reached", True),
                      ("insufficient quota", True), ("model is overloaded", True), ("no progress for 600s", False),
                      ("exit 1", False), ("panic: something broke", False)):
        assert bool(ow.API_RE.search(line)) == api, line
    return "429 on stderr -> kind api with the evidence in cause, the next model ran and posted; the provider-error patterns match"


def test_hang_then_resume():
    with fake_opencode("resume-hang", ["hang", "ok"]) as d:
        r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", idle=1.5, startup=5, data_dir=d / "data", log=lambda s: None)
        assert r["class"] == "ok" and r["kind"] is None, (r["class"], r["cause"])
        assert runs_started(d) == 2
        a2 = json.loads((d / "argv-2.json").read_text())
        assert a2[a2.index("--session") + 1] == "ses_fake" and "--title" not in a2, a2
        assert a2[1] == ow.RESUME_MSG and "-f" in a2, a2
        st = json.loads((d / "run" / "state.json").read_text())
        assert st["session"] == "ses_fake" and st["attempt"] == 2 and st["status"] == "ok", st
    return "idle-timeout -> opencode run --session ses_fake with the fixed message (no new title) -> ok; state.json attempt 2"


def test_crash_after_resumes_is_a_process_failure():
    with fake_opencode("resume-crash", ["crash", "crash", "crash", "ok"]) as d:
        final, stop, failures = chain(d)
        assert final is None and stop and not failures, (final, stop, failures)
        m, r = stop
        assert r["class"] == "nonzero-exit" and r["kind"] == "process" and r["session"] == "ses_fake", r
        assert runs_started(d) == 3, "first run + 2 resumes, and no other model: %d" % runs_started(d)
        a3 = json.loads((d / "argv-3.json").read_text())
        assert a3[a3.index("--session") + 1] == "ses_fake"
        msg = er.process_message(m, r)
        rd = str(d / "logs" / "run-1")
        assert msg.startswith("OpenCode process failure: provider/model: nonzero-exit: exit 1;") and "session ses_fake" in msg \
            and f"run dir {rd}" in msg and f"resume with --resume {rd}" in msg, msg
        assert (d / "logs" / "run-1" / "result.json").exists() and (d / "logs" / "run-1" / "stdout.log").exists()
    return "crash, 2 resumes, crash -> kind process, no second model, exit-6 message names session, run dir and --resume"


def test_bad_format_is_a_process_failure():
    with fake_opencode("bad-format", ["badformat", "ok"]) as d:
        final, stop, failures = chain(d)
        assert final is None and stop and not failures, (final, stop)
        r = stop[1]
        assert r["class"] == "bad-format" and r["kind"] == "process", r
        assert runs_started(d) == 1, "no fallback to another model"
        assert json.loads((d / "logs" / "run-1" / "result.json").read_text())["class"] == "bad-format"
        assert "bad-format" in (d / "logs" / "run-1" / "status.txt").read_text()
        prev = json.loads((d / "logs" / "run-1" / "result.prev-1.json").read_text())
        assert prev["class"] == "ok" and prev["text"], prev      # the ok result is kept, not overwritten (rule 6)
    return "no header line -> bad-format, kind process, chain stopped after one run, recorded in result.json and status.txt"


def make_db(path, session):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path)
    c.execute("create table part (id text, message_id text, session_id text, time_created int, time_updated int, data text)")
    c.execute("create table todo (session_id text, content text, status text, priority text, position int, time_created int, time_updated int)")
    for i, (tool, inp) in enumerate((("read", {"filePath": "findings/x.md"}), ("bash", {"command": "git diff --stat"}))):
        c.execute("insert into part values (?,?,?,?,?,?)", (f"p{i}", "m", session, 100 + i, 100 + i,
                                                          json.dumps({"type": "tool", "tool": tool, "state": {"input": inp}})))
    c.execute("insert into part values ('t','m',?,200,200,?)", (session, json.dumps({"type": "text", "text": "hi"})))
    for i, (t, st) in enumerate((("read the diff", "completed"), ("check the tests", "in_progress"), ("write the review", "pending"))):
        c.execute("insert into todo values (?,?,?,?,?,?,?)", (session, t, st, "high", i, 1, 1))
    c.commit()
    c.close()


def view_dir(root, name, state, result=None, progress=None):
    rd = root / name / "run-1"
    rd.mkdir(parents=True)
    (rd / "state.json").write_text(json.dumps(state))
    if result:
        (rd / "result.json").write_text(json.dumps(result))
    if progress:
        (rd / "progress.jsonl").write_text(json.dumps(progress) + "\n")


def test_progress_and_status():
    with fake_opencode("progress", ["slow"]) as d:
        make_db(d / "data" / "opencode" / "opencode.db", "ses_fake")
        r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None,
                   meta={"kind": "pr", "number": 66, "head": HEAD})
        assert r["class"] == "ok", r
        lines = [json.loads(x) for x in (d / "run" / "progress.jsonl").read_text().splitlines()]
        got = [x for x in lines if x.get("tools") == 2]
        assert got, lines
        g = got[-1]
        assert g["last_tool"] == "bash git diff --stat" and g["todo_done"] == 1 and g["todo_total"] == 3 \
            and g["todo_now"] == "check the tests" and g["session"] == "ses_fake", g
        assert not (d / "data" / "opencode" / "auth.json").exists()
        # rendering: a live run (this very process is the watcher), a stopped one, a dead one
        root, now, mine = d / "view", time.time(), "openai/gpt-5.6-luna#high"
        view_dir(root, "pr66-aaaaaa", {"kind": "pr", "number": 66, "model": mine, "status": "running", "pid": os.getpid(),
                                       "started": now - 250, "updated": now, "session": "ses_live"},
                 progress={"tools": 12, "last_tool": "read findings/x.md", "todo_done": 2, "todo_total": 3})
        view_dir(root, "pr66-bbbbbb", {"kind": "pr", "number": 66, "model": mine, "status": "idle-timeout", "pid": 1,
                                       "started": now - 900, "updated": now - 60, "session": "ses_dead"},
                 result={"class": "idle-timeout", "kind": "process", "cause": "no progress for 600s"})
        view_dir(root, "pr67-cccccc", {"kind": "pr", "number": 67, "model": "minimax/MiniMax-M2.7", "status": "running",
                                       "pid": 2 ** 22 + 12345, "started": now - 90, "updated": now - 60, "session": "ses_x"})
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "opencode_status.py"), "--root", str(root)],
                             capture_output=True, text=True, check=True).stdout.splitlines()
        assert out[0] == "PR 66 review · gpt-5.6-luna · running 4m · 12 steps · now: read findings/x.md · todo 2/3", out
        assert any("STOPPED (process: idle-timeout) · no progress for 600s · session ses_dead · resume: python3 scripts/external_review.py --resume "
                   in x for x in out), out
        assert any("PR 67 review · MiniMax-M2.7 · DIED" in x for x in out), out
    return "progress.jsonl got tool count, last tool and todo 1/3 from a read-only DB; opencode_status.py rendered running, STOPPED, DIED"


def test_only_stderr_is_api_evidence():
    with fake_opencode("text-429", ["textcrash"] * 3) as d:
        final, stop, failures = chain(d)
        assert final is None and stop and not failures, (final, stop)
        r = stop[1]
        assert r["kind"] == "process" and r["class"] == "nonzero-exit" and "429" not in (r["cause"] or ""), r
        assert runs_started(d) == 3, "a model's text is not an API failure: it is resumed, not passed on"
    with fake_opencode("err-429", ["apicrash", "ok"]) as d:
        final, stop, failures = chain(d)
        assert final and not stop and failures == [("provider/model", "nonzero-exit")], (final, stop, failures)
        r1 = json.loads((d / "logs" / "run-1" / "result.json").read_text())
        assert r1["kind"] == "api" and "statusCode" in r1["cause"], r1
        assert runs_started(d) == 2, "an api failure is not resumed: the next model took over"
    return "'429 rate limit' in the model's stdout stays process (resumed 2x, no fallback); OpenCode's `Error: {... 429}` on stderr is api"


def test_resume_limit_holds_across_invocations():
    with fake_opencode("resume-limit", ["crash", "crash", "crash", "ok"]) as d:
        final, stop, failures = chain(d)
        assert stop, (final, stop)
        rd = d / "logs" / "run-1"
        assert json.loads((rd / "state.json").read_text())["resumes_used"] == 2
        before = (rd / "result.json").read_text()
        r = ow.run(rd.parent / "brief-1.md", ROOT, "provider/model", rd, data_dir=d / "data", log=lambda s: None, resume_session="ses_fake")
        assert r["class"] == "resume-limit" and "--force-resume" in r["cause"], r
        assert runs_started(d) == 3 and (rd / "result.json").read_text() == before, "a refused resume must touch nothing"
        assert er.resume_run(rd, False) == 2 and runs_started(d) == 3          # the CLI path refuses too, before any repository call
        r = ow.run(rd.parent / "brief-1.md", ROOT, "provider/model", rd, data_dir=d / "data", log=lambda s: None,
                   resume_session="ses_fake", force_resume=True)
        assert r["class"] == "ok", r
        st = json.loads((rd / "state.json").read_text())
        assert len(st["forced_resumes"]) == 1 and st["forced_resumes"][0]["resumes_used"] == 2 and st["resumes_used"] == 1, st
        assert (rd / "result.prev-1.json").exists() and runs_started(d) == 4
    return "after 2 resumes a manual resume is refused (nothing written, exit 2); --force-resume goes on, logged in state.json, count restarts"


TESTS = ["agent_body_has_no_git_c", "agent_rules_only_deny_git_c", "brief_template_has_no_git_c",
         "prompt_the_watcher_hands_to_opencode", "api_failure_falls_to_next_model", "hang_then_resume",
         "crash_after_resumes_is_a_process_failure", "bad_format_is_a_process_failure", "progress_and_status",
         "only_stderr_is_api_evidence", "resume_limit_holds_across_invocations"]

if __name__ == "__main__":
    bad = 0
    for n in sys.argv[1:] or TESTS:
        try:
            print(f"PASS {n}: {globals()['test_' + n]()}", flush=True)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print(f"FAIL {n}: {type(e).__name__}: {e}", flush=True)
    sys.exit(1 if bad else 0)
