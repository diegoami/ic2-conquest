"""Private exact projections for original/native gate/comparison. Never overwrite."""
from original import *
import argparse
p=argparse.ArgumentParser();p.add_argument('--version',required=True);q=p.parse_args()
world=json.load(open(R/'artifacts/run-exp-restrictions85/remake4d70275a/data/worlds/classical-mediterranean.json'));owners=[n['id']for n in world['nations']]
def army(a):return [owners[a['owner']],a['x'],a['y'],a['moves'],a['morale'],a['money'],a['supplies'],a['embarked'],None if a['embarked']else a['cell'],[[u['merc'],sav.UNIT_TYPES.index(u['type']),u['troops'],u['quality'],u['name']]for u in a['units']]]
def shape(s):
 live={a['id']:army(a)for a in s['armies']if a['owner']>=0 and a['troops']>0}
 armies=sorted(live.values(),key=lambda x:json.dumps(x,separators=(',',':'),ensure_ascii=False))
 fleets=[[owners[f['owner']],f['x'],f['y'],f['moves'],f['ships'],f['condition'],f['money'],f['supplies'],live.get(f['army'])]for f in s['fleets']if f['owner']>=0 and not f['building']]
 cities=[[c['x'],c['y'],c['owner'],c['allegiance'],c['loyalty'],c['supplies'],c['fort']+100*c['fort_pending'],c['pop'],c['max_pop'],c['tribute'],c['name']]for c in s['cities']]
 nations=[[n['treasury'],n['wealth'],n['unity'],n['mobilization'],n['human']]for n in s['nations']]
 return dict(armies=armies,fleets=fleets,cities=cities,nations=nations)
for spec in json.load(open(D/(q.version+'-plan.json'))):
 folder=A/('private-'+q.version)/spec['id']
 for phase in ['before','expected']:write(folder/(phase+'-shape-v2.json'),shape(json.load(open(folder/(phase+'.json')))))
print('private projections written')
