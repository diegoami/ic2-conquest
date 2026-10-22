# Original Windows tax-subset validation — prepared, not performed

Runtime coordination is **PENDING**. This is a reviewable manual procedure for the owner-coordinated original Windows session; no original process has been launched and no output directory/save has been created by this preparation. Current Windows gate: **0 completed / 3 required**. File preflight is not a completed native case.

Use the existing physical candidates from writer commit `8c31728bf4124cd87465568e4429d202ddaf2f8d` (draft/unmerged main PR1202, scoped Kimi approval reported in [research37 checkpoint](https://github.com/diegoami/imperial-conquest-2-research/issues/37#issuecomment-6247428351)). Research PR43 is already merged; no duplicate intake is needed. The [metadata preflight](candidate-files-preflight-v1.json) independently checks actual file hashes/lengths/differences and preserves every original. It does not establish original EXE equivalence, complete GUI composition, native acceptance or future RNG equivalence.

## Exact private inputs

Candidate directory:

`C:\Users\diego\projects\imperial_conquest_2\rendered\sav-export-candidates\bound-original-tax-only`

Source directory:

`C:\Users\diego\projects\imperial_conquest_2\rendered\v061-test-fixtures\saves`

| Case | Source reference | Physical candidate | Current nation | Initial candidate tax | Bytes / changed offset |
|---|---|---|---:|---:|---|
| 1 | `1.sav`, tax10 | `t184-tax-1-n0-0.SAV` | 0 | **0** | 131313 / 111294 |
| 2 | `1_thracia_271_spring_1.sav`, tax9 | `t184-tax-thracia-n15-40.SAV` | 15 | **40** | 131557 / 128874 |
| 3 | `1_rome_270_winter_7.sav`, tax20 | `t184-tax-rome-n0-30.SAV` | 0 | **30** | 132149 / 111398 |

Exact candidate SHA-256:

- Case1: `5e85a985382dc56ae964889ed01d4fda56b0e2414ccaede5e18d03b3bd2a314c`
- Case2: `2afa2d64170a63fefbf12c5678700a02024f01eb0f682a0cbc7efffa63b7288f`
- Case3: `5d82f47aa77f2736afddeac8c23754305455afa7e524636b98d12b4c2a88669a`

Source hashes are in the metadata preflight and `reference-availability-v1.json`. Private receipts beside the candidates are `delivery-manifest.json`, `candidates-manifest.json`, `candidates-oracle.json`, `main-independent-oracle.json` and `KIMI-REVIEW.md`. Preserve them and the runner/oracle files unchanged. The writer DLL hash/revision is provenance for the producer, **not** the original runtime EXE identity.

## Before the first original launch

1. Record the owner's coordinated time/session, approved original EXE path and working directory. Published original EXE path is `C:\Users\diego\Documents\imp_conq_original\Imperial Conquest 2.exe`; verify the actual launched path and hash/version before using it. Record Windows version/architecture, display resolution/scaling, original EXE SHA-256 and available file/product version. Do not infer equivalence to the seeded research EXE or writer DLL. Preserve the installation; no patch/install step belongs to this checklist.
2. Recheck all three source/candidate hashes against the preflight. A mismatch makes that case incomplete pending investigation; do not regenerate, repair or overwrite the file to force a pass.
3. Choose a new private output directory outside code repositories, candidate/source directories and the installation. Proposed destination: `C:\Users\diego\Documents\ic2-tax-native\<RUN_NONCE>\`. Replace `<RUN_NONCE>` with a fresh owner-selected timestamp/nonce. This directory is only proposed here; it has not been created.
4. Reserve a fresh four-character `<NNNN>` token for the filenames below. Check every proposed output path is absent before saving. If any exists, choose a new token; retain old/failed files. Names stay within8characters before `.SAV` for conservative original-dialog compatibility. Record the final concrete filenames in the private case log.
5. Start a **fresh original Windows process per control/candidate branch**. Do not load into an owner's active game. Record no queued automation/input, pending move, modal offer/dialog or unresolved event before beginning. Wait for the initial load to settle, then record unselected cell/army/fleet before any inspection click.
6. Capture the actual unit-map width/height and scroll getters, geometry of area/unit/information/main windows, selected-cell state and runtime army/fleet selectors. Relevant scalars: form `+21A`, globals `004A0328/004A032A`, scrollbar values, actual width/height. Use an owner-approved read-only observer if available; do not patch/write memory. If only visual observations are available, label them as such and retain unobservable scalars/callback internals as **UNVERIFIED**. A successful dialog alone is not a claim that every internal scalar was observed.

## Per-case output names

All names below are proposed, not created. Substitute the same fresh `<NNNN>` token, and record the actual private output directory.

| Case | Reference control: before / after tax dialog | Candidate: after load / after order / after End turn / after reopen |
|---|---|---|
| 1 | `C1B<NNNN>.SAV` / `C1T<NNNN>.SAV` | `N1L<NNNN>.SAV` / `N1O<NNNN>.SAV` / `N1E<NNNN>.SAV` / `N1R<NNNN>.SAV` |
| 2 | `C2B<NNNN>.SAV` / `C2T<NNNN>.SAV` | `N2L<NNNN>.SAV` / `N2O<NNNN>.SAV` / `N2E<NNNN>.SAV` / `N2R<NNNN>.SAV` |
| 3 | `C3B<NNNN>.SAV` / `C3T<NNNN>.SAV` | `N3L<NNNN>.SAV` / `N3O<NNNN>.SAV` / `N3E<NNNN>.SAV` / `N3R<NNNN>.SAV` |

## A. Reference control: complete original tax-command composition

Do this on the corresponding **source reference**, in a separate fresh process, preserving both source and candidate.

1. Load the source reference. Establish the fresh/unselected/stable conditions above. Record its expected current tax10/9/20, current nation/controller, calendar, offer state and geometry/getter values. Use **Save As** to the absent `CiB<NNNN>.SAV`; hash this new baseline copy. Record any load/save geometry normalization separately.
2. Open the original **Change tax** dialog. Set the case's candidate tax0/40/30 and press OK once. Observe the dialog closing, message/event processing settling, unit-map refresh, nation information/tax display and absence of unintended selection/movement/attack/modal action. Record before/after scroll/geometry and whether the identity clamp holds.
3. This is the runtime composition under investigation: tax setter `004540B8`, refresh `0045BA6C → 00445D38/0043BA7C`, posted close `0042313C`, then geometry capture `0045BB1C` and writer `004484D0`. Record the observation method: visual outcome, read-only scalar sampling or approved tracing. Do not claim instruction/callback execution traces from GUI appearance alone.
4. Save As the absent `CiT<NNNN>.SAV`, hash it and close the original process. Compare its decoded state with `CiB<NNNN>.SAV` and the intended candidate: expected tax change and stable game state; document UI-geometry differences explicitly. Any unexpected non-UI change is an unresolved finding, not silently permitted. Do not alter the candidate to match a control.

## B. Physical candidate: open, inspect, order AND End turn, save-copy and reopen

Use a fresh original process for each candidate, not the control process.

1. Recheck its exact candidate hash, load it directly, and establish/record fresh/unselected/stable state before inspection. Confirm the table's intended tax0/40/30 and current nation. Do not change its tax again to manufacture tax-dialog evidence; branch A provides that control separately.
2. Inspect and record these states against the source/candidate private oracle and expected tax-only delta: nation/controller/tax/treasury/history; city ownership/population; army ownership/location/units; fleet ownership/location/count/carried-army/building state; recruitment queues; pending offers; turn order/current seat and calendar. Record the unit/city/fleet indices or private references used. Inspection itself can change selection/UI preferences; record this instead of treating later geometry as byte identity. Save As the absent `NiL<NNNN>.SAV` and hash it.
3. Perform **one ordinary, verifiable order** available in that state, e.g. an owned army's legal adjacent move or regular recruitment. Record the selected object, intended action and observed effect. A cancelled dialog/no-op is not a completed order. Save As the absent `NiO<NNNN>.SAV` and hash it. Keep unexpected dialogs/failures and their private observations; do not overwrite an earlier stage.
4. Perform **End turn once**. Wait for the original to finish processing and reach the next controllable state; do not issue End turn again merely because processing is slow. Record any intervening offers/battles/events and the decisions made, calendar/controller progression and resulting state. Save As the absent `NiE<NNNN>.SAV`; hash it. Both the ordinary order and End turn must be recorded for this case.
5. Close the original process fully. Start a fresh process, reopen `NiE<NNNN>.SAV`, and verify the recorded post-order/post-turn nation/city/army/fleet/queue/offer/calendar state. Initial candidate tax is verified at step1; later values must be compared with the actual recorded turn effects rather than presumed unchanged. Save As the absent `NiR<NNNN>.SAV`, hash it and retain it alongside every earlier copy.
6. Hash the original source and physical candidate again; both must match their immutable input hashes. Hash and retain every control/candidate-stage save; record exact private paths, lengths, timestamps, runtime identity and observations. Keep private binaries/screenshots/traces off Git and releases; share only approved scalar/redacted observations and private artifact references.

## Case record and completion

Use one private record per case containing: input hashes; actual runtime EXE hash/version; concrete output paths/hashes; pre-load/fresh-selection and geometry/getter evidence; reference tax-dialog/refresh/posted-close/save observations and method; initial candidate inspections; ordinary-order effect; End-turn effect; new-copy save/reopen result; unchanged source/candidate hashes; anomalies and remaining UNVERIFIED items.

Current status for **all three cases is UNPERFORMED**. Do not replace it with PASS from physical-file preflight, the producer's reader/oracles or a Wine run. Report each observed step and unresolved runtime/provenance item separately; no full3/3 claim until all required original-Windows steps and composition obligations are satisfied. Runtime failures remain evidence and require a new distinct output on retry.

This gate concerns the **bound-original tax-only subset**. Even a successful three-case result does not satisfy the separate **twelve native-JSON conversion target**, general new-record/relocation mapping or full T184–T186 completion. Research37 remains open until its stated remaining obligations are resolved; do not infer future RNG equivalence.
