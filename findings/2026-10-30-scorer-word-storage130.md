# The AI target scorers keep the winner as a signed word and add its distance as a word; only the city scorer can overflow

**Tag:** [confirmed] from the disassembly. The original instructions were run under emulation with stubbed helper results:
22 boundary controls, each matching the word model below exactly, plus 2 zero-divisor traps. Reachability was measured on
original saves with the real helpers: 251,182 scorer calls on 8,872 distinct parsed saves, each result equal to the model.
**Task:** research [#130](https://github.com/diegoami/imperial-conquest-2-research/issues/130) (remake #1216 item 2),
delegated to conquest on 2026-10-30.
**Background:** `2026-10-16-strategic-ai-regions-resupply.md` said both scorers "store the winning score as a word" and end
with a word addition, without overflow cases. This finding pins both.

## The rule (both scorers)

`FUN_0044ece4` (city, 0x44ECE4–0x44EE5C) and `FUN_0044ee60` (army, 0x44EE60–0x44EFC3). Both are called with ax = the army,
edx → index word, ecx → score word, and [esp+4] → distance word, and both end with `ret 4`.

1. **Initial values.**
   - Score word = −10000 (`0xD8F0`; 0x44ED0E / 0x44EE82); distance word = 0.
   - **City:** index word = −1 (0x44ED06).
   - **Army:** the index word is **not written**. It keeps whatever the caller had there.
2. **The candidate score is 32-bit signed** (`imul` / `cdq; idiv`, quotient truncated toward zero):
   - **City:** `s = FUN_0044a98c(city)`, and `s = s*9/10` when the army's owner equals the city's allegiance (+0x14).
     `score = A*110/s − d`. In another region: `score −= trunc(score/2)` (0x44EDD4: `sar 1`, then `adc 0` when negative).
     ×2 when `A > s` and `d < 7`; ×2 again when the city is a capital and `2s/3 < A`. Here `A = FUN_0044a930(army)` and
     d is the distance.
   - **Army:** `score = A*110/s − d` with `A = FUN_0044a8cc(army)` and `s = FUN_0044a8cc(target)`. The same halving
     applies in another region. Then `score = min(score, 1000)` (0x44EF58), then `+1000` when `A > s` and `d < 7`.
3. **The distance is a word:** the low 16 bits of `FUN_00449018`'s eax.
   - **City:** kept as a word (0x44ED72), then sign-extended where it is used.
   - **Army:** sign-extended to 32 bits at once (0x44EF15). The store keeps the low word.
4. **The comparison:** the 32-bit candidate against the **sign-extended** stored word (`movsx`; 0x44EE19 / 0x44EF7C).
   - The candidate wins only if it is **greater** (city `jge` skip, army `jle` skip). So **an equal score keeps the earlier
     candidate**, and this holds after truncation too.
5. **The store** happens only on a win: index = the loop index (word), score = **the low word of the 32-bit candidate**
   (0x44EE2A / 0x44EF90), distance = the low word of d.
   - **This is the truncation point.** A winner above 32767 is kept as `score − 65536`, and the next candidate is compared
     against that value.
6. **The final add:** `add word [score], distance` (0x44EE53 / 0x44EFBA): a 16-bit addition that wraps modulo 65536.
   - There is no meaningful return value. eax holds the distance word in ax and stack-pointer bits above it, and neither
     caller reads it.
   - The callers (`FUN_0044f31c` 0x44F3B8–0x44F4B0, `FUN_0044efc8` 0x44F188–0x44F1CE) read the score as a **signed word**
     (`cmp word, 0x64/0x46/0x55` with `jle`) and the distance as a word.
7. **No target:**
   - **City:** index −1, score −10000, distance 0.
   - **Army:** the index word is untouched, score −10000, distance 0.
   - Every caller uses the index only behind a score test above 70, 85 or 100, so the untouched army index is never read.

**A minimal implementable form:**

```
best_word = -10000; dist_word = 0; index = (city ? -1 : untouched)
for each eligible candidate in table order:
    s32 = candidate score (32-bit, truncating divisions, army: min(...,1000) then +1000)
    if s32 > sign_extend16(best_word):
        index = i; best_word = low16(s32); dist_word = low16(d)
result = sign_extend16(low16(best_word + dist_word))
```

The remake (`AiArmyTargetTree.ScoreCityTarget` / `ScoreArmyTarget` at v0.8.5 `1622407e`) keeps a `long` best and returns
`bestScore + bestDistance` as a `long`. With no target it returns **0**, where the original's word holds −10000. Both are below
every caller threshold.

## Controls (original instructions, stubbed helper results)

`runs/experiments/scorer130/scorers.py controls`. The helpers (`FUN_0044a930`, `FUN_0044a98c`, `FUN_0044a8cc`,
`FUN_00449018`, `FUN_0044cab4`, `FUN_0044eb9c`, `FUN_0044b8d0`) are stubbed at their entry, so each returns a chosen value
for the candidate being visited. The scorer's own instructions run unmodified on the #187 snapshot, with Carthage at war with
the candidates' owner.

Every row's emulated result equals the model above, the candidate scores included (`model_matches` in `controls-v1.json`).
The "wide" column is the same arithmetic with a 32-bit best and a 32-bit add.

| Control | A | candidates (s, d) | candidate scores | stored best word | **original result** (index, score) | wide |
|---|---:|---|---|---:|---|---|
| city ordinary | 15000 | (22000, 10), (5000, 4) | 65, 652 | 652 | **2, 656** | 2, 656 |
| city 32767 + carry | 32777 | (110, 10) | 32767 | 32767 | **1, −32759** | 1, 32777 |
| city 32768 | 32778 | (110, 10) | 32768 | −32768 | **1, −32758** | 1, 32778 |
| city 65535 | 65545 | (110, 10) | 65535 | −1 | **1, 9** | 1, 65545 |
| city 65536 | 65546 | (110, 10) | 65536 | 0 | **1, 10** | 1, 65546 |
| city final 32757 + 10 | 32767 | (110, 10) | 32757 | 32757 | **1, 32767** | 1, 32767 |
| city final 32757 + 11 | 32768 | (110, 11) | 32757 | 32757 | **1, −32768** | 1, 32768 |
| city negative halving (other region) | 0 | (110, 7) | −4 (−7 − trunc(−3.5)) | −4 | **1, 3** | 1, 3 |
| city below the sentinel | 0 | (110, 10001) | −10001 | (−10000) | **−1, −10000** | −1, −10000 |
| city just above the sentinel | 0 | (110, 9999) | −9999 | −9999 | **1, 0** | 1, 0 |
| **city: a truncated first winner loses to a smaller second** | 40010 | (110, 10), (1000, 10) | 40000, 4391 | 4391 | **2, 4401** | 1, 40010 |
| city: the larger second winner is stored negative | 30010 | (110, 10), (80, 10) | 30000, 41253 | −24283 | **2, −24273** | 2, 41263 |
| city: a tie after truncation keeps the first | 65646 | (110, 10), (65646, 10) | 65636, 100 | 100 | **1, 110** | 1, 65646 |
| city: distance eax 0x10003 is the word 3 | 1100 | (110, 0x10003) | 2194 | 2194 | **1, 2197** | 1, 2197 |
| army ordinary | 15000 | (22000, 10), (5000, 4) | 65, 1326 | 1326 | **2, 1330** | 2, 1330 |
| army cap | 50000 | (110, 10) | 1000 | 1000 | **1, 1010** | 1, 1010 |
| army cap + 1000 (the maximum) | 50000 | (110, 3) | 2000 | 2000 | **1, 2003** | 1, 2003 |
| army negative halving | 0 | (110, 7) | −4 | −4 | **1, 3** | 1, 3 |
| army no target | 0 | (110, 10001) | −10001 | (−10000) | **index untouched (0x1234 left), −10000** | same |
| army: two capped scores tie | 50000 | (110, 10), (120, 20) | 1000, 1000 | 1000 | **1, 1010** | 1, 1010 |
| army, diagnostic: distance word 40000 | 0 | (110, 0x9C40) | 1000 (0 − (−25536), capped) | 1000 | **1, −24536** | same |
| army, diagnostic: final add 1000 + 32000 | 50000 | (110, 32000) | 1000 | 1000 | **1, −32536** | 1, 33000 |
| city / army, s = 0 | 100 | (0, 10) | — | — | **#DE trap** at `idiv` (0x44EDAB / 0x44EF2C) | — |

## What can happen in normal play

**The army scorer cannot truncate.** After the cap and the bonus, a candidate is at most 2000. A winner must also exceed the
stored word, which starts at −10000 and only rises. So every winner lies in (−10000, 2000], and the word store is lossless for
**any** register values. The final add can wrap only if the winner's distance word is above 30767, or negative (the two
diagnostic rows). A map distance is far below that. **The 1000/2000 cap makes both army boundaries unreachable in normal
states.** Only the final-add boundary can be reached, and only with a diagnostic distance word.

