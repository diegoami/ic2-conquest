#!/usr/bin/env python3
"""Static reader/writer index of the original-SAV fields (conquest issue #107).

    python3 scripts/sav_atlas_access.py --source $IC2_DECOMPILE/all_app_functions.txt \
        --out-dir runs/experiments/data/run-exp-sav-atlas107 --tag v1

Scans the pinned decompilation for every literal address inside a serialized
runtime table (map, nations, cities, armies, fleets, mercenary pool, news,
trailer globals, battle header/slots/grid). It resolves each address to a
field of field-map-v1.csv:
  - offset = (address - base) mod stride (Ghidra folds the field offset into
    the label; a label just below a base is record -1, as in `F - 1` indexing);
  - plus a constant term inside a following `[...]`, scaled by the element
    size stride / multiplier.
Each hit is classed `write` (assignment or ++/--), `read`, or `escape` (the
address is taken and passed on: a copy/compare/serializer whose bytes this scan
cannot attribute). Lines that index with a record stride but name no table
literal (a pointer variable or parameter) are counted per function as the
`pointer frontier`.

This is a literal-address lead index, not reader/writer closure: pointer
aliases, escapes and indirect calls stay open. Output holds function names,
addresses, line numbers and classes only, never source text. Files are created
exclusively (CLAUDE.md rule 6).
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sav_atlas_coverage as cov  # noqa: E402

# Serialized runtime tables: (name, base, stride, records, ledger record type).
TABLES = [
    ("map", 0x45E870, 2, 320 * 140, "map_cell"),
    ("nation", 0x474670, 1172, 16, "nation"),
    ("city", 0x479590, 34, 334, "city"),
    ("army", 0x47C1EC, 656, 200, "army"),            # 200 slots to the fleet base; 198 usable
    ("fleet", 0x49C26C, 26, 100, "fleet"),           # ends at the label-name table 0x49CC94
    ("merc", 0x49D0A4, 12, 251, "merc"),             # DAT templates 0-200; live (saved) pool 201-250
    ("news", 0x49F994, 61, 40, "news_slot"),
    ("battle_slot", 0x4A0344, 44, 40, "battle_slot"),
    ("battle_grid", 0x4A0A24, 2, 168, None),
]
MERC_LIVE = 201
WIDTH = {"char": 1, "byte": 1, "undefined1": 1, "bool": 1, "short": 2, "ushort": 2, "undefined2": 2,
         "int": 4, "uint": 4, "undefined4": 4, "dword": 4, "float": 4}
LIT = re.compile(r"(?:DAT_|PTR_|UNK_|_DAT_)([0-9a-fA-F]{8})\b|\b0x([0-9a-fA-F]{6,8})\b")
FUNC = re.compile(r"^// ==== (.+?) @ ([0-9a-fA-F]+) ====")
STRIDES = {656: "army", 0x148: "army", 0x494: "nation", 0x24A: "nation", 34: "city", 0x11: "city",
           26: "fleet", 0xD: "fleet"}


def scalar_fields(rows):
    """Single-address ledger fields (counts, trailer, battle header) from their runtime column."""
    out = {}
    for r in rows:
        m = re.fullmatch(r"0x([0-9A-Fa-f]+)", r["runtime"].strip())
        if m and r["record"] in ("army_count", "fleet_count", "news_index", "trailer", "battle"):
            out[int(m.group(1), 16)] = (r, r["last"] - r["first"] + 1)
    return out


def field_at(rows, rec, off):
    """(field_id, offset within the field) of byte `off` of record type `rec`."""
    for r in rows:
        if r["record"] == rec and r["first"] <= off <= r["last"]:
            if r["type"].startswith("rec:"):
                sub = r["type"][4:]
                fid, rel = field_at(rows, sub, (off - r["first"]) % cov.RECORD_LEN[sub])
                return fid, rel
            return r["field_id"], off - r["first"]
    return None, None


def bracket(text, i):
    """If text[i:] starts with `[` (after spaces/`)`), return (inner, end index)."""
    j = i
    while j < len(text) and text[j] in " )":
        j += 1
    if j >= len(text) or text[j] != "[":
        return None, i
    depth = 0
    for k in range(j, len(text)):
        depth += text[k] == "["
        depth -= text[k] == "]"
        if depth == 0:
            return text[j + 1:k], k + 1
    return None, i


def top_level_terms(expr):
    terms, depth, cur, sign = [], 0, "", 1
    for ch in expr:
        depth += ch in "(["
        depth -= ch in ")]"
        if depth == 0 and ch in "+-" and cur.strip():
            terms.append((sign, cur.strip())); cur, sign = "", (1 if ch == "+" else -1)
        else:
            cur += ch
    if cur.strip():
        terms.append((sign, cur.strip()))
    return terms


def const(term):
    m = re.fullmatch(r"\(?(?:int|short|uint)?\)?\s*(0x[0-9a-fA-F]+|\d+)", term)
    return int(m.group(1), 0) if m else None


ASSIGN = re.compile(r"\s*\)*\s*(?:[-+*/|&^]|<<|>>)?=(?!=)|\s*\)*\s*(?:\+\+|--)")
CAST_DEREF = re.compile(r"\*\s*\(\s*(\w+)\s*\*\s*\)\s*\(\s*(?:\(\s*\w+\s*\)\s*)?$")


def access(line, lm):
    """(kind, byte offset to add, width or None, elem or None, has_index) of the literal match lm."""
    s = lm.start() - (1 if line[lm.start() - 1:lm.start()] == "&" else 0)
    amp = s < lm.start()
    inner, end = bracket(line, lm.end())
    add, width, elem, indexed = 0, None, None, False
    if inner is not None:
        indexed = True
        terms = top_level_terms(inner)
        mult = [int(x, 0) for _, t in terms for x in re.findall(r"\*\s*(0x[0-9a-fA-F]+|\d+)\s*$", t)]
        return "idx", terms, mult, end, s
    m = CAST_DEREF.search(line[:s])
    if m:
        depth, end = 1, len(line)
        for k in range(lm.end(), len(line)):
            depth += line[k] == "("
            depth -= line[k] == ")"
            if depth == 0:
                end = k + 1
                break
        terms = top_level_terms(line[lm.end():end - 1])
        add = sum(sg * c for sg, t in terms if (c := const(t)) is not None)
        indexed = any("*" in t for _, t in terms)
        variable = any(const(t) is None for _, t in terms)
        mults = [int(x, 0) for _, t in terms for x in re.findall(r"\*\s*(0x[0-9a-fA-F]+|\d+)\s*$", t)]
        width = WIDTH.get(m.group(1))
        return "cast", add, width, end, indexed, variable, mults
    if amp:
        return "escape", 0, None, lm.end(), False
    return "plain", 0, None, lm.end(), False


def kind_of(line, end, start):
    if ASSIGN.match(line[end:]) or re.search(r"(?:\+\+|--)\s*$", line[:start]):
        return "write"
    return "read"


def fields_over(rows, rec, off, width):
    """Every leaf field overlapping bytes [off, off + width) of one `rec` record."""
    out = []
    for b in range(off, off + (width or 1)):
        if b >= cov.RECORD_LEN[rec]:
            break
        fid, _ = field_at(rows, rec, b)
        if fid not in out:
            out.append(fid)
    return out


def scan(lines, rows):
    scal = scalar_fields(rows)
    by_addr = {}
    for a, (r, w) in scal.items():
        for k in range(w):
            by_addr[a + k] = (r["field_id"], k)
    hits, frontier, func = [], defaultdict(int), ("?", "0")
    for n, line in enumerate(lines, 1):
        m = FUNC.match(line)
        if m:
            func = (m.group(1), m.group(2).lower()); continue
        if line.lstrip().startswith("//"):
            continue
        named = False
        for lm in LIT.finditer(line):
            a = int(lm.group(1) or lm.group(2), 16)
            form = access(line, lm)
            hit = None
            if a in by_addr:
                fid, rel = by_addr[a]
                width = form[2] if form[0] == "cast" else None
                hit = dict(fields=[fid], record=None, width=width)
            else:
                for name, base, stride, count, rec in pick_tables(a, form):
                    idx, off = divmod(a - base, stride)
                    width, indexed = None, False
                    if form[0] == "idx":
                        terms, mult = form[1], form[2]
                        indexed = True
                        elem = stride // mult[0] if mult and mult[0] and stride % mult[0] == 0 else (
                            stride if stride <= 2 else None)
                        for sg, t in terms:
                            c = const(t)
                            if c is not None and elem:
                                off += sg * c * elem
                        width = elem if elem and elem <= 4 else None
                    elif form[0] == "cast":
                        off += form[1]
                        width, indexed = form[2], form[4] or form[5]
                    idx, off = idx + off // stride, off % stride
                    fids = ["BATTLE.grid"] if rec is None else fields_over(rows, rec, off, width)
                    hit = dict(fields=fids, record=None if indexed else idx, width=width, table=name)
                    if name == "merc":
                        hit["merc_part"] = "template_or_live" if indexed else (
                            "live" if idx >= MERC_LIVE else "template")
                    break
            if not hit:
                continue
            named = True
            kind = "escape" if form[0] == "escape" else kind_of(line, form[3], lm.start())
            if kind == "escape":
                hit["escape"] = "seed" if re.match(r"\s*\w+\s*=\s*(?:\([^()]*\)\s*)*\(?\s*(?:\(int\)\s*)?&", line) else "arg"
            hits.append(dict(function=func[0], address="0x" + func[1], line=n, kind=kind, form=form[0], **hit))
        if not named:
            for st, tbl in STRIDES.items():
                if re.search(r"\*\s*%s\b" % (hex(st) if st > 9 else st), line) and not LIT.search(line):
                    frontier[(func[0], "0x" + func[1], tbl)] += 1
                    break
    return hits, frontier


def variable_terms(form):
    """True when the access expression has a non-constant term (an index)."""
    if form[0] == "idx":
        return True
    if form[0] == "cast":
        return form[4] or form[5]
    return False


def pick_tables(a, form):
    """Tables that can hold address a, best first.

    A label within one stride below a table's base is that table's record -1
    only when the expression is indexed (`F - 1` style); a constant label there
    is the previous table's (or a standalone global). An index multiplier m
    selects the table whose stride is m, 2m or 4m.
    """
    inside = [t for t in TABLES if t[1] <= a < t[1] + t[2] * t[3]]
    below = [t for t in TABLES if t[1] - t[2] <= a < t[1]] if variable_terms(form) else []
    cands = below + inside
    mults = form[2] if form[0] == "idx" else form[6] if form[0] == "cast" else []
    for m in mults:
        fit = [t for t in cands if m and t[2] in (m, 2 * m, 4 * m)]
        if fit:
            return fit[:1]
    return cands[:1]


def escape_frontier(hits):
    """Per table: functions taking a record address into a pointer (seed) or passing it on (arg)."""
    out = defaultdict(lambda: {"seed": set(), "arg": set()})
    for h in hits:
        if h["kind"] == "escape":
            out[h.get("table", "scalar")][h["escape"]].add(f"{h['function']}@{h['address']}")
    return {t: {k: sorted(v) for k, v in d.items()} for t, d in sorted(out.items())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    raw = a.source.read_bytes()
    rows = cov.load_map()
    hits, frontier = scan(raw.decode("latin1").splitlines(), rows)
    per = defaultdict(lambda: {"read": set(), "write": set(), "escape": set(), "n": defaultdict(int)})
    for h in hits:
        for fid in h["fields"]:
            p = per[fid]
            p[h["kind"]].add(f"{h['function']}@{h['address']}")
            p["n"][h["kind"]] += 1
    index = a.out_dir / f"access-index-{a.tag}.csv"
    with open(index, "x", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["field_id", "record", "semantic", "n_write", "n_read", "n_escape", "writers", "readers", "escapes"])
        for r in rows:
            if r["type"].startswith("rec:"):
                continue
            p = per.get(r["field_id"])
            n = p["n"] if p else {}
            w.writerow([r["field_id"], r["record"], r["semantic"], n.get("write", 0), n.get("read", 0),
                        n.get("escape", 0)] + [";".join(sorted(p[k])) if p else "" for k in ("write", "read", "escape")])
    refs = a.out_dir / f"access-refs-{a.tag}.jsonl"
    with open(refs, "x") as fh:
        for h in hits:
            fh.write(json.dumps(h) + "\n")
    summary = {"source_sha256": hashlib.sha256(raw).hexdigest(),
               "field_map_sha256": hashlib.sha256(cov.FIELD_MAP.read_bytes()).hexdigest(),
               "method": "literal-address resolution (offset mod stride + scaled bracket constant); "
                         "not alias, escape or indirect-call closure",
               "hits": len(hits), "by_kind": {k: sum(h["kind"] == k for h in hits) for k in ("write", "read", "escape")},
               "unresolved_offsets": sum(None in h["fields"] for h in hits),
               "multi_field_hits": sum(len(h["fields"]) > 1 for h in hits),
               "fields_without_literal_access": [r["field_id"] for r in rows
                                                 if not r["type"].startswith("rec:") and r["field_id"] not in per],
               "escape_frontier": escape_frontier(hits),
               "pointer_frontier": [dict(function=f, address=ad, table=t, lines=c)
                                    for (f, ad, t), c in sorted(frontier.items())]}
    with open(a.out_dir / f"access-summary-{a.tag}.json", "x") as fh:
        json.dump(summary, fh, indent=1); fh.write("\n")
    print(json.dumps({k: summary[k] for k in ("hits", "by_kind", "unresolved_offsets")}))
    print("fields without literal access:", len(summary["fields_without_literal_access"]),
          "pointer-frontier functions:", len(summary["pointer_frontier"]))


if __name__ == "__main__":
    sys.exit(main())
