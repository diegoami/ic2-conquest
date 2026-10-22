#!/usr/bin/env python3
"""Check an exported (candidate) SAV against the research #37 gate-2 policy (conquest #99, #107).

    python3 scripts/sav_export_policy_check.py CANDIDATE.SAV [--source ORIGINAL.SAV] --out RECEIPT.json

The policy is findings/2026-10-22-sav-export-gate2-policy.md. The checker runs:
- every cross-record invariant of sav_atlas_invariants.check, failing on any violation except the two
  documented drifts the original itself produces (a stale army marker band, the stale cities count of an
  eliminated nation);
- the policy rules below, each failing closed with its reason.
It reads only the candidate (and the optional source) and writes counts, indices and reasons, never bytes.
The output file is created exclusively (CLAUDE.md rule 6).
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sav_atlas_coverage as cov  # noqa: E402
import sav_atlas_invariants as inv  # noqa: E402

ALLOWED_DRIFT = {"army_marker_band_current", "city_count_eliminated"}
INERT = [(0x450, 0x46A), (0x46D, 0x46D), (0x491, 0x493)]
TEXT = {"city": [(0, 14)], "nation": [(0x00, 11), (0x0B, 27)], "army_slot": [(8, 24)], "news_slot": [(0, 61)]}


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def tail_dirty(b, off, n):
    """True when a NUL-terminated buffer has non-zero bytes after its terminator (or has no terminator)."""
    buf = b[off:off + n]
    k = buf.find(b"\0")
    return k < 0 or any(buf[k:])


def policy(b, src=None):
    """[(rule, ok, detail)] for the candidate b (and the source SAV src, when the export has one)."""
    blocks, facts = cov.frame(b)
    pos = {r: o for r, o, _ in blocks}
    out = []

    def rule(name, ok, detail=None, required=True):
        out.append((name, bool(ok), detail, required))

    rule("no_battle_block", not facts["battle_flag"], "an open tactical battle is outside the supported state")
    A, F = facts["armies"], facts["fleets"]
    rule("no_army_tombstones", facts["army_tombstones"] == 0, facts["army_tombstones"])
    rule("no_fleet_tombstones", facts["fleet_tombstones"] == 0, facts["fleet_tombstones"])
    # INERT bytes: carried from the source when there is one, else zero (the program's own initial value)
    n0 = pos["nation"]
    s_n0 = {r: o for r, o, _ in cov.frame(src)[0]}["nation"] if src else None
    bad = []
    for n in range(16):
        for lo, hi in INERT:
            cur = b[n0 + 1172 * n + lo: n0 + 1172 * n + hi + 1]
            want = src[s_n0 + 1172 * n + lo: s_n0 + 1172 * n + hi + 1] if src else bytes(hi - lo + 1)
            if cur != want:
                bad.append([n, hex(lo)])
    rule("inert_bytes_carried_or_zero", not bad, bad[:8])
    # fleets under construction, from scratch: moves 0 (a leftover is observable at launch), route x -1
    bf = []
    for j in range(F):
        o = pos["fleet"] + 26 * j
        if i16(b, o + 8) >= 0 and i16(b, o + 10) >= 0 and (i16(b, o + 12) != 0 or i16(b, o + 4) != -1):
            bf.append(j)
    # (the original writes such leftovers itself, increment 6, so with a source they are reported only)
    rule("building_fleet_moves_0_route_x_minus1", not bf, bf[:8], required=src is None)
    # carrier: an aboard army stands on its fleet's tile
    cb = []
    for j in range(F):
        o = pos["fleet"] + 26 * j
        a = i16(b, o + 22)
        if i16(b, o + 8) >= 0 and 0 <= a < A:
            ao = pos["army"] + 656 * a
            if (i16(b, ao), i16(b, ao + 2)) != (i16(b, o), i16(b, o + 2)):
                cb.append(j)
    rule("carried_army_on_fleet_tile", not cb, cb[:8])
    # canonical text: nothing after the NUL (tails are never read; zero is the canonical form)
    dirty = []
    for c in range(334):
        if tail_dirty(b, pos["city"] + 34 * c, 14):
            dirty.append(["city", c])
    for n in range(16):
        for off, ln in TEXT["nation"]:
            if tail_dirty(b, n0 + 1172 * n + off, ln):
                dirty.append(["nation", n, off])
    for k in range(A):
        for s in range(20):
            so = pos["army"] + 656 * k + 16 + 32 * s
            if i16(b, so + 4) > 0 and tail_dirty(b, so + 8, 24):
                dirty.append(["slot", k, s])
    # canonical-form rules bind a from-scratch export only: with a source, residue carried from it is allowed
    # (the original itself writes and reads it back unchanged), so they are then reported, not required
    rule("text_tails_canonical", not dirty, {"count": len(dirty), "first": dirty[:8]}, required=src is None)
    # empty unit slots: canonical zero (their bytes are never read)
    es = [[k, s] for k in range(A) for s in range(20)
          if i16(b, pos["army"] + 656 * k + 16 + 32 * s + 4) <= 0
          and any(b[pos["army"] + 656 * k + 16 + 32 * s: pos["army"] + 656 * k + 48 + 32 * s])]
    rule("empty_slots_zero", not es, {"count": len(es), "first": es[:8]}, required=src is None)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--source", type=Path, help="the original SAV the export came from, if any")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    b = a.candidate.read_bytes()
    src = a.source.read_bytes() if a.source else None
    invariants = {k: dict(checked=n, violations=len(v), first=v[:5]) for k, (n, v) in inv.check(b).items()}
    hard = {k: v for k, v in invariants.items() if v["violations"] and k not in ALLOWED_DRIFT}
    rules = [dict(rule=r, ok=ok, required=req, detail=d) for r, ok, d, req in policy(b, src)]
    out = dict(candidate=a.candidate.name, sha256=hashlib.sha256(b).hexdigest(),
               source_sha256=hashlib.sha256(src).hexdigest() if src else None,
               policy="findings/2026-10-22-sav-export-gate2-policy.md",
               accepted=not hard and all(r["ok"] for r in rules if r["required"]),
               invariant_failures=sorted(hard), invariants=invariants, rules=rules)
    with open(a.out, "x") as fh:
        json.dump(out, fh, indent=1, default=str); fh.write("\n")
    print(json.dumps({"accepted": out["accepted"], "invariant_failures": out["invariant_failures"],
                      "failed_rules": [r["rule"] for r in rules if not r["ok"] and r["required"]],
                      "reported_only": [r["rule"] for r in rules if not r["ok"] and not r["required"]]}))
    return 0 if out["accepted"] else 1


if __name__ == "__main__":
    sys.exit(main())
