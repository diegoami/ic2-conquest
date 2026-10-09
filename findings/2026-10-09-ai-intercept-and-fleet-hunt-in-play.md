# AI checks 3 and 4 in play: the homeland intercept and the fleet hunt-or-port decision fire as decompiled, logged by an inert hook over 144 End turns. The hunt score does not fall with distance, and a fleet called as a ferry skips the hunt

**Status:** promoted 2026-10-09 into imperial-conquest-2-research at `b538a0d` (by ic2-research, from `4ede45f`); this draft is kept for history, the research repo is canonical. It does the two in-play checks left open by `2026-10-07-ai-turn-corroboration.md` (research): check 3, the homeland intercept dispatch (report `2026-10-07-strategic-ai-turn.md` §3.1), and check 4, the fleet hunt-vs-port decision (§4). The player asked for it on 2026-10-09. It also corrects §3.1, §4 and §5 of the report on four points.

**Tags:**
- `[confirmed]` (Wine): logged by the hook in natural play, nothing edited, and checked against the decision-time state.
- `[confirmed: decompile]`: capstone disassembly; excerpts are in the data folder.
- `[derived]`: inferred, not observed directly.
- **L1:** the one staged run, labelled.

## How it was observed

- **The hook:** a build of the seed exe (`patches/ai_hook.py`) re-points the AI's decision calls to stubs. Each stub logs the decision and jumps on to the original target:
  - the two moves of `FUN_0044efc8`: toward the threat, or to the capital;
  - the two moves of `FUN_0044f608` after the hunt scorer: hunt, or port;
  - in v4, also its stored-destination move.

  Each record holds the nation, the unit, the target, the caller's locals (scores, distances, chosen indices) and the unit records **at decision time**. That matters because army and fleet indices shift within a turn, and AI moves in a save are left over from the unit's last turn.
  - The stubs preserve every register, flag and the stack (`tests/test_ai_hook.py`, unicorn, 5 sites × 4 buffer states × 20 random states).
  - **The hooked game is byte-identical to the plain one:** 25/25 autosaves (v1) and 25/25 (v2) at seed 12345, 40/40 (v2) and 40/40 (v3) at seed 2.
- **The games:** natural play from `saves/run0-start-AUTO0720-seed12345.SAV`, with Rome human and only End turn clicked. Seeds 12345 (25 End turns), 2 (40), 10 (40) and 14 (39), so **144 End turns**.
- **The counts: 457 decisions logged**: 102 intercepts toward an army, 7 intercepts to the capital, 341 port moves and 7 hunts. **All 457 pass every decision-time check** (`summary.json`).

## Check 3: the homeland intercept `[confirmed]`

**What the code does** (`FUN_0044efc8.asm`, `[confirmed: decompile]`):

1. **The threats:** up to 9 foreign armies (owner ≥ 0, not the nation) whose position is in the capital's region box (`FUN_0044eb9c` = 0). They must be within Chebyshev distance 20 of the capital when the threat's owner is at war with the nation (relation 3), else within 10.
2. **The responders:** own armies with moves > 0, while fewer than threats + 2 have been dispatched. An army is skipped when an army target or a city target scores above 100, its distance is below the army's moves, and the capital is more than 3 × moves away.
3. **The choice:** the nearest threat. **A threat whose owner is not at war is accepted only when the responder is at least 20 from the capital** (`cmp [esp+6], 0x14`). This rule is not in the report.
4. **The branch:**
   - toward the threat army (`FUN_0044dba8(army, threat xy)`) when the nation is at war with its owner and it is on land (cell ≠ −1);
   - otherwise back to the capital.

**In play** (`analysis_hook_s*.json`):
- **102 dispatches toward an enemy army** in all four seeds, by Galatia, Illyria, Greece, Macedonia, Seleucid and others. For every one:
  - the responder is the nation's own and has moves at decision time;
  - the game's own distances to the capital and to the threat equal Chebyshev distances recomputed from the logged positions;
  - the threat is within 20 of the capital and at war with the nation;
  - the exemption rule does not apply.
