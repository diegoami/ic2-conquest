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
    if "--refresh" in a and (d / "refresh_err").exists():
        sys.stderr.write((d / "refresh_err").read_text() + "\\n")
        sys.exit(1)
    if (d / "models_err").exists():
        sys.stderr.write((d / "models_err").read_text() + "\\n")
        sys.exit(1)
    print("provider/model")
elif a[:2] == ["debug", "agent"]:
    print(json.dumps({"name": a[2]}))
elif a[:2] == ["session", "list"]:
    t = (d / "title").read_text() if (d / "title").exists() else None
    print(json.dumps([{"id": "ses_fake", "title": t, "updated": 1}] if t else []))
elif a[:1] == ["export"]:
    hdr = (d / "hdr.txt").read_text() if (d / "hdr.txt").exists() else "PR review (x)"
    last = (d / "lastmode").read_text() if (d / "lastmode").exists() else "ok"
    if (d / "export_bad").exists():
        print((d / "export_bad").read_text())
        sys.exit(0)
    if last in ("hang", "crash", "textcrash", "apicrash", "authcrash", "429", "perm", "permlate", "permbash", "permbashexit0", "rejectedline", "diffcrash", "permbashhang") or last == "reportcrash":
        # a run that died: mid-work (finish tool-calls, partial text) or after a final message (reportcrash: stopped and reported)
        stop = last == "reportcrash"
        info = {"role": "assistant", "agent": "external-reviewer", "finish": "stop" if stop else "tool-calls"}
        if (d / "export_error").exists():
            info["error"] = json.loads((d / "export_error").read_text())
        print(json.dumps({"info": {}, "messages": [{"info": info,
                                                    "parts": [{"type": "text", "text": "BLOCKED: I need file X" if stop else "partial notes"}]}]}))
        sys.exit(0)
    text = "tool chatter only" if (d / "badformat").exists() else hdr + "\\napprove\\nR1 a.py:1 non-blocking: x\\napprove"
    print(json.dumps({"info": {}, "messages": [{"info": {"role": "assistant", "agent": "external-reviewer", "finish": "stop"},
                                                 "parts": [{"type": "text", "text": text}]}]}))
elif a[:1] == ["run"]:
    n = int((d / "count").read_text()) + 1 if (d / "count").exists() else 1
    (d / "count").write_text(str(n))
    plan = json.loads((d / "plan.json").read_text()) if (d / "plan.json").exists() else []
    mode = plan[n - 1] if n <= len(plan) else "ok"
    (d / "lastmode").write_text(mode)
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
    if mode == "auth-nosession":     # refused before any session: still our credentials, never a fallback
        sys.stderr.write('Error: {"name": "ProviderAuthError", "data": {"providerID": "provider", "message": "token expired"}}\\n')
        sys.exit(1)
    if "--title" in a:
        (d / "title").write_text(a[a.index("--title") + 1])
    if mode == "hang":
        time.sleep(600)
    if mode == "crash":
        sys.stderr.write("panic: something broke\\n")
        sys.exit(1)
    if mode in ("perm", "permlate"):      # OpenCode auto-rejects a path outside the worktree: a line that STARTS with "!"
        sys.stderr.write("! permission requested: external_directory (/etc/x/*); auto-rejecting\\n")
        sys.stderr.flush()
        if mode == "perm":
            time.sleep(30)
        sys.exit(1)
    if mode in ("permbash", "permbashexit0"):
        sys.stderr.write("! permission requested: bash (git push origin main); auto-rejecting\\n")
        sys.stderr.flush()
        if mode == "permbash":
            time.sleep(30)
        sys.exit(0)
    if mode == "permbashhang":   # a rejection line, then a hang: the watcher's own kill (idle or total timeout) ends it
        sys.stderr.write("! permission requested: bash (git push origin main); auto-rejecting\\n")
        sys.stderr.flush()
        time.sleep(30)
    if mode == "rejectedline":
        sys.stderr.write("Error: The user rejected permission to use this specific tool call.\\n")
        sys.exit(1)
    if mode == "diffcrash":      # the model's TOOL OUTPUT lands on stderr: a diff that mentions 429 and a FileNotFoundError
        sys.stderr.write("+            raise FileNotFoundError(args[0])\\n+  # too many requests, rate limit 429, status code 503\\n")
        sys.exit(1)
    if mode == "reportcrash":    # the model stops and reports, then the process dies
        sys.stderr.write("panic: after the report\\n")
        sys.exit(1)
    if mode == "authcrash":      # a session started, then the provider refused the credentials
        sys.stderr.write('Error: {"name": "APIError", "data": {"message": "invalid key", "statusCode": 401, "isRetryable": false}}\\n')
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
                      ("exit 1", False), ("panic: something broke", False),
                      ("Error: 500", True), ("HTTP 503", True), ("HTTP/1.1 505 HTTP Version Not Supported", True),
                      ("status code 505", True), ("statusCode: 529", True), ("599 Network Connect Timeout Error", True),
                      ("503 Service Unavailable", True), ("got a 5xx from the provider", True), ("status: 500", True),
                      ("see line 503 of the file", False), ("at x.py:503", False), ("read 550 lines", False), ("port 5000 is in use", False),
                      ("exit code 512", False), ("error handling lives at line 503", False)):
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
        assert sorted(x.name for x in (d / "logs" / "run-1").glob("export*.json")) == ["export-attempt1-final.json"], \
            "the final message was exported once, under its own name, and no export.json"
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
        assert r1["kind"] == "api" and "status 429" in r1["cause"], r1
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


