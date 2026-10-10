# OpenCode resilience (branch `tooling/opencode-resilience`)

Owner's brief 2026-10-10: an OpenCode failure caused by our own process is diagnosed, never passed to another model; only an
API failure falls through; a dying run is resumable; running jobs are visible. A successor continues from this file and the branch.

## Checklist
- [x] A. failure `kind` (api|process) in result.json; chain falls through on api only; process failure -> exit 6
- [x] B. state.json per run dir, auto-resume (2x, same session), `external_review.py --resume <run dir>`
- [x] C. progress.jsonl + status.txt every ~30 s, `scripts/opencode_status.py`
- [x] D. DEFAULT_MODELS = luna#high, MiniMax-M2.7; self-test/docs updated
- [x] E. tests (fake opencode scenarios) in tests/test_reviewer_prompt.py
- [x] F. docs/external-review.md (exit codes, kinds, resume, status, chain, `&&` correction)
- [ ] PR opened (next: gh pr create; the owner runs one live check)

## Decisions
- Progress source: the session DB opened read-only (`part`, `todo` tables), not `--format json`: the default formatted output
  stays as it is (the permission-rejection detector reads it), and the DB gives todo state, which JSON events do not.
- An api-kind failure is not resumed (the provider is down; the next model takes over); process-kind ones are resumed 2x.
- Each attempt (first run and each resume) gets its own idle and total timeout.

## Review round 1 (PR #67, luna: rework), all fixed
- [x] R1 bad-format keeps the ok result as result.prev-N.json (ow.keep_prev)
- [x] R2 API evidence from stderr only (OpenCode prints errors as `Error: {json}` on stderr, stdout empty; forced with an unknown provider in a throwaway data dir); tests for stdout text vs stderr error
- [x] R3 resumes_used in state.json, limit across --resume, --force-resume logged in forced_resumes; tests
- [x] tests write to a tempfile dir only
