# Battle outcome after SAV exchange — conquest #154 / remake #1355

2026-10-23: owner supplied exact native JSON, exported SAV and template paths in
`C:\Users\diego\Documents\imp_conq_original`, and instructed End turn then
Ptolemaic attack on Seleucid with Computer general in both games. Authorization
recorded at https://github.com/diegoami/ic2-conquest/issues/154 . This remains
separate from completed broad strategic conversion #153 and the paused battle
research queue. No source change in another repo or rebalancing authorized.

All three original input files copied unchanged into
`artifacts/run-exp-battle1355/private-v1/inputs/`; private SHA256/source manifest
beside them outside Git. Never upload owner saves, full traces or private
hashes to public Git/Drive/release. All outputs use exclusive new names; never
delete/overwrite a measured save. Track code and aggregate/public-safe evidence
here; keep complete private evidence/hashes in ignored private artifacts.

Input is actual format4, calendar Summer week11,269BC, native turnIndex5, human
Ptolemaic. Likely pair is native army-11(Ptolemaic,213,93,73564troops) and
army-4(Seleucid,219,93,78857troops); confirm after End turn before attacking.
Windows checkout current head ae614899d63ac721ee46d1e3213191fe1f43a676, matching
the effective pinned production build used by broad153. Linux base a510c33 is
read-only; current two-file production overlay/assembly hashes are in that
packet. No runtime game input edited; owner existing SAV and fresh re-export
will be compared privately before considering a conversion cause.

Plan: baseline native-vs-SAV unit/quality/morale/position checks; End turn in
both real engines; compare actual battle-entry states and select unique pair;
record Computer general placement/orders/exchanges/losers/survivors. Determine
first input/decision/exchange divergence; do not dismiss the observed outcome
as RNG without evidence or assume equal numeric seeds mean equal draw streams.
Native/public tactical API exposes frames and exchange log; original tracing
uses read-only memory/screenshots in isolated Wine prefix, without touching an
active owner game. Read complete results/errors before retrying; preserve work
and commit safe progress each batch/at least every30min. No model delegate.

## Baseline/reproduction progress (2026-10-23)

Separate branch experiment/battle1355 from broad publication main83d52d2bad99ad8e3870f498cd7d939e0354f482. Broad #153 complete/mergedPR155/relayed; its report excludes Computer general parity. Private owner originals/manifest never uploaded.

Fresh current-engine export of owner actual format4 JSON with supplied AUTO0742 template is BYTE-IDENTICAL to supplied exported SAV. SourceEXE9d753... and DAT match installed original runtime. Native End succeeds: Autumn week1,269BC, turnIndex6; Ptolemaicarmy11(213,93)73564troops/morale63, Seleucidarmy4(212,94)78857/morale62. Native ComputerGeneral attack finishes Ptolemaic winner20946survivors out73564;1194frames. Complete native tactical events/draws and before/after snapshots private. Read-only reflection retains actual public tactical controller solely to capture its event log; no rule/RNG mutation.

Original unmodified preflight End succeeds atturn756, same troops/morale, defender(212,96), not native(212,94). Thus first observed strategic position difference before battle; not yet a causal attribution, original seeds clock-based and different algorithms. Original record indices attacker9/defender4 map to nativearmy11/army4. Original enemy-distance3 requires approach to free adjacent land; clicking nonadjacent enemy only selects its information. Reviewed flow-v1 no-progress retained, flow-v2 approaches(213,95) thenattacks, initialBattlecounter2 matchesnativecounter2. Tactical unit morale values differ atentry (random copy-in); every value retained privately, no attributionyet.

Original saved UI oversized: initial1280screen had no safe neutral root pixel; v2preflight andfullflows use2560x1440 without save edits, derive visible map dimensions. flow-v2battle poll captured102states/18s,counters2..6; generic harness8sprogress watchdog falsely stopped during busy half-round. This is driver timeout, not frozen game. Full result/trace/screenshot read before nextattempt. flow-v3uses CGonce, Endonce, thenobserves up to900s; avoids injecting repeated Endturn clicks during autoplay. Private entry checkpoint waits for inspected toolbar atx165/end114/y112. New tool session recorded in runtime; no measured output overwritten.

Relatedissues read fully:1107unexplained targeting/draw divergences,1324grid/rout/lookup/Walk discrepancies,1329strategiccaller evidence gaps. No productionfix or rebalance selected. Need actual original full result andmatched-entry controlledcomparison beforecause claim.

## Full result and matched control

