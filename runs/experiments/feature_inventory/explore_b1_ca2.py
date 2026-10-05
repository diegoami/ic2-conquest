from explore_lib import *
g = Game()
for i in range(3):
    if not g.find_windows('^Cellular Automata$'): break
    g.click(776, 341, pause=1.2)
wins(g, 'b1', 'after closing cellauto')
cs = g.controls('About Imperial Conquest 2'); g.close_controls('About Imperial Conquest 2', cs, text='OK')
wins(g, 'b1', 'after About OK')
