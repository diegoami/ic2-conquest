# Remake v0.8.4: three known differences remain, and its commands accept what both interfaces refuse

**Status:** promoted by research PR #92 (merge `d8c8e39`), with the corrections below applied here on 2026-10-29.
**Tag:** [confirmed, partial]. Original-vs-remake differential runs under Wine, same start save and same orders in
both games. Not run on native Windows.
**Tasks:** conquest [#229](https://github.com/diegoami/ic2-conquest/issues/229) and
[#230](https://github.com/diegoami/ic2-conquest/issues/230) (tracker #228). Remake **v0.8.4**
(`d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`), `classical-faithful`. Original: `Imperial Conquest 2 fast
rollingsave seed.exe` (SHA-256 `354d8265…`), startup seed 12345. Harness: `difftest/`.

## 1. Build fleet still uses a different city (known since 2026-10-09)

`findings/2026-10-09-fleet-build-city-nearest-capital.md` found that the original builds at the free coastal city
nearest the capital, while the remake takes the first free one in world order. At v0.8.4 this is unchanged. From
the Rome 270 BC start, the original builds at **Caere** (city 82) and the remake at **Pisae** (city 71). The fleet's
size and the cost agree.

Evidence (run `run-exp-diff084-orders`, turn 0720): `fleet-10/original/a001.SAV` vs `fleet-10/remake/a001.SAV`;
`fleet-25/original-r2/a001.SAV` vs `fleet-25/remake-r2/a001.SAV`; `fleet-two/…/a001.SAV`.

## 2. The remake's engine commands accept orders that both games' interfaces refuse

These differences only appear through the remake's command layer: the CLI, scripts, and anything that submits
`GameSession` commands directly. A player using the remake's interface does not see them, because its dialog or
map click refuses the order as the original does. They matter for automation, and for any AI or tool that issues
the same commands.

| Order | Original | Remake interface | Remake command | Evidence |
|---|---|---|---|---|
| Recruit below battalion / 5 (1,000 heavy infantry) | the dialog cannot go below 1,200 (the arrows stop) | the Recruit dialog clamps to battalion / 5 (`RecruitUnitDialogModel`, `godot/UI/Dialogs/StrategyDialogModels.cs`) | `recruit-standing … 1000` is accepted: slot of 1,000 troops, 100 talents | run `run-exp-diff084-tooling`, `toy3-original-1` receipt ("stuck at 1200"); `self5-remake-1/a003.SAV` |
| Move an army toward a sea tile | the click does nothing | the map click does nothing (`godot/UI/MapClickRules.cs`: an army with a sea tile is "nothing at all") | `move` walks toward it as far as the shore (4 moves to (98,41); 1 move to (121,54)) | run `run-exp-diff084-orders`, `move-far` and `move-sea`: `original*/a001.SAV` vs `remake*/a001.SAV` |

The engine's own check for the recruit amount is only `troops > 0` (`RecruitStandingUnitCommandHandler`).

## 3. After the first End turn, the AI nations act differently (known families)

The same orders give identical states in both games up to the first End turn: tax 20, a move, and a 1,200 heavy
infantry recruit at Rome (run `run-exp-diff084-tooling`, `toy3b-original-1` vs `toy3b-remake-1`, checkpoints
`a000`–`a003`, 0 differences). Rome's own records also stay equal after it. Over that End turn (turn 0720 → 0721):
- six AI armies (records 3, 5, 8, 9, 12 and 13; 12 is Galatia's) and two fleets stand elsewhere;
- Bithynia, Celtiberia and Gaul queue different recruits (mobilization: Gaul 50 vs 63, Celtiberia 56 vs 73, Bithynia
  47 vs 45);
- the pending offer comes from Celtiberia in the original and from Seleucid in the remake;
- the 48 cities whose supplies differ all belong to AI nations: Gaul 24, Celtiberia 18, Bithynia 3 and Galatia 3
  (Acroinon, Gordium, Iconium). Their supply growth follows the different recruitment and, for Galatia, its army.

These are the AI recruitment and diplomacy families of #176 and #177; the remake was given no recorded original
draws here. Of the 54 cases of #230 batches 1 and 2 (6 of them give more than one order), 46 leave Rome's own records equal
after End turn. The other 8 keep the difference their order made at once (Build fleet site ×3, the sea-target
moves ×2, the ally relation ×3); End turn does not widen it. (Wording corrected after research PR #93.)

## Not covered

Fleet orders, mobilization and unit-level orders (#230 batch 3); battles (#231); multi-turn play (#232); random
outcomes (#233, `findings/2026-10-29-ai-fleet-hunt-absent-in-remake233.md` for the AI fleet). The test registry is
`difftest/REGISTRY.md`.

**Corrections (research intake, PR #92, 2026-10-29):** the first version said "seven AI armies" (six), left out
Bithynia's mobilization and Galatia's three cities, and said "52 single-order cases" (54: batch 1 has 49 cases,
not 47). The fleet-hunt finding it cites was on branch `research/diff084-stats233` at intake and reaches main with
that branch's PR.
