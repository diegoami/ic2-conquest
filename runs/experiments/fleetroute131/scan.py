#!/usr/bin/env python3.12
"""Research #131 part 1: fleet route words (+4/+6) in every distinct original save on this machine (remake-written saves
excluded). Counts live fleets with x >= 0 (an active route), x = -1, other negatives, and the y left behind under x < 0.

    python3.12 runs/experiments/fleetroute131/scan.py --version v1
"""
import argparse
import hashlib
import json
import os
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "runs/experiments/data/run-exp-fleetroute131"


def fleets(b):
    a = struct.unpack_from("<h", b, 100956)[0]
    if not 0 <= a <= 198:
        return None, None
    of = 100958 + a * 656
    f = struct.unpack_from("<h", b, of)[0]
    if not 0 <= f <= 200:
        return None, None
    on = of + 2 + f * 26
    tail_cur = None
    return [struct.unpack_from("<13h", b, of + 2 + 26 * k) for k in range(f)], on


def find_saves(roots):
    """Every *.SAV under the roots, without following symlinks (Wine prefixes link dosdevices/z: to /)."""
    out = []
    for r in roots:
        r = Path(r)
        if r.is_file():
            out.append(str(r))
            continue
        for d, dirs, files in os.walk(r, followlinks=False):
            out += [os.path.join(d, f) for f in files if f.upper().endswith(".SAV")]
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1")
    a = ap.parse_args()
    roots = [ROOT / "saves", ROOT / "artifacts", Path.home() / "ic2-work-archive", Path.home() / "ic2-work"]
    seen = set()
    c = Counter()
    ys = Counter()
    active = []
    for fn in find_saves(roots):
        if True:
            if "/remake" in fn or "remake/" in fn:
                continue
            b = Path(fn).read_bytes()
            h = hashlib.sha256(b).hexdigest()
            if h in seen or len(b) < 120000:
                continue
            seen.add(h)
            fl, _ = fleets(b)
            if fl is None:
                c["unparsed"] += 1
                continue
            c["saves"] += 1
            for k, r in enumerate(fl):
                x, y, rx, ry, owner, countdown = r[0], r[1], r[2], r[3], r[4], r[5]
                if owner < 0:
                    c["tombstones"] += 1
                    continue
                c["live_fleets"] += 1
                if rx >= 0:
                    c["active_route"] += 1
                    if len(active) < 200:
                        active.append(dict(save=Path(fn).name, sha=h[:12], fleet=k, pos=[x, y], route=[rx, ry], owner=owner,
                                           countdown=countdown, moves=r[6], cargo=r[11],
                                           path=str(Path(fn).relative_to(ROOT)) if str(fn).startswith(str(ROOT)) else "~/" +
                                           str(Path(fn).relative_to(Path.home()))))
                elif rx == -1:
                    c["x_minus1"] += 1
                    ys[ry] += 1
                else:
                    c["x_other_negative"] += 1
    res = dict(counts=c, y_under_x_minus1_top=ys.most_common(20), active_examples=active, corpus=len(seen))
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / f"scan-{a.version}.json", "x") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "active_examples"}, indent=1))
    for x in active[:30]:
        print(x)


if __name__ == "__main__":
    main()
