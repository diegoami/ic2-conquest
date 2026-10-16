"""Matched synthetic same/cross-region AI field targets, plain and observed builds.

All AI decisions execute in the original under Wine. Artificial land corridors,
army composition, moves and human-seat flags are declared staging, not natural
play. The observer reads scorer outputs without changing its inputs or results.
"""
from probe_common import *
from supply_probe import SOURCE,prepare
import score_hook as H


def edit(b,case):
    description=prepare(b,'army',{'aboard':False})
    state=sav.parse(b)
    # Suppress unrelated deliveries and free hires rather than infer matched
    # decision-time strengths from the staged starting records alone.
    for k in range(40):
        struct.pack_into('<h',b,stage._nation(b,0)+0x2e8+8*k,0)
    na=len(state['armies']);nf=len(state['fleets'])
    merc_off=sav.ARMY_OFF+2+na*sav.ARMY_LEN+2+nf*sav.FLEET_LEN+16*sav.NATION_LEN
    for k in range(50):struct.pack_into('<h',b,merc_off+12*k+8,-1)
    for a in state['armies']:
        if a['cell']>=0:
            struct.pack_into('<h',b,(a['x']*140+a['y'])*2,a['cell'])
        if a['id']>2:stage.set_army_field(b,a['id'],'owner',-1)
    if case=='boundary':
        positions=[(60,57),(58,57),(62,57)]
    elif case=='same_only':
        positions=[(59,57),(62,57),(56,57)]
    elif case=='cross_only':
        positions=[(59,57),(56,57),(62,57)]
    elif case=='fallback_same':
        positions=[(158,72),(161,72),(155,72)]
    elif case=='fallback_cross':
        positions=[(158,72),(155,72),(161,72)]
    elif case=='same_left':
        positions=[(59,57),(62,57),(56,57)]
    else:
        positions=[(59,57),(56,57),(62,57)]
    xmin,xmax=min(p[0] for p in positions)-2,max(p[0] for p in positions)+2
    ymin,ymax=min(p[1] for p in positions)-2,max(p[1] for p in positions)+2
    for x in range(xmin,xmax+1):
        for y in range(ymin,ymax+1):struct.pack_into('<h',b,(x*140+y)*2,2)
    for i,(x,y) in enumerate(positions):
        stage.set_units(b,i,[('li',30000,6)])
        for field,value in dict(owner=0 if i==0 else 1,moves=1 if i==0 else 0,
                                supplies=300,money=500,morale=90).items():
            stage.set_army_field(b,i,field,value)
        struct.pack_into('<2h',b,stage._army(b,i),x,y)
        struct.pack_into('<h',b,stage._army(b,i)+8,2)
        struct.pack_into('<h',b,(x*140+y)*2,200+i)
    if case in ('same_only','cross_only','fallback_same','fallback_cross'):
        stage.set_army_field(b,2,'owner',-1)
        x,y=positions[2]
        struct.pack_into('<h',b,(x*140+y)*2,2)
    stage.set_relation(b,0,1,3)
    description.update(case=case,positions=positions,synthetic_plain_corridor=[xmin,xmax,ymin,ymax],
                       armies_above_slot2_removed=True,army0_moves=1,enemy_stats='matched to army0',
                       rome_queue_troops_zero=True,all_mercenary_pool_troops=-1,
                       slot2_removed=case in ('same_only','cross_only','fallback_same','fallback_cross'))
    return description


for case in sys.argv[1:]:
    src=staged(SOURCE,'reg_'+case,lambda b:edit(b,case))
    for mode in ('plain','observed'):
        g=PrivateGame(exe=drv.EXE if mode=='plain' else H.DST,
                      log=lambda text:log('driver',case=case,mode=mode,message=text))
        try:
            g.load(src,seed=12345)
            before=snapshot(g)
            log('region_before',case=case,mode=mode,input=src.name,snapshot=before,
                exe=g.exe,exe_sha256=sha(drv.G/g.exe))
            auto,texts=g.end_turn(timeout=180,reclick=False)
            after=snapshot(g)
            auto_kept=keep(drv.G/auto,f'reg_{case}_{mode}-{STAMP}-{auto}')
            post=keep(g.save_as(f'r16_{case}_{mode}_{os.getpid()}.SAV'),f'reg_{case}_{mode}-{STAMP}-post.SAV')
            scores=H.read(g) if mode=='observed' else []
            log('region_after',case=case,mode=mode,input=src.name,autosave=auto_kept.name,
                post=post.name,snapshot=after,scores=scores,texts=texts)
            assert after['current']==11 and before['turn']==after['turn']
        except BaseException as exc:
            log('failure',case=case,mode=mode,exception=repr(exc))
            raise
        finally:g.kill()
