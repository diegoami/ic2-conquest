# Research31: automatic foreign-provider support

Original code, staged Wine and separately labelled original-x86 execution; no native Windows confirmation. Owner selected Codex implementation / MiniMax review. Conquest issue92/PR93; research issue31. No build edits or T177 expansion.

Canonical records:

- `matrix-final.md` / `matrix-final.json`: compact complete56-case Wine table, exact post save/turn734 and all support deltas.
- `summary-final-20261017.json`: raw-offset independent decoding of all56 loaded/post pairs,227 save hashes,17 matching land/embarked pairs; all failed attempts retained.
- `audit-final-20261017.json`: complete original city-loop callers executed on all58 input saves with no patches/stubs. All58 arithmetic/order comparisons pass.53 complete Wine cases match every compared stock/treasury/unit field; three hostile cases match support fields/seller treasuries but retain explicit buyer-treasury confounds. Two input-only attempts are not completed Wine results.
- `release-verified-final-20261017.json`: all227 manifested saves independently match GitHub release digests; no extra assets. Release https://github.com/diegoami/ic2-conquest/releases/tag/run-exp-resupply31 .
- `SAVES.sha256`: complete saves only. `incomplete-artifacts.json` hashes the retained zero-byte interrupted autosave, which is not a valid save/result or published asset.
- `complete-source-audit.txt`, `complete-source-provenance.json`, `upstream-seat-source.txt`: full original function bodies/caller sites, pinned original listing SHA256. `dat-hashes.json` pins game data.
- Original `source-listing.txt`/`source-provenance.json` and inherited runner-source snapshots remain; they are not invented fresh observations. Initial adapted runner version is also pinned by commit b634d7a. Later logs include the actual probe hash.
- `wine-*.jsonl`: all staging edits, before/after fields, fingerprints, exact names, failure records. `environment.jsonl` is the driver's additional environment sink. First two logs include the research-side interruption and first conquest batch including disk-full interruption.
- `release-sync-*.json`, `audit-batch1-failure.txt`: upload/audit failure receipts and corrections; no original output removed. Mid-run JSON captures remain as historical subsets and include input-only cases not yet played at that checkpoint. Canonical final records supersede their selection/counts, not their measured data.

Scripts: `runs/experiments/resupply31/{probe,audit,summarize,release_sync}.py`. Never delete a save, overwrite a measured output, or regenerate missing evidence into an old name. Fresh probes create unique names and refuse existing artifacts. Commit/push after every batch and within30minutes.

Workspace (owner authorized): /home/diego/projects/ic2-work/resupply31/conquest. Sibling `artifacts` holds all228 files (227 complete saves plus one empty interrupted copy); `wine-land`, `wine-aboard`, `wine-fleet` are stopped private prefixes. Old /tmp archive and prefixes retained as extra copies. Copy Wine prefixes with symlinks preserved (`cp -a`); never follow the z: symlink.

All new unit coordinates are (102,49), moves0. City relocation and ownership do not rebuild city lists/map overlays. Carrier is human-owned; carrier-far is record-based staging, not a synchronization claim. Other units disabled, recruitment slots cleared, mercenary offers disabled. Hostile AI recruitment before support remains explicitly confounded.
