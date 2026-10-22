# PR 81, round 2: re-check of the round-1 fixes (R1-R9)

Round 1 (gpt-6.1-sol, rework) is pasted at the end. Fixes since (Sonnet subagent): e3bb864 (R1 release_sync versioned
record + offline test), 3656b18 (R2/R4 news_scan2: nation-matched whole treaty blocks at any distance, per-file SHA-256,
versioned outputs, v1 dedup record), 1dddd87 (R3 q6 gate check, R7 code_extract_g3.v3 with FUN_0044fa20, R9 proposer-name
check, analysis_g3.v2, news_scan2 selftest), d88ccc9 (finding text R2-R9), bf4a5f9 (END, README). No Wine run was made.
Check `git diff 976145d..HEAD`: each round-1 finding's fix and the new code and text. Do not re-review code untouched since
round 1. Notes: "Review fixes, round 1" / "END (review round 1)" in `docs/progress/g3-original-checks.md`.

## Scope
This task protects: the truth of every claim in the finding (each backed by a tracked output or a cited, hashed, uploaded
save; rule 5) and measured evidence (never deleted or overwritten; rule 6).

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A round-1 finding R1-R9 is not fixed as asked, or its fix does not do what the notes or finding say.
1b. A check the task names (1a-1f, 2, 3, 5, 6) is answered without evidence, or answered with a substitute that is not what
   rows_g3.md asks, without saying so.
2. What this task protects can be got past:
   - a measured autosave or staged save that is not kept under a case/stamp/turn-specific name, hashed in `SAVES.sha256`
     and uploaded (check the release sync records), or a code path in the new scripts that deletes or overwrites a save,
     a log or an earlier output (unconditional writes on non-unique names, `write_text` over an existing file, `cp`
     without a uniqueness guard, a New Game or turn that writes AUTO* without preserving the previous ones);
   - a "nothing happened" or "no change" observation without a positive control in the SAME Wine process;
   - a staged save that is not L1 (fields beyond the named ones changed, save length changed, names over their field size).
   A bypass you proved is blocking.
3. A finding sentence claims more than its tracked output shows: a number that the cited log does not contain, a rule
   stated as [code] without a line in the tracked code extract, a frequency compared with a prediction without the trial
   counts, an incomplete reading (e.g. the stale news buffer after File > Open) used as evidence, or a cited log/save that
   does not exist.
4. Driver clicks at fixed screen coordinates where controls could be read; a test or analysis script whose result does not
   follow from the data it reads.
Not blocking: wording, style, and defects in code the PR did not change. File those as follow-ups. Limits the finding
itself states ("What this does not establish") are not blocking unless the text elsewhere claims them as established.
When unsure, rate it blocking and say why. An approve with a proven bypass is the costliest mistake a review can make.

## Report every blocking finding in this one review
This review is your only pass before the author fixes. Do not stop at the first blocking finding: finish reading the whole
diff and the task file, check every Done-when line and every item under "Blocking means", and report all blocking findings
together.
- Before you write the verdict, make one last pass over the full diff for anything you have not yet rated, and say
  "Final pass done" as the last line before the verdict.
- Number the findings R1, R2, … in order of severity. A finding you held back because an earlier one was already blocking is
  a review defect: if two problems share a cause, list both and say so.
- Do not rely on a later round. The author fixes everything you list, and the next review checks those fixes and new code
  only, not anything you saw but did not report.
- If you ran out of time or context before covering the whole diff, say which files or sections you did not cover. Do not
  approve in that case.

## Round 1 review (for reference)
> PR review (gpt-6.1-sol)
> rework
> R1 runs/experiments/data/run-exp-g3-original-checks/release_sync.py:35 blocking: The sync record uses unconditional `write_text` with a seconds-resolution filename. Two invocations finishing in the same second overwrite the earlier upload record, violating the brief’s preservation requirement. Use `versioned.write_new` or exclusive creation with collision handling, including when nothing needs uploading.
> 
> R2 runs/experiments/data/run-exp-g3-original-checks/news_scan.py:3 blocking: The documented rerun command redirects into the existing measured `news_scan.txt`, truncating it. This shares R1’s missing exclusive/versioned-output protection. Provide a versioned writer and document that invocation; retain the existing scan unchanged.
> 
> R3 findings/2026-10-12-g3-original-checks.md:86 blocking: The stated `[code]` trade-offer rule omits an essential gate. Extract lines 55002–55015 require the candidate nation to have a current trade partner whose tax base is below Rome’s, in addition to the preceding candidate-versus-Rome-partners test. Thus “the others offer trade” does not follow merely from passing the roll and being non-neighbours. Describe both gates, including the fewer-than-three-partners branch, and retain 30 as an upper bound rather than an unconditional trade prediction.
> 
> R4 runs/experiments/data/run-exp-g3-original-checks/news_scan.py:17 blocking: Restricting comparisons to `abs(i - j) <= 1` cannot detect the reverse ordering under investigation: a four-line treaty block followed by its destruction line places the header four positions earlier. Unrelated adjacent lines can also be paired because nation names are not matched. Consequently the report’s zero reverse-adjacent-pair count does not establish the finding at line 70 that treaty blocks are “never first.” Match the participating nations and complete treaty blocks, or narrow the finding to the adjacent pairs actually inspected. Also record per-file hashes and the deduplication calculation supporting “870 distinct by SHA-256”; neither the tracked scan nor its generator contains that evidence. Write any new scan/report beside the old outputs.
> 
> R5 findings/2026-10-12-g3-original-checks.md:59 blocking: Correct two deposition-effect claims. The logged +149/+150 values are changes from staged unity 400, not differences “over its undeposed trials”: undeposed values reach 423, while deposed values are capped at 550. Distinguish before-to-after changes from the capped increment applied after the ordinary tick. Also, `FUN_0044c8f0` lines 50809–50811 clears only cooldowns −1 through −5, not all negative cooldowns.
> 
> R6 findings/2026-10-12-g3-original-checks.md:36 blocking: The alive-Greece staging does not have “the same result” as the dead-Greece staging apart from its count. Its capital remains Athens (166); the logged Athens record receives the capital bonuses, while Tarrentum remains at fortification 62, maximum population 56 and tribute 64. State explicitly which results coincide and which differ. In the preceding seven-city-control paragraph, also remove “relations take the quarter’s thaw only”: `analysis_g3.txt:89` records Greece’s relations with Seleucid and Macedonia changing from 1 to −8, which is not thaw.
> 
> R7 findings/2026-10-12-g3-original-checks.md:7 blocking: The turn-sequencing explanation cites `FUN_0044fa20`, lines 53208–53236, but that function is absent from both tracked extracts. Append a new extract version containing it and cite that version. Correct line 5’s blanket reference to `code_extract_g3.txt` as well: the cited `FUN_004494e4` body exists only in `.v2.txt`. Preserve both existing extracts.
> 
> R8 findings/2026-10-12-g3-original-checks.md:77 non-blocking: Disclose that the condition-60 runs restart the same seed and replay a prefix. `SAVES.sha256:451–474` and `:477–500` show byte-identical corresponding results for the first twelve pairs. The 32 played pairs and pooled arithmetic are real, but they do not represent 32 independent RNG trajectories; separate the repeatability evidence from the frequency comparison.
> 
> R9 runs/experiments/data/run-exp-g3-original-checks/g3_report.py:224 non-blocking: The OCR comparison checks only offer kind, not proposer identity, although finding line 85 claims agreement on both nation and kind. Add an explicit proposer check with documented handling of OCR variants such as `liyia`, or label the automated result as kind-only and record the separate name verification.
> 
> Final pass done
> rework
> 
