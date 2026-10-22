# run-exp-manual-gaps: screenshots the manual still lacks, and rules seen only in the code

Short staged runs of *Imperial Conquest 2* under Wine, approved by the owner on 2026-10-22. Items A1-A6 are screenshots for the
user manual; items B7-B11 observe rules that were known only from the decompiled code, each as a before/after save diff.

- **PNGs**: `/home/user/ic2-conquest/artifacts/run-exp-manual-gaps/shots/` (gitignored, rule 1), all prefixed `MG_`, never
  overwritten (a re-take is `_v2`). `shots.csv`: file, item, what it shows, source save, turn, exe, sha256.
- **Saves**: `/home/user/ic2-conquest/artifacts/run-exp-manual-gaps/saves/` (gitignored), prefixed `MG_`; SHA-256 in
  `SAVES.sha256`. Copied to Drive `gdrive:IC2/artifacts/run-exp-manual-gaps`. To go to release `run-exp-manual-gaps`.
- **Staged (SYNTHETIC) saves**: `runs/experiments/manual_gaps/stage.py`; every edit (offset, old, new) is in `staged-edits.jsonl`.
  The other saves are natural play from them.
- **Logs**: `run-log.jsonl` (every load, shot, measurement), `a5-trials.jsonl`, `b10-storms.jsonl`, `b11-war.jsonl`;
  save diffs `B*-diff.txt` (`diff_saves.py`: decoded map, cities, armies, fleets, nations, news, calendar).
- Environment: Xvfb 1280x1024, Wine, no window manager; the seed build `Imperial Conquest 2 fast rollingsave seed.exe`
  (SEED.TXT 12345 unless a seed is named). Only one game ran at a time.
- Scripts (`runs/experiments/manual_gaps/`): `mg.py` (start/attach/snap/keep_save, after `manual133/m.py`), `craft.py`
  (save edits, map markers kept consistent), `stage.py`, `inspect_save.py`, `diff_saves.py`, `a5_peace.py`, `b10_storms.py`,
  `b11_war.py`.

## Progress