def test_models_listing_provider_error_is_api():
    for err, kind in (("Error: connect ETIMEDOUT 1.2.3.4:443", "api"), ("Error: 429 Too Many Requests", "api"),
                      ("Error: bad config file", "process")):
        with fake_opencode("models-err", []) as d:
            (d / "models_err").write_text(err)
            r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
            assert r["class"] == "nonzero-exit" and r["kind"] == kind, (err, r["class"], r["kind"])
            assert not (d / "count").exists(), "the listing failed before any run was started"
    return "`opencode models` failing with a network/429 line is kind api, with any other stderr it is process"


def test_stopped_and_reported_is_not_resumed():
    with fake_opencode("report", ["reportcrash", "ok"]) as d:
        final, stop, failures = chain(d)
        assert final is None and stop and not failures, (final, stop)
        r = stop[1]
        assert r["class"] == "stopped-with-report" and r["kind"] == "process" and "BLOCKED: I need file X" in r["text"], r
        assert runs_started(d) == 1, "a report is answered, not resumed over"
        rd = d / "logs" / "run-1"
        st = json.loads((rd / "state.json").read_text())
        assert st["last_message"]["finish"] == "stop" and "BLOCKED" in st["last_message"]["text"] and st.get("resumes_used", 0) == 0, st
        assert "BLOCKED" in json.loads((rd / "result.json").read_text())["text"] and (rd / "export-attempt1-read.json").exists()
    with fake_opencode("midwork", ["crash", "ok"]) as d:
        r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
        assert r["class"] == "ok" and runs_started(d) == 2, r
        st = json.loads((d / "run" / "state.json").read_text())
        assert st["last_message"]["finish"] == "tool-calls" and st["last_message"]["text"] == "partial notes", st
    return "final message + death -> stopped-with-report (process, text kept, no resume); death mid-work -> last message read and recorded, then resumed"


def test_api_failure_reads_the_session_first():
    with fake_opencode("api-read", ["apicrash", "ok"]) as d:
        lines = []
        failures = []
        final, stop = er.run_chain(["provider/model"] * 2, "pr", 5, "t", "body", BASE, HEAD, ROOT, d / "logs", "",
                                   "external-reviewer", failures, d / "data", log=lines.append)
        assert final and not stop, (final, stop)
        r1 = json.loads((d / "logs" / "run-1" / "result.json").read_text())
        assert r1["kind"] == "api" and r1["last_message"]["text"] == "partial notes", r1
        assert json.loads((d / "logs" / "run-1" / "state.json").read_text())["last_message"]["text"] == "partial notes"
        assert any("last message" in x and "partial notes" in x for x in lines), lines
    return "an api failure with a session: its last message is in result.json, state.json and the log before the next model runs"


