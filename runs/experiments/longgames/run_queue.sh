#!/usr/bin/env bash
# Owner 2026-11-04: "complete this and play a game with all civilizations" (the 7 civs not yet played, 40 turns, full
# campaigns) and "5 games x 150 turns: Rome, Carthago, Ptolomeans, Seleucids, Macedons ... save checkpoints so that we can
# continue if interrupted" (original only: the comparison is the anchored replay; owner: "we need to get to the later years").
# Remake v0.9.3 (a44c42fc). One game at a time; each waits for free memory (memory wait-for-free-memory). Re-running this
# script continues where it stopped: a finished game (summary.json) is skipped, an unfinished one is resumed exactly
# (difftest.campaign --resume). Every 25 turns and at the end a pack goes to the save corpus (release ic2-save-corpus +
# gdrive:IC2/artifacts/save-corpus). After each game: anchored replay with per-turn seeds (+ retries), archive, commit, push.
set -u
cd "$(dirname "$0")/../../.."
PIN=a44c42fc
export IC2_REMAKE=$HOME/projects/ic2-remake-pin-$PIN IC2_DIFF_BUILD=$PWD/artifacts/diffpin-$PIN-build PYTHONUNBUFFERED=1 IC2_LOG_RANDSEED=1
LOG=artifacts/longgames-queue.log
QUEUE="${QUEUE:-v093:S09_Illyria:40:full v093:S10_Dacia:40:full v093:S11_Bithynia:40:full v093:S12_Galatia:40:full v093:S13_Armenia:40:full v093:S14_Media:40:full v093:S15_Thracia:40:full long:S00_Rome:150:orig long:S01_Carthage:150:orig long:S03_Ptolemaic:150:orig long:S02_Seleucid:150:orig long:S04_Macedonia:150:orig}"
say() { echo "$(date -Is) $*" | tee -a $LOG; }
wait_free() {  # available memory > 6 GB and no other game process
  while true; do
    avail=$(free -m | awk '/^Mem:/{print $7}')
    other=$(pgrep -f "Imperial Conquest 2" | wc -l)
    [ "$avail" -gt 6000 ] && [ "$other" -eq 0 ] && return
    say "waiting: available ${avail} MB, game processes ${other}"; sleep 120
  done
}
for item in $QUEUE; do
  IFS=: read exp start turns mode <<< "$item"
  if [ $mode = orig ]; then
    # Long games: difftest.longgame (parts, exact resume, human-seat handover after End of Game, corpus, anchored).
    g=$(echo ${start#*_} | tr A-Z a-z)-rulebot1-${turns}t; A=artifacts/run-exp-longgames; mkdir -p $A
    if grep -q "done:" $A/$g.longgame.log 2>/dev/null; then say "skip $g (done)"; continue; fi
    wait_free; say "longgame $g"
    python3 -m difftest.longgame artifacts/run-exp-civ-sweep/${start}_AUTO0720.SAV $A/$g --turns $turns --pin $PIN >> $LOG 2>&1 \
      || { say "STOPPED longgame $g: re-run this script to resume"; exit 1; }
    python3 scripts/archive_measurements.py run-exp-longgames --commit >> $LOG 2>&1 || say "archive failed for $g"
    git push -q >> $LOG 2>&1 || say "push failed"
    continue
  fi
  case $exp in v093) NAME=run-exp-longrun-v093;; long) NAME=run-exp-longgames;; esac
  A=artifacts/$NAME; mkdir -p $A
  g=$(echo ${start#*_} | tr A-Z a-z)-rulebot1-${turns}t; G=$A/$g
  if [ -f $G/summary.json ]; then say "skip $g (finished)"; else
    wait_free
    flags="--turns $turns --seed 12345"; [ $mode = orig ] && flags="$flags --original-only"
    if [ -d $G ]; then flags="$flags --resume"; say "resume $g"; else say "start $g"; fi
    python3 -m difftest.campaign artifacts/run-exp-civ-sweep/${start}_AUTO0720.SAV $G $flags >> $A/$g.log 2>&1 &
    pid=$!; last=0
    while kill -0 $pid 2>/dev/null; do
      sleep 60
      done_t=$(wc -l < $G/turns.jsonl 2>/dev/null || echo 0)
      if [ $mode = orig ] && [ $((done_t / 25)) -gt $((last / 25)) ]; then
        python3 -m difftest.save_corpus publish $G >> $LOG 2>&1 || say "corpus publish failed at $done_t"; last=$done_t
      fi
    done
    wait $pid; rc=$?; say "end $g exit $rc ($(wc -l < $G/turns.jsonl) turns)"
    [ -f $G/summary.json ] || { say "STOPPED $g without summary: re-run this script to resume"; exit 1; }
  fi
  [ -f $A/$g.corpus-done ] || { python3 -m difftest.save_corpus publish $G >> $LOG 2>&1 && touch $A/$g.corpus-done; }
  if [ ! -f $A/$g.anchored-done ]; then
    wait_free
    python3 -m difftest.anchored $G --pin $PIN --turn-seed 12345 --out anchored-turnseed >> $A/$g.anchored-turnseed.log 2>&1
    python3 -m difftest.anchored $G --pin $PIN --turn-seed 12345 --out anchored-turnseed --retry-errors >> $A/$g.anchored-turnseed.log 2>&1
    touch $A/$g.anchored-done; say "anchored $g done"
  fi
  python3 scripts/archive_measurements.py $NAME --commit >> $LOG 2>&1 || say "archive failed for $g"
  git push -q >> $LOG 2>&1 || say "push failed"
done
say "queue done"
