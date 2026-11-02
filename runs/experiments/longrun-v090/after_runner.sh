#!/usr/bin/env bash
# After run_all.sh: the Seleucid game again (r2, the first stopped at turn 26 on a checkpoint save timeout), then the
# original's decide/walk hook from the Rome game's own end-of-turn saves before turns 2, 4 and 7 (capital armies,
# Carthage at Castulo, Seleucid at Astacus). One Wine run at a time.
set -u
cd "$(dirname "$0")/../../.."
RUNNER_PID=$1
while kill -0 $RUNNER_PID 2>/dev/null; do sleep 30; done
A=artifacts/run-exp-longrun-v090
STARTS=S02_Seleucid SUFFIX=-r2 runs/experiments/longrun-v090/run_all.sh
R=$A/rome-rulebot1-40t/original
echo "hooks start $(date -Is)" >> $A/runner.log
PYTHONUNBUFFERED=1 python3 -m difftest.probes.decide_hook_run $A/hooks-decide-v1 1 \
  $(ls $R/t01-a*.SAV | tail -1) $(ls $R/t03-a*.SAV | tail -1) $(ls $R/t06-a*.SAV | tail -1) > $A/hooks-decide-v1.log 2>&1
echo "hooks end exit $? $(date -Is)" >> $A/runner.log
python3 scripts/archive_measurements.py run-exp-longrun-v090 --commit >> $A/runner.log 2>&1
echo "after_runner done $(date -Is)" >> $A/runner.log
