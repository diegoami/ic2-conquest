"""Dump the word tables the panels index (from the DAT, via the loader's read order) with the memory address, DAT offset, index expression and its decompile line.
    python3 extract_tables.py [--write]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, write_new
import panel_model as M
SPEC = [  # name, address, stride, entries shown, who indexes it (decompile line in all_app_functions.txt)
    ('quality words', 0x47938c, 11, 10, 'DAT_0047938c + q*0xb: F:41257 (city mercs), F:41302 (army units), q = the unit/merc quality field 0..9 used directly'),
    ('unity/loyalty words', 0x4793fc, 11, 10, 'DAT_004793fc + (unity/100)*0xb: F:40830 (nation); DAT_004793fc + (loyalty/10)*0xb: F:40926 (city); signed truncating division'),
    ('morale words (= unity table from entry 4)', 0x479428, 11, 6, 'DAT_00479428 + ((m-0x33, or m-0x30 when that is < 0) >> 2)*0xb: F:41052-41058; same bytes as the unity table entries 4..9'),
    ('relation words', 0x4794c8, 6, 5, 'DAT_004794c8 + rel*6 when 0 < rel: F:40871 (rel = nation record +0x26 + 2*other)'),
    ('terrain names', 0x4792e4, 14, 12, 'DAT_004792e4 + cell*0xe: F:41072 (army +8, when >= 0)'),
    ('unit type names', 0x478fb0, 0x28, 5, 'DAT_00478fb0 + type*0x28: F:41094, 41254, 41298'),
]
rows = ['table\tindex\tmem_address\tdat_offset\tword\tindexed_by\n']
for name, a, st, n, why in SPEC:
    off, size = [v for k, v in M.TABLES.items() if k <= a < k + v[1]][0] if False else (None, None)
    base = max(k for k in M.TABLES if k <= a)
    for i in range(n):
        addr = a + i * st
        doff = M.TABLES[base][0] + (addr - base)
        rows.append('%s\t%d\t0x%06X\t0x%05X\t%r\t%s\n' % (name, i, addr, doff, M.cstr(addr), why if i == 0 else ''))
rows.append('# tribute word (foreign city), F:40961-40977, u = the city +0x20 field as unsigned 16-bit: u<0xb poor; (u-0xb)<0x14 moderate; (u-0x1f)<0x46 rich; (u-0x65)<0x26ac very rich; otherwise no word (the number text stays)\n')
rows.append('# sea word F:41220: fleet +0x18 (DAT_0049c284) == 0 -> calm, else rough\n')
out = ''.join(rows); print(out)
if '--write' in sys.argv: print(write_new(DATA + 'code_word_tables.tsv', out))
