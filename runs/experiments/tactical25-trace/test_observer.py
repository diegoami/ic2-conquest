"""CPU noninterference plus active snapshot payload/DF/bounds checks; no Wine."""
import contextlib,hashlib,io,json,random,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));import observer as O
O.configure()
from tests import test_battle_hook_caves as T
from unicorn.x86_const import *
T.HIGH=O.STATE_END;T.STACK_TOP=0x3010000;T.L.BUF=O.H.BUF;T.rng_small=lambda seed:seed%7 # Force snapshot execution, not random high counters.
old_new=T.new_machine
def machine(state):
 uc,caves=old_new(state);uc.mem_write(O.SNAPSHOT,O.snapshot_code());return uc,caves
T.new_machine=machine
stamp=time.strftime('%Y%m%d-%H%M%S',time.gmtime());out=ROOT/'runs/experiments/data/run-exp-tactical25-trace'/('cpu-'+stamp+'.json');stdout=io.StringIO();checks=[]
with contextlib.redirect_stdout(stdout):
 sys.argv=[sys.argv[0],'--trials','100'];rc=T.main()
 rng=random.Random(25)
 for df in [0,1]:
  for counter in [0,6,7]:
   for index in [0,O.STATE_CAP-1,O.STATE_CAP]:
    state=T.random_state(rng);regs,stack,seed=state;regs[UC_X86_REG_EFLAGS]=(regs[UC_X86_REG_EFLAGS]&~0x400)|(df<<10)
    uc,caves=machine(state);code=b'\xe8'+O.H.rel32(T.SITE,caves['random'][0]);T.prepare(uc,state,T.SITE,code+b'\xf4')
    payload=rng.randbytes(2176);uc.mem_write(0x4a0344,payload[:2096]);uc.mem_write(0x45e6b0,payload[2096:]);uc.mem_write(O.H.COUNTER_HR,struct.pack('<H',counter));uc.mem_write(O.H.CTL,struct.pack('<I',index))
    T.run(uc,T.SITE,T.SITE+5)
    over=struct.unpack('<I',uc.mem_read(O.OVERFLOW,4))[0]
    assert over==int(counter<=6 and index>=O.STATE_CAP)
    if counter<=6 and index<O.STATE_CAP:
     raw=bytes(uc.mem_read(O.STATE_BUF+index*O.STATE_REC,O.STATE_REC));assert raw[128:]==payload
     base=T.L.decode(bytes(uc.mem_read(O.H.BUF+index*O.H.REC,O.H.REC)),index);decoded=O.decode_snapshot(raw,base)
     assert decoded['original_esp']==regs[UC_X86_REG_ESP]-4 and decoded['stack_words'][0]==T.SITE+5
     assert uc.reg_read(UC_X86_REG_EFLAGS)&0x400==df<<10
    checks.append(dict(df=df,counter=counter,index=index,pass_=True))
rec=dict(exit=rc,checks=stdout.getvalue(),snapshot_payload_cases=checks,observer_sha256=hashlib.sha256(Path(O.__file__).read_bytes()).hexdigest(),test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),forced_counter='seed%7 so every normal noninterference trial captures state',provenance='Unicorn original-v-observer registers/EFLAGS/ESP/live stack and guest image; not Wine/native')
with out.open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
print(stdout.getvalue());print(out);raise SystemExit(rc)
