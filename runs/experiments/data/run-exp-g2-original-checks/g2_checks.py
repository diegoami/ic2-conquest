"""Original-side checks 3, 4 and 5 of the v0.5.0 gap analysis (rows_g2.md "Original-side checks needed"; issue #75): selecting a 0-move army (MM01),
an unreachable move target (MM03), and Change units: Join with three or more units, Rename with two selected, Split unit at the R41 threshold
and the Split unit spinner range (UA06, D05, D06). (Check 7, the storm, is run-free: c7_storm_reanalysis.py.)

One fresh Wine process per case: python3 g2_checks.py <case>. Fast rollingsave seed exe, seed 12345, Xvfb. Every case that expects
"nothing happens" has a positive control in the same run. Cases: C3, C4, C5a (Join 3 and 4 units), C5b (Rename with two selected, one selected as
control), C5c (Split unit: type size table from game memory, threshold tests, spinner range, smallest and largest new unit).

Staging (L1, labelled per case): unit slots and army moves only (runs/experiments/battles/stage.py); armies' positions are never edited.
Saves and screenshots go to artifacts/run-exp-g2-original-checks/ with unique names <case>_<stamp>_<name>; each case logs one JSON line per
step to g2_checks-<case>-<stamp>.jsonl beside this script (rule 6: never overwritten; SAVES.sha256 gets every binary's hash)."""
import hashlib, json, re, shutil, struct, subprocess, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "runs/experiments/battles"))
import harness.driver as drv
from harness.driver import Game, G, DriverError, ARMY_TOOLBAR_Y, sh, WORK, WINE
from state import sav
import stage

START = R / "saves/run0-start-AUTO0720-seed12345.SAV"
PORT = R / "saves/fleet-port-antium-0734.SAV"
ART = R / "artifacts/run-exp-g2-original-checks"; ART.mkdir(parents=True, exist_ok=True)
D = Path(__file__).resolve().parent
STAMP = time.strftime("%Y%m%d-%H%M%S"); CASE = sys.argv[1]
LOG = D / f"g2_checks-{CASE}-{STAMP}.jsonl"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log(step, **kw):
    kw.update(step=step, t=time.strftime("%H:%M:%S")); print(json.dumps(kw, default=str), flush=True)
    with LOG.open("a") as f: f.write(json.dumps(kw, default=str) + "\n")


from harness import environment as _env   # every start records the Wine/font environment in this log
_env.add_sink(lambda rec: log("environment", **{k: v for k, v in rec.items() if k != "step"}))


def keep(src, name):
    dst = ART / f"{CASE}_{STAMP}_{name}"
    if dst.exists(): raise SystemExit(f"{dst} exists: names must be unique")
    shutil.copy2(src, dst)
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    return dst.name


def save(g, name):
    return keep(g.save_as(f"{CASE}_{STAMP}_{name}"), name)


def shot(g, name, window="root"):
    p = ART / f"{CASE}_{STAMP}_{name}.png"; g.shot(p, window=window)
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(p)}  {p.name}\n")
    return p.name


def ocr_png(p):
    t = subprocess.run(["tesseract", str(p), "-", "--psm", "6"], capture_output=True, text=True).stdout
    return " ".join(t.split())


def ocr_window(g, name, wid):
    """Screenshot window wid, keep it, and return (file name, OCR text)."""
    f = shot(g, name, window=str(wid)); return f, ocr_png(ART / f)


def info_panel(g):
    """The permanent Information panel (an 'Information' window taller than 600 px): (file, OCR) or None."""
    for w in g.find_windows("^Information$"):
        if w[5] > 600: return ocr_window(g, "info_panel_%d" % int(time.time() * 10 % 100000), w[0])
    return None


def strip_sig(g, tag):
    """Photograph the army button strip (y 96..122 of the root window) and return (file, sha of its pixels, OCR of the region above it)."""
    f = shot(g, "strip_" + tag)
    crop = ART / f"{CASE}_{STAMP}_strip_{tag}_crop.png"
    subprocess.run(["convert", str(ART / f), "-crop", "260x30+335+96", "+repage", str(crop)], check=True)
    px = subprocess.run(["convert", str(crop), "rgb:-"], capture_output=True).stdout
    with (D / "SAVES.sha256").open("a") as fh: fh.write(f"{sha(crop)}  {crop.name}\n")
    return {"root": f, "crop": crop.name, "pixels_sha256": hashlib.sha256(px).hexdigest()}


