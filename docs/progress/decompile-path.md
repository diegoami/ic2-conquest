# Decompile path (branch tooling/decompile-path)

- [ ] 1 shared module `harness/decompile.py` (stdlib only so any script can import it with the repo root on sys.path; harness/ is where driver.py's IC2_WORK lives)
- [ ] 2 pin SHA-256 (module + docs/environment.md), `check()`
- [ ] 3 replace hardcoded defaults in runs/experiments (no hits in tests/ or scripts/)
- [ ] 4 docs
- [ ] 5 scratch/datload.txt missing: `decompile.MISSING`, `decompile.path()` fails naming it
- [ ] 6 verify

Decisions: precedence IC2_DECOMPILE > IC2_RETOOLS > $IC2_WORK/decompile; IC2_DUMP / IC2_SYMBOLS override single files.
