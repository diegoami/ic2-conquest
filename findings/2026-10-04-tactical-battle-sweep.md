# Tactical battle sweep, Stage 1 so far (battles plan B1 to B4): the battle block decoded, crafted mid-battle saves, one pairing (HI v HI, size one) end to end

**Status:** draft finding from `ic2-conquest`, awaiting promotion; **this is the running draft of the research request's deliverable** (the sweep table, B5, and the screenshots, B8, will be added to it). **Wine-only: every result below is a candidate until the desktop original confirms it.** Branch `experiment/battle-sweep-b` (stacked on PR #35 `experiment/battle-sweep`); saves and screenshots are in release `run-exp-battle-sweep` (SHA-256 in `runs/experiments/data/run-exp-battle-sweep/SAVES.sha256`), logs, `trials.jsonl`, half-round logs and tables under `runs/experiments/data/run-exp-battle-sweep/`. Tags: **[O]** observed, **[D]** derived, **[?]** unknown. Everything is **lab** (battle-lab build, seed baked in, `patches/battle_lab.py`) and **L1** (strategic edit before the attack, placement and initiative the game's own) or **L2** (block edit of a mid-battle save), as labelled.

**Answer.**
- **The battle block is decoded** (B2): 9 header bytes, 40 slots of 44 bytes (position x, y, origin label, type, troops, quality, battle-local morale, a movement-points field, an ammunition field, a target slot, the name) and a 14 × 12 grid of unit **sprites** (`state/battle_block.py`). The block is in game memory at **0x4A0344** (slots and grid, contiguous) with its header fields at 0x4A0B74..0x4A0B7D, so `Game.battle_state()` reads a live battle without saves: it was equal to File > Save As's block 12 in all 3 phases tried (`b2-verify-20261004-093834.json`). The grid ↔ screen mapping holds on **all 168 cells in all three phases** (`B2_placement.SAV`, `B2_after_end_turn_1.SAV`, `B2_after_end_turn_2.SAV`, screenshots `b2_*_window.png`).
- **The research request's "slot word +2" is the unit's origin label** (byte +4 of a 44-byte slot, `DAT_004a0348` = 0x4A0344 + 4): 0 for a regular unit, 11 for the Gallic mercenary, equal to the strategic unit's label for every unit. It is **not** a link to the army's unit index (hypothesis rejected; the slot order itself is the link, below). The header word at bytes 2-3 is the **defender's strategic army index** (10).
- **Crafted mid-battle saves are accepted and play from the edited state** (B3, L2): a no-op block edit is byte-identical and resumes to a byte-identical series (`CRAFT_c0_control.SAV` v `CRAFT_c1_noop.SAV`); a troops edit, a type edit and an adjacency edit change the battle as expected; the game **refills the movement-points field on resume** and does **not** repair an inconsistent grid.
- **B4: HI v HI, one unit each, seeds 1 to 3, both sides on Computer general, each seed run four times: all four runs of a seed are byte-identical** (all `BATTLEnn.SAV` of the series and the post-battle save, `compare-hi-hi-one_s{1,2,3}_r1-*.json`), **53.4 s per battle** on average (48.4 to 58.5 s, 12 trials, process start to post-battle save). Rome (the attacker) lost all three; Gaul kept 2,958 / 2,831 / 4,196 of 6,000 in 19 / 18 / 15 half-rounds.

## Method

