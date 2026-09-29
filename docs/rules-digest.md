# Rules digest for the Rome bot (strategy `rome-v1`)

Source: `diegoami/imperial-conquest-2-research` at commit `60475a306a80ed8a2092c47899837f720ef91e56`, `docs/reports/*.md` (cited by filename). Written for a bot playing **Rome, new game, default DAT, 270 BC Spring week 1**, driving the original v1.01 executable under Wine/Xvfb with xdotool.

**Evidence tags**

- **[C]** confirmed: read from decompiled code (instruction or pseudocode level) and/or checked against saves or the game's own screens.
- **[D]** derived: arithmetic or reasoning on confirmed facts, or an inference the report itself marks as such.
- **[O]** observed only: user testimony or a recording, no code behind it.
- **[P]** parsed for this digest from a fixture save or the DAT in `imp_conquest_fixtures` (`1.sav`, `1_thracia_271_spring_1.sav`, `1_cartago_271_spring_1.sav`, `Imperial Conquest 2.dat`); not stated in any report.

Integer division truncates toward zero (`div`). "Chebyshev" is `max(|dx|,|dy|)`, the game's only grid metric (decompiled-mobilization-and-mercenary-restock.md).

---

## 1. Calendar and turn sequencing

- **One turn = one round of all 16 seats = 2 weeks.** After the 16th seat, `TPremierForm_EndTurn` runs the round tick `FUN_004514ec` once **[C]** (decompiled-turn-and-calendar-sequencing.md). One save = one turn = one tick **[C]** (supply-driven-morale-and-fleet-attrition.md).
- **Calendar:** `week = (week + 2) mod 12`, so weeks are 1, 3, 5, 7, 9, 11. On the wrap to 1, `season = (season + 1) mod 4` (0 Spring, 1 Summer, 2 Autumn, 3 Winter); on the season wrap to 0 the BC year decreases by 1 **[C]** (decompiled-turn-and-calendar-sequencing.md). A season is 6 turns, a year 24 turns **[C]** (supply-driven-morale-and-fleet-attrition.md).
- **Length and victory:** the game runs 270 BC to 250 BC (about 480 turns), checked at the start of each human turn in `FUN_00452034` **[C]** (upkeep-payment-and-desertion.md, decompiled-diplomacy-peace-terms-and-instant-battles.md). **The win is holding all 334 cities** ("You have conquerred the Mediterranean") **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md).
- **Turn order:** New Game shuffles the 16-entry turn order, so Rome's seat differs per game (observed indices 13, 10, 7, 5) **[C]** (2026-09-29-new-game-recruitment-queues-come-from-the-dat.md) **[P]**. The AI seats ahead of Rome play turn 1 first: they recruit, hire and move **[C]** (same report; decompiled-new-game-mercenary-fill.md).
- **The round tick, in order** **[C]** (decompiled-turn-and-calendar-sequencing.md, city-population-growth.md, decompiled-mobilization-and-mercenary-restock.md, news-log-format-and-messages.md):
  1. city supply production;
  2. armies: moves recomputed, supply consumed, morale rule;
  3. fleets: consumption, storms, moves;
  4. recruitment-slot readiness `+2` (cap 24);
  5. weather roll `FUN_00451304`;
  6. calendar advance;
  7. **if the week wraps to 1:** quarterly tick `FUN_00451b40`, mercenary restock `FUN_00449130`, then the season advance;
  8. the news lines `" "` and `Week N Season YYY BC`.

  The exact position of step 4 inside the tick is not stated **[D]**.
- **When things happen:** "quarterly" = once per season, at the end of the week-11 turn, before the season advances **[C]** (decompiled-quarterly-billing-and-economy.md, city-population-growth.md). The first quarterly tick is at the wrap into Summer, 6 turns in **[C]** (decompiled-new-game-mercenary-fill.md). Rebellion runs inside the quarterly city loop (decompiled-quarterly-rebellion.md); readiness advances every tick (decompiled-mobilization-and-mercenary-restock.md); mobilization decays by 3 per quarter (city-population-growth.md) **[C]**.
- **The tick uses the season before the advance** **[D]**, from the order above: the tick ending Autumn week 11 applies Autumn rates, and Winter rates apply to the 6 ticks at the ends of Winter weeks 1–11. The weather roll explicitly uses the pre-advance season and week **[C]** (decompiled-weather-events.md, correction).
- **At the start of each human turn** (`FUN_00452034`): the trade/alliance offer roll (an OK-only box), then the debt/unity game-over test, then the 250 BC and 334-city checks **[C]** (decompiled-ai-offers-to-human-seats.md, upkeep-payment-and-desertion.md).
- **End-turn warning:** `FUN_0045af00` looks at armies that have not acted this week and clears the "ready" flag when one is under 20 % supply (`0x14`, with a further condition) or its money is below a required amount. It never blocks an AI seat **[C]** (decompiled-turn-and-calendar-sequencing.md). The harness always clicks a confirm *End turn*; whether that dialog appears every time or only on this warning is not stated.

## 2. Supply

### Fields and capacity

- **Army supplies** are army `+10`, in tons. The displayed percentage is `supplies × 10000 div troops`, i.e. percent of capacity **[C]** (supply-capacity-rounding.md).
- **Capacity by path** **[C]** (supply-capacity-rounding.md):
  - the supply dialog (`TAFSupply`): `troops div 100 + 1`;
  - every automatic path (auto-resupply, army-to-army, a battle winner absorbing supplies): `troops div 100`;
  - no cap: an instant-battle defender's win, and `JoinArmies`;
  - fleets: `ships × 8` on every path.

### Consumption per turn (per tick)

