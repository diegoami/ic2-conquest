"""Pin targeted original function extracts; outputs are exclusive and immutable."""
import re,json,hashlib,argparse,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
source=Path('/home/diego/ic2-work/decompile/all_app_functions.txt');raw=source.read_bytes();lines=raw.decode().splitlines()
starts=[(i,re.search(r'// ==== (.+?) @ ([0-9a-fA-F]+) ====',line)) for i,line in enumerate(lines)];starts=[(i,m.group(1),m.group(2)) for i,m in starts if m]
ranges=[(0x474670,0x474b04,'nation0'),(0x47c1ec,0x47c47c,'army0'),(0x49c26c,0x49c286,'fleet0'),(0x4a031c,0x4a0338,'globals'),(0x49f008,0x49f00c,'pending_offer')]
functions=[];refs=[]
for n,(start,name,addr) in enumerate(starts):
 end=starts[n+1][0] if n+1<len(starts) else len(lines);hits=[]
 for i in range(start,end):
  for m in re.finditer(r'(?:DAT_|PTR_|UNK_)([0-9a-fA-F]{8})',lines[i]):
   value=int(m.group(1),16)
   for lo,hi,label in ranges:
    if lo<=value<hi:hits.append(dict(line=i+1,address=hex(value),region=label,text=lines[i]))
 if hits:
  functions.append(dict(name=name,address='0x'+addr,first_line=start+1,last_line=end,lines=[f'{i+1}: {lines[i]}' for i in range(start,end)],references=hits));refs.extend(dict(function=name,**h) for h in hits)
record=dict(source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),method='Targeted named-global reference inventory, not proof of exhaustive pointer-alias coverage.',functions=functions,references=refs)
with a.output.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(functions=len(functions),references=len(refs),source_sha256=record['source_sha256'])))
