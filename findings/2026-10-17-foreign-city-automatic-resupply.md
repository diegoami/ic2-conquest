# Foreign-city automatic resupply: entry-purse eligibility and live purchase arithmetic

**Status:** draft for research [#31](https://github.com/diegoami/imperial-conquest-2-research/issues/31), conquest #92 / PR93. Original-side research; no build edits or T177 expansion. Build [#759](https://github.com/diegoami/imperial_conquest_2/issues/759) and [#823](https://github.com/diegoami/imperial_conquest_2/issues/823) require their own evaluation of any new evidence.

`[code]` means the pinned original listing; `[x86]` means the original complete city-loop instructions executed on the staged save records under Unicorn, without patches or stubs. `[Wine, staged]` means the original game played one AI seat with explicitly edited records. There is no native Windows confirmation. This extends the [October 16 support finding](2026-10-16-strategic-ai-regions-resupply.md); its embarked-army answer and own-city controls remain established.

## Original call paths and eligibility

The full `all_app_functions.txt` SHA256 is `2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`, rechecked locally. The seeded original executable is `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`. Complete source extracts and caller inventories are in `runs/experiments/data/run-exp-resupply31/complete-source-audit.txt`, `complete-source-provenance.json`, and `upstream-seat-source.txt`; numbered lines refer to the full pinned listing.

`[code]` AI-seat `FUN_0044fa20` calls diplomacy `0044fb7c`, recruitment `0044ffbc`, army handling `0044f31c`, then fleet handling `0044f608` (53213–53220). Army support therefore precedes fleet support when both compete for a stockpile. That order is source evidence; the new controls isolate the subject rather than measure a shared AI army/fleet stock race.

`FUN_0044f31c` calls army city loop `0044e41c` for each own army while no battle is active, **before** its positive-moves gate (52924–52928). The loop does not test embarked status, follow a carrier link, or check terrain/coast. Launched own fleets (`countdown == -1`) run `0044e5dc` before movement (53046–53049). Both loops visit all 334 cities in ascending table index and compute Chebyshev distance from the subject's stored coordinates using `00449018`.

| Gate | Army loop `0044e41c` | Fleet loop `0044e5dc` |
|---|---|---|
| Range | distance < 5 | distance < 4 |
| Own city | stock > 0 | no stock requirement |
| Foreign city | relation != 3, stock > 0, entry purse > 0 | signed relation < 3, stock > 0, entry purse > 0 |
| Purse captured | once, before city 0 (52234) | once, before city 0 (52288) |
| Per-provider helper | `0044f6d8` | `0044f7e4` |

On normal diplomacy codes 0/1/2/3, peace, trade and alliance permit purchase; war blocks it. The `!= 3` and signed `< 3` predicates differ for deliberately staged out-of-domain values, which are not evidence that natural diplomacy produces those values. An own city can also satisfy the syntactic non-war branch, but the stock/entry-purse alternatives above describe the effective gates.

The army loop also contains a separate mercenary-offer scan (52248–52268). Every new input clears the offers so a unit join cannot alter capacity midway through this experiment.

The helpers have other callers: army movement `0044d734` calls `0044f6d8` beside a non-war target city (51655); fleet movement `0044e1fc` calls `0044f7e4` in its adjacent non-war target-city branch with moves remaining (52193). These are separate movement paths, not extra gates in the automatic city loops. No issued-order experiment was necessary for the requested zero-move automatic controls; manual Supply-dialog behavior is not inferred.

## Helper arithmetic and operation order

`[code][x86]` Let `S` be current supply, `P` the **live** unit purse, `C` city stock, and `trunc` signed division toward zero. `00448fd0` compares signed low words; signed word storage and wraparound remain part of the original. For the bounded staged values below no intermediate overflows.

```text
army capacity K = trunc(sum of all 20 slot troop words / 100)
fleet capacity K = ships * 8
Q = min(signed_word(K - S), C)

foreign branch:
    Q = min(Q, trunc(P / 5))
    cost = trunc(Q / 5)
    purse -= cost
    seller nation treasury += cost

finally, in either ownership branch:
    unit supply += Q
    city stock -= Q
```

The quantity is capped by **purse / 5**, then cost is **quantity / 5**. It is not a cap of purse * 5. Foreign purchase directly changes the unit purse and seller treasury; there is no buyer-national-treasury debit in that branch. A positive stock of 4 can transfer for zero cost. Exact capacity yields Q=0. Above capacity yields negative Q rather than clamping to zero, returning stock and reversing the cost. These are literal source behaviors on staged inputs, not recommended build changes.

The entry purse is used only by the loop eligibility gate. Earlier own-city grants cannot make a zero-entry-purse subject eligible for a later foreign city. Once entry purse is positive, each eligible provider recomputes quantity from the updated supply, stock and **live** purse. Stock and purse commits happen within each helper before the next city is visited.

Own-city branches are separate. The army helper returns purse excess above 1000 to its own treasury, then adds 500 if purse < 500 and treasury > 0. The fleet helper adds 100 if purse < 100 and treasury > 100; independently, condition < 95 repairs to 100 for `trunc((100-condition)*ships/5)`, without a solvency gate. Both compute Q before their purse operations and commit supply/stock after them. Foreign providers cannot reach those grant/repair branches because the ownership test takes the foreign branch. The new own-city controls are comparisons, not evidence of foreign repair.

## Matched original-game controls

The runner was recovered read-only from unpublished research work, then adapted into `runs/experiments/resupply31/probe.py`. It uses the existing conquest driver/staging helpers and the unchanged source save `fleet-port-antium-0734.SAV`. The source hash, actual executable hash, driver/staging hashes, runner hash, prefix/display fingerprint and exact staging edits are logged. Seed is 12345. Every completed control runs Armenia human → Rome AI → Bithynia human, turn **0734**, without a weekly tick.

Each subject has moves 0 at stored coordinates (102,49). Army capacity is 300 (30,000 LI), fleet capacity 720 (90 ships). Default supply/purse/stock are 50/500/100; fleet condition is 94. All other cities are relocated outside range and have zero stock; providers are explicit table indices 88/89/90. Other units are disabled; an embarked subject has a human-owned carrier, preventing AI fleet support from consuming its city's stock. The land/embarked records use identical army coordinates. The carrier-far control deliberately separates carrier and army coordinates.

These are synthetic record controls. City relocation/ownership does not rebuild city lists or map overlays. They support the record-reading automatic loops, not natural movement, harbor reachability, or a remake coordinate-synchronization claim. Loaded city/army/fleet/nation records are checked against the staged input before advancing the AI seat.

Binary evidence: [run-exp-resupply31](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-resupply31). Complete filenames and SHA256 are in `SAVES.sha256`; before/after fields and failures remain in the unique `wine-*.jsonl` files. Summary and final matrix follow after the active batch completes.

## Limits and retained failures

The prior research session completed land:peace and was interrupted during the first embarked load. Both attempts were retained. During this session a prefix-copy mistake followed Wine's `z:` symlink and exhausted `/tmp`, interrupting a fleet:war save copy. The original manifested saves all passed digest verification after space recovery. The incomplete zero-byte autosave remains outside the manifest and is never treated as a result. The fleet:war case was repeated under a fresh unique name. No measured save was deleted or overwritten.

One release upload received HTTP400 Bad Content-Length for that incomplete zero-byte save. The same uploader was corrected to select only manifested complete saves and verify each digest; the same `gh release upload` route then succeeded. No release policy refusal, overwrite, alternate API or credential route was used.

Hostile full AI seats can recruit before support: buyer treasury changes in those cells are confounded. Exact observed treasury changes are retained, while caller-only x86 execution isolates the support loop and verifies the unchanged subject/stock/seller fields. A whole-seat treasury delta is not attributed to support. No native Windows runner was available, and no natural-play or whole strategic-AI equivalence claim is made.
