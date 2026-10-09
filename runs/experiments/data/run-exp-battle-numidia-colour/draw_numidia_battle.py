"""Wine, lab build s1: Rome's army 0 attacks army 10 after an L1 edit gives army 10 to Numidia (owner 5) and sets the Rome-Numidia relation
to the Rome-Gaul value (3). Labelled synthetic: positions untouched, units natural (Gaul's five LI/HI units). At the placement phase and
after one proven End turn: a window screenshot, File > Save As, and the live battle block. Then the battle is left (process killed).
Outputs: artifacts/run-exp-battle-numidia-colour/ (saves, screenshots; never overwritten), log draw-<stamp>.jsonl here (tracked).
python3 draw_numidia_battle.py"""
import hashlib, json, shutil, sys, time
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest"); sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "runs/experiments/battles"))
import common as C, stage, trials as T
from harness.driver import Game
from state import battle_block as BB
STAMP = time.strftime("%Y%m%d-%H%M%S")
ART = R / "artifacts/run-exp-battle-numidia-colour"; ART.mkdir(parents=True, exist_ok=True)
LOG = R / f"runs/experiments/data/run-exp-battle-numidia-colour/draw-{STAMP}.jsonl"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def log(ev, **kw):
    kw.update(event=ev, t=time.strftime("%H:%M:%S")); print({k: v for k, v in kw.items() if k != "block"})
    with LOG.open("a") as f: f.write(json.dumps(kw, default=str) + "\n")
def keep(src, name):
    dst = ART / f"{STAMP}_{name}"; assert not dst.exists(); shutil.copy2(src, dst); return dst
OPS = [("owner", C.GAUL_ARMY, 5), ("relation", 0, 5, 3)]
start = ART / f"{STAMP}_NUM_start.SAV"
stage.edit(R / "artifacts/run-exp-battle-sweep" / C.FLD_RG_NAME, start, OPS)
log("staged", ops=OPS, start=start.name, sha256=sha(start), src_sha256=sha(R / "artifacts/run-exp-battle-sweep" / C.FLD_RG_NAME))
g = Game(exe=C.LAB_EXE % 1)
try:
    for f in C.D.G.glob("BATTLE*.SAV"):
        keep(f, "stray_" + f.name); f.unlink()
    g.start(); boxes = g.open(start)
    a0, a10 = g.army_state(C.ROME_ARMY), g.army_state(C.GAUL_ARMY)
    log("loaded", boxes=boxes, army0=(a0["owner"], a0["x"], a0["y"], a0["moves"]), army10=(a10["owner"], a10["x"], a10["y"]))
    if a10["owner"] != 5: raise SystemExit("army 10 owner read back %s, not 5" % a10["owner"])
    g.select_army(C.ROME_ARMY, *C.STAGE_TILE); g.click_tile(*C.GAUL_TILE, pause=0.0)
    T.wait_battle(g, log); time.sleep(2)
    win = g.find_windows(" v ")[0]; log("battle_open", title=win[1], geom=win[2:])
    for phase in ("placement", "after_end_turn_1"):
        if phase != "placement":
            C.battle_end_turn(g, win[0]); time.sleep(2)
        png = ART / f"{STAMP}_NUM_{phase}_window.png"; g.shot(png, window=str(win[0]))
        st = g.battle_state()
        sv = keep(g.save_as(f"NUM_{phase}.SAV"), f"NUM_{phase}.SAV")
        log("phase", phase=phase, screenshot=png.name, shot_sha256=sha(png), save=sv.name, save_sha256=sha(sv),
            attacker_army=st["attacker_army"], defender_army=st["defender_army"], half_round=st["half_round"],
            occupied=[(s["slot"], s["side"], s["type"], s["x"], s["y"], s["troops"]) for s in st["slots"] if s["alive"]])
    for f in C.D.G.glob("BATTLE*.SAV"):
        keep(f, f.name); f.unlink()
finally:
    C.kill_stale(g); log("done")
