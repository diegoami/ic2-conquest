"""AI checks 3 and 4 (research report 2026-10-07-strategic-ai-turn.md §3.1, §4) in natural play: from `saves/run0-start-AUTO0720-seed12345.SAV`
(Rome human, nothing edited) the human only ends turns. VARIANT `hook` runs the AI-decision hook build (patches/ai_hook.py) and, after every End
turn, reads the new hook records from game memory; VARIANT `plain` runs the unhooked seed exe (the inertness control: same seed, same clicks, the
autosaves must be byte-identical). Every autosave is copied to artifacts/run-exp-ai-intercept-hunt/<variant>_s<seed>_<name> (never overwritten),
hashed into SAVES.sha256, and one JSON line per End turn is appended to <variant>_s<seed>.jsonl here (resumable: nothing is rewritten).
python3 watch.py hook|plain SEED MAX_END_TURNS"""
import hashlib, json, shutil, struct, sys, time
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest")
sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "patches"))
import ai_hook as A
from harness.driver import G, Game, GameOver
START = R / "saves/run0-start-AUTO0720-seed12345.SAV"
ART = R / "artifacts/run-exp-ai-intercept-hunt"; ART.mkdir(parents=True, exist_ok=True)
DATA = R / "runs/experiments/data/run-exp-ai-intercept-hunt"
variant, seed, max_ends = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
EXE = {"hook": A.DST, "plain": A.SRC}[variant]
LOG = DATA / f"{variant}_s{seed}.jsonl"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(rec):
    rec["t"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a") as f: f.write(json.dumps(rec) + "\n")
g = Game(exe=EXE)
g.load(START, seed=seed)
n_seen = 0
if variant == "hook":
    magic, cap = struct.unpack("<II", g.mem(A.CTL + 4, 8))
    if magic != A.MAGIC: raise SystemExit("hook magic not found: %#x" % magic)
    n_seen = struct.unpack("<I", g.mem(A.CTL, 4))[0]
write({"event": "start", "variant": variant, "exe": EXE, "seed": seed, "start": START.name, "start_sha256": sha(START),
       "seed_line": g.seed_line, "hook_records_at_start": n_seen})
for i in range(1, max_ends + 1):
    t0 = time.time()
    try:
        name, texts = g.end_turn(timeout=400)
    except GameOver as e:
        write({"event": "game_over", "end": i, "text": e.text}); break
    dst = ART / f"{variant}_s{seed}_{name}"
    if not dst.exists():
        shutil.copy2(G / name, dst)
        with (DATA / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    rec = {"event": "end_turn", "end": i, "autosave": name, "copy": dst.name, "sha256": sha(dst), "seconds": round(time.time() - t0, 1), "texts": texts}
    if variant == "hook":
        n = struct.unpack("<I", g.mem(A.CTL, 4))[0]
        recs = A.decode(g.mem(A.BUF + A.REC * n_seen, A.REC * (n - n_seen)), n - n_seen) if n > n_seen else []
        for r in recs: r["i"] += n_seen
        rec.update(hook_count=n, records=recs); n_seen = n
        rec["by_site"] = {s: sum(r["site"] == s for r in recs) for s, *_ in A.SITES}
    write(rec)
    print(i, name, rec.get("by_site"), flush=True)
g.kill()
write({"event": "done"})
