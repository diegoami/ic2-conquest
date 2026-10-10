#!/usr/bin/env python3
"""Run `opencode run` under a watcher and classify how it ended.

    opencode_watched.py --brief B.md --worktree WT --model provider/model[#variant] --run-dir DIR

The result is DIR/result.json: {"class": ..., "kind": null|"api"|"process", "text": <final assistant message>, ...}; DIR also
gets state.json, progress.jsonl and status.txt while it runs (resume and status: docs/external-review.md). The model
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
         "openrouter/deepseek/deepseek-v4-pro", "alibaba-token-plan/deepseek-v4-pro-0813", "alibaba-token-plan/qwen3.8-max",
         "alibaba-token-plan/glm-5.3", "minimax/MiniMax-M3")

# The variants each of the new providers' models actually offers (`opencode models --verbose`, 2026-10-06), and the variant to use
# when the generic ladder (heavy #low / light #high, with heavy #high/#max lowered to #medium) lands outside that set: the
# normalisation must never invent a variant the model does not offer. A model listed with () offers no variant at all: nothing
# may be appended to it. Models absent from OFFERS take the generic ladder unchanged.
OFFERS = {
    "minimax/MiniMax-M3": ("none", "thinking"),                 # thinking is its high (the player, 2026-10-06)
    "minimax/MiniMax-M2.7": (),
    "alibaba-token-plan/deepseek-v4-pro-0813": ("high", "max"),  # no low: heavy default high (the player, 2026-10-06)
    "alibaba-token-plan/qwen3.8-max": ("low", "medium"),
    "alibaba-token-plan/qwen3.8-flash": ("low", "medium"),       # no plain high: light default medium
    "alibaba-token-plan/deepseek-v4.1-flash": ("low", "high", "max"),
    "alibaba-token-plan/glm-5.3": ("low", "high", "max"),
}
DEFAULT_VARIANT = {
    "minimax/MiniMax-M3": "thinking",
    "alibaba-token-plan/deepseek-v4-pro-0813": "high",
    "alibaba-token-plan/qwen3.8-max": "low",
    "alibaba-token-plan/qwen3.8-flash": "medium",
    "alibaba-token-plan/deepseek-v4.1-flash": "high",
    "alibaba-token-plan/glm-5.3": "low",
}


def is_heavy(base):
    """True for a heavy model id (fast variants included, e.g. 'openai/gpt-6.1-sol-fast'); the Flash/Luna light models are not."""
    return any(base == h or base.startswith(h + "-") for h in HEAVY) and "flash" not in base


def effort(model):
    """'provider/model[#variant]' with its effort made explicit. A light model: no variant means high, and max is lowered to high
    (overkill and slower; decision 2026-10-02). A heavy model: no variant means low, and high or max is lowered to medium (the player,
    2026-10-05: low, or medium when needed, never high). A model in OFFERS never gets a variant it does not offer: an unoffered
    result becomes its DEFAULT_VARIANT (every DEFAULT_VARIANT value is one of its model's OFFERS), and a model with no variants
    at all keeps no suffix."""
    base, variant = split_model(model)
    if is_heavy(base):
        variant = 'low' if variant is None else 'medium' if variant in ('high', 'max') else variant
    else:
        variant = 'high' if variant in (None, 'max') else variant
    offered = OFFERS.get(base)
    if offered is not None:
        if not offered:
            return base
        if variant not in offered:
            variant = DEFAULT_VARIANT[base]
    return base if variant is None else f"{base}#{variant}"


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
        data = json.loads(out[i:]) if i >= 0 else []
    except ValueError:
        return []
    return [x for x in data if isinstance(x, dict) and x.get("id")] if isinstance(data, list) else []


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


def final_text(exe, env, cwd, session, run_dir, fname):
    """(text, finish, agent_seen) of the last assistant message, from `opencode export`. The export goes to a file (through a pipe a
    large export arrives truncated), opened with "x": an export is a measurement and is never overwritten (CLAUDE.md rule 6), so
    every call needs its own fname. ValueError when the export is empty, not JSON, or not shaped like an export (messages a list of
    {info: {...}, parts: [...]}): the callers turn that into a process failure, never a crash."""
    path = Path(run_dir) / fname
    with open(path, "x") as f:
        r = subprocess.run([exe, "export", session], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                           stdout=f, stderr=subprocess.DEVNULL, timeout=120)
    out = path.read_text(errors="replace")
    i = out.find("{")
    if i < 0:
        raise ValueError(f"empty export (exit {r.returncode})")
    d = json.loads(out[i:])
    if not isinstance(d, dict) or not isinstance(d.get("messages"), list):
        raise ValueError("export has no messages list")
    last = None
    for m in d["messages"]:
        if not isinstance(m, dict) or not isinstance(m.get("info"), dict):
            raise ValueError("export message without info")
        if m["info"].get("role") == "assistant":
            if not isinstance(m.get("parts"), list) or not all(isinstance(x, dict) for x in m["parts"]):
                raise ValueError("assistant message without a parts list")
            last = m
    if last is None:
        return "", None, None
    texts = [x.get("text", "") for x in last["parts"] if x.get("type") == "text"]
    if not all(isinstance(t, str) for t in texts):
        raise ValueError("text part is not a string")
    return "".join(texts).strip(), last["info"].get("finish"), last["info"].get("agent")


# ---- failure kinds, state, progress (opencode resilience, 2026-10-10) --------------------------------------------------
# A failure of an OpenCode run is never normal. It has one of two kinds, and only the first may move a chain to another model:
#   api     the provider did not answer: no session ever started, or provider error text (429, rate limit, 5xx/overloaded,
#           quota/usage limit, network). The next model may be tried; nothing was wrong with our process.
#   process everything else (timeouts, cut-off, crash, unreadable output, permission refusal, wrong agent, our own setup):
#           diagnose and fix it; never hand it to another model. The run is resumable (state.json, --session).
ALWAYS_API = ("no-session", "exited-without-session")
ALWAYS_PROCESS = ("unknown-model", "no-executable", "unknown-agent", "permission-rejected", "default-agent", "stopped-with-report",
                  "session-unreadable")
RESUMABLE = ("idle-timeout", "total-timeout", "nonzero-exit")      # continued in the SAME session, up to RESUMES times
RESUMES = 2
RESUME_MSG = "Continue where you stopped; finish the task in the attached brief and end with the final message it asks for."
TICK = 3                  # seconds between checks (the tests lower it)
PROGRESS_EVERY = 30       # seconds between progress lines
API_RE = re.compile(
    # every 5xx counts, but only as a status: after "status", "status code", "HTTP[/1.1]" or "Error", before an error word, or as "5xx";
    # a bare number ("line 503", "x.py:503") never does
    r"\b429\b|rate[ _-]?limit|too many requests|\b(?:status(?:[ _-]?code)?|http(?:/[\d.]+)?|error)\W{0,3}5\d\d\b"
    r"|\b5\d\d\b\W{0,3}(?:\w+ ){0,3}(?:error|unavailable|gateway|overloaded|timeout)|\b5xx\b"
    r"|internal server error|overloaded|service unavailable|bad gateway|gateway time-?out|quota|usage[ _-]limit|insufficient"
    r"|ECONNRESET|ETIMEDOUT|ECONNREFUSED|ENOTFOUND|EAI_AGAIN|network error|fetch failed|socket hang up|connection (?:reset|refused|error)", re.I)


def api_evidence(res, offsets=(0, 0)):
    """The first provider-error line OpenCode wrote to STDERR in the current attempt (after the byte offset offsets[0]), or None.
    stdout is never read: it carries the model's own text and the tool output (a review of this very file says "429" and "rate
    limit"), so text there must never make a run look like an API failure. OpenCode 1.18.34 prints its errors to stderr and leaves
    stdout empty (forced 2026-10-10 with an unknown provider in a throwaway data dir: stderr `Error: {"name": ..., "data":
    {"message": ...}}`, stdout empty, exit 1)."""
    try:
        data = Path(res["stderr"]).read_bytes()[offsets[0]:].decode(errors="replace")
    except OSError:
        return None
    for ln in ANSI.sub("", data).splitlines():
        if API_RE.search(ln):
            return ln.strip()[:200]
    return None


def keep_prev(path):
    """Measurements are never overwritten (CLAUDE.md rule 6): move an existing file to <stem>.prev-N<ext> before it is rewritten."""
    path = Path(path)
    if path.exists():
        k = 1
        while path.with_name(f"{path.stem}.prev-{k}{path.suffix}").exists():
            k += 1
        path.rename(path.with_name(f"{path.stem}.prev-{k}{path.suffix}"))


def resume_refusal(run_dir, resumes=None):
    """None, or why a manual --resume is refused: the run already used its resumes (automatic ones and earlier manual ones, counted
    in state.json), and another needs --force-resume (a human decision after a fix)."""
    st = read_json(Path(run_dir) / "state.json") or {}
    used, limit = st.get("resumes_used", 0), RESUMES if resumes is None else resumes
    if used >= limit:
        return (f"{run_dir}: this run already used {used} of {limit} resumes; find and fix the cause first (read the session's final message), "
                "then resume once more with --force-resume (logged in state.json)")
    return None


def write_json(path, obj):
    """Atomic: a reader (opencode_status.py) never sees half a file."""
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    os.replace(tmp, path)


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def snapshot(data_home_dir, session, worktree=""):
    """Progress of a session from OpenCode's own database, opened READ-ONLY (never auth.json): tool calls so far, the last one
    (name + short argument), and the todo list. Chosen over `--format json` events: the default output the permission-rejection
    detector reads stays untouched, and only the database has the todo list. {} when the database or session is not readable yet."""
    import sqlite3
    db = Path(data_home_dir).expanduser() / "opencode" / "opencode.db"
    if not session or not db.is_file():
        return {}
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2)
        try:
            tools = c.execute("select count(*) from part where session_id=? and json_extract(data,'$.type')='tool'", (session,)).fetchone()[0]
            last = c.execute("select data from part where session_id=? and json_extract(data,'$.type')='tool' "
                             "order by time_created desc, rowid desc limit 1", (session,)).fetchone()
            todos = c.execute("select content, status from todo where session_id=? order by position", (session,)).fetchall()
        finally:
            c.close()
    except sqlite3.Error:
        return {}
    snap = {"tools": tools, "todo_total": len(todos), "todo_done": sum(1 for _, s in todos if s == "completed")}
    now = next((t for t, s in todos if s == "in_progress"), None) or next((t for t, s in todos if s == "pending"), None)
    if now:
        snap["todo_now"] = now[:80]
    if last:
        try:
            d = json.loads(last[0])
            inp = (d.get("state") or {}).get("input") or {}
            arg = next((str(inp[k]) for k in ("filePath", "path", "pattern", "command", "url", "query") if inp.get(k)), "")
            if worktree:
                arg = arg.replace(str(worktree) + "/", "").replace(str(worktree), ".")
            snap["last_tool"] = (d.get("tool", "?") + (" " + arg.replace("\n", " ")[:60] if arg else "")).strip()
        except Exception:                                 # progress is best-effort: an odd row never stops the watcher
            pass
    return snap


def human(sec):
    sec = int(sec)
    return f"{sec}s" if sec < 60 else f"{sec // 60}m" if sec < 3600 else f"{sec // 3600}h{sec % 3600 // 60:02d}m"


def pid_alive(pid):
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (TypeError, ValueError):
        return False
    return True


def model_short(model):
    return split_model(model)[0].split("/")[-1]


def describe(run_dir, now=None):
    """One plain-words line for a run dir (state.json, progress.jsonl, result.json), or None when it is not a run dir. Used for
    status.txt and by scripts/opencode_status.py."""
    run_dir = Path(run_dir)
    st = read_json(run_dir / "state.json")
    if not st:
        return None
    now = now or time.time()
    live = st.get("status") in ("starting", "running", "resuming")
    res = None if live else read_json(run_dir / "result.json")
    prog = None
    try:
        lines = (run_dir / "progress.jsonl").read_text().strip().splitlines()
        prog = json.loads(lines[-1]) if lines else None
    except (OSError, ValueError):
        pass
    n = st.get("number")
    label = (f"PR {n} review" if st.get("kind") == "pr" else f"issue {n} release review" if st.get("kind") == "release"
             else st.get("label") or run_dir.name)
    head = f"{label} · {model_short(st.get('model', '?'))}"
    sid = st.get("session") or "none"
    resume = (f" · resume: python3 scripts/external_review.py --resume {run_dir}"
              if st.get("kind") in ("pr", "release") and st.get("session") else "")
    if live:
        if not pid_alive(st.get("pid")):
            return f"{head} · DIED (the watcher is gone; last status {st['status']}) · session {sid}{resume}"
        parts = [f"running {human(now - st.get('started', now))}"]
        if st.get("attempt", 1) > 1:
            parts.append(f"attempt {st['attempt']}")
        if prog:
            parts.append(f"{prog.get('tools', 0)} steps")
            if prog.get("last_tool"):
                parts.append(f"now: {prog['last_tool']}")
            if prog.get("todo_total"):
                parts.append(f"todo {prog.get('todo_done', 0)}/{prog['todo_total']}" + (f" ({prog['todo_now']})" if prog.get("todo_now") else ""))
        else:
            parts.append("starting" if not st.get("session") else "no progress data yet")
        return " · ".join([head] + parts)
    res = res or {}
    if res.get("class") == "ok":
        return f"{head} · DONE (ok) · {human(st.get('updated', now) - st.get('started', now))} · session {sid}"
    return (f"{head} · STOPPED ({res.get('kind') or '?'}: {res.get('class') or st.get('status')}) · "
            f"{res.get('cause') or 'no cause recorded'} · session {sid}{resume}")


def run(brief, worktree, model, run_dir, agent="external-reviewer", message=None, startup=180,
        idle=600, total=3600, data_dir=None, log=print, meta=None, resume_session=None, resumes=RESUMES, force_resume=False):
    """One watched `opencode run`. result.json has `class` and `kind` (None when ok, else api or process, see above). With
    resume_session the run continues THAT session (opencode run --session) instead of starting one; after an idle-timeout,
    total-timeout or nonzero exit with a known session it continues the same session by itself, up to `resumes` times, each
    attempt with its own idle and total timeout (not after an api failure: the provider is down, the next model takes over). The
    resumes used (automatic and manual) are kept in state.json["resumes_used"], so the limit holds across invocations: a resume
    past it is refused (class resume-limit, nothing written) unless force_resume, which is logged in state.json["forced_resumes"]
    and starts a fresh count.
    state.json, progress.jsonl and status.txt in run_dir say what it is doing."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    if resume_session and not force_resume and resume_refusal(run_dir, resumes):     # refused: nothing is touched
        return {"class": "resume-limit", "kind": "process", "cause": resume_refusal(run_dir, resumes), "session": resume_session,
                "stdout": str(run_dir / "stdout.log"), "stderr": str(run_dir / "stderr.log"), "text": ""}
    keep_prev(run_dir / "result.json")
    res = {"class": None, "kind": None, "model": model, "agent": agent, "session": resume_session, "text": "",
           "stdout": str(run_dir / "stdout.log"), "stderr": str(run_dir / "stderr.log"), "cause": None}
    model = effort(model)
    state = read_json(run_dir / "state.json")
    state = state if isinstance(state, dict) else {}
    state.update(meta or {})
    state.update(model=model, agent=agent, brief=str(brief), worktree=str(worktree), session=resume_session, status="starting",
                 pid=os.getpid(), started=time.time(), attempt=state.get("attempt", 0) + 1, run_dir=str(run_dir),
                 data_dir=str(data_dir or WORK_DEFAULT / "opencode-data"), startup=startup, idle=idle, total=total)

    def save(**kw):
        state.update(kw, updated=time.time())
        write_json(run_dir / "state.json", state)
        line = describe(run_dir)
        if line:
            (run_dir / "status.txt").write_text(line + "\n")

    offs = [0, 0]                                             # byte offsets of this attempt in stderr.log, stdout.log

    ctx = {"read": {}}                                        # exe and env once known (read_last needs them); the reads made per attempt

    def export_name(purpose):
        """A name no earlier export has: export-attemptN-<purpose>[-k].json."""
        base = f"export-attempt{state['attempt']}-{purpose}"
        name, k = f"{base}.json", 2
        while (run_dir / name).exists():
            name, k = f"{base}-{k}.json", k + 1
        return name

    def read_last():
        """CLAUDE.md rule 7, read before you retry, resume or re-route: the session's last assistant message of THIS attempt (export to
        export-attemptN.json, once per attempt), kept in state.json and logged. The one helper every failure decision goes through
        (done() calls it for every failed run with a session). {tag, finish, text}; {tag, error} when the export cannot be read;
        None when there is no session."""
        if not (res["session"] and "exe" in ctx):
            return None
        tag = f"attempt{state['attempt']}"
        if tag in ctx["read"]:
            return ctx["read"][tag]
        try:
            text, finish, _ = final_text(ctx["exe"], ctx["env"], worktree, res["session"], run_dir, export_name("read"))
            lm = {"tag": tag, "finish": finish, "text": text[:4000]}
            log(f"opencode session {res['session']}: last message ({tag}) finish={finish!r}: {text[:300]!r}")
        except Exception as e:                            # a malformed or missing export is "unreadable", never a crash
            lm = {"tag": tag, "error": f"{type(e).__name__}: {e}"[:200]}
            log(f"opencode session {res['session']}: last message UNREADABLE ({tag}): {lm['error']}")
        ctx["read"][tag] = state["last_message"] = lm
        return lm

    def done(cls, cause=None, evidence=None):
        res["class"], res["cause"] = cls, cause
        if cls != "ok":
            ev = evidence or (None if cls in ALWAYS_PROCESS else api_evidence(res, offs))
            res["kind"] = "api" if (cls in ALWAYS_API or ev) else "process"
            if ev:
                res["cause"] = f"{cause}; {ev}" if cause else ev
            lm = read_last()                                  # every failure with a session is read before anything is decided
            res["last_message"] = lm
            if lm and lm.get("error"):                        # unread: never resumed, never handed to another model
                res["kind"] = "process"
                res["cause"] = f"{res['cause'] or cls}; session export unreadable: {lm['error']}"
        write_json(run_dir / "result.json", res)
        save(status=cls, session=res["session"])
        log(f"opencode run: {cls}" + (f" [{res['kind']}]" if res["kind"] else "") + (f" ({res['cause']})" if res["cause"] else "")
            + f"; stdout {res['stdout']}; stderr {res['stderr']}")
        return res

    save()
    exe = find_exe()
    if not exe:
        return done("no-executable", "no native opencode: set OPENCODE_EXE or install ~/.opencode/bin/opencode")
    env = dict(os.environ)
    env.update(data_home(state["data_dir"]))
    ctx["exe"] = exe
    # The reviewer's agent (its permissions) comes from the trusted main checkout, never from the
    # worktree under review: a PR must not be able to change what its own reviewer may do.
    cfg = Path(__file__).resolve().parent.parent / ".opencode"
    if cfg.is_dir():
        env["OPENCODE_CONFIG_DIR"] = str(cfg)
        # OpenCode MERGES the project's own .opencode/ (here: the PR's, in the worktree) with this one, and a
        # PR could add an allow rule to its own reviewer ("python3 *": allow). Ignore the project config.
        env["OPENCODE_DISABLE_PROJECT_CONFIG"] = "1"
    ctx["env"] = env
    mid, variant = split_model(model)
    # Fail fast, before anything is billed.
    def listed(*args, timeout=60):
        """`opencode models ...` -> (names, None) or (None, failed result). A provider/network error shape on stderr (429, 5xx,
        ETIMEDOUT, ...) means the provider did not answer: api, not our process."""
        r = oc(exe, env, worktree, "models", *args, timeout=timeout)
        if r.returncode == 0:
            return r.stdout.split(), None
        ev = next((ln.strip()[:200] for ln in ANSI.sub("", r.stderr).splitlines() if API_RE.search(ln)), None)
        return None, done("nonzero-exit", f"`opencode models {' '.join(args)}` failed ({r.returncode}): {r.stderr.strip()[:120]}".replace("  ", " "),
                          evidence=ev)

    models, failed = listed()
    if failed:
        return failed
    if mid not in models and mid.startswith("opencode-go/"):
        _, failed = listed("--refresh", timeout=120)                   # the catalog may be stale
        if failed:
            return failed
        models, failed = listed()
        if failed:
            return failed
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
    except (ValueError, AttributeError):
        return done("unknown-agent", "unreadable `opencode debug agent` output")

    title = f"review-{uuid.uuid4().hex[:10]}"
    tail = ["--agent", agent, "--model", mid, "--dir", str(worktree)] + (["--variant", variant] if variant else [])

    def resume_cmd():
        return [exe, "run", RESUME_MSG, "--session", res["session"], *tail, "-f", str(brief)]

    cmd = resume_cmd() if resume_session else [exe, "run", message or "Follow the attached brief exactly.", *tail,
                                                "--title", title, "-f", str(brief)]
    if resume_session:
        # Rule 7 for a manual resume too (a DIED run has no result.json): read the session first. A model that stopped with a report
        # is answered, not resumed over, unless a human says --force-resume after reading it.
        lm = read_last()
        save()
        if lm and lm.get("error"):
            return done("session-unreadable", f"the session could not be read before resuming: {lm['error']}")
        if lm and lm.get("finish") == "stop" and lm.get("text", "").strip():
            if not force_resume:
                res["text"] = lm["text"]
                return done("stopped-with-report", "the model had ended its turn with a final message (read result.json text, answer it); "
                            "resume anyway only with --force-resume")
            log("opencode run: --force-resume over a final message of the model (human decision)")
            state.setdefault("forced_resumes", []).append({"t": round(time.time()), "over": "stopped-with-report"})
        # a manual resume is itself one resume of the budget
        if force_resume and resume_refusal(run_dir, resumes):
            state.setdefault("forced_resumes", []).append({"t": round(time.time()), "resumes_used": state.get("resumes_used", 0)})
            state["resumes_used"] = 0
            log("opencode run: --force-resume: the resume limit was lifted by a human decision (logged in state.json)")
        state["resumes_used"] = state.get("resumes_used", 0) + 1
        save()
    session, t_prog, first = resume_session, 0.0, not resume_session
    while True:
        if first:                                                 # never truncate a log that is already there
            keep_prev(res["stdout"])
            keep_prev(res["stderr"])
        # AFTER the archiving: this attempt's output starts where the current files end (0 for a fresh file), so a reused run dir
        # never skips new error output
        offs[:] = [Path(res["stderr"]).stat().st_size if Path(res["stderr"]).exists() else 0,
                   Path(res["stdout"]).stat().st_size if Path(res["stdout"]).exists() else 0]
        out, err = open(res["stdout"], "w" if first else "a"), open(res["stderr"], "w" if first else "a")
        first = False
        proc = subprocess.Popen(cmd, cwd=worktree, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
        save(status="running" if session else "starting")
        t0 = last_move = time.time()
        seen_updated, cls, cause = None, None, None
        try:
            while True:
                time.sleep(TICK)
                now = time.time()
                # a permission auto-rejection: a line that STARTS with "!" (only this attempt's output)
                for f, off in ((res["stdout"], offs[1]), (res["stderr"], offs[0])):
                    data = Path(f).read_bytes()[off:].decode(errors="replace")
                    for ln in ANSI.sub("", data).splitlines():
                        m = PERM.match(ln)
                        if m:
                            kill_tree(proc)
                            if session is None:               # the session may exist already: look once, so it can be read
                                session = res["session"] = next((x["id"] for x in session_list(exe, env, worktree)
                                                                 if x.get("title") == title), None)
                            return done("permission-rejected", m.group(1))
                if session is None:
                    for s in session_list(exe, env, worktree):
                        if s.get("title") == title:
                            session = res["session"] = s["id"]
                            last_move = now
                            log(f"opencode session started: {session} (model {model})")
                            save(session=session, status="running")
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
                        cls, cause = "idle-timeout", f"no progress for {idle}s"
                if cls is None and now - t_prog >= PROGRESS_EVERY:
                    t_prog = now
                    try:                                          # best-effort: progress never stops the watcher
                        snap = snapshot(state["data_dir"], session, worktree)
                        with open(run_dir / "progress.jsonl", "a") as pf:
                            pf.write(json.dumps({"t": round(now), "elapsed": round(now - state["started"]), "session": session,
                                                 "attempt": state["attempt"], **snap}) + "\n")
                        save()
                    except Exception:
                        pass
                if cls is None and proc.poll() is None and now - t0 > total:
                    kill_tree(proc)
                    cls, cause = "total-timeout", f"over {total}s"
                if cls or proc.poll() is not None:
                    break
        finally:
            out.close()
            err.close()
            if proc.poll() is None:
                kill_tree(proc)
        if cls is None and proc.returncode != 0:
            cls, cause = "nonzero-exit", f"exit {proc.returncode}"
        if cls is None:
            break
        if cls in RESUMABLE and session and state.get("resumes_used", 0) < resumes and not api_evidence(res, offs):
            # Rule 7: read the session first. A model that ended its turn with text (finish stop) STOPPED AND REPORTED: that report is
            # answered by the caller, not resumed over. Only a run that died mid-work (no final stop message) is continued.
            lm = read_last()
            save()
            if lm and lm.get("error"):
                return done("session-unreadable", f"the run ended ({cls}: {cause}) and its session could not be read, so it is not resumed")
            if lm and lm["finish"] == "stop" and lm["text"].strip():
                res["text"] = lm["text"]
                return done("stopped-with-report", f"the model ended its turn with a final message and then the run ended ({cls}: {cause}); "
                            "read result.json text and answer it")
            cmd = resume_cmd()
            save(attempt=state["attempt"] + 1, status="resuming", resumes_used=state.get("resumes_used", 0) + 1)
            log(f"opencode run: {cls} ({cause}); resuming session {session} ({state['resumes_used']}/{resumes})")
            continue
        return done(cls, cause)
    try:
        text, finish, seen = final_text(exe, env, worktree, session, run_dir, export_name("final"))
    except Exception as e:
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
