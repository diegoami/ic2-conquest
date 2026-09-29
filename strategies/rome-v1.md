---
id: rome-v1
nation: Rome
author: player (diegoami), 2026-09-29
status: proposed          # proposed -> accepted -> in-trial -> validated | refuted | revised
start: new game, Rome human, default DAT (270 BC Spring week 1)
parent: none
---

# Rome: take the neighbours, keep the armies fed, then the three hard ones

## Player's intent (in the player's words, not edited by the bot)

Rome can easily defeat the countries near it, provided it manages and combines its armies well and never forgets to supply them. The game is seasonal: in winter the armies have to go back to towns where they can be supplied. After most of Europe is conquered, the tough ones are Carthage, the Seleucids and the Ptolemies, which take back and forth to defeat.

*Added 2026-09-29, after reviewing the first draft:*

There are no "garrisons" in the game. Only towns that are recruiting soldiers have garrisons, and those are difficult to take, and there are few of them. Only towns with high-level fortifications can recruit. You can build fortifications to make sure that more towns can recruit.

Recruiting is important from day one, because Rome at the beginning does not have enough troops even to defeat the Gauls.

Mercenaries are nice to have, but remember that your armies need money too.

Another principle is that you use fleets to supply armies far from home.

Not only army size is important, but also army composition. The Gauls, for instance, have bigger armies than Rome, but Rome's heavy infantry defeats the Gauls' light infantry.

Winter is not so easy: in winter towns have little supply too. Your army has to retreat to friendly territory where it can draw supply from several cities, sometimes even splitting so that smaller detachments can each be supplied from different cities. Supply is important for morale.

Relax the rule about fortifications: build fortifications only with a purpose, in towns near to where you want your armies to be. They are expensive.

## Principles (checkable rules the bot must follow)

| # | Principle | How the bot checks it from the save |
|---|---|---|
| P1 | Combine armies before attacking; do not attack with small detachments. Judge strength by **composition**, not headcount: Roman heavy infantry beats Gallic light infantry even when outnumbered | every attack order: the attacker's matchup-weighted strength ≥ the defender's × k (k to calibrate). Strength is computed per unit type with the research repo's type-effectiveness matrix (DAT `0x1F3B8`, `combat-type-effectiveness-matrix.md`) and power term (`troops·(q·10+morale)`), not from raw troops. Raw troop ratios are logged too, to show the difference |
| P1b | Recruit the composition that beats the next enemy | recruitment orders are logged by type, with the enemy they are meant for. Against Gaul (light-infantry-heavy), heavy infantry first |
| P2 | Never let an army run out of supply; supply keeps morale up | per turn: every Roman army's supplies ≥ its weekly consumption × turns until it can next resupply; the army morale field (`+14`) is logged per army, per turn |
| P3 | Winter: before winter, pull the armies back into friendly territory where several own cities can feed them; split an army when one city cannot | at the Autumn week 11 checkpoint: for every army, the supply its reachable own cities can give over winter ≥ its winter consumption. An army that fails this is split or moved, and the plan says which |
| P4 | Recruit from day one; Rome starts too weak even for Gaul | the recruitment queue is never empty in the first year; the number of new slots per turn is logged |
| P5 | Fortifications are expensive: build them only with a purpose, in towns near where the armies need to be, so those towns can recruit close to the front | every fortification order names its purpose (which campaign, which army it will reinforce) in the turn plan; no fortification order without one. Spending on fortifications is logged per season against treasury. **A town can recruit if it is the capital or its fortification is ≥ 75%** (research report `2026-09-29-which-cities-may-recruit-and-troop-amounts.md`); only 23 of 334 towns start at that level. **An order costs the town's population per point, paid up front; it builds at most 10 points a turn; an adjacent enemy army cancels it without refund. Order to 75%, never to exactly 100% with a remainder (a known bug resets the town to 0%)** (research report `2026-09-29-fortification-orders-cost-rate-and-the-100-bug.md`). At the start Rome can recruit at Rome and Luceria (77%); Arretium, Pisae and Antium reach 75% in one turn for 99–198 each. **The AI never fortifies**, so its recruiting towns stay fixed, while Rome's can grow. All of this is confirmed live |
| P6 | Mercenaries only when the money is there: armies need money too | before hiring: treasury after hiring ≥ the armies' upkeep for the next N turns (N to calibrate; upkeep as in the research repo's `upkeep-payment-and-desertion.md`) |
| P7 | Use fleets to supply armies far from home | an army more than a set distance from any own city has a fleet supply route in the plan; the supply transfers are logged |

