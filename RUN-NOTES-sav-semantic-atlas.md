# Whole-file SAV semantic atlas — running notes

Owner explicitly requested a broad original-SAV identification issue and a
findings record. Main session implements; standing GLM5.3Flash reviewer.
Isolated worktree /tmp/ic2-sav-semantic-atlas-20261021, branch
research/original-sav-semantic-atlas from7fe20bedba0b9cdbb012b1b348c96507f6a65768.

Plan: inspect existing99/research37/47 and current semantic/layout reports;
create one whole-file umbrella without restarting settled work; record the
block skeleton, alias corrections, unresolved register, dictionary schema and
honest completion contract; check references/whitespace; publish for GLM review.

Created conquest issue107 with entire file scope and acceptance criteria.
Existing research47 remains the whole-program UNKNOWN/residue workstream.
Prepared findings/2026-10-21-original-sav-semantic-atlas.md as a living index;
scope/consolidation, not a newly solved field dictionary or exporter claim.
No new tests/measurement/control required for this prose-only organizational
change; no game, private-copy, ACL, fixture, source dump or sibling-repo write.

Review coordination: research main reserved next GLM slot for its PR48 native
evidence intake. No atlas reviewer launched; use the same selected GLM Flash
after that slot is released. No fallback/model change or automatic child task.

## END — scope authoring delivered, review pending

Issue107 created and linked to draftPR108. Findings/notes committed8c27007
and pushed; all introduced local links and staged whitespace checks passed.
Independent GLM review/normal merge remain pending the researchPR48 review slot,
not a missing user model choice. No reviewer was started or substituted.
The atlas is a research scope/evidence baseline, not completed identification.
Issue107 stays open for actual field-by-field work; no other ticket closed.

Last reported/delivered main-source findings baseline remains conquest
7fe20bedba0b9cdbb012b1b348c96507f6a65768. New atlas finding is on this pushed
branch only, delivered to ic2-research with exact8c27007 source pin; it is not
claimed reviewed, merged or canonically promoted. This notes-only handoff
commit is published next and updates the PR head without changing the finding.

## 2026-10-21 cloud continuation (Claude Code cloud session, session-led workflow)