def test_every_failure_reads_the_session_and_exports_are_per_attempt():
    with fake_opencode("unreadable", ["crash", "ok"]) as d:
        (d / "export_bad").write_text("1")
        r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
        assert r["class"] == "session-unreadable" and r["kind"] == "process" and "unreadable" in r["cause"].lower(), r
        assert runs_started(d) == 1, "an unreadable session is never resumed"
    with fake_opencode("unreadable-api", ["apicrash", "ok"]) as d:
        (d / "export_bad").write_text("1")
        final, stop, failures = chain(d)
        assert final is None and stop and not failures, (final, stop, failures)
        assert stop[1]["kind"] == "process" and "export unreadable" in stop[1]["cause"] and runs_started(d) == 1, stop[1]
    with fake_opencode("perm", ["permbash", "ok"]) as d:
        r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
        assert r["class"] == "permission-rejected" and r["kind"] == "process", r
        assert r["last_message"]["text"] == "partial notes" and runs_started(d) == 1, r
    with fake_opencode("exhausted", ["crash", "crash", "crash", "ok"]) as d:
        r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
        assert r["class"] == "nonzero-exit" and r["last_message"]["tag"] == "attempt3", r
        names = sorted(x.name for x in (d / "run").glob("export*.json"))
        assert names == ["export-attempt1-read.json", "export-attempt2-read.json", "export-attempt3-read.json"], names
    return "unreadable export -> session-unreadable/process (no resume, no fallback); permission-rejected and exhausted resumes read the session; one export file per attempt"


@contextlib.contextmanager
def main_env(d, plan, argv):
    """er.main() against the fake opencode with git and gh stubbed: records every `gh ... comment` call. Yields (code, posted, stderr, out)."""
    import io
    import contextlib as cl
    posted, calls = [], []

    def fake_sh(*args, cwd=None, check=True, text=True):
        calls.append(args)
        if args[:2] == ("gh", "pr") and args[2] == "comment":
            posted.append(args)
        if args[:2] == ("git", "worktree") and args[2] == "add":
            Path(args[-2]).mkdir(parents=True, exist_ok=True)
        if "rev-parse" in args:
            return HEAD
        if "merge-base" in args:
            return BASE
        return ""

    meta = {"title": "t", "body": "b", "headRefOid": HEAD, "baseRefName": "main", "commits": [], "labels": []}
    saved = (er.sh, er.gh_json, er.quota_skip, er.pricing_note, er.REVIEW_ROOT, er.WORK, er.REPO, sys.argv)
    er.sh, er.gh_json, er.quota_skip, er.pricing_note = fake_sh, (lambda *a, fields=None: meta), (lambda m: None), (lambda m: None)
    er.REVIEW_ROOT, er.WORK, er.REPO = d / "review", d / "work", d / "repo"
    sys.argv = ["external_review.py"] + argv
    out, err = io.StringIO(), io.StringIO()
    try:
        with cl.redirect_stdout(out), cl.redirect_stderr(err):
            code = er.main()
        yield code, posted, err.getvalue(), out.getvalue()
    finally:
        er.sh, er.gh_json, er.quota_skip, er.pricing_note, er.REVIEW_ROOT, er.WORK, er.REPO, sys.argv = saved


def test_main_exit_codes():
    two = ["--pr", "5", "--model", "provider/model,provider/model"]
    with fake_opencode("main-process", ["crash", "crash", "crash", "ok"]) as d:
        with main_env(d, None, two) as (code, posted, err, out):
            assert code == 6, (code, err)
            assert not posted, "a process failure posts nothing"
            assert "OpenCode process failure: provider/model#high: nonzero-exit" in err and "resume with --resume" in err, err
            assert runs_started(d) == 3, "no second model after a process failure"
    with fake_opencode("main-api", ["429", "429"]) as d:
        with main_env(d, None, two) as (code, posted, err, out):
            assert code == 3 and not posted and "OpenCode unavailable" in err, (code, err)
            assert runs_started(d) == 2, "both models' APIs were tried"
    with fake_opencode("main-fallback", ["429", "ok"]) as d:
        with main_env(d, None, two) as (code, posted, err, out):
            assert code == 0 and len(posted) == 1, (code, err, posted)
    return "main(): process failure -> exit 6, no post, one model; every API failing -> exit 3, no post; api then ok -> posted, exit 0"


