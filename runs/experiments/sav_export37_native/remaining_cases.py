"""Finite cases2/3 orchestration using original UI; never writes process memory."""
import argparse,hashlib,importlib.util,json,struct,subprocess,time
from pathlib import Path
from case1_actions import action,save_as,DATA,PRIVATE,WIN,ROOT
CASES={2:dict(source='1_thracia_271_spring_1.sav',candidate='t184-tax-thracia-n15-40.SAV',nation=15,old=9,target=40,source_sha='c548b724b2d9988af42d0595436548cd6b29a4021e942f4e61238339f0dc63e3',candidate_sha='2afa2d64170a63fefbf12c5678700a02024f01eb0f682a0cbc7efffa63b7288f'),3:dict(source='1_rome_270_winter_7.sav',candidate='t184-tax-rome-n0-30.SAV',nation=0,old=20,target=30,source_sha='7979e22ac6971eedd36c889da08b9b1af27fd4661945f1ce58eaa9b72029bf9a',candidate_sha='5d82f47aa77f2736afddeac8c23754305455afa7e524636b98d12b4c2a88669a')}
SOURCE=Path('/mnt/c/Users/diego/projects/imperial_conquest_2/rendered/v061-test-fixtures/saves');CAND=Path('/mnt/c/Users/diego/projects/imperial_conquest_2/rendered/sav-export-candidates/bound-original-tax-only')
def record(label,data):
 with (DATA/(label+'.json')).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
def rows(pid,label):return action(pid,'enumerate',label)
def top(w,cls):return next(r['handle'] for r in w if r['cls']==cls and r['visible'])
def button(w,text):return next(r['handle'] for r in w if r['cls'] in ('Button','TButton') and r['text']==text and r['visible'])
def launch(label):
 cmd=[__import__('sys').executable,str(Path(__file__).with_name('windows_bridge.py')),'--action','launch','--output',str(DATA/(label+'.json'))];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 return json.loads(json.loads((DATA/(label+'.json')).read_text())['stdout'])['pid']
def transport(source,name,digest,label):
 raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
 with (PRIVATE/name).open('xb') as f:f.write(raw)
 assert hashlib.sha256((PRIVATE/name).read_bytes()).hexdigest()==hashlib.sha256(source.read_bytes()).hexdigest()==digest
 record(label,dict(source_name=source.name,private_transport_name=name,sha256=digest,source_unchanged=True,byte_identical_transport_not_export=True))
def open_file(pid,name,prefix):
 w=rows(pid,prefix+'-initial-windows');main=top(w,'TPremierForm');action(pid,'command',prefix+'-open-command',main,3);w=rows(pid,prefix+'-open-dialog')
 edit=next(r['handle'] for r in w if r['cls']=='Edit' and r['id']==1152 and r['visible']);ok=next(r['handle'] for r in w if r['cls']=='Button' and r['id']==1 and r['visible'])
 action(pid,'text',prefix+'-open-path',edit,WIN+name);action(pid,'click',prefix+'-open-confirm',ok);w=rows(pid,prefix+'-loaded-windows');assert not any(r['visible'] and r['cls']=='#32770' for r in w)
 return main,w
def capture(pid,hwnd,png,label):return action(pid,'capture',label,hwnd,WIN+png)
def close(pid,main,prefix,png):
 action(pid,'message',prefix+'-request',main,'0x10,0,0');w=rows(pid,prefix+'-dialog');dialog=top(w,'TMessageForm');assert next(r for r in w if r['handle']==dialog)['text']=='Confirm';capture(pid,dialog,png,prefix+'-capture');action(pid,'click',prefix+'-yes',button(w,'&Yes'))
 ps='/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe';r=subprocess.run([ps,'-NoProfile','-NonInteractive','-Command',"@{count=@(Get-Process | Where-Object {$_.ProcessName -like '*Conquest*'}).Count}|ConvertTo-Json -Compress"],capture_output=True,text=True);d=json.loads(r.stdout);record(prefix+'-processes',d);assert d['count']==0

def layout(b):
 na=struct.unpack_from('<h',b,100956)[0];fo=100958+na*656;nf=struct.unpack_from('<h',b,fo)[0];no=fo+2+nf*26;news=no+16*1172+600;last=struct.unpack_from('<h',b,news)[0];tail=news+2+(last+1)*61;assert len(b)==tail+55 and b[tail+54]==0
 return na,nf,no,last,tail

