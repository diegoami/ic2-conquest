# AI audit #195, pass 0: inventory and coverage matrix of all original AI behaviour against remake v0.9.4

**Tag:** [inventory: documents and code read on both sides; end-to-end levels cited from earlier measured reports]. No new
measurement in this pass.
**Status:** early draft for research (#195 asks for the matrix to be published first, so that omissions are visible).
**Task:** research issue #195, delegated by ic2-research on 2026-11-04 at the owner's request.

**Pins.**
- **Remake:** v0.9.4 = `168dbc04`, which is the tag. The audit baseline is v0.9.3 `a44c42fc`.
- **Original:** the seeded fast rollingsave build, the same exe as every earlier report. All runtime evidence is Wine;
  none of it establishes native Windows parity.

## How the matrix was built, and how far to trust it

**Six read-only passes**, one per area (A–F below). Each pass read:
- research's `docs/rules-specification.md` sections, the research reports and `docs/findings-intake.md`;
- the remake source and test names at `168dbc04`, and the remake's docs (tasks, release plan, investigations);
- this repo's findings and `difftest/REGISTRY.md`.

**Spot-checks.** The session checked these code-level differences in the remake source itself:
- A07/C07/E17: economy, then capital defence, then the hire pass, then a scored loop that holds the war, alliance and trade
  candidates, then fleets (`AiTurn.cs` 150–391);
- A36/C34: `maxActionsPerTurn: 24` in `classical-faithful.json`, enforced at `AiTurn.cs:241`;
- B03: `AiEconomyPhase.ProposeMobilization`, called from `AiFaithfulEconomy.cs:113`, keeps the designed `IsThreatened`
  restraint. Its own comment says "the original's FUN_004504f4 has no such test";
- D05: `AiFaithfulEconomy.cs:647` treats a city as busy when it has a fleet under construction of any nation.

**Not yet checked.** The other rows are as the passes read their sources. Pass 1 re-reads every row it acts on.

**Support levels**, from the owner's comment on #195:
- **i:** the original routine was inspected;
- **ii:** its callers, conditions, state lifetime and downstream effects were traced;
- **iii:** the remake implements the complete behaviour;
- **iv:** the behaviour was verified end to end against the original. That means the original against the remake from the
  same state, in Wine, and it always names the remake pin it was measured on.

Decompiled code alone never reaches iv.

**Categories:**
- **MATCH:** matches, with the cited source;
- **DIFF:** a confirmed difference, invented restrictions included;
- **AMB:** ambiguous or partly investigated;
- **MISSING:** an original behaviour with no remake counterpart;
- **APPR:** an owner-approved or Improved difference;
- **AUTH:** a remake-authored feature with no original equivalent;
- **UNAUD:** not audited yet.

A row is never MATCH unless a specific document states it.

**Tests.**
- **mirror:** a remake test built from the specification's numbers. It pins the implementation, not the original.
- **discr:** a test that discriminates against original captures or measurements.

Almost all remake AI tests are mirror; the discriminating evidence lives mostly outside the remake (difftest, Wine hooks,
anchored replays).

**Pin caveat for level iv.** Many iv rows were measured on remake main `05b02936`, `8e2d9053` or `e20a6488` (2026-10-30/31),
not at `168dbc04`. The v0.9.4 recheck (`2026-11-04-remake-168dbc04-recheck.md`) re-measured unit positions on 19 games and
the 139 registry tests, not economy, supply, hire or diplomacy details. Each row names its pin where it matters.

Short names:
- **RS** is research `docs/rules-specification.md`; **R/** is research `docs/reports/`; **F/** is this repo's `findings/`.
- Remake symbols are under `src/IC2.Engine/`. Test names are abbreviated.

## Summary

| area | rows | MATCH | DIFF | AMB | MISSING | APPR | AUTH | UNAUD |
|---|---|---|---|---|---|---|---|---|
| A: seat loop, scheduling, draws, authored automation | 43 | 12 | 4 | 13 | 0 | 3 | 8 | 3 |
| B: economy, recruitment, mercenaries, supply | 35 | 17 | 3 | 9 | 0 | 1 | 2 | 3 |
| C: army phase | 34 | 20 | 2 | 4 | 1 | 1 | 2 | 4 |
| D: fleets | 33 | 18 | 2 | 9 | 0 | 0 | 2 | 2 |
| E: diplomacy | 41 | 20 | 3 | 13 | 1 | 1 | 1 | 2 |
| F: tactical AI and battle transitions | 43 | 30 | 1 | 3 | 0 | 1 | 7 | 1 |
| **total** | **229** | **117** | **15** | **51** | **2** | **7** | **22** | **15** |

Updated 2026-11-05 after X3 (`2026-11-05-x3-seat-replay-remake.md`): A12, C02 and F34 go from AMB to "MATCH (Tactical) / DIFF (Instant)", D30 from AMB and B33 from UNAUD to MATCH (Tactical).

These counts are taken from the tables below; a mixed row (for example "MATCH / AMB") counts once, under its first
category. Many MATCH rows reach level iv only at an older pin, and their remake tests are mirror only. The battle AI (F) is the best covered. Its 318 recorded tactical series matched state and draws at `b593c6e2`,
which `168dbc04` contains; no later commit touches `Battle/Tactical/General/*`. The strategic phases have many MATCH rows
from 80-round comparisons at older pins, and their open questions concentrate in **ordering and timing inside a seat**.

## Cross-cutting differences (the same cause seen from several areas)

These are the outcome-changing items. Pass 1 takes them first, one finding each.

1. **X1. Phase order inside a seat** (A07, C07, E17).
   - **Original:** `FUN_0044fa20` runs diplomacy (`FB7C`), then the economy (`FFBC`), then armies (`F31C`, whose entry is
     capital defence `EFC8`), then fleets (`F608`).
   - **Remake:** the economy and capital defence run first, then the hire and support pass, then a scored loop in which
     the war, alliance and trade candidates compete with the armies.
   - **Consequence:** a war declared this seat is not counted in the threat budget (15,000 per war), the capital-defence
     radius (19 at war, 9 otherwise), the hire gate ("at war with someone") or the busy test.
   - **Code:** confirmed on both sides. **Measured (2026-11-05, the economy only):** in 8 of the 11 seats where both games start the same war, the original runs the gap call FUN_004504f4 (mobilise and/or raise recruits) in that seat and the remake does not (3 by mobilising, research PR #207 follow-up for the other 5); this attributes 3 seats' position rows (`2026-11-05-x1-war-before-economy.md`). Radius, hire gate and busy test: not measured.
2. **X2. Support and hire pass timing** (A09, B22, C08).
   - **Original:** `E41C` is each army's first call inside `F31C` (`0x44F366`), so later armies see the earlier armies'
     moves, battles and treaties.
   - **Remake:** in Instant or headless play (the CLI default and every anchored replay), one pass covers all armies up
     front. The per-army pass runs only for Tactical human battles with a living human seat, outside watch mode, under classical army navigation (`GameSession.cs:2163`, `2398`; research PR #206).
   - **Consequence:** this is the leading candidate for the Greece t21 resupply flip and for some of the 10 own-capital
     stays.
3. **X3. A seat replayed after a human battle** (A12, A13, B33, C02, D19, D30, E18, F34).
   - **Original:** the battle flag `0x4A0B7C` stops `F31C`; the fleet phase still runs; the whole seat then runs again on
     the partial state. Phase 1 draws a second, fresh war roll, alliance roll and trade pass, the economy runs again
     (twice in week 11), and the fleet route from pass 1 survives until the round tick.
   - **Remake:** with Tactical battles (T255–T257, T277), the pass is kept and then restarted. The named RNG streams
     (`ai.faithful-economy:{nation}:{turn}`, `warRoll:{nation}:{turn}`) repeat pass 1's draws, and `OriginalFleetRoutes` is
     a new store per call.
   - **Instant mode:** there is no interruption at all.
   - **Evidence:** the original measured 5 seats in 80 rounds (R/2026-10-31-ai-seat-replayed-after-human-battle.md). The
     remake has never been measured end to end on this path, because every anchored replay runs Instant.
4. **X4. The action cap and early stops** (A36, A37, A38, C34). These are remake-authored and still active under Faithful:
   - 24 actions per seat, shared between armies and diplomacy or trade candidates;
   - a no-op non-march action ends the seat;
   - an exact tie is broken with a random draw.

   The original has none of these. A large late-game seat can leave its last armies unplayed; check the three 264 BC games.
5. **X5. Capital defence with a pending human battle** (A14, C06, F35).
   - **Remake:** implemented by T277.
   - **Original:** what it does with a second attack on the human in the same pass is not established. No stored row
     exercises the case.
6. **X6. Instant human battles** (F02, F01). The CLI default resolves human battles with the instant resolver, which has no
   original counterpart for human battles, so every anchored replay compares strategic AI under that model. This is
   APPR/AUTH as a design, and it is the reason X2, X3 and X5 have no end-to-end evidence.

## Single-area differences and gaps worth a finding

- **B03 (DIFF, authored restraint under Faithful):** a ready slot at a city with a hostile army adjacent is not mobilised.
  The original mobilises (`FUN_004504f4` has no such test).
- **B14 / D01 (settled 2026-11-04):** research read `FUN_00450768` (PR #197): launched +1 and under construction +4, as the
  remake has it. The spec was wrong and is corrected. Now MATCH at levels i and iii.
- **D05 (DIFF):** the build-city busy test counts any nation's fleet under construction; the original counts only the
  seat's own.
- **D09 (DIFF):** a fleet launched into a reused, compacted index keeps the old fleet's leftover moves in the original, so
  it can hunt or reach port on its launch turn. In the remake it has 0 moves.
- **C23 (MISSING):** the `D734` end-check tail for a city not at war (`F6D8` resupply and purse normalisation at the walk's
  end) does not exist for AI walks in the remake. A mid-seat supply transfer is lost, which changes the city stock that
  later armies' `E670` reads.
- **C22 (AMB):** `D734` contact at callers never measured: the `E84C` run walk, the `F4A3` chase continuation and the `F47C`
  resupply walk. The original would besiege or attack on arrival; the remake does not opt in.
- **C18 / D15 (AMB):** `D9A8` case (b), an adjacent ferry that embarks, is never measured in play.
- **E28 (AMB):** the remake's human peace-offer gate adds a `!Battle.Capped` condition and measures strength with
  `ArmyPower.Compute`; neither is cited.
- **E32 (DIFF):** a treaty reseeds `RandSeed = winner + loser` in the original; the remake does not.
- **A19 / F31 (APPR):** the remake uses named SplitMix streams instead of one global LCG. This is owner-approved, but it means
  parity can only ever be distributional, and anchored replays need `--turn-seed`.
- **F26 / F28 (AMB, code only):**
  - a mid-pass takeover of the computer general looks unreachable in the remake;
  - general flags survive a reload in the remake but are cleared in the original.
- **E23 (MISSING):** loading a save re-announces a stored offer in the original; no remake counterpart was found.
- **A30 (DIFF, APPR):** when a human falls, the remake keeps playing in watch mode; the original ends the game. This was
  approved on PR #375.

## Open end-to-end rows, placed

| row (game, turn) | where it sits | state |
|---|---|---|
| 10 own-capital stays (Antioch ×4, Alexandria ×2, Ecbatana ×2, Carthago, Rome) | open | **pass 1: not X2 (Tactical = Instant); draw-sensitive in the remake; unattributed** |
| Greece t21 resupply flip (Seleucid army 2, Antioch → Aradus) | X2 (C08) | **attributed (pass 1): matches the original in Tactical mode on 3 seeds** |
| Greece army at (112,70): Bithynia t30–31, Media t31–32; Numidia t24–25 | C20 (T277) | fixed on 168dbc04; not hook-confirmed |
| Numidia t32 | — | not attributed |
| Celtiberia t15/t17 (Pella capital army) | A18 war-roll stream, or X1 | candidate |
| Celtiberia t37 (0-move army at Ambracia) | C22, or state | candidate |
| Late-year AI-phase differences (266–264 BC) | all areas | not classified |

## The matrix

The six area tables follow as the passes returned them, lightly edited for length. Where a row appears in more than one
area, its cross-reference is in the X list above.

### A. Seat loop, scheduling, random draws, authored automation

| id | behaviour | original | remake | levels | cat | difference / uncertainty | tests |
|---|---|---|---|---|---|---|---|
| A01 | Seat advance `pos=(pos+1) mod 16`; the order table is never rewritten | TPremierForm_EndTurn; FA20 tail | Calendar/SeatRotationSystem | i, ii (RS "Seat and turn order"); iii | AMB | The remake skips Eliminated seats (designed, T17); the original advances past them | mirror |
| A02 | New Game turn-order shuffle: naive swap with Random(16) | FUN_00448AA4 | Calendar/NewGameTurnOrder | i, ii; iv (original only) | APPR | Algorithm parity, not seed parity (owner 2026-10-03) | mirror |
| A03 | Round tick after the last seat's wrap: cities, armies (moves overwritten), fleets, weather, calendar | FUN_004514ec | SeatRotationSystem → RoundTick; TurnPhase order | i, ii; iii | AMB | Tick order not isolated end to end against AI state | none |
| A04 | Dead-record compaction on dispatcher entry and before every AI seat, never before a human turn start | 451FDC → 44ADB0 | Armies/ArmyTableSweepSystem (SeatStart) | i, ii; iii | AMB | Looks equivalent; not compared | mirror |
| A05 | Dispatcher loop: while the seat is a computer, not over, flag 0x4A0B7C = 0; break when no human | 451FDC, 449050 | GS.PlayUntilOneFullLapOrRepeat | i, ii | AMB | The remake is lap-based; termination semantics differ | mirror |
| A06 | Per-seat guard: skip the AI's work when unity ≤ 0, still advance | FA20 | AiTurn.Run (Eliminated / not AI) | i, ii | AMB | A living nation with unity ≤ 0 would still act in the remake; reachability not audited | none |
| A07 | Phase order: diplomacy, economy, armies, fleets | FA20 | AiTurn.Run (economy first; diplomacy inside the scored loop) | i, ii (both sides) | DIFF | **X1** | none |
| A08 | Armies one at a time in table order, count latched at 0x44F32F | F31C | OriginalArmyOrder (T253) | iv (R/2026-10-31-army-order-within-a-seat: 678/679, at 8e2d9053) | MATCH | — | mirror |
| A09 | `E41C` support and hire as each army's first call | F31C 0x44F366 | AiMercenaryHirePass.Run up front; per army only with Tactical human battles, a living human seat and no watch mode (GameSession 2398) | iv (merges176: 2 army-order differences; Greece t21 Instant vs Tactical, 3 seeds, pass 1) | DIFF | **X2** | mirror |
| A10 | Capital defence at F31C entry | F31C 0x44F32A → EFC8 | AiCapitalDefence.Run | i–iii; partial iv (decisions report: 0 differences) | AMB | 10 own-capital stays open | mirror |
| A11 | Phase-mode flag DAT_004a0340 (0 armies, 1 fleets) | F31C/F608 | none | i | UNAUD | Readers not traced | none |
| A12 | A battle with a human interrupts and replays the seat | 0x4A0B7C; F31C 0x44F348; FA20 0x44FA56 | AiPhaseBattleGate (Faithful Tactical only) | iv original; iii remake; iv remake Tactical (x3-seat-replay-v1: 5/5 seats, 13/15 runs; the 2 misses are battle winners) | MATCH (Tactical) / DIFF (Instant, no replay: 3 of 5 seats differ) | **X3**; no interruption under Instant | mirror |
| A13 | The replayed pass draws fresh Random values and reruns the economy | FA20 second call | named streams per (nation, turn) | ii (remake code) | UNAUD | **X3**: the same draws repeat; x3: no roll fired in 30 runs, still unmeasured | none |
| A14 | Capital defence continues with a human battle pending | EFC8 under the flag | AiCapitalDefence continuePending (T277) | i–iii | AMB | **X5** | mirror |
| A15 | Which battle kinds set the flag (siege of a human city, naval) | 437DE4 callers | gate: AttackArmy on a human army only | i | UNAUD | Interrupts may be missing | none |
| A16 | Stale walk word carried from E84C into the same army's EBE8 | F31C/E84C/EBE8/DB38/D9A8 | OriginalArmyIntermediateSearchFailed (T276/T277) | iv (v0.9.4 recheck: Numidia t37, Celtiberia t39–40) | MATCH | Other carry-overs not measured | mirror |
| A17 | Seat-local scratch state: one-pass trade swap, first-sweep war leaders, fleet routes | FB7C; F608 | OriginalTradeSwapPass; OriginalFleetRoutes | iv for the swap (8e2d9053) | MATCH / AMB | Routes across a replayed pass (**X3**) | mirror |
| A18 | War Random(10) at most once per seat; alliance Random(20) | FB7C 0x44FD2F/0x44FD61 | ProposeOwnWarDeclaration; ProposeOwnAlliance | iv for candidates: 833/833 | MATCH / APPR | Different generators; 21 first divergences are rolls | mirror |
| A19 | One global LCG stream; treaty and TBattlePols reseed | 40284C; 450C68 | SplitMix64 ForStream | i, ii | APPR | Distributional parity only; no reseed (E32) | mirror |
| A20 | Fleet strength jitter Random(4)×v/10 per evaluation | 44AA54 | OriginalFleetHunt; FleetPower | iv distributional (gap C was a seed artefact) | AMB | — | discr (storm/naval) |
| A21 | Recruitment draws (type buckets, troops) | 4501F4, 4504F4 | AiFaithfulEconomy.RollType/RollTroops | iv for counts (265/265) | MATCH | Draws not compared | mirror |
| A22 | Order city chosen once per turn | 4502E0 at 0x450664 | PlaceOrders | iv (economy report) | MATCH | Not re-measured on 168dbc04 | mirror |
| A23 | Week-11 tax, computer seats only | FFBC | NextTaxRate | iv 113/113 | MATCH | The zero-tax rule never fired | mirror |
| A24 | Pending offer: rolled and shown only at a human seat's start; type byte keeps residue | 452034 | PendingOfferSystem (SeatStart, human) | iv for the residue (late-replays §2) | DIFF (cosmetic) / AMB (timing) | The remake's human SeatStart may run at the human's End, before the next orders | mirror |
| A25 | Mobilisation asymmetries (AI radius 5, new army 1 move, state 24) | 4504F4 | MobilizationReadiness / ReceivingArmy | iv 1,059/1,059 | MATCH | — | mirror |
| A26 | The End-turn warning never blocks an AI seat | 45AF00 | not consulted | i, ii | AMB | Equivalent by construction; no document says so | none |
| A27 | Free AI mercenary hire | E41C | AiMercenaryHirePass | iv 1,192/1,200 | MATCH | Timing: **X2** | mirror |
| A28 | AI deficit floor and 8-order cap | 4504F4 | AiFaithfulEconomy | iv 265/265 | MATCH | — | mirror |
| A29 | Human fall check at turn start (5 reasons) | 452034 → 44C8F0 | GS.DepositActiveHumanSeat… | iv (Seleucid t26) | MATCH | — | mirror |
| A30 | After a human fall: End of Game, then idle | THumanFalls | watch mode | iv | DIFF / APPR (PR #375) | The remake keeps playing | mirror |
| A31 | AI deposition: quarterly, 1 in 9, debt test | 451B40 → 44C8F0 | AiDepositionHandler | i, ii | AMB | Draws only for nations in debt (assumed); draw order unknown | mirror |
| A32 | All-AI game impossible in the original; observer via a patched build | 449050 | AiGameRunner, watch mode | iv (late-replays §4) | AUTH | — | mirror |
| A33 | AI–AI treaty takes effect inside the battle path | 0x44B1C4 → 450C68 | PeaceTreatySystem (applied immediately, Faithful) | iv for the difference at 8e2d9053; iii | AMB | Fixed; not re-measured | none |
| A34 | Human peace-treaty box raised during the AI phase | TBattlePols | GS pending peace offers | ii | AMB | Modal during the phase vs deferred prompt | mirror |
| A35 | Weekly moves overwrite; a −1 army is frozen until the tick | 4514EC | import clamp to 0 | ii | AMB | Whether any guard tells 0 from −1 is not checked | none |
| A36 | Action cap of 24 per seat | none | MaxActionsPerTurn (classical-faithful.json) | iii | AUTH | **X4** | mirror |
| A37 | A no-op non-march action ends the seat | none | AiSubstantiveState | iii | AUTH | **X4** | mirror |
| A38 | Exact-tie random choice among candidates | none (table order) | AiTurn.Select | iii | AUTH | **X4** | mirror |
| A39 | Personality profiles | none | AiPersonalityProfile | iii | AUTH | Default 500 in Classical; designed paths only | mirror |
| A40 | Stall tracker | none | AiStallTracker | iii | AUTH | Metric only | mirror |
| A41 | Barbarian seat and arrivals | none | AiTurn.RunBarbarian; Barbarians/* | iii | AUTH | italy-500bc-barbarians only | mirror |
| A42 | Improved/designed preset | none | AiEconomyPhase, AiMilitaryPhase.Propose | iii | APPR | — | mirror |
| A44 | FA20's first call, `FUN_0045c084` (research intake) | `TPremierForm_SetTurnTitle` @ 0045c084 (the decompile's function header) | window caption | i | not AI | The turn-title caption update, so no audit row is needed beyond this note | — |
| A43 | Human auto-support | none | Economy/HumanAutoSupport (T265) | iii | AUTH | A human-side asymmetry | mirror |

### B. Economy, recruitment, mercenaries, supply

| id | behaviour | original | remake | levels | cat | difference / uncertainty | tests |
|---|---|---|---|---|---|---|---|
| B01 | Threat-vs-own budget | FFBC, 44A8CC | AiFaithfulEconomy.Threat/Own | iv (economy report 1,059; 8e2d9053: 1,063/0) | MATCH | Threat term corroborated only indirectly; inputs depend on **X1** | mirror |
| B02 | Mobilise pass (state 24, gate, stop at the deficit) | 4504F4 → 44A4E0 | FaithfulMobilizationGate / ProposeMobilization | iv deployments 1,059/1,059 | MATCH | — | mirror |
| B03 | No mobilisation at a city with a hostile army adjacent | none in the original | ProposeMobilization `IsThreatened` (spot-checked) | i, ii (both sides) | DIFF (authored, under Faithful) | Probably never hit in the 1,059 deployments | none |
| B04 | Receiving army d < 6 (last match); new 1-unit army | 44A4E0 | MobilizationReceivingArmy / ArmyCreation | ii; iv via counts | MATCH | Identity not compared | mirror |
| B05 | Order stopping rule (k < 8, deficit, 40 slots) | 4504F4 loop | PlaceOrders | iv 265/265, 263/263 | MATCH | Rule replayed on each side's own draws | mirror |
| B06 | Deficit floor (≤ 3 orders below it) | 4504F4 | MayPlaceAnother | iv inside B05 | MATCH | — | mirror |
| B07 | Order city chosen once (capital / fort ≥ 75 town) | 4502E0 | ChooseCity | iv (4 → 0 at 8e2d9053) | MATCH | The 15-tile boundary (≤ or <) not isolated | mirror |
| B08 | Order-city tie | 4502E0 (undocumented) | lower city id wins | i | AUTH | The original probably keeps table order | mirror |
| B09 | Order type and troops draws | 4501F4 | RollType/RollTroops, own stream | ii | AMB | Draws not compared | mirror |
| B10 | Order cost and mobilisation increment, debt allowed | 4504F4 | RecruitStandingUnit (allowDebt) | ii | AMB | AI treasury debit not compared | mirror |
| B11 | The AI never orders fortification | absent from FFBC | Propose returns early | i, ii | AMB | Absence read from code only | mirror |
| B12 | Week-11 tax rules | FFBC tail | NextTaxRate | iv 113/113 | MATCH | — | mirror |
| B13 | Auto-tax for computer seats only | — | AiTurn | ii | AMB | Human side at week 11 not established | none |
| B14 | Fleet order gates and score | 450768 (0x450768–0x450855), 4496E0 | OrderFleet, FleetScore, ChoosePort | i (research disassembly, PR #197 `5dc1387`: +1 per own fleet, +3 more under construction; gates count 0x4A0326 < 99, treasury > 3000, cities +0x446 > 50/100); iii (FleetScore read: launched +1, under construction +4) | MATCH | The spec's "at sea +4" was wrong and is corrected; not measured in play | mirror |
| B15 | Unit consolidation | 450858 | ConsolidateUnits | iv (joins 54, disbands 16) | MATCH | The remake keeps an army's last unit (designed, #565) | mirror |
| B16 | AI army merge | 4509F0 | MergeArmies | iv (18 merges) | MATCH | Purse: the remake saturates, the original wraps at 16 bits | mirror |
| B17 | AI fleet merge | 450B30 | MergeFleets | i–iii | AMB | = D27, never exercised | mirror |
| B18 | Own-city free resupply | E41C → F6D8 | AutomaticResupply.ForArmy | iv 1,197/1,200 | MATCH | 3 seats: state or order | mirror |
| B19 | Purse normalisation (> 1000 to treasury; < 500 gets +500) | F6D8 | AutomaticResupply | ii | AMB | Not logged by the remake, so not compared | mirror |
| B20 | Foreign non-war city sale | E41C/F6D8 | FaithfulProviderEligible | iv talents 1,200/1,200 | MATCH | Signed/refund cases staged only | mirror |
| B21 | Embarked army resupplied and hiring at its own coordinates | E41C | AiResupplyPass (#759) | ii–iii | AMB | Not isolated end to end | mirror |
| B22 | Support and hire pass timing | F31C → E41C | prepass (per army only with Tactical human battles and a living human seat, no watch mode) vs per army | ii; iv (Greece t21, pass 1) | DIFF | **X2** | none |
| B23 | Free hire gates | E41C | AiMercenaryHirePass | iv 1,199/1,200 | MATCH | Labels compared as counts | mirror |
| B24 | Hire after a post-battle treaty in the same seat | 450C68 | PeaceTreatySystem.ApplyBeforeAiContinues | iv difference at 8e2d9053; fix in (iii) | DIFF → fixed, not re-measured | — | none |
| B25 | Hire gate on army byte +0x274 | E41C | none | i | UNAUD | Meaning unknown | none |
| B26 | Mercenary-run offer choice; embarked run lands at the offer | E84C | MercenaryRunDestination | iv (28/30 controls; v0.9.3) | AMB | 2 controls unexplained | none |
| B27 | Quarterly mercenary pay and desertion (AI) | 451B40 | MercenaryDesertion | ii | UNAUD | No AI comparison | mirror + one discr |
| B28 | Regular, garrison and ship upkeep (AI) | 451B40 | ArmyUpkeep… | ii | UNAUD | No AI comparison | mirror |
| B29 | AI deposition | 44C8F0 | AiDepositionHandler | ii; rolls seen | MATCH | Stream differs (see A31) | mirror |
| B30 | Trade swap, one forward pass | FB7C | OriginalTradeSwapPass | iv (10 → 0) | MATCH | — | mirror |
| B31 | Loop-1 trade skip for the war leader | FB7C | handled by T274 (see E14) | ii | AMB | Not re-measured | mirror |
| B32 | AI embark over capacity | F8FC via B79C | ArmyTransportTrim (T224) | iii | APPR | Not re-measured | none |
| B33 | Seat replay reruns the economy | FA20 | AiTurn re-entered | ii; iv (x3: pass-1 budgets identical in 15/15 runs, pass 2 reruns the economy) | MATCH (Tactical) | **X3** | none |
| B34 | Fleet support and repair | E5DC/F7E4 | AutomaticResupply.ForFleet | iv synthetic 23/23 | MATCH (synthetic) | No natural-play comparison | mirror |
| B35 | Designed economy (Improved) | none | AiEconomyPhase.Propose | iii | AUTH | — | mirror |

### C. Army phase

| id | behaviour | original | remake | levels | cat | difference / uncertainty | tests |
|---|---|---|---|---|---|---|---|
| C01 | Army loop: table order, count at entry, one army at a time | F31C | OriginalArmyOrder; AiTurn loop | iv (e20a6488: 0/156 out of order) | MATCH | — | mirror |
| C02 | Battle with a human: remaining armies skipped, seat replayed | 0x4A0B7C; FA20 | AiPhaseBattleGate (T256) | i, ii; iii (Tactical); iv remake Tactical (x3-seat-replay-v1: 5/5 seats, 13/15 runs; the 2 misses are battle winners) | MATCH (Tactical) / DIFF (Instant) | **X3, X6** | mirror |
| C03 | Capital-defence threat list (≤ 9, region, radius 19/9) | EFC8, EB18/EB9C | AiCapitalDefence.Threats | iv common cases (05b02936) | MATCH | The 9-cap and ties seen only in emulation | mirror |
| C04 | Responders (order, offence skip, limit, non-war rule) | EFC8 | Run, CommittedToOffence, NearestThreat | iv (decisions report) | MATCH | Dispatch counted without a command: not isolated | mirror |
| C05 | Responder destination and arrival attack | EFC8 → DBA8 → D734 | Destination, ArrivalAttack (T249) | iv (17 → 0) | MATCH | — | mirror |
| C06 | Capital defence while a human battle is pending | EFC8 (no flag test) | continuePending (T277) | i–iii | AMB | **X5** | mirror |
| C07 | Capital defence and support read relations after this turn's declaration | FB7C first | war candidate inside the loop | ii (code) | UNAUD (suspected DIFF) | **X1** | none |
| C08 | Per-army support and hire at each army's entry | E41C at 0x44F366 | up front (Instant, headless, watch mode) | iv for transfers; iv for timing (Greece t21, pass 1) | DIFF | **X2**; Greece t21 attributed | mirror |
| C09 | Enemy-city scorer | ECE4, CAB4, EB9C | ScoreCityTarget; OriginalWordScore | iv (selection187; decisions) | MATCH | Whole-scorer word overflow never played | discr |
| C10 | Enemy-army scorer | EE60 | ScoreArmyTarget | iv (army3 fixed; e20a) | MATCH (+ IMPROVED zero guard) | The original divides by zero | mirror |
| C11 | Resupply/defence city scorer | E670 | ScoreResupplyCity | iv (v0.9.2 tie rows gone) | MATCH | Foreign preference not isolated; the capital test is "any nation's capital" | mirror |
| C12 | F31C decision tree boundaries | F31C 0x44F3B8–0x44F4C7 | DecideFromScores | iv (selection187; decisions) | MATCH | — | discr (boundary controls) |
| C13 | #925 reachable tiers | none | Improved only | owner decision | APPR | Off under Faithful | mirror |
| C14 | Mercenary-run offer choice | E84C | MercenaryRunDestination | iv common cases | MATCH | Offer with no city: the original has no guard | mirror |
| C15 | Second walk in the same army turn (army > 70, city > 85) | F31C 0x44F4A3/0x44F4C7 | RetainMercenaryContinuation (T249/T254) | iv | MATCH | — | mirror |
| C16 | Ferry rendezvous written at 0 army moves | DBA8 → DB38 → D9A8 | ZeroMoveRendezvous | i–iii | AMB | Not re-measured after e20a6488 | mirror |
| C17 | Army aboard drives its fleet; embarked run to the offer | DBA8 aboard branch | OriginalArmyTransport.Carried (T276) | iv (v0.9.3) | MATCH | — | mirror |
| C18 | Cross-class transport search | DB38 → D9A8 → CD08/B79C | OriginalArmyTransport.Ferry | iv for case (a) only | AMB | Case (b) and distant-route outcomes not measured | mirror |
| C19 | DBA8 walk (CB40, D174, CEC8, recursion) | DBA8 | MoveArmyCommandHandler; ClassicalArmyNavigation | iv (3,303 + 44,734 emulator cases; in-play rows) | MATCH | D174 unbounded recursion: the remake drops the march | mirror |
| C20 | Stale DBA8 word suppression | DB38 0x44DB47 | inheritFailedIntermediate (T276/T277) | iv (v0.9.4 recheck) | MATCH (measured scope) | Greece (112,70), Numidia t24–25 not hook-confirmed | mirror |
| C21 | D734 end check at the measured callers | D734 0x44D895–98C | OriginalArmyWalkContact; EndCheck | iv (v0.9.1: 17 → 0) | MATCH | — | mirror |
| C22 | D734 contact at unmeasured callers (E84C walk, F4A3, F47C) | D734 | EndCheck None there | i, ii partly | AMB | The original would besiege or attack | mirror |
| C23 | D734 "not at war" city tail: F6D8 resupply at the walk's end | D734 → F6D8 | none (Ruleset.cs acknowledges it) | i, ii | MISSING | Mid-seat supply transfer absent | none |
| C24 | D734 land tail (one more step if cost < moves) | D734 tail | MovementWalker | i, ii | UNAUD | — | none |
| C25 | Garrison fallback destination | EBE8 | GarrisonFallback | iv (gap A 410 → 0) | MATCH | Capital −1 edge (C26) | mirror |
| C26 | EBE8 with no capital | EBE8 (no guard) | returns null | i | DIFF (code) | Capital-less nation only | mirror |
| C27 | AAB4 gate after a command | 0x44F4CC | MovesForActionCheck (#1723) | iv | MATCH | — | mirror |
| C28 | AAB4 gate with no command (#1739) | F31C → AAB4 | ProposeArmyTree gate | iv (v0.9.2) | MATCH | — | mirror |
| C29 | Siege or attack when already adjacent; repeated sieges | F31C → D734 | Besiege/AttackArmy candidates | iv (gap B, v0.9.1) | MATCH | — | mirror |
| C30 | Siege-gate tally | none | AiSiegeGateTally | iii | AUTH | Diagnostics only | mirror |
| C31 | Capture and holding after a won siege | B27C | capture | — | UNAUD | Siege-resolution audit pending | — |
| C32 | Joining (merge, consolidation) | 4509F0, 450858 | AiFaithfulEconomy | iv | MATCH | = B15/B16 | mirror |
| C33 | Splitting by the AI | none found | none | i | UNAUD | Absence not proven | none |
| C34 | Scored-candidate driver: cap 24, random ties, no-op stop | none | AiTurn.Select | iii | AUTH | **X4** | mirror |

### D. Fleets

| id | behaviour | original | remake | levels | cat | difference / uncertainty | tests |
|---|---|---|---|---|---|---|---|
| D01 | Fleet-order gates and score | 450768 | OrderFleet, FleetScore | i (disassembly, research PR #197); iii; partial iv | MATCH | = B14 (weights settled: one under construction blocks further builds) | mirror |
| D02 | Ship count min(100, cities + 50) | 450768 | OrderFleet | ii (derived); iii | AMB | Order size never compared | mirror |
| D03 | Build city nearest the capital, eastern zone excluded | 4496E0, 4496BC | ChoosePort; OriginalFleetPort.IsPort | iv (v0.9.3: Media rows gone) | MATCH | — | mirror |
| D04 | Build-city tie: first record | 4496E0 | ChoosePort | ii; iii | MATCH (code) | Not seen in play | mirror |
| D05 | Busy build city | 4496E0 (own fleet only) | any nation's fleet (spot-checked, line 647) | ii, iii | DIFF | Captured coastal city with a foreign fleet under construction | mirror (asserts the divergent rule) |
| D06 | Port predicate for the build city | 4492C0 (body not read) | IsPort (E920 3×3) | i | AMB | Substituted routine | mirror |
| D07 | Launch tile: 939C mode 0 on the live map | 44939C via 44A050 | CoastalCity.LaunchTile | iv (v0.9.3) | MATCH | — | discr |
| D08 | Launch after the build city changes hands | 44A050 | FleetTickSystem | ii; iii | AMB | Not compared | none |
| D09 | Launch-turn moves in a reused, compacted index | 44A050, 44ADB0 | moves 0 | ii | DIFF | The original's fleet can hunt or reach port on its launch turn | none |
| D10 | Fleet phase branch order | F608 | OriginalFleetPhase.Run | iv (124/150; 26 rows attributed) | MATCH | — | discr (emulation) |
| D11 | Supply, purse and repair prepass | E5DC, F7E4 | AiResupplyPass(onlyFleetId) | ii; iii | AMB | Staged Wine only | mirror |
| D12 | Port pick | E9A8, E920 | OriginalFleetPort.Pick | iv (gap C a seed artefact; port rows) | MATCH | — | mirror |
| D13 | Hunt | F4F8, 4494E4, 44AA54 | OriginalFleetHunt | iv (storm30/30b consistent at 168dbc04) | MATCH | — | discr |
| D14 | Hunt skips a target of strength ≤ 0 | no guard | guard | ii | AUTH | The original would fault | none |
| D15 | Ferry search | D9A8, CD08 | OriginalArmyTransport.Ferry | iv for case (a) | MATCH | Case (b) not measured | mirror |
| D16 | Failed-search −1 word | D9A8 (a)/(b) | IntermediateSearchFailed (T277) | iv | MATCH | = C20 | mirror |
| D17 | Ferry route at 0 army moves | DBA8 → D9A8 | ZeroMoveRendezvous | ii, iii | AMB | = C16 | mirror |
| D18 | Carried army drives its fleet | DBA8 → CD08 | Carried | iv | MATCH | = C17 | mirror |
| D19 | Stored-route lifetime | route_x +4 | OriginalFleetRoutes (per call) | ii, iii | AMB | **X3** | mirror |
| D20 | E1FC move contract | E1FC, D174, CEC8, 939C | OriginalFleetMove | iv partial (24/26) | MATCH | — | discr (emulation) |
| D21 | 939C returns the fleet's own tile (Thracia fleet 6) | 939C | ReplaceLandTarget | i | AMB | Unexplained; no position difference | none |
| D22 | D174 unbounded recursion | D174 | FleetIntermediate | i | UNAUD | — | none |
| D23 | Coincident target is a no-op | CB40 uninitialised | `origin == target` | ii | AUTH | The original made a 24-move round trip once | mirror |
| D24 | AI disembark (B840 mode 1) | B840 | LandingTarget | iv 3/3 | MATCH | — | mirror |
| D25 | Port arrival resupply | E1FC → F7E4 | OriginalFleetMove port arrival | ii | MATCH (code) | Not isolated | mirror |
| D26 | Naval contact on arrival | E1FC → B5D0 | AttackFleet → ResolveNaval | iv (naval30, storm30) | MATCH | — | discr |
| D27 | AI fleet merge | 450B30 | MergeFleets | ii, iii | AMB | Never exercised; 16-bit wrap vs saturation | mirror |
| D28 | Embark overflow | F8FC | PartitionWholeUnits | ii + controls | MATCH (branch) | Other branches unproved | none |
| D29 | Reachability: any fleet makes every target reachable | CAB4 | ClassicalArmyNavigation | ii, iii | MATCH (code) | No iv | none |
| D30 | Fleet phase still runs in an interrupted seat | FA20 0x44FA56 | ArmyPhaseInterrupted → OriginalFleetPhase | ii, iii; iv (x3: pass 1 runs the fleet phase; S08 fleet 0 to port then stored route, as the original) | MATCH (Tactical) | **X3** | none |
| D31 | Weather ignored by AI choices; rough sea counts as sea | storm pass; MapCode | IsRoughSea → 1 | iv for storm damage | MATCH | Ignorance inferred | discr |
| D32 | Elimination removes fleets and carried armies | R/2026-10-09 elimination | conquest cascade | ii; iii | AMB | Not compared | mirror |
| D33 | The AI never scuttles, splits, transfers or joins fleets with a human | none documented | none found | i | UNAUD | Absence not stated by research | none |

### E. Diplomacy

| id | behaviour | original | remake | levels | cat | difference / uncertainty | tests |
|---|---|---|---|---|---|---|---|
| E01 | Relation setter, two-way; peace becomes a cooldown | 449B40 | RelationTransitions | iv for the trade case (v0.5.0) | MATCH | −24 measured in the original only | mirror |
| E02 | War cascade, one step | 449B40 → 449A44 | DeclareWar | iv (rel-war-* at v0.9.3) | MATCH | Beyond one step: code only | discr (difftest) |
| E03 | Dialog war leaves a higher-index ally at −18 | TPolitics_OK | DeclareWarCommand | iv | APPR (#1586) | Changes later AI war candidates | discr |
| E04 | Alliance puts the new ally at war with the partner's enemies | setter(…, 2) | FormAlliance | iv (diplomacy-longrun §3) | MATCH | — | mirror |
| E05 | Busy gate | FB7C; FAA0 | IsBusy | iv 833/833 | MATCH | Read after the economy (**X1**) | mirror |
| E06 | Busy flag uninitialised when nothing passes | 0x44FC55 | always computed | i, ii | AMB | Never observed | none |
| E07 | Power | FB7C | Power | iv | MATCH | — | mirror |
| E08 | War target | FB7C loop 1 | BestWarTarget | iv 833/833 | MATCH | The remake counts cities live; the original reads the stored +0x446 | mirror |
| E09 | War roll and one declaration per turn | FB7C | ProposeOwnWarDeclaration | iv for the rate | MATCH | Draws differ; TurnIndex-0 imports reuse a draw | mirror |
| E10 | AI declares war on a human (news only) | FB7C | DeclareWarCommand | iv original; iii remake | AMB | Not compared end to end | none |
| E11 | Protected test | FAA0 | IsProtected | iv | MATCH | unity > 0 with 0 cities open | mirror |
| E12 | Alliance roll and partner | FB7C | ProposeOwnAlliance | iv for the rate | MATCH | The remake rolls after the search, the original before | mirror |
| E13 | Treaties only with AI partners | FB7C | handlers | iii | MATCH | — | mirror |
| E14 | Fresh trades: loop-1 skip of the war leader (D3) | FB7C | OriginalTradePartners (T274) | i–iii | AMB | Fix not re-measured | mirror |
| E15 | Trade swap single forward pass | FB7C | OriginalTradeSwapPass | iv | MATCH | — | mirror |
| E16 | Swap drops a human partner to −8 | FB7C | MaySwapTradePartner | i–iii | AMB | Not observed in either game | none |
| E17 | Phase order inside a seat | FA20 | AiTurn.Run | ii | AMB | **X1** | none |
| E18 | Seat replay: FB7C runs again with fresh rolls | FA20 0x44FA56 | streams keyed by (nation, turn) | iv original | DIFF | **X3**; x3: no roll fired in 30 runs, the remake side unmeasured | none |
| E19 | The AI never offers or writes peace over a war | FB7C | no peace branch | iv | MATCH | — | mirror |
| E20 | Offer roll at a human turn start | 452034 | PendingOfferSystem | iii; iv for the rate (v0.5.0) | MATCH | Rate checked at v0.5.0 only | mirror |
| E21 | Offer shown as an OK-only box | StartTurn 0x45AC5C | event | iv at v0.5.0 (no box) | AMB | Display not rechecked | none |
| E22 | Accepting an offer (one-click) | TPolitics_MakeTrade | AcceptPendingOfferCommand | iii | AUTH | The original has no Accept button | mirror |
| E23 | Loading re-announces a stored offer | StartTurn on load | none found | i | MISSING | — | none |
| E24 | Empty offer type survives export | save trailer | exporter writes 0 | iv | DIFF (cosmetic) | = A24 | none |
| E25 | Human trade proposal rules | TPolitics_MakeTrade | ProposeTradeCommand | iv (rel-trade-*) | MATCH | — | discr |
| E26 | Human alliance proposal to an AI | TPolitics_MakeAlliance | ProposeAllianceCommand | iv original; iii | AMB | Not exercised in the remake | mirror |
| E27 | Human peace proposal | TPolitics_MakePeace | MakePeaceCommand | iv (rel-peace-gaul) | MATCH | — | discr |
| E28 | Post-battle peace-offer gate | TBattleOver_OK → TBattlePols | InstantBattleResolver; TacticalBattleSession | iv original; iii | AMB | `!Battle.Capped` and ArmyPower not cited | mirror |
| E29 | TBattlePols Yes | 450C68 | PeaceTreatySystem | iv original; iii | AMB | Not run end to end | mirror |
| E30 | AI–AI treaty trigger | 0x44B1C4 | peaceRoll | iv | MATCH | — | mirror |
| E31 | Honourable vs sues branch | 450C68 | HonourablePeaceGate | iv | MATCH | Strength measure caveat (E28) | mirror |
| E32 | Reparations; the treaty reseeds RandSeed | 450C68 | ReparationsFormula | i–iii | DIFF (code) | No reseed in the remake | mirror |
| E33 | Treaty ally loop | 450C68 | ApplyAllyPeaceCascade | iv | MATCH | — | mirror |
| E34 | Elimination resets relations | 44BED8/44C528 | ResetAllOnElimination | i–iii | AMB | Trade/alliance mapping not cited | mirror |
| E35 | Conquest merges the neighbour mask | 44C528 | ConquestCascade.MergeNeighbours | i–iii | AMB | Never observed | unknown |
| E36 | Quarterly thaw (columns 0–7 bug) | 451B40 | QuarterlyThawSystem | iv | MATCH | — | mirror |
| E37 | AI deposition and cooldown reset | 44C8F0 | AiDepositionHandler | iv | MATCH | — | mirror |
| E38 | Rebirth relations | 44C360 | rebirth path | ii–iii | AMB | Wine candidate only | mirror |
| E39 | Diplomacy news lines | 449A44 | NewsLogWriter | iii | AMB | Not compared at this pin | mirror |
| E40 | Hotseat battle writes no relation | THVHBatPols_OK | not located | i | UNAUD | — | none |
| E41 | The AI attacks only nations it is at war with | rel == 3 gate | military phase | i | UNAUD | Army area | — |

### F. Tactical AI and battle transitions

The 318 recorded tactical series matched state and ordered draws at `b593c6e2`
(F/2026-10-25-current-main-battle-replay157.md, F/2026-10-30-tactical-residuals-attributed25.md). `168dbc04` contains that
commit, and no later commit touches `Battle/Tactical/General/*`. In this table, iv means a recorded-corpus replay in Wine.

| id | behaviour | original | remake | levels | cat | difference / uncertainty | tests |
|---|---|---|---|---|---|---|---|
| F01 | A battle involving a human opens the board; AI vs AI goes to the instant resolver | 44AEE4 → 437DE4/439968 | TryOpenTacticalBattle; AiPhaseBattleGate | i–iii (Tactical only) | MATCH | Holds under Tactical mode only | mirror |
| F02 | Human battles resolved instantly (CLI default) | none | HumanBattleMode.Instant | i | AUTH | **X6** | mirror |
| F03 | No tactical siege or naval battle | 44B27C, 44B5D0 | ResolveSiege/ResolveNaval | iv distributional (siege10, naval30) | MATCH | — | discr |
| F04 | Instant field resolver | 44AEE4, 44AE20 | ResolveField | i–iii | MATCH (code) | Not end to end (comparisons exclude battle draws) | mirror |
| F05 | Copy-in for an AI nation | 437DE4, 437D10 | TacticalCopyIn | i–iv | MATCH | — | discr (GM) |
| F06 | AI side adopts the opponent's delay settings | 437DE4 | not written | i, ii | DIFF | Save bytes only | none |
| F07 | Initial morale and Random(0) draw | 0x43801A | TacticalCopyIn | i–iv | MATCH | — | discr |
| F08 | Control predicate | 438378 | IsComputerDriven | i–iv | MATCH | — | discr |
| F09 | AI placement | 4381A4 | GeneralPlacement | i–iv | MATCH | — | discr |
| F10 | Half-round setup and slow advance | 439968 | ApplySetup | i–iv | MATCH | — | discr |
| F11 | Sequencing of placement and moves | 439C84, 439C20 | TacticalDriver | i–iv | MATCH | — | discr |
| F12 | Pass 1 type order | 43A31C | GeneralOrders.InOrder | i–iv | MATCH | — | mirror |
| F13 | Target choice | 439E08 | GeneralTargeting | i–iv | MATCH | — | discr |
| F14 | Engage | 43A160 | GeneralEngage; GeneralLine | i–iv | MATCH | Crafted-grid Wine boundaries | discr |
| F15 | Pass 2 | 43A544, 439D0C | GeneralPassTwo | i–iv | MATCH | — | discr |
| F16 | Later passes in slot order | 43A544/43ABB4 | InSlotOrder | i–iv | MATCH | — | regression |
| F17 | Threat move | 43ABB4, 43A718 | GeneralPassThree | i–iv | MATCH | — | mirror |
| F18 | Flank | 43ABB4 | FlankUnit | iv at draw level | MATCH | Complete causal paths open | mirror |
| F19 | Computer-unit movement | 438D24, 438A6C | TacticalMovement | i–iv | MATCH | — | mirror |
| F20 | Shooting exchange | 43910C | TacticalShooting | i–iv | MATCH | — | discr |
| F21 | Melee | 4393EC | TacticalMelee | i–iv | MATCH | — | discr |
| F22 | Rout and cascade | 438FB0 | TacticalRout | i–iv | MATCH | Cascade not observed directly | mirror |
| F23 | Termination | TBattleMap end | Winner; HalfRoundCap 0 | i–iii | MATCH | Both sides emptied: unexercised | mirror |
| F24 | Improved preset (cap, retreat losses…) | none | ruleset options | iii | APPR | Off under Faithful | mirror |
| F25 | Human presses Computer general | 0x437AB8 | ComputerGeneralOn | i–iv | MATCH | — | discr |
| F26 | Information-window click interrupts the general mid-pass | 43A31C/43ABB4 polls | GeneralOff between commands only | i, ii | AMB | Takeover looks unreachable (code) | none |
| F27 | Reload of a mid-battle save | StartBattle → 439968 | Reopen; Resume | i–iv | MATCH | — | discr |
| F28 | General flags across a reload | StartBattle | SavedTacticalBattle keeps the flags | i, ii | AMB | The remake keeps them; the original clears them (code) | mirror |
| F29 | Surrender | toolbar | TacticalSurrender | i–iii | MATCH | — | mirror |
| F30 | Draw order of the 14 Random sites | module sites + 0x4592BD, 0x45951C | RngBattleDraws | i–iv | MATCH | — | discr |
| F31 | Random source | global | SplitMix streams | i | AUTH (designed) | = A19 | none |
| F32 | Write-back | TBattleOver_OK | TacticalWriteBack | i–iv | MATCH | — | discr |
| F33 | Post-battle peace gate on the board | TBattleOver_OK → TBattlePols | Conclude | i–iv (hook 77/77) | MATCH | Barbarian exclusion authored; compare E28 for the instant path | discr |
| F34 | AI attack on a human army interrupts the seat | FA20, 451FDC, F31C, 0x4A0B7C | PlaySeatTurn/ResumeAiLap | i, ii; iii; iv remake Tactical (x3-seat-replay-v1: 5/5 seats, 13/15 runs; the 2 misses are battle winners) | MATCH (Tactical) / DIFF (Instant) | **X3** | mirror |
| F35 | Capital defence while a battle is pending | EFC8 | AiPhaseBattleGate | i–iii | AMB | **X5** | mirror |
| F36 | Human attack in their own turn declares war implicitly | 44AEE4 | TryOpenTacticalBattle | i–iii | MATCH | — | mirror |
| F37 | "Board cannot host" fallback | none | CanBeFought | iii | AUTH | Unreachable under the 20-unit cap | none |
| F38 | Save during a battle | Save As | refused | i | AUTH (restriction) | — | mirror |
| F39 | Per-exchange delay | 0x448FFC | none | i | AUTH (omitted) | Presentation | none |
| F40 | Tactical Undo | none | TacticalUndo (T267) | iii | AUTH | — | mirror |
| F41 | AI siege and attack at a walk's end | D734 → B27C/AEE4 | walk end contact (1724/1729) | i–iv | MATCH | = C21 | discr (anchored) |
| F42 | Natural owner-entry battle; installed or native build | none | whole stack | iv on recorded inputs | UNAUD | #1355 acceptance open (T206) | none |
| F43 | Stronger Improved computer general | none | absent (planned for v0.10) | — | AUTH | — | none |

## Subsystems added to the #195 checklist by this inventory

- **Ordering and timing:**
  - dead-record compaction timing (A04);
  - the phase-mode flag `DAT_004a0340` (A11);
  - the RNG behaviour of a replayed seat (A13);
  - the pending-offer roll's timing against the human's orders (A24);
  - the unity ≤ 0 guard against `Eliminated` (A06).
- **Remake driver mechanics that bind under Faithful:** the action cap, the no-op stop and random tie-breaks (**X4**).
- **Support and hire:** the timing of the support and hire pass (**X2**); the `D734` end-check tails (C22–C24); the hire
  byte `+0x274` (B25).
- **Fleets:**
  - the economy-tail fleet merge and its 16-bit purse arithmetic (B16/D27);
  - fleet-table compaction and leftover launch moves (D09);
  - CAB4 reachability through any fleet (D29);
  - the `F8FC` embark overflow (B32/D28).
- **Battles and diplomacy:** the post-battle treaty's reseed (E32); the hotseat battle relation path (E40); mid-battle save
  and reload, and the general flags (F27/F28/F38).
- **Remake-only automation, kept apart from Faithful:** barbarians, personality profiles, human auto-support, watch mode and
  Tactical Undo (A39–A43, F40).

## Pass 1 plan, ordered by likely outcome impact

Each item becomes its own finding: a minimal trigger, expected against actual, the player-visible consequence, addresses
and symbols, and a discriminating experiment.

1. **X2, support and hire timing.** Replay the Greece t21 seat with the remake's per-army path (the Tactical retained pass),
   or stage two armies at one own city, and hook `E41C` in the original. The question is whether the flip goes away when
   support is per army.
2. **X1, phase order.** Find seats in the stored games where the war roll fired (both games), and compare that seat's
   budget, capital-defence threats and hire against a replay with the declaration applied first. Then design a staged
   control.
3. **The 10 own-capital stays.** Attribute each one, with the `EFC8`/`E41C`/`D734` hooks on the original start saves,
   against the X1, X2 and C23 candidates.
4. **X4, the action cap.** Count the seats in the three 264 BC games where the remake hit `HitActionCap` or the no-op stop
   (the remake logs it), and check whether the last table armies went unplayed.
5. **X3, seat replay.** The adapter supports `tactical`. Replay the five seats the original replayed (R/2026-10-31) under
   the remake's Tactical retained pass, and compare the second pass's draws, routes and economy.
6. **C23, the missing F6D8 walk tail;** **C22, unmeasured D734 callers;** **D09, launch moves;** **D05, busy city;**
   **B03, mobilisation restraint.** Each gets a code read first, then a staged Wine control.
7. **The late-year AI-phase differences (266–264 BC):** classify them by class with
   `runs/experiments/longrun-v090/classify.py`, then place each class in this matrix.

## Pass 1 results so far

- **X4, the action cap (measured 2026-11-04, `runs/experiments/data/run-exp-audit195/x4-orders-per-seat-168dbc04-v1.txt`,
  script `runs/experiments/audit195/orders_per_seat.py`).**
  - **Measurement:** the remake's End-turn report lines across all 19 anchored replays on `168dbc04` (12,991 AI seats, years
    270–264 BC). No seat issued more than 20 orders. One seat issued 20 (Seleucid, Galatia game, t14), 3 issued 19, and 98 %
    issued 10 or fewer.
  - **Conclusion:** the cap of 24 counts loop iterations, not orders, so it is unlikely to have bound in any stored game.
    The Seleucid t14 seat (at most 4 non-order iterations) is not excluded.
  - **Open:** the no-op stop (A37) and random tie-breaks (A38) cannot be seen in these lines.
  - **Rows:** A36/C34 stay AUTH, now with "not binding in the stored games (≤ 20 orders per seat)".
  - **Research caveat (intake PR #198):** `classical-faithful.json:1367` says the cap "binds occasionally" in the remake's
    own 16-nation free play (1–2 times per 480-turn run, seeds 1–10). "Not binding" therefore holds for these 19 anchored
    replays only.
- **X2, support and hire timing (measured 2026-11-04, remake only; `run-exp-audit195/x2-greece-t21-v1`,
  `x2-stays-v1`; scripts `runs/experiments/audit195/x2_mode_probe.py`, `x2_stays_batch.sh`).**
  - **Method:** each turn is replayed on `168dbc04` from the original's own start, in Instant mode and in Tactical mode,
    with seeds 12345 + k, 12345 and 99. Tactical mode uses the remake's per-army support pass (AiTurn PrepareArmy, the
    retained pass); Instant runs the whole-army prepass up front. The owner's armies and launched fleets are compared with
    the original's end state.
  - **Greece t21 (Seleucid): X2 is the cause.**
    - In Instant mode, on all 3 seeds, the 27,113-man army leaves Antioch (221,60) for (221,64) and pushes the 20,400-man
      army to (222,64).
    - In Tactical mode, on all 3 seeds, both armies match the original.
    - So the up-front support pass alone flips the resupply choice. Per-army timing (the original's `E41C` inside `F31C`)
      reproduces the original.
  - **The other 11 rows** (Rome t10, Carthage t21/t33/t35, Gaul t29/t40, Ptolemaic t9, Numidia t6/t11 ×2, Greece t6) have
    two properties:
    - Tactical and Instant give the same result on every seed;
    - each row disappears under at least one other seed.

    These rows are therefore **sensitive to the remake's draws and not X2. They stay unattributed, not MATCH.** Research's
    narrowing at intake (PR #203): a row disappearing under other remake seeds shows only that the remake's outcome depends
    on its draws. The original was not re-sampled under those seeds, so its rule is not shown to match.
    - Numidia t6/t11 were already attributed to war rolls.
    - The 10 own-capital stays included in these rows stay open; a hook on the original start would settle each one.
  - **Is the mode switch a one-change probe? (research intake, PR #203)** For this turn, yes, from the code:
    - At `168dbc04` the Tactical/Instant switch reaches the AI turn through one flag,
      `IAiBattleInterruption.RetainPartialAiPass`.
    - In `AiTurn.cs` the flag only moves the support and hire pass: the up-front pass at line 186 against `PrepareArmy` per
      army at line 251, plus the logging at lines 215 and 388.
    - Its one other reader is `AiCapitalDefence.cs:82`, `continuePending`, which acts only while a human battle is pending.
    - The Greece t21 replays opened no battle in either mode (no battle line in the receipts), and the human's only order
      was a recruit.

    So in this turn the switch changes the support pass's placement and nothing else. No remake patch was needed.
  - **Consequence:** X2 is a real Faithful gap in Instant and headless play, which is the CLI default and every anchored
    replay. It changes which city an army resupplies at, so it changes the army's position. The remake's Tactical path
    already has the right timing. A candidate remake fix is to run the support pass per army in every Faithful mode.
  - **Rows:** A09/B22/C08 become **DIFF (iv on Greece t21, 3 seeds)**.

## Evidence

- **This pass reads documents only:** research `docs/rules-specification.md`, `docs/reports/` and `docs/findings-intake.md`;
  this repo's `findings/` and `difftest/REGISTRY.md`; the remake at `168dbc04` (`src/IC2.Engine/Ai`, `Battle`, `Diplomacy`,
  `Economy`, `Naval`, `Movement`, `Presentation`, `data/rulesets/classical-faithful.json`, `docs/tasks`, and the test names).
- **No saves are cited.** Every level-iv row names the report that holds its saves.
