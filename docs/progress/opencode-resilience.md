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

## Review round 2 (PR #67), all fixed
- [x] R1 `opencode models` stderr with a provider/network shape -> kind api
- [x] R2 read the session before any automatic resume (state.json last_message, log, export-attemptN.json); finish=stop with text -> stopped-with-report (process, text in result.json), else resume
- [x] R3 api failure with a session: last message read into result.json, state.json and the log before the chain moves on

## Review round 3 (PR #67), all fixed
- [x] R1 unreadable session export -> process failure (`session-unreadable` before a resume; error in cause otherwise), no resume/fallback
- [x] R2 one helper `read_last` called by done() for every failure with a session (permission-rejected looks the session up first)
- [x] R3 per-attempt export-attemptN.json everywhere, final_text takes the name
- [x] R4 tests run er.main() against the fake with git/gh stubbed: exit 6 (no post, one model), exit 3 (no post), fallback posts

## Review round 4 (PR #67), all fixed (main merged in, no conflict)
- [x] R1 every export has its own name (export-attemptN-<purpose>[-k].json), opened with "x"
- [x] R2 export shape validated -> ValueError -> session-unreadable; 10 malformed shapes tested
- [x] R3 manual resume reads the session first (DIED runs too); report -> stopped-with-report unless --force-resume
- [x] R4 `models --refresh` and the listing after it: provider errors are api
- [x] Adversarial pass, found and fixed: session_list / debug-agent output of a wrong shape crashed the watcher; progress and snapshot errors could stop it (now best-effort);
  first-run stdout/stderr logs were truncated if present (keep_prev); comment.md was overwritten on a second post (keep_prev); bad-format did not record the session's last message;
  a watcher exception was a bare traceback (now `watcher-crash`, process, exit 6 path); resume_run did not check all state keys; opencode_status died on one bad run dir;
  the exit-6 line now shows what a stopped-with-report model said.
- Known limit: a watcher-crash record cannot read the session (the watcher is what died); the run dir and session id are still printed.

## Review round 5 (PR #67), all fixed
- [x] R1 every 5xx is api evidence as a status (status/status code/HTTP/Error before 5NN, 5NN before an error word, 5xx); a bare number such as "line 503" is not
- [x] R2 evidence offsets computed after the logs are archived; test with a reused run dir
- [x] R3 vacuous asserts replaced by real ones (export names, no run started on a listing failure); grep found no others

## Review round 6 (PR #67), all fixed
- [x] R1 structured OpenCode errors are the primary evidence (api_text / classify_error_obj; shapes read from the 1.18.34 binary); text regex only for unstructured lines, with `returned 5NN`, `responded with NNN`
- [x] R2 the models-listing classification uses only that call's own stderr (done(scan_logs=False)); test with a reused run dir holding an old 429
- [x] R3 docs/proposals/fleet-battles-and-storms.md:273 is the bot's own text (section 13, 'Author: Claude Sonnet 5.5'): updated with the date of the change
