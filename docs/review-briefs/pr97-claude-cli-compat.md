# Direct Claude CLI compatibility test

Owner explicitly asked to try gh pr diff piped to claude -p. CLI2.1.293, PR97 exact merged head019950846ae613cda7b201330dd30b158e289c1c, isolated /home/diego/projects/ic2-work/claude98-review97. Parent captured gh pr diff97 stdout and fed identical bytes to claude stdin. Command selected --safe-mode --model sonnet --effort high --tools "" --output-format json -p <review prompt + shared policy>. No commands/tools were permitted to the reviewer; no game/configuration changes, no fallback requested. Source diff SHA256 ff102b3b38d90bef2c93372498bdb95991aacca518e5a23b1b2acea63bc8fb4e. Full raw JSON retained alongside this receipt.

Completed exit0, is_error=false, terminal_reason=completed, nonempty approving static review, permission_denials empty. Session26f3f745-b4e7-4d71-8263-021b03cb446c. IMPORTANT: returned modelUsage reports MiniMax-M3[1m], canonical minimax-m3[1m], despite --model sonnet. stderr reports unrecognized_model MiniMax-M3[1m]. This proves the direct Claude CLI can execute the piped-diff review, NOT Sonnet routing. Model override provenance remains undiagnosed; no credentials/settings inspected or changed. No approval/gate/model-attribution changed based on this compatibility test.

Parent read full returned report before acting. No blocking bugs/security findings. Nonblocking: CI/rules/session metadata not reproducible from diff alone (parent previously verified); dense notes/spacing/historical END states; full report duplication; different file counts across review and receipt snapshots; static-review brief limits. The policy wording itself was rated consistent. No cosmetic follow-up applied to already merged PR. Review ran only over supplied diff/policy and did not verify external systems. The process completed before parent attempted a stop after spotting the model mismatch; no stop signal was sent because the process had already exited.

# Review of PR97 (diegoami/ic2-conquest)

PR97 is a documentation/policy-only change that promotes a research finding, amends the CLAUDE.md "Merging" rule, records an agy/Sonnet pilot review, and adds review receipts. No code, runtime, or build changes. PR97 is already merged (per the prompt); this is a static review of the supplied diff. I have not run any commands, accessed GitHub, or independently verified any external claim.

## Bugs

**None.** The PR contains no code paths, no configuration, no executable logic, and no new dependencies. The agy invocation was run in `plan+sandbox` mode; `--dangerously-skip-permissions` was not used; no credentials were inspected.

## Security

**None.** No new external endpoints, no permission grants, no secrets, no writes to any other repository (rule 2 honored). The stderr file (`docs/review-briefs/pr97-agy-initial-stderr.txt`) records a `--dangerously-skip-permissions` suggestion; the receipt and notes correctly state this was not used.

## Verification claims worth confirming (non-blocking, before relying on them)

These are factual assertions about external systems that the Sonnet reviewer explicitly said it did not verify, and for which the parent receipt claims verification but includes no evidence. They are not blocking if the parent actually re-checked them, but a reader cannot confirm them from the diff alone.

1. `findings/2026-10-17-hostile-control-recruitment-treasury-ledger.md:7` — "Research GitGuardian passed". This is a new CI-status claim about research PR34 that was not in the supplied canonical context. The receipt (`RUN-NOTES-resupply33-promotion.md`, second-to-last paragraph) asserts "R1 research GitGuardian success independently reconfirmed by GH", but no `gh pr checks 34` output or equivalent is committed. The CLAUDE.md rule says "never report a skipped check as passed"; the claim is not about a skipped check, but it is about a non-local check whose status cannot be reconstructed from the diff. Confirm or drop the clause.
2. `RUN-NOTES-resupply33-promotion.md`, "Pre-receipt reviewed head had GitGuardian SUCCESS" — a CI-status claim about PR97 itself. The receipt also claims "Repository rules API returns[] for main; normal gh merge (no --admin) will honor enforced requirements". If the rules API response is genuinely empty, GitGuardian is optional and may be skipped; if it contains GitGuardian as a required check, skipping contradicts the new rule. Both claims are stated as fact, neither is documented.
3. `RUN-NOTES-resupply33-promotion.md` — "intake session approval independently verified in research pinned64adfb1 docs/data/resupply33-intake-review.json". Sonnet flagged R2 that the MiniMax session id `ses_eb6fd7a66ffeaRTTx2XUQxqFUI` "appears only in implementer-authored files". The receipt now points at a research repo file. A reader cannot confirm the file at the merge commit contains this id without fetching the pinned research checkout.

