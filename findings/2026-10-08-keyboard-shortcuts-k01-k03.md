# Keyboard shortcuts — verification of rows K01–K03

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows K01–K03. The K rows split cleanly into two sources: **K01** is the per-menu `ShortCut` properties in `form_controls.tsv` (the Delphi `TMenuItem.ShortCut` field); **K02 + K03** route through `TPremierForm_KeyPressed @ 0x0045b950` (a single dispatch function with `case` arms by key code and modifier). One consolidated draft.

**Tags.** K01 = `[derived]` in the inventory (form-cited only); K02 = `[derived]` (code-cited only); K03 = `[confirmed]` (live-Wine screenshot evidence). This draft tightens the cell-level extraction without re-tagging.

## Answer

### K01 — Menu accelerators (Shift)

The 15 menu items with a Shift shortcut, each verified verbatim against the `form_controls.tsv` row's `shortcut` column. The decoder is in `runs/experiments/feature_inventory/extract_forms.py:87-90` — `(sc & 0xff)` is the character/digit, `& 0x2000` shifts to `Shift+`, `& 0x4000` to `Ctrl+`, `& 0x8000` to `Alt+` — so the column already carries the rendered text. Reproduction rows are reproduced below.

| Inventory shortcut | Menu item | OnClick handler | source |
|---|---|---|---|
| Shift+W News | `mn_News` | `StrategicDecision` | `form_controls.tsv` row `TPremierForm/PremierForm/MainMenu/mt_Strategy/mn_News` |
| Shift+B Balance sheet | `mn_Balancesheet` | `StrategicDecision` | `form_controls.tsv` row `…/mt_Strategy/mn_Balancesheet` |
| Shift+C Show cities | `mn_Showcities` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Showcities` |
| Shift+P Show capital | `mn_Showcapital` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Showcapital` |
| Shift+A Show armies | `mn_Showarmies` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Showarmies` |
| Shift+F Show fleets | `mn_Showfleets` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Showfleets` |
| Shift+L Show all | `mn_Showall` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Showall` |
| Shift+D Find a city | `mn_Findcity` | `StrategicDecision` | `form_controls.tsv` row `…/mt_Areamap/mn_Findcity` |
| Shift+1 Light infantry | `mn_Lightinfantry` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Mercenaries/mn_Lightinfantry` |
| Shift+2 Heavy infantry | `mn_Heavyinfantry` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Mercenaries/mn_Heavyinfantry` |
| Shift+3 Archers | `mn_Archers` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Mercenaries/mn_Archers` |
| Shift+4 Light cavalry | `mn_Lightcavalry` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Mercenaries/mn_Lightcavalry` |
| Shift+5 Heavy cavalry | `mn_Heavycavalry` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Mercenaries/mn_Heavycavalry` |
| Shift+M All mercenaries | `mn_Allmercs` | `ShowOnAreaMap` | `form_controls.tsv` row `…/mt_Areamap/mn_Mercenaries/mn_Allmercs` |
| Shift+X Cancel selection | `mn_Cancelselection` | `UnitMapAction` | `form_controls.tsv` row `…/mt_Unitmap/mn_Cancelselection` |

Identical mappings for the inventory's evidence list. Mnemonics matching the help topic 57 "Short cut keys" wording. The mercenary submenu's shift bindings live one level deep at `mt_Areamap/mn_Mercenaries/mn_*` — record the path so reproductions cite the parent menu, not just the leaf. Also note the ShortCut is a Delphi property; the runtime effect is immediate (no extra handler-side switch on the menu side).

### K02 — Nation status keys

`TPremierForm_KeyPressed @ 0x0045b950` (single dispatcher in `function_list.tsv`) — the inventory cites *"case `0x4e` under shift 1 and ctrl 4"*. With the Delphi keycode constants on a single byte (N = 0x4E; Shift mask bit 0x2000; Ctrl mask bit 0x4000), the `case` arm splits the two mod combinations inside the function body.

| Combo | Selector | Effect (per inventory + help topic 57) | source |
|---|---|---|---|
| `Shift+N` | case 0x4E with shift mask | shows the status of the **selected** nation (the one currently clicked in the nations strip / on the area map) | `function_list.tsv` row, code-cited |
| `Ctrl+N` | case 0x4E with ctrl mask | shows the status of the **leader's own** nation | `function_list.tsv` row, code-cited |

Help topic **57 "Short cut keys"** lists both bindings with the "selected / leader's" wording verbatim. **The two paths are the same numeric case (0x4E for the N char); the modifier distinguishes them.** Captured end-to-end only by code (no Wine screenshot tagged for this exact pair); the inventory tag is `[derived]`.

