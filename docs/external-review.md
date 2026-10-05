# External PR reviewer (OpenCode)

## Roles and models (player decisions, 2026-10-01; revised 2026-10-02, twice)

**Sonnet is the only implementer.** The reviewer is not a Claude model: a chain of two, then the caller decides.

| Role | First | Then |
|---|---|---|
| Implementer | Claude Sonnet (no OpenCode implementer) | – |
| Reviewer | DeepSeek V4.1 Flash (`opencode-go/deepseek-v4.1-flash#high`) | OpenAI GPT-5.6 Luna (`openai/gpt-5.6-luna#high`, the OpenAI OAuth credential, on its own weekly pool; not the Go copy, and not GPT-6 Luna, which draws on the main pool with Sol: harness_imperial L51, 2026-10-05) |

**Before choosing a reviewer, check the quota (harness_imperial L50, `CLAUDE.md` Code map, `docs/environment.md`):** skip a model whose provider is `exhausted`, pass the next one with quota explicitly with `--model`, and say so in the PR comment or body. The default chain below is what runs when no `--model` is given.

- The chain moves to the next model only after an infrastructure failure (including "no review at all"), never
  after a real or flagged review. When both fail, `scripts/external_review.py` exits **3** and the caller decides
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
  when the PR needs it, never `#high`** (the player, 2026-10-05).

A second, independent reviewer that is not Claude: an OpenCode model reviews a PR in its own git worktree
and `scripts/external_review.py` posts the result. The model never writes to GitHub.

```bash
python3 scripts/external_review.py --pr 7                        # the default chain, posts one comment
python3 scripts/external_review.py --pr 7 --model opencode-go/kimi-k3#high
python3 scripts/external_review.py --pr 7 --apply-label          # also sets status:approved|rework|decision
python3 scripts/external_review.py --issue 9 --kind release      # a gate issue; reviews origin/main
python3 scripts/external_review.py --pr 7 --dry-run              # prints the arguments, starts no model
python3 scripts/external_review.py --pr 7 --review-file R.md     # offline: what would be posted, its note, the exit code
python3 scripts/external_review.py --self-test                   # the review parser over 15 sample outputs
```

Exit codes: **0** posted · **2** usage · **3** `OpenCode unavailable: <cause>` (nothing posted; record the cause in
one PR comment and run the fallback you choose, e.g. Claude Opus) · **4** posted **flagged** (the verdict could not be read or the
review looks cut off: a note line on top, no label; read it and decide; no fallback to another paid review) · **5**
the PR head moved during the review (nothing posted).

**A review is never thrown away; only acting on what cannot be read is refused.** The parser
(`parse_review`) finds the header case-insensitively, also wrapped in Markdown (`**…**`, a leading `#`,
backticks) and after a preamble; skips blank lines before the verdict; reads the verdict with decoration, a
`Verdict:` prefix or trailing punctuation; looks for the closing verdict among the last three non-empty lines;
and accepts a review flattened onto one line. Then:

| What the model returned | Result |
|---|---|
| no header line anywhere (tool chatter, nothing: the early-stop case) | the **only** failure: next model, or exit 3 |
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
  cut-off, unknown-model, unknown-agent, no-executable. `result.json` and the stdout/stderr logs are kept.
- `scripts/external_review.py`: unique detached worktree under `$IC2_REVIEW_ROOT` (default `$IC2_WORK/review`,
  outside the repo) removed in `finally`; the brief with the PR body pasted in; the tolerant parser above; the
  head-SHA re-check; one comment; optional label. `--self-test` runs 15 sample outputs through the parser.
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
grep, ls, cat, head, tail, find and `python3 -m py_compile`. Denies placed last win: redirections, `tee`, `;`,
`&&`, `$(...)`, backticks, `| sh|bash|python`, `xargs`, `--output`, `--pre`, `sort -o`, `find -exec|-delete`,
curl/wget, and any path containing `auth.json`, `opencode-data`, `.config`, `.ssh`, `.env`. The agent writes
no files; its findings are its final message. Tested on a throwaway worktree with a dummy `auth.json` and 18
commands: every write, redirect, push, `gh pr comment`, `python3 -c`, curl and `env` was refused, `ls`,
`git log` and `py_compile` ran, no file appeared, and a read of `/etc/hostname` was auto-rejected as
permission-rejected. Re-run that kind of battery after any change to the allowlist.

## Failures and trust

The classes written to `result.json`: ok, no-session, idle-timeout, total-timeout, exited-without-session,
nonzero-exit, permission-rejected, default-agent, cut-off, unknown-model, unknown-agent, no-executable. With an
explicit `--model a,b` list the next model is tried only after an infrastructure failure (including "no review
at all"), never after a real or flagged review; the list stops after two consecutive failures of one class, and
`permission-rejected`, `unknown-agent` and `no-executable` stop it at once. The posted header names the failures:
`PR review (gpt-5.6-luna; deepseek-v4.1-flash failed: no-session)`. Verdicts differ between models and between runs of one
model (the same PR got `rework` and then `approve`): treat a verdict as one opinion, and read the findings.

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
- **The tree proof (first two tool calls, separate because `;` and `&&` are denied):** `git rev-parse --show-toplevel HEAD` (the first line must
  be the worktree path the brief names, the second the head SHA it names) and `git diff --name-only <base>...HEAD` (must not be empty for a PR;
  a release review has no diff by design). If anything is wrong the reviewer says it is in the wrong tree (verdict `decision`) and stops.
- **Guard:** `tests/test_reviewer_prompt.py` fails if the agent's body, its permission rules, the brief template, or what the watcher hands to
  opencode (checked with a fake opencode: the brief file it receives, and the fixed message and arguments of its command line, which
  fails if someone edits that message to ask for it) ask for `git -C`. It was broken by hand in each of those four places
  and failed each time. Not changed: the Claude-side `/review-pr` skill also uses `git -C "$WT"`, but there it is a shell variable in Claude's
  own session (whose working directory is the main checkout), not text a model retypes.
