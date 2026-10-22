"""Read-only metadata comparison of the owner-created original Windows control1 saves."""
import argparse,hashlib,importlib.util,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
FILES={
 'source':(Path('/mnt/c/Users/diego/projects/imperial_conquest_2/rendered/v061-test-fixtures/saves/1.sav'),'d20971d5c73a39c82bb9a6c76413394d1d6fc8174bf5ae857a8161eaba5d7c10'),
 'candidate':(Path('/mnt/c/Users/diego/projects/imperial_conquest_2/rendered/sav-export-candidates/bound-original-tax-only/t184-tax-1-n0-0.SAV'),'5e85a985382dc56ae964889ed01d4fda56b0e2414ccaede5e18d03b3bd2a314c'),
 'control_before':(Path('/mnt/c/Users/diego/Documents/ic2-tax-native/20261018T085043Z/C1B68B2.SAV'),'26c4cc3b6b963fb45ac1b41d4ad45bb741f0ed3d747f1338d8eec897379a2574'),
 'control_after':(Path('/mnt/c/Users/diego/Documents/ic2-tax-native/20261018T085043Z/C1T68B2.SAV'),'27f2aaee278f836ae33747604800847943dd836a6865ec875c49d5f5181faa66')}

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 spec=importlib.util.spec_from_file_location('projection',ROOT/'runs/experiments/sav_export37_semantics/transition_proof.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 raw={role:path.read_bytes() for role,(path,digest) in FILES.items()};hashes={role:hashlib.sha256(b).hexdigest() for role,b in raw.items()}
 assert all(hashes[role]==expected for role,(path,expected) in FILES.items())
 assert {len(b) for b in raw.values()}=={131313}
 layouts={role:module.layout(b) for role,b in raw.items()};assert len(set(layouts.values()))==1
 na,fo,nf,no,news,last,tail=layouts['source'];spans=module.spans(raw['source'])
 assert [(off,size) for _,_,size,off in spans if size]==[(off,size) for _,_,size,off in module.spans(raw['control_after']) if size]
 # Every byte belongs to exactly one original serialized span, with no gaps.
 coverage=[i for _,at,size,off in spans for i in range(off,off+size)];assert coverage==list(range(131313))
 rd=lambda b,off:struct.unpack_from('<h',b,off)[0]
 fields={0x44a:'tax',0x46e:'area_map_left',0x470:'area_map_top',0x472:'area_map_height',0x474:'area_map_width',0x476:'unit_map_left',0x478:'unit_map_top',0x47a:'unit_map_height',0x47c:'unit_map_width',0x47e:'information_left',0x480:'information_top',0x482:'information_height',0x484:'information_width',0x486:'viewport_y',0x488:'viewport_x'}
 def scalar_state(b):
  return dict(army_count=na,fleet_count=nf,news_last_index=last,current_nation=rd(b,tail+36),seat=rd(b,tail+38),week=rd(b,tail+40),year=rd(b,tail+42),season=rd(b,tail+44),pending_offer_source=rd(b,tail+32),pending_offer_type=rd(b,tail+34),battle_flag=b[tail+54],current_nation_fields={name:rd(b,no+offset) for offset,name in fields.items()},main_window_geometry=list(struct.unpack_from('<4h',b,tail+46)))
 states={role:scalar_state(b) for role,b in raw.items()}
 assert all(s['current_nation']==0 for s in states.values())
 def classify(offset):
  for name,at,size,start in spans:
   if start<=offset<start+size:
    result=dict(serialized_region=name,offset_decimal=offset)
    if name=='nations':
     n,o=divmod(offset-no,1172);result.update(nation=n,nation_relative_offset=hex(o))
     for field,name in fields.items():
      if field<=o<field+2:result['field']=name;result['field_WORD_offset_decimal']=no+n*1172+field
    return result
  raise AssertionError('unclassified serialized byte')
 comparisons=[]
 for left,right in [('source','control_before'),('source','candidate'),('control_before','control_after'),('candidate','control_after')]:
  diffs=[i for i,(a,b) in enumerate(zip(raw[left],raw[right])) if a!=b]
  classified=[classify(o) for o in diffs];by_region=[]
  for name,at,size,start in spans:
   hits=[o for o in diffs if start<=o<start+size];by_region.append(dict(region=name,size=size,changed_byte_count=len(hits),changed_offsets_decimal=hits))
  word_offsets=sorted({c['field_WORD_offset_decimal'] for c in classified if 'field_WORD_offset_decimal' in c})
  scalar_changes=[dict(field=next(c['field'] for c in classified if c.get('field_WORD_offset_decimal')==o),WORD_offset_decimal=o,before=rd(raw[left],o),after=rd(raw[right],o)) for o in word_offsets]
  comparisons.append(dict(before=left,after=right,changed_byte_count=len(diffs),changed_offsets_decimal=diffs,classified_changes=classified,scalar_WORD_changes=scalar_changes,all_serialized_regions=by_region))
 control=next(c for c in comparisons if c['before']=='control_before');assert control['changed_offsets_decimal']==[111294,111330,111331,111332,111333]
 assert control['scalar_WORD_changes']==[dict(field='tax',WORD_offset_decimal=111294,before=10,after=0),dict(field='area_map_left',WORD_offset_decimal=111330,before=2,after=1168),dict(field='area_map_top',WORD_offset_decimal=111332,before=72,after=293)]
 assert all(s['current_nation_fields']['viewport_x']==97 and s['current_nation_fields']['viewport_y']==39 for s in states.values())
 assert all(c['serialized_region']=='nations' and c.get('field') in {'tax','area_map_left','area_map_top'} for c in control['classified_changes'])
 after_hashes={role:hashlib.sha256(path.read_bytes()).hexdigest() for role,(path,_) in FILES.items()};assert after_hashes==hashes
 result=dict(method='Read-only whole-file and complete serialized-span comparison of exact owner-created reference control1 before/after saves, immutable source and physical production candidate. Metadata/offsets/scalars only; no buffers/unit names/private JSON emitted; no file/process/UI action.',files={role:dict(name=path.name,size=len(raw[role]),sha256=hashes[role],sha256_after_readonly_comparison=after_hashes[role],unchanged=True) for role,(path,_) in FILES.items()},scalar_states=states,comparisons=comparisons,control1_result=dict(expected_tax_change_observed_in_files=True,area_map_window_left_top_changed=True,area_map_before=[2,72],area_map_after=[1168,293],viewport_changed=False,viewport_x=97,viewport_y=39,extra_gameplay_byte_changes=False,all_other_serialized_bytes_equal_between_control_saves=True,exact_UI_geometry_identity=False),owner_visual_dialog_or_window_movement_observation='PENDING with parent',internal_GUI_callback_trace='NOT_ESTABLISHED by saved files',Windows_candidate_cases_completed=0,reference_control_is_completed_candidate_case=False,child_process_or_UI_actions=0,child_save_writes=0)
 with args.output.open('x') as out:json.dump(result,out,indent=2);out.write('\n')
 print(json.dumps(dict(control_changed_bytes=5,tax_change=[10,0],area_map_left_top=[[2,72],[1168,293]],viewport_changed=False,extra_gameplay_byte_changes=False,source_candidate_controls_unchanged=True,completed_candidate_cases=0)))
if __name__=='__main__':main()
