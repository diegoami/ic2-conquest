# ic2-conquest: Codex entry point

Read **all of `CLAUDE.md` before acting**. It is the shared project policy for
Codex, Claude and other backends, despite its historical filename. Keep that
single source of rules; do not copy it here or replace the Claude entry point.
Then read `README.md` and `docs/agent-workflow.md` for backend mappings and checks.

For continuing work, read the task's brief, its running notes and the
latest relevant dated entry in `HANDOVER.md`. Its opening section and the two
old session prompts describe earlier stages, not a current task queue. Verify
branch, PR and issue state before acting on them. Battles and bots remain paused
until the owner resumes them (`CLAUDE.md`, "Working with the owner").

For cloud migration or SAV research continuation, read `docs/cloud-continuation.md`.

## Current checkpoint: remaining fleet research #174

Owner requested wind-down on 2026-10-26. Work is paused on
`research/fleet-overflow174`; first read `RUN-NOTES-fleet-overflow174.md`,
its latest END checkpoint, and the latest checkpoint comment on
https://github.com/diegoami/ic2-conquest/issues/174. The packet is unfinished;
do not treat the older handover as its queue or rerun retained measurements.
On startup report state only. Continue #174 on an explicit resume; do not
auto-start #178, another task, or the paused battle/bot queue.

## Codex mappings

- Use the tools this session actually exposes. Claude's `Agent`, `ListAgents`,
  `SendMessage`, transcript paths and `$ARGUMENTS` are not Codex APIs. Do not
  invent a command or assume a Claude skill is automatically loaded by Codex.
- Follow the session-led workflow in `CLAUDE.md`: worktrees and separate reviews
  are optional, with no model-family restriction. Honor explicit owner choices
  and use the available harness/tools. Preserve others' work in the checkout.
- Record plans, progress, commits, validation and an END handoff in the task's
  running-notes file. Claude session memory is not a cross-backend handoff.
  Record relay and reported-findings baselines in task-owned tracked notes,
  including the commit SHA. If no trustworthy baseline is available, say so and
  recover it from repository history or the owner; never guess it.
- `scripts/external_review.py` is an optional external-review route; supply a
  task-specific brief when using it. Describe the actual reviewer accurately;
  a same-model review is not independent evidence.
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
