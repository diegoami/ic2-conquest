"""Check 4, staged (L1, labelled synthetic): `saves/fleets-adjacent-at-sea-0723.SAV` (two human seats, Carthage and Ptolemaic, at war; their fleets
adjacent at sea; Ptolemaic to move) with ONE edit: Carthage's human flag (nation +0x490) set to 0, so Carthage plays as a computer seat. The human
Ptolemaic ends its turn without acting; Carthage (seat 13) then runs its AI turn, fleet phase included. The AI-decision hook build (v2) logs the
fleet decisions. One fresh process per seed; the autosave of Ptolemaic's next turn is kept.
python3 staged_hunt.py SEED [SEED ...]   -> staged_hunt.jsonl here (appended), saves in artifacts/run-exp-ai-intercept-hunt/"""
import hashlib, json, shutil, struct, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "patches")); sys.path.insert(0, str(R / "runs/experiments/battles"))
import ai_hook as A, stage
from harness.driver import G, Game
from state import sav
ART = R / "artifacts/run-exp-ai-intercept-hunt"; ART.mkdir(parents=True, exist_ok=True)
DATA = R / "runs/experiments/data/run-exp-ai-intercept-hunt"
SRC = R / "saves/fleets-adjacent-at-sea-0723.SAV"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
b = bytearray(SRC.read_bytes())
o = stage._nation(b, 1) + 0x490
assert b[o] == 1, "Carthage is not human in the fixture"
b[o] = 0
start = ART / "staged_hunt_start_carthage_ai.SAV"
if not start.exists():
    start.write_bytes(bytes(b))
    with (DATA / "SAVES.sha256").open("a") as f: f.write(f"{sha(start)}  {start.name}\n")
assert sha(start) == hashlib.sha256(bytes(b)).hexdigest()
s0 = sav.load(str(start))
assert not s0["nations"][1]["human"] and s0["nations"][3]["human"] and s0["current_nation"] == 3
for seed in map(int, sys.argv[1:]):
    g = Game(exe=A.DST)
    g.load(start, seed=seed)
    magic = struct.unpack("<I", g.mem(A.CTL + 4, 4))[0]
    n0 = struct.unpack("<I", g.mem(A.CTL, 4))[0]
    name, texts = g.end_turn(timeout=400)
    n = struct.unpack("<I", g.mem(A.CTL, 4))[0]
    recs = A.decode(g.mem(A.BUF + A.REC * n0, A.REC * (n - n0)), n - n0)
    dst = ART / f"staged_hunt_s{seed}_{name}"
    if not dst.exists():
        shutil.copy2(G / name, dst)
        with (DATA / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    rec = {"seed": seed, "exe": A.DST, "exe_sha256": sha(G / A.DST), "magic": hex(magic), "start": start.name, "start_sha256": sha(start),
           "source": SRC.name, "source_sha256": sha(SRC), "edit": "Carthage (1) nation +0x490 human flag 1 -> 0", "seed_line": g.seed_line,
           "autosave": name, "copy": dst.name, "sha256": sha(dst), "texts": texts, "records": recs, "t": time.strftime("%Y-%m-%d %H:%M:%S")}
    with (DATA / "staged_hunt.jsonl").open("a") as f: f.write(json.dumps(rec) + "\n")
    print(seed, name, [(r["site"], r["nation"], r.get("hunt_score"), r.get("hunt_fleet")) for r in recs if r["site"].startswith("fleet")], texts[:3], flush=True)
    g.kill()
