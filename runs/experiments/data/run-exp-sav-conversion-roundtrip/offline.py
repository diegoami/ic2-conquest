"""Run the pinned CLI and adapter with immutable command/output receipts."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'artifacts/run-exp-sav-conversion-roundtrip'
REMAKE = Path('/home/diego/projects/imperial_conquest_2')
DOTNET = '/home/diego/.dotnet/dotnet'
CLI = ART / 'build/bin/IC2.Cli/debug/IC2.Cli.dll'
PROBE = ART / 'probe-build/bin/ConversionProbe/debug/ConversionProbe.dll'

def run(name, argv):
    receipt = HERE / (name + '.json')
    if receipt.exists():
        raise RuntimeError('Receipt exists: ' + str(receipt))
    result = subprocess.run(list(map(str, argv)), cwd=REMAKE, capture_output=True, text=True)
    with receipt.open('x') as f:
        json.dump({'argv': list(map(str, argv)), 'cwd': str(REMAKE), 'returncode': result.returncode,
                   'stdout': result.stdout, 'stderr': result.stderr}, f, indent=2)
        f.write('\n')
    print(name, 'exit', result.returncode, flush=True)
    if result.returncode:
        print(result.stderr[-2500:], flush=True)
    return result

if __name__ == '__main__':
    mode = sys.argv[1]
    version = sys.argv[2] if mode == 'export' and len(sys.argv) > 2 else 'v1'
    native = ART / 'native-v1'
    exports = ART / ('exports-' + version)
    exports.mkdir(parents=True, exist_ok=True)
    if mode == 'generate':
        run('generate-v1', [DOTNET, PROBE, 'generate', REMAKE, native])
    elif mode == 'export':
        template = ROOT / 'saves/run0-start-AUTO0720-seed12345.SAV'
        for src in sorted(native.glob('*.json')):
            target = exports / (src.stem + '.SAV')
            result = run('export-' + src.stem + '-' + version, [DOTNET, CLI, '--export-sav', src, '--output', target, '--template', template])
            if target.exists():
                run('policy-' + src.stem + '-' + version, [sys.executable, ROOT / 'scripts/sav_export_policy_check.py', target,
                    '--out', HERE / ('policy-result-' + src.stem + '-' + version + '.json')])
                run('import-' + src.stem + '-' + version, [DOTNET, PROBE, 'import', REMAKE, target, exports / (src.stem + '-back.json')])
    elif mode == 'policy':
        for target in sorted((ART / 'exports-v2').glob('*.SAV')):
            run('policy-' + target.stem + '-v3', [sys.executable, ROOT / 'scripts/sav_export_policy_check.py', target,
                '--out', HERE / ('policy-result-' + target.stem + '-v3.json')])
    elif mode == 'import':
        src, dst, name = sys.argv[2:5]
        run(name, [DOTNET, PROBE, 'import', REMAKE, src, dst])
    elif mode == 'hash':
        lines = []
        for p in sorted(ART.rglob('*')):
            if p.is_file() and p.suffix.lower() in {'.sav', '.png', '.json'} and 'runtime' not in p.parts and not any(x in p.parts for x in ('build', 'probe-build')):
                lines.append(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(ART)))
        target = HERE / sys.argv[2]
        target.write_text('\n'.join(lines) + '\n') if not target.exists() else sys.exit('Hash receipt exists')
    else:
        raise SystemExit('generate/export/import/hash')
