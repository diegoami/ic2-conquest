"""Decode scalar classification checks on already-public selected SAVs; no output saves."""
from pathlib import Path
import struct,json,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[3]
i16=lambda b,o:struct.unpack_from('<h',b,o)[0]
i32=lambda b,o:struct.unpack_from('<i',b,o)[0]
cstr=lambda b:b.split(b'\0',1)[0].decode('ascii')
rows=[]
for path in sorted((root/'saves').glob('*.SAV')):
 b=path.read_bytes();na=i16(b,100956);fo=100958+656*na;nf=i16(b,fo);no=fo+2+26*nf
 cities=[dict(id=i,name=cstr(b[89600+34*i:89614+34*i]),owner=i16(b,89618+34*i)) for i in range(334)]
 nations=[]
 for n in range(16):
  o=no+1172*n;count=i16(b,o+0x446);ids=list(struct.unpack_from('<334h',b,o+0x48));active=ids[:count]
  own=[c['id'] for c in cities if c['owner']==n];expected=sorted(own,key=lambda x:cities[x]['name'].encode('ascii'))
  names=[cities[x]['name'] for x in active if 0<=x<334]
  nations.append(dict(nation=n,count=count,active_matches_owned=set(active)==set(own) and len(active)==len(own),active_ASCII_sorted=active==expected,list_prefix=active,sentinel=ids[count] if count<334 else None,non_minusone_after_count=sum(v!=-1 for v in ids[count:]),population=i32(b,o+0x430),population_baseline=i32(b,o+0x434),treasury=i32(b,o+0x438),treasury_baseline=i32(b,o+0x43c),cities_baseline=i16(b,o+0x448),conqueror=i16(b,o+0x44e),unknown_450_46a_unique=sorted(set(b[o+0x450:o+0x46b])),flags_46b_46c=list(b[o+0x46b:o+0x46d]),unknown_46d=b[o+0x46d],human=b[o+0x490],unknown_491_493=list(b[o+0x491:o+0x494])))
 turnoff=no+16*1172+600;news=i16(b,turnoff);tail=turnoff+2+61*(news+1)
 rows.append(dict(file=path.name,sha256=hashlib.sha256(b).hexdigest(),armies=na,fleets=nf,nations=nations,pending_offer=list(struct.unpack_from('<2h',b,tail+32)),current=i16(b,tail+36),seat=i16(b,tail+38),week=i16(b,tail+40),year=i16(b,tail+42),season=i16(b,tail+44),battle=b[tail+54]))
record=dict(provenance='Only selected already-public tracked saves, unchanged; no owner-private input, no game/Windows run, no exported candidate.',records=rows)
with a.output.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(saves=len(rows),nation_records=16*len(rows),owned_matches=sum(n['active_matches_owned'] for r in rows for n in r['nations']),ASCII_sorted=sum(n['active_ASCII_sorted'] for r in rows for n in r['nations']))))