def test_malformed_exports_are_session_unreadable():
    shapes = ["", "{}", '{"messages": "x"}', '{"messages": [1]}', '{"messages": [{"role": "assistant"}]}', "[1, 2]",
              '{"messages": [{"info": {"role": "assistant"}, "parts": "x"}]}',
              '{"messages": [{"info": {"role": "assistant"}, "parts": [{"type": "text", "text": 5}]}]}',
              '{"messages": [{"info": {"role": "assistant"}, "parts": [3]}]}', "{not json"]
    for i, shape in enumerate(shapes):
        with fake_opencode("shape%d" % i, ["crash", "ok"]) as d:
            (d / "export_bad").write_text(shape)
            r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
            assert r["class"] == "session-unreadable" and r["kind"] == "process", (shape, r["class"], r["kind"])
            assert runs_started(d) == 1, shape
    d_ok = '{"messages": []}'                       # a valid export with no message yet is readable, not an error
    with fake_opencode("shape-empty", ["crash", "ok"]) as d:
        (d / "export_bad").write_text(d_ok)
        r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
        assert r["class"] != "session-unreadable" and runs_started(d) == 2, r["class"]    # a valid, empty export is readable: it was resumed
    return "%d malformed export shapes -> session-unreadable (process), none resumed, none crashed the watcher" % len(shapes)


def test_exports_are_never_overwritten():
    with fake_opencode("no-overwrite", ["crash", "ok"]) as d:
        d.joinpath("run").mkdir()
        try:
            ow.final_text(str(d / "fake-opencode"), dict(os.environ), ROOT, "ses_fake", d / "run", "x.json")
            ow.final_text(str(d / "fake-opencode"), dict(os.environ), ROOT, "ses_fake", d / "run", "x.json")
        except FileExistsError:
            pass
        else:
            raise AssertionError("a second export under the same name overwrote the first")
    return "final_text refuses to write an export name twice"


def test_manual_resume_reads_the_session_first():
    for mode, force, want in (("reportcrash", False, "stopped-with-report"), ("reportcrash", True, "ok"), ("crash", False, "ok")):
        with fake_opencode("manual-resume", ["ok"]) as d:
            (d / "lastmode").write_text(mode)
            rd = d / "run"
            rd.mkdir()
            (rd / "state.json").write_text(json.dumps({"attempt": 1, "session": "ses_fake", "status": "running", "pid": 2 ** 22 + 99}))   # DIED: no result.json
            r = ow.run(write_brief(d), ROOT, "provider/model", rd, data_dir=d / "data", log=lambda s: None,
                       resume_session="ses_fake", force_resume=force)
            assert r["class"] == want, (mode, force, r["class"], r["cause"])
            st = json.loads((rd / "state.json").read_text())
            assert st["last_message"]["finish"] == ("stop" if mode == "reportcrash" else "tool-calls"), st
            if want == "stopped-with-report":
                assert r["kind"] == "process" and "BLOCKED" in r["text"] and not (d / "count").exists(), "refused: no run started"
            else:
                assert (d / "count").exists()
            if force and mode == "reportcrash":
                assert any(x.get("over") == "stopped-with-report" for x in st["forced_resumes"]), st
    return "manual resume of a DIED run reads the session: a report is refused (no run) unless --force-resume (logged); mid-work is resumed"


def test_refresh_listing_errors_are_api():
    for err, kind, cls in (("Error: connect ETIMEDOUT", "api", "nonzero-exit"), ("Error: weird failure", "process", "nonzero-exit"), (None, "process", "unknown-model")):
        with fake_opencode("refresh", []) as d:
            if err:
                (d / "refresh_err").write_text(err)
            r = ow.run(write_brief(d), ROOT, "opencode-go/nosuch", d / "run", data_dir=d / "data", log=lambda s: None)
            assert r["class"] == cls and r["kind"] == kind, (err, r["class"], r["kind"])
    return "`models --refresh` failing with a network line -> api, other stderr -> process, model simply absent -> unknown-model (process)"


