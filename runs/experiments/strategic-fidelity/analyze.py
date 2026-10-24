"""Analyze measured strategic decisions without hiding missing comparisons.

All result files are exclusive new outputs. Outcome differences are different
continuations, not automatically rule defects; local helper rows have gates.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'runs/experiments/data/run-exp-strategic-fidelity';BASE=ROOT/'artifacts/run-exp-strategic-fidelity'
p=argparse.ArgumentParser();p.add_argument('--version',default='v1');p.add_argument('--manifest',default='case-manifest-v2.json');a=p.parse_args()
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
def create(name,value):
    with (DATA/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
manifest=read(DATA/a.manifest);ledger=[];caseRows=[];nations=collections.Counter();commands=collections.Counter();originalSites=collections.Counter();eligibilityCounts=collections.Counter();fromScoreCount=0
for case in manifest['cases']:
    label=case['label'];folder=DATA/(label+'-hook-v1');result=read(folder/'result.json');assert result['complete']
    original=rows(folder/'original-decisions-v1.jsonl');native=rows(folder/'native-decisions-v2.jsonl')
    eligibility={r['snapshot']:r for r in rows(folder/'original-target-eligibility-v1.jsonl')}
    fromScores=rows(folder/'original-target-from-scores-v1.jsonl')
    assert all(r['gate'] and r['originalKind']==r['nativeKind'] for r in fromScores)
    assert len(fromScores)==len(original)
    fromScoreCount+=len(fromScores)
    assert len(original)==len(native)==result['snapshots']
    for old,new in zip(original,native,strict=True):
        assert old['snapshot']==new['snapshot'] and old['army']==new['army'] and new['gate']
        diff=[]
        for name in ['resupply','city','enemy']:
            if old[name]['target']!=new[name]['target']:diff.append(name+'-target')
            elif name!='resupply' and old[name]['target'] is not None and old[name]['score']!=new[name]['score']:diff.append(name+'-score')
        kindEqual=old['decision']['kind']==new['decision']['kind']
        if not kindEqual:diff.append('tree-branch')
        if not kindEqual:destinationEqual=False
        elif old['decision']['kind']==0:destinationEqual=old['city']['target']==new['city']['target']
        elif old['decision']['kind']==1:destinationEqual=old['enemy']['target']==new['enemy']['target']
        elif old['decision']['kind']==3:destinationEqual=old['resupply']['target']==new['decision']['resolvedResupply']
        else:destinationEqual=None  # Mercenary branch continuation is not replayed completely.
        nation=new['nation'];nations[nation]+=1
        for field,key in [('city','originalCityReachable'),('enemy','originalEnemyReachable')]:
            if old[field]['target']!=new[field]['target']:
                eligibilityCounts[field+'_different_targets']+=1
                assert eligibility[old['snapshot']]['gate']
                if eligibility[old['snapshot']][key] is False:eligibilityCounts[field+'_original_winner_excluded']+=1
        ledger.append(dict(case=label,snapshot=old['snapshot'],army=old['army'],nation=nation,
            gate_fields=new['checkedFields'],original_kind=old['decision']['kind'],native_kind=new['decision']['kind'],
            branch_equal=kindEqual,city_target_equal=old['city']['target']==new['city']['target'],
            enemy_target_equal=old['enemy']['target']==new['enemy']['target'],
            raw_resupply_equal=old['resupply']['target']==new['resupply']['target'],
            primary_destination_equal=destinationEqual,original_live_first_call_verified=old['observed_first_call_matches'],
            differences=diff,classification='local helper/tree discrepancy; attribution bounded' if diff else 'compared helper/tree outputs agree',
            evidence=f'{label}-hook-v1/{old["snapshot"]:03}'))
    records=read(folder/'records.json')
    for r in records:originalSites[f'{r["site"]:08x}']+=1
    nativeOutput=read(BASE/'native'/(label+'-v1')/'output.json');assert not nativeOutput['battleOpen']
    routes=read(BASE/'native'/(label+'-v1')/'routes.json')
    for r in routes:
        if r['Kind']==0:commands[r['Identity']]+=1
    # Whole-turn scalar outcome comparison by nation. Inputs are the same
    # campaign but RNG, ordering and later state histories are not aligned.
    actual=read(BASE/'original'/(label+'-hook-v1')/'after.json')
    predicted=read(BASE/'native'/(label+'-v1')/'after.json')
    ids=[n['Id'] for n in predicted['Nations']];nationDifferences=[]
    for i,oldNation in enumerate(actual['nations']):
        newNation=predicted['Nations'][i];name=ids[i]
        oldArmies=[x for x in actual['armies'] if x['owner']==i]
        newArmies=[x for x in predicted['Armies'] if x['Nation']==name]
        summaryOld=dict(army_count=len(oldArmies),troops=sum(x['troops'] for x in oldArmies),treasury=oldNation['treasury'],unity=oldNation['unity'],
            recruits=sum(x['troops'] for x in oldNation['recruit_slots']))
        summaryNew=dict(army_count=len(newArmies),troops=sum(u['Troops'] for x in newArmies for u in x['Units']),treasury=newNation['Treasury'],unity=newNation['Unity'],
            recruits=sum(x['Troops'] for x in newNation['RecruitmentSlots']))
        if summaryOld!=summaryNew:nationDifferences.append(dict(nation=name,original=summaryOld,native=summaryNew))
    caseRows.append(dict(case=label,focus=case['focus'],original_turn=[result['before_turn'],result['after_turn']],
        decisions=len(original),branches_equal=sum(x['original_kind']==x['native_kind'] for x in ledger if x['case']==label),
        raw_resupply_equal=sum(x['raw_resupply_equal'] for x in ledger if x['case']==label),
        whole_turn_scalar_differences=nationDifferences,whole_turn_rng_aligned=False))

for label in ['N-rome','H-seleucid-capital']:
    for boundary in ['before','after']:
        h=next((BASE/'original'/(label+'-hook-v1')).glob('*-'+boundary+'.SAV'))
        plain=next((BASE/'original'/(label+'-plain-v1')).glob('*-'+boundary+'.SAV'))
        assert h.read_bytes()==plain.read_bytes()
assert read(BASE/'native/N-rome-v1/after.json')==read(BASE/'native/N-rome-unobserved-v1/after.json')
assert read(BASE/'native/N-numidia-v1/after.json')==read(BASE/'native/W-rome-gaul-v1/after.json')
neg=read(DATA/'negative-gates-v1.json');assert len(neg)==2 and all(x['rejected'] and not x['output_created'] for x in neg)
controls=read(DATA/'resupply-original-controls-v1.json');nativeControls=rows(DATA/'resupply-native-controls-v2.jsonl')
assert [r['resupply']['target'] for r in nativeControls]==[152,144,152,152,152,159]
assert all(r['gate'] for r in nativeControls)
controlRows=[dict(name=o['name'],original=o['original_resupply'],native=n['resupply']['target'],gate_fields=n['checkedFields']) for o,n in zip(controls,nativeControls,strict=True)]
count=len(ledger);knownDest=[r for r in ledger if r['primary_destination_equal'] is not None]
summary=dict(cases=len(caseRows),byte_distinct_inputs=len({x['input_sha256'] for x in manifest['cases']}),
    original_observed_runs=len(caseRows),original_plain_runs=2,native_normal_runs=len(caseRows)+1,native_unobserved_control_runs=1,
    matched_original_decision_states=count,matched_state_gate_checks=sum(r['gate_fields'] for r in ledger),
    ai_nations_at_compared_boundaries=dict(nations),branches_equal=sum(r['branch_equal'] for r in ledger),
    city_target_equal=sum(r['city_target_equal'] for r in ledger),enemy_target_equal=sum(r['enemy_target_equal'] for r in ledger),
    raw_resupply_equal=sum(r['raw_resupply_equal'] for r in ledger),primary_destination_equal=sum(r['primary_destination_equal'] is True for r in ledger),
    primary_destination_compared=len(knownDest),primary_destination_unresolved=count-len(knownDest),
    original_live_first_calls_verified=sum(r['original_live_first_call_verified'] is True for r in ledger),
    original_cpu_states=792,original_paired_whole_save_controls=2,native_observation_inert=True,negative_input_gates=2,
    original_rng_calls_in_compared_helpers=0,resupply_controls=controlRows,
    original_scores_restore_native_branches=fromScoreCount,target_eligibility_attribution=dict(eligibilityCounts),
    accepted_native_commands=dict(commands),original_observed_call_sites=dict(originalSites),
    limits=['Conditional comparisons test local scorers/tree from original states, not the full native greedy command selection.',
        'Raw resupply target and reachability-resolved destination are reported separately.',
        'No-candidate score sentinels -10000/original and0/native are retained, not counted as distinct target choices.',
        'Whole-turn outcome differences have unmatched RNG/order histories and are not individual defect proofs.',
        'Mercenary-run continuation destinations are unresolved in the primary-destination denominator.',
        'Fleet destination observations, recruitment/economy/diplomacy outcomes are not complete same-input decision/RNG comparisons.',
        'One End turn per case; no all16start, multi-seed campaign, short continuation or Windows acceptance claim.'])
create('summary-'+a.version+'.json',summary);create('cases-'+a.version+'.json',caseRows)
with (DATA/('decision-ledger-'+a.version+'.jsonl')).open('x') as f:
    for r in ledger:f.write(json.dumps(r)+'\n')
with (DATA/('case-summary-'+a.version+'.csv')).open('x',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['case','focus','decisions','branches_equal','raw_resupply_equal','different_nation_scalar_outcomes']);w.writeheader()
    for r in caseRows:w.writerow({k:r[k] for k in ['case','focus','decisions','branches_equal','raw_resupply_equal']}|{'different_nation_scalar_outcomes':len(r['whole_turn_scalar_differences'])})
print(json.dumps({k:v for k,v in summary.items() if k in ['cases','matched_original_decision_states','branches_equal','raw_resupply_equal','primary_destination_equal','primary_destination_compared','primary_destination_unresolved','original_live_first_calls_verified']}))
