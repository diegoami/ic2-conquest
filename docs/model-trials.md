# Model trials: how the reviewers did

One line per review where a model's verdict is worth remembering: a proven bypass rated "not blocking", a wrong rework, a review
that caught what another missed. Started 2026-10-04 with the "Blocking means" rule (`docs/review-briefs/README.md`).

| date | PR | reviewer | verdict | what happened |
|---|---|---|---|---|
| 2026-10-04 | #33 | deepseek-v4.1-flash | rework, then approve | Caught that the gate's cited comparison files were made by no committed command (blocking, right). The approve's notes included a rule-6 overwrite in `keep()` (R5) rated non-blocking; fixed in #35. Under the new rule a proven overwrite of a measurement would be blocking. |
| 2026-10-04 | #35 | deepseek-v4.1-flash | rework, then approve | Rework was right (B2's decoder leaked into A). The approve's R2 (`b0_probe.keep` can still overwrite on a second collision in the same second, rule 6) was rated non-blocking; fixed on #36 before its review. |
