# Long runs, original vs remake v0.9.0 (88c1989b), owner 2026-11-02

Owner's choice: anchored + free-running, 4 starts x 40 turns (Rome, Carthage, Seleucid, Gaul), rule bot rulebot-1 as
the human, seed 12345. Runner: `run_all.sh` (campaign, then `difftest/anchored.py`, archive, release
`run-exp-longrun-v090`). Data: `runs/experiments/data/run-exp-longrun-v090/`.

## Recheck of the registered tests on 88c1989b (remake side only)

`python3 -m difftest.recheck 88c1989b --version v1` → unchanged 113, FIXED 11, REGRESSED 11, CHANGED 4
(`runs/experiments/data/run-exp-recheck-88c1989b/report-v1.md`).

The 11 REGRESSED and 3 of the 4 CHANGED are one field: the human (Rome) fleet's condition after End turn, 96 in the
original vs 97 in the remake (93/94 and 95/96 in two of them). Not a rule change:
- the staged saves share the fleet (id 2 at 101,46, 30 ships, condition 97); the original's End turn takes 1 point
  (the storm pass's light branch, 0 or 1 near the coast);
- `join-20-ok` (join-armies + End turn), remake seeds 1-12 on 88c1989b: 96 ×9, 97 ×3; on v0.8.4 (d9cc71bc) seeds 1-6:
  96 ×2, 97 ×4. Both outcomes on both builds;
- the default-seed outcome flipped at T247 (d8e7a646, faithful fleet phase): its fleet phase draws from the same
  stream before the storm pass. Pins: d9cc71bc, 1622407e, dab3a2ea → 96; d8e7a646 and later → 97. End turn alone → 96
  on every pin (the order before End turn shifts the stream).
So these tests compare one random draw; their v0.8.4 "same" was a coincidence. The 4th CHANGED (`walk-gaul-army9`)
is Gaul's relations after End turn (AI diplomacy, not our order).
Probe: the scratch script ran `remake.run` with `seed=` over the staged `join-20-ok.SAV`; outputs not kept beyond the
counts above (rerunnable in seconds).

## Gap C hook (owner "do all", 2026-11-02)

`fleetphase_hook_run` from copies of the original's end-of-turn saves (named by game and turn so the hook's folders are
unique): gaul t30 end (Carthage fleet at Utica, turn 31), gaul t39 end (Leptis Magna, turn 40), rome t16 end (Ptolemaic
fleet at Alexandria, turn 17). Output `hooks-fleet-v1/`.

## Seleucid turn 26 (open, harness) — r1-r5

Every run stops at the checkpoint after turn 26's End turn (deterministic: same seed, same orders). r5's save-timeout
diagnostics (`seleucid-rulebot1-40t-r5/original/receipt.jsonl`, `t26-a01-*.png`):
- seat 2 (Seleucid), battle flag 0x4A0B7C = 0;
- a window "Ptolemaic  v  Seleucid          Seleucid to move units." at (5,103), 448×414, never painted (black);
- main window title without "Seleucid's turn"; the Information pane shows Week 5 Spring 269 BC news;
- raising the battle window, Computer general and 30 End turn clicks change nothing (the title stays the same); File > Save
  does not respond.
Loading the run's AUTO0746.SAV shows no battle (probes/battle-t26). The battle state is not in the save, so reproducing it
needs the 22-minute game. Not pursued further; the analysis uses r1's 25 turns. Two end_turn changes were tried and reverted.
