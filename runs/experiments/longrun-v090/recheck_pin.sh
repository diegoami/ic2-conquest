#!/usr/bin/env bash
# Anchored turn-seeded replays of every stored game on a new remake pin (2026-11-04: candidate v0.9.4 = main 168dbc04).
# Remake only (no Wine), so it may run beside the long-game queue; each game waits for > 6 GB available memory
# (memory wait-for-free-memory). Resumable: a game with <out>/turns.jsonl covering all its turns is skipped by anchored.py's
# own resume; error rows are retried at the end. Writes <campaign>/anchored-<pin>-ts and artifacts/recheck-<pin>.log.
set -u
cd "$(dirname "$0")/../../.."
PIN=${PIN:-168dbc04}; LOG=artifacts/recheck-$PIN.log
export IC2_REMAKE=$HOME/projects/ic2-remake-pin-$PIN IC2_DIFF_BUILD=$PWD/artifacts/diffpin-$PIN-build PYTHONUNBUFFERED=1
GAMES=${GAMES:-"run-exp-longrun-v090/rome-rulebot1-40t run-exp-longrun-v090/carthage-rulebot1-40t run-exp-longrun-v090/gaul-rulebot1-40t run-exp-longrun-v090/seleucid-rulebot1-40t run-exp-longrun-v091/ptolemaic-rulebot1-40t run-exp-longrun-v091/macedonia-rulebot1-40t run-exp-longrun-v092/numidia-rulebot1-40t run-exp-longrun-v092/greece-rulebot1-40t run-exp-longrun-v093/celtiberia-rulebot1-40t run-exp-longrun-v093/armenia-rulebot1-40t run-exp-longrun-v093/bithynia-rulebot1-40t run-exp-longrun-v093/dacia-rulebot1-40t run-exp-longrun-v093/galatia-rulebot1-40t run-exp-longrun-v093/illyria-rulebot1-40t run-exp-longrun-v093/media-rulebot1-40t run-exp-longrun-v093/thracia-rulebot1-40t run-exp-longgames/rome-rulebot1-150t run-exp-longgames/rome-rulebot1-150t-h1 run-exp-longgames/carthage-rulebot1-150t"}
wait_free() { while [ "$(free -m | awk '/^Mem:/{print $7}')" -lt 6000 ]; do sleep 60; done; }
for g in $GAMES; do
  d=artifacts/$g; [ -d $d ] || { echo "$(date -Is) missing $g" >> $LOG; continue; }
  [ -e $d/anchored-$PIN-ts.done ] && continue
  wait_free; echo "$(date -Is) start $g" >> $LOG
  python3 -m difftest.anchored $d --pin $PIN --turn-seed 12345 --out anchored-$PIN-ts >> $d.anchored-$PIN-ts.log 2>&1
  python3 -m difftest.anchored $d --pin $PIN --turn-seed 12345 --out anchored-$PIN-ts --retry-errors >> $d.anchored-$PIN-ts.log 2>&1
  touch $d/anchored-$PIN-ts.done; echo "$(date -Is) done $g" >> $LOG
done
echo "$(date -Is) all done" >> $LOG
