"""Read-only audit of retained v1/v2 evidence. Never executes a game or command.

Requires private artifacts. Writes only new versioned receipts and a private
closure manifest; no per-input hashes, original bytes or full states go public.
This is the author's audit, not a separate review or fresh experimental run.
"""
import argparse
import base64
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct
import subprocess

import original as o

R, A, D = o.R, o.A, o.D
NATIVE = R / 'artifacts/run-exp-restrictions85/remake4d70275a'


def load(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def army_shape(a, owners, native=False):
    if native:
        types = ['light_infantry', 'heavy_infantry', 'archers', 'light_cavalry', 'heavy_cavalry']
        return [a['Nation'], a['X'], a['Y'], a['Moves'], a['Morale'], a['Money'],
                a['SupplyTons'], a['AboardFleetId'] is not None, a['CoveredTileCode'],
                [[u['MercenaryLabel'], types.index(u['UnitTypeId']), u['Troops'],
                  u['Quality'], u['Name']] for u in a['Units']]]
    return [owners[a['owner']], a['x'], a['y'], a['moves'], a['morale'], a['money'],
            a['supplies'], a['embarked'], None if a['embarked'] else a['cell'],
            [[u['merc'], o.sav.UNIT_TYPES.index(u['type']), u['troops'], u['quality'],
              u['name']] for u in a['units']]]


def original_shape(s, owners):
    live = {a['id']: army_shape(a, owners) for a in s['armies']
            if a['owner'] >= 0 and a['troops'] > 0}
    return dict(
        armies=sorted(live.values(), key=canonical),
        fleets=[[owners[f['owner']], f['x'], f['y'], f['moves'], f['ships'],
                 f['condition'], f['money'], f['supplies'], live.get(f['army'])]
                for f in s['fleets'] if f['owner'] >= 0 and not f['building']],
        cities=[[c['x'], c['y'], c['owner'], c['allegiance'], c['loyalty'], c['supplies'],
                 c['fort'] + 100*c['fort_pending'], c['pop'], c['max_pop'], c['tribute'],
                 c['name']] for c in s['cities']],
        nations=[[n['treasury'], n['wealth'], n['unity'], n['mobilization'], n['human']]
                 for n in s['nations']])


def native_shape(s, owners):
    armies = {a['Id']: army_shape(a, owners, True) for a in s['Armies']}
    return dict(
        armies=sorted(armies.values(), key=canonical),
        fleets=[[f['Nation'], f['X'], f['Y'], f['Moves'], f['Ships'],
                 f['ConditionPercent'], f['Money'], f['SupplyTons'], armies.get(f['CarriedArmyId'])]
                for f in s['Fleets'] if f['ConstructionTicksRemaining'] is None],
        cities=[[c['X'], c['Y'], owners.index(c['Owner']), owners.index(c['Allegiance']),
                 c['Loyalty'], c['SupplyTons'], c['FortificationCode'], c['PopulationThousands'],
                 c['MaxPopulationThousands'], c['Tribute'], c['Name']] for c in s['Cities']],
        nations=[[n['Treasury'], n['Wealth'], n['Unity'], n['MobilizedPercent'],
                  n['Control'] == 0] for n in s['Nations']])


def normalized_shape(s):
    return {**s, 'armies': sorted(s['armies'], key=canonical)}


def placement(s, world, terrain, post):
    # Independent reading of the pinned last-qualifying scan, not an engine call.
    source, fleet = s['armies'][0], s['fleets'][0]
    centre = (fleet['x'], fleet['y']) if post else (source['x'], source['y'])
    occupied = {(c['x'], c['y']) for c in s['cities']}
    occupied.update((f['x'], f['y']) for f in s['fleets'] if f['owner'] >= 0 and not f['building'])
    occupied.update((a['x'], a['y']) for a in s['armies'] if a['owner'] >= 0 and
                    a['troops'] > 0 and not a['embarked'] and not (post and a['id'] == 0))
    passable = {t['code'] for t in world['tileTypes'] if t['passableByArmies']}
    chosen = None
    for x in range(centre[0]-1, centre[0]+2):
        for y in range(centre[1]-1, centre[1]+2):
            if (0 <= x < world['width'] and 0 <= y < world['height'] and
                    terrain[y*world['width']+x] in passable and (x, y) not in occupied):
                chosen = [x, y]
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    out = D / ('audit-' + args.version + '.json')
    manifest = A / ('closure-' + args.version + '.json')
    disassembly = A / ('source-audit-' + args.version + '.txt')
    assert not any(p.exists() for p in (out, manifest, disassembly)), 'choose a fresh version'
    pins = load(D / 'source-pins-v1.json')
    for pin in pins['files']:
        data = (NATIVE / pin['path']).read_bytes()
        assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == pin['sha'], pin['path']
    # The imported common module checks the full stock EXE identity. No emulator is created.
    source_ranges = [(0x44b79c, 0x44b83d), (0x44f8fc, 0x44fa1f),
                     (0x449f08, 0x44a001), (0x44acb4, 0x44ad36),
                     (0x44ab90, 0x44abde), (0x4492c0, 0x44939c)]
    listings = []
    for start, stop in source_ranges:
        listings.append(subprocess.check_output(['objdump', '-d', '-Mintel',
            f'--start-address={start}', f'--stop-address={stop}',
            '/home/diego/ic2-work/build/Imperial Conquest 2.exe'], text=True))
    text = '\n'.join(listings)
    # Source anchors checked after reading complete functions; preserve raw text privately.
    for anchor in ['44b7e9:', '44b7fb:', '44b806:', '44b80a:', '44b833:',
                   '44f91f:', '44f9c8:', '44f9f8:', '449f3c:', '44ad18:', '44abd6:']:
        assert anchor in text
    with disassembly.open('x') as f:
        f.write(text)
    world = load(NATIVE / 'data/worlds/classical-mediterranean.json')
    owners = [n['id'] for n in world['nations']]
    terrain_bytes = base64.b64decode((NATIVE / 'data/worlds' / world['terrain']['dataFile']).read_bytes())
    terrain = struct.unpack('<' + 'H'*(len(terrain_bytes)//2), terrain_bytes)
    assert len(terrain) == world['width']*world['height']
    private = A / 'private-original-v1'
    initial = load(private / 'hashes.json')
    for name, expected in initial.items():
        assert digest((private / name).read_bytes()) == expected, name
    specs = load(D / 'original-v1-plan.json')
    native = {r['id']: r for r in load(D / 'native-v2.json')}
    comparison = {r['id']: r for r in load(D / 'comparison-v2.json')['rows']}
    groups = defaultdict(list)
    rows = []
    endpoints = 0
    for spec in specs:
        case = spec['id']
        folder = private / case
        original = load(D / ('original-v1_' + case + '.json'))
        parsed = {}
        ram = {}
        for phase in ('before', 'expected'):
            ram[phase] = (folder / (phase + '.ram')).read_bytes()
            saved = (folder / (phase + '.SAV')).read_bytes()
            assert saved == o.old.container(ram[phase]), (case, phase, 'RAM/container')
            parsed[phase] = o.sav.parse(saved)
            assert canonical(parsed[phase]) == canonical(load(folder / (phase + '.json'))), (case, phase, 'SAV/JSON')
            assert normalized_shape(original_shape(parsed[phase], owners)) == normalized_shape(
                load(folder / (phase + '-shape-v2.json'))), (case, phase, 'projection')
            assert canonical(o.summary(ram[phase])) == canonical(original['after' if phase == 'expected' else 'before'])
            endpoints += 1
        groups[digest(ram['before'])].append(case)
        traces = [load(folder / name) for name in ('instruction-trace.json', 'variant-trace.json')]
        assert traces[0]['calls'] == traces[1]['calls']
        assert traces[0]['watched_writes'] == traces[1]['watched_writes']
        for trace in traces:
            for reg in ('ebx', 'esi', 'edi', 'ebp'):
                assert trace['cpu_before'][reg] == trace['cpu_after'][reg]
            assert trace['cpu_after']['esp'] == trace['cpu_before']['esp'] + 4
        calls = [c['site'] for c in traces[0]['calls']]
        assert calls == original['calls'] and 'random' not in calls and 'compactarmy' not in calls
        assert o.read(ram['before'], 0x45e030, 4) == o.read(ram['expected'], 0x45e030, 4)
        raw_negative = [w for w in traces[0]['watched_writes'] if o.ARMY-656 <= w['address'] < o.ARMY]
        if original['negative_index_writes']:
            assert [(w['address'], w['size'], w['value']) for w in raw_negative] == [
                (o.ARMY-656+10, 2, 30), (o.ARMY-656+12, 2, 33)]
            assert o.read(ram['expected'], o.ARMY-656+10, 4) == struct.pack('<2h', 30, 33)
        else:
            assert not raw_negative
        # Every preexisting non-source raw record is unchanged, including occupied candidates.
        b, e = parsed['before'], parsed['expected']
        for i in range(1, len(b['armies'])):
            assert o.read(ram['before'], o.ARMY+656*i, 656) == o.read(ram['expected'], o.ARMY+656*i, 656)
        new = [a for a in e['armies'][len(b['armies']):] if a['owner'] >= 0 and a['troops'] > 0]
        assert len(new) <= 1
        if new:
            assert new[0]['moves'] == 0 and len(e['armies']) == len(b['armies'])+1
        n = native[case]
        row = dict(id=case, endpoints_verified=2, traces_verified=2,
                   original_call_count=len(calls), negative_index_write_count=len(raw_negative),
                   existing_non_source_raw_records_unchanged=True,
                   raw_source_tombstoned=e['armies'][0]['owner'] == -1,
                   raw_compaction_called=False)
        if not spec.get('helper_no_land'):
            state = load(A / 'private-native-v2' / (case+'-state.json'))
            actual = native_shape(state, owners)
            assert actual == normalized_shape(load(A / 'private-native-v2' / (case+'-projection.json')))
            sections = [k for k in actual if actual[k] != original_shape(e, owners)[k]]
            assert sections == n['mismatch_sections']
            assert n == load(D / ('native-v2_'+case+'.json')) == comparison[case]['native']
            assert n['complete_input_projection_equal']
            assert n['pre_placement'] == placement(b, world, terrain, False)
            assert n['post_placement'] == placement(b, world, terrain, True)
            checks = 0
            for a in b['armies']:
                if a['owner'] >= 0 and a['troops'] > 0 and not a['embarked']:
                    assert terrain[a['y']*world['width']+a['x']] == a['cell']
                    checks += 1
            for f in b['fleets']:
                if f['owner'] >= 0 and not f['building']:
                    assert terrain[f['y']*world['width']+f['x']] <= 1
                    checks += 1
            assert checks == n['terrain_checks']
            row.update(native_state_projection_verified=True, terrain_checks=checks,
                       placement_queries_rederived=True, mismatch_sections=sections)
            if new:
                receiver = next(a for a in state['Armies'] if a['Id'].startswith('army-0-overflow'))
                original_receiver = army_shape(new[0], owners)
                native_receiver = army_shape(receiver, owners, True)
                fields = ['owner', 'x', 'y', 'moves', 'morale', 'money', 'supply', 'embarked', 'covered_cell', 'units']
                differences = [name for i, name in enumerate(fields) if original_receiver[i] != native_receiver[i]]
                expected_fields = ['y', 'moves'] if case in ('free-receiver', 'raw197', 'single-all-overflow') else ['x', 'y', 'moves']
                if case == 'single-all-overflow':
                    expected_fields += ['money', 'supply']
                assert differences == expected_fields, (case, differences)
                assert n['post_placement'] == [new[0]['x'], new[0]['y']]
                row['receiver_differing_fields'] = differences
                if case == 'single-all-overflow':
                    assert (e['armies'][0]['money'], e['armies'][0]['supplies']) == (67, 60)
                    row['resource_difference'] = 'original live receiver33/30, source tombstone67/60; native live receiver100/90'
            if not n['accepted']:
                assert n['full_state_unchanged']
                assert actual == original_shape(b, owners)
                row['retained_dispatcher_full_state_unchanged'] = True
                row['independent_input_projection_unchanged'] = True
        rows.append(row)
    duplicate_groups = [g for g in groups.values() if len(g) > 1]
    assert len(groups) == 13
    differing = [r for r in rows if 'receiver_differing_fields' in r]
    assert len(differing) == 8
    # New closure includes all private v1/v2 evidence plus this private source reread.
    files = [p for p in A.rglob('*') if p.is_file()]
    inventory = {str(p.relative_to(A)): dict(bytes=p.stat().st_size, sha256=digest(p.read_bytes())) for p in sorted(files)}
    o.write(manifest, inventory)
    receipt = dict(scope='author read-only audit of retained artifacts; no experimental reexecution',
        source_pin=pins['pin'], source_public_blobs_verified=len(pins['files']), stock_original_identity_verified=True,
        original_endpoints_verified=endpoints, original_trace_records_verified=32,
        original_declared_controls=16, byte_distinct_inputs=13, duplicate_input_groups=duplicate_groups,
        native_full_state_projections_verified=15, retained_input_gates=15,
        placement_queries_independently_rederived=30, original_no_rng_or_compaction_in_retained_traces=True,
        accepted_receiver_discrepancies=8, placement_moves_only_rows=7,
        single_all_overflow_additional_resource_difference=True,
        initial_private_hashes_verified=len(initial), private_closure_files=len(inventory),
        private_closure_manifest=manifest.name, public_per_input_hashes=False,
        reran_original_or_native=False, additional_union_control_run=False,
        full_native_import_reexecution=False, rows=rows)
    o.write(out, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
