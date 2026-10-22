"""Inert original per-decision snapshots, alongside the tested48-byte battle hook.

Only the observer's PE section/control/buffers are written. Snapshot records are
pre-call state, NOT completed Random results. Preserve original registers,
EFLAGS (including DF), ESP and live stack through the existing private-stack guard.
"""
import struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'patches'));import battle_hook as H
SNAPSHOT=0x565200
OVERFLOW=0x565180
STATE_BUF=0x866000
STATE_REC=2304
STATE_CAP=8192
STATE_END=STATE_BUF+STATE_REC*STATE_CAP
EXTRA_MARKERS=(
 ('target_best',0x439e08,bytes.fromhex('5356575583c4f4')),
 ('engage',0x43a160,bytes.fromhex('558bec83c4ec')),
 ('pass2',0x43a544,bytes.fromhex('5356575583c4e8')),
 ('pass3',0x43abb4,bytes.fromhex('558bec83c4d8')),
 ('threat',0x43a718,bytes.fromhex('558bec81c46cffffff')),
 ('walk',0x438d24,bytes.fromhex('558bec83c4e8')),
)
def configure():
 if getattr(H,'tactical25_state_configured',False):return
 base=H.Asm
 class SnapshotAsm(base):
  def b(self,*chunks):
   super().b(*chunks)
   if chunks==(b'\x89\x35'+H.u32(H.CTL+8),):self.call(SNAPSHOT)
   return self
 H.Asm=SnapshotAsm;H.MARKERS+=EXTRA_MARKERS;H.BUF=0x566000;H.RAW_SIZE=0x2000;H.tactical25_state_configured=True

def snapshot_code():
 # RB has already set CUR. ESI points to the record, its seq gives the parallel slot.
 a=H.Asm(SNAPSHOT)
 a.b(b'\x0f\xb7\x05'+H.u32(H.COUNTER_HR),b'\x83\xf8\x06');a.j32(0x87,'done')
 a.b(b'\x8b\x46\x04',b'\x3d'+H.u32(STATE_CAP));a.j8(0x72,'room')
 a.b(b'\xc7\x05'+H.u32(OVERFLOW)+H.u32(1),b'\xc3');a.label('room')
 a.b(b'\x69\xf8'+H.u32(STATE_REC),b'\x81\xc7'+H.u32(STATE_BUF))
 a.b(b'\xfc',b'\xb9'+H.u32(12),b'\xf3\xa5') # header48
 a.b(b'\xa1'+H.u32(0x45e6ac),b'\xab') # enemyFirst, ownFirst (two words), off48
 a.b(b'\xa1'+H.u32(0x45e6a8),b'\xab') # selected, activeNation, off52
 a.b(b'\xa1'+H.u32(0x45e6a4),b'\xab') # original general/end/interrupted flags, off56
 a.b(b'\xa1'+H.u32(H.SV),b'\xab') # original ESP, off60
 a.b(b'\x89\xc6',b'\xb9'+H.u32(16),b'\xf3\xa5') #64bytes of original live stack, off64
 for va,count in [(0x4a0344,440),(0x4a0a24,84),(0x45e6b0,20)]:
  a.b(b'\xbe'+H.u32(va),b'\xb9'+H.u32(count),b'\xf3\xa5')
 a.label('done');a.b(b'\xc3');return a.done()

def apply(b):
 from types import SimpleNamespace
 configure();info=H.apply(b,1,SimpleNamespace(BATTLE_START_CALL=0x45c1ae,SEED_CAVE=0x564400,TBATTLE_START=0x436fb4))
 code=snapshot_code();off=H.PATCH_RAW_START+SNAPSHOT-H.PATCH_VA
 assert SNAPSHOT>=H.CTL+0x200 and SNAPSHOT+len(code)<=H.BUF
 b[off:off+len(code)]=code
 vsize=STATE_END-H.PATCH_VA;hdr=0x1f8+8*40
 struct.pack_into('<I',b,hdr+8,vsize);struct.pack_into('<I',b,0x118+56,(STATE_END-H.BASE+0xfff)&~0xfff)
 info.update(snapshot_va=SNAPSHOT,snapshot_bytes=code.hex(),state_buf=STATE_BUF,state_rec=STATE_REC,state_cap=STATE_CAP,state_end=STATE_END,state_overflow=OVERFLOW,snapshot_max_counter=6)
 return info

def decode_snapshot(raw,base):
 assert len(raw)==STATE_REC
 f=struct.unpack_from('<12I',raw);assert f[0]==base['tag'] and f[1]==base['seq'] and f[5]==base['seed_before']
 enemy,own,selected,nation=struct.unpack_from('<4h',raw,48)
 names=['x','y','origin','type','troops','quality','morale','moves','shots','target']
 slots=[]
 for i in range(40):
  data=raw[128+44*i:128+44*(i+1)];slots.append(dict(slot=i,**dict(zip(names,struct.unpack_from('<10h',data))),name=data[20:].split(b'\0')[0].decode('latin1')))
 return dict(seq=base['seq'],kind=base['kind'],site=hex(base['site']),counter=base['counter'],side=base['side'],eax=base['eax'],edx=base['edx'],ecx=base['ecx'],ebp=base['ebp'],seed_before=base['seed_before'],enemy_first=enemy,own_first=own,selected=selected,active_nation=nation,flags=list(raw[56:60]),original_esp=struct.unpack_from('<I',raw,60)[0],stack_words=list(struct.unpack_from('<16I',raw,64)),slots=slots,grid=list(struct.unpack_from('<168h',raw,1888)),actor_claim_targets=list(struct.unpack_from('<40h',raw,2224)))
