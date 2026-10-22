"""Matched L1-staged, unmodified-seed-exe AI resupply probes. One AI seat only.

Run with explicit private IC2_WORK/DISPLAY_IC2; every case saves before/after.
No measured save is deleted or overwritten. Unique stamp includes PID.
"""
from probe_common import *

SOURCE = ROOT / 'saves/fleet-port-antium-0734.SAV'
FLEET_OFF = {'x':0,'y':2,'dest_x':4,'dest_y':6,'owner':8,'countdown':10,
             'moves':12,'supplies':14,'money':16,'ships':18,'condition':20,'army':22,'cell':24}


def fleet_set(b, i, **fields):
    na = struct.unpack_from('<h', b, sav.ARMY_OFF)[0]
    base = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN + 2 + i * sav.FLEET_LEN
    for key,value in fields.items():
        struct.pack_into('<h', b, base + FLEET_OFF[key], value)


def prepare(b, kind, config):
    s = sav.parse(b)
    # Current seat Armenia -> only Rome AI -> Bithynia human, without a weekly tick.
    for n in range(16):
        b[stage._nation(b,n) + 0x490] = int(n != 0)
        stage.set_relation(b,0,n,0)
    tail = s['tail_off']
    struct.pack_into('<2h',b,tail+32,-1,-1)
    struct.pack_into('<2h',b,tail+36,13,10)
    # Zero moves prevents target movement. 30,000 troops prevents small-army merging.
    stage.set_units(b,0,[('li',30000,6)])
    # Other Rome armies in this fixture also visit Antium. Tombstone them and
    # restore their covered map cells; normal original compaction removes them.
    removed=[]
    for a in s['armies']:
        if a['owner']==0 and a['id']!=0:
            stage.set_army_field(b,a['id'],'owner',-1)
            if a['cell']>=0:
                struct.pack_into('<h',b,(a['x']*140+a['y'])*2,a['cell'])
            removed.append(a['id'])
    for field,value in dict(moves=0,supplies=50,money=500,morale=90).items():
        stage.set_army_field(b,0,field,value)
    for c in range(334):
        stage.set_city(b,c,{'supplies':0})
    stage.set_city(b,89,{'supplies':config.get('stock',330)})
    treasury = config.get('treasury',1000)
    struct.pack_into('<i',b,stage._nation(b,0)+0x438,treasury)
    # The existing Rome fleet at Antium is index 2, source ships=30.
    fleet_set(b,2,dest_x=-1,dest_y=-1,moves=0,supplies=720,money=100,ships=90,condition=100,army=-1)
    if kind == 'army':
        aboard = config.get('aboard',True)
        x,y = (101,46) if aboard else (101,45)
        if config.get('distance') is not None:
            x,y = 102-config['distance'],46
            fleet_set(b,2,x=x,y=y)
        army = stage._army(b,0)
        oldx,oldy = s['armies'][0]['x'],s['armies'][0]['y']
        struct.pack_into('<h',b,(oldx*140+oldy)*2,s['armies'][0]['cell'])
        struct.pack_into('<2h',b,army,x,y)
        struct.pack_into('<h',b,army+8,-1 if aboard else 2)
        if not aboard:
            struct.pack_into('<h',b,(x*140+y)*2,200)
        fleet_set(b,2,army=0 if aboard else -1)
        stage.set_army_field(b,0,'money',config.get('money',500))
        if config.get('hostile'):
            stage.set_city(b,89,{'owner':1})
            stage.set_relation(b,0,1,3)
        if config.get('repeat'):
            # Named synthetic second own city within distance 4, visited before Antium.
            c=88; o=sav.CITY_OFF+c*sav.CITY_LEN
            struct.pack_into('<2h',b,o+14,x+1,y+1)
            stage.set_city(b,c,{'owner':0,'supplies':330})
        return dict(kind=kind,config=config,subject_army=0,carrier_fleet=2,city=89,
                    all_other_city_stocks=0,ai_seat=0,current_seat=13,next_human=11,
                    source_army_units_replaced=True,subject_moves=0,other_rome_armies_removed=removed)
    for field,value in config.items():
        if field in ('money','condition','supplies','ships'):
            fleet_set(b,2,**{field:value})
    # Army is full and purse normalized, so its visit cannot consume stock or money.
    stage.set_army_field(b,0,'supplies',300)
    if 'distance' in config:
        old = s['fleets'][2]
        struct.pack_into('<h',b,(old['x']*140+old['y'])*2,old['cell'])
        x,y=(102,46+config['distance']) if config.get('axis')=='y' else (102-config['distance'],46)
        fleet_set(b,2,x=x,y=y,cell=0)
        struct.pack_into('<h',b,(x*140+y)*2,302)
    if config.get('hostile'):
        stage.set_city(b,89,{'owner':1})
        stage.set_relation(b,0,1,3)
    if config.get('repeat'):
        stage.set_city(b,85,{'supplies':50}) # Rome, city 85, distance 3, visited before Antium
    return dict(kind=kind,config=config,subject_fleet=2,city=89,ai_seat=0,
                current_seat=13,next_human=11,army_supplies_at_capacity=True,subject_moves=0,
                other_rome_armies_removed=removed)


