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

WORK_DEFAULT = Path(os.environ.get("IC2_WORK", Path.home() / "ic2-work"))
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
    """The reviewer's OWN OpenCode dirs, so the desktop app (2.x), which shares the default database and can
    migrate it to a schema the 1.x CLI cannot read ("no such column: project_id"), never touches them:
    XDG_DATA_HOME = <base>, XDG_CACHE_HOME = <base>/cache, XDG_STATE_HOME = <base>/state, TMPDIR = <base>/tmp, all absolute. They go
    only into the child process's environment, so the caller's own environment needs no restore.
    auth.json (API-key providers) is COPIED from the default dir when missing or older; it is never read or
    printed. OpenCode Go is not in auth.json: it comes from `opencode console login`, which lives in this data
    dir's database, so every data dir needs its own login."""
    base = Path(base).expanduser().resolve()
    dst = base / "opencode"
    dst.mkdir(parents=True, exist_ok=True)
    (base / "cache").mkdir(exist_ok=True)
    (base / "state").mkdir(exist_ok=True)
    src = Path(os.environ.get("OPENCODE_AUTH", Path.home() / ".local/share/opencode/auth.json"))
    if src.is_file() and (not (dst / "auth.json").exists() or src.stat().st_mtime > (dst / "auth.json").stat().st_mtime):
        shutil.copyfile(src, dst / "auth.json")
        os.chmod(dst / "auth.json", 0o600)
    (base / "tmp").mkdir(exist_ok=True)
    # TMPDIR too: OpenCode saves long tool results (a denial message lists all the rules) under <tmp>/opencode
    # and the model reads them back. In the shared /tmp/opencode that read is an out-of-tree access (and exposes
    # other OpenCode sessions' output); in the reviewer's own tmp the agent can allow just that path.
    return {"XDG_DATA_HOME": str(base), "XDG_CACHE_HOME": str(base / "cache"), "XDG_STATE_HOME": str(base / "state"),
            "TMPDIR": str(base / "tmp")}


# Heavy models (docs/environment.md): effort low, or medium when the task needs it, never high (the player, 2026-10-05)
HEAVY = ("openai/gpt-6.1-sol", "openai/gpt-6-sol", "openai/gpt-5.6-sol", "zai-coding-plan/glm-5.3", "opencode-go/deepseek-v4-pro",
         "openrouter/deepseek/deepseek-v4-pro")


def is_heavy(base):
    """True for a heavy model id (fast variants included, e.g. 'openai/gpt-6.1-sol-fast'); the Flash/Luna light models are not."""
    return any(base == h or base.startswith(h + "-") for h in HEAVY) and "flash" not in base


def effort(model):
    """'provider/model[#variant]' with its effort made explicit. A light model: no variant means high, and max is lowered to high
    (overkill and slower; decision 2026-10-02). A heavy model: no variant means low, and high or max is lowered to medium (the player,
    2026-10-05: low, or medium when needed, never high)."""
    base, variant = split_model(model)
    if is_heavy(base):
        return f"{base}#{'low' if variant is None else 'medium' if variant in ('high', 'max') else variant}"
    return f"{base}#{'high' if variant in (None, 'max') else variant}"


def split_model(spec):
    """'provider/model#variant' -> ('provider/model', 'variant' or None)."""
    m, _, v = spec.partition("#")
    return m, (v or None)


def oc(exe, env, cwd, *args, timeout=60):
    """Run an opencode subcommand. A hang is a result, not an exception: returncode 124, empty output."""
    try:
        return subprocess.run([exe, *args], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess([exe, *args], 124, "", f"timed out after {timeout}s")


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


def final_text(exe, env, cwd, session, run_dir):
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
    env.update(data_home(data_dir or WORK_DEFAULT / "opencode-data"))
    # The reviewer's agent (its permissions) comes from the trusted main checkout, never from the
    # worktree under review: a PR must not be able to change what its own reviewer may do.
    cfg = Path(__file__).resolve().parent.parent / ".opencode"
    if cfg.is_dir():
        env["OPENCODE_CONFIG_DIR"] = str(cfg)
        # OpenCode MERGES the project's own .opencode/ (here: the PR's, in the worktree) with this one, and a
        # PR could add an allow rule to its own reviewer ("python3 *": allow). Ignore the project config.
        env["OPENCODE_DISABLE_PROJECT_CONFIG"] = "1"
    model = effort(model)
    mid, variant = split_model(model)
    # Fail fast, before anything is billed.
    listing = oc(exe, env, worktree, "models")
    if listing.returncode != 0:
        return done("nonzero-exit", f"`opencode models` failed ({listing.returncode}): {listing.stderr.strip()[:120]}")
    models = listing.stdout.split()
    if mid not in models and mid.startswith("opencode-go/"):
        oc(exe, env, worktree, "models", "--refresh", timeout=120)      # the catalog may be stale
        models = oc(exe, env, worktree, "models").stdout.split()
    if mid not in models:
        hint = ""
        if mid.startswith("opencode-go/"):
            hint = ("; OpenCode Go comes from a console login in this data dir's database: run "
                    f"XDG_DATA_HOME={env['XDG_DATA_HOME']} XDG_CACHE_HOME={env['XDG_CACHE_HOME']} "
                    f"XDG_STATE_HOME={env['XDG_STATE_HOME']} {exe} console login (then `models opencode-go`)")
        elif not (Path(env["XDG_DATA_HOME"]) / "opencode" / "auth.json").exists():
            hint = "; no auth.json in the reviewer's data dir: log in to the provider and set OPENCODE_AUTH"
        return done("unknown-model", f"{mid} is not in `opencode models`{hint}")
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
        text, finish, seen = final_text(exe, env, worktree, session, run_dir)
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
