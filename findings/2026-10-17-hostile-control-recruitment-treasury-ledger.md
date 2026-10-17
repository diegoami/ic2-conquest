# Hostile resupply controls: recruitment accounts for the treasury losses

2026-10-17. **Promoted** through research [PR34](https://github.com/diegoami/imperial-conquest-2-research/pull/34), merge `64adfb1aedb6a277bcf3fa41537f574d9448a905`; research [#33](https://github.com/diegoami/imperial-conquest-2-research/issues/33); conquest [#95](https://github.com/diegoami/ic2-conquest/issues/95). Implementer Codex/OpenAI; owner-selected reviewer MiniMax M3. This attributes the three hostile treasury confounds retained in [research31's promoted report](https://github.com/diegoami/imperial-conquest-2-research/blob/2ed46252e28a5ac48ff7aafccecced12b48ed090/docs/reports/2026-10-17-foreign-city-automatic-resupply.md). That report and the original measurements remain unchanged.

**[confirmed, partial]** The Roman treasury losses are recruitment queue debits: 1,010 for land and aboard, 1,445 for fleet. The exact ledger has zero treasury residual. Three fresh unchanged-original staged-Wine replays reproduce the retained loaded/post saves byte-for-byte. Separate unmodified-original-x86 controls, initialized from the retained loaded saves and fresh pre-click runtime inputs, put every debit in recruitment, before army/fleet support. Wine itself was not observed at phase entry. This does not promote native/natural behavior or complete strategic-turn equivalence.

Canonical report: [hostile-control recruitment treasury ledger](https://github.com/diegoami/imperial-conquest-2-research/blob/64adfb1aedb6a277bcf3fa41537f574d9448a905/docs/reports/2026-10-17-hostile-control-recruitment-treasury-ledger.md). Research #33 is closed. Independent intake verified 35 packet blobs unchanged in conquest merge `356171b0e27d6f188a9f45f60eceda277c5dbfd5`, 997 source-extract lines, 286 instructions, nine fresh plus nine selected legacy save/release digests and all three Wine endpoint identities; reran all three original-x86 controls and independently decoded the queue/DAT ledger with residuals 0/0/0. Research MiniMax M3 session `ses_eb6fd7a66ffeaRTTx2XUQxqFUI` approved intake. Research GitGuardian passed; the source PR96 size-skipped scan remained NEUTRAL and was merged with the owner's explicit authorization.

The canonical report separately retains the input→loaded Armenia13 Information-form WORD708→704 at `+0x482`, distinct from the next-human Bithynia11 x86/Wine endpoint UI mismatch below. The historical measurements and limits remain unchanged. IC main reads the canonical research report through the owner-carried handoff; no direct main/build message is claimed.

## Evidence and pins

Tracked evidence: [run-exp-resupply33](../runs/experiments/data/run-exp-resupply33/README.md), especially `summary-canonical-20261017.json`, the three `phases-*-byte-audit-20261017.json` controls, three `replay-*.jsonl` logs and their `runtime-preclick-*.json` snapshots. Nine fresh binary saves are in [release run-exp-resupply33](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-resupply33); `SAVES.sha256` and `release-verification-20261017-1031.json` verify all nine against local bytes and published asset digests. Original cases remain in [release run-exp-resupply31](https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-resupply31).

| Case | Retained stem (each has `-input.SAV`, `-loaded.SAV`, `-post.SAV`) | Fresh replay suffix after stem |
|---|---|---|
| Land | `land-war-20261017-083008-11228` | `-replay-20261017-101820-85339` |
| Aboard | `aboard-war-20261017-084100-17426` | `-replay-20261017-101914-87061` |
| Fleet | `fleet-war-20261017-084059-17272` | `-replay-20261017-101915-87214` |

Each fresh suffix has `-loaded.SAV`, `-auto.SAV`, `-post.SAV`. Loaded turn is 734. Loaded relevant decoded fields equal the staged input; the fresh loaded and post **whole save bytes** equal their respective retained loaded and post bytes in all three cases. The source listing SHA-256 is `2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8`; pinned EXE `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`; DAT `94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd`. Full numbered function extracts are in `source-audit-initial.txt`; original instruction bytes in `recruitment-disassembly-20261017.txt`.

## Exact debit ledger

The loaded Roman treasury is 1,000, wealth 1,767,000, mobilization 24. All 40 logical recruitment slots are empty (troop words zero; stale type/state/city bytes remain). New queues are state 0, city 85. These are queued recruits, not new live troops. Source `FUN_004504f4`, listing lines 53817–53821, deducts `trunc(troops / 200) * initial_price`. The write instruction at **0045070e** is `29 86 38 04 00 00`, `sub dword ptr [esi+0x438], eax`. Every treasury write in each successful control is at that site with call frames `recruitment → budget_recruit` and nation 0.

| Queue slot | Type | Troops | DAT initial price | Debit | Treasury after debit | Cases |
|---|---|---:|---:|---:|---:|---|
| 0 | LI | 12,800 | 2 | 128 | 872 | All three |
| 1 | LI | 9,200 | 2 | 92 | 780 | All three |
| 2 | HC | 2,200 | 30 | 330 | 450 | All three |
| 3 | HI | 4,700 | 20 | 460 | -10 | All three |
| 4 | LC | 5,800 | 15 | 435 | -445 | Fleet only |

The HI debit uses **23**, not 23.5, lots of 200. Initial price is the WORD at DAT offset `0x1f2f0 + type_index*40 + 0x22`, mapped to `0x478fd2 + type_index*40`; type indices LI=0, HI=1, LC=3, HC=4. The queue totals exactly equal `1000 - post_treasury`: land/aboard 1,010 and fleet 1,445. Residuals are **0, 0, 0**.

## Why four versus five queues, and why treasury crosses zero

**[derived, corroborated by original x86]** Recruitment `FUN_0044ffbc` adds 15,000 target power per war relation (listing 53487–53488). These controls have one war, no allied contribution and no active enemy armies. The land/aboard subject's LI 30,000 at morale 90 contributes `trunc((20*30000/100)/80)*90 = 6750` through `FUN_0044a8cc` (49199–49216). Embarkation is not a filter in this army loop. Thus land and aboard request 8,250; fleet has no own army and requests 15,000. Both targets are observed as EAX at entry to original `004504f4`.

The new queues contribute power 2,560, 1,840, 2,640, 4,700, then 3,480 (`trunc(troops/100)*type_power`, listing 53813–53816). Cumulative power reaches 11,740 at the fourth queue, satisfying 8,250; fleet needs the fifth to reach 15,220. The first four random queue outcomes match across cases using the fresh captured input.

The queue guard (53805–53810) requires an empty troop word, accumulated power below target, mobilization below 100, and `(treasury > trunc(wealth/-500) OR created_count < 3)`, with at most eight new queues and 40 scanned slots. Here the treasury threshold is -3,534. The guard permits the fourth/fifth queues even with low treasury; it does not check affordability of the next queue. Mobilization increments by `trunc(troops*1000/wealth)+1`, capped at 100 (53822–53829): 24→32→38→40→43, and fleet→47. These source rules explain the observed queue count and negative treasury without charging a support purchase.

## Phase comparison and related state

The following table is an **original-x86 control**, not a Wine phase trace. `phases.py` executes original instructions without patches/stubs and records phase entry/return state and every treasury write.

| Original function / phase | Land and aboard treasury | Fleet treasury |
|---|---|---|
| `0044fb7c` diplomacy | 1000→1000 | 1000→1000 |
| `0044ffbc` recruitment | 1000→-10 | 1000→-445 |
| `0044f31c` army support | -10→-10 | -445→-445 |
| `0044f608` fleet support | -10→-10 | -445→-445 |

All 334 city records remain unchanged from loaded to post. Live army/fleet records, including purses, supply and condition, remain unchanged; fleet slot compaction changes indices but not live record bytes. The x86 controls reproduce Wine's queues, treasury, mobilization, all city bytes and all live unit record bytes. No other nation's treasury is written.

Full nation-byte equivalence is explicitly **false** in the controls: the only differing byte is next-human Bithynia record offset `0x482`, x86 196 versus Wine 192, the low byte of a saved Information-form UI size WORD 708→704. `TInformation_InitializeForm @0043b014`, listing 40327–40331 (`ui-size-source-20261017.txt`), rounds that word down to a multiple of 16. That human UI call is outside the emulated AI phase calls. The raw mismatch is retained, not normalized. No full-world/map byte equivalence is asserted for the x86 controls.

## Method and limits

The first x86 control supplied the seed-file value 12345 and completed but failed endpoint comparisons. It remains as `phases-control-seed12345-20261017.json`, not a recovered legacy seed. A prior raw ledger guard also failed on stale empty-slot bytes; its source and failure log remain. No measurements were replaced.

Only the three hostile cases were replayed under Wine 10.0/Xvfb, using the already staged inputs and original EXE. Fresh read-only memory snapshots taken immediately **before the End-turn click**, after the same hover/reset as the prior runner, record RandSeed **4169717509**, original unit stats, regions and coasts. This is a new observation, not a missing legacy seed backfill or a phase-entry snapshot. The x86 controls load retained SAV records using the pinned original loader layout, advance the current seat from the loaded human nation 13 to the known intervening Roman AI nation 0, apply those fresh runtime inputs and invoke the four original phases in source order. UI/caller work and the next human turn are outside that control. Its precise endpoint agreement and explicit UI exception support this bounded attribution.

No support matrix rerun, native Windows observation, natural game proof, build/fixture/T177 change or new foreign-supply rule is included. The original31 three whole-seat confounds stay in that historical matrix; this companion finding supplies their recruitment attribution. Research #33 is addressed by the independently verified canonical promotion. Complete corrected battles for task #25 remain unverified and untouched.
