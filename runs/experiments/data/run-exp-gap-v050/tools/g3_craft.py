#!/usr/bin/env python3
"""Craft edited copies of a remake CLI save (JSON) for the g3 turn-cycle probes. Usage: g3_craft.py <src.sav> <dst.sav> key=value ...
keys: nation.<id>.<field>=<json>, city.<id>.<field>=<json>, cal.<field>=<json>, allcities=<nation>, army.<id>.<field>=<json>, unit.<army>.<idx>.<field>=<json>
Writes only to the git-ignored artifacts dir (the remake clone is never touched)."""
import json, sys
src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src)); s = d['save']['state']
for kv in sys.argv[3:]:
    k, v = kv.split('=', 1) if '=' in kv else (kv, ''); v = json.loads(v) if v else v
    p = k.split('.')
    if p[0] == 'nation':
        n = [x for x in s['nations'] if x['id'] == p[1]][0]; n[p[2]] = v
    elif p[0] == 'city':
        c = [x for x in s['cities'] if x['id'] == p[1]][0]; c[p[2]] = v
    elif p[0] == 'cal':
        s['calendar'][p[1]] = v
    elif p[0] == 'allcities':
        for c in s['cities']: c['owner'] = v
    elif p[0] == 'onlyarmies':
        s['armies'] = [a for a in s['armies'] if a['nation'] == p[1]]; s['fleets'] = [f for f in s['fleets'] if f['nation'] == p[1]]
    elif p[0] == 'rel':
        ids = s['relations']['nationIds']; i, j = ids.index(p[1]), ids.index(p[2]); s['relations']['matrix'][i][j] = v; s['relations']['matrix'][j][i] = v
    elif p[0] == 'giveaway':
        # giveaway.<from>.<to>.<city,city,...>  (value ignored): hands the named cities over
        for c in s['cities']:
            if c['owner'] == p[1] and c['id'] in p[3].split(','): c['owner'] = p[2]
    elif p[0] == 'army':
        a = [x for x in s['armies'] if x['id'] == p[1]][0]; a[p[2]] = v
    elif p[0] == 'unit':
        a = [x for x in s['armies'] if x['id'] == p[1]][0]; a['units'][int(p[2])][p[3]] = v
    else: raise SystemExit('bad key ' + k)
json.dump(d, open(dst, 'w'))
print('wrote', dst)
