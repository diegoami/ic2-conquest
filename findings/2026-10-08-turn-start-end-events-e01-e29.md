# Turn-start and turn-end events — verification of rows E01–E29

**Status:** draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` rows E01–E29. The largest section of the inventory (29 rows). All rows are either `[confirmed]` (live-save evidence) or `[derived]` (decompile-only, with the dispatching function cited in the inventory). Coverage: `coverage.md §4` and several research-side reports (`R:decompiled-quarterly-billing-and-economy.md`, `R:decompiled-turn-and-calendar-sequencing.md`, `R:city-population-growth.md`, `R:army-moves-field-signed-and-the-ffff-underflow.md`, etc.).

**Tag scheme.** Carried from inventory; this draft tightens the cell-level evidence without re-tagging.

## Per-row sources

**E01 — Diplomatic offer box at turn start** | `X:TPremierForm_StartTurn @ 0x0045ac5c`; coverage §3 `Turn start (AI offers)` ✅ (`BASE.SAV` turn 0720, Bithynia). Refusal / offer paths cited per `R:news-log-format-and-messages.md Q5` and `decompiled-ai-offers-to-human-seats.md`. `[confirmed]` carry-over.

**E02 — Round tick (week, season, year)** | Reproduction: `tests/results.md 'attack'` — news tail *"Week 3 Spring 270BC"* after first End turn (`T_ATTACK.SAV`). `R:decompiled-turn-and-calendar-sequencing.md`. `H:'Time'`. `[confirmed]`.

**E03 — Quarterly tick** | `X:FUN_00451b40` (the quarterly dispatcher; appears in E13/E16/E17/E29 too). `R:decompiled-quarterly-billing-and-economy.md` + `upkeep-payment-and-desertion.md` + `decompiled-quarterly-rebellion.md`. coverage §4 `Quarterly billing and taxes`. The order is *"upkeep → wealth/tax base rebuild → city loop → nation loop → relation thaw"*. `[confirmed]`.

**E04 — Supply use and morale** | `H:'Time', 'Armies'`; `R:rules-digest.md §2` → `supply-driven-morale-and-fleet-attrition.md`. coverage §4 `Supply consumption and seasonal rates` `[confirmed]`.

**E05 — Fleet completion** | `X:FUN_0044a050`; coverage §4 `Fleets: build, launch`. Live: `saves/fleet-port-antium-0734.SAV` ordered 0720, launched 0732 (countdown 24 ÷ 2 = 12 ticks). `[confirmed]`.

**E06 — Storms at sea** | `X:FUN_004514ec`; `R:decompiled-storms-and-losses-at-sea.md`. Live: `NAT_seed1_13_0727_seat02.SAV` — *"A fleet belonging to Ptolemaic is lost at sea."*. `[confirmed]`.

**E07 — Weather (rough sea)** | `X:FUN_00451304 / FUN_004511bc`. `R:decompiled-weather-events.md` + `decompiled-map-code1-overlay.md`. Twenty fixed sea-region centres, rolled each tick per `DAT_0x4790*` block; spring 1/15 / summer 1/40 / autumn 1/30 / winter 1/5; **code-painted onto calm (code 0) — never written to DAT**. `[derived]` carry-over.

**E08 — AI wars, alliances, peace** | `SS:FI_b1_01_main.png`. `R:news-log-format-and-messages.md Q4 #1 / #2 / #14–#18`. `R:decompiled-war-cascade-and-peace-paths.md`. `[confirmed]` (the treaty block at row L06 documents the visible side).

**E09 — Siege attempts** | `X:FUN_0044b27c` (the siege dispatch). `R:decompiled-defection-and-siege-attrition.md`. Live: `T_ATTACK.SAV` (army 23,700 → 21,765; Felsina loyalty 79→76, fort 68→65, pop 26→25; news *"Rome fails to capture Felsina (Gaul)"*). coverage §1 `Attack a city (siege)` ✅. `[confirmed]`.

**E10 — Mercenary offers appear and are taken** | `SS:FI_b1_22_show_all_mercenaries.png`. `R:decompiled-mobilization-and-mercenary-restock.md` + `decompiled-new-game-mercenary-fill.md`. coverage §1 `Hire mercenaries` ✅ (`saves/merc-hire-free-0720.SAV`). 50 fixed merc slots; each quarter an empty slot refills p=0.85 and a live offer is replaced p=1/9; quality 5–9. `[confirmed]`.

**E11 — City capture, defection, elimination** | `X:FUN_0044b27c / FUN_0044bed8 / FUN_0044c528`. `R:decompiled-city-capture-resolution.md` + `decompiled-defection-and-siege-attrition.md` + `decompiled-elimination-cleanup.md` + `news-log-format-and-messages.md Q4 #5, #9, #11`. Live captures documented in the AI-mover intake (`run-exp-ai-contact` batches b1 / b3). `[confirmed]`.

