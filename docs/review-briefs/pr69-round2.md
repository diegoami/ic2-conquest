
## Scope
This task protects the owner's requirement (2026-10-10) that every run's log records the Wine version and the font set, so screenshot, OCR
and save evidence says which environment produced it (RESULTS.md of run-exp-machine-move: the host fonts change text rendering).

## Blocking means (any one is enough; a blocking finding means rework, never approve)
1. A Game run (start, load, new_game) can produce evidence without the environment being recorded in that run's own log: check how
   experiment scripts pass `log` to Game and whether the line reaches their jsonl/log files, not only the console. If it only reaches a
   console for the common runners, that is blocking.
2. A probe failure can raise or abort the game start, or slow start by more than a second.
3. The fingerprint reads or prints anything from the prefix registry beyond font names (paths, host names, user names).
4. The baseline check can pass while Book Antiqua maps to a different font, the Wine version differs, or the exe hash differs.
5. A test passes with the behaviour it names deleted.
Not blocking: wording, style. When unsure, rate it blocking and say why.

## Report every blocking finding in this one review
Finish the whole diff, check every item above, say "Final pass done" as the last line before the verdict, number findings R1, R2, ….

## Round 2
Round 1 (gpt-5.6-luna) found: R1 the line only reached the console (now $IC2_WORK/environment.jsonl on every start plus add_sink hooks into runner logs); R2 start() overrides bypassed it (now __init_subclass__ wraps them); R3 10 s probe timeouts (now 0.8 s each, 2 s budget); R4 path leaks in errors (sanitize); R5 cache key; R6 tautological cache test; R7 progress claim uncited. Try to get past each fix, check that the runners listed as covered really record into their own logs and that the uncovered list is honest, then review the new code.