## Style / wording (non-blocking)

1. `RUN-NOTES-resupply33-promotion.md` — pervasive missing spaces around SHA/session anchors make several sentences hard to parse:
   - `origin/main356171b0e27d6f188a9f45f60eceda277c5dbfd5` (paragraphs 2, 3, 5)
   - `MERGED64adfb1aedb6a277bcf3fa41537f574d9448a905` (paragraph 2)
   - `pin356171b/head41ca53d` (paragraph 2)
   - `PR97 OPEN at88fe825` (paragraph 4)
   - `pinned64adfb1` (last paragraph)
   - `All6nonblocking notes` (last paragraph)
   - `comment6234109662` (last paragraph)
   Same pattern in `docs/review-briefs/pr97.md`: `merge64adfb1aedb6a277bcf3fa41537f574d9448a905`, `intake35blobs/997lines/286instructions/9+9digests/3Wine identities/3x86 reruns/residual0`. A single character of spacing per occurrence would fix all of them.
2. `RUN-NOTES-resupply33-promotion.md` — the file is a chain of long, single-paragraph blocks that mix temporal states ("END pending reviewer choice", "Owner selected agy", "END reviewed/ready to merge"). The chronological layering is recoverable but adds friction; a brief subheading per phase would help. Sonnet's R5 (refresh the END block) was addressed in the last paragraph but the earlier "END pending reviewer choice" paragraph was left in place.
3. `docs/review-briefs/pr97-agy-result.md` — duplicates the full review body verbatim under a separate "# Sonnet via agy review receipt" header. Either keep the receipt prose and reference `pr97-agy-result.json` for the body, or keep the body and drop the receipt wrapper; the current shape repeats ~70 lines.
4. File-count phrasing: the Sonnet report says "the six changed files" and then enumerates four plus "the diff context"; the receipt says "actual reviewed diff four, complete patch supplied". The supplied PR diff actually touches ten tracked paths (4 modified, 6 new). The discrepancy is not material because the review artifacts (`pr97-agy-initial*`, `pr97-agy-result.*`, `pr97.md`) are receipts of the review process rather than content for review; but the wording "four changed files" should match the actual review-subset the reviewer saw, which by the reviewer's own list is the four content files, not the diff total.
5. `docs/review-briefs/pr97.md:9` — "All file paths relative to your review worktree." reads naturally; the surrounding paragraph also tells the reviewer to use `gh pr view`/`gh issue view` for verification, which the reviewer correctly chose not to run. Worth noting in the brief that static-only review leaves the listed acceptance items to the parent (which the review explicitly does).
6. `CLAUDE.md:70` — the amended bullet is internally consistent and matches the owner's quoted instruction. No wording issue; included for completeness.

## Uncovered limits

- I did not run any commands and have no tools enabled, so I cannot verify: the SHA `019950846ae613cda7b201330dd30b158e289c1c` as the PR head; the research PR34 merge `64adfb1aedb6a277bcf3fa41537f574d9448a905`; issue33 closure; the canonical report URL at the pinned merge; the contents of `docs/data/resupply33-intake-review.json`; the GitGuardian status of PR34 or of PR97; the repository rules API response for `main`; whether `git diff --check` passes on the supplied diff.
- The Sonnet review is explicitly a static pass; the reviewer flagged the same limits and did not attempt to verify them.
- The agy result lacks a response model-id field, so the reviewer identity is the pinned CLI selection (`claude-sonnet-5-5-high` from a live catalogue listing) and not a self-attestation by the model. The receipt and `docs/model-trials.md` note this honestly.
- I did not see the full text of `findings/2026-10-17-hostile-control-recruitment-treasury-ledger.md`, only the hunks. Sonnet saw the same and noted that the Bithynia "below" reference relies on unchanged text.
- The earlier Sonnet review (R1-R6) is treated by the parent as resolved by re-running checks and small wording edits; the wording edits (R3, R4, R6) are visible in the diff, the recheck confirmations (R1, R2) are stated without evidence.

## Decision

**approve.** No blocking bugs, no security issues, no policy contradictions. The PR is a status/policy change with reviewer receipts and has already been merged under the owner's authorization to skip optional CI. The non-blocking notes above (verification claims to confirm; the cluster of missing spaces in `RUN-NOTES-resupply33-promotion.md` and `docs/review-briefs/pr97.md`; the duplicated receipt body in `pr97-agy-result.md`) are wording/clean-up and can be addressed in a follow-up if desired, or left as-is given the merged state.
