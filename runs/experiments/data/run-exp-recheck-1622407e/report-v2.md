# Re-check against remake 1622407e (v0.8.5: Docs: define v0.8.5 checkpoint claims from the approved correction contracts (#1623))

Counts: CHANGED 2, FIXED 8, unchanged 129

| tier | test | v0.8.4 | now | label | finding |
|---|---|---|---|---|---|
| campaigns | allhuman-rulebot1-32 | first divergence turn 5 | first divergence turn 16 | **CHANGED** |  |
| orders | fleet-second-walk-87-47 | differs-immediate | differs-after-end-turn | **CHANGED** | 2026-10-30-paths-in-play-and-fleet-walks42.md |
| orders | fleet-second-walk-88-32 | differs-immediate | same | **FIXED** | 2026-10-30-paths-in-play-and-fleet-walks42.md |
| orders | move-far | refusal-difference | same | **FIXED** | 2026-10-29-v084-known-differences-and-command-gaps.md |
| orders | move-sea | refusal-difference | same | **FIXED** | 2026-10-29-v084-known-differences-and-command-gaps.md |
| orders | walk-carthage-army3 | differs-immediate | same | **FIXED** | 2026-10-29-walk-stops-at-own-city-on-line230.md |
| orders | walk-city-on-line | differs-immediate | same | **FIXED** | 2026-10-29-walk-stops-at-own-city-on-line230.md |
| orders | walk-city-on-line-near | differs-immediate | same | **FIXED** | 2026-10-29-walk-stops-at-own-city-on-line230.md |
| orders | walk-gaul-army9 | differs-immediate | same | **FIXED** | 2026-10-29-walk-stops-at-own-city-on-line230.md |
| orders | walk-line-clear | refusal-difference | same | **FIXED** |  |
| campaigns | armenia-rulebot1-5t | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | bithynia-rulebot1-5t | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | carthage-rulebot1-5t-r2 | first divergence turn 1 | first divergence turn 1 | **unchanged** | 2026-10-29-walk-stops-at-own-city-on-line230.md |
| campaigns | celtiberia-rulebot1-5t-r2 | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | dacia-rulebot1-5t | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | galatia-rulebot1-5t | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | gaul-rulebot1-5t-r2 | first divergence turn 1 | first divergence turn 1 | **unchanged** | 2026-10-29-walk-stops-at-own-city-on-line230.md |
| campaigns | greece-rulebot1-5t-r2 | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | illyria-rulebot1-5t | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | macedonia-rulebot1-5t-r2 | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | media-rulebot1-5t | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | numidia-rulebot1-5t-r2 | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | ptolemaic-rulebot1-5t-r2 | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | rome-rulebot1-5t | first divergence turn 1 | first divergence turn 1 | **unchanged** | 2026-10-29-walk-stops-at-own-city-on-line230.md |
| campaigns | seleucid-rulebot1-5t-r2 | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| campaigns | thracia-rulebot1-5t | first divergence turn 1 | first divergence turn 1 | **unchanged** |  |
| orders | buy-arretium-20 | same | same | **unchanged** |  |
| orders | buy-heraclea-50 | same | same | **unchanged** |  |
| orders | disband-army-0 | same | same | **unchanged** |  |
| orders | disband-slot-0 | same | same | **unchanged** |  |
| orders | disband-slot-3 | same | same | **unchanged** |  |
| orders | disband-unit | same | same | **unchanged** |  |
| orders | embark | same | same | **unchanged** | 2026-10-29-export-city-marker-variant-and-empty-offer230.md |
| orders | embark-20-ships | same | same | **unchanged** |  |
| orders | embark-21-ships | same | same | **unchanged** |  |
| orders | embark-22-ships | same | same | **unchanged** |  |
| orders | embark-sail | same | same | **unchanged** |  |
| orders | embark-turn-disembark | differs-after-end-turn | differs-after-end-turn | **unchanged** |  |
| orders | fleet-10 | differs-immediate | differs-immediate | **unchanged** | 2026-10-29-v084-known-differences-and-command-gaps.md |
| orders | fleet-25 | differs-immediate | differs-immediate | **unchanged** | 2026-10-29-v084-known-differences-and-command-gaps.md |
| orders | fleet-sail | differs-after-end-turn | differs-after-end-turn | **unchanged** | 2026-10-29-ai-fleet-hunt-absent-in-remake233.md |
| orders | fleet-two | differs-immediate | differs-immediate | **unchanged** | 2026-10-29-v084-known-differences-and-command-gaps.md |
| orders | fortify-arretium-25 | same | same | **unchanged** |  |
| orders | fortify-caere-50 | same | same | **unchanged** |  |
| orders | fortify-full | same | same | **unchanged** |  |
| orders | fortify-in-progress | same | same | **unchanged** |  |
| orders | fortify-pisae-10 | same | same | **unchanged** |  |
| orders | fortify-rome-5 | same | same | **unchanged** |  |
| orders | hire-merc-25 | same | same | **unchanged** |  |
| orders | join-100k-exact | same | same | **unchanged** |  |
| orders | join-100k-over | same | same | **unchanged** |  |
| orders | join-20-ok | same | same | **unchanged** |  |
| orders | join-21-refused | same | same | **unchanged** |  |
| orders | join-fleets | same | same | **unchanged** |  |
| orders | join-fleets-100 | same | same | **unchanged** |  |
| orders | join-fleets-101 | differs-after-end-turn | differs-after-end-turn | **unchanged** |  |
| orders | join-purse-1600 | same | same | **unchanged** |  |
| orders | join-purse-2000 | same | same | **unchanged** |  |
| orders | join-units-hi | same | same | **unchanged** |  |
| orders | merc-20-units | same | same | **unchanged** |  |
| orders | merc-low-supplies | same | same | **unchanged** |  |
| orders | mobilize-base-3 | same | same | **unchanged** |  |
| orders | mobilize-port-0 | same | same | **unchanged** |  |
| orders | move-far-land | same | same | **unchanged** |  |
| orders | move-forest | same | same | **unchanged** |  |
| orders | move-mountain | same | same | **unchanged** |  |
| orders | move-own-city | same | same | **unchanged** |  |
| orders | move-plain-1 | same | same | **unchanged** |  |
| orders | move-river | same | same | **unchanged** |  |
| orders | move-twice | same | same | **unchanged** |  |
| orders | recruit-ar-max | same | same | **unchanged** |  |
| orders | recruit-ar-min | same | same | **unchanged** |  |
| orders | recruit-hc-max | same | same | **unchanged** |  |
| orders | recruit-hc-min | same | same | **unchanged** |  |
| orders | recruit-hi-max | same | same | **unchanged** |  |
| orders | recruit-hi-min | same | same | **unchanged** |  |
| orders | recruit-lc-max | same | same | **unchanged** |  |
| orders | recruit-lc-min | same | same | **unchanged** |  |
| orders | recruit-li-max | same | same | **unchanged** |  |
| orders | recruit-li-min | same | same | **unchanged** |  |
| orders | recruit-luceria | same | same | **unchanged** |  |
| orders | recruit-mob-100 | same | same | **unchanged** |  |
| orders | recruit-no-money | same | same | **unchanged** |  |
| orders | recruit-slot-40 | same | same | **unchanged** |  |
| orders | recruit-slot-41 | same | same | **unchanged** |  |
| orders | recruit-then-disband | same | same | **unchanged** |  |
| orders | recruit-two | same | same | **unchanged** |  |
| orders | rel-ally-carthage | same | same | **unchanged** |  |
| orders | rel-ally-illyria | same | same | **unchanged** |  |
| orders | rel-peace-gaul | same | same | **unchanged** |  |
| orders | rel-trade-bithynia | same | same | **unchanged** |  |
| orders | rel-trade-carthage | same | same | **unchanged** |  |
| orders | rel-war-bithynia | differs-immediate | differs-immediate | **unchanged** | 2026-10-29-war-declaration-ally-cooldown-diff230.md |
| orders | rel-war-carthage | differs-immediate | differs-immediate | **unchanged** | 2026-10-29-war-declaration-ally-cooldown-diff230.md |
| orders | rel-war-dacia | differs-immediate | differs-immediate | **unchanged** | 2026-10-29-war-declaration-ally-cooldown-diff230.md |
| orders | rel-war-illyria | same | same | **unchanged** |  |
| orders | rel-war-macedonia | same | same | **unchanged** |  |
| orders | rel-war-numidia | same | same | **unchanged** | 2026-10-29-war-declaration-ally-cooldown-diff230.md |
| orders | rel-war-thracia | same | same | **unchanged** | 2026-10-29-war-declaration-ally-cooldown-diff230.md |
| orders | repair-3 | differs-after-end-turn | differs-after-end-turn | **unchanged** |  |
| orders | scuttle | same | same | **unchanged** |  |
| orders | split-army-1unit | same | same | **unchanged** |  |
| orders | split-army-2units | same | same | **unchanged** |  |
| orders | split-at-197 | same | same | **unchanged** |  |
| orders | split-at-198 | same | same | **unchanged** |  |
| orders | split-fleet-10 | differs-after-end-turn | differs-after-end-turn | **unchanged** |  |
| orders | split-fleet-19 | same | same | **unchanged** |  |
| orders | split-one-unit | same | same | **unchanged** |  |
| orders | split-then-join | same | same | **unchanged** |  |
| orders | split-transfer-unit | same | same | **unchanged** |  |
| orders | tax-0 | same | same | **unchanged** |  |
| orders | tax-25 | same | same | **unchanged** |  |
| orders | tax-40 | same | same | **unchanged** |  |
| orders | tax-then-recruit | same | same | **unchanged** |  |
| orders | transfer-into-20 | same | same | **unchanged** |  |
| orders | transfer-ships-5 | differs-after-end-turn | differs-after-end-turn | **unchanged** |  |
| orders | walk-line-clear-land | same | same | **unchanged** |  |
| stats | naval30:attacker_ships_lost | consistent | consistent | **unchanged** |  |
| stats | naval30:attacker_survives | consistent | consistent | **unchanged** |  |
| stats | naval30:defender_condition | consistent | consistent | **unchanged** |  |
| stats | naval30:defender_ships_lost | consistent | consistent | **unchanged** |  |
| stats | naval30:defender_survives | consistent | consistent | **unchanged** |  |
| stats | siege10:army_troops_lost | consistent | consistent | **unchanged** |  |
| stats | siege10:captured | consistent | consistent | **unchanged** |  |
| stats | siege10:fort_change | consistent | consistent | **unchanged** |  |
| stats | siege10:loyalty_change | consistent | consistent | **unchanged** |  |
| stats | siege10:pop_change | consistent | consistent | **unchanged** |  |
| stats | storm30:at_target | differs | differs | **unchanged** | 2026-10-29-ai-fleet-hunt-absent-in-remake233.md |
| stats | storm30:fleet_survives | differs | differs | **unchanged** | 2026-10-29-ai-fleet-hunt-absent-in-remake233.md |
| stats | storm30:ships_lost | differs | differs | **unchanged** | 2026-10-29-ai-fleet-hunt-absent-in-remake233.md |
| stats | storm30b:at_target | consistent | consistent | **unchanged** | 2026-10-29-ai-fleet-hunt-absent-in-remake233.md |
| stats | storm30b:condition_lost | consistent | consistent | **unchanged** | 2026-10-29-ai-fleet-hunt-absent-in-remake233.md |
| stats | storm30b:fleet_survives | consistent | consistent | **unchanged** | 2026-10-29-ai-fleet-hunt-absent-in-remake233.md |
| stats | storm30b:ships_lost | consistent | consistent | **unchanged** | 2026-10-29-ai-fleet-hunt-absent-in-remake233.md |
| stats | weather30:any_rough | consistent | consistent | **unchanged** |  |
| stats | weather30:rough_cells | consistent | consistent | **unchanged** |  |
| stats | weather60h:any_rough | consistent | consistent | **unchanged** |  |
| stats | weather60h:hits | consistent | consistent | **unchanged** |  |
| stats | weather60h:rough_cells | consistent | consistent | **unchanged** |  |
