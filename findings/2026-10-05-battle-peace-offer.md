# The post-battle "Offer of peace" (`TBattlePols`, battles plan B16): when it opens, what Yes and No do, and the gate measured

**Status:** draft finding from `ic2-conquest` for the research repo's intake, awaiting promotion; **Wine-only: every result is a candidate until the desktop original confirms it.** Branch `experiment/battle-peace-b16` (PR "battles: B16 the Offer of peace"). Data (text, tracked) in `runs/experiments/data/run-exp-battle-peace/`; saves, memory snapshots and screenshots (binaries, never in git) in release `run-exp-battle-peace` as per-batch `.tar.gz` archives, each member listed with its SHA-256 in the tracked `MANIFEST-b16-batch*.txt` / `release-manifest-*.json` and in `SAVES.v3.sha256`, and cited here by bare file name. Tags: **[O]** observed in a save, a memory snapshot or a screenshot; **[D]** derived; **[R-code]** the decompiled report's claim (`docs/reports/2026-10-04-decompiled-tactical-battle-rules.md` §9 item 6; `decompiled-war-cascade-and-peace-paths.md` §2.3), stated as measured only where a row below measures it.

## Answer

- **The box exists and has one shape [O].** Title `Offer of peace`, 406 x 360 at (13, 94), two `TButton`s `Yes` and `No` (nothing else is a control; the text is painted, so it is read from the screenshot). Text after a human defeat: "After defeating you in battle Gaul are willing to end their war with you, if you agree to the terms below. An honourable peace with no reparations or penalt[ies] If the peace terms are acceptable click YES. Otherwise to continue the war click NO." After a human victory the first words are "After losing to you in battle Gaul are willing to end their war with you" (`win-own126,strong126,unity6600,weak2500,weak13500_s3_survey_r1_dialog-Offer_of_peace-*.png`). Both match the report's two wordings. The two lines for reparations are empty in every box seen.
- **Open rate [O], normal build, D-LOSS (Rome's army 0 = one 3,000 LI battalion, Computer general on both sides): 10 of 30 seeds** (seeds 1, 3, 5, 6, 7, 8, 12, 18, 28, 30), 33 %. In all 30 the three tests of `[R-code]` (armies(W) < armies(L), unity(L) > 500, cities(L) > 7) hold, so the rate is that of the draw alone. **D-WIN (Gaul's army 10 = one 3,000 LI battalion): 0 of 10**, and its tests fail (armies(Gaul) = 0 after its army is deleted, Gaul's unity 377).
- **D-WIN can be made to open [O], with an L1 edit:** Dacia's army 12 given to Gaul (`owner`) and made six 6,000 HI battalions, Gaul's unity 600, Rome's armies 2 and 13 cut to 500 LI each, read back from memory before each run: the tests then hold (armies(Rome) 11,775 to 11,839 < armies(Gaul) 29,700, Gaul unity 575 after the -25, 23 cities) and the box opened in **2 of 5 seeds** (3 and 5).
- **Yes versus No [O], 12 pairs (10 D-LOSS seeds, 2 D-WIN-with-second-army seeds), the same save and seed in two fresh processes:** the state before the answer is identical (below), the click was verified (Yes in one, No in the other, box closed), and then: **Rome-Gaul relation -18 in both directions after Yes, 3 (war) after No; no money, unity, city or army change at the answer, only the relation and one news line "Gaul and Rome have agreed to end their war."** On the next End turn the -18 becomes -14 (+1 and +3 of the quarterly thaw) and stays -14 for the four turns. After No the war goes on: **in the D-LOSS pairs Gaul takes one Rome city per End turn from turn 2 (Rome 30, 29, 28, 27 cities after turns 1 to 4; Gaul 23 to 26), after Yes Rome keeps 30**; in the D-WIN pairs nobody takes a city in four turns.
- **No v No is byte-identical [O]** on two seeds (1 and 3): the post-answer save and all four End-turn autosaves. There is **no run-to-run noise** on the normal build, so every Yes/No difference is caused by the answer; the answer includes the RNG stream (a Yes calls the treaty routine, which reseeds and draws, `[R-code]`), so other nations' relations and the mercenary offers differ from turn 1 on [D].
- **The gate against `[R-code]` [O]:** the loser's unity **501 opens, 500 does not** (3 seeds each; unity is read after the battle's -25, so the loser needs more than 525 before it); the loser's city-count word **8 opens, 7 does not**; Rome's other armies cut so that armies(Rome) 127 < armies(Gaul) 12,992 **does not open** (`loss+weak2=500,weak13=500`: armies(L), Rome the loser, is 127 against armies(W), Gaul, 12,992, so the test `armies(W) < armies(L)` fails). With the B11 exchange hook on 16 hooked lab seeds the box opens **exactly when the logged `Random(5)` at `0x45951C` is below 2** (3 of 3 opens, draws 0, 1, 0; 13 closed, draws 2 to 4), and **no draw is made at all when a test fails** (9 hooked runs with unity 500, 7 cities or weak armies: 0 records at `0x45951C`). So the condition `[R-code]` gives is **measured, not only uncontradicted**, for the three tests as thresholds and for the draw; not measured: equality of the two army sums, human-human, and a human-AI battle in which neither side is the human's choice of loser (below).

