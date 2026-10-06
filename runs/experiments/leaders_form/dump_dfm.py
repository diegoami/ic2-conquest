#!/usr/bin/env python3
"""Dump the TPickLeaders form resource (TPF0) of the original exe as indented text. Read-only on the exe.
usage: dump_dfm.py EXE OUT.txt   (uses the TPF0 parser of runs/experiments/feature_inventory/extract_forms.py; never overwrites: next free version)"""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'feature_inventory'))
import extract_forms as ef

def dump(o, ind, out):
    out.append('%sobject %s: %s' % ('  ' * ind, o['name'], o['class']))
    for k, v in o['props'].items():
        out.append('%s  %s = %r' % ('  ' * ind, k, v))
    for c in o['children']:
        dump(c, ind + 1, out)
    out.append('%send' % ('  ' * ind))

def main(exe, outp):
    d = open(exe, 'rb').read()
    out = ['# TPF0 resource of TPickLeaders from %s (sha-independent dump; offset in the exe file given)' % os.path.basename(exe)]
    for m in re.finditer(rb'TPF0\x0c', d):
        s = m.start()
        if d[s + 5:s + 17] != b'TPickLeaders': continue
        r = ef.P(d, s + 4); o = ef.obj(r)
        out.append('# offset %s end %s' % (hex(s), hex(r.p)))
        dump(o, 0, out)
    p = outp; n = 1
    while os.path.exists(p):
        n += 1; b, e = os.path.splitext(outp); p = '%s.v%d%s' % (b, n, e)
    open(p, 'w').write('\n'.join(out) + '\n'); print(p)
main(*sys.argv[1:3])
