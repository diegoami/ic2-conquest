from explore_lib import *
g = Game()
g.click(308, 110, pause=2.0); g.shot(ART + 'FI_b1_17_find_city_dialog.png'); ws = wins(g, 'b1', 'Find city button')
for w in ws:
    if w[0] not in ('Unit map','Area map','Information') and 'turn' not in w[0]:
        cs = g.controls(w[0]); log('b1', '%s controls: %s' % (w[0], [(c['cls'], c['text']) for c in cs if c['text']][:40]))