| Item | Outcome | Files |
|---|---|---|
| A1 attack-army box | **done** | `MG_A1_attack_army_confirm.png`, `..._context_v2.png` (the first context crop cut the box's right edge) |
| A2 attack-fleet box | **done** | `MG_A2_attack_fleet_confirm.png`, `..._context.png` |
| A3 army too large for fleet | **done** | `MG_A3_army_too_large_for_fleet.png`, `..._context.png` |
| A4 Cellular Automata | **done** (seed build: every N gives the same pattern, see below) | `MG_A4_about_box_cancell_button.png`, `MG_A4_cellular_automata_blank.png`, `..._after_N.png` (+ `_v2`..`_v6`, identical), `..._context.png`; varied patterns from the original exe: `MG_A4_orig_cellular_automata_N1..N4.png` |
| A5 Offer of peace | **done** (seed 2; seed 1 gave no box) | `MG_A5_offer_of_peace_seed2.png`, `..._context.png`; `a5-trials.jsonl` |
| B7 disband army | **done**, matches the code | `B7-disband-diff.txt`; finding `2026-10-22-disband-and-scuttle-return-money-and-supplies.md` |
| B8 scuttle fleet | **done**, matches the code | `B8-scuttle-diff.txt`; same finding |
| B9 buy supplies from a foreign city | **done**, matches the code (two cases) | `B9-buy-supplies-diff.txt`, `MG_B9_*.png`, `MG_B9b_*.png`; finding `2026-10-22-buying-supplies-from-a-foreign-city.md` |

| A6 End of Game | **done**: (a) 250 BC, (b) deposition for debt, (c) victory | `MG_A6{a,b,c}_end_of_game_window.png`, `..._context.png`, `..._after_ok_screen.png`; `a6-eog.jsonl` |
| B11 AI declares war on the human | **done** (seed 12345, turn 0733->0734; news line only, no box) | `b11-war.jsonl`, `B11-0733-0734-diff.txt`, `MG_B11_seed12345_after_declaration_screen.png`; finding `2026-10-22-ai-declares-war-on-a-human-seat.md` |
| B10 Winter storm spike | **done**: 4 spikes in 72 fleet-turns, every loss as the code says | `b10-storms.jsonl`, `b10-table.v1.md`; finding `2026-10-22-winter-storm-spike-on-own-fleets.md` |

### A1 attack-army box (turn 0720)
- Staged save `MG_A1_staged_carthage_army3_at_101_37.SAV`: run0 start with Carthage's army 3 (peace with Rome) moved by a save
  edit to (101,37), next to Rome's army 0 at (100,37) (map markers moved with it).
- Select army 0, click army 3: box title **Confirm**, text **"Are you sure you want to attack this army ?"**, buttons **Yes, No,
  Cancel**. The Information panel already shows the clicked army ("Army of Carthage", its troops by type; Moves, Supply,
  Morale, Money blank for a foreign army). Answered **No**: relation Rome-Carthage stays 0 both ways, both armies unchanged.

### A2 attack-fleet box (turn 0723)
- Staged save `MG_A2_staged_ptolemaic_carthage_peace_0723.SAV`: `saves/fleets-adjacent-at-sea-0723.SAV` (two human seats,
  Ptolemaic to play) with the Ptolemaic-Carthage relation set from 3 (war) to 0 (peace) both ways.
- Ptolemaic's fleet 1 selected, Carthage's fleet 0 clicked: **Confirm**, **"Are you sure you want to attack this fleet ?"**,
  Yes / No / Cancel. Answered **No**: relation stays 0, fleets 90 and 70 ships unchanged. The Information panel shows "Fleet of
  Carthage", Ships 90, Capacity 45,000 troops, Sea calm.

### A3 army too large (turn 0734)
- `saves/fleet-split-antium-0734.SAV` unedited: Rome's army 0 (10,700 troops) at (101,45) clicked onto fleet 2 (20 ships,
  capacity 10,000) at (101,46). Box title **Confirm** (sic) with **OK only**, text **"The army is too large for this fleet ?"**.
  After OK the army is still on land (not embarked), fleet 2 unchanged.

### A4 Cellular Automata
- Help menu items: Help topics, Show hints (ticked), About Imperial Conquest. About box `About Imperial Conquest 2`
  (300 x 235), buttons **OK** and **CAncell**. CAncell opens **Cellular Automata** (300 x 428, centred), canvas blank; N draws.
- In the seed build all six N presses drew a **pixel-identical** pattern (blue field with a red central band): the patch sends
  the CA's `Randomize` through SEED.TXT (as `findings/2026-10-09-cellular-automata-savebmp-format.md` says), so with seed 12345
  every N gives this one rule. Re-take with the original `Imperial Conquest 2.exe` (clock seed, no game loaded: Help > About
  works before a game is opened): four N clicks, four different patterns (`MG_A4_orig_cellular_automata_N1..N4.png`); use these
  for the manual.
- X closes the window (at (754,341) here); the About box's OK then needed a second click.

### A5 Offer of peace
- Staged save `MG_A5_staged_rome0_3000li_gaul9_third_0722.SAV` (from `M133_session1_AUTO0722.SAV`): the D-LOSS set-up of
  `findings/2026-10-05-battle-peace-offer.md`: Rome's army 0 = one Lit inf battalion of 3,000 (quality 6), Gaul's army 9 cut
  to a third (44,757 -> 14,880) so that armies(Gaul) < armies(Rome). In play army 0 moved to (99,37) and attacked army 9 at
  (98,36); Computer general; the battle ended at that click (0 End-turn clicks).
