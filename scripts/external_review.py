#!/usr/bin/env python3
"""External PR reviewer: an OpenCode model reviews a PR in its own git worktree and THIS script
posts the result. The model never writes to GitHub.

    external_review.py --pr 7 [--model a#variant,b,c] [--exclude-model x] [--apply-label] [--dry-run]
    external_review.py --issue 9 --kind release [--brief-file F]

Exit: 0 posted · 2 usage · 3 "OpenCode unavailable: <cause>" (nothing posted: the caller runs the Claude
fallback, Opus) · 4 posted FLAGGED (verdict unreadable or review cut off; no label; the caller reads it and
decides) · 5 the PR head moved while the review ran (nothing posted).

Flow: unique detached worktree at the PR head (removed in `finally`) -> a brief per attempt, with the PR
body pasted in -> scripts/opencode_watched.py -> validate the review's shape -> re-check the head SHA ->
ONE comment (+ a status label with --apply-label). A review is never thrown away: only "no review at all" (no
header line anywhere) falls to the next model or to exit 3; a readable review is normalised and acted on; one
whose verdict cannot be read or that looks cut off is posted with a note line, no label, exit 4.
Default: one OpenCode model, effort high; the caller falls back to Claude Opus on exit 3.
"""
import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opencode_watched as ow  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WORK = Path(os.environ.get("IC2_WORK", Path.home() / "ic2-work"))
REVIEW_ROOT = Path(os.environ.get("IC2_REVIEW_ROOT", WORK / "review"))   # outside the repo
DEFAULT_MODELS = "opencode-go/glm-5.3-flash#high"      # one OpenCode model, then Claude (exit 3 -> caller)
VERDICTS = {"approve": "status:approved", "rework": "status:rework", "decision": "status:decision"}
FATAL = {"permission-rejected", "no-executable", "unknown-agent"}     # not retried on another model


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

Worktree (your cwd, detached, read-only for you): {wt}
Base SHA: {base}
Head SHA under review: {head}
Use `git -C {wt} diff {base}...{head}`. Stay inside the worktree: a read outside it is auto-rejected and the
run is reported as permission-rejected.

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
    print(f"{len(SELF_TEST) - bad}/{len(SELF_TEST)} passed")
    return 1 if bad else 0


def effort(model):
    """Effort 'high' for every variant (see opencode_watched.effort); say so when max is lowered."""
    if ow.split_model(model)[1] == "max":
        print(f"effort: {model} lowered to #high (decision 2026-10-02)", flush=True)
    return ow.effort(model)


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
    ap.add_argument("--self-test", action="store_true", help="run the review parser over sample outputs")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.pr or a.issue):
        ap.error("one of --pr / --issue is required (or --self-test)")
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
    if not models:
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
    failures, final = [], None
    try:
        if sh("git", "-C", str(wt), "rev-parse", "HEAD") != head:
            raise RuntimeError("worktree HEAD is not the head SHA")
        extra = Path(a.brief_file).read_text() if a.brief_file else ""
        streak = []
        for m in models:
            hdr = header(kind, m, failures)
            brief = logs / f"brief-{len(failures) + 1}.md"
            brief.parent.mkdir(parents=True, exist_ok=True)
            brief.write_text(brief_text(kind, n, meta["title"], meta["body"], base, head, hdr, wt) + extra,
                             encoding="utf-8")
            r = ow.run(brief, wt, m, logs / f"run-{len(failures) + 1}", agent=a.agent,
                       data_dir=WORK / "opencode-data", log=lambda s: print(s, flush=True))
            cls = r["class"]
            if cls == "ok":
                pr = parse_review(r["text"], hdr)
                if pr["status"] != "none":               # a readable (or flagged) review is never thrown away
                    final = (m, pr)
                    break
                cls, r["cause"] = "bad-format", "no review in the final message (no header line)"
            if cls in FATAL:
                failures.append((m, cls))
                if cls == "permission-rejected":
                    print(f"permission-rejected: {r['cause']}; nothing posted", file=sys.stderr)
                break
            failures.append((m, cls))
            streak.append(cls)
            if len(streak) >= 2 and streak[-1] == streak[-2]:
                break
    finally:
        sh("git", "worktree", "remove", "--force", str(wt), check=False)
        if kind == "pr":
            sh("git", "update-ref", "-d", f"refs/review/pr{n}", check=False)
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
            sh("git", "worktree", "prune", check=False)

    if not final:
        cause = "; ".join(f"{label_of(m)}: {c}" for m, c in failures) or "no model ran"
        print(f"OpenCode unavailable: {cause}", file=sys.stderr)
        return 3
    model, pr = final
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
    if a.apply_label and not flagged:                    # a flagged review sets no label
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


if __name__ == "__main__":
    sys.exit(main())
