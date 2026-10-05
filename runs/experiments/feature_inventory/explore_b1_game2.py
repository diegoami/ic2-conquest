from explore_lib import *
g = Game()
cs = g.controls('Human and computer leaders'); log('b1', 'PickLeaders controls n=%d classes=%s' % (len(cs), sorted({c['cls'] for c in cs})))
g.close_controls('Human and computer leaders', cs, text='Cancel'); wins(g, 'b1', 'after Cancel')
for i, name in ((2, 'newnation'), (3, 'abdicate')):
    g.menu('game', i); time.sleep(1); g.shot(ART + 'FI_b1_09_game_%s.png' % name); ws = wins(g, 'b1', 'Game item %d' % i)
    for b in g.message_boxes(): log('b1', 'box: %s' % (b,))
    g.dismiss_popups(strict=True)   # answers a Confirm with No under strict
    wins(g, 'b1', 'after dismiss %d' % i)