## For the clone: the facts to copy (each audited, `b16-claims-audit-*.md`)

1. **The box.** Window title `Offer of peace`, 406 x 360 at (13, 94) in the game window's coordinates, two buttons `Yes` and `No` (class `TButton`; 70 x 25 each; Yes at box-relative (81, 320), No at (256, 320), from the `controls` records). Text, painted: "After defeating you in battle <Winner> are willing to end their war with you, if you agree to the terms below." (human defeated) or "After losing to you in battle <Loser> are willing to end their war with you, if you agree to the terms below." (human won); then "An honourable peace with no reparations or penalt[ies]" (the box clips the line), two empty lines (the reparation lines, never filled), "If the peace terms are acceptable click YES." and "Otherwise to continue the war click NO." It opens after the "Battle ended" box's OK, modal.
2. **Yes.** Relation between the two nations set to **-18** in both directions; news line **"<Winner> and <Loser> have agreed to end their war."** ("Gaul and Rome have agreed to end their war." after a human defeat, "Rome and Gaul have agreed to end their war." after a human victory); **no change of money, unity, city count or armies** at the answer; on the **next End turn -18 becomes -14** (quarterly thaw) and stays -14 over the following three turns. Yes also reseeds and draws (`[R-code]`): other nations' relations and mercenary offers then differ from the No branch from the next turn on.
3. **No.** Nothing is written: the relation stays **3 (war)** and the war goes on (in the staged D-LOSS position Gaul then takes one Rome city per End turn from turn 2).
4. **The gate, as measured.** The box opens in a human-AI battle only if, after the battle's write-back (winner unity +25, loser -25): **armies(W) < armies(L)** (sum of field strength of each nation's live armies; Rome 32,743 v Gaul 12,992 opens, 127 v 12,992 does not), **unity(L) > 500** (501 opens, 500 does not), **cities(L) > 7** (the city-count word: 8 opens, 7 does not); **then a draw `Random(5)` at `0x45951C` must be below 2** (hooked: draws 0, 1, 0 opened, 2, 3, 4 did not; no draw is made at all when a test fails). Any of the three tests failing means no box and no draw. Rate with the tests met: 10 of 30 seeds (33 %); 2 of the 5 values of the draw open it (40 %).
5. **The reseed.** When the box opens the game sets `RandSeed := winner + loser`: read with the box up, `RandSeed` is **`0x3033181F`** in every opened run (Rome 0, Gaul 6), whatever the seed, and a hooked reseed record at `0x457907` marks it. Everything after the box starts from that stream.

## Method

