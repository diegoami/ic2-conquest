# Task B11: the exchange hook (Stage 2)

Plan: `docs/proposals/battles.md` §4 B11 and §9 item 3. The player said on 2026-10-04 to take the routine addresses from the research
session's decompile instead of a separate relay: `docs/reports/2026-10-04-decompiled-tactical-battle-rules.md` in
`diegoami/imperial-conquest-2-research` (read only, never written; rule 2). Everything taken from it is labelled **[R-code]** and
checked against the game, never assumed. It starts **after the B5/B8 PR is merged** (one game, one working tree).

## Scope

This task protects: **the game's own battle behaviour and the completeness of the exchange log.** The hook only observes. A hooked
lab exe must play every battle byte for byte as the unhooked lab exe of the same seed does, and its log must hold every `Random`
draw of the battle module, in order, with nothing dropped or invented.

Forbidden results (any one fails the task):
- a hooked battle whose `BATTLEnn.SAV` series or post-battle save differs from the unhooked lab exe's for the same seed and fixture;
- a log that misses a draw, holds a draw twice, or holds a record whose site is not one of the module's call sites (when the buffer
  fills, the hook stops writing and sets an overflow flag: it never wraps silently);
- an exchange line (actor, target, kind, losses) written as known when the log and the snapshot do not fix it;
- the hook writing game memory outside its own buffer, or changing a register or flag that the hooked call site relies on;
- a measured output overwritten or deleted, a binary (exe, save, screenshot) in git, a blind second End turn, a dialog answered Yes
  automatically (CLAUDE.md rules 1 and 6, battles.md §3).

## Design (the planner's choice; change it only with a stated reason)

1. **Hook `Random`, not the routines.** `Random` is `0x40284C` [R-code]; the module calls it from 12 sites (`0x43801A`, `0x43812F`,
   `0x43820D`, `0x438FFB`, `0x439006`, `0x439188`, `0x439191`, `0x439557`, `0x43955F`, `0x4395CE`, `0x4395D8`, `0x43AA88`) and from 2
   after the battle (`0x4592BD`, `0x45951C`) [R-code]. Re-point each of those `call` instructions to one cave that calls the real
   `Random` and then appends a record `(site, range, result, RandSeed 0x45E030 before and after the call, half-round counter 0x4A0B7A,
   side to move 0x4A0B78)` to a buffer. **The cave preserves every register and flag**: `pushfd`/`pushad` around its own work, and
   on return EAX holds exactly the real `Random` result and every other register, EFLAGS and the stack pointer equal what a direct
   call would leave (the real `Random` is called with the caller's EAX unchanged). An offline test runs the cave under an x86
   emulator (e.g. `unicorn`, or a hand-checked disassembly if no emulator is available) with randomised register/flag states and
   compares them with a direct call's. Check
   each site's bytes are `E8 rel32` to `0x40284C` before patching; refuse to build otherwise. The calling convention is Delphi
   register (`range` in EAX, result in EAX): verify it on the first site by reading the record against the formula.
2. **Markers at the routine entries** (`FUN_0043910C` shot, `FUN_004393EC` melee pass, `FUN_00438FB0` Rout) [R-code]: one record with
   the entry's EAX/EDX/ECX, so the log shows which shot, melee or rout the draws belong to. If a register layout is not as the report
   implies, record that and use only the `Random` records.
3. **The buffer is in memory, not a file.** Enlarge the `.patch` section's virtual size (zero-filled, writable; update
   `SizeOfImage`) for a buffer of at least 64 Ki records, a write index and an overflow flag. The harness reads it through
   `/proc/<pid>/mem` after the battle (`Game` already reads memory) and writes it to the tracked data folder. No file I/O in the cave.
4. **Build** in `patches/battle_lab.py` as an option (`lab.py [seed] --hook`), on top of the existing lab caves; record each exe's
   SHA-256 in the data folder.

## Work

1. **Inertness first.** On FLD-RG, HI v HI size one and one mixed cell, seeds 1-3: the hooked and unhooked exes give identical
   series and post-battle saves. If not, stop and report.
2. **Completeness, zero tolerance.** Delphi's `Random` advances `RandSeed` by exactly one LCG step (`seed·0x08088405 + 1`) per call,
   so each record's seed-before must equal the previous record's seed-after, from the battle's first draw to its last. Any break
   (a call from an unhooked site, a dropped or duplicated record) fails the battle's log; the task is not done while any hooked
   battle has a break. Separately, compare the records per half-round with the count the report's draw order predicts from the snapshot
   (copy-in `Random(q·4)` per live slot, placement `Random(5)`, 2 per shot, 4 per melee, 2 per qualifying rout, `Random(3)` per flank,
   `Random(4)` per surviving winner unit). With the chain intact, a mismatch here is a finding about the report's draw order, not a
   gap in the log: list each one in the finding.
3. **Exchange log.** From each half-round's snapshot (targets in slot word 9, shots in word 8) plus the records, rebuild every
   shot and melee: actor, target, `n`, the draws, the predicted loss by the report's formulas, and the observed loss from the next
   snapshot. Report how many exchanges the formulas reproduce exactly; each miss is listed, not averaged away.
4. **Re-run B5 with the hook** (battles.md §5 step 7) once 1-3 pass: the same cells and seeds; the sweep table gains the exchange
   columns, and the share of attributed loss rows becomes exact or each gap is named.

## Done when

- The inertness check passes on all listed cells (comparison files in `runs/experiments/data/run-exp-battle-sweep/`).
- The seed chain is unbroken in every hooked battle (0 breaks, tracked output per battle); the draw-order comparison is in the
  finding with every mismatch listed.
- The register/flag preservation test passes.
- The exchange log exists for every B5 re-run battle; the formula check's result is in the finding with its tracked output.
- `tests/`: an offline test that the build refuses a site whose bytes are not `E8 rel32 → 0x40284C`, and one that the log reader
  stops at the write index and reports the overflow flag.
- The findings draft section B11 states what the hook does not establish (Wine-only; the lab reseed; the AI general's choices are
  observed, not decompiled by this task).
- CLAUDE.md rule 6 holds throughout: text outputs tracked, committed and pushed per batch, never overwritten; binaries in the release
  `run-exp-battle-sweep` with their SHA-256.
