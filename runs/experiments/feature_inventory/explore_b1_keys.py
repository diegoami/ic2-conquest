from explore_lib import *
import hashlib, subprocess
g = Game()
def area(tag):
    p = ART + 'FI_b1_30_area_%s.png' % tag
    sh('import', '-window', 'root', '-crop', '328x142+2+126', p); 
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:12]
def clear():
    g.click(20, 110, pause=0.8); g.click(20, 110, pause=0.8)
def key(k):
    sh('xdotool', 'mousemove', '520', '45'); time.sleep(0.3); sh('xdotool', 'key', k); time.sleep(1.5)
clear(); base = area('cleared'); log('b1', 'area map cleared hash %s' % base)
res = {}
for k in ('ctrl+p', 'ctrl+q', 'ctrl+c', 'shift+p', 'shift+c'):
    clear(); b = area('cleared_before_' + k.replace('+', '_'))
    key(k); h = area(k.replace('+', '_')); res[k] = (b != h)
    log('b1', 'key %s: area map changed vs cleared: %s (%s -> %s)' % (k, b != h, b, h))
clear()
g.shot(ART + 'FI_b1_31_after_keys.png')
