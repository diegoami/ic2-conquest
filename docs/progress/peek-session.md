# Running notes: session ids and peek.sh in every update (2026-10-11)

Implementer: the main session, own worktree (the owner's choice; suggestion shown: light tier pick minimax/MiniMax-M2.7, rank 1, spare, 0.99).
Source: isles-pro (isle-wars-archaeology) CLAUDE.md rule 6.7 and its tools/harness/peek.sh, adapted.

## Plan
1. scripts/peek.sh: the isles-pro script, defaults changed to this repo's OpenCode data dir ($IC2_WORK/opencode-data) and to our run log line ("opencode session started: ses_...").
2. CLAUDE.md monitoring rules: give the session id with a peek line; repeat id and step in every update; agent id + transcript path for Claude subagents.

## Progress
