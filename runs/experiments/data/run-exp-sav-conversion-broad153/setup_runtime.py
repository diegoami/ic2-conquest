"""Copy an existing runtime without its saves; never modify the source prefix."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path('/home/diego/ic2-work')
DEST = ROOT / 'artifacts/run-exp-sav-conversion-broad153/runtime'
if DEST.exists():
    raise SystemExit('Runtime already exists; preserve it and choose a new destination for a retry')
DEST.mkdir(parents=True)
shutil.copytree(SOURCE / 'prefix', DEST / 'prefix', symlinks=True,
                ignore=lambda directory, names: ['IC2'] if Path(directory).name == 'drive_c' else [])
game = DEST / 'prefix/drive_c/IC2'
game.mkdir()
copied = []
for src in sorted((SOURCE / 'prefix/drive_c/IC2').iterdir()):
    if src.is_file() and src.suffix.lower() in {'.exe', '.dat', '.hlp', '.cnt', '.dll'}:
        shutil.copy2(src, game / src.name)
        copied.append({'name': src.name, 'sha256': hashlib.sha256(src.read_bytes()).hexdigest()})
if (SOURCE / 'prefix/drive_c/IC2/WAVS').exists():
    shutil.copytree(SOURCE / 'prefix/drive_c/IC2/WAVS', game / 'WAVS')
for src in SOURCE.iterdir():
    if src.is_file() and (src.name in {'win_controls.exe', 'win_slider.exe'} or src.name.endswith('_toolbar.json') or src.name == 'toolbar.json'):
        shutil.copy2(src, DEST / src.name)
receipt = Path(__file__).parent / 'runtime-files-v1.json'
with receipt.open('x') as f:
    json.dump({'source': str(SOURCE), 'destination': str(DEST), 'files': copied,
               'source_saves_copied': 0, 'display': ':153'}, f, indent=2)
    f.write('\n')
print('Isolated runtime prepared; files:', len(copied))
