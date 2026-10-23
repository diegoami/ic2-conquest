"""Immutable artifact batch: saves, native JSON and screenshots, no runtime."""
import hashlib,json,sys,tarfile
from pathlib import Path
from offline import ART,HERE
name=sys.argv[1];target=ART/(name+'.tar.gz')
if target.exists():raise SystemExit('Existing archive preserved')
files=list((ART/'native-v1').glob('*.json'))+list((ART/'exports-v1').glob('*'))
files+=list((ART/'negative-v1').glob('*')) if (ART/'negative-v1').exists() else []
for receipt in HERE.glob('live-*-v*.json'):
    r=json.loads(receipt.read_text())
    # A failed attempt's binary evidence is as important as a passed attempt.
    folder=ART/receipt.stem
    if folder.exists():files+=list(folder.glob('*'))
files=sorted(set(p for p in files if p.is_file() and p.suffix.lower() in {'.json','.sav','.png'}))
rows=[dict(file=str(p.relative_to(ART)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
with tarfile.open(target,'x:gz') as tar:
    for p in files:tar.add(p,arcname=str(p.relative_to(ART)))
with (HERE/(name+'-manifest.json')).open('x') as f:
    json.dump(dict(archive=target.name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),files=rows),f,indent=2);f.write('\n')
with (HERE/(name+'-SAVES.sha256')).open('x') as f:
    for row in rows:f.write(row['sha256']+'  '+row['file']+'\n')
print('Bundled',len(rows),'files;',target.stat().st_size,'bytes;',target)
