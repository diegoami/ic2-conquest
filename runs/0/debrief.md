# Run 0 debrief: Rome pilot, rome-v1, 270 BC Spring week 1 → 269 BC Spring week 1

Written by the bot after the run. Every claim cites a save of run 0 (`artifacts/run-0/<season>/`, SHA-256 in `runs/0/SAVES.sha256`); the turn files `runs/0/turns/nnnn.md` hold the plans, orders, results and battle logs.

## Outcome in one paragraph

All 24 turns were played, each in a fresh game process from its own autosave with seed `12345 + turn − 720`, and no turn stalled. Rome destroyed **all three Gallic field armies** (0722 and twice on 0737), took or received **7 Gallic cities** (Brixia, Modena, Verona, Altinum, Felsina, Mediolanum, Taurasia) and lost one (Taurasia, to Carthage on 0743). It ends on **31 cities** (25 at the start), treasury 838, unity 959 (`AUTO0744.SAV`). The price was the army: 45,700 troops at the start, a peak of 57,228 (`AUTO0731.SAV`), and **17,877 at the end**, after the 0737 battle against Gaul's 88,800 cost 73 % of the field army. Carthage declared war on 0727-0728, landed 28,800 troops in North Italy on 0737, and ends the run with two starving armies in Italy that Rome is too weak to attack.

## Curve (Rome)

| Save | Cities | City share | Troops | Troop share | Treasury | Unity |
|---|---:|---:|---:|---:|---:|---:|
| `run0-start-AUTO0720-seed12345.SAV` | 25 | 7.5 % | 45,700 | 10.1 % | 2,200 | 821 |
| `AUTO0726.SAV` | 28 | 8.4 % | 33,752 | 11.7 % | 941 | 880 |
| `AUTO0732.SAV` | 30 | 9.0 % | 55,192 | 15.8 % | 596 | 911 |
| `AUTO0738.SAV` | 32 | 9.6 % | 14,877 | 4.1 % | 1,171 | 961 |
| `AUTO0744.SAV` | 31 | 9.3 % | 17,877 | 4.5 % | 838 | 959 |

## What worked

