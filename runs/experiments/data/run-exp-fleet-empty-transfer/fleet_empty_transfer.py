"""Fleet emptied by Transfer ships: does the receiving fleet get the giver's money and supplies? (ic2-research docs/pending-requests.md ef0d3e2)
One fresh process per case: python3 fleet_empty_transfer.py <Td0|Td1|Td2>. Fast rollingsave seed exe, seed 12345, Xvfb.
Start saves/fleet-split-antium-0734.SAV: fleet 2 at (101,46), fleet 5 at (101,47). Staging (L1, labelled): fleet records only (ships +18,
supplies +14, money +16); x and y are never edited. Only the ship arrows are touched in the dialog.
- Td0: fleet 5: 10 ships, supplies 37, money 123; fleet 2: 20 ships, supplies 50, money 400; fleet 5 gives 5 of 10 (partial, control).
- Td1: same values; fleet 5 gives all 10 (giver emptied and deleted).
- Td2: fleet 5: 10 ships, supplies 90, money 123; fleet 2: 5 ships, supplies 40, money 400; fleet 5 gives all 10 (room 15 x 8 = 120 < 130).
Text logs go straight to this tracked folder (rule 6); saves and screenshots to artifacts/run-exp-fleet-empty-transfer/, hashed in SAVES.sha256."""
import hashlib, json, shutil, struct, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "runs/experiments/battles"))
import harness.driver as drv
from harness.driver import Game, G, DriverError, ARMY_TOOLBAR_Y, sh
from state import sav
import stage

START = R / "saves/run0-start-AUTO0720-seed12345.SAV"
PORT = R / "saves/fleet-port-antium-0734.SAV"
SPLIT = R / "saves/fleet-split-antium-0734.SAV"
ART = R / "artifacts/run-exp-fleet-empty-transfer"; ART.mkdir(parents=True, exist_ok=True)
D = Path(__file__).resolve().parent
STAMP = time.strftime("%Y%m%d-%H%M%S"); CASE = sys.argv[1]
LOG = D / f"fleet_empty_transfer-{CASE}-{STAMP}.jsonl"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log(step, **kw):
    kw.update(step=step, t=time.strftime("%H:%M:%S")); print(json.dumps(kw, default=str), flush=True)
    with LOG.open("a") as f: f.write(json.dumps(kw, default=str) + "\n")


def keep(src, name):
    dst = ART / f"{CASE}_{STAMP}_{name}"
    if dst.exists(): raise SystemExit(f"{dst} exists: names must be unique")
    shutil.copy2(src, dst)
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    return dst.name


def save(g, name):
    return keep(g.save_as(name), name)


def shot(g, name, window="root"):
    p = ART / f"{CASE}_{STAMP}_{name}.png"; g.shot(p, window=window)
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(p)}  {p.name}\n")
    return p.name


def staged(src, ops, fleet_ops=()):
    """src with stage ops and ('fleet', f, field, v) ops; a new labelled file in ART, hashed."""
    b = bytearray(Path(src).read_bytes()); stage.apply(b, ops)
    f0 = stage._offsets(b)["army0"] + stage._offsets(b)["na"] * sav.ARMY_LEN + 2
    for f, field, v in fleet_ops:
        struct.pack_into("<h", b, f0 + f * sav.FLEET_LEN + {"ships": 18, "moves": 12, "supplies": 14, "money": 16}[field], v)
    dst = ART / f"{CASE}_{STAMP}_staged_{Path(src).stem}.SAV"; dst.write_bytes(bytes(b))
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    log("staged", src=Path(src).name, src_sha256=sha(src), dst=dst.name, ops=ops, fleet_ops=list(fleet_ops))
    return dst


def army(g, i):
    s = g.army_state(i); s["troops"] = sum(struct.unpack_from("<h", g.army_rec(i), 16 + 32 * k + 4)[0] for k in range(20)
                                            if struct.unpack_from("<h", g.army_rec(i), 16 + 32 * k + 4)[0] > 0)
    s["units"] = sum(1 for k in range(20) if struct.unpack_from("<h", g.army_rec(i), 16 + 32 * k + 4)[0] > 0)
    return s


def treasury(g):
    return g.nation_state(0)["treasury"]


def rome_armies(g):
    n = g.i16(0x4A0324)
    return {i: army(g, i) for i in range(n) if struct.unpack_from("<h", g.army_rec(i), 4)[0] == 0}


def rome_fleets(g):
    n = g.i16(0x4A0326)
    return {i: g.fleet_state(i) for i in range(n) if g.fleet_state(i)["owner"] == 0}


