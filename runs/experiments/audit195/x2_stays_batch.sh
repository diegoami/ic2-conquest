#!/usr/bin/env bash
# #195 X2 on the 13 remaining "original stays, remake moves" rows of the 168dbc04 recheck (stays-168dbc04-ts-v1.txt):
# each turn replayed in Instant and Tactical mode, seeds 12345+k, 12345, 99, owner nation only. Remake only.
set -u
cd "$(dirname "$0")/../../.."
A=/home/diego/projects/ic2-conquest/artifacts
export IC2_REMAKE=$HOME/projects/ic2-remake-pin-168dbc04 IC2_DIFF_BUILD=$A/diffpin-168dbc04-build
while read game turn nation; do
  case $game in rome*|carthage*|gaul*) run=run-exp-longrun-v090;; ptolemaic*) run=run-exp-longrun-v091;; *) run=run-exp-longrun-v092;; esac
  out=$A/run-exp-audit195/x2-stays-v1/$game-t$turn-$nation
  [ -e $out ] && continue
  echo "== $game t$turn $nation"
  python3 runs/experiments/audit195/x2_mode_probe.py $A/$run/$game $turn $out --seeds $((12345+turn)),12345,99 --nation $nation 2>&1 | tail -6
done <<'LIST'
rome-rulebot1-40t 10 Macedonia
carthage-rulebot1-40t 21 Seleucid
carthage-rulebot1-40t 33 Ptolemaic
carthage-rulebot1-40t 35 Ptolemaic
gaul-rulebot1-40t 29 Seleucid
gaul-rulebot1-40t 40 Carthage
ptolemaic-rulebot1-40t 9 Rome
numidia-rulebot1-40t 6 Media
numidia-rulebot1-40t 11 Media
numidia-rulebot1-40t 11 Seleucid
greece-rulebot1-40t 6 Carthage
LIST
