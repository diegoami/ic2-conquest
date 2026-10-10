"""Original-side checks of the v0.5.0 gap analysis (rows_g2.md "Original-side checks needed" 1, 2 and 6): the Supply dialog's providers,
Transfer ships edge cases, and the per-unit clamps of Transfer unit at 100,000 troops and at a full fleet.
One fresh process per case: python3 supply_transfer.py <case>. Fast rollingsave seed exe, seed 12345, Xvfb.

Code reading this tests (Imperial Conquest 2.exe, capstone; see README.md):
- TUnitMap_SupplyArmy 0x446f50 opens TAFSupply only when FUN_004495c8 (own city in 3x3, else any city whose owner is not at war,
  relation 3) or FUN_00449e50 (a marker (cell-300) mod 16 == nation in 3x3, resolved to a fleet by FUN_00449970) finds something;
  else it returns with no box. No army is searched.
- TUnitMap_SupplyFleet 0x4477fc: city as above, else FUN_00449e50 on the fleet's own tile, and the dialog opens only when the fleet
  found differs from the fleet itself. FUN_00449e50 keeps the LAST match of its scan (x-1..x+1 outer, y-1..y+1 inner), and the fleet's
  own tile matches, so a partner fleet scanned before the own tile (any x-1 tile, or (x, y-1)) is overwritten: prediction, no dialog.
- TAFSupply_FindProviders 0x43f468: up to 2 cities not at war and 3 own fleets (not the target fleet) within one tile; no army.

Staging (L1, labelled per case): unit slots, army moves/owner, Rome-Gaul relation, fleet ships; armies' and fleets' x, y are never
edited (they are moved in play). Saves go to artifacts/run-exp-supply-transfer-clamps/ with unique names <case>_<stamp>_<name>;
every case logs one JSON line per step to supply_transfer-<case>-<stamp>.jsonl beside this script (rule 6: never overwritten)."""
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
ART = R / "artifacts/run-exp-supply-transfer-clamps"; ART.mkdir(parents=True, exist_ok=True)
D = Path(__file__).resolve().parent
STAMP = time.strftime("%Y%m%d-%H%M%S"); CASE = sys.argv[1]
LOG = D / f"supply_transfer-{CASE}-{STAMP}.jsonl"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log(step, **kw):
    kw.update(step=step, t=time.strftime("%H:%M:%S")); print(json.dumps(kw, default=str), flush=True)
    with LOG.open("a") as f: f.write(json.dumps(kw, default=str) + "\n")


from harness import environment as _env   # every start records the Wine/font environment in this log (harness/environment.py)
_env.add_sink(lambda rec: log("environment", **{k: v for k, v in rec.items() if k != "step"}))


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
        struct.pack_into("<h", b, f0 + f * sav.FLEET_LEN + {"ships": 18, "moves": 12}[field], v)
    dst = ART / f"{CASE}_{STAMP}_staged_{Path(src).stem}.SAV"; dst.write_bytes(bytes(b))
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    log("staged", src=Path(src).name, src_sha256=sha(src), dst=dst.name, ops=ops, fleet_ops=list(fleet_ops))
    return dst


def army(g, i):
    s = g.army_state(i); s["troops"] = sum(struct.unpack_from("<h", g.army_rec(i), 16 + 32 * k + 4)[0] for k in range(20)
                                            if struct.unpack_from("<h", g.army_rec(i), 16 + 32 * k + 4)[0] > 0)
    s["units"] = sum(1 for k in range(20) if struct.unpack_from("<h", g.army_rec(i), 16 + 32 * k + 4)[0] > 0)
    return s


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


def press_supply(g, kind, i, label):
    """Select army/fleet i, press its Supply button (x from the tooltip calibration) and wait 6 s for the dialog or a box.
    A dialog is photographed, its controls listed, and closed with OK unchanged. Returns what was seen."""
    title = "Supply army" if kind == "army" else "Supply fleet"
    if kind == "army":
        x0, y0 = g.army_pos(i); g.select_army(i, x0, y0)
        if not g.army_x: g.calibrate_army_toolbar()
        x = g.army_x.get("supply", g.ARMY_TOOLS["supply"])
    else:
        g.select_fleet(i)
        if not g.fleet_x: g.calibrate_fleet_toolbar()
        x = g.fleet_x.get("supply", drv.FLEET_TOOLS["supply"])
    opened, clicks = False, 0
    for _ in range(2):        # the first click into an inactive window may only activate it
        g.click(x, ARMY_TOOLBAR_Y, pause=0.5); clicks += 1
        t0 = time.time()
        while time.time() - t0 < 6:
            if g.find_windows("^%s$" % title) or g.popups(): break
            time.sleep(0.3)
        if g.find_windows("^%s$" % title) or g.popups(): break
    w = g.find_windows("^%s$" % title)
    r = {"label": label, "kind": kind, "id": i, "pos": (g.army_pos(i) if kind == "army" else g.fleet_pos(i)), "clicks": clicks,
         "selected_army": g.i16(drv.SEL_ARMY), "selected_fleet": g.i16(drv.SEL_FLEET), "windows": [(x[1], x[4], x[5]) for x in g.find_windows(".")]}
    if w:
        opened = True; g.raise_window(w[0][0]); time.sleep(0.5)
        r["dialog_shot"] = shot(g, f"{label}_dialog", window=str(w[0][0]))
        cs = None
        for _ in range(6):
            try: cs = g.controls(title); break
            except DriverError: time.sleep(1)
        r["controls"] = [(c["cls"], c["text"], c["x"], c["y"]) for c in (cs or [])]
        if cs and any(c["text"] == "OK" for c in cs): g._ok_until_closed(title, cs)
        else: g.close_dialog(title, (239, 337))
    else:
        r["root_shot"] = shot(g, f"{label}_nothing")
    r["opened"] = opened; r["popups"] = g.dismiss_popups()
    log("supply_press", **r)
    return r


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
    before = rome_fleets(g); log("fleets_before", fleets=before, file=save(g, "before.SAV"))
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
        ok_clicks=clicks, windows_after_ok=seen, popups=texts, still_open_after_ok=still, fleets_after=after,
        armies_after={k: v for k, v in rome_armies(g).items() if k in (0, 12, 13)}, file=save(g, "after.SAV"))


