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
  fills, the hook stops writing and sets an overflow flag: it never wraps silently, and a battle whose flag is set fails its log);
- an exchange line (actor, target, kind, losses) written as known when the log and the snapshot do not fix it;
- the hook writing game memory outside its own buffer, or changing a register or flag that the hooked call site relies on;
- a measured output overwritten or deleted, an EXE, DAT, save, screenshot or video in git, a blind second End turn, a dialog answered Yes
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
   **Every call site is covered:** the build scans the whole `CODE` section for every reference to `0x40284C` (`E8`/`E9` rel32,
   `FF 15`/`FF 25` and any absolute dword equal to it), lists those inside the battle module (`0x436FB4`–`0x43ABB4` [R-code]) and in
   `TBattleOver_InitializeForm`/`OK` (their address ranges taken from the report [R-code] and confirmed by the two post-battle sites
   falling inside them), and refuses to build unless that list equals the hooked list (the report's 12 + 2, or the
   scan's list with the difference stated in the finding).
2. **Markers at the routine entries** (`FUN_0043910C` shot, `FUN_004393EC` melee pass, `FUN_00438FB0` Rout) [R-code]: one record with
   the entry's EAX/EDX/ECX, so the log shows which shot, melee or rout the draws belong to. A marker displaces the entry's first
   instruction(s) into its cave: the build checks those bytes against the ones recorded in this task's first build (and refuses on any
   difference), and the marker cave is held to the same rule as the `Random` cave: every register, EFLAGS and ESP preserved, the
   displaced instructions re-executed exactly, then a jump back; the same emulator test covers it. If a register layout is not as the report
   implies, record that and use only the `Random` records.
   **Every memory address used** (all [R-code]: `RandSeed 0x45E030`, counter `0x4A0B7A`, side `0x4A0B78`, battle flag `0x4A0B7C`, the routine entries, `Random`) is checked
   once live before the hook relies on it: the header words against B2's decoder and a Save As block, the battle flag by reading it 1 during a battle and 0 right after
   "Battle ended" in the same process (B0 used it; record it again here), `RandSeed` by stepping the LCG
   across one known `Random` call, the entries by a breakpoint-free check (the marker fires exactly where a lab snapshot says a shot,
   melee or rout happened). Each check is a tracked output.
3. **The buffer is in memory, not a file.** Enlarge the `.patch` section's virtual size (zero-filled, writable; update
   `SizeOfImage`) for a buffer of at least 64 Ki records, a write index and an overflow flag. The harness reads it through
   `/proc/<pid>/mem` after the battle (`Game` already reads memory) and writes it to the tracked data folder. No file I/O in the cave.
4. **Build** in `patches/battle_lab.py` as an option (`lab.py [seed] --hook`), on top of the existing lab caves; record each exe's
   SHA-256 in the data folder.

## Work

1. **Inertness first.** On FLD-RG, HI v HI size one and the mixed cell `MIX-RG` (FLD-RG with both armies as they stand in the research start save, no edit:
   Rome's army 0 against Gaul's army 10, the B0 battle), seeds 1-3: the hooked and unhooked exes give identical
   series and post-battle saves. If not, stop and report.
2. **Completeness, zero tolerance.** Delphi's `Random` advances `RandSeed` by exactly one LCG step (`seed·0x08088405 + 1` mod 2^32, the Delphi RTL; confirmed by the live
   `RandSeed` check above) per call,
   so each record's seed-before must equal the previous record's seed-after, from the battle's first draw to its last. **The
   boundaries are pinned too:** the first record's seed-before must equal the seed the lab cave writes at battle start or resume
   (nothing drawn before it), and the cave also records `RandSeed` when the battle flag `0x4A0B7C` [R-code, checked live above] clears and after the last
   post-battle site, which must equal the last record's seed-after (nothing drawn after it, up to `TBattlePols`' reseed). Any break
   (a call from an unhooked site, a dropped or duplicated record) fails the battle's log; the task is not done while any hooked
   battle has a break. Separately, compare the records per half-round with the count the report's draw order [R-code] predicts from the snapshot
   (copy-in `Random(q·4)` per live slot, placement `Random(5)`, 2 per shot, 4 per melee, 2 per qualifying rout, `Random(3)` per flank,
   `Random(4)` per surviving winner unit). With the chain intact, a mismatch here is a finding about the report's draw order, not a
   gap in the log: list each one in the finding.
3. **Exchange log.** Slot word 9 = melee target slot (−1 none) and word 8 = shots left [R-code], and a lab snapshot is the state
   after a side's moves and before its melee [R-code]: check both first, on the B5 data, against `state/battle_block.py` and the
   next snapshot (a word-9 target must be adjacent to its unit and the pair's troops must drop at the melee; a word-8 drop must
   match a shot), with a tracked output; if either fails, attribute from the `Random` records and markers only and say so. Then,
   from each half-round's snapshot plus the records, rebuild every
   shot and melee: actor, target, `n`, the draws, the predicted loss by the report's formulas (§4 shooting, §5 melee, §6 rout [R-code]), and the observed loss from the next
   snapshot. Report how many exchanges the formulas reproduce exactly; each miss is listed, not averaged away.
4. **Re-run B5 with the hook** (battles.md §5 step 7) once 1-3 pass: the same cells and seeds, and **every hooked battle is compared byte for byte with its unhooked B5 row** (the
   `BATTLEnn` series and post-battle save SHA-256 recorded by B5); any difference stops the re-run and is reported; the sweep table gains the exchange
   columns, and the share of attributed loss rows becomes exact or each gap is named.

## Done when

- The inertness check passes on all listed cells and on every B5 re-run battle (comparison files in `runs/experiments/data/run-exp-battle-sweep/`).
- The seed chain is unbroken in every hooked battle (0 breaks, tracked output per battle); the draw-order comparison is in the
  finding with every mismatch listed.
- The register/flag preservation test passes for the `Random` cave and every marker cave; the call-site scan equals the hooked
  list; each address check has its tracked output.
- The exchange log exists for every B5 re-run battle; the formula check's result is in the finding with its tracked output.
- `tests/`: an offline test that the build refuses a site whose bytes are not `E8 rel32 → 0x40284C`, and one that the log reader
  stops at the write index and reports the overflow flag.
- The findings draft section B11 states what the hook does not establish (Wine-only; the lab reseed; the AI general's choices are
  observed, not decompiled by this task).
- CLAUDE.md rule 6 holds throughout: text outputs tracked, committed and pushed per batch, never overwritten; binaries (EXE, DAT, saves, screenshots, video) never in git (rule 1), in the release
  `run-exp-battle-sweep` with their SHA-256.