def compare_control(case,c):
 before=(PRIVATE/f'C{case}B68B2.SAV').read_bytes();after=(PRIVATE/f'C{case}T68B2.SAV').read_bytes();na,nf,no,last,tail=layout(before);assert layout(after)==(na,nf,no,last,tail);n=c['nation'];taxoff=no+n*1172+0x44a
 diffs=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b];allowed=set(range(taxoff,taxoff+2))|set(range(no+n*1172+0x46e,no+n*1172+0x48a))|set(range(tail+46,tail+54));assert set(diffs)<=allowed
 assert struct.unpack_from('<h',before,taxoff)[0]==c['old'] and struct.unpack_from('<h',after,taxoff)[0]==c['target']
 geom=[]
 names={0x46e:'area_left',0x470:'area_top',0x472:'area_height',0x474:'area_width',0x476:'unit_left',0x478:'unit_top',0x47a:'unit_height',0x47c:'unit_width',0x47e:'info_left',0x480:'info_top',0x482:'info_height',0x484:'info_width',0x486:'viewport_y',0x488:'viewport_x'}
 for o,name in names.items():
  a=struct.unpack_from('<h',before,no+n*1172+o)[0];b=struct.unpack_from('<h',after,no+n*1172+o)[0]
  if a!=b:geom.append(dict(field=name,before=a,after=b,offset=no+n*1172+o))
 result=dict(case=case,source_tax=c['old'],target_tax=c['target'],before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),changed_offsets=diffs,UI_geometry_changes=geom,no_extra_gameplay_changes=True,internal_callback_trace='UNVERIFIED; actual UI/scalar/save observations only')
 record(f'control{case}-comparison-v1',result);print(json.dumps(result),flush=True)

def control(case,c):
 prefix=f'control{case}';transport(SOURCE/c['source'],f'C{case}I68B2.SAV',c['source_sha'],prefix+'-input-transport-v1');pid=launch(prefix+'-launch-v1');main,w=open_file(pid,f'C{case}I68B2.SAV',prefix+'-source-v1');s=action(pid,'snapshot',prefix+'-before-scalars-v1');assert s['current']==c['nation'] and s['tax']==c['old'] and s['offer_source']==-1 and s['selected_army']==s['selected_fleet']==s['selected_cell_x']==-1
 save_as(pid,main,f'C{case}B68B2.SAV',prefix+'-baseline-save-v1');action(pid,'command',prefix+'-tax-command-v1',main,15);w=rows(pid,prefix+'-tax-dialog-v1');dialog=top(w,'TChangeTax');track=top(w,'TTrackBar');capture(pid,dialog,f'C{case}TX01.PNG',prefix+'-tax-before-capture-v1')
 # Real trackbar keyboard events invoke its original UI change handler; no memory patch.
 keys=[0x23] if c['target']==40 else [0x24]+[0x22]*6
 for i,key in enumerate(keys):
  action(pid,'message',prefix+f'-track-key{i}-down-v1',track,f'0x100,{key},0');action(pid,'message',prefix+f'-track-key{i}-up-v1',track,f'0x101,{key},0')
 q=action(pid,'query',prefix+'-track-position-v1',track,'0x400');assert q['value']==c['target'],q
 capture(pid,dialog,f'C{case}TX02.PNG',prefix+'-tax-target-capture-v1');action(pid,'click',prefix+'-tax-ok-v1',button(w,'OK'));w=rows(pid,prefix+'-tax-closed-windows-v1');assert not any(r['cls']=='TChangeTax' and r['visible'] for r in w)
 s=action(pid,'snapshot',prefix+'-after-scalars-v1');assert s['current']==c['nation'] and s['tax']==c['target'];save_as(pid,main,f'C{case}T68B2.SAV',prefix+'-tax-save-v1');compare_control(case,c);close(pid,main,prefix+'-normal-close-v1',f'C{case}EX01.PNG')
 record(prefix+'-result-v1',dict(case=case,reference_control_UI_tax_change_observed=True,ordinary_original_tax_control=True,source_unchanged=hashlib.sha256((SOURCE/c['source']).read_bytes()).hexdigest()==c['source_sha'],candidate_sequence_completed=False,original_process_closed_normally=True))
 print('CONTROL COMPLETE '+str(case),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',type=int,choices=(2,3),required=True);p.add_argument('--phase',choices=('control',),required=True);a=p.parse_args();control(a.case,CASES[a.case])
