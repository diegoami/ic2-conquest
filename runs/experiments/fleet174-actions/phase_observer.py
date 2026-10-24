"""Memory-only original fleet-phase before/after wrapper at CALL0044FA51.

Original callee executes at original stack depth. A temporary return address
records its exit, then jumps to the original return point. Preserves CPU state;
only observer scratch written. No original game helper replaced in live runs.
"""
import struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'patches'));import ai_hook as A
CTL,BUF,SNAP=0x566000,0x566100,0x570000
REC,CAP,SIZE,ORIGIN=64,64,0x43000,0x45e000
MAGIC=0x31465046;SITE,TARGET,RETURN=0x44fa51,0x44f608,0x44fa56
def record(kind):
 b=bytearray(b'\x9c\x60\xa1'+A.u32(CTL)+b'\x3d'+A.u32(CAP))
 full=len(b);b+=b'\x0f\x83'+bytes(4)
 b+=b'\x89\xc3\x6b\xdb'+bytes([REC])+b'\x81\xc3'+A.u32(BUF)
 b+=b'\xc7\x03'+A.u32(kind)+b'\x89\x43\x0c'
 b+=b'\x0f\xbf\x15'+A.u32(0x4a0320)+b'\x89\x53\x04'
 b+=b'\x8b\x15'+A.u32(0x45e030)+b'\x89\x53\x08'
 for i in range(8):b+=b'\x8b\x54\x24'+bytes([i*4])+b'\x89\x53'+bytes([16+i*4])
 b+=b'\x8b\x54\x24\x20\x89\x53\x30'
 b+=b'\x8b\x54\x24\x0c\x83\xc2\x04\x89\x53\x34'
 b+=b'\x8b\x54\x24\x24\x89\x53\x38'
 b+=b'\x69\xf8'+A.u32(SIZE)+b'\x81\xc7'+A.u32(SNAP)
 b+=b'\xbe'+A.u32(ORIGIN)+b'\xb9'+A.u32(SIZE//4)+b'\xfc\xf3\xa5'
 b+=b'\xff\x05'+A.u32(CTL)
 done=len(b);b+=b'\xe9'+bytes(4)
 struct.pack_into('<i',b,full+2,len(b)-full-6)
 b+=b'\xc7\x05'+A.u32(CTL+12)+A.u32(1)
 struct.pack_into('<i',b,done+1,len(b)-done-5)
 b+=b'\x61\x9d';return bytes(b)
def stub(va,sid,target):
 b=bytearray(record(0));b+=b'\x9c\x60'
 fix=len(b);b+=b'\xc7\x44\x24\x24'+bytes(4)
 b+=b'\x61\x9d\xe9'+A.rel32(va+len(b)+2,target)
 post=va+len(b);struct.pack_into('<I',b,fix+4,post)
 b+=record(1);b+=b'\xe9'+A.rel32(va+len(b),RETURN)
 return bytes(b)
def build(source):
 A.SITES=(('fleet-phase',1,SITE,TARGET),);A.CTL,A.BUF,A.RAW_SIZE=CTL,BUF,0x2200
 A.REC,A.CAP,A.MAGIC,A.stub=REC,CAP,MAGIC,stub
 b=bytearray(source);caves=A.build(b);vsize=SNAP+CAP*SIZE-A.PATCH_VA
 struct.pack_into('<I',b,0x1f8+8*40+8,vsize)
 struct.pack_into('<I',b,0x118+56,(A.PATCH_VA-A.BASE+vsize+0xfff)&~0xfff)
 return bytes(b),caves['fleet-phase']
def read(g):
 count,magic,capacity,overflow=struct.unpack('<4I',g.mem(CTL,16))
 assert magic==MAGIC and capacity==CAP and count<=CAP and not overflow
 raw=g.mem(BUF,count*REC);meta=[];snaps=[]
 for i in range(count):
  kind,nation,seed,index=struct.unpack_from('<IiII',raw,i*REC);assert index==i and kind in (0,1)
  meta.append(dict(index=i,kind=kind,nation=nation,seed=seed,registers=list(struct.unpack_from('<8I',raw,i*REC+16)),flags=struct.unpack_from('<I',raw,i*REC+48)[0]))
  snaps.append(g.mem(SNAP+i*SIZE,SIZE))
 return meta,raw,snaps
