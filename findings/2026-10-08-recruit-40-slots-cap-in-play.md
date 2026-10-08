# Recruit unit: the 40-recruited-units cap in play (row L11, 40 recruited units)

**Status:** a draft from `ic2-conquest`, awaiting promotion. Companion to `findings/2026-10-05-player-facing-feature-inventory.md` row L11 and to `findings/2026-10-05-refusal-texts-and-conditions.md` R46 / RC01. RC01 staged only the 40th slot (nation 0 +0x420 = 1); this run fills **all 40 slots** and checks that the queue does not grow.

**Tag:** `[confirmed, partial]` for the "40 recruited units" bullet of L11 (Recruit unit at one city; mercenary hire and other cities not run).

## Answer

- With Rome's 40 recruitment slots all occupied, a 41st **Recruit unit** order is refused with the box *"You have reached your limit of 40 units."* (R46, `TArmyRecruits_RecruitUnit`:56033). The OCR of the box read `'e ‘You have reached your lint of 40 units aK'`, and R46 has the literal text.
- The queue stays at 40 occupied slots at city 85 (Rome), before and after: nothing is queued.

| Slots occupied before | Order | Box | Slots occupied after |
|---:|---|---|---:|
| 40 (all at city 85) | Recruit unit, Rome, heavy infantry, 2 (thousands) | "You have reached your limit of 40 units." | 40 |

Evidence: run-exp-l11-40-recruit-slots, `T_RECRUIT_40SLOTS.SAV` (sha256 `aca5cebb84d41eee…`, release `run-exp-l11-40-recruit-slots`); `runs/experiments/data/run-exp-l11-40-recruit-slots/test_run_1.log` and `SAVES.sha256`. The test is `tests/test_orders.py` `recruit_40_slots_cap`, which first passed at `6bddb39` (log in `tests/results.md`, "2026-10-08, L11 40-recruited-units gate regression") and was re-run for this draft.

## Method

- Pre-state: `_make_patched_save_full_slots(BASE, nation_index=0, city_id=85, n_slots=40, state=12, typ=1, troops=3200)`. Each of Rome's 40 slots at nation +0x2E4 (8 bytes: state, type, troops, city) gets (12, heavy infantry, 3,200, city 85). BASE.SAV is 270 BC Spring week 1 with Rome human.
- Fast rollingsave seed exe, seed 12345, Xvfb :99. Load, save, check 40 occupied slots at city 85, issue `g.recruit(city_row=1, unit_type="hi", thousands=2)`, capture the box text, save, and count the slots again.
- The gate in code (R46): slot 39's troops (nation +0x420) must be below 1, so a full queue is detected by its last slot.

## Not established

- The mercenary path (`TRecruitMercs_RecruitMercUnit`), which L11 also cites.
- Whether the gate tests only slot 39 (R46's reading) or the whole queue. A save with slots 0-38 empty and slot 39 occupied (RC01) refuses as well, which is consistent with the slot-39 test.
