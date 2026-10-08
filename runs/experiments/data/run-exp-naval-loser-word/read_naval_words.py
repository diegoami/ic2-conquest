"""Read the fleet map words in the run-exp-naval-battle saves (no new play), 2026-10-08: per fleet, owner, tile, ships,
the map word at the tile, the band the ships imply (owner + 300 / 316 / 332 for < 25 / < 50 / more), and the record's
covered-cell field (+24). A loser is tombstoned (owner -1).
python3 read_naval_words.py <dir with fleets-adjacent-at-sea-0723.SAV, PROBE_AFTER.SAV, NB_*_seed1.SAV>"""
import sys, struct, glob, os
sys.path.insert(0, "/home/diego/projects/ic2-conquest")
from state.sav import load
d = sys.argv[1]
w = lambda b, x, y: struct.unpack_from('<h', b, x * 280 + y * 2)[0]
band = lambda o, n: o + (300 if n < 25 else 316 if n < 50 else 332)
def cover(b, x, y, owner):
    for off in range(0, len(b) - 26):
        f = struct.unpack_from('<13h', b, off)
        if f[0] == x and f[1] == y and f[4] == owner:
            return f[12]
paths = [os.path.join(d, 'fleets-adjacent-at-sea-0723.SAV'), os.path.join(d, 'PROBE_AFTER.SAV')] + sorted(glob.glob(os.path.join(d, 'NB_*_seed1.SAV')))
for p in paths:
    b = open(p, 'rb').read(); s = load(p)
    rows = [f"f{f['id']} owner {f['owner']} ({f['x']},{f['y']}) ships {f['ships']} word {w(b, f['x'], f['y'])} "
            f"expect {band(f['owner'], f['ships']) if f['owner'] >= 0 else 'tombstone'} cover {cover(b, f['x'], f['y'], f['owner'])}"
            for f in s['fleets'] if f['id'] in (0, 1, 2)]
    print(os.path.basename(p), ' | '.join(rows))