def test_watcher_crash_is_a_process_failure():
    real = ow.run
    ow.run = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        with fake_opencode("crash-watcher", []) as d:
            final, stop, failures = chain(d)
    finally:
        ow.run = real
    assert final is None and stop and not failures, (final, stop)
    assert stop[1]["class"] == "watcher-crash" and stop[1]["kind"] == "process" and "boom" in stop[1]["cause"], stop[1]
    return "an exception inside the watcher becomes a recorded process failure (exit 6 path), not a traceback"


def test_reused_run_dir_does_not_skip_new_errors():
    with fake_opencode("reuse", ["apicrash", "ok"]) as d:
        rd = d / "run"
        rd.mkdir()
        (rd / "stderr.log").write_text("old noise\n" * 500)
        (rd / "stdout.log").write_text("old text\n" * 500)
        r = ow.run(write_brief(d), ROOT, "provider/model", rd, data_dir=d / "data", log=lambda s: None)
        assert r["class"] == "nonzero-exit" and r["kind"] == "api" and "status 429" in r["cause"], r
        assert (rd / "stderr.prev-1.log").read_text().startswith("old noise") and (rd / "stdout.prev-1.log").exists()
    return "logs already in a reused run dir are archived and the new attempt's error output is still read from byte 0"


def test_structured_errors_are_the_primary_evidence():
    J = json.dumps
    pretty = "Error: " + json.dumps({"name": "APIError", "data": {"message": "slow down", "statusCode": 429, "isRetryable": True}}, indent=2)
    api = [
        "Error: " + J({"name": "APIError", "data": {"message": "x", "statusCode": 503, "isRetryable": True}}),
        pretty,
        "Error: " + J({"name": "APIError", "data": {"message": "x", "statusCode": 529, "isRetryable": False}}),     # any 5xx
        "Error: " + J({"name": "APIError", "data": {"message": "billing", "statusCode": 402, "isRetryable": False}}),      # payment/quota stays api
        "Error: " + J({"name": "APIError", "data": {"message": "x", "isRetryable": True}}),
        "Error: " + J({"name": "AI_APICallError", "statusCode": 502, "message": "bad gateway"}),
        "Error: " + J({"name": "FetchTimeoutError", "data": {"message": "x"}}),
        "info line\n" + J({"error": {"status": 500, "message": "oops"}}) + "\nmore",
        "Error: " + J({"name": "UnknownError", "data": {"message": "provider returned 503", "ref": "err_1"}}),      # unstructured: the fallback
    ]
    process = [
        "Error: " + J({"name": "APIError", "data": {"message": "bad request", "statusCode": 400, "isRetryable": False}}),
        "Error: " + J({"name": "APIError", "data": {"message": "x", "isRetryable": False}}),
        "Error: " + J({"name": "ContextOverflowError", "data": {"message": "prompt too long; the provider said 429 rate limit"}}),
        "Error: " + J({"name": "ContentFilterError", "data": {"message": "blocked, status 503 in the text"}}),
        "Error: " + J({"name": "MessageAbortedError", "data": {"message": "aborted"}}),
        "Error: " + J({"name": "UnknownError", "data": {"message": "Unexpected server error. Check server logs for details.", "ref": "err_2"}}),
        "Error: " + J({"name": "ProviderModelNotFoundError", "data": {"providerID": "x", "modelID": "y"}}),
        "{broken json 503",
    ]
    auth = [
        "Error: " + J({"name": "APIError", "data": {"message": "bad key", "statusCode": 401, "isRetryable": False}}),
        "Error: " + J({"name": "APIError", "data": {"message": "no access", "statusCode": 403}}),
        "Error: " + J({"name": "ProviderAuthError", "data": {"providerID": "openai", "message": "token expired"}}),
        "Error: 401 Unauthorized",
        "HTTP 403 Forbidden",
        "Error: " + J({"name": "APIError", "data": {"message": "x", "statusCode": 429}}) + "\nError: " + J({"name": "ProviderAuthError", "data": {"message": "m"}}),
    ]
    for t in auth:
        assert ow.error_verdict(t)[0] == "auth" and ow.api_text(t) is None, ("should be auth (process), never api", t, ow.error_verdict(t))
    for t in api:
        assert ow.api_text(t), ("should be api", t)
    for t in process:
        got = ow.api_text(t)
        assert got is None, ("should not be api", t, got)
    assert ow.api_text("{broken json 503") is None
    fallback = [("provider returned 503", True), ("the server returned 429", True), ("responded with 529", True), ("it replied with HTTP 502", True),
                ("returned 503 lines", False), ("returned 550 bytes", False), ("see line 503", False), ("responded with 200", False)]
    for line, want in fallback:
        assert bool(ow.api_text(line)) == want, line
    return "%d api, %d auth (401/403/ProviderAuthError: process) and %d process JSON error shapes, and %d text fallbacks classify as designed" % (
        len(api), len(auth), len(process), len(fallback))


