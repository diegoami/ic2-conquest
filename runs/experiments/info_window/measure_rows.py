"""Pixel evidence for list rows (PR #46 round 2 R2): for every list capture (right-click lists and mercenary lists, scrolled or not) and every panel line 0..23,
the left and right extent of the dark ink of that line in the screenshot (crop 326 px wide, line n at y = 22 + 16 n, 14 px high; the window's right border is at 326).
A row may be treated as clipped by the window only if its ink reaches the edge: right clip when ink_right >= 318, left clip when ink_left <= 2 (normal rows start at x = 7).
    python3 measure_rows.py [--write]     writes DATA/row_extents.tsv (versioned): png, line, ink_left, ink_right"""
import sys, os, csv, glob, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, ART, write_new
KINDS = ('army_right', 'army_right_scrolled', 'merc_list', 'merc_list_scrolled', 'fleet_right', 'army_foreign_right')
def extent(png, line):
    r = subprocess.run(['convert', png, '+repage', '-crop', '326x14+0+%d' % (22 + 16 * line), '+repage', '-colorspace', 'Gray', '-threshold', '55%', '-negate', '-format', '%@', 'info:'],
                       capture_output=True, text=True).stdout.strip()
    m = re.fullmatch(r'(\d+)x(\d+)\+(\d+)\+(\d+)', r)
    if not m or int(m.group(1)) == 0: return None
    w, h, x, y = map(int, m.groups()); return (x, x + w)
def main(write=False):
    rows = []
    for f in sorted(glob.glob(DATA + 'captures*.tsv')):
        for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'):
            if r['kind'] in KINDS: rows.append(r['png'])
    out = ['png\tline\tink_left\tink_right\n']
    for png in sorted(set(rows)):
        for line in range(24):
            e = extent(ART + png, line)
            if e: out.append('%s\t%d\t%d\t%d\n' % (png, line, e[0], e[1]))
    print(len(out) - 1, 'line extents')
    if write: print(write_new(DATA + 'row_extents.tsv', ''.join(out)))
if __name__ == '__main__': main('--write' in sys.argv)
