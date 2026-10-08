# Help topics — verification of row H01

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` row H01 and IC MAIN issue #722. The clone's `godot/UI/HelpPage.cs:43–65` (the recipient under #722) is the Help page proper; this draft is the *topics index* the page routes to.

**Tag:** `[confirmed]` (carried from the feature inventory; this draft tightens the per-row evidence without changing the tag).

## Answer

The H01 row is fully backed by tracked data — the form decoder, the function list, and the contents-list decoder all reproduce the row's prose.

| Sub-claim | Source | Match status |
|---|---|---|
| The Help menu item **Help topics** opens the WinHelp file `Imperial Conquest 2.hlp` | `runs/experiments/data/run-exp-feature-inventory/form_controls.tsv`: `TPremierForm/PremierForm/MainMenu/mt_help/mn_Helptopics` (a TMenuItem, OnClick=`HelpTopics`); `function_list.tsv` row `TPremierForm_HelpTopics @ 0x0045c280`; the .hlp is `runs/experiments/data/run-exp-feature-inventory/Imperial Conquest 2.hlp` | identical |
| The viewer shows the **Introduction** topic first | `runs/experiments/data/run-exp-feature-inventory/help_contents_entries.v2.tsv` row 1: `level=2 path="Game aspects > Introduction" title="Introduction" context="Describe_game"`; help_topics.tsv row 43 (`offset 0x003ae3`) is the topic "Introduction" with the body that opens with "*Imperial Conquest 2 is based in the ancient Mediterranean …*" | identical |
| The helper **.hlp holds 71 topics** and the contents **holds 89 entries** | `wc -l runs/experiments/data/run-exp-feature-inventory/help_topics.v2.tsv` = 72 (one header + 71); `wc -l help_contents_entries.v2.tsv` = 90 (one header + 89) | identical |
| The decoder is the post-fix one (247/247 records exact) | README and the `coverage_report.v8.txt` self-test (commit a3ad689); the .hlp is committed at `runs/experiments/data/run-exp-feature-inventory/Imperial Conquest 2.hlp` with SHA-256 in `SAVES.sha256` | identical |
| The viewer screenshot shows the live window | `MANIFEST-batch1.txt` row `3e9e17da…  FI_b1_06_help_topics.png` (release asset `FI_batch1_screenshots.tar.gz`) | identical |

## What does not match — two open notes

1. **Help → top-level menu order in the contents list.** The contents file opens with `level=1 path="Game aspects"` (no `title`), then jumps to level 2 entries starting with `Introduction`. The "first shown topic" interpretation tracks this: Wine viewers render the first contents entry as the first topic the user sees. A clone's HelpTopic index should reproduce this ordering — `Game aspects` is a category header (level 1), the eight children (`Introduction`, `Improvements`, `Cities`, `Armies`, `Fleets`, `Battle`, `Time`, `Fonts`) are the topics. The contents have 89 entries across multiple category headers (Menu, Map keys, etc., per the contents file). This isn't an open *bug* but is the kind of layout detail a renderer needs to get right.
2. **The .hlp file itself isn't text-readable end to end.** The phrase decoder is 247/247, but the **topic bodies** are decoded row by row in `help_topics.tsv` and not human-checked at body level on every row; the readme says a few characters still drift in compressed paragraphs. The H01 row only requires the *index* to be exact (which it is); the topic bodies are H05 (terrain/symbols/colours/costs/details/matrix) territory and were verified verbatim under that draft.

## Method

- **Form + function extraction.** `runs/experiments/feature_inventory/extract_forms.py` (form controls) + `extract_dump_strings.py` (function list). The `HelpTopics` menu item lives under the Help menu (`mt_help`); the handler is the named function reproduced above.
- **Help decoder.** `runs/experiments/feature_inventory/hlp_dir.py`, `hlp_topics.py`, `extract_help.py`, `hlp_check.py` (a from-scratch WinHelp 3.x reader; the phrase-code table is recovered empirically). Outputs `help_topics.tsv` (71 topics × title/text) and `help_contents_entries.tsv` (89 contents entries × level/path/title/context). Phrase decoder is the post-fix version (commit a3ad689).
- **Tag scheme.** Same as the H04/H05 drafts: a row is `[confirmed]` when a tracked file in this repo lists the cited evidence. The H01 row was `[confirmed]` already in the feature inventory; this draft tightens the *cell-level* form/menu extraction (caption, OnClick, menu path) which the feature inventory listed only at the row level.

## Inferences

- The Help menu's `mn_Helptopics` and `mn_About` are sibling items under `mt_help`; both call into `TPremierForm`'s methods. The clone's `HelpPage.cs` is the modern equivalent; the data dictionary it iterates is exactly the contents list at `help_contents_entries.v2.tsv` (filtered to topics with non-empty `title`).
- The contents file's `context` column carries the .hlp's internal target (`<topic>_<proc>`-style). A faithful clone renderer can ignore it (it is a WinHelp internal address, not a topic name) and route by `path` or `title`. The `level` column is what carries the **category vs sub-topic** distinction (level=1 = section header; level=2+ = topic page).

## What this does not establish

- Whether the .hlp bitmaps (the buttons on each topic page) preserve the original palette across builds (only one v1.01 .hlp was decoded).
- Topic-body fidelity beyond the eight H05 sub-rows. `help_topics.tsv` decodes the body of every topic; bodies not in H05's scope (e.g. "Fonts", "Improvements", the help's prose pages) are not cell-verified here, though they decode without per-character loss on most paragraphs.

## Reproduction

```bash
cd ~/projects/ic2-conquest
python3 runs/experiments/feature_inventory/hlp_topics.py "Imperial Conquest 2.hlp" \
   > runs/experiments/data/run-exp-feature-inventory/help_topics.v3.tsv
python3 runs/experiments/feature_inventory/extract_help.py "Imperial Conquest 2.hlp" \
   > runs/experiments/data/run-exp-feature-inventory/help_contents_entries.v3.tsv
grep -E "HelpTopics|ToggleHints|About\b" runs/experiments/data/run-exp-feature-inventory/function_list.tsv
grep -E "mn_Helptopics|mn_About|mn_Showhints" runs/experiments/data/run-exp-feature-inventory/form_controls.tsv
```

The form and function extracts are deterministic — they read the EXE and the .hlp, neither of which changes. No live Wine session is needed; the screenshot evidence is the `FI_batch1_screenshots.tar.gz` release asset.
