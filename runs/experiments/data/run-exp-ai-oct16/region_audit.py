"""Reproduce region classification from Wine tables and execute original x86 boundaries.

This is code/emulator corroboration of table membership, not a Wine target-choice
observation. It does not emulate a corrected remake or alter original fixtures.
Outputs are exclusively created, including the complete city-id mapping.
"""
import csv
import hashlib
import json
import struct
import sys
import time
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_ESP

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'patches'))
from battle_hook import sections
DATA=Path(__file__).resolve().parent
STAMP=time.strftime('%Y%m%d-%H%M%S')
records=[]
for p in DATA.glob('probe-*.jsonl'):
    for line in p.read_text().splitlines():
        r=json.loads(line)
        if r['event']=='runtime_tables':records.append((p,r))
assert len(records)==1,'Select an explicit runtime table record if more than one exists'
source,rec=records[0]
boxes,coasts=rec['region_boxes'],rec['coast_pairs']
exe=Path(sys.argv[1])
exe_bytes=exe.read_bytes()
assert hashlib.sha256(exe_bytes).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
uc=Uc(UC_ARCH_X86,UC_MODE_32)
uc.mem_map(0x400000,0x300000)
uc.mem_map(0x800000,0x10000)
for _,va,vsize,raw,rsize,_ in sections(exe_bytes):
    if rsize:uc.mem_write(va,exe_bytes[raw:raw+rsize])
uc.mem_write(0x4794e8,struct.pack('<32h',*(v for row in boxes for v in row)))
uc.mem_write(0x479528,struct.pack('<12h',*(v for row in coasts for v in row)))
STOP,STACK,OUT_R,OUT_C=0x600000,0x80f000,0x80f100,0x80f104


def actual(x,y):
    uc.mem_write(STACK,struct.pack('<I',STOP))
    uc.mem_write(OUT_R,b'\x55'*8)
    for reg,val in ((UC_X86_REG_EAX,(x&65535)|((y&65535)<<16)),
                    (UC_X86_REG_EDX,OUT_R),(UC_X86_REG_ECX,OUT_C),(UC_X86_REG_ESP,STACK)):
        uc.reg_write(reg,val)
    uc.emu_start(0x44eb18,STOP,count=10000)
    assert uc.reg_read(UC_X86_REG_ESP)==STACK+4
    return [struct.unpack('<h',uc.mem_read(OUT_R,2))[0],uc.mem_read(OUT_C,1)[0]]


def classify(x,y):
    region=-1
    for i,(xmin,xmax,ymin,ymax) in enumerate(boxes):
        if xmin<x<xmax and ymin<y<ymax:region=i
    coast=int(not any(x<cx and y<cy for cx,cy in coasts))
    return [region,coast]


points={(-1,-1),(0,0),(319,139),(320,140)}
for xmin,xmax,ymin,ymax in boxes:
    mx,my=(xmin+xmax)//2,(ymin+ymax)//2
    points.update((x,my) for x in (xmin-1,xmin,xmin+1,xmax-1,xmax,xmax+1))
    points.update((mx,y) for y in (ymin-1,ymin,ymin+1,ymax-1,ymax,ymax+1))
for cx,cy in coasts:
    points.update((x,y) for x in (cx-1,cx,cx+1) for y in (cy-1,cy,cy+1))
for c in rec['snapshot']['cities']:points.add((c['x'],c['y']))
checks=[]
for x,y in sorted(points):
    expected,observed=classify(x,y),actual(x,y)
    checks.append(dict(x=x,y=y,expected=expected,original_x86=observed))
    assert expected==observed,(x,y,expected,observed)
overlap=[]
for i,(a,b,c,d) in enumerate(boxes):
    for j,(e,f,g,h) in enumerate(boxes):
        if i<j and max(a,e)+1<min(b,f) and max(c,g)+1<min(d,h):overlap.append([i,j])
mapping=DATA/f'city-regions-{STAMP}.csv'
with mapping.open('x',newline='') as out:
    w=csv.writer(out);w.writerow(('city_id','name','x','y','region','coast_flag'))
    for c in rec['snapshot']['cities']:
        w.writerow((c['id'],c['name'],c['x'],c['y'],*classify(c['x'],c['y'])))
result=dict(provenance='original x86 under Unicorn, using Wine-read tables; not Wine target choice',
            input_save=rec['save'],turn=rec['turn'],runtime_log=source.name,
            runtime_log_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            exe_sha256=hashlib.sha256(exe_bytes).hexdigest(),function='0x44eb18',region_boxes=boxes,coast_pairs=coasts,
            comparisons=checks,checks=len(checks),overlapping_box_pairs=overlap,
            city_mapping=mapping.name,city_mapping_sha256=hashlib.sha256(mapping.read_bytes()).hexdigest(),
            semantics=dict(edges='all four box edges strict/excluded',overlap='last matching box wins',
                           fallback_region=-1,coast='0 if any x<cx AND y<cy, else 1',
                           same_region='both region index and coast flag must match'))
with (DATA/f'region-audit-{STAMP}.json').open('x') as out:json.dump(result,out,indent=2)
print(json.dumps(dict(checks=len(checks),cities=334,boxes=boxes,overlap=overlap,mapping=mapping.name)))
