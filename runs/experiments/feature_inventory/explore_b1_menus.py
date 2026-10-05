from explore_lib import *
g = Game()
for name, x in (('file', 14), ('game', 45), ('strategy', 97), ('nations', 148), ('area', 202), ('unit', 259)):
    g.reset_ui(); g.click(x, 36, pause=1.0); g.shot(ART + 'FI_b1_11_menu_%s.png' % name)
g.reset_ui(); g.click(202, 36, pause=1.0); g.click(230, 56 + 16*6 + 4, pause=1.0); g.shot(ART + 'FI_b1_12_menu_area_mercs_submenu.png')
g.reset_ui(); g.click(259, 36, pause=1.0); g.click(285, 56 + 4, pause=1.0); g.shot(ART + 'FI_b1_13_menu_unit_army_submenu.png')
g.reset_ui(); g.click(259, 36, pause=1.0); g.click(285, 56 + 16*2 + 4, pause=1.0); g.shot(ART + 'FI_b1_14_menu_unit_fleet_submenu.png')
g.reset_ui(); g.click(259, 36, pause=1.0); g.click(285, 56 + 16*4 + 4, pause=1.0); g.shot(ART + 'FI_b1_15_menu_unit_city_submenu.png')
g.reset_ui(); wins(g, 'b1', 'after menus')
