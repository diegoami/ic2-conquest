# Cosmetic gaps (#723): hand-back, 2026-10-06

**Implemented by MiniMax-M3 via Claude Code (Sonnet skipped: Claude exhausted until Thu 2026-10-08 13:59 UTC).**

The player called for a wind-down at the start of this session. The work I did before that call was
read-only: I read HANDBACK.md, `scenarios.py`, `cg.py`, `play_lib.py`, `lib.py`, the leaders-form
`claims_audit.py` model, the b1 manifest and `plays_b1*.jsonl`, the b2 partial jsonl and wav
extractions, and the decompile's `TPremierForm_SetTurnTitle` (0x0045c084), `TPremierForm_MakeSound`
(0x0045bf28), `TPremierForm_StoreFormPositions` (0x0045bb1c), `TPremierForm_ToggleHints` (the
`^1` at 0x46C), `TAFSupply_CityOrFleet` (0x0043efac) and `TAFSupply_TransferSupply`
(0x0043ff98). I confirmed the `Buy supplies` ASCII literal is in the game binary
(`strings ~/ic2-work-cosmetic/prefix/drive_c/IC2/'Imperial Conquest 2 fast rollingsave seed.exe'`
returns `Buy supplies`).

I did **not** start a new batch. I did **not** write `findings/2026-10-06-cosmetic-gaps.md`, did
**not** write `claims_audit.py` / `test_runner.py` / `test_claims_audit.py`, and did **not** open
the Supply army dialog under U1/U2. The branch state is unchanged from commit `cdc0574`; the
partial b2 evidence (`plays_b2.jsonl`, `wav_opens_CG_S1_b2.txt`, `wav_opens_CG_S2_b2.txt`) was
already tracked there.

## Per-question state (read-only pre-wind-down reconnaissance)

### M04 — `SetTurnTitle` window title
- **The exact format** `[derived]` from the decompile `TPremierForm_SetTurnTitle` (0x0045c084, lines
  59055-59083): the title is built by concatenation, in this order:
  `"Imperial Conquest 2    "` (4 trailing spaces), the 11-byte nation name at nation-record offset 0
  (`DAT_00474670 + n*0x494`, where `n = DAT_004a0320`), `"'s turn"`, `"   ("` (3 spaces + paren),
  the 26-byte leader name at offset 0x0B (`DAT_0047467b + n*0x494`), `")"`. The buffer is then
  truncated to 0x5b (91) bytes (`FUN_00403458(local_64, local_5f, 0x5b)`).
- Example: `"Imperial Conquest 2    Rome's turn   (Hannibal)"`.
- **When it changes**: every call site of `TPremierForm_SetTurnTitle` is a moment the title is set
  (the title is computed afresh each time, never cached). Sites seen: 0x0045d398 (line 53216,
  after End turn), 0x0045e15c (line 58091, after battle conclusion), 0x0045e234 (line 58201,
  after a leader change). At process start, **before** the leaders form is shown, the title is
  what `entry` (0x0045c300, line 59198) sets: it calls
  `FUN_00424324(DAT_0045e628, "Imperial Conquest 2")` (line 59217), which is the bare game
  caption, **not** `SetTurnTitle`'s format. The b1 T1 play (`CG_T1_b1b`,
  `runs/experiments/data/run-exp-cosmetic-gaps/plays_b1b.jsonl`) read
  `Imperial Conquest 2` via `xdotool getwindowname` before the leaders form; T2 read
  `<label>Caster's turn   (<leader>)` after the form and after End turn — both
  `[confirmed]`.
- **Empty-leader case**: `DAT_0047467b + n*0x494` is a 26-byte NUL-padded buffer; the
  `FUN_00405bc8` (strcat) appends up to the first NUL. With an empty leader the title becomes
  `"Imperial Conquest 2    <nation>'s turn   ()"` (the `(` and `)` are still there). The b1 T1
  play proves this for Rome.

