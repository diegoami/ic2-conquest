#!/usr/bin/env python3
"""Write the tracked table of the leader-name pool read from 'Imperial Conquest 2.dat' (a static extract; the DAT itself is not in git, its SHA-256 is in the file's header).
The offset is NOT typed here: it is the sum of the reads FUN_004481a0 makes before the pool read, recomputed from the tracked code extract (claims_audit.py does the same and compares).
usage: extract_dat_pool.py [DAT]"""
import os, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new, latest, DATA
import loader_offsets
from play_meta import NATIONS
DAT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.dat')
d = open(DAT, 'rb').read()
off, length, dst = loader_offsets.pool_read(latest(os.path.join(DATA, 'code_extract_leaders.txt')))
out = ['# leader-name pool of the DAT; sha256 %s; file offset %#x (sum of the reads of FUN_004481a0 before the read of %d bytes into %s); %d nations x 12 names x 26 bytes' % (hashlib.sha256(d).hexdigest(), off, length, dst, 16),
       'nation_index\tnation\tslot\tname']
for n in range(16):
    for k in range(12):
        b = d[off + n * 312 + k * 26: off + n * 312 + (k + 1) * 26]
        out.append('%d\t%s\t%d\t%s' % (n, NATIONS[n], k, b.split(b'\0')[0].decode('latin1')))
print(write_new(os.path.join(DATA, 'dat_leader_pool.tsv'), '\n'.join(out) + '\n'))
