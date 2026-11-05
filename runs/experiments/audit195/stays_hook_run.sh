#!/usr/bin/env bash
# #195 the own-capital stays (9 rows of stays-168dbc04-ts-v1.txt, Greece t21 being X2): hooks on the original's own starts.
# The v0.9.0-v0.9.2 games did not log a RandSeed per checkpoint, so step 1 replays each game's original side from its start
# (seed 12345, rulebot-1, IC2_LOG_RANDSEED=1) up to the turn before the row; step 2 (stays_seeds.py) checks the replayed
# saves are byte-identical to the stored ones and writes the starts + seeds; step 3 runs decide_hook and capdef_hook one
# round from each start with its RandSeed. Holds Wine like c22c23_hook_run.sh (one Wine game at a time).
#   setsid nohup bash runs/experiments/audit195/stays_hook_run.sh <out dir> [wait-for-file] [line]
set -u
cd "$(dirname "$0")/../../.."
OUT=$1; WAITFILE=${2:-}; WAITLINE=${3:-}
LOG=$OUT.runner.log
CS=/home/diego/projects/ic2-conquest/artifacts/run-exp-civ-sweep
say() { echo "$(date -Is) $*" | tee -a $LOG; }
[ -e $OUT ] && { say "refusing: $OUT exists"; exit 1; }
if [ -n "$WAITFILE" ]; then until grep -q "$WAITLINE" "$WAITFILE" 2>/dev/null; do sleep 2; done; say "seen '$WAITLINE'"; fi
while [ "$(pgrep -f 'Imperial Conquest 2' | wc -l)" -gt 0 ] || [ "$(free -m | awk '/^Mem:/{print $7}')" -lt 6000 ]; do sleep 2; done
bash -c 'exec -a "hold: Imperial Conquest 2 (stays hook run)" sleep 86400' & HOLD=$!
trap 'kill $HOLD 2>/dev/null' EXIT
say "holding Wine (pid $HOLD)"
mkdir -p $OUT/regen
for spec in rome:S00_Rome:9 carthage:S01_Carthage:34 gaul:S06_Gaul:28 ptolemaic:S03_Ptolemaic:8 numidia:S05_Numidia:10 greece:S07_Greece:5; do
  IFS=: read g s k <<< "$spec"
  say "regen $g ($s) $k turns"
  IC2_LOG_RANDSEED=1 PYTHONUNBUFFERED=1 python3 -m difftest.campaign $CS/${s}_AUTO0720.SAV $OUT/regen/$g-rulebot1 --turns $k --seed 12345 --original-only >> $OUT/regen/$g.log 2>&1
  say "regen $g exit $?"
done
python3 runs/experiments/audit195/stays_seeds.py $OUT >> $LOG 2>&1 || { say "seeds check failed: see $LOG"; exit 1; }
for hook in decide_hook capdef_hook; do
  say "hook $hook"
  IC2_FLEET_HOOK=$hook IC2_HOOK_LOG=${hook%_hook} IC2_START_RANDSEEDS=$OUT/starts/seeds.json PYTHONUNBUFFERED=1 \
    python3 -m difftest.probes.fleetphase_hook_run $OUT/$hook 1 $OUT/starts/*.SAV >> $LOG 2>&1
  say "hook $hook exit $?"
done
say "done; hold released"