- **An army on the map** consumes `((90 − v) × troops) div 20000`, with `v` from the season table at DAT `0x1F7D8` (Spring 50, Summer 80, Autumn 80, Winter 20) **[C]** (supply-driven-morale-and-fleet-attrition.md). Troops and season are the only inputs **[C]** (supply-capacity-rounding.md).

  | Season | Per turn | 22,000 troops | 45,700 troops (Rome's two starting armies) |
  |---|---|---:|---:|
  | Spring | troops/500 | 44 | 91 |
  | Summer, Autumn | troops/2000 | 11 | 22 |
  | Winter | 7·troops/2000 | 77 | 159 |

  A full army lasts 5 turns in Spring, 20 in Summer/Autumn, **2.86 in Winter** **[D]**. Winter costs 7× Summer **[C]**.
- **An army aboard a fleet:** a flat `troops div 200` per turn, all year **[C]** (supply-driven-morale-and-fleet-attrition.md).
- **A fleet:** loses `ships` tons every turn **[C]** (same report). A full fleet (`ships × 8`) feeds only itself for 8 turns **[D]**.
- The calendar report's "at a city vs not at a city" wording is superseded: the code's branch is on-map vs aboard a fleet **[C]** (supply-driven-morale-and-fleet-attrition.md).

### Supply drives morale and moves

Applied in the same tick, on the percentage **after** consumption **[C]** (supply-driven-morale-and-fleet-attrition.md):

| Supply % after consumption | Morale `+14` | Moves |
|---|---|---|
| below 10 | −2, floored at **51** | −1 |
| 10–15 | no change (dead band) | — |
| above 15 | +1, capped at **70** | — |

- Morale falls from 70 to 51 in 10 starving turns and takes 19 turns to recover. It starts falling while supplies are still above 0, since the threshold is a percentage **[C]** (same report).
- This is the only supply-to-morale path in the binary; **starvation never kills troops** **[C]** (same report).
- Morale multiplies both strategic strengths (siege and field) and seeds each unit's tactical morale **[C]** (decompiled-unit-map-orders-and-record-fields.md, battle-quality-promotion-and-morale-array-decompiled.md).
- Mercenaries refuse to join an army under 15 % supply **[C]** (decompiled-mercenary-offer-list-and-position.md).
- Display: `moraleNames[(v − 51) >> 2]`, five tiers over 51–70 (68 reads "high") **[C]** (decompiled-unit-map-orders-and-record-fields.md, ptolemy-run-ui-inventory-and-leader-draw.md).

### How an army resupplies

1. **The supply dialog** (Unit map → Army → Supply army, `TAFSupply`).
   - **Providers:** every city within Chebyshev 1 of the army whose owner is **not at war** with you, plus your own fleets within 1 tile **[C]** (supply-capacity-rounding.md, decompiled-unit-map-orders-and-record-fields.md).
   - **Own city or own fleet:** free and immediate. Each `+10`/`+100` press moves tons, capped by the provider's stock and by `troops div 100 + 1 − supplies` **[C]** (supply-capacity-rounding.md).
   - **Foreign non-war city:** paid and staged. The amount is capped by stock, capacity and `money × 5` (the army's purse); the *Transfer* button commits it, and the army pays `amount div 5` talents to the **selling city's owner** **[C code; no save yet]** (supply-capacity-rounding.md).
   - **Money controls** move talents between the treasury and the army purse; a purse is capped at **1,000** **[C]** (decompiled-unit-map-orders-and-record-fields.md).
   - **Several cities:** an army whose tile touches two or three friendly cities can fill from each in turn **[D]** (from `FindProviders`). Splitting an army lets its parts stand next to different cities. No army record stores a "home city" or supply source **[C]** (pending-offer-block-army-split-and-naupactus.md).
2. **Automatic resupply** (`FUN_0044F6D8`) **[C code; no controlled human save yet]** (supply-capacity-rounding.md, upkeep-payment-and-desertion.md).
   - **Trigger:** a human army's move that ends against a non-hostile city fills it to `troops div 100` from that city's stock.
   - **Own city:** the fill is free; a purse over 1,000 sends the excess to the treasury; a purse under 500, with a treasury above 0, receives **500 from the treasury**.
   - **Foreign city:** at most `money div 5` tons, costing `tons div 5`.
   - The AI runs this every turn for each non-hostile city within 4 tiles, which is why AI armies rarely run dry.
3. **Army-to-army dialog:** on OK, each army's supplies above `troops div 100` are pushed to the other **[C]** (supply-capacity-rounding.md).
4. **Battle:** the winner takes the loser's supplies (capped at `troops div 100`) and money **[C]** (supply-capacity-rounding.md, ptolemy-run-ui-inventory-and-leader-draw.md).

### City supply stock (`+0x18`), per tick

**[C: 10,693 of 10,980 city-turns exact]** (city-population-growth.md):

```text
s   = pop × (v − 40) / 10              # Spring +pop, Summer/Autumn +4·pop, Winter −2·pop per turn
inc = s − s × mobilization / 200       # Rome's mobilization of 30 → ×0.85
if an at-war army is adjacent (3x3): inc = min(inc, 0)
stock = clamp(stock + inc, 0, pop × 10)
if stock == 0 and Winter and Random(3) == 0: loyalty −= 1
```

- **In Winter every city loses stock** **[D]**. A pop-23 town at a full 230 t is empty after about 6 Winter turns at mobilization 30, and Rome (pop 181, cap 1,810) loses about 308 t a turn.
- Stocks start well below the cap **[P]**: Rome 990, other Roman towns 79–243 (§10).

### What costs troops

Troops are lost only to battles, siege attempts (attacker casualties, §5), storms (armies aboard fleets, §8) and desertion (unpaid mercenaries, §3). Starvation is not on the list **[C]** (supply-driven-morale-and-fleet-attrition.md, decompiled-defection-and-siege-attrition.md, upkeep-payment-and-desertion.md). The uniform 2.5–2.85 % loss across every unit of an army that took Mediolanum **[O]** (field-recruitment-uniform-attrition-and-fleet-drift.md) is the siege-attempt rule `FUN_0044AE20` **[D]** (decompiled-defection-and-siege-attrition.md).

## 3. Treasury, taxes, upkeep, desertion

### The quarterly tick `FUN_00451b40`

In order **[C]** (upkeep-payment-and-desertion.md, city-population-growth.md):
1. upkeep: ships; army units (regulars to the treasury, mercenaries to their army's purse); city units (the 40 recruitment slots);
2. wealth and tax base zeroed;
3. city loop: population growth, wealth and tax-base rebuild, loyalty draws, rebellion;
4. nation loop: mobilization −3, income credit, trade, unity update, AI debt test;
5. relation thaw.

**The quarterly treasury change** **[C: exact for the human nation in 6 of 6 quarter pairs]** (upkeep-payment-and-desertion.md):

```text
Δtreasury = − 3 × ships (launched fleets only)
            − Σ regular army units  (troops div 200) × price[type]
            − Σ city-unit slots      (troops div 200) × price[type]   # "not ready" slots included
            + taxBase × taxRate div 100 + taxBase div 4
            − cities × 7 − wealth div 20000
            + Σ over trade/alliance partners (relation 1 or 2): partner.taxBase div 12
```

- **Quarterly price per 200 troops** (DAT unit table `+0x24`): LI 1, HI 2, Archers 1, LC 3, HC 4 **[C]** (unit-type-stat-table-in-dat.md).
- Regulars, city units and ships are billed with **no balance check**: the treasury just goes negative, and **regulars never desert**. A fleet under construction costs nothing **[C]** (upkeep-payment-and-desertion.md).
- **Tax base** (nation `+0x44C`) is rebuilt each quarter as `Σ owned cities (tribute × pop / maxPop) << 2`; **wealth** (`+0x430`) is `Σ pop × 3000` **[C]** (nation-tax-base-and-city-economy-fields.md).

### Mercenary pay and desertion

**[C]** (upkeep-payment-and-desertion.md)
- **Pay:** `((troops div 200) × price × quality) div 5` per unit per quarter, from **that army's purse** (`+12`), never from the treasury. At quality 5 that equals a regular's upkeep; at quality 9 it is 1.8×.
- **Desertion:** units are processed in slot order. If the purse is **≤ 0 when a mercenary slot comes up**, the whole unit leaves and takes `troops div 100` tons of supplies. The army's last unit is swapped into the hole and not revisited. No news line, no morale change. The purse is floored at 0 afterwards.
- **Refills:** the tick never refills a purse. Only the dialogs and the automatic +500 top-up at your own city (§2) do. A rich treasury does not stop a mercenary deserting from an empty purse.

### Debt and deposition

**[C]** (upkeep-payment-and-desertion.md)
- **The test:** `treasury < −(wealth div 500)`, or `treasury < −20000`, or `unity < 400`.
- **Human:** tested at the start of each of the human's turns; failing it **ends the game** ("Your army have deposed you because they have not been paid." or "Your unpopularity has forced the army to overthrow you.") **[C code; derived for the human]**.
- **AI:** a 1-in-9 chance per quarter of deposing the leader, which resets a negative treasury to 0.
- **Rome's debt line** is about −5,000 to −5,900. The human Rome in the saves ran at −75 to −904 without penalty **[C]**.

### Tax effects

- **Per city, per quarter** **[C]** (city-population-growth.md):
  - loyalty `+= Random(4)` if tax < 11 and loyalty < 80;
  - with a 1-in-3 chance, loyalty `−= Random(taxRate) div 8`;
  - population growth: `d = (maxPop − pop) >> 2; d −= d×tax/120; pop += d − d×mob/300 + 1`, skipped when a hostile army is adjacent.
- **Per nation, per quarter:** `unity = min(990, max(300, unity + 25 − tax/2 − mob/5))`; mobilization −3 (floor 0) **[C]** (city-population-growth.md).
- **Taxation dialog** (Strategy → Taxation, "Change tax level"): a slider with current/new tax and income; the income shown is `taxBase × tax / 100` **[C]** (decompiled-fleet-tax-and-mercenary-formulas.md, ptolemy-run-ui-inventory-and-leader-draw.md).

### Rome's economy at the start

DAT values **[P, matching nation-tax-base-and-city-economy-fields.md]**: treasury 2,200; tax 10 %; tax base 2,528 (the first rebuild gives about 2,464); wealth 2,577,000; unity 821; mobilization 30; 25 cities; capital city 85.

First-quarter estimate at 10 % tax **[D]**:

| Item | Talents |
|---|---:|
| Tax | +252 |
| Tax base / 4 | +632 |
| Cities × 7 | −175 |
| Wealth / 20000 | −128 |
| Trade (Macedonia 85, Illyria 29) | +114 |
| **Income** | **≈ +695** |
| Upkeep: army 0 (232), army 1 (221), 4 queued city units (121) | −574 |
| **Net per quarter** | **≈ +120** |

**Trade is cheap income** **[D]**. Each partner pays `taxBase div 12` a quarter. A trade is refused if the relation is negative or above 1, if you already have 3 partners, or if the target has 3 partners (unless it has a pending trade offer to you) **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md, decompiled-ai-offers-to-human-seats.md). Rome has **one free slot**. Candidates at peace with Rome, from the DAT **[P]**:

| Nation | Its trades | Income per quarter |
|---|---:|---:|
| Ptolemaic | 2 | **~513** (tax base 6,164) |
| Media | 1 | 72 |
| Thracia | 1 | 54 |
| Numidia | 0 | 37 |

Carthage (tax base 8,264) and Seleucid already have 3 trades **[P]**. An AI may drop its trade with a human to swap to a richer AI partner **[C]** (decompiled-war-cascade-and-peace-paths.md).

## 4. Recruitment, mobilization, fortification, mercenaries

### The recruitment queue

- **Storage:** 40 slots of 8 bytes at nation `+0x2E4`, words `{state, type, troops, city}`, kept as a compacted list (deleting shifts later slots down) **[C]** (decompiled-mobilization-and-mercenary-restock.md).
- **It is the garrison:** the queue is the "Units at <city>" rows of the *Army recruits* dialog and the troop count beside a city's fortification ("78% (85,000)"). There is no separate garrison pool **[C]** (city-units-army-transfer-and-mercenaries.md, decompiled-mobilization-and-mercenary-restock.md).
- **Slots cost upkeep** even when not ready, add `troops/2` to their city's siege defence, and are cleared when the city is captured **[C]** (decompiled-city-capture-resolution.md).
- **New game:** copied unchanged from the DAT (nation record `+0x2C9`) **[C]** (2026-09-29-new-game-recruitment-queues-come-from-the-dat.md).
  - **Rome**, all at city 85: LI 5,500 (state 9), HI 3,500 (13), HI 4,000 (17), HC 1,000 (17).
  - **Gaul**, at Nimes (city 45): HI 1,500 (9), LI 8,500 (13), HC 800 (15), LI 5,700 (19). Gaul appended 8 state-0 orders before the human's turn in each of three test games.

### Placing an order

`TArmyRecruits_RecruitUnit`, via Strategy → Recruit unit **[C]** (decompiled-mobilization-and-mercenary-restock.md, decompiled-recruitment-cost-formula.md):
- takes the first free slot, else refuses: "You have reached your limit of 40 units.";
- costs `(troops div 200) × initialPrice[type]` from the treasury at once;
- raises mobilization: `min(100, mobilization + 1 + troops × 1000 div wealth)`, refusing at 100 with "Your mobilisation rate is already 100%". Rome gains 3 per 6,000-troop order and 6 per 15,000 **[D]**. High mobilization shrinks city supply production (`× (1 − mob/200)`), population growth and unity **[C]** (city-population-growth.md);
- the dialog's default troop count is `standardSize / 5` **[C]** (decompiled-recruitment-cost-formula.md). The **maximum** it allows is not in any report (the #515 gap);
- **Disband** in the dialog cancels an order: `mobilization −= 1 + troops × 1000 / wealth` **[C]**. Whether the initial cost is refunded is not stated.

**Unit-type table** (DAT `0x1F2F0`, stride 40) **[C]** (unit-type-stat-table-in-dat.md, battle-replayed-rout-mechanic-and-combat-constants.md). The "full battalion" column is **[D]** arithmetic.

| Type (code), name | Standard battalion | Initial /200 | Quarterly /200 | Full battalion: initial / quarterly | Tactical moves | Shots | Range | Shot vulnerability | AI power weight |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| Light inf (0), "Foot" | 15,000 | 2 | 1 | 150 / 75 | 4 | 7 | 1 | 18 | 20 |
| Heavy inf (1), "Guards" | 6,000 | 20 | 2 | 600 / 60 | 2 | 0 | 0 | 2 | 100 |
| Archers (2), "Bowmen" | 3,500 | 4 | 1 | 68 / 17 | 4 | 25 | 2 | 18 | 40 |
| Light cav (3), "Lancers" | 7,000 | 15 | 3 | 525 / 105 | 6 | 9 | 1 | 15 | 60 |
| Heavy cav (4), "Dragoons" | 2,500 | 30 | 4 | 360 / 48 | 5 | 0 | 0 | 4 | 120 |

### Readiness and quality

- A slot starts at state 0 and gains +2 per tick, capped at 24. A mobilized unit's quality is `state / 4`, **permanently**. Quality names (DAT `0x1F6CA`): 0–3 "not ready", 4 very poor, 5 poor, 6 average, 7 good, 8 very good, 9 elite. The player may mobilize at state > 15 (quality ≥ 4); the AI waits for 24 **[C]** (decompiled-mobilization-and-mercenary-restock.md, ptolemy-run-readiness-ladder-and-mobilization-rate-confirmed.md).
- Ladder **[D]** (+2 per tick; the reports give it in weeks, state = weeks): turns 0–7 → state 0–14, not ready; turn 8 → 16, very poor; turn 10 → 20, poor; turn 12 → 24, average.
- **Rome's starting slots** **[D]**: HI 4,000 and HC 1,000 are mobilizable now (very poor) and reach 24 (average) after 4 turns; HI 3,500 is mobilizable after 2 turns; LI 5,500 after 4.

### Mobilizing

The *Mobilize* button in Army recruits, acting on the selected rows **[C]** (decompiled-mobilization-and-mercenary-restock.md, mobilization-movement-and-city-capture-modes.md).
- **Receiving army:** your army at Chebyshev **exactly 1** from the slot's city (the last one in army-index order), if it has fewer than 20 units and `troops + new ≤ 100,000`.
- **Otherwise a new army** is created on a land cell in the city's 3×3 (the last match of the scan, usually south-east) with **0 supplies, 0 money, 0 moves** (a human's cannot act that turn) and morale 59. The army cap is 198.
- **Supply a new army at once** **[D]**: at 0 % it loses 2 morale per tick.
- Mobilizing does not change the mobilization rate; placing orders does **[C]**.
- Units take the next free nation-wide ordinal per type ("3rd Foot Battalion") **[C]**.

### Which cities can recruit, and fortification (imperial_conquest_2#515)

- **No report says which cities the recruit dialog offers, or that any fortification level is required.** The dialog lists "eligible recruiting cities" **[O]** (menu-and-toolbar-inventory.md). Every observed order was at a capital, Rome (city 85) or Alexandria **[C]** (rome-city-recruitment-and-nations.md, ptolemy-run-readiness-ladder-and-mobilization-rate-confirmed.md). The gate in `TArmyRecruits_*` was not decompiled. The player's rule ("only towns with high-level fortifications can recruit") exists only in `rome-v1.md`.
- **Fortification** **[C]** (decompiled-unit-map-orders-and-record-fields.md, city-population-growth.md, decompiled-defection-and-siege-attrition.md):
  - Unit map → City → Fortify city (`TFortifyCity`); refused for a city under siege, at 100, or with an order in progress;
  - offers 0 to `100 − current` points at **`population (thousands) × points` talents**, encoded as `fort += points × 100` (a value above 100 means pending);
  - builds up to **10 points per turn** **[D]** (from `fort += min(10, fort/100)` in the tick);
  - a hostile adjacent army at the tick, or any siege attempt, cancels the unbuilt remainder;
  - adds `250 × fort` to siege defence (§5).
  - Example **[D]**: Arretium (pop 33, fort 72) to 100 costs 924 talents over 3 turns; at Rome each point costs 181.

### Mercenaries

- **Pool:** 50 fixed slots `(x, y, label, type, troops, quality)`, each on a city tile (134 template cities) **[C]** (decompiled-mercenary-offer-list-and-position.md). About 42.6 are filled at New Game **[C]** (decompiled-new-game-mercenary-fill.md). Each quarter an empty slot refills with probability 85 % and a live offer is replaced with probability 1/9. Offers have quality 5–9 and troops 1.5×–3× their template, capped at the standard battalion **[C]** (decompiled-mobilization-and-mercenary-restock.md). Labels are ethnic names (11 Gallic, 21 Ligurian, 34 Insubre, 37 Etruscan, 40 Boii…) **[C]** (decompiled-mercenary-offer-list-and-position.md).
- **Player hire** (select the army, then Unit map → Army → Recruit mercenaries) **[C]** (decompiled-mercenary-offer-list-and-position.md):
  - works only if a live offer's city tile is at Chebyshev **exactly 1** from the army; otherwise **nothing happens and no message shows**. With several, the city of the lowest-numbered live slot is used;
  - the dialog "Units at <city>" lists that city's offers (up to 10). The city can be neutral or foreign, as long as its owner is not at war with you;
  - refusals: "This army already has 20 units.", "This army cannot get any bigger." (over 100,000 troops), "You cannot recruit from an enemy city.", "No mercenaries will join an army with so few supplies." (under 15 %), and fleet capacity for an embarked army;
  - **price** `(troops × price[type] div 1000) × quality`, checked against and paid from the **army's purse** ("Your army has too little money to pay these mercenaries.") **[C code]** (decompiled-unit-map-orders-and-record-fields.md). The deduction has not been seen in a save;
  - the hired unit keeps the offer's quality and is named by its label ("Gallic"); its upkeep comes from the purse (§3).
- **AI hire** **[C]** (decompiled-mercenary-offer-list-and-position.md): the AI hires **every** live offer on any city within Chebyshev 4 of an army, when its nation is at war with someone and the army's purse is above 50. There is **no cost** and no troop, supply or fleet cap. **Gaul does this on turn 1** **[P]**: in `1.sav` its army went from 40,500 to 67,077 by hiring Insubre (11,577) and Gallic (15,000) before Rome moved.

## 5. Movement, attack, siege, capture

### Moves

- **Weekly maximum:** `moves = 10 − min(5, troops div 20000)`, −1 if supply is under 10 % (range 10 to 4) **[C: 625 of 627 records]** (army-moves-field-signed-and-the-ffff-underflow.md). Recomputed only at the tick, so an army that grows mid-turn keeps its old allowance. Unit types play no part. Examples: 23,700 troops → 9; 45,700 → 8; 100,000 → 5.
- **Set to 0 by** join, field battle (attacker), siege attempt, embark/disembark, and army creation (human) **[C]** (same report).
- The field is **signed**; `0xFFFF` = −1, an underflow bug that freezes the army until the next tick. **An army needs moves > 0 to be selected at all** **[C]** (same report).

### Walking

`TUnitMap_CheckForMove` → `MoveHumanArmy` → `FUN_0044d734` **[C]** (decompiled-army-movement-and-river-cost.md, terrain-move-cost-table-in-dat.md).
- **One click issues the whole move**, along a **straight Bresenham line** from the army to the clicked tile. Each step pays the entered tile's cost (DAT `0x1F622`):

  | Code | Terrain | Cost |
  |---:|---|---:|
  | 0 / 1 | calm / rough sea (fleets only) | 1 / 3 |
  | 2 / 3 | plain / desert | 1 |
  | 4 | forest | 2 |
  | 5 | mountains | 4 |
  | 6–11 | river | 4 |

- **For a human the walk stops at the first unaffordable step and keeps the remaining moves**; only the AI loses all its moves there. Codes ≥ 12 stop the walk: city (20–99), army (200–247) and fleet (300–347) markers, and sea for armies **[C]** (terrain-move-cost-table-in-dat.md). A straight line can end early on a mountain, river or city in the way, so the bot should click waypoints **[D]**.

### Adjacency and attack orders

- **An army never stands on a city tile.** Attack, siege, supply, mobilization and mercenary hire all work at Chebyshev 1 **[O user + C code]** (attack-and-siege-are-adjacency-orders.md, decompiled-mobilization-and-mercenary-restock.md).
- **What happens at the destination:** a hostile city → siege `FUN_0044b27c`; a friendly or neutral city → auto-resupply `FUN_0044f6d8`; an army marker → field battle `FUN_0044aee4` **[C]** (decompiled-army-movement-and-river-cost.md, supply-capacity-rounding.md).
- **Attack confirmation:** clicking an enemy city, army or fleet with your unit selected asks "Are you sure you want to attack this …?" (Yes/No). **Yes declares war** (relation 3, with the ally cascade) before the attack resolves **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md, decompiled-ai-offers-to-human-seats.md).

