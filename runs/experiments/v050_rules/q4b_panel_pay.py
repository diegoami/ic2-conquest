"""Q4 (R1/R2 of the PR #47 review): the actual quarterly pay of the hired mercenaries as the army panel reports it ("Mercenary pay N talents per quarter",
TInformation_ShowArmyDetails :41076-41100: sum over mercenary units of ((troops div 200) x price x quality) div 5 per unit, the tick's formula), read from the screen
for army 1 after the Samnite hire (Q4_04) and after the Thurii hire as well (Q4_06). An independent record to compare with the formulas."""
import sys, os, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
g = MyGame(); xvfb()
for tag, save in (('Q4b_00_after_heraclea_hire', 'Q4_04_after_heraclea_hire.SAV'), ('Q4b_01_after_thurii_hire', 'Q4_06_after_thurii_hire.SAV')):
    log('q4b', 'load %s: %s' % (save, g.load(SAVEDIR + save, seed=12345)))
    ax, ay = g.army_pos(1); g.select_army(1, ax, ay)
    p = snap(g, '%s_army1_panel.png' % tag)
    txt = ocr_text(p, crop='330x740+0+270')
    m = re.search(r'Mercenary\s+pay\s+(\d+)', txt)
    log('q4b', '%s: panel text %r -> Mercenary pay %s' % (tag, ' | '.join(l for l in txt.splitlines() if l.strip())[-200:], m.group(1) if m else None))
    with open(DATA + 'q4_panel_pay.tsv', 'a') as f: f.write('%s\t%s\t%s\n' % (os.path.basename(p), save, m.group(1) if m else ''))
g.kill()
