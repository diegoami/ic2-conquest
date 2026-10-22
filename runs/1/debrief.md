# Run 1 debrief: Rome, rome-v2 (k = 3), 270 BC Spring week 1 → 269 BC Spring week 1

Written by the bot after the run. Every claim cites a save of run 1 (`artifacts/run-1/<season>/`, SHA-256 in `runs/1/SAVES.sha256`, copies on Drive `IC2/artifacts/run-1`). The turn files `runs/1/turns/nnnn.md` hold the plans, orders, results and battle logs; the checkpoints are in `runs/1/checkpoints/` and on issue #144.

## Outcome in one paragraph

All 24 turns were played, each in a fresh game process from its own autosave with seed `12345 + turn − 720`. No turn was replayed and none stalled. Rome destroyed **three enemy field armies**:
- Gaul's opening army (0722, 44,757), identical to run 0;
- **Carthage's landing army** (0739, 22,138), which had failed four sieges of Antium;
- **Gaul's main army of 85,664** (0743).

It took 8 Gallic cities (two by defection; peak 33 on `AUTO0736.SAV`) and lost 5 of them in Winter while the army fought in the south (4 to Gaul, Modena to Carthage). It ends on **28 cities** (25 at the start) with **44,032 troops in the field and 70,500 in the queue** (troop share 10.2 %), treasury −4,499 against a floor of −4,556, unity 875 (`AUTO0744.SAV`). Run 0, same seeds, ended with 31 cities and 17,877 troops. The rome-v2 policy (tax 25 %, recruit into debt) bought about three times the army and kept it. It cost three cities and every talent of slack, and the money ran out by Summer.

## Run 1 vs run 0 (same seeds, same start)

| Save | Run 1 cities | Run 0 cities | Run 1 field + queue | Run 0 field + queue | Run 1 treasury (floor) | Run 0 treasury | Run 1 unity / mob | Run 0 unity / mob |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `run0-start-AUTO0720-seed12345.SAV` | 25 | 25 | 45,700 + 14,000 | same | 2,200 (−4,154) | 2,200 | 821 / 30 | 821 / 30 |
| `AUTO0726.SAV` | 28 | 28 | 33,752 + 107,000 | 33,752 + 15,500 | −3,376 (−4,544) | 941 | 866 / 71 | 880 / 35 |
| `AUTO0732.SAV` | 30 | 30 | 40,493 + 107,000 | 55,192 + 10,000 | −4,262 (−4,724) | 596 | 882 / 79 | 911 / 38 |
| `AUTO0738.SAV` | 32 | 32 | 53,038 + 79,500 | 14,877 + 0 | −4,655 (−5,066) | 1,171 | 886 / 77 | 961 / ~35 |
| `AUTO0744.SAV` | 28 | 31 | 44,032 + 70,500 | 17,877 + 13,000 | −4,499 (−4,556) | 838 | 875 / 74 | 959 / 38 |

The two runs were identical to 0725, because the AI moves did not change. They diverge from 0726, when run 0 joined its armies north and run 1 kept a southern army, and above all on 0737. That turn run 0 attacked Gaul's 88,800 at ratio 3.13 and lost 73 %. Run 1 declined at 3.28, gathered the reserve, and fought Gaul's army six turns later, starving, at 5.84.

## What the debt / tax / recruit policy bought and cost

- **Bought:**
  - **110,000 troops recruited** in 23 orders (HI 8 × 6,000, archers 12 × 3,500, HC 2 × 2,500, LI 1 × 15,000) for 6,486 talents, against 9 orders in run 0.
  - Of these, **HI 36,000** (Arretium 18,000 on 0732 and 0738, Rome 18,000 on 0740) and **archers 3,500** joined the field army at quality 5–6 and kept the army's morale at 70.
  - They made the two Winter victories possible: P1 rose from 3.28 to 5.75 against the same Gallic army between `AUTO0737.SAV` and `AUTO0741.SAV`.
  - The rest (70,500) is still queued as city garrisons at the end.