### Siege

`FUN_0044b27c(army, city)`, run on every attempt **[C]** (decompiled-city-capture-resolution.md, decompiled-defection-and-siege-attrition.md):

```text
atk = (Σ troops, archers ×3) div 80 × army.morale(+14)
fort := fort mod 100 if an order is pending          # the unbuilt remainder is lost
def = loyalty×150 + fort×250 + pop(thousands)×200
      × 5/3  if the city is any nation's capital and loyalty > 59
      × 4/5  if owner ≠ allegiance
      + (owner's recruitment-slot troops at this city) / 2
def = def × 9/10  if the attacker's nation is the city's allegiance
loyalty, fort, pop each = max(x×3/4, min(x×19/20+1, x×def/atk))     # erosion, win or lose
pop = max(pop, maxPop/6 + 1)
attacker casualties: every unit loses troops/(Random(15)+105) × r,  r = max(1, min(15, def×6 div atk))
   units left under standardSize/10 (regular) or /5 (mercenary) are deleted
army.moves = 0
atk > def → "<City> (<Owner>) falls to <Nation>."   else → "<Nation> fails to capture <City> (<Owner>)."
```

- Ties go to the defender, and the garrison takes no casualties **[C]**.
- **Attacker losses** **[D]**: about 4–5 % for a narrow win, about 1 % for a crushing one, about 13 % for a hopeless attempt (`def ≥ 2.5 × atk`).
- **Archers count triple in a siege** and are the cheapest unit: 68 initial and 17 a quarter for 3,500 troops **[C]** (unit-type-stat-table-in-dat.md) **[D]**.
- **Worked starting numbers** **[D]**, from the formula and the DAT values in §10:
  - defences: Taurasia 17,800; Brixia 24,100; Verona 25,550; Modena 26,200; Felsina 34,050; Mediolanum 35,450; Nimes (Gaul's capital, ×5/3 plus its 16,500-troop queue) ≈ 67,600;
  - Roman siege strength: army 0 alone (23,700 troops, morale 70) 20,720; armies 0 and 1 combined (45,700, at morale 70) 39,970.
  - **Army 0 alone takes Taurasia; only the combined force takes Felsina** (P1).

### Capture, defection cascade, conquest, rebellion

- **Capture** (`FUN_0044bb18`) **[C]** (decompiled-city-capture-resolution.md, nation-tax-base-and-city-economy-fields.md, decompiled-quarterly-rebellion.md):
  - the owner flips, the allegiance stays;
  - unity: winner +9 (cap 990), loser −15;
  - `pop × 3000` wealth and `contribution × 4` tax base move to the winner (`contribution = tribute × pop / maxPop`), and the winner's treasury gains `contribution × 4`;
  - the old owner's recruitment slots at the city are cleared;
  - loyalty becomes `min(90, 140 − L′)` if the capturer is the city's allegiance nation, else `max(40, min(60, 100 − L′))`, where `L′` is the loyalty after erosion;
  - a city stays easier to retake while owner ≠ allegiance (the ×4/5).
- **Defection cascade** (`FUN_0044ba1c`, after each capture) **[C]** (decompiled-defection-and-siege-attrition.md). Every other city of the **loser** defects to the capturer, with no battle, when all hold:
  - it is no nation's capital, and it lies at Chebyshev < 10 from the attacking army;
  - the loser's unity, after its −15, is **< 650**, and the city's loyalty is **< 65**;
  - its defence (÷3 if its allegiance is the capturer) is below the attacker's strength.

  **Gaul starts at unity 577, so cascades can fire from the first capture** **[D]**. Near Rome, Taurasia (loyalty 54) and Modena (63) are candidates **[P]**. A defected city keeps its population and fortification. The receiver's unity +3; the loser's unity −20 (floored at 250). Loyalty becomes `min(65, max(50, 100 − L))`, usually 50 **[C]** (decompiled-quarterly-rebellion.md).
- **Conquest** **[C]** (decompiled-elimination-cleanup.md): a capture that leaves the loser with **fewer than 6 cities** (or takes a capital that cannot be moved) runs `FUN_0044C528`, which annexes **every** remaining city at once ("X conquers Y."). The loser's armies and its fleets at sea are deleted with their money and supplies; fleets under construction go to the conqueror; the neighbour masks merge.
- **Rebellion** (quarterly, a non-capital city with loyalty **< 30**) **[C code; never observed]** (decompiled-quarterly-rebellion.md):
  - if owner ≠ allegiance: the city returns to its allegiance nation if that nation is alive; if it is dead, the city triggers its rebirth (which needs more than 7 disloyal cities);
  - otherwise: to a nation at war with the owner that has an army within Chebyshev 9, else to the best-placed live neighbour.

  Captured Gallic cities keep allegiance Gaul, so they would defect back to a living Gaul below 30 **[D]**. No save in the corpus ever held a city below loyalty 39 **[C]**.

## 6. Combat

### Which resolver runs

When an army attacks an army (`FUN_0044aee4`), two computer nations fight with the **instant resolver**. **Any battle involving Rome goes to the tactical screen (`TBattleMap`)**, whoever attacked. The attacker's moves become 0 **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md, 2026-09-28-battle-minigame-headless-feasibility.md).

### Tactical battle

- A 14 × 12 grid: each side places its units, then the sides alternate ("Rome to place units.", "Rome to move units.") **[O]** (full-battle-resolution-rome-vs-gaul.md, battle-observation.md). The *Computer general* button makes the AI play the human side **[C]** (2026-09-28-battle-minigame-headless-feasibility.md).
- A **computer-controlled** side gets +3 strategic morale (`+14`) on battle entry; the human side gets nothing. Each unit's starting morale is `clamp(Random(quality×4) + army.morale, 60, 90)` **[C]** (battle-quality-promotion-and-morale-array-decompiled.md).

**Melee** **[C]** (decompiled-combat-formula-structure.md, battle-replayed-rout-mechanic-and-combat-constants.md); the 40 % caps are confirmed on 11 exchanges:

```text
atkPower = M[atkType][defType] × atkTroops × (atkQuality×10 + atkMorale) / 2000 + 12
defPower = M[defType][atkType] × defTroops × (defQuality×10 + defMorale) / 2000 + 12
f = min(4, number of units attacking this defender)          # focus fire
atkLoss = min((Random(n)+Random(n)) × (5−f)/5, 30000, atkTroops×0.4) + 1,  n = atkTroops×defPower/atkPower/12 + 1
defLoss = min((Random(n)+Random(n)) × (2f+5)/5, 30000, defTroops×0.4) + 1,  n = defTroops×atkPower/defPower/10 + 1
tactical morale: +2 for the side with the better power ratio, −3 for the other (cap 99)
```

**Type-effectiveness matrix `M[attacker][defender]`** (DAT `0x1F3B8`; orientation confirmed from the index arithmetic) **[C]** (combat-type-effectiveness-matrix.md):

| Attacker ↓ / Defender → | LI | HI | Ar | LC | HC |
|---|---:|---:|---:|---:|---:|
| **LI** | 4 | 1 | 0 | 3 | 0 |
| **HI** | 1 | 4 | 3 | 3 | 4 |
| **Ar** | 0 | 1 | 3 | 0 | 1 |
| **LC** | 4 | 4 | 3 | 1 | 0 |
| **HC** | 1 | 4 | 3 | 0 | 2 |

**Caveat for P1** **[D]**: HI against LI is 1 in both directions, so the matrix alone does not make Roman HI beat Gallic LI in melee. HI's edge over LI comes from shooting vulnerability (HI 2 against LI 18), quality and morale, and the per-unit 40 % cap. In one exchange a Gallic LI (7,135) attacking a Roman HI (5,405) lost 2,855 (its cap) and inflicted 49 **[O]** (battle-replayed-rout-mechanic-and-combat-constants.md). The matrix bites in the cavalry rows (LC 4 against both infantry types).

**Shooting** **[C]** (battle-replayed-rout-mechanic-and-combat-constants.md):

```text
base = shooterTroops × quality × morale × vuln[targetType] / (shooterTroops×5 + 150000)
base ×2 if the grid distance is < range[shooterType]
r = min(shooterTroops/3, targetTroops/2, base) + 1;   loss = Random(r) + Random(r)
target morale −= min(3, loss×35/(targetTroops+1))
```

**Rout** (`FUN_00438fb0`, after every exchange) **[C]** (battle-replayed-rout-mechanic-and-combat-constants.md):
- a unit is removed below `standardSize/25` troops (LI 600, HI 240, Ar 140, LC 280, HC 100) or at morale ≤ 19; at morale 20–39 it routs if `Random(m) + Random(m) ≤ 29`;
- each rout costs every friendly unit 6 morale and removes any left under 30 (one level only), while every enemy unit gains 5;
- the loser was annihilated in both observed Rome–Gaul battles.

**After the battle** **[C]** (battle-replayed-rout-mechanic-and-combat-constants.md): the winner takes the loser's money and supplies (capped); unity moves ±25; the loser's army is tombstoned (owner −1) and compacted at the end of the turn. Promotion **[D, empirical]**: each surviving unit becomes `max(q, 6)`, then has a 1-in-4 chance of +1 (cap 9).

**Tactical battles are strongly stochastic** **[C]**: the same save replayed gave Rome losses of 36.6 % and then 24.4 % (battle-replayed-rout-mechanic-and-combat-constants.md), and the RNG is reseeded from the clock on every load (2026-09-28-battle-minigame-headless-feasibility.md). The bot's strength estimate must be a distribution or carry a margin `k` **[D]**.

**Post-battle peace:** `TBattleOver_OK` may open `TBattlePols` ("After defeating you in battle X are willing to end …"). Its gate makes any treaty accepted there the **honourable** one, with no reparations **[C]** (decompiled-war-cascade-and-peace-paths.md).

### Strategic strengths and the instant resolver

- **Used by the AI and the treaty test, not by tactical battles** **[C]** (decompiled-unit-map-orders-and-record-fields.md): field strength `(Σ weight[type] × troops/100) / 80 × morale` (weights LI 20, HI 100, Ar 40, LC 60, HC 120); siege strength `(Σ troops, archers ×3) / 80 × morale`.
- **Instant resolver (AI against AI)** **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md, instant-resolver-cannot-reproduce-a-tactical-battle.md): higher field strength wins (ties to the defender); the winner takes casualties `FUN_0044AE20` at ratio `loserPower × 40 / winnerPower` (≤ 40); the loser is deleted; with a 2-in-5 chance, if the loser has unity above 500 and more than 7 cities, peace with reparations follows. It does not reproduce tactical outcomes.

