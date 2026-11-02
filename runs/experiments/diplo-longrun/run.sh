#!/usr/bin/env bash
# Diplomacy attribution of the long runs (owner 2026-11-03): the original's relation writes (diplo hook) from 7 long-run
# states x 3 rounds, the remake main 11f713e2 replaying each round from the original's own autosave, then the comparer.
set -u
cd "$(dirname "$0")/../../.."
D=artifacts/run-exp-diplo-longrun; PIN=11f713e2
export PYTHONUNBUFFERED=1
python3 -m difftest.probes.diplo_hook_run $D/orig-v1 3 $D/starts/*.SAV > $D/orig-v1.log 2>&1 || echo "hook run exit $?" >> $D/orig-v1.log
python3 runs/experiments/aidecide/compare.py remake $D/orig-v1 $PIN $D/remake-$PIN-v1 > $D/remake.log 2>&1
python3 runs/experiments/diplo/compare.py $D/orig-v1 $D/remake-$PIN-v1 $D/report-diplo-v1.json > $D/compare.log 2>&1
python3 scripts/archive_measurements.py run-exp-diplo-longrun --commit >> $D/compare.log 2>&1
echo done >> $D/compare.log
