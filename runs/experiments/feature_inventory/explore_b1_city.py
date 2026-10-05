from explore_lib import *
g = Game()
g.click(107, 169, pause=1.5); time.sleep(1); g.shot(ART + 'FI_b1_23_unitmap_rome_centered.png')
g.click(545, 366, pause=1.5); g.shot(ART + 'FI_b1_24_city_left_click.png')
rclick(g, 545, 366, pause=1.5); g.shot(ART + 'FI_b1_25_city_right_click.png')
wins(g, 'b1', 'after city clicks')
