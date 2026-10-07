#!/usr/bin/env python3
"""A01 run-length measurement: the byte-flag in TAreaMap_PaintForm is an ImageList index, so the two toggle states
are two image sets of the same tile bitmap. The two sets differ in their run-length profile: a uniform/political
map has long runs of identical grey per row; a per-tile-shaded terrain map has short runs. The claim is that the
measurement of identical-grey runs on the b8 screenshots (CG_T3_b8_area_before.png, ..._after_one.png) still
distinguishes the two states — the finding's [confirmed by measurement] annotation depends on this.

usage: a01_runs.py

Prints the per-row run-length mean / median / max for both screenshots, and exits non-zero when the measurement
no longer distinguishes the two (byte 1 should be MUCH longer-run than byte 0; the script fails when the
mean-run ratio drops below 1.5x). Read-only on the game state apart from the screenshots themselves."""
import os, struct, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(os.path.dirname(HERE), '..', '..', 'artifacts', 'run-exp-cosmetic-gaps')

def measure(path, w=304, hh=150, step=4):
    """Mean/median/max of identical-grey runs across every step-th row of the bitmap crop (x=8+34 304x150)."""
    out = subprocess.run(['convert', path, '-colorspace', 'Gray', '-depth', '8', '-crop',
                          '%dx%d+%d+%d' % (w, hh, 8, 34), '+repage', 'RGB:-'],
                         capture_output=True, check=True).stdout
    runs = []
    for y0 in range(0, hh, step):
        row = out[y0 * w:(y0 + 1) * w]
        run = 1
        for x in range(1, w):
            if row[x] == row[x - 1]:
                run += 1
            else:
                runs.append(run); run = 1
        runs.append(run)
    return statistics.mean(runs), statistics.median(runs), max(runs), len(runs)

def main():
    a = os.path.join(ART, 'CG_T3_b8_area_before.png')        # byte 1
    b = os.path.join(ART, 'CG_T3_b8_area_after_one.png')    # byte 0
    for f in (a, b):
        if not os.path.exists(f):
            sys.exit('missing screenshot %s' % f)
    ma, meda, _, _ = measure(a)
    mb, medb, _, _ = measure(b)
    ratio = ma / mb
    print('byte 1: mean=%.2fpx median=%d   (CG_T3_b8_area_before.png)' % (ma, meda))
    print('byte 0: mean=%.2fpx median=%d   (CG_T3_b8_area_after_one.png)' % (mb, medb))
    print('ratio byte1/byte0: %.2fx' % ratio)
    if ratio < 1.5:
        sys.exit('run-length ratio below 1.5x — the measurement no longer distinguishes the two states')
    if not (ma > mb):
        sys.exit('byte-1 mean is not greater than byte-0 mean')

if __name__ == '__main__':
    main()