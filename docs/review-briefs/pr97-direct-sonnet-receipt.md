# Direct Claude Sonnet CLI test — corrected settings isolation

Owner asked to retry using the working setup in https://github.com/diegoami/malpaco/issues/155 . Read the complete issue and comments, read-only. Its key working flag is --setting-sources user,project, excluding repository-local settings; select --model sonnet and verify stream init identity rather than trusting the alias. This invocation resolves the preceding MiniMax-remapped attempt without modifying global settings or provider credentials.

Tested on PR97 exact merged head019950846ae613cda7b201330dd30b158e289c1c, isolated /home/diego/projects/ic2-work/claude98-review97. gh pr diff97 stdout passed byte-for-byte through stdin, SHA256 ff102b3b38d90bef2c93372498bdb95991aacca518e5a23b1b2acea63bc8fb4e. CLI2.1.293 arguments: --model sonnet --setting-sources user,project --effort high --verbose --output-format stream-json --session-id27d4c2a6-7bb9-4abe-80aa-5707a63430ab --tools "" --disable-slash-commands -p <review prompt/shared policy>. Neither --safe-mode nor permission bypass used in the successful retry. No automatic fallback selected.

Identity guard required startup model exactly claude-sonnet-5-5 and matching final modelUsage; mismatch would stop and reject the trial. Both verified. Exit0,85.457seconds, no denied permissions, nonempty full static approve. Session27d4c2a6-7bb9-4abe-80aa-5707a63430ab. Raw final JSON retained alongside this receipt; complete local stream/logs/launcher under /home/diego/projects/ic2-work/claude98-sonnet-runtime. Inherited nonsecret model overrides and endpoint URL were absent. Endpoint provenance from loaded user/project settings was not independently attested; production should verify endpoint as malpaco155 requires. No credentials read or global settings changed.

This is an explicitly requested extra compatibility test of already merged PR97, not a new merge gate, a default reviewer switch, or production adapter completion. Reviewer ran no tools and had only the complete diff/shared policy. All limitations and findings below retained. S1/S2 are nonblocking owner/policy follow-ups, not applied automatically. S3 is an unverified stale-rule search suggestion. S4 and W1–W9 cover attribution/wording, including correct distinction between rulesets and classic branch protection. Parent had separately queried classic branch protection (404 Branch not protected) and rulesets ([]), and normal merge used no admin bypass. Prior research/CI/session checks remain independently recorded in running notes. No game, new CI or source-evidence change.

# Static review of PR97 at head `019950846ae613cda7b201330dd30b158e289c1c`

**Reviewer:** Claude Sonnet 5.5 through the direct Claude CLI, as an owner-requested compatibility test. The implementer is Codex/OpenAI. This review does not replace the earlier Sonnet-via-agy review and does not authorize a merge.

**Method:** I read only the diff pasted into this prompt, plus the shared project policy. I ran no tools. I did not check GitHub, the files, the hashes, CI or the research repo. Anything below that depends on those is marked as unverified.

**Opening verdict: approve.** I found no bugs and nothing that meets any of the four "Blocking means" items. I did find one policy gap and one process concern about the `CLAUDE.md` merge rule. Both are worth a follow-up. The rest is wording and style.

## Bugs / substantive issues

There are no code bugs. The diff is docs, policy and receipts only. The items below are policy defects, not runtime defects.

### S1. The new merge rule says nothing about a check that ran and failed (medium, non-blocking)
Evidence: `CLAUDE.md:70`. The old rule required "green CI (`gh pr checks`)". The new rule says:
- "Skip optional CI where possible."
- "Reviewed work need not wait for optional CI or a size-skipped scan."
- "Honor any required checks."

The rule does not define "optional" versus "required". It also says nothing about an optional check that has finished red. Read literally, a merger could treat a failed optional check as ignorable. That is not what the brief's item 3 intends ("skipped scan called passed", "mandatory requirements bypassed"). It is also not what the owner's quoted instruction asks for, which is to avoid waiting on CI, not to ignore failures.

Suggested fix, as a follow-up edit: add a sentence such as "A check that has already run and failed is read like a review finding, not ignored. A check is required only if the repository enforces it, which a normal `gh pr merge` refuses to bypass."

This is not blocking because required checks are explicitly honored and skipped checks must be reported truthfully. So Blocking-means item 3 is not triggered.

### S2. A PR-specific owner instruction becomes standing policy, and the PR applies that policy to itself (medium, non-blocking, needs owner confirmation)
Evidence:
- `docs/review-briefs/pr97.md` quotes the owner's "exact new instruction" as: "yes, check that we can skip as much CI as possible. You can merge if it is reviewed". It reads as an answer to a question about this task.
- `RUN-NOTES-resupply33-promotion.md` calls it a "standing instruction". That label comes only from the implementer's notes.
- The `CLAUDE.md` Merging rule is a durable behavior change for all future PRs and all backends. Here it is derived from one reply.
- The PR is also merged under the owner's direct instruction. The notes say so, which is correct. The rule does not need to bless its own merge.

The reading is plausible and the brief endorses it. But it is the implementer's interpretation, and the diff holds no independent record that the owner meant it as standing. The project's own "Ask, don't guess" rule applies here. Because PR97 is already merged, the cheap fix is to have the owner confirm the standing scope. Link that confirmation, or the issue comment, from the `CLAUDE.md` bullet or the notes.

### S3. Other copies of the old rule may remain (low, unverified)
`docs/agent-workflow.md` is updated in this diff. `CLAUDE.md` says shared policy lives in one place so the entry points do not drift. This diff cannot show whether other restatements of "green CI" exist, such as `AGENTS.md`, `.claude/skills/review-pr`, `docs/external-review.md` or `docs/review-briefs/README.md`. It also cannot show whether the session memory note "Merge on approve + green CI" is now stale. That note is outside the repo. A grep for `green CI` and `gh pr checks` would settle it.

### S4. The approval covers an earlier head than the one merged (low, disclosed)
The stored review receipt is for `af4ff13`. This PR's head is `0199508`. The delta includes:
- the `CLAUDE.md` amended-date wording,
- the `agent-workflow.md` change,
- the finding's added paragraphs,
- the notes and receipts.

The notes disclose this and call the delta trivial wording fixes. I read the final diff and agree that nothing in it changes evidence or boundaries. The `model-trials.md` row records "approve (static)" without naming the reviewed head. Naming it would help later readers.

## Blocking-means check (items 1–4)

1. **Canonical link, counts and attribution.** These are internally consistent across the finding, brief and notes:
   - merge `64adfb1aedb6a277bcf3fa41537f574d9448a905`;
   - 35 blobs, 997 lines, 286 instructions, 9+9 digests, 3 Wine identities, 3 x86 reruns, residuals 0/0/0;
   - MiniMax session `ses_eb6fd7a66ffeaRTTx2XUQxqFUI`;
   - base `356171b…` equal to "conquest merge" in the finding.

   Whether they are true cannot be checked from the diff. Nothing contradicts them.
2. **No new evidence or boundaries.** The finding's changes are the header, two new paragraphs and the last sentence. The partial-confirmation limit ("does not promote native/natural behavior") and the task #25 "unverified and untouched" limit are kept.
3. **Owner instruction.** It is kept in substance, subject to S1 and S2. Review approval is retained, blocking findings still mean rework, required checks are honored, and a skipped scan is reported as NEUTRAL rather than passed.
4. **Messages and authority.** The text says "no direct main/build message is claimed" and describes IC main as reached through the owner-carried handoff. See W3. The notes say "Ack queued", not delivered.

The Armenia13 exception is kept as the input→loaded Information-form WORD 708→704 at `+0x482`. It is explicitly distinguished from the next-human Bithynia11 x86/Wine endpoint mismatch.

## Nonblocking wording / style

- **W1. Run-together tokens** make the hashes and counts hard to search or copy, in both the notes and the brief:
  - `origin/main356171b…`, `MERGED64adfb1…`, `head41ca53d`, `35blobs/997lines`, `baseline356171b…`, `merge64adfb1…` in the brief's Done-when line, `comment6234109662`, `conversation314043a4-…`.
  - The notes exist so another backend can continue, per `docs/agent-workflow.md`, so these should be fixed. The brief's Done-when line is the review contract, so it matters most.
- **W2. Naming mismatch.** The file is `RUN-NOTES-resupply33-promotion.md` but its title is "Research33 promotion receipt".
- **W3. Tense.** The finding says IC main "is reached through the owner-carried handoff", but the notes list that handoff as still to be given. "Will be reached" or "is to be reached" is accurate. The grammar of that sentence is also awkward.
- **W4. Unlinked PR number.** "the source PR96 size-skipped scan" has no link or description. A reader of the finding alone cannot tell what PR96 is.
- **W5. Multiple END blocks.** The notes contain an old "END pending reviewer choice" followed by "END reviewed/ready to merge". The later block says it supersedes the earlier one. A single final END, or a clear "superseded" marker, would be easier to follow.
- **W6. Local paths and identifiers.** `/home/diego/projects/ic2-work/...` appear in tracked notes. This is harmless and no secrets are visible, but the paths are machine-specific.
- **W7. Unverified evidence cited as "returns []".** The notes say the "Repository rules API returns []" for `main`. To my knowledge that endpoint reports ruleset rules, not classic branch protection. So `[]` does not prove that no required checks exist. The notes' real safeguard, a normal `gh merge` without `--admin`, is correct. I would drop `[]` as evidence.
- **W8. Reviewer-report quirks.** The stored report says "six changed files" (already acknowledged). Its closing section lists files that are not in the diff. The pasted model-trials row uses a different model-label format from older rows. All are cosmetic. The raw JSON, the initial stderr and the initial JSON were retained, which follows the "keep, never delete" spirit of rule 6.
- **W9. Possible duplicate.** `pr97-agy-result.md` repeats the whole report that is also in `pr97-agy-result.json`. That is acceptable for readability.

## Secrets, safety and process

- I see no credentials, tokens or `IC2_RELEASE_TOKEN` use. The stderr file mentions `--dangerously-skip-permissions` only as the tool's suggestion. The notes say it was not used.
- The model-identity caveat is stated honestly: the model comes from the pinned CLI selection, not from a response field.
- The documents state no original-measurement changes, no game runs and no CI configuration changes. I can confirm only that nothing in the diff touches those areas.

## Uncovered limits

I did not verify any of these:
- that PR34 is merged and issue #33 closed;
- that the canonical report URL resolves at `64adfb1…`;
- that GitGuardian passed on research PR34 (new claim in the finding; the notes say it was re-confirmed);
- that PR97 comment `6234109662` exists;
- the 35/997/286/9+9/3/3/0 figures against the research repo;
- any branch protection or required checks on `main`;
- the full finding file (I saw only the hunks, so the "below" reference to Bithynia relies on unchanged text);
- whether other files still carry the old merge wording (S3).

No game, test or CI was needed for a status-only change.

## Decisions for the owner

1. Confirm that the 2026-10-17 instruction is meant as standing merge policy (S2).
2. Decide whether to add the "failed check" sentence to `CLAUDE.md` (S1).

Final pass done.

**Closing verdict: approve (static; nothing blocking).** The follow-ups are S1 and S2, plus a check for stale restatements of the old rule (S3). The rest is wording cleanup.
