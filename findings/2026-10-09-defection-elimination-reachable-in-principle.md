# Defection elimination (FUN_0044BED8): reachable in principle through rebirth, not tested; its army loop is settled by code

**Status:** a draft from `ic2-conquest`, awaiting promotion. It records why the defection elimination path, the last army-removal path open after `2026-10-09-turn-end-and-ai-army-removals-restore-their-tile.md` (research `e6b4643`), was not run. The player chose to record it without a test (2026-10-09). The reachability chains below were worked out by ic2-research from its reports, at our request.

**Tag:** `[derived]` for the reachability chains (no save shows them). `[confirmed: decompile]` for the army loop (research's report).

## Answer

- **What would happen to armies.** `FUN_0044BED8` eliminates a nation when its city count reaches 0, and its army loop is `for each army a: if a.owner == old: FUN_0044AB90(a)` (`decompiled-elimination-cleanup.md`, :229). `FUN_0044AB90` restored the covered cell in every removal run in play: disband, join, battle loss, siege attrition, mercenary desertion, the AI-vs-AI battle, and the conquest elimination, which runs the same army loop (`6be3778`, `99899ac`, `e6b4643`). So a defection elimination would restore its armies' tiles too. No hand-built test was run, because it would add little to the tile question.
- **Why it is rare.** The capture cascade `FUN_0044BA1C` and the quarterly rebellion `FUN_0044C204` skip capitals, so by those routes a live nation never loses its capital to defection. The one route without a capital test is **rebirth** (`FUN_0044C360`). A dead nation A returns when more than 7 cities with allegiance A have loyalty under 40, triggered by a quarterly rebellion of an A-allegiance city under 30. It moves every such city to A, **whoever owns it**, capitals included.
- **The prerequisite** (research, `[derived]`). A conquest (`FUN_0044C528`) hands every city of the loser A to the winner W, and those cities keep their allegiance to A. W's own capital has W allegiance, so rebirth never takes it. Therefore W's capital must first move onto an A city: W's original capital is captured while W has unity above 415 and at least 8 cities, and `FUN_0044BD2C` moves the capital to W's best city at least 11 tiles away, which can be an A city.
- **Then, two chains:**
  1. **Direct.** W has already lost every W-allegiance city to captures that left it at 6 or more cities. All it holds are A cities at loyalty under 40, so one rebirth takes everything and `FUN_0044BED8` eliminates W.
  2. **Through a stale capital pointer.** Rebirth takes W's A-city capital while W keeps other cities. W stays alive with its capital pointer (+0x444) naming a city A now owns, so `FUN_0044B8D0` no longer protects W's remaining cities. They can then rebel (loyalty under 30) or go in the capture cascade, and the last one leaving runs `FUN_0044BED8`. Rebellions, unlike captures, do not trigger a conquest below 6 cities.
- **None of this appears in any save** on either side. The only elimination in the research saves (Galatia) is a conquest.

## Why not a hand-built test

Testing the end state needs edited city ownership, both nations' sorted city lists, the counts, the capital pointer and the city markers, all consistent. An inconsistent count already corrupted the nation table in this repository's first elimination attempt (`run-exp-turn-end-army-removal`, `attempt_elimination_patched_count.tar.gz`). The state would also be artificial, and the tile question is already answered by the code plus the seven paths run in play.

## Not established

- Any defection elimination in play, natural or hand-built.
- Whether the chains occur in real AI play, and how often.
