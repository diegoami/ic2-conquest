# Strategic fidelity pilot #171

Final finding: `findings/2026-10-24-strategic-fidelity-pilot171.md`.
Intaken by Research PR69/main `cdb355fde49b7047d6164de26b2922054fb120ee`,
canonical `docs/reports/2026-10-24-strategic-fidelity-pilot171.md`.
Canonical section3.3/spec now correct destination thresholds/capital preference;
automatic transfer capacity remains /100. Measurements unchanged.
Final scalar result: `summary-v2.json`, `decision-ledger-v2.jsonl`,
`case-summary-v2.csv`, `coverage-v1.csv`. Version1 results retain the first ten
cases; v2 includes the separately declared isolated shortage case.

**Eleven distinct inputs,112original army decision states.** Own-scorer branch
kinds agree58/112; raw resupply14/112; branch+primary destination9/109 with3
mercenary continuations unresolved. Actual original scores fed to native
DecideFromScores restore112/112 branch kinds. All51differing city targets and
55differing army targets exclude the original winner under native direct-walk
eligibility. Do not interpret rows as independent campaigns or every mismatch
as a separately attributed bug. Full native greedy command selection is outside
the conditional tree comparison. Same-target score comparisons retain empty
sentinel differences explicitly without counting -10000vs0 as another target.

Source/data pin55d96876a98ba3bb7142ca7c1ecc0d1b61095c18;349 archived Git blobs
verified in `source-pin-v1.json`. No other checkout modified. Scripts are in
`runs/experiments/strategic-fidelity/`; running notes at repository root.

## Artifacts and exact provenance

Drive folder: <https://drive.google.com/drive/folders/1gNiyzqi7RbgV0U4AJ5xwiYeDzK58H8-i>.

1. `pilot-evidence-batch01.tar.gz`,455members,9008591bytes,
   SHA256 `03f77f01cf23cac83cd86598115aa482f2903826efb525bbb719e8222cbf4f24`;
   file `17WwEnBzQTlrOgJ-n7bTbBq7jwjEKLzRD`.
2. `isolated-scarcity-and-tools-batch02.tar.gz`,42members,1301860bytes,
   SHA256 `e3dfd26a4607d20832790f6e139daec5c10543734971c560f79550e500c519cc`;
   file `1cF2nLkQPvkTMl98UIuG7lPm2VEqr3v1z`.
3. `terrain-sidecars-batch03.tar.gz`,2members,12551bytes,
   SHA256 `d52e297b3211890af5c51dc917c2cb0d7a3c9d71419cd2012e45ef1c84b2d620`;
   file `1ICs45mHD4lvbV7Utol6H-AQAv5VDGw5D`.
   Required native `.terrain.b64` sidecars, pinned with the source. The first
   recovery exposed their omission from batch01's JSON-only allowlist. That
   failed receipt and both existing archives remain preserved.
4. `geometry-audit-tools-batch04.tar.gz`,5members,601045bytes,
   SHA256 `f0b92b307836a78e9c7017762dd99f20ec7fd48588ec3da7ab94e6163bac8613`;
   file `1k5tbljKOYEJX6McF4bMepmUQLB0yoll9`. Independent compiled map audit.

All504members were locally rehashed from the completed archives. Upload size
and destination parent were read back; no remote-download digest verification
is claimed. Member/archive hashes are appended in `SAVES.sha256`. Existing
owner1355input hash canaries are absent from every selected member. Explicit
allowlists include only generated inputs, original outputs, observed generated
RAM, diagnostic projections, native states, dataJSON and compiled helperDLLs.
No original EXE/DAT, Wine prefix/runtime tree, owner1355/1388 material, credential,
PDB or unrelated directory is uploaded. Do not use the generic archive walker.

Batch01 `tools/` precedes the original-score counterfactual mode. Use the
separate batch02 `tools-v7/` for the latest compiled Probe, Engine/DataDLLs and
runtime/dependencyJSON. The first three bundles supply the Probe and required
terrain sidecars. Batch04 supplies `tools-geometry/`.
`bundle-verification-v3.json` records fresh exclusive four-bundle recovery and
compiled-tool replay: eleven decision rows and112geometry rows exactly equal
retained output. V2 retains the earlier successful three-bundle recovery.
Original/native engine behavior is unchanged; added
diagnostic modes/expanded gates are named in the immutable build logs. Published
script source hashes and compiled artifact hashes define the actual tool;
assembly informational Git metadata can precede the source changes it compiled.

The archive layout places RAM under `snapshots/<run>/`; local runners use
`original/<run>/snapshots/`. When recovering into a NEW workspace, supply that
path mapping or a read-only link. Projections/native folders retain their local
layout. Extracted root `data/` can be passed as `Probe`'s repository-root argument
(its parent, not the data directory itself). For example:

```bash
dotnet tools-v7/Probe.dll decisions EXTRACTED_ROOT \
  EXTRACTED_ROOT/projections/N-rome-hook-v1-v1 NEW_OUTPUT.jsonl
```

Use `eligibility` or `from-scores` in place of `decisions` for those diagnostics.
Original instruction replays additionally require the separately retained
original EXE pinned9d753d5d at the script's declared local path; it is excluded
from the bundles. These are retained diagnostic tools, not a game release.

## Measurement safeguards

Original observation:22guarded sites,792CPU preservation/capacity controls;
Roman and threat-case observer/plain pairs have identical full before/after
SAVs. Native observation-disabled Roman final state matches observed state.
Input gates validate112states/290524checks; troop/relation mutations reject
before comparable output. Six additional synthetic resupply controls use actual
original instructions and pass full native gates. Positive agreement controls
are included. No scoring, targeting, movement or RNG game helper is stubbed.
The independent Geometry.csproj/.cs.txt tool compares original map land codes
and army blocking against native terrain/entity occupancy at every cell of all
112states. Geometry-audit-v1 reports zero differences over5017600cell checks.
This is an army passability audit, not a sea-weather equality assertion.

Original same-seed repeats are controls, not additional scenarios. Input seed1
does not align original and native whole-turn random streams. Original RAM
projections retain news/UI metadata outside the decision-input gate, and are
synthetic diagnostic containers, never original Save As claims.

Manifestv1 war edit was a no-op; its native observation remains. Manifestv2
adds an explicit peace control rather than counting the duplicate. Manifestv3
adds a shortage case beyond automatic supply-provider range after the first
shortage case was naturally refilled. All previous declarations/results stay.

Failed initial site-count assertion and C# compile attempts were corrected
before dependent observations. Raw disassembly has two trailing blank operands;
its bytes are preserved. Authored code/docs are checked separately. Never
delete/overwrite any save or result to rerun: use a new version/label, including
analysis outputs. The first Roman raw decoder represented EDX as a coordinate
pair even at the scorer entry, where EDX is an output pointer. Those original
records are preserved; destination analysis uses only movement CALL sites.
Later decoding labels the scorer-entry goal null and retains raw EDX explicitly.
Commits/pushes preserve batches. Full fleet/homeland/economy/
diplomacy decision/RNG comparison, all16starts, short continuations and native
Windows acceptance remain open coverage; no production fix is claimed.
