# Selected saves

Small (~130 KB) saves kept in git by the player's decision (2026-09-29). Only saves that are interesting for play or for research are kept here; everything else stays in `$IC2_WORK` or a run's artifacts. All come from the build `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, and all load in the normal game. Every "0720" save starts from `run0-start-AUTO0720-seed12345.SAV`, and every "0721" save is one End turn after it.

| File | Turn | What happened | Why it is interesting |
|---|---|---|---|
| `run0-start-AUTO0720-seed12345.SAV` | 0720, 270 BC Spring week 1 | New game, Rome human, `SEED.TXT` = 12345 (= `BASE.SAV` of the tests) | **Run 0's start.** Two independent new games with this seed are byte-identical (sha256 `050bc354…`). Rome is seat 12 of 16, Gaul seat 15; Rome trades only with Illyria; Macedonia's relation is −8 (it dropped its trade with Rome before Rome's first turn). |
| `det-AUTO0721-seed12345.SAV` | 0721 | Start save opened, End turn, seed 12345 | Determinism proof: a second run gives the same bytes (sha256 `48857fdd…`). |
| `det-AUTO0721-seed999.SAV` | 0721 | Same, seed 999 | Control: 592 bytes differ from the seed-12345 result. |
| `det-AUTO0721-clock.SAV` | 0721 | Same, no `SEED.TXT` (clock) | Control: another clock run differs again. `findings/2026-09-29-loading-a-save-does-not-reseed.md`. |
| `phase0-scripted-turn-AUTO0721.SAV` | 0721 | Army 0 moved to (101,36), HI 3,200 recruited at Rome, End turn | **Phase 0's done criterion**: a second run gave identical bytes. |
| `siege-felsina-failed-0721.SAV` | 0721 | Army 0 alone besieged Felsina (Gaul) | The siege formula confirmed: attack 20,720 against defence 34,050 fails; the army lost 8.2 % (23,700 → 21,765); Felsina loyalty 79→76, fort 68→65, pop 26→25. No "Are you sure" box, because Rome and Gaul were already at war. |
| `recruit-hi3200-0720.SAV` | 0720 | Recruit HI 3,200 at Rome | Cost `3,200 div 200 × 20` = 320; mobilization 30 → 32, as the research formula predicts. |
| `merc-hire-free-0720.SAV` | 0720 | Army 1 hired the Samnite LI (3,868, quality 8) at Heraclea | **Research check:** no hire price was deducted, neither from the army purse (100 → 100) nor from the treasury (2,200 → 2,200). The research predicted 24 talents from the purse. The offer left the pool. |
| `fortify-arretium-0720.SAV` | 0720 | Arretium fortified by 3 points (72 → 75), plus the hire above | Stored as 372 (a pending order); cost 99 = pop 33 × 3. After the tick, Arretium should enter the recruit list (fortification ≥ 75, `findings/2026-09-29-recruiting-cities-need-fortification-75.md`). |
| `mobilize-new-army-0720.SAV` | 0720 | HI 4,000 (state 17) mobilized at Rome, plus the hire and fortification above | New army 14 at (102,44): quality 4 (= 17 div 4), 0 supplies, 0 moves, morale 59, as the research says. |
| `trade-numidia-0720.SAV` | 0720 | Trade proposed to several nations; Numidia accepted | Carthage, Ptolemaic, Seleucid, Greece, Celtiberia and Dacia refused ("You cannot trade with X."). Media, Thracia, Bithynia, Armenia and Galatia gave no box and no change (unexplained, see HANDOVER.md). Rome now trades with Illyria and Numidia. |
