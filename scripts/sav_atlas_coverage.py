#!/usr/bin/env python3
"""Coverage checker for the original-SAV field map (conquest issue #107).

    python3 scripts/sav_atlas_coverage.py                       # static check only
    python3 scripts/sav_atlas_coverage.py --root DIR SAV... --out runs/experiments/data/run-exp-sav-atlas107/<name>.json

Static check: every record type's rows in the field map (default field-map-v13.csv;
`--field-map` selects another, e.g. v1) tile its stride
exactly (no gap, no overlap; `rec:<type>` rows nest a sub-record array), every
row has a known semantic class, and the nation rows have exactly the ranges of
the research37 nation-matrix-v2.csv.

Corpus check: frames each SAV in the order of the original serializer
(save FUN_004484D0 / load FUN_004487C4), requires the walk to end exactly at
the file end (battle block included when the trailer flag is set), and counts
every byte of the file by its field's semantic class. It also counts, per
UNKNOWN or INERT nation range, how many of the 16 records hold a non-zero byte.

Output is scalar only (sizes, counts, hashes, metric totals): no SAV bytes,
names or values are written. Inputs are opened read-only. The output file is
created exclusively and never overwritten (CLAUDE.md rule 6).
"""
import argparse
import csv
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "runs" / "experiments" / "data"
FIELD_MAP = DATA / "run-exp-sav-atlas107" / "field-map-v13.csv"  # v1-v12 kept beside it
NATION_MATRIX = DATA / "run-exp-sav-export37" / "nation-matrix-v2.csv"

RECORD_LEN = {"map_cell": 2, "city": 34, "army_count": 2, "army": 656, "army_slot": 32,
              "fleet_count": 2, "fleet": 26, "nation": 1172, "merc": 12, "news_index": 2,
              "news_slot": 61, "trailer": 55, "battle": 2105, "battle_slot": 44}
SEMANTIC = ("CONFIRMED", "CONTEXTUAL", "PARTIAL", "UNKNOWN", "INERT")
MAP_CELLS, CITIES, NATIONS, MERCS, ARMY_CAP, NEWS_MAX = 320 * 140, 334, 16, 50, 198, 39


def load_map(path=FIELD_MAP):
    rows = list(csv.DictReader(open(path, newline="")))
    for r in rows:
        r["first"], r["last"] = int(r["first"], 0), int(r["last"], 0)
        r["repeat"] = int(r["repeat"])
    return rows


def static_check(rows, matrix=NATION_MATRIX):
    """Return a list of problems (empty = the map tiles every record exactly)."""
    errs, ids = [], set()
    for r in rows:
        if r["field_id"] in ids:
            errs.append(f"duplicate field id {r['field_id']}")
        ids.add(r["field_id"])
        if r["record"] not in RECORD_LEN:
            errs.append(f"{r['field_id']}: unknown record {r['record']}")
        if r["semantic"] not in SEMANTIC:
            errs.append(f"{r['field_id']}: unknown semantic class {r['semantic']}")
        width = r["last"] - r["first"] + 1
        if r["type"].startswith("rec:"):
            sub = r["type"][4:]
            if sub not in RECORD_LEN or width != RECORD_LEN[sub] * r["repeat"]:
                errs.append(f"{r['field_id']}: array of {sub} x{r['repeat']} is not {width} bytes")
        elif r["repeat"] != 1:
            errs.append(f"{r['field_id']}: repeat only allowed on rec: rows")
    for rec, length in RECORD_LEN.items():
        own = sorted((r for r in rows if r["record"] == rec), key=lambda r: r["first"])
        pos = 0
        for r in own:
            if r["first"] != pos:
                errs.append(f"{rec}: {'gap' if r['first'] > pos else 'overlap'} at 0x{pos:X} before {r['field_id']}")
            pos = max(pos, r["last"] + 1)
        if pos != length:
            errs.append(f"{rec}: rows end at 0x{pos:X}, record is 0x{length:X}")
    if matrix and Path(matrix).exists():
        want = [(int(m["first"], 16), int(m["last"], 16)) for m in csv.DictReader(open(matrix, newline=""))]
        have = sorted((r["first"], r["last"]) for r in rows if r["record"] == "nation")
        if want != have:
            errs.append("nation rows differ from nation-matrix-v2.csv ranges")
    return errs


