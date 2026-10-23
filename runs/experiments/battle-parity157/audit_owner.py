"""Publish scalar checks only. Owner inputs, hashes and full states stay private."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state import battle_block as BB

BASE = ROOT / 'artifacts/run-exp-battle-parity157/private'
OBS = BASE / 'owner-seed1-prefix-v1'
PLAIN = BASE / 'owner-seed1-plain-v1'
DATA = ROOT / 'runs/experiments/data/run-exp-battle-parity157'
FIELDS = dict(x='X', y='Y', merc='Origin', type='Type', troops='Troops', quality='Quality',
              morale='Morale', state='Moves', ammo='Shots', target='Target', name='Name')

def read(path):
    return json.loads(path.read_text())

def compare(native, block):
    differences = 0
    for actual, expected in zip(native['Slots'], block['slots'], strict=True):
        for old, new in FIELDS.items():
            value = expected[old]
            if old == 'type' and isinstance(value, str):
                value = BB.TYPES.index(value)
            differences += actual[new] != value
    differences += sum(a != b for a, b in zip(native['Grid'], block['grid'], strict=True))
    return differences

if __name__ == '__main__':
    obs, plain = read(OBS / 'result.json'), read(PLAIN / 'result.json')
    assert obs['complete'] and plain['complete']
    game = lambda p: p / 'runtime/prefix/drive_c/IC2'
    boundary_equal = [(game(OBS) / f'BATTLE{i:02d}.SAV').read_bytes() ==
                      (game(PLAIN) / f'BATTLE{i:02d}.SAV').read_bytes() for i in range(1, 16)]
    hook = read(OBS / 'hook-after-writeback.json')
    assert not hook['chain_breaks'] and not hook['result_misses']
    ctl = hook['control']
    assert ctl['magic_ok'] and not any(ctl[k] for k in ['overflow', 'reentered', 'busy', 'truncated_reader'])
    inert = all(boundary_equal) and all(obs[k] == plain[k] for k in ['terminal_slots_hex', 'terminal_seed', 'terminal_counter'])
    assert inert
    result = read(OBS / 'native-decisions-v5.json')
    rows = result['results']
    assert len(rows) == 60 and all(r['targetEqual'] and r['walksEqual'] and not r['choiceStateDifferences']
                                  and not r['afterDifferences'] for r in rows)
    proof = result['threatOrderProof'][:3]
    assert all(r['sharedGameplayInput'] for r in proof)
    assert [(r['originalActor'], r['nativeActor']) for r in proof] == [(0, 0), (1, 1), (2, 10)]
    raw = bytes.fromhex(obs['terminal_slots_hex'])
    terminal = dict(slots=[BB.parse_slot(raw[i * 44:(i + 1) * 44], i) for i in range(40)],
                    grid=list(struct.unpack_from('<168h', raw, 1760)))
    variants = []
    for native in result['fullBattles']:
        boundaries = []
        for phase in native['phases']:
            path = game(OBS) / f'BATTLE{phase["Counter"]:02d}.SAV'
            if path.exists():
                boundaries.append(dict(counter=phase['Counter'], differences=compare(phase, BB.block_of_save(path.read_bytes()))))
        variants.append(dict(label=native['label'], counter=native['Counter'], troops=native['troops'],
                             terminal_differences=compare(native, terminal),
                             terminal_rng_equal=native['RandSeed'] == obs['terminal_seed'],
                             boundaries=boundaries))
    fixed = next(r for r in variants if r['label'] == 'slot-both-later-passes')
    assert fixed['counter'] == 15 and fixed['troops'] == [0, 51178]
    assert fixed['terminal_differences'] == 0 and fixed['terminal_rng_equal']
    assert len(fixed['boundaries']) == 14 and all(r['differences'] == 0 for r in fixed['boundaries'])
    report = dict(scope='Fresh fixed-seed1 owner after-End input; distinct from historical natural-RNG outcome. Wine original, diagnostic native iteration alternatives.',
                  owner_data_published=False, original_observer_inert=True, byte_identical_boundary_saves=15,
                  original_save_and_fresh_reopen=True, original_counter=obs['terminal_counter'], original_troops=[0, 51178],
                  pass1_engagements_compared=60, pass1_targets_goals_slots_grid_claims_all_equal=True,
                  first_actor_order_difference=dict(counter=3, original_seq=78, original_actor=2, native_actor=10,
                                                    preceding_actors=[0,1], shared_slots_grid_claim_counts=True),
                  variants=variants,
                  limits=['Original semantic snapshots stop after counter6; complete movement-step/exchange-exit logs not yet available.',
                          'Native boundary comparison covers after-placement/movement slots, names and grid, not strategic writeback.',
                          'Initial selected slot was not sampled; diagnostic native entry uses -1.',
                          'Iteration alternatives are task harness controls, not a production fix or full318-corpus acceptance.',
                          'Native Windows and other hypotheses outside measured controls remain open.'])
    semantic = BASE / 'owner-seed1-semantic-v1'
    if (semantic / 'semantic-comparison-v1.json').exists():
        current = read(semantic / 'result.json')
        full = read(semantic / 'native-decisions-v1.json')
        assert current['complete'] and current['entry_selected'] == -1
        assert all(current[k] == plain[k] for k in ['terminal_slots_hex','terminal_seed','terminal_counter'])
        assert all((game(semantic)/f'BATTLE{i:02d}.SAV').read_bytes() ==
                   (game(PLAIN)/f'BATTLE{i:02d}.SAV').read_bytes() for i in range(1,16))
        comparison = semantic / 'semantic-comparison-v2.json'
        checks = read(comparison if comparison.exists() else semantic / 'semantic-comparison-v1.json')
        corrected = next(v for v in checks['variants'] if v['label']=='slot-both-later-passes')
        assert corrected['all_equal']
        hooks = read(semantic / 'hook.json')['records']
        combat = [r for r in hooks if r['kind']=='random' and r['site'] not in [0x4592bd,0x45951c]]
        begin = next(i for i,r in enumerate(combat) if r['seed_before']==current['entry_seed'])
        combat = combat[begin:]
        fixed = next(v for v in full['fullBattles'] if v['label']=='slot-both-later-passes')
        draws = [e['data'] for e in fixed['events'] if e['type']=='TacticalDrawEvent']
        assert [(r['eax'],r['result']) for r in combat] == [(r['Bound'],r['Value']) for r in draws]
        report['full_semantic_validation'] = dict(observer_inert=True, byte_identical_boundary_saves=15,
            actual_initial_selected=current['entry_selected'],summary=read(semantic / 'semantic-summary-v1.json'),
            combat_draws=len(combat),combat_draws_exact=True,
            variants=[dict(label=v['label'],all_equal=v['all_equal'],checks=[dict(kind=c['kind'],original_count=c['original_count'],native_count=c['native_count'],equal=c['equal'],
                first_difference_index=c['first_difference']['index'] if c['first_difference'] else None) for c in v['checks']]) for v in checks['variants']])
        report['limits'] = ['Individual placement-write order and every silent target write are not asserted.',
                            'Native strategic writeback and full318-corpus acceptance remain open.',
                            'Native Windows and other hypotheses outside measured controls remain open.']
    historical = BASE / 'historical-entry-assumption-control-v1/native-counterfactual-v1.json'
    if historical.exists():
        h = read(historical)['fullBattles']
        assert h[0]['troops']==[22090,0] and h[2]['troops']==[48969,0] and h[2]['Counter']==21
        report['historical_entry_assumption_control'] = dict(
            provenance='Same earlier entry reconstruction, explicitly assumed clear flags/claims and selected=-1; missing original runtime fields not backfilled.',
            variants=[dict(label=r['label'],counter=r['Counter'],troops=r['troops']) for r in h],
            survivor_and_counter_match_original=True, exact_historical_event_equality_not_claimed=True)
    version = 1
    while (DATA / f'owner-iteration-audit-v{version}.json').exists():
        version += 1
    with (DATA / f'owner-iteration-audit-v{version}.json').open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report, indent=2))
