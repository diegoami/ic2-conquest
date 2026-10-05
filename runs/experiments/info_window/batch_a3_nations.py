"""Batch a3: nation panel (N03). Unity word band edges (unity div 100 -> 11-byte table), population/treasury formatting, relations row
(values -18..100), the conquered-nation row. One save; nations 0..14 each with their own unity and population; nation 15 conquered (unity 0)."""
from iw_lib import *
BASE = '/home/diego/ic2-work/fixtures/BASE.SAV'
base = sav.load(BASE)
UN = [100, 250, 499, 500, 599, 600, 699, 700, 799, 800, 899, 900, 999, 1000, 1100]
POP = [0, 7, 999, 1000, 12345, 1234567, 123456789, 2147483647, -5000, 100000, 3, 40, 500, 5000, 50000]
TAX = [0, 5, 10, 15, 20, 25, 30, 35, 40, 1, 2, 3, 4, 6, 7]
REL1 = [3, None, 0, 1, 2, -1, 4, 5, 6, 7, 100, -18, 0, 3, 2, 1]
def edits(s):
    for n in range(15): s.nation(n, unity=UN[n], tax=TAX[n]); s.put(s.nation0 + n * sav.NATION_LEN + 0x430, POP[n], 'i')
    s.nation(15, unity=0, conquered_by=2)
    for m, v in enumerate(REL1):
        if v is not None: s.relation(1, m, v)
save = ART + 'saves/A3_nations_unity_relations.SAV' if len(sys.argv) > 1 else stage_save('a3', BASE, edits, 'A3_nations_unity_relations.SAV')
g = Game(); launch(g, save)
for n in (range(15) if len(sys.argv) < 2 else range(int(sys.argv[1]), 15)):
    nation_menu(g, n)
    st = {'unity': UN[n], 'pop': POP[n], 'tax': TAX[n], 'name': sav.NATIONS[n]}
    if n == 1: st['relations_row'] = REL1
    png, ocr = capture('a3', save, 'nation', n, st, 'A3_nation_%02d_%s.png' % (n, sav.NATIONS[n]))
    print(n, st, '=>', ' | '.join(l for l in ocr.splitlines() if l.strip())[:420])
stop(g)
