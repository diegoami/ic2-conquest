from explore_lib import *
g = Game()
for i in range(3):
    if not g.find_windows('^Confirm$'): break
    g.answer('Confirm', yes=False); time.sleep(1)
wins(g, 'b1', 'after No x%d' % (i+1))