## Phases and milestones

| Phase | Goal | Milestone (checked in the save) | Deadline (to calibrate after run 1) |
|---|---|---|---|
| 0 | Build up first | recruitment running from turn 1; the combined field army is stronger (by composition) than Gaul's largest army | end of 270 BC summer (to calibrate) |
| 1 | Secure Italy and the nearest neighbours | Rome owns every city of the nearest neighbour nations | end of 269 BC |
| 2 | Most of Europe | Rome owns ≥ 50% of cities west of Greece | end of 266 BC |
| 3 | Carthage | Carthage eliminated or reduced to ≤ 2 cities | open |
| 4 | Seleucids and Ptolemies | both eliminated or reduced to ≤ 2 cities | open |
| — | Domination | Rome owns ≥ 75% of the 334 cities | open |

## Open questions the player may answer before the run

- Which neighbour first: Gaul, Celtiberia, Illyria, Greece or Macedonia?
- Diplomacy: make peace or trade with the far nations while fighting the near ones?
- Fleets: when does Rome start building them for Carthage?
- Taxes and recruitment: what level is sustainable in the first year?

## Rules the bot still needs from the research (before or during run 0)

- ~~The fortification level a town needs to recruit, and the dialog's troop amounts~~ **Answered (#515):**
  - a town can recruit if it is the capital or its fortification is ≥ 75%; otherwise the refusal is `This city's fortification has fallen below 75%.`;
  - the other refusals are `You have reached your limit of 40 units.` and `Your mobilisation rate is already 100%.`;
  - the dialog amount runs from battalion/5 (the default) to the full battalion (LI 15,000, HI 6,000, archers 3,500, LC 7,000, HC 2,500), in steps of 100 and 1,000;
  - recruiting has no treasury check, so the treasury can go negative; P6's money discipline matters.

  See the research report `2026-09-29-which-cities-may-recruit-and-troop-amounts.md`.
- ~~The cost and build time of fortifications~~ **Answered:** population × points, paid up front, at most 10 points per turn. See the research report `2026-09-29-fortification-orders-cost-rate-and-the-100-bug.md`.
- How composition decides a battle in each path. A battle with a human side is tactical (grid battle, the type matrix per exchange). A battle between two computer nations uses the instant resolver, which compares a per-type power weight (unit-type table `+0x26`). The bot's strength estimate should match the tactical path, since Rome is human. The battle golden-master plan in the research repo would make that estimate exact.
- The winter supply each city gives (the seasonal supply table is in the research repo), and how an army draws supply from several cities.

---

## Bot validation (written by the bot before the run)

Written 2026-09-29 for run 0. Rules are cited from `docs/rules-digest.md` (research repo at `60475a30`) and this repository's `findings/`. Numbers for the start position come from `BASE.SAV` (new game, Rome, seed 12345, 270 BC Spring week 1, turn 0720).

### How the bot understood rome-v1

Build up from turn 1 (recruit and fortify with a purpose), bring Rome's two field armies together before any attack, and take Gaul's cities nearest Italy first, choosing units by what beats the Gauls. Keep every army fed, and before winter bring the armies home to where several Roman cities can feed them, splitting them if needed. Hire mercenaries only when the army purses can pay them. Fleets carry supply to distant armies later; they are outside the pilot.

### What the researched rules support, principle by principle

