#!/usr/bin/env bash
# Long runs on remake v0.9.0 (88c1989b), owner 2026-11-02: 4 starts x 40 turns, rule bot as the human.
# Per game: difftest.campaign (free-running: each game continues its own state) then difftest.anchored (the remake
# re-plays every turn from the original's own state). Archive + commit + push every 25 min and after each game
# (rule 6); saves to release run-exp-longrun-v090 as one tarball per game (rule 1). A game folder that exists is
# skipped (a stopped original game is re-run under a new name, never resumed: its random stream would restart).
set -u
cd "$(dirname "$0")/../../.."
NAME=run-exp-longrun-v090; A=artifacts/$NAME; PIN=88c1989b; TURNS=${TURNS:-40}
export IC2_REMAKE=$HOME/projects/ic2-remake-pin-$PIN IC2_DIFF_BUILD=$PWD/artifacts/diffpin-$PIN-build PYTHONUNBUFFERED=1
mkdir -p $A
archive() { python3 scripts/archive_measurements.py $NAME --commit >> $A/runner.log 2>&1 || echo "archive failed $(date)" >> $A/runner.log; }
release() {  # $1 = game folder name
  tar -C $A -czf $A/$1-saves.tar.gz --exclude anchored/turns.jsonl $1 && \
  if gh release view $NAME >/dev/null 2>&1; then gh release upload $NAME $A/$1-saves.tar.gz --clobber
  else gh release create $NAME $A/$1-saves.tar.gz --title "$NAME" --notes "Long runs original vs remake v0.9.0 ($PIN): rule bot, 40 turns per start. Data: runs/experiments/data/$NAME"; fi \
  >> $A/runner.log 2>&1 || echo "release upload failed for $1 $(date)" >> $A/runner.log
}
for start in ${STARTS:-S00_Rome S01_Carthage S02_Seleucid S06_Gaul}; do
  g=$(echo ${start#*_} | tr A-Z a-z)-rulebot1-${TURNS}t
  [ -e $A/$g ] && { echo "skip $g (exists)" >> $A/runner.log; continue; }
  echo "start $g $(date -Is)" >> $A/runner.log
  python3 -m difftest.campaign artifacts/run-exp-civ-sweep/${start}_AUTO0720.SAV $A/$g --turns $TURNS --seed 12345 > $A/$g.log 2>&1 &
  pid=$!; echo "pid $pid" >> $A/runner.log
  last=$(date +%s)
  while kill -0 $pid 2>/dev/null; do
    sleep 30
    if [ $(( $(date +%s) - last )) -ge 1500 ]; then python3 -m difftest.anchored $A/$g >> $A/$g.anchored.log 2>&1; archive; last=$(date +%s); fi
  done
  wait $pid; echo "end $g exit $? $(date -Is)" >> $A/runner.log
  python3 -m difftest.anchored $A/$g >> $A/$g.anchored.log 2>&1
  archive; release $g
done
echo "all done $(date -Is)" >> $A/runner.log
