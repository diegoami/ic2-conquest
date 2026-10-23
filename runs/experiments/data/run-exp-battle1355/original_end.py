"""Owner1355 End turn in the exact unmodified original, private copies only."""
import json,os,shutil,subprocess,sys,time,traceback,struct,threading
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
PRIVATE=ROOT/'artifacts/run-exp-battle1355/private-v1';WORK=PRIVATE/'runtime'
if not WORK.exists():
 source=Path('/home/diego/ic2-work');WORK.mkdir()
 shutil.copytree(source/'prefix',WORK/'prefix',symlinks=True,ignore=lambda d,n:['IC2'] if Path(d).name=='drive_c' else [])
 game=WORK/'prefix/drive_c/IC2';game.mkdir()
 for p in (source/'prefix/drive_c/IC2').iterdir():
  if p.is_file() and p.suffix.lower() in {'.exe','.dll','.dat','.hlp','.cnt'}:shutil.copy2(p,game/p.name)
 for p in source.iterdir():
  if p.is_file() and (p.name in {'win_controls.exe','win_slider.exe','toolbar.json'} or p.name.endswith('_toolbar.json')):shutil.copy2(p,WORK/p.name)
os.environ['IC2_WORK']=str(WORK);os.environ['DISPLAY_IC2']=':155'
sys.path.insert(0,str(ROOT))
from harness.driver import Game,G,ENV,CUR_NATION,RAND_SEED,DriverError
from harness import environment
from state import sav
environment.set_data_folder(PRIVATE)
attempt=sys.argv[1] if len(sys.argv)>1 else 'v1'
screen=sys.argv[2] if len(sys.argv)>2 else '1280x1024'
fight=len(sys.argv)>3 and sys.argv[3]=='battle'
out=PRIVATE/('original-end-'+attempt);out.mkdir()
record={'runtime':'unmodified original/Wine, owner files copied unchanged','complete':False}
display=None;g=None
def log(s):
 with (out/'driver.log').open('a') as f:f.write(str(s)+'\n')
