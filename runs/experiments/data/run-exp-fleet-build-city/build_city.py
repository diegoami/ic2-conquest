"""Original-side check of the v0.5.0 gap analysis (rows_g1 NEW-g1-3, rows_g2 check 8): at which city does the original build a fleet
ordered through Build fleet, by what rule, and does a city with a fleet under construction count as free?
Start: saves/run0-start-AUTO0720-seed12345.SAV (Rome human, treasury 2,200), seed 12345, the seed exe. Build fleet (10 ships) is ordered
again and again in the same turn (Game.build_fleet: OK, then Cancel), recording the box text ("The fleet will be built at <city>") and,
from game memory after each order, the new fleet record's build-city index (+20 while under construction) and the treasury, until a
refusal box or 25 orders. File > Save As after the first order and at the end. Then, for comparison, every Rome city with its
Chebyshev distance to the capital and whether a water tile touches it (3x3), from the start save's map.
Saves to artifacts/run-exp-fleet-build-city/ (SHA-256 in SAVES.sha256); log build_city-<stamp>.jsonl (tracked). python3 build_city.py"""
import hashlib, json, shutil, struct, sys, time
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest"); sys.path.insert(0, str(R))
import harness.driver as drv
from harness.driver import Game, G
from state import sav
START = R / "saves/run0-start-AUTO0720-seed12345.SAV"
ART = R / "artifacts/run-exp-fleet-build-city"; ART.mkdir(parents=True, exist_ok=True)
D = R / "runs/experiments/data/run-exp-fleet-build-city"
STAMP = time.strftime("%Y%m%d-%H%M%S"); LOG = D / f"build_city-{STAMP}.jsonl"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def log(step, **kw):
    kw.update(step=step, t=time.strftime("%H:%M:%S")); print(kw, flush=True)
    with LOG.open("a") as f: f.write(json.dumps(kw, default=str) + "\n")
def keep(src, name):
    dst = ART / f"{STAMP}_{name}"; shutil.copy2(src, dst)
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    return dst.name
s0 = sav.load(str(START))
cities = s0["cities"]
cap = cities[s0["nations"][0]["capital"]]
def water_adjacent(c):
    return any(sav.terrain_name(sav.cell(s0, c["x"] + dx, c["y"] + dy)).lower().startswith(("sea", "water", "ocean", "lake"))
               for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy))
table = sorted(({"city": i, "name": c["name"], "xy": (c["x"], c["y"]), "dist_capital": max(abs(c["x"] - cap["x"]), abs(c["y"] - cap["y"])),
                 "water_adjacent": water_adjacent(c)} for i, c in enumerate(cities) if c["owner"] == 0), key=lambda r: r["dist_capital"])
log("rome_cities", capital=cap["name"], table=table)
g = Game(); g.load(START, seed=12345)
nf0 = None
def fleets():
    """Fleet count and records from memory: the fleet table at 0x49C26C, count at 0x4A0326."""
    n = g.i16(0x4A0326)
    return n, [struct.unpack("<13h", g.mem(0x49C26C + 26 * i, 26)) for i in range(n)]
n0, _ = fleets(); log("start", fleets=n0, treasury=g.nation_state(0)["treasury"])
for k in range(1, 26):
    try:
        texts = g.build_fleet(10)
    except Exception as e:
        shot = ART / f"{STAMP}_timeout_order{k}.png"; g.shot(shot)
        log("order_error", k=k, error=repr(e), windows=g.find_windows(".", tooltips=True), shot=shot.name, shot_sha256=sha(shot))
        break
    n, recs = fleets()
    new = recs[n0:]
    log("order", k=k, texts=texts, notices=getattr(g, "build_fleet_notices", []), fleets=n, new_fleet=new[-1] if n > n0 else None,
        build_city=(cities[new[-1][10]]["name"] if n > n0 and 0 <= new[-1][10] < len(cities) else None),
        treasury=g.nation_state(0)["treasury"])
    if k == 1: log("saved", file=keep(g.save_as("FB_after_1.SAV"), "FB_after_1.SAV"))
    if n == n0:
        break
    n0 = n
log("saved", file=keep(g.save_as("FB_end.SAV"), "FB_end.SAV"))
g.kill(); log("done")
