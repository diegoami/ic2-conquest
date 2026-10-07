# The cosmetic rules the clone lists in its #723: the title bar, the ten sounds, window positions in the save, the area-map colour toggle, and the Supply army Buy button

**Status:** draft finding from `ic2-conquest`, awaiting promotion. For clone issue `imperial_conquest_2` #723 (post-0.5.0 cosmetic
batch; feature-inventory rows M04, M05, M06, A01, UA01). Task `docs/tasks/cosmetic-gaps.md`, experiment
`runs/experiments/data/run-exp-cosmetic-gaps/` (release `run-exp-cosmetic-gaps`: `batch-b1.tar.gz`, `batch-b3.tar.gz`,
`batch-b4.tar.gz`, which also carries the b5, b6 and close-probe binaries — 16 members).

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; the cited lines are kept with
their dump line numbers in `runs/experiments/data/run-exp-cosmetic-gaps/code_extract_cosmetic.v5.txt` — **v5**: v1/v2's CALLSITES
enclosing-function column is wrong (a lookup bug fixed from v3 on); v3 lacks the `TAFSupply` and sound-event function bodies
(added in v4) and the entry and the two size getters (added in v5)). `[confirmed]` = seen in play with the verified runner: every
click located and proved (tooltip-proved toolbar x, `win_state` control lines, the driver's tile targeting), the save/screenshot
hashed in `SAVES.sha256`. The two tags are never mixed. The non-hostile-city play runs on a **staged** save, labelled as such
below and in the play record; every other play is a repo fixture.

## Answer

### 1. The title bar (M04)

The title is built by concatenation `[derived]` (`TPremierForm_SetTurnTitle` @ `0045c084`, dump lines 59055-59083):
`"Imperial Conquest 2    "` (**four** trailing spaces) + the nation name (11 bytes at nation-record offset 0, `DAT_00474670 + n*0x494`)
+ `"'s turn"` + `"   ("` (**three** spaces + paren) + the leader name (26 bytes at offset 0x0B) + `")"`, then truncated to 91 bytes.
With an empty leader the parens stay: `Imperial Conquest 2    Rome's turn   ()`.

Seen in play `[confirmed]` (the X window name read with `xdotool getwindowname`, never OCR):

| moment | title | play |
|---|---|---|
| process start, before the leaders form | `Imperial Conquest 2` | `CG_T1_b1b` |
| leaders form open, no game yet | `Imperial Conquest 2` | `CG_T1_b1b` |
| first human turn, EMPTY leader name | `Imperial Conquest 2    Rome's turn   ()` | `CG_T1_b1b` |
| after loading a save with a named leader | `Imperial Conquest 2    Rome's turn   (Appius Claudius)` | `CG_T2_b1c` |
| after End turn (same seat again) | unchanged from the row above | `CG_T2_b1c` |

the bare start caption itself is `[derived]` from the entry code; each table row is only the `[confirmed]` observation of it.

**When it is set** `[derived]`: `SetTurnTitle` is called from three places — `FUN_0044fa20` (line 53216, the seat-advance path after
End turn), `TPremierForm_OpenGameFile` (58091, after a load) and `TPremierForm_StartTurn` (58201). At process start the caption is
**not** built by it: the entry code (`0x0045c300`, line 59217) sets the bare `Imperial Conquest 2` through `FUN_00424324`, which is
what the first two rows show `[confirmed]`.

### 2. The ten sounds (M06)

`TPremierForm_MakeSound` @ `0045bf28` (59008-59048) appends `Sound<N>` to the Premier form's WAV directory (form field +0x36a,
default `WAVS\`) and `.WAV`, then `PlaySoundA(path, 0, 0)` — case *N* plays `Sound<N>.WAV`, one line per case, nothing else
`[derived]`. Every call site in the dump (16), with its event:

| case | WAV | event | call site(s): dump line, in function | evidence |
|---|---|---|---|---|
| 1 | Sound1 | an army marches (main map) | 51503 in `FUN_0044d420` (the army-move executor: terrain cost check, record swap, movement-point deduction) | `[confirmed]` `CG_S1_b7`: the move window opened `WAVS/SOUND1.WAV` (first seen in `CG_S1_b2`) |
| 1 | Sound1 | a unit moves on the battle map | 37735 in `TBattleMap_PlaceUnit`; 38236 in `FUN_004381a4`; 38694 in `FUN_00438a6c` (the second battle move path, same pick-the-cheaper-tile shape) | `[derived]` |
| 2 | Sound2 | a fleet sails | 51985 in `FUN_0044dd70` (the fleet-move executor, same shape) | `[confirmed]` `CG_S2_b7`: `WAVS/SOUND2.WAV` (first seen in `CG_S2_b2`) |
| 3 | Sound3 | battle ranged attack, firing unit's type byte = 2 | 38975 in `FUN_0043910c` | `[derived]` |
| 4 | Sound4 | battle ranged attack, any other unit type | 38978 in `FUN_0043910c` (the `else` of the same test) | `[derived]` |
| 5 | Sound5 | a battle attack order / melee | 37682 in `TBattleMap_SelectUnit` (the hostile-target click); 39077 in `FUN_004393ec` (melee resolution, the 0x47946c matrix) | `[derived]` |
| 6 | Sound6 | a city assault is repelled | 49828 in `FUN_0044b27c`, the `else` of the message `"<nation> fails to capture <city>"` | `[derived]` |
| 7 | Sound7 | a city falls | 49817 in `FUN_0044b27c`, with the message `"<city>   (<owner>)  falls to <nation>."` | `[derived]` |
| 8 | Sound8 | a fleet is lost — scuttled | 47348 in `TUnitMap_ScuttleFleet` | `[confirmed]` `CG_S3_b7`: the scuttle's Confirm→Yes window opened `WAVS/SOUND8.WAV` |
| 8 | Sound8 | a fleet is lost at sea, or destroyed in a fleet battle | 54594 in `FUN_004514ec`, with the message `"A fleet belonging to <nation> is lost at sea."`; 49902 in `FUN_0044b5d0` (fleet-vs-fleet resolution) | `[derived]` (no play provoked these two paths) |
| 9 | Sound9 | an army battle whose BOTH sides are non-local nations | 49639 in `FUN_0044aee4` (guard: both owners' local-seat byte = 0) | `[confirmed]` `CG_S4_b7`: during the computer nations' phase after End turn, `WAVS/SOUND9.WAV` (first seen in `CG_S4_b3`) |
| 10 | Sound10 | a nation is eliminated: every one of its cities is transferred to the conqueror | 50627 in `FUN_0044c528` (iterates all 334 cities, transfers, merges the visibility bitmaps) | `[derived]` |

Two guards shape what is audible `[derived]`: the move sounds (cases 1, 2) play only when the byte at
`DAT_00474b00 + <current nation>*0x494` is non-zero — the **local-seat** flag, so a move is heard only when the moving nation is
played on this machine; case 9 is the complement (both sides non-local, a "distant battle" cue).

**No sound device: the file still opens** `[confirmed]`: this rig has no audio output (Wine under Xvfb), and the WAV open happens
anyway — every `[confirmed]` row above is the `openat` of the WAV in the play's strace log (`wav_opens_CG_*_*.txt`, attributed to
the play step whose log-offset mark it follows). Nothing here says the audio backend plays anything (or fails): with no device on
the rig, the file open is the whole of what is established (see *What this does not establish*).

### 3. The area-map colour toggle (A01)

`TAreaMap_ToggleMap` @ `0043dfd4` (41725-41733) is two lines: XOR the byte at nation-record +0x46C with 1, then repaint
(`TAreaMap_PaintForm` @ `0043de0c`) `[derived]`. There is one palette byte, no separate mono/terrain path.

**What the byte switches** `[derived]`: `TAreaMap_PaintForm` (0x0043de0c) draws the map background through `FUN_00417200` with
the flag **1** when the byte is 0 and **0** when it is 1 (the only two-way use of the byte in the function) — the same tile
bitmaps, two draw modes. Which mode the inventory called "mono" and which "terrain" is NOT established here: what is
established is two visibly different renders and the byte that selects between them.

**The button's own appearance** `[derived]` from the form resource (`forms.json` of the feature-inventory data): `sb_areatog` is
a `TSpeedButton` with one `Glyph.Data` (362 bytes), `ShowHint`, and **no** `GroupIndex`/`AllowAllUp`/second glyph — it has no
latched-down look, so the button looks the same in both palette states; the state shows in the map face, not on the button (its
tooltip `Toggle colour` was seen before each click `[confirmed]`).

Played `[confirmed]` (`CG_T3_b1c`, button located from the live Panel1 rectangle plus the form resource's declared offset, its
tooltip `Toggle colour` seen before each click): byte `1 → 0 → 1` over two clicks; the map face's grey mean moved
`109.402 → 82.368 → 111.385` (the render really changes and returns); screenshots of all three states
(`CG_T3_b1c_area_before/after_one/after_two.png`). The byte after two clicks returns to its start; the region hash returns to
within 2 of it, not byte-identically — the map is repainted, and the screenshots, not the hash, are the evidence of what the eye
sees. Before the repaint the toggle resets the map's own selected-cell word (form field +0x2B8 to 0xFFFF) and a byte (+0x1EE);
there is no path that clears drawn markers — the claim "two clicks clear the markers" has no code behind it `[derived]`.

### 4. The Supply army dialog and its Buy button (UA01)

**The form** `[derived]` from its TPF0 resource (`dfm_TAFSupply.v2.txt`, dumped read-only from the exe): `object AFSupply:
TAFSupply`, `Caption = 'Supply army'`, ClientWidth 470, ClientHeight 335 — and the live window is exactly 470x335 `[confirmed]`
(`CG_U1_b6`). The paid-path button is `btn_buy: TButton`, `Caption = 'Buy supplies'`, at resource Left 320 Top 136 100x26, its
OnClick is `TransferSupply`; `btn_ok` (Left 200 Top 300 70x25) runs `TAFSupply_OK`, which sets the form's confirmed flag and posts
`CM_RELEASE` (`FUN_0042313c`, message 0xB021) — the form frees itself **seconds after** the OK click on this rig
`[confirmed]` (`CG_CLOSE_PROBE2`, a fully verified click with its `win_state` line, pointer read-back and target: closed at
t+4.75 s; the first raw-click probe `probe_close_b5.txt` measured t+4.0 s).

**Who may provide supplies** `[derived]` (`TAFSupply_FindProviders` @ `0043f468`): a 3×3 scan around the army; tiles with a city
terrain code (20-99) whose owner's relation to the current nation is **not 3 (war)** become providers (two slots); own fleets in
range are providers too (three slots). A hostile city is never a provider.

**Money and stock are not part of the enablement** `[derived]`: `CityOrFleet`'s two branches read only the provider slot and the
city's owner — no treasury, army-purse or supplies value enters the Visible decisions (the paid path's money check, if any, is in
`TransferSupply`, the click handler, which this task did not play). The staged-neutral dialog showed `Buy supplies` enabled with
army 0's purse and supplies as the fixture held them `[confirmed]`.

**What the button does in each case** — `TAFSupply_CityOrFleet` @ `0043efac` (42337-42564) toggles **Visible**, not Enabled
(`FUN_00412c08` posts `CM_VISIBLECHANGED`, message 0xB00B; the M04-era note "the buy controls are disabled" is wrong) `[derived]`,
and every row below is `[confirmed]` from the live control list (`win_state` enumerates a control only when it has a window: a
VCL control hidden before it is ever shown has no HWND):

| case | dialog | `Buy supplies` | controls seen | play |
|---|---|---|---|---|
| own city (Arretium) | opens 470x335 | **absent** (hidden) | OK + 4 updowns + the provider listbox (itself invisible) | `CG_U1_b6` (b3/b5 runs read the same list) |
| hostile foreign city (Felsina, relation 3) | **does not open at all** | — | no window ≥200px named `Supply army` within 10 s | `CG_U2_b4` |
| foreign non-hostile city — **STAGED** | opens 470x335 | **present, enabled, visible** at screen (343,185) 100x26 — the resource's declared rectangle | OK + Buy supplies + 2 buy updowns + listbox | `CG_U2B_b6` |

The staged row is `STAGED-felsina-neutral-0721.SAV`: a copy of `saves/siege-felsina-failed-0721.SAV` whose ONLY edit is
Rome↔Gaul relations 3→0 (both directions, nation-record offset +0x26; the change and its assert are in
`STAGED-felsina-neutral.txt`, the staging script `stage_neutral.py` is tracked). No repo fixture has a Roman army next to a
non-hostile foreign city (near army 0 only Gaul's Felsina and Modena stand, and Rome starts at war with Gaul), which is why the
case is staged rather than played. In the own-city and staged-neutral dialogs alike the free-supply/buy control groups swap as
the code says (own: the four supply updowns; staged-neutral: the two buy updowns + Buy supplies).

### 5. Window positions kept in the save (M05)

`TPremierForm_StoreFormPositions` @ `0045bb1c` (58796-59007) writes, into the **current nation's** record, the four shorts of each
secondary window, in memory order **Left, Top, Height, Width** — Area map L+0x46E T+0x470 **H+0x472 W+0x474**; Unit map
L+0x476 T+0x478 **H+0x47A W+0x47C**; Information L+0x47E T+0x480 **H+0x482 W+0x484** `[derived]`. The assignment is read from the
write pairing, not guessed: `DAT_0045e718[9]/[10]` (the form's Left/Top) go to +0x46E/+0x470, `FUN_00412880(form)` to +0x474 and
`FUN_004128c4(form)` to +0x472 — and `FUN_00412880` returns the RECT's **Right** of the form's client area (**client Width**:
it calls the form's virtual at VMT+0x2C, a `GetClientRect`-style fill, and reads the word at offset 8), `FUN_004128c4` the
**Bottom** (**client Height**, offset 12) `[derived]`. The recorded words decide the order beyond dispute: `CG_T4_b1c`'s save
holds `[42, 104, 170, 320]` consecutively from +0x46E — a client 170 high and 320 wide under an X window of 328x196
(~26 px Wine title bar) — so +0x472 is Height and +0x474 Width `[confirmed]`. The main window's four shorts do not go there: the
save tail carries them as L, T, H, W at +0, +2, +4, +6 (`FUN_004484d0` @ `004484d0`, 47516-47522: the main form's [9]/[10], then
`FUN_00412880` at +6 and `FUN_004128c4` at +4) `[derived]`. The function runs from `TPremierForm_SaveGameFile` (58108),
`SaveGameFileAs` (58127) and `CloseAllForms` (58786) `[derived]`.

Played `[confirmed]` (`CG_T4_b1c`): the Area map moved by (40,30) (`xdotool windowmove`, verified by the X geometry), End turn,
autosave `CG_T4_b1c_AUTO0721.SAV` — its nation-0 Area-map words read `[42, 104, 170, 320]` (L, T, H, W: the **client** size; the X
window measures 328x196 with the ~26 px Wine title bar), and the main-window tail words `[-4, -4, 281, 650]` (client 650x281);
after a restart and reload of that save the Area map is back at (42,104) with the same X geometry. The clone (one window) needs
nothing but its own title; for the record, a save restores per-nation geometry and the tail's main-window rect.

## Method

- **Code.** All reads from `/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt` with the line cited; the tracked
  extract `code_extract_cosmetic.v3.txt` (written by `make_extract.py`, which had an enclosing-function lookup bug fixed before
  v3) holds the functions and every `MakeSound`/`SetTurnTitle`/`StoreFormPositions` call with three lines of context. The form
  resource is `dfm_TAFSupply.v2.txt` (`dump_dfm_supply.py`; v1 in the same dir has a garbled root header from a parser off-by-one
  and is superseded — its children, which parsed correctly, are identical).
- **Play.** `runs/experiments/cosmetic_gaps/` (`run_play.py BATCH ID...`), on the leaders-form runner's verified helpers: tooltip-
  proved toolbar clicks, `win_state` control lines, the driver's tile targeting, the X window name for the title. Own display
  (:744) and game folder (`~/ic2-work-cosmetic`), build `Imperial Conquest 2 fast rollingsave seed.exe`, fixtures from `saves/`.
  Batches: b1 (T1-T4), b2 (S1-S3; S3 crashed on a runner import bug, re-run in b3), b3 (S3, S4, U1, U2 — the U plays hit two
  runner bugs: the tooltip window hijacked the dialog search, and the close step polled 1 s short of the form's ~4 s release),
  b5/b6 (U1, U2B with the fixes; b5's evidence is complete but both plays are marked FAILED because the close gave up early —
  `probe_close_b5.txt` measured the release), and **b7** (S1, S2, S3, S4, T2 re-run under the review-hardened runner: every
  click of a recording carries its target proof — the tooltip for toolbar buttons, the driver's view geometry for tile clicks,
  the control's verbatim `win_state` line for dialog buttons — and every cited event keeps its post-event autosave, harvested
  and hashed; the sound rows cite b7). The close probes: `probe_close_b5.txt` (raw xdotool, superseded) and `CG_CLOSE_PROBE2`
  (verified clicks, `probe_close2.txt`). Sound plays run under `strace -f -e trace=openat,open` (`IC2_STRACE`); the WAV opens
  are harvested per step mark into `wav_opens_CG_<play>_<batch>.txt`.
- **Staging.** One staged save, described in §4.
- **Audit.** `claims_audit.py` (`claims_audit_cosmetic.v6.txt`: **277 checks, 0 mismatches**) re-reads every claim from its
  source — the v4 code extract (the CALLSITES table, the function bodies, the offsets as the dump spells them, the DFM), the
  recordings (every cited tag must exist; every click's pointer read back; every sound row's case, WAV name and cited play bound together), the WAV harvests, the SAV decoded from its hashed file, the artifacts' hashes — and binds
  the finding's *own* quoted values (the title strings, the toggle triple, the caption, the SAV words, the cited tags) to them;
  its bent-claim tests (`test_claims_audit.py`: one bent claim at a time — a caption byte, a case line, a play tag, a toggle value, an offset, a
  title spacing, a swapped offset pair, a wrong-but-existing tag — each must produce mismatches) and the runner tests (`test_runner.py`, 6 tests OK:
  unique tags, pointer read-backs on every click of every recording, verified steps, hashed screenshots, harvests) are tracked
  with their outputs (`test_claims_audit_out.txt`, `test_runner_out.txt`).

## What this does not establish

- Sound cases 3, 4, 5, 6, 7 and 10 are `[derived]` only: no play in this task provoked a battle ranged attack, a battle melee, a
  city assault either way, or a nation's elimination (they belong to the battle/siege experiments' territory).
- Whether anything is *audible* with a real sound device: no device on this rig; the evidence is the WAV file open, which happens
  regardless. Which backend `PlaySoundA` uses when it does play is not examined.
- The local-seat byte at `DAT_00474b00 + n*0x494` is inferred from the two guards that read it (moves play for it, distant
  battles play without it); no writer of the byte was located.
- The non-hostile-city dialog row rests on the STAGED save; a naturally-occurring neutral neighbour was not played.
- The 0x474b00/0x474696 relation tables are cited as the decompile addresses them; the save-file layout (`state/sav.py`, record
  +0x26) is a different, serialized arrangement — the two were cross-checked only through the staged save taking effect in play.
- Which of the two area-map render modes the inventory's "mono" and "terrain" names refer to is not established (two distinct
  renders and the selecting byte are); the `Buy supplies` **click** path (`TransferSupply`) was not played, so whether it refuses
  on insufficient money is not established; no audio device exists on the rig, so nothing is claimed about audible playback.
- The battle-screen sound sites (cases 3, 4, 5 and the battle-map case-1 sites) were not provoked by plays; their event names
  come from the enclosing functions' own code (highlight, counter decrement, the melee matrix), not from a recording.
