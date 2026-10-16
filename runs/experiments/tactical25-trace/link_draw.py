"""Link the fresh first mismatch's exchange actors to the immutable model diagnostic."""
import csv,hashlib,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'runs/experiments/data/run-exp-tactical25-trace';path=DATA/'hook-20261016-191329-1302174.csv';records=list(csv.DictReader(path.open()));pending=[];actor=None;actor_seq=None;index=0;mapping={}
for r in records:
 site=int(r['site'],0)
 if r['kind']=='random':
  if 0x4393ec<=site<0x439968:pending.append(index);assert len(pending)<=4
  index+=1
 if r['kind']=='marker' and site==0x438fb0 and len(pending)==4:
  slot=int(r['eax'])&65535;assert slot<40
  if actor is None:actor=slot;actor_seq=int(r['seq'])
  else:
   assert actor//20!=slot//20
   for i in pending:mapping[i]=dict(actor=actor,target=slot,rout_entry_seqs=[actor_seq,int(r['seq'])])
   pending=[];actor=None
assert not pending
old=ROOT/'runs/experiments/data/run-exp-tactical25/production-20261016-174818/mix-rg_s1_r5_hook-draws.json';model=json.loads(old.read_text())[24];fresh=[r for r in records if r['kind']=='random'][24]
assert mapping[24]['actor']==23 and mapping[24]['target']==2 and model['actor']['unit']==22 and model['actor']['target']==1
assert (int(fresh['eax']),int(fresh['result']),model['bound'],model['value'])==(1085,357,172,56)
rec=dict(provenance='Fresh Wine actor pair from two rout-entry AX words following four melee draws; model unchanged production typed event',fresh_log_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),model_draw_file_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),draw_index=24,fresh_draw=fresh,fresh_exchange=mapping[24],model_draw=model,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
out=DATA/('draw-link-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime())+'.json')
with out.open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(out)