def transfer_units_case(g, src, rows):
    """Select army src, open Transfer unit, ctrl-click `rows` of the left list, press its Transfer, OK (probe_transfer20.py's steps)."""
    before = {k: v for k, v in rome_armies(g).items() if k in (0, 12, 13)}
    log("armies_before", armies=before, fleets=rome_fleets(g), file=save(g, "before.SAV"))
    ax, ay = g.army_pos(src); g.select_army(src, ax, ay)
    if not g.army_x: g.calibrate_army_toolbar()
    for _ in range(2):
        g.click(g.army_x["transfer"], ARMY_TOOLBAR_Y, pause=0.5)
        try: g.wait(lambda: g.find_windows("^Army to army transfer$"), 6, "Army to army transfer"); break
        except DriverError: pass
    else:
        log("transfer_units_no_dialog", popups=g.dismiss_popups(), shot=shot(g, "no_dialog")); return
    cs = g.controls("Army to army transfer")
    lst = sorted((c for c in cs if c["cls"] == "TListBox"), key=lambda c: c["x"])
    btn = sorted((c for c in cs if c["text"] == "Transfer"), key=lambda c: c["x"])[0]
    g.click(lst[0]["x"] + lst[0]["w"] // 2, lst[0]["y"] - 8, pause=0.6)
    sh("xdotool", "keydown", "ctrl")
    for r in rows: g.click(lst[0]["x"] + lst[0]["w"] // 2, lst[0]["y"] + 6 + 10 * r, pause=0.4)
    sh("xdotool", "keyup", "ctrl")
    sel = shot(g, "selection")
    g.click_control(btn, pause=1.5)
    seen = [(x[1], x[4], x[5]) for x in g.find_windows(".")]
    box_shot = shot(g, "after_transfer_button")
    texts = g.dismiss_popups()
    for _ in range(3):
        g.click_control(g.control(cs, text="OK"), pause=1.5)
        if not g.find_windows("^Army to army transfer$"): break
    texts += g.dismiss_popups()
    after = {k: v for k, v in rome_armies(g).items() if k in (0, 12, 13)}
    log("transfer_units", src=src, rows=rows, selection_shot=sel, after_button_shot=box_shot, windows_after_button=seen, popups=texts,
        armies_after=after, fleets_after=rome_fleets(g), file=save(g, "after.SAV"))


g = Game()
try:
    if CASE == "P1":        # army alone, then next to an own army only (start, army 0 walked to (100,34), then split)
        g.load(START, seed=12345); log("loaded", save=START.name, seed_line=g.seed_line)
        walk(g, 0, [(100, 36), (100, 35), (100, 34)]); log("saved", file=save(g, "alone.SAV"), armies=rome_armies(g))
        press_supply(g, "army", 0, "army_alone")
        texts = g.split_army(0, (0,)); log("split", popups=texts, armies=rome_armies(g), file=save(g, "split.SAV"))
        new = max(rome_armies(g))
        press_supply(g, "army", 0, "army_next_to_own_army")
        press_supply(g, "army", new, "new_army_next_to_own_army")
        walk(g, 0, [(100, 35)])              # positive control: (100,35) is next to Arretium (99,36), an own city
        press_supply(g, "army", 0, "control_army_next_to_arretium")
    elif CASE in ("P2", "P3"):   # next to Felsina (Gaul): P2 staged at peace with Gaul, P3 unstaged (at war, relation 3)
        src = staged(START, [("relation", 0, 6, 0)]) if CASE == "P2" else START
        g.load(src, seed=12345); log("loaded", save=Path(src).name, seed_line=g.seed_line,
                                     rome_gaul=g.i16(drv.NATIONS + 0x26 + 2 * 6), gaul_rome=g.i16(drv.NATIONS + 6 * drv.NATION_LEN + 0x26))
        walk(g, 0, [(100, 36), (100, 35), (100, 34), (100, 33), (99, 32)]); log("saved", file=save(g, "at_felsina.SAV"), armies=rome_armies(g))
        press_supply(g, "army", 0, "army_next_to_felsina_" + ("peace" if CASE == "P2" else "war"))
    elif CASE == "P4":      # army next to an own fleet only; the fleet next to an own army only (army 0 moves staged 15)
        src = staged(PORT, [("moves", 0, 15)])
        g.load(src, seed=12345); log("loaded", save=src.name, seed_line=g.seed_line)
        walk(g, 0, [(101, 44), (102, 43), (103, 44), (103, 45), (104, 46), (104, 47), (105, 48)])
        sail(g, 2, [(101, 47), (102, 48), (103, 48), (104, 48)])
        log("saved", file=save(g, "placed.SAV"), armies=rome_armies(g), fleets=rome_fleets(g))
        press_supply(g, "army", 0, "army_next_to_own_fleet")
        press_supply(g, "fleet", 2, "fleet_next_to_own_army")
    elif CASE == "P5":      # fleet alone at sea, then split: the two fleets supply each other?
        g.load(PORT, seed=12345); log("loaded", save=PORT.name, seed_line=g.seed_line)
        sail(g, 2, [(100, 46), (99, 46), (98, 46), (97, 46)]); log("saved", file=save(g, "alone.SAV"), fleets=rome_fleets(g))
        press_supply(g, "fleet", 2, "fleet_alone")
        texts = g.split_fleet(2, 10); fl = rome_fleets(g); log("split", popups=texts, fleets=fl, file=save(g, "split.SAV"))
        new = max(fl)
        press_supply(g, "fleet", 2, "fleet2_next_to_new_fleet")
        press_supply(g, "fleet", new, "new_fleet_next_to_fleet2")
    elif CASE.startswith("Ta"):   # one fleet carries an army: fleet 2 staged 30 ships, army 0 (10,700) embarked by a normal order
        g.load(staged(SPLIT, [], [(2, "ships", 30)]), seed=12345); log("loaded", seed_line=g.seed_line)
        texts = g.embark(0, 2); log("embark", popups=texts, fleets=rome_fleets(g), army0=army(g, 0))
        if g.fleet_state(2)["army"] != 0: raise DriverError("army 0 not aboard fleet 2")
        {"Ta1": lambda: transfer_ships_case(g, 2, 5), "Ta2": lambda: transfer_ships_case(g, 2, 10),
         "Ta3": lambda: transfer_ships_case(g, 5, 5), "Ta4": lambda: transfer_ships_case(g, 2, 30)}[CASE]()   # Ta4: every ship of the carrying fleet
    elif CASE == "Tb1":     # combined over 100: fleet 2 staged 95, fleet 5 staged 10; 8 ships from 5 to 2 (103)
        g.load(staged(SPLIT, [], [(2, "ships", 95), (5, "ships", 10)]), seed=12345); log("loaded", seed_line=g.seed_line)
        transfer_ships_case(g, 5, 8)
    elif CASE in ("Tc1", "Tc2"):  # every ship: Tc1 all 10 of fleet 5 into fleet 2; Tc2 all 20 of fleet 2 into fleet 5
        g.load(SPLIT, seed=12345); log("loaded", save=SPLIT.name, seed_line=g.seed_line)
        transfer_ships_case(g, 5, 10) if CASE == "Tc1" else transfer_ships_case(g, 2, 20)
    elif CASE == "U1":      # 100,000 troops: army 0 3 x hi 1,000 into a partner of 8 x hi 12,250 = 98,000 (armies 12 and 13 both)
        big = [("hi", 12250, 6)] * 8
        g.load(staged(PORT, [("units", 0, [("hi", 1000, 6)] * 3), ("units", 12, big), ("units", 13, big)]), seed=12345)
        log("loaded", seed_line=g.seed_line); transfer_units_case(g, 0, [0, 1, 2])
    elif CASE in ("U2", "U3", "U3b"):  # full fleet: army 0 (10,700) embarked on fleet 2 (30 ships); army 12 (moves 3) sends units into it
        units = {"U2": [("li", 1600, 6)] * 3, "U3": [("li", 4799, 6)], "U3b": [("li", 4800, 6)]}[CASE]
        g.load(staged(PORT, [("moves", 12, 3), ("owner", 13, 1), ("units", 12, units)]), seed=12345); log("loaded", seed_line=g.seed_line)
        texts = g.embark(0, 2); log("embark", popups=texts, fleets=rome_fleets(g), army0=army(g, 0))
        if g.fleet_state(2)["army"] != 0: raise DriverError("army 0 not aboard fleet 2")
        transfer_units_case(g, 12, list(range(len(units))))
    else:
        raise SystemExit("unknown case " + CASE)
    log("done")
except Exception as e:
    log("error", error=repr(e))
    try: log("error_state", shot=shot(g, "error"))
    except Exception: pass
    raise
finally:
    g.kill()
