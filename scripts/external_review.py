#!/usr/bin/env python3
"""External PR reviewer: an OpenCode model reviews a PR in its own git worktree and THIS script
posts the result. The model never writes to GitHub.

    external_review.py --pr 7 [--model a#variant,b,c] [--exclude-model x] [--apply-label] [--dry-run]
    external_review.py --issue 9 --kind release [--brief-file F]
    external_review.py --resume <run dir>        # continue a run that stopped, in the same OpenCode session

Exit: 0 posted · 2 usage · 3 "OpenCode unavailable: <cause>" (every model's API did not answer or was skipped; nothing
posted: the caller decides the fallback) · 4 posted FLAGGED (verdict unreadable or review cut off; no label; the caller
reads it and decides) · 5 the PR head moved while the review ran (nothing posted) · 6 "OpenCode process failure: ..." (a
failure of our own process: timeout after the automatic resumes, cut-off, crash, unreadable output, permission refusal, wrong
agent, no review header; nothing posted, NO fallback to another model: diagnose it, then `--resume <run dir>`).

Flow: unique detached worktree at the PR head (removed in `finally`) -> a brief per attempt, with the PR
body pasted in -> scripts/opencode_watched.py -> validate the review's shape -> re-check the head SHA ->
ONE comment (+ a status label with --apply-label). A review is never thrown away: a readable review is normalised and acted
on; one whose verdict cannot be read or that looks cut off is posted with a note line, no label, exit 4. Only an `api` failure
(opencode_watched.py: the provider did not answer) moves the chain to the next model; a `process` failure, "no review at all"
(no header line) included, stops it with exit 6.
Default: the DEFAULT_MODELS chain, after the quota check (models whose provider is exhausted are skipped, L50). Effort: light models
#high, heavy models #low (#high/#max lowered to #medium; opencode_watched.effort). The caller falls back to Claude Opus on exit 3; on exit 6 nobody falls back: the process failure is fixed.
"""
import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import time
import urllib.request
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opencode_watched as ow  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WORK = Path(os.environ.get("IC2_WORK", Path.home() / "ic2-work"))
REVIEW_ROOT = Path(os.environ.get("IC2_REVIEW_ROOT", WORK / "review"))   # outside the repo
DEFAULT_MODELS = "openai/gpt-5.6-luna#high,minimax/MiniMax-M2.7"     # then exit 3 -> the caller (the owner, 2026-10-10: DeepSeek and Alibaba only when asked)
VERDICTS = {"approve": "status:approved", "rework": "status:rework", "decision": "status:decision"}
EXIT_PROCESS = 6                                                  # a failure of our own process: no fallback, resumable


def sh(*args, cwd=REPO, check=True, text=True):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=text)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def gh_json(*args, fields):
    return json.loads(sh("gh", *args, "--json", fields))


def label_of(model):
    """'opencode/big-pickle#high' -> 'big-pickle'."""
    return ow.split_model(model)[0].split("/")[-1]


QUOTA_URL = os.environ.get("IC2_QUOTA_URL", "http://localhost:8765")     # quota-tracker (docs/environment.md)
PROVIDERS = (("openai/", "openai"), ("zai-coding-plan/", "zai"), ("opencode-go/", "opencode_go"), ("openrouter/", "openrouter"),
             ("alibaba-token-plan/", "alibaba"), ("minimax/", "minimax"))
LUNA_WINDOW = ("openai/gpt-5.6-luna", "gpt-5.6-luna:7d")                # GPT-5.6 Luna has its own weekly pool


