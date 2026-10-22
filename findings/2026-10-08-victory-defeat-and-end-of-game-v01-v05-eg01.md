# Victory and defeat (V01–V05) and End-of-game screens (EG01) — verification

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows V01–V05 and EG01. Six rows that close the 146-row inventory. V01–V05 share `THumanFalls_InitializeForm @ 0x00455e38` (the *End of Game* form initialiser); EG01 is the form itself. One consolidated draft.

**Tags.** All `[derived]` (the End-of-game screen is opened only when one of these triggers fires; coverage.md §4 not yet seen).

## Answer — per-row sources

**V01 — Victory: all 334 cities** | The game ends with *"You have conquerred the Mediterranean, a unique achievement."* when the nation holds all 334 cities | `dump_string_literals.v2.tsv` **row 384** reproduces the literal at `THumanFalls_InitializeForm 0x00455e38`. `X:THumanFalls_InitializeForm` (cities test against 334); `X:FUN_00452034` (the cities-count test fired at every human turn start). `R:decompiled-diplomacy-peace-terms-and-instant-battles.md 'Victory condition'`. `H:'Victory'`. coverage.md §4 `Victory` — `[not yet seen]` per the inventory's row prose. `[derived]`.

**V02 — End of the allotted 20 years** | At 250 BC the game ends with *"You have reached the end of your allotted 20 years."* | `dump_string_literals.v2.tsv` **row 379** reproduces the literal at `THumanFalls_InitializeForm 0x00455e38`. `X:THumanFalls_InitializeForm` (year compared with 250); `X:FUN_00452034` (tested at every human turn start). `R:decompiled-diplomacy-peace-terms-and-instant-battles.md`. `H:'Time' (Conquest must end by 250 BC)`. `[derived]`.

