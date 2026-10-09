"""Read the map word at each storm-trial fleet's tile in the kept result saves of run-exp-storms.

Usage (repo root, saves from release run-exp-storms in artifacts/run-exp-storms/):
    python3 runs/experiments/data/run-exp-storm-sunk-tile/storm_tiles.py
Writes storm_tiles.json and prints storm_tiles.log lines. Reads only; no game run.
"""
import glob, json, os, struct

A = 'artifacts/run-exp-storms'
HERE = os.path.dirname(os.path.abspath(__file__))


def word(b, x, y):
    return struct.unpack_from('<H', b, x * 280 + y * 2)[0]


rows = json.load(open('runs/experiments/data/run-exp-storms/t4_trials.json'))
same_seed_cover = {}  # (condition-85 cell, seed) -> covered field after, from survivors on the rough tile
TWIN = {'R45s': 'R85s', 'R45sA': 'R85sA', 'R45w': 'R85w'}
for r in rows:
    if r['cell'] in ('R85s', 'R85sA', 'R85w') and r['after']:
        same_seed_cover[(r['cell'], r['seed'])] = r['after'].get('cell')
out = []
for r in rows:
    b4 = r['before']
    x, y = b4['x'], b4['y']
    f = f"{A}/ST_{r['cell']}_seed{r['seed']}_AUTO{r['turn_after']:04d}.SAV"
    if not os.path.exists(f):
        continue
    b = open(f, 'rb').read()
    o = dict(cell=r['cell'], seed=r['seed'], tile=[x, y], covered_before=b4.get('covered'),
             lost=r['after'] is None, word_after=word(b, x, y), save=os.path.basename(f),
             news=r['news'],
             rough_tiles_after=sum(1 for i in range(0, 200 * 280, 2)
                                   if i + 2 <= len(b) and struct.unpack_from('<H', b, i)[0] == 1))
    if r['cell'].startswith('R'):
        o['same_seed_survivor_covered_after'] = same_seed_cover.get((TWIN.get(r['cell']), r['seed']))
    out.append(o)
for f, tile in [('NAT_seed1_11_0726_seat02.SAV', (164, 66)), ('NAT_seed1_13_0727_seat02.SAV', (164, 66))]:
    b = open(f'{A}/{f}', 'rb').read()
    out.append(dict(cell='natural', seed=1, tile=list(tile), save=f, word_after=word(b, *tile)))
json.dump(out, open(os.path.join(HERE, 'storm_tiles.json'), 'w'), indent=1)
for o in out:
    print(o['cell'], o['seed'], tuple(o['tile']), 'covered', o.get('covered_before'),
          {True: 'LOST', False: 'kept'}.get(o.get('lost'), 'natural'), 'word', o['word_after'],
          'survivor-cover', o.get('same_seed_survivor_covered_after', '-'), o['save'])
