# Computer General: control predicate, setup timing, interruption and reload state

**Status:** draft for research issue #24 / build issue #1104, awaiting research
intake and MiniMax review. This supplies original-side evidence; it does not
change the remake, comparison harness, fixtures or expected draws. Issue #25's
full comparison remains gated on integrating an independently reviewed
general-control correction.

**Provenance:** `[code]` pinned original decompile/instructions; `[x86]` original
instructions under Unicorn; `[Wine]` direct original execution, including
explicitly staged human/AI flags. **No native Windows confirmation.**

**Source:** `all_app_functions.txt`, SHA-256
`2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`;
functions with original line numbers are retained in
`runs/experiments/data/run-exp-ai-oct16/targeted-code-extract.txt`; the second
Information-window clear handler is retained separately in
`runs/experiments/data/run-exp-ai-oct16/general-clear-handler-source.txt`.
The fixed-seed-1 lab observer is built from the existing lab EXE; it records
Random calls and entry markers at setup, control checks, general-on and Walk.
Its reserved record word reads the four bytes at `0x45e6a4`: attacker general,
defender general, battle ended, human interruption. It writes no game fields.
The task-local observer's CPU/stack noninterference checks and a plain-lab
control are recorded with the data.

**Saved evidence:** unchanged `gate2_a_BATTLE01.SAV`, `...02.SAV`, `...03.SAV`
from [run-exp-battle-probe](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-battle-probe),
turn **0743**. New boundary saves and observer binaries are in
[run-exp-ai-oct16](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-ai-oct16),
with `SAVES.sha256`. `observations-20261016-152721.json` and its Markdown table
name every authoritative log, saved boundary and exact slot state. Lab file
numbers restart per process; the board counter carried inside each save is
recorded separately. They are not interchangeable.

## Predicate and its consumers

`[code][x86]` `FUN_00438378` (38271) is:

```text
computer_control = (active nation's human byte == 0)
                OR (active side == attacker AND attacker_general)
                OR (active side == defender AND defender_general)
```

Only the active side's general matters. The actual original function agrees
with all 16 human/side/two-general-bit combinations in
`code-truth-tables-20261016-150205.json`. Its callers include setup
`FUN_00439968`, Walk `FUN_00438d24` and its step helper `FUN_00438a6c`, and
shooting `FUN_0043910c` (tracked caller index). The top-level general loop
`FUN_00439c84` similarly forces the active nation's human flag to computer
behavior when that side's general bit is set.

`[code]` Setup clears the active side's target words to -1, assigns type move
allowances, and changes moves to **1** when all of these hold at setup time:

1. the control predicate above is true;
2. unit type is not heavy infantry (type 1);
3. the nearest living opposing unit is farther than 2;
4. the **pre-increment** board counter is < 10.

Setup then increments the counter. There is no placement-phase exclusion in
that gate. The source is `FUN_00439968` (39189-39285), particularly 39257-39279.
The move-exhaustion/target-check ordering inside Walk remains distinct from
the meaning of this predicate; no combined emulation was used as proof.

## Placement and first movement

`[Wine]` The immutable original pair itself shows the effect to explain:

- `gate2_a_BATTLE02.SAV`, counter 2, attacker/placement: Rome's heavy infantry
  slot 0 at (7,2) has 2 moves; archers slot 1 at (8,2) have 4; heavy cavalry
  slot 2 has 5; light infantry slot 3 has 4.
- `gate2_a_BATTLE03.SAV`, counter 3, attacker/movement: slot 0 reaches (6,4),
  Chebyshev distance **2**, and slot 1 reaches (7,3), distance **1**. Those
  units have exhausted their moves. Targets in these rows remain -1.

These are original files, not port output or tolerated differences.

`[Wine][code]` A fresh process resuming BATTLE02 starts with general bits 0.
Setup runs before the toolbar is clicked: the human gets full type allowances.
Clicking Computer General sets the active side's bit and starts its general
loop; it does not retroactively refill or reduce a setup already performed.
The following movement setup sees general on and limits non-heavy-infantry
moves under the gate above. This explains full placement moves alongside a
one-cell early movement without a phase-specific exemption.

| Control | Observed setup/behavior | Evidence (turn 0743) |
|---|---|---|
| Human nation, general off, fresh-process resume | heavy infantry 2, archers 4, cavalry 5, light infantry 4; next movement setup also full | `gen_human_off-20261016-150636-540904-BATTLE01.SAV`, states in the same run log |
| Same human, general enabled after placement setup | full existing placement allowances; next setup marker has attacker-general=1 and early movement uses the slow gate | `gen_human_on-20261016-150636-540904-BATTLE01.SAV` / `...BATTLE02.SAV`, setup/Walk/draw trace |
| AI Rome, general off; Gaul made human to retain a UI stop | Rome's resumed placement setup already uses 1 for non-heavy-infantry; heavy infantry remains 2 | `gen_ai_control-20261016-150636-540904-BATTLE01.SAV` |

