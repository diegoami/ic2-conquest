# Model trials: how the reviewers did

One line per review where a model's verdict is worth remembering: a proven bypass rated "not blocking", a wrong rework, a review
that caught what another missed. Started 2026-10-04 with the "Blocking means" rule (`docs/review-briefs/README.md`).

| date | PR | reviewer | verdict | what happened |
|---|---|---|---|---|
| 2026-10-04 | #33 | deepseek-v4.1-flash | rework, then approve | Caught that the gate's cited comparison files were made by no committed command (blocking, right). The approve's notes included a rule-6 overwrite (R5: bare `shutil.copy` in `battle_series`/`run_battle` onto fixed names) rated non-blocking; fixed in #35 by routing both through `keep()`. Under the new rule a proven overwrite of a measurement would be blocking. |
| 2026-10-04 | #35 | deepseek-v4.1-flash | rework, then approve | Rework was right (B2's decoder leaked into A). The approve's R2 (`b0_probe.keep` can still overwrite on a second collision in the same second, rule 6) was rated non-blocking; fixed on #36 before its review. |
| 2026-10-04 | #36 | deepseek-v4.1-flash | rework, then rework | First review: R1/R2 (screenshots overwritten and unhashed, a sprite-rule claim with no tracked output) were real and blocking. Second review: R1 a real catch (the defender-slot mirror used an index although B2 had shown the AI side is re-sorted); R3 (`halflog.py` could overwrite a `-<STAMP>` file on a third regeneration, rule 6) was rated non-blocking despite the brief's item 2 and was treated as blocking. |
| 2026-10-04 | #36 | deepseek-v4.1-flash | rework (third) | R1/R2 were real catches (a size-range and a loss-row figure that did not match the cited output; the audit then found more of the same kind). R3 (`sweep-table`/`compare` could overwrite in the same second, rule 6) and R5 (a `grid` edit past the grid overwrote the header, the `header` op took unknown keys) were rated non-blocking despite the brief's item 2 and treated as blocking. |
| 2026-10-04 | #38 | gpt-6-luna#high | rework ×7, then approve | Each round reported one new blocker that was already visible in earlier rounds, 8 rounds in all. This led to the "Report every blocking finding in this one review" section in every brief (`docs/review-briefs/README.md`). Sol is used for complex PRs since. |
