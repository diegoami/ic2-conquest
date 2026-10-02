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
import json
import os
import re
import stat
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import external_review as er  # noqa: E402
import opencode_watched as ow  # noqa: E402

AGENT = ROOT / ".opencode" / "agents" / "external-reviewer.md"
SCRATCH = ROOT / "rendered" / "test-reviewer-prompt"        # git-ignored, inside the repository: never TEMP
WT, BASE, HEAD = "/home/user/ic2-work/review/pr5-review-0123456789ab", "b" * 40, "a" * 40
GIT_C = re.compile(r"git\s+-C\b")

FAKE = '''#!/usr/bin/env python3
import json, os, pathlib, sys
d = pathlib.Path(os.environ["FAKE_OC_DIR"]); a = sys.argv[1:]
if a[:1] == ["models"]:
    print("provider/model")
elif a[:2] == ["debug", "agent"]:
    print(json.dumps({"name": a[2]}))
elif a[:2] == ["session", "list"]:
    t = (d / "title").read_text() if (d / "title").exists() else None
    print(json.dumps([{"id": "ses_fake", "title": t, "updated": 1}] if t else []))
elif a[:1] == ["export"]:
    text = "PR review (x)\\napprove\\nR1 a.py:1 non-blocking: x\\napprove"
    print(json.dumps({"info": {}, "messages": [{"info": {"role": "assistant", "agent": "external-reviewer", "finish": "stop"},
                                                 "parts": [{"type": "text", "text": text}]}]}))
elif a[:1] == ["run"]:
    (d / "argv.json").write_text(json.dumps(a))
    (d / "title").write_text(a[a.index("--title") + 1])
    (d / "brief.txt").write_text(open(a[a.index("-f") + 1]).read())
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


TESTS = ["agent_body_has_no_git_c", "agent_rules_only_deny_git_c", "brief_template_has_no_git_c",
         "prompt_the_watcher_hands_to_opencode"]

if __name__ == "__main__":
    bad = 0
    for n in sys.argv[1:] or TESTS:
        try:
            print(f"PASS {n}: {globals()['test_' + n]()}", flush=True)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print(f"FAIL {n}: {type(e).__name__}: {e}", flush=True)
    sys.exit(1 if bad else 0)
