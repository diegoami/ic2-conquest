"""Cargo control, return-trip gameplay and repeat-export comparisons."""
import hashlib
import json
import sys
from pathlib import Path
from offline import ART, HERE, ROOT, REMAKE, DOTNET, CLI, run

probe = ART / 'probe-build-v2/bin/ConversionProbe/debug/ConversionProbe.dll'
template = ROOT / 'saves/run0-start-AUTO0720-seed12345.SAV'
if sys.argv[1] == 'cargo':
    src = ART / 'native-v1/native-initial.json'
    native = ART / 'native-v1/native-cargo.json'
    run('generate-cargo-v1', [DOTNET, probe, 'cargo', REMAKE, src, native])
    target = ART / 'exports-v2/native-cargo.SAV'
    run('export-native-cargo-v2', [DOTNET, CLI, '--export-sav', native, '--output', target, '--template', template])
    run('policy-native-cargo-v3', [sys.executable, ROOT / 'scripts/sav_export_policy_check.py', target,
        '--out', HERE / 'policy-result-native-cargo-v3.json'])
    run('import-native-cargo-v2', [DOTNET, probe, 'import', REMAKE, target, ART / 'exports-v2/native-cargo-back.json'])
    before = hashlib.sha256(target.read_bytes()).hexdigest()
    p = run('negative-overwrite-v1', [DOTNET, CLI, '--export-sav', native, '--output', target, '--template', template])
    after = hashlib.sha256(target.read_bytes()).hexdigest()
    with (HERE / 'negative-overwrite-integrity-v1.json').open('x') as f:
        json.dump({'returncode': p.returncode, 'hash_before': before, 'hash_after': after,
                   'unchanged': before == after}, f, indent=2)
elif sys.argv[1] == 'return':
    for p in sorted(HERE.glob('live-*.json')):
        r = json.loads(p.read_text())
        if not r['complete']:
            continue
        if (HERE / ('return-' + p.stem + '-v2.json')).exists():
            print('Preserving existing return measurement:', p.stem, flush=True)
            continue
        step = next(s for s in r['steps'] if s['label'] == 'fresh-reopen-resave')
        src = ART / step['file']
        folder = src.parent
        result = run('return-' + p.stem + '-v2', [DOTNET, probe, 'import', REMAKE, src,
            folder / 'returned-v2.json', folder / 'continued-v2.json'])
        if result.returncode:
            raise SystemExit('Return import failed: read its complete receipt')
        target = folder / ('RETURN' + r['case'] + '.SAV')
        result = run('reexport-' + p.stem + '-v2', [DOTNET, CLI, '--export-sav', folder / 'continued-v2.json',
            '--output', target, '--template', template])
        if result.returncode:
            raise SystemExit('Returned native export failed: read its complete receipt')
        run('reexport-policy-' + p.stem + '-v2', [sys.executable, ROOT / 'scripts/sav_export_policy_check.py', target,
            '--out', HERE / ('reexport-policy-result-' + p.stem + '-v2.json')])
else:
    raise SystemExit('cargo/return')
