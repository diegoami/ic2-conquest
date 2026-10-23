"""Validate private evidence and emit ONLY public-safe aggregate facts.

Owner file hashes, complete owner state and full traces never enter Git.
"""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
P=ROOT/'artifacts/run-exp-battle1355/private-v1'
manifest=json.loads((P/'private-input-manifest-v1.json').read_text())
for item in manifest:
 copy=P/'inputs'/item['file'];assert hashlib.sha256(copy.read_bytes()).hexdigest()==item['sha256']
 assert Path(item['source']).read_bytes()==copy.read_bytes()
assert (P/'inputs/classical-mediterranean-saveyy.sav').read_bytes()==(P/'owner-reexport-v1.SAV').read_bytes()
native=json.loads((P/'native-battle-v1/native-general-output.json').read_text())['EndedBattleReport']
assert native['WinnerNationId']=='ptolemaic' and native['WinnerStartTotal']==73564 and native['WinnerFinishTotal']==20946
original=P/'original-end-flow-v3'
r=json.loads((original/'result.json').read_text());assert r['battle_result']['computer_general_clicks']==1 and r['battle_result']['initial_end_turn_clicks']==1
poll=[json.loads(l) for l in (original/'original-battle-poll.jsonl').read_text().splitlines()]
poll=[x for x in poll if 'snapshot' in x];last=poll[-1]['snapshot']['battle']
totals=lambda slots,key:[sum(s[key] for s in slots[i:i+20]) for i in (0,20)]
assert totals(last['slots'],'troops')==[48969,0]
assert (original/'failure.png').exists() # result dialog, visually read48969, matches memory
assert r['error']['message']=='battle_state: no battle pending (flag 0x4A0B7C is 0)'
matched=json.loads((P/'matched-original-v1/matched-final.json').read_text())
matched2=json.loads((P/'matched-original-v2/matched-final.json').read_text())
assert matched==matched2 and matched['State']['IsOver']
assert totals(matched['State']['Slots'],'Troops')==[22090,0]
o=[x['snapshot']['battle'] for x in poll if x['snapshot']['battle']['half_round']==4 and x['snapshot']['battle']['x2']==1]
n=[json.loads(l) for l in (P/'matched-original-v1/matched-observer.jsonl').read_text().splitlines()];n=[x for x in n if x['counter']==4 and x['side']==1]
assert all(x['x2']==1 for x in o) and all(x['side']==1 for x in n)
assert all(totals(x['slots'],'troops')==[73564,78857] for x in o)
assert all(totals(x['Slots'],'Troops')==[73564,78857] for x in n)
positions=[]
for i in range(17):
 a=sorted({(x['slots'][i]['x'],x['slots'][i]['y']) for x in o});b=sorted({(x['Slots'][i]['X'],x['Slots'][i]['Y']) for x in n})
 if a!=b:positions.append(dict(slot=i,original=a,matched_native=b))
assert [x['slot'] for x in positions]==[3,9,11,13,15,16]
summary=dict(owner_originals_preserved=True,fresh_export_byte_equal=True,production_pin='ae614899d63ac721ee46d1e3213191fe1f43a676',
 original_runtime='unmodified original under Wine10.0; suppliedEXE/DAT match',
 army_start_totals=[73564,78857],original_survivors=48969,native_survivors=20946,matched_native_survivors=22090,
 native_repeat_with_journal_equal=True,original_terminal_counter=21,matched_native_terminal_counter=29,
 earliest_completed_boundary=dict(counter=4,side_to_move=1,casualties_yet=False,differing_positions=positions),
 original_memory_snapshots=len(poll),native_actual_frames=1194,
 limits=['Original polling50ms, not instruction-atomic; exact first original instruction/draw not proved',
 'Control assumes clear general claims at placement and computer flags inferred from human/AI ownership',
 'Original battle completed but recorder failed AFTER result when flag cleared; no postbattleSAV/reopen claim',
 'One full unmodified original result; no outcome distribution/seed sweep or productionfix',
 'Initial tactical morale/defender formation differ in natural flows; controlled replay matches those measured inputs',
 'No owner inputs/hashes/fulltraces public; private local aliases only'])
with (HERE/sys.argv[1]).open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
print('PASS private-input preservation, actual outcomes, matched-repeat equality, completed-half movement divergence; no private hashes emitted')