def test_models_listing_looks_only_at_its_own_stderr():
    with fake_opencode("listing-own", []) as d:
        rd = d / "run"
        rd.mkdir()
        (rd / "stderr.log").write_text("Error: 429 Too Many Requests from an earlier attempt\n")
        (d / "models_err").write_text("Error: bad config file")
        r = ow.run(write_brief(d), ROOT, "provider/model", rd, data_dir=d / "data", log=lambda s: None)
        assert r["class"] == "nonzero-exit" and r["kind"] == "process", (r["class"], r["kind"], r["cause"])
        (d / "models_err").write_text("Error: " + json.dumps({"name": "APIError", "data": {"message": "x", "statusCode": 503, "isRetryable": True}}))
        r = ow.run(write_brief(d), ROOT, "provider/model", rd, data_dir=d / "data", log=lambda s: None)
        assert r["kind"] == "api", r
    return "a listing that fails with a process-only error is process even when the run dir's old stderr holds a 429; a JSON 503 from the listing is api"


def test_refused_credentials_are_a_process_failure():
    for plan in (["authcrash", "ok"], ["auth-nosession", "ok"]):
        with fake_opencode("auth-" + plan[0], plan) as d:
            final, stop, failures = chain(d)
            assert final is None and stop and not failures, (plan, final, stop, failures)
            r = stop[1]
            assert r["kind"] == "process", r
            assert "provider credentials refused (401/403): renew the login for provider" in r["cause"], r["cause"]
            assert runs_started(d) == 1, "no resume and no second model for refused credentials"
    return "401 and ProviderAuthError (with or without a session) -> process, cause names the login to renew, no resume, no fallback"


FIXTURE = ROOT / "tests" / "fixtures" / "pr69-run"


def test_review_worktree_name_and_relative_paths_in_the_prompts():
    wt = er.review_worktree("a6c69b")
    assert wt == er.REVIEW_ROOT / "a6c69b" and "review" not in wt.name and "pr" not in wt.name, wt
    brief = er.brief_text("pr", 5, "t", "b", BASE, HEAD, "h", str(wt))
    assert "RELATIVE" in brief and "read runs/x.py" in brief and "PRINT absolute paths" in brief
    _, body = agent_parts()
    assert "relative paths" in body and "`grep` and `glob` PRINT absolute paths" in body and "`read`, `grep`, `glob`" in body
    return "worktree = <root>/<token>; brief and agent say file tools take relative paths and grep/glob print absolute ones"