- **Defeat the army first, then the cities** (owner's rule). Gaul's opening army was destroyed on 0722 (`AUTO0723.SAV`); after that every siege was against an undefended city, cost 3.6-4.4 % and succeeded, and two cities defected (Modena 0723, Taurasia 0733) because Gaul's unity was under 650.
- **Combine before attacking (P1).** Felsina (34,050) and Mediolanum (35,450) fell only to the combined 57,228 army with archers (siege strength 48,922; archers ×3). The army waited three turns for it (0728-0730) instead of failing sieges with 36,000.
- **Archers in sieges** (owner's yes): 3,500 archers add 7,000 to the siege sum, the cheapest siege strength there is (68 talents).
- **Front-city fortification (P5):** Arretium +3 (99 talents) on 0720 made it a recruiting city from 0721 on; it produced HI 6,000 and two archer units.
- **Supply discipline (P2):** every army was supplied when beside an own city; the only shortfall was army 0 at 31 % on 0743 (the winter drain, below).
- **Trade:** three partners most of the time (Illyria and Numidia from 0720, Celtiberia briefly, Armenia from 0723, Galatia from 0732). Ptolemaic refused on 0721 and 0722 as the owner asked to try.
- **Harness:** 24 turns, about 2 minutes each, with every order verified from game memory. A turn can be replayed exactly (0724 was replayed after a wrong click).

## What the principles predicted vs what happened

| Principle | Prediction | What happened |
|---|---|---|
| P1 (matrix strength) | HI crushes LI; ratio ≥ k wins | **The winner was right in 4 of 4 battles**, but the loss rate was not: 36.5 % at ratio 5.43 (0722), **72.9 % at 3.13** (0737), 21.3 % at 7.44 (Gaul attacking a pure-HI army, 0737). Rome's light infantry and light cavalry died first in every battle; the HI survived and was promoted (q8-q9). |
| P1b | HI first against Gaul | Right against LI; but Gaul's late armies brought archers (7,000) and cavalry, and the big 0737 battle was still a near-pyrrhic win. |
| P2 | Supply keeps morale | Morale stayed 60-70 all run; no army fell below 10 %. Joining recruits (morale 59-62) into the veterans (70) dropped the field army's morale to 61-63 (`AUTO0730.SAV`), which costs siege strength in proportion. |
| P3 | Winter: several cities feed an army | The 0737 plan counted 2,520 t in North Italy. In practice **winter emptied Taurasia and Mediolanum by 0742** (`AUTO0743.SAV`: stocks 0, 0, others 10-36 t) while an army of only 11,377 drew from them; a 53,000 army would have starved. The fix used on 0743 (walk past three cities and draw from each) worked. |
| P4 | Recruit from day one | The queue was never empty; 9 recruit orders, 7 mobilizations. Recruits reach quality 4 only after 8 turns (state 16) and average after 12. |
| P6 | Mercenaries cost the purse | The Samnite LI (0720) took nothing from the purse and died in the first battle before any pay was due. |

## k calibration (P1), from the logged battles

| Battle (save) | P1 ratio | Raw troop ratio | Rome's loss |
|---|---:|---:|---:|
| 0722 Rome attacks Gaul (`AUTO0723.SAV`) | 5.43 | 1.11 | 36.5 % (all LI/LC) |
| 0737 Rome attacks Gaul (`AUTO0738.SAV`) | 3.13 | 0.60 | 72.9 % |
| 0737 Gaul attacks Rome (`AUTO0738.SAV`) | 7.44 | 0.62 | 21.3 % |
| 0737 Carthage attacks Rome's archers (`AUTO0738.SAV`) | 0.01 | 0.12 | 100 % |

The matrix ratio orders the battles correctly, but Rome's losses are much higher than the ratio suggests. **Bot's proposal: k = 5 to attack** (to lose under about 40 %), and k ≈ 3 only for a battle that ends a war. The raw troop ratio is a poor guide (0.60 won), as the player said.

## What went wrong (with turns and saves)

1. **0737: attacking Gaul's 88,800 at ratio 3.13** with k = 1.5 (`AUTO0737.SAV` → `AUTO0738.SAV`). Gaul's army was destroyed but Rome's field army fell to 14,450, and Rome lost its campaigning power just as Carthage landed. Waiting for the 0738-0740 recruits, or letting Gaul's starving army come to Rome's cities in winter, would have kept the army.
2. **0736-0737: an archer army walked alone** to join the field army and was destroyed by Carthage's landing (`AUTO0738.SAV`). A lone detachment broke P1's spirit.
3. **0725: a siege click with 0 moves** did nothing (`AUTO0726.SAV`): the walk cost 9 moves where the planner said 8 (river step). Fixed: 2-move margin, attack effect checked.
4. **0724: the wrong recruit-list row** (an "All cities" row appears once two cities hold queued units). The turn was replayed from `AUTO0724.SAV`; rows are now found by their caption.
5. **0743: Taurasia (loyalty 50) fell to Carthage** (`AUTO0744.SAV`). Recently taken cities have low loyalty and defence (12,000-20,000), and no garrison.

## Harness problems

- Refusal boxes of International Relations OCR to an empty string (the refusal is still seen from the relation value).
- `planner/path.py` undercounts some walks across rivers by one move (0725, 0727).
- Army ids are renumbered when armies merge; the bot re-reads ids from every save.
- `play_battle` does not return the "Battle ended" text unless `on_dialog` is set; the battle log reads the armies from memory before and after instead (`runs/0/turns/*.result.json`, `battles`).
- `harness/environment` wrote `runs/0/environment.jsonl` (kept as a measurement).

## Proposals for rome-v2 (bot's words only; the player decides)

1. **P1 margin k = 5** for field attacks (k = 3 only if the battle ends the enemy's last army), and compute the ratio after any joins (morale dilution).
2. **Never march a unit alone within an enemy army's reach** (enemy moves + 1); mobilize recruits where the field army can absorb them, or keep them in the queue (queued troops add half to the city's siege defence).
3. **Winter plan by stock, not by city count**: assume every city loses 2×pop a turn from Winter week 1; plan the army's route past several cities and stop campaigning by Autumn week 9.
4. **Garrison the frontier with queued units or a small army**, and fortify one captured city (purpose: hold the conquest against Carthage's landings), since newly taken cities defend at 12,000-20,000.
5. **Plan for Carthage from Summer**: Carthage declared war in Summer week 3-5 (also seen in `findings/` B11 with seed 12345). Rome needs a second army in the south, or an early peace offer, before its field army goes north.
6. Tax: 10 % kept the treasury between 435 and 2,200; recruiting was limited by money from 0731 on. A test of 15-20 % in a branch would show whether the extra income is worth the loyalty cost (captured cities are already at loyalty 41-55).
