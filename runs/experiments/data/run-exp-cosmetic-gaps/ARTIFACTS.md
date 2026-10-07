# Preparing the artifacts for the claims audit and the tests (review R9)

The audit (`runs/experiments/cosmetic_gaps/claims_audit.py`) and `test_runner.py` read the binary
artifacts (screenshots, saves, strace logs, the staged save) from `artifacts/run-exp-cosmetic-gaps/`
— which is git-ignored (rule 1). From a fresh checkout:

```bash
# 1. every batch archive is on the GitHub release (no auth needed for public repos; a private
#    repo needs gh, which is already logged in on this machine):
gh release view run-exp-cosmetic-gaps --repo diegoami/ic2-conquest     # lists the assets
mkdir -p artifacts/run-exp-cosmetic-gaps && cd artifacts/run-exp-cosmetic-gaps
for a in batch-b1 batch-b3 batch-b4 batch-b7 batch-b8; do
  gh release download run-exp-cosmetic-gaps --repo diegoami/ic2-conquest \
      --pattern "$a.tar.gz" --output "$a.tar.gz"
  tar xf "$a.tar.gz" && rm "$a.tar.gz"     # the archives hold paths relative to this folder
done
cd ../..

# 2. verify: every member's sha256 is in the tracked manifests beside this file
python3 - <<'EOF'
import hashlib, glob, os
for m in sorted(glob.glob('runs/experiments/data/run-exp-cosmetic-gaps/MANIFEST-*.txt')):
    for l in open(m):
        p = l.split()
        if len(p) == 2 and p[1].startswith('member:'):
            f = os.path.join('artifacts/run-exp-cosmetic-gaps', p[1][7:])
            assert hashlib.sha256(open(f, 'rb').read()).hexdigest() == p[0], f
    print('manifest ok:', os.path.basename(m))
EOF

# 3. then, from runs/experiments/cosmetic_gaps/:
#    python3 claims_audit.py      (0 mismatches; --out writes a tracked versioned report)
#    python3 test_runner.py       (12 tests)
#    python3 test_claims_audit.py (11 tests)
```

Which batch carries what: b1 = the first title/toggle/position plays' binaries; b3 = the scuttle and
end-turn plays; b4 = a sweep archive that also carries b5, b6 and the first close probe (16 members,
`MANIFEST-b4.txt` lists them); b7 = the hardened sound plays with their post-event saves; b8 = the
hardened re-runs of the title, toggle, position and supply plays plus the markers play.
`STAGED-felsina-neutral-0721.SAV` (the staged save of §4) is inside the batch that was current when
it was crafted — `grep STAGED MANIFEST-*.txt` names it.
