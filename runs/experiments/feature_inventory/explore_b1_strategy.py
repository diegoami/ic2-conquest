from explore_lib import *
g = Game()
g.tool('balance', pause=2.0); g.shot(ART + 'FI_b1_16_balance_sheet.png'); ws = wins(g, 'b1', 'Balance sheet')
t = [w[1] for w in ws if w[1] not in ('Unit map','Area map','Information') and 'Rome' not in w[1]]
log('b1', 'dialog titles: %s' % t)
for title in t:
    cs = g.controls(title); log('b1', '%s controls: %s' % (title, [(c['cls'], c['text']) for c in cs if c['text']]))
    g.close_controls(title, cs, text='OK')
wins(g, 'b1', 'after')
