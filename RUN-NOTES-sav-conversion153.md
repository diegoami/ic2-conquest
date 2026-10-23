# Broad conversion matrix — issue #153

2026-10-23: owner explicitly requested a broad follow-up to #151, with starts
from several nations and feature-by-feature conversion tests in both directions.
Approval recorded in https://github.com/diegoami/ic2-conquest/issues/153 .
Branch `experiment/sav-conversion-broad`, base `4ca3afa04c3eb8454c63ed6a4984f5564e8e0496`.
No additional findings on origin/main at start. Preserve all existing owner files.

Plan: all16 human-nation starts (two startup seeds across the sweep); progressed
states for four contrasting nations; targeted state/action cases for strategic
army/naval/economy/recruitment/diplomacy/city/combat-aftereffect features; hotseat,
pending offer, elimination, text and numerical limits; actual unsupported-state
refusals/migration tests where valid. Report distinct coverage levels: preserved
state, original action, remake action after return, refused, blocked, untested.
This is conversion testing, not resumption of the paused battle research queue.

Reuse pinned, read-only remake assemblies and build only task-owned adapters
into ignored artifact folders. Use isolated original Wine prefix/display. Check
findings for each mechanic and driver workarounds before creating experiments.
No source change in another repo; defects get evidence and an upstream issue.

Never delete/overwrite a save or measurement, including failed attempts. Every
save, script and attempt uses unique names. Text measurements go directly to
`runs/experiments/data/run-exp-sav-conversion-broad153/`; binary/native JSON
artifacts stay under `artifacts/run-exp-sav-conversion-broad153/` and Drive, with
SHA256 manifests. Commit/push each batch and at least every30min. Record complete
outcomes before adapting. No subagents/reviewers launched. Native Windows and
the owner's twelve-save manifest remain separate owner gates.

## First batch

Current remake main ae614899d63ac721ee46d1e3213191fe1f43a676 differs from read-only local a510c33 by PR1353 quality4 fix (2production files +2tests). Verified GitHub blob identities of2production files, built current CLI via compile-item substitutions without changing or cloning another repository. Build output/assembly pins retained in artifact folder and source-pin receipt. All16human starts (alternating seeds7/11) and4progressed states (Rome6/Carthage12/Ptolemaic18/Macedonia24) export, pass independent policy, import/reload/resume, and execute their selected prediction command. Original all16sweep currently running serially in private Wine/Xvfb: first4complete, movement verified, freshreopen byte-equal. Feature adapter initially lacked the tests-only ValueList.Replace extension; corrected task-owned helper, no save trial repeated. Port geometry checked against selected existing fixture; Antium at102,46, fleet101,46, adjacent sea100,46. Feature captions will be read via a task-owned LB_GETTEXT helper, not assumed row numbers.

## Mid-run diagnosis/checkpoint

All16nation starts and their returned remake continuations pass; normalized deterministic start actions agree. First feature wave found known original Split-unit R41 refusal for LI4800 (<6000); native accepts it. Keep v1 failure, add HI5000 positive case and rerun LI as explicit refusal, not a hidden replacement. F02 transfer donor/recipient move difference and F09 mercenary-name difference retained for assessment.

Driver-only failures: Supply army's old fixed OK coordinate misses actual button (screenshot confirms dialog still open); task-local control-based spinners/OK fix. Recruitment caption helper initially chose by X only and used ANSI; actual output was only L/R from UTF16 city strings. Min-top selection and SendMessageW/UTF8 decoding fixed it. control-diagnostic-v2.json proves full ROME and control-based supply close. Every original failed attempt/screenshot retained.

Checkpointed own runner PID1720119 after F20; SIGINT reached F21 during startup, before any save/order. Finally cleaned game/display and wrote incomplete F21 receipt. Original tool session65042 exit130. reviewed-recovery-plan-v1.json records all12reviewed causes; resume_live.py skips every completed case, uses v2 names for reviewed failures, and retains original-refusal controls. New runner session id recorded in session tools; source/measurements do not restart wholesale. No model/subagent launched.

One return-import batch was scheduled before adapter-v6 build finished; F00-F03 command-not-found receipts preserved. Corrected by asserting adapter exists and using versioned v2 return files; all four then passed. This was experiment orchestration, not a game/converter failure.

Matrix now75accepted source states (16starts,4progressed,54features,1synthetic legacy4) +11actual CLI/input refusal controls. Every source export/policy/import succeeds. Native prediction includes intended negative caps and alliance/war-peace refusals; positive diplomacy/split controls added separately. Artifact batch01 uploaded successfully to Drive folder1PwRAw0xg4WKp5MpgpcRO3Fg6B4H5dnmn; source measurements pushed e62dd13. Final field/state and feature outcome comparisons pending ongoing original cases.

## Second evidence batch

Reviewed UI diagnostic passed: Unicode city captions now full ROME; actual supply button/spinner coordinates derived from controls. Resume runner session37590 runs same private prefix, skips all completed cases, and appends unique v2 results. LI4800 refusal control now completes byte-stable roundtrip (known g2 behavioral difference remains); supply/money and first recruitment cases complete. Original recruit helper uses spinner INCREMENTS above per-type default, not an absolute troop request: observed LI4000 for +1000. Initial native1000 prediction is retained; compare additional matched predictions using observed original amount, without rerunning/hiding original game results. Same principle applies if original auto-selects a different build port from native explicit Neapolis.

