# Decompile path (branch tooling/decompile-path)

- [x] 1 shared module `harness/decompile.py` (stdlib only so any script can import it with the repo root on sys.path; harness/ is where driver.py's IC2_WORK lives)
- [x] 2 pin SHA-256 (module + docs/environment.md), `check()`
- [x] 3 replaced hardcoded defaults in runs/experiments (no hits in tests/ or scripts/); the five `paths.py` import from the module
- [x] 4 docs (docs/tasks, intent-and-approaches, environment, two data READMEs); findings/ and measured outputs untouched
- [x] 5 scratch/datload.txt missing: `decompile.MISSING`, `decompile.path()` fails naming it; nothing in the code reads it (panel_model.LOADER is a transcription)
- [x] 6 verify: test_info_window 10 PASS, 3 SKIP, 0 FAIL; both check_dump_vs_extract report 0 differ with no env vars

Decisions: precedence IC2_DECOMPILE > IC2_RETOOLS > $IC2_WORK/decompile (if it exists) > ~/ic2-work/decompile (experiment libs set IC2_WORK to a private folder). IC2_DUMP / IC2_SYMBOLS override single files (check() accepts them only if the basename is a pinned name).
Note: importing refusal_texts/class_table.py writes a new versioned tracked output (class_sites.v2.tsv) as a side effect; it was created during verification and left untracked, not committed.
