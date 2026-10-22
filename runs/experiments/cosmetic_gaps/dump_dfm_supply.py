#!/usr/bin/env python3
"""Dump the TAFSupply form resource (TPF0) of the game exe as indented text, into the tracked data dir (rule 6).
Read-only on the exe. usage: dump_dfm_supply.py [EXE]   (uses the TPF0 parser of runs/experiments/feature_inventory/
extract_forms.py; never overwrites: next free version). Modeled on runs/experiments/leaders_form/dump_dfm.py."""
import sys, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'feature_inventory'))
sys.path.insert(0, HERE)
import extract_forms as ef
import importlib.util as _ilu               # ef's import cached feature_inventory's common: load OURS by path
_spec = _ilu.spec_from_file_location('cg_common', os.path.join(HERE, 'common.py'))
_cg_common = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_cg_common)
write_new, DATA = _cg_common.write_new, _cg_common.DATA

EXE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    '~/ic2-work-cosmetic/prefix/drive_c/IC2/Imperial Conquest 2 fast rollingsave seed.exe')
FORM = b'TAFSupply'

def dump(o, ind, out):
    out.append('%sobject %s: %s' % ('  ' * ind, o['name'], o['class']))
    for k, v in o['props'].items():
        out.append('%s  %s = %r' % ('  ' * ind, k, v))
    for c in o['children']:
        dump(c, ind + 1, out)
    out.append('%send' % ('  ' * ind))

d = open(EXE, 'rb').read()
out = ['# TPF0 resource of %s from %s (read-only dump; offset in the exe file given)' % (FORM.decode(), os.path.basename(EXE))]
found = 0
for m in re.finditer(rb'TPF0', d):
    p = m.start() + 4
    if d[p] != len(FORM) or d[p + 1:p + 1 + len(FORM)] != FORM: continue
    r = ef.P(d, p); o = ef.obj(r)
    out.append('# offset %s end %s' % (hex(m.start()), hex(r.p)))
    dump(o, 0, out)
    found += 1
if not found:
    sys.exit('no %s TPF0 resource found in %s' % (FORM.decode(), EXE))
p = write_new(os.path.join(DATA, 'dfm_TAFSupply.txt'), '\n'.join(out) + '\n')
print(p, '(%d form resource(s))' % found)
