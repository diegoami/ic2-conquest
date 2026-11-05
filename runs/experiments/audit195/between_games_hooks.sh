#!/usr/bin/env bash
# #195, run between two long-game queue items: (1) C22: the D734 hook v2 (outer caller past DBA8's recursion) on the 16
# starts; (2) the own-capital stays: the FB7C diplomacy hook, one round from each of the 8 exact starts (research PR #213).
# waits for a NEW "done: N turns in K part(s)" line in the queue log (polled each second past the line count at start), takes a Wine hold
# at once (before the queue's next wait_free), runs, releases. Holds and runs in this one script (memory
# wine-one-run-at-a-time: never chain jobs on a phrase a launcher echoes).
set -u
cd "$(dirname "$0")/../../.."
OUT=$1; Q=/home/diego/projects/ic2-conquest/artifacts/longgames-queue.log
LOG=$OUT.runner.log
[ -e $OUT ] && { echo "refusing: $OUT exists" >> $LOG; exit 1; }
N0=$(wc -l < $Q)                                  # only lines written after the start count
until tail -n +$((N0 + 1)) $Q | grep -q 'done: [0-9]* turns in [0-9]* part(s)'; do sleep 1; done
bash -c 'exec -a "hold: Imperial Conquest 2 (#195 hooks between games)" sleep 14400' & HOLD=$!
trap 'kill $HOLD 2>/dev/null' EXIT
echo "$(date -Is) queue item finished; holding Wine (pid $HOLD)" >> $LOG
while [ "$(pgrep -f '^Imperial Conquest' | wc -l)" -gt 0 ]; do sleep 2; done
STARTS=$(ls /home/diego/projects/ic2-conquest/artifacts/run-exp-civ-sweep/S??_*_AUTO0720.SAV)
IC2_FLEET_HOOK=d734tail_hook IC2_HOOK_LOG=d734 PYTHONUNBUFFERED=1 python3 -m difftest.probes.fleetphase_hook_run $OUT 5 $STARTS >> $LOG 2>&1
echo "$(date -Is) v4 hook run exit $?" >> $LOG
SV=/home/diego/projects/ic2-conquest/artifacts/run-exp-audit195/stays-hook-v1/starts
IC2_FLEET_HOOK=fb7c_hook IC2_HOOK_LOG=fb7c IC2_START_RANDSEEDS=$SV/seeds.json PYTHONUNBUFFERED=1 \
  python3 -m difftest.probes.fleetphase_hook_run ${OUT%/*}/stays-fb7c-v1 1 $SV/*.SAV >> $LOG 2>&1
echo "$(date -Is) fb7c hook run exit $?; releasing the queue" >> $LOG
