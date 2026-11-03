# The two own-port fleet rows are draws in both games; the remake lands an embarked army at home where the original sails it to a mercenary offer

**Tag:** [confirmed: inert Wine hooks with written RandSeed + remake seed sweeps and code]. Wine only.
**Task:** owner 2026-11-04, "yes do that": the open items of `2026-11-04-v092-followups.md` after research's intake (PR #189):
- the two own-port fleet rows left in the turn-seeded stays;
- Numidia t29–31, Rome's carried army.

Remake v0.9.2 `1723c673`.

**Tooling.** `difftest/probes/fleetphase_hook_run.py` now writes RandSeed after loading:
- `IC2_START_RANDSEEDS` = a JSON map {start stem: seed}, for an exact replay of the campaign's round;
- `IC2_START_RANDSEED` = one value for every start, to sample the original's draws from one state.

## 1. The two own-port fleet rows are draws

The starts are the original's state before End turn (`portstarts/`): Carthage game `t21-a01`, Gaul game `t39-a00` (turn 40
has no human orders). The v0.9.0 games logged no RandSeed, so both games are sampled over several seeds.

| Row | Original: fleet-phase hook, `IC2_START_RANDSEED` 11/22/33/44/55, 10 of 10 inert | Remake: `aiprobe` and `remake.run`, seeds 1–20 |
|---|---|---|
| Gaul t40, Carthage fleet 0 at Leptis Magna (111,93) | hunt scores 107, 98, 76, 108, 82. **It leaves for (140,89) with 2 of 5 seeds** (hunt > 100), and stays otherwise | branch "hunt" with 4 of 20 seeds, "port" otherwise |
| Carthage t21, Seleucid fleet 0 at Aradus (220,65) | port 261, hunt −10000 every time. **It leaves (to (220,66)) with 1 of 5 seeds**, and stays otherwise | from the original's post-orders state, it stays with all 10 seeds tried (1–10) and with 12366. In the anchored chain (the end of t20, the human's orders, End turn) it leaves with 2 of 11 (seeds 3 and 12366), and stays otherwise |

Both are random in both games. Leptis Magna is the AI hunt roll (`> 100`), like the earlier Utica row. At Aradus the
original's draw that moves the port-branch fleet one tile is not identified, but the original takes it too. **With gap C
(`2026-11-04-v092-followups.md` §2), no own-port fleet row is left unexplained by a draw.**

## 2. Embarked army: the remake ignores the mercenary run's offer and lands the army at home

**Original.** Numidia game, turns 29 and 30. The run `hooks-route-num-v1` (`patches/fleetroute_hook.py`) uses the campaign's
logged RandSeed. Both turns are inert, and the hooked autosaves equal the campaign's armies and fleets, so they are exact
replays.
- Rome's army 8 (6,460 troops) is aboard fleet 4.
- At its seat, DBA8's aboard branch writes the carrier's route (probe 4, after the `call FUN_0044cd08` at 0x44DBF2). The target
  is **(111,69) Syracusae**, and the route (109,63), the same in both turns.
- The fleet phase then follows that stored route (port 89, then 111). The army lands at (110,64) on turn 31.
- Syracusae holds two mercenary offers, pool slots 31 and 40 (3,367 and 3,223 light infantry).
- The decide inputs (`hooks-decide-num-v1`): city target 117 Vindobona at score 42 and 54 tiles, home 85 Rome, supplies 64
  against 6,460/500 = 12. That is the E84C branch, the mercenary run. So the walk at Syracusae is E84C's walk to the offer.

**Remake.** `probes/1723c673-num-t30pre-seed12375`:
- The decision for army-8 is `MercenaryRun`, city vindobona, score 42, the same as the original.
- The log reads "request carried-army landing (101, 43) with army-8", that is **Rome, the home city**.
- `AiMilitaryPhase.ProposeArmyTree`'s embarked branch (Classical navigation) maps the decision to a landing target:
  - the attack city or the attack army;
  - `MercenaryRun` only with the `MarchAtCityTarget` continuation;
  - otherwise **`_ when decision.Resupply?.City`**.
- A mercenary run without a city continuation therefore lands the army at its resupply or home city. The offer destination
  (`AiArmyTargetTree.MercenaryRunDestination`), which the land path uses (`AiMilitaryPhase.cs:416`), is never consulted.

The original's fleet sails south three turns running, and the remake's turns back. These are the Numidia t29–31 Rome army and
fleet rows (4 of them).

**Fix direction:** under Classical navigation, an embarked army whose decision is `MercenaryRun` requests its landing at the
mercenary run's offer city (`MercenaryRunDestination`), as E84C's walk does through DBA8's aboard branch. The resupply city is
then used only where the original's tree walks home.

## Open

- The draw that moves the Aradus port fleet one tile.
- Greece t21 (`2026-11-04-v092-followups.md` §5): the remake's state change during the round, not identified.
- Numidia t24, t32.

## Evidence

**Data:** `runs/experiments/data/run-exp-longrun-v092/`
- §1: `hooks-fleet-port-seed{11,22,33,44,55}-v1`, `port-rows-original-seeds-v1.txt`, `remake-seed-sweep-v1/`
  (`*-seed*/ailog.txt`, `carthage-t21-fleet-ends.txt`, the `carthage-t21-chain-seed*` runs);
- §2: `hooks-route-num-v1`, `hooks-decide-num-v1`, `probes/1723c673-num-t30pre-seed12375`.

**Saves:** release `run-exp-longrun-v092` (`port-and-carried-army-saves.tar.gz`). Starts: `portstarts/carthage-t21pre.SAV`
(= the Carthage game's `original/t21-a01.SAV`), `portstarts/gaul-t40pre.SAV` (= the Gaul game's `original/t39-a00.SAV`),
`decidestarts-num/num-t29pre.SAV`, `num-t30pre.SAV`.
