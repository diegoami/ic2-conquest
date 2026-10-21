# Working with Codex and Claude

The project tests strategies and discovers rules in the original Imperial
Conquest 2 under Wine. The process is evidence first: approved run proposals,
save-backed claims and immutable measurements. Sessions choose their workflow,
with optional worktrees and reviews and no model-family gate. The harness,
parsers, archive tools and OpenCode reviewer are Python and shell programs;
they do not require the orchestrator to be Claude.

`CLAUDE.md` remains the shared policy and Claude's existing entry point. Codex
loads the root `AGENTS.md`, which explicitly directs it to read that policy.
This follows [OpenAI's instruction discovery documentation](https://developers.openai.com/codex/guides/agents-md/)
without requiring a personal fallback-filename configuration. Make policy
changes in `CLAUDE.md`; keep backend mappings in `AGENTS.md` and this document.
Existing `.claude/skills/` and `.opencode/` files remain in place.

## Session procedure

1. Read the shared rules, then the task brief, current running notes and latest
   relevant dated handover. Check git status and the current branch; preserve
   other sessions' uncommitted work. The opening and next-session prompts are
   historical bootstrap material, not instructions to repeat setup or old runs.
2. Work in the supplied checkout and preserve other sessions' changes. A branch
   is normal; use a worktree only when useful for isolation.
3. Implement using the session's available tools and models, honoring explicit
   owner choices. Commit and push useful progress and open a PR. Keep measured
   outputs and save hashes tracked; never replace evidence with a rerun.
4. Run checks appropriate to the change. Separate offline checks from Wine
   integration tests; a mock test pass does not prove game behavior.
5. Choose whether additional review helps. The default harness, a separate model
   or no external review are all valid. No model-family restriction applies.
   Read complete reports and resolve material findings. Honor required checks;
   a posted external verdict is not required for merging.
6. Leave an END handoff with branch, commit, tests, pending decisions and next
   steps. For findings, retain the reported and last-delivered baselines in
   tracked notes so another backend can continue without private session memory.

## Backend boundaries

| Process | Claude | Codex |
|---|---|---|
| Project rules | `CLAUDE.md` | `AGENTS.md` directs reading `CLAUDE.md` |
| Named delegate | Available Claude agent tools | Available Codex delegation tools, only if authorized and the named model is available |
| Delegate progress | Agent id and Claude transcript, when exposed | Exposed agent/run id and progress reports; no assumed Claude transcript path |
| External model review | `scripts/external_review.py` | Optional script or available harness |
| User chooses a Claude reviewer | `.claude/skills/review-pr` in a Claude session | Route to a reachable Claude session; report if unavailable |
| Research relay | Existing relay skill and reachable research session | Read the same procedure; use a reachable bridge or provide its paste-ready fallback |
| Durable handoff | Repository notes plus optional session memory | Repository notes; never assume Claude memory exists |

An unavailable tool is a workflow limitation, not permission to substitute a
tool, claim a delivered message or write into the research repo.
Neither backend's instruction files replace runtime permissions.

## Checks without Wine or external models

Run from the working checkout:

```bash
python3 scripts/external_review.py --self-test
python3 -m tests.test_reviewer_prompt
python3 -m tests.test_environment
python3 -m tests.test_archive_pycache
git diff --check
```

The reviewer tests use a fake OpenCode executable and temporary data; they test
review prompts, model selection, failures, progress and resume behavior.
The environment tests mock Wine/display commands, and the archive tests use
temporary measurements. None starts a real game or calls a model provider.

For real driver changes, consult `docs/wsl-setup.md`, `docs/environment.md` and
`tests/results.md`, verify the game fixtures and environment fingerprint, then
run the relevant named driver tests. Do not run `sudo setup/setup.sh` as a
routine session startup step. System setup, Wine prefix writes, `/proc` access,
Xvfb, external work directories, network and git metadata writes must be allowed
by the current environment. Changing `IC2_WORK` also changes the location where
game fixtures and prefixes are expected; an empty temporary directory is not a
replacement for an installed game environment.

## Compatibility assessment

The portability gaps were instruction discovery, backend-specific agent tools,
private memory used as a relay baseline, and stale bootstrap prompts. The entry
point and mappings address those without moving or duplicating shared policy.
Family identification remains informational; it does not restrict reviewer choice.

Remaining prerequisites are environmental: game binaries and pinned inputs,
Wine/display tooling, authenticated GitHub/OpenCode access, and an optional
bridge to the separate research session. Offline checks cannot establish those
or prove a fresh Claude/Codex client's end-to-end behavior.
