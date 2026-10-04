# Plan: battles (the tactical screen half-round by half-round, sieges and the instant resolver, the post-battle peace)

**Status:** plan for review (2026-10-04, revised the same day for the research request). Nothing here has been run.
Author: Claude Opus 5.5 (planner). Implementation: Sonnet; review: DeepSeek V4.1 Flash, then GPT-6 Sol once per PR at low effort.
These are **experiments, not runs**: no issue approval is needed (rule 4 concerns real runs). Battles come before the chatbot work.
The form follows `docs/proposals/fleet-battles-and-storms.md`: tasks with cells and seeds, acceptance criteria, natural and synthetic
evidence, and each experiment ends with a `findings/` draft and a release `run-exp-<name>`.

## 0. Decisions recorded, and what is still open

**Decided by the player (2026-10-04):**

1. **Scope: all four areas.** (A) field battles under *Computer general*; (B) playing the tactical screen ourselves;
   (C) city sieges and the instant resolver; (D) the post-battle peace dialog `TBattlePols`.
2. **Process:** Opus plans, Sonnet implements, DeepSeek V4.1 Flash and then GPT-6 Sol (low, once per PR) review.
3. **Order:** battles first, then the chatbot. **No issue approval for experiments.**
4. **The research request** (relayed 2026-10-04 from the `imperial_conquest_2` research session; quoted in §0.2) is **the real scope
   and the deliverable shape of A and B**. It feeds the clone's v0.5.0 "Battles", research issue `imperial_conquest_2#496` and the
   research roadmap §3 item "Battle minigame: exchange log and sweeps". **Nothing is written to that repository or to the research
   repository**: the bot tells the user the draft's file name and branch for the research repo's findings intake.
5. Carried over from the fleet plan: synthetic states are acceptable when labelled; 30 seeds at parity cells where a **win rate**
   is the measure. The research sweep asks for 2–3 seeds per cell, because the measure there is the **exchange log** and not a rate (§4).

**Open after §9's answers:** the rout wording ("half the battalion" v `standardSize/25`), the exchange hook's addresses (the research decompile is under way; the player relays them), and the player's go for each stage. The start save, the reading of "three standard battalions", the staging of the budget and the rule that no save is committed are answered in §9.

### 0.1 Changes after the research request

- **A and B are rebuilt around a half-round dataset.** The old B1–B4 (win-rate grids under Computer general, from edited strategic
  armies) become: one sweep of **25 ordered type pairings × 3 sizes × 3 seeds**, every half-round logged from the battle block, both
  sides on Computer general (B4–B5). The win-rate cells that are still useful to the chatbot (the natural Rome v Gaul battle,
  repeatability, HI v LI, the morale clamp) become one smaller task, B10.
- **The battle-lab build is now the main instrument, not an optional probe.** It reseeds at battle start and saves every half-round
  (`patches/battle_lab.py`). It was question 2 of the first version; now it is the design, labelled `lab` in every table.
- **New tasks:** the battle-block decoder and a round-trip check (B2); **crafted mid-battle saves** (B3); the survey of every button
  and the human order set (B7, which absorbs the old B5–B6); screenshots of every unit type at every icon size, plus the full layout
  (B8); terrain (B9); an **exchange hook** if the research side supplies the addresses (B11).
- **Kept as they were:** the sieges (now B13–B14), the instant resolver (B15), `TBattlePols` (B16), the dialog capture before any
  battle is run (§3.5), the scripted plans against Computer general (B12, lower priority).
- **Budget:** the first version guessed 3 minutes a trial and 25–30 h. With the lab build (a battle computes in 1.3–1.9 s, [R]) a sweep
  trial is about 1 minute, so the sweep's 225 battles (315 with the size matrix, B5) take **about 5–6 h**. That figure is still unmeasured: B0 measures it (§5).

### 0.2 The research request, in short

