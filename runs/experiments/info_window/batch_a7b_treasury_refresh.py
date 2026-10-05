"""Batch a7b: re-capture the A7 treasury variants 1..4. In batch a7 the nation panel was not refreshed after File > Open when the same nation was chosen again
(it still showed the previous save's values), so here another nation is chosen first, then Rome."""
from iw_lib import *
g = Game()
for k in (1, 2, 3, 4):
    save = ART + 'saves/A7_rome_treasury%d.SAV' % k
    if k == 1: launch(g, save)
    else: g.open(save)
    nation_menu(g, 1); nation_menu(g, 0)
    p = sav.load(save)['nations'][0]
    png, ocr = capture('a7b', save, 'nation', 0, {'treasury': p['treasury'], 'mobilization': p['mobilization'], 'tax': p['tax'], 'refresh': 'other nation first'}, 'A7b_nation00_treasury%d.png' % k)
    print(k, ' | '.join(l for l in ocr.splitlines() if l.strip())[:200])
stop(g)
