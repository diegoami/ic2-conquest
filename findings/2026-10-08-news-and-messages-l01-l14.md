# News and messages — verification of rows L01–L14

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows L01–L14. Fourteen rows covering the news-templates (L01–L08 + L07b), unit-order refusals (L09, L11), confirmations (L10), the End-turn warning set (L12), the information-panel text (L13 — overlapping with N03 + UM02–UM07, cited in those drafts), and the dialog labels and number formatting (L14). One consolidated draft.

**Tags.** Mixed: most rows = `[derived]` (literals never saved against a known-byte seed), L05 = `[confirmed]` (live save evidence), L13 = `[confirmed]` (live-screenshot evidence). Carried from inventory.

## Answer — per-row sources

**L01 — News log lines** | `[report] 40 slots of at most 60 characters; oldest at top; the display shows them in the Information window` | `R:news-log-format-and-messages.md Q1`; `SS:FI_b1_01_main.png` (the log on screen). `[confirmed]` carry-over (visible in the screenshot).

**L02 — Seeded history** | `[report] 27 of them (272 BC, 271 BC, then Week 1 Spring 270 BC)` | `R:news-log-format-and-messages.md 'The DAT seeds the log'`; `SS:FI_b1_01_main.png`. `[confirmed]` carry-over.

**L03 — War line** | `"A declares war on B."`; upper-cased when human involved; declaration adds cascade lines for the target's allies | `F:2026-10-03-fleet-peace-prompt.md` (`PTOLEMAIC DECLARES WAR ON CARTHAGE.` + `... ON NUMIDIA.`); `F:2026-10-02-unit-map-mouse-orders-and-tax-range.md (b) (ROME DECLARES WAR ON GREECE.; PP_yes_seed1.SAV)`; `X:FUN_00449a44`; `R:news-log-format-and-messages.md Q4 #2`. `[confirmed]`.

**L03b — Alliance line** | `"A forms an alliance with B."`; alliance also makes A declare war on each nation at war with B | `X:FUN_00449a44`; `R:news-log-format-and-messages.md Q4 #1` (4 events in the research saves, none in this repo). `[derived]`.

**L04 — Siege line** | `"N fails to capture C   (A)."` (three spaces before bracket) | `C:§1 'Attack a city (siege)' (T_ATTACK.SAV news tail 'Rome fails to capture Felsina   (Gaul).' in tests/results.md 'attack')`; `X:FUN_0044b27c`. `[confirmed]`.

**L04b — Capture / defection / capital lines** | `"C   (A)  falls to B."`, `"C defects from A to B."`, `"N have moved their capital to C."` | `X:FUN_0044b27c`, `FUN_0044bed8`, `FUN_0044bd2c`; `R:news-log-format-and-messages.md Q4 #5, #8, #9` (the capital line is code-only). `[derived]`.

**L05 — Battle lines** | `"A destroys army of B."` and `"A sinks fleet of B."` | `SS:FI_b1_01_main.png` (*"Seleucid destroys army of Ptolemaic."* after Week 1 — written by play, not seeded); `F:2026-10-04-battle-probe.md` (`NB_post_battle.SAV: "Gaul destroys army of Rome."`); `F:2026-10-03-fleet-peace-prompt.md` (*"Carthage sinks fleet of Ptolemaic."*); `X:TBattleOver_OK @ 0x00459220`, `FUN_0044aee4 @ 0x0044aee4`, `FUN_0044b5d0 @ 0x0044b5d0`. `[confirmed]`.

**L06 — Treaty block** | `"B sues A for peace and;"` + three indented lines (`ends all trading agreements`, `ends all alliances`, `pays reparations of N talents`) + `"A and B have agreed to end their war."` | `SS:FI_b1_01_main.png` (Ptolemaic sues Seleucid ... 2,242 talents); `X:FUN_00450c68 @ 0x00450c68`; `R:news-log-format-and-messages.md Q4 #14–#18`. `[confirmed]`.

**L07 — Fleet loss lines** | `"A fleet belonging to N is lost at sea."` and `"A fleet belonging to N is damaged in a storm."` | `F:2026-10-03-storms-and-losses-at-sea.md` (`NAT_seed1_13_0727_seat02.SAV: 'A fleet belonging to Ptolemaic is lost at sea.'`); `X:FUN_004514ec`; `R:news-log-format-and-messages.md Q4 #19, #20`. `[confirmed]`.

**L07b — Fleet launch line** | `"N finishes a new fleet at C."` (with the final period) | `X:FUN_0044a050 @ 0x0044a050`; `R:news-log-format-and-messages.md Q4 #3` (*"code-only, never saved"*). `[derived]`.

