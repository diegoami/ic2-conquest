#!/usr/bin/env bash
# #195 C22/C23: run the D734 end-check hook (patches/d734tail_hook.py) on the 16 civ-sweep starts, 5 rounds, seed 12345 (the
# layout of run-exp-econ2), once Wine is free. While it runs, a placeholder process named "Imperial Conquest 2 hold" keeps
# runs/experiments/longgames/run_queue.sh waiting (its wait_free counts `pgrep -f "Imperial Conquest 2"`): one Wine game at a
# time (memory wine-one-run-at-a-time), even in the gaps between this runner's games.
#   setsid nohup bash runs/experiments/audit195/c22c23_hook_run.sh <out dir> [wait-for-file-line]
set -u
cd "$(dirname "$0")/../../.."
OUT=$1; WAITFILE=${2:-}; WAITLINE=${3:-}
LOG=$OUT.runner.log
say() { echo "$(date -Is) $*" | tee -a $LOG; }
[ -e $OUT ] && { say "refusing: $OUT exists"; exit 1; }
if [ -n "$WAITFILE" ]; then
  until grep -q "$WAITLINE" "$WAITFILE" 2>/dev/null; do sleep 20; done
  say "seen '$WAITLINE' in $WAITFILE"
fi
while [ "$(pgrep -f 'Imperial Conquest 2' | wc -l)" -gt 0 ] || [ "$(free -m | awk '/^Mem:/{print $7}')" -lt 6000 ]; do sleep 5; done
bash -c 'exec -a "Imperial Conquest 2 hold (c22c23 hook run)" sleep 86400' & HOLD=$!
say "holding Wine (pid $HOLD); starting the hook run"
STARTS=$(ls /home/diego/projects/ic2-conquest/artifacts/run-exp-civ-sweep/S??_*_AUTO0720.SAV)
IC2_FLEET_HOOK=d734tail_hook IC2_HOOK_LOG=d734 PYTHONUNBUFFERED=1 python3 -m difftest.probes.fleetphase_hook_run $OUT 5 $STARTS >> $LOG 2>&1
rc=$?
kill $HOLD
say "hook run exit $rc; hold released"
