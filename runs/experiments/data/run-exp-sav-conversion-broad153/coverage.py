"""Render explicit coverage levels from a retained comparison receipt."""
import csv,json,sys
from pathlib import Path
from offline import HERE
rows=json.loads((HERE/sys.argv[1]).read_text())
dest=HERE/sys.argv[2]
fields=['case','category','nation','seed','provenance','original_action','export_policy','original_action_verified','original_fresh_reopen','original_save','original_turn','return_import','return_order','return_export_policy','game_field_differences','differential_kind','notes']
with dest.open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for row in rows:
  case=row['case'];original=row['original'];notes=[]
  if original.get('not_run'):notes.append('not yet run in original')
  if original.get('error'):notes.append(original['error']['type']+': '+original['error']['message'])
  continuation=row.get('return_continuation');payload=continuation.get('payload') if continuation else None
  if row.get('input_alignment_receipt'):notes.append('inputs aligned; earlier prediction retained')
  diff=row.get('input_aligned_differential_differences',row.get('action_differential_differences'))
  kind='random continuation, no outcome-equivalence claim' if row.get('action_differential_random') else 'same-input deterministic action'
  if case['originalAction'].get('expect_unchanged') or (case['name'] in ('F04-unit-split','F42-alliance','F43-peace')):notes.append('original refusal control')
  attempts=row.get('original_attempts',[])
  if len(attempts)>1:notes.append(str(len(attempts))+' attempts; earlier failures retained')
  w.writerow(dict(case=case['name'],category=case['category'],nation=case['nation'],seed=case['seed'],provenance=case['provenance'],
   original_action=row.get('executed_original_action',case['originalAction'])['kind'],export_policy='pass' if row['export_success'] and row['policy_pass'] else 'FAIL',
   original_action_verified=original.get('action_verified','pending'),original_fresh_reopen=original.get('reopen_byte_equal','pending'),
   original_save=row.get('original_files',{}).get('reopen',{}).get('file',''),original_turn=row.get('original_saved_turn',''),
   return_import=row.get('return_success',False),return_order=bool(payload and payload.get('changed')),return_export_policy=row.get('return_policy_pass',False),
   game_field_differences=len(diff) if diff is not None else '',differential_kind=kind,notes='; '.join(notes)))
print('Wrote',len(rows),'coverage rows to',dest.name)