## 7. Diplomacy

- **Relations** are nation `+0x26`, 16 symmetric words: 0 peace, 1 trade, 2 alliance, 3 war; a negative value is peace with a cooldown (leaving trade writes −8, an alliance −24, ending a war −18). **Thaw:** each quarter every negative value gains +1, and with a 1-in-3 chance `v = min(0, v + 3)`. **Only columns 0–7 thaw**, a bug: a cooldown between two nations indexed ≥ 8 never decays **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md).
- **Cascade, one step only** **[C]** (decompiled-war-cascade-and-peace-paths.md): declaring war on B drags in every ally of B you are not already at war with; allying with B drags you into war with everyone at war with B.
- **Player diplomacy** (Strategy → International relations: a peace/trade/ally/war grid per nation, committed with OK) **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md, decompiled-ai-offers-to-human-seats.md):
  - peace with an AI you are at war with is refused ("X does not want to make peace at this time.");
  - trade: at most 3 partners (§3);
  - an alliance with an AI is refused while you, or an ally of yours, is at war with anyone. The AI target's own wars are **not** checked, so an alliance can drag you into them;
  - war is set directly.
- **A human–AI war ends only** when the human answers *Yes* in the post-battle `TBattlePols` dialog, or when either side is eliminated **[C]** (decompiled-war-cascade-and-peace-paths.md). So Rome cannot make peace with Gaul from the relations screen, and while at war with anyone Rome can form no alliances **[D]**.
- **The AI toward a human** **[C]** (decompiled-ai-offers-to-human-seats.md):
  - an offer is an OK-only notice ("X wants to trade with Rome.") that lapses at the next turn start and never changes a relation; to accept it, make the trade yourself;
  - the AI declares war only when it is at war with nobody, its mobilization is ≤ 40 and it is not Winter; the target borders it (neighbour mask) and is not "protected" by an ally; and `8 × P(me) / P(target) > 10`, with `P = (wealth/20000) × (unity/100)`. It then declares with a 1-in-10 chance per turn.
  - At the start, Rome's P ≈ 1,024 and Illyria's ≈ 186, so Illyria cannot declare on Rome; Carthage is busy fighting Celtiberia **[D]**.