def fetch_quota(provider):
    """quota-tracker's record for one provider, or None when the service cannot be reached (then the chain goes on: L50)."""
    try:
        with urllib.request.urlopen(f"{QUOTA_URL}/quota/{provider}", timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def quota_skip(model, fetch=fetch_quota):
    """harness_imperial L50: the reason to skip this model now ("quota exhausted ..."), or None to use it. A provider whose status is
    'exhausted' is skipped; GPT-5.6 Luna is judged on its own 'gpt-5.6-luna:7d' window instead (usable under 95 % even when openai is
    exhausted). An unknown provider, or no answer from quota-tracker, never skips."""
    mid = ow.split_model(model)[0]
    prov = next((name for prefix, name in PROVIDERS if mid.startswith(prefix)), None)
    q = fetch(prov) if prov else None
    if not q:
        return None
    if mid == LUNA_WINDOW[0]:
        w = next((w for w in q.get("windows", []) if w.get("name") == LUNA_WINDOW[1]), None)
        if w is not None:
            return None if w.get("used_pct", 0) < 95 else f"quota exhausted ({LUNA_WINDOW[1]}, resets in {w.get('resets_in')})"
    if q.get("status") == "exhausted":
        return f"quota exhausted ({prov}, usable in {q.get('available_in')})"
    return None


def pricing_note(model, fetch=fetch_quota):
    """One line about time-of-day pricing for a model about to be used (docs/environment.md), or None. Alibaba's night discount
    (22:00-08:00 UTC+8: qwen3.8-max/flash 60% off, deepseek-v4-pro-0813 and deepseek-v4.1-flash 50% off, glm-5.3 none) and Z.ai's
    weekday peak (Mon-Fri 14:00-18:00 UTC+8 from 8 Oct 2026: glm-5.3 3x quota, glm-5.3-flash 1.2x), both from quota-tracker's
    `pricing` block."""
    mid = ow.split_model(model)[0]
    prov = next((name for prefix, name in PROVIDERS if mid.startswith(prefix)), None)
    if prov not in ("alibaba", "zai"):
        return None
    q = fetch(prov)
    if not q:
        return None
    p = q.get("pricing") or {}
    until = p.get("next_change_at")
    until = time.strftime("%H:%M", time.localtime(until)) if until else "?"
    if prov == "alibaba" and p.get("discount_now"):
        return f"pricing: alibaba night discount until {until} (qwen3.8-max/flash 60% off, deepseek-v4-pro-0813 and v4.1-flash 50% off, glm-5.3 none)"
    if prov == "zai" and p.get("peak_now"):
        return f"pricing: zai peak until {until} (glm-5.3 3x quota, glm-5.3-flash 1.2x)"
    return None


def header(kind, model, failures):
    base = "Release review" if kind == "release" else "PR review"
    names = "; ".join(f"{label_of(m)} failed: {c}" for m, c in failures)
    return f"{base} ({label_of(model)}{'; ' + names if names else ''})"


def implementer_names(pr):
    """Names to exclude from the chain: Co-Authored-By trailers and model:<name> labels."""
    names = set()
    for c in pr.get("commits", []):
        for m in re.finditer(r"Co-Authored-By:\s*([^<\n]+?)\s*(?:<|$)", c.get("messageBody", ""), re.I | re.M):
            name = m.group(1).strip().lower()
            if len(re.sub(r"[^a-z0-9]", "", name)) >= 6:      # a short or generic name would match too much
                names.add(name)
    for lb in pr.get("labels", []):
        if lb["name"].lower().startswith("model:"):
            names.add(lb["name"].split(":", 1)[1].strip().lower())
    return names


def brief_text(kind, n, title, body, base, head, hdr, wt):
    ask = ("the release gate issue below" if kind == "release" else f"pull request #{n}")
    return f"""You are the external reviewer for {ask} of ic2-conquest.

HEADER LINE (line 1 of your final message, exactly): {hdr}
ALLOWED VERDICTS (line 2, and again alone as the last line): {", ".join(VERDICTS)}
  approve = no blocking finding; rework = at least one blocking finding; decision = a choice only the player can make.

Worktree (your working directory, detached, read-only for you): {wt}
Base SHA: {base}
Head SHA under review: {head}
Your working directory IS that worktree: run git there as it is, WITHOUT -C, and never type the worktree's path
(a retyped path that is one character off is an out-of-tree access: the run is auto-rejected and lost).
TREE PROOF, your first two tool calls, separate calls: `git rev-parse --show-toplevel HEAD` (the first line must be {wt}, the
second {head}) and `git diff --name-only {base}...HEAD` ({"a release review has no diff by design: skip this one" if kind == "release" else "it must not be empty"}).
If anything is wrong you are in the wrong tree: say so in a review whose verdict is `decision` and stop.
The diff to review is `git diff {base}...HEAD`. Stay inside the worktree: a read outside it is auto-rejected and the run
is reported as permission-rejected.

Title: {title}

--- {'ISSUE' if kind == 'release' else 'PR'} BODY (pasted; do not look it up) ---
{body or '(empty)'}
--- END ---

Follow the instructions of the external-reviewer agent. Your final message is the review and nothing else:
no preamble, no summary of what you checked, no closing remark. Its exact shape (replace the angle brackets):

{hdr}
<one of: {", ".join(VERDICTS)}>
R1 <file:line> blocking|non-blocking: <what to change>
R2 <file:line> blocking|non-blocking: <what to change>
<one of: {", ".join(VERDICTS)}, the same as line 2>
"""


NOTE = "> Note from scripts/external_review.py: "
CLOSERS = re.compile(r"\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.I)


def deco(line):
    """A line without Markdown decoration: quote/heading markers, bold, italics, code, table bars."""
    s = re.sub(r"^[>#\s]+", "", line.strip())
    return s.strip("*_`~ \t|")


def plain(line):
    """deco() plus a leading 'Verdict:' and trailing punctuation: the form a verdict is read in."""
    s = re.sub(r"^(?:final\s+)?verdict\s*[:=-]\s*", "", deco(line), flags=re.I)
    prev = None
    while prev != s:                       # decoration and punctuation can nest: **`approve`.**
        prev = s
        s = s.strip("*_`~ \t|").rstrip(".,:;!?)").strip()
    return s


def verdict_of(line):
    p = plain(line).lower()
    return p if p in VERDICTS else None


def rewrite_keywords(text):
    """'fixes #551' -> 'fixes 551': GitHub closes issues from PR bodies and commits, not from comments, but
    a closing keyword in a review is still rewritten. Returns (text, [changes])."""
    changes = [m.group(0) for m in CLOSERS.finditer(text)]
    return CLOSERS.sub(lambda m: f"{m.group(1)} {m.group(2)}", text), changes


def parse_review(text, hdr):
    """Read a model's final message. Returns a dict: status 'ok' | 'unreadable' | 'cutoff' | 'none',
    text (what to post, without the note), verdict, rewrites.

    Only 'none' (no header line anywhere: tool chatter, or nothing) is a failure that falls to the next model.
    'ok' is normalised to header / verdict / findings / verdict. 'unreadable' (the verdict after the header
    cannot be read, or the two verdicts disagree) and 'cutoff' (no closing verdict among the last three
    non-empty lines) are posted anyway, flagged, with no label."""
    raw = (text or "").strip()
    lines = raw.splitlines()
    h = hdr.lower()
    start = next((i for i, ln in enumerate(lines) if deco(ln).lower().startswith(h)), None)
    if start is None:
        return {"status": "none", "text": raw, "verdict": None, "rewrites": []}
    body_lines = lines[start:]
    first = body_lines[0]
    rest = deco(first)[len(hdr):].strip(" \t:-—–*_`")
    nonempty = [(i, ln) for i, ln in enumerate(body_lines) if ln.strip()]
    verdicts = "|".join(VERDICTS)

    def result(status, post, verdict=None):
        post, rw = rewrite_keywords(post)
        return {"status": status, "text": post, "verdict": verdict, "rewrites": rw}

    flat = "\n".join(body_lines).strip()
    if rest and len(nonempty) == 1:                      # the whole review on one line
        m = re.match(r"^\W*(" + verdicts + r")\b(.*?)\b(" + verdicts + r")\W*$", rest, re.I | re.S)
        if m and m.group(1).lower() == m.group(3).lower():
            v = m.group(1).lower()
            return result("ok", "\n".join(x for x in (hdr, v, m.group(2).strip(), v) if x), v)
        m = re.match(r"^\W*(" + verdicts + r")\b", rest, re.I)
        if m and re.search(r"\b(" + verdicts + r")\W*$", rest, re.I):     # a closing verdict, but a different one
            return result("unreadable", flat)
        return result("cutoff" if m else "unreadable", flat, m.group(1).lower() if m else None)
    after = [x for x in nonempty[1:]]
    if not after:
        return result("unreadable", flat)
    v = verdict_of(after[0][1])
    if v is None:
        return result("unreadable", flat)
    tail = [x for x in after[1:]][-3:]
    close = next(((i, ln) for i, ln in reversed(tail) if verdict_of(ln)), None)
    if close is None:
        return result("cutoff", flat, v)
    if verdict_of(close[1]) != v:
        return result("unreadable", flat)
    middle = "\n".join(body_lines[after[0][0] + 1:close[0]]).strip()
    return result("ok", "\n".join(x for x in (hdr, v, middle, v) if x), v)


SELF_TEST = [
    # (name, review text, expected status, expected verdict, expect the keyword rewrite)
    ("canonical", "PR review (m)\napprove\nR1 a.py:1 non-blocking: x\napprove", "ok", "approve", False),
    ("bold header and verdict", "**PR review (m)**\n**rework**\nR1 a.py:1 blocking: x\n**rework**", "ok", "rework", False),
    ("heading, blank lines", "## PR review (m)\n\n\napprove\n\nR1 a.py:1 non-blocking: x\n\napprove", "ok", "approve", False),
    ("Verdict: prefix", "PR review (m)\nVerdict: rework\nR1 a.py:1 blocking: x\nVerdict: rework.", "ok", "rework", False),
    ("punctuated", "PR review (m)\n`decision`.\nR1 a.py:1 blocking: x\nDecision!", "ok", "decision", False),
    ("signed off", "PR review (m)\napprove\nR1 a.py:1 non-blocking: x\napprove\n\n-- glm", "ok", "approve", False),
    ("preamble, lowercase header", "All checks done.\n\npr review (M)\napprove\nR1 a.py:1 non-blocking: x\napprove", "ok", "approve", False),
    ("one line", "PR review (m) rework R1 a.py:1 blocking: x. R2 b.py:2 non-blocking: y. rework", "ok", "rework", False),
    ("closing keyword", "PR review (m)\nrework\nR1 a.py:1 blocking: this fixes #551 for good\nrework", "ok", "rework", True),
    ("no closing verdict", "PR review (m)\napprove\nR1 a.py:1 non-blocking: x\nR2 b.py:2 non-blocking: y", "cutoff", "approve", False),
    ("unreadable verdict", "PR review (m)\nlooks good to me\nR1 a.py:1 non-blocking: x\nlooks good", "unreadable", None, False),
    ("verdicts disagree", "PR review (m)\napprove\nR1 a.py:1 blocking: x\nrework", "unreadable", None, False),
    ("one line, verdicts disagree", "PR review (m) approve R1 a.py:1 blocking: x. rework", "unreadable", None, False),
    ("tool chatter only", "$ git diff\nran 3 commands\ndone", "none", None, False),
    ("empty", "", "none", None, False),
]


def self_test():
    bad = 0
    for name, text, status, verdict, rewrote in SELF_TEST:
        r = parse_review(text, "PR review (m)")
        ok = (r["status"] == status and r["verdict"] == verdict and bool(r["rewrites"]) == rewrote
              and (status != "ok" or (r["text"].splitlines()[0] == "PR review (m)" and r["text"].splitlines()[-1] == verdict)))
        if rewrote:
            ok = ok and "fixes 551" in r["text"] and "#551" not in r["text"]
        print(f"{'PASS' if ok else 'FAIL'} {name}: {r['status']} {r['verdict']}")
        bad += 0 if ok else 1
    n = len(SELF_TEST)
    q = {"openai": {"status": "exhausted", "available_in": "2h",
                    "windows": [{"name": "7d", "used_pct": 99}, {"name": "gpt-5.6-luna:7d", "used_pct": 10, "resets_in": "3d"}]},
         "zai": {"status": "exhausted", "available_in": "1h", "windows": []},
         "opencode_go": {"status": "ok", "windows": []},
         "alibaba": {"status": "ok", "windows": [], "pricing": {"discount_now": True, "next_change_at": 1791330000}},
         "minimax": {"status": "exhausted", "available_in": "4h", "windows": []}}
    lunafull = dict(q, openai=dict(q["openai"], windows=[{"name": "gpt-5.6-luna:7d", "used_pct": 96, "resets_in": "3d"}]))
    qpeak = dict(q, zai={"status": "ok", "windows": [], "pricing": {"peak_now": True, "next_change_at": 1791330000}})
    qoffpeak = dict(q, zai={"status": "ok", "windows": [], "pricing": {"peak_now": False, "next_change_at": 1791330000}})
    for name, model, data, skip in (
            ("quota: exhausted provider skipped", "zai-coding-plan/glm-5.3#low", q, True),
            ("quota: ok provider used", "opencode-go/deepseek-v4.1-flash#high", q, False),
            ("quota: Luna on its own pool though openai is exhausted", "openai/gpt-5.6-luna#high", q, False),
            ("quota: Sol skipped when openai is exhausted", "openai/gpt-6.1-sol#low", q, True),
            ("quota: Luna skipped when its own window is full", "openai/gpt-5.6-luna#high", lunafull, True),
            ("quota: alibaba model used while alibaba has quota", "alibaba-token-plan/qwen3.8-max#low", q, False),
            ("quota: minimax model skipped when minimax is exhausted", "minimax/MiniMax-M3#thinking", q, True),
            ("quota: no service, nothing skipped", "zai-coding-plan/glm-5.3#low", {}, False)):
        got = quota_skip(model, fetch=lambda p, d=data: d.get(p))
        ok = bool(got) == skip
        print(f"{'PASS' if ok else 'FAIL'} {name}: {got}")
        bad += 0 if ok else 1
        n += 1
    for name, model, data, want in (
            ("pricing: alibaba night discount noted", "alibaba-token-plan/qwen3.8-max#low", q, "60% off"),
            ("pricing: no note while zai is off-peak", "zai-coding-plan/glm-5.3#low", qoffpeak, None),
            ("pricing: zai peak noted", "zai-coding-plan/glm-5.3#low", qpeak, "3x quota"),
            ("pricing: nothing for a provider without pricing", "opencode-go/deepseek-v4.1-flash#high", q, None)):
        got = pricing_note(model, fetch=lambda p, d=data: d.get(p))
        ok = (got or "") .count(want or "") > 0 if want else got is None
        print(f"{'PASS' if ok else 'FAIL'} {name}: {got}")
        bad += 0 if ok else 1
        n += 1
    for model, want in (("openai/gpt-6.1-sol", "openai/gpt-6.1-sol#low"), ("openai/gpt-6.1-sol#high", "openai/gpt-6.1-sol#medium"),
                        ("zai-coding-plan/glm-5.3#max", "zai-coding-plan/glm-5.3#medium"), ("openai/gpt-6.1-sol#medium", "openai/gpt-6.1-sol#medium"),
                        ("openai/gpt-6.1-sol-fast", "openai/gpt-6.1-sol-fast#low"), ("zai-coding-plan/glm-5.3-flash", "zai-coding-plan/glm-5.3-flash#high"),
                        ("openai/gpt-5.6-luna", "openai/gpt-5.6-luna#high"), ("opencode-go/deepseek-v4.1-flash#max", "opencode-go/deepseek-v4.1-flash#high"),
                        ("minimax/MiniMax-M3", "minimax/MiniMax-M3#thinking"),
                        ("minimax/MiniMax-M3#high", "minimax/MiniMax-M3#thinking"),
                        ("minimax/MiniMax-M3#none", "minimax/MiniMax-M3#none"),
                        ("minimax/MiniMax-M3#thinking", "minimax/MiniMax-M3#thinking"),
                        ("minimax/MiniMax-M2.7", "minimax/MiniMax-M2.7"),
                        ("minimax/MiniMax-M2.7#high", "minimax/MiniMax-M2.7"),
                        ("alibaba-token-plan/deepseek-v4-pro-0813", "alibaba-token-plan/deepseek-v4-pro-0813#high"),
                        ("alibaba-token-plan/deepseek-v4-pro-0813#max", "alibaba-token-plan/deepseek-v4-pro-0813#high"),
                        ("alibaba-token-plan/deepseek-v4-pro-0813#low", "alibaba-token-plan/deepseek-v4-pro-0813#high"),
                        ("alibaba-token-plan/qwen3.8-max", "alibaba-token-plan/qwen3.8-max#low"),
                        ("alibaba-token-plan/qwen3.8-max#high", "alibaba-token-plan/qwen3.8-max#medium"),
                        ("alibaba-token-plan/qwen3.8-flash", "alibaba-token-plan/qwen3.8-flash#medium"),
                        ("alibaba-token-plan/qwen3.8-flash#high", "alibaba-token-plan/qwen3.8-flash#medium"),
                        ("alibaba-token-plan/qwen3.8-flash#low", "alibaba-token-plan/qwen3.8-flash#low"),
                        ("alibaba-token-plan/deepseek-v4.1-flash", "alibaba-token-plan/deepseek-v4.1-flash#high"),
                        ("alibaba-token-plan/deepseek-v4.1-flash#medium", "alibaba-token-plan/deepseek-v4.1-flash#high"),
                        ("alibaba-token-plan/glm-5.3", "alibaba-token-plan/glm-5.3#low")):
        got = ow.effort(model)
        ok = got == want
        print(f"{'PASS' if ok else 'FAIL'} effort {model}: {got}")
        bad += 0 if ok else 1
        n += 1
    chain = [ow.split_model(m)[0] for m in DEFAULT_MODELS.split(",")]
    ok = chain == ["openai/gpt-5.6-luna", "minimax/MiniMax-M2.7"]      # the owner's decision 2026-10-10: no DeepSeek, no Alibaba
    print(f"{'PASS' if ok else 'FAIL'} default chain: {chain}")
    bad += 0 if ok else 1
    n += 1
    print(f"{n - bad}/{n} passed")
    return 1 if bad else 0


def effort(model):
    """The model with its effort made explicit (opencode_watched.effort: light #high, heavy #low, heavy #high/#max -> #medium); says so when
    an explicit variant is lowered."""
    out = ow.effort(model)
    v = ow.split_model(model)[1]
    if v is not None and out != model:
        print(f"effort: {model} lowered to #{ow.split_model(out)[1]} (decisions 2026-10-02, 2026-10-05)", flush=True)
    return out


def excluded(model, excl):
    """True if the model is one of the excluded names (the implementer's): compared without punctuation,
    so the trailer 'DeepSeek V4.1 Flash' matches 'opencode-go/deepseek-v4.1-flash'."""
    flat = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    return any(e and flat(e) in flat(ow.split_model(model)[0]) for e in excl)


def ensure_labels():
    have = {x["name"] for x in json.loads(sh("gh", "label", "list", "--json", "name", "-L", "200"))}
    for lb in VERDICTS.values():
        if lb not in have:
            sh("gh", "label", "create", lb, "--description", "set by scripts/external_review.py")


def drop_worktree(wt, kind, n):
    sh("git", "worktree", "remove", "--force", str(wt), check=False)
    if kind == "pr":
        sh("git", "update-ref", "-d", f"refs/review/pr{n}", check=False)
    if Path(wt).exists():
        shutil.rmtree(wt, ignore_errors=True)
        sh("git", "worktree", "prune", check=False)


def judge(r, hdr, run_dir):
    """One finished ow.run -> (final review or None, r). Only a readable (or flagged) review is final. An ok run whose final message
    has no header line is a `bad-format` PROCESS failure (the class and kind are written back to result.json and state.json: the
    model ended its turn without the review, which is ours to diagnose, not another model's to redo)."""
    if r["class"] == "ok":
        pr = parse_review(r["text"], hdr)
        if pr["status"] != "none":
            return pr, r
        r["class"], r["kind"], r["cause"] = "bad-format", "process", "no review in the final message (no header line)"
        ow.write_json(Path(run_dir) / "result.json", r)
        st = ow.read_json(Path(run_dir) / "state.json") or {}
        st["status"] = "bad-format"
        ow.write_json(Path(run_dir) / "state.json", st)
        (Path(run_dir) / "status.txt").write_text((ow.describe(run_dir) or "") + "\n")
    return None, r


def process_message(model, r):
    """The line printed on exit 6: what failed, where its record is, how to continue it."""
    rd = Path(r["stdout"]).parent
    sid = r.get("session")
    return (f"OpenCode process failure: {model}: {r['class']}: {r.get('cause')}; session {sid or 'none'}; run dir {rd}; "
            + (f"resume with --resume {rd}" if sid else "no session to resume: fix the cause and run again"))


def run_chain(models, kind, n, title, body, base, head, wt, logs, extra, agent, failures, data_dir, log=print):
    """Try the models in order. Returns (final, stop): final = (model, parsed review) or None; stop = (model, result) when a PROCESS
    failure ended the chain (nothing falls through: that failure is diagnosed and resumed, not handed to another model). Only an
    `api` failure (the provider did not answer) is appended to `failures` and moves to the next model."""
    for m in models:
        hdr = header(kind, m, failures)
        k = len(failures) + 1
        brief = logs / f"brief-{k}.md"
        brief.parent.mkdir(parents=True, exist_ok=True)
        brief.write_text(brief_text(kind, n, title, body, base, head, hdr, wt) + extra, encoding="utf-8")
        meta = {"kind": kind, "number": n, "head": head, "base": base, "title": title, "hdr": hdr}
        r = ow.run(brief, wt, m, logs / f"run-{k}", agent=agent, data_dir=data_dir, log=log, meta=meta)
        pr, r = judge(r, hdr, logs / f"run-{k}")
        if pr:
            return (m, pr), None
        if r["kind"] != "api":
            return None, (m, r)
        failures.append((m, r["class"]))
    return None, None


def post_review(kind, n, model, pr, logs, head, apply_label):
    """The posting half: head re-check, ONE comment, optional label. Exit code as documented at the top."""
    flagged = pr["status"] in ("unreadable", "cutoff")
    note = {"unreadable": "verdict unreadable", "cutoff": "review may be cut off"}.get(pr["status"])
    text, verdict = (NOTE + note + "\n\n" if flagged else "") + pr["text"], pr["verdict"]
    for c in pr["rewrites"]:
        print(f"rewrote closing keyword: {c!r}", flush=True)
    if kind == "pr" and gh_json("pr", "view", str(n), fields="headRefOid")["headRefOid"] != head:
        print("the PR head moved during the review; nothing posted", file=sys.stderr)
        return 5
    body = logs / "comment.md"
    body.write_bytes((text + "\n").encode("utf-8"))        # UTF-8, no BOM
    noun = "issue" if kind == "release" else "pr"
    sh("gh", noun, "comment", str(n), "--body-file", str(body))
    if apply_label and not flagged:                      # a flagged review sets no label
        ensure_labels()
        for lb in VERDICTS.values():
            if lb != VERDICTS[verdict]:
                sh("gh", noun, "edit", str(n), "--remove-label", lb, check=False)
        sh("gh", noun, "edit", str(n), "--add-label", VERDICTS[verdict])
    if flagged:
        print(f"posted one FLAGGED comment on {noun} #{n} ({note}; model {label_of(model)}); no label set; "
              f"read it and decide; logs {logs}", file=sys.stderr)
        return 4
    print(f"posted one comment on {noun} #{n}: verdict {verdict} (model {label_of(model)}); logs {logs}")
    return 0


def resume_run(run_dir, apply_label):
    """--resume <run dir>: continue the recorded OpenCode session where it stopped. Recreates the worktree at the recorded head
    (exit 5 if the PR head, or origin/main for a release review, moved since), continues the SAME session, then parses and posts
    as usual. The run dir (and its earlier results, kept as result.prev-N.json) is never deleted."""
    rd = Path(run_dir).resolve()
    st = ow.read_json(rd / "state.json")
    if not st or st.get("kind") not in ("pr", "release") or not st.get("session") or not st.get("head"):
        print(f"{rd}: no resumable state.json (needs kind, number, head and a session)", file=sys.stderr)
        return 2
    kind, n, head = st["kind"], st["number"], st["head"]
    if ow.pid_alive(st.get("pid")) and st.get("status") in ("starting", "running", "resuming"):
        print(f"{rd}: the run is still going (pid {st['pid']}); not resuming it twice", file=sys.stderr)
        return 2
    if kind == "release":
        sh("git", "fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main")
        cur = sh("git", "rev-parse", "refs/remotes/origin/main")
    else:
        cur = gh_json("pr", "view", str(n), fields="headRefOid")["headRefOid"]
        sh("git", "fetch", "-q", "origin", f"+pull/{n}/head:refs/review/pr{n}")
    if cur != head:
        if kind == "pr":
            sh("git", "update-ref", "-d", f"refs/review/pr{n}", check=False)
        print(f"the {'PR head' if kind == 'pr' else 'origin/main'} moved since the run ({head[:12]} -> {cur[:12]}); nothing resumed, nothing posted",
              file=sys.stderr)
        return 5
    wt = Path(st["worktree"])
    try:
        REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
        if wt.exists():
            drop_worktree(wt, "release", n)                 # a leftover tree: recreate it clean at the recorded head
        sh("git", "worktree", "add", "--detach", str(wt), head)
    except Exception:
        if kind == "pr":
            sh("git", "update-ref", "-d", f"refs/review/pr{n}", check=False)
        raise
    try:
        r = ow.run(st["brief"], wt, st["model"], rd, agent=st["agent"], data_dir=st["data_dir"], log=lambda s: print(s, flush=True),
                   resume_session=st["session"], startup=st.get("startup", 180), idle=st.get("idle", 600), total=st.get("total", 3600))
        pr, r = judge(r, st["hdr"], rd)
    finally:
        drop_worktree(wt, kind, n)
    if pr:
        return post_review(kind, n, st["model"], pr, rd.parent, head, apply_label)
    if r["kind"] == "api":
        print(f"OpenCode unavailable: {label_of(st['model'])}: {r['class']}: {r.get('cause')}; run dir {rd}", file=sys.stderr)
        return 3
    print(process_message(st["model"], r), file=sys.stderr)
    return EXIT_PROCESS


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--pr", type=int)
    g.add_argument("--issue", type=int)
    ap.add_argument("--kind", choices=("pr", "release"), default=None)
    ap.add_argument("--brief-file", help="extra instructions appended to the generated brief")
    ap.add_argument("--model", default=DEFAULT_MODELS, help="provider/model[#variant],... (first is primary)")
    ap.add_argument("--exclude-model", default="", help="comma-separated names to skip")
    ap.add_argument("--agent", default="external-reviewer")
    ap.add_argument("--apply-label", action="store_true", help="set status:* from the verdict")
    ap.add_argument("--dry-run", action="store_true", help="print the arguments only; start no model; post nothing")
    ap.add_argument("--review-file", help="offline: parse this file as the model's final message and print what "
                    "would be posted, its note line, the label and the exit code. No model runs, nothing is posted")
    ap.add_argument("--resume", metavar="RUN_DIR", help="continue a run that stopped (its run dir under rendered/<kind><n>-<token>/run-<k>), "
                    "in the same OpenCode session, then parse and post as usual; exit 5 if the PR head moved")
    ap.add_argument("--self-test", action="store_true", help="run the review parser over sample outputs")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.resume:
        return resume_run(a.resume, a.apply_label)
    if not (a.pr or a.issue):
        ap.error("one of --pr / --issue is required (or --self-test or --resume)")
    kind = a.kind or ("release" if a.issue else "pr")
    n = a.pr or a.issue
    models = [effort(m.strip()) for m in a.model.split(",") if m.strip()]
    excl = {e.strip().lower() for e in a.exclude_model.split(",") if e.strip()}

    if a.review_file:                                    # offline: parse a saved review, bill nothing
        hdr = header(kind, models[0], [])
        r = parse_review(Path(a.review_file).read_text(encoding="utf-8"), hdr)
        flagged = r["status"] in ("unreadable", "cutoff")
        note = {"unreadable": "verdict unreadable", "cutoff": "review may be cut off"}.get(r["status"])
        code = {"ok": 0, "none": 3}.get(r["status"], 4)
        print(f"status {r['status']}; verdict {r['verdict']}; label "
              f"{VERDICTS[r['verdict']] if r['status'] == 'ok' and a.apply_label else 'none'}; exit {code}")
        for c in r["rewrites"]:
            print(f"rewrote closing keyword: {c!r}")
        if r["status"] != "none":
            print("---- would post ----")
            print((NOTE + note + "\n\n" if flagged else "") + r["text"])
        return code

    if a.dry_run:
        print(json.dumps({"kind": kind, "number": n, "models": models, "exclude": sorted(excl),
                          "apply_label": a.apply_label, "worktree_root": str(REVIEW_ROOT),
                          "opencode": ow.find_exe(), "agent": a.agent}, indent=1))
        return 0

    if kind == "release":
        meta = gh_json("issue", "view", str(n), fields="title,body")
        sh("git", "fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main")
        head = base = sh("git", "rev-parse", "refs/remotes/origin/main")
    else:
        meta = gh_json("pr", "view", str(n), fields="title,body,headRefOid,baseRefName,commits,labels")
        bref = f"refs/remotes/origin/{meta['baseRefName']}"
        # explicit refspecs: a bare `git fetch origin <branch>` only reliably sets FETCH_HEAD
        sh("git", "fetch", "-q", "origin", f"+pull/{n}/head:refs/review/pr{n}",
           f"+refs/heads/{meta['baseRefName']}:{bref}")
        head = sh("git", "rev-parse", f"refs/review/pr{n}")
        base = sh("git", "merge-base", bref, head)
        excl |= implementer_names(meta)
    models = [m for m in models if not excluded(m, excl)]      # the implementer never reviews its own PR
    skipped = []                                               # L50: a model whose provider is out of quota is skipped, and the header says so
    for m in list(models):
        why = quota_skip(m)
        if why:
            print(f"skipping {m}: {why}", flush=True)
            skipped.append((m, why))
            models.remove(m)
        else:
            note = pricing_note(m)
            if note:
                print(f"{m}: {note}", flush=True)
    if not models:
        if skipped:
            if kind == "pr":
                sh("git", "update-ref", "-d", f"refs/review/pr{n}", check=False)
            print("OpenCode unavailable: " + "; ".join(f"{label_of(m)}: {w}" for m, w in skipped), file=sys.stderr)
            return 3
        if kind == "pr":
            sh("git", "update-ref", "-d", f"refs/review/pr{n}", check=False)
        print("OpenCode unavailable: every model is excluded", file=sys.stderr)
        return 3

    token = secrets.token_hex(3)
    wt = REVIEW_ROOT / f"{kind}{n}-review-{token}"
    logs = REPO / "rendered" / f"{kind}{n}-{token}"
    try:
        REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
        sh("git", "worktree", "add", "--detach", str(wt), head)
    except Exception:
        if kind == "pr":
            sh("git", "update-ref", "-d", f"refs/review/pr{n}", check=False)
        raise
    failures, final, stop = list(skipped), None, None
    try:
        if sh("git", "-C", str(wt), "rev-parse", "HEAD") != head:
            raise RuntimeError("worktree HEAD is not the head SHA")
        extra = Path(a.brief_file).read_text() if a.brief_file else ""
        final, stop = run_chain(models, kind, n, meta["title"], meta["body"], base, head, wt, logs, extra, a.agent, failures,
                                WORK / "opencode-data", log=lambda s: print(s, flush=True))
    finally:
        drop_worktree(wt, kind, n)      # the run dirs under logs stay: they are the record a --resume continues

    if stop:                            # our own process failed: nothing posted, no other model
        print(process_message(*stop), file=sys.stderr)
        return EXIT_PROCESS
    if not final:
        cause = "; ".join(f"{label_of(m)}: {c}" for m, c in failures) or "no model ran"
        print(f"OpenCode unavailable: {cause}", file=sys.stderr)
        return 3
    return post_review(kind, n, final[0], final[1], logs, head, a.apply_label)


if __name__ == "__main__":
    sys.exit(main())
