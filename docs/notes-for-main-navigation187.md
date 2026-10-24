# T212 / #187 handoff — rule package and exact stop limit

Read `findings/2026-10-24-army-navigation-rule187.md`,
`docs/navigation187-rule.md` and the interpreted data/public matrix under
`runs/experiments/data/run-exp-navigation187/`. Research PR72 merged at
`c863a97cb1fc66206e23521c7bdd024548ba41dd`:
use the [promoted report](https://github.com/diegoami/imperial-conquest-2-research/blob/c863a97cb1fc66206e23521c7bdd024548ba41dd/docs/reports/2026-10-24-army-navigation-rule187.md)
before changing production behavior. No T212 label
was cleared and no production patch was made here.

The reusable eligibility and first-destination rules/data are recovered and
original-instruction checked:58 valid points,3x7x8 route rows,8 strict geographic
boxes,6 coordinate split thresholds. Eligibility is same geographic pair OR any
own fleet, independent of line/usable ferry. CB40 is medium continuity excluding
the endpoint, not occupancy pathfinding. D174 uses visible nodes, row-index
distance and hub fallback, not a shortest path. Ferry result includes waiting/
embark/request side effects even with intermediate X−1. Low-level contact remains
the walker's separate budget/war dispatch.

Do not invent a fourth island routing table. It does not exist; static-world
land-domain enumeration proves graph fallback cannot be reached for valid
same-island pairs. Do not equate the coordinate split bit with water adjacency.
The owner final conditional and current native supplied-waypoint walker pass;
portable fixture descriptions give broader regressions without owner data.

Caller limit: DBA8 direct post-walk guard reads an uninitialized local. Actual
F31C target-tree/recursive context is proved nonnegative, but standalone/other
garrison/mercenary/homeland histories are not universally defined. Do not guess
universal initialization. Exact competing outputs and the minimal next original
call-site capture are in the report. A broader cleanup contract stays blocked;
scope any narrower T212 implementation explicitly around covered branches.
Behavior-preserving target/walker regressions can proceed independently.

Research replayed the retained controls/build, not an independent rebuild or
new caller experiment. Four older branch call lists gain DBA8 observer entries
under the current observer; only those added entries are normalized in its
receipt. No endpoint/budget/contact result changed. PR190's newer strategic
continuation is queued separately; its evidence is not promoted by this intake.

The requested caller follow-up is now measured in
`findings/2026-10-24-garrison-mercenary-caller-guards187.md` (separate intake
pending). In full F31C, a refused mercenary route can pass −1 to garrison;
without the offer it inherits zero. All other game input bytes match, and the
blocked budget differs. Do not initialize those callers universally to zero.
Main's existing approved scope/labels are not changed by these draft results.