- **7 dispatches back to the capital,** all of the "not at war" kind and all Gaul's (seeds 12345 and 10): armies pulled home from 27 to 52 tiles away because a Carthaginian army (relation 2) stood 1 to 9 tiles from Gaul's capital. The ≥ 20 acceptance rule held in all 7.
- **No threat aboard a fleet occurred,** so that branch is not observed.
- **A war declared earlier in the same turn counts:** in 7 seed-14 records Greece and Macedonia go to war in the diplomacy phase (news "Greece declares war on Macedonia."), which runs before the army phase. Their armies are dispatched at each other in the same turn.
- **The armies then move:** 54 of the 102 armies ended the round closer to the threat's logged position, and 30 were gone or renumbered by the next save. The other 18 ended level or farther: the threat itself moves later in the round. Of the 7 sent home, 5 got closer to the capital.

## Check 4: the fleet hunt or port `[confirmed]`

**What the code does** (`FUN_0044f4f8_f608.asm`, `[confirmed: decompile]`). For each own fleet that is launched (countdown −1):

1. resupply (`FUN_0044e5dc`), then pick a port (`FUN_0044e9a8`);
2. **if the fleet has a stored destination (+4 ≥ 0), sail there, with no hunt and no port choice;**
3. otherwise, if moves > 0, score the hunt (`FUN_0044f4f8`): **above 100 (strictly), chase the target fleet's position; otherwise sail to the port.**

**In play:**
- **341 port moves,** all with a hunt score ≤ 100 (−10,000 when no enemy fleet qualifies) and a target equal to the chosen port city's position. Every fleet was launched, had moves and had no stored destination.
- **7 hunts** (seeds 2 and 14), all with a score above 100: Numidia chasing Ptolemaic (4 at seed 2, 1 at seed 14), Ptolemaic chasing Numidia, and Carthage chasing Ptolemaic.
  - All at war, and the target was the hunted fleet's position at decision time.
  - All 7 ended the round closer to it.
  - **They chased across 26 to 181 tiles.**

## Corrections to the report (research `2026-10-07-strategic-ai-turn.md`)

1. **The hunt score does not fall with distance (§4).**
   - In the loop the score is `my × 100 / their − d`, doubled when the target is weaker and `d < 18`. **On return the chosen target's distance is added back** (0x44f5f4: `add [score], best distance`).
   - So the score compared with 100 is `my × 100 / their` for a target at 18 or more, and `2 × (ratio − d) + d` for a weaker one closer than 18. Distance only ranks the candidates.
   - **In play, an AI fleet chases any weaker enemy fleet at war that is at sea, however far.** Numidia chased Ptolemaic from 174 tiles away (`AUTO0751.SAV`, seed 2).
   - The 6 hunts logged by v3 (seed 2) are reproduced **exactly** by this formula, with the decision-time ships and condition and one jitter pair each (`hunt_bounds_hook_s2.v7.json`, the last version). The report's formula reproduces none of the 6 (`hunt_bounds_hook_s2.json`, scored with the before-turn values that v2 recorded).
2. **Boundaries:**
   - the hunt needs a score **above** 100 (`jle 0x64`), not ≥ 100;
   - the doubling needs `d < 18` (`cmp bx, 0x12; jge`), not "within 18".
3. **The strength jitter is `v + Random(4) × (v div 10)`** (`FUN_0044aa54`), not `Random(4) × v / 10` (§5). The rounding matters for an exact fit.
   - The carried army adds `(Σ troops, ×3 for archers) div 80 × morale div 50`, with the morale **at decision time**.
   - In the turn-36 hunt, army 7's morale had already fallen from 70 to 68, because its supplies ran out that turn.
4. **The intercept accepts a non-war threat only for a responder at least 20 from the capital (§3.1).** All 7 capital dispatches were of this kind.

