"""Serial broad original-game cases. Every failed case is retained and named.

Default unmodified original; instrumented original only for end-turn/combat
continuation. No overwrite, no blind retries, no owner prefix/process touched.
"""
import copy,hashlib,json,os,shutil,subprocess,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
ART=ROOT/'artifacts/run-exp-sav-conversion-broad153'
os.environ['IC2_WORK']=str(ART/'runtime');os.environ['DISPLAY_IC2']=':153'
sys.path.insert(0,str(ROOT))
from harness.driver import Game,G,CUR_NATION,ENV,WINE
from harness import environment
from state import sav
environment.set_data_folder(HERE)
display=None

class IsolatedGame(Game):
    def ensure_xvfb(self):
        global display
        if subprocess.run(['xdpyinfo','-display',':153'],capture_output=True).returncode:
            display=subprocess.Popen(['Xvfb',':153','-screen','0','1280x1024x24'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            time.sleep(2)
            if display.poll()!=None:raise RuntimeError('Private display failed')

def action(g,p):
    kind=p['kind']
    if kind=='move':return g.move(p['army'],p['x'],p['y'])
    if kind=='tax':return g.taxation(p['value'])
    if kind=='split-army':return g.split_army(p['army'],tuple(p.get('units',[0])))
    if kind=='join-armies':return g.join(p['army'])
    if kind=='transfer-units':return g.transfer_units(p['army'],p.get('unit',0))
    if kind=='rename-unit':return g.rename_unit(p['army'],p.get('unit',0),p['text'])
    if kind=='split-unit':return g.split_unit(p['army'],p.get('unit',0),hundreds=p.get('hundreds',10))
    if kind=='join-units':return g.join_units(p['army'],p.get('units',[0,1]))
    if kind=='disband-army':return g.disband_army(p['army'])
    if kind=='disband-regular':return g.change_units_disband(p['army'],p.get('unit',0))
    if kind=='supply':
        g.army_tool(p['army'],'supply','Supply army');cs=g.controls('Supply army')
        spins=sorted((c for c in cs if c['cls']=='TUpDown'),key=lambda c:(c['y'],c['x']))
        for _ in range((p.get('tons',10)+9)//10):g.click_control(spins[0],fy=.25,pause=.2)
        for _ in range(abs(p.get('money_100s',0))):g.click_control(spins[-1],fy=.25 if p['money_100s']>0 else .75,pause=.2)
        g.click_control(g.control(cs,text='OK'),pause=.6)
        g.wait(lambda:not g.find_windows('^Supply army$'),10,'Supply army closed')
        return {'control_based_supply':True,'controls':cs,'messages':g.dismiss_popups()}
    if kind=='mercenary':return g.hire_mercs(p['army'],rows=(p.get('row',0),))
    if kind=='move-fleet':return g.move_fleet(p['fleet'],p['x'],p['y'])
    if kind=='repair-fleet':return g.repair_fleet(p['fleet'],p.get('points',3))
    if kind=='split-fleet':return g.split_fleet(p['fleet'],p.get('ships',10))
    if kind=='join-fleets':return g.join_fleets(p['fleet'])
    if kind=='transfer-ships':return g.transfer_ships(p['fleet'],p.get('ships',5))
    if kind=='scuttle':return g.scuttle_fleet(p['fleet'])
    if kind=='supply-fleet':return g.supply_fleet(p['fleet'],tons=p.get('tons',100),money=p.get('money',0))
    if kind=='embark':return g.embark(p['army'],p['fleet'])
    if kind=='disembark':return g.disembark(p['fleet'],p['x'],p['y'])
    if kind=='relation':return g.relation(p['nation'],p['relation'])
    if kind=='fortify':return g.fortify(p['city'],p['x'],p['y'],p.get('points',1))
    if kind in ('recruit','mobilize','disband-slot'):
        # Resolve actual list text; All cities can be inserted and city rows vary.
        g.open_recruit();cs=g.controls('Army recruits');control=g.control(cs,cls='TListBox',index=0)
        # win_controls helper emits list items through Wine message queries below.
        # Existing captions are read via the helper's list-text mode when available.
        query=subprocess.run([WINE,str(ART/'runtime/list_items.exe'),'Army recruits',str(control['x'])],env=ENV,capture_output=True,text=True,check=True)
        items=[(int(line.split('\t',1)[0]),line.split('\t',1)[1]) for line in query.stdout.splitlines() if '\t' in line]
        row=next(i for i,text in items if p['city'].casefold()==text.strip().casefold())
        g.close_controls('Army recruits',cs)
        if kind=='recruit':return g.recruit(row,p.get('type','hi'),thousands=p.get('thousands',1))
        if kind=='mobilize':return g.mobilize(row,p.get('units',[0]))
        return g.disband_unit(row,p.get('unit',0))
    if kind=='build-fleet':return g.build_fleet(p.get('ships',10))
    if kind=='siege':return g.attack(p['army'],p['x'],p['y'])
    if kind=='attack-fleet':return g.attack_fleet(p['fleet'],p['enemy'],answer=True)
    if kind=='end-turn':
        g.supersede_autosaves()
        name,texts=g.end_turn(timeout=240,reclick=False,strict_confirm=True)
        return {'autosave':name,'messages':texts}
    if kind=='observe':return {'observation_only':True}
    raise ValueError('Unsupported plan '+kind)

def basic_verify(plan,before,after):
    k=plan['kind'];me=before['current_nation'];a=plan.get('army',0);f=plan.get('fleet',0)
    if plan.get('expect_unchanged'):
        values=[]
        for s in (before,after):
            s=copy.deepcopy(s)
            for key in ('size','tail_off'):s.pop(key,None)
            for nation in s['nations']:nation.pop('view',None)
            values.append(s)
        return values[0]==values[1]
    if k=='move':return (after['armies'][a]['x'],after['armies'][a]['y'])==(plan['x'],plan['y']) and after['armies'][a]['moves']<before['armies'][a]['moves']
    if k=='tax':return after['nations'][me]['tax']==plan['value']
    if k=='end-turn':return after['turn']>before['turn'] or after['current_nation']!=before['current_nation']
    if k=='split-army':return len(after['armies'])>len(before['armies'])
    if k=='mobilize':return sum(x['troops'] for x in after['armies'] if x['owner']==me)>sum(x['troops'] for x in before['armies'] if x['owner']==me) and len(after['nations'][me]['recruit_slots'])<len(before['nations'][me]['recruit_slots'])
    if k=='join-armies':return sum(x['owner']==me for x in after['armies'])<sum(x['owner']==me for x in before['armies'])
    if k=='disband-army':return sum(x['owner']==me for x in after['armies'])<sum(x['owner']==me for x in before['armies'])
    if k=='rename-unit':return after['armies'][a]['units'][plan.get('unit',0)]['name']==plan['text']
    if k=='transfer-units':return len(after['armies'][a]['units'])<len(before['armies'][a]['units'])
    if k=='split-unit':return len(after['armies'][a]['units'])==len(before['armies'][a]['units'])+1 and after['armies'][a]['troops']==before['armies'][a]['troops']
    if k=='join-units':return len(after['armies'][a]['units'])==len(before['armies'][a]['units'])-1 and after['armies'][a]['troops']==before['armies'][a]['troops']
    if k=='supply':return (after['armies'][a]['money']>before['armies'][a]['money']) if plan.get('money_100s',0)>0 else (after['armies'][a]['supplies']>before['armies'][a]['supplies'])
    if k=='mercenary':return len(after['armies'][a]['units'])>len(before['armies'][a]['units'])
    if k=='disband-regular':return len(after['armies'][a]['units'])<len(before['armies'][a]['units'])
    if k=='embark':return after['armies'][a]['embarked'] and after['fleets'][f]['army']==a
    if k=='disembark':return after['fleets'][f]['army']==-1
    if k=='split-fleet':return len(after['fleets'])>len(before['fleets'])
    if k in ('join-fleets','scuttle'):return sum(x['owner']==me for x in after['fleets'])<sum(x['owner']==me for x in before['fleets'])
    if k=='repair-fleet':return after['fleets'][f]['condition']>before['fleets'][f]['condition']
    if k=='move-fleet':return (after['fleets'][f]['x'],after['fleets'][f]['y'])==(plan['x'],plan['y'])
    if k=='supply-fleet':return (after['fleets'][f]['money']>before['fleets'][f]['money']) if plan.get('money',0)>0 else (after['fleets'][f]['supplies']>before['fleets'][f]['supplies'])
    if k=='transfer-ships':return after['fleets'][f]['ships']==before['fleets'][f]['ships']-plan['ships']
    if k=='recruit':return len(after['nations'][me]['recruit_slots'])>len(before['nations'][me]['recruit_slots'])
    if k=='disband-slot':return len(after['nations'][me]['recruit_slots'])<len(before['nations'][me]['recruit_slots'])
    if k=='build-fleet':return len(after['fleets'])>len(before['fleets'])
    if k=='fortify':
        x=next(c for c in before['cities'] if c['name']==plan['city']);y=next(c for c in after['cities'] if c['name']==plan['city'])
        return y['fort_pending']>x['fort_pending']
    if k=='relation':
        value=after['nations'][me]['relations'][sav.NATIONS[plan['nation']]]
        return value<=0 if plan['relation']=='peace' else value=={'trade':1,'ally':2,'war':3}[plan['relation']]
    if k=='observe':return True
    # Full before/after scalar comparison separately establishes precise effects.
    return before!=after

def run_case(case,index,attempt='v1'):
    name=case['name'];receipt=HERE/f'live-{name}-{attempt}.json'
    if receipt.exists():print('PRESERVE existing',name,flush=True);return
    out=ART/f'live-{name}-{attempt}';out.mkdir()
    logpath=HERE/f'live-{name}-{attempt}.txt'
    def log(s):
        with logpath.open('a') as f:f.write(str(s)+'\n')
    def shot(label):
        subprocess.run(['import','-display',':153','-window','root',str(out/(label+'.png'))],capture_output=True)
    result=dict(name=name,case=case,attempt=attempt,complete=False,files={},runtime='Wine/Xvfb')
    save_prefix=f'Q153{index:02d}' if attempt=='v1' else f'Q{index:02d}{attempt.upper()}'
    source=ART/'exports-v1'/(name+'.SAV');g=None
    def archive(path,key):
        dest=out/path.name
        if dest.exists():raise RuntimeError('Refusing existing artifact')
        shutil.copy2(path,dest)
        result['files'][key]=dict(file=str(dest.relative_to(ART)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),bytes=dest.stat().st_size)
        with (HERE/f'live-{name}-{attempt}-progress.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
        return dest
    try:
        result['input_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
        instrumented=case['originalAction']['kind'] in ('end-turn','siege','attack-fleet','field-battle')
        exe='Imperial Conquest 2 fast rollingsave seed.exe' if instrumented else 'Imperial Conquest 2.exe'
        g=IsolatedGame(exe=exe,log=log);result['exe']=exe
        if instrumented:result['load_messages']=g.load(source,seed=12345)
        else:g.start();result['load_messages']=g.open(source,strict=False)
        result['environment']=g.environment
        result['active_nation']=g.i16(CUR_NATION)
        original=sav.load(source)
        if result['active_nation']!=original['current_nation']:raise RuntimeError('Wrong human nation after load')
        immediate=archive(g.save_as(save_prefix+'I.SAV'),'immediate')
        p=case['originalAction']
        if 'load_offer_nation' in p:
            current=sav.load(immediate)
            value=current['nations'][current['current_nation']]['relations'][sav.NATIONS[p['load_offer_nation']]]
            result['offer_processed_on_load']=value==p['load_offer_value']
            if not result['offer_processed_on_load']:raise RuntimeError('Pending offer not accepted on original load')
        result['action_output']=action(g,case['originalAction'])
        changed=archive(g.save_as(save_prefix+'O.SAV'),'order')
        result['action_verified']=basic_verify(case['originalAction'],sav.load(immediate),sav.load(changed))
        if not result['action_verified']:raise RuntimeError('Expected action effect absent')
        if isinstance(result['action_output'],dict) and 'autosave' in result['action_output']:
            archive(G/result['action_output']['autosave'],'autosave')
        shot('after-order')
        if instrumented:result['reopen_messages']=g.load(changed,seed=12345)
        else:g.start();result['reopen_messages']=g.open(changed,strict=False)
        reopened=archive(g.save_as(save_prefix+'R.SAV'),'reopen')
        result['byte_stable_reopen']=changed.read_bytes()==reopened.read_bytes()
        result['complete']=True
    except Exception as e:
        result['error']=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc());log(result['error']['traceback'])
        try:shot('failure')
        except Exception:pass
    finally:
        if g is not None:g.kill()
        result['input_unchanged']=source.exists() and hashlib.sha256(source.read_bytes()).hexdigest()==result.get('input_sha256')
        with receipt.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
        print(name,'complete',result['complete'],'reopen',result.get('byte_stable_reopen'),'error',result.get('error',{}).get('message'),flush=True)

def main():
    try:
        group=sys.argv[1]
        cases=[json.loads(l) for l in (ART/'native-v1/manifest.jsonl').read_text().splitlines()]
        for index,case in enumerate(cases):
            if group!='all' and case['category']!=group:continue
            if not (ART/'exports-v1'/(case['name']+'.SAV')).exists():continue
            print('START',index,case['name'],case['originalAction']['kind'],flush=True)
            run_case(case,index)
    finally:
        if display is not None:display.terminate();display.wait(timeout=10)

if __name__=='__main__':main()
