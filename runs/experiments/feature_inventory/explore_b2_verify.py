"""Offline re-check of the batch-2 submenu screenshots with the strict rule: identical crop of the parent menu and the submenu image must differ,
and ALL expected item names of the submenu must be read back by OCR. Output goes to a new versioned log (rule 6)."""
import sys, os, subprocess, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new, DATA
ART = os.path.normpath(os.path.join(DATA, '..', '..', '..', '..', 'artifacts', 'run-exp-feature-inventory')) + '/'
EXPECT = {'army': ['Supply army', 'Recruit mercenaries', 'Transfer unit', 'Split army', 'Join armies', 'Change units', 'Disband army'],
          'fleet': ['Supply fleet', 'Repair fleet', 'Transfer ships', 'Split fleet', 'Join fleets', 'Scuttle fleet'], 'city': ['Fortify city']}
def crop(path, geom, out):
    subprocess.run(['convert', path, '-crop', geom, '+repage', out], check=True)
    return hashlib.sha256(open(out, 'rb').read()).hexdigest()
def words(path):
    tmp = '/tmp/claude-1000/v_ocr.png'
    subprocess.run(['convert', path, '-resize', '400%', '-colorspace', 'Gray', tmp], check=True)
    t = subprocess.run(['tesseract', tmp, 'stdout', '--psm', '4'], capture_output=True, text=True).stdout.lower()
    return ' '.join(t.split())
log = []
ph = crop(ART + 'FI_b2_01_unit_menu_parent.png', '480x300+0+0', '/tmp/claude-1000/v_parent.png')
log.append('parent crop 480x300 hash %s' % ph[:12])
allok = True
for k, items in EXPECT.items():
    p = ART + 'FI_b2_02_unit_%s_submenu.png' % k
    h = crop(p, '480x300+0+0', '/tmp/claude-1000/v_%s.png' % k)
    txt = words(p)
    # the submenu region only (right of the parent menu)
    sub = crop(p, '300x300+380+0', '/tmp/claude-1000/v_%s_sub.png' % k); subtxt = words('/tmp/claude-1000/v_%s_sub.png' % k)
    missing = [i for i in items if i.lower() not in subtxt]
    ok = (h != ph) and not missing
    allok &= ok
    log.append('%s: identical-crop hash %s (parent %s) differs=%s; missing items=%s -> %s' % (k, h[:12], ph[:12], h != ph, missing, 'PROVEN' if ok else 'NOT PROVEN'))
log.append('ALL PROVEN' if allok else 'SOME NOT PROVEN')
print('\n'.join(log)); print(write_new(os.path.join(DATA, 'explore', 'b2_offline_verify.log'), '\n'.join(log) + '\n'))
