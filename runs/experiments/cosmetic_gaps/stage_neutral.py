#!/usr/bin/env python3
"""Stage the neutral-Felsina save for the U2b play: a copy of saves/siege-felsina-failed-0721.SAV with the
Rome<->Gaul relation words set to 0 (both directions; both were 3, war), NOTHING else changed. This is a STAGED
save (docs/tasks/cosmetic-gaps.md: a staged save must be labelled as staged): the play's record says STAGED and
this note is tracked beside the data. The save itself is a binary: it stays in the gitignored artifacts dir,
hashed into SAVES.sha256 and uploaded with the batch (rule 1).
usage: stage_neutral.py"""
import os, sys, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from paths import ROOT, ART, DATA
import state.sav as SAV
from state.sav import ARMY_OFF, ARMY_LEN, FLEET_LEN, NATION_LEN, NATIONS

SRC = ROOT + '/saves/siege-felsina-failed-0721.SAV'
DST = ART + 'STAGED-felsina-neutral-0721.SAV'

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

b = bytearray(open(SRC, 'rb').read())
na = struct.unpack_from('<h', b, ARMY_OFF)[0]
o = ARMY_OFF + 2 + na * ARMY_LEN
nf = struct.unpack_from('<h', b, o)[0]
o += 2 + nf * FLEET_LEN
rome, gaul = NATIONS.index('Rome'), NATIONS.index('Gaul')
rb, gb = o + rome * NATION_LEN, o + gaul * NATION_LEN
assert SAV.cstr(bytes(b[rb:rb + 11])) == 'Rome' and SAV.cstr(bytes(b[gb:gb + 11])) == 'Gaul', 'nation records not where the layout says'
# Felsina's owner word (city table, 0x11 stride at 0x4795a2 in memory; in the save the city records follow the map)
d = SAV.parse(bytes(b))
fels = next(c for c in d['cities'] if c['name'] == 'Felsina')
assert NATIONS[fels['owner']] == 'Gaul', 'Felsina owner %r is not Gaul' % fels['owner']
br = struct.unpack_from('<h', b, rb + 0x26 + 2 * gaul)[0]
bg = struct.unpack_from('<h', b, gb + 0x26 + 2 * rome)[0]
assert br == 3 and bg == 3, 'expected war (3), got Rome->Gaul %d, Gaul->Rome %d' % (br, bg)
struct.pack_into('<h', b, rb + 0x26 + 2 * gaul, 0)
struct.pack_into('<h', b, gb + 0x26 + 2 * rome, 0)
if os.path.exists(DST):
    sys.exit('%s already exists (rule 6: never overwrite); it is kept' % DST)
open(DST, 'wb').write(b)
with open(DATA + 'SAVES.sha256', 'a') as f:
    f.write('%s  %s\n' % (sha(DST), os.path.basename(DST)))
note = ['# Staged save %s' % os.path.basename(DST),
        '# source %s (sha256 %s)' % (os.path.basename(SRC), sha(SRC)),
        '# staged sha256 %s' % sha(DST),
        '# the ONLY change: Rome->Gaul relation 3->0 and Gaul->Rome 3->0 (nation records +0x26, 16 shorts)',
        '# purpose: the U2b play needs a foreign NON-hostile city (Felsina) next to army 0; every repo fixture has Rome at war with Gaul',
        '# labelled STAGED in the play record and the finding']
from common import write_new
print(write_new(os.path.join(DATA, 'STAGED-felsina-neutral.txt'), '\n'.join(note) + '\n'))
print(DST)
