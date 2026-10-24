"""Original strategic decision/move observer; original game RAM is read only.

Reuses ai_hook's section builder and the #1388 register/stack-preserving marker
pattern. Snapshots are diagnostic RAM, not original Save As files. Fail closed
on either capacity. No decision, Random call or movement helper is replaced.
"""
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'patches'))
import ai_hook as A
CTL,BUF,REC,CAP=0x566000,0x566100,96,8192
SNAP,SNAP_BASE,SNAP_SIZE,SNAP_CAP=0x640000,0x45e000,0x43000,64
MAGIC=0x31375353

def u32(n):return struct.pack('<I',n&0xffffffff)
def stub(va,sid,target):
    b=bytearray(b'\x9c\x60\x8b\x0d'+u32(CTL))
    b+=b'\x81\xf9'+u32(CAP)
    skip=len(b);b+=b'\x0f\x83'+bytes(4)
    b+=b'\x6b\xc9'+bytes([REC])+b'\x81\xc1'+u32(BUF)
    b+=b'\xc7\x01'+u32(sid)
    for saved,out in ((28,4),(20,8),(36,16)):
        b+=b'\x8b\x44\x24'+bytes([saved])+b'\x89\x41'+bytes([out])
    b+=b'\x0f\xbf\x05'+u32(A.NATION)+b'\x89\x41\x0c'
    b+=b'\xa1'+u32(0x45e030)+b'\x89\x41\x14'
    b+=b'\x0f\xbf\x44\x24\x1c\x69\xc0'+u32(26 if target==0x44e1fc else 656)
    table=A.FLEETS if target==0x44e1fc else A.ARMIES
    for k in range(8):
        b+=b'\x8b\x90'+u32(table+4*k)+b'\x89\x51'+bytes([24+4*k])
    b+=b'\xc7\x41\x38'+u32(-1)
    # Original caller stack values let the move records expose scorer outputs.
    for k in range(8):
        b+=b'\x8b\x44\x24'+bytes([40+4*k])+b'\x89\x41'+bytes([64+4*k])
    if target==0x44e670:
        b+=b'\xa1'+u32(CTL+12)+b'\x3d'+u32(SNAP_CAP)
        full=len(b);b+=b'\x0f\x83'+bytes(4)
        b+=b'\x89\x41\x38\x69\xc0'+u32(SNAP_SIZE)+b'\x05'+u32(SNAP)+b'\x89\xc7'
        b+=b'\x51\xfc\xbe'+u32(SNAP_BASE)+b'\xb9'+u32(SNAP_SIZE//4)+b'\xf3\xa5\x59'
        b+=b'\xff\x05'+u32(CTL+12)
        done=len(b);b+=b'\xe9'+bytes(4)
        struct.pack_into('<i',b,full+2,len(b)-full-6)
        b+=b'\xc7\x05'+u32(CTL+16)+u32(1)
        struct.pack_into('<i',b,done+1,len(b)-done-5)
    b+=b'\xff\x05'+u32(CTL)
    finished=len(b);b+=b'\xe9'+bytes(4)
    struct.pack_into('<i',b,skip+2,len(b)-skip-6)
    b+=b'\xc7\x05'+u32(CTL+16)+u32(1)
    struct.pack_into('<i',b,finished+1,len(b)-finished-5)
    b+=b'\x61\x9d\xe9'+A.rel32(va+len(b)+2,target)
    return bytes(b)

def configure(source):
    import capstone
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    sites=[]
    for off in range(0x400,0x5b800-4):
        if source[off]!=0xe8:continue
        va=off+0x401000-0x400;target=va+5+struct.unpack_from('<i',source,off+1)[0]
        if target not in (0x44dba8,0x44d734,0x44e1fc) and va!=0x44f38b:continue
        ins=list(md.disasm(source[off:off+5],va))
        assert len(ins)==1 and ins[0].mnemonic=='call' and ins[0].size==5
        if va==0x44f38b:assert target==0x44e670
        sites.append((f'{va:08x}',len(sites)+1,va,target))
    assert len(sites)==22 and any(s[2]==0x44f38b for s in sites)
    A.SITES=tuple(sites);A.CTL,A.BUF,A.RAW_SIZE=CTL,BUF,0x2200
    A.REC,A.CAP,A.MAGIC,A.stub=REC,CAP,MAGIC,stub
    return sites

def build(source):
    sites=configure(source);b=bytearray(source);caves=A.build(b)
    size=SNAP+SNAP_CAP*SNAP_SIZE-A.PATCH_VA
    struct.pack_into('<I',b,0x1f8+8*40+8,size)
    struct.pack_into('<I',b,0x118+56,(A.PATCH_VA-A.BASE+size+0xfff)&~0xfff)
    return bytes(b),sites,caves

def read(g):
    count,magic,cap,snapshots,overflow=struct.unpack('<5I',g.mem(CTL,20))
    assert magic==MAGIC and cap==CAP and count<CAP and snapshots<=SNAP_CAP and not overflow
    raw=g.mem(BUF,count*REC);records=[]
    for i in range(count):
        sid,eax,edx,nation,ret,seed=struct.unpack_from('<IIIiII',raw,i*REC)
        site=next(s for s in A.SITES if s[1]==sid)
        records.append(dict(seq=i,site=site[2],target=site[3],unit=eax&65535,nation=nation,
            goal=None if site[3]==0x44e670 else list(struct.unpack('<2h',struct.pack('<I',edx))),
            edx=edx,seed=seed,return_address=ret,
            unit_header=list(struct.unpack_from('<16h',raw,i*REC+24)),
            snapshot=struct.unpack_from('<i',raw,i*REC+56)[0],
            caller_stack=list(struct.unpack_from('<16h',raw,i*REC+64))))
    return records,raw,[g.mem(SNAP+i*SNAP_SIZE,SNAP_SIZE) for i in range(snapshots)]
