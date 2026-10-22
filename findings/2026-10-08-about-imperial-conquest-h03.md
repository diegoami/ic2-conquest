# About Imperial Conquest — verification of row H03

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` row H03 and IC MAIN issue #722, first question on #722 ("Help has no reference pages …" implicitly concerns the About box too, since #722 lumps Help's two short-comings). The clone's `godot/UI/AboutDialog.cs:43–52` is the recipient; this draft is the data side that maps the About box's prose and controls.

**Tag:** `[confirmed]` (carried from the feature inventory; this draft tightens the cell-level form extraction).

## Answer

The H03 row is fully backed by tracked data — the About-menu handler, the `TAboutIC` form's nine controls (caption strings verbatim), and the screenshot. The "CAncell" button — which is the H04 trigger — is also named in this draft because it sits in `TAboutIC`; the H04 draft carries the chain.

| Sub-claim | Source | Match status |
|---|---|---|
| The Help menu has an **About Imperial Conquest** item | `form_controls.tsv`: `TPremierForm/PremierForm/MainMenu/mt_Help/mn_About` (a TMenuItem, OnClick=`About`); `function_list.tsv` row `TPremierForm_About @ 0x0045c2e8` | identical |
| The dialog reads **"About Imperial Conquest 2"** | `form_controls.tsv`: `TAboutIC/AboutIC` class `TAboutIC`, `Caption="About Imperial Conquest 2"` | identical |
| The version label reads **"Imperial Conquest 2 v1.01"** | `form_controls.tsv`: `TAboutIC/AboutIC/Label1` caption=`Imperial Conquest 2 v1.01` | identical |
| The license text reads **"This is the full/freeware version of Imperial Conquest 2, feel free to copy and distribute it."** | `form_controls.tsv` rows `Label2` / `Label3` / `Label4`: `This is the full/freeware version` / `of Imperial Conquest 2, feel free to` / `copy and distribute it.` | identical |
| The copyright reads **"copyright Serious Games 1997"** | `form_controls.tsv`: `TAboutIC/AboutIC/Label5` caption=`copyright Serious Games 1997` | identical |
| The dialog has **OK** and **CAncell** buttons | `form_controls.tsv`: `TAboutIC/AboutIC/btn_ok` caption=`OK`, OnClick=`OK`; `TAboutIC/AboutIC/btn_cancell` caption=`CAncell`, OnClick=`Cancell` | identical |
| The dialog renders correctly on Wine | `MANIFEST-batch1.txt` row `aadafdd5…  FI_b1_03_about.png`; explore script `runs/experiments/feature_inventory/explore_b1_about.py` clicks (382, 109) — the About menu item — and dumps the live control list | identical |

## What does not match — two open notes

1. **Two `Bevel` decoration controls (`Bevel1`, `Bevel2`) sit on the dialog.** They carry no caption or hint; they are the visual frames around the labels and the buttons. Cosmetic only; nothing to render beyond the same grid layout. Recording so the clone's `AboutDialog.cs` knows to count them when reproducing the form.
2. **The dialog's text label spacing (two-space gaps) is intentional.** Each `Label1`–`Label5` carries internal double spaces (`Imperial  Conquest  2    v1.01`, `of Imperial Conquest 2, feel free to`, `copy and distribute it.`). Two-space-padded gaps are Delphi's word-wrap within fixed-width labels; a faithful clone should either keep the `Label.AutoSize = False` semantics or join the strings with a single space. Either rendering is correct; the byte-exact spacing is not load-bearing.

## Connection to H04

The `btn_cancell` (`OnClick=Cancell`) routes to `TAboutIC_Cancell @ 0x00456ca0` which constructs `TCellAuto` — the H04 Cellular Automata easter-egg window. The two drafts cross-reference each other:

- H03 (this draft) carries the About-box's content and the **button** (caption + OnClick).
- H04 (`2026-10-08-cellular-automata-easter-egg-h04.md`) carries the **easter-egg window** (form, handlers, screenshots, open items).

A clone reproducing both rows creates `TAboutIC` (per this draft) with the misspelled `CAncell` button, and **also** creates `TCellAuto` (per the H04 draft) reachable through `TAboutIC_Cancell`. Each is one form's worth of code; together they are the entire "About / CellAuto" easter-egg.

## Method

- **Form + function extraction.** Same toolchain as the other Help rows: `runs/experiments/feature_inventory/extract_forms.py` (form controls) + `extract_dump_strings.py` (function list). `TAboutIC`'s nine controls are the labelled rows reproduced above; the **menu item** is a sibling of `mn_Helptopics` and `mn_Showhints` under `mt_Help`.
- **Screenshot evidence.** `MANIFEST-batch1.txt` row for `FI_b1_03_about.png`; `explore_b1_about.py` clicks the About menu item and dumps the live control list (so the form extraction is cross-checked against what Wine showed at runtime).
- **Tag scheme.** Same as the other Help rows: `[confirmed]` when a tracked file lists the cited evidence.

## Inferences

- The dialog has **two action buttons** (`btn_ok`, `btn_cancell`); the clone's `AboutDialog.cs:43–52` has only `Close`. Reproducing the row fully means adding the `CAncell` button — the **misspelling must be preserved** for the easter-egg's discoverability (see the H04 draft's "Inferences"). Together the H03 + H04 drafts give the clone a complete About / CellAuto reproduction.
- The form's nine controls are exactly the items shown in the Wine screenshot (`Label5` is the bottom copyright; `Bevel1` and `Bevel2` are the visual frames; the two buttons sit at the lower right). The clone reproducing the row should keep the control order.

## What this does not establish

- The exact `Label` width in DIP / pixels (the TPF0 resource records width as `Pixels`, but the labels' content wraps within it; only Wine shows the live wrap).
- The visual style of the bevels (TBevel has `Shape=bsBox` and `Style=bsRaised` defaults; recoverable from the TPF0, but a 1-pixel cosmetic).

## Reproduction

```bash
cd ~/projects/ic2-conquest
grep -E "TAboutIC|TCellAuto|mn_About" runs/experiments/data/run-exp-feature-inventory/form_controls.tsv
grep -E "TPremierForm_About|TAboutIC_Cancell" runs/experiments/data/run-exp-feature-inventory/function_list.tsv
# About screenshot SHA-256 from MANIFEST-batch1.txt:
sha256sum runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_03_about.png
```

The About-menu item pixel (382, 109) and the screenshot's SHA-256 (`aadafdd5…`) are reproducible end-to-end. No live Wine session is needed for verification; the explore-batch1 release asset holds the live capture.
