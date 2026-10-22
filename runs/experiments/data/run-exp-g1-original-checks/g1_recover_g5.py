#!/usr/bin/env python3
"""Review fix R2 (round 3): recover the one G5 autosave still in the game folder. `AUTO0720.SAV` (mtime 06:55:46) was written by the G5 patched
run g1_checks-G5-20261012-065502.jsonl (06:55:02-06:55:59; its autosave_log_tail shows the new-game line). Copies (never moves, never overwrites)
it under a G5/stamp name, hashes it (SAVES.sha256) and writes recovered-g5-<stamp>.jsonl with the evidence of origin. The autosaves of the G5
runs -233302, -065259 and -065348 were overwritten by later New Game starts and are not recoverable (logged); the replacement trial is a new G5 run."""
import hashlib, json, time
from pathlib import Path


def reserve(path, mode="xb"):
    """Open `path` for exclusive creation; on a collision allocate `<stem>.v<N><ext>` (round 4 R2). Never replaces: 'x' fails atomically if the
    name exists, so there is no exists()-then-write race. Returns (file object, the path used)."""
    path = Path(path); n = 1; cand = path
    while True:
        try:
            return open(cand, mode), cand
        except FileExistsError:
            n += 1; cand = path.with_name(f"{path.stem}.v{n}{path.suffix}")


def copy_exclusive(src, dst):
    """Copy src's bytes to a newly reserved name next to `dst`; returns the path used."""
    data = Path(src).read_bytes()
    f, used = reserve(dst, "xb")
    with f: f.write(data)
    return used


def recover(G, ART, D, stamp):
    ART.mkdir(parents=True, exist_ok=True)
    src = G / "AUTO0720.SAV"
    dst = copy_exclusive(src, ART / "G5_20261012-065502_recovered_AUTO0720.SAV"); h = hashlib.sha256(dst.read_bytes()).hexdigest()
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{h}  {dst.name}\n")
    rec = [{"autosave": "AUTO0720.SAV", "kept_as": dst.name, "sha256": h, "size": dst.stat().st_size,
            "game_folder_mtime": time.strftime("%H:%M:%S", time.localtime(src.stat().st_mtime)), "log": "g1_checks-G5-20261012-065502.jsonl", "log_window": "06:55:02-06:55:59"},
           {"not_recoverable": "G5 autosaves of g1_checks-G5-20261011-233302, -20261012-065259 and -20261012-065348 (patched runs): overwritten by the next New Game start; the original-exe run -233412 writes no autosave. Replacement trial: a new `G5 patched` run keeps its autosave."}]
    lf, log = reserve(D / f"recovered-g5-{stamp}.jsonl", "x")
    with lf: lf.write("\n".join(json.dumps(r) for r in rec) + "\n")
    return rec, dst, log


if __name__ == "__main__":
    D = Path(__file__).resolve().parent; R = D.parents[3]
    rec, dst, log = recover(Path.home() / "ic2-work/prefix/drive_c/IC2", R / "artifacts/run-exp-g1-original-checks", D, time.strftime("%Y%m%d-%H%M%S"))
    print(*rec, sep="\n")
