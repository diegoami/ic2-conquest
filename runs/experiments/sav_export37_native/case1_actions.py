"""Small HWND-specific helpers; each action is a new exclusive bridge measurement."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BRIDGE=Path(__file__).with_name('windows_bridge.py');DATA=ROOT/'runs/experiments/data/run-exp-sav-export37-native';PRIVATE=Path('/mnt/c/Users/diego/Documents/ic2-tax-native/20261018T085043Z');WIN='C:\\Users\\diego\\Documents\\ic2-tax-native\\20261018T085043Z\\'
def action(pid,kind,label,hwnd=0,value=None):
 out=DATA/(label+'.json');assert not out.exists()
 cmd=[sys.executable,str(BRIDGE),'--action',kind,'--pid',str(pid),'--hwnd',str(hwnd),'--output',str(out)]
 if value is not None:cmd+=['--value',str(value)]
 r=subprocess.run(cmd,capture_output=True,text=True);record=json.loads(out.read_text())
 if r.returncode:raise RuntimeError(record)
 return json.loads(record['stdout']) if record['stdout'].strip() else None

def save_as(pid,main,name,prefix):
 dest=PRIVATE/name;assert not dest.exists();assert len(WIN+name)<100
 action(pid,'command',prefix+'-command',main,5)
 rows=action(pid,'enumerate',prefix+'-dialog')
 edits=[r for r in rows if r['cls']=='Edit' and r['id']==1152 and r['visible']]
 buttons=[r for r in rows if r['cls']=='Button' and r['id']==1 and r['visible']]
 assert len(edits)==len(buttons)==1,(edits,buttons)
 action(pid,'text',prefix+'-path',edits[0]['handle'],WIN+name)
 action(pid,'click',prefix+'-confirm',buttons[0]['handle'])
 for _ in range(50):
  if dest.exists() and dest.stat().st_size>100000:break
  time.sleep(.1)
 assert dest.exists(),name
 raw=dest.read_bytes();record=dict(private_name=name,size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),saved_by_original_UI=True,exclusive_new_destination=True)
 with (DATA/(prefix+'-file.json')).open('x') as f:json.dump(record,f,indent=2);f.write('\n')
 return record
