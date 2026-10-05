"""Band edges: for each word field, the model's (code + DAT) word at every value of its domain, the edges (where the word changes), and for every
edge whether BOTH sides were captured in play (band_samples.tsv: value, expected word, seen word, png) -> 'confirmed', else 'derived' with the reason.
    python3 edges.py [--write]"""
import sys, os, csv, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, write_new
import panel_model as M

def latest(pattern):
    fs = sorted(glob.glob(DATA + pattern), key=lambda p: (len(p), p)); return fs[-1]
def samples():
    d = {}
    for f in sorted(glob.glob(DATA + 'band_samples*.tsv'), key=lambda p: (len(p), p)):
        for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'):
            if r['status'] == 'OK': d.setdefault((r['field'], int(r['value'])), []).append(r['png'])
    return d
# (field, word function, domain lo, hi, the range the game can produce / that the task covers, note)
FIELDS = [
    ('loyalty', M.loyalty_word, -29, 119, (0, 109), 'value div 10 (truncating) -> DAT_004793fc table; <0 and >=110 read other memory'),
    ('unity', M.unity_word, 0, 1199, (1, 1099), 'value div 100 -> the same table; 0 means conquered (not shown as a word)'),
    ('morale', M.morale_word, 40, 80, (51, 80), '(m-51)>>2, or (m-48)>>2 when m<51 -> DAT_00479428 (= unity table entry 4)'),
    ('relation', lambda v: M.relation_word(v).strip(), -3, 8, (-3, 5), 'table at DAT_004794c8, 6-byte entries, only when value > 0'),
    ('tribute_word_foreign', lambda v: (M.tribute_word(v) if M.tribute_word(v) is not None else '<number>'), 0, 10100, (0, 10100), 'foreign city only; unsigned 16-bit tribute'),
    ('sea', lambda v: 'calm' if v == 0 else 'rough', -3, 3, (-3, 3), 'fleet +24 field == 0'),
    ('quality', lambda q: M.quality_word(q).replace(' ', ''), -1, 12, (0, 11), 'DAT_0047938c table, the unit quality 0..9 directly'),
]
def main(write=False):
    S = samples(); rows = []
    for fld, fn, lo, hi, (rlo, rhi), note in FIELDS:
        prev = None
        for v in range(lo, hi + 1):
            w = fn(v)
            if prev is not None and w != prev[1]:
                a, b = prev[0], v
                ca, cb = S.get((fld, a)), S.get((fld, b))
                inrange = rlo <= a and b <= rhi
                if ca and cb: st = 'confirmed'
                elif not inrange: st = 'derived (outside the range the game produces / staged range; code only)'
                else: st = 'derived (a side not staged)'
                rows.append((fld, '%d|%d' % (a, b), prev[1], w, st, (ca or ['-'])[0], (cb or ['-'])[0], note))
            prev = (v, w)
    hdr = 'field\tedge(last value of the lower word|first value of the higher word)\tword_below\tword_above\tstatus\tpng_below\tpng_above\tnote\n'
    body = ''.join('\t'.join(map(str, r)) + '\n' for r in rows)
    n = len(rows); c = sum(1 for r in rows if r[4] == 'confirmed')
    print(hdr + body); print('edges %d, confirmed %d, derived %d' % (n, c, n - c))
    if write: print(write_new(DATA + 'band_edges.tsv', hdr + body))
if __name__ == '__main__': main('--write' in sys.argv)
