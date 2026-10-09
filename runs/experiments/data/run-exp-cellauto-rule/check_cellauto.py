"""Check the decoded TCellAuto rule (tcellauto_456668.asm) against the Wine screenshot FI_b1_05_cellauto_N.png (one N press).
Model: 300 cells, states 0-3 drawn white ffffff / red ff0000 / blue 0000ff / green 008000 (form fields +0x1C0..+0x1CC);
row 0 = state 1 on cells 144..155, else 0; cells -1 and 300 stay 0; next[i] = table[old[i-1] + old[i] + old[i+1]], table = 10
values Random(4); 400 rows drawn at canvas y = 28 + row; each row drawn as runs of equal state: a single cell by Pixels[], a longer
run by MoveTo(start)/LineTo(end), which leaves the run's last pixel unpainted (the white of the cleared rectangle).
Steps: locate the canvas (row 0 known), mask the tooltip, fit the table depth-first row by row (an entry is fixed when first needed,
by every value whose redraw of that row matches the screen), then redraw all 400 rows and compare.
python3 check_cellauto.py <png> <out_json>"""
import collections, json, subprocess, sys
png, out = sys.argv[1], sys.argv[2]
raw = subprocess.run(["convert", png, "-depth", "8", "rgb:-"], capture_output=True, check=True).stdout
W, H = 1280, 1024
px = lambda x, y: raw[3 * (y * W + x):3 * (y * W + x) + 3].hex()
COL = ["ffffff", "ff0000", "0000ff", "008000"]
N, ROWS = 300, 400
def simulate(table):
    row = [0] * N
    for i in range(144, 156): row[i] = 1
    rows = [row]
    for _ in range(ROWS - 1):
        old = [0] + row + [0]
        row = [table[old[i] + old[i + 1] + old[i + 2]] for i in range(N)]
        rows.append(row)
    return rows
def draw(rows):
    img = []
    for row in rows:
        line = ["ffffff"] * N
        s = 0
        for d in range(N):
            if d < N - 1 and row[d + 1] == row[s]:
                continue
            if d == s:
                line[s] = COL[row[s]]
            else:
                for x in range(s, d): line[x] = COL[row[s]]   # LineTo excludes its end point d
            s = d + 1
        img.append(line)
    return img
# locate: the canvas is the 300 x 400 block whose top-left best matches; search where the CA colours are (right part of the screen)
best = None
inv = {c: k for k, c in enumerate(COL)}
for ox in range(480, 500):
    for oy in range(345, 365):
        # row 0 must read white except cells 144..154 red (155 is the run end, white)
        r0 = [px(ox + x, oy) for x in range(N)]
        exp0 = draw(simulate([0] * 10))[0]
        score = sum(a == b for a, b in zip(r0, exp0))
        if best is None or score > best[0]:
            best = (score, ox, oy)
_, ox, oy = best
shot = [[px(ox + x, oy + y) for x in range(N)] for y in range(ROWS)]
# the "New structure" tooltip covers part of the top-left rows: mask its bounding box (pixels outside the four CA colours, plus 1 px)
odd = [(x, y) for y in range(ROWS) for x in range(N) if shot[y][x] not in COL]
mask = set()
if odd:
    x0, x1 = min(p[0] for p in odd) - 1, max(p[0] for p in odd) + 1
    y0, y1 = min(p[1] for p in odd) - 1, max(p[1] for p in odd) + 1
    mask = {(x, y) for y in range(max(0, y0), y1 + 1) for x in range(max(0, x0), x1 + 1)}
def row_ok(y, row):
    line = draw([row])[0]
    return all(line[x] == shot[y][x] or (x, y) in mask for x in range(N))
import itertools
def fit():
    """Depth-first: a table entry is fixed the first time a row needs it, by every value whose redraw of that row matches."""
    sols = []
    def go(y, row, table):
        if y == ROWS:
            sols.append(list(table)); return
        if not row_ok(y, row):
            return
        if y == ROWS - 1:
            sols.append(list(table)); return
        old = [0] + row + [0]
        sums = [old[i] + old[i + 1] + old[i + 2] for i in range(N)]
        need = sorted({s for s in sums if table[s] is None})
        for vals in itertools.product(range(4), repeat=len(need)):
            t2 = list(table)
            for s, v in zip(need, vals): t2[s] = v
            go(y + 1, [t2[s] for s in sums], t2)
    row0 = [0] * N
    for i in range(144, 156): row0[i] = 1
    go(0, row0, [None] * 10)
    return sols
sols = fit()
table = sols[0] if len(sols) == 1 else None
model = draw(simulate([t if t is not None else 0 for t in table])) if table else None
diff = sum(model[y][x] != shot[y][x] for y in range(ROWS) for x in range(N) if (x, y) not in mask) if model else None
votes, conflicts = {}, {}
res = {"screenshot": png, "canvas_origin": [ox, oy], "row0_match": best[0], "solutions": sols, "table": table, "unused_sums": [k for k in range(10) if table and table[k] is None],
       "masked_pixels": len(mask), "mask_box": [x0, y0, x1, y1] if odd else None,
       "redraw_mismatch_pixels_outside_mask": diff, "pixels": N * ROWS, "screen_colours": dict(collections.Counter(c for r in shot for c in r))}
json.dump(res, open(out, "w"), indent=1)
print({k: res[k] for k in ("canvas_origin", "row0_match", "solutions", "unused_sums", "masked_pixels", "mask_box", "redraw_mismatch_pixels_outside_mask", "screen_colours")})
