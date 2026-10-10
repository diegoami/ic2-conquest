# Task: rule reads for the clone's v0.5.0 (purse cap, tribute, disbanding, a priced hire, a refused attack) (given 2026-10-05)

Requested by the imperial_conquest_2 main session for its v0.5.0 tasks. One finding per question, so each can be promoted on its own.

## Scope
This task protects: **the exactness of the rules the clone will copy.**
- Every rule is read from the code with its line cited.
- Every "seen in play" claim cites a save before and after.
- Code and play are never mixed: a [derived] rule is never presented as [confirmed].
- Nothing is written to another repository.

Forbidden results (any one fails the task, and a reviewer will block on it):
- a rule stated without its code citation (function and address) or its save pair;
- a gate or condition from the code dropped from the stated rule;
- a play claim whose before/after saves do not show it;
- a measured output overwritten or deleted, a binary in git, a write to another repository, a blind second End turn, a run on a player run's saves.

## Questions, in order of need
1. **The purse cap (T72, imperial_conquest_2 #317, bug #315).**
   - List every write to an army's purse (its money field) in the decompile: every function and line, and for each, whether the result is capped at 1,000 (or another value) and how (min, a refusal, the surplus moved elsewhere).
   - Cover at least: Supply army / Buy supplies, army-to-army transfer OK, Split, Join armies (the clone caps at 1,000; the original's save IP016 holds 1,066), the automatic resupply on a move (E12: +500 top-up, excess over 1,000 to the treasury), mercenary pay and desertion, a captured treasury, and the quarterly tick.
   - Confirm two of them in play, Join armies and one other, with save pairs.
2. **The Balance sheet's "Tribute" line (T109, #567).** Which income term it names. The likely candidate is the tax-base quarter share. Give the formula from `TPolitics` / the balance-sheet code, and check it against one save's numbers.
3. **Disbanding a queued recruitment (T108, #566).** How much of the money already invested is lost. The help says it is lost; the amount is unread. Read it from the code, then confirm it in play: treasury and queue before and after one disband.
4. **A hire from a priced mercenary offer (T113, #571).** The inventory saw only a free offer. In play:
   - hire a priced offer;
   - check the price is taken from the army's purse, as the formula `(troops × quarterlyPrice[type]) / 1000 × quality` says;
   - record the offer, the purses before and after, and the unit added.
5. **Disbanding a regular unit lowers mobilisation (T136, #706).** It is [derived: code]. Confirm it in play: the nation's mobilisation before and after one disband.
6. **A refused attack (T135, #705).** Does the original declare war before or after it checks that the attack is legal?
   - Read the order in the attack path: the prompt "Are you sure you want to attack…?", the war declaration (relation 3 and the ally cascade), and the legality checks (moves, adjacency, and so on).
   - If cheap, confirm in play: an attack that is refused (for example an army with 0 moves) on a nation at peace, and whether the relation changed.

## Sources (read-only)
- `~/ic2-work/decompile/all_app_functions.txt` and `delphi_symbols.tsv`.
- `~/ic2-work/build/Imperial Conquest 2.exe`.
- The research reports, especially:
  - `upkeep-payment-and-desertion.md`;
  - `decompiled-fleet-tax-and-mercenary-formulas.md`;
  - `decompiled-quarterly-billing-and-economy.md`;
  - `2026-10-03-army-to-army-ok-supply-rebalancing.md`;
  - `controlled-army-supply-transfer.md`;
  - `decompiled-mobilization-and-mercenary-restock.md`;
  - `decompiled-diplomacy-peace-terms-and-instant-battles.md`.
- This repository's `docs/rules-digest.md`, `coverage.md`, `findings/`, `harness/driver.py` and `state/sav.py`.

## Work
Branch `experiment/v050-rule-reads`. Data in `runs/experiments/data/run-exp-v050-rules/`; scripts in `runs/experiments/v050_rules/`; binaries to release `run-exp-v050-rules` as per-batch tar.gz archives with a tracked manifest.

For each question:
- read the code first;
- then run the shortest play confirmation on the normal build, from fixture saves (copies) only;
- write the result as one finding `findings/2026-10-05-<slug>.md` in the research-report format, with Method, the rule (tagged), the evidence table, and "What this does not establish".

Commit and push each finding as soon as it is done. Questions 1-3 come first.

## Done when
- One finding per question, each with its code citations and, where play was run, save pairs released and hashed.
- A claims audit, recomputed from raw saves and the code extract, gives 0 mismatches.
- CLAUDE.md rule 6 holds throughout.

## Rules (CLAUDE.md rule 6, in full)
Measurements are kept, committed and pushed as they are made, and never deleted.
- Every text output a finding or a PR may cite goes under the tracked data folder above.
- Commit and push after each batch, and at least every 30 minutes.
- A re-run writes new files beside the old ones: versioned writers.
- Saves, screenshots and exes never go in git: their SHA-256 go in `SAVES.sha256`, and the files go to the release.
- If a release call is refused, keep the artifacts and report the exact command.
- Never print `IC2_RELEASE_TOKEN`.

Driver pitfalls:
- Hover before clicking, verify every order's effect, retry at most twice, and never retry End turn.
- Use your own Xvfb display and game folder.
- Kill only pids you started, and never use `pkill -f`.

## Deliverables
One PR against main, "findings: rule reads for the clone's v0.5.0". Its body maps every Done-when line to its evidence and lists which clone task each finding serves. Do not merge, and do not run the reviewer. If something blocks, stop, commit what was found, and report.