Original full flow-v3 battle COMPLETED: Ptolemaic wins48969survivors from73564, Seleucid78857->0, counter21. Final result dialog visually read and agrees with last actual memory slot totals48969/0. Recorder then raised when asking battle_state after original cleared battleflag0; this is POST-RESULT collection error, not battle failure. It killed original infinally, so no postbattleSAV/reopen/writeback claim. Result dialog screenshot/finalpoll/fullprivate logs preserved. Future collector guards the clearedflag and can save; no original rerun needed solely tohide cleanup failure.

Actual native user-flow result20946survivors. Controlled native run from ORIGINAL live entry slots/grid/morale/counter2/side0 plus ORIGINAL measured RandSeed using existingDelphiBattleDraws:22090survivors/counter29. Thus changing only initialstate/RNG implementation does not remove gap. Control assumes general claims clear at placement (recorded limit); no production rules changed. Private actualobserver/events full.

Earliest completed-half divergence now bounded: at counter4 with both sides1and no casualties yet, Original vs matchedNative attacker positions differ for slots3,9,11,13,15,16. Example slot3original(11,2)vsnative(12,2), slot9(9,2)vs(7,2), slot13(8,1)vs(12,3). This follows first computer movementhalf3. Sourcepoll50ms notinstruction-atomic; do not claim exact first original instruction or culprit. Original firstcounter4 drawindex8vsnative7 (originalLCG), beforecounts reconverge9atcounter5. At firstcounter7sameRandSeed/drawindex36 alreadydifferent trooploss totals, causal lead notexactatomicproof. Originalcounter3slotstates observedduringmovement; usecompletedcounter4boundary, notrawearlypartial snapshots, for robustclaim.

Native controlv2withGeneralDecisionjournal should reproducev1exactly; then audit/public-safe scalar finding/issue154update/relay. Need no sourcefix orrebalance. Keep all private hashes/ownerfiles/tracesoutsideGit; publish onlyaggregates/opaqueartifactrefs. Read related1107/1324/1329; firstmovementdifference suggests investigateGeneralOrders/Targeting/Engage/PassTwo/PassThree andmovement caller behavior, not assumedattribution.

## END — bounded reproduction complete, no fix claimed

Public-safe auditv2passes original preservation/fresh-export equality/actual outcomes/matched-repeat equality/earliestcompletedphase. Auditv1wronglyincludednativecounter4transient side0setup; retainedfailure, correctedfilter counter4ANDside1. Controlled journal observation leavesfinalstateexactlyunchanged22090/counter29. Public aggregate contains noownerfilehashes/fulltraces. Finding drafted findings/2026-10-23-ptolemaic-seleucid-computer-general-gap1355.md.

Complete original outcome48969vsnative20946; same-entry/Delphi-state controlledNative22090. Completed firstmovementhalf divergesbeforecasualties for6attackerpositions atcounter4/side1. Strong bounded lead, notexactoriginalinstructionattribution or productionfix; controlclaims clearatplacement assumed, UI transition/draworder needsfurtheraudit. No moreoriginal game runneeded for thisreproduction. Future collector guardsclearedbattleflag so resultcanbeSaved; currentcompletedrun's resultdialog+terminalmemoryagreebut nofinalSAVclaimed.

Next: commit/pushpublic-safe evidence, post154link/aggregate, PR/checks/merge undercurrentpolicy, relayfinding toresearch. Reporteddeliveredmainbaseline83d52d2includesbroad153andnarrow151promotionmarker; new1355finding notyetmain. Keep ownerprivatefolder intact, hashmanifestonlyprivate. Existingowner/untrackedworkpreserved. Do not call1355resolved orstarta productionfix/rebalancingwithoutscopedauthorization. No otherrepo/sourcewrite or modeldelegate/reviewer.

## END publication receipt

Completed evidence contentd2ae04a26379168bcbe55adb45bd456d03ca6758, PR156. GitGuardian success scans2commits, no secrets; full focused branch whitespace/Pythoncompilation passed; nativebuilds passed; public-safe auditv2passed. Samecontentpin successfully delivered viaresearch sessionbridge with exactbounds and noprivatedata. Source reported/delivered branchbaseline nowd2ae04a; mainbaseline83d52d2untilmerge. FinalmainSHA/receipt tobe posted on154/156 andsenttoresearch. Reproductiontaskcomplete; upstream1355remainsopen, exactroutine/drawattribution andanyproductionfixunperformed. No moreliveexperimentsrunning.