def test_permission_scan_and_corrective_resume():
    saved = ow.PERM_IN_LOOP
    try:
        with fake_opencode("perm-late", ["permlate", "ok"]) as d:           # final scan after the exit finds it, then ONE corrective resume
            ow.PERM_IN_LOOP = False
            r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
            assert r["class"] == "ok" and runs_started(d) == 2, (r["class"], r["cause"])
            a2 = json.loads((d / "argv-2.json").read_text())
            assert a2[a2.index("--session") + 1] == "ses_fake" and a2[1].startswith("That path is outside your working directory; use paths relative to it."), a2
            st = json.loads((d / "run" / "state.json").read_text())
            assert st["resumes_used"] == 1 and st["perm_resumes"] == 1 and st["last_message"]["finish"] == "tool-calls", st
        with fake_opencode("perm-twice", ["perm", "perm", "ok"]) as d:      # the second rejection ends it
            ow.PERM_IN_LOOP = True
            r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
            assert r["class"] == "permission-rejected" and r["kind"] == "process" and runs_started(d) == 2, (r["class"], runs_started(d))
        with fake_opencode("perm-bash", ["permbash", "ok"]) as d:           # any other permission: exit 6 path, no resume, no fallback
            final, stop, failures = chain(d)
            assert final is None and stop and not failures and stop[1]["class"] == "permission-rejected" and runs_started(d) == 1, (stop, failures)
        with fake_opencode("perm-exit0", ["permbashexit0", "ok"]) as d:     # exit 0 after a rejection is not ok and not cut-off
            ow.PERM_IN_LOOP = False
            r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
            assert r["class"] == "permission-rejected" and r["kind"] == "process" and runs_started(d) == 1, (r["class"], r["kind"])
        with fake_opencode("perm-newline", ["rejectedline", "ok"]) as d:    # the newer wording alone
            ow.PERM_IN_LOOP = True
            r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
            assert r["class"] == "permission-rejected" and r["kind"] == "process" and runs_started(d) == 1, (r["class"], r["kind"])
    finally:
        ow.PERM_IN_LOOP = saved
    return "final scan after exit; `Error: The user rejected permission` recognised; an outside-path rejection resumed once with the corrective message, a second or any other one ends (process)"


def test_session_error_is_authoritative_and_tool_output_is_not_evidence():
    with fake_opencode("diff-stderr", ["diffcrash"] * 3) as d:              # free text on stderr (a diff) never makes an api failure
        r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", data_dir=d / "data", log=lambda s: None)
        assert r["kind"] == "process" and r["class"] == "nonzero-exit" and runs_started(d) == 3, (r["class"], r["kind"], r["cause"])
    with fake_opencode("export-503", ["diffcrash", "ok"]) as d:             # the export's info.error decides
        (d / "export_error").write_text(json.dumps({"name": "APIError", "data": {"message": "x", "statusCode": 503, "isRetryable": True}}))
        final, stop, failures = chain(d)
        assert final and failures == [("provider/model", "nonzero-exit")] and runs_started(d) == 2, (stop, failures)
        r1 = json.loads((d / "logs" / "run-1" / "result.json").read_text())
        assert r1["kind"] == "api" and "status 503" in r1["cause"] and r1["last_message"]["provider_error"]["name"] == "APIError", r1
    with fake_opencode("export-400", ["diffcrash"] * 3) as d:             # a 4xx error in the export beats a 429 in stderr text
        (d / "export_error").write_text(json.dumps({"name": "APIError", "data": {"message": "bad", "statusCode": 400, "isRetryable": False}}))
        final, stop, failures = chain(d)
        assert final is None and stop and stop[1]["kind"] == "process" and runs_started(d) == 3, (stop, failures)   # resumed twice, never handed on
    assert not ow.API_RE.search("raise FileNotFoundError(args[0])"), "ENOTFOUND must be a whole word"
    return "free text on stderr is never evidence when there is a session; the export's info.error is (api 503, process 400); FileNotFoundError is not ENOTFOUND"


def test_pr69_run_is_classified_right_offline():
    import shutil as sh
    tmp = SCRATCH / "pr69-fixture"
    tmp.mkdir()
    (tmp / "stderr.log").write_text("".join(ln[2:] if ln.startswith("> ") else ln for ln in (FIXTURE / "stderr.log.txt").read_text().splitlines(True)))
    for n in ("export-attempt1-read.json", "state.json"):
        sh.copy(FIXTURE / n, tmp / n)
    text = (tmp / "stderr.log").read_text()
    assert "FileNotFoundError(args[0])" in text and "permission requested: external_directory" in text and "The user rejected permission" in text
    assert ow.error_verdict(text) == (None, None) and ow.session_verdict(None, text) == (None, None), "the diff line is not evidence"
    got = ow.reclassify(tmp)
    assert got["class"] == "permission-rejected" and got["kind"] == "process" and got["corrective_resume"] is True, got
    assert "external_directory" in got["cause"], got
    return "PR #69's run (trimmed fixture): permission-rejected, process, resumable with the corrective message; the diff line is not api evidence"


