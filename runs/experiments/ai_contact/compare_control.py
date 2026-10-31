"""Compare this experiment's control snapshots with the ai-turn run's tracked snapshots (same
seed 424242, Rome idle): the saves' parsed content must match turn for turn for the contact
plays to build on the same deterministic base. Writes the comparison table to the tracked data
dir (rule 6). Usage: compare_control.py"""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from common import write_new
from paths import DATA

AI_TURN = os.environ.get('AI_TURN_TURNS', '/tmp/ai-turn-intake/runs/experiments/data/run-exp-ai-turn/turns')   # the ai-turn run's tracked snapshots (branch experiment/ai-turn of ic2-conquest; the saves are release-verified)

KEYS = ('week', 'season', 'year_bc', 'current')


def skel(s):
    return {'nations': [{k: n[k] for k in ('name', 'tax', 'unity', 'treasury', 'wealth', 'cities_count')}
                         for n in s['nations']],
            'armies': [{k: a[k] for k in ('owner', 'x', 'y', 'moves', 'supplies', 'money', 'troops')}
                       for a in s['armies']],
            'mercenaries': s['mercenaries']}


rows = []
for f in sorted(glob.glob(DATA + 'turns/AUTO*.SAV.json')):
    if '.v2.' in f:
        continue
    name = os.path.basename(f)
    other = os.path.join(AI_TURN, name)
    if not os.path.exists(other):
        rows.append((name, 'no ai-turn counterpart', ''))
        continue
    a, b = json.load(open(f)), json.load(open(other))
    same = all(a.get(k) == b.get(k) for k in KEYS) and skel(a) == skel(b)
    rows.append((name, 'content-identical' if same else 'DIFFERS', ''))
    if not same:
        for k in KEYS:
            if a.get(k) != b.get(k):
                print(name, k, a.get(k), b.get(k))
        if skel(a)['armies'] != skel(b)['armies']:
            for x, y in zip(skel(a)['armies'], skel(b)['armies']):
                if x != y:
                    print(name, 'army', x, 'vs', y)
        if skel(a)['nations'] != skel(b)['nations']:
            for x, y in zip(skel(a)['nations'], skel(b)['nations']):
                if x != y:
                    print(name, 'nation', x, 'vs', y)
tbl = '%s\n' % '\n'.join('%-18s %s %s' % r for r in rows)
p = write_new(DATA + 'control_vs_ai_turn.txt', tbl)
print(tbl)
print('->', p)
