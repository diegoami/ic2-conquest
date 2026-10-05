from explore_lib import *
g = Game()
g.click(382, 109, pause=1.5); g.shot(ART + 'FI_b1_03_about.png'); wins(g, 'b1', 'about')
cs = g.controls('About Imperial Conquest 2'); log('b1', 'about controls: %s' % [(c['cls'], c['text']) for c in cs])
c = g.control(cs, text='CAncell'); g.click_control(c, pause=1.5)
g.shot(ART + 'FI_b1_04_cellauto.png'); wins(g, 'b1', 'after CAncell')
