"""Independent Python comparisons: native JSON and conquest's SAV parser.

Differences are recorded, never waived wholesale. Native IDs are canonicalized
by record index; RNG seed cannot survive original SAV. These are separate from
full byte comparisons and original-program acceptance.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'artifacts/run-exp-sav-conversion-roundtrip'
sys.path.insert(0, str(ROOT))
from state import sav

def differences(a, b, path=''):
    if type(a) != type(b):
        return [{'path': path, 'before': a, 'after': b}]
    if isinstance(a, dict):
        out = []
        for k in sorted(a.keys() | b.keys()):
            out += differences(a.get(k), b.get(k), path + '/' + str(k))
        return out
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return [{'path': path + '/length', 'before': len(a), 'after': len(b)}]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, path + '/' + str(i))]
    return [] if a == b else [{'path': path, 'before': a, 'after': b}]

def native(path):
    s = json.loads(Path(path).read_text())['save']['state']
    ids = {x['id']: f'army-{i}' for i, x in enumerate(s['armies'])}
    ids.update({x['id']: f'fleet-{i}' for i, x in enumerate(s['fleets'])})
    def walk(x):
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v) for v in x]
        return ids.get(x, x) if isinstance(x, str) else x
    s = walk(s)
    seed = s.pop('randomSeed')
    for f in s['fleets']:
        if f['constructionTicksRemaining'] is None:
            f['buildCityId'] = None
    for army in s['armies']:
        for u in army['units']:
            label = u['mercenaryLabel']
            if label and u['name'] == f'Mercenary unit (label {label})':
                u['name'] = f'Mercenary (label {label})'
    return s, seed

def savcompare(a, b):
    aa, bb = sav.load(a), sav.load(b)
    # These are storage metadata or interface viewport only; all other parser
    # fields are compared, including map markers, treasury, queues and news.
    for s in (aa, bb):
        for key in ('size', 'tail_off'):
            s.pop(key)
        for n in s['nations']:
            n.pop('view')
    raw_a, raw_b = a.read_bytes(), b.read_bytes()
    offsets = [i for i, (x, y) in enumerate(zip(raw_a, raw_b)) if x != y]
    return {'semantic_differences': differences(aa, bb), 'byte_equal': raw_a == raw_b,
            'lengths': [len(raw_a), len(raw_b)], 'differing_byte_count': len(offsets),
            'differing_offsets': offsets, 'before_sha256': hashlib.sha256(raw_a).hexdigest(),
            'after_sha256': hashlib.sha256(raw_b).hexdigest()}

def main():
    out = {'native_export_import': {}, 'original_sessions': {}, 'returned_sessions': {}}
    for p in sorted((ART / 'native-v1').glob('native-*.json')):
        back = ART / 'exports-v2' / (p.stem + '-back.json')
        if not back.exists():
            continue
        a, seed_a = native(p)
        b, seed_b = native(back)
        out['native_export_import'][p.stem] = {'differences': differences(a, b),
            'source_seed': seed_a, 'imported_seed': seed_b,
            'excluded': ['record ids normalized by index', 'randomSeed (not stored in original)',
                         'launched fleet build-city metadata', 'documented mercenary-name alias']}
    for receipt in sorted(HERE.glob('live-*.json')):
        r = json.loads(receipt.read_text())
        entry = {'complete': r['complete'], 'error': r.get('error'), 'comparisons': {}}
        files = {step['label']: ART / step['file'] for step in r['steps']}
        initial = ART / r['input']['file']
        if 'immediate-native-save' in files:
            entry['comparisons']['export_vs_original_immediate'] = savcompare(initial, files['immediate-native-save'])
        if 'after-tax-order' in files:
            entry['comparisons']['immediate_vs_tax_order'] = savcompare(files['immediate-native-save'], files['after-tax-order'])
        final = files.get('after-one-turn', files.get('after-tax-order'))
        if final and 'fresh-reopen-resave' in files:
            entry['comparisons']['original_save_vs_reopen_resave'] = savcompare(final, files['fresh-reopen-resave'])
        out['original_sessions'][receipt.stem] = entry
        folder = ART / receipt.stem
        if (folder / 'continued-v2.json').exists():
            a, seed_a = native(folder / 'returned-v2.json')
            b, seed_b = native(folder / 'continued-v2.json')
            continued = folder / ('RETURN' + r['case'] + '.SAV')
            out['returned_sessions'][receipt.stem] = {
                'remake_order_differences': differences(a, b), 'rng_before_order': seed_a, 'rng_after_order': seed_b,
                'rng_advanced_once': seed_b == (seed_a + 0x9E3779B97F4A7C15) % (1 << 64),
                'original_vs_remake_reexport': savcompare(files['fresh-reopen-resave'], continued)}
    target = HERE / sys.argv[1]
    with target.open('x') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    for name, r in out['native_export_import'].items():
        print(name, 'native differences', len(r['differences']))
    for name, r in out['original_sessions'].items():
        print(name, 'complete', r['complete'],
            {k: len(v['semantic_differences']) for k, v in r['comparisons'].items()})

if __name__ == '__main__':
    main()
