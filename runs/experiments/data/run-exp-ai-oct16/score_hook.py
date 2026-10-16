"""Observation-only wrappers around the original AI target scorers.

Each original CALL still executes its original target with the same registers,
flags, stack arguments and stack depth. Its return address is temporarily a
postlude which records output words, restores the returned CPU state, and jumps
to the original return address. No strategic game fields are written.
"""
import struct
import sys
import hashlib
import json
import os
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'patches'))
import ai_hook as A

SITES=(('city_score',1,0x44f39f,0x44ece4),('army_score',2,0x44f3b3,0x44ee60))
CTL,BUF,REC,CAP=A.CTL,A.BUF,64,8192
DST='Imperial Conquest 2 oct16 scores.exe'
u32=A.u32


def stub(va,sid,target):
    args=0x564e00+sid*16
    body=bytearray(b'\x9c\x60')
    for k,offset in enumerate((28,20,24,40)):
        body+=b'\x8b\x44\x24'+bytes([offset])+b'\xa3'+u32(args+4*k)
    patch=len(body)
    body+=b'\xc7\x44\x24\x24'+bytes(4) # replace original return address
    body+=b'\x61\x9d'
    body+=b'\xe9'+A.rel32(va+len(body),target)
    struct.pack_into('<I',body,patch+4,va+len(body))
    body+=b'\x9c\x60\x8b\x0d'+u32(CTL)
    body+=b'\x81\xf9'+u32(CAP)
    skip=len(body);body+=b'\x0f\x83'+bytes(4)
    body+=b'\x6b\xc9'+bytes([REC])+b'\x81\xc1'+u32(BUF)
    body+=b'\xc7\x01'+u32(sid)
    body+=b'\xa1'+u32(args)+b'\x89\x41\x04'
    body+=b'\x0f\xbf\x05'+u32(A.NATION)+b'\x89\x41\x08'
    for k,out in ((1,12),(2,16),(3,20)):
        body+=b'\xa1'+u32(args+k*4)+b'\x0f\xbf\x00\x89\x41'+bytes([out])
    body+=b'\x0f\xbf\x15'+u32(args)+b'\x69\xd2'+u32(A.ARMY_LEN)
    for k in range(4):
        body+=b'\x8b\x82'+u32(A.ARMIES+k*4)+b'\x89\x41'+bytes([24+k*4])
    body+=b'\xa1'+u32(0x45e030)+b'\x89\x41\x28'
    body+=b'\xff\x05'+u32(CTL)
    struct.pack_into('<i',body,skip+2,len(body)-(skip+6))
    body+=b'\x61\x9d\xe9'+A.rel32(va+len(body)+2,sid and next(site+5 for _,i,site,_ in SITES if i==sid))
    return bytes(body)


def build(source):
    A.SITES=SITES
    A.stub=stub
    A.REC,A.CAP,A.MAGIC=REC,CAP,0x3143534f
    b=bytearray(source)
    caves=A.build(b)
    return b,caves


def read(g):
    n=struct.unpack('<I',g.mem(CTL,4))[0]
    assert n<=CAP
    raw=g.mem(BUF,n*REC)
    out=[]
    for i in range(n):
        r=raw[i*REC:(i+1)*REC]
        sid,army,nation,target,score,distance=struct.unpack_from('<6i',r)
        out.append(dict(site=SITES[sid-1][0],army=army,nation=nation,target=target,score=score,distance=distance,
                        army_header=list(struct.unpack_from('<8h',r,24)),seed=struct.unpack_from('<I',r,40)[0]))
    return out


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: score_hook.py <private game folder>')
    folder=Path(sys.argv[1]);source=folder/A.SRC
    b,caves=build(source.read_bytes())
    destination=folder/DST
    if destination.exists():assert destination.read_bytes()==b,'existing observer differs; preserve it and choose a new workspace'
    else:
        with destination.open('xb') as out:out.write(b)
    stamp=time.strftime('%Y%m%d-%H%M%S')+f'-{os.getpid()}'
    art=ROOT/'artifacts/run-exp-ai-oct16';art.mkdir(parents=True,exist_ok=True)
    kept=art/f'score-observer-{stamp}.exe'
    with kept.open('xb') as out:out.write(b)
    digest=hashlib.sha256(b).hexdigest()
    data=Path(__file__).resolve().parent
    with (data/'SAVES.sha256').open('a') as out:out.write(f'{digest}  {kept.name}\n')
    record=dict(source=source.name,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                output=DST,output_sha256=digest,artifact=kept.name,caves=caves,sites=SITES)
    with (data/f'score-hook-build-{stamp}.json').open('x') as out:json.dump(record,out,indent=2)
    print(json.dumps(record))