- **Reparations** (the AI treaty's "sues" branch): `taxBase/4 + Random(taxBase/4) + cities × 10`, and the loser ends all its trades and alliances **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md, nation-tax-base-and-city-economy-fields.md).
- **Starting matrix** (DAT: 5 wars, 13 trades, 4 alliances) **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md): Rome trades with Macedonia and Illyria and is at war with Gaul. Also **[P]**: Carthage is allied with Numidia and at war with Celtiberia; Gaul trades with Celtiberia, Illyria and Dacia.

## 8. Fleets

- **Build** (Strategy → Build fleet, `TBuildFleet`) **[C]** (decompiled-fleet-tax-and-mercenary-formulas.md, decompiled-unit-map-orders-and-record-fields.md, fleet-order-at-caere.md): 10 to 100 ships; cost `ships × 10` at once; upkeep `ships × 3` a quarter once launched; troop capacity `ships × 500`. The dialog says "The fleet will be built at <city>"; **how that city is chosen is not documented**.
- **Construction** **[C]** (decompiled-unit-map-orders-and-record-fields.md, fleet-owner-field-confirmed.md): the countdown starts at 24 and drops 2 per tick, so **12 turns**, with the fleet at `(0,0)`. On launch it gets condition 100, supplies 50 and money 0; news: "<nation> finishes a new fleet at <city>."
- **Moves** **[C]** (supply-driven-morale-and-fleet-attrition.md): `30 − (ships − 50)/10`, minus `troops aboard/100/ships + 1` when carrying, −3 with 0 supplies, and `(70 − condition)>>2` below condition 70. Fleets move on sea codes 0 and 1 only (cost 1 and 3) **[C]** (terrain-move-cost-table-in-dat.md).
- **Embark** (select the army, click a friendly fleet) **[C]** (decompiled-unit-map-orders-and-record-fields.md): needs `ships ≥ troops/500` ("The army is too large for this fleet ?"); one army per fleet; both units' moves become 0; the army leaves the map (`+8 = −1`) and moves with the fleet. Disembark is `FUN_0044B840`; how a human picks the landing tile is not documented.
- **Supplying an army from a fleet:** a friendly fleet within 1 tile is a free provider in the Supply army dialog. The fleet side is Unit map → Fleet → Supply fleet, against a city or another fleet **[C + O user]** (decompiled-unit-map-orders-and-record-fields.md). A fleet holds `8 × ships` and burns `ships` a turn; a carried army burns `troops/200`. Supplying a distant army means shuttling the fleet to a port **[D]**.
- **Storms**, every turn, every launched fleet **[C]** (supply-driven-morale-and-fleet-attrition.md, decompiled-map-code1-overlay.md):

  ```text
  dmg = max(1, Random(100 − condition)/10);  Winter: min(5, dmg×2);  rough sea: min(8, dmg×3)
  not adjacent to one of its own cities: dmg = 2·dmg + 1, and in Winter a 1-in-20 spike to 30;  else dmg = dmg/2
  dmg < 6: condition −= dmg
  dmg ≥ 6: ships and condition lose d/300 each, d = (10000/(dmg+100))²/100; an army aboard takes casualties, and if d > 70 loses whole units
  condition < 40: "A fleet belonging to X is lost at sea." (the fleet and any army aboard die)
  out of supply: −3 moves and −Random(2) condition per turn
  ```

  Park fleets next to your own cities **[D]**.
