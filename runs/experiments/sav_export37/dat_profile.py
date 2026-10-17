"""Independent scalar checks of the original DAT historical baseline/profile."""
import json,hashlib,struct,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3];path=root.parent.parent/'resupply31/wine-aboard/prefix/drive_c/IC2/Imperial Conquest 2.dat';b=path.read_bytes();rows=[]
for n in range(16):
 r=b[0x1b100+1055*n:0x1b100+1055*(n+1)];ids=list(struct.unpack_from('<334h',r,45));count=struct.unpack_from('<h',r,1047)[0]
 assert all(x==-1 for x in ids[count:])
 rows.append(dict(nation=n,name=r[:11].split(b'\0',1)[0].decode('ascii'),population_baseline=struct.unpack_from('<i',r,1033)[0],treasury_baseline=struct.unpack_from('<i',r,1037)[0],cities_baseline=count,city_list_active=ids[:count],inactive_sentinel_all_minus_one=True,neighbour_mask=struct.unpack_from('<H',r,43)[0],conqueror=struct.unpack_from('<h',r,1053)[0]))
public=json.loads((root/'runs/experiments/data/run-exp-sav-export37/public-scalar-audit-initial.json').read_text())
for s in public['records']:
 for row in s['nations']:
  dat=rows[row['nation']]
  assert row['population_baseline']==dat['population_baseline'] and row['treasury_baseline']==dat['treasury_baseline'] and row['cities_baseline']==dat['cities_baseline']
with a.output.open('x') as f:json.dump(dict(provenance='Original DAT scalar profile; no owner-private data. Canonical applicability requires exact scenario/history identity, not merely same counts.',dat_sha256=hashlib.sha256(b).hexdigest(),table_offset='0x1b100',stride=1055,records=rows,public_nation_baseline_matches=224),f,indent=2);f.write('\n')
print('PASS16 DAT rows;224 public nation historical baselines match')
