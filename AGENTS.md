# ic2-conquest: Codex entry point

Read **all of `CLAUDE.md` before acting**. It is the shared project policy for
Codex, Claude and other backends, despite its historical filename. Keep that
single source of rules; do not copy it here or replace the Claude entry point.
Then read `README.md` and `docs/agent-workflow.md` for backend mappings and checks.

For continuing work, read the task's brief, its worktree's running notes and the
latest relevant dated entry in `HANDOVER.md`. Its opening section and the two
old session prompts describe earlier stages, not a current task queue. Verify
branch, PR and issue state before acting on them. Battles and bots remain paused
until the owner resumes them (`CLAUDE.md`, "Working with the owner").

## Codex mappings

- Use the tools this session actually exposes. Claude's `Agent`, `ListAgents`,
  `SendMessage`, transcript paths and `$ARGUMENTS` are not Codex APIs. Do not
  invent a command or assume a Claude skill is automatically loaded by Codex.
- Preserve the user's implementer and reviewer choices. A request addressed to
  this session to do the work authorizes this session to implement it; do not
  ask again for an already supplied choice. Ask about choices still missing.
  Never silently select a delegate, reviewer or fallback model.
- Work in an isolated git worktree. Use an allowed writable location, such as
  `/tmp`, if the default sibling or home directory is outside the sandbox.
  A linked worktree also needs access to the original repository's git metadata.
- Record plans, progress, commits, validation and an END handoff in the worktree's
  running-notes file. Claude session memory is not a cross-backend handoff.
  Record relay and reported-findings baselines in task-owned tracked notes,
  including the commit SHA. If no trustworthy baseline is available, say so and
  recover it from repository history or the owner; never guess it.
- For an external review, use `scripts/external_review.py` with the ONE model the
  user named and a task-specific brief (`docs/external-review.md`). Record the
  implementer's actual model in PR metadata or pass `--exclude-model <model>`.
  Codex/OpenAI is the OpenAI family; another OpenAI model is not independent.
- `.claude/skills/review-pr/SKILL.md` remains the Claude-only review route when
  the user chooses a Claude reviewer. Do not run its instructions as a Codex
  reviewer or attribute a Codex review to Claude.
- For an authorized research relay, read
  `.claude/skills/relay-to-research/SKILL.md` as a procedure. Use a session bridge
  only if it can reach the intended research session. Codex's local agent list
  does not establish access to independent Claude sessions. If unavailable,
  produce the procedure's paste-ready message and state that delivery is pending.
  Never claim a relay was sent or update its last-delivered SHA until it succeeds.
- Repository instructions and Claude `allowed-tools` metadata do not grant
  sandbox, network or credential access. Request the runtime's permission when
  necessary. Do not read credentials or bypass a release refusal; preserve the
  existing fallback instructions in `CLAUDE.md`.

Do not start a game run, install system packages, launch a reviewer or send a
research message merely to check agent compatibility. Use the offline checks in
`docs/agent-workflow.md`; game validation has separate prerequisites.