- **Repair** (only at one of your own cities): `ships × points / 5` talents, and the fleet's moves become 0 **[C]** (supply-driven-morale-and-fleet-attrition.md).
- **Other orders** **[C]** (decompiled-unit-map-orders-and-record-fields.md): join (fewer than 100 ships combined, neither carrying an army), split (at least 20 ships), scuttle (only next to your own city), transfer ships (`TFleetToFleet`).
- **Naval battle** (click an enemy fleet) **[C]** (decompiled-diplomacy-peace-terms-and-instant-battles.md): strength `ships × condition/10`, plus a carried army's `siegeStrength/50`, plus a random 0–30 %. The loser sinks with its army. "You cannot attack a fleet docked at its own city !"

## 9. Weather and elimination

- **Weather** (`FUN_00451304`, every tick) **[C]** (decompiled-weather-events.md, decompiled-map-code1-overlay.md): 20 fixed sea-region centres (DAT `0x1F876`) are each rolled per tick: Spring 1/15 (radius 4) in weeks < 6, else 1/30 (3); Summer 1/40 (2); Autumn 1/30 (3) in weeks < 7, else 1/15 (4); **Winter 1/5 (5)**. A hit paints calm sea as **rough sea** (code 1) for a week. Weather affects fleets only, through movement cost and storm damage; no report ties it to armies or cities.
- **Elimination** (see §5, Conquest) **[C]** (decompiled-elimination-cleanup.md, galatia-elimination-and-city-resupply-confirmed.md): an eliminated nation shows unity 0 and capital `0xFFFF`, and its stale city count can stay above 0. An eliminated human gets the `THumanFalls` dialog and the seat turns AI.