**The city scorer has no cap.** Its candidate is `A*110/s − d`, doubled up to twice. It passes 32767 when the army's strength
is large against a weak city: about `A/s ≥ 298` with no doubling, or `≥ 75` with both doublings.
- A is `(troops/80) × morale`, with unit type 2 counted ×3; morale is 51–70 in normal play.
- s is `150·loyalty + 250·fortification% + 200·population`, adjusted for a capital, a foreign allegiance and the garrison
  term.

**The survey** (`scorers.py survey`) runs both scorers with the real helpers for every army of every nation in each save. That
is a superset of the calls the game makes, which come only from an AI seat's own armies. Each call is checked against the model,
candidate by candidate: **0 mismatches in 251,182 calls**.

| | city scorer | army scorer |
|---|---:|---:|
| calls / with a target | 125,591 / 62,672 | 125,591 / 46,056 |
| largest candidate | **13,022** | 2,000 |
| smallest candidate | −205 | −105 |
| largest result (best + distance) | 13,023 | 2,006 |
| largest A/s | 59.2 | 529 |
| winners above 32,767 / final adds that wrapped | **0 / 0** | 0 / 0 |
| s = 0 (divide trap) | 0 | **38** |

**What the survey shows:**
- **The city boundary was not reached:** the largest candidate, 13,022, is about 40% of 32,767. The corpus is early play (to
  turn 0759), so a later game with a far larger army may come closer.