**L08 — Elimination banner + leader lines** | A dashed line, `"A conquers B."`, a dashed line (59 dashes); `"N depose their leader L."` | `R:news-log-format-and-messages.md Q4 #10–#13` (*'2 of 2' banners, 2 events of #13*); `X:FUN_0044c528`, `FUN_0044c8f0`. `[derived]`.

**L09 — Refusals of orders** | Single-line information boxes, grouped by the function that raises them | `exe_strings.tsv` + `dump_string_literals.tsv` (functions `TUnitMap_*`, `TArmyRecruits_*`, `TRecruitMercs_*`, `TPolitics_*`, `TPremierForm_BuildNewFleet`, `TChangeArmyUnits_*`, `TArmyToArmy_*`) | `coverage.md §3 Messages (seen: embark refusal T_EMBARK_REFUSED.SAV; "too small to split" T_CHUNITS_REFUSED.SAV; "You cannot trade with ..." trade-numidia-0720.SAV; "Only nations with coastal cities can build fleets." civ-sweep)`. Multiple refusal literals already cited across drafts (UA01, UA03, UA04, UA05, UA06, UA07, UF02, UF05, UF06, S02a, S05a/b, D04, K03). `[confirmed]` carry-over.

**L10 — Confirmation boxes** | Yes/No/Cancel questions (lead a different nation, abdicate, attack a fleet, scuttle a fleet); `[code only]` start a new game, quit, attack a city or army (a city prompt was seen: `B2_PEACE_GENUA_*`), disband (army, unit), surrender | `SS:FI_b1_09_game_newnation.png`, `FI_b1_10_game_abdicate.png` (the New-nation / Abdicate boxes already cited in the G03 + G04 draft); coverage.md §3 `Attack rows` (attack this fleet: `PP_yes_seed1.SAV`); `X:TPremierForm_NewGame`, `TPremierForm_CheckQuit`, `TUnitMap_SelectUnit`, `TUnitMap_DisbandArmy`, `TUnitMap_ScuttleFleet`, `TArmyRecruits_DisbandUnits`, `TChangeArmyUnits_Disband`, `TBattleOver_OK`. `[confirmed]`.

**L11 — Unit-order limits shown as refusals** | 20 units and 100,000 troops per army, 100 ships per fleet, 40 recruited units, 500 troops per ship, 198 armies, mobilisation 100 percent | `X:TUnitMap_JoinArmies`, `TUnitMap_JoinFleets`, `TArmyToArmy_Army1Transfer @ 0x00442500`, `TRecruitMercs_RecruitMercUnit`, `TArmyRecruits_RecruitUnit` | literals in `dump_string_literals.tsv` (functions cited). **The 100-ships-per-fleet case (Join fleets) is the exact in-play prompt the user just pasted — the decompile reads `< 0x65` (accept 100, refuse 101); a live-driver reproduction is being run separately.** Forward-pointer: see the future `findings/2026-10-XX-join-fleets-cap-in-play.md` once published. `[derived]`.

**L12 — "End turn ?" warning lines** | Five lines: *"An army of yours needs supplies."*, *"An army of yours cannot afford to pay its mercenary units."*, *"A fleet of yours needs repairing."*, *"One of your fleets is not docked at its own city."*, *"A fleet of yours needs supplies."` | `F:2026-10-03-end-turn-warning-box.md`; `coverage.md §3 End turn (warnings, one box with five lines seen without a save)`; `X:TToEndTurn_InitializeForm @ 0x00459828`. **The five-warning strings are NOT in `dump_string_literals.v2.tsv`** — `[derived]` carry-over (the warnings are joined strings assembled in the function body; would need capstone on `TToEndTurn_InitializeForm` to enumerate). One of the lines *"An army of yours needs supplies."* has been seen live (`tests/results.md` / `F:2026-10-02-unit-map-mouse-orders-and-tax-range.md` *"An army of yours needs supplies"*); the others are `[code]`. `[derived]`.

**L13 — Information-panel text** | Labelled lines of nation/city/army/fleet panels and the readiness/loyalty/unity/morale words | **Cell-level extraction is in the N01–N03 + UC01+UM01–UM09 drafts already on main.** Literal examples: *"Fleet of "* / *"Ships -"* / *"Repair -"* / *"Capacity -"* / *"Sea-"* / *"calm"* / *"rough"* (`dump_string_literals.v2.tsv` rows 152, 154, 155, 162, 164–166 for the fleet panel); *"Mercenaries at "*, *"There are no mercenaries at "* (rows 168–169 for the city-merc panel); *"Mobilized"*, *"Treasury"* (rows carrying nation-status table — N03 draft cites these). `X:TInformation_ShowNationStatus`, `ShowCityDetails`, `ShowArmyDetails`, `ShowFleetDetails`. Multiple SS screenshots: `FI_b1_21_nation_rome.png` (Rome's panel — Mobilized 30%, Treasury 2,200), `FI_b1_24_city_left_click.png` (city panel), `FI_b1_*.png` (fleet + army panels cited via N01–N03 + UC01+UM01–UM09 drafts). `[confirmed]`.

**L14 — Dialog labels and formatted numbers** | Fixed labels *"Create unit at"*, *"Units at"*, *"Supplies at"*, *"will pay / will receive"*; numbers printed with hard-coded comma every three digits | `X:TArmyRecruits_SetCityRecruits @ 0x0045495c`, `TAFSupply_CityOrFleet`, `THVHBatPols_PrintNumbers @ 0x004584b8`, `FUN_00448e74 @ 0x00448e74` (FormatNumber); `R:news-log-format-and-messages.md Q2`. `[derived]` carry-over for the comma-format logic; the labels themselves appear in `dump_string_literals.tsv` at the cited functions.

## What does not match — five open notes

1. **L12's warning strings aren't pinned cell-by-cell** — `dump_string_literals.v2.tsv` doesn't list them; the function joins them at runtime. Carrying `[derived]` carry-over; would need capstone on `TToEndTurn_InitializeForm`. **One warning ("*An army of yours needs supplies."*) is seen on a save** (`tests/results.md` / `F:2026-10-02-unit-map-mouse-orders-and-tax-range.md`); the other four are `[code]` only.
2. **L13 overlaps N01–N03 + UC01+UM01–UM09** — the panel literals are reproduced verbatim there; this draft *cites* those drafts rather than re-enumerating. No work duplicated.
3. **L11 forward-pointer** — the 100-ships-per-fleet bullet is the same boundary the Join-fleets paste-prompt asks to verify. The decompile reading (`< 0x65`) is from `function_list.tsv` (literal at row 247 of `dump_string_literals.v2.tsv`); the live-driver reproduction is being run separately and will land at `findings/2026-10-XX-join-fleets-cap-in-play.md` when complete.
4. **L07b's "fleet launch" is `[code] never saved`** — the inventory's note marks it as such; the *code-only* nature means even a complete live-Wine reproduction wouldn't surface the line in a save's news log. Carrying forward.
5. **L14's comma-format helper (`FUN_00448e74`)** — the inventory's row prose references it but the function-table search returns just `FUN_00448e74` (Delphi RTTI didn't recover a class+name); reproducing the comma logic would need capstone on this address. `[derived]`.

## Method

- **News-template literals.** Eight rows (L01–L08 + L07b) cite either the inventory's evidence column (function address, save path, or research-side report). Where literals appear in `dump_string_literals.tsv` / `dump_string_literals.v2.tsv`, the cited functions back them; where the literal is assembled at runtime (L07b, L08's two-space banner), the function is the only pointer.
- **Refusal literals (L09, L11, L12).** Cited across drafts already (UA01, UA03, UA04, UA05, UA06, UA07, UF02, UF05, UF06, S02a, S05a/b, D04, K03). This draft enumerates the inventory's evidence-column call sites (function names) so a single read of `dump_string_literals.tsv` per function reproduces the cell-level text.
- **L13 dedup.** The information-panel row cites N01–N03 + UC01+UM01–UM09 drafts verbatim for the literals and the screenshot hashes; no work duplicated here.
- **L14 functions.** `TArmyRecruits_SetCityRecruits`, `TAFSupply_CityOrFleet` (function-table row not surfaced — possibly a helper without a Delphi RTTI name; `[derived]`), `THVHBatPols_PrintNumbers @ 0x004584b8`, `FUN_00448e74 @ 0x00448e74`.
- **Tag scheme.** Carried from the inventory without re-tagging.

## Inferences

- **The news-template rows (L01–L08 + L07b) all funnel through `X:FUN_00449a44`** (the news-line dispatcher cited for L03 and reused by L03b, L04, L04b, L05, L06, L07, L07b, L08 — confirmed at `0x00449a44`). One dispatcher writes the entire news-log format.
- **The five L12 warning strings are not in the literals table** because they're joined at runtime inside `TToEndTurn_InitializeForm`; a faithful reproduction needs the function walked with capstone to confirm the join order.
- **L11 + the freshly-pasted Join-fleets prompt share the same byte-boundary question** (combined ships = 99 / 100 / 101); the L11 row carries forward to that future draft.

## What this does not establish

- L12's full warning-string text (open note 1).
- L13's per-row literal list (open note 2; cited from sibling drafts).
- L11's 100-ships boundary on a live save (open note 3; reproduced by the upcoming live-driver experiment).
- L07b's "[code] never saved" line (open note 4).
- L14's comma-format helper logic (open note 5).

## Reproduction

```bash
cd ~/projects/ic2-conquest
# News + treaty dispatchers + fleet events
grep -E "FUN_0044(aee4|b5d0|50c68|a050|c528|c8f0|514ec)|FUN_00449a44|FUN_00448e74" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
# Refusal literal anchors (UA01, UA03-UA07, UF02, UF05, UF06, etc.)
grep -nE "Are you sure you want to|too large|cannot attack|cannot join|cannot trade|too small" \
     runs/experiments/data/run-exp-feature-inventory/dump_string_literals.v2.tsv
sha256sum runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_09_game_newnation.png \
          runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_10_game_abdicate.png \
          runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_20_nation_carthage.png \
          runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_21_nation_rome.png \
          runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_24_city_left_click.png
```

The function and literal extracts are deterministic. The five screenshot SHA-256s should match `MANIFEST-batch1.txt`. Live Wine is only needed for the L11 / Join-fleets bullet (open note 3) and reproducing the L12 warnings-end-to-end (open note 1).
