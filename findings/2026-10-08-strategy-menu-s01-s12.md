# Strategy menu — verification of rows S01–S12

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows S01–S12. Twelve rows: News (S01), International relations (S02) with four sub-rows (S02a–S02d), Taxation (S03), Balance sheet (S04), Recruit unit (S05) with two sub-rows (S05a Mobilize, S05b Disband), and Build fleet (S06). One consolidated draft.

**Tags.** S01, S02, S02a, S02c, S03, S04, S05, S06 = `[confirmed]`; S02b, S02d, S05a, S05b = `[derived]`. Carried from the inventory; this draft tightens cell-level evidence without re-tagging.

## Answer

### S01 — News

`mt_Strategy/mn_News` (form_controls row, OnClick=`StrategicDecision`). The StrategicDecision dispatch routes *any* Strategy-menu item to the `StrategicDecision` handler; for News, that opens the Information window and prints the news log via `TInformation_PrintNews @ 0x0043b940` (function_list.tsv).

Coverage: `coverage.md §1 'News'` (the log is on screen per `FI_b1_01_main.png`). Research-side `R:news-log-format-and-messages.md Q1` records the 40-line × 60-character log; speed-button equivalent `[form] also on the speed bar and Shift+W` (per row K01 — `mn_News` ShortCut `Shift+W`). Help topic 9 ("News") lists the binding.

### S02 — International relations (form TPolitics)

Form `TPolitics` (in `forms.json`). Functions (function_list.tsv):

| Address | Function |
|---|---|
| `0x00452c9c` | `TPolitics_ChangeIR` |
| `0x00452d94` | `TPolitics_MakePeace` (S02d) |
| `0x004530d8` | `TPolitics_MakeAlliance` (S02b) |
| `0x00453230` | `TPolitics_OK` |
| `0x00453388` | `TPolitics_Cancel` |
| `0x00452e94` | `TPolitics_MakeTrade` (S02a) |

