#!/usr/bin/env python3
"""Independent source for the unit price tables: read them from the game's DAT file (not from the decompile, not from the findings).
Layout (research report unit-type-stat-table-in-dat.md): five 40-byte records from file offset 0x1F2F0 (light infantry, heavy infantry, archers,
light cavalry, heavy cavalry): 16-byte name, 8-byte abbreviation, then 8 words; word +0x22 = initial recruit price, +0x24 = quarterly price per 200 troops.
Writes dat_unit_prices.tsv (tracked, versioned) with the DAT's SHA-256. usage: extract_dat_prices.py [path-to-dat]"""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DAT, DATA
from common import write_new
p = sys.argv[1] if len(sys.argv) > 1 else DAT
b = open(p, 'rb').read()
rows = ['# source: Imperial Conquest 2.dat sha256 %s; records at 0x1F2F0 + 0x28*k' % hashlib.sha256(b).hexdigest(), 'type\tname\tinitial_price\tquarterly_price']
for k, t in enumerate(('li', 'hi', 'ar', 'lc', 'hc')):
    o = 0x1F2F0 + 0x28 * k
    name = b[o:o + 16].split(b'\0')[0].decode('latin1')
    ini, q = struct.unpack_from('<2H', b, o + 0x22)
    rows.append('%s\t%s\t%d\t%d' % (t, name, ini, q))
print(write_new(os.path.join(DATA, 'dat_unit_prices.tsv'), '\n'.join(rows) + '\n'))
