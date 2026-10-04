#!/bin/bash
# B5 batch driver: for each batch (an attacker type x a size = 15 battles, or a size-matrix pairing = 18), run trials.py, then sync the release,
# then commit and push the tracked data (CLAUDE.md rule 6: every batch, at least every 30 min). Stops after a batch with errors (the data of it is
# still committed). Usage: sweep_run.sh <batch-name>:<cell,cell,...> ...   (seeds 1-3 each)
cd "$(dirname "$0")/../../.." || exit 1
rc_all=0
for b in "$@"; do
  name=${b%%:*}; cells=${b#*:}
  python3 runs/experiments/battles/trials.py run ${cells//,/ } --seeds 1-3 --stop-on-error; rc=$?
  python3 runs/experiments/battles/trials.py table
  python3 runs/experiments/battles/release_sync.py "$name"; rs=$?
  git add runs/experiments/data/run-exp-battle-sweep runs/experiments/battles tests
  git commit -qm "B5 sweep batch $name (trials rc=$rc)

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
  git push -q 2>&1 | tail -1
  echo "BATCH $name trials_rc=$rc release_rc=$rs"
  if [ $rc -ne 0 ] || [ $rs -ne 0 ]; then rc_all=1; break; fi
done
echo SWEEP_DONE rc=$rc_all