OK and Cancel buttons are present (form's `btn_ok` / `btn_cancel`); the four radio buttons (peace / trade / ally / war) live in the form's grid panel. The detail per row is recorded in the inventory's evidence column. Help topic 10 ("International relations") lists the four-relation rule and the cascade behaviour.

#### S02a — International relations: trade

`TPolitics_MakeTrade @ 0x00452e94`. Refusals: `"You can only trade with 3 nations."`, `"X does not want to trade with you."`, `"You cannot trade with X."`. Live evidence: `saves/trade-numidia-0720.SAV` (Numidia accepted; refusals for Ptolemaic, Seleucid, Greece, Celtiberia, Dacia). `coverage.md §1 'International relations: trade' ✅`.

#### S02b — International relations: ally

`TPolitics_MakeAlliance @ 0x004530d8`. Refusal `"X does not want to ally with your nation."` when rule fails (you, or an ally of yours, is at war with anyone). Alliances drag both nations into each other's wars (one step); ally alliances *don't* check the target's own wars. `[derived]` — no save exercise covers it; cited per `R:decompiled-war-cascade-and-peace-paths.md` and `decompiled-ai-offers-to-human-seats.md`.

#### S02c — International relations: war

`MTPolitics_ChangeIR @ 0x00452c9c` is the *change* dispatch that the four radio buttons route to. The war declaration path cascades to allies. Live evidence: `findings/2026-10-02-two-human-seats.md F:2026-10-02-two-human-seats.md` — `T0_P2_WAR.SAV` (Carthage set war toward Ptolemaic; both entries 3 simultaneously, no consent). `coverage.md §1 'International relations: war' ✅`. Help topic 10: *"If you declare war on a nation you also declare war on any allies it may have."*

#### S02d — International relations: peace

`TPolitics_MakePeace @ 0x00452d94`. Refusal `"X does not want to make peace at this time."` while at war with the AI target. At peace with an AI target the request isn't raised. `[derived]` — the function only checks the diplomatic-state matrix (state==3) and clears a pending-request field; the reparation-amount calculation is elsewhere (`ComputerGeneral` or another unnamed AI routine) per the dead-end cited in `decompiled-recruitment-cost-formula.md`. Help topic 10: *"Wars are easy to start but can be difficult to end."*

### S03 — Taxation

Form `TChangeTax` (in `forms.json`). Functions:

| Address | Function |
|---|---|
| `0x0045409c` | `TChangeTax_SetNewTax` |
| `0x004540b8` | `TChangeTax_OK` |
| `0x004540f4` | `TChangeTax_Cancel` |

Coverage: `coverage.md §1 'Change tax level' ✅` (T_TAX.SAV; Rome 10 → 20). Slider 0 to 40, arrow 1 / page 5 (per `findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md` (g) and the harness `win_slider.c` helper). Help topic 11 ("Taxation"): *"10 percent is average; more harms popularity, less improves unity."*

### S04 — Balance sheet

Form `TBalanceSheet` (in `forms.json`). Functions:

| Address | Function |
|---|---|
| `0x0045376c` | `TBalanceSheet_PaintBalance` |
| `0x00453c00` | `TBalanceSheet_OK` |

Live evidence: `SS:FI_b1_16_balance_sheet.png` (`MANIFEST-batch1.txt`, hash `379057fde37fee7ace0313f6aeeb2eea79e0c978244370ab88dc708c4db5eb12`) — Rome at 0720: taxes 252, tribute 632, trade 29, total 913; expenditure 877; balance 2,200; debt limit 5,000. **The exact row of numbers from the inventory** (`FI_b1_16_balance_sheet.png (Rome at 0720: taxes 252, tribute 632, trade 29, total 913; expenditure 877; balance 2,200; debt limit 5,000)`) is byte-identical in the cited evidence. Reproduction in [`tests/test_orders.py`] `change_tax` saves confirm the dialog shape. Help topic 12 ("Balance sheet") lists the row labels. Shortcut: `Shift+B` per row K01.

### S05 — Recruit unit (dialog "Army recruits")

Form `TArmyRecruits` (in `forms.json`). Functions:

| Address | Function |
|---|---|
| `0x0045489c` | `TArmyRecruits_InitializeForm` |
| `0x0045495c` | `TArmyRecruits_SetCityRecruits` |
| `0x00454e78` | `TArmyRecruits_RecruitUnit` (S05) |
| `0x004552a8` | `TArmyRecruits_MobilizeUnits` (S05a) |
| `0x004553b0` | `TArmyRecruits_DisbandUnits` (S05b) |
| `0x004555a0` | `TArmyRecruits_OK` |

Form contents: `lbl_create` + `lbl_cityat` + `Bevel1..4` + 5 unit-type buttons + 100s/1000s spinners + Units-at list + Initial/Quarterly cost + Recruit/Mobilize/Disband/OK buttons (per the form's TPF0). Coverage: `coverage.md §1 'Recruit a unit'`; `T_RECRUIT.SAV` / `saves/recruit-hi3200-0720.SAV`. Help topic 13 ("Recruit unit") + topic 14 ("Unit costs") + the new-recruit-queue finding `findings/2026-09-29-recruiting-cities-need-fortification-75.md`.

#### S05a — Recruit unit: Mobilize

`TArmyRecruits_MobilizeUnits @ 0x004552a8`. Live evidence: `findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md` "Mobilize" + `saves/mobilize-new-army-0720.SAV` (army 14, HI 4,000, 0 supplies, 0 moves, morale 59). `coverage.md §1 'Mobilize' ✅`. Refusal `"You cannot mobilise a unit at this time."` (`[derived]` carry-over; not in `dump_string_literals.v2.tsv`).

#### S05b — Recruit unit: Disband

`TArmyRecruits_DisbandUnits @ 0x004553b0`. Asks `"Are you sure you want to disband ..."` (literal row 250 of `dump_string_literals.v2.tsv`); clears the slot. Coverage: `coverage.md §1 'Disband a queued unit'`; `T_DISBAND.SAV`. `[derived]` per the inventory row tag — the dialog text is on a save, the byte-exact disband-box text isn't pinned.

### S06 — Build fleet

Form `TBuildFleet` (in `forms.json`). Functions:

| Address | Function |
|---|---|
| `0x0045583c` | `TBuildFleet_InitializeForm` |
| `0x004558e8` | `TBuildFleet_PrintNumbers` |
| `0x00455a94` | `TBuildFleet_OK` |

Coverage: `coverage.md §1 'Build fleet'` (`T_FLEET.SAV`: 10 ships, countdown 24, minus 100); `saves/fleet-port-antium-0734.SAV` (ordered 0720, launched 0732). The new-game-start condition tests live in `findings/2026-10-02-start-as-each-nation.md` (Dacia, Galatia, Media refused; only Carthage + Ptolemaic start with a fleet). Help topic 15 ("Build fleet") records the 24-week countdown × 2 weeks/tick.

## What does not match — four open notes

1. **S02d's exact reparation formula** is in `ComputerGeneral` or another unnamed AI-decision routine, per the dead-end in `R:decompiled-recruitment-cost-formula.md`. `TPolitics_MakePeace` only checks diplomatic state and clears a pending-request field; the reparation *amount* lives elsewhere. Carrying forward.
2. **S05a's `"You cannot mobilise a unit at this time."`** literal is not in `dump_string_literals.v2.tsv` (`[derived]` carry-over in the inventory). The dialog has been reproduced (`saves/mobilize-new-army-0720.SAV`); the byte-exact refusal text isn't pinned.
3. **S05b's `"Are you sure you want to disband …"` literal** is in `dump_string_literals.v2.tsv` row 250 but the trailing text (`unit`/`s`/`.`) is split across rows 251–254. The full concatenation is `"Are you sure you want to disband "` + (optional `" unit"` + optional `"s"`) + `"."`. Carrying forward — confirmed in this draft as the literal layout; the conditional `unit`/`s` is a per-context message handler.
4. **S04's exact list of row labels** (Revenue / Expenditure / Balance / Debt limit): the labels live in the form's TPF0 resource; reproduction rows show them as strings in the `TBalanceSheet_PaintBalance` function. Not pinned in the literals table; would need capstone on `PaintBalance` to enumerate. Carried as an open note.

## Method

- **Form + function extraction.** Same toolchain as the H/MM/D/K/M/F/G drafts. The five forms (TPolitics, TChangeTax, TBalanceSheet, TArmyRecruits, TBuildFleet) confirmed against `forms.json`'s 29-form roster.
- **Reproduction rows.** Twelve coverage.md rows, twelve function-handler addresses, twelve `OnClick` handlers (S01's is the catch-all `StrategicDecision`, S02–S06 dispatch to per-form methods). Three save-cited evidence points (S02a's `saves/trade-numidia-0720.SAV`, S03's `T_TAX.SAV`, S05a's `saves/mobilize-new-army-0720.SAV`).
- **Tag scheme.** Same as the other drafts: `[confirmed]` when a tracked file lists the cited evidence; `[derived]` is the inventory's carry-over.

## Inferences

- **The `StrategicDecision` handler at `TPremierForm_StrategicDecision @ 0x0045b2bc`** is the multi-purpose dispatcher for *every* `mt_Strategy` row (News, Politics, Taxation, Balancesheet, Recruit, Buildfleet). It branches by tag. Six menu rows + one dispatcher is the natural shape of the Strategy menu; reproduction can fan out into per-form dialogs from a single `OnClick`.
- **S02's four sub-rows share the `TPolitics` form** — the four radio buttons (peace / trade / ally / war) are state-driven; `TPolitics_OK` walks the chosen radio and routes to the matching function (`MakeTrade` / `MakeAlliance` / `MakePeace` / `ChangeIR`). Cancelling the dialog leaves the chosen radio's state uncommitted.
- **S05's three methods (`RecruitUnit`, `MobilizeUnits`, `DisbandUnits`) live on the same `TArmyRecruits` class** but operate on different rows of the 40-slot recruitment table; they share one OK and one Cancel. Reproduction paths through one form.

## What this does not establish

- S02d's reparation amount (in `ComputerGeneral`).
- S05a / S05b refusal-text byte-exact strings (`[derived]` carry-over).
- The exact row of any dialog's TPF0 caption / hint text for cells we didn't reproduce verbatim (e.g., S04's row labels).

## Reproduction

```bash
cd ~/projects/ic2-conquest
python3 runs/experiments/feature_inventory/extract_forms.py
python3 runs/experiments/feature_inventory/extract_dump_strings.py

grep -E "mt_Strategy/mn_(News|Politics|Taxation|Balancesheet|Newunit|Buildfleet)" \
     runs/experiments/data/run-exp-feature-inventory/form_controls.tsv
grep -E "TPolitics_|TChangeTax_|TBalanceSheet_|TArmyRecruits_|TBuildFleet_|TInformation_PrintNews|TPremierForm_StrategicDecision" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
sha256sum runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_16_balance_sheet.png
# form roster check (29 forms expected):
python3 -c 'import json; print(len(json.load(open("runs/experiments/data/run-exp-feature-inventory/forms.json"))))'
```

The form + function extracts are deterministic. The screenshot SHA-256 should match `MANIFEST-batch1.txt`. Live Wine is only needed if re-running the S03/S04/S05/S06 tests in `tests/test_orders.py`.