## 10. Rome's starting position (270 BC Spring week 1)

- **Map:** 320 × 140 tiles. Rome (city 85) is at (101, 43), Carthago at (93, 78) **[C]** (map-layout.md).
- **Rome's neighbour mask** (DAT) is **{Carthage, Gaul, Illyria}**; it drives AI war targets, offers and rebellion recipients. Greece is not in it, though Greek cities lie close to Roman ones **[C]** (dat-neighbour-mask.md).

**Rome's 25 cities** **[P]** (allegiance Rome except Heraclea and Tarrentum, allegiance Greece):

| City (index) | Tile | Fort | Pop (k) | Loyalty | Stock (t) | Tribute |
|---|---|---:|---:|---:|---:|---:|
| Rome (85), capital | (101,43) | 78 | 181 | 95 | 990 | 317 |
| Pisae (71) | (93,35) | 69 | 23 | 74 | 99 | 7 |
| Tarquinii (80) | (98,39) | 56 | 27 | 78 | 119 | 11 |
| Arretium (81) | (99,36) | 72 | 33 | 95 | 150 | 19 |
| Caere (82) | (99,42) | 50 | 34 | 77 | 153 | 17 |
| Ariminum (87) | (102,33) | 52 | 24 | 77 | 104 | 7 |
| Carsioli (88) | (102,41) | 55 | 22 | 96 | 98 | 9 |
| Antium (89) | (102,46) | 69 | 33 | 92 | 146 | 14 |
| Alba Fucens (90) | (104,42) | 61 | 23 | 92 | 99 | 6 |
| Fregellae (91) | (104,44) | 61 | 23 | 81 | 105 | 13 |
| Hadria (96) | (106,39) | 62 | 18 | 89 | 79 | 6 |
| Cales (97) | (106,46) | 51 | 28 | 78 | 123 | 11 |
| Capua (100) | (108,49) | 57 | 27 | 73 | 115 | 6 |
| Neapolis (101) | (109,52) | 40 | 34 | 75 | 152 | 16 |
| Paestum (106) | (113,54) | 58 | 19 | 95 | 82 | 6 |
| Luceria (110) | (115,48) | 77 | 39 | 95 | 169 | 12 |
| Rhegium (111) | (115,63) | 44 | 27 | 65 | 119 | 11 |
| Teanum Apulum (113) | (116,45) | 58 | 24 | 76 | 106 | 9 |
| Venusia (115) | (118,51) | 61 | 31 | 95 | 132 | 7 |
| Locri (116) | (118,63) | 30 | 22 | 62 | 97 | 8 |
| Thurii (119) | (120,56) | 51 | 27 | 61 | 122 | 14 |
| Heraclea (120) | (121,53) | 46 | 31 | 50 | 139 | 16 |
| Croton (122) | (122,60) | 45 | 33 | 69 | 146 | 15 |
| Tarrentum (123) | (124,52) | 62 | 47 | 52 | 243 | 64 |
| Brundisium (125) | (127,52) | 38 | 29 | 75 | 127 | 11 |

**Rome's starting armies** **[P]**: identical in `1.sav`, `1_thracia_271_spring_1.sav` and `1_cartago_271_spring_1.sav`, so they come from the DAT. All units are regulars (quality 6 average, 7 good, 8 very good).

| Army | Tile | Troops | Units | LI | HI | LC | HC | Supplies (cap) | Money | Morale | Moves |
|---:|---|---:|---:|---|---|---|---|---|---:|---:|---:|
| 0 | (100,37), next to Arretium | 23,700 | 6 | 4,800 q6 | 5,000 q8 + 5,200 q7 + 5,900 q7 = 16,100 | 900 q6 | 1,900 q7 | 170 (237) | 100 | 70 | 8 |
| 1 | (120,53), next to Heraclea | 22,000 | 6 | 4,100 q6 | 5,500 q8 + 4,000 q7 + 5,100 q7 = 14,600 | 1,500 q7 | 1,800 q7 | 176 (220) | 100 | 68 | 8 |

Moves read 8 in the start state and become 9 after the first tick **[D]** (the session-start effect noted in supply-driven-morale-and-fleet-attrition.md). The queue is the four slots in §4 (14,000 troops). Rome has no fleets.

**Gaul** **[P]**: 28 cities, capital Nimes (city 45, at (67,33)), unity 577, mobilization 25, treasury 315. **Its only army** stands at (93,28), next to Brixia and 2 tiles from Mediolanum: 40,500 troops (LI 33,600, HI 4,900, LC 1,400, HC 600; 2 of its 8 units are the Ligurian and Spanish mercenaries). After Gaul's first AI turn it can be 67,000 (hires, §4). Gaul's cities near Rome, as tile fort/pop/loyalty: Taurasia (84,27) 22/21/54; Mediolanum (91,27) 66/37/77; Brixia (94,27) 37/18/75; Modena (95,30) 51/20/63; Verona (97,27) 45/19/70; Felsina (98,31) 68/26/79; Altinum (102,24) 21/17/69; Veldidena (100,19) 46/15/85; Virunum (106,21) 55/19/78.

**Other nations near Rome** **[P]**:
- **Carthage:** 34 cities, treasury 11,000, armies at (47,62) (33,900) and at Carthago (93,79) (18,600). It holds Aleria (90,44), Olbia (89,53), Lilybaeum (100,65) and Panormus (104,64).
- **Greece:** 21 cities, **no army**; it holds Genua (89,30), Massilia (71,36), Messana (113,63) and Syracusae (111,69).
- **Illyria:** 9 cities, **no army**, unity 690, trades with Rome: Tergeste (106,25), Salona (117,34), Scodra (128,39), Epidamnus (129,43) and others.
- **Macedonia:** 16 cities and one army of 29,800 at (144,41). **Dacia:** 8 cities, no army.

