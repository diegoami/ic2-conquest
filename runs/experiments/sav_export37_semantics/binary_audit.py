"""Recursive x86 CFG/displacement/relocation leads; unresolved edges stay explicit."""
import argparse, collections, hashlib, json, re
from pathlib import Path
import capstone, pefile
from capstone.x86 import X86_OP_IMM, X86_OP_MEM
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
source=Path('/home/diego/ic2-work/decompile/all_app_functions.txt').read_bytes()
assert hashlib.sha256(source).hexdigest()=='2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8'
exe_path=Path('/home/diego/projects/ic2-work/resupply31/wine-aboard/prefix/drive_c/IC2/Imperial Conquest 2 fast rollingsave seed.exe');raw=exe_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f'
pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
sections=[(base+s.VirtualAddress,base+s.VirtualAddress+s.Misc_VirtualSize,s.get_data()[:s.Misc_VirtualSize]) for s in pe.sections if s.Characteristics&0x20000000]
def code(at):
 for lo,hi,data in sections:
  if lo<=at<hi:return data[at-lo:at-lo+15]
 return b''
seeds={int(m.group(1),16) for m in re.finditer(rb'// ==== .+? @ ([0-9a-fA-F]+) ====',source)}
# Full dump omits some save/DAT/NewGame functions; supplemental originals supply these entry points.
seeds|={0x4481a0,0x4487c4,0x448aa4,base+pe.OPTIONAL_HEADER.AddressOfEntryPoint}
relocated_code_seeds=set()
for block in getattr(pe,'DIRECTORY_ENTRY_BASERELOC',[]):
 for entry in block.entries:
  if entry.type==3:
   target=int.from_bytes(pe.get_data(entry.rva,4),'little')
   if code(target):relocated_code_seeds.add(target)
seeds|=relocated_code_seeds
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);cs.detail=True
pending=list(seeds);decoded={};covered={};overlap=[];fail=[];indirect=[];calls=[];refs=[]
unknown=set(range(0x450,0x46b))|{0x46d,0x491,0x492,0x493}
def nation(value):
 if 0x474670<=value<0x478fb0:
  n,o=divmod(value-0x474670,1172);return dict(nation=n,offset=hex(o),starts_in_unknown=o in unknown)
 return None
while pending:
 at=pending.pop()
 while code(at) and at not in decoded:
  if at in covered:overlap.append(dict(target=hex(at),instruction_start=hex(covered[at])));break
  ins=next(cs.disasm(code(at),at,count=1),None)
  if ins is None:fail.append(hex(at));break
  decoded[at]=ins
  for i in range(ins.size):covered[at+i]=at
  text=ins.mnemonic+' '+ins.op_str
  for op in ins.operands:
   val=op.imm if op.type==X86_OP_IMM else op.mem.disp if op.type==X86_OP_MEM else None
   n=nation(val) if val is not None else None
   if n:refs.append(dict(pc=hex(at),bytes=ins.bytes.hex(),text=text,kind='immediate' if op.type==X86_OP_IMM else 'memory-displacement',size=op.size,access=op.access,base=ins.reg_name(op.mem.base) if op.type==X86_OP_MEM else None,index=ins.reg_name(op.mem.index) if op.type==X86_OP_MEM else None,**n))
  is_call=ins.group(capstone.CS_GRP_CALL);is_jump=ins.group(capstone.CS_GRP_JUMP)
  if is_call or is_jump:
   target=ins.operands[0].imm if ins.operands and ins.operands[0].type==X86_OP_IMM else None
   row=dict(pc=hex(at),bytes=ins.bytes.hex(),text=text,kind='call' if is_call else 'jump',target=hex(target) if target is not None else None)
   if target is None:indirect.append(row)
   else:
    if is_call:calls.append(row)
    if code(target):pending.append(target)
   if is_jump and ins.mnemonic=='jmp':break
  if ins.group(capstone.CS_GRP_RET) or ins.mnemonic in {'int3','ud2','hlt'}:break
  at+=ins.size
relocs=[]
for block in getattr(pe,'DIRECTORY_ENTRY_BASERELOC',[]):
 for entry in block.entries:
  if entry.type!=3:continue
  value=int.from_bytes(pe.get_data(entry.rva,4),'little');n=nation(value)
  if n:relocs.append(dict(location=hex(base+entry.rva),value=hex(value),decoded_instruction=hex(covered[base+entry.rva]) if base+entry.rva in covered else None,**n))
# Resource scalar evidence only; no form/binary content copied into repository.
resources=[]
for typ in pe.DIRECTORY_ENTRY_RESOURCE.entries:
 for name in typ.directory.entries:
  label=str(name.name) if name.name else str(name.id)
  if label not in {'TCHANGETAX','TRENAMEARMYUNIT'}:continue
  for lang in name.directory.entries:
   s=lang.data.struct;b=pe.get_data(s.OffsetToData,s.Size)
   prop=b'\x03Max\x02' if label=='TCHANGETAX' else b'\x09MaxLength\x02'
   assert b.count(prop)==1
   i=b.index(prop)+len(prop)
   resources.append(dict(resource=label,property='Max' if label=='TCHANGETAX' else 'MaxLength',encoded_integer_type=2,value=b[i],resource_sha256=hashlib.sha256(b).hexdigest(),size=len(b),RVA=hex(s.OffsetToData)))
result=dict(method='Recursive disassembly from pinned decompiler function entries, missing supplemental entries, PE entry and ALL executable targets of PE HIGHLOW relocations; follow direct calls/branches and fallthrough. All indirect edges retained unresolved. Does not prove all executable bytes/code entry points or computed-pointer dataflow. Operand starts/displacements are leads, not effective-address/width proof.',exe_sha256=hashlib.sha256(raw).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),capstone_version=capstone.__version__,pefile_version=pefile.__version__,seed_count=len(seeds),relocated_code_seeds=len(relocated_code_seeds),decoded_instructions=len(decoded),covered_code_bytes=len(covered),executable_virtual_bytes=sum(hi-lo for lo,hi,b in sections),decode_failures=fail,overlapping_targets=overlap,direct_calls=len(calls),indirect_edges=indirect,nation_operand_leads=refs,unknown_operand_starts=[r for r in refs if r['starts_in_unknown']],nation_relocations=relocs,unknown_relocations=[r for r in relocs if r['starts_in_unknown']],resources=resources)
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in result.items() if k not in {'method'}}))
