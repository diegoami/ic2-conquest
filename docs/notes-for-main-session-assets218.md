# Main-session prompt: retrieve the reviewed original-assets extractor

```text
Original-asset extraction for remake #1740 / Research #218 is implemented and
reviewed. Please retrieve the tool rather than duplicate the extractor work.

Repository: diegoami/ic2-conquest, PR #346.
Reviewed source pin: 1544d666c45004f1eda362cb84a4701e0e4143d2.
Tool: scripts/extract_original_assets.py (version 1.0.1).
Tool SHA-256: 5d266a075ce1cc75ccb359f2b4a64aa5bbf82e2dca031965c729e6abd53a97f5.
Guide: docs/original-assets-extractor.md.
Tests: tests/test_original_assets.py (36 synthetic tests).

Retrieve the source file from that exact commit and verify its SHA-256. The
single file has no conquest or third-party imports. It needs Python 3.10+;
main must explicitly arrange the runtime to ship it, or port the tested contract
into .NET. Do not assume a player's machine already has Python.

Research independently qualified the static extractor: isolated tests, exact
original metadata reproduction, PNG decoding and 362 private output hashes.
The tool inventories PE/DFM assets, emits versioned metadata, optionally writes
private PNG/CUR/ICO/WAV files and refuses to overwrite existing outputs.

Main owns packaging and actual consumers: per-machine cache/fallback, owner city
variants, six river shapes, recolouring, mask/SRCERASE composition and scenario
gaps. Follow your repository's current scope before implementing integration;
this handoff does not authorize a release, gameplay changes or game runs.
Original/extracted media stays private and user-supplied; only the tool ships.

Canonical extraction contract: Research PR219, merge
a0870dd26b86f74233334e7d9500309082403933,
docs/reports/2026-11-07-original-assets218-extraction-spec.md.
Conquest code is reviewed; full original-art adapter/UI/native acceptance is not.
```

[Reviewed tool source](https://github.com/diegoami/ic2-conquest/blob/1544d666c45004f1eda362cb84a4701e0e4143d2/scripts/extract_original_assets.py)
and [source PR](https://github.com/diegoami/ic2-conquest/pull/346).
The original reviewed commit's guide predates the acceptance receipt; the tool
file pin/hash above is unchanged by later documentation-only handoff commits.