def test_final_scan_after_timeout_kills_too():
    saved = ow.PERM_IN_LOOP
    try:
        ow.PERM_IN_LOOP = False                                   # only the final scan can see it
        for name, kw, was in (("idle", {"idle": 1.5, "total": 60}, "idle-timeout"), ("total", {"idle": 60, "total": 1.5}, "total-timeout")):
            with fake_opencode("scan-" + name, ["permbashhang", "ok"]) as d:
                r = ow.run(write_brief(d), ROOT, "provider/model", d / "run", startup=5, data_dir=d / "data", log=lambda s: None, **kw)
                assert r["class"] == "permission-rejected" and r["kind"] == "process", (name, r["class"], r["kind"], r["cause"])
                assert was in r["cause"] and runs_started(d) == 1, (name, r["cause"])
    finally:
        ow.PERM_IN_LOOP = saved
    return "a rejection line written just before an idle-timeout or total-timeout kill is permission-rejected (process), not the timeout"


def test_reclassify_picks_the_newest_export_numerically():
    tmp = SCRATCH / "numeric-exports"
    tmp.mkdir()
    (tmp / "stderr.log").write_text("")
    (tmp / "state.json").write_text(json.dumps({"session": "ses_x"}))
    (tmp / "result.json").write_text(json.dumps({"class": "nonzero-exit", "kind": "process"}))

    def export(err):
        info = {"role": "assistant", "finish": "tool-calls"}
        if err:
            info["error"] = err
        return json.dumps({"messages": [{"info": info, "parts": []}]})

    (tmp / "export-attempt2-read.json").write_text(export(None))
    (tmp / "export-attempt10-read.json").write_text(export({"name": "APIError", "data": {"message": "x", "statusCode": 503, "isRetryable": True}}))
    got = ow.reclassify(tmp)
    assert got["kind"] == "api" and "503" in got["cause"], got       # attempt10 is the newest, although "attempt10" < "attempt2" as text
    return "the newest export is chosen by attempt number (and k), not by file name order"


TESTS = ["agent_body_has_no_git_c", "agent_rules_only_deny_git_c", "brief_template_has_no_git_c",
         "prompt_the_watcher_hands_to_opencode", "api_failure_falls_to_next_model", "hang_then_resume",
         "crash_after_resumes_is_a_process_failure", "bad_format_is_a_process_failure", "progress_and_status",
         "only_stderr_is_api_evidence", "resume_limit_holds_across_invocations",
         "models_listing_provider_error_is_api", "stopped_and_reported_is_not_resumed", "api_failure_reads_the_session_first",
         "every_failure_reads_the_session_and_exports_are_per_attempt", "main_exit_codes",
         "malformed_exports_are_session_unreadable", "exports_are_never_overwritten", "manual_resume_reads_the_session_first",
         "refresh_listing_errors_are_api", "watcher_crash_is_a_process_failure",
         "reused_run_dir_does_not_skip_new_errors",
         "structured_errors_are_the_primary_evidence", "models_listing_looks_only_at_its_own_stderr",
         "refused_credentials_are_a_process_failure",
         "review_worktree_name_and_relative_paths_in_the_prompts", "permission_scan_and_corrective_resume",
         "session_error_is_authoritative_and_tool_output_is_not_evidence", "pr69_run_is_classified_right_offline",
         "final_scan_after_timeout_kills_too", "reclassify_picks_the_newest_export_numerically"]

if __name__ == "__main__":
    bad = 0
    for n in sys.argv[1:] or TESTS:
        try:
            print(f"PASS {n}: {globals()['test_' + n]()}", flush=True)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print(f"FAIL {n}: {type(e).__name__}: {e}", flush=True)
    sys.exit(1 if bad else 0)
