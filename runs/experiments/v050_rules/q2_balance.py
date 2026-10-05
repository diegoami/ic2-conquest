"""Q2 play: the Balance sheet of Rome at 0720 (run0-start fixture) at tax 10% and after Taxation to 20%: which line is taxBase div 4?
Prediction from TBalanceSheet_PaintBalance (:55439-55456): Taxes = taxBase x tax / 100; Tribute = taxBase div 4 (not tax-dependent);
Trade = sum of partner taxBase div 12 over relation 1 or 2. Rome: taxBase 2,528 -> Taxes 252, Tribute 632 at 10%; Taxes 505, Tribute 632 at 20%."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
g = MyGame(); xvfb()
log('q2', 'load: %s' % g.load(fixture('run0-start-AUTO0720-seed12345.SAV'), seed=12345))
snapstate(g, 'Q2_00_start_tax10')
def sheet(tag):
    open_tool(g, 'balance', 'Balance sheet')
    time.sleep(1.0)
    p = snap(g, 'Q2_%s_balance_sheet.png' % tag)
    w = g.find_windows('^Balance sheet$')[0]
    txt = ocr_text(p, crop='%dx%d+%d+%d' % (w[4], w[5], w[2], w[3]))
    log('q2', 'balance sheet %s OCR: %s' % (tag, ' | '.join(l for l in txt.splitlines() if l.strip())))
    cs = g.controls('Balance sheet'); g.close_controls('Balance sheet', cs)
    return p
keep_save(g, 'Q2_00_start_tax10.SAV')
sheet('00_tax10')
log('q2', 'taxation 20: %s' % g.taxation(20))
snapstate(g, 'Q2_01_tax20')
keep_save(g, 'Q2_01_tax20.SAV')
sheet('01_tax20')
g.kill()
