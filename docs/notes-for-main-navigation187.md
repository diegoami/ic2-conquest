# T212 / #187: promoted navigation and caller-history handoff

Use the canonical Research reports:

- [Navigation data and decision rule, PR72](https://github.com/diegoami/imperial-conquest-2-research/blob/c863a97cb1fc66206e23521c7bdd024548ba41dd/docs/reports/2026-10-24-army-navigation-rule187.md).
- [Garrison/mercenary caller histories, PR73](https://github.com/diegoami/imperial-conquest-2-research/blob/2420f67295e39d3a37ce4ff4f7adf242822fe1cb/docs/reports/2026-10-24-garrison-mercenary-caller-guards187.md).

Main #1394 is open with `status:in-progress`. Its current T212 contract covers
original-policy F31C enemy-army target selection/routing and its tested recursive
context. Garrison, mercenary and homeland production behavior remains unchanged
under that contract. Promotion does not widen scope or constitute implementation
acceptance. Conquest changed no production code or task labels.

The first report specifies 58 valid navigation points, three route matrices,
eight strict geographic boxes and six coordinate splits. Eligibility is the
same geographic pair or any own fleet, independent of direct line or a usable
ferry. Waypoints use visibility, row-index distance and hub fallback. No fourth
island route matrix exists. The conditioned native walker result is retained;
it does not prove native navigation or whole-turn parity.

The promoted caller follow-up completes the requested tests: 88 original
controls, including 64 full F31C histories, and 20 single-word offer pairs.
Research freshly reproduces every ledger field and all 88 unobserved whole-RAM/
stack identities without normalization. No fresh game or native comparison.

Mercenary entry inherits zero from EE60's loop counter. A refused nested
mercenary route can instead leave−1 for later garrison. The blocked absent/
present-offer pair ends with zero/nine moves; a progress-then-block pair retains
seven with the negative guard, versus recursive cleanup ending at signed−1.
Do not use universal zero, make all garrison guards nonnegative, clamp the
observations, or propagate every refusal without respecting caller depth.

The source-shaped decision table distinguishes ordinary destination returns,
mercenary refusal, no offer and recursion. Arbitrary standalone/interception/
combat/embarked histories are not universally resolved. A broader production
contract needs its own explicit review; the tests do not require a new owner
save or screen access.

The older navigation packet's four observer-only DBA8 call additions remain
documented separately; the new caller ledgers reproduce without normalization.
PR190 economy/diplomacy/provider/embark-overflow evidence is now promoted in
Research PR74 at `16ec64575d85582378705c407e0f1b82df848328`, including evidence
for Main #1412. Keep that packet distinct from PR72/73.
The city-versus-army classification is promoted by Research PR75 at
`2c2a18370c4d9c6be49692fdc7f830fee6912323`:
use the [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/2c2a18370c4d9c6be49692fdc7f830fee6912323/docs/reports/2026-10-24-city-army-selection187.md)
and its safe receipt. Main #1417/#1418 track city policy and the independent
exact-100 boundary. The retained branch difference comes from the unchanged
designed city filter, not import or this state's branch predicates. Weak score
checks include 100; the separate better-city comparison remains strictly >100.
Research reproduces the complete native v3 scalar and all 32 grid rows. No
production correction, broader T212 contract or acceptance follows automatically.
Main receives this handoff through the owner and issue1394; no unverified direct
Main session channel is substituted.
