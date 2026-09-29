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

Winter is not so easy: in winter towns have little supply too. Your army has to retreat to friendly territory where it can draw supply from several cities, sometimes even splitting so that smaller detachments can each be supplied from different cities. Supply is important for morale.

## Principles (checkable rules the bot must follow)

| # | Principle | How the bot checks it from the save |
|---|---|---|
| P1 | Combine armies before attacking; do not attack with small detachments | every attack order: attacker troops ≥ defender troops × k (k to calibrate, start at 1.5) |
| P2 | Never let an army run out of supply; supply keeps morale up | per turn: every Roman army's supplies ≥ its weekly consumption × turns until it can next resupply; the army morale field (`+14`) is logged per army, per turn |
| P3 | Winter: before winter, pull the armies back into friendly territory where several own cities can feed them; split an army when one city cannot | at the Autumn week 11 checkpoint: for every army, the supply its reachable own cities can give over winter ≥ its winter consumption. An army that fails this is split or moved, and the plan says which |
| P4 | Recruit from day one; Rome starts too weak even for Gaul | the recruitment queue is never empty in the first year; the number of new slots per turn is logged |
| P5 | Build fortifications so that more towns can recruit | fortification build orders are logged per city; the count of Roman towns able to recruit is tracked per season. The threshold is **not yet known** (see below) |
| P6 | Mercenaries only when the money is there: armies need money too | before hiring: treasury after hiring ≥ the armies' upkeep for the next N turns (N to calibrate; upkeep as in the research repo's `upkeep-payment-and-desertion.md`) |
| P7 | Use fleets to supply armies far from home | an army more than a set distance from any own city has a fleet supply route in the plan; the supply transfers are logged |

## Phases and milestones

| Phase | Goal | Milestone (checked in the save) | Deadline (to calibrate after run 1) |
|---|---|---|---|
| 0 | Build up first | recruitment running from turn 1; first fortifications started; the combined field army is stronger than Gaul's largest army | end of 270 BC summer (to calibrate) |
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
- Which towns to fortify first: those closest to the front, or the richest?

## Rules the bot still needs from the research (before or during run 0)

- **The fortification level a town needs to recruit, and the troop amounts the recruit dialog allows** (imperial_conquest_2#515, open). P5 cannot be planned exactly until this is known. In the pilot the bot records which towns the dialog offers.
- The cost and build time of fortifications.
- The winter supply each city gives (the seasonal supply table is in the research repo), and how an army draws supply from several cities.

---

## Bot validation (written by the bot before the run)

- **Understood as:** the principles and phases above, turned into per-turn constraints and milestones.
- **Supported by the rules as researched:** supply, seasons and winter attrition are documented in the research repo (weekly tick, supply capacity `troops div 100 + 1`, upkeep and desertion, supply-driven morale). Gaps that could break it: the recruitment and fortification rule (P5), and how an army draws supply from several cities (P3).
- **Test plan:** pilot run of 24 turns (one year) with checkpoints every season; baseline comparison later.

## Trials

| Run | Turns | Result | Debrief |
|---|---|---|---|
| — | — | — | — |
