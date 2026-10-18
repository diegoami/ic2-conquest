"""Read-only gates on exactly the owner's three published private SAV references.

Output contains metadata/scalars/booleans only; no save bytes, text or JSON content.
This is not authenticity, semantic compatibility, complete native binding or runtime proof.
"""
import argparse,hashlib,importlib.util,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
REFERENCES=Path('/mnt/c/Users/diego/projects/imperial_conquest_2/rendered/v061-test-fixtures/saves')
NAMES=('1.sav','1_thracia_271_spring_1.sav','1_rome_270_winter_7.sav')

def framing(raw):
 def word(at):
  if not 0<=at<=len(raw)-2:raise ValueError('truncated WORD at computed framing boundary')
  return struct.unpack_from('<h',raw,at)[0]
 na=word(100956)
 if not 0<=na<=198:raise ValueError('army count outside0..198')
 fleet_at=100958+656*na;nf=word(fleet_at)
 if not 0<=nf<=100:raise ValueError('fleet count outside0..100')
 nation_at=fleet_at+2+26*nf;news_at=nation_at+16*1172+600;last=word(news_at)
 if not -1<=last<=39:raise ValueError('news last index outside-1..39')
 tail=news_at+2+61*(last+1)
 if tail+55>len(raw):raise ValueError('truncated strategic trailer')
 battle=raw[tail+54]
 # Full original stream: conditional WORDs2+2+2, BYTE1, WORD2, tactical0x6E0+0x150.
 tactical_size=2+2+2+1+2+0x6e0+0x150 if battle else 0
 if len(raw)!=tail+55+tactical_size:raise ValueError('size does not match complete original strategic/conditional tactical framing')
 order=list(struct.unpack_from('<16h',raw,tail));current=word(tail+36);seat=word(tail+38)
 return dict(armies=na,fleets=nf,nation_at=nation_at,news_last=last,tail=tail,battle=battle,current=current,seat=seat,order=order)

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 provenance=json.loads((ROOT/'runs/experiments/data/run-exp-sav-export37-semantics/reference-availability-v1.json').read_text())
 expected={r['name']:r['sha256'] for r in provenance['references']};assert set(expected)==set(NAMES)
 spec=importlib.util.spec_from_file_location('tax_profile',Path(__file__).with_name('transition_proof.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 rows=[]
 # Controlled parser negatives contain no private input: reject truncation before array indexing.
 for raw in (b'',bytes(100956),bytes(100957)):
  try:framing(raw)
  except ValueError:pass
  else:raise AssertionError('framing truncation check inactive')
 for name in NAMES:
  path=REFERENCES/name;raw=path.read_bytes();before=hashlib.sha256(raw).hexdigest()
  gates={'published_hash_matches':before==expected[name]};reasons=[];metadata={};targets=[]
  try:
   f=framing(raw);no=f['nation_at'];tail=f['tail'];n=f['current']
   gates['complete_original_framing']=True;gates['army_count_within0_198']=0<=f['armies']<=198;gates['fleet_count_within0_100']=0<=f['fleets']<=100
   gates['strategic_no_open_battle']=f['battle']==0;gates['current_nation_within0_15']=0<=n<16
   gates['turn_order_is_permutation']=sorted(f['order'])==list(range(16))
   gates['seat_matches_current_nation']=0<=f['seat']<16 and gates['current_nation_within0_15'] and f['order'][f['seat']]==n
   metadata.update(army_count=f['armies'],fleet_count=f['fleets'],news_last_index=f['news_last'],current_nation_index=n)
   if gates['current_nation_within0_15']:
    at=no+n*1172;read=lambda o:struct.unpack_from('<h',raw,at+o)[0]
    tax=read(0x44a);offer=struct.unpack_from('<h',raw,tail+32)[0];width,height,x,y=(read(o) for o in (0x47c,0x47a,0x488,0x486))
    gates['current_controller_is_human1']=raw[at+0x490]==1;gates['current_tax_within0_40']=0<=tax<=40;gates['pending_offer_source_is_minus1']=offer==-1
    gates['bound_ui_dimensions_within_profile']=271<=width<=1295 and 269<=height<=1005
    gates['bound_viewport_within_map_bounds']=0<=x<=319 and 0<=y<=139
    clamp_x=max(0,min(x,319-(width-15)//32));clamp_y=max(0,min(y,139-(height-45)//32))
    gates['viewport_clamp_is_identity']=(clamp_x,clamp_y)==(x,y)
    metadata.update(current_tax=tax,pending_offer_source=offer)
    for target in (0,40):
     if target==tax:continue
     entry=dict(proposed_tax=target,differs_from_source=True,reference_helper_accepts=False,allowed_tax_word_change_only=False,candidate_file_written=False)
     try:
      projected=module.tax_projection(raw,n,target,width,height,x,y)
      delta=[i for i,(left,right) in enumerate(zip(raw,projected)) if left!=right]
      allowed=set(range(at+0x44a,at+0x44c));assert len(projected)==len(raw) and delta and set(delta)<=allowed
      assert struct.unpack_from('<h',projected,at+0x44a)[0]==target
      entry.update(reference_helper_accepts=True,allowed_tax_word_change_only=True)
      del projected
     except (ValueError,AssertionError,struct.error) as exc:entry['rejection_reason']=str(exc) or type(exc).__name__
     targets.append(entry)
   else:
    for gate in ('current_controller_is_human1','current_tax_within0_40','pending_offer_source_is_minus1','bound_ui_dimensions_within_profile','bound_viewport_within_map_bounds','viewport_clamp_is_identity'):gates[gate]=False
  except (ValueError,struct.error) as exc:
   gates['complete_original_framing']=False;reasons.append(str(exc))
  for gate,ok in gates.items():
   if not ok:reasons.append(gate)
  after=hashlib.sha256(path.read_bytes()).hexdigest();gates['source_hash_unchanged_after_assessment']=before==after
  if before!=after:reasons.append('source hash changed during read-only assessment')
  all_file_gates=all(gates.values()) and bool(targets) and any(t['reference_helper_accepts'] for t in targets)
  rows.append(dict(name=name,size=len(raw),sha256_before=before,sha256_after=after,metadata=metadata,file_checkable_gates=gates,file_checkable_gate_pass=all_file_gates,rejection_reasons=reasons,tax_targets=targets,provenance_runtime_gates={key:'UNVERIFIED' for key in ('source_authentic_version_equivalence','published_original_exe_version_equivalence','complete_native_baseline_binding','trusted_import_tax_only_edit_journal','fresh_load_unselected_no_pending_movement','no_queued_modal_or_unrelated_events','stable_actual_runtime_getters_and_geometry','owner_Windows_runtime_coordination')},full_candidate_approved=False))
  del raw
 result=dict(method='Read-only finite private-reference gates using robust full original stream framing and existing tax_projection in memory. No save bytes/text/private JSON emitted; no candidate file generated. File gates do not prove authenticity/native binding/GUI composition/Windows compatibility.',issue_comment=provenance['issue_comment'],profile='bound-original-current-human-tax-v1 candidate',implementer='gpt-6.1-sol medium (OpenAI)',last_delivered_MAIN_findings_baseline='c8f11fceaa5b414724e7925f025c2185fdbf1dcd',records=rows,parser_truncation_negative_checks=3,changed_candidate_files_written=0,private_JSON_files_read=0,Windows_round_trips=0)
 with a.output.open('x') as out:json.dump(result,out,indent=2);out.write('\n')
 assert all(r['file_checkable_gates']['source_hash_unchanged_after_assessment'] for r in rows)
 print(json.dumps(dict(records=len(rows),file_gate_passes=sum(r['file_checkable_gate_pass'] for r in rows),full_candidates_approved=0,Windows_round_trips=0)))
if __name__=='__main__':main()
