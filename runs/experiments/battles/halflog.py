"""The per-half-round log of a trial (battles plan B2/B4): every file of the trial's BATTLEnn series decoded by `state/battle_block.py`.

One line per half-round file in `halfrounds-<trial>.jsonl` (tracked data folder): the header, every ALIVE slot (side, type, x, y, troops,
quality, morale, state, ammo, target, name) and the diff against the previous file: moves, losses with the inferred kind / actor
(**[D]**: `unknown` whenever the diff does not fix them uniquely, see `BB.diff`) and who seems to have acted. The position, troops, quality
and morale columns are exact (read from the block); the action columns are inferred.

    python3 runs/experiments/battles/halflog.py TRIAL...      # regenerate for recorded trials (a new file beside an old one, never overwritten)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from state import battle_block as BB  # noqa: E402

KEEP = ("slot", "side", "type", "x", "y", "troops", "quality", "morale", "state", "ammo", "target", "name", "merc")


def acting_sides(d, a, b):
    """Which side(s) acted between two files [D]: a side whose unit moved, shot (ammo fell) or acquired a target."""
    out = set()
    for k, row in d["slots"].items():
        if "move" in row or "d_ammo" in row or ("d_target" in row and row["d_target"][1] != -1):
            out.add(row["side"])
    return sorted(out)


def decode_series(paths):
    blocks = [BB.from_save(p) for p in paths]
    rows, prev = [], None
    for p, b in zip(paths, blocks):
        row = {"file": Path(p).name, "half_round": b["half_round"], "x2": b["x2"], "y1": b["y1"], "attacker_army": b["attacker_army"],
               "defender_army": b["defender_army"], "slots": [{k: s[k] for k in KEEP} for s in b["slots"] if s["alive"]],
               "grid_problems": len(BB.check_grid(b))}
        if prev is not None:
            d = BB.diff(prev, b)
            row["since_previous"] = {"acting_sides_D": acting_sides(d, prev, b), "slots": d["slots"], "losses": d["losses"],
                                     "unambiguous": d["unambiguous"], "ambiguous": d["ambiguous"]}
        rows.append(row)
        prev = b
    return rows


def write_halflog(trial_id, series_names, art=None, out=None):
    """Decode a series (names in the artifacts folder) and write halfrounds-<trial>[-<stamp>].jsonl; returns (path, summary)."""
    art = art or C.ART
    rows = decode_series([art / n for n in series_names])
    out = out or C.DATA
    out.mkdir(parents=True, exist_ok=True)
    p = C.write_new(out, f"halfrounds-{trial_id}.jsonl", "".join(json.dumps(r, default=str) + "\n" for r in rows))
    loss = sum(r.get("since_previous", {}).get("losses", 0) for r in rows)
    amb = sum(r.get("since_previous", {}).get("ambiguous", 0) for r in rows)
    unamb = sum(r.get("since_previous", {}).get("unambiguous", 0) for r in rows)
    first = rows[0]["slots"] if rows else []
    return p, {"files": len(rows), "loss_rows": loss, "unambiguous_rows": unamb, "ambiguous_rows": amb,
               "grid_problems": sum(r["grid_problems"] for r in rows),
               "first_file_positions": {s["slot"]: (s["x"], s["y"]) for s in first}}


if __name__ == "__main__":
    import trials as T
    recs = {r["trial"]: r for r in T.read_trials() if r.get("status") == "ok"}
    for t in sys.argv[1:]:
        p, s = write_halflog(t, recs[t]["series"])
        print(p, s)
