# Three bound-original tax candidates: original Windows observations

The three physical tax-only candidates completed the original-Windows **open → ordinary recruitment order → one End turn → new Save As → normal close → fresh reopen → new Save As** sequence. Each initial load/save is byte-identical to its candidate; each fresh-reopen save is byte-identical to the preceding post-turn save. These are three observed compatibility sequences for the bound-original tax subset. They do not establish general export readiness or conversion of the twelve native JSON states.

Evidence: [native packet README](../runs/experiments/data/run-exp-sav-export37-native/README.md), [read-only validation/hash manifest](../runs/experiments/data/run-exp-sav-export37-native/native-packet-validation-v2.json), [case1](../runs/experiments/data/run-exp-sav-export37-native/case1-completion-v1.json), [case2](../runs/experiments/data/run-exp-sav-export37-native/case2-completion-v1.json), [case3](../runs/experiments/data/run-exp-sav-export37-native/case3-completion-v1.json). Earlier status snapshots are immutable chronological records; their 0/3,1/3,2/3 and UNPERFORMED statuses are superseded here, not rewritten.

## Runtime and physical inputs

Owner coordinated availability and authorized autonomous original UI checks. Runtime was Windows NT10.0.26200.0 x64, original `C:\Users\diego\Documents\imp_conq_original\Imperial Conquest 2.exe`, SHA256 `9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31`; file/product versions were null. This runtime EXE is identified by hash; equivalence to the prior decompilation binary is not independently established by version metadata. No Wine, process-memory writes, patches or system installs were used.

Published physical candidates were produced by writer `8c31728bf4124cd87465568e4429d202ddaf2f8d` (main PR1202, separately reviewed). Original source and candidate bytes were read only, checked before/after, and remain unchanged. Full hashes and private stage filenames are in the manifest. Candidate basenames and initial states:

| Case | Physical candidate | Current nation / tax | Actual saved calendar | Armies/fleets | Candidate SHA256 |
|---|---|---|---|---|---|
|1|t184-tax-1-n0-0.SAV|Rome0 /0|270 Spring week1|14/2|5e85a985382dc56ae964889ed01d4fda56b0e2414ccaede5e18d03b3bd2a314c|
|2|t184-tax-thracia-n15-40.SAV|Thracia15 /40|270 Spring week1|14/2|2afa2d64170a63fefbf12c5678700a02024f01eb0f682a0cbc7efffa63b7288f|
|3|t184-tax-rome-n0-30.SAV|Rome0 /30|270 Winter week7|14/6|5d82f47aa77f2736afddeac8c23754305455afa7e524636b98d12b4c2a88669a|

Case2's source filename contains271, but the saved/runtime year is270; the observations use the actual value.

The original Open path buffer truncated the long published candidate path. This was retained as a transport failure, not a candidate-format rejection. Exclusive short private `N1I68B2.SAV`/`N2I68B2.SAV`/`N3I68B2.SAV` copies are byte-identical transport copies, not regenerated exports. All new SAV/PNG outputs remain private under `C:\Users\diego\Documents\ic2-tax-native\20261018T085043Z`; none are committed or uploaded. Private source directory is the published `rendered\v061-test-fixtures\saves`; candidate directory is `rendered\sav-export-candidates\bound-original-tax-only` under the owner's `imperial_conquest_2` checkout.

## Reference controls and complete serialized comparisons

Control1 was performed manually by the owner: original source tax10→0, before/after Save As. Its five changed bytes are tax offset111294 and area-map window left/top offsets111330..111333: `(2,72)→(1168,293)`. Viewport remained `(97,39)`. This is a real UI geometry difference; the control is not byte-identical to the production candidate. Source→baseline also moved the Information window. [Control1 comparison](../runs/experiments/data/run-exp-sav-export37-native/control1-comparison-v1.json) covers all serialized regions and separates these changes; it finds no extra gameplay-byte changes. The cause of window movement was not instrumented.