The AI control changes **only** Rome/Gaul human flags in a copied battle save;
it does not recopy or resort tactical slots. The matching human-off plain-lab
boundary `gen_plain_off-20261016-150636-540904-BATTLE01.SAV` is byte-identical to
the observed-build human-off boundary.

## Off/on through the UI

`[code]` `TBattleMap_ComputerGeneral` at `0x437ab8` sets the active side's bit to
1; it is not a symmetric bit toggle. The general's targeting/movement passes
poll mouse-down messages on the **Information** window. A human-side click
there clears that side's general bit and sets interruption byte `0x45e6a7`.
The relevant clear sites are in `FUN_0043a31c` / `FUN_0043abb4` (39835-39838,
40254-40257). AI-nation control remains true even with general off.

`[Wine]` Queuing an Information-window click after general-on produced flags
`[0,0,0,1]` and returned control to Rome at counter 6; non-heavy-infantry slots
which had not yet moved retained their one-move setup. Re-enabling through
the toolbar produced `[1,0,1,0]` by battle end. This is a real UI interruption,
not a write into the general bits. It is not claimed to stop before the first
unit: the saved sequence shows the half-rounds that ran before the click was
consumed. Evidence: `probe-20261016-150939-545243.jsonl` and its
`gen_interrupt_on-20261016-150939-545243-BATTLE*.SAV` series, turn 0743.

## Reload has a transient setup effect

`[code]` `TBattleMap_StartBattle` calls fresh-copy-in or resumed setup **before**
clearing both general bytes (37447-37457). The general flags are runtime state,
not fields restored from the 2,105-byte saved battle block. Therefore a fresh
process and an existing process with a previous general bit still set can
perform the same resumed setup differently, even though both return with the
general bits cleared.

`[Wine]` In one process, finish the human-general battle, then reopen unchanged
`gate2_a_BATTLE02.SAV` through the ordinary UI:

| Moment | General flags | Counter / phase | Active moves HI / Ar / HC / LI |
|---|---|---|---|
| initial fresh-process resume | 0,0 | 3 / placement | 2 / 4 / 5 / 4 |
| previous battle finished | 1,0 | battle ended | n/a |
| same-process resume | 0,0 | 3 / placement | **2 / 1 / 1 / 1** |
| next setup, after one manual End turn | 0,0 | 4 / movement | **2 / 4 / 5 / 4** |

The transient short-move placement is saved as
`gen_reload_on-20261016-152304-549608-BATTLE27.SAV`, turn 0743; its state
and the following setup are in `probe-20261016-152304-549608.jsonl`. An earlier
replicate in `probe-20261016-150636-540904.jsonl` shows the same live state.
Setup-entry markers read the old attacker-general=1 on reload; subsequent
control checks see 0. This is separate from the source save's board counter
and from whether the nation is human.

## Morale, sorting and draws

`[code]` The +3 strategic morale adjustment and pre-copy unit sorting in
`FUN_00437de4` test the nation's human flag only. A battle general does not
turn a human nation into an AI nation for those operations. They must remain
separate from the control predicate. These new resume probes do not execute
fresh copy-in and therefore do not independently confirm those bonuses in play.

`[Wine]` Each observed run retains raw Random range/result/site/counter/side
and seed records, plus setup/predicate/Walk markers and general bits. All Random
results match the original generator formula; no recorder overflow or re-entry
was seen. Seed chains match within each battle-start segment. A same-process
lab resume deliberately reseeds to 1: the raw cross-start mismatch is retained
and the analysis splits at the explicit start marker, without renumbering,
changing or discarding a draw. This is not an unexplained draw divergence.

The saved boundaries retain exact slots, grid, moves and targets, including
later half-rounds. General off, on, interrupted and re-enabled are different
input sequences; their streams are not claimed interchangeable. No full
remake replay, original-fixture modification or range rebaseline was performed.

## Limits and next step

This establishes the predicate, early setup gate, UI interruption and the
observed reload ordering for the cited original/Wine inputs. It does not
establish native Windows behavior or resolve the remaining 318-log target
selection investigation. Research should intake this report, then the build
session can define a bounded correction preserving nation-only sorting/morale
and accounting for reload timing. Only after that correction and #1103/#1105
are integrated may research issue #25 rerun the immutable comparison.
