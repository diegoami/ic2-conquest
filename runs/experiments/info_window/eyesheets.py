"""Contact sheets for the by-eye check: one strip per band sample (the panel line that carries the word, cropped from the screenshot), labelled with
the staged value and the code's expected word. Written to the gitignored artifacts folder (they are screenshots); the verdicts go in eye_check.tsv."""
import sys, os, csv, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, ART, new_path
LINE = {'loyalty': 4, 'unity': 5, 'morale': 3, 'tribute_word_foreign': 6, 'sea': 7}
rows = []
for f in sorted(glob.glob(DATA + 'band_samples*.tsv'), key=lambda p: (len(p), p)):
    rows += list(csv.DictReader(open(f), delimiter='\t'))
def png_path(name):
    for d in (ART,):
        if os.path.exists(d + name): return d + name
by = {}
for r in rows:
    if r['field'] in LINE: by.setdefault(r['field'], []).append(r)
for fld, rs in by.items():
    seen, tiles = set(), []
    for r in sorted(rs, key=lambda r: int(r['value'])):
        k = (r['value'], r['png'])
        if k in seen: continue
        seen.add(k)
        tmp = '/tmp/claude-1000/strip_%d.png' % len(tiles)
        y = 20 + 16 * LINE[fld] if fld != 'sea' else 20 + 16 * 7
        subprocess.run(['convert', png_path(r['png']), '+repage', '-crop', '300x16+0+%d' % y, '+repage', '-bordercolor', 'white', '-border', '0', tmp], check=True)
        tiles += ['-label', '%s=%s expect "%s"' % (fld, r['value'], r['expected_word']), tmp]
    out = new_path(ART + 'eye_%s.png' % fld)
    subprocess.run(['montage', '-tile', '2x', '-geometry', '+4+2', '-pointsize', '11'] + tiles + [out], check=True)
    print(out, len(tiles) // 2)
