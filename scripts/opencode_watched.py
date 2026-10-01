#!/usr/bin/env python3
"""Run `opencode run` under a watcher and classify how it ended.

    opencode_watched.py --brief B.md --worktree WT --model provider/model[#variant] --run-dir DIR

The result is DIR/result.json: {"class": ..., "text": <final assistant message>, ...}. The model
only ever returns text; this script and external_review.py are the only writers to GitHub.

Why a watcher (each of these cost time once):
- Run the REAL binary (default ~/.opencode/bin/opencode, or $OPENCODE_EXE), never the Windows npm
  shim under /mnt/c: killing a shim orphans the real process.
- stdin is /dev/null: `run` waits for EOF before it creates a session, which looks like a hang.
- Own data dir (XDG_DATA_HOME) so the desktop app's database, which can be migrated to a schema the
  1.x CLI cannot read, is never shared. auth.json is copied there, never read or printed.
- The brief is attached with -f and the message is ONE line placed BEFORE the flags (-f is an
  array option and swallows the next argument).
- The session is found by a unique --title with `opencode session list --format json` from the same
  cwd. Timeouts kill the whole process group: startup, idle (the session's `updated` only moves at
  step boundaries), total.
- Permission auto-rejection is a line that STARTS with `!`; the bare phrase is not matched, because a
  reviewed change that contains this very file would make the model echo the regex.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
PERM = re.compile(r"^\s*!\s*permission requested: (.+?); auto-rejecting\s*$")

CLASSES = ("ok", "no-session", "idle-timeout", "total-timeout", "exited-without-session",
           "nonzero-exit", "permission-rejected", "default-agent", "cut-off", "unknown-model",
           "unknown-agent", "no-executable")


def find_exe():
    """The native Linux opencode. Never the Windows shim under /mnt/."""
    cands = [os.environ.get("OPENCODE_EXE"), str(Path.home() / ".opencode/bin/opencode"),
             shutil.which("opencode")]
    for c in cands:
        if c and not c.startswith("/mnt/") and os.access(c, os.X_OK):
            return c
    return None


def data_home(base):
    """An own XDG_DATA_HOME with auth.json copied in (copy only: never read or print it)."""
    base = Path(base)
    dst = base / "opencode"
    dst.mkdir(parents=True, exist_ok=True)
    src = Path(os.environ.get("OPENCODE_AUTH", Path.home() / ".local/share/opencode/auth.json"))
    if src.is_file() and not (dst / "auth.json").exists():
        shutil.copyfile(src, dst / "auth.json")
        os.chmod(dst / "auth.json", 0o600)
    return str(base)


def split_model(spec):
    """'provider/model#variant' -> ('provider/model', 'variant' or None)."""
    m, _, v = spec.partition("#")
    return m, (v or None)


def oc(exe, env, cwd, *args, timeout=60):
    return subprocess.run([exe, *args], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=timeout)


def session_list(exe, env, cwd):
    """`opencode session list --format json`, parsed from the first '[' so a warning line before the JSON
    does not abort the watcher."""
    out = oc(exe, env, cwd, "session", "list", "--format", "json", "-n", "20").stdout
    i = out.find("[")
    try:
        return json.loads(out[i:]) if i >= 0 else []
    except ValueError:
        return []


def kill_tree(proc):
    """Kill the process group (it was started with its own session)."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def final_text(exe, env, cwd, session, agent, run_dir):
    """(text, finish, agent_seen) of the last assistant message, from `opencode export`. The export
    goes to a file: through a pipe a large export arrives truncated."""
    path = Path(run_dir) / "export.json"
    with open(path, "w") as f:
        subprocess.run([exe, "export", session], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                       stdout=f, stderr=subprocess.DEVNULL, timeout=120)
    out = path.read_text(errors="replace")
    i = out.find("{")
    if i < 0:
        return "", None, None
    d = json.loads(out[i:])
    msgs = [m for m in d.get("messages", []) if m.get("info", {}).get("role") == "assistant"]
    if not msgs:
        return "", None, None
    last = msgs[-1]
    text = "".join(p.get("text", "") for p in last.get("parts", []) if p.get("type") == "text")
    return text.strip(), last["info"].get("finish"), last["info"].get("agent")


