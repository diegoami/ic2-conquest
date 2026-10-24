# Main handoff: #1388 strategic targeting and routing

Conquest attributed the retained owner's End-turn boundary. Source finding:
`findings/2026-10-24-seleucid-strategic-target-routing1388.md`; scalar evidence
`runs/experiments/data/run-exp-seleucid1388/audit-v1.json`; runners in
`runs/experiments/seleucid1388/`. Research PR69 is verified merged at
`cdb355fde49b7047d6164de26b2922054fb120ee`.
Use the [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/cdb355fde49b7047d6164de26b2922054fb120ee/docs/reports/2026-10-24-seleucid-strategic-target-routing1388.md).
Research independently reproduced retained controls; it did not launch another
original/Wine game or implement a production correction.

Original chooses enemy at191,95 (7000troops,score828), then its destination
wrapper routes toward189,104. Remake3c186007 rejects the farther target using
direct-walk reachability, chooses207,95 (31565troops,score212) and walks directly.
This explains212,96vs212,94. Same low-level waypoint gives identical7steps;
changing only target without routing gives213,94 and is insufficient.

Before implementing, read the promoted report and inspect the original
`FUN_0044CAB4` region/coast/fleet eligibility and the `DBA8/DB38/D174` destination
wrapper/navigation tables and line tests. Scope a faithful port for both target
eligibility and intermediate routing through the normal Main issue/PR workflow.
Keep the human low-level move command's caller semantics distinct from the AI
destination wrapper. Do not replace these rules with universal reachability,
hardcoded coordinates, a newly designed pathfinder or a change to combat stats.

Acceptance should include the private owner's precise target choice/waypoint/
entered cells, destination-only negative control, route/obstacle/contact cases,
original intermediate-point data identity, region/coast/fleet eligibility gates,
and appropriate ordinary engine/solution/CI regressions. Existing tactical
parity/writeback evidence remains valid within its scope. #1355 stays open;
native Windows check remains incomplete and physical Escape stopped Computer
Use. No optional Improved-controller tuning or native Computer Use restart is
part of this investigation.