def staged(src, ops, tag):
    b = bytearray(Path(src).read_bytes()); stage.apply(b, ops)
    dst = ART / f"{CASE}_{STAMP}_staged_{tag}_{Path(src).stem}.SAV"; dst.write_bytes(bytes(b))
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    log("staged", src=Path(src).name, src_sha256=sha(src), dst=dst.name, ops=ops)
    return dst


def army(g, i):
    s = g.army_state(i); rec = g.army_rec(i)
    s["slots"] = [(struct.unpack_from("<h", rec, 16 + 32 * k + 2)[0], struct.unpack_from("<h", rec, 16 + 32 * k + 4)[0],
                   sav.cstr(rec[16 + 32 * k + 8:16 + 32 * k + 32])) for k in range(20) if struct.unpack_from("<h", rec, 16 + 32 * k + 4)[0] > 0]
    s["troops"] = sum(t for _, t, _ in s["slots"]); s["units"] = len(s["slots"]); return s


def rome_armies(g):
    n = g.i16(0x4A0324)
    return {i: army(g, i) for i in range(n) if struct.unpack_from("<h", g.army_rec(i), 4)[0] == 0}


def sel(g): return {"army": g.i16(drv.SEL_ARMY), "fleet": g.i16(drv.SEL_FLEET)}


def windows(g): return [(w[1], w[4], w[5]) for w in g.find_windows(".") if w[4] > 1]


def close_dialog_ok(g, title, cs):
    if cs and any(c["text"] == "OK" for c in cs): g._ok_until_closed(title, cs)
    else: g.close_dialog(title, (239, 337))


def press_tool(g, tool, title, label, army_id):
    """Army army_id is selected; press its toolbar button `tool` (x from the tooltip calibration) and wait up to 6 s for the dialog `title` or a box.
    A dialog is photographed (OCR), its controls listed, and closed with OK unchanged. Returns what was seen."""
    if not g.army_x: g.calibrate_army_toolbar()
    x = g.army_x.get(tool, g.ARMY_TOOLS[tool])
    clicks = 0
    for _ in range(2):        # the first click into an inactive window may only activate it
        g.click(x, ARMY_TOOLBAR_Y, pause=0.5); clicks += 1
        t0 = time.time()
        while time.time() - t0 < 6:
            if g.find_windows("^%s$" % title) or g.popups(): break
            time.sleep(0.3)
        if g.find_windows("^%s$" % title) or g.popups(): break
    w = g.find_windows("^%s$" % title)
    r = {"label": label, "tool": tool, "button_x": x, "army": army_id, "clicks": clicks, "selection": sel(g), "windows": windows(g)}
    if w:
        g.raise_window(w[0][0]); time.sleep(0.5)
        r["dialog_shot"], r["dialog_ocr"] = ocr_window(g, f"{label}_dialog", w[0][0])
        cs = None
        for _ in range(6):
            try: cs = g.controls(title); break
            except DriverError: time.sleep(1)
        r["controls"] = [(c["cls"], c["text"], c["x"], c["y"]) for c in (cs or [])]
        close_dialog_ok(g, title, cs)
    else:
        pops = g.popups(); r["boxes"] = [(p[1], g.read_popup(p)) for p in pops]
        r["root_shot"] = shot(g, f"{label}_nothing")
    r["opened"] = bool(w); r["popups_dismissed"] = g.dismiss_popups(); r["windows_after"] = windows(g)
    log("tool_press", **r); return r


def click_army_tile(g, i, label):
    """Click army i's tile up to 3 times (the first click into an inactive window may only activate it); log selection after each."""
    x, y = g.army_pos(i)
    log("pre_click", label=label, army=i, pos=(x, y), state=army(g, i), selection=sel(g), windows=windows(g), info=info_panel(g), strip=strip_sig(g, label + "_before"))
    out = []
    for k in range(3):
        g.click_tile(x, y); time.sleep(0.6)
        out.append({"click": k + 1, "selection": sel(g), "boxes": [(p[1], g.read_popup(p)) for p in g.popups()]})
        if g.i16(drv.SEL_ARMY) == i: break
    time.sleep(2.5)       # a selection that is dropped later (a 0-move army "dropped at 0 moves") shows here
    log("click_result", label=label, clicks=out, selection_after_wait=sel(g), windows=windows(g), info=info_panel(g), strip=strip_sig(g, label + "_after"),
        army_state=army(g, i), dismissed=g.dismiss_popups())
    return g.i16(drv.SEL_ARMY) == i