**E12 — Automatic resupply on a move** | `X:FUN_0044f6d8` (the auto-resupply handler). `R:supply-capacity-rounding.md` + `upkeep-payment-and-desertion.md`. `docs/rules-digest.md §2 "How an army resupplies" 2` + `§5 "Adjacency and attack orders"`. coverage §4 `Auto-resupply next to an own city`. `[derived]` carry-over (the per-row save test is open).

**E13 — Rebellion and rebirth** | `X:FUN_0044c204 + FUN_00451b40`. `R:decompiled-quarterly-rebellion.md`. `docs/rules-digest.md §5`. coverage §4 `Rebellion, rebirth` `[derived]` — "never observed; no save held a city below loyalty 39".

**E14 — Capture effects + defection cascade** | `X:FUN_0044bb18 + FUN_0044ba1c`. `R:decompiled-city-capture-resolution.md` + `decompiled-defection-and-siege-attrition.md`. coverage §4 `City capture, defection cascade`. `[derived]`.

**E15 — Mercenary pay and desertion** | `R:upkeep-payment-and-desertion.md` + `decompiled-fleet-tax-and-mercenary-formulas.md`. `docs/rules-digest.md §3 "Mercenary pay and desertion"`. `X:FUN_00451b40`. `[derived]`.

**E16 — Debt and deposition of an AI leader** | `X:FUN_0044c8f0 + FUN_00451b40`. `R:upkeep-payment-and-desertion.md "Debt and deposition"`. `news-log-format-and-messages.md Q4 #13` (2 events). coverage §4 `Debt and deposition`. `[derived]`.

**E17 — Tax effects** | `R:city-population-growth.md` + `decompiled-quarterly-billing-and-economy.md`. `docs/rules-digest.md §3 "Tax effects"`. `X:FUN_00451b40`. `[derived]`.

**E18 — Mobilisation rate** | `R:decompiled-mobilization-and-mercenary-restock.md` + `decompiled-recruitment-cost-formula.md`. `docs/rules-digest.md §4 "Placing an order", "Mobilizing"`. `X:TArmyRecruits_RecruitUnit`. Live: `saves/recruit-hi3200-0720.SAV` (30 → 32). `[derived]`.

**E19 — City supply stock and winter famine** | `R:city-population-growth.md` + `decompiled-turn-and-calendar-sequencing.md (correction note)`. `docs/rules-digest.md §2 "City supply stock"`. `X:FUN_004514ec`. coverage §4 `Winter attrition of city stocks` `[derived]` (one of the cited `What this does not establish` items).

**E20 — Army moves per turn and walking** | `R:army-moves-field-signed-and-the-ffff-underflow.md` + `decompiled-army-movement-and-river-cost.md` + `terrain-move-cost-table-in-dat.md`. `docs/rules-digest.md §5 "Moves", "Walking"`. coverage §1 `Move army` ✅ (`T_MOVE.SAV`: army 0 (100,37) → (101,36), moves 8 → 4 — river tile). `[confirmed]`.

**E21 — Siege resolution and attrition** | `X:FUN_0044b27c`. `R:decompiled-city-capture-resolution.md` + `decompiled-defection-and-siege-attrition.md`. `docs/rules-digest.md §5 "Siege"`. coverage §1 `Attack a city (siege) ✅`. `[derived]`.

**E22 — AI diplomacy toward the player + cooldowns** | `R:decompiled-ai-offers-to-human-seats.md` + `decompiled-diplomacy-peace-terms-and-instant-battles.md` + `decompiled-war-cascade-and-peace-paths.md`. `docs/rules-digest.md §7`. coverage §4 `AI declares war on Rome` `[derived]`.

**E23 — New game start state** | `R:decompiled-new-game-mercenary-fill.md` + `F:2026-09-29-new-game-recruitment-queues-come-from-the-dat.md`. `docs/rules-digest.md §1, §10`. `C:§1 'New game (any nation human; several for several human seats)'`. `F:2026-10-02-start-as-each-nation.md` — five nations start with no army (Numidia, Greece, Illyria, Dacia, Armenia); only Carthage and Ptolemaic have a fleet at start. `[confirmed]`.

**E24 — Recruitment queue as garrison and training** | `R:ptolemy-run-readiness-ladder-and-mobilization-rate-confirmed.md` + `decompiled-mobilization-and-mercenary-restock.md`. `docs/rules-digest.md §4 "The recruitment queue", "Readiness and quality"`. `H:'Recruit unit'`. coverage §4 `Recruitment readiness and mobilization` ✅ (`saves/mobilize-new-army-0720.SAV`). `[confirmed]`.

**E25 — Fleet supply, condition, moves** | `R:supply-driven-morale-and-fleet-attrition.md` + `F:field-recruitment-uniform-attrition-and-fleet-drift.md`. `docs/rules-digest.md §8`. `H:'Fleets'`. `F:2026-10-02-fleets-sail-and-drift.md`. `[derived]`.

**E26 — AI mercenary hiring** | `R:decompiled-mercenary-offer-list-and-position.md` + `decompiled-mobilization-and-mercenary-restock.md`. `docs/rules-digest.md §4 "Mercenaries"`. `[derived]`.

