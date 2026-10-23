"""Exact scalar audit of completed synthetic controls, retaining every gap."""
import json
import struct
from pathlib import Path
from audit_owner import BB, compare, DATA, ROOT

ART = ROOT / 'artifacts/run-exp-battle-parity157'
rows = []
for case in json.loads((DATA / 'pilot-manifest-v1.json').read_text())['cases']:
    label = case['label']
    folder = DATA / label
    if not (folder / 'result.json').exists():
        rows.append(dict(label=label, status='not yet run'))
        continue
    original = json.loads((folder / 'result.json').read_text())
    if not original['complete'] or not (folder / 'native-decisions-v1.json').exists():
        rows.append(dict(label=label, status='incomplete, inspect retained receipt'))
        continue
    hook = json.loads((folder / 'hook-after-writeback.json').read_text())
    ctl = hook['control']
    assert ctl['magic_ok'] and not any(ctl[k] for k in ['overflow', 'reentered', 'busy', 'truncated_reader'])
    assert not hook['chain_breaks'] and not hook['result_misses']
    raw = bytes.fromhex(original['terminal_slots_hex'])
    terminal = dict(slots=[BB.parse_slot(raw[i*44:(i+1)*44], i) for i in range(40)],
                    grid=list(struct.unpack_from('<168h', raw, 1760)))
    draws = [r for r in hook['records'] if r['kind'] == 'random' and r['site'] not in [0x4592bd,0x45951c]]
    start = next(i for i, d in enumerate(draws) if d['seed_before'] == original['entry_seed'])
    draws = draws[start:]
    expected_draws = [(d['eax'],d['result']) for d in draws]
    native = json.loads((folder / 'native-decisions-v1.json').read_text())
    variants = []
    game = ART / 'public' / label / 'runtime/prefix/drive_c/IC2'
    expected_saves = {int(p.stem[6:]):p for p in game.glob('BATTLE*.SAV')
                      if int(p.stem[6:]) >= original['entry']['half_round']}
    for variant in native['fullBattles']:
        observed_draws = [(e['data']['Bound'],e['data']['Value']) for e in variant['events'] if e['type']=='TacticalDrawEvent']
        boundaries = []
        for counter, path in sorted(expected_saves.items()):
            matches = [p for p in variant['phases'] if p['Counter'] == counter]
            boundaries.append(dict(counter=counter,differences=compare(matches[0],BB.block_of_save(path.read_bytes())) if len(matches)==1 else None))
        v = dict(label=variant['label'],counter=variant['Counter'],troops=variant['troops'],
                 terminal_differences=compare(variant,terminal),terminal_rng_equal=variant['RandSeed']==original['terminal_seed'],
                 original_draws=len(draws),native_draws=len(observed_draws),draws_equal=expected_draws==observed_draws,boundaries=boundaries)
        v['exact_measured_match'] = (v['terminal_differences']==0 and v['terminal_rng_equal'] and v['draws_equal']
                                    and variant['Counter']==original['terminal_counter'] and all(b['differences']==0 for b in boundaries))
        variants.append(v)
    rows.append(dict(label=label,status='complete',nations=case['nations'],quality=case['quality'],army_morale=case['army_morale'],
                     original_counter=original['terminal_counter'],original_troops=[sum(s['troops'] for s in terminal['slots'][i:i+20]) for i in (0,20)],
                     original_save_reopen=original['reopen_save']['byte_equal'],variants=variants))
report = dict(scope='Synthetic strategic fixtures, fixed seed1; matched actual original tactical entry, full combat draws and boundary states. Not all features/seeds.',cases=rows)
version = 1
while (DATA/f'pilot-audit-v{version}.json').exists():
    version += 1
with (DATA/f'pilot-audit-v{version}.json').open('x') as f:
    json.dump(report,f,indent=2)
    f.write('\n')
for row in rows:
    print(row['label'],row['status'],[(v['label'],v['exact_measured_match']) for v in row.get('variants',[])])
