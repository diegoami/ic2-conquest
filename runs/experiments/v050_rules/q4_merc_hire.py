"""Q4 play: hiring priced mercenary offers (Recruit mercenaries) with a small purse, on a copy of run0-start-AUTO0720-seed12345.SAV
(Rome human, army 1 at (120,53) next to Heraclea, purse 100, supplies 176, treasury 2,200).
Offers (pool slots of the start save): Heraclea slot 25 Samnite LI 3,868 q8 (gate (3868x1 div 1000) x 8 = 24; the dialog's "Quarterly cost" (3868x1x8) div 1000 = 30),
Thurii slot 34 Insubre... HC 960 q9 (gate (960x4 div 1000) x 9 = 27; Quarterly cost 960x4x9 div 1000 = 34).
Prediction from TRecruitMercs_RecruitMercUnit (:43633-43636): the hire is refused if purse < gate; otherwise the unit is added and NOTHING is subtracted
from the purse or the treasury.
Steps: (1) purse 20 (< 24) at Heraclea: refusal; (2) purse 30: hire the Samnite (30 >= 24): purse stays 30; (3) move to (120,55) next to Thurii, purse 30:
hire the HC (30 >= 27 although < 34): purse stays 30."""
import sys; sys.path.insert(0, '/home/diego/projects/wt-rules/runs/experiments/v050_rules')
from lib import *
g = MyGame(); xvfb()
log('q4', 'load: %s' % g.load(fixture('run0-start-AUTO0720-seed12345.SAV'), seed=12345))
A = (0, 1)
def pool(): return [(m['slot'], m['x'], m['y'], m['label'], m['type'], m['troops'], m['quality']) for m in S.parse(open(g_save, 'rb').read())['mercenaries']] if False else None
snapstate(g, 'Q4_00_start', A)
keep_save(g, 'Q4_00_start.SAV')
def hire(tag, row=0):
    g.army_tool(1, 'mercs', 'Recruit mercenary unit')
    cs = g.controls('Recruit mercenary unit')
    lb = g.control(cs, cls='TListBox')
    g.click(lb['x'] + lb['w'] // 2, lb['y'] + 12 + 12 * row, pause=0.6)
    snap(g, 'Q4_%s_offer_selected.png' % tag)
    g.click_control(g.control(cs, text='Recruit unit'), pause=1.2)
    p = snap(g, 'Q4_%s_after_recruit_click.png' % tag)
    boxes = [w for w in g.find_windows('.') if w[1] in ('Information', 'Confirm') and w[4] < 600 and w[5] < 300 and w[1] != 'Information' or (w[1] == 'Information' and w[5] < 300 and w[4] < 600)]
    texts = [ocr_text(p, crop='%dx%d+%d+%d' % (w[4], w[5], w[2], w[3])).strip().replace('\n', ' ') for w in boxes]
    g.dismiss_popups()
    if g.find_windows('^Recruit mercenary unit$'):
        cs = g.controls('Recruit mercenary unit'); g.close_controls('Recruit mercenary unit', cs)
    return texts
log('q4', 'supply army 1 money 10s x -8: %s' % supply_dialog(g, 1, money10=-8))
snapstate(g, 'Q4_01_purse20', A); keep_save(g, 'Q4_01_purse20_before_hire.SAV')
log('q4', 'hire at Heraclea with purse 20: %s' % hire('02_heraclea_purse20'))
snapstate(g, 'Q4_02_after_refused_hire', A); keep_save(g, 'Q4_02_after_refused_hire.SAV')
log('q4', 'supply army 1 money 10s x +1: %s' % supply_dialog(g, 1, money10=1))
snapstate(g, 'Q4_03_purse30', A); keep_save(g, 'Q4_03_purse30_before_hire.SAV')
log('q4', 'hire at Heraclea with purse 30: %s' % hire('04_heraclea_purse30'))
snapstate(g, 'Q4_04_after_heraclea_hire', A); keep_save(g, 'Q4_04_after_heraclea_hire.SAV')
log('q4', 'move army 1 to (120,55): %s' % (g.move(1, 120, 55),))
snapstate(g, 'Q4_05_at_120_55', A); keep_save(g, 'Q4_05_before_thurii_hire.SAV')
log('q4', 'hire at Thurii with purse 30: %s' % hire('06_thurii_purse30'))
snapstate(g, 'Q4_06_after_thurii_hire', A); keep_save(g, 'Q4_06_after_thurii_hire.SAV')
g.kill()