g = Game()
try:
    if CASE == "C3":        # MM01: selecting an own army with 0 moves. PORT: army 12 (102,45) has moves 0; control = the same army staged to moves 8
        for tag, src in (("zero_moves", PORT), ("control_moves8", staged(PORT, [("moves", 12, 8)], "army12_moves8"))):
            g.load(src, seed=12345) if tag == "zero_moves" else g.open(src)
            if tag != "zero_moves": g.wait(g.loaded, 20, "loaded")
            log("loaded", tag=tag, save=Path(src).name, seed_line=g.seed_line, armies={k: (v["x"], v["y"], v["moves"], v["troops"]) for k, v in rome_armies(g).items()},
                fleets=[g.fleet_state(i) for i in range(g.i16(0x4A0326)) if g.fleet_state(i)["owner"] == 0], file=save(g, tag + "_loaded.SAV"))
            if tag != "zero_moves": sh("xdotool", "mousemove", "1000", "900", check=False)
            ok = click_army_tile(g, 12, tag)
            log("selected", tag=tag, selected_army_is_12=ok)
            if ok:
                for tool, title in (("supply", "Supply army"), ("transfer", "Army to army transfer"), ("split", "Split army"), ("change", "Change units")):
                    press_tool(g, tool, title, f"{tag}_{tool}", 12)
                    if g.i16(drv.SEL_ARMY) != 12: click_army_tile(g, 12, f"{tag}_reselect_{tool}")
            else:
                # a dropped selection: record that the toolbar buttons do nothing for an unselected army, by pressing them anyway
                for tool, title in (("supply", "Supply army"), ("transfer", "Army to army transfer"), ("split", "Split army"), ("change", "Change units")):
                    press_tool(g, tool, title, f"{tag}_unselected_{tool}", 12)
            log("end_of_tag", tag=tag, armies=rome_armies(g), file=save(g, tag + "_end.SAV"))
    elif CASE == "C4":      # MM03: army 0 (moves 8) at (100,37), target 12 tiles north; control a target 5 tiles north
        for tag, tgt in (("far12", (100, 25)), ("near5", (100, 32))):
            g.load(START, seed=12345) if tag == "far12" else g.open(START)
            if tag != "far12": g.wait(g.loaded, 20, "loaded")
            ax, ay = g.army_pos(0)
            log("loaded", tag=tag, target=tgt, army0=army(g, 0), file=save(g, tag + "_before.SAV"))
            g.select_army(0, ax, ay); log("selected", selection=sel(g), shot=shot(g, tag + "_selected"))
            g.click_tile(*tgt, pause=2.0)
            t_sel = sel(g); texts = g.dismiss_popups()
            log("clicked_target", tag=tag, target=tgt, selection=t_sel, popups=texts, pos=g.army_pos(0), moves=army(g, 0)["moves"], shot=shot(g, tag + "_after_click"))
            time.sleep(2)
            log("after_wait", tag=tag, pos=g.army_pos(0), army0=army(g, 0), file=save(g, tag + "_after.SAV"))
    elif CASE == "C4b":     # explains C4's cost: one click per tile north of (100,37) (terrain costs read from the save), then a stop at a river with too few moves
        for tag in ("steps", "river_with_1_move_left"):
            src = START if tag == "steps" else staged(START, [("moves", 0, 11)], "army0_moves11")
            g.load(src, seed=12345) if tag == "steps" else g.open(src)
            if tag != "steps": g.wait(g.loaded, 20, "loaded")
            log("loaded", tag=tag, army0=army(g, 0), file=save(g, tag + "_before.SAV"))
            ax, ay = g.army_pos(0); g.select_army(0, ax, ay)
            if tag == "steps":
                s0 = sav.parse(START.read_bytes())
                for y in range(36, 28, -1):
                    pos0, mv0 = g.army_pos(0), army(g, 0)["moves"]
                    if g.i16(drv.SEL_ARMY) != 0: g.select_army(0, *pos0)
                    g.click_tile(100, y, pause=1.0)
                    log("step", to=(100, y), terrain=sav.terrain_name(sav.cell(s0, 100, y)), table_cost=sav.move_cost(sav.cell(s0, 100, y)),
                        pos=g.army_pos(0), moves_before=mv0, moves_after=army(g, 0)["moves"], selection=sel(g), popups=g.dismiss_popups())
            else:
                g.click_tile(100, 25, pause=2.0)
                log("clicked_target", target=(100, 25), pos=g.army_pos(0), army0=army(g, 0), selection=sel(g), popups=g.dismiss_popups(), shot=shot(g, tag + "_after_click"))
            log("end", tag=tag, army0=army(g, 0), file=save(g, tag + "_after.SAV"))
    elif CASE == "C5a":     # Join units: three, then four units of one type (army 0 staged), then three of a type next to another unit
        for tag, units, rows in (("join3", [("li", 1000, 6), ("li", 1200, 6), ("li", 1500, 6), ("hi", 5000, 6)], [0, 1, 2]),
                                 ("join4", [("li", 1000, 6), ("li", 1200, 6), ("li", 1500, 6), ("li", 1700, 6), ("hi", 5000, 6)], [0, 1, 2, 3]),
                                 ("join2_control", [("li", 1000, 6), ("li", 1200, 6), ("li", 1500, 6), ("hi", 5000, 6)], [0, 1])):
            src = staged(START, [("units", 0, units)], tag)
            g.load(src, seed=12345) if tag == "join3" else g.open(src)
            if tag != "join3": g.wait(g.loaded, 20, "loaded")
            log("loaded", tag=tag, rows=rows, army0=army(g, 0), file=save(g, tag + "_before.SAV"))
            cs = g._change_units(0, rows, "Join units")
            time.sleep(1.0)
            boxes = [(p[1], g.read_popup(p)) for p in g.popups()]
            log("join_pressed", tag=tag, rows=rows, boxes=boxes, windows=windows(g), shot=shot(g, tag + "_after_join"), army0=army(g, 0))
            texts = g.dismiss_popups(); g._close_change_units(cs)
            log("join_done", tag=tag, popups=texts, army0=army(g, 0), file=save(g, tag + "_after.SAV"))
    elif CASE == "C5b":     # Rename unit: two selected (the refusal), one selected (control), both on the same staged army
        src = staged(START, [("units", 0, [("li", 4800, 6), ("hi", 5000, 6), ("hi", 5200, 6)])], "rename")
        g.load(src, seed=12345); log("loaded", army0=army(g, 0), file=save(g, "before.SAV"))
        cs = g._change_units(0, [0, 1], "Rename unit"); time.sleep(1.0)
        w = g.find_windows("^Rename unit$"); boxes = [(p[1], g.read_popup(p)) for p in g.popups()]
        log("rename_two_selected", rename_dialog_open=bool(w), boxes=boxes, windows=windows(g), shot=shot(g, "two_selected"), army0=army(g, 0))
        if w:       # the original renames... whichever: type a name and OK so the save shows which unit changed
            rc = g.controls("Rename unit"); log("rename_controls", controls=[(c["cls"], c["text"]) for c in rc])
            edit = g.control(rc, cls="TEdit"); g.click_control(edit, pause=0.4); g.key("End"); sh("xdotool", "key", "--repeat", "30", "BackSpace")
            sh("xdotool", "type", "--delay", "60", "Renamed"); g._ok_until_closed("Rename unit", rc)
        texts = g.dismiss_popups(); g._close_change_units(cs)
        log("rename_two_done", popups=texts, army0=army(g, 0), file=save(g, "after_two.SAV"))
        texts = g.rename_unit(0, 2, "Control")
        log("rename_one_control", popups=texts, army0=army(g, 0), file=save(g, "after_one.SAV"))
    elif CASE == "C5c":     # Split unit: size table, thresholds, spinner range (sizes read from the dialog's two number boxes by OCR)
        g.load(START, seed=12345)
        table = {t: struct.unpack("<h", g.mem(0x478fca + t * 40, 2))[0] for t in range(len(sav.UNIT_TYPES))}
        rows = {t: [struct.unpack_from("<h", g.mem(0x478fca - 10 + t * 40, 40), k * 2)[0] for k in range(20)] for t in table}
        thr = {sav.UNIT_TYPES[t]: (v * 2) // 5 for t, v in table.items()}
        log("type_table", types=sav.UNIT_TYPES, size_limit_at_0x478fca=table, records=rows, thresholds=thr)
        tests = []
        for ty, th in thr.items():
            for tr in sorted({th - 1, th, 100}):
                tests.append((ty, tr, "default"))
        tests += [("hi", 5000, "probe"), ("hi", 5000, "ext_A"), ("hi", 5000, "ext_B"), ("li", 4800, "probe")]
        if len(sys.argv) > 2:
            tests = [(a.split(":")[0], int(a.split(":")[1]), a.split(":")[2] if a.count(":") > 1 else "default") for a in sys.argv[2:]]
        log("plan", tests=tests)

        READINGS = []       # every sizes() reading: index, stamp, images, OCR text; attached to the split_test line as r["size_readings"]

        def sizes(wid, tag=None):
            """(left, right) sizes shown in the Split unit dialog: the two number boxes, cropped, enlarged, OCR'd as digits.
            Every reading writes its own uniquely named images (<case>_<stamp>_<test>_rd<NNN>_{full,left,right}.png), hashed into SAVES.sha256
            and listed in READINGS (review fix R3: the earlier fixed names _split*.png were overwritten on every call)."""
            n = len(READINGS); base = f"{CURTEST[0]}_rd{n:03d}"
            full = shot(g, base + "_full", window=str(wid)); p = ART / full; out = []; rec = {"reading": n, "time": time.strftime("%H:%M:%S"), "full": full, "crops": {}}
            for x, side in ((8, "left"), (140, "right")):
                c = ART / f"{CASE}_{STAMP}_{base}_{side}.png"
                subprocess.run(["convert", str(p), "-crop", "58x26+%d+115" % x, "+repage", "-resize", "400%", "-colorspace", "Gray", str(c)], check=True)
                with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(c)}  {c.name}\n")
                t = subprocess.run(["tesseract", str(c), "-", "--psm", "7", "-c", "tessedit_char_whitelist=0123456789,"], capture_output=True, text=True).stdout.strip()
                v = int(t.replace(",", "")) if t.replace(",", "").isdigit() else t
                out.append(v); rec["crops"][side] = {"image": c.name, "ocr": t, "value": v}
            READINGS.append(rec); return tuple(out)

        def run_to_end(wid, sp, fy, cap=40):
            """Press spinner `sp` (fy 0.25 = up arrow, 0.75 = down) until the sizes stop changing twice in a row; returns the readings."""
            seq = [sizes(wid)]
            for _ in range(cap):
                g.click_control(sp, fy=fy, pause=0.25); seq.append(sizes(wid))
                if len(seq) >= 3 and seq[-1] == seq[-2] == seq[-3]: break
            return seq

        CURTEST = [""]
        for n, (ty, tr, mode) in enumerate(tests):
            tag = f"{ty}{tr}_{mode}"; CURTEST[0] = tag; READINGS.clear()
            src = staged(START, [("units", 0, [(ty, tr, 6), ("hi", 5000, 6)])], tag)
            g.open(src); g.wait(g.loaded, 20, "loaded")
            log("loaded", test=tag, army0=army(g, 0), file=save(g, tag + "_before.SAV"))
            cs = g._change_units(0, [0], "Split unit"); time.sleep(1.2)
            boxes = [(p[1], g.read_popup(p)) for p in g.popups()]
            w = g.find_windows("^Split unit$")
            r = {"test": tag, "type": ty, "troops": tr, "mode": mode, "threshold": thr[ty], "dialog_open": bool(w), "boxes": boxes, "windows": windows(g)}
            if w:
                wid = w[0][0]; g.raise_window(wid); time.sleep(0.5)
                r["dialog_shot"], r["dialog_ocr"] = ocr_window(g, tag + "_dialog", wid)
                sc = g.controls("Split unit"); r["controls"] = [(c["cls"], c["text"], c["x"], c["y"]) for c in sc]
                r["updown_ranges"] = subprocess.run([WINE, str(WORK / "win_updown.exe"), "Split unit"], capture_output=True, text=True, env=drv.ENV).stdout.strip().splitlines()
                s100, s1000 = sorted((c for c in sc if c["cls"] == "TUpDown"), key=lambda c: c["x"])
                r["sizes_initial"] = sizes(wid)
                if mode == "probe":
                    r["runs"] = {}
                    for name, sp in (("1000s", s1000), ("100s", s100)):
                        for dname, fy in (("up", 0.25), ("down", 0.75)):
                            r["runs"][f"{name}_{dname}"] = run_to_end(wid, sp, fy)
                    r["final_shot"] = shot(g, tag + "_final", window=str(wid))
                elif mode in ("ext_A", "ext_B"):
                    fy = 0.75 if mode == "ext_A" else 0.25
                    r["runs"] = {"1000s": run_to_end(wid, s1000, fy), "100s": run_to_end(wid, s100, fy)}
                    r["sizes_before_ok"] = sizes(wid); r["final_shot"] = shot(g, tag + "_before_ok", window=str(wid))
                if mode == "probe":      # a probe never applies: Cancel
                    g.click_control(g.control(sc, text="Cancel"), pause=1.0)
                    for _ in range(2):
                        if g.find_windows("^Split unit$"): g.click_control(g.control(sc, text="Cancel"), pause=1.0)
                else:
                    g._ok_until_closed("Split unit", sc)
                pass
            r["popups_after"] = g.dismiss_popups()          # a refusal box ("This unit is too small to split.") is closed before the Change units dialog
            g._close_change_units(cs)
            r["army0_after"] = army(g, 0); r["file"] = save(g, tag + "_after.SAV")
            r["size_readings"] = list(READINGS)
            log("split_test", **r)
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
