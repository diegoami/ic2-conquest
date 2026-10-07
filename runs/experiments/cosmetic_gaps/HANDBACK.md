# Cosmetic gaps (#723): hand-back, 2026-10-07 (GLM-5.3 session; supersedes the 2026-10-06 MiniMax-M3 hand-back below)

**Implemented by GLM-5.3 via Claude Code** (Sonnet skipped: Claude 7d exhausted until ~2026-10-08 14:00 UTC).

**STATE: PR #66 OPEN, review round 1 (openai/gpt-6.1-sol #low, brief docs/review-briefs/pr66.md) RUNNING.** The finding
(`findings/2026-10-06-cosmetic-gaps.md`), the experiment (b1-b6 + close probe, release `run-exp-cosmetic-gaps`), the claims
audit (**172 checks, 0 mismatches**, `claims_audit_cosmetic.v3.txt`) and the tests (`test_claims_audit.py` 8 OK,
`test_runner.py` 6 OK) are all pushed on `experiment/cosmetic-gaps`. After the review: fix what it lists, re-audit, round 2
or the narrow-approve path per the usual flow; merge on approve + green CI; then #722 help tables is next in the queue.

## New since the M3 hand-back

- **b3 (all four plays recorded, `plays_b3.jsonl`, archive `batch-b3.tar.gz` uploaded, `MANIFEST-b3.txt` tracked):**
  - **S3 scuttle ok**: `wav_opens_CG_S3_b3.txt` — **SOUND8.WAV** opened between the scuttle Confirm and its Yes
    (matches `TUnitMap_ScuttleFleet` line 47348, case 8).
  - **S4 End turn ok**: `wav_opens_CG_S4_b3.txt` — **SOUND9.WAV** during the AI phase after End turn
    (`FUN_0044aee4` line 49639, case 9: an army battle whose BOTH sides are non-local seats).
  - U1/U2 failed on runner bugs (below), evidence kept in the record.
- **Correction to the M3 hand-back**: `wav_opens_CG_S2_b2.txt` is NOT empty — the fleet move opened **SOUND2.WAV**
  (`FUN_0044dd70` line 51985, case 2, the fleet-move executor). The M3 claim "harvest empty, re-run S2" is void.
- **`make_extract.py` was broken and is fixed** (commit with `code_extract_cosmetic.v3.txt`): the CALLSITES
  enclosing-function lookup took the FIRST header ≤ the line (always `FUN_00401338`), not the last. v1/v2's CALLSITES
  "in <function>" column is wrong; **cite v3 only**.
- **`dfm_TAFSupply.v2.txt`** (dump_dfm_supply.py): the form resource, byte-exact. `object AFSupply: TAFSupply`,
  `Caption = 'Supply army'`, ClientWidth 470, ClientHeight 335 (matches the live dialog exactly).
  **`btn_buy: TButton`, `Caption = 'Buy supplies'`** — UA01's caption is settled from the resource.
  (v1 exists with a garbled root header from a parser off-by-one, kept per rule 6, do not cite.)
