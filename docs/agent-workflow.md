# Working with Codex and Claude

The project tests strategies and discovers rules in the original Imperial
Conquest 2 under Wine. The process is evidence first: approved run proposals,
save-backed claims, immutable measurements, isolated implementation worktrees,
and a user-selected reviewer from a different model family. The harness,
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
2. Honor the owner's implementation choice. An explicit request for the current
   session to implement supplies that choice. Otherwise ask who implements and
   which model, as the shared rules require; quota-tracker only suggests.
3. Implement in a separate worktree and keep its running notes. Commit and push
   as required by the shared rules, then open a PR with the actual implementer
   model recorded. Keep measured outputs and save hashes under the task's tracked
   path; never replace evidence with a rerun.
4. Run checks appropriate to the change. Separate offline checks from Wine
   integration tests; a mock test pass does not prove game behavior.
5. Ask for the external reviewer model when that choice is missing. Use one
   reviewer at a time, a brief with "Blocking means", and a different model
   family. Read the complete returned report before fixing, resuming or escalating.
   Follow the shared "Merging" rule in `CLAUDE.md` for review and required checks;
   optional CI need not delay an independently approved change.
6. Leave an END handoff with branch, commit, tests, pending decisions and next
   steps. For findings, retain the reported and last-delivered baselines in
   tracked notes so another backend can continue without private session memory.

## Backend boundaries

| Process | Claude | Codex |
|---|---|---|
| Project rules | `CLAUDE.md` | `AGENTS.md` directs reading `CLAUDE.md` |
| Named delegate | Available Claude agent tools | Available Codex delegation tools, only if authorized and the named model is available |
| Delegate progress | Agent id and Claude transcript, when exposed | Exposed agent/run id and progress reports; no assumed Claude transcript path |
| External model review | `scripts/external_review.py` | Same script and restrictions |
| User chooses a Claude reviewer | `.claude/skills/review-pr` in a Claude session | Route to a reachable Claude session; report if unavailable |
| Research relay | Existing relay skill and reachable research session | Read the same procedure; use a reachable bridge or provide its paste-ready fallback |
| Durable handoff | Repository notes plus optional session memory | Repository notes; never assume Claude memory exists |

An unavailable tool is a workflow limitation, not permission to substitute a
model, skip review, claim a delivered message or write into the research repo.
Neither backend's instruction files replace runtime permissions.

## Checks without Wine or external models

Run from the implementation worktree:

```bash
python3 scripts/external_review.py --self-test
python3 -m tests.test_reviewer_prompt
python3 -m tests.test_environment
python3 -m tests.test_archive_pycache
git diff --check
```

The reviewer tests use a fake OpenCode executable and temporary data; they test
review prompts, family restrictions, failures, progress and resume behavior.
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
The external reviewer's existing family detection already recognizes Codex and
OpenAI, so its implementation and permission allowlist need no change.

Remaining prerequisites are environmental: game binaries and pinned inputs,
Wine/display tooling, authenticated GitHub/OpenCode access, and an optional
bridge to the separate research session. Offline checks cannot establish those
or prove a fresh Claude/Codex client's end-to-end behavior.
