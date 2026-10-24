"""Verify retained diagnostic container against original RAM; scalar audit only."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'runs/experiments/navigation187'));import core as C
p=argparse.ArgumentParser();p.add_argument('--private-input',type=Path,required=True);p.add_argument('--version',required=True);a=p.parse_args()
raw=(a.private_input/'input.ram').read_bytes();b=(a.private_input/'before.SAV').read_bytes();na=C.short(raw,0x4a0324);nf=C.short(raw,0x4a0326)
blocks=[('map',0x45e870,89600),('cities',0x479590,11356)];offset=0
for name,address,size in blocks:assert b[offset:offset+size]==C.read(raw,address,size);offset+=size
assert struct.unpack_from('<h',b,offset)[0]==na;offset+=2
assert b[offset:offset+na*656]==C.read(raw,0x47c1ec,na*656);offset+=na*656
assert struct.unpack_from('<h',b,offset)[0]==nf;offset+=2
for name,address,size in [('fleets',0x49c26c,nf*26),('nations',0x474670,18752),('mercenaries',0x49da10,600)]:assert b[offset:offset+size]==C.read(raw,address,size);offset+=size
parsed=C.sav.parse(b);assert json.loads(json.dumps(parsed))==json.loads((a.private_input/'before.json').read_text())
tail=parsed['tail_off'];assert b[tail:tail+32]==C.read(raw,0x49efe8,32)
for off,address in [(36,0x4a0320),(38,0x4a0322),(40,0x4a0330),(42,0x4a0332),(44,0x4a032e)]:assert struct.unpack_from('<h',b,tail+off)[0]==C.short(raw,address)
result=dict(map_city_army_fleet_nation_queue_relation_mercenary_bytes_equal=True,turn_order_and_seat_calendar_equal=True,decoded_JSON_equals_container=True,news_UI_metadata_not_used_by_scorers=True,owner_state_paths_hashes_published=False,scope='exact relevant RAM-to-diagnostic-container identity; not an original Save As or native Windows acceptance')
with (ROOT/'runs/experiments/data/run-exp-city-army187'/('projection-gate-'+a.version+'.json')).open('x') as f:json.dump(result,f,indent=2)
print('PASS exact relevant original RAM/table-to-container and decoded identity; no private data emitted')
