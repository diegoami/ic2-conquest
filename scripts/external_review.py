#!/usr/bin/env python3
"""External PR reviewer: an OpenCode model reviews a PR in its own git worktree and THIS script
posts the result. The model never writes to GitHub.

    external_review.py --pr 7 [--model a#variant,b,c] [--exclude-model x] [--apply-label] [--dry-run]
    external_review.py --issue 9 --kind release [--brief-file F]

Exit: 0 posted · 2 usage · 3 "OpenCode unavailable: <cause>" (nothing posted) · 5 the PR head moved
while the review ran (nothing posted).

Flow: unique detached worktree at the PR head (removed in `finally`) -> a brief per attempt, with the PR
body pasted in -> scripts/opencode_watched.py -> validate the review's shape -> re-check the head SHA ->
ONE comment (+ a status label with --apply-label). The chain moves to the next model only on an
infrastructure failure, never on a real verdict, and stops after two consecutive failures of one class.
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
DEFAULT_MODELS = "opencode-go/gpt-6-luna,opencode/claude-opus-5-5"
VERDICTS = {"approve": "status:approved", "rework": "status:rework", "decision": "status:decision"}
INFRA = {"no-session", "idle-timeout", "total-timeout", "exited-without-session", "nonzero-exit",
         "cut-off", "default-agent", "bad-format", "unknown-model", "unknown-agent"}
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
            names.add(m.group(1).strip().lower())
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


def validate(text, hdr):
    """Return (ok, normalized text, why). Accept a one-line flattened review only if it starts with
    header+verdict and ends with the verdict; restore its paragraph breaks."""
    t = text.strip()
    # Models often open with a sentence ("All checks done ..."): drop everything before the header line,
    # which must still be exact. Only the stripped text is posted.
    ls = t.splitlines()
    for i, ln in enumerate(ls):
        if ln.strip() == hdr:
            t = "\n".join(ls[i:]).strip()
            break
    verdicts = "|".join(VERDICTS)
    lines = [ln.rstrip() for ln in t.splitlines()]
    if len(lines) == 1 and t.startswith(hdr):
        m = re.match(re.escape(hdr) + r"\s+(" + verdicts + r")\b(.*)\b\1\s*$", t, re.S)
        if m:
            v, mid = m.group(1), m.group(2).strip()
            t = f"{hdr}\n{v}\n\n{mid}\n\n{v}"
            lines = t.splitlines()
    nz = [ln for ln in lines if ln.strip()]
    if len(nz) < 3 or nz[0].strip() != hdr:
        return False, t, "line 1 is not the header"
    v = nz[1].strip()
    if v not in VERDICTS:
        return False, t, f"line 2 {v!r} is not a verdict"
    if nz[-1].strip() != v:
        return False, t, "the verdict is not repeated as the last line"
    t = re.sub(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+(#\d+)", r"see \1", t, flags=re.I)
    return True, t, v


def ensure_labels():
    have = {x["name"] for x in json.loads(sh("gh", "label", "list", "--json", "name", "-L", "200"))}
    for lb in VERDICTS.values():
        if lb not in have:
            sh("gh", "label", "create", lb, "--description", "set by scripts/external_review.py")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pr", type=int)
    g.add_argument("--issue", type=int)
    ap.add_argument("--kind", choices=("pr", "release"), default=None)
    ap.add_argument("--brief-file", help="extra instructions appended to the generated brief")
    ap.add_argument("--model", default=DEFAULT_MODELS, help="provider/model[#variant],... (first is primary)")
    ap.add_argument("--exclude-model", default="", help="comma-separated names to skip")
    ap.add_argument("--agent", default="external-reviewer")
    ap.add_argument("--apply-label", action="store_true", help="set status:* from the verdict")
    ap.add_argument("--dry-run", action="store_true", help="print the arguments only; start no model")
    a = ap.parse_args()
    kind = a.kind or ("release" if a.issue else "pr")
    n = a.pr or a.issue
    models = [m.strip() for m in a.model.split(",") if m.strip()]
    excl = {e.strip().lower() for e in a.exclude_model.split(",") if e.strip()}

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
    models = [m for m in models if not any(e and e in m.lower() for e in excl)]
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
        (wt / "rendered").mkdir(exist_ok=True)
        extra = Path(a.brief_file).read_text() if a.brief_file else ""
        streak = []
        for m in models:
            hdr = header(kind, m, failures)
            brief = logs / f"brief-{len(failures) + 1}.md"
            brief.parent.mkdir(parents=True, exist_ok=True)
            brief.write_text(brief_text(kind, n, meta["title"], meta["body"], base, head, hdr, wt) + extra,
                             encoding="utf-8")
            r = ow.run(brief, wt, m, logs / f"run-{len(failures) + 1}", agent=a.agent, data_dir=WORK / "opencode-data", log=lambda s: print(s, flush=True))
            cls = r["class"]
            if cls == "ok":
                ok, text, why = validate(r["text"], hdr)
                if ok:
                    final = (m, text, why)
                    break
                cls, r["cause"] = "bad-format", why
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
    model, text, verdict = final
    if kind == "pr" and gh_json("pr", "view", str(n), fields="headRefOid")["headRefOid"] != head:
        print("the PR head moved during the review; nothing posted", file=sys.stderr)
        return 5
    body = logs / "comment.md"
    body.write_bytes((text + "\n").encode("utf-8"))        # UTF-8, no BOM
    noun = "issue" if kind == "release" else "pr"
    sh("gh", noun, "comment", str(n), "--body-file", str(body))
    if a.apply_label:
        ensure_labels()
        for lb in VERDICTS.values():
            if lb != VERDICTS[verdict]:
                sh("gh", noun, "edit", str(n), "--remove-label", lb, check=False)
        sh("gh", noun, "edit", str(n), "--add-label", VERDICTS[verdict])
    print(f"posted one comment on {noun} #{n}: verdict {verdict} (model {label_of(model)}); logs {logs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
