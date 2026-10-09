"""Natural AI conquest of a nation whose launched fleet carries an army (ic2-research request for the player, 2026-10-09).
Nothing edited: from `saves/run0-start-AUTO0720-seed12345.SAV` (Rome human), the human only ends turns; every autosave is read for
(a) launched fleets with an army aboard (+22 >= 0, +10 == -1): owner, carried army, its owner, tile word;
(b) new news lines "X conquers Y." / "defects" eliminations.
Autosaves are kept when a loaded fleet exists or a conquest line is new (and the one before a conquest). One JSON line per turn is
appended to idle_watch_seed<k>.jsonl in the tracked data folder (resumable runs append; nothing is rewritten).
python3 idle_watch.py SEED MAX_END_TURNS"""
import json, shutil, struct, sys, time
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest")
sys.path.insert(0, str(R))
from harness.driver import G, Game
from state import sav
START = R / "saves/run0-start-AUTO0720-seed12345.SAV"
ART = R / "artifacts/run-exp-ai-conquest-aboard"
DATA = R / "runs/experiments/data/run-exp-ai-conquest-aboard"
seed, max_ends = int(sys.argv[1]), int(sys.argv[2])
word = lambda b, x, y: struct.unpack_from("<h", b, x * 280 + y * 2)[0]

def scan(path):
    b = path.read_bytes(); s = sav.load(str(path))
    arm = {a["id"]: a for a in s["armies"]}
    loaded = [{"fleet": f["id"], "owner": f["owner"], "x": f["x"], "y": f["y"], "ships": f["ships"], "army": f["army"],
               "army_owner": arm.get(f["army"], {}).get("owner"), "army_troops": arm.get(f["army"], {}).get("troops"),
               "word": word(b, f["x"], f["y"])}
              for f in s["fleets"] if f["army"] >= 0 and not f["building"]]
    cities = {}
    for c in s["cities"]:
        cities[c["owner"]] = cities.get(c["owner"], 0) + 1
    return s, loaded, cities

g = Game()
log = DATA / f"idle_watch_seed{seed}.jsonl"
seen_news = set(); prev = None
try:
    g.load(START, seed=seed)
    s0, l0, c0 = scan(START)
    seen_news = {n for n in s0["news"] if "conquers" in n}
    for i in range(max_ends):
        t0 = time.time()
        try:
            name, texts = g.end_turn(timeout=400)
        except Exception as e:          # record what blocks the turn, then stop this seed
            wins = g.find_windows(".", tooltips=True)
            g.shot(ART / f"STUCK_seed{seed}_{i + 1:03d}.png")
            with log.open("a") as fh:
                fh.write(json.dumps({"seed": seed, "end": i + 1, "error": repr(e), "windows": wins}, default=str) + "\n")
            print("STUCK", seed, i + 1, repr(e), wins, flush=True)
            raise
        p = G / name
        s, loaded, cities = scan(p)
        conq = [n for n in s["news"] if "conquers" in n and n not in seen_news]
        seen_news |= set(conq)
        keep = bool(loaded or conq)
        tag = f"seed{seed}_{i + 1:03d}_{s['turn']:04d}"
        last = ART / f"_last_seed{seed}.SAV"
        if keep:
            shutil.copy(p, ART / f"IW_{tag}.SAV")
            if conq and prev is not None and last.exists() and not (ART / f"IW_{prev}.SAV").exists():
                shutil.copy(last, ART / f"IW_{prev}.SAV")       # the autosave before the conquest
        shutil.copy(p, last)
        prev = tag
        rec = {"seed": seed, "end": i + 1, "turn": s["turn"], "secs": round(time.time() - t0, 1), "loaded_fleets": loaded,
               "new_conquests": conq, "cities": cities, "kept": keep, "popups": texts}
        with log.open("a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        print(i + 1, s["turn"], rec["secs"], loaded, conq, flush=True)
        if 0 not in cities:
            break
finally:
    g.kill()
