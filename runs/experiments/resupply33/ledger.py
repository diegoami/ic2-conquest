"""Derive debit sums from immutable raw recruitment queues and pinned DAT prices."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3]
ART=ROOT.parent.parent/'resupply31/artifacts'
DAT=ROOT.parent.parent/'resupply31/wine-aboard/prefix/drive_c/IC2/Imperial Conquest 2.dat'
dat=DAT.read_bytes();assert hashlib.sha256(dat).hexdigest()=='94d0ccfc67148d727de4c4e60aefc3c53ba9e67775bd689f0fcb2e23c12e5fbd'
types=['li','hi','ar','lc','hc'];records=[]
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def nation(b):
 o=100958+h(b,100956)*656
 return o+2+h(b,o)*26
for stem in ('land-war-20261017-083008-11228','aboard-war-20261017-084100-17426','fleet-war-20261017-084059-17272'):
 before=(ART/(stem+'-loaded.SAV')).read_bytes();after=(ART/(stem+'-post.SAV')).read_bytes();nb,na=nation(before),nation(after)
 assert all(h(before,nb+0x2e8+8*i)==0 for i in range(40))
 debit=[]
 for i in range(40):
  state,typ,troops,city=struct.unpack_from('<4h',after,na+0x2e4+i*8)
  if troops:
   price=h(dat,0x1f2f0+40*typ+0x22);power=h(dat,0x1f2f0+40*typ+0x26)
   debit.append(dict(slot=i,state=state,type=types[typ],type_index=typ,troops=troops,city=city,initial_price=price,cost=(troops//200)*price,power=(troops//100)*power,dat_price_offset=hex(0x1f2f0+40*typ+0x22),original_price_address=hex(0x478fd2+40*typ)))
 treasury=lambda b,n:struct.unpack_from('<i',b,n+0x438)[0]
 total=sum(x['cost'] for x in debit);observed=treasury(before,nb)-treasury(after,na)
 assert total==observed
 records.append(dict(stem=stem,provenance='Raw original staged-Wine save queues plus source-prescribed arithmetic; phase attribution still to be traced.',treasury_before=treasury(before,nb),treasury_after=treasury(after,na),observed_debit=observed,ledger=debit,total=total,residual=observed-total))
with Path(sys.argv[1]).open('x') as out:json.dump(dict(dat_sha256=hashlib.sha256(dat).hexdigest(),records=records),out,indent=2);out.write('\n')
for r in records:print(r['stem'],[x['cost'] for x in r['ledger']],r['total'],'residual',r['residual'])
