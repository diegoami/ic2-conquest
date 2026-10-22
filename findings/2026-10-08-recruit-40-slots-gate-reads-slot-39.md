# Recruit unit: the 40-unit gate reads only slot 39 (addendum to the 40-slot finding)

**Status:** promoted 2026-10-08 into imperial-conquest-2-research at `02303d0` (by ic2-research); this draft is kept for history, the research repo is canonical. It is an addendum to `2026-10-08-recruit-40-slots-cap-in-play.md` (promoted at research `f1d5b21`) and to R46 / RC01 in `2026-10-05-refusal-texts-and-conditions.md`. The research session asked for it on 2026-10-08.

**Tag:** `[confirmed]` for "the R46 gate tests the 40th slot only, not a count of the queue" (Recruit unit only; the mercenary path was not run).

## Answer

Rome's slot 0 is empty and slots 1-39 are occupied (39 queued units, so one slot is free). A Recruit unit order at Rome is still **refused** with R46 *"You have reached your limit of 40 units."* Nothing is queued: the saves before and after the order are **byte-identical** (both `c57740050bc9ba6f…`).

| Layout | Free slots | R46 slot-39-only reading | Whole-queue reading | Observed |
|---|---:|---|---|---|
| RC01: only slot 39 occupied | 39 | refuse | accept | refused |
| this run: slot 0 empty, slots 1-39 occupied | 1 | refuse | accept (into slot 0) | **refused**, queue unchanged |
| 40-slot finding: all 40 occupied | 0 | refuse | refuse | refused |

The gate is the test R46 quotes, `nation +0x420 < 1` (slot 39's troops; `TArmyRecruits_RecruitUnit` L55949), and nothing else: a free slot lower in the queue is never used while slot 39 is occupied. In play the queue is presumably filled from the front, so slot 39 is the last one taken. That is `[derived]`: this run did not show where an accepted recruit lands.

Evidence: run-exp-l11-40-recruit-slots, `MIRROR_PRE.SAV` (`39c16c9ad05d43f1…`), `MIRROR_BEFORE.SAV` and `MIRROR_AFTER.SAV` (both `c57740050bc9ba6f…`), all in release `run-exp-l11-40-recruit-slots`; `runs/experiments/data/run-exp-l11-40-recruit-slots/probe_mirror.py`, `probe_mirror.json`, `probe_mirror.log`, `SAVES.sha256`.

## Method

- Pre-state: `_make_patched_save_full_slots(BASE, 0, 85, n_slots=40, state=12, typ=1, troops=3200)`, then slot 0 (nation 0 +0x2E4) is zeroed. BASE.SAV is 270 BC Spring week 1, with Rome human.
- Fast rollingsave seed exe, seed 12345, Xvfb :99. Load, save (`MIRROR_BEFORE`), `g.recruit(city_row=1, unit_type="hi", thousands=2)` at Rome, save (`MIRROR_AFTER`), compare the recruitment slots. The box text came from OCR (`'e ‘You have reached your lint of 40 units aK'`); R46 holds the literal.

## Not established

- The mercenary path at a full slot 39.
- Where an accepted recruit lands (first free slot, presumably).
