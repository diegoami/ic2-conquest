from explore_lib import *
g = Game()
cs = g.controls('Balance sheet'); log('b1', 'Balance sheet controls: %s' % [(c['cls'], c['text']) for c in cs if c['text']])
g.close_controls('Balance sheet', cs, text='OK'); wins(g, 'b1', 'after')
# Find a city (Shift+D)
g.reset_ui(); g.key('shift+d'); time.sleep(1.5); g.shot(ART + 'FI_b1_17_find_city_shift_d.png'); ws = wins(g, 'b1', 'Shift+D')