Two non-conversion action differences observed so far: recipient of unit transfer at(101,37) has8moves in native prediction vs0original; freshly hired label1 is generic Mercenary(label1) in native vs Numidian original. Full comparisons preserve fields. Read-only searches found no open transfer-moves issue; do not change remake source. Research consolidation will receive these with final pins and existing/conjectured classification. Known conqueror1351 remains separate; all benchmarks use exact current converter pin ae614899.

All source/migration/refusal cases are prepared:75accepted cases and11refusal controls. Initial all16start game-field comparisons agree, all16 returned sessions resume and reexport. Synthetic format4 output differs from source7 at weather (v4 migration intentionally supplies empty rough-sea overlay); do not claim byte-identical migration or owner legacy validation. Latest live/per-case counts are in receipts; final pass/gap count is not yet known. New binary batch02 archived/uploaded to established Drive; all failures retained. No native Windows or other-repository write/agent dispatch.

## Later coverage and research acknowledgment

Original successful cases now cover fleet/cargo, hotseat, siege/capture, native field-battle aftermath and winter rough-fleet continuation; exact per-case receipts/SaveAs names are authoritative. All5recruitment types, quality4mobilization and disband/cap controls recovered with verified Unicode caption helper; first failures remain. Same-quantity recruitment and same-port build predictions agree after retaining initial differing-input predictions. Input case count is77, but serialized exported SAV hashes are53distinct (some identical source bytes deliberately receive different actions); never call77distinct worlds/saves.

F32 pending trade offer loaded unchanged and displayed correct Numidia notice; v1's autoaccept assumption was false. Actual original acceptance is International Relations trade after dismissing the notice (g4 pending-offer exemption research); add reviewed explicit action, not a converter fix. F46 foreign-supply dialog selected quantity but v1 omitted Buy supplies commit; controls show that distinct layout. Add explicit Buy supplies click before OK for reviewed retry, retain v1. resume_live.py recovery-plan-v3 records these cases for next pass after current runner completes; do not interfere with its live process.

Research peer reported narrow151 intake complete at research PR65/head558a76a87adf39eb5a46ba0e1d6e879f037da092, UNMERGED under owner's research merge hold. It reproduced comparison-v6/validation-v2 byte-for-byte,164archiveentries/tarmembers and13policychecks, adding708->704geometry explanation. It holds broad153 evidence separately and #63 separately. No action requested from conquest; do not request merging that held PR or claim broad intake complete.

Research update supersedes its earlier merge hold for narrow151: owner approved researchPR65 merge at412f1f9b3bc1293aa67792c98207a7b7eaf44b16; canonical report promoted. Source narrow151draft marked intaken with canonical link; measurement content unchanged. Broad153 still separate. Third immutable artifact batch archived/uploaded and checkpoint committed; ongoing live runner remains session37590. Final pass counts/remaining reviewed cases still pending.

## END — broad testing complete; publication

Final input matrix78cases:77exported roundtrips with53distinct source SAV hashes, plus F55city-overlap refused; eleven other CLI/input controls make12safe refusals total. Groups of successful roundtrips:16nation starts,4progressed,56feature cases,1synthetic legacy4. All77original action/refusal verifications, byte-stable fresh reopens, returned imports/resumes/tax19/reexports and policy checks pass. Comparison-final/coverage-final/validation-final authoritative. Final audit7groups/2754hashchecks across selected saves and4archives.68normalized deterministic comparisons:64match,4explicit mismatches (recipient moves,knownLI4800splitrefusal,mercenaryname,regular-name spacing).9random continuations do not claim equivalent outcomes. Known conqueror1351loss retained; no pure record-order permutation. All first failures retained; F55never launched original because its export was refused. F56separate valid sea-tile compaction passes.

Final bundle batch-final.tar.gz21030521bytes/900files/SHA35db99998eb18955469200eb3af755d0abc6cf980cc5f9dd38a13f43905688c1 uploaded to Drive folder1PwRAw0xg4WKp5MpgpcRO3Fg6B4H5dnmn, file16xF3L8qDSFcotMLhA5yOon2Rqm56gJXc; metadata readback confirms size/parent. Batch03first upload was premature after archive command yielded; detected11580004vs18246387bytes, markedINCOMPLETE-do-not-use, preserved, and separately uploaded completed bytes as1NqswRHJiHyEpqyRjHCmxt6b7P7DW7Ioi. Local completed archive and all member hashes valid; no remote-download hash check claimed. This orchestration failure did not lose any save/result. End notes source extra private1355files are outside broad bundle and never uploaded.

Owner supplied new #1355reproduction during publication. Separate conquest154/RUN-NOTES-battle1355.md and private artifacts track exact owner format4JSON/SAV/template and Computer general investigation. Broad finding explicitly excludes battle-outcome equivalence and links it; do not handwave as RNG. Owner files private hashes outsideGit. Broad work is done; no further broad game run needed. No other repo source changed; no delegate/reviewer launched. Next publication steps: final commit/PR/checks/merge, relay pinned broad findings to research, record final main SHA/receipt on153. Previous source reported/delivered main baseline4ca3afa remains until this new finding is published. Narrow151draft marked promoted at research412f1f9 per successful peer intake.
