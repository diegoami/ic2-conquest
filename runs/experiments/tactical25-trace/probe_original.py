"""Original pure threat helper on NEW Wine inputs; validate every result against its fresh observed Walk goal."""
import argparse,hashlib,json,struct,sys,time
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
p=argparse.ArgumentParser();p.add_argument('--states',type=Path,required=True);p.add_argument('--validation',type=Path,required=True);p.add_argument('--exe',type=Path,required=True);p.add_argument('--dat',type=Path,required=True);a=p.parse_args()
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'patches'));from battle_hook import sections
validation=json.loads(a.validation.read_text());assert validation['pass'] and all(s['byte_equal'] for s in validation['saves'])
raw=a.exe.read_bytes();dat=a.dat.read_bytes();assert hashlib.sha256(raw).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f';assert hashlib.sha256(dat).hexdigest()=='94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd'
u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x100000)
for _,va,vsize,rptr,rsize,_ in sections(raw):
 if rsize:u.mem_write(va,raw[rptr:rptr+rsize])
u.mem_write(0x47946c,dat[0x1f7a6:0x1f7a6+50]);u.mem_write(0x478fb0,dat[0x1f2f0:0x1f2f0+200]);assert bytes(u.mem_read(0x43a8af,4))==bytes.fromhex('807deb00')
names=['x','y','origin','type','troops','quality','morale','moves','shots','target'];observed={}
def hook(uc,address,size,data):
 if address==0x43a8af:
  bp=uc.reg_read(UC_X86_REG_EBP);observed.update(keys=list(struct.unpack('<20i',uc.mem_read(bp-0x94,80))),order=list(struct.unpack('<20h',uc.mem_read(bp-0x44,40))))
 if address==0x43a8f3:observed.setdefault('candidates',[]).append(uc.reg_read(UC_X86_REG_EDI)&65535)
u.hook_add(UC_HOOK_CODE,hook,begin=0x43a8af,end=0x43a8f3)
records=json.loads(a.states.read_text())['records'];rows=[]
for n,r in enumerate(records):
 if r['kind']!='marker' or r['site']!='0x43a718':continue
 actor=r['eax']&65535
 for i,s in enumerate(r['slots']):u.mem_write(0x4a0344+44*i,struct.pack('<10h',*[s[k] for k in names])+bytes(24))
 u.mem_write(0x4a0a24,struct.pack('<168h',*r['grid']));u.mem_write(0x45e6b0,struct.pack('<40h',*r['actor_claim_targets']));u.mem_write(0x45e6ac,struct.pack('<2h',r['enemy_first'],r['own_first']))
 u.mem_write(0x8ff000,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_ESP,0x8ff000);u.reg_write(UC_X86_REG_EAX,actor);u.reg_write(UC_X86_REG_EDX,0x8ffe00);observed.clear();u.emu_start(0x43a718,0x600000,count=1000000);assert u.reg_read(UC_X86_REG_EIP)==0x600000
 aim=list(struct.unpack('<2h',u.mem_read(0x8ffe00,4)));next_marker=next(x for x in records[n+1:] if x['kind']=='marker');assert next_marker['site']=='0x438d24' and next_marker['eax']&65535==actor
 wine_aim=[next_marker['edx']&65535,next_marker['edx']>>16];assert aim==wine_aim
 rows.append(dict(counter=r['counter'],actor=actor,wine_input_seq=r['seq'],wine_walk_seq=next_marker['seq'],wine_goal=wine_aim,original_x86_goal=aim,original_x86_chosen_enemy=observed['candidates'][-1],original_x86_order=observed['order'],original_x86_sorted_keys=observed['keys'],original_x86_candidates=observed['candidates'],result_matches_fresh_wine=True))
rec=dict(provenance='Original x86 pure helper on explicitly NEW Wine state; x86 inferred keys/order/chosen enemy are distinct from directly observed Wine Walk goals',states=a.states.name,validation=a.validation.name,exe_sha256=hashlib.sha256(raw).hexdigest(),dat_sha256=hashlib.sha256(dat).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows)
out=ROOT/'runs/experiments/data/run-exp-tactical25-trace'/('pure-original-'+time.strftime('%Y%m%d-%H%M%S',time.gmtime())+'.json')
with out.open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(out);print([(r['counter'],r['actor'],r['original_x86_chosen_enemy'],r['wine_goal']) for r in rows])
