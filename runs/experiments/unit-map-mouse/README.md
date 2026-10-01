# Unit map mouse orders and the Taxation range (questions a-g)

From the `imperial_conquest_2` main session, relayed by the player (2026-10-01). Findings draft: `findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md`. Saves and screenshots: release `run-exp-unitmap-mouse` (kept in the gitignored `artifacts/run-exp-unitmap-mouse/` until the player creates the release).

| Question | Script | Status |
|---|---|---|
| (a) click-to-move, stays selected | `a_c_d_e.py` | measured |
| (b) the attack prompt at peace, none at war | `b2_attack_prompt.py` (`b_attack_prompt.py` is the first, confounded attempt: the menu save cleared the selection) | measured, cities only |
| (c) left/right click on a unit | `a_c_d_e.py` | measured (own selected army) |
| (d) Shift+X | `a_c_d_e.py` | measured |
| (e) where Split army puts the new army | `a_c_d_e.py` | measured (adjacent, +1,+1) |
| (f) embark and unload by click | - | **not run** (needs a launched fleet: 12 turns) |
| (g) Taxation range | `g_taxation.py` | measured (0..40, line 1, page 5) |

`common.py` has the shared helpers. `harness/win_slider.c` reads a trackbar's range from the control.
