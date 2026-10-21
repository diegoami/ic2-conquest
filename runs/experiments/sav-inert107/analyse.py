#!/usr/bin/env python3
"""Analyse run-exp-sav-inert107 saves; writes a JSON receipt (counts and offsets only).

    python3 runs/experiments/sav-inert107/analyse.py ART_DIR --out runs/experiments/data/run-exp-sav-inert107/<name>.json
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import sav_atlas_coverage as cov  # noqa: E402

INERT = [(0x450, 0x46A), (0x46D, 0x46D), (0x491, 0x493)]


def inert_offsets(b):
    n0 = {r: o for r, o, _ in cov.frame(b)[0]}["nation"]
    return {n0 + 1172 * n + o for n in range(16) for lo, hi in INERT for o in range(lo, hi + 1)}


def marker_ok(b):
    """Every INERT byte holds the craft.py marker."""
    n0 = {r: o for r, o, _ in cov.frame(b)[0]}["nation"]
    return all(b[n0 + 1172 * n + o] == ((0x80 if k == 0 else 0xC0) | n)
               for n in range(16) for k, (lo, hi) in enumerate(INERT) for o in range(lo, hi + 1))


def inert_zero(b):
    return not any(b[o] for o in inert_offsets(b))


def diff(a, b):
    """Offsets where two saves differ, split into INERT and other (same length required)."""
    if len(a) != len(b):
        return dict(same_length=False, len_a=len(a), len_b=len(b))
    ins = inert_offsets(a)
    d = [i for i in range(len(a)) if a[i] != b[i]]
    other = [i for i in d if i not in ins]
    return dict(same_length=True, differing=len(d), inside_inert=len(d) - len(other), outside_inert=len(other),
                outside_first=[hex(i) for i in other[:20]])


def fleets(b):
    blocks, facts = cov.frame(b)
    f0 = {r: o for r, o, _ in blocks}["fleet"]
    out = []
    for f in range(facts["fleets"]):
        x, y, rx, ry, owner = struct.unpack_from("<5h", b, f0 + 26 * f)
        out.append(dict(f=f, owner=owner, route_x=rx, route_y=ry))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("art", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    files = {p.name: p.read_bytes() for p in sorted(a.art.glob("*.SAV"))}
    r = dict(art=a.art.name, files={k: hashlib.sha256(v).hexdigest() for k, v in files.items()})
    inp = ROOT / "artifacts/run-exp-sav-inert107/inputs"
    if "T1B_marked_saveas.SAV" in files:
        A, B = files["T1A_plain_autosave_after_end_turn.SAV"], files["T1B_marked_autosave_after_end_turn.SAV"]
        start = (ROOT / "saves/run0-start-AUTO0720-seed12345.SAV").read_bytes()
        r["T1"] = dict(
            marked_saveas_markers_intact=marker_ok(files["T1B_marked_saveas.SAV"]),
            marked_saveas_vs_input=diff((inp / "T1M_0720_inert_marked.SAV").read_bytes(), files["T1B_marked_saveas.SAV"]),
            plain_saveas_inert_zero=inert_zero(files["T1A_plain_saveas.SAV"]),
            after_end_turn_markers_intact=marker_ok(B),
            after_end_turn_plain_vs_marked=diff(A, B),
            plain_after_end_turn_inert_zero=inert_zero(A))
        if "T1B_marked_new_game_autosave.SAV" in files:
            N = files["T1B_marked_new_game_autosave.SAV"]
            r["T1"].update(new_game_markers_intact=marker_ok(N), new_game_inert_zero=inert_zero(N),
                           new_game_vs_reference_start_save=diff(start, N))
    if "T2A_plain_saveas.SAV" in files:
        r["T2"] = {k: fleets(files[k]) for k in ("T2A_plain_saveas.SAV", "T2A_plain_autosave_after_end_turn.SAV",
                                                  "T2B_sentinel_saveas.SAV", "T2B_sentinel_autosave_after_end_turn.SAV")
                   if k in files}
        if "T2B_sentinel_autosave_after_end_turn.SAV" in files:
            r["T2"]["plain_vs_sentinel_after_end_turn"] = diff(files["T2A_plain_autosave_after_end_turn.SAV"],
                                                                files["T2B_sentinel_autosave_after_end_turn.SAV"])
    if "T3_original_saveas.SAV" in files:
        r["T3"] = dict(markers_intact=marker_ok(files["T3_original_saveas.SAV"]),
                       vs_input=diff((inp / "T1M_0720_inert_marked.SAV").read_bytes(), files["T3_original_saveas.SAV"]))
    with open(a.out, "x") as fh:
        json.dump(r, fh, indent=1); fh.write("\n")
    print(json.dumps({k: v for k, v in r.items() if k != "files"}, indent=1))


if __name__ == "__main__":
    main()