| # | Supported by | What it means in numbers at the start | Gap or risk |
|---|---|---|---|
| P1 | Siege strength is `(Σ troops, archers ×3) div 80 × morale`; siege defence `loyalty×150 + fort×250 + pop×200` (+capital, +queued troops/2). Field battles with Rome are always tactical (grid battle, *Computer general*). | Army 0 alone: 20,720; armies 0 + 1: 39,987 at morale 70. Felsina defends 34,050, Mediolanum 35,450, Modena 26,200, Taurasia 17,800. **Only the combined army takes Felsina**; army 0 alone failed there in the test (`T_ATTACK.SAV`, −8.2 %). | For sieges, composition matters only through archers (×3). For field battles, the melee matrix rates HI against LI **1 both ways**: HI's edge over Gallic LI comes from shooting vulnerability (HI 2 vs LI 18), quality and morale. One recorded exchange (Gallic LI 7,135 into Roman HI 5,405) cost the Gauls 2,855 and the Romans 49. The margin `k` must be calibrated from logged battles. |
| P1b | Unit table: HI 6,000 per battalion, 600 initial, 60 a quarter; archers 3,500, 68 initial, 17 a quarter, 25 shots at range 2. | Gaul's field army is 40,500, of which 33,600 LI (quality 5–6). | **Proposed addition (bot):** archers alongside HI. They are the cheapest unit, count triple in a siege and shoot LI hard. The player decides. |
| P2 | Consumption per turn `((90 − v) × troops) div 20000`, v = 50/80/80/20 (Spring/Summer/Autumn/Winter); capacity `troops div 100`; morale −2 below 10 % supply, +1 above 15 % (cap 70). | Spring: army 0 eats 47 t a turn of a 237 t capacity (5 turns); Summer/Autumn 11–12; Winter 82. | Free top-up from an adjacent own city via *Supply army*; the automatic resupply at the end of a move is in the code but never confirmed on a human save: the pilot checks it. |
| P3 | In Winter every city **loses** 2×pop tons of stock a turn; armies eat 7× their Summer rate. | Rome (pop 181) loses ~308 t a turn in Winter; a 22,000-troop army needs ~77 t a turn. | How much the reachable cities can give must be computed from their stocks at Autumn week 11 (checkpoint 0737). |
| P4 | Recruitment queue: 40 slots, readiness +2 a turn, quality `state/4` at mobilization (≥ 16 to mobilize, 24 = average). An order costs `troops div 200 × initial price` and raises mobilization by `1 + troops × 1000 div wealth`. | Rome starts with 4 queued units (14,000): HI 4,000 and HC 1,000 reach average on turn 0724, HI 3,500 on 0726, LI 5,500 on 0728. | High mobilization cuts city supply production (× (1 − mob/200)) and unity. |
| P5 | **Resolved by this repo** (`findings/2026-09-29-recruiting-cities-need-fortification-75.md`, from the code at `0x454582`): a city can recruit if its **fortification is ≥ 75**, or it is the capital, or it already holds a queued unit. Fortifying costs `pop (thousands) × points` and builds ~10 points a turn. | At the start only Rome (78, capital) and Luceria (77) can recruit. Arretium (72), next to the Gallic front, needs 3 points: **99 talents**. | The maximum troops per recruit order is still unprobed. |
| P6 | Mercenary hire costs `(troops × quarterly price div 1000) × quality` **from the army's purse**; pay `((troops div 200) × price × quality) div 5` a quarter from the purse; an unpaid mercenary deserts at the quarter with its supplies. | The Samnite LI offer at Heraclea (3,868, quality 8), adjacent to army 1: 24 talents, then 30 a quarter. Army purses start at 100. | N for "the armies' upkeep for the next N turns" is set to one quarter (6 turns) for the pilot. |
| P7 | A fleet within 1 tile is a free supply provider; fleets hold `ships × 8` t and eat `ships` a turn; build takes 12 turns, `ships × 10` talents. | — | Out of the pilot's scope (Gaul is reached overland). |

### Gaps that could break the plan

1. **Battles are stochastic and the Roman side is played by *Computer general*.** The same battle replayed gave Rome 36.6 % and 24.4 % losses. Fixed seeds make each turn repeatable but do not make a battle predictable before it is played.
2. **Seat order**: in this game Rome moves 12th of 16 and Gaul 15th, so Gaul answers every Roman move in the same round. Gaul, at war, hires every mercenary offer within 4 tiles of its army for free; its 40,500 can grow.
3. **Defection cascade**: Gaul's unity is 577 (< 650), so the first capture can make nearby low-loyalty Gallic cities defect (Taurasia 54, Modena 63), if their defence is below the Roman army's strength.
4. **Orders not yet driven** (each gets a headless save-diff test before its first use in the run): supply army, join armies, mobilize, hire mercenaries, fortify city, international relations. Move, attack (siege), recruit and end turn are done (`tests/results.md`).

### Test plan

Run 0 is the pilot: 24 turns (270 BC Spring week 1 to Winter week 11, autosaves 0720–0744), every season a checkpoint in the run's issue, and the Autumn week 11 winter check (turn 0737). Each turn is played from its own autosave in a fresh game process with a recorded seed (`12345 + turn − 720`), so any turn can be replayed exactly. The baseline comparison comes after the pilot.

## Trials

| Run | Turns | Result | Debrief |
|---|---|---|---|
| — | — | — | — |