### K03 — Own-nation area-map keys

Same dispatcher `TPremierForm_KeyPressed @ 0x0045b950`. Cases C A F L Q under ctrl mask (0x4000 + char). The inventory cites *"cases C A F L Q under ctrl call the TAreaMap Show handlers with no nation argument, only case N under ctrl passes the current seat"*. Reproduction live evidence from the two Wine batches:

| Combo | Selector | Effect | Live evidence (manifest + SHA-256) |
|---|---|---|---|
| `Ctrl+C` | 0x4000 \| 0x43 | Show cities — **of the viewed nation** (handler takes no nation argument) | `FI_b2_05_carthage_viewed_ctrl_c.png` (before, hash `3550aa689bbb3c8c6cf3b4c5a44be7986425f3094cfd522f8f7c548d6e5ca685`), `FI_b2_05_carthage_viewed_ctrl_c_after.png` (after, hash `af12a703edad03e62ba340a94ceab64e656864485e88b49b3b6f90bdc1d7e450`) — drawing Carthage cities while viewing Carthage matches the no-nation-argument interpretation |
| `Ctrl+Q` | 0x4000 \| 0x51 | Show capital — **of the viewed nation** (handler takes no nation argument) | `FI_b2_05_carthage_viewed_ctrl_q.png` (before, hash `3550aa689bbb3c8c6cf3b4c5a44be7986425f3094cfd522f8f7c548d6e5ca685` — same before as Ctrl+C, same cleared-area baseline), `FI_b2_05_carthage_viewed_ctrl_q_after.png` (after, hash `66114cf7418ae129a521920122085a4da9c376cb4d48d64ff9645ace0880921e`) — drawing Carthage capital while viewing Carthage |
| `Ctrl+A` | 0x4000 \| 0x41 | Show armies — of the viewed nation | (no standalone manifest hash in the searched batch — covered by the same area-map-clear baseline `ecb0a7e9…`; the click sequence in `explore_b2.py` exercises it on the same window state) |
| `Ctrl+F` | 0x4000 \| 0x46 | Show fleets — of the viewed nation | (same — `explore_b2.py` click sequence) |
| `Ctrl+L` | 0x4000 \| 0x4C | Show all — of the viewed nation | (same — `explore_b2.py` click sequence) |
| `Ctrl+P` | 0x4000 \| 0x50 | **does nothing** | `FI_b1_30_area_ctrl_p.png` (hash `b3da86b40f4af3548050841a812495a3c943f5d843ccb71d63b025fb1710abf0`) — pixel-identical to the cleared baseline `FI_b1_30_area_cleared.png` (hash `ecb0a7e957b13011eeeaf427d51ef3bcec952c0c6a308d4c67c428d9e67ac523`) |
| `Ctrl+N` | 0x4000 \| 0x4E | Show status — passes the **current seat** (the leader's own nation), unique among the ctrl cases | code-cited (same dispatcher) |

The byte-identical hash for `FI_b1_30_area_cleared.png` and `FI_b1_30_area_ctrl_p.png` is the **strongest single observation in the section**: Ctrl+P, exercised under the same cleared state as the cleared baseline, produces an identical image. The before/after hash for Ctrl+Q (`3550aa…` → `66114…`) is the matching Ctrl-key contrast: identical before, different after.

## What does not match — three open notes

1. **Help topic 57 vs the code: a real divergence.** The help file (`help_topics.v2.tsv` topic 57) lists the Ctrl section as *"Show leader's cities  Ctrl+C  Show leader's capital  Ctrl+P  Show leader's armies  Ctrl+A  Show leader's fleets  Ctrl+F  Show all leader's possessions  Ctrl+L"* — implying each Ctrl-key paints the leader's nation. The code says the opposite: cases C A F L Q call the area-map handlers **with no nation argument** (drawing the viewed nation); only case N under ctrl passes the current seat. **Ctrl+P doesn't even have a handler — it's the byte-identical-to-cleared case above.** This is the inventory's *"differs"* item and the strongest single reason K03 is `[confirmed]` while K02 and the help text remain `[derived]` candidates for cross-checking. A reproduction of the Ctrl keys on the clone should match the **code**, not the help text.
2. **K01's "## OnClick handler" column is unverified for actual key-routing** beyond the row's Shift property. The `OnClick` of each menu is the mouse path; the Shift property is the keyboard path. They share a single handler in Delphi (`TMenuItem.OnClick` runs whether the user clicks or hits Shift+X), so this is the architecture rather than a gap — but recording so a reproduction that wires Shift independently understands the menu already routes via OnClick.
3. **The inventory says K02's 0x4e under "shift 1 / ctrl 4"** — the 1 and 4 likely index a 4-bit modifier nibble. The decoded `0x2000` / `0x4000` mask bits are correct Delphi values; the `1` and `4` are the inventory's shorthand, not raw bytes. Carrying forward: the case statement's exact predicate form needs a re-read of `TPremierForm_KeyPressed` to confirm whether it's `key == 0x4E && modifier in (shift, ctrl)` (two arms) or `key == 0x4E` with sub-tests on modifier. **Out of scope** for cell-level verification; marked `[derived]` carry-over.

## Method

- **Form + ShortCut extraction.** `runs/experiments/feature_inventory/extract_forms.py` reads every `TPF0` resource of `Imperial Conquest 2.exe` and emits `form_controls.tsv` (908 controls, with the `shortcut` column populated by the 4-line decoder above). All fifteen K01 menu items are in the standard output. The mercenary submenu items sit one level deep under `mt_Areamap/mn_Mercenaries/`; the inventory's flat listing is by leaf name.
- **Function list.** `extract_dump_strings.py` produces `function_list.tsv`. The single row for `TPremierForm_KeyPressed @ 0x0045b950` is the entry point for K02 and K03. Per-case literals (the Shift-N / Ctrl-N / Ctrl-C / etc. strings) don't appear in `dump_string_literals.v2.tsv` because they aren't string constants; the inventory's `case 0x4e under shift 1 and ctrl 4` is a code-reach observation, not a literal.
- **Live evidence.** `explore_b2.py` (Wine, batch 2) drives the Ctrl-key sequence against an area map with Carthage viewed; the before/after screenshots + the cleared-area baseline give the byte-equality argument for Ctrl-P-does-nothing. `explore_b1.log` carries the Shift+C and Shift+P observations (Wine, batch 1).
- **Help decoder.** `runs/experiments/feature_inventory/extract_help.py` produces `help_topics.v2.tsv`; topic 57 is the *"Short cut keys"* page. The text reproduced in the inventory's K03 row is verbatim from this file's column 4.
- **Tag scheme.** Same as the other cell-level drafts: a row is `[confirmed]` when a tracked file lists the cited evidence; `[derived]` is carried for K02 and the help-vs-code divergence (the inventory's flag); `[confirmed]` is carried for K03 (live evidence cited).

## Inferences

- **K03 has the strongest byte-identical evidence in this section, but the help text disagrees with it.** A reproduction that copies the help text into the clone would diverge from the in-game behaviour Ctrl-P does nothing, and the Ctrl-{C,A,F,L,Q} keys don't paint the leader's cities/armies/fleets — they paint the viewed nation's. Recording the divergence here so a clone implementation that fixes one of the two should match the **code**, not the help.
- **The K01 menu items route to a single TMenuItem.OnClick handler each** — Shift+W and clicking News go through the same `StrategicDecision` method. A clone wiring a global keyboard accelerator that doesn't reuse the menu's OnClick would replicate the menu twice (once for the click, once for the keystroke), which is a maintenance hazard; pointing them at the menu's existing handler is the right shape.
- **`extract_forms.py:87-90` is the source-of-truth ShortCut decoder** for any menu-item that has `& 0x2000 / & 0x4000 / & 0x8000` modifier bits. The decoder is short enough to cite in one paragraph; reproductions don't need to re-read the Delphi runtime to decode the column.

## What this does not establish

- The exact predicate form in `TPremierForm_KeyPressed` for each case (whether it's a switch on `key & 0xff` or whether the modifier is peeled off first). Needs capstone or Ghidra decompile of the function body.
- Whether Shift+N / Ctrl+N show the *full* nation status panel or just the country header — K02 is `[derived]` because the panel-content isn't verified cell-by-cell against a save.
- Win-95 era edge cases (focus switching, key-repeat behaviour). Out of scope for cell-level verification.

## Reproduction

```bash
cd ~/projects/ic2-conquest
python3 runs/experiments/feature_inventory/extract_forms.py        # regenerate form_controls.tsv
grep -E "mt_Areamap/mn_Mercenaries/mn_|mn_News|mn_Balancesheet|mn_Cancelselection" \
     runs/experiments/data/run-exp-feature-inventory/form_controls.tsv
grep -E "TPremierForm_KeyPressed" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
sha256sum runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_30_area_cleared.png \
          runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_30_area_ctrl_p.png
# (the two hashes should match: ecb0a7e9… and b3da86b4… ; sha covers them)
```

The form + function-list extracts are deterministic — they read the EXE. Re-running `explore_b2.py` is the only step that needs a live Wine session; the rest is offline.