Controls2/3 used fresh original processes, byte-identical short source transport copies, new baseline saves, the real Tax trackbar keyboard events and OK, scalar readback, and new saves. Private dialog captures were inspected. Control2 tax9→40 changed only offset128874; control3 tax20→30 changed only offset111398. Their before saves exactly match their sources and after saves exactly match their corresponding production candidates. No geometry or other serialized changes occurred in those two controls. Normal quit left zero original processes after each control.

## Candidate observations

All three loaded with current nation and target tax as above, offer source=-1 and sampled army/fleet/cell selections=-1. Owned UnitMap/Information forms and Tax dialogs were captured privately; Tax dialogs showed current tax/income0/0,40/262,30/787 and were cancelled without changing tax. Complete initial save equality covers nation/city/army/fleet/recruitment/offer/calendar state; this is not a claim of manually opening every unit/city dialog or proving all queued runtime work absent.

Each ordinary order was an original Recruit action for3000 regular light infantry, verified by a newly occupied queue entry and the original save's treasury/mobilization changes:

| Case | City / queue slot | Treasury | Mobilization | End-turn result | Post-turn and fresh-reopen SHA256 |
|---|---|---|---|---|---|
|1|Rome85 /4|2200→2170|30→32|Spring270 week3; tax0|96ef516dda14b154928684ad9635e9bc254aa45d52a3d3b56a65181dd618684c|
|2|Byzantium192 /3|520→490|22→25|Spring270 week3; tax40|13a64beae3e90d60ad4179e24b0d51e178698347725e567af3096a2887df4498|
|3|Rome85 /1|-818→-848|59→61|Winter270 week9; tax30|3e867d29fc18a69e6e9a9d6569f3246c1dff16b2062687952b143d362e703d3d|

Case3's empty recruitment slot retained type24 with zero troops before the order; original UI replaced it with the new regular unit. The original allowed recruitment despite negative treasury; no balance was patched. The single End-turn command opened a supply warning, “An army of yours needs supplies.” Its actual dialog was captured/inspected and End turn confirmed once. This completed the pending turn; no second menu command was issued. Cases1/2 had no blocking event dialog observed. All returned to the same human nation with offer source=-1. No battle control was needed in these sequences.

Post-turn saves were normal-closed, opened by fresh guarded original processes, checked by read-only scalar sampling, and saved to distinct new paths. Each reopen/save matches its entire post-turn file, including news and trailing state. Case1 fresh-reopen Information PrintWindow captures were blank despite News refresh; runtime/file equality supplies that reopened-state evidence, not a visual news-text claim. Case3 post-turn Information capture visibly shows Winter week9. All processes were normally quit; final independent process count was zero.

## Reproducibility and limits

The task-owned bridge enumerates the actual visible `TPremierForm` and separately owned forms; `MainWindowHandle`'s zero-size TApplication dummy is insufficient. Original menu IDs, native file-dialog controls, trackbar keyboard input, recruitment buttons and confirmation buttons were used. ReadProcessMemory is read only and restricted to numeric control/state scalars; original save output supplies whole-state comparisons. Every save/capture/log destination is exclusive. Failed initial launches, long-path Open, bridge encoding/guard errors, and case3's Python missing-local continuation error remain retained. The latter occurred after fresh reopen/scalar sampling and before the new save; correction resumed that same process without repeating the order/turn.

`verify_native_packet.py` rechecks all source/candidate/EXE hashes, initial/load identities, order/turn file changes, post-turn/reopen identities, full strategic file framing, JSON readability, Python compilation and zero remaining game processes. It launches no game and creates no save. The recorded run passed3cases/334measurement JSON files/38private capture hashes. Committed whitespace is checked against current MAIN separately; no broad/native replay is needed for review.

Internal GUI callback instruction traces remain **UNVERIFIED**. Operational UI/scalar/serialized observations establish what happened for these inputs; they do not prove every callback target or absolute absence of queued work. UNKNOWN31 bytes remain UNKNOWN and preserved, with no padding/default/whole-program-unused conclusion. New-record creation, inactive/text residue semantics, arbitrary historical/profile lineage, other edits and twelve envelope-free native JSON conversions remain outside this result. The bound-original provenance/edit restrictions still apply. Research37/conquest99 are not automatically closed. Independent owner-selected Kimi review and any MAIN promotion remain subsequent steps handled by the parent.
