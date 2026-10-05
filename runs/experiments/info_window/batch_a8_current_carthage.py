"""Batch a8 (PR #46 R6): the own-nation panel when the current nation is Carthage (A7_current_carthage.SAV: Mobilized 12, Treasury 7,777), captured after a
VERIFIED refresh: another nation is chosen first, and the capture is accepted only when its OCR names the nation asked for (up to 3 tries)."""
from iw_lib import *
save = ART + 'saves/A7_current_carthage.SAV'
g = Game(); launch(g, save)
p = sav.load(save); print('current', p['current_nation'], p['nations'][1]['treasury'], p['nations'][1]['mobilization'])
for n in (1, 0, 2):
    for attempt in range(3):
        nation_menu(g, (n + 2) % 15 if attempt == 0 else (n + 3 + attempt) % 15); nation_menu(g, n)
        png, ocr = capture('a8', save, 'nation', n, {'current': 1, 'attempt': attempt, 'verified_refresh': 'other nation first'}, 'A8_cur1_nation%02d.png' % n)
        if ('Nation ' + sav.NATIONS[n]) in ocr: break
    print(n, attempt, ' | '.join(l for l in ocr.splitlines() if l.strip())[:230])
stop(g)
