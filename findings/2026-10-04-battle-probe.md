# One tactical battle end to end (battles plan, B0): the screen, Save As inside a battle, the lab build's 57-second repeatable battle, resume, and the post-battle "Offer of peace" box

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** Natural state: nothing edited, one start save, one pair of armies. It is task **B0** of `docs/proposals/battles.md`; saves and screenshots are in release `run-exp-battle-probe`, the logs under `runs/experiments/data/run-exp-battle-probe/`. Results are labelled **normal** (the `fast rollingsave seed` build, seed 12345 in `SEED.TXT`) or **lab** (`patches/battle_lab.py`, seed baked in, one `BATTLEnn.SAV` per half-round).

**Answer.**
- **The gate passes.** Six lab battles in a row (seed 1) completed headless with one End turn click each, and **all six `BATTLEnn.SAV` series (15 files each) and all six post-battle saves are byte-identical**. A lab trial takes **57.3 s on average (56.9 to 57.4)** from process start to the post-battle save.
- **Item 2: Save As inside a battle works through the File menu** (not through the toolbar Save, which does nothing in a battle). The file carries **block 12** (battle flag 1, 2,105 more bytes), the battle window stays open and the battle continues. It needs human control: with Computer general **on**, the battle runs at the next input event, before any dialog opens.
- **Item 4: File → Open of a mid-battle `BATTLEnn.SAV` resumes the battle** (lab) in about 2 s, **but the remaining half-rounds are NOT byte-identical to the original's.** Two resumes of the same save are identical to each other, so a resumed battle is deterministic given (save, seed); it is not a continuation of the original random stream (the plan's "[R]" claim is contradicted).
- **A post-battle box opens in some battles, and it is not the battle-ended box:** an **"Offer of peace"** window (title, text and two buttons below, the `TBattlePols` of the plan) appeared after OK in 3 of the 17 logged battles (16 human defeats and one victory): two lab seed 2, one lab seed 1 with Rome idle; never after the other 13 defeats or after the victory. It was captured, left open, and answered No.
- **A post-battle Save As carries the battle's news** ("Gaul destroys army of Rome.", "Rome destroys army of Gaul."), so an End turn is not needed to read the result.

## Method

