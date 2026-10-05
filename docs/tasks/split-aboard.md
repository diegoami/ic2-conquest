# Task: can an army aboard a fleet be split? (given 2026-10-05)

For the clone's T111 (Split army) and its plan PR #736 (imperial_conquest_2). The clone refuses a split aboard today, and keeps that refusal until there is evidence either way.

## Scope
This task protects: **the exactness of the split rule the clone will copy.**
- The answer is read from the code with its line cited, and confirmed in play with a save pair.
- Code and play are never mixed: a [derived] answer is never presented as [confirmed].

Forbidden results: an answer without a code citation; a play claim without its saves; a measured output overwritten or deleted; a binary in git; a write to another repository; a run on a player run's saves; processes killed by pattern.

## Questions
1. Read `TUnitMap_SplitArmy`'s opening checks. Is there an aboard refusal, as Join armies has? Give its message text if there is one.
2. If a split aboard is allowed, where does `FUN_00449F08` place the new army: on the fleet, or on a land tile next to it? If on land, which tile, and what happens when none is free?
3. In play, with Unit map → Army → Split army on an army embarked on a fleet: what happens? Record the save before and after, the refusal box if any, and where each army is afterwards.

## Work
- Branch `experiment/split-aboard`.
- Data in `runs/experiments/data/run-exp-split-aboard/`; binaries to release `run-exp-split-aboard` as tar.gz with a manifest.
- Finding `findings/2026-10-05-split-army-aboard-a-fleet.md`, in the research-report format: Method, the rule (tagged), the evidence, and "What this does not establish".

## Done when
- The code answer has citations, and the play answer has a released and hashed save pair.
- A claims audit over the raw saves and the code extract gives 0 mismatches.
- CLAUDE.md rule 6 holds.

One PR against main, "findings: splitting an army aboard a fleet". Do not merge, and do not run the reviewer.
