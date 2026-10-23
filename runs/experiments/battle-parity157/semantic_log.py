"""Join complete original snapshots/draws into semantic action logs.

No port data is used to reconstruct original actions. Full raw states remain
authoritative; unmatched boundaries, record holes and incomplete draws fail.
Owner invocation writes only into its private folder.
"""
import argparse
import collections
import json
import sys
from pathlib import Path
import semantic_observer as O
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from state import hook_log as L

p = argparse.ArgumentParser()
p.add_argument('folder', type=Path)
args = p.parse_args()
folder = args.folder
hook = json.loads((folder / 'hook.json').read_text())
states = json.loads((folder / 'states.json').read_text())
assert not states['overflow'] and not hook['chain_breaks'] and not hook['result_misses']
assert not L.chain_check(hook['records'], sites=O.H.SITES) and not L.result_check(hook['records'])
ctl = hook['control']
assert ctl['magic_ok'] and not any(ctl[k] for k in ['overflow','reentered','busy','truncated_reader'])
assert len(states['records']) == len(hook['records'])
by_seq = {s['seq']:s for s in states['records']}
stacks = collections.defaultdict(list)
actions = []
events = []
pending_melee = None
names = {0x438d24:'walk',0x438a6c:'step',0x43910c:'shot',0x4393ec:'melee_pass',
         0x438fb0:'rout',0x438f78:'remove'}
exits = {0x438f70:'walk',0x438d1b:'step',0x439397:'shot',0x439906:'melee_pass',
         0x439104:'rout',0x438fa2:'remove'}
MELEE = [0x439557,0x43955f,0x4395ce,0x4395d8]
SHOT = [0x439188,0x439191]

def signed(v):
    return v if v < 2**31 else v - 2**32

def action(kind, start, end, **values):
    row = dict(kind=kind, begin_seq=start['seq'], end_seq=end['seq'],counter=start['counter'],**values)
    actions.append(row)
    return row

