"""Audit the completed, immutable experiment; no game execution or regeneration."""
import hashlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path
from compare import ART, HERE, sav

summary = json.loads((HERE / 'comparison-v6.json').read_text())
assert len(summary['native_export_import']) == 6
assert len(summary['original_sessions']) == 7
assert len(summary['returned_sessions']) == 7
checks = []
manifest_files = 0
for name in ('batch1-conversions', 'batch2-complete'):
    m = json.loads((HERE / (name + '-manifest.json')).read_text())
    assert hashlib.sha256((ART / m['archive']).read_bytes()).hexdigest() == m['sha256']
    for row in m['files']:
        p = ART / row['file']
        assert p.stat().st_size == row['bytes']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256']
        manifest_files += 1
    checks.append(name + ': archive and every listed artifact SHA256 match')
ui_words = []
for name, comparisons in summary['original_sessions'].items():
    receipt = json.loads((HERE / (name + '.json')).read_text())
    assert receipt['complete'] and receipt['input_unchanged'] and receipt['order']['verified']
    source = ART / receipt['input']['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == receipt['input']['sha256']
    s = sav.load(source)
    nbase = 100956 + 2 + len(s['armies']) * 656 + 2 + len(s['fleets']) * 26
    c = comparisons['comparisons']
    assert c['export_vs_original_immediate']['semantic_differences'] == []
    assert c['export_vs_original_immediate']['lengths'][0] == c['export_vs_original_immediate']['lengths'][1]
    assert c['export_vs_original_immediate']['differing_offsets'] == [nbase + 0x482]
    assert c['immediate_vs_tax_order']['semantic_differences'] == [
        {'path': '/nations/0/tax', 'before': receipt['order']['before'], 'after': 26}]
    assert c['immediate_vs_tax_order']['differing_offsets'] == [nbase + 0x44A]
    assert c['original_save_vs_reopen_resave']['byte_equal']
    first = next(x for x in receipt['steps'] if x['label'] == 'immediate-native-save')
    raw_a = source.read_bytes()
    raw_b = (ART / first['file']).read_bytes()
    ui_words.append({'case': name, 'nation_relative_offset': '0x482',
        'before': struct.unpack_from('<h', raw_a, nbase + 0x482)[0],
        'after': struct.unpack_from('<h', raw_b, nbase + 0x482)[0]})
    for step in receipt['steps']:
        assert hashlib.sha256((ART / step['file']).read_bytes()).hexdigest() == step['sha256']
    continued = summary['returned_sessions'][name]
    assert continued['remake_order_differences'] == [
        {'path': '/nations/0/taxRatePercent', 'before': 26, 'after': 27}]
    assert continued['rng_advanced_once']
    assert continued['original_vs_remake_reexport']['semantic_differences'] == [
        {'path': '/nations/0/tax', 'before': 26, 'after': 27}]
    assert json.loads((HERE / ('return-' + name + '-v2.json')).read_text())['returncode'] == 0
    assert json.loads((HERE / ('reexport-' + name + '-v2.json')).read_text())['returncode'] == 0
    assert json.loads((HERE / ('reexport-policy-' + name + '-v2.json')).read_text())['returncode'] == 0
checks.append('7 original sessions: UI-only immediate change; tax-only order; byte-identical fresh reopen; unchanged input')
checks.append('7 returned remake sessions: reload/resume succeeds; tax27 is the only normalized state change; reexport policy passes')
native_diffs = {}
allowed = {'cityCountAtStart', 'population', 'populationAtStart', 'treasuryAtStart', 'turnIndex', 'coveredTileCode'}
for name, entry in summary['native_export_import'].items():
    counts = Counter(d['path'].split('/')[-1] for d in entry['differences'])
    assert set(counts) <= allowed
    assert json.loads((HERE / ('policy-native-' + name.removeprefix('native-') + '-v3.json')).read_text())['returncode'] == 0
    native_diffs[name] = dict(counts)
checks.append('6 source exports: policy passes; all native differences explicitly classified (not claimed equal)')
negative = json.loads((HERE / 'export-negative-improved-v2.json').read_text())
assert negative['returncode'] == 2 and 'UNSUPPORTED_RULESET' in negative['stderr']
assert not (ART / 'exports-v2/negative-improved.SAV').exists()
negative2 = json.loads((HERE / 'negative-overwrite-integrity-v1.json').read_text())
assert negative2['returncode'] == 2 and negative2['unchanged']
checks.append('2 refusal controls: unsupported ruleset writes no SAV; overwrite refusal preserves SHA256')
cargo = sav.load(ART / 'live-native-cargo-v1/P151FR.SAV')
assert cargo['armies'][0]['embarked'] and cargo['fleets'][0]['army'] == 0
assert (cargo['armies'][0]['owner'], cargo['armies'][0]['x'], cargo['armies'][0]['y']) == (
    cargo['fleets'][0]['owner'], cargo['fleets'][0]['x'], cargo['fleets'][0]['y'])
checks.append('Synthetic cargo: reciprocal index, owner, coordinates and off-map army sentinel survive original reopen')
turn = json.loads((HERE / 'live-native-orders-seed-v1.json').read_text())
assert turn['end_turn']['calendar'] == {'season': 0, 'week': 3, 'year_bc': 270}
steps = {s['label']: s for s in turn['steps']}
assert steps['autosave-after-one-turn']['turn'] == 721
assert steps['after-one-turn']['sha256'] == steps['fresh-reopen-resave']['sha256']
checks.append('Instrumented-original continuation: exactly one calendar tick 0720 -> 0721, autosave/SaveAs/reopen identical')
binaries = {}
for rel in ('build/bin/IC2.Cli/debug/IC2.Cli.dll', 'build/bin/IC2.Cli/debug/IC2.Engine.dll',
            'build/bin/IC2.Cli/debug/IC2.Data.dll',
            'probe-build/bin/ConversionProbe/debug/ConversionProbe.dll',
            'probe-build-v2/bin/ConversionProbe/debug/ConversionProbe.dll'):
    binaries[rel] = hashlib.sha256((ART / rel).read_bytes()).hexdigest()
with (HERE / sys.argv[1]).open('x') as f:
    json.dump({'passed': True, 'checks': checks, 'manifest_file_checks': manifest_files,
               'original_sessions': 7, 'distinct_native_scenarios': 6, 'refusal_controls': 2,
               'ui_adjustments': ui_words, 'native_difference_counts': native_diffs,
               'assembly_sha256': binaries, 'not_proved': ['native Windows acceptance',
               'the owner twelve-save manifest', 'RNG equivalence or full fidelity',
               'all unsupported-state refusals', 'independent model review']}, f, indent=2)
    f.write('\n')
print('PASS:', len(checks), 'groups;', manifest_files, 'artifact hash checks; 7 original/return sessions')
