
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

## Round 5 (fresh)
Round 4 was answered by MiniMax only because the Luna run was misclassified (see the orchestrator note on this PR); that approval does not count. This is a full review of the current head. Earlier rounds fixed: console-only line (environment.jsonl + sinks + folder_sink), start() overrides and monkeypatched starts (record on Game.pid), probe budget 0.9 s, path sanitising, cache key, per-pid logging, tests. Try to get past each, then review the whole diff.
