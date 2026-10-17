"""Verify immutable saves with raw offsets and emit a fresh compact Wine matrix.

No game or emulator execution. Outputs are exclusively created. Save bytes are
never changed. Labels retain staged/Wine provenance and failed attempts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--artifacts', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
data = Path(__file__).resolve().parents[3] / 'runs/experiments/data/run-exp-resupply31'
manifest = {}
for line in (data / 'SAVES.sha256').read_text().splitlines():
    digest, name = line.split(None, 1)
    assert name not in manifest or manifest[name] == digest
    manifest[name] = digest
for name, digest in manifest.items():
    assert hashlib.sha256((a.artifacts / name).read_bytes()).hexdigest() == digest, name


def raw(name, subject):
    b = (a.artifacts / name).read_bytes()
    h = lambda offset: struct.unpack_from('<h', b, offset)[0]
    # Original SAV: map320*140 words, then 334 cities34 bytes, army count
    # and records656 bytes, fleet count and records26 bytes, nations1172 bytes.
    city = 320 * 140 * 2
    army_count = city + 334 * 34
    army = army_count + 2
    fleet_count = army + h(army_count) * 656
    fleet = fleet_count + 2
    nation = fleet + h(fleet_count) * 26
    units = [fleet + i * 26 for i in range(h(fleet_count))] if subject == 'fleet' else [army + i * 656 for i in range(h(army_count))]
    owned = [u for u in units if h(u + (8 if subject == 'fleet' else 4)) == 0]
    assert len(owned) == 1, (name, owned)
    unit = owned[0]
    sup, purse = (14, 16) if subject == 'fleet' else (10, 12)
    return dict(supplies=h(unit + sup), purse=h(unit + purse),
                condition=h(unit + 20) if subject == 'fleet' else None,
                coordinates=[h(unit), h(unit + 2)],
                stocks=[h(city + i * 34 + 24) for i in range(334)],
                treasuries=[struct.unpack_from('<i', b, nation + i * 1172 + 0x438)[0]
                            for i in range(16)])


rows, failures = [], []
for log in sorted(data.glob('wine-*.jsonl')):
    before = {}
    for line in log.read_text().splitlines():
        r = json.loads(line)
        if r['event'] == 'failure':
            failures.append(dict(log=log.name, case=r['case'], exception=r['exception']))
        if r['event'] == 'before':
            before[r['case']] = r
        if r['event'] != 'after':
            continue
        prior = before[r['case']]
        subject = r['case'].split(':')[0]
        b, e = raw(prior['loaded'], subject), raw(r['post'], subject)
        for observed, decoded in ((prior['fields'], b), (r['fields'], e)):
            assert observed['unit']['supplies'] == decoded['supplies'], (r['case'], observed['unit'], decoded)
            assert observed['unit']['money'] == decoded['purse']
            assert observed['condition'] == decoded['condition']
            assert observed['treasuries'] == decoded['treasuries']
            assert observed['turn'] == 734
            for c in observed['providers']:
                assert c['supplies'] == decoded['stocks'][c['id']]
        assert b['coordinates'] == e['coordinates'] == [102, 49]
        assert r['fields']['current'] == 11 and prior['fields']['current'] == 13
        delta = {k: e[k] - b[k] for k in ('supplies', 'purse')}
        delta['stock'] = {str(i): y - x for i, (x, y) in enumerate(zip(b['stocks'], e['stocks']))
                          if x != y}
        delta['treasury'] = {str(i): y - x for i, (x, y) in enumerate(zip(b['treasuries'], e['treasuries']))
                             if x != y}
        if subject == 'fleet':
            delta['condition'] = e['condition'] - b['condition']
        rows.append(dict(case=r['case'], log=log.name, before=prior['loaded'], after=r['post'],
                         autosave=r['autosave'], turn=734, initial=b, final=e, delta=delta))

by_case = {}
for row in rows:
    assert row['case'] not in by_case, 'Repeated completed case requires explicit selection'
    by_case[row['case']] = row
paired = []
for case, row in by_case.items():
    if not case.startswith('aboard:'):
        continue
    other = by_case.get(case.replace('aboard:', 'land:'))
    if other:
        assert row['initial'] == other['initial']
        assert row['final'] == other['final']
        paired.append(case.split(':')[1])
result = dict(provenance='Staged original game under Wine; raw save-offset verification; not native Windows.',
              saves_verified=len(manifest), cases=len(rows), matched_land_aboard=paired,
              failures=failures, records=rows)
with a.output.open('x') as out:
    json.dump(result, out, indent=2)
    out.write('\n')
print('PASS', len(manifest), 'save hashes;', len(rows), 'Wine cases;', len(paired), 'matched land/aboard cases')
