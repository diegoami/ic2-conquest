#!/usr/bin/env python3
"""Execute complete original city-loop callers on staged inputs; check Wine saves.

Requires Unicorn. This is original-x86/model-input evidence, not original play.
No original code is patched or stubbed. Mercenary offers in inputs are disabled.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time

sys.dont_write_bytecode=True
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--bot',type=Path,required=True)
p.add_argument('--exe',type=Path,required=True)
p.add_argument('--artifacts',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
sys.path[:0]=[str(a.bot),str(a.bot/'patches')]
from state import sav
from battle_hook import sections
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ESP

raw=a.exe.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'


def run(path,subject):
    b=path.read_bytes();s=sav.parse(b)
    u=Uc(UC_ARCH_X86,UC_MODE_32)
    u.mem_map(0x400000,0x300000);u.mem_map(0x800000,0x10000)
    for _,va,vs,rp,rs,_ in sections(raw):
        if rs:u.mem_write(va,raw[rp:rp+rs])
    u.mem_write(0x479590,b[sav.CITY_OFF:sav.ARMY_OFF])
    na=sav.i16(b,sav.ARMY_OFF);base=sav.ARMY_OFF+2
    u.mem_write(0x47c1ec,b[base:base+na*sav.ARMY_LEN])
    base+=na*sav.ARMY_LEN;nf=sav.i16(b,base);base+=2
    u.mem_write(0x49c26c,b[base:base+nf*sav.FLEET_LEN]);base+=nf*sav.FLEET_LEN
    u.mem_write(0x474670,b[base:base+16*sav.NATION_LEN]);base+=16*sav.NATION_LEN
    u.mem_write(0x49da10,b[base:base+50*12])
    u.mem_write(0x4a0320,struct.pack('<h',0))
    idx=2 if subject=='fleet' else 0
    unit=0x49c26c+idx*26 if subject=='fleet' else 0x47c1ec
    so,po=(14,16) if subject=='fleet' else (10,12)

    def i16(addr):return struct.unpack('<h',u.mem_read(addr,2))[0]
    def i32(addr):return struct.unpack('<i',u.mem_read(addr,4))[0]
    def state():
        return dict(supplies=i16(unit+so),money=i16(unit+po),
                    condition=i16(unit+20) if subject=='fleet' else None,
                    stocks=[i16(0x479590+i*34+24) for i in range(334)],
                    treasuries=[i32(0x474aa8+i*1172) for i in range(16)])

    calls=[];active=[]
    entry=0x44f7e4 if subject=='fleet' else 0x44f6d8
    back=0x44e65d if subject=='fleet' else 0x44e4d2
    def observe(uc,address,size,data):
        if address==entry:
            assert not active
            active.append(dict(city=uc.reg_read(UC_X86_REG_EAX)&65535,before=state()))
        if address==back and active:
            record=active.pop();record['after']=state();calls.append(record)
    u.hook_add(UC_HOOK_CODE,observe)
    before=state()
    u.mem_write(0x80f000,struct.pack('<I',0x600000))
    u.reg_write(UC_X86_REG_ESP,0x80f000)
    u.reg_write(UC_X86_REG_EAX,idx)
    u.emu_start(0x44e5dc if subject=='fleet' else 0x44e41c,0x600000,count=200000)
    assert u.reg_read(UC_X86_REG_ESP)==0x80f004 and not active
    return before,state(),calls


def trunc(v,d):return (abs(v)//d)*(1 if v>=0 else -1)
def word(v):return (v+32768)%65536-32768


def derive(path,subject):
    s=sav.parse(path.read_bytes());unit=s['fleets'][2] if subject=='fleet' else s['armies'][0]
    sup=unit['supplies'];money=unit['money'];entry=money
    condition=unit.get('condition');cap=unit['ships']*8 if subject=='fleet' else unit['troops']//100
    stocks=[c['supplies'] for c in s['cities']];treasuries=[n['treasury'] for n in s['nations']]
    calls=[]
    for city in s['cities']:
        owner=city['owner'];stock=stocks[city['id']]
        rel=0 if owner==0 else s['nations'][0]['relations'][sav.NATIONS[owner]]
        own=owner==0
        near=max(abs(unit['x']-city['x']),abs(unit['y']-city['y'])) < (4 if subject=='fleet' else 5)
        eligible=(own if subject=='fleet' else own and stock>0) or (
            (rel<3 if subject=='fleet' else rel!=3) and stock>0 and entry>0)
        if not near or not eligible:continue
        calls.append(city['id'])
        q=min(word(cap-sup),stock)
        if own:
            if subject=='fleet':
                if money<100 and treasuries[0]>100:money+=100;treasuries[0]-=100
                if condition<95:treasuries[0]-=trunc((100-condition)*unit['ships'],5);condition=100
            else:
                if money>1000:treasuries[0]+=money-1000;money=1000
                if money<500 and treasuries[0]>0:money+=500;treasuries[0]-=500
        else:
            q=min(q,trunc(money,5));cost=trunc(q,5)
            money=word(money-cost);treasuries[owner]+=cost
        sup=word(sup+q);stocks[city['id']]=word(stock-q)
    return dict(supplies=sup,money=money,condition=condition,stocks=stocks,treasuries=treasuries),calls


records=[]
for path in sorted(a.artifacts.glob('*-input.SAV')):
    case=path.name.split('-2026')[0];subject=case.split('-')[0]
    before,after,calls=run(path,subject)
    expected,order=derive(path,subject)
    assert after==expected,(case,after,expected)
    assert [c['city'] for c in calls]==order
    post=path.with_name(path.name.replace('-input.SAV','-post.SAV'))
    record=dict(input=path.name,input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                case=case,before=before,after=after,calls=calls,reference_matches=True)
    if post.exists():
        s=sav.parse(post.read_bytes());rows=s['fleets'] if subject=='fleet' else s['armies']
        unit=next(x for x in rows if x['owner']==0)
        actual=dict(supplies=unit['supplies'],money=unit['money'],condition=unit.get('condition'),
                    stocks=[c['supplies'] for c in s['cities']],treasuries=[n['treasury'] for n in s['nations']])
        assert after==actual,(case,{k:(after[k],actual[k]) for k in after if after[k]!=actual[k]})
        record.update(post=post.name,post_sha256=hashlib.sha256(post.read_bytes()).hexdigest(),wine_matches=True)
    records.append(record)
with a.output.open('x') as out:
    json.dump(dict(provenance='Complete original x86 city-loop callers, crafted inputs; no stubs. Not native play.',
                   exe_sha256=hashlib.sha256(raw).hexdigest(),records=records),out,indent=2)
    out.write('\n')
print('PASS',len(records),'original x86/reference cases;',sum(r.get('wine_matches',False) for r in records),'Wine comparisons')
