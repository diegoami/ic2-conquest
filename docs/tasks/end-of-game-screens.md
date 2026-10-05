# Task: the original's End of Game screens (T138) (given 2026-10-05)

This task is for the clone's T138 (imperial_conquest_2 #708/#701). The clone's End of Game window merged today (#748). It copies the original's title, the years in power and the start-versus-end table. Any difference this task finds between the original and that window goes back to the clone through the research intake as a bug, so the original's behaviour must be exact.

## Scope
This task protects: **the exactness of what the original shows and does when a human seat's game ends.**
- Every screen text, number and after-OK effect is observed in play (a screenshot plus the save before and after), or read from the code with its line cited. The two are never mixed: a `[derived]` claim is never presented as `[confirmed]`.
- A staged (edited) save is labelled as staged wherever it is used. Each edit writes only its own field, and the finding names the edits.

Forbidden results (any one fails the task, and a reviewer will block on it):
- a screen text or table number claimed without its screenshot (or its code line, if `[derived]`);
- a number in the start-versus-end table not traced to its source: which save field or which recorded start value, and the formula;
- a staged state presented as natural play;
- a measured output overwritten or deleted, a binary in git, or a write to another repository;
- a run on a player run's saves, or processes killed by pattern (kill only your own pids).

## Read first
- `CLAUDE.md` (rules 1-6).
- `findings/2026-10-05-player-facing-feature-inventory.md`: rows G04 (Abdicate), V01-V05, EG01 and E16. The research repo's reports (read only): `decompiled-diplomacy-peace-terms-and-instant-battles.md` ("Victory condition"), `decompiled-elimination-cleanup.md` §3, `upkeep-payment-and-desertion.md` ("Debt and deposition").
- The decompile (read only): `THumanFalls_InitializeForm` @ 00455E38, `THumanFalls_OK` @ 004564E4, `FUN_00452034` (the checks at the start of a human turn), `TPremierForm_HumanLeaderFalls` @ 0045C238, `TPremierForm_Abdicate` @ 0045B24C, `FUN_00449078`, `FUN_0044c8f0`.
- The code: `harness/driver.py`, `state/sav.py`, and `runs/experiments/battles/stage.py` for save edits (unity, treasury, city fields; add a field such as the calendar only by the same rule: one field per operation, and no operation means byte-identical). Recent examples of the task layout: `runs/experiments/split_aboard/`, `runs/experiments/v050_rules/`.

## Questions
1. **Code.** For each reason, what does `THumanFalls_InitializeForm` write into each label (`lbl_result1`, `lbl_result2`, `lbl_changes`, `lbl_nat1/2`, `lbl_pop1/2`, `lbl_cities1/2`, `lbl_money1/2`) and the caption? The reasons are: all 334 cities (victory), 250 BC reached, conquered, deposed for debt, deposed for unity below 400, and Abdicate. Where does each "start" value come from, and when is it recorded? How are the years in power computed? What is the order of the tests in `FUN_00452034`, so which reason wins when two hold at once? What does `THumanFalls_OK` do: the seat turns AI, the game ends when no human is left, anything else?
2. **Play.** For each reason that can be reached from a staged save, take one screenshot of the End of Game window, OCR its text, and keep the saves before and after (or the last autosave, if the game ends). Then record what happens after OK: the seat's control, the next window, and whether the program exits or returns to a menu. The reasons: deposition by debt (treasury edited below the limit), deposition by unity (unity edited below 400), the 250 BC end (calendar edited to the last turn before it), Abdicate Yes, and conquered (a human seat reduced to its last city, then that city captured or the capture staged), plus victory if 334 cities can be staged without breaking the save (say if not).
3. **Two humans.** With two human seats, does one seat's End of Game end the game or hand that seat to the computer while the other plays on? Answer this for at least one reason in play.
4. **Exactness.** Check each table number against its source (Q1) on the captured saves.

## Work
- Branch `experiment/end-of-game`; worktree `/home/diego/projects/wt-eog`.
- Data in `runs/experiments/data/run-exp-end-of-game/`. Binaries go to release `run-exp-end-of-game` as per-batch tar.gz files with a tracked manifest. Scripts go in `runs/experiments/end_of_game/`.
- Use your own Xvfb display and game folder.
- Driver pitfalls: hover before clicking; verify every click's effect (memory, a window, or the save), retrying at most twice; never click End turn twice unless the first click provably did nothing. Locate controls with `Game.controls`/OCR, not fixed coordinates (the last review rounds blocked on raw coordinates and unverified clicks).
- Finding: `findings/2026-10-05-end-of-game-screens.md`, in the research-report format.
  - Sections: Method, an Answer per reason (the window text verbatim, the table with sources, the after-OK effect), a table that compares with the clone's End of Game window (title, years in power, the start-versus-end table) where the original differs or adds something, and "What this does not establish" (Wine only; staged saves; the reasons not reached).
  - Mark every claim `[confirmed]` or `[derived]`, and cite saves by bare filename.
- A claims audit (`claims_audit.py`) recomputes every number from the raw saves, the tracked code extract and the tracked OCR readings, with 0 mismatches. A test shows that a doctored save, and a doctored claim in the finding, both fail it. No expected result is typed into the checker: the claimed values are read from the finding and compared with values recomputed from the sources.

## Done when
- Each reason in Q2 is either captured (screenshot, saves released and hashed) or reported as not reachable, with why.
- Q1, Q3 and Q4 are answered with citations.
- The claims audit gives 0 mismatches, and its tests pass.
- CLAUDE.md rule 6 holds throughout: commit and push after each batch and at least every 30 minutes; never delete or overwrite a measured output (a re-run writes new files beside the old ones); saves and screenshots never go in git (their SHA-256 go in `SAVES.sha256`, the files go to the release); if a release call is refused, keep the artifacts and report the exact command; never print `IC2_RELEASE_TOKEN`.

## Deliverables
One PR against main, "findings: the End of Game screens". Its body maps every Done-when line to its evidence.
- Do not merge, and do not run the reviewer.
- If something blocks (a reason that cannot be staged, or a decision only the player can make), stop, commit what was measured, and report.
