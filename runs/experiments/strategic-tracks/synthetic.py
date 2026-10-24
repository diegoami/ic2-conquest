"""Declared one-variable economy/diplomacy controls; immutable generated state."""
from original_support import *
meta=json.loads((DATA/'ST-rom-hook-v1/phase-records.json').read_text())
raw_at=lambda phase,n:(BASE/'live/ST-rom-hook-v1/snapshots'/f"{next(r['index'] for r in meta if r['kind']==0 and r['phase']==phase and r['nation']==n):03}.ram").read_bytes()
E=raw_at('economy',12);D=raw_at('diplomacy',4);nbase=0x474670;cases=[]
def case(name,phase,raw,n,changes):cases.append(dict(name=name,phase=phase,nation=n,changes=changes,base=raw))
n=12;na=nbase+n*1172;wealth=struct.unpack('<i',read(E,na+1072,4))[0];floor=-(wealth//500)
for name,value in [('healthy',10000),('floor-minus1',floor-1),('floor',floor),('floor-plus1',floor+1)]:case('econ-treasury-'+name,'economy',E,n,[(na+1080,4,value)])
for value in [99,100]:case('econ-mobilization-'+str(value),'economy',E,n,[(na+1090,2,value)])
for week in [9,11]:
 for unity in [499,500,649,650]:case(f'econ-tax-week{week}-unity{unity}','economy',E,n,[(0x4a0330,2,week),(na+1088,2,unity),(na+1080,4,1000)])
for treasury in [-1,0,999,1000]:case('econ-tax-treasury-'+str(treasury),'economy',E,n,[(0x4a0330,2,11),(na+1080,4,treasury)])
for count in [39,40]:
 changes=[];cap=short(E,na+1092)
 for slot in range(40):
  for offset,value in enumerate([0,0,100 if slot<count else 0,cap]):changes.append((na+740+slot*8+offset*2,2,value))
 case('econ-queue-'+str(count),'economy',E,n,changes)
for mob in [40,41]:case('dip-mobilization-'+str(mob),'diplomacy',D,4,[(nbase+4*1172+1090,2,mob)])
for season in [2,3]:case('dip-season-'+str(season),'diplomacy',D,4,[(0x4a032e,2,season)])
for wealth in [19999,20000,39999,40000,4000000]:case('dip-wealth-'+str(wealth),'diplomacy',D,4,[(nbase+4*1172+1072,4,wealth)])
# Declare before executing any original control. Input modifications are exact.
write(DATA/'synthetic-manifest-v1.json',[{k:v for k,v in c.items() if k!='base'} for c in cases])
OUT=BASE/'synthetic-v1';OUT.mkdir(exist_ok=False);rows=[]
for index,c in enumerate(cases,1000):
 raw=bytearray(c['base'])
 for address,width,value in c['changes']:struct.pack_into('<h' if width==2 else '<i',raw,address-RAM_BASE,value)
 raw=bytes(raw);u,after,trace=execute(raw,0x44ffbc if c['phase']=='economy' else 0x44fb7c)
 folder=OUT/f"{index:03}-{c['phase']}-{c['nation']}";pair(folder,raw,after)
 row=dict(index=index,caseName=c['name'],phase=c['phase'],nation=c['nation'],**trace)
 if c['phase']=='diplomacy':row['original_facts']=diplomacy_facts(raw)
 rows.append(row);write(folder/'original-result.json',row)
write(DATA/'synthetic-original-v1.json',rows);print(f'Preserved {len(rows)} synthetic original phase controls')