- **Build:** the NORMAL build, `Imperial Conquest 2 fast rollingsave seed.exe` (`RandSeed` from `SEED.TXT` at program start; `Game.load(save, seed)` = a fresh process, then File > Open), as battles plan §7 asks. One process per run, Wine 9.0, three private Xvfb displays and game folders (never the shared ones). The hooked runs use `lab hook s<seed>` (PR #42, `setup/build_lab_exes.sh --hook`; SHA-256 in `EXES-hook-sha256*.txt`): the lab build reseeds at every battle start, so a hooked seed is **not** the normal build's seed of the same number.
- **Start:** `FLD-RG_0743_rome_army0_at_86_28.SAV` (Rome's army 0 at (86, 28) next to Gaul's army 10 at (85, 28); Rome 30 cities, unity 881; Gaul 23 cities, unity 402; Rome's other armies 2 and 13). Cells are **L1 synthetic edits** (`stage.py`, positions never edited): `loss` = army 0 one LI battalion of 3,000, quality 6; `win` = army 10 the same; `win+own12=6,strong12=6,unity6=600,weak2=500,weak13=500` = `win` with army 12 (Dacia's, at (150, 61), far from the battle) given to Gaul and made six 6,000 HI battalions, Gaul's unity 600, Rome's armies 2 and 13 one 500 LI battalion each; gate cells = `loss` plus `unity0=<v>`, `ncities0=<v>` (the count word at nation `+0x446`; the city list is not edited) or `weak2=500,weak13=500`. **Every extra edit is read back from game memory before the attack** (`readback` in `trials-b16.jsonl`); a mismatch is an error record. Both sides on Computer general.
- **A run (`b16_run.py`):** load, read back, Rome's army 0 attacks Gaul's army 10, `play_battle(on_dialog=..., pre_answer=...)`. **The state before the answer is read from game memory while the box is up and before the click** (`0x45E030..0x4A0B80`: `RandSeed`, the map, the nation, army, fleet tables, the battle block and header, 273,232 bytes, `<trial>_pre.snap.gz`); a run whose box does not open gets the same read right after the Battle ended box closed. The box is answered through the new **`Game.answer_battle_peace(yes)`**: it reads the text (OCR) and the controls, requires both buttons, checks that the click point lies inside the wanted button and outside the other, clicks, re-clicks the same button if the box is open after 2.5 s, and raises unless the box closed. The click and the closing are in every record (`answered`, `answer_click`): 35 No and 12 Yes answers took 2 clicks each, one early No 3 (the first click only activates the window). **A Yes or a No is recorded from the click, never inferred from the outcome.** `No` runs of a pair use the driver's `capture` mode (screenshot and controls kept, then No).
- **A pair:** the same save and seed twice, answer Yes in one and No in the other; after the answer a Save As (`<trial>_post.SAV`), then **4 strategic End turns, each proven** (`end_turn(reclick=False)`: no second click without a sign of the turn starting; the "army needs supplies" box answered End turn), each autosave copied (`turns/`), Rome and Gaul read from memory, the news boxes OCR'd, a screenshot of the screen (the Information panel holds the news).
- **Error records:** one in `trials-b16.jsonl`: `loss_s5_hook-capture_r1` (the lab hook exe for seed 5 had not been built yet; kept, seed 5 rerun as `r2`). Two survey trials killed by an early stop wrote no record; they were rerun.
- **Output rule (rule 6):** `trials-b16.jsonl` is append-only; every table is a new file (`b16-survey-table-*.csv`, `b16-pairs-*.json`, `b16-pairs-summary-*.csv`, `b16-repeat-*.json`, `b16-hook-table-*.csv`, `hooklog-*.csv`); nothing was deleted; an earlier run that was superseded (`loss_s1_no_r1`, the first No of seed 1, which recorded no screenshot) stays and is used as a repeat.
- **Audit:** `b16_audit.py` recomputes this finding's numbers from the raw snapshots, saves and screenshots (`b16-claims-audit-*.md`).

## Observations

### The identity of a pair's state before the answer [O]
For all 12 pairs the two pre-answer snapshots are equal **except at most two bytes, one in each of the words at `0x45E614` and `0x45E616`**, and the text, controls, geometry and screenshot of the box are byte-identical (the PNGs have the same SHA-256). Those two words (values 74 to 92 and 1 or 2) are not game state: they vary from run to run for the same save, seed and answer (`loss_s8_survey_r1`, `loss_s8_yes_r1`, `loss_s8_no_r1` hold 78, 76 and 74), and they lie outside every table and the battle block. Between runs of different roles (a survey run and a pair run) up to 11 more bytes of the same area `0x45E420..0x45E700` differ; **in no comparison does any named region differ** (`RandSeed`, map, nations, armies, fleets and news area, battle block, battle header: `b16-repeat-*.json`, 19 comparisons). The title text read when the battle window opens ("Rome to place units" or "Gaul to place units") is a poll-time read and differed in one pair (seed 5); the memory state does not. `RandSeed` read at the box is the same value, `0x3033181F`, in every opened run (the reseed at `0x457907` `winner + loser`, then the preview's draw), so the stream after the box does not depend on the seed.

### D-LOSS, D-WIN: the per-seed table [O]

**D-LOSS (30 seeds)**

| seed | box | winner | armies(W) | armies(L) | unity(L) | cities(L) | tests pass | dialog screenshot | pre-answer snapshot |
|---:|:---:|---|---:|---:|---:|---:|:---:|---|---|
| 1 | **open** | Gaul | 12992 | 32743 | 856 | 30 | yes | `loss_s1_survey_r1_dialog-Offer_of_peace-1791142747.png` | `loss_s1_survey_r1_pre.snap.gz` |
| 2 | closed | Gaul | 13050 | 32743 | 856 | 30 | yes | - | `loss_s2_survey_r1_pre.snap.gz` |
| 3 | **open** | Gaul | 12934 | 32743 | 856 | 30 | yes | `loss_s3_survey_r1_dialog-Offer_of_peace-1791142857.png` | `loss_s3_survey_r1_pre.snap.gz` |
| 4 | closed | Gaul | 13050 | 32743 | 856 | 30 | yes | - | `loss_s4_survey_r1_pre.snap.gz` |
| 5 | **open** | Gaul | 12992 | 32743 | 856 | 30 | yes | `loss_s5_survey_r1_dialog-Offer_of_peace-1791202522.png` | `loss_s5_survey_r1_pre.snap.gz` |
| 6 | **open** | Gaul | 12992 | 32743 | 856 | 30 | yes | `loss_s6_survey_r1_dialog-Offer_of_peace-1791202581.png` | `loss_s6_survey_r1_pre.snap.gz` |
| 7 | **open** | Gaul | 12992 | 32743 | 856 | 30 | yes | `loss_s7_survey_r1_dialog-Offer_of_peace-1791202640.png` | `loss_s7_survey_r1_pre.snap.gz` |
| 8 | **open** | Gaul | 12934 | 32743 | 856 | 30 | yes | `loss_s8_survey_r1_dialog-Offer_of_peace-1791202699.png` | `loss_s8_survey_r1_pre.snap.gz` |
| 9 | closed | Gaul | 13050 | 32743 | 856 | 30 | yes | - | `loss_s9_survey_r1_pre.snap.gz` |
| 10 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s10_survey_r1_pre.snap.gz` |
| 11 | closed | Gaul | 12934 | 32743 | 856 | 30 | yes | - | `loss_s11_survey_r1_pre.snap.gz` |
| 12 | **open** | Gaul | 12992 | 32743 | 856 | 30 | yes | `loss_s12_survey_r1_dialog-Offer_of_peace-1791202917.png` | `loss_s12_survey_r1_pre.snap.gz` |
| 13 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s13_survey_r1_pre.snap.gz` |
| 14 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s14_survey_r1_pre.snap.gz` |
| 15 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s15_survey_r1_pre.snap.gz` |
| 16 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s16_survey_r1_pre.snap.gz` |
| 17 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s17_survey_r1_pre.snap.gz` |
| 18 | **open** | Gaul | 12992 | 32743 | 856 | 30 | yes | `loss_s18_survey_r1_dialog-Offer_of_peace-1791202522.png` | `loss_s18_survey_r1_pre.snap.gz` |
| 19 | closed | Gaul | 13050 | 32743 | 856 | 30 | yes | - | `loss_s19_survey_r1_pre.snap.gz` |
| 20 | closed | Gaul | 12934 | 32743 | 856 | 30 | yes | - | `loss_s20_survey_r1_pre.snap.gz` |
| 21 | closed | Gaul | 12934 | 32743 | 856 | 30 | yes | - | `loss_s21_survey_r1_pre.snap.gz` |
| 22 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s22_survey_r1_pre.snap.gz` |
| 23 | closed | Gaul | 13050 | 32743 | 856 | 30 | yes | - | `loss_s23_survey_r1_pre.snap.gz` |
| 24 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s24_survey_r1_pre.snap.gz` |
| 25 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s25_survey_r1_pre.snap.gz` |
| 26 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s26_survey_r1_pre.snap.gz` |
| 27 | closed | Gaul | 13050 | 32743 | 856 | 30 | yes | - | `loss_s27_survey_r1_pre.snap.gz` |
| 28 | **open** | Gaul | 13050 | 32743 | 856 | 30 | yes | `loss_s28_survey_r1_dialog-Offer_of_peace-1791203059.png` | `loss_s28_survey_r1_pre.snap.gz` |
| 29 | closed | Gaul | 12992 | 32743 | 856 | 30 | yes | - | `loss_s29_survey_r1_pre.snap.gz` |
| 30 | **open** | Gaul | 13050 | 32743 | 856 | 30 | yes | `loss_s30_survey_r1_dialog-Offer_of_peace-1791203172.png` | `loss_s30_survey_r1_pre.snap.gz` |

**D-WIN (10 seeds)**

| seed | box | winner | armies(W) | armies(L) | unity(L) | cities(L) | tests pass | dialog screenshot | pre-answer snapshot |
|---:|:---:|---|---:|---:|---:|---:|:---:|---|---|
| 1 | closed | Rome | 44455 | 0 | 377 | 23 | no | - | `win_s1_survey_r1_pre.snap.gz` |
| 2 | closed | Rome | 44455 | 0 | 377 | 23 | no | - | `win_s2_survey_r1_pre.snap.gz` |
| 3 | closed | Rome | 44391 | 0 | 377 | 23 | no | - | `win_s3_survey_r1_pre.snap.gz` |
| 4 | closed | Rome | 44391 | 0 | 377 | 23 | no | - | `win_s4_survey_r1_pre.snap.gz` |
| 5 | closed | Rome | 44391 | 0 | 377 | 23 | no | - | `win_s5_survey_r1_pre.snap.gz` |
| 6 | closed | Rome | 44391 | 0 | 377 | 23 | no | - | `win_s6_survey_r1_pre.snap.gz` |
| 7 | closed | Rome | 44391 | 0 | 377 | 23 | no | - | `win_s7_survey_r1_pre.snap.gz` |
| 8 | closed | Rome | 44455 | 0 | 377 | 23 | no | - | `win_s8_survey_r1_pre.snap.gz` |
| 9 | closed | Rome | 44455 | 0 | 377 | 23 | no | - | `win_s9_survey_r1_pre.snap.gz` |
| 10 | closed | Rome | 44327 | 0 | 377 | 23 | no | - | `win_s10_survey_r1_pre.snap.gz` |

**D-WIN with a second Gaul army (5 seeds)**

| seed | box | winner | armies(W) | armies(L) | unity(L) | cities(L) | tests pass | dialog screenshot | pre-answer snapshot |
|---:|:---:|---|---:|---:|---:|---:|:---:|---|---|
| 1 | closed | Rome | 11839 | 29700 | 575 | 23 | yes | - | `win-own126,strong126,unity6600,weak2500,weak13500_s1_survey_r1_pre.snap.gz` |
| 2 | closed | Rome | 11839 | 29700 | 575 | 23 | yes | - | `win-own126,strong126,unity6600,weak2500,weak13500_s2_survey_r1_pre.snap.gz` |
| 3 | **open** | Rome | 11775 | 29700 | 575 | 23 | yes | `win-own126,strong126,unity6600,weak2500,weak13500_s3_survey_r1_dialog-Offer_of_peace-1791203505.png` | `win-own126,strong126,unity6600,weak2500,weak13500_s3_survey_r1_pre.snap.gz` |
| 4 | closed | Rome | 11775 | 29700 | 575 | 23 | yes | - | `win-own126,strong126,unity6600,weak2500,weak13500_s4_survey_r1_pre.snap.gz` |
| 5 | **open** | Rome | 11775 | 29700 | 575 | 23 | yes | `win-own126,strong126,unity6600,weak2500,weak13500_s5_survey_r1_dialog-Offer_of_peace-1791203620.png` | `win-own126,strong126,unity6600,weak2500,weak13500_s5_survey_r1_pre.snap.gz` |


(`armies(W)`, `armies(L)` are the sums of field strength over each nation's live armies read from the snapshot, the quantity `FUN_0044A8CC` sums; unity and cities are the loser's.)

### Repeatability [O]
Normal build, same save, same seed, different process: `loss_s1_{capture,survey,no_r1,no_r2}` are equal in every named region and in the post-answer save, and `loss_s1_no_r1` v `loss_s1_no_r2` and `loss_s3_no_r1` v `loss_s3_no_r2` are **byte-identical in the post-answer save and in all four End-turn autosaves** (`b16-repeat-*.json`). So no lab build was needed for the pairs.

## Inferences

- **[D] Why the 10 D-LOSS pairs look alike.** The box reseeds `RandSeed := winner + loser` when it opens (`0x457907`, hooked records `loss_s10_hook-capture_r1` etc.), so everything after the box starts from the same stream whatever the seed; the ten seeds differ only in the battle's survivors (the two post-answer saves of seeds 1 and 30 differ in 6 bytes, the turn-4 autosaves in 7). The 10 pairs are therefore close replicates of one post-battle situation, not ten independent samples of the strategic aftermath; they are independent samples of the open/closed draw and of the identity proof.
- **[D] Yes leaves the war machinery alone and costs nothing.** Treasury and unity of both nations are equal in the post-answer saves; the only non-news fields that differ are the two relation words (`b16-pairs-*.json`, `post_save_diff`). The report's "honourable peace with no reparations" matches: no money moved.
- **[D] The -14 on the next turn** is the quarterly thaw of a negative relation (+1, and +3 with a 1-in-3 chance) acting on -18; it stays -14 over the next three End turns because no further quarter boundary falls in them.
- **[D] After No Gaul keeps attacking Rome in the D-LOSS cell** because Rome's armies are weak there; that Gaul takes a city a turn is a property of this staged position (Rome's army 0 gone, Gaul's army 10 adjacent), not a rate.
- **[R-code] and [O].** Measured: the draw is `Random(5)` (range 5 logged in all 16 hooked runs), the box opens exactly when it is < 2, it is drawn only when the three tests pass, and the tests' thresholds are strict (`unity > 500`, `cities > 7`, `armies(W) < armies(L)` at its extremes).

## Hooked lab runs, gate cells, pairs: tables [O]
**Yes versus No (12 pairs; each cell is Yes/No)**

| cell | seed | rel after answer | rel after turn 1..4 | Rome cities t1..t4 | Gaul cities t4 | Rome unity t4 | Gaul unity t4 | Rome treasury t4 |
|---|---:|---|---|---|---|---|---|---|
| D-LOSS | 1 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 3 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 5 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 6 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 7 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 8 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 12 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 18 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 28 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-LOSS | 30 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/29 30/28 30/27 | 23/26 | 858/813 | 422/449 | -347/-347 |
| D-WIN + 2nd Gaul army | 3 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/30 30/30 30/30 | 23/23 | 908/908 | 570/570 | -72/-72 |
| D-WIN + 2nd Gaul army | 5 | -18/3 | -14/3 -14/3 -14/3 -14/3 | 30/30 30/30 30/30 30/30 | 23/23 | 908/908 | 570/570 | -72/-72 |

**Gate cells (normal build, D-LOSS with one L1 edit, No answered)**

| cell (edit) | Rome unity at the box (after the -25) | Rome cities word | armies(Rome) | armies(Gaul) | seed 1 | seed 3 | seed 5 |
|---|---:|---:|---:|---:|:---:|:---:|:---:|
| `loss+ncities0=7` | 856 | 7 | 32743 | 12992 | closed | closed | closed |
| `loss+ncities0=8` | 856 | 8 | 32743 | 12992 | **open** | **open** | **open** |
| `loss+unity0=524` | 499 | 30 | 32743 | 12992 | closed | closed | closed |
| `loss+unity0=525` | 500 | 30 | 32743 | 12992 | closed | closed | closed |
| `loss+unity0=526` | 501 | 30 | 32743 | 12992 | **open** | **open** | **open** |
| `loss+weak2=500,weak13=500` | 856 | 30 | 127 | 12992 | closed | closed | closed |

**Hooked lab runs (peace draw `Random(5)` at `0x45951C`)**

| trial | box | tests pass | draws at 0x45951C | draw result | reseed record |
|---|:---:|:---:|---:|---:|---|
| `loss_s1_hook-capture_r1` | closed | yes | 1 | 4 | - |
| `loss_s2_hook-capture_r1` | closed | yes | 1 | 2 | - |
| `loss_s3_hook-capture_r1` | closed | yes | 1 | 4 | - |
| `loss_s4_hook-capture_r1` | closed | yes | 1 | 2 | - |
| `loss_s5_hook-capture_r2` | closed | yes | 1 | 3 | - |
| `loss_s6_hook-capture_r1` | closed | yes | 1 | 4 | - |
| `loss_s7_hook-capture_r1` | closed | yes | 1 | 2 | - |
| `loss_s8_hook-capture_r1` | closed | yes | 1 | 4 | - |
| `loss_s9_hook-capture_r1` | closed | yes | 1 | 2 | - |
| `loss_s10_hook-capture_r1` | **open** | yes | 1 | 0 | 69@0x457907 |
| `loss-unity0525_s10_hook-capture_r1` | closed | no | 0 | - | - |
| `loss-ncities07_s10_hook-capture_r1` | closed | no | 0 | - | - |
| `loss-weak2500,weak13500_s10_hook-capture_r1` | closed | no | 0 | - | - |
| `loss_s11_hook-capture_r1` | **open** | yes | 1 | 1 | 66@0x457907 |
| `loss-unity0525_s11_hook-capture_r1` | closed | no | 0 | - | - |
| `loss-ncities07_s11_hook-capture_r1` | closed | no | 0 | - | - |
| `loss-weak2500,weak13500_s11_hook-capture_r1` | closed | no | 0 | - | - |
| `loss_s12_hook-capture_r1` | closed | yes | 1 | 3 | - |
| `loss_s13_hook-capture_r1` | closed | yes | 1 | 3 | - |
| `loss_s14_hook-capture_r1` | **open** | yes | 1 | 0 | 54@0x457907 |
| `loss-unity0525_s14_hook-capture_r1` | closed | no | 0 | - | - |
| `loss-ncities07_s14_hook-capture_r1` | closed | no | 0 | - | - |
| `loss-weak2500,weak13500_s14_hook-capture_r1` | closed | no | 0 | - | - |
| `loss_s15_hook-capture_r1` | closed | yes | 1 | 2 | - |
| `loss_s16_hook-capture_r1` | closed | yes | 1 | 3 | - |

## What this does not establish

- **Wine-only.** The desktop original was not run.
- **Computer general on both sides**, no human-clicked battle. Whether a battle the human plays differently reaches the same box is not tested.
- **One geometry.** Rome v Gaul at (86, 28) / (85, 28), Rome's army 0 or Gaul's army 10 reduced to one 3,000 LI battalion (L1 synthetic). The 33 % open rate is that of the draw at this geometry and does not depend on anything else here; it is not a property of every battle. The D-WIN opening needs the second-Gaul-army edit (an existing army re-owned, positions and map untouched; the unit map's marker for army 12 was not looked at), and its 2 of 5 is five seeds.
- **The normal build for pairs, the lab hook build for the draw.** The hooked seeds are lab seeds; the pairing "this seed's draw" is not carried over to the normal build's seeds.
- **Four End turns only**, and a position in which Rome's relations with its allies were not part of the question: the ally loop of the treaty (`rel[W][k] == 2 and rel[L][k] == 3`, ally relations to -8) was not exercised (no case has Rome or Gaul with an ally at war with the other).
- **Not tested:** `armies(W)` equal to `armies(L)`; unity or city counts between the pairs of thresholds tested (501/500, 8/7); human against human (`THVHBatPols`); more than one box in a turn; what a Yes does when the loser is the AI and the human the winner beyond the two D-WIN pairs (relation -18, no other non-news field differs).
- The **two volatile words** at `0x45E614/0x45E616` were not identified; they are excluded from the identity proof and listed in every pair's record.

## Claims audit
`b16-claims-audit-*.md` (written by `runs/experiments/battles/b16_audit.py`): every number above recomputed from the raw snapshots, saves and screenshots, 0 mismatches; and `SAVES.sha256` note: the older `SAVES.sha256` mixes two name forms (the runner's bare names, and `shots/...`-prefixed names after one run of `scripts/archive_measurements.py`); it is not edited, and `SAVES.v3.sha256` lists every binary once as `<sha256>  <bare file name>`.