CASES = {
    'aboard':('army',{}), 'land':('army',{'aboard':False}),
    'a_dist4':('army',{'distance':4}), 'a_dist5':('army',{'distance':5}),
    'a_hostile':('army',{'hostile':True}), 'a_empty':('army',{'stock':0}),
    'a_repeat':('army',{'money':0,'repeat':True}),
    'a_positive':('army',{'money':0,'treasury':1}),
    'a_zero':('army',{'money':0,'treasury':0}),
    'f99t101':('fleet',{'money':99,'treasury':101,'supplies':50}),
    'f99t100':('fleet',{'money':99,'treasury':100,'supplies':50}),
    'f100t101':('fleet',{'money':100,'treasury':101,'supplies':50}),
    'f101t101':('fleet',{'money':101,'treasury':101,'supplies':50}),
    'f0t101':('fleet',{'money':0,'treasury':101,'supplies':50}),
    'f94':('fleet',{'money':100,'treasury':1,'condition':94,'supplies':50}),
    'f95':('fleet',{'money':100,'treasury':1,'condition':95,'supplies':50}),
    'f96':('fleet',{'money':100,'treasury':1,'condition':96,'supplies':50}),
    'f_dist3':('fleet',{'money':99,'treasury':101,'supplies':50,'distance':3}),
    'f_dist4':('fleet',{'money':99,'treasury':101,'supplies':50,'distance':4}),
    'f_hostile':('fleet',{'money':99,'treasury':101,'supplies':50,'hostile':True}),
    'f_cap':('fleet',{'money':100,'treasury':101,'supplies':700}),
    'f_empty':('fleet',{'money':100,'treasury':101,'supplies':50,'stock':0}),
    'f_y3':('fleet',{'money':99,'treasury':101,'supplies':50,'distance':3,'axis':'y'}),
    'f_y4':('fleet',{'money':99,'treasury':101,'supplies':50,'distance':4,'axis':'y'}),
    'f94t101':('fleet',{'money':100,'treasury':101,'condition':94,'supplies':50}),
    'f94grant':('fleet',{'money':99,'treasury':101,'condition':94,'supplies':50}),
    'f94s91':('fleet',{'money':100,'treasury':1,'condition':94,'supplies':50,'ships':91}),
    'f_repeat':('fleet',{'money':99,'treasury':101,'condition':94,'supplies':50,'stock':50,'repeat':True}),
}


def delta(before,after):
    out={}
    for table,idx in (('armies',0),('fleets',2),('cities',89),('nations',0)):
        a,b=before[table][idx],after[table][idx]
        out[f'{table}/{idx}']={k:[a[k],b[k]] for k in a if a[k]!=b[k]}
    out['cities_changed']=[dict(id=a['id'],before=a,after=b) for a,b in zip(before['cities'],after['cities']) if a!=b]
    return out


if __name__ == '__main__':
    for index,name in enumerate(sys.argv[1:]):
        kind,config=CASES[name]
        src=staged(SOURCE,name,lambda b:prepare(b,kind,config))
        g=PrivateGame(log=lambda text:log('driver',case=name,message=text))
        try:
            g.load(src,seed=12345)
            before=snapshot(g)
            log('before',case=name,save=src.name,snapshot=before,exe=g.exe,exe_sha256=sha(drv.G/g.exe))
            assert before['current']==13 and before['armies'][0]['moves']==0
            auto,texts=g.end_turn(timeout=180)
            after=snapshot(g)
            kept=keep(drv.G/auto,f'{name}-{STAMP}-{auto}')
            manual=g.save_as(f'o16_{name}_{os.getpid()}_{index}.SAV')
            post=keep(manual,f'{name}-{STAMP}-post.SAV')
            log('after',case=name,input=src.name,autosave=kept.name,post=post.name,
                snapshot=after,deltas=delta(before,after),texts=texts)
            assert after['current']==11 and after['turn']==before['turn'], 'AI interval included an unexpected seat/tick'
        except BaseException as exc:
            log('failure',case=name,exception=repr(exc),windows=g.find_windows() if g.pid else [])
            raise
        finally:
            g.kill()
