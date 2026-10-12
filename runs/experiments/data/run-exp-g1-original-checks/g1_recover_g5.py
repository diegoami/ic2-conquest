#!/usr/bin/env python3
"""Review fix R2 (round 3): recover the one G5 autosave still in the game folder. `AUTO0720.SAV` (mtime 06:55:46) was written by the G5 patched
run g1_checks-G5-20261012-065502.jsonl (06:55:02-06:55:59; its autosave_log_tail shows the new-game line). Copies (never moves, never overwrites)
it under a G5/stamp name, hashes it (SAVES.sha256) and writes recovered-g5-<stamp>.jsonl with the evidence of origin. The autosaves of the G5
runs -233302, -065259 and -065348 were overwritten by later New Game starts and are not recoverable (logged); the replacement trial is a new G5 run."""
import hashlib, json, shutil, time
from pathlib import Path
D = Path(__file__).resolve().parent; R = D.parents[3]
G = Path.home() / "ic2-work/prefix/drive_c/IC2"; ART = R / "artifacts/run-exp-g1-original-checks"; ART.mkdir(parents=True, exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S"); out = D / f"recovered-g5-{stamp}.jsonl"
src = G / "AUTO0720.SAV"; dst = ART / "G5_20261012-065502_recovered_AUTO0720.SAV"
if dst.exists(): raise SystemExit(f"{dst} exists")
shutil.copy2(src, dst); h = hashlib.sha256(dst.read_bytes()).hexdigest()
with (D / "SAVES.sha256").open("a") as f: f.write(f"{h}  {dst.name}\n")
rec = [{"autosave": "AUTO0720.SAV", "kept_as": dst.name, "sha256": h, "size": dst.stat().st_size,
        "game_folder_mtime": time.strftime("%H:%M:%S", time.localtime(src.stat().st_mtime)), "log": "g1_checks-G5-20261012-065502.jsonl", "log_window": "06:55:02-06:55:59"},
       {"not_recoverable": "G5 autosaves of g1_checks-G5-20261011-233302, -20261012-065259 and -20261012-065348 (patched runs): overwritten by the next New Game start; the original-exe run -233412 writes no autosave. Replacement trial: a new `G5 patched` run keeps its autosave."}]
out.write_text("\n".join(json.dumps(r) for r in rec) + "\n"); print(*rec, sep="\n")
