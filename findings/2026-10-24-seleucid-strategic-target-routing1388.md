# Seleucid End-turn divergence: reachability filtering and intermediate routing

**Tag:** [confirmed, partial: one private owner campaign, original Wine controls,
original-instruction replays and pinned production-native diagnostics].
**Status:** draft for Research intake. Remake [#1388](https://github.com/diegoami/imperial_conquest_2/issues/1388)
remains open; no production correction implemented. Related acceptance:
[#1355](https://github.com/diegoami/imperial_conquest_2/issues/1355).

## Answer

The defender's `(212,96)` versus `(212,94)` boundary has a deterministic
strategic explanation in the recorded campaign. The two engines choose different
enemy targets because they use different reachability tests. The original also
routes through an intermediate point which the remake's move command omits.
This local explanation does not synchronize the whole End-turn RNG/action stream.

The original selects the 7,000-troop Ptolemaic army at `(191,95)` with returned
army score **828**. Its destination wrapper first chooses `(189,104)` as an
intermediate point. Seven moves from `(219,93)` then finish at **`(212,96)`**.

Pinned remake `main` **`3c1860079db6dd9b1fb11ceb8b726c7fd95293ac`** rejects that
western target as unreachable by its direct walker. It instead selects the
31,565-troop army at `(207,95)`, score **212**, and finishes at **`(212,94)`**.

Conditional replays isolate both requirements:

| Destination actually given to the low-level walker | Original instructions | Production remake | Matching entered steps |
|---|---|---|---|
| `(207,95)`, remake target | `(212,94)` | `(212,94)` | 7/7 |
| `(191,95)`, original target with routing bypassed | `(213,94)` | `(213,94)` | 7/7 |
| `(189,104)`, original intermediate point | `(212,96)` | `(212,96)` | 7/7 |

Thus the observed discrepancy does not require a low-level step correction.
Changing only target filtering would still produce the wrong endpoint in this
case. Faithful evaluation must cover both target eligibility and the destination
wrapper's routing. No morale, training, tactical coefficient or Computer general
change is justified by this strategic observation.

## Evidence and controls

Runners: `runs/experiments/seleucid1388/`.
Public scalar checks: `runs/experiments/data/run-exp-seleucid1388/audit-v1.json`.
Source identity: `source-pin-v1.json` there verifies all **332** archived source
blobs against the pinned Git tree. Engine/Data were built in this repository's
ignored artifact tree, with no writes to another checkout. Engine build passed
with three existing Data nullable warnings; diagnostic builds passed.

Private run `run-exp-seleucid1388`, original turn **0755 → 0756**:

- `S1388-hook-seed1-v1-before.SAV` / `S1388-hook-seed1-v1-after.SAV`;
- `S1388-plain-seed1-v1-before.SAV` / `S1388-plain-seed1-v1-after.SAV`;
- `S1388-hook-seed1-v2-before.SAV` / `S1388-hook-seed1-v2-after.SAV`.

All three before saves are byte-identical; all three after saves are
byte-identical. The two observer versions and one control without hooks use
the same seed and input: **one trajectory, not three independent scenarios**.
The defender has 78,857 troops and zero moves at `(212,96)` after each End turn.
These are isolated Wine runs of the seeded fast rollingsave build. Earlier
unmodified-original acceptance runs remain separate evidence on #1355/#1388.

Memory-only CALL-site observers preserve GPRs, flags, stack, army header and
seed across **816 emulated CPU states**, including full-buffer cases. Seventeen
guarded call sites are covered. The second observer takes one atomic pre-walk
RAM snapshot for original army record 4; the snapshot and complete logs remain
private. Its whole-save control equality includes the extra snapshot work.

Observed original calls for that army:

1. `0x44F409 → 0x44DBA8`: strategic destination `(191,95)`, origin `(219,93)`,
   seven moves. This is the target tree's attack-army branch.
2. `0x44DC3A → 0x44D734`: low-level walk toward `(189,104)` from the same origin.
   This is the destination wrapper's indirect-routing branch.

Actual unmodified original instructions were then run under Unicorn from that
captured RAM, with **no targeting, movement, terrain or RNG helper replaced**:

- `FUN_0044EE60` returns original target record 24, score 828, distance 28.
- `FUN_0044CAB4` accepts both western targets. `FUN_0044CA30` gives the same
  `(region=-1, coast=1)` pair for origin and both target coordinates. No fleet
  exception is required for this case.
- `FUN_0044CB40` rejects the direct line to `(191,95)`;
  `FUN_0044DB38` returns intermediate point `(189,104)`.
- The complete original `FUN_0044DBA8` wrapper reproduces the **entire 656-byte
  defender army record** in the real post-End-turn save, including `(212,96)`.
- Original targeting/routing/walking helpers call no `System.Random`
  (`0x40284C`) here and preserve `RandSeed`. Five local emulator inputs
  (`0,1,2,12345,0xFFFFFFFF`) retain target 24 and endpoint `(212,96)`.
  These are local seed controls, not five new whole-turn games.

Three diagnostic ordinary `GameSession.Submit("end")` runs of the pinned remake
produce identical terminal native states and `(212,94)`. Its decision log,
accepted travel timeline and exact pre-command state are retained privately.
All four relevant army field strengths match the original snapshot exactly:
actor 22,320; enemy strengths 26,460 / 11,529 / 2,964. Target choice is therefore
not explained by differing strategic morale or power inputs in this control.

Using that native command boundary, actual production `WalkTowards` reproduces
all **21/21** original coordinate-store steps over the three conditional walks
above. Its unlimited walk to `(191,95)` stops at `(209,94)`, blocked at
`(207,94)`, so production `IsReachable` rejects it. The nearer target's unlimited
walk reaches adjacency and is accepted. The original's eligibility test does
not require this direct-walk success.

## Source boundary and downstream work

Original pinned `all_app_functions.txt` SHA256
`2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`:
`FUN_0044CA30` / `CAB4` at lines 50819/50856, `CB40` at 50898,
`D174` at 51274, `DB38` at 51761, `DBA8` at 51790,
`EE60` at 52715 and target tree `F31C` at 52899.
Routing reads the original intermediate-point/connectivity data and line tests;
it is more than a geometric line to the final target.

Remake source boundaries are
`Ai/AiArmyTargetTree.cs::IsReachable`, the target scorers calling it,
`Ai/AiMilitaryPhase.cs::AddArmyTargetCandidate`, and
`Movement/Commands/MoveArmyCommandHandler.cs`. Current movement calls the
low-level walker directly. A downstream correction needs the normal Main
workflow, meaningful destination-wrapper and eligibility regressions, the
original navigation data, and broader routing/contact/fleet controls. A blanket
"all targets reachable" change or hardcoded intermediate point is unsupported.

## Limits and privacy

No production source correction, full strategic AI parity, whole-turn draw
alignment, general export readiness or native Windows acceptance is claimed.
These conditional original/native controls have their respective measured
states, not an assertion that every campaign field is identical. The exact
matched field strengths, target rules and 21 paired steps bound the attribution.
Other strategic scorer/state differences can coexist.

Owner inputs, saves, full RAM/state/traces and their hashes stay private under
ignored artifacts. No owner binaries were uploaded or published. Earlier
failed setup/build attempts and superseded controls are retained; the v1 helper
replay's RNG hook address was corrected before the final v4 helper evidence.
The physical Escape interruption of native Computer Use remains respected.
