# Task: battles B7 (every button and the human order set) and B12 (scripted plans against Computer general) (queued 2026-10-05)

## Scope
This task protects: **the driver's battle orders and the honesty of the plan comparison.**
- Every battle order the driver issues is verified on the battle block before the next one; no click goes unverified, and End turn is
  never clicked a second time without proof that the first did nothing.
- A plan's result is compared with Computer general on the same seed, and the pairing is proven: the same start state and the same
  RandSeed at battle start. A difference is never reported as a plan's effect when it may be RNG divergence.
- Every number traces to a tracked output and a released save (CLAUDE.md rules 5 and 6).

Forbidden results (any one fails the task, and a reviewer will block on it):
- a battle order reported as done without a block read-back showing its effect (position, target word 9, shots word 8, header);
- a blind second End turn, or a retry beyond two for any order;
- the Surrender box or the Offer of peace answered other than the trial's plan says;
- a plan-versus-Computer-general difference claimed without the paired start state and seed proven identical;
- a significance claim not computed as stated (McNemar on the discordant pairs, with the counts shown);
- a measured output overwritten or deleted, a binary in git, or a write to another repository.

## Read first
- `CLAUDE.md` (rules 1-6).
- `docs/proposals/battles.md`: §3, §4 B7 and B12, §5 and §7.
- The findings `findings/2026-10-04-tactical-battle-sweep.md` (B5/B8) and `findings/2026-10-04-battle-exchange-hook.md` (B11: the hook
  logs every draw, so a played battle's exchanges are known exactly).
- The decompiled report `docs/reports/2026-10-04-decompiled-tactical-battle-rules.md` in the research repo (read only): the AI general
  moves types in the order HI, HC, LC, LI, Ar; melee, shot and rout formulas; focus fire.
- The code: `harness/driver.py` (`play_battle`, `battle_state`, `end_turn_proven`), `state/battle_block.py`,
  `runs/experiments/battles/`.

## Work
Branch `experiment/battle-orders-b7-b12`. Data in `runs/experiments/data/run-exp-battle-orders/`; binaries in release
`run-exp-battle-orders` as per-batch tar.gz archives with a tracked manifest.

### B7. Every button and the human order set
1. **Survey.** Every toolbar button (by tooltip) and every control (`Game.controls`) on the battle screen is clicked once on a lab save,
   with its effect read from the block and a screenshot: End turn, Computer general, Surrender (the "Are you sure you want to surrender ?"
   box: **No**, then, in a separate trial, **Yes**, with what is captured), and any others found (B8's layout run lists 8 tooltips).
2. **Human order set.** Place, move, melee, shoot and end turn, by mouse. Each order is verified on `Game.battle_state()`, retried at
   most twice, and followed by no second End turn unless the first provably did nothing.
   - Driver orders: `battle_place`, `battle_move`, `battle_attack`, `battle_shoot`, `battle_end_turn`, `battle_surrender(answer)`.
   - Offline tests in `tests/test_battle_orders.py`, with a fake battle where a wrong cell or a silent no-op fails the order.
3. **Acceptance:**
   - a table of buttons with their effects and screenshots;
   - each order tested once live;
   - 5 played battles in a row complete headless (Rome driven by the bot, Gaul by Computer general).

### B12. Scripted plans against Computer general
**Proposed definitions** (the plan names these but does not define them; the player may adjust them before the work starts):
- `P-HOLD`: Rome's units never advance. Archers shoot the nearest enemy in range. Every unit melees only an enemy that is already
  adjacent.
- `P-FOCUS`: every Rome unit that can reach or shoot the same enemy unit attacks it, until it routs or leaves; then the next. The target
  is the enemy with the fewest troops among the nearest. The plan says focus fire `f = 4` gives attacker loss ×1/5 and defender ×13/5 [D].
- `P-CAV`: the cavalry (LC, HC) go around a flank and attack enemy archers first, then the nearest enemy. The infantry hold, as in P-HOLD.
- `S-PAR`: MIX-RG, which is FLD-RG with both armies as they stand in the research start save, no edit (the B11 inertness cell), on
  seeds 1-30.
- **Two hard sweep cells:** `li>hi` one/one and `ar>li` one/one, the B5 cells Rome lost 0 of 9. Seeds 1-10 each.

Steps:
1. **Pairing.** For each plan, cell and seed, run the plan, with Rome driven by the bot and Gaul by Computer general. Pair it with Rome on
   Computer general, on the same lab exe, seed and start save.
   - Prove the start block is identical.
   - Use the B11 hooked lab exe for both runs of a pair. Its log gives each run's draws and exchanges exactly, so the point where the
     two runs diverge is known.
2. **Played-battle repeatability.** The plan says repaint routines write RandSeed. Run one plan twice on the same seed (with the hook)
   and report whether the played battle replays exactly, and if not, which draw site first differs.
3. **Acceptance:**
   - a paired table per plan and cell: wins, losses, the discordant pairs, the McNemar statistic and p (exact binomial when the
     discordant count is small);
   - the time per played battle;
   - one win and one loss saved per plan.
   - The finding answers "can the bot drive or auto-play the battle screen in each case": auto-play from B5 (all 25 pairings × 3 sizes),
     manual driving from B7 and these cells only. Manual driving of all 25 pairings is not claimed.

### Findings draft
`findings/2026-10-05-battle-orders-and-plans.md`, in the research-report format.
- Sections: Method, the button table, the order set with its tests, the paired tables, repeatability, and "What this does not
  establish": Wine-only; the lab build; 30 and 10 seeds describe these cells, not the game at large; the plans are the bot's, not
  optimal.
- Mark every claim `[O]`, `[D]` or `[R-code]`, and cite saves by bare filename.
- A claims audit recomputed from raw saves and hook logs, with 0 mismatches.

## Done when
- The button survey table and screenshots are tracked and released, Surrender No and Yes included.
- The six driver orders exist with offline tests (a wrong cell or a no-op fails), and each passed once live; 5 played battles in a row
  completed headless.
- The paired tables for P-HOLD, P-FOCUS and P-CAV on S-PAR (30) and the two hard cells (10 each) are tracked. Each pair's identical start
  is proven, and each run's hook log is checked (chain unbroken).
- The repeatability result is in the finding.
- The claims audit gives 0 mismatches, and the coverage.md rows for the battle orders are updated with saves.
- CLAUDE.md rule 6 holds throughout.

## Rules (CLAUDE.md rule 6, in full)
Measurements are kept, committed and pushed as they are made, and never deleted.
- Every text output a finding or a PR may cite goes under the tracked data folder above.
- Commit and push after each batch, and at least every 30 minutes.
- A re-run writes new files beside the old ones; use `common.write_new` / `common.keep`.
- Saves, screenshots and exes never go in git: their SHA-256 go in `SAVES.sha256`, and the files go to the release.
- If a release call is refused, keep the artifacts and report the exact command.
- Never print `IC2_RELEASE_TOKEN`.

Driver pitfalls:
- Hover before clicking, verify every order's effect, retry at most twice, and never retry End turn.
- Use your own Xvfb display and game folder, and kill only your own pids.

## Deliverables
One PR against main, "battles: B7 order set and B12 scripted plans". Its body maps every Done-when line to its evidence.
- Do not merge, and do not run the reviewer.
- If something blocks (an order that cannot be driven headless, pairs that do not replay, or a decision only the player can make), stop,
  commit what was measured, and report.