**V03 — Conquered** | A human nation with no cities left sees *"Your nation has been conquerred by <nation>."* and the seat turns computer-controlled | `dump_string_literals.v2.tsv` **row 382** reproduces the literal up to the trailing space (the `<nation>` is appended at runtime from the conqueror's name — `TInformation_ShowNationStatus @ 0x0043ba7c` carries the equivalent panel text at row 104 `" conquerred by "`). `X:THumanFalls_InitializeForm @ 0x00455e38`, `X:TPremierForm_HumanLeaderFalls @ 0x0045c238`. `R:decompiled-elimination-cleanup.md §3`. coverage.md §4 `Conquest` — `[not yet seen]`. `[derived]`.

**V04 — Deposed by the army** | *"Your unpopularity has forced the army to overthrow you."* when unity is below 400, otherwise *"Your army have deposed you because they have not been paid."* (debt); the game ends for that seat and it turns computer-controlled | `dump_string_literals.v2.tsv` **rows 380 + 381** reproduce both literals at `THumanFalls_InitializeForm 0x00455e38`. Test: treasury below `-(wealth div 500)` or below -20,000, or unity below 400, run at the start of each human turn (not conquered, not 250 BC). `X:THumanFalls_InitializeForm`, `X:FUN_0044c8f0` (the deposit-leader dispatcher — also cited in the E16 quarterly-tick row). `R:upkeep-payment-and-desertion.md 'Debt and deposition'`. `H:'Balance sheet' (debt limit)`. `[derived]`.

**V05 — Survival and peaceful targets** | Help states only one sure way to win (dominate the Mediterranean) and no difficulty level; players set their own targets | `H:'Victory'`. `[derived]` carry-over (no save diff exercises this — purely a help-text claim).

**EG01 — End of Game screen** | Window *"End of Game"*: the reason, the leader's years in power and a start-versus-end table of population, cities and money; OK closes and the seat is handed over (or the game ends when no human is left) | form `THumanFalls` (in `forms.json`); `THumanFalls_InitializeForm @ 0x00455e38` (the form-init populating `lbl_result1` / `lbl_result2` / `lbl_changes` / `lbl_nat1..2` / `lbl_pop1..2` / `lbl_cities1..2` / `lbl_money1..2` / `OK` per the inventory); `X:THumanFalls_InitializeForm`, `X:THumanFalls_OK`. `R:decompiled-elimination-cleanup.md §3`. coverage.md §4 `End of Game` — `[not yet seen]`. `[derived]`.

## What does not match — three open notes

1. **V01–V04 are `[not yet seen]` per `coverage.md §4`** (the inventory carries this verbatim). They are not in the live-save evidence path because the End-of-Game screen is reachable only when one of the four triggers fires. Reproducing V01 requires 334-city ownership (a long game); V02 requires the year reaching 250 BC (also long); V03 requires the human nation to be eliminated (mid-game); V04 requires the unity or treasury gate to fire (mid-game). None of these are in the runs/ directory's tracked live tests.
2. **V03's `<nation>` placeholder** is appended at runtime from the conqueror's nation record; the `THumanFalls_InitializeForm @ 0x00455e38` literal is *"Your nation has been conquerred by "* (trailing space), and the runtime then writes the conqueror's name. Reproduction would need a save pair where the human is conquered; the literal text up to the conqueror name is the cell-level pinning.
3. **EG01's exact label strings** (`lbl_result1`/`lbl_result2`/`lbl_changes`/etc.) are form-level TPF0 captions that live in `forms.json` for the `THumanFalls` form. Cell-level reproduction would pin those captions verbatim; the inventory's evidence row already lists the labels.

## Method

- **Form + function extraction.** Same toolchain. `THumanFalls_InitializeForm @ 0x00455e38` and `TPremierForm_HumanLeaderFalls @ 0x0045c238` from `function_list.tsv`. Four outcome-panel literals confirmed in `dump_string_literals.v2.tsv` rows 379/380/381/382/384 verbatim (including the deliberate *"conquerred"* misspelling with double *r*).
- **Cross-row reuse.** V01–V04 all route through `THumanFalls_InitializeForm`; EG01 *is* `THumanFalls`. One form, five (V01–V05 + EG01) visible rows.
- **`FUN_00452034`** is the per-human-turn-start check (cities + year); cited in both V01 and V02.
- **`FUN_0044c8f0`** is the deposit-leader dispatcher — also cited in the E16 quarterly-tick row (D-row reuse carried forward).
- **Tag scheme.** Same as the other drafts.

## Inferences

- **The four outcome-panel literals are all in one function (`THumanFalls_InitializeForm`)** at addresses `0x00455e38`. A reproduction can wire one form-init that branches by the trigger (cities == 334 → V01; year == 250 → V02; nationsEliminated → V03; unity < 400 or treasury < threshold → V04) and emits the corresponding literal.
- **EG01 is the form that displays them** — the labels (`lbl_result1`/`lbl_result2`/`lbl_changes`/etc.) are the *frame*, the four-literal set is the *content*. Capturing both is enough to render the End-of-Game screen.

## What this does not establish

- Live-save test for V01–V04 (open note 1).
- V03's runtime conqueror-name substitution (open note 2).
- EG01's per-label TPF0 captions verbatim (open note 3).

## Reproduction

```bash
cd ~/projects/ic2-conquest
grep -E "THumanFalls_InitializeForm|TPremierForm_HumanLeaderFalls|FUN_00452034|FUN_0044c8f0" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
grep -nE "allotted 20 years|unpopularity has forced|deposed you because|Your nation has been conquerred|conquerred the Mediterranean" \
     runs/experiments/data/run-exp-feature-inventory/dump_string_literals.v2.tsv
# form roster (29 forms total expected):
python3 -c 'import json; print(len(json.load(open("runs/experiments/data/run-exp-feature-inventory/forms.json"))))'
```

The form, function and literal extracts are deterministic. Re-running `tests/test_orders.py` does not reach any of V01–V04 — those triggers are game-end conditions, not in the coverage.md test set.