## A ferry call takes the fleet before the hunt `[confirmed]` + `[derived]`

- **The staged start (L1):** `saves/fleets-adjacent-at-sea-0723.SAV`, with Carthage made a computer seat (human flag +0x490 → 0). Carthage's 90-ship fleet (condition 74) sits adjacent to Ptolemaic's weaker 70-ship one (condition 63), at war.
- **It never hunted** (`staged_hunt.jsonl`):
  - In 3 seeds on v3, Carthage's fleet logged neither a hunt nor a port move.
  - The v4 run shows why: the fleet already had a **stored destination, (96,78), at decision time**, although it was −1 in the save. It sailed there, ending the round at (96,78).
- **What set the destination** `[confirmed: decompile]`: two places in the code compute the address of a fleet's +4 destination (`0x49C270 + 26·i`, the only absolute references to that field), both in the army movers. Each passes it to `FUN_0044cd08`, which stores a path point through it on return (0x44CEB4 through ECX, 0x44CEBC through its stack argument; `FUN_0044cd08.asm`). Writes through a fleet pointer held in a register (a human sail order, for example) were not scanned. (Corrected 2026-10-09 after promotion at research `b538a0d`: the draft said "only two places write" it.)
  - `FUN_0044d9a8` (`FUN_0044d9a8.v2.asm`), called from 0x44db8b: an army whose target lies in another region box takes the nearest own launched, empty fleet with moves. If the fleet is adjacent, the army embarks (0x44b79c); otherwise 0x44da5a passes the fleet's +4 to `FUN_0044cd08` (stack argument).
  - `FUN_0044dba8` (`FUN_0044dba8_head.asm`), 0x44dbc9-0x44dbf2: an army aboard (cell −1) finds its fleet and passes that fleet's +4 to `FUN_0044cd08` (ECX), so it steers its fleet.
- **The link here** `[derived]`: Carthage's army 3 stood 3 tiles from (96,78) before the turn, so it most likely called the fleet. The army phase runs before the fleet phase, so **a fleet called as a ferry skips the hunt and the port choice that turn.**

## Evidence

- **Data:** `runs/experiments/data/run-exp-ai-intercept-hunt/` (its `README.md` lists every file):
  - hook logs `hook_s{12345,2,10,14}.jsonl`, controls `plain_s{12345,2}.jsonl`, `staged_hunt.jsonl`;
  - checks `analysis_hook_s*.json`, `hunt_bounds_hook_s*.json`, `summary.json`;
  - disassembly excerpts;
  - `EXES-sha256.txt`, `SAVES.sha256`, `MANIFEST-saves.txt`.
- **Code:** `patches/ai_hook.py`, `tests/test_ai_hook.py`.
- **Release** [`run-exp-ai-intercept-hunt`](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-ai-intercept-hunt): every autosave of the runs (for example `hook_s2_AUTO0751.SAV`, the 174-tile hunt; `hook_s14_AUTO0758.SAV`, the same-turn war), `staged_hunt_start_carthage_ai.SAV`, and `staged_hunt_s1_AUTO0724.SAV`.
- **Start saves:** `saves/run0-start-AUTO0720-seed12345.SAV`, `saves/fleets-adjacent-at-sea-0723.SAV`.

## Not established

- **The threat-aboard branch** of the intercept (sent to the capital): not seen.
- **The region box** (`FUN_0044eb18`): not modelled. The threat list was not rebuilt independently; the radius and war tests were checked on the chosen threat only.
- **The port choice** (`FUN_0044e9a8`'s candidates and scores): only its branch was checked, not which port won.
- **Hunts by other nations:** only Numidia, Ptolemaic and Carthage hunted. The one seed-14 hunt was logged by v2, which has no fleet ships or condition, so its score was not recomputed.
- **The staged ferry link:** derived; the army's call itself was not hooked.
- **The desktop original:** Wine only.
