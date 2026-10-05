"""Play: split an army that is aboard a fleet. Fixture copy: saves/fleet-port-antium-0734.SAV (Rome; fleet 2, 30 ships, at (101,46);
army 0, 3 units, 10,700 troops at (101,45)). Steps: embark army 0 on fleet 2 (select the army, click the fleet); save (SA_01); select the FLEET; Unit map >
Army > Split army (the menu: with a fleet selected TUnitMap_SplitArmy takes the fleet's carried army); transfer the first unit; OK; save (SA_02)."""
import sys; sys.path.insert(0, '/home/diego/projects/wt-split/runs/experiments/split_aboard')
from lib import *
D = sys.modules['harness.driver']
g = MyGame(); xvfb()
log('split', 'load: %s' % g.load(fixture('fleet-port-antium-0734.SAV'), seed=12345))
def armies(tag):
    out = {}
    for i in range(30):
        a = g.army_state(i)
        if a['troops'] > 0 and a['owner'] == 0: out[i] = (a['x'], a['y'], a['moves'], a['troops'], len(a['units']), a['embarked'], a['money'], a['supplies'])
    log('split', '%s: armies %s fleet2 %s' % (tag, out, g.fleet_state(2)))
armies('SA_00_start')
keep_save(g, 'SA_00_start.SAV')
log('split', 'embark: %s' % g.embark(0, 2))
armies('SA_01_aboard')
keep_save(g, 'SA_01_aboard_before_split.SAV')
g.select_fleet(2)
log('split', 'selected fleet %d army %d' % (g.i16(D.SEL_FLEET), g.i16(D.SEL_ARMY)))
g.click(259, 36, pause=1.0); g.click(275, 57, pause=1.0)
snap(g, 'SA_menu_army_submenu.png')
g.click(455, 108, pause=2.0)
log('split', 'windows after Split army: %s' % [w[1] for w in g.find_windows('.') if w[4] > 1])
snap(g, 'SA_split_dialog_open.png')
cs = g.controls('Split army')
left = g.control(cs, cls='TListBox', index=0)
transfer = sorted((c for c in cs if c['text'] == 'Transfer'), key=lambda c: c['x'])[0]
g.click(left['x'] + left['w'] // 2, left['y'] + 12, pause=0.4)
g.click_control(transfer, pause=0.6)
snap(g, 'SA_split_dialog_transferred.png')
g._ok_until_closed('Split army', cs)
log('split', 'popups: %s' % g.dismiss_popups())
armies('SA_02_after_split')
keep_save(g, 'SA_02_after_split.SAV')
g.kill()