class PrivateGame(Game):
 def ensure_xvfb(self):
  global display
  if subprocess.run(['xdpyinfo','-display',':155'],capture_output=True).returncode:
   display=subprocess.Popen(['Xvfb',':155','-screen','0',screen+'x24'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True);time.sleep(2)
 def show(self,x,y):
  import harness.driver as d
  w=self.find_windows('^Unit map$')[0]
  d.VIEW_COLS=max(1,(w[4]-20)//32);d.VIEW_ROWS=max(1,(w[5]-70)//32)
  d.UNIT_PAINT=(335+w[2]-333,96+w[3]-75)
  return super().show(x,y)
def keep(path,key):
 dest=out/path.name
 if dest.exists():raise RuntimeError('Refusing existing private output')
 shutil.copy2(path,dest);record[key]=str(dest.relative_to(PRIVATE));return dest
try:
 g=PrivateGame(exe='Imperial Conquest 2.exe',log=log);g.start();record['environment']=g.environment
 record['load_messages']=g.open(PRIVATE/'inputs/classical-mediterranean-saveyy.sav',strict=False)
 record['rng_before_end']=struct.unpack('<I',g.mem(RAND_SEED,4))[0]
 before=keep(g.save_as('B1355-'+attempt+'-BEFORE-END.SAV'),'before_end');cal=g.calendar();me=g.i16(CUR_NATION)
 g.tool('end_turn');started=time.time();messages=[]
 while time.time()-started<240:
  if g.in_battle():
   record['unexpected_battle_during_end']=g.battle_state();raise RuntimeError('Battle opened during original End turn; inspect before further orders')
  if g.find_windows('^End turn \\?$'):
   cs=g.controls('End turn ?');g.click_control(g.control(cs,text='End turn'),pause=.6)
  messages+=g.dismiss_popups(strict=False)
  if g.i16(CUR_NATION)==me and g.calendar()!=cal:
   time.sleep(1)
   if g.i16(CUR_NATION)==me and not g.popups():break
  time.sleep(.2)
 else:raise RuntimeError('Original End turn did not return to same human')
 after=keep(g.save_as('B1355-'+attempt+'-AFTER-END.SAV'),'after_end')
 record['messages']=messages;record['rng_after_end']=struct.unpack('<I',g.mem(RAND_SEED,4))[0]
 state=sav.load(after)
 with (out/'original-after-end-state.json').open('x') as f:json.dump(state,f)
 g.shot(out/'after-end.png')
 if fight:
  attacker=next(a for a in state['armies'] if a['owner']==3 and a['troops']==73564)
  defender=next(a for a in state['armies'] if a['owner']==2 and a['troops']==78857)
  ai,di=attacker['id'],defender['id'];record['selected_pair']={'attacker':attacker,'defender':defender}
  record['approach_clicks']=[]
  for click in range(3):
   if g.in_battle():break
   pos=g.army_pos(ai);target=(defender['x'],defender['y'])
   if max(abs(pos[0]-target[0]),abs(pos[1]-target[1]))>1:
    candidates=[(target[0]+dx,target[1]+dy) for dx in (-1,0,1) for dy in (-1,0,1)
      if (dx or dy) and 0<=target[0]+dx<320 and 0<=target[1]+dy<140
      and 2<=state['map'][(target[0]+dx)*140+target[1]+dy]<=11]
    target=min(candidates,key=lambda p:(max(abs(p[0]-pos[0]),abs(p[1]-pos[1])),abs(p[0]-pos[0])+abs(p[1]-pos[1])))
   record['approach_clicks'].append({'before':pos,'target':target,'enemy':[defender['x'],defender['y']]})
   g.select_army(ai,*pos);g.click_tile(*target,pause=1)
   if g.find_windows('^Confirm$'):g._answer_confirm(g.find_windows('^Confirm$')[0][0],yes=True)
   time.sleep(2)
   record['approach_clicks'][-1]['after']=g.army_pos(ai)
   if not g.in_battle() and g.army_pos(ai)==pos:raise RuntimeError('Attack click made no progress; inspect exact UI before retry')
  g.wait(g.in_battle,30,'owner battle opening')
  g.wait(lambda:g.find_windows(' v '),30,'battle window')
  record['battle_entry']=g.battle_state();record['rng_at_battle_entry']=struct.unpack('<I',g.mem(RAND_SEED,4))[0]
  record['army_records_at_entry']={'attacker':sav.parse_army(g.army_rec(ai),ai),'defender':sav.parse_army(g.army_rec(di),di)}
  record['battle_windows']=g.find_windows(' v ')
  g.shot(out/'battle-entry.png')
  with (out/'battle-ready.json').open('x') as f:json.dump(record,f,indent=2)
  print('BATTLE READY: private entry snapshot; waiting for inspected toolbar control',flush=True)
  control=out/'battle-continue.json'
  wait_start=time.time()
  while not control.exists():
   if time.time()-wait_start>600:raise RuntimeError('Inspection checkpoint exceeded10min; private entry snapshot retained')
   time.sleep(.25)
  settings=json.loads(control.read_text());import harness.driver as d
  if 'toolbar_y' in settings:d.BATTLE_TOOLBAR_Y=settings['toolbar_y']
  if 'computer_x' in settings:g.battle_x={'computer':settings['computer_x'],'end_turn':settings['end_x']}
  stop=threading.Event()
  def poll():
   previous=None
   with (out/'original-battle-poll.jsonl').open('x') as f:
    while not stop.is_set():
     try:
      item={'battle':g.battle_state(),'rng':struct.unpack('<I',g.mem(RAND_SEED,4))[0],'in_battle':g.in_battle()}
      text=json.dumps(item)
      if text!=previous:f.write(json.dumps({'monotonic':time.monotonic(),'snapshot':item})+'\n');f.flush();previous=text
     except Exception as e:f.write(json.dumps({'poll_error':str(e)})+'\n')
     stop.wait(.05)
  observer=threading.Thread(target=poll,daemon=True);observer.start()
  try:
   # Unmodified rendering can spend >8s inside one half-round. Toggle once,
   # End turn once, then OBSERVE; never inject repeated turns into autoplay.
   g.click(g.battle_x.get('computer',165),d.BATTLE_TOOLBAR_Y,pause=1.5)
   if g.in_battle() and not g.find_windows('Battle ended'):
    g.click(g.battle_x.get('end_turn',114),d.BATTLE_TOOLBAR_Y,pause=1)
   g.wait(lambda:g.find_windows('Battle ended') or not g.in_battle(),900,'Computer general battle completion',step=.5)
   boxes=g.wait(lambda:g.find_windows('Battle ended'),30,'Battle ended result')
   record['battle_result']={'computer_general_clicks':1,'initial_end_turn_clicks':1,'battle_ended_text':g.read_popup(boxes[0])}
   record['final_battle_before_writeback']=g.battle_state()
   g.shot(out/'battle-ended.png')
   cs=g.controls('Battle ended');g.click_control(g.control(cs,text='OK'),pause=1.5)
   if g.find_windows('^Offer of peace$'):record['peace_declined']=g.answer_battle_peace(False)
   g.dismiss_popups(strict=False)
  finally:stop.set();observer.join(timeout=5)
  final=keep(g.save_as('B1355-'+attempt+'-AFTER-BATTLE.SAV'),'after_battle')
  finalstate=sav.load(final)
  with (out/'original-after-battle-state.json').open('x') as f:json.dump(finalstate,f)
  record['surviving_ptolemaic_armies']=[a for a in finalstate['armies'] if a['owner']==3]
  record['rng_after_battle']=struct.unpack('<I',g.mem(RAND_SEED,4))[0]
 record['complete']=True
 print(json.dumps({'complete':True,'turn':state['turn'],'current_nation':state['current_nation'],
  'battle_result':record.get('battle_result'),'survivors':[(a['x'],a['y'],a['troops']) for a in record.get('surviving_ptolemaic_armies',[])],
  'armies':[dict(index=a['id'],owner=a['owner'],x=a['x'],y=a['y'],moves=a['moves'],morale=a['morale'],troops=a['troops']) for a in state['armies'] if a['owner'] in (2,3)]}),flush=True)
except Exception as e:
 record['error']=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc());print(record['error']['message'],flush=True)
 if g is not None:
  try:g.shot(out/'failure.png')
  except Exception:pass
finally:
 if g is not None:g.kill()
 if display is not None:display.terminate();display.wait(timeout=10)
 with (out/'result.json').open('x') as f:json.dump(record,f,indent=2)
sys.exit(0 if record['complete'] else 1)
