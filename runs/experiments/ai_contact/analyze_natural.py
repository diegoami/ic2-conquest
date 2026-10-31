"""Extract the natural contact evidence from the control saves (seed 424242, Rome idle):
(1) the AI-mover-vs-human-army contact of 0721->0722 (Gaul v Rome: battle screen at Rome's
defence, Gaul's army destroyed, purse absorbed) with both army records before/after;
(2) every city whose owner or population moved between consecutive saves (the AI siege path,
FUN_0044b27c) with the army standing on the city tile, plus the failed sieges' army losses.
Reads the artifacts saves and the tracked snapshots; writes natural_evidence.txt (rule 6).
Usage: analyze_natural.py"""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..'))
from common import write_new
from paths import ART, DATA
from state.sav import parse as parse_sav, NATIONS

out = []
order = sorted(os.path.basename(p) for p in glob.glob(ART + 'AUTO*.SAV'))
sv = {n: parse_sav(open(ART + n, 'rb').read()) for n in order}
sn = {n: json.load(open(DATA + 'turns/' + n + '.json')) for n in order if os.path.exists(DATA + 'turns/' + n + '.json')}


def army_rows(s, owner_name):
    return [a for a in s['armies'] if NATIONS[a['owner']] == owner_name]


def fmt(a):
    return 'id%d (%d,%d) moves %d sup %d money %d troops %d morale %d' % (
        a['id'], a['x'], a['y'], a['moves'], a['supplies'], a['money'], a['troops'], a['morale'])


out.append('# Natural contact evidence, control run (seed 424242, Rome idle)')
out.append('# saves: ' + ', '.join(order))
for a, b in zip(order, order[1:]):
    A, B = sv[a], sv[b]
    # city changes
    for ca, cb in zip(A['cities'], B['cities']):
        moved = {k: (ca[k], cb[k]) for k in ('owner', 'allegiance', 'loyalty', 'fort', 'pop', 'supplies')
                 if ca[k] != cb[k]}
        if 'owner' in moved or ('pop' in moved and abs(moved['pop'][1] - moved['pop'][0]) > 200):
            out.append('%s->%s CITY %s (%d,%d): %s' % (a, b, ca['name'], ca['x'], ca['y'],
                        ' '.join('%s %s->%s' % (k, v[0], v[1]) for k, v in moved.items())))
            stand = [f for f in B['armies'] if (f['x'], f['y']) == (ca['x'], ca['y'])]
            out.append('   armies on the tile after: ' + ('; '.join(NATIONS[f['owner']] + ' ' + fmt(f) for f in stand) or 'none'))
    # armies destroyed or created
    idsA = {f['id']: f for f in A['armies']}
    idsB = {f['id']: f for f in B['armies']}
    for i, f in idsA.items():
        if i not in idsB:
            out.append('%s->%s ARMY GONE %s %s' % (a, b, NATIONS[f['owner']], fmt(f)))
    for i, f in idsB.items():
        if i not in idsA:
            out.append('%s->%s ARMY NEW  %s %s' % (a, b, NATIONS[f['owner']], fmt(f)))
    # the Rome/Gaul pair around the 0722 battle
    if (a, b) == ('AUTO0721.SAV', 'AUTO0722.SAV'):
        out.append('%s->%s Rome armies before: %s' % (a, b, [fmt(f) for f in army_rows(A, 'Rome')]))
        out.append('%s->%s Rome armies after:  %s' % (a, b, [fmt(f) for f in army_rows(B, 'Rome')]))
        out.append('%s->%s Gaul armies before: %s' % (a, b, [fmt(f) for f in army_rows(A, 'Gaul')]))
        out.append('%s->%s Gaul armies after:  %s' % (a, b, [fmt(f) for f in army_rows(B, 'Gaul')]))
    # battles/news of the turn
    tt = sn.get(b, {}).get('turn_texts')
    if tt:
        out.append('%s->%s turn_texts: %s' % (a, b, tt))

p = write_new(DATA + 'natural_evidence.txt', '\n'.join(out) + '\n')
print('\n'.join(out))
print('->', p)
