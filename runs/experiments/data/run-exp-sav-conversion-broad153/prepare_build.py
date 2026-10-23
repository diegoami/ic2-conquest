"""Build latest converter without writing the remake checkout.

Live main differs from local a510c33 only by two production source files
(quality-4 fix). Fetch those exact GitHub blobs and substitute at compile time.
No second checkout, source edits, or copying a repository is involved.
"""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'artifacts/run-exp-sav-conversion-broad153'
PIN = 'ae614899d63ac721ee46d1e3213191fe1f43a676'
OVERLAY = ART / 'build-overlay'
OVERLAY.mkdir(parents=True, exist_ok=True)
rows = []
for rel in ['src/IC2.Data/SaveArmyTable.cs', 'src/IC2.Engine/Import/OriginalSaveExporter.cs']:
    r = subprocess.run(['gh', 'api', f'repos/diegoami/imperial_conquest_2/contents/{rel}?ref={PIN}'], capture_output=True, text=True, check=True)
    item = json.loads(r.stdout)
    content = base64.b64decode(item['content'])
    gitblob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
    assert gitblob == item['sha']
    dest = OVERLAY / Path(rel).name
    with dest.open('xb') as f:
        f.write(content)
    rows.append({'path': rel, 'git_blob': gitblob, 'sha256': hashlib.sha256(content).hexdigest()})
with (HERE / 'build-source-pin-v1.json').open('x') as f:
    json.dump({'remake_main': PIN, 'read_only_local_base': 'a510c33f0aaa2998ff1186127ff18eb13f489496',
               'change': 'PR1353 quality4 fix; compare API reports only these2 production sources and2 test files',
               'compile_substitutions': rows}, f, indent=2)
print('Verified 2 upstream production blobs for', PIN)
