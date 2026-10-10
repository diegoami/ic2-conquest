# External PR reviewer (OpenCode)

## Roles and models (player decisions, 2026-10-01; revised 2026-10-02, twice)

**Sonnet is the only implementer.** The reviewer is not a Claude model: a chain of two, then the caller decides. **Since 2026-10-10 the
chain is `openai/gpt-5.6-luna#high` then `minimax/MiniMax-M2.7`** (the owner; DeepSeek and Alibaba are used only when asked). The table
below is the history of the earlier chain.

| Role | First | Then |
|---|---|---|
| Implementer | Claude Sonnet (no OpenCode implementer) | – |
| Reviewer | DeepSeek V4.1 Flash (`opencode-go/deepseek-v4.1-flash#high`) | OpenAI GPT-5.6 Luna (`openai/gpt-5.6-luna#high`, the OpenAI OAuth credential, on its own weekly pool; not the Go copy, and not GPT-6 Luna, which draws on the main pool with Sol: harness_imperial L51, 2026-10-05) |

**Before choosing a reviewer, check the quota (harness_imperial L50, `CLAUDE.md` Code map, `docs/environment.md`):** skip a model whose provider is `exhausted`, pass the next one with quota explicitly with `--model`, and say so in the PR comment or body. The default chain below is what runs when no `--model` is given. The script also checks itself: before the chain runs it asks quota-tracker (`IC2_QUOTA_URL`, default `http://localhost:8765`) about each model's provider, skips one whose provider is `exhausted` (GPT-5.6 Luna is judged on its own `gpt-5.6-luna:7d` window), names the skip in the posted header (`PR review (gpt-5.6-luna; glm-5.3 failed: quota exhausted (zai, usable in 1h))`) and exits 3 when every model is skipped; when quota-tracker does not answer it goes on unchanged.

- The chain moves to the next model only after an **api** failure (the provider did not answer, see "Failure kinds, resume, status"),
  never after a real or flagged review and never after a **process** failure. When every model's API fails, `scripts/external_review.py` exits **3** and the caller decides
  what runs next. The Claude fallback is the `/review-pr <n>` skill (`.claude/skills/review-pr`, merged in #7), run
  in a session on Opus; nothing starts it automatically.
- **The implementer's model never reviews its own PR** (`Co-Authored-By` trailers and `model:<name>` labels are
  excluded, compared without punctuation; `--exclude-model` adds names). Today the implementer is Sonnet, which is
  not in the chain, so nothing is excluded.
- **History, so the reasons survive:** the earlier plan was DeepSeek then Sonnet as implementer, and GLM-5.3 Flash
  then Opus as reviewer. GLM-5.3 and GLM-5.3-Flash sometimes end their turn early in long implementer runs (a
  whole run of reading, then exit 0 with no commit); Go's `gpt-6-luna` returned "Bad Request" in long agent loops
  (a third-party upstream rejecting assistant messages with empty content), which is why the Luna in the chain is
  the **direct OpenAI** one. Both are untested as long runs here; reviews are short.
- **Effort is `high`, never `max`** (Go lists low/high/max; max is overkill and slower). A model without a
  variant gets `#high`; an explicit `#max` is lowered to `#high` with a log line. That suits the light models in
  the chain. **A heavy model (`openai/gpt-6.1-sol`, `zai-coding-plan/glm-5.3`) is passed with `#low`, or `#medium`
  when the PR needs it, never `#high`** (the player, 2026-10-05). `opencode_watched.effort` enforces it: a heavy model with no variant
  gets `#low`, and `#high` or `#max` on one is lowered to `#medium` with a log line.

A second, independent reviewer that is not Claude: an OpenCode model reviews a PR in its own git worktree
and `scripts/external_review.py` posts the result. The model never writes to GitHub.

```bash
python3 scripts/external_review.py --pr 7                        # the default chain, posts one comment
python3 scripts/external_review.py --pr 7 --model opencode-go/kimi-k3#high
python3 scripts/external_review.py --pr 7 --apply-label          # also sets status:approved|rework|decision
python3 scripts/external_review.py --issue 9 --kind release      # a gate issue; reviews origin/main
python3 scripts/external_review.py --pr 7 --dry-run              # prints the arguments, starts no model
python3 scripts/external_review.py --pr 7 --review-file R.md     # offline: what would be posted, its note, the exit code
python3 scripts/external_review.py --self-test                   # the review parser (15 sample outputs), the quota skip, pricing, effort rule and default chain
python3 scripts/external_review.py --resume rendered/pr7-ab12cd/run-1   # continue a run that stopped, in the same OpenCode session
python3 scripts/opencode_status.py                               # what is running / stopped, in plain words
python3 tests/test_reviewer_prompt.py                            # fake-opencode tests (kinds, resume, progress, status)
```