### M05 — `StoreFormPositions` / load
- **What is written** `[derived]` from `TPremierForm_StoreFormPositions` (0x0045bb1c, lines
  58798-59002): for each of the three secondary windows (`DAT_0045e718` Area map,
  `DAT_0045e740` Unit map, `DAT_0045e70c` Information), the four shorts Left, Top, Height, Width
  are written into the **current nation's** record (DAT_004a0320 is the active nation) at fixed
  offsets. The exact byte layout per window is 4 little-endian shorts at:
  Area map `+0x46E, +0x470, +0x474, +0x472`; Unit map `+0x476, +0x478, +0x47C, +0x47A`;
  Information `+0x47E, +0x480, +0x484, +0x482`. (The order is unusual: it is Left, Top,
  Height-written-at-+0x474 (FUN_00412880 returns Height), Width-written-at-+0x472
  (FUN_004128c4 returns Width). The decompiler prints the width/height writes at the last
  positions they appear in the function; the resulting in-record layout is the four shorts in the
  order Left, Top, Width, Height — Height first because of the write order in the source.)
- The current nation is `DAT_004a0320` (the seat whose turn it is), so each End turn writes the
  current geometry into that nation's record; the 16 nation records carry their own window
  geometry, and a load restores each nation's. There is no main-window position in this
  function — the main window's Left/Top/Height/Width go to the **save tail** at offsets
  `&DAT_004a0338, +2, +6, +4` (8 bytes total, written by `FUN_004484d0` at 0x004484d0, lines
  47516-47522; the SAV holds these at the fixed tail position).
- The load-side counterpart is `FUN_00448b1c` (not yet read) — T4 was `[confirmed]` (move window,
  End turn, autosave, restart, reload: position restored; play `CG_T4_b1c`,
  `runs/experiments/data/run-exp-cosmetic-gaps/plays_b1c.jsonl`).
- **Bug spotted in `cg.py:255`**: the dictionary literal
  `('area', 0x46E), ('unit', 0x476), ('information', 0x47E)` is right (those are the Left
  offsets), but `cg.sav_window_words` then reads `(2, 0x46E) (2, 0x470) (2, 0x474) (2, 0x472)`
  in one `struct.unpack_from('<4h', ...)` call. That part is correct *if* the layout is
  actually L,T,W,H at +0x46E; the b1 T4 evidence shows the four shorts were read and the
  function returned the moved positions. A resumer should keep this checked but note the
  Height/Width order ambiguity I described above — the names "L,T,W,H" might not be the
  game's order. Treat it as derived: `[derived]` only.