- **All 38 divide traps are in staged saves;** no natural game's save has one: the `run-exp-battle-sweep` b8 starts and their
  `BATTLE01` saves, the `run-exp-siege-army-removal` one-man / u79 / ar26 starts, and the join-over-20-units tests.
  - The target army's strength `FUN_0044a8cc` is `(Σ troops·weight/100)/80 × morale`, which is 0 for an army of fewer than
    about 80 weighted troops.
  - So the original army scorer divides by zero whenever such an army is an eligible target. Whether natural play produces
    one in reach of an AI army at war is not established here.

**Diagnostic only:**
- a negative A or s;
- `A*110` beyond 2^31 (A > 19,522,909);
- distance words ≥ 32768;
- s = 0 for the **city** scorer (a city of loyalty 0, fortification 0 and population 0).

**Not purely diagnostic:** s = 0 in the **army** scorer traps with a divide error (#DE at 0x44EF2C), and staged saves reach it
(above). The original has no guard. The remake skips such candidates (`theirStrength <= 0`, and `cityDefense <= 0` for cities),
which is a choice where the original has no defined result.

## Limits

- The survey covers the original saves on this machine (10,105 distinct files, 8,872 parsed; staged test saves included; turns up to 0759). It is not a proof that no normal state reaches the
  city boundary.
- Callers were read only for how they consume the outputs. Their thresholds (100, 70, 85) are quoted from the disassembly,
  not re-measured.
- The fleet hunt `FUN_0044f4f8` ends with the same word add (0x44F5FB) but was not part of this task (#131 covers the fleet
  phase).
- No new gameplay. Emulation used the pinned unpatched EXE and the #187 snapshot, which stay out of git.

## Evidence

- Script: `runs/experiments/scorer130/scorers.py` (`controls`, `survey`).
- Data: `runs/experiments/data/run-exp-scorer130/controls-v1.json` and `survey-v1-public.json` (aggregates and the
  trap examples without hashes).
  - The full survey, with the corpus hashes, is kept privately in `artifacts/run-exp-scorer130/private/survey-v1.json`,
    because the corpus includes owner-derived material. Its hash is in `PRIVATE.sha256`.
- Disassembly: addresses as cited; the decompile `all_app_functions.txt` :52657–52776 for the same routines.
