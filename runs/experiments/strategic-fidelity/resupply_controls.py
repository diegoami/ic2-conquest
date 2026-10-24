"""Six same-input original-instruction/native resupply controls, no game run.

Only city supply stocks and one capital pointer change in captured state.
No coordinates, unit stats, formula or game helper are replaced. Outputs new.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ESP,UC_X86_REG_EIP
import observer as O
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));from state import sav
BASE=ROOT/'artifacts/run-exp-strategic-fidelity';DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity'
OUT=BASE/'resupply-controls-v1';OUT.mkdir(exist_ok=False)
raw=(BASE/'original/N-rome-hook-v1/snapshots/000.ram').read_bytes()
source=(BASE/'projections/N-rome-hook-v1-v1/000.SAV').read_bytes();s=sav.parse(source)
assert s['armies'][7]['troops']==29800 and s['armies'][7]['owner']==4
exe=Path('/home/diego/ic2-work/build/Imperial Conquest 2.exe').read_bytes()
assert hashlib.sha256(exe).hexdigest()=='9d753d5de78801f2368d06125cc87f296b92f671b686c39fd6ac149838ebba31'
pe=struct.unpack_from('<I',exe,0x3c)[0];n,opt=struct.unpack_from('<H',exe,pe+6)[0],struct.unpack_from('<H',exe,pe+20)[0]
sections=[]
for k in range(n):
    o=pe+24+opt+40*k;vs,va,rs,rp=struct.unpack_from('<4I',exe,o+8);sections.append((0x400000+va,rp,rs))
def original(ram):
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
    for va,rp,rs in sections:
        if rs:u.mem_write(va,exe[rp:rp+rs])
    u.mem_write(O.SNAP_BASE,ram);esp=0x80f000;out=0x80a000
    u.mem_write(esp,struct.pack('<I',0x600000));u.reg_write(UC_X86_REG_EAX,7);u.reg_write(UC_X86_REG_EDX,out);u.reg_write(UC_X86_REG_ESP,esp)
    calls=[]
    def hook(uc,address,size,data):
        if address==0x40284c:calls.append(address)
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x44e670,0x600000,count=4000000)
    assert u.reg_read(UC_X86_REG_EIP)==0x600000 and not calls and bytes(u.mem_read(O.SNAP_BASE,O.SNAP_SIZE))==ram
    return struct.unpack('<h',u.mem_read(out,2))[0]
variants=[('capital-a',30,30,144,144),('capital-b',30,30,152,152),
    ('stock29',0,29,144,144),('stock30',0,30,144,152),('stock297',0,297,144,152),('stock298',0,298,144,152)]
rows=[];nationOffset=100958+len(s['armies'])*656+2+len(s['fleets'])*26
for i,(name,stockA,stockB,capital,want) in enumerate(variants):
    ram=bytearray(raw);b=bytearray(source)
    stocks={c['id']:0 for c in s['cities'] if c['owner']==4};stocks.update({144:stockA,152:stockB})
    for city,value in stocks.items():
        struct.pack_into('<h',ram,0x479590+city*34+24-O.SNAP_BASE,value)
        struct.pack_into('<h',b,89600+city*34+24,value)
    struct.pack_into('<h',ram,0x474670+4*1172+0x444-O.SNAP_BASE,capital)
    struct.pack_into('<h',b,nationOffset+4*1172+0x444,capital)
    result=original(bytes(ram));assert result==want,(name,result,want)
    with (OUT/f'{i:03}.SAV').open('xb') as f:f.write(b)
    with (OUT/f'{i:03}.json').open('x') as f:json.dump(sav.parse(b),f)
    rows.append(dict(snapshot=i,army=7,name=name,nation=4,capital=capital,stockA=stockA,stockB=stockB,
        original_resupply=result,random_calls=0,provenance='synthetic city-stock/capital edits of captured original decision, no new original game'))
with (OUT/'manifest.json').open('x') as f:json.dump(rows,f,indent=2)
with (DATA/'resupply-original-controls-v1.json').open('x') as f:json.dump(rows,f,indent=2)
print('PASS six original resupply controls; stocks29/30/297/298 and swapped capital; no RNG calls')
