#!/usr/bin/env python3
"""Review fix R1(c): recover the autosaves the first g1 runs left in the game folder and never kept. Copies (never moves, never overwrites)
the AUTO07xx.SAV files that the usable G10 run (g1_checks-G10-20261011-235901.jsonl, 23:59:01-00:00:05) wrote, under a case/stamp/turn name,
hashes them (SAVES.sha256) and writes recovered-<stamp>.jsonl with each file's mtime and the log's round time as the evidence of origin.
The autosaves of G2_depose (AUTO0721 x6) and of the two unusable G10 runs were overwritten by later runs: not recoverable (logged)."""
import hashlib, json, shutil, sys, time
from pathlib import Path
D = Path(__file__).resolve().parent; R = D.parents[3]
sys.path.insert(0, str(R))
G = Path.home() / "ic2-work/prefix/drive_c/IC2"; ART = R / "artifacts/run-exp-g1-original-checks"; ART.mkdir(parents=True, exist_ok=True)
stamp = time.strftime("%Y%m%d-%H%M%S"); out = D / f"recovered-{stamp}.jsonl"
rounds = {}
for ln in (D / "g1_checks-G10-20261011-235901.jsonl").read_text().splitlines():
    j = json.loads(ln)
    if j.get("step") == "after_round": rounds[j["autosave"]] = (j["round"], j["t"], j["calendar"])
rec = []
for name, (rnd, t, cal) in sorted(rounds.items()):
    src = G / name; dst = ART / f"G10_20261011-235901_recovered_{name}"
    if dst.exists(): raise SystemExit(f"{dst} exists")
    shutil.copy2(src, dst); h = hashlib.sha256(dst.read_bytes()).hexdigest()
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{h}  {dst.name}\n")
    mt = time.strftime("%H:%M:%S", time.localtime(src.stat().st_mtime))
    rec.append({"autosave": name, "kept_as": dst.name, "sha256": h, "size": dst.stat().st_size, "game_folder_mtime": mt, "log_round": rnd, "log_time": t, "log_calendar": cal})
    print(rec[-1])
rec.append({"not_recoverable": "G2_depose AUTO0721 (logs -234640 -234713 -234745 -234836 -234911 -234946) and G10 runs -235532, -235656: overwritten by later runs (the game folder holds only the last writer of each AUTO name)"})
out.write_text("\n".join(json.dumps(r) for r in rec) + "\n")
