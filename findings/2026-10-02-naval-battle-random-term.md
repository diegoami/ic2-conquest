# The random term of a naval battle: 160 battles fit "strength × (1 + U(0, 0.3)) on each side", with no attacker bonus

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It settles the question left open by `findings/2026-10-02-naval-battles.md` (whether the research formula's "random 0–30 %" is on both sides, on one, or smaller): **160 battles** at war, no army aboard, calm sea, one pair of fleets, 8 cells of 10 to 30 seeds each, about parity.

**Answer.**
- **The research formula read literally fits:** each fleet's strength `ships × condition / 10` is multiplied by `1 + U(0, 0.3)`, independently for the two sides, and the larger product wins. It is the best of the models tried by AIC (161.2), its Pearson chi-square over the 8 cells is **6.2** (a good fit), and no model with more freedom wins on AIC (H6 and H7 fit slightly better on log-likelihood, -80.23 and -79.88 against -80.61, which does not pay for their extra parameters).
- **No attacker bonus:** an attacker factor `k` has a best value of **0.990** with an approximate 95 % interval of **0.970 to 1.015**.
- **The width of the random term** is best at **0.32**, interval **0.24 to 0.54**, which contains 0.30. A term on the attacker only is rejected (AIC 1,206).
- **The strength formula `ships × condition` stands:** fitting `ships × condition^γ` gives γ = 1.1, interval **1.0 to 1.2**.
- **The earlier "outlier" was chance:** the first 10 seeds of the near-parity cell gave 9 attacker wins; the next 20 seeds gave 9 of 20.
- **Battles are exactly reproducible by seed:** four trials re-run on a later version of the driver gave identical fleet records.

## Method

- **Build and seed:** `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…532f`), Wine 9.0, Xvfb. One fresh process per trial, `SEED.TXT` = the trial's seed.
- **Fixtures:** the T1 fixture of `findings/2026-10-02-fleets-sail-and-drift.md` at Ptolemaic's seat (`FIX_P`) and at Carthage's (`FIX_C`), as in `findings/2026-10-02-naval-battles.md`, plus **`FIX_P2`**, made by `runs/experiments/fleet-battles/stage_p2.py`: at Carthage's seat Carthage splits 30 ships off its fleet (it keeps 60), ends its turn, and the autosave of Ptolemaic's next turn (0724) is the fixture. There Ptolemaic's fleet (70 ships, condition 60) and Carthage's (60 ships, condition 70) have **exactly equal strength, 420 v 420**, with the attacker role swapped.
- **Cells** (attacker v defender; strength `ships × condition / 10`): C50 370 v 441, C55 407 v 441, **P60 420 v 420**, **C60 444 v 441**, C65 481 v 441, plus the earlier P 441 v 666, C70 518 v 441, C 666 v 441. C55, C60, C65, P60 have 30 seeds each; the others 10.
- **Analysis** (`runs/experiments/fleet-battles/random_term.py`; its models H1 to H6 and the cell list were fixed before the new data came in, while H7 (the γ fit), the parameter intervals and the chi-square were added with the final 160 trials): the attacker wins when `k · A · (1 + ua) > D · (1 + ud)`, `ua ~ U(0, wa)`, `ud ~ U(0, wd)`; for each cell the probability that the attacker wins is computed on a fine grid and the binomial log-likelihood summed over cells; models are compared by log-likelihood and AIC; parameter intervals are the values within 1.92 log-likelihood units of the best.

## Observations

Saves and `trials.json` are in release `run-exp-naval-battle` (160 trials, 0 errors, 0 battles with both or neither fleet left).

| cell | attacker v defender (strength) | ratio | seeds | attacker wins | expected, literal model | z |
|---|---|---|---|---|---|---|
| P | 441 v 666 | 0.662 | 10 | 0 | 0.0 | 0.00 |
| C50 | 370 v 441 | 0.839 | 10 | 1 | 0.5 | +0.63 |
| C55 | 407 v 441 | 0.923 | 30 | 7 | 7.2 | −0.09 |
| **P60** | **420 v 420** | **1.000** | 30 | **10** | 15.0 | **−1.83** |
| C60 | 444 v 441 | 1.007 | 30 | 18 | 15.8 | +0.82 |
| C65 | 481 v 441 | 1.091 | 30 | 21 | 23.3 | −1.01 |
| C70 | 518 v 441 | 1.175 | 10 | 10 | 9.3 | +0.90 |
| C | 666 v 441 | 1.510 | 10 | 10 | 10.0 | 0.00 |

**Models** (log-likelihood over the 8 cells; AIC = 2·parameters − 2·logL):