**Question:** how does `TBattleMap` play out, half-round by half-round, for each pairing of LI, HI, archers, LC and HC at three sizes?
It covers movement and initiative, the AI general's placement and target choice, shooting against melee, rout, surrender, the capture
of money and supplies, promotion, terrain and end conditions, and whether the bot can drive or auto-play the screen in each case.
**Design:** a start save with a provoked battle, then crafted mid-battle saves; the seed fixed at battle start; both sides on Computer
general; separately, a human side issuing its own orders; try every button. **Measure every half-round:** each slot's position,
troops, quality and morale; who acted, the action and the target; losses, routs, surrenders, captures, promotions. **At the end:** the
result dialog, the strategic armies before and after, the news. Add an exchange-level hook if feasible.
**Deliver:** the saves in a release; a findings draft (Method, Observations, Inferences, a sweep table, "What this does not
establish", Wine-only); screenshots of every type at every size the screen distinguishes, and of the whole layout.

## 1. What is known, what is only claimed, what was measured live

Tags as in `docs/rules-digest.md`: **[C]** decompiled code, **[D]** derived, **[O]** observed only, **[P]** parsed. New tag **[R]**:
stated by the research request from research reports this repo cannot see (mainly `2026-09-28-battle-minigame-headless-feasibility.md`).
An [R] item is to be checked, not assumed.

### A–B. The tactical battle

- Any army-v-army battle with a human side goes to `TBattleMap`; two AI nations use the instant resolver [C] (§6). Code map [R]:
  `FUN_0044aee4` → `TBattleMap.StartBattle` (`0x436FB4`); a fresh start through `FUN_00437de4`, a resume through `FUN_00439968`;
  the Computer general loop `FUN_00439c84`/`FUN_00439ce8`; the half-round end `FUN_00439c20`; 12 random-draw sites; RandSeed `0x45E030`.
- **Repeatability [R]:** with RandSeed fixed at battle start, a battle replays byte-identically. **A save written inside the battle**
  holds the battle block for every half-round (each slot's position, type, troops, quality and battle-local morale, plus the grid).
  **Loading it resumes the battle deterministically, and an edited one plays out from the edited state.** A fast-build battle
  computes in 1.3–1.9 s over 13–20 half-rounds.
- Battle block in a save (block 12): `2+2+2+1+2+1760+336` bytes, present only with the battle flag set (`docs/sav-layout-notes.md`).
  The field layout is not in this repo. A guess from the sizes, unverified: 1760 = 40 slots × 44 bytes, 336 = 14 × 12 × 2.
  There is an unknown slot word at `+2` (`DAT_004a0348`) [R].
- **Confirmed [R/C]:** melee loss cap `min(raw, floor(0.4 × troops)) + 1`; initial morale `clamp(Random(q×4) + army.morale, 60, 90)`,
  +3 for a computer side. Rout: the request says "half the standard battalion (600, 240, 140, 280, 100)", but those numbers are
  **`standardSize/25`** (LI 15,000, HI 6,000, Ar 3,500, LC 7,000, HC 2,500; `rules-digest.md` §4 table, §6 Rout). That wording is to be
  settled with the research session: it is **still open** (§9 item 2 answers only the 'three standard battalions' half; the research decompile may settle the rout wording).
- **Only structurally checked [R]:** the type matrix `M`, the power term `M × troops × (q×10 + morale)/2000 + 12`, the focus and defence
  factors, the shooting formula, the morale deltas (§6 gives them as [C]). Tactical moves: LI 4, HI 2, Ar 4, LC 6, HC 5 (§4 table).
- **Open (the request's gaps):** movement and initiative; placement and target choice (the AI general is not decompiled, §12 gap 6);
  surrender, capture of money and supplies, promotion (`max(q,6)` then 1-in-4 +1 is only [D, empirical]); terrain; the slot word `+2`;
  how the screen draws each type at each size.
- Digest claims to recheck: "36.6 % then 24.4 % from the same save" (clock-seeded: a spread across seeds, not a repeatability
  failure, `findings/2026-09-29-loading-a-save-does-not-reseed.md`); HI v LI (matrix 1 both ways, §12 gap 10).

**Measured live:** `runs/experiments/gallic-army/`. Rome's joined army (45,700) beat Gaul's (about 43,150) in 4 of 4 seeds and lost
20.6–30.2 %; the battle turn is byte-repeatable on the normal seed build. The driver knows the battle toolbar (y = 112: End turn
about 114, Computer general about 165, by tooltip), the phase text in the title ("Rome  v  Gaul          Rome to place units."),
the battle flag `0x4A0B7C`, and that Computer general must be on during placement. The auto-play is flaky: the window can end up
below others (`coverage.md` §1 🟡). **Defects found by reading:** `gallic-army.py` keeps only the last unit of each type in
Gaul's composition; `play_battle` discards the texts of the boxes it closes, and `dismiss_popups` answers any Confirm **Yes**, so
whether a post-battle dialog appeared in those battles is unknown.

### C. Sieges and the instant resolver (unchanged)

- Siege `FUN_0044b27c` [C] (§5 Siege): `atk = (Σ troops, archers ×3) div 80 × morale`; `def = loyalty×150 + fort×250 + pop×200`,
  then ×5/3 (a capital with loyalty > 59), ×4/5 (owner ≠ allegiance), + slot troops/2, and ×9/10 (the attacker is the allegiance
  nation). **`atk > def` wins, ties go to the defender, and the outcome has no random term.** Erosion happens win or lose. Casualties
  are `troops/(Random(15)+105) × r` with `r = max(1, min(15, def×6 div atk))`. Capture, cascade and conquest rules: §5 [C].
- The **2.5–2.85 % uniform loss** claim [O] is exactly `r = 3` (3/119 to 3/105) [D, this plan].
- Instant resolver [C] (§6): higher field strength wins; the winner's casualties are at ratio `loserPower × 40 / winnerPower`; with
  a 2-in-5 chance, peace with reparations follows when the loser's unity is above 500 and it has more than 7 cities (`docs/rules-digest.md` §6).
- **Live:** one failed siege, `saves/siege-felsina-failed-0721.SAV` (atk 20,720 v def 34,050; −8.2 % against the formula's 7.6–8.6 %;
  erosion `x×19/20+1`), and Genua at peace (`findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md`). No capture, cascade,
  conquest or AI-v-AI battle has been measured.

### D. `TBattlePols` (unchanged)

`TBattleOver_OK` may open it ("After defeating you in battle X are willing to end …"); a treaty accepted there is the honourable one
[C]. It is the only way a human–AI war ends, short of elimination [C] (§7). It has never been seen live.

**Digest gaps this plan closes:** §12 gap 6 (AI general, sampled and logged), 10 (HI v LI), 3 (battle-screen and `TBattlePols` controls),
11 (repeatability of a battle and of a played battle); the ⬜/🟡 rows of `coverage.md` for field battle, capture, cascade, conquest,
post-battle peace and "Are you sure you want to surrender ?".

## 2. Evidence classes and the two levels of crafting

- **Natural:** reached by `Game` orders from a New Game with a seed.
- **Synthetic L1 (strategic edit):** a save edited **before** the attack (an army's units, quality and morale; a city's fields), and
  the battle then starts fresh. **Placement and initiative stay the game's own**, so L1 is what the sweep uses.
- **Synthetic L2 (block edit):** a **mid-battle** save whose battle block is edited (slot types, troops and positions). The battle
  resumes from it. L2 controls positions, ranges and terrain, but it skips placement.
- **Lab:** run on the battle-lab build. Every sweep row is `lab`. The normal seed build is used for natural anchors and for D.
  The tables keep these classes apart.

## 3. Common infrastructure (one PR, before any battle grid)

**3.1 Lab builds per seed.** `patches/battle_lab.py` bakes the seed into the exe (`lab.py [seed]` → "IC2 lab.exe", built from
`patch_exe` with async sound, no delay and autosave). It writes `BATTLEnn.SAV` before every half-round, with a two-digit counter that
is **not reset between battles**, so one battle per process. Deliverable: `setup/` builds `IC2 lab s<seed>.exe` for seeds 1–3
(more on demand), recording each exe's SHA-256. *Acceptance:* the same battle twice on one lab exe gives identical `BATTLEnn.SAV`
series [R to confirm]; two seeds differ.

**3.2 Trial runner** `runs/experiments/battles/trials.py` (the `fleet-battles/trials.py` pattern). A cell table maps each cell to
(fixture, L1/L2 edits, exe, order, general); per trial it starts a fresh process, loads, snapshots, provokes or resumes, plays, snapshots
again, copies the `BATTLEnn.SAV` series and a post-battle Save As. Results go to append-only `trials.jsonl`; the runner is resumable,
records errors, never retries silently, and kills stale wine pids. *Acceptance:* offline dry run with a fake `Game`; one live trial.

**3.3 Staging tool** `runs/experiments/battles/stage.py`. L1: `set_units`, `set_morale`, `set_supplies`, `set_money`, `set_city`,
`set_unity`, `set_relation`. **Army positions are never edited** (the marker rule is unverified); adjacency comes from `Game.move`.
*Acceptance:* `tests/test_battle_stage.py`: a no-op edit is byte-identical; each edit changes only its own field; the game reads the
edited values back from memory.

**3.4 Result reader** `state/battle.py` plus `Game.army_state`/`nation_state`. It reads every unit (slot, type, troops, quality,
mercenary label), morale, supplies, money, unity and relations, and the news lines of a post-battle Save As. `diff()` gives the winner,
losses per unit and type, promotions, what was taken and the unity change. *Acceptance:* tests on saved pairs; the gallic per-type bug
is fixed.

**3.5 Dialog capture in battles** (driver). `play_battle(..., on_dialog="capture"|"yes"|"no"|"strict")`: any window that appears after
"Battle ended" is screenshotted, OCR'd and dumped with `Game.controls`, and its text is **returned**. Default behaviour stays as it is
until D. *Acceptance:* offline tests in the style of `tests/test_end_turn_reclick.py`.

**3.6 Media.** Screenshots and videos go to `artifacts/run-exp-<name>/` and then the release, cited by bare filename, **never in git**. **Measurements (CLAUDE.md rule 6):** every trial table, `trials.jsonl`, probe log, timing, tooltip/OCR dump and result table is written under the tracked `runs/experiments/data/run-exp-<name>/`, committed and pushed after each batch and at least every 30 minutes, never deleted or overwritten (a re-run writes new files beside the old); saves and screenshots stay out of git, with their SHA-256 in `SAVES.sha256`, and are uploaded to the release as batches finish.

**3.7 Repeatability.** Normal build: `SEED.TXT` is read at program start and New Game only, and loading does not reseed. Lab build:
reseeded at battle start and on resume [R]. Cells that share a seed set are paired samples, and the analyses say so.

## 4. Tasks

S < 1 day, M 1–2 days, L more. "Game" = needs Wine. Sizes per type (standard battalion `std`: LI 15,000, HI 6,000, Ar 3,500,
LC 7,000, HC 2,500): **half** = one unit of `std/2`; **one** = one unit of `std`; **three** = **three units of `std`**, because a
unit's troops are an i16 (45,000 LI does not fit) and one unit per slot is the game's own grain (a reading to confirm, §9).

### B0. Probe (S, game): one battle end to end, both builds

From `FLD-RG` (§4 B1) or the research start save `1_rome_270_winter_11.sav` (release `run-1-rome`, if the player makes it available), nothing auto-answered,
screenshots at every step:
1. The normal seed build: attack. Record the title's phase text, `in_battle`, the window geometry and stacking, the time to open,
   `Game.controls` of the battle window, a tooltip scan of the **whole** toolbar width, the Computer general run, the click count,
   the "Battle ended" box (OCR and controls), whatever opens after OK (§3.5, **left open**, then **No**), and the post-battle
   Save As news.
2. **Save As inside a battle:** with the battle window open, try File → Save As (menu and toolbar). Record whether it is reachable,
   whether the file has block 12, whether it clears anything (`SEL_ARMY`, the battle flag, the window) and whether the battle continues.
3. The lab build (seed 1): the same battle; keep the `BATTLEnn.SAV` series; time per trial (process start to post-battle save).
4. **Resume:** File → Open of `BATTLE05.SAV` (lab) resumes the battle, and the remaining half-rounds equal the original's byte for byte [R].

*Acceptance:* findings note, release `run-exp-battle-probe`; measured time per trial; answers to items 2 and 4.
**Gate:** 5 battles in a row complete headless, and the resume works. If not, stop and report before B3.

### B1. Fixtures (S, game)

`FLD-RG` (Rome's joined army adjacent to Gaul's at Rome's turn, moves > 0; the `gallic-army.py` route, turn 0723), `FLD-R0G` (army 0
alone), `SIE-FEL`, `SIE-TAU` (siege approaches), and terrain fixtures for B9 (the same armies adjacent on plain, forest and mountain
tiles, if they can be reached in a few turns). Built natural, seed 12345, twice byte-identical (`tests/make_battle_fixtures.py`).

### B2. Battle-block decoder (M, game for the inputs)

`state/battle_block.py` parses block 12 from B0's lab series. It decodes the per-slot fields (position, type, troops, quality,
battle-local morale, the word `+2`) and the grid, checked against the screenshots and the strategic armies, and finds the block in game
memory so a live battle can be read without saves (`Game.battle_state()`). Diffs between half-rounds give inferred actions: a position
change is a move; a loss with no adjacent enemy is shooting; a loss next to an enemy is melee. Inferred actions are labelled `[D]`,
since one half-round can hold several exchanges: **actor, target and the split of a loss between shooting and melee are `unknown` in any half-round where the diff does not fix them uniquely (several units changed, or several enemies adjacent), and they are only supplied for every exchange by the B11 hook**. Without B11 the action-level columns of the request are delivered as inferred-or-unknown with the share of rows that are unambiguous stated; the position, troops, quality and morale columns are exact. *Acceptance:* every field named or listed as unknown; the grid ↔ screen mapping
checked on 4 cells; the word `+2` tested as a link to the army's unit index (hypothesis).

### B3. Crafted mid-battle saves (M, game)

`stage.py block`: edit slots (type, troops, quality, morale, position) and the grid in a `BATTLEnn.SAV`, **keeping the strategic armies'
units consistent**. How slots link to units is unknown; B2 decides it. *Acceptance:* the round-trip (a no-op edit is identical, each
edit is local); an edited save loaded in the lab build resumes and plays from the edited state [R], shown by its first half-round
diff; one edit that the game rejects or "repairs" is reported.

### B4. One pairing end to end (S, game)

HI v HI at size *one*, both on Computer general, seeds 1–3, L1. The full logger (§3.2 + B2) produces the sweep-table row and the
per-half-round log, and the same seed runs twice. *Acceptance:* the row format is fixed here; the replay is byte-identical. **Every battle End-turn click's half-round advance is verified** (the `BATTLEnn` series or the battle state moves on after each click); the logger stops with a typed error instead of re-clicking when it cannot prove an advance, so `play_battle`'s 120-click loop (`harness/driver.py:1214-1219`) is never trusted unverified for the dataset.

### B5. The sweep (L, game): the request's main dataset

- **Cells:** attacker type × defender type (**25 ordered pairings**: the attacker is the human side, Rome, both on Computer general) ×
  **3 sizes** (both sides at the same level: half/half, one/one, three/three) × **seeds 1–3** = **225 battles**, L1 from `FLD-RG`
  (natural positions, edited armies, q6, morale 65). Then a **size matrix** for 5 pairings (the diagonal HI-HI, HI→LI, LI→HI, LC→Ar,
  Ar→HC: 3 × 3 sizes minus the diagonal = 6 extra combinations × 3 seeds = 90 battles).
- **Per half-round** (from the block): each slot's position, troops, quality, morale; inferred actor, action and target (`unknown` when ambiguous, see B2); losses on
  both sides; routs (a slot removed or fleeing), surrenders. **At the end:** the result box's text, the strategic armies before and
  after (troops, money, supplies, morale, per-unit quality: promotion), unity, news, the end condition (annihilation, rout, surrender,
  turn limit) and the number of half-rounds.
- **Sweep table:** one row per battle: pairing, sizes, seed, half-rounds, winner, losses each side, end condition, saves (start,
  `BATTLEnn` series, post-battle).
- *Acceptance:* 315 rows, or the gaps stated; every row cites its saves in release `run-exp-battle-sweep`; placement per type and
  initiative (who moves first, in what order) tabulated from half-round 0–1; target choice tabulated (nearest? weakest? by type?)
  as observations of the AI general, not rules.

### B6. Mixed armies and the attacker side (M, game)

Eighteen mixed-army battles, six cells × 3 seeds: Rome's natural composition against Gaul's (`FLD-RG` as is), a balanced mix against a cavalry-heavy
and an archer-heavy mix, and the same three with the roles swapped. Roles swap through a two-human seat game (Rome and Gaul human;
`findings/2026-10-02-two-human-seats.md`). That also answers whether Computer general gets the +3, and what the screen does when both
sides are human. If two humans cannot share a battle, record that and keep Rome as the attacker. *Acceptance:* rows in the sweep
table; the +3 question answered from the battle-local morale at half-round 0.

### B7. Every button and the human order set (M–L, game): the old B5–B6

- **Survey:** every toolbar button (by tooltip) and every control (`Game.controls`) on the battle screen, each clicked once on a lab
  save with its effect read from the block: End turn, Computer general, Surrender (the "Are you sure you want to surrender ?" box, **No**
  then, in a separate trial, **Yes**: what is captured), and any others found.
- **Human order set:** place, move, melee, shoot and end turn by mouse, each verified on `Game.battle_state()`, retried at most twice,
  never a second End turn unless the first provably did nothing. Driver orders: `battle_place`, `battle_move`, `battle_attack`,
  `battle_shoot`, `battle_end_turn`, `battle_surrender(answer)`, with `tests/test_battle_orders.py`.
- *Acceptance:* a table of buttons with their effects and screenshots; each order tested once; 5 played battles in a row complete
  headless; the request's "can the bot drive or auto-play in each case" answered per sweep pairing (auto-play from B5; driven from B12).

### B8. Screenshots: every type at every size, and the layout (S–M, game)

- **Icon ladder:** using L2 crafted saves, set one slot per type to troop counts on a ladder (100, 250, 500, 1,000, 2,000, … up to the
  i16 limit), **plus, for each type, one single unit at about ¼, ½, 1× and 2× its standard battalion (LI 15,000, HI 6,000, archers 3,500, LC 7,000, HC 2,500, capped at 32,767; §9 item 2)**, screenshot the grid at each step, image-diff the slot's icon and bisect between steps where it changes. That gives how
  many variants the screen draws per type and at what troop thresholds.
- **Layout:** the whole screen at placement, at a move phase and at the end; panels, the toolbar with tooltips, the unit information
  shown on click, the result dialog, the surrender box, any post-battle dialog.
- *Acceptance:* a screenshot index (type × variant × threshold) in the finding; every image in the release; thresholds to ±1 step of
  the bisection.

### B9. Terrain (S–M, game)

Does the 336-byte grid change with the strategic tile? Compare the grid of battles from plain, forest, mountain and river-adjacent
fixtures (B1). If it does: two pairings (HI-HI, LC→LI) × the terrain variants × 3 seeds, and L2 edits of the grid to isolate one
terrain cell. If the grid never changes: report that and stop. *Acceptance:* the grid contents per fixture; a stated answer.

### B10. Win rates for the chatbot (M, game): what remains of the old B1–B4

On the normal seed build, Computer general: the natural Rome v Gaul (`FLD-RG`, 30 seeds) and army 0 alone (`FLD-R0G`, 30), the
same-seed repeatability (5 × 2, byte compare), HI v LI at troop ratios 1, 1.25, 1.5, 2 (10 seeds each), and the **morale clamp test**:
army morale 30 v 35 at q6 must give every unit 60, so the two cells must be identical seed by seed [D]; 90 v 95 likewise.
*Acceptance:* win rates with intervals; the 36.6/24.4 % claim against the observed spread; the clamp passes or fails seed by seed.

### B11. Exchange hook (M, conditional)

Research roadmap step 4: a cave on the exchange routine (as `battle_lab.py` does for the half-round end) appends one line per
exchange to `EXCH.LOG`: attacker and defender slots, types, troops, terrain, the random draws and the resulting losses. **It needs the
routine's address and its register/stack layout**, which are in research reports not available here (§9). *Acceptance:* on B4's
battles the log's losses sum to each half-round's block diff; then re-run B5 with the hook (it is cheap once built).

### B12. Scripted plans against Computer general (M, game, lower priority)

`P-HOLD`, `P-FOCUS` (focus fire `f = 4`: attacker loss ×1/5, defender ×13/5 [D]) and `P-CAV`, paired against Computer general on the same
seeds (S-PAR 30, two hard sweep cells 10), plus played-battle repeatability (paint routines write RandSeed). *Acceptance:* a paired
table (McNemar on the discordant pairs), time per played battle, one win and one loss saved per plan. **What this answers:** the request's "can the bot drive or auto-play the battle screen in each case" is answered for auto-play by B5 (Computer general on both sides in all 25 pairings × 3 sizes, success rate stated) and for manual driving by B7 (the order set, tried on a few pairings) and these two sweep cells only; manual driving of all 25 pairings is not claimed.

### B13. Siege threshold and modifiers (S–M, game): unchanged

3 seeds a cell (the outcome is deterministic): atk = def (fails), def ± 1 % (falls / fails), the same atk built with archers (identical
to the others seed by seed), fort 0/50/100/pending, capital loyalty 59 v 60, owner ≠ allegiance, attacker = allegiance (×9/10, missing
from `state/sav.siege_defence`), slot troops. *Acceptance:* every outcome as predicted; one natural capture (`SIE-TAU`) with saves.

### B14. Siege casualties, erosion, capture (M, game): unchanged

Casualties at `r` = 1, 3, 9, 15, 10 seeds each (within `r/119 … r/105`; one shared draw or one per unit; the 2.5–2.85 % claim at `r = 3`;
small units deleted); erosion against the formula; capture effects (owner, unity +9/−15, wealth, treasury, loyalty, slots, the recruit
list); the defection cascade (natural if possible); conquest (lowest priority). *Acceptance:* tables against the formula, each
disagreement listed.

### B15. Instant resolver, AI v AI (M, game): unchanged

Natural sampling from autosave pairs (10 seeds × 6 turns, Rome passive); each "X destroys army of Y" between two AI nations is matched to
both armies; predicted winner by field strength; casualties `loserPower × 40 / winnerPower` %; the 2-in-5 peace. Battles are labelled
*confounded* if an army also moved or hired that turn. A synthetic boost is used if natural battles are fewer than about 20.
*Acceptance:* a table with saves; the rule confirmed or contradicted.

### B16. `TBattlePols` (S–M, game): unchanged

After §3.5. D-LOSS (a human defeat: `FLD-R0G` seeds Rome loses, or a weak synthetic army, 10 seeds), D-WIN (a human victory,
10 seeds): does the dialog open, with what title, text, buttons and controls; **Yes v No** on the same seed: relations (expect −18),
news, reparations, the next turns. The gate is varied (unity, cities) if the rate is neither 0 nor 1. *Acceptance:* screenshots, saves,
`answer_battle_peace(yes)` with a test, the `coverage.md` rows.

## 5. Sequencing and an honest budget

| step | task | battles | time per battle | game time |
|---|---|---:|---|---:|
| 1 | B0 probe and gate | ~10 | measured here | 1 h |
| 2 | §3 infrastructure, B1 fixtures, B2 decoder | ~10 | — | 1–2 h (mostly offline work) |
| 3 | B3 crafted saves, B4 one pairing | ~10 | ~1 min | 0.5 h |
| 4 | **B5 sweep** | 315 | ~1 min [est.] | **5–6 h** |
| 5 | B7 buttons + order set, B8 screenshots | ~60 + ladder | 1–3 min | 3–4 h |
| 6 | B9 terrain, B6 mixed | ~50 | ~1 min | 1–2 h |
| 7 | B11 hook (if addresses), B5 re-run with the hook | 315 | ~1 min | 5–6 h |
| 8 | B16 `TBattlePols`, B13, B14 sieges | ~120 | ~1 min | 2–3 h |
| 9 | B10 win rates, B15 instant resolver, B12 plans | ~250 | 1–2 min | 6–8 h |

**The ~1 min per battle is an estimate.** It is about 10 s of process start, 5 s to load, about 5 s to open the battle and play
it (1.3–1.9 s of compute [R] plus the clicks), and about 10 s for the result, a Save As and copying the `BATTLEnn` series. A fleet
trial took about 0.8 min. B0 replaces the estimate with a measurement. An End turn per trial (for the next autosave's news) would add
30–60 s, so the plan reads the news from a post-battle Save As instead (to be verified in B0). Running several Wine prefixes in
parallel (one `IC2_WORK` per worker) could cut wall time but is not planned.

**Releases and drafts:** `run-exp-battle-probe` (B0), **`run-exp-battle-sweep`** (B2–B9, B11: start, crafted and every `BATTLEnn`
save, screenshots), `run-exp-battle-plans` (B10, B12), `run-exp-siege` (B13–B14), `run-exp-instant` (B15), `run-exp-battle-peace`
(B16). The research request's draft is **`findings/<date>-tactical-battle-sweep.md` on branch `experiment/battle-sweep`**; the bot
gives the user that name and branch for the research repo's intake. If the release call is refused (HTTP 403), keep the artifacts and
post the `gh release create` command.

## 6. What the chatbot will need from this (not planned here)

- `legal`: adjacent targets with the relation; the siege's exact outcome (B13) and casualty range (B14); a field battle's win
  probability and losses by composition and size (B5, B10), flagged as sampled.
- Typed `attack` effects `{kind, winner, losses per unit, taken, unity, dialog}`; `answer_battle_peace(yes|no)` as an explicit order.
- A battle mode `general: computer | plan:<name>` (B7, B12) with the measured time and its failure modes as typed errors.
- Macros (M9) need the margins of B5/B10 and the exact siege rule.

## 7. Risks, and what to verify first

- The battle window below other windows; auto-play stalls; hidden auto-answers (fixed by §3.5): B0 counts each.
- **The lab build and the normal build may differ** (seed at battle start versus at program start): the sweep is `lab`; B10 and B16 run
  on the normal build; one sweep cell is re-run on the normal build as a cross-check.
- **Crafted saves the game "repairs" or rejects**, or slots out of step with the strategic army: B3's acceptance; L1 crafting is preferred
  wherever placement matters.
- **Half-round diffs merge exchanges**: actions inferred from them are `[D]`; the B11 hook fixes it if the addresses come.
- **2–3 seeds per cell** describe how a battle unfolds, not its odds; any win rate quoted from B5 says so, and the odds come from B10.
- **The two-digit `BATTLEnn` counter** caps a process at 100 half-round saves, and it is not reset between battles: one battle per
  process; a battle longer than 99 half-rounds is flagged.
- The AI general is a policy sampled at one geometry (Rome approaching Gaul from the east); B6 and B9 vary it a little, no more.
- Played-battle repeatability (repaint writes RandSeed): B12 tests it.
- Two human seats in one battle may not be driveable (B6): fall back to Rome as attacker.
- Wine-only: every finding is a candidate until the desktop original confirms it.

**Verify first (B0):** one battle on each build, Save As inside a battle, the resume of a `BATTLEnn.SAV`, the time per battle and the
post-battle dialog captured unanswered.

## 8. Review plan

- **This PR:** this file only. `python3 scripts/external_review.py --pr <n>` (DeepSeek V4.1 Flash, then GPT-6 Sol, low, once);
  `/review-pr <n>` if the OpenCode reviewer exits 3; the player's go starts each stage (§9).
- **Each task PR:** code, findings draft, a `tests/results.md` line, `coverage.md` rows; the same review once per PR. Reviewers check
  that every claim cites a save, that `lab`/L1/L2 cells are labelled, and that no binary is in git.

## 9. Questions for the player: answered (2026-10-04, relayed by the player from the research session)

The answers below were written by the research session and relayed by the player in this conversation; the player's separate go is still required before Stage 1 starts (the player said not to start on 2026-10-04).

1. **Start save:** yes, download it: `gh release download run-1-rome --repo diegoami/imp_conquest_fixtures --pattern "1_rome_270_winter_11.sav" --dir <dir>` (the repository is public). It is the branch where the battle was replayed on auto with no freeze: `1_rome_270_winter_7` → `winter_7_b` → `winter_9_b` → `winter_11`. The research repository's `docs/evidence-index.md` maps every cited save to its release.
2. **"Three standard battalions"** = three units, each of one standard battalion. The standard battalions (DAT unit-type table `+0x1A`) are light infantry 15,000, heavy infantry 6,000, archers 3,500, light cavalry 7,000 and heavy cavalry 2,500 (three LI battalions in one unit would pass the 32,767 cap). **For the icon question, also vary a single unit's troop count across the type's range: about ¼, ½, 1× and 2× the standard battalion, capped at 32,767**, to find the thresholds at which the screen changes a unit's drawing (added to B8).
3. **Exchange hook (B11):** not yet. A research pass decompiling the whole battle module started on 2026-10-04; its reports (a tactical-battle spec) will name the exchange routine's address and the order of the Random draws. **Build the hook only after they land**; the player will relay the address.
4. **Budget and staging, and do not start before the player's go.**
   - **Stage 1:** the sweep with Computer general on both sides, plus the screenshots (each unit type at each size, and the full layout), delivered as a findings draft (B0 to B5, B8, with B1-B4 as their prerequisites).
   - **Stage 2:** the exchange-level hook (once the address arrives) and the human-driven side (B7, B11, B12 and the sweep re-run with the hook).
   - B6 (mixed armies), B9 (terrain), B10 (win rates), and the sieges, resolver and `TBattlePols` (B13 to B16) are not assigned to a stage by the research session; they wait for the player's go after Stage 1.
5. **No save from these experiments is committed** (no new file in `saves/`; the 14 already tracked stay, CLAUDE.md rule 1). They go in the experiment's release (`run-exp-<name>`, as §3.6 and §5 name them), cited by bare file name; working copies, including a resumable mid-battle save, stay in the git-ignored `artifacts/run-exp-<name>/` (the committed `saves/` folder gets no new file). Neither `imperial_conquest_2` nor the research repository ever holds a save. **This replaces the plan's request to add fixtures to `saves/` in git** (the existing committed saves stay as they are).
6. **Human-style plan for B12:** the bot scripts it, for example advance in line, shoot when in range, melee the nearest enemy; the plan is recorded exactly with the run so it can be repeated; the player may supply their own later.

## Appendix: unverified items

- Every **[R]** item: byte-identical replay, resume and edited resume of a battle save, 1.3–1.9 s per battle, the code addresses, the slot
  fields; all from reports this repo cannot read.
- The battle block's layout (40 × 44 and 14 × 12 × 2 are guesses); the meaning of the slot word `+2`.
- Whether File → Save As is reachable during a battle and what it clears; whether a post-battle Save As carries the battle's news.
- Whether Computer general gets the +3; whether the grid has terrain; whether a battle has a turn limit.
- Whether a post-battle dialog appeared in the gallic battles; `TBattlePols`'s title, buttons and gate.
- The ~1 min per battle and the budget table; the download of `run-1-rome` (stated public by the research session, not yet fetched).

## Bot validation: B0 (2026-10-04, bot-owned; the plan above is unchanged)

Measured in `findings/2026-10-04-battle-probe.md` (release `run-exp-battle-probe`): the **gate passes** (6 lab seed-1 battles in a row plus seed 2 twice, `gate-summary-20261004-085012.json`: all `BATTLEnn.SAV` series and post-battle saves byte-identical; **57.9 s per battle**, the mean of the six seed-1 trials, process start to post-battle save; an earlier gate run aborted on the Offer of peace box, kept and fixed); Save As inside a battle works through the menu at human-controlled phases (block 12 present, battle continues); resume of a `BATTLEnn.SAV` works and is deterministic given the save, but the **remaining half-rounds are not byte-identical to the original's** (the Appendix's [R] item is contradicted for the lab build: the stream restarts at resume); the post-battle **"Offer of peace"** box appeared after OK in 3 of 17 logged battles. `1_rome_270_winter_11.sav` is a strategic save (flag 0): the probe walks army 0 to (86,28) first. The start save opens a 1143 × 903 unit map and `reset_ui`'s click point lies on it (a selected army is moved): see the finding before B1.

## Bot validation: PR A, infrastructure and B1 (2026-10-04, bot-owned; the plan above is unchanged)

- **§3.1** `setup/build_lab_exes.sh [seed ...]` (default 1 2 3) builds `Imperial Conquest 2 lab s<seed>.exe`, SHA-256 in `runs/experiments/data/run-exp-battle-sweep/EXES-sha256.txt`; seeds 1 and 2 reproduce B0's hashes (`06bc469d…`, `6616a7cc…`), seed 3 is `62fd1290…`. **§3.2** `runs/experiments/battles/trials.py` (append-only `trials.jsonl`, errors recorded and not retried, kills by pid; `tests/test_battle_trials.py` is the offline dry run). **§3.3** `runs/experiments/battles/stage.py` (`tests/test_battle_stage.py`, live read-back passed). **§3.4** `state/battle.py` (`by_type` fixes the gallic per-type bug; `Game.army_state`/`nation_state`). **§3.5** `Game.play_battle(on_dialog=...)`.
- **Driver fixes found by B0:** `reset_ui` clicks a point proven outside every window (`Game.neutral_point`); `Game.open` handles a save that opens with a modal box. **The B0 finding's reason was wrong:** with `1_rome_270_winter_11.sav` the main window's title never contains "turn" (box or no box), so `Game.open` timed out for that reason; `Game.loaded()` now also accepts both map windows. `play_battle` proves every End turn advance (no blind re-click; a battle that ends at the Computer general click gets no End turn click).
- **B1:** `FLD-RG` = the B0 pre-attack state, built twice from the research start save on the normal build (seed 12345): byte-identical, SHA-256 `39edecd1fa74776ef7ed817794b2f2bea951b6b2b36ef09ab42813208095f0ad` (= B0's `NB_pre_attack-20261004-081149.SAV`). `FLD-R0G` is **not distinct** (army 0 is the only army walked; army 13 stays at (93,28)); `SIE-FEL`, `SIE-TAU` and terrain fixtures are not Stage 1 and were not built.

## Bot validation: PR B, B2 to B4 (2026-10-04, bot-owned; the plan above is unchanged)

Measured in `findings/2026-10-04-tactical-battle-sweep.md` (release `run-exp-battle-sweep`, data `runs/experiments/data/run-exp-battle-sweep/`).
- **B2** met: `state/battle_block.py` and `Game.battle_state()` (memory 0x4A0344, header 0x4A0B74..0x4A0B7D); every field named, `state`/`y1`/`x2` flagged as understood only in part; slot positions ↔ screen (occupied or empty) checked on all 168 cells in 3 phases, and the grid words checked against the slots in 763 saves (`b2-analysis-20261004-110552.json`); the grid word is a **sprite** (`side × 20 + 3 × type + size class`, class thresholds std/3 and 2·std/3), no terrain. **The "word +2" is the unit's origin label** (byte +4 of a slot), not a link to the army's unit index (rejected); the header word at +2 is the defender's army index. Unverified: the memory addresses of the attacker-army and `x2` header words.
- **B3** met: `stage.py` `block_edit` (no-op byte-identical, each edit local, mirrored into the army's unit by default); a crafted save resumes and plays from the edited state; reported: the game refills the movement points on resume (a type edit hi → hc is "repaired" in `state`), does not repair an inconsistent grid, ignores position edits made during placement (the AI re-places). **The plan's [R] "an edited save resumes" holds; "remaining half-rounds byte for byte" does not (B0).**
- **B4** met: HI v HI size one, seeds 1 to 3, four runs each, **all byte-identical per seed**, 53.4 s per battle (12 trials), 0 End turn clicks needed; the sweep-row format is `trials.py` `COLUMNS`. The End-turn proof also uses the half-round counter (a BATTLEnn file count is not a proof: a re-run overwrites files).

## Bot validation: PR C, B5 and B8 (2026-10-04, bot-owned; the plan above is unchanged)

Measured in `findings/2026-10-04-tactical-battle-sweep.md`. **B5 met:** 315 rows (225 grid + 90 size matrix), 0 errors, 52.0 s per battle, tabulations in `b5-*-20261004-193033.*` (placement, initiative, target choice, end state, losses, promotions, money, Offer of peace 76 of 315, always after a Gaul win). **B8 met:** the icon size changes at `std div 3` and `2 x (std div 3)` troops, exact to the troop, both sides (`b8-thresholds-20261004-192949.json`); B2's `3 x troops < std` was off by 1 or 2 for Ar, LC and HC; layout screenshots incl. the surrender box answered No. **Infrastructure fact:** one release holds at most 1000 assets (`run-exp-battle-sweep` is full): saves of later work go in per-batch `.tar.gz` archives with manifests (`release_sync.py`; README of the data folder). The research repo's decompiled battle report was used as [R-code] and checked against the data (`x2` = side to move; words 8 and 9; icon thresholds).

