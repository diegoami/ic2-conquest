from explore_lib import *
g = Game()
g.menu('nations', 1); time.sleep(1.5); g.shot(ART + 'FI_b1_20_nation_carthage.png'); wins(g, 'b1', 'Nations>Carthage')
g.click(240, 59, pause=1.5); g.shot(ART + 'FI_b1_21_nation_rome.png')
g.click(281, 110, pause=1.5); g.shot(ART + 'FI_b1_22_show_all_mercenaries.png')