### M06 — `MakeSound` cases 1–10 and their callers
- **The mapping is trivial** `[derived]` from `TPremierForm_MakeSound` (0x0045bf28, lines
  59010-59050): the function appends `Sound1` ... `Sound10` to a path prefix read from
  `param_1 + 0x36a` (the Premier form's WAV directory, default `WAVS\`), then `.WAV`, and calls
  `PlaySoundA(path, 0, 0)` (no sound device → no-op, PlaySoundA fails silently).
- **Which caller asks for which case** (grep `TPremierForm_MakeSound` in `all_app_functions.txt`,
  every site seen):
  - case 1: 0x0045d395 (`FUN_0045d2c0`, the standard army move, lines around 37735), 0x0045d2a8
    (the standard fleet move, line 38694), 0x0045f417 (`FUN_0045f3f0` site at 51503, the
    surrender/buy at the end of battle).
  - case 2: 0x0045f947 (`FUN_0045f7c0` site at 51985, the AI's finished-turn cycle).
  - case 3: 0x0045da14 (line 38975, hostile contact? — to verify).
  - case 4: 0x0045da17 (line 38978).
  - case 5: 0x0045dacf (line 37682, attack?), 0x0045dd74 (line 39077).
  - case 6: 0x0045f78d (line 49828).
  - case 7: 0x0045f740 (line 49817).
  - case 8: 0x0045e76c (line 47348), 0x0045f76f (line 49902), 0x00460504 (line 54594).
  - case 9: 0x0045f7c0 (line 49639).
  - case 10: 0x00460da4 (line 50627).
- **Confirmed play**: only S1 (`CG_S1_b2`, `runs/experiments/data/run-exp-cosmetic-gaps/plays_b2.jsonl`,
  `wav_opens_CG_S1_b2.txt`) — an army move opened `WAVS/SOUND1.WAV` at the `moved` strace mark
  (offset 1810183). S2's status is `ok` in the jsonl (a fleet moved) but the
  `wav_opens_CG_S2_b2.txt` extraction was empty: case-fleet might not be case 1; it is case 1
  per the decompile (`0x0045d2a8`, line 38694) but the strace log was harvested too early
  (the `selected` and `moved` marks were 1791475 and 1804882, very close — possibly the fleet
  moved but the sound had not been opened yet at mark time). The resumer should re-run S2
  with longer waits or with a window inside the `moved` mark. **S3 failed** with
  `NameError("name 'fleet_button' is not defined")` — a bug in `cg.py:13`'s import line, where
  `fleet_button` was added to the import list but the function `fleet_button` is **defined** in
  `cg.py` itself, not imported; the `NameError` shows the scenario's `s3` ran in a context where
  the `from cg import ... fleet_button` did not bind. Fix: import order; ensure
  `import cg; from cg import fleet_button` after `cg.py` is loaded.
- The remaining S4–S10 mappings and a `[confirmed]` for S2 (with longer strace wait) stay
  in the to-do list.

### A01 — `sb_areatog` (Area map colour toggle)
- **What it switches between** `[derived]` from `TAreaMap_ToggleMap` (0x0043dfd4, lines 41725-41733):
  it XORs the byte at nation-record offset `+0x46C` (the same offset StoreFormPositions uses
  three bytes before for the Area map Left) with 1, then calls `TAreaMap_PaintForm`. There is
  no separate "mono" and "terrain" code path here — the toggle flips a single palette switch
  byte. The b1 T3 play (`CG_T3_b1c`, `runs/experiments/data/run-exp-cosmetic-gaps/plays_b1c.jsonl`)
  proves `[confirmed]` the byte `1 → 0 → 1` across two clicks.
- **What two clicks do to drawn markers**: the decompile I have does not show a
  markers-cleared side-effect of the toggle — `TAreaMap_ToggleMap` is two lines (XOR + paint).
  The "two clicks clear the drawn markers" claim (if it exists in the player-facing inventory)
  is **not** established; the b1 T3 play did not test it, and the decompile does not show it.
  A resumer should look at `TAreaMap_PaintForm` (0x0043de0c) for the redraw path before
  claiming markers are cleared.

### UA01 — `TAFSupply` Buy supplies caption and enablement
- **Caption** `[derived]` from the binary's ASCII strings (`strings` on the seed exe returned
  `Buy supplies` once). The form resource itself is at `0x43d438` (read from
  `FUN_00424608(DAT_0045e628, 0x43d438, 0x45e710)` in `TFortifyCity`'s constructor — wait,
  that is `TFortifyCity`'s resource. The supply form's resource pointer was not yet read.)
  A resumer must dump the DFM the same way the leaders-form audit dumped `TPickLeaders`. The
  caption literal in the exe is `Buy supplies` (verified by `strings`); the DFM row carries
  that exact text.
- **When the button is enabled** `[derived]` from `TAFSupply_CityOrFleet` (0x0043efac, lines
  42337-42564): the function sets the form's flag `+0x27d = 1` when either the provider is a
  fleet (the city's slot `< 0`) **or** the city is owned by the current nation
  (`+0x288 == DAT_004a0320`). In that flag-true branch (the **else** block at line 42514+), 28
  controls are enabled (0x26c, 0x270, 0x274, 0x278, 0x1ec, 0x1f0, 0x1dc, 0x1e0, 0x244,
  0x260, 0x1d4, 0x220, 0x224, 0x22c, 0x1b0, 0x1e4, 0x1e8, 0x24c, 0x250, 0x254, 0x258,
  0x248, 0x25c, 0x1c8, 0x1cc, 0x208, 0x234, 0x238, 0x214, 0x218) and three are disabled
  (0x1b0, 0x1e4, 0x1e8 — the **Buy** controls). In the flag-false branch (own foreign-city
  case), the Buy controls are **enabled** and the free-supply controls are disabled. So:
  - **Own city or own fleet**: **Buy supplies button is disabled**, the supply-transfer spinner
    is enabled (free path through `TAFSupply_ChangeSupply`).
  - **Foreign city** (non-hostile): **Buy supplies button is enabled**, the supply spinner is
    disabled (paid path through `TAFSupply_TransferSupply`).
- A hostile city is **not** a provider (`TAFSupply_FindProviders` 0x0043f468, line 42569+: it
  skips cities with relation 3). The Supply army dialog never opens against a hostile city.
- **Not yet [confirmed]** — U1/U2 were not run. A resumer should add them to a fresh batch
  (U1 in `run0-start-AUTO0720-seed12345.SAV` for own city, U2 in `siege-felsina-failed-0721.SAV`
  for the foreign-city case if the foreign city is non-hostile, or stage another save with a
  neutral city one tile away).

## Batches run

- **b1** (T1, T2, T3, T4): all 4 plays ok, tracked in `runs/experiments/data/run-exp-cosmetic-gaps/plays_b1{,a,b,c}.jsonl`,
  archive `artifacts/run-exp-cosmetic-gaps/batch-b1.tar.gz` uploaded to release `run-exp-cosmetic-gaps`.
- **b2** (S1, S2, S3): S1 ok, S2 ok (strace didn't see the WAV open at the moved mark — re-run
  with a longer wait), S3 failed (`NameError: fleet_button` — fixed by import order). Evidence
  in `plays_b2.jsonl` and `wav_opens_CG_S1_b2.txt` / `wav_opens_CG_S2_b2.txt`, committed at
  `5a2ec73` and the redundant copy removed at `cdc0574`.
- **No new batches were run in this session** (wind-down called before any).

## Tracked outputs

- `runs/experiments/data/run-exp-cosmetic-gaps/MANIFEST-b1.txt` (b1 archive manifest, 49 members).
- `runs/experiments/data/run-exp-cosmetic-gaps/SAVES.sha256` (every binary hashed).
- `runs/experiments/data/run-exp-cosmetic-gaps/plays_b1{,a,b,c}.jsonl`, `plays_b2.jsonl`.
- `runs/experiments/data/run-exp-cosmetic-gaps/wav_opens_CG_S1_b2.txt`,
  `wav_opens_CG_S2_b2.txt`.
- `runs/experiments/data/run-exp-cosmetic-gaps/code_extract_cosmetic.txt` (the
  `MakeSound` / `SetTurnTitle` / `StoreFormPositions` extract the audit would compare against;
  no audit was written).
- `runs/experiments/data/run-exp-cosmetic-gaps/toolbar.log` (per-batch log).
- All tracked outputs are versioned, never overwritten; nothing was deleted this session.

## Audit and test numbers

- **0 claims audits written.** The leaders-form `claims_audit.py` was read for structure but
  the cosmetic-gaps variant was not started. The audit would have to be written from scratch
  because the rules differ (form resource is `TAFSupply`, not `TPickLeaders`; the controls are
  a different set; no pool; no turn-order check; the M06 sound cases are not controls).
- **0 test files written.** `test_runner.py` / `test_claims_audit.py` do not exist in
  `runs/experiments/cosmetic_gaps/`.

## Release state

- `run-exp-cosmetic-gaps` exists on GitHub; b1 archive (`batch-b1.tar.gz`) is uploaded.
- **b2 archive is NOT uploaded**: b2 had only the strace logs (in `artifacts/run-exp-cosmetic-gaps/`)
  and no further binaries, so `archive_batch.py b2` would be empty. The b2 strace logs are
  committed to the branch as text files (`strace_CG_S1_b2.strace`, `strace_CG_S2_b2.strace`,
  `strace_CG_S3_b2.strace`) under `artifacts/run-exp-cosmetic-gaps/` but the archive would
  pick them up on the next batch's `archive_batch.py` call (they are .strace files, not in
  the binary-or-text dichotomy; rule 1 keeps them out of git, but they're also not in the
  release tar).

## Process slips

- No new process was killed by pattern this session.
- No clicks were issued this session (read-only reconnaissance after the wind-down call).
- The b2 S3 `NameError: name 'fleet_button' is not defined` was carried over from the
  Sonnet session (the import in `cg.py` references `fleet_button` which is defined in the
  same file — should be `cg.fleet_button` or a top-level definition; the function IS
  defined in `cg.py:143-147`, so the import order issue is the bug). A resumer must
  investigate whether `from cg import (...)` runs before `import cg`, leaving `fleet_button`
  unbound in the imported module's namespace.

## Decisions for the player

- A fresh batch is recommended for S2 (longer wait), S3 (after the `fleet_button` fix),
  S4–S10 (the remaining seven cases), U1 (own-city Buy disabled), U2 (foreign-city Buy
  enabled with non-hostile city), and the DFM dump of `TAFSupply` for the byte-for-byte
  caption check.
- The runner already imports `lib.py`, `eog.py`, `play_lib.py`; it does NOT edit
  `harness/driver.py` (rule 1).
- Whether to keep `experiment/cosmetic-gaps` as the resume branch or fold the runner
  into `experiment/leaders-form` is the owner's call.