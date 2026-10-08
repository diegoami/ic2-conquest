# Cellular Automata (hidden easter-egg) — verification of row H04

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` row H04 and IC MAIN's clone-side issue #722 (the second question on #722, "the About box's hidden Cellular Automata window is absent"). The clone's `godot/UI/AboutDialog.cs:43–52` is the recipient of the reproduction decision; this draft is the data side and the open items.

**Tag policy:** same as `2026-10-05-player-facing-feature-inventory.md`. The row is `[confirmed]` for the original because the help-Wine screenshot shows the live window and the form extraction matches; the clone-side decision (reproduce or skip) is the issue's question and is not data.

## Answer

The H04 row is fully explainable from this repo's tracked forms and function-list extracts plus the two screenshots. Every byte the original draws is named in tracked files; nothing here would prevent a faithful reproduction if the owner chooses to render it.

| Sub-claim | Source | Match status |
|---|---|---|
| The About box's button reads **"CAncell"** (deliberate misspelling) | `runs/experiments/data/run-exp-feature-inventory/form_controls.tsv` row `TAboutIC/AboutIC/btn_cancell` — `name=btn_cancell`, `caption=CAncell`, `OnClick=Cancell` | identical |
| Clicking that button creates the **Cellular Automata** window | `function_list.tsv` row `TAboutIC_Cancell @ 0x00456ca0` (which the decompile shows constructs `TCellAuto`); form `TCellAuto` `caption=Cellular Automata`, `OnCreate=InitializeForm` | identical |
| The window has buttons **N (New structure)**, a **save icon (Save structure as .BMP)** and **X (Close)** | `form_controls.tsv` rows under `TCellAuto/CellAuto/Panel1/`: `sb_next` (caption `N`, hint `New structure`, OnClick=`TCellAuto_NewPattern`); `sb_Save` (no caption, hint `Save structure as .BMP`, OnClick=`TCellAuto_SaveBMP`); `sb_OK` (caption `X`, hint `Close Cellular Automata`, OnClick=`TCellAuto_OK`) | identical (every caption, hint and handler matches the row's prose) |
| The handler chain | `function_list.tsv`: `TCellAuto_InitializeForm @ 0x00456668`, `TCellAuto_NewPattern @ 0x00456744`, `TCellAuto_SaveBMP @ 0x004569c0`, `TCellAuto_OK @ 0x00456a70`, `TAboutIC_Cancell @ 0x00456ca0` | identical |
| The window actually shows a pattern after N | Wine screenshot `FI_b1_05_cellauto_N.png` (released under `run-exp-feature-inventory` as `FI_batch1_screenshots.tar.gz`, hashed in `SAVES.sha256`); explore script `runs/experiments/feature_inventory/explore_b1_ca.py` clicks (509, 341) — the N button — and takes the screenshot. | identical |
| The X button closes the window | `explore_b1_ca.py` clicks (776, 341) — the X button — and snapshots `Cellular Automata` no longer in the window list; `explore_b1_ca2.py` repeats this three times, then closes the About box. | identical |
| The non-gameplay call | Clone's `imperial_conquest_2/docs/design-audit.md` line 19: "*Two whole classes turned out to be non-gameplay (`TCellAuto` is a cellular-automaton toy with a `SaveBMP` button …); `TBattleDelays` is a settings dialog for the tactical pacing pauses …)*" | identical |

## What does not match — three open items

1. **The CA rule set itself is not decoded.** The form has an `Image1` (the canvas) and a `Panel1` with the three buttons. The simulation's *content* is computed by `TCellAuto_InitializeForm` and `TCellAuto_NewPattern`, both at decompile addresses but neither rule listed in tracked data. A faithful reproduction needs the rule (Conway Game-of-Life? a Wolfram 1D rule? an L-system?). The clone can render the *form* from the controls above; the *content* of the canvas is the open piece.
2. **The SaveBMP format is unspecified.** `TCellAuto_SaveBMP @ 0x004569c0` writes a `*.BMP` file. The size of the bitmap (the Image1 width × height), the palette (16-colour VGA? 256-colour?), and the cell-to-pixel mapping are not in this repo's tracked data; a faithful clone would need to read `SaveBMP` byte-exact or pick a simple default (e.g. 1 bit per cell, 1 byte per pixel = `BMP` mode).
3. **The About-box layout has two buttons (`OK` and `CAncell`); the clone's `godot/UI/AboutDialog.cs:43–52` has only `OK`.** The reproduction question is whether the second button should exist at all. If yes: the misspelling must be **preserved** (`CAncell`, capital A, capital C, lowercase rest) to keep the easter-egg discoverable; if no: omit the control, leaving the OK-only dialogue as the clone's current shape.

## Method

- **Form extraction.** `runs/experiments/feature_inventory/extract_forms.py` parses every `TPF0` resource of `Imperial Conquest 2.exe`; outputs `runs/experiments/data/run-exp-feature-inventory/forms.json` (29 forms) and `form_controls.tsv` (908 controls, with caption / hint / event handler / Delphi `ShortCut` columns). The two relevant form rows here — `TCellAuto` with five controls and `TAboutIC` with nine — are reproduced verbatim from `form_controls.tsv`.
- **Function symbols.** `runs/experiments/feature_inventory/extract_dump_strings.py` and the EXE's Delphi RTTI produce `function_list.tsv` (with `addr`, `name`, `symbol`, `dump_line` columns) and `dump_string_literals.tsv`. The five function rows cited are reproduced verbatim.
- **Screenshots.** `runs/experiments/feature_inventory/explore_b1_ca.py` (N button at (509, 341), shot `FI_b1_05_cellauto_N.png`; X button at (776, 341)) and `explore_b1_ca2.py` (close + close About box). Pixel positions are the original's; a clone reproducing the form should preserve them so the same screenshots can be regenerated as regression tests.
- **Non-gameplay call.** `imperial_conquest_2/docs/design-audit.md` ("Two whole classes turned out to be non-gameplay (`TCellAuto` is a cellular-automaton toy with a `SaveBMP` button …)"). That doc is **on the clone repo**, not here; reading it is allowed by rule 2 but writing to it isn't.
- **Tag scheme.** Same as the H05 draft: a row is `[confirmed]` when the cited evidence is a tracked file in this repo, `[derived]` when only a function name or address is given. The H04 row in `2026-10-05-player-facing-feature-inventory.md` is `[confirmed]` already; this draft tightens the *cell-level* form extraction (caption, hint, OnClick) which the feature inventory listed only at the row level.

## Inferences

- The misspelling `CAncell` is the **only** observable trigger for the easter egg. A reproduction that spells it correctly (`Cancel`) would lose the discoverability — the player must see the error to want to click. **If reproducing, keep the spelling as in the original.**
- The form's three controls are all *speed buttons* (`TSpeedButton`) inside a `TPanel`, not toolbar buttons; that matches the visual style in the Wine screenshot. A clone implementation may need to add a `TSpeedButton` analogue if not already in the UI kit (Godot's `TextureButton` or a similar clickable bitmap is the natural fit).
- `TCellAuto_OK @ 0x00456a70` is **named `OK`** but does **not** draw an OK tick — it draws `X` and closes the window. This is a Delphi naming habit (all panel sub-OKs were conventionally called `sb_OK` regardless of glyph) and not a bug. A faithful clone should keep the function name `OK` for parity but render the X glyph.

## What this does not establish

- The CA simulation rule (`TCellAuto_InitializeForm`, `TCellAuto_NewPattern`) — see open item 1.
- The `SaveBMP` file format (palette, dimensions, alignment) — see open item 2.
- Whether the easter egg runs *outside* the live game (`TCellAuto_*` only fires when `TAboutIC_Cancell` is clicked — there is no menu, shortcut or other entry point).
- Whether `TCellAuto` references any nation / city / unit data. (`dump_string_literals.tsv` listed no such literals in the function bodies, suggesting the CA's state is self-contained; not decompiled here.)

## Reproduction

```bash
cd ~/projects/ic2-conquest
python3 -m state.sav --help                                    # not for H04; sanity only
python3 runs/experiments/feature_inventory/extract_forms.py    # regenerate form_controls.tsv
grep -E "TAboutIC|TCellAuto" runs/experiments/data/run-exp-feature-inventory/form_controls.tsv
grep -E "TAboutIC_Cancell|TCellAuto_" runs/experiments/data/run-exp-feature-inventory/function_list.tsv
```

The form and function extracts are deterministic — they read the EXE and DAT, neither of which changes. No live Wine session is needed for verification; the explore scripts in batch 1 of `run-exp-feature-inventory` (release asset `FI_batch1_screenshots.tar.gz`) hold the live screenshots.