- Seed 1: battle, Rome lost, **no box**. Seed 2: **box opened** after the Battle ended OK: "After defeating you in battle Gaul are
  willing to end their war with you, if you agree to the terms below." / "An honourable peace with no reparations or
  penalties." / two empty lines / "If the peace terms are acceptable click YES." / "Otherwise to continue the war click NO.";
  buttons **Yes**, **No** (no title bar without a window manager). Answered **No** (2 clicks, box closed): relation Rome-Gaul
  stays 3. Save after: `MG_A5_after_no_seed2.SAV`. The context shot shows the maps not yet repainted behind the box.

### B7 disband army (turn 0720)
- From the A1 session (its prompt answered No): `MG_B7_before_disband.SAV` -> Disband army 0 at (100,37) next to Arretium ->
  Yes -> `MG_B7_after_disband.SAV`. Army 0: 23,700 troops, money 100, supplies 170. **Treasury 2,200 -> 2,300, Arretium's
  supplies 150 -> 320**, army 0 owner -1, map (100,37) back to plain (2). Nothing else changed.

### B8 scuttle fleet (turn 0734)
- `saves/fleet-split-antium-0734.SAV` session (after A3): Supply fleet 2 with 100 tons and 100 talents (Antium 330 -> 230,
  treasury 1,730 -> 1,630), `MG_B8_before_scuttle.SAV`, Scuttle fleet -> Yes, `MG_B8_after_scuttle.SAV`: **treasury 1,630 ->
  1,730, Antium 230 -> 330**, fleet 2 owner -1, map (101,46) back to sea (0). Nothing else changed.

### B9 buying supplies (turn 0720)
- Staged save `MG_B9_staged_rome_army1_at_107_67_agrigentum.SAV`: Rome's army 1 moved to (107,67), next to Agrigentum
  (Carthage, peace), no own city within one tile.
- The dialog differs from the own-city one: "Supplies at Agrigentum", "Army's supplies", 10s/100s arrows, "Supplies amount",
  "Supplies cost", **Buy supplies** button, "Army's money", OK; no National balance row.
- Five 10s clicks: amount 45 (capacity 22,000 div 100 + 1 - 176), cost 9. Buy supplies: army supplies 176 -> 221, purse 100 ->
  91, **Carthage's treasury 11,000 -> 11,009**, Agrigentum 197 -> 152; Rome's treasury unchanged. No box.
- Purse cap (`MG_B9b_staged_army1_purse5_supplies0.SAV`, purse 5, supplies 0): amount 25, cost 5; purse 5 -> 0, Carthage
  11,000 -> 11,005, Agrigentum 197 -> 172.

### A6 End of Game (`a6_eog.py`)
- Each from a staged run0-start save, one End turn, the window **End of Game** (450 x 347 at (13,89), one button **OK**)
  opens at the next human turn start, **after** the autosave line (`end_turn` returns first; the script then waits for it).
  - (a) `MG_A6a_staged_251bc_winter_w11.SAV` -> turn 1200 (`MG_A6a_AUTO1200.SAV`): "The game is over for Appius Claudius the
    leader of Rome." / "You have reached the end of your allotted 20 years." / "Your 20 years in power in Rome produced these
    changes." / Rome in 270 BC: Population 2,577,000, Cities 25, Treasury 2,200 talents; Rome in 250 BC: 2,601,000, 25, 2,221.
  - (b) `MG_A6b_staged_rome_treasury_-30000.SAV` -> turn 0721: "Your army have deposed you because they have not been paid." /
    "Your  short time in power in Rome produced these changes." / Treasury "- 30,000 talents".
  - (c) `MG_A6c_staged_rome_cities_count_334.SAV` -> turn 0721: "You have conquerred the Mediterranean, a unique achievement."
    (sic); Cities 25 -> 334. **Staged by the city-count word only** (as `EOG_victory_b1` of
    `findings/2026-10-05-end-of-game-screens.md`): the map still shows 25 Roman cities, so this is the window, not a won game.
