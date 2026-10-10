# Reviewer live fixes (branch `tooling/reviewer-live-fixes`)

Live review of PR #69 (rendered/pr69-a6c69b/run-1) failed and fell through to MiniMax (rule 8). Three bugs.

## Checklist
- [x] 1. worktree named by its token alone; brief and agent say file tools take relative paths (read/grep/glob resolve against the directory: verified in the 1.18.34 binary)
- [x] 2. final permission scan after exit; `Error: The user rejected permission ...` recognised; an external_directory rejection is resumed once with a corrective message after reading the session
- [x] 3. with a session the export info.error is the authority; stderr counts only `Error: {json}` lines; ENOTFOUND now whole-word (FileNotFoundError matched it)
- [ ] tests + fixture (tests/fixtures/pr69-run, lines prefixed "> " so a reviewer reading it does not echo a live permission line), PR

- [x] tests (29 pass) + fixture; docs/external-review.md updated; PR opened next

## PR #70 review round 1
- [x] R1 final permission scan after every termination (exit, idle and total kills); tested both
- [x] R2 reclassify picks the newest export numerically (attempt10 after attempt2); tested
