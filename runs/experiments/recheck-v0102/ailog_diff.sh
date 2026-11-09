#!/bin/bash
# usage: ailog_diff.sh <campaign rel> <turn> <nation lower>
S=/tmp/claude-1000/-home-diego-projects-ic2-conquest/35bcd764-7222-43db-8d6f-c64a8bfa1c98/scratchpad
C=$HOME/projects/ic2-conquest/artifacts/$1; k=$2; n=$3; tag=$(basename $1)-t$k
for P in 168dbc04 d4a12c21; do
  [ -d $S/ad/$tag-$P ] || IC2_REMAKE=$HOME/projects/ic2-remake-pin-$P IC2_DIFF_BUILD=$HOME/projects/ic2-conquest/artifacts/diffpin-$P-ailog-build python3 -I $S/ailog_turn.py $C $k $S/ad/$tag-$P >/dev/null 2>&1
  python3 -c "
import json,sys
for l in open('$S/ad/$tag-$P/s$((12345+k))/receipt.jsonl'):
  r=json.loads(l)
  if r.get('kind')=='ai' and r['nation']=='$n':
    for x in r['lines']: print(x[:170])
" > $S/ad/$tag-$P.$n.txt
done
diff $S/ad/$tag-168dbc04.$n.txt $S/ad/$tag-d4a12c21.$n.txt
