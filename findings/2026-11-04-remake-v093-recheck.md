# Recheck on remake v0.9.3 (a44c42fc): three fixes confirmed in play; the stale-word fix misses cross-region mercenary runs

**Tag:** [confirmed: remake replays against the stored original games; inert Wine walk hook + remake code]. Wine only.
**Task:** owner 2026-11-04, "0.9.3 is out".

**The release.** Remake `v0.9.3` = main `a44c42fc` = `1723c673` + 3 commits. The engine change is `031296d8`, T276
(#1753), "Faithful AI execution fixes":
- **launch:** `LaunchTile` → `ClassicalFleetNavigation.ReplaceLandTarget` on the live map;
- **AI build city:** `ChoosePort` under Classical uses `OriginalFleetPort.IsPort` (the eastern zone excluded) and the first
  city record on ties;
- **embarked army:** a `MercenaryRun` lands at `MercenaryRunDestination`;
- **stale word:** a failed DB38 search event (`OriginalArmyIntermediateSearchFailed`) suppresses the next EBE8 walk's swing
  and recursion.

`AiCapitalDefence` is unchanged.

## 1. Anchored replays of the eight stored long games

**Runs.** Rome, Carthage, Gaul and Seleucid (`run-exp-longrun-v090`), Ptolemaic and Macedonia (`-v091`), Numidia and Greece
(`-v092`), 305 turns each way:
- `--pin a44c42fc --turn-seed 12345 --out anchored-a44c42fc-ts`;
- `--out anchored-a44c42fc`, the fixed seed.

**Failed turns, all transient.** Three turns failed for lack of memory while other jobs ran ("Out of memory", exit −6):
Carthage t14 and t17, Seleucid t24 (turn-seeded). They were replayed with the new `anchored.py --retry-errors`, all
successfully. An error scan of every anchored folder (`anchored-error-scan-v1.txt`) found one more, earlier failure: the v0.9.2
turn-seeded Seleucid t12 ("Process terminated", FailFast). The v0.9.2 analysis had skipped it silently; it was retried
successfully. `stays.py` now reads retried turns (`tNN-rN`).

**Turn-seeded, against v0.9.2's turn-seeded replays** (`ts-a44c42fc-vs-1723c673-v1.txt`):

| Game | Position rows | Gone | Fix |
|---|---|---|---|
| Rome | 14 → 13 | Seleucid fleet t36 | launch on the live map (the v0.9.2 regression at Issus) |
| Gaul | 23 → 22 | Seleucid fleet t30 | launch |
| Macedonia | 26 → 19 | Seleucid fleet t30; Media fleets t19, t25, t26, t27; Ptolemaic army and fleet t33 | launch; Caspian build city |
| Numidia | 26 → 19 | Rome army and fleet t29, t30, t31; Gaul t31 | the embarked mercenary-run landing |
| Carthage, Seleucid, Ptolemaic, Greece | unchanged | — | — |

The Seleucid game's Ptolemaic t12 row looked new, but it was the v0.9.2 failed turn: after the retry, v0.9.2 shows the same
row.

**Stays.**
- Turn-seeded (`stays-a44c42fc-ts-v1.txt`): 14 rows. The Numidia t37 stale-word row remains (§2).
- Fixed seed (`stays-a44c42fc-v1.txt`): identical to v0.9.2's, the four war-roll rows and four port rows of the fixed-seed
  artefact.

## 2. Remaining: the stale-word fix requires the same region, and the measured cases cross regions

**T276's rule** (`MoveArmyCommandHandler`): the failed-search event is published only when
`Classify(from) == Classify(target)` and `Intermediate(...)` is null. A cross-region target takes the ferry branch instead.
When no transport is found, that branch ends the walk without the event, so the following EBE8 walk still swings.

**Both measured cases cross regions** (the remake's own `ClassicalArmyNavigation.Classify`):

| Case | E84C walk | Classify | Original (inert `walk_hook`) | v0.9.3 |
|---|---|---|---|---|
| Numidia t37, Ptolemaic army 13 | (193,96) → offer (192,77) on Cyprus | (−1,1) against region 7 (the 190–207 × 68–79 box) | e913 direct 0, word −1; EBE8 (ecd6) direct 1, entry word −1; no swing; stays (193,96) | "garrison fallback moved army-13 to (195, 97)" (`probes/a44c42fc-num-t37pre`) |
| **Celtiberia t39–40, new**, Macedonia army 8 (13,138) | (143,49) → offer (162,54) | side 0 against side 1 (the coordinate split) | `hooks-walk-celt40-v1` seq 23–27: e913 direct 0, word −1; EBE8 (ecd6) toward Larissa (142,49), direct 1, entry −1; no swing; stays (143,49) with 10 moves | "garrison fallback moved army-8 to (143, 48)" (`probes/a44c42fc-celt-t40pre-seed12385`) |

So in the original, DB38's −1 is written on these cross-region E84C walks too. The walk hook shows the word go from 0 at
entry to −1 at the no-progress test, and research verified DB38 as the only writer.

**Fix direction:** publish the failed-search event whenever the E84C walk's initial search yields no intermediate point,
including the cross-region case where the remake's ferry branch finds no transport. Which original branch runs there (DB38
alone, or D9A8 first) is for research to specify.

## 3. Registry and capital defence

- **Registry recheck** (`run-exp-recheck-a44c42fc/report-v1.json`): 113 / 11 / 11 / 4, row for row identical to v0.9.2.
- **Capital defence while a human battle is pending:** unchanged (not addressed by v0.9.3).

## 4. A new long game on v0.9.3: Celtiberia

Celtiberia, rulebot-1, 40 turns, seed 12345, RandSeed logged (`run-exp-longrun-v093/celtiberia-rulebot1-40t`). 40 turns, no
game over.

**Failed turn.** The fixed-seed replay's turn 3 failed with a segmentation fault (exit −11). The retry was fine, and the
turn-seeded replay had no error.

**Stays:**
- fixed seed: 3 rows;
- turn-seeded: 5 rows (`stays-celtiberia-*-v1.txt`):
  - **Macedonia t39, t40** (Larissa): the §2 gap, in both seedings;
  - **Macedonia t15, t17** (Pella, capital army): turn-seeded only, consistent with war rolls; not examined;
  - **Macedonia t37** (an army next to the enemy city Ambracia with 0 moves; in the remake it no longer exists): not
    examined.

**Classify:** 95 relation nation-turns, 21 position, 2 count, 21 draw-only turns.

## Open

- §2: the cross-region failed search (for research to specify, then IC main).
- Capital defence while a human battle is pending.
- Greece t21 (resupply flip during the round), Numidia t24 and t32, Celtiberia t15, t17 and t37.

## Evidence

**Data:**
- `runs/experiments/data/run-exp-longrun-v093/`: `ts-a44c42fc-vs-1723c673-v1.txt`, `stays-a44c42fc*-v1.txt`,
  `anchored-error-scan-v1.txt`, `celtiberia-rulebot1-40t`, `stays-celtiberia-*`, `classify-celtiberia-v1.txt`,
  `hooks-walk-celt40-v1`, `probes/`;
- `run-exp-longrun-v09{0,1,2}/*/anchored-a44c42fc{,-ts}`;
- `run-exp-recheck-a44c42fc`.

**Saves:** releases `run-exp-longrun-v093` (`celtiberia-rulebot1-40t-saves.tar.gz`, `v093-recheck-saves.tar.gz`) and
`v093-anchored-saves.tar.gz` on `run-exp-longrun-v090`, `-v091` and `-v092`. Start: `decidestarts/celt-t40pre.SAV` = the
campaign's `original/t39-a00.SAV` (turn 40 has no human orders).

**Tooling:** `difftest/anchored.py --retry-errors`.