Exit codes: **0** posted · **2** usage · **3** `OpenCode unavailable: <cause>` (nothing posted; record the cause in
one PR comment and run the fallback you choose, e.g. Claude Opus) · **4** posted **flagged** (the verdict could not be read or the
review looks cut off: a note line on top, no label; read it and decide; no fallback to another paid review) · **5**
the PR head moved during the review (nothing posted) · **6** `OpenCode process failure: <model>: <class>: <cause>; session <id>; run dir <dir>;
resume with --resume <dir>` (our own process failed; nothing posted, **no fallback**: diagnose it, then resume). Exit 3 now means only "every
model's API was unavailable, or skipped for quota".

**A review is never thrown away; only acting on what cannot be read is refused.** The parser
(`parse_review`) finds the header case-insensitively, also wrapped in Markdown (`**…**`, a leading `#`,
backticks) and after a preamble; skips blank lines before the verdict; reads the verdict with decoration, a
`Verdict:` prefix or trailing punctuation; looks for the closing verdict among the last three non-empty lines;
and accepts a review flattened onto one line. Then:

| What the model returned | Result |
|---|---|
| no header line anywhere (tool chatter, nothing: the early-stop case) | `bad-format`, a **process** failure: stop, exit 6 (read the session's final message, then `--resume`) |
| readable | normalised (header, verdict, findings, verdict), posted, label set with `--apply-label`, exit 0 |
| verdict unreadable, or the two verdicts disagree | posted with `> Note from scripts/external_review.py: verdict unreadable`, no label, exit 4 |
| no closing verdict (cut off) | posted with `> Note …: review may be cut off`, no label, exit 4 |
| `fixes #N`, `closes #N`, `resolves #N` in the text | **rewritten** to `fixes N` (GitHub closes issues from PR bodies and commits, not comments), logged |

## Parts

- `.opencode/agents/external-reviewer.md`: the agent. OpenCode 1.x uses a `permission:` **map** (last match wins);
  the V2 list form (`permissions:` with action/resource/effect) is silently ignored. After any edit, check that
  every deny shows up in `~/.opencode/bin/opencode debug agent external-reviewer`. It denies edit, task, the web tools (webfetch, websearch, codesearch: a planted URL in a PR must not be fetched), skill, git
  push/commit/stash/worktree, every `gh` write, the game tests, Wine/Xvfb/xdotool, kill and rm; a read outside
  the worktree is auto-rejected.
- `scripts/opencode_watched.py`: runs `opencode run` and classifies the end: ok, no-session, idle-timeout,
  total-timeout, exited-without-session, nonzero-exit, permission-rejected (with the path), default-agent,
  cut-off, unknown-model, unknown-agent, no-executable, and gives each failure a **kind** (below). `result.json`, `state.json`,
  `progress.jsonl`, `status.txt` and the stdout/stderr logs are kept, never deleted.
- `scripts/opencode_status.py`: one plain line per run (see "Failure kinds, resume, status").
- `scripts/external_review.py`: unique detached worktree under `$IC2_REVIEW_ROOT` (default `$IC2_WORK/review`,
  outside the repo) removed in `finally`; the brief with the PR body pasted in; the tolerant parser above; the
  head-SHA re-check; one comment; optional label. `--self-test` runs the sample outputs through the parser.
  Logs go to the main checkout's git-ignored `rendered/`.

## WSL notes (this repo's reviewer runs on WSL2, not Windows)

- Use the **native Linux binary** `~/.opencode/bin/opencode` (or `$OPENCODE_EXE`). The `opencode` on PATH here
  is the Windows npm shim under `/mnt/c`; the watcher refuses anything under `/mnt/`.
- Own directories, for the child process only (the caller's environment is untouched, so nothing to restore):
  `XDG_DATA_HOME=$IC2_WORK/opencode-data`, `XDG_CACHE_HOME=…/cache`, `XDG_STATE_HOME=…/state`, `TMPDIR=…/tmp`, all absolute. The
  OpenCode desktop app (2.x) shares the default `~/.local/share/opencode/opencode.db` and can migrate it to a
  schema the 1.x CLI cannot read (`no such column: project_id`). `auth.json` is **copied** from
  `~/.local/share/opencode/auth.json` (set `OPENCODE_AUTH` to point elsewhere) when missing or older; it is never
  read or printed. With no auth only the free `opencode/*` models work; the `openai/*` models need the OpenAI OAuth credential in it.
- **OpenCode Go models** (`opencode-go/*`) come from a console (organisation) login, not from `auth login`:
  run `opencode console login` once per data dir (the device flow: a URL and a code you approve in the browser),
  once for the default dir and once for the reviewer's own:

  ```bash
  XDG_DATA_HOME=$IC2_WORK/opencode-data XDG_CACHE_HOME=$IC2_WORK/opencode-data/cache XDG_STATE_HOME=$IC2_WORK/opencode-data/state \
    ~/.opencode/bin/opencode console login
  ```

  Check with `opencode console orgs` and `opencode models opencode-go` (about 29 models; `opencode models
  --refresh` if none; the watcher refreshes once itself and then says which login is missing). The account
  lives in that dir's **database**, not in `auth.json`, so the default dir's login does not carry over. Needs OpenCode >= 1.18.34 only if the catalog lacks
  the provider (`opencode models --refresh`); `opencode upgrade` may use the Windows npm, so the WSL binary was
  installed from the GitHub release tarball (`opencode-linux-x64.tar.gz`).
- **`TMPDIR` is the reviewer's own, and the agent allows reading `…/opencode-data/tmp/opencode/*`.** OpenCode saves a
  long tool result (a denial message that lists all the rules is long) under `<tmp>/opencode` and the model reads it
  back. In the shared `/tmp/opencode` that read was an out-of-tree access, auto-rejected as `permission-rejected`:
  the first real run on PR #9 (2026-10-02) died on it with nothing posted (exit 3). Only that path is allowed.
- Process control is a process group (`start_new_session`, `killpg`), not `taskkill`; stdin is `/dev/null`.
- The attached brief goes with `-f`, and the one-line message must come **before** the flags: `-f` is an array
  option and swallows the next argument as a file.
- `opencode export` is written to a file, not read from a pipe: a large export arrives truncated through a pipe.
- The agent file is read from the main checkout (`OPENCODE_CONFIG_DIR`), **and the worktree's own `.opencode/` is
  ignored** (`OPENCODE_DISABLE_PROJECT_CONFIG=1`), so a PR cannot change what its own reviewer may do. This is not
  automatic: OpenCode *merges* the two, so before the switch a worktree copy of the agent file could add an allow
  rule (`"python3 *": allow`) that the trusted file only blocked through its catch-all deny. Found by a battery run
  on 2026-10-02 (a `git checkout` allowed from an older copy); re-test after any change with
  `OPENCODE_DISABLE_PROJECT_CONFIG=1 OPENCODE_CONFIG_DIR=<main>/.opencode opencode debug agent external-reviewer`
  from inside a worktree whose agent file has an extra allow.

## The reviewer's shell: a read-only allowlist

`bash` is deny-by-default (`"*": deny`), then allows git read commands (run in the worktree as they are, **never with `-C`**), `gh pr view|diff`, `gh issue view`, rg,
grep, ls, cat, head, tail, find and `python3 -m py_compile`. **Chains: OpenCode 1.18.34 checks each command of a chain on its own** (verified live
2026-10-10), so `git diff --stat X && git diff X` runs (both parts are allowed), while `ls && touch f`, a `;` followed by `rm`, `>`, `tee` and
`$(...)` are refused. An earlier version of this page said `&&` is always denied: that was wrong. Denies placed last win: redirections, `tee`,
`;` before a denied command, `$(...)`, backticks, `| sh|bash|python`, `xargs`, `--output`, `--pre`, `sort -o`, `find -exec|-delete`,
curl/wget, and any path containing `auth.json`, `opencode-data`, `.config`, `.ssh`, `.env`. The agent writes
no files; its findings are its final message. Tested on a throwaway worktree with a dummy `auth.json` and 18
commands: every write, redirect, push, `gh pr comment`, `python3 -c`, curl and `env` was refused, `ls`,
`git log` and `py_compile` ran, no file appeared, and a read of `/etc/hostname` was auto-rejected as
permission-rejected. Re-run that kind of battery after any change to the allowlist.

## Failures and trust

The classes written to `result.json`: ok, no-session, idle-timeout, total-timeout, exited-without-session,
nonzero-exit, permission-rejected, default-agent, cut-off, unknown-model, unknown-agent, no-executable, `bad-format` (an ok run
whose final message has no review header) and `stopped-with-report` (the model ended its turn with a final message and then the run ended: a process failure whose text is in `result.json`; answer it, do not resume over it). With an explicit `--model a,b` list the next model is tried only after an **api** failure,
never after a real or flagged review or a process failure. The posted header names the api failures:
`PR review (minimax-m2.7; gpt-5.6-luna failed: exited-without-session)`. Verdicts differ between models and between runs of one
model (the same PR got `rework` and then `approve`): treat a verdict as one opinion, and read the findings.

### Failure kinds, resume, status (the owner's rule, 2026-10-10)

A failure of an OpenCode run is never normal: it is diagnosed and fixed, not silently passed to another model. `result.json` has `kind`:

| kind | what | what happens |
|---|---|---|
| `api` | no session ever started (`no-session`, `exited-without-session`), or stderr that says the provider did not answer. **Structured first**: OpenCode prints its errors as `Error: {"name": ..., "data": {...}}` (read from the 1.18.34 binary: `APIError` {message, statusCode, isRetryable, responseBody}, `ProviderAuthError`, `ContextOverflowError`, `ContentFilterError`, `MessageAbortedError`, `UnknownError` {message, ref}); every JSON object in stderr is classified: status 429, 5xx, 408, 409, 402 or `isRetryable` or a network-looking name = api; `ContextOverflowError`, `ContentFilterError`, `MessageAbortedError`, a 4xx `APIError` = process (words inside a decided object are ignored). Only what is not such an object falls back to text patterns (429, rate limit, 5xx as a status, `returned 503`, overloaded, quota, ECONNRESET ...; a bare number like `line 503` never counts). stdout is never read. The evidence line is stored in `cause` | the next model of the chain is tried; all failing: exit 3 |
| `process` (credentials) | **401/403 or `ProviderAuthError`** (also as `Error: 401 Unauthorized` text), with or without a session, even next to api evidence | an expired or invalid login is a flaw in our setup the owner must fix: exit 6, cause `provider credentials refused (401/403): renew the login for <provider>`, no resume, never a fallback to another model (CLAUDE.md rule 8). 402 (payment/quota) stays api |
| `process` | everything else: idle-timeout, total-timeout, cut-off, nonzero-exit, bad-format, permission-rejected, default-agent, and our own setup (`unknown-model`, `unknown-agent`, `no-executable`) | the chain stops, nothing is posted, exit 6 with the session id, the run dir and the resume command |
| null | ok | |

- **Automatic resume.** After an `idle-timeout`, `total-timeout` or `nonzero-exit` with a known session (and no api evidence in that attempt's
  output), `opencode_watched.run` continues THE SAME session (`opencode run --session <id>`, the brief attached again, the fixed message
  "Continue where you stopped; finish the task in the attached brief and end with the final message it asks for.") up to 2 times, logging
  each. **Every failed run with a session has its last assistant message read first** (one helper, `read_last`; also before any resume), and an unreadable export ends the run as a process failure (`session-unreadable`, or the original class with the read error in `cause`): never resumed, never handed on. Every export has its own file (`export-attemptN-<purpose>[-k].json`, opened exclusively: never overwritten), and an export that is not shaped like an export (no messages list, messages without info or parts, non-string text) is unreadable too. Specifically, before any resume the last assistant message is read (CLAUDE.md rule 7; `export-attemptN.json`, `state.json` `last_message`, the log): a final
  message with finish `stop` means the model reported, so the run ends as `stopped-with-report` instead; the same read is recorded for an api failure with a session before the next
  model runs (`result.json` `last_message`). A failing `opencode models` listing with a network/429/5xx shape on stderr is an api failure too. Every attempt has its own idle and total timeout; the stdout/stderr logs are appended, not replaced.
  **The limit is kept in `state.json` (`resumes_used`)** and holds across invocations: a manual `--resume` counts as one. Past the limit
  `--resume` is refused (exit 2, nothing written) unless `--force-resume` is given, a human decision after a fix: it is logged in
  `state.json` (`forced_resumes`) and the count restarts.
- **state.json** in every run dir, written at the start and updated as the run goes: kind (`pr` or `release`), number, head and base SHA, title,
  header line, model, agent, session id, attempt, brief path, worktree path, data dir, timeouts, status, watcher pid.
- **`external_review.py --resume <run dir>`**: recreates the worktree at the recorded path and head (**exit 5** if the PR head, or origin/main for
  a release review, moved), continues the recorded session, then parses and posts as usual (`--apply-label` as for a normal run). A previous
  `result.json` is kept as `result.prev-N.json`; run dirs are never deleted (they live under the main checkout's git-ignored `rendered/`).
  A manual `--resume` reads the session first too (also for a run that DIED with no `result.json`): if the model had ended its turn with a final message the
  resume is refused as `stopped-with-report` (answer the report) unless `--force-resume`, which is logged. `opencode models` / `--refresh` failures with a
  network or 429 shape are api failures; a crash of the watcher itself is recorded as `watcher-crash` (process, exit 6).
  Answer a process failure the way CLAUDE.md rule 7 says: read the session's final message first, then resume (or fix the cause and re-run).
- **Progress.** While the run goes, about every 30 s the watcher appends a line to `progress.jsonl` (elapsed, tool calls so far, last tool call
  with a short argument, current todo item and done/total) and rewrites `status.txt`. Source: the session database of the run's data dir, opened
  **read-only** (`mode=ro`, tables `part` and `todo`; `auth.json` is never touched). Chosen over `--format json` events because the default output,
  which the permission-rejection detector reads, stays as it is, and only the database has the todo list.
- **`python3 scripts/opencode_status.py [--root rendered] [--hours 24] [--all]`** lists running runs first, then recently ended ones:

  ```
  PR 66 review · gpt-5.6-luna · running 4m · 12 steps · now: read findings/x.md · todo 2/3 (check the diff)
  PR 66 review · gpt-5.6-luna · STOPPED (process: idle-timeout) · no progress for 600s · session ses_… · resume: python3 scripts/external_review.py --resume <dir>
  PR 67 review · MiniMax-M2.7 · DIED (the watcher is gone; last status running) · session ses_… · resume: …
  ```

**Read before you retry (CLAUDE.md rule 7, the owner, 2026-10-05).** Before a run is retried, re-routed to another model or called a
failure, read what it returned. A run that stopped and reported a blocker can end with the same exit as an early end, and the log's
tail shows only the last tool output. The model's final message is in the session record of the run's data dir (default
`$IC2_WORK/opencode-data`), opened read-only; the session id is the `opencode session started: ses_…` line of the run's log:

```
python3 - <<'EOF'
import sqlite3, json, os
db = 'file:' + os.path.expanduser('~/ic2-work/opencode-data/opencode/opencode.db') + '?mode=ro'
c = sqlite3.connect(db, uri=True)
sid = 'ses_...'   # from the run's log
parts = c.execute("select data from part where session_id=? order by time_created", (sid,)).fetchall()
texts = [json.loads(d) for (d,) in parts if json.loads(d).get('type') == 'text']
print(texts[-1]['text'] if texts else 'no text part')
EOF
```

Never read `auth.json` in that directory. A run that reported gets an answer (amend the task, decide, or escalate), and its report is
posted on the task's PR or run issue. An earlier "model X ends runs early" verdict stays unconfirmed until its runs' final messages
have been read.

## Lessons

**2026-10-02: never make the reviewer type its worktree's path (`git -C <worktree>`).**
- **What happened (another project, harness_imperial#15):** its reviewer agent was told to pass `git -C <worktree>` on every git command. In
  the first real review the model retyped a 90-character worktree path and got one character wrong; OpenCode auto-rejected the path as
  `external_directory`, which ends `opencode run`, and the review was lost after 17 seconds. Every retyped path is another chance for it.
- **Did it apply here:** yes, the same instruction was in our agent file and in the brief, with eleven `git -C * ...` allow rules. Our 13
  logged reviews had the model type `git -C <path>` 131 times and never got one wrong, so we had not hit it, but the hazard was identical.
- **Why `-C` buys nothing:** the script already starts OpenCode inside the worktree (`--dir <worktree>` and the process's working directory),
  so plain `git` runs there. The reason for `-C` was to be sure the model looks at the right tree; the **tree proof** covers that.
- **The rule now:** the agent file and the brief say "your working directory is the worktree: run git there as it is, without `-C`, and never
  type the worktree's path". The `git -C * ...` allow rules are gone; `git -C * push|commit|stash|worktree|checkout|reset` stay as deny
  rules (a safeguard if an allow is ever added again).
- **The tree proof (first two tool calls, kept as separate calls so each output is clean; a chain would run too, each part is checked on its own):** `git rev-parse --show-toplevel HEAD` (the first line must
  be the worktree path the brief names, the second the head SHA it names) and `git diff --name-only <base>...HEAD` (must not be empty for a PR;
  a release review has no diff by design). If anything is wrong the reviewer says it is in the wrong tree (verdict `decision`) and stops.
- **Guard:** `tests/test_reviewer_prompt.py` fails if the agent's body, its permission rules, the brief template, or what the watcher hands to
  opencode (checked with a fake opencode: the brief file it receives, and the fixed message and arguments of its command line, which
  fails if someone edits that message to ask for it) ask for `git -C`. It was broken by hand in each of those four places
  and failed each time. Not changed: the Claude-side `/review-pr` skill also uses `git -C "$WT"`, but there it is a shell variable in Claude's
  own session (whose working directory is the main checkout), not text a model retypes.