**E27 — Trade and tribute income** | `R:nation-tax-base-and-city-economy-fields.md` + `decompiled-quarterly-billing-and-economy.md`. `H:'Nations'` (lists tribute + trade income). Live: `SS:FI_b1_16_balance_sheet.png` (Rome at 0720: trade 29). coverage §4 `Trade income` ✅. `[confirmed]`.

**E28 — Elimination cleanup** | `X:FUN_0044c528`. `R:decompiled-elimination-cleanup.md`. `docs/rules-digest.md §9`. Live: `SS:FI_b1_20_nation_carthage.png` (Carthage status panel layout after elimination). coverage §4 `Conquest` `[derived]` (consistency with V03 / row's status panel layout).

**E29 — Army morale from supply** | `R:supply-driven-morale-and-fleet-attrition.md` + `decompiled-unit-map-orders-and-record-fields.md Part 1`. `docs/rules-digest.md §2 "Supply drives morale and moves"`. `H:'Armies'`. coverage §4 `Morale from supply` `[derived]`.

## What does not match — five open notes

1. **E07 ("paint onto calm")** is `[derived]` and the inventory's note records the correction: *"code 1 is rough sea: a weekly weather overlay that FUN_00451304 / FUN_004511bc paint onto calm sea (code 0) and clear again a week later. The DAT holds no code-1 cell."* Carrying forward per the inventory's explicit correction note in `R:terrain-move-cost-table-in-dat.md`.
2. **E13's "no save held a city below loyalty 39"** is `[derived]` carry-over per the inventory's row prose. Reproduction would need a controlled save that takes a city below 30 loyalty (a long siege with high tax).
3. **E15's "desertion takes the army's last unit's place; supplies troops div 100 tons"** is the only [code] carry-over; not in literals.
4. **E19's "winter famine / loyalty -1 with 1/3 chance"** is `[derived]` — no save held an empty winter stock (every test's cities had positive supply going into winter).
5. **E25's fleet-moves formula details (30 - (ships-50)/10 - troops/100/ships - 3 at zero supplies; (70 - condition) >> 2 when below 70)** are `[derived]` carry-over from the inventory's row prose.

## Method

- **Per-row evidence.** Each row above reproduces the inventory's evidence column verbatim, plus the dispatcher function address where the inventory cited one. Sources are: `function_list.tsv` (for `X:` cites), `coverage.md §1 / §3 / §4` (for `C:` cites), and the research-side reports cited as `R:` (all `~/projects/imperial-conquest-2-research/docs/reports/...`).
- **Where coverage.md §4 is `[derived]`**, the inventory's row tag carries over; this is the dominant `[derived]` tag across E-section.
- **`FUN_00451b40`** recurs as the quarterly-tick dispatcher (E03 / E13 / E16 / E17 / E29). Single source, multiple call sites — recorded once.
- **Research-side reports** that are the canonical `R:` cites for this section sit under `~/projects/imperial-conquest-2-research/docs/reports/` and are read-only from this session.

## Inferences

- **`FUN_00451b40` is the quarterly-tick dispatcher**, the single function called from E03 / E13 / E16 / E17 / E29. Carrying this as a *single* function across rows means a reproduction can wire one shared helper with branching per-tick sub-routine, rather than five independent functions.
- **The dispatching functions cited in the inventory's `X:` column are the highest-confidence pointers** for each row's behaviour; `[derived]` carry-over flags them as decompile-only with no live-save test.
- **E09 / E11 / E21 share `FUN_0044b27c`** (the siege dispatch); E21's "capture-after-siege" path then runs `FUN_0044bed8` (the city ownership transfer) or `FUN_0044c528` (the elimination). Three rows share a function stack — reproductions need this stack, not the row-by-row entry points.

## What this does not establish

- E07's weather-overlay paint (open note 1).
- E13's no-below-loyalty-39 save (open note 2).
- E15's desertion semantics (open note 3).
- E19's winter-famine path (open note 4).
- E25's exact fleet-moves formula details (open note 5).

## Reproduction

```bash
# function-table search for the dispatchers
grep -E "FUN_00451b40|FUN_0044b27c|FUN_0044bed8|FUN_0044c528|FUN_0044a050|FUN_0044c8f0|FUN_0044c204|FUN_0044ba1c|FUN_0044bb18|FUN_0044f6d8|FUN_004514ec|FUN_00451304|FUN_004511bc|FUN_0044a4e0|TPremierForm_StartTurn" \
     runs/experiments/data/run-exp-feature-inventory/function_list.tsv
# coverage rows for E03/E04/E05/E19/E22/E23
grep -E "Quarterly|Supply consumption|build, launch|AI declares war|New game|Storms" coverage.md
# screenshot hashes for the live rows
sha256sum runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_20_nation_carthage.png \
          runs/experiments/data/run-exp-feature-inventory/explore/FI_b1_22_show_all_mercenaries.png
```

The function + coverage extracts are deterministic. Re-running the existing quarterly-tick tests in `tests/test_orders.py` covers the live evidence path for the rows that have it.