def byte_classes(rows, rec):
    """Semantic class of each byte of one `rec` record, sub-arrays expanded."""
    out = []
    for r in sorted((r for r in rows if r["record"] == rec), key=lambda r: r["first"]):
        if r["type"].startswith("rec:"):
            out += byte_classes(rows, r["type"][4:]) * r["repeat"]
        else:
            out += [r["semantic"]] * (r["last"] - r["first"] + 1)
    return out


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def frame(b):
    """Walk the serializer order. Returns (blocks [(record, offset, count)], facts) or raises ValueError."""
    blocks, o = [], 0

    def take(rec, n=1):
        nonlocal o
        if n < 0 or o + RECORD_LEN[rec] * n > len(b):
            raise ValueError(f"{rec} x{n} at {o} runs past the end ({len(b)})")
        blocks.append((rec, o, n))
        o += RECORD_LEN[rec] * n

    take("map_cell", MAP_CELLS)
    take("city", CITIES)
    take("army_count")
    a = i16(b, o - 2)
    take("army", a)
    army_off = o - 656 * a
    take("fleet_count")
    f = i16(b, o - 2)
    take("fleet", f)
    fleet_off = o - 26 * f
    take("nation", NATIONS)
    nation_off = o - 1172 * NATIONS
    take("merc", MERCS)
    take("news_index")
    ni = i16(b, o - 2)
    if not -1 <= ni <= NEWS_MAX:
        raise ValueError(f"news index {ni} outside -1..{NEWS_MAX}")
    take("news_slot", ni + 1)
    take("trailer")
    flag = b[o - 1]
    if flag:
        take("battle")
    if o != len(b):
        raise ValueError(f"walk ends at {o}, file is {len(b)} bytes")
    facts = {"armies": a, "army_tombstones": sum(i16(b, army_off + 656 * k + 4) == -1 for k in range(a)),
             "army_count_within_runtime_cap": a <= ARMY_CAP,
             "fleets": f, "fleet_tombstones": sum(i16(b, fleet_off + 26 * k + 8) == -1 for k in range(f)),
             "news_index": ni, "battle_flag": flag, "nation_off": nation_off}
    return blocks, facts


def scan(b, rows):
    blocks, facts = frame(b)
    counts = dict.fromkeys(SEMANTIC, 0)
    cache = {}
    for rec, _, n in blocks:
        cls = cache.setdefault(rec, byte_classes(rows, rec))
        for c in cls:
            counts[c] += n
    unknown = {}
    for r in rows:
        if r["record"] == "nation" and r["semantic"] in ("UNKNOWN", "INERT"):
            span = range(r["first"], r["last"] + 1)
            unknown[r["field_id"]] = sum(any(b[facts["nation_off"] + 1172 * n + k] for k in span)
                                         for n in range(NATIONS))
    facts.pop("nation_off")
    facts["bytes_by_semantic"] = counts
    facts["physical_coverage"] = sum(counts.values()) == len(b)
    facts["unknown_nation_ranges_nonzero_records"] = unknown
    return facts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("saves", nargs="*", type=Path, help="SAV files or directories (searched for *.sav, any case)")
    ap.add_argument("--root", type=Path, help="report paths relative to this directory")
    ap.add_argument("--out", type=Path, help="write the JSON receipt here (created exclusively)")
    ap.add_argument("--field-map", type=Path, default=FIELD_MAP)
    args = ap.parse_args()
    rows = load_map(args.field_map)
    errs = static_check(rows)
    rec_bytes = {rec: dict((c, byte_classes(rows, rec).count(c)) for c in SEMANTIC) for rec in RECORD_LEN}
    fmap = args.field_map.resolve()
    report = {"field_map": str(fmap.relative_to(ROOT)) if fmap.is_relative_to(ROOT) else str(fmap),
              "field_map_sha256": hashlib.sha256(fmap.read_bytes()).hexdigest(),
              "rows": len(rows), "static_errors": errs, "record_bytes_by_semantic": rec_bytes, "files": []}
    files = []
    for p in args.saves:
        files += sorted(q for q in p.rglob("*") if q.suffix.lower() == ".sav") if p.is_dir() else [p]
    for p in files:
        b = p.read_bytes()
        entry = {"path": str(p.relative_to(args.root) if args.root else p), "bytes": len(b),
                 "sha256": hashlib.sha256(b).hexdigest()}
        try:
            entry.update(scan(b, rows))
            entry["framed"] = True
        except ValueError as e:
            entry.update(framed=False, error=str(e))
        report["files"].append(entry)
    framed = [e for e in report["files"] if e["framed"]]
    report["summary"] = {"files": len(files), "framed_to_eof": len(framed),
                         "with_battle_block": sum(1 for e in framed if e["battle_flag"]),
                         "total_bytes_by_semantic": {c: sum(e["bytes_by_semantic"][c] for e in framed) for c in SEMANTIC},
                         "unknown_ranges_nonzero_in_any_file": sorted(
                             {k for e in framed for k, v in e["unknown_nation_ranges_nonzero_records"].items() if v})}
    text = json.dumps(report, indent=1) + "\n"
    if args.out:
        with open(args.out, "x") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    for e in errs:
        print("static:", e, file=sys.stderr)
    bad = [e["path"] for e in report["files"] if not e["framed"]]
    for p in bad:
        print("not framed:", p, file=sys.stderr)
    return 1 if errs or bad else 0


if __name__ == "__main__":
    sys.exit(main())
