#!/usr/bin/env python3
"""Attribute CURRENT registered draw boundaries to immutable original hook rows.

No model/port replay, no original execution, no fixture writes. Missing current
port phase state and original claims/pass history remain unavailable.
"""
import argparse
import base64
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build-revision', required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise SystemExit('choose a new output; measurements are immutable')
    path = 'tests/IC2.Engine.Tests/Battle/Tactical/GoldenMaster/KnownFailures.json'
    obj = json.loads(subprocess.check_output(['gh', 'api',
        f'repos/diegoami/imperial_conquest_2/contents/{path}?ref={a.build_revision}'], text=True))
    registry_bytes = base64.b64decode(obj['content'])
    registry = json.loads(registry_bytes)
    root = Path(__file__).resolve().parents[3]
    hooks = root / 'runs/experiments/data/run-exp-battle-hook'
    out = {'build_revision': a.build_revision, 'registry_path': path,
           'registry_git_blob': obj['sha'], 'registry_sha256': hashlib.sha256(registry_bytes).hexdigest(),
           'registry': registry, 'assertion_count': len(registry),
           'note': 'Current registry read plus original-hook attribution; NOT a fresh replay or causal closure',
           'attributions': []}
    for row in registry:
        if not row['Case'].startswith('The_port_draws_what_the_original_drew:'):
            continue
        series = row['Case'].split(':', 1)[1]
        m = re.search(r'draw (\d+): half-round counter (\d+) .*original site (\S+) Random\((\d+)\) = (\d+), port Random\((\d+)\) = (\d+)', row['FirstDifference'])
        assert m, row
        idx, hr, site, bound, value, port_bound, port_value = m.groups()
        raw_path = hooks / f'hooklog-{series}.csv'
        raw = raw_path.read_bytes()
        rows = list(csv.DictReader(raw.decode().splitlines()))
        draws = [r for r in rows if r['kind'] == 'random']
        selected = draws[int(idx)]
        assert (int(selected['counter']), selected['site'], int(selected['eax']), int(selected['result'])) == (int(hr), site, int(bound), int(value))
        before = rows[:rows.index(selected)]
        marker = next(r for r in reversed(before) if r['kind'] == 'marker' and r['site'] == '0x43910c')
        actor, target = int(marker['eax']) & 65535, int(marker['edx']) & 65535
        exchanges_path = hooks / f'exchanges-{series}.jsonl'
        exchanges = exchanges_path.read_bytes()
        prior = next(r for r in map(json.loads, exchanges.decode().splitlines())
                     if r.get('kind') == 'shot' and r.get('seq') == int(marker['seq']))
        assert (prior['actor'], prior['target']) == (actor, target)
        out['attributions'].append({'series': series, 'zero_based_draw': int(idx),
            'original_raw_random': selected, 'original_shot_marker': marker,
            'actor': actor, 'target': target, 'existing_exchange': prior,
            'port_registered_bound': int(port_bound), 'port_registered_result': int(port_value),
            'raw_hook_path': str(raw_path.relative_to(root)), 'raw_hook_sha256': hashlib.sha256(raw).hexdigest(),
            'exchange_path': str(exchanges_path.relative_to(root)), 'exchange_sha256': hashlib.sha256(exchanges).hexdigest(),
            'original_claims': 'not recorded', 'original_general_pass': 'not recorded',
            'current_port_actor_target_and_phase': 'not available in this registry'})
    with a.output.open('x') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    print(f'{len(registry)} current assertions; {len(out["attributions"])} exact original draw/actor attributions; no replay')


if __name__ == '__main__':
    main()