previous = None
for r in hook['records']:
    s = by_seq[r['seq']]
    assert s['seq'] == r['seq'] and s['seed_before'] == r['seed_before'] and r['seq_ok']
    assert s['site'] == hex(r['site']) and s['kind'] == r['kind']
    assert s['counter'] == r['counter'] and s['side'] == r['side']
    assert r['kind'] in ['random','marker','flag_clear','start','reseed']
    if r['kind'] == 'marker':
        assert r['site'] in {entry for _,entry,_ in O.H.MARKERS}
    site = r['site']
    event = dict(seq=r['seq'], counter=r['counter'], side=r['side'], site=hex(site),kind=r['kind'],
                 seed_before=r['seed_before'], seed_after=r['seed_after'],provenance='original semantic pre-call snapshot; completed draw joined by sequence')
    if previous is not None:
        event['slot_changes'] = [dict(slot=i,before=previous['slots'][i],after=s['slots'][i])
                                 for i in range(40) if previous['slots'][i] != s['slots'][i]]
        event['grid_changes'] = [dict(cell=i,before=a,after=b) for i,(a,b) in enumerate(zip(previous['grid'],s['grid'],strict=True)) if a != b]
        event['claim_changes'] = [dict(actor=i,before=a,after=b) for i,(a,b) in enumerate(zip(previous['actor_claim_targets'],s['actor_claim_targets'],strict=True)) if a != b]
    previous = s
    if r['kind'] == 'random':
        event.update(bound=r['eax'],value=r['result'])
        if site == MELEE[0]:
            assert pending_melee is None
            # Original ESP includes the Random call's return address. Routine local
            # +0 packs actor/focus; +12/+16 contain the two computed powers.
            actor = s['stack_words'][1] & 65535
            assert 0 <= actor < 40
            target = s['slots'][actor]['target']
            assert 0 <= target < 40
            pending_melee = dict(start=s,actor=actor,target=target,draws=[],
                                 focus=s['stack_words'][1]>>16,
                                 attacker_power=signed(s['stack_words'][4]),defender_power=signed(s['stack_words'][5]))
        if site in MELEE:
            assert pending_melee is not None
            pending_melee['draws'].append(r)
        if site in SHOT:
            assert stacks['shot']
            stacks['shot'][-1]['draws'].append(r)
    elif r['kind'] == 'marker':
        if site == 0x438fb0:
            if pending_melee is not None:
                m = pending_melee
                assert [d['site'] for d in m['draws']] == MELEE
                actor,target=m['actor'],m['target']
                before=m['start']['slots'];after=s['slots']
                action('melee',m['start'],s,actor=actor,target=target,
                       focus=m['focus'],attacker_power=m['attacker_power'],defender_power=m['defender_power'],
                       attacker_bound=m['draws'][0]['eax'],defender_bound=m['draws'][2]['eax'],
                       attacker_loss=before[actor]['troops']-after[actor]['troops'],
                       defender_loss=before[target]['troops']-after[target]['troops'],
                       attacker_troops=after[actor]['troops'],defender_troops=after[target]['troops'],
                       attacker_morale=after[actor]['morale'],defender_morale=after[target]['morale'],
                       draw_values=[d['result'] for d in m['draws']],
                       input_slots=[before[actor],before[target]],input_provenance='Observed before first melee draw; actor/focus/powers from original stack locals')
                pending_melee=None
            if stacks['shot'] and not stacks['shot'][-1].get('logged'):
                shot=stacks['shot'][-1]
                assert [d['site'] for d in shot['draws']] == SHOT
                actor,target=shot['actor'],shot['target']
                before=shot['start']['slots'][target];after=s['slots'][target]
                action('shot',shot['start'],s,actor=actor,target=target,bound=shot['draws'][0]['eax'],
                       loss=before['troops']-after['troops'],morale_loss=before['morale']-after['morale'],
                       target_troops=after['troops'],target_morale=after['morale'],
                       draw_values=[d['result'] for d in shot['draws']],
                       input_slots=[shot['start']['slots'][actor],before])
                shot['logged']=True
        if site in names:
            kind=names[site]
            item=dict(start=s,draws=[])
            if kind in ['walk','shot','rout','remove']:
                item['actor']=r['eax'] & 65535
            if kind == 'walk':
                item['goal']=[r['edx'] & 65535,r['edx'] >> 16]
            elif kind == 'step':
                assert stacks['walk']
                item['actor']=stacks['walk'][-1]['actor']
            elif kind == 'shot':
                item['target']=r['edx'] & 65535
            stacks[kind].append(item)
        if site in exits:
            kind=exits[site]
            assert stacks[kind], (r['seq'],kind,'unmatched exit')
            item=stacks[kind].pop()
            if kind == 'step':
                actor=item['actor'];before=item['start']['slots'][actor];after=s['slots'][actor]
                moved=(before['x'],before['y']) != (after['x'],after['y'])
                action('move' if moved else 'step_without_move',item['start'],s,actor=actor,
                       from_x=before['x'],from_y=before['y'],to_x=after['x'],to_y=after['y'],
                       moves_before=before['moves'],moves_left=after['moves'])
            elif kind == 'walk':
                actor=item['actor']
                action('walk',item['start'],s,actor=actor,goal=item['goal'],before=item['start']['slots'][actor],after=s['slots'][actor])
            elif kind == 'remove':
                action('remove',item['start'],s,actor=item['actor'])
            elif kind == 'shot':
                assert item.get('logged'), 'Shot returned without observed pre-rout completion'
            elif kind == 'rout':
                action('rout_check',item['start'],s,actor=item['actor'],before=item['start']['slots'][item['actor']],after=s['slots'][item['actor']])
    events.append(event)

assert pending_melee is None and not any(stacks.values()), {k:len(v) for k,v in stacks.items() if v}
for name,rows in [('semantic-events-v1.jsonl',events),('semantic-actions-v1.jsonl',actions)]:
    with (folder/name).open('x') as f:
        for row in rows:
            f.write(json.dumps(row,separators=(',',':'))+'\n')
report=dict(records=len(events),actions_by_kind=dict(collections.Counter(x['kind'] for x in actions)),
            sequence_complete=True,boundaries_balanced=True,
            provenance='Direct original semantic snapshots; melee actor/focus/powers decoded from guarded original stack layout, not port predictions',
            limits='Full raw snapshots are authoritative. Placement is captured as routine/setup boundaries, not every individual placement write. Strategic writeback is a separate save.')
with (folder/'semantic-summary-v1.json').open('x') as f:
    json.dump(report,f,indent=2)
    f.write('\n')
print(json.dumps(report))
