# Mercenary hire: the recruitment queue does not block it, and R08 keeps it off slot 20

**Status:** promoted 2026-10-08 into imperial-conquest-2-research at `b72cfae` (by ic2-research); this draft is kept for history, the research repo is canonical. The research session asked for it on 2026-10-08 (ask B). It extends `2026-10-05-mercenary-hire-price-is-a-gate-not-a-charge.md`, R08 in `2026-10-05-refusal-texts-and-conditions.md`, and `2026-10-08-join-armies-20-unit-gate-counts-last-slot.md` (research `6466d56`).

**Tag:** `[confirmed]`.

## Answer

- **A full recruitment queue does not block a mercenary hire.** With Rome's 40 slots occupied, army 1 hired the Samnite offer (li 3,868, quality 8, label 38) into slot 6. No R46 box appeared, and the queue was the same before and after. The control with an empty queue gives the same result (slot 6, the same unit).
- **Nothing is charged.** Purse 100 → 100 and treasury 2,200 → 2,200 in every case, as the 2026-10-05 finding says: the price is only a minimum purse. The hire's other effect is that the offer leaves the pool (mercenary pool record 25: troops 3,868 → -1, `TRecruitMercs_RecruitMercUnit` :43672).
- **The hire goes to the last occupied slot + 1, not the first free slot.** With army 1 holding units only in slots 0 and 18, the Samnite landed in **slot 19**; slots 1-17 stayed empty.
- **No overflow into the next army record is reachable through the UI.** Research's report predicted one: the hire writes slot `FUN_0044a66c(army)` with no check for 20 (:43658-43669), and slot 20 would be the next record's header. But the toolbar order `TUnitMap_RecruitMercenaries` refuses to open the dialog when **slot 19** holds troops (L46884 `*(short *)(&DAT_0047c460 + army * 0x290) < 1`; 0x47C460 = army +0x274 = slot 19 troops). That is R08, *"This army already has 20 units."* Inside the dialog, a hire that fills slot 19 closes it (:43686 `if (iVar3 == 0x13 ...) TRecruitMercs_OK`). Both cases that would reach slot 20 were refused by R08, and the next record (army 2: (47,62), owner 1) and the army count (14) were unchanged:
  - 20 units in slots 0-19: refused by R08.
  - **only slot 19 occupied, 1 real unit**: also refused by R08. The box says "already has 20 units" for an army with one.

| Case | Queue | Army 1 slots before | Result | Lands in | Purse / treasury |
|---|---|---|---|---|---|
| c1 | 40 occupied | fixture (0-5) | **hired**, no box | slot 6 | 100 / 2,200 unchanged |
| c2 | empty | fixture (0-5) | **hired** | slot 6 | unchanged |
| c3 | fixture | 0-19 (20 regular units) | **refused R08**, no dialog | | unchanged |
| c4 | fixture | 0 and 18 | **hired** | **slot 19** (1-17 empty) | unchanged |
| c5 | fixture | 19 only (1 unit) | **refused R08**, no dialog | | unchanged |

**Byte differences between the before and after saves:**
- c3 and c5 (refused): only Rome's unit-map view origin (nation 0 +0x486/+0x488), which the selection click scrolls.
- c1 and c4: army 1's new slot, the pool record, and the view origin.
- c1 only: the map word at (120,53), army 1's tile, went from 200 to 216. This is unexplained; it does not appear in c4.

Evidence: run-exp-merc-full-queue, `<case>_{PRE,BEFORE,AFTER}.SAV` for c1_full_queue, c2_empty_queue, c3_army_20_slots, c4_army_gap_0_18, c5_army_only_slot19 (release `run-exp-merc-full-queue`; SHA-256 in `runs/experiments/data/run-exp-merc-full-queue/SAVES.sha256`); `probe_merc.py`, `probe_merc.log`, `probe_merc_*.json`.

## Method

The fixture is `saves/run0-start-AUTO0720-seed12345.SAV`: Rome human, army 1 at (120,53) next to Heraclea's Samnite offer, purse 100 (the gate is 24). Rome's queue (nation +0x2E4) was set to 40 or 0 slots of (12, hi, 3,200, city 85). Army 1's 20 slots were rewritten only in c3-c5, with regular heavy-infantry units of 1,000 men, quality 7, named `S1-<slot>`. Fast rollingsave seed exe, seed 12345, Xvfb :99. Load, save `BEFORE`, `g.hire_mercs(1, rows=(0,))` (toolbar Recruit mercenaries, offer row 0, Recruit unit, OK), collect any boxes, save `AFTER`.

## Not established

- The map word change in c1 (200 → 216 at army 1's tile).
- Whether an edited save with slot 19 empty but a FUN_0044a66c value of 20 can exist. It cannot: the value is the last occupied slot + 1, so 20 means slot 19 is occupied, and R08 covers that.
