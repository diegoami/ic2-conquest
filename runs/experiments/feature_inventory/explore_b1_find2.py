from explore_lib import *
g = Game()
g.click(379, 279, pause=1.0); g.shot(ART + 'FI_b1_18_find_city_selected.png')
cs = g.controls('Find city'); g.close_controls('Find city', cs, text='OK', pause=1.5)
g.shot(ART + 'FI_b1_19_find_city_result.png'); wins(g, 'b1', 'after Find city OK')
