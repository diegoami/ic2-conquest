# External PR reviewer (OpenCode)

A second, independent reviewer that is not Claude: an OpenCode model reviews a PR in its own git worktree
and `scripts/external_review.py` posts the result. The model never writes to GitHub.

```bash
python3 scripts/external_review.py --pr 7                        # default model chain, posts one comment
python3 scripts/external_review.py --pr 7 --model opencode/big-pickle#high,opencode/mimo-v2.6-flash-free
python3 scripts/external_review.py --pr 7 --apply-label          # also sets status:approved|rework|decision
python3 scripts/external_review.py --issue 9 --kind release      # a gate issue; reviews origin/main
python3 scripts/external_review.py --pr 7 --dry-run              # prints the arguments, starts no model
```

Exit codes: 0 posted · 3 `OpenCode unavailable: <cause>` (nothing posted; record the cause in one PR comment
and fall back to `/review-pr`) · 5 the PR head moved during the review (nothing posted).

## Parts

- `.opencode/agents/external-reviewer.md`: the agent. OpenCode 1.x uses a `permission:` **map** (last match wins);
  the V2 list form (`permissions:` with action/resource/effect) is silently ignored. After any edit, check that
  every deny shows up in `~/.opencode/bin/opencode debug agent external-reviewer`. It denies edit, task, git
  push/commit/stash/worktree, every `gh` write, the game tests, Wine/Xvfb/xdotool, kill and rm; a read outside
  the worktree is auto-rejected.
- `scripts/opencode_watched.py`: runs `opencode run` and classifies the end: ok, no-session, idle-timeout,
  total-timeout, exited-without-session, nonzero-exit, permission-rejected (with the path), default-agent,
  cut-off, unknown-model, unknown-agent, no-executable. `result.json` and the stdout/stderr logs are kept.
- `scripts/external_review.py`: unique detached worktree under `$IC2_REVIEW_ROOT` (default `$IC2_WORK/review`,
  outside the repo) removed in `finally`; the brief with the PR body pasted in; validation of the review's shape
  (header line, verdict, verdict repeated last); the head-SHA re-check; one comment; optional label.
  Logs go to the main checkout's git-ignored `rendered/`.

## WSL notes (this repo's reviewer runs on WSL2, not Windows)

- Use the **native Linux binary** `~/.opencode/bin/opencode` (or `$OPENCODE_EXE`). The `opencode` on PATH here
  is the Windows npm shim under `/mnt/c`; the watcher refuses anything under `/mnt/`.
- Own data dir (`XDG_DATA_HOME=$IC2_WORK/opencode-data`). `auth.json` is **copied** from
  `~/.local/share/opencode/auth.json` if it exists (set `OPENCODE_AUTH` to point elsewhere); it is never read
  or printed. With no auth only the free `opencode/*` models work.
- **OpenCode Go models** (`opencode-go/*`) come from a console (organisation) login, not from `auth login`:
  run `opencode console login` once per data dir (the device flow; it showed the account at once here), with
  `XDG_DATA_HOME=$IC2_WORK/opencode-data` set for the reviewer's own dir. The account lives in that dir's
  database, so the default dir's login does not carry over. Needs OpenCode >= 1.18.34 only if the catalog lacks
  the provider (`opencode models --refresh`); `opencode upgrade` may use the Windows npm, so the WSL binary was
  installed from the GitHub release tarball (`opencode-linux-x64.tar.gz`).
- Process control is a process group (`start_new_session`, `killpg`), not `taskkill`; stdin is `/dev/null`.
- The attached brief goes with `-f`, and the one-line message must come **before** the flags: `-f` is an array
  option and swallows the next argument as a file.
- `opencode export` is written to a file, not read from a pipe: a large export arrives truncated through a pipe.
- The agent file is read from the main checkout (`OPENCODE_CONFIG_DIR`), never from the worktree under review,
  so a PR cannot change what its own reviewer may do.

## Chain and trust

The next model is tried only after an infrastructure failure, never after a real verdict; the chain stops after
two consecutive failures of one class; `permission-rejected`, `unknown-agent` and `no-executable` stop it at
once. The posted header names the failures: `PR review (big-pickle; mimo-v2.6-flash-free failed: no-session)`.
Models named in `Co-Authored-By` trailers and `model:<name>` labels are excluded. Verdicts differ between
free models and between runs of one model (the same PR got `rework` and then `approve`): treat a verdict as one
opinion, and read the findings.