- **Start save:** `1_rome_270_winter_11.sav` (release `run-1-rome` of `imp_conquest_fixtures`, downloaded as the research session said). Inspected with `state/sav.py`: Rome's turn, **turn 0743** (Winter week 11, 270 BC), **battle flag 0, no block 12**, so loading it opens the strategic map, not a battle. Rome's army 0 (37,081, nine units: HI 2,094, Ar 3,411, HC 2,337, LI 5,895, Ar 789, Ar 3,317, LC 4,421, LI 13,697, LI 1,120) is at (92,27) with 8 moves, army 13 (38,455) at (93,28); Gaul's army 10 (46,700, five units: LI 14,400, HI 5,900, LI 14,500, LI 6,900, HI 5,000) is at (85,28); Rome and Gaul are at war (relation 3). The save is **not** one attack away: the probe walks army 0 to (86,28) in three legs (cost 6 of 8 moves, `planner/path.py`) and attacks (85,28). The `FLD-RG` fallback was not needed. The save opens with a modal box ("Bithynia wants to trade with Rome.").
- **Probe:** `runs/experiments/battles/b0_probe.py` (commands `normal`, `savein [lab]`, `lab SEED TAG`, `gate`, `resume SEED TAG NN`, `win`, `compare`) and `b0_peace_capture.py` (run once against the box a stopped trial left open). Nothing is auto-answered: the attack is a bare click, `dismiss_popups` is not used after it, every window is listed every 0.5 s. Every step logs to `b0-*.log`/`.jsonl`; screenshots and saves are kept under new names, never overwritten.
- **Builds:** normal `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`); lab exes built with `PYTHONPATH=$IC2_WORK/build python3 patches/battle_lab.py <seed>` and renamed `Imperial Conquest 2 lab s<seed>.exe` (the driver finds the pid by the name prefix): seed 1 `06bc469d…c40`, seed 2 `6616a7cc…60a`; all hashes in `EXES-sha256.txt` (the exes are not in git or in the release). Wine 9.0, Xvfb 1280x1024, one process per trial.
- **Driver deviations (probe only, `harness/driver.py` unchanged):** with this save the unit map opens **1143 × 903 px** (29 × 27 tiles in view, not 13 × 13), so the probe sets `VIEW_COLS/ROWS` to 29/27; and the driver's `NEUTRAL` click point (1000, 900) lies **on the unit map**, so `reset_ui` (called by every `menu()`) **orders a move for a selected army**: the first normal attempt's Save As moved army 0 from (86,28) to (86,30) and cost it its 2 remaining moves. The probe uses (700, 1005), bare root. `Game.open` times out on a save that pops a modal box (the main window's title only gets "turn" after the box is closed), so the probe opens the file itself.

## Observations

### Item 1: the normal build, nothing auto-answered (seed 12345)

Files: `NB_pre_attack-20261004-081149.SAV` (staged, before the attack), `NB_post_battle.SAV`, screenshots `b0-normal-20261004-081149-0*.png`, log `b0-normal-20261004-081149.log`.

| what | observed |
|---|---|
| click on Gaul's tile → battle window | **6.7 s** (6.72 normal, 6.66 to 6.69 lab); `in_battle` (flag `0x4A0B7C`) = 1 |
| title at open | `Rome  v  Gaul          Rome to place units.` |
| windows | battle window **(5,99) 448 × 414**; its own `Information` panel (458,70) 338 × 426; the Area map, Unit map and strategic Information windows are unmapped for the whole battle. The battle window was on top in every battle of the probe (no stacking failure; `xdotool search` does not give the order, so only geometry was recorded) |
| `Game.controls` of the battle window | **one control**: a `TPanel` (5,99) 448 × 28, the toolbar strip; the grid is not made of controls |
| tooltip scan (x 5 to 455 step 3, y = 112) | **8 buttons**: Unit moves (x 8-17), Friendly units (35-44), Enemy units (59-68), Cancel selection (83-92), **End turn (110-119)**, Change pauses (137-146), **Computer general on (161-170)**, **Surrender (188-197)**; nothing from 198 to 455 |
| Computer general click | title becomes `Rome  v  Gaul          Rome to move units.` (placement is done for us), `in_battle` still 1 |
| battle | **1 End turn click** in all 16 logged defeats; the "Battle ended" box is up about 3 to 4 s after the click. In the one human victory (`WIN_post_battle.SAV`) the Computer general click alone ended it (0 End turn clicks): the loop must test the flag before clicking |
| "Battle ended" box | window (13,94) 450 × 445; `Game.controls`: **one `TButton` "OK"** (203,499) 70 × 25 (the numbers and sentences are not child windows, and tesseract garbles the table: "light fanry Ce]"), so they were read from the screenshot `b0-normal-20261004-081149-04b-battle-ended-window.png`: "Gaul's army defeats Rome's army."; Gaul start 35,800 LI + 10,900 HI = 46,700, finish 10,362 + 6,877 = 17,239; Rome start 20,712 LI, 2,094 HI, 7,517 Ar, 4,421 LC, 2,337 HC = 37,081, finish 0; "The army of Gaul captured 156 talents." "The army of Gaul captured no suuplies." (sic: the game's typo) |
| after OK | for 12 s: nothing opened (no Confirm, no Offer of peace) at seed 12345; the strategic windows return about 3 to 4 s after the click |
| post-battle Save As (`NB_post_battle.SAV`, 8.0 s) | flag 0, 132,149 bytes (no block 12); army 0 gone, Gaul's army 10 at 17,239; news ends "Week 11 Winter 270BC / Gaul destroys army of Rome." Rome's unity 881 → 856, Gaul's 402 → 427; the relation stays 3 / 3 |

**Human victory** (`NB_post_battle.SAV` re-opened, army 13 walked to (86,28) and attacked army 10 at 17,239, normal, seed 12345): "Rome's army defeats Gaul's army.", army 13 38,455 → 34,871, Gaul's army destroyed; **nothing opened after OK**; the post-battle save's news ends "Gaul destroys army of Rome. / Rome destroys army of Gaul." (`WIN_post_battle.SAV`).

**The "Offer of peace" box** (lab seed 2, twice, `lab2_a_after_no.SAV`, `lab2_b_post.SAV`; and lab seed 1 with Rome idle, `SI_lab_post_battle.SAV`): it opens after OK of "Battle ended" (within the 2 s the probe waits), window titled **`Offer of peace`**, (13,94) 406 × 360, text read from `b0-lab-b-20261004-083709-offer-of-peace-window.png`: "After defeating you in battle Gaul are willing to end their war with you, if you agree to the terms below." / "An honourable peace with no reparations or penalt" (the label is clipped by its frame) / two empty rows / "If the peace terms are acceptable click YES." / "Otherwise to continue the war click NO."; controls: **TButton "Yes" (94,414) and "No" (269,414), 70 × 25 each**. A ghost `Battle ended` window (53,99) 64 × 1 stays in the window list while it is open. **No** closed it (the window was still listed for about 4 to 6 s after the click); war went on (relations 3 / 3, no news line). It was left open for 3 s and screenshotted before the answer; Yes was not tried. The driver's `dismiss_popups` would not have answered it (it only handles titles `Information`, `Confirm`, `Warning`, `Error` and empty).

### Item 2: Save As inside a battle

Normal build, one battle, seed 12345 (`SI_placement_menu.SAV`, `SI_mid_menu.SAV`, `SI_mid2_menu.SAV`; the same three on the lab build as `SI_lab_*`), logs `b0-savein-20261004-082013.log` and `b0-savein-lab-20261004-083350.log`; the earlier attempts `081536` and `081801` are the Computer-general-on cases below.

| attempt | reachable | file | battle after |
|---|---|---|---|
| File → Save As at the **placement** phase | yes: the Save dialog opens over the battle window | 134,254 bytes = 132,149 + 2,105: **block 12 present, flag 1** | window and `in_battle` unchanged, title unchanged |
| the same after **two End turn clicks with Computer general off** (Rome idle, Gaul playing; titles stay "Rome to move units.") | yes | 134,254 bytes, block 12, flag 1; the block differs from the placement save in 25 bytes (its bytes 6-7 go from `00 00` to `01 05`, then `01 07`) and 18 bytes in the next one | unchanged; after a third End turn and a third Save As the same; then Computer general + End turn ended the battle normally (Gaul 27,387 at the end: Rome idled) |
| toolbar **Save** icon (x 34, tooltip "Save game position") in the battle | the tooltip shows | **no file written** (no file in the game folder changed) | unchanged. Control: the same click on the strategic map rewrites the opened file |
| File → Save As with **Computer general on** | the menu opens, but the battle runs to its end at the next input event | none: the dialog never opened (the battle was over about 4 to 5 s after the toggle, with the File click as the only input; the second attempt, `081801`, avoided the two Escape presses of `reset_ui` and still ended it) | the "Battle ended" box |

**What Save As clears:** nothing visible. `SEL_ARMY` is already **-1** when the battle opens (the attack clears it), so there was nothing to clear; the flag stayed 1, the window stayed, and the battle continued in every case. **Outside block 12 the three files differ from the pre-attack save in the same 62 bytes** (offsets 24136 and 24140 in the map, 100960 in army 0's record and a run from 107532 in army 10's record, i.e. the battle's own set-up of the two armies; not interpreted).

### Item 3: the lab build (seed 1, the same battle)

Series `lab1_a_BATTLE01.SAV` to `lab1_e_BATTLE15.SAV` and `lab1_t0_*`, post-battle `lab1_a_post.SAV` to `lab1_e_post.SAV`, `trials.jsonl`, `b0-series-comparison-20261004.json`.

| trial | process start → post-battle save | half-round saves | Gaul's army 10 after | post-battle sha (first 12) |
|---|---:|---:|---:|---|
| lab1_t0, a, b, c, d, e | 57.0, 56.9, 57.3, 57.3, 57.4, 57.4 s | **15** each | **28,428** | `415797f3a927` (all six) |
| lab2_b (seed 2, peace offer answered No) | 82.5 s (the offer and its wait add about 26 s) | **18** | 23,431 | `82eadd4ec9b4` |
| normal, seed 12345 (`NB_post_battle.SAV`) | n/a (that run also scanned the toolbar) | not written | 17,239 | `3cbf595185ac` |

- **Time per battle: 57.3 s** on average, split (cumulative, lab1_a): process started 4.6 s, save opened 19.0 s (14.4 s of it File → Open, 3 s fixed waits, the modal box), army staged 26.6 s (three legs, 2.5 s each), click → battle window 6.7 s, Computer general + End turn + box + screenshot/OCR + OK + the strategic windows back 14.5 s, post-battle Save As 7.9 s. The battle itself (End turn click to "Battle ended" box) is about **3 to 4 s**. The sweep's "about 1 minute" holds; a trial without the 8 s Save As would be about 49 s.
- **Repeatability:** the six seed-1 series are byte-identical file by file (90 files), as are their post-battle saves. **Seed 2** run twice (`lab2_a`, `lab2_b`, two processes): **18 saves, identical**, post-battle identical. **Seed 1 and seed 2 differ from `BATTLE01`** (29 bytes) and in length (15 v 18 half-rounds). The normal build's seed 12345 gave a third outcome (Gaul 17,239); the normal and lab builds draw differently, as expected from a reseed at battle start.
- Rome's army 0 was destroyed in every battle of this start save (Gaul 46,700 against 37,081). The probe therefore measures one lopsided matchup; it says nothing about win rates.

### Item 4: resume

Source `lab1_a_BATTLE05.SAV` (sha `458a1c60…593`, block 12 present), fresh lab seed-1 process, File → Open: `resume05_lab1_a_BATTLE01.SAV` to `BATTLE10`, `resume_05_lab1_a_post.SAV`, comparison `b0-resume-comparison-20261004.json`, logs `b0-resume-lab1_a-05-*.log`.

- **It resumes:** 2.1 s after the Open, the battle window is back (`Rome  v  Gaul          Rome to move units.`, `in_battle` 1, Computer general off again: the toggle is not saved). Computer general + End turn played it to the end (1 click): **10 more half-round saves** (the original had 15, of which BATTLE05 was the source), Gaul's army at **25,265** (the original: 28,428).
- **Not byte-identical to the original's remaining half-rounds:** the resumed `BATTLE01` differs from the original `BATTLE06` in **114 bytes** (block 12 and the strategic tables), and no resumed file equals any original file.
- **Deterministic given the save:** a second resume of the same `BATTLE05` in a new process gives 10 files **identical to the first resume's** (and the same post-battle save). Resuming `lab1_a_BATTLE01.SAV` gives yet another battle (22 half-rounds, Gaul 16,139).

## Inferences

- **The lab build reseeds `RandSeed` when a battle is resumed as well as when it starts.** Without that, two resumes in two processes (each seeded from the clock at program start) could not be identical; with it, a resume restarts the random stream at the baked seed, which is why its tail differs from the original's, whose stream had run on for five half-rounds. So the plan's [R] statement ("the remaining half-rounds equal the original's byte for byte") is **false for the lab build as built**, while "an edited save resumes and plays out deterministically" is not contradicted. For B3 (crafted mid-battle saves) this is enough; for a "continue exactly where it was" replay a lab variant without the reseed on the resume path would be needed.
- **Mid-battle saves can be had without the lab build:** Save As at a human-controlled phase writes a resumable file (block 12 with flag 1); whether the **normal** build resumes one was not tried.
- **The battle is a single input event once Computer general is on**, and a single End turn click otherwise. A driver must test `in_battle` before every click and must never press Escape or click anywhere (the File menu included) while Computer general is on and the battle is not meant to run.
- **`TBattlePols` ("Offer of peace") exists and is reachable headless**, but it depends on the battle (seed, and what the human side did), not only on who lost: Rome lost 16 of the 17 logged battles from `1_rome_270_winter_11.sav` and the box showed in 3 of those 16. The driver does not answer it; B16 should add `answer_battle_peace(yes|no)`.

## What this does not establish

- **One matchup, one geometry, one start save.** Rome's army 0 against Gaul's army 10 from the east, on plain; Rome lost every time. Nothing about win rates, other types, sizes or terrain.
- **What decides the Offer of peace.** 3 of 16 logged defeats; the gate (unity, cities, loss margin, a random draw) is not known. Yes, and the box after a victory by an AI (or a double defeat), were not tried.
- **Whether the lab and normal builds resume alike**, and whether a normal-build Save As in a battle is loadable.
- **That the half-round series are what they look like:** block 12 was only compared, not decoded (B2), and the first-differing-byte offsets above are not interpreted.
- **Why the unit map opens 1143 × 903 with this save** (the other fixtures open at the default size): not investigated; it may come from the Wine window state and not from the save.
- **The text of the Offer of peace's terms row beyond "penalt"** (clipped) and of any version with reparations.
- **Wine-only.**

## Reproduction

```text
setup/setup.sh
gh release download run-1-rome --repo diegoami/imp_conquest_fixtures --pattern "1_rome_270_winter_11.sav" --dir artifacts/run-exp-battle-probe/
cd $IC2_WORK/build && for s in 1 2; do PYTHONPATH=. python3 <repo>/patches/battle_lab.py $s \
  && mv "IC2 lab.exe" "Imperial Conquest 2 lab s$s.exe" && cp "Imperial Conquest 2 lab s$s.exe" ../prefix/drive_c/IC2/; done
python3 runs/experiments/battles/b0_probe.py normal          # item 1 (110 s of it is the tooltip scan)
python3 runs/experiments/battles/b0_probe.py savein          # item 2 (and: savein lab)
python3 runs/experiments/battles/b0_probe.py gate            # item 3: 5 lab seed-1 battles + 1 seed 2 (ends on the peace offer unless play_out answers it)
python3 runs/experiments/battles/b0_probe.py resume 1 lab1_a 05   # item 4
python3 runs/experiments/battles/b0_probe.py win             # a human victory
```
