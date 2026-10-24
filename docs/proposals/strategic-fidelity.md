# Strategic fidelity research: original IC2 versus remake

## Authorization and purpose

Owner requested strategic scenario research across several nations and decisions,
then explicitly approved execution on 2026-10-24: “Yes make it happen”. This is
a separate research investigation, not the paused battle queue or optional
Improved Computer general work. Record this approval on the new run issue before
launching games. #1388 is the existing reference case, not a new discovery here.

Question: given comparable campaign inputs, do both games select the same
strategic actions? At a differing action, can matching the local decision inputs
explain whether the cause is an original-fidelity defect, an intentional remake
choice, a conversion/state difference, randomness, or an unresolved boundary?

## Declared first pilot

Pin current remake source/data before starting. Reuse original instructions,
isolated Wine harness and verified observer components. No other repository is
written. Six retained generated campaign starts from conversion #153 provide
human seats Rome, Carthage, Seleucid, Ptolemaic, Numidia and Gaul, turn0720.
Each original End turn visits other AI seats; these are six campaign inputs,
not six isolated single-nation AI tests or six seeds of the same state.

Add four separately declared, reproducibly staged strategic cases:

1. Rome–Gaul war from the Numidian start, leaving the human out of that war.
2. Carthage–Numidia war from the Roman start, leaving the human out of that war.
3. Ptolemaic shortages from the Carthaginian start: existing Ptolemaic armies
   have zero supplies and money; morale is retained, so supply/hire gates can
   be distinguished from morale thresholds.
4. A threatened Seleucid capital from the Roman start: a computer-controlled
   Carthaginian army is moved to an empty land cell 12–16 cells from Antioch,
   and the two computer nations are at war. Record exact tile/army selection
   and all edits in the manifest before launching it.

Run one End turn per case, without player orders. Compare whole-turn observed
states, but locate differences at recorded local decisions. Selected plain
versus observed same-seed controls must produce identical complete saves before
trusting a new recorder. Do not assume equal integer seed values align engines'
random streams. Unexpected human tactical battles stop that case with evidence
retained; do not inject battle orders to force a strategic result.

## What the pilot measures

- Ordinary native End-turn decisions, accepted commands/routes and resulting
  armies/fleets/nation resources, with deterministic repetition controls.
- Original strategic army target-tree entry states and destination calls;
  fleet destination calls where captured. Capture original RAM at the decision
  boundary and preserve observations before attempting another run.
- Conditional production-native decisions from the original captured state,
  after an explicit import/projection gate. Compare target scores, selected
  targets and resupply destinations against actual original instructions.
  Validate unit order/type/troops/quality, morale, army resources, city ownership
  and relations before calling a comparison same-input.
- Track recruitment, resource and diplomatic outcomes separately. Their complete
  original decision/RNG traces are a later instrumentation stage unless the
  pilot actually records them. Never call final-state coverage exact decision
  tracing, or a family with no observed event tested.

An original RAM-to-SAV projection is a synthetic diagnostic container, not an
original Save As. Label it accordingly. Identity joins use raw record lineage
and attributes, not assumptions about native IDs or record compaction.

## Analysis and deliverables

One ledger row per scenario and compared decision, with phase, actor, inputs,
original/remake choice, earliest attributable difference, evidence references,
classification and remaining uncertainty. Preserve raw results and mismatches;
do not normalize differences away or infer bugs from total casualties alone.
For a leading discrepancy, attempt a bounded conditional replay/negative
control. Clearly distinguish different whole-turn histories from a local
same-input rule difference. Report matches with their exact denominator.

Deliver the pilot finding and scripts, a coverage matrix for all decision
families, and a prioritized expansion plan. Expand subsequently to all16starts,
more terrain/resource/war scenarios and short3–5turn continuations. Longer
campaigns are useful after first-divergence controls exist; the pilot does not
promise whole-game equivalence. The issue stays open for research coverage
that remains; production fixes follow their own Main workflow.

## Evidence and privacy requirements

Never delete or overwrite a measured output or save, even to regenerate it.
Each run/script uses unique labels and exclusive file creation. Keep public-safe
text in `runs/experiments/data/run-exp-strategic-fidelity/`, runners in
`runs/experiments/strategic-fidelity/`, and durable notes in
`RUN-NOTES-strategic-fidelity.md`. Commit/push each batch and at least every30min.
EXE/DAT/PNG/SAV/RAM remain outside Git; preserve hashes and approved artifact
bundles. Existing owner #1355/#1388 inputs/full states/hashes stay private and
are never mixed into generated-scenario bundles. Do not run a generic archiver
over private runtime trees. Respect the stopped native Computer Use session;
Wine controls do not establish Windows acceptance.

Publish findings here, then relay actual landed pins to Research for intake.
Main is reached through the owner and consumes promoted research reports.
No direct Main message, production source write, package install or reviewer
launch is authorized merely to exercise compatibility.
