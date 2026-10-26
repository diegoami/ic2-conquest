# Carried-army disband218 — running notes

## 2026-10-26 authorization / plan

Owner selected recommended task1 (“ok do it”): establish original GUI reachability
for embarked-army disband. Conquest218 records authorization before launch.
Main802 closed residual question and Research86 sweep are existing routes; no
new remake correction presumed. Read shared CLAUDE/AGENTS, prior task notes,
promoted sweep and original exact callers. GitHub/main checked; no open conquest
PR. Synced main69d02e3; preserve eleven unrelated untracked files.

Startup findings comparison since reported/delivered433e3d0 is empty. This is
also the last trustworthy relay baseline; update only after actual new delivery.

Scope: original whole-army menu vs selection/repaint/modal-return paths; separately
Change units last-unit removal and Army transfer disband/cleanup; land positive
control, own-city/mercenary gates, confirmation/Cancel/OK/save/reopen, actual
landing if useful. No owner-game/Windows access, Endturn, battle/AI, remake code
or deliberate565/1340/no-wrap/T207/T216 policy change.

Source discoveries, not yet new runtime claims: wholeDisband004476AC reads only
form+220. Fleet marker selection004466CC clears+220; repaint00445D38 reselects
the cursor tile. Supply/Hire/Change temporarily resolve cargo into+220, but modal
returnUpdate00446EF4 callsPaint and clears it again. Global/temporary selection
and menu reachability are distinct. ChangeUnitsOK00445378 copies the army back
without an explicit empty-army delete, whereas ArmyToArmyOK00442EF8 explicitly
merges/deletes emptied armies via0044AB90 (clears valid carrier pointer). Thus
last-unit removal cannot be presumed to mean complete army deletion. Test these
separately. No whole-program absence proof from a grep.

Preservation: never delete/overwrite measured outputs/saves, including failures;
unique cd218 versions and per-phase progress. Public scalars/runners under
runs/experiments/{data/run-exp-carried-disband,carried-disband}; full original
states/screenshots/identities/hashes only ignored artifacts/run-exp-carried-
disband. Reuse stopped private work85 Wine context with unique filenames;
original byte identity verified privately. Fresh own Xvfb:760, no attach to
existing display. Record all runtime limits honestly. Commit/push per batch and
<=30min. No public release of original artifacts/private hashes.

Initial positive land control complete: cd218-pilot-v1_land-whole-yes_before.SAV
→_after.SAV,turn0734: owner−1,treasury1730→1767,Antium330→353,mobilization24
unchanged. Confirms whole-command menu navigation and actual refund handler.
Important source refinement: FleetButtonsOn00446188 shows the cargo army's
buttons, including Disband, at shifted positions; visibility does not resolve
form+220. Added separate actualtooltip-verified carried/landtoolbar controls.
Information resource has no click/doubleclick event/selection picker; keys
forward to main's bounded map/info shortcuts, DisbandmenuShortcut0. Source
sites26+syntacticstore candidates10 and117bounded resource callback/shortcut
rows retained; these are bounded interface audits, not indirect-store absence
proof. Missing ChangeUnits empty cleanup is a separate prediction to test.
