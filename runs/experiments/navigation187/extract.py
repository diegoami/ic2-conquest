"""Publish interpreted static values and provenance; never publish raw bytes."""
import csv,json
from core import *
dat=Path('/home/diego/ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.dat').read_bytes()
blocks=[('waypoints',0x4790ac,232,0x1f3ea),('routes',0x479194,336,0x1f4d2),('regions',0x4794e8,64,0x1f81e),('coordinate_splits',0x479528,24,0x1f85e)]
ledger=[]
for name,address,size,offset in blocks:
 b=read(RAM,address,size);assert dat[offset:offset+size]==b and dat.find(b)==offset and dat.find(b,offset+1)<0
 count=0
 for p in (ROOT/'artifacts/run-exp-fleet-actions174/live/live-rom-hook-v1/snapshots').glob('*.ram'):
  assert read(p.read_bytes(),address,size)==b;count+=1
 ledger.append(dict(name=name,ram_address=hex(address),dat_offset=hex(offset),bytes=size,static_equal_in_live_snapshots=count))
points=[dict(index=i,x=xy(RAM,0x4790a8+4*i)[0],y=xy(RAM,0x4790a8+4*i)[1],group=0 if i<26 else 1 if i<40 else 2 if i<55 else 3) for i in range(1,59)]
routes=[dict(group=g,row=r,points=list(struct.unpack('<8h',read(RAM,0x479194+g*112+r*16,16)))) for g in range(3) for r in range(7)]
regions=[list(struct.unpack('<4h',read(RAM,0x4794e8+8*i,8))) for i in range(8)]
splits=[xy(RAM,0x479528+4*i) for i in range(6)]
for name,rows in [('waypoints-v1.csv',points),('routes-v1.csv',routes)]:
 with (DATA/name).open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
spec=dict(waypoints=points,routes=routes,regions=regions,coordinate_splits=splits,
 widths='little-endian signed16 x/y and route IDs; point0is not a valid nav point',groups={0:[1,25],1:[26,39],2:[40,54],3:[55,58]},
 hubs={0:9,1:32,2:43},route_shape=[3,7,8],route_padding=-1,group3_route_table_absent=True)
with (DATA/'navigation-data-v1.json').open('x') as f:json.dump(spec,f,indent=2)
with (DATA/'source-pin-v1.json').open('x') as f:json.dump(dict(original_exe_sha256=hashlib.sha256(EXE).hexdigest(),original_dat_sha256=hashlib.sha256(dat).hexdigest(),listing_sha256=hashlib.sha256(DUMP.read_bytes()).hexdigest(),blocks=ledger,
 loader_evidence='pinned news_log_decomp.txt DAT loader reads4790ac:e8,479194:150,4794e8:40,479528:18; SAV layout has no nav section'),f,indent=2)
print('Verified58points,3x7x8routes,8boxes,6coordinate splits against unique DAT blocks and30live snapshots')