- **Start state:** `FLD-RG_0743_rome_army0_at_86_28.SAV` (PR #35; the research start save `1_rome_270_winter_11.sav` with Rome's army 0 walked to (86,28), next to Gaul's army 10 at (85,28)), built twice byte-identical (`39edecd1…`). Natural (nothing edited) for B2; for B4 the L1 edits of `runs/experiments/battles/stage.py`: army 0 and army 10 each set to one HI unit of 6,000, quality 6, army morale 65 (`hi-hi-one_start.SAV`). Army positions are never edited.
- **Builds:** lab exes `Imperial Conquest 2 lab s1/s2/s3.exe` (`setup/build_lab_exes.sh`, SHA-256 in `EXES-sha256.txt`). One process per battle. Wine 9.0, Xvfb 1280 × 1024.
- **Decoder:** reverse-engineered from B0's `gate2_a` and `gate2_s2a` series (30 files) and the trials' series, then checked on **137 decoded files** (`b2-analysis-20261004-095840.json`), against game memory and against screenshots (`b2_probe.py`).
- **Crafted saves:** `stage.block_edit` on `hi-hi-one_s1_r1_BATTLE02.SAV` / `BATTLE03.SAV` (and B0's `gate2_a_BATTLE04.SAV`), resumed by File > Open on the lab seed-1 exe (`b3_crafted.py`).
- **Runner:** `runs/experiments/battles/trials.py` (PR #35); every End turn click goes through `Game.end_turn_proven` (flag, title, BATTLEnn count or the half-round counter must move within 8 s). The half-round log: `halflog.py`.

## Observations

### B2: the block (`state/battle_block.py`; every field is named or listed unknown)

| where | field | what | tag |
|---|---|---|---|
| header +0 | attacker army index | 0 (Rome's army 0) in every battle | [O] |
| header +2 | defender army index | 10 (Gaul's army 10) in every battle | [O] |
| header +4 | `x2` | 1 at the first file of a series, then 0, 0, 1, 0, 1, 0 ...: **the side that acted in the half-round before this file (0 Rome, 1 Gaul)**; the two sides alternate | [D] (fits every file of the 12 trials' series; its memory address is **unverified**, below) |
| header +6 | `y1` (byte) | 0 until the placement is done (the first two saves), then 1 | [O] meaning [?] |
| header +7 | half-round counter | equals the BATTLEnn number in a lab series (1, 2, 3 ...); 2 at the placement Save As, 3, 5, 7 after End turn clicks (two half-rounds per click) | [O] |
| slot +0, +2 | x (0 to 13), y (0 to 11) | grid index = x × 12 + y | [O] |
| slot +4 | origin label | 0 regular, 11 Gallic mercenary; = the strategic unit's label | [O] |
| slot +6, +8, +10 | type, troops, quality | = the strategic unit's at the start | [O] |
| slot +12 | battle-local morale | 60 to 99 seen; the winner's rises to the cap 99, the loser's falls (`halfrounds-hi-hi-one_s1_r3.jsonl`: Rome 65 → 31, Gaul 88 → 99) | [O] |
| slot +14 | `state` | **movement points** by type: HI 2, Ar 4, HC 5, LC 6, LI 4 (Rome's LI; Gaul's LI read 1 at the second file, not understood); reset to the type's value when the unit's side starts a half-round (the game does it on resume, below) | [D] |
| slot +16 | `ammo` | 0 for HI and HC, **LI 7, LC 9, Ar 25** at the start; falls when the unit shoots (Ar by 4 per volley, LI by 2 then more) | [D] |
| slot +18 | `target` | the slot index of the enemy it last attacked, −1 none (set in melee; Gaul slots show −1 only for the AI side at start) | [D] |
| slot +20 | name | 24 bytes | [O] |
| grid | 14 × 12 words | **50 = empty, else `side × 20 + 3 × type + size class`**: a *sprite* (drawn icon), derived from the slots (0 inconsistent files, 0 sprite-rule violations in 137 files and in the 455 lab saves of B0, the trials and B3's resumed series). Size class 0 below std/3 troops, 1 below 2·std/3, else 2 (std: LI 15,000, HI 6,000, Ar 3,500, LC 7,000, HC 2,500); observed ranges HI 489 to 816 / 2,094 to 3,964 / 4,226 to 5,900, Ar 181 to 789 / 1,215 to 2,046 / 2,881 to 3,411 and likewise for LI, LC, HC (`b2-analysis-20261004-095840.json`). No terrain in any grid seen. | [D] thresholds ±gap, a pre-answer to B8 |

- **Slots and strategic armies.** Slots 0 to 19 are the attacker's army, 20 to 39 the defender's. In a save written inside a battle **the strategic army's units are in slot order**: Rome's slot k is army 0's unit k; the **AI side is re-sorted at battle start** (Gaul's HI first, then LI: army 10's records `7th Foot, 4th Guards, 8th Foot, 9th Foot, 5th Guards` are in slots as `4th Guards, 5th Guards, 8th Foot, 7th Foot, 9th Foot`, `b2-verify-20261004-093834.json` `side1`). The army records keep the **start** troops through the battle; the slots hold the live ones.
- **Memory.** `Game.battle_state()` = slots and grid at 0x4A0344 (2,096 bytes) plus header words at 0x4A0B74 (attacker army), 0x4A0B76 (defender army), 0x4A0B78 (`x2`), 0x4A0B7A (half-round counter) and the byte 0x4A0B7D (`y1`); the battle flag is 0x4A0B7C. Equal to the Save As block in 3 of 3 phases. **Unverified:** the attacker-army and `x2` addresses (both read 0 in the comparisons) and, after a resume, `x2` reads 0 where the file has 1 (`b3-crafted-20261004-095138.jsonl`, `gate2_a_BATTLE04.SAV`): either the resume resets it or the address is wrong.
- **Resume bumps the counter and refills moves.** After File > Open of a block save the counter reads +1 (2 → 3, 3 → 4) or +2 (4 → 6) and every unit's `state` is its type's movement allowance.
- **Diff and inferred actions.** One 14-unit natural battle (B0's `gate2_a`, `gate2_s2a`): 261 loss rows, **150 (57 %) unambiguous** (exactly one adjacent enemy or one shooter, `BB.diff`); the rest are `unknown`. In the 1-v-1 battles of B4 **every** loss row is unambiguous (26 of 26 for seed 1). Position, troops, quality and morale are exact; kind and actor are [D].

### B3: crafted saves (L2; `b3-crafted-20261004-094135.jsonl`, `-094308`, `-094745`, `-095138`; files `CRAFT_*.SAV`, `b3_*_post.SAV`)

| scenario (edit of a lab save) | game memory v the file after the resume | outcome |
|---|---|---|
| c0 control (`hi-hi-one_s1_r1_BATTLE02.SAV`, unedited) | counter 2 → 3 only | 16 half-rounds, Gaul keeps 3,533 |
| c1 no-op block edit | same | **file byte-identical to c0; series and post-battle save byte-identical to c0's** |
| c2 Rome HI 6000 → 3000 (mirrored in the army) | counter only | 11 half-rounds, Gaul keeps 5,330 |
| c4 the same, **slot only** (the army keeps 6,000) | counter only | the same battle as c2 (Gaul 5,330): **the battle plays from the slots; the army record does not matter** |
| c7 Rome HI → HC | `state` 2 → 5 (the game **repaired** it to HC's movement) | Rome wins, keeps 3,876 |
| c3 / c5 / c6 position, grid and same-cell edits **during the placement phase** (`y1` = 0) | counter only | **identical to c0**: the AI re-places the units, position edits made at placement are overwritten |
| d0 control (`..._BATTLE03.SAV`, placement done), d3 Rome moved next to Gaul, d5 Gaul's grid cell emptied, d6 both on one cell, d8 Rome at (13,0) | counter and `state` only: **the grid is not repaired** (d5's stale cell persists for at least 3 half-rounds, `BB.check_grid`) | **all five end with the same post-battle save** (`b3_d*_post.SAV`, Gaul keeps 3,285) though they last 13, 11, 13, 11 and 15 half-rounds; d3 shows the edited start at once (first half-round: `target` −1 → 20, no move) |

### B4: HI v HI, size one, lab seeds 1 to 3 (L1, `hi-hi-one_start.SAV`)

Row format fixed in `trials.py` `COLUMNS` (`sweep-table-20261004-095840.csv`, 12 rows): `trial, cell, attacker, defender, size, seed, rep, exe, status, half_rounds, winner, end_turn_clicks, att_troops_before/after/loss, def_troops_before/after/loss, att_destroyed, def_destroyed, att_promotions, def_promotions, end_condition, result, dialog, seconds, start_save, series_first, series_last, post_save, post_sha12, series_sha12, halflog, loss_rows, unambiguous_rows`. Every trial is also a full record in `trials.jsonl` (units, news, taken, timings, dialogs); the per-half-round log is `halfrounds-<trial>.jsonl`.

| seed | half-rounds | winner | Gaul's HI after | Offer of peace | post-battle sha (12) | runs identical |
|---|---:|---|---:|---|---|---|
| 1 | 19 | Gaul | 2,958 | yes (declined) | `1043d0aaccf3` | 4 of 4 |
| 2 | 18 | Gaul | 2,831 | no | `3e4a5b00b6de` | 4 of 4 |
| 3 | 15 | Gaul | 4,196 | yes (declined) | `0e99a9b52809` | 4 of 4 |

- **Placement and initiative [D], from the first files:** Gaul's HI is placed first on row y = 9 at x = 4 / 10 / 7 (seeds 1 / 2 / 3), then Rome's is placed (the human side's units wait parked on row y = 0 at x = 0, 1, ... until then); the sides then alternate, Rome (the attacker) first. HI moves 2 cells per half-round and stops one cell short of contact, then melee: `target` is set on both and every half-round after contact is a mutual melee exchange (`halfrounds-hi-hi-one_s1_r3.jsonl`).
- **Time per battle: 53.4 s** (12 trials; seed 2 about 49 s, seeds 1 and 3 about 55 s): load and boxes 18.7 s, click to battle window 6.3 s, battle open to over 19.9 s (the Computer general click runs the whole battle: **0 End turn clicks** in all 12), post-battle Save As 8.1 s.
- **Every End turn click is proven** (flag, title, BATTLEnn count or the half-round counter moves within 8 s; `Game.end_turn_proven`, `tests/test_driver_battle.py`); in these battles it was not needed (0 clicks), and was exercised live in `b2_probe.py` (2 clicks, each proven by the half-round counter). Two things found on the way: after a File > Save As the battle window is inactive and the first click may only activate it, and the BATTLEnn **file count is not a safe proof** (a re-run overwrites old files), so the half-round counter was added to the proof.
- **The Offer of peace appeared in 2 of 3 seeds** (identically in each of the 4 runs of a seed): it depends on the battle, not on randomness outside it. It was captured, declined (No), never accepted.

## Inferences

- **The slot order is the link between a battle and its strategic army**, not a per-slot index word; the "word +2" of the research request is the origin label.
- **The random stream is consumed by the exchanges, not by movement:** five different geometries of the same HI v HI battle after a resume (d0 to d8: adjacent, far away, same cell, stale grid) end in the same post-battle save (Gaul 3,285 and Rome destroyed), only the number of half-rounds changes. So, for a fixed seed, timing and placement alter *when* the exchanges happen, not their results, at least for this pairing. [D]
- **The grid is a drawing aid** (sprites; no terrain in these battles); the game plays from the slots and does not repair the grid.
- **Crafted L2 saves are usable for B8-style icon ladders** (troop counts per unit) and for placing units after the placement phase; they cannot place units *during* it.

## What this does not establish

- Anything about other pairings, sizes or the sweep (B5): one pairing, three seeds, one geometry; HI v HI with equal sizes and Rome losing every time says nothing about win rates.
- The meaning of `y1`, and of `x2` beyond "the side that acted last"; the memory addresses of the attacker-army and `x2` header words; why Gaul's LI `state` reads 1 not 4; what `ammo` falls by for each unit type (only archers' 4 per volley is clear).
- That `state` is exactly "movement points left" (it fits the type's allowance and the moves seen), and the thresholds of the size classes beyond ±the gap between observed troop counts (B8 bisects them).
- Whether the normal build resumes a block save as the lab build does; whether edits during placement could ever stick (L2 positions at placement are overwritten).
- The end condition of a battle (annihilation, rout or surrender): the strategic result only tells that the loser's army is gone.
- **Wine-only.**

## Reproduction

```text
setup/build_lab_exes.sh 1 2 3
python3 -m tests.make_battle_fixtures                                   # FLD-RG twice, byte compare
python3 runs/experiments/battles/trials.py run hi-hi-one --seeds 1-3 --reps 4
python3 runs/experiments/battles/trials.py compare hi-hi-one_s1_r1 hi-hi-one_s1_r2
python3 runs/experiments/battles/halflog.py hi-hi-one_s1_r1             # the half-round log of one trial
python3 runs/experiments/battles/b2_probe.py                            # memory v Save As, grid v screen
python3 runs/experiments/battles/b2_analyze.py                          # field statistics over all kept series
python3 runs/experiments/battles/b3_crafted.py                          # the crafted-save scenarios (needs the B4 series)
python3 -m tests.test_battle_stage; python3 -m tests.test_battle_trials; python3 -m tests.test_driver_battle
```