def walk(g, i, steps):
    for x, y in steps:
        pos, texts = g.move(i, x, y)
        log("army_step", army=i, to=(x, y), pos=pos, popups=texts, moves=g.army_state(i).get("moves"))
        if tuple(pos) != (x, y): raise DriverError(f"army {i} stopped at {pos}, not {(x, y)}")


def sail(g, i, steps):
    for x, y in steps:
        pos, texts = g.move_fleet(i, x, y)
        log("fleet_step", fleet=i, to=(x, y), pos=pos, popups=texts)
        if tuple(pos) != (x, y): raise DriverError(f"fleet {i} stopped at {pos}, not {(x, y)}")


def open_transfer_ships(g, i):
    g.select_fleet(i)
    if not g.fleet_x: g.calibrate_fleet_toolbar()
    x = g.fleet_x.get("transfer", drv.FLEET_TOOLS["transfer"])
    for _ in range(2):
        g.click(x, ARMY_TOOLBAR_Y, pause=0.5)
        t0 = time.time()
        while time.time() - t0 < 6:
            if g.find_windows("^Fleet to fleet transfer$") or g.popups(): break
            time.sleep(0.3)
        if g.find_windows("^Fleet to fleet transfer$") or g.popups(): break
    return g.find_windows("^Fleet to fleet transfer$")


def transfer_ships_case(g, i, ships):
    """Transfer ships from fleet i (positive: down arrows, first -> second) and press OK; photograph the dialog before OK."""
    before = rome_fleets(g); log("fleets_before", fleets=before, treasury=treasury(g), file=save(g, "before.SAV"))
    w = open_transfer_ships(g, i)
    if not w:
        log("transfer_ships_no_dialog", popups=g.dismiss_popups(), shot=shot(g, "no_dialog")); return
    g.raise_window(w[0][0]); cs = g.controls("Fleet to fleet transfer")
    ups = [c for c in cs if c["cls"] == "TUpDown"]; top = min(u["y"] for u in ups)
    row = sorted((c for c in ups if abs(c["y"] - top) < 10), key=lambda c: c["x"])
    g.click(w[0][2] + 20, w[0][3] + 5, pause=0.6)          # activate the dialog (title strip) before the arrows
    n, fy = abs(ships), (0.75 if ships > 0 else 0.25)
    g._spin(row[1], n // 10, fy=fy); g._spin(row[0], n % 10, fy=fy)
    labels = [(c["cls"], c["text"], c["x"], c["y"]) for c in g.controls("Fleet to fleet transfer")]
    pre = shot(g, "dialog_before_ok", window=str(w[0][0]))
    boxes_before_ok = g.dismiss_popups()
    clicks = 0
    for _ in range(3):       # v2 (after the first batch): wait up to 4 s for the dialog to go; never press Cancel after an OK
        g.click_control(g.control(cs, text="OK"), pause=1.0); clicks += 1
        t0 = time.time()
        while time.time() - t0 < 4 and g.find_windows("^Fleet to fleet transfer$"): time.sleep(0.3)
        if not g.find_windows("^Fleet to fleet transfer$"): break
    seen = [(x[1], x[4], x[5]) for x in g.find_windows(".")]
    texts = g.dismiss_popups()
    still = bool(g.find_windows("^Fleet to fleet transfer$"))
    if still:
        log("dialog_still_open_after_ok", shot=shot(g, "still_open"))
    after = rome_fleets(g)
    log("transfer_ships", fleet=i, ships_requested=ships, controls_before_ok=labels, dialog_shot=pre, boxes_before_ok=boxes_before_ok,
        ok_clicks=clicks, windows_after_ok=seen, popups=texts, still_open_after_ok=still, fleets_after=after, treasury_after=treasury(g),
        armies_after={k: v for k, v in rome_armies(g).items() if k in (0, 12, 13)}, file=save(g, "after.SAV"))


g = Game()
try:
    V = {"Td0": (37, 123, 10, 50, 400, 20, 5), "Td1": (37, 123, 10, 50, 400, 20, 10), "Td2": (90, 123, 10, 40, 400, 5, 10)}[CASE]
    s5, m5, n5, s2, m2, n2, give = V
    fo = [(5, "ships", n5), (5, "supplies", s5), (5, "money", m5), (2, "ships", n2), (2, "supplies", s2), (2, "money", m2)]
    g.load(staged(SPLIT, [], fo), seed=12345); log("loaded", save=SPLIT.name, seed_line=g.seed_line)
    transfer_ships_case(g, 5, give)
    log("done")
except Exception as e:
    log("error", error=repr(e))
    try: log("error_state", shot=shot(g, "error"))
    except Exception: pass
    raise
finally:
    g.kill()
