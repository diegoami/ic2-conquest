"""The TPickLeaders resource of an exe as the lines of dfm_TPickLeaders.txt (without the '#' header lines), for the audit's re-extraction check (read-only on the exe)."""
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'feature_inventory'))
import extract_forms as ef

def _dump(o, ind, out):
    out.append('%sobject %s: %s' % ('  ' * ind, o['name'], o['class']))
    for k, v in o['props'].items(): out.append('%s  %s = %r' % ('  ' * ind, k, v))
    for c in o['children']: _dump(c, ind + 1, out)
    out.append('%send' % ('  ' * ind))

def dump(exe):
    d = open(exe, 'rb').read(); out = []
    for m in re.finditer(rb'TPF0\x0c', d):
        s = m.start()
        if d[s + 5:s + 17] != b'TPickLeaders': continue
        r = ef.P(d, s + 4); _dump(ef.obj(r), 0, out)
    return out