Migration: restored `gdrive:IC2/conquest/cloud-migration-20261021` with the
env-var rclone remote (shared rclone client id; the token is in the
environment's secrets, never printed). The container's `IC2_DRIVE_REMOTE`
pointed at `gdrive:IC2/artifacts` (only a test file), so the documented path
was used instead. The archive's SHA-256 equals the documented `2bea418b…3008e`
and SHA256SUMS passes 128/128. The EXE/DAT/all_app_functions hashes equal the
pins of the finding. The bundle sits outside git at `~/ic2-inputs`. Research
was cloned read-only at `16f019397e65` (the PR48 merge).

Branch: designated cloud branch `claude/sharp-meitner-293aq1` = main `80eaf3e`
plus a merge of PR108's branch `97ba1d8`. Old PR108 review-slot note
superseded: under the 2026-10-21 policy review is optional, and none was run.

Increment 1 (issue107 work-sequence steps 1-2): ledger
`runs/experiments/data/run-exp-sav-atlas107/field-map-v1.csv` (113 rows,
14 record types), checker `scripts/sav_atlas_coverage.py`, offline test
`tests/test_sav_atlas_coverage.py`. Receipts: corpus-public-v1.json (14/14
framed), corpus-private-bundle-v1.json (42/42 framed, 16 with battle block),
UNKNOWN31 zero in all 56 files (sample only). Findings and parser-notes
pointer updated. No game run and no SAV written; private bytes stay out of git.

Next: fill the reader/writer/lifecycle columns per row, starting with the
PARTIAL rows (fleet +4/+6, trailer client size, battle side) and the
non-serialized 0x4A0328/0x4A032A. UNKNOWN31 stays with research #47. Relay
the finding to research only once it is on main.

Findings baseline: last delivered/reported main-source baseline
`7fe20bedba0b9cdbb012b1b348c96507f6a65768`. This branch changes only
`findings/2026-10-21-original-sav-semantic-atlas.md` (not on main yet).

## 2026-10-21 increment 2: static reader/writer index

The owner asked to watch PR108 (subscribed) and to continue with the
reader/writer columns. Resolver `scripts/sav_atlas_access.py` and test
`tests/test_sav_atlas_access.py` (16 cases). The scratch iterations it1-it4
(outside git, not cited) found and fixed two faults: writes to plain globals
were missed, and below-base labels were ambiguous (`0x4A031C`, fleet `F-1`).
The recorded run is `access-*-v1` (source `2018c205…`). Its controls
44A004/44A050/437DE4 match the reports exactly. Results: 2,632 hits, 82/111
fields with a literal writer, UNKNOWN31 with no literal access, the fleet route
dword written by FUN_0044CD08 param_4, and 0x4A0328/032A = the selected army and fleet.

Next: work through the 29 no-literal-writer fields via the escape and pointer
frontiers (names, slot copies, DAT/NewGame), then a ledger v2 with
reader/writer columns joined from the access index.

## 2026-10-21 increment 3 (Claude Code cloud session, session-led workflow)

Start state: PR108 was already merged by the owner (merge `a5051a3`, 22:02);
no review comments; issue #107 open. This session did not subscribe to PR108
(the previous session's watch stays with it). Working branch
`claude/eager-sagan-po9v87` from main `a5051a3`. Private bundle restored from
`gdrive:IC2/conquest/cloud-migration-20261021` (the container's
`IC2_DRIVE_REMOTE` again pointed elsewhere); archive SHA-256 OK, SHA256SUMS
128/128. Research cloned read-only at `22ec86e`.

Verified count: access-index-v1 has 111 leaf rows, 29 with no literal writer.

Findings:
- The decompilation lacks 7 called functions and 3 methods. Among them are the
  DAT loader 0x4481A0, the SAV loader 0x4487C4, the NewGame initialiser
  0x448AA4 and split fleet 0x447C04, which is where most of the 29 writers were.
- New `scripts/sav_atlas_asm.py` (capstone machine-code index; test 9/9).
  Scratch iterations it1-it6 were outside git and are not cited. They fixed:
  - false function starts from raw E8 bytes;
  - desync on inline strings (now disassembled per function);
  - a `jmp` dropping facts;
  - ebp used as a general register;
  - the record -1 label rule;
  - push/pop;
  - library-region decodes.
  Recorded runs: asm v1, and asm v2 (multi-field scalar blocks). Control:
  250/252 v1 writer pairs reproduced; the other 2 are v1 false positives.
- New `scripts/sav_atlas_init.py` (test 8/8). The DAT layout is verified
  against the instruction bytes and the reads sum to the DAT size. NewGame
  constants are extracted. The provenance checks hold in all 56 saves.
- The ledger `field-map-v2.csv` is now authoritative: 0 UNKNOWN, 3 INERT
  (with a stated proof scope), 1 PARTIAL (BATTLE.side). The trailer client
  size and fleet route are resolved. The coverage checker accepts INERT and
  defaults to v2. Corpus v2 receipts: 56/56 framed.

Validation: tests coverage, access, asm and init pass; `git diff --check`.
No game run, no SAV written, no private bytes or source text in git.

Next: BATTLE.side, joining the readers into the ledger, and per-writer
formulas for the CONTEXTUAL rows. The INERT confirmation goes to research #47
(relay). Any native control needs the owner's authorisation.

Increment 3, continued: BATTLE.side resolved statically. The writers are the
copy-in (new battles only), FUN_00439C20 (half-round end) and the loader; the
resume only reads it, so the 2026-10-04 "memory 0, file 1" can only follow a
completed half-round. Ledger v3 (v2 + readers column + BATTLE.side): 0 PARTIAL,
0 UNKNOWN. The coverage checker defaults to v3; corpus v3 receipts 56/56.

PR #110 merged at main `c5cf759` (validation: 4 atlas tests, 3 repo tests,
diff check, links; GitGuardian green; no separate review). Relay: the atlas
finding was delivered with send_message (status "delivered") to the cloud
session "IC2 Research" (`session_01FEmvQUyuHYp4iXbTmBeY85`) at main
`c5cf759`. A cloud session cannot reply by message; read its transcript.
**Last delivered findings baseline: `c5cf75906c151bbccda32e90bdca95f142dec8a5`**
(the previous one was 7fe20bed…). Follow-up: the runtime global 0x4A031C is
identified (the info-panel line index).

## END: increment 3 delivered

Branch `claude/eager-sagan-po9v87`. Ledger v3 is authoritative: 0 UNKNOWN,
0 PARTIAL. Open:
- domains and invariants for the CONTEXTUAL rows (static);
- the INERT claim and the route timing, which can be confirmed natively or
  under an emulator only with the owner's authorisation;
- research #47 to confirm INERT.

## 2026-10-21 increment 4: native run run-exp-sav-inert107 (owner-approved)

The owner approved it in the session; the proposal is on #107.
`setup/setup.sh` ran in the container (apt Wine). The fixtures were cloned
public at `d3cfa91`, and the seed build hash matches. T1, T2 and T3 each ran
once, with no retries:
- T1/T3: INERT is carried, unread and kept across File > New.
- T2: the route_x reset and route_y retention are confirmed.

There was no release token, so the 12 saves went to
`gdrive:IC2/artifacts/run-exp-sav-inert107/` (12 matching) plus the local
`artifacts/`. Ledger v4 is authoritative and the checker defaults to it.
Next: relay to IC2 Research and ask it to consolidate (owner request).

The PR #112 merge is at main `29cc3a8`. A consolidation request, as the owner
asked, was delivered to the cloud session "IC2 Research"
(`session_01FEmvQUyuHYp4iXbTmBeY85`; status "delivered").
**Last delivered findings baseline: `29cc3a8770caf394bde2967c5c0a3cfd746d315a`.**

## END: increment 4 delivered

Ledger v4 is authoritative. Open:
- domains and invariants for the CONTEXTUAL rows;
- native observation of AI-set waypoints;
- research #47 to review INERT;
- an optional release of the run's saves (no token here; they are on Drive).

## 2026-10-21 increment 5: research #47 residue items (static)

- New-record residue: the army keeps 560 unwritten bytes, but no reader can
  see them (guards and troops = 0). The fleet's leftover `moves` survive
  launch until the next tick; that is a candidate effect.
- Deleted slots and text tails are never read.
- History: wealth0/treasury0/cities0/conqueror are presentation only;
  allegiance drives gameplay and needs a historical profile.
- Ledger v5 is authoritative; tests pass. One correction found while checking
  the draft: FUN_0044B27C scales the siege defence, not losses.

PR #115 merged at main `ad0af2d`. Increment 5 relayed to "IC2 Research" (status "delivered").
**Last delivered findings baseline: `ad0af2d8f4afd8485ae48368146febf23548e4b9`.**

## 2026-10-22 increment 6: run-exp-sav-fleetmoves107 (owner-approved)

- T4: the natural path confirms the compaction copy and the order's
  leftovers (x,y (101,47) in a fleet under construction).
- T5: launch keeps the leftover moves (17 against 0).
- 7 saves on Drive (no release token). Ledger v6 is authoritative; tests pass.

PR #117 merged at main `22b450d`. Increment 6 relayed to "IC2 Research" (status "delivered"), with a proposal to close research #47.
**Last delivered findings baseline: `22b450d0d52de146fc7b1f623565fdcd65c66769`.**

## 2026-10-22 increment 7: invariants and domains (static, corpus)

- `scripts/sav_atlas_invariants.py` (test 6/6) checks 20 code-derived
  invariants.
- City lists are ordered by name.
- 17 of 362 army marker bands are stale in natural saves.
- Eliminated nations keep a stale `cities` count.
- The aboard links and the battle grid can't be tested on this corpus.
- Ledger v7 is authoritative.

PR #120 merged at main `b4f17a4`. Increment 7 relayed to "IC2 Research" (status "delivered").
**Last delivered findings baseline: `b4f17a422448e64360bf3d0b4196b407edb73da6`.**

## 2026-10-22 increment 8: rebellion rule (static)

FUN_0044C204, FUN_0044C360 and FUN_0044B8D0 are read: capitals never rebel,
and the revival threshold is more than 7 cities with loyalty < 40. Ledger v8
is authoritative.

PR #121 merged at main `e8c8e5d`. Increment 8 relayed to "IC2 Research" (status "delivered").
**Last delivered findings baseline: `e8c8e5d35ddd15ea51a6f71f693a52e70f58ad06`.**

## END: increments 7-8 delivered

Ledger v8 is authoritative. Open:
- the aboard links and the battle-grid count (no natural cases in the corpus; a game run is needed);
- native observation of a rebellion or revival;
- independent review of increments 3-8.

## 2026-10-22 increment 9: aboard and battle grid (owner-approved run + releases)

The battle grid holds on research natural saves (6/6, 15/15). Natural embark run-exp-sav-aboard107: links hold in 2/2. Saves on Drive. Ledger v9 is authoritative. A separate same-model review of increments 3-8 is running.

## 2026-10-22 increment 10: review corrections

A separate same-model review of increments 3-8 ran; the report is kept in the
session scratchpad, and its findings are in the finding's increment 10.
Upheld: INERT, DAT layout, route/moves, battle side, residue, city-list order,
markers, rebellion constants.

Fixed:
- B1: the empty fort invariant; a negative test then showed it also read the
  population word.
- B2: the revival relations.
- I1: the army-cell check.
- I2: the neighbours writer artefact (documented in sav_atlas_asm.py).
- I3: route residue.
- M1-M7.

Receipts invariants-*-v2 are recorded (v1 kept). Ledger v10 is authoritative.
The invariants test has 11 cases.

PRs #123/#124 merged at main `de952d1`. Increments 9-10 relayed to "IC2 Research" (status "delivered").
**Last delivered findings baseline: `de952d113d75b3ccacbeb51b47b404777e3f76a2`.**

## END: increments 9-10 delivered

Ledger v10 is authoritative. Open:
- a native rebellion/revival observation;
- independent (other-family) review if wanted;
- an optional release of run-exp-sav-aboard107 (2 saves on Drive).