- After OK the maps close; only the main window ("Imperial Conquest 2") stays (`MG_A6*_after_ok_screen.png`).
- **Differs from the 2026-10-05 finding:** there the reason line was clipped in Wine ("...have not been pa",
  "...a unique achievem"); here both lines are shown in full (`MG_A6b_end_of_game_window.png`, `MG_A6c_end_of_game_window.png`).
  The font environment of this machine differs; the clipping is not a property of the game.

### B10 Winter storms (`b10_storms.py`, `b10_analyse.py`)
- Staged save `MG_B10_staged_6_rome_fleets_at_sea_winter_270.SAV` (from `saves/fleet-split-antium-0734.SAV`): fleet records 0-5
  all made Rome's, launched, 50 ships, condition 100, supplies 400, money 0, on calm sea at (80,44) (80,48) (80,52) (83,42)
  (83,46) (84,44) (every neighbour sea, nearest city 6-9 tiles; map markers 332 written), calendar Winter week 1, 270 BC.
- Six End turns, seeds 12345 and 1 (autosaves `MG_B10_seed<s>_AUTO0739..0744.SAV`). 72 fleet-turns: 61 x (0 ships, -5
  condition), 7 x the dmg-9 step, **4 x the spike** (-9 ships and -15..-17 condition, d = 57). See the finding.
- End turn box texts seen (the "End turn ?" box, not shot): "One of your fleets is not docked at its own city" (one line per
  fleet), "A fleet of yours needs repairing.", "An army of yours needs supplies."; turn-start offers ("Greece wants to trade with
  Rome.", shot `MG_B10_seed1_t0742_box001.png`).

### B11 AI declares war on the human (`b11_war.py`)
- Staged save `MG_B11_staged_carthage_celtiberia_-18.SAV`: run0 start with Carthage-Celtiberia 3 -> -18 (one edit), so
  Carthage is at war with nobody and Rome is its only eligible neighbour (8 x P ratio 13.1).
- Seed 12345, End turn only: Carthage declared on Rome in its seat after turn 0733 (Week 3 Autumn 270 BC), the 14th turn with
  the conditions met; seen in `MG_B11_seed12345_AUTO0734.SAV` (relation 3 both ways). **No box**: the human sees only the news
  line "CARTHAGE DECLARES WAR ON ROME." (`MG_B11_seed12345_after_declaration_screen.png`). Meanwhile Gaul took 9 Roman cities
  (25 -> 16), lowering Rome's P from 1,058 to 634. Finding `2026-10-22-ai-declares-war-on-a-human-seat.md`.

## Re-takes and shots to ignore

| Shot | Why | Use instead |
|---|---|---|
| `MG_A1_attack_army_confirm_context.png` | crop 772 px wide cut the Confirm box (it reaches x 782) | `..._context_v2.png` |
| `MG_A4_cellular_automata_after_N*.png` | seed build: the same pattern at every N | `MG_A4_orig_cellular_automata_N1..N4.png` |
| `MG_A5_offer_of_peace_seed2_context.png` | the maps behind the box were not yet repainted (only the main window strip) | the crop `MG_A5_offer_of_peace_seed2.png` |

## Not done / open

- **Release `run-exp-manual-gaps`**: not created: `IC2_RELEASE_TOKEN` is not set in this session. All binaries are on Drive
  (`gdrive:IC2/artifacts/run-exp-manual-gaps`) and hashed in `SAVES.sha256` / `shots.csv`. For the player:
  `cd /home/user/ic2-conquest/artifacts/run-exp-manual-gaps && gh release create run-exp-manual-gaps --repo diegoami/ic2-conquest --title run-exp-manual-gaps --notes "Saves and screenshots of run-exp-manual-gaps" saves/*.SAV shots/*.png`
- A5 used the seed build only; the box is drawn by the same form in both exes (not re-shot in the original).
- A6c victory is the window only (staged city-count word); a real 334-city conquest was not staged.
- B10/B11 are staged positions with natural play after; their limits are listed in the findings.