def run(brief, worktree, model, run_dir, agent="external-reviewer", message=None, startup=180,
        idle=600, total=3600, data_dir=None, log=print):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    res = {"class": None, "model": model, "agent": agent, "session": None, "text": "",
           "stdout": str(run_dir / "stdout.log"), "stderr": str(run_dir / "stderr.log"),
           "cause": None}

    def done(cls, cause=None):
        res["class"], res["cause"] = cls, cause
        (run_dir / "result.json").write_text(json.dumps(res, indent=1))
        log(f"opencode run: {cls}" + (f" ({cause})" if cause else "")
            + f"; stdout {res['stdout']}; stderr {res['stderr']}")
        return res

    exe = find_exe()
    if not exe:
        return done("no-executable", "no native opencode: set OPENCODE_EXE or install ~/.opencode/bin/opencode")
    env = dict(os.environ)
    env["XDG_DATA_HOME"] = data_home(data_dir or Path.home() / "ic2-work/opencode-data")
    # The reviewer's agent (its permissions) comes from the trusted main checkout, never from the
    # worktree under review: a PR must not be able to change what its own reviewer may do.
    cfg = Path(__file__).resolve().parent.parent / ".opencode"
    if cfg.is_dir():
        env["OPENCODE_CONFIG_DIR"] = str(cfg)
    mid, variant = split_model(model)
    # Fail fast, before anything is billed.
    models = oc(exe, env, worktree, "models").stdout.split()
    if mid not in models:
        return done("unknown-model", f"{mid} is not in `opencode models`")
    a = oc(exe, env, worktree, "debug", "agent", agent)
    if a.returncode != 0:
        return done("unknown-agent", f"`opencode debug agent {agent}` exited {a.returncode}")
    try:
        if json.loads(a.stdout[a.stdout.find("{"):]).get("name") != agent:
            return done("unknown-agent", f"`opencode debug agent {agent}` returned another agent")
    except ValueError:
        return done("unknown-agent", "unreadable `opencode debug agent` output")

    title = f"review-{uuid.uuid4().hex[:10]}"
    cmd = [exe, "run", message or "Follow the attached brief exactly.", "--agent", agent,
           "--model", mid, "--dir", str(worktree), "--title", title, "-f", str(brief)]
    if variant:
        cmd += ["--variant", variant]
    out, err = open(res["stdout"], "w"), open(res["stderr"], "w")
    proc = subprocess.Popen(cmd, cwd=worktree, env=env, stdin=subprocess.DEVNULL, stdout=out,
                            stderr=err, start_new_session=True)
    t0, last_move, seen_updated, session = time.time(), time.time(), None, None
    try:
        while True:
            time.sleep(3)
            now = time.time()
            # a permission auto-rejection: a line that STARTS with "!"
            for f in (res["stdout"], res["stderr"]):
                lines = ANSI.sub("", Path(f).read_text(errors="replace")).splitlines()
                for ln in lines:
                    m = PERM.match(ln)
                    if m:
                        kill_tree(proc)
                        return done("permission-rejected", m.group(1))
            if session is None:
                for s in session_list(exe, env, worktree):
                    if s.get("title") == title:
                        session = s["id"]
                        res["session"] = session
                        last_move = now
                        log(f"opencode session started: {session} (model {model})")
                if session is None and proc.poll() is not None:
                    return done("exited-without-session", f"exit {proc.returncode}")
                if session is None and now - t0 > startup:
                    kill_tree(proc)
                    return done("no-session", f"no session within {startup}s")
            else:
                for s in session_list(exe, env, worktree):
                    if s["id"] == session and s.get("updated") != seen_updated:
                        seen_updated, last_move = s.get("updated"), now
                if proc.poll() is None and now - last_move > idle:
                    kill_tree(proc)
                    return done("idle-timeout", f"no progress for {idle}s")
            if proc.poll() is not None:
                break
            if now - t0 > total:
                kill_tree(proc)
                return done("total-timeout", f"over {total}s")
    finally:
        out.close()
        err.close()
        if proc.poll() is None:
            kill_tree(proc)
    if proc.returncode != 0:
        return done("nonzero-exit", f"exit {proc.returncode}")
    try:
        text, finish, seen = final_text(exe, env, worktree, session, agent, run_dir)
    except (ValueError, OSError, subprocess.SubprocessError) as e:
        return done("cut-off", f"the export could not be read: {e}")
    res["text"] = text
    if seen and seen != agent:
        return done("default-agent", f"the run used agent {seen!r}, not {agent!r}")
    if finish != "stop" or not text:
        return done("cut-off", f"finish={finish!r}")
    return done("ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--model", required=True, help="provider/model[#variant]")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--agent", default="external-reviewer")
    ap.add_argument("--startup", type=int, default=180)
    ap.add_argument("--idle", type=int, default=600)
    ap.add_argument("--total", type=int, default=3600)
    a = ap.parse_args()
    r = run(a.brief, a.worktree, a.model, a.run_dir, agent=a.agent, startup=a.startup, idle=a.idle,
            total=a.total)
    sys.exit(0 if r["class"] == "ok" else 1)


if __name__ == "__main__":
    main()