## 11. The UI, for the xdotool driver

- **Screen:** 1280 × 1024 on Xvfb `:99`; Wine 9.0 with a 32-bit prefix works **[C]** (2026-09-28-autosave-hook-feasibility.md).
- **Menu bar:** File · Game · Strategy · Nations · Area map · Unit map · Help. The toolbar icons are shortcuts to the same commands **[O + C form data]** (menu-and-toolbar-inventory.md, ptolemy-run-ui-inventory-and-leader-draw.md):

| Menu | Entries |
|---|---|
| File | New, Open, Save, Save As, Close |
| Game | End turn, New player, New nation, Abdicate |
| Strategy | News, International relations, Taxation, Balance sheet, Recruit unit, Build fleet |
| Nations | the 16 nations, All nations |
| Area map | Show cities / capital / armies / fleets / all / mercenaries (by type), Find a city |
| Unit map → Army | Supply army, Recruit mercenaries, Transfer unit, Split army, Join armies, Change units, Disband army |
| Unit map → Fleet | Supply fleet, Repair fleet, Transfer ships, Split fleet, Join fleets, Scuttle fleet |
| Unit map → City | Fortify city |
| Unit map | Cancel selection (**Shift+X**) |

**Known click coordinates** on the 1280 × 1024 screen, all tested headless **[C]** (2026-09-28-autosave-hook-feasibility.md, 2026-09-28-battle-minigame-headless-feasibility.md, `harness/*.sh`):

| Action | Clicks |
|---|---|
| File → Open | *File* (14,36), *Open* (30,72), filename field (636,450), type the name, Enter |
| File → New | (30,56), the nation's *human* tick at (109, 114 + 20 × row), OK (344,194) |
| Offer dialog OK | (638,547) |
| Game → End turn | *Game* (45,30), *End turn* (62,51), confirm *End turn* (122,307) |
| Battle | *Computer general on* (158,112); *End turn* (110,112), repeated until "Battle ended" shows; result *OK* (220,478) |

- Detect windows by title: " v " is the battle screen, "Battle ended" the result **[C]** (`harness/battle_auto.sh`).
- **Autosave:** the rollingsave build writes `AUTOnnnn.SAV` and an `AUTOSAVE.LOG` line at the start of each human turn; `nnnn` is 0720 at 270 BC Spring week 1 **[C]** (2026-09-28-autosave-hook-feasibility.md).

**How orders are given** **[C code + O user]** (decompiled-unit-map-orders-and-record-fields.md, decompiled-army-movement-and-river-cost.md, attack-and-siege-are-adjacency-orders.md, army-moves-field-signed-and-the-ffff-underflow.md):
- **Select and move:** left-click the army's marker (`TUnitMap_SelectUnit` accepts marker codes 200–247 for armies, 300–347 for fleets; the army needs moves > 0), then **click a destination tile. There is no drag**: the whole straight-line move runs on that one click. A click on sea (code < 2) is treated as a fleet move, on land as an army move (decompiled-map-code1-overlay.md).
- **Attack or siege:** with the army selected, click the adjacent enemy city or army, then answer **Yes** to "Are you sure you want to attack this …?". A fleet attacks a fleet the same way. **Embark:** with the army selected, click a friendly fleet.
- **Map ↔ screen:** no report gives the unit-map scale or the pixel-to-tile mapping. The only known grid is the tactical one (32 px per tile on a 1920-wide recording, battle-observation.md). **The bot must calibrate this** (Gaps).
- **Dialogs, as described:**
  - **Army recruits** (Strategy → Recruit unit): five type selectors, a troop-quantity control, a recruiting-city list, the units at the city with readiness words, *Initial cost* / *Quarterly cost*, and buttons *Recruit unit*, *Mobilize*, *Disband* **[O]** (menu-and-toolbar-inventory.md, ptolemy-run-ui-inventory-and-leader-draw.md).
  - **Supply army** (`TAFSupply`): provider choice (city or fleet), city and army stocks, national balance and army money, `10s`/`100s` ± steppers, *Transfer* for foreign purchases **[O + C]** (galatia-elimination-and-city-resupply-confirmed.md, supply-capacity-rounding.md).
  - **Army to army transfer** and **Split army**: two unit lists ("Units in first army" / "Units in second army") with *Transfer* and *Disband* under each, supply and money spinners (`10s`/`100s`), *OK* **[O + C]** (army-to-army-transfer-confirmed.md, ptolemy-run-ui-inventory-and-leader-draw.md).
  - **Change tax level:** a slider with current/new tax and income. **International relations:** a peace/trade/ally/war grid, one row per nation, *OK*.
  - **Army information panel:** moves, supply (tons and %), morale as a word, money, terrain, troops per type, unit count, regular cost and mercenary pay. **Enemy armies show only composition and terrain** **[C]** (ptolemy-run-ui-inventory-and-leader-draw.md).
- **Watch-outs:** interruptions come from the offer box at turn start (OK only), the battle screen opening **inside the AI seats** when an AI attacks Rome, the `TBattlePols` peace offer, and the end-turn confirmation. The mercenary order is silent when no offer is adjacent. Dialogs give little feedback, so verify every order by diffing the next save.

## 12. Open gaps for rome-v1

1. **Which cities can recruit, and at what fortification level** (imperial_conquest_2#515). Nothing in the research ties recruitment eligibility to fortification; the `TArmyRecruits` city-list gate is not decompiled; all observed orders were at capitals. The dialog's maximum troops per order is also unknown. P5 cannot be grounded yet; the pilot should log the city list the dialog offers.
2. **Map pixel ↔ tile mapping and the unit-map scroll state**, needed to click armies, destinations and cities. The 8 bytes of window geometry at the end of a save are UI state and not decoded (news-log-format-and-messages.md).
3. **Button coordinates inside the game dialogs**: Recruit, Supply, Transfer, Split, Tax, Relations, Fortify, Build fleet, the attack Yes/No box and `TBattlePols` Yes/No. Only File/Open/New, End turn, the offer OK and the battle buttons are mapped.
4. **Auto-resupply on a human move** onto a friendly city: the code says it fills to `troops div 100` and tops the purse up by 500, but no controlled human save shows it (supply-capacity-rounding.md).
5. **Foreign supply purchase**: never saved, and the money was unchanged in the one video (decompiled-unit-map-orders-and-record-fields.md). The mercenary hire deduction is not verified either.
6. **The AI general** that plays Rome's side under *Computer general* (placement, targeting) is not decompiled, so Rome's battle outcomes can only be sampled (2026-09-28-battle-minigame-headless-feasibility.md). The promotion rule is empirical.
7. **How the fleet build city is chosen**, and the disembark landing rule.
8. **Rebellion and rebirth** have never been observed; the 1-in-3 winter famine loyalty loss is code only.
9. **Whether disbanding a recruitment order refunds its initial cost.**
10. **P1's HI-vs-LI claim** is not supported by the melee matrix (1 both ways). Calibrate `k` from logged battles, not from the matrix alone.
11. **Determinism:** the RNG is reseeded from the clock on every load, so branching needs the seed patch (README; 2026-09-28-battle-minigame-headless-feasibility.md).
12. **Random turn order:** Gaul may move, hire and attack before Rome's first turn, so Gaul's army at Rome's turn 1 ranges from 40,500 to about 67,000 troops.