- **Tax 25 %:** income about 1,050 a quarter against about 700 at 10 % (`budget.py`), so +350. Unity held at 851–903 (−20 a quarter was the forecast at mobilisation 100; at 74–81 it stayed flat because of the conquests). The tax base fell slightly (2,528 → 2,592 with more cities, against run 0's 2,676 with 31).
- **Cost:**
  - **The money ran out by Summer.** Turn 1 alone spent 3,521 (P10 room 6,354 → 2,833). By `AUTO0732.SAV` the queue's upkeep was 807 a quarter against income 1,014, so every bill was negative (−79, −194, −171), and the room fell to 462. From 0732 the bot could recruit only once more (0736, HC 360 after two conquests), so P9 was short on 9 of the last 12 turns.
  - **Mobilisation 71–81** from 0726: city supply production × 0.6. Winter stocks were still enough for one army of 45,000–63,000.
  - **The debt floor tracks wealth**, and wealth falls when towns fall. The five Winter losses raised the line by about 480 and pushed the treasury **9 below the floor on `AUTO0743.SAV`** with no spending. It was back to +57 after the Spring bill turned positive (+156) on `AUTO0744.SAV`, because the battles cut army upkeep.
  - **About 55,000 queued troops (archers 38,500, LI 15,000) never fought.** They were bought for sieges and mass, then kept out of the field army because they lower its matrix ratio (below).

## k recalibration from every logged battle (run 0 + run 1)

| Run, turn (save) | Enemy (supplies) | Rome's army | P1 ratio at battle start | Raw ratio | Rome's loss | Of which non-HI | HI loss |
|---|---|---|---:|---:|---:|---|---:|
| 0, 0722 (`AUTO0722.SAV` of run 0) | Gaul 44,757, LI-heavy (70 %) | 49,568 (LI 12,768, LC 2,400) | 5.43 | 1.11 | 36.5 % | all LI and LC died | −8 % |
| 1, 0722 (`AUTO0722.SAV`) | same | same | 5.43 | 1.11 | 36.5 % | same | −8 % |
| 0, 0737 (run 0 `AUTO0737.SAV`) | Gaul 88,800 (**the same army as run 1's 0743 battle**), 67 morale, supplied | 53,228 (HI 45,222 incl. 11,148 at q4; LI 5,116, archers 3,252, HC 3,637), morale 67 | 3.13 | 0.60 | **72.9 %** | all LI, archers and HC died | −68 % |
| 0, 0737 | Gaul army 11 (23,200) attacking a pure-HI army | 14,450 HI | 7.44 | 0.62 | 21.3 % | none | −21 % |
| 0, 0737 | Carthage attacking a lone archer army | 3,500 archers | 0.01 | 0.12 | 100 % | — | — |
| 1, 0739 (`AUTO0739.SAV`) | Carthage 22,138, HI-heavy, **0 t** | 59,038 (HI 79 %) | 4.00 | 2.67 | 23.5 % | LI −85 %, HC −20 %, archers −12 % | −18 % |
| 1, 0743 (`AUTO0743.SAV`) | Gaul 85,664, LI-heavy, **0 t** | 63,180 (HI 90 %) | 5.84 | 0.74 | 30.3 % | every LI, archer and HC unit | −22 % |

Readings:
1. **The winner was right in 7 of 7 battles; the loss size depends mostly on composition.** Every non-HI unit in a Roman army is likely to be lost whole: LI and LC in 0722, all of LI, archers and HC in 0743. HI losses run 8–22 % at ratios 4–7.
2. Between ratio 4 and 7 Rome lost 21–37 %. The one battle at 3.1 lost 73 %, and HI then lost 68 % too. The matrix ratio is not linear in losses: below about 4 they jump. **The cleanest comparison is the same Gallic army** (88,800 in run 0 at `AUTO0737.SAV`, 85,664 in run 1 at `AUTO0743.SAV`). At 3.13 (supplied, morale 67, Rome with 11,000 q4 HI) Rome lost 73 %. At 5.84 (starving, morale 64, Rome with 18,000 more HI at q6) Rome lost 30 %.
3. Both run-1 Winter battles were against armies at **0 supplies**. That likely helps (their morale was 64–68 at battle entry, near normal, so the effect, if any, is not in the morale term).

**Bot's k proposal: k = 4 for a field attack**, with the expected loss estimated as (non-HI troops) + about 20 % of HI. k = 3 only to destroy a starving army or an enemy's last army, as rome-v1's run 0 already suggested. The matrix ratio stays a good winner predictor; the raw troop ratio is not (0.74 won easily).

## What went wrong (with turns and saves)

1. **Turn-1 spending locked the year's budget.** Recruiting to the floor in the first two turns (−2,521 by `AUTO0722.SAV`) left only cheap orders afterwards, and the queue's upkeep (807 a quarter on `AUTO0732.SAV`) made every bill negative. P10's floor keeps the game alive but does not pace the spending.
2. **Composition: 12 archer orders and 1 LI order were mostly wasted.** `whatif.py` showed on `AUTO0737.SAV` that archers *lower* the matrix ratio against Gaul (3.54 with Rome's HI + archers vs 3.80 with HI alone). Against Carthage's HI army, LI is a liability: Carthage's HI scores 60 against it. The bot then kept them queued.
3. **P12, the southern army, did not work against Carthage.** The matrix gives Roman HI 5 against HI and HC 12, so a second army of 14,000 rated 0.31 against the 28,800 landing (`AUTO0730.SAV`), and even 57,500 with the whole wave would have rated 0.78. Army 9 fled north and joined army 0 (0731). What actually stopped the landing was **Rome's queue as garrison**: Antium held through four sieges (0731, 0733, 0735, 0737), and the starving army was destroyed on 0739.
4. **Towns lost in Winter:** Taurasia (0737), Mediolanum (0739), Brixia (0740), Verona (0741) to Gaul, and Modena (0742) to Carthage, while army 0 went south for the reserve and Carthage's landing. This was accepted under P8, but it cost wealth and with it the P10 margin (above).
5. **L4 by two turns:** the northern campaign stopped on 0737 (Autumn week 11), not week 9; the turns went to the Mediolanum siege (0735) and a hold (0736).
6. **L7 margin:** both winning attacks walked with 1 spare move, not 2. The bot accepted this because a failed attack would still have left the army above k (P8). Both worked.

## Harness problems

- **Mobilise into an adjacent army read as a failure** (0726): the check looked only for a new army and retried; the next rows were not ready, so nothing extra moved. Fixed in `runs/1/bot/turn.py`: a shorter queue counts as success, never retried.
- **"Battle ended" box:** now waited for (`on_dialog="no"` in the runner's `play_battle`), screenshotted and read (OCR text in `0739.result.json` and `0743.result.json`). Run 0 never caught it.
- **Supply with no adjacent own city** (0742) raised "Supply army did not open" three times. The runner should check adjacency first.
- **Walks:** `goto` needed 2 attempts on 0730, and stopped 1 tile short with 3 moves left on 0742 (the planner priced the last step higher than the moves left). The planner undercount seen in run 0 did not recur.
- New planning tools (all read-only, from a save): `budget.py` (the debt line, floor and next bill), `view.py` (one-page view), `whatif.py` (the ratio after joins with averaged morale, also for a new army), `dist.py` (an army's path cost to a tile: used for every "can it reach us" check).

## Proposals for rome-v3 (bot's words only; the player decides)

1. **k = 4** for field attacks; k = 3 only against a starving army or an enemy's last army. Count the non-HI part of the Roman army as lost when judging a battle.
2. **Field armies of HI, with HC as the second type.** HC scores 12 against HI (the best against Carthage) and costs +1 mobilisation per battalion. Archers only as many as a siege needs; no LI for the field.
3. **Pace the debt.** Spend so that the room above the floor stays positive through the **next two** bills, and keep the queue's upkeep below about 40 % of income. On top, keep about 500 talents for the wealth lost if 3–5 towns fall while the army is away.
4. **Against Carthage's landings:** no small coastal army. Keep ready recruits queued at Rome and the port cities (garrison defence), let the landing besiege and starve, and strike it at ≥ 4 when its supplies reach 0 (0739).
5. **Winter is the time to strike the starving enemy.** Both Winter kills were at 0 enemy supplies, at a cost of 23–30 %. Keep the field army fed on the Arretium–Rome line (Rome's stock 1,810 carried a 63,000 army).
6. **Mobilise recruits at state 24 (quality 6) into the field army only when it stands beside the recruiting city.** The joins kept the army's morale at 70 (0732, 0738, 0740).

## Artifacts

Saves `AUTO0721.SAV` … `AUTO0744.SAV`, per-turn screenshots, two battle screenshots, `AUTOSAVE.LOG` / `SEED.LOG` copies: `artifacts/run-1/{270BC-spring,270BC-summer,270BC-autumn,270BC-winter,269BC-spring}/`, all hashed in `runs/1/SAVES.sha256`, copied to `gdrive:IC2/artifacts/run-1`. There is no release (the brief said so).