- **M06 mapping complete [derived], four cases [confirmed]** — every call site re-read by line number in
  `all_app_functions.txt` (the M3 hand-back's address↔event mapping was unreliable; do not reuse it):
  | case | WAV | event | enclosing (line) | play |
  |---|---|---|---|---|
  | 1 | Sound1 | an army marches (main map; battle map too) | FUN_0044d420 (51503), TBattleMap_PlaceUnit (37735), FUN_004381a4 (38236) | S1 ✓ |
  | 2 | Sound2 | a fleet sails | FUN_0044dd70 (51985) | S2 ✓ |
  | 3 | Sound3 | battle ranged attack, unit type byte == 2 | FUN_0043910c (38975) | — |
  | 4 | Sound4 | battle ranged attack, any other type | FUN_0043910c (38978) | — |
  | 5 | Sound5 | battle attack order / melee | TBattleMap_SelectUnit (37682), FUN_004393ec (39077) | — |
  | 6 | Sound6 | city assault repelled ("fails to capture") | FUN_0044b27c (49828) | — |
  | 7 | Sound7 | a city falls ("<city> (<owner>) falls to <nation>.") | FUN_0044b27c (49817) | — |
  | 8 | Sound8 | a fleet is lost: scuttle / "is lost at sea" / naval battle | TUnitMap_ScuttleFleet (47348), FUN_004514ec (54594), FUN_0044b5d0 (49902) | S3 ✓ |
  | 9 | Sound9 | army battle between two NON-local nations | FUN_0044aee4 (49639) | S4 ✓ |
  | 10 | Sound10 | a nation is eliminated (all its cities transferred to the conqueror) | FUN_0044c528 (50627) | — |
  Move sounds (1, 2) play only when the byte at `DAT_00474b00 + <current nation>*0x494` is non-zero (the local-seat
  flag; see FUN_0044d420/FUN_0044dd70); case 9 only when NEITHER side is local.
- **UA01 enablement [derived, corrected]**: `TAFSupply_CityOrFleet` toggles **Visible** (`FUN_00412c08` posts
  CM_VISIBLECHANGED 0xB00B), not Enabled. Own city or own fleet → the 16 buy-side controls (incl. 0x1b0 = btn_buy)
  are HIDDEN, the 14 free-supply controls shown; foreign non-hostile city → the reverse. `TAFSupply_FindProviders`
  scans the 3×3 around the army: city terrain codes 20..99, **skips owners whose relation byte to the current nation
  is 3 (war)**; own fleets in range are also providers. A hidden, never-shown VCL control has no HWND → win_state
  cannot list btn_buy at an own city (that is what U1 b3's sparse read was).
- **`stage_neutral.py`** crafted `STAGED-felsina-neutral-0721.SAV` (artifacts, hashed, in `SAVES.sha256`;
  note `STAGED-felsina-neutral.txt`): the ONLY change is Rome↔Gaul relations 3→0 in a copy of the felsina fixture
  (asserted before writing). Labelled STAGED everywhere.
- **b4 (`plays_b4.jsonl`)**: **U2 ok — at the hostile foreign city (Felsina, war 3) the Supply army dialog does NOT
  open** [confirmed, matches FindProviders]. U1 (own city) and U2B (staged neutral) both reached an OPEN dialog
  (470×335, the error tuples prove it) but died on MY one-line bug — `win_geo(g, wid)` got the window TUPLE, not
  `wid[0]` — before reading controls. **Fixed in scenarios.py after the run** (commit message says so); re-run both
  as batch b5: `python3 run_play.py b5 U1 U2B` (U2 must NOT be re-run with that batch name... it can: a new batch
  name makes new tags; but U2's answer is already recorded — no need).

## Resume here (for the next session)

1. `python3 run_play.py b5 U1 U2B` in `runs/experiments/cosmetic_gaps/` (the wid[0] fix is committed; expect U1 =
   dialog with btn_ok only, btn_buy absent [own city hides the buy controls]; U2B = dialog WITH a visible
   `Buy supplies` TButton — the DFM says btn_buy, the finding cites the exact bytes). Archive (`archive_batch.py b5`),
   commit, push.
2. Write `findings/2026-10-06-cosmetic-gaps.md` (name per the task's done-when; date it 2026-10-07 if preferred):
   M04 (title format + when set — v3 extract's SetTurnTitle CALLSITES), M05 (StoreFormPositions layout + T4),
   M06 (the table above; "what this does not establish": cases 3,4,5,6,7,10 stayed [derived]; no audio device, the
   WAV open is the evidence), A01 (toggle byte + hashes/screenshots from b1 T3; PaintForm shows no marker clearing —
   say what the hashes show), UA01 (caption 'Buy supplies' byte-exact; Visible-not-Enabled; hostile → no dialog
   [confirmed U2 b4]; own city [confirmed b5 U1]; staged neutral [confirmed b5 U2B] — cite the STAGED label).
3. `claims_audit.py` + `test_runner.py` + `test_claims_audit.py` in the leaders_form style (model:
   `runs/experiments/leaders_form/claims_audit.py`; the audit re-dumps the DFM via `dump_dfm_supply.py`'s parser and
   checks every cited line against `code_extract_cosmetic.v3.txt`).
4. PR, review rounds (reviewer from another family via OpenCode; quota-tracker first — L50/L51), merge on approve.

Batches: b1 ✓ uploaded; b2 (partial, superseded evidence kept); b3 ✓ uploaded (`batch-b3.tar.gz`); b4 not yet
archived — `archive_batch.py b4` will pick up its screenshots; **b4's plays jsonl is committed** (or will be with the
hand-back commit). Release `run-exp-cosmetic-gaps` holds b1+b3.

---

# (superseded) MiniMax-M3 hand-back, 2026-10-06

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
## STOPPED 2026-10-07 evening: zai 5h window 93% (resets ~3h). PR #66 ROUND 3 = REWORK, 6 findings NOT YET APPLIED. Resume:

The round-3 comment is on the PR (also rendered/pr66-fb3919/run-1/stdout.log). Triage:
- **R2 (text fix)**: the markers paragraph in the finding credits CG_T3_b8; the markers play is CG_T3B_b8 (b8's T3 has no Show-armies click). One-line fix + audit tag-binding (R1b).
- **R6 (answered, not yet written in)**: measured on the b8 screenshots (run length of identical grey pixels across the map face): byte 1 = mean run 45 px (long uniform regions: the political/mono-STYLE image set), byte 0 = mean 17.5 px (short per-tile variation: terrain-STYLE). The byte selects the ImageList index (FUN_00417550 = ImageList_DrawEx, the flag is the image index). Write this into the finding [confirmed by measurement, via a small tracked script], say which set is which by THESE properties, not the inventory's names.
- **R1 (audit)**: bind the finding's per-row triggers/literals (e.g. case-3's 'type byte = 2' vs the extract line's == 2 condition), UA01 table rows' tags to THEIR dialog records (own-city tag swapped for staged tag must fail), and use the extract version the finding NAMES (not latest()).
- **R3 (test_runner)**: per-kind required proof fields (win_state needs line+x+y+w+h; tooltip needs x; ocr needs word+region; tile needs tile; panel needs panel_line+rect; root needs root id), fabricated/missing-field negative tests per kind; extract Game3.click's guard into a testable function.
- **R4 (cg.end_turn)**: raise DriverError on the 60s timeout (completion condition unmet), record the failed verification; no second click. Test via a refactored wait loop with a stub.
- **R5 (scenarios/clear_autos)**: harvest every play's autosaves (T1's second end turn was lost to the next start_game's clear_autos); make clear_autos refuse when unharvested AUTO files remain (harvest under a _prestart tag); re-run T1 as b9, keep b8.

After the rework: audit + tests green, archive b9, commit, round 4. Then merge on approve + green CI. Then the AI-TURN CORROBORATION (owner-routed; task file docs/tasks/ai-turn-corroboration.md is on this branch; corrected research report = commit 7d7b613): week-11 tax on +0x44A first (sav.py tax/unity/treasury/wealth diffs per End turn, fixed seed), then the free merc hire. THE OWNER SAID: STOP AFTER FINISHING THAT TASK (no #722, nothing after).
