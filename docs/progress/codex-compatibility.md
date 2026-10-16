# Codex compatibility — 2026-10-16

## Plan

- Inspect shared policy, startup prompts, Claude skills, handoffs and reviewer.
- Add Codex instruction discovery and map backend-specific capabilities.
- Preserve Claude policy, skill behavior and reviewer permissions.
- Validate offline, push the isolated branch and open a draft PR.

## Progress

- Implementer: current Codex session, authorized by the user's request to
  analyze the project and make it Codex compatible while retaining Claude.
  No delegate or reviewer selected; quota recommendations did not select one.
- Branch: `chore/codex-compatibility`, based on `6af3f69`, implementation
  worktree `/tmp/ic2-conquest-codex-compatibility`.
- Added `AGENTS.md` directing Codex to the complete existing policy; added
  `docs/agent-workflow.md` with backend mappings and the compatibility assessment.
- Added cross-links and historical-prompt notices. Shared hard rules, Claude
  skills, OpenCode agent configuration and executable code are unchanged.
- Validation: reviewer self-test 83/83; full `tests.test_reviewer_prompt` suite
  passed; `tests.test_environment` 16 passed; `tests.test_archive_pycache`
  passed; workflow file references and `git diff --check` passed.
- GitHub authentication works outside the network sandbox. No game, external
  reviewer, research relay, system setup or measurement batch was started.

## END

Implementation and offline validation complete; ready for independent review.
The PR records the final commit and publication state. The owner still chooses
the reviewer model, from a different family than the OpenAI implementer; no
automatic reviewer or model fallback. Fresh-client instruction discovery and
real Wine integration were not exercised. No findings changed, and this task
does not establish a new findings-reporting or research-relay baseline.