| model | parameters | logL | AIC |
|---|---|---|---|
| H1 literal: wa = wd = 0.3, k = 1 | 0 | −80.61 | **161.22** |
| H2 term on the attacker only: wa = 0.3, wd = 0 | 0 | −603.09 | 1206.19 |
| H3 equal free width, k = 1 | 1 | −80.61 | 163.22 |
| H4 free wa and wd | 2 | −80.61 | 165.22 |
| H5 wa = wd = 0.3, free attacker factor k | 1 | −80.61 | 163.22 |
| H6 everything free (best: wa 0.2, wd 0.4, k 1.08) | 3 | −80.23 | 166.45 |
| H7 strength = ships × condition^γ, literal term (best γ 1.1) | 1 | −79.88 | 161.76 |

**Intervals** (within 1.92 log-likelihood units of the best): equal width **0.24 to 0.54** (best 0.32); attacker factor **0.970 to 1.015** (best 0.990); γ **1.0 to 1.2** (best 1.1). **Goodness of fit** of H1: Pearson chi-square 6.24 over the 8 cells.

**The first outlier.** In `findings/2026-10-02-naval-battles.md` the near-parity cell C60 had the attacker winning 9 of 10 (expected 5.3; about 1.7 % under the literal model). With seeds 11 to 30 added it is **18 of 30**, and the 20 new seeds alone gave 9 of 20.

**The two parity cells differ**, with Ptolemaic attacking at 420 v 420 (ratio 1.000) winning **10 of 30** and Carthage attacking at 444 v 441 (ratio 1.007) winning **18 of 30**. As a two-sample comparison that is a difference with p of about 0.04, **not corrected** for the eight cells looked at and treating the two cells as independent samples although equal seeds may share a draw; against the model each cell is within |z| < 2 (P60: z = −1.83).

**Determinism.** Re-running seeds 1 and 2 of cells C and P through a later version of `Game.attack_fleet` (which added click verification) gave fleet records identical to the earlier runs in all four trials: `determinism_check.json` in the release holds both versions of each record and the comparison.

## Inferences

- The research report's reading of the naval battle is supported as far as 160 battles can show: strength `ships × condition / 10`, a random 0–30 % factor **on each side**, no advantage for the attacker. The data cannot tell a uniform factor from another shape with a similar spread, and the interval for the width (0.24 to 0.54) is wide.
- With the width at 0.3, a strength ratio of 1.17 gives the stronger side about 93 %, 1.09 about 78 %, 1.0 about 50 %, and 1.5 or more certainty (the weaker side's largest product is 1.3 × its strength): the practical rule is that a 17 % edge nearly decides a battle and a 50 % edge decides it.
- The two parity cells that disagree (P60 low, C60 high) are the only hint of an effect beyond the model: in both, the side with **more condition and fewer ships** did better (66 % and 60 %), which a γ above 1 would produce; the fit prefers γ = 1.1 only slightly (AIC 161.8 against 161.2), so this is **unresolved, not found**. It needs more seeds in cells where the two sides differ in condition at equal strength.

## What this does not establish

- **One pair of fleets, one fixture turn, one seed range (1 to 30), calm sea, nothing aboard, war already declared, both fleets worn and unsupplied.** The random term may differ with supplies, the seat, rough sea, or cargo (T3: the carried army's `siegeStrength/50` term is untested).
- **The shape** of the random term (uniform assumed) and whether the same draw is shared between cells with equal seeds (several seeds gave the same ship loss in two cells): not tested.
- **The damage to the winner** (a fraction of ships and of condition, `findings/2026-10-02-naval-battles.md`) was not fitted here: this finding is about who wins.
- **The P60 versus C60 difference** is not explained and not shown to be real; γ is consistent with 1 but not pinned (1.0 to 1.2).
- **Wine-only.**

## Reproduction

```text
setup/setup.sh
python3 -m tests.make_fleet_battle_fixture                              # the T1 fixture (about 20 minutes)
python3 runs/experiments/fleet-battles/stage_cells.py                   # FIX_C
python3 runs/experiments/fleet-battles/stage_p2.py                      # FIX_P2
python3 runs/experiments/fleet-battles/trials.py P C C70 C60 C50       # 10 seeds each (with no cell named, all eight cells run)
python3 runs/experiments/fleet-battles/trials.py P60 --seeds 30         # about 25 minutes
python3 runs/experiments/fleet-battles/trials.py C60 --seeds 30 --from 11
python3 runs/experiments/fleet-battles/trials.py C65 C55 --seeds 30
python3 runs/experiments/fleet-battles/random_term.py                   # the fits
```
