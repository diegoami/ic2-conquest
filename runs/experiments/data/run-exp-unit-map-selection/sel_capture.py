"""Capture the selection frame in the original IC2 unit map for armies, fleets and towns.

One fresh Wine process per unit type. For each:
  1. Load the reference save (fleet-port-antium-0734.SAV, turn 734, 270BC Spring)
  2. Bring the target tile into the unit map (show, not click-to-select yet)
  3. Park mouse on neutral point, screenshot "unselected" state
  4. Click tile to select the unit
  5. Screenshot "selected" state
  6. Two more captures 300 ms apart (blinking check)
  7. Save the game with selection active

Cases:
  Army 0:  (101, 45), troops 10,700
  Fleet 2: (101, 46), 30 ships (sea tile)
  Antium:  (101, 47), Roman city

Usage: python3 sel_capture.py
Output: artifacts/run-exp-unit-map-selection/ (created if absent)
"""
import hashlib, json, os, shutil, struct, subprocess, sys, time
from pathlib import Path

R = Path(__file__).resolve().parents[4]   # repo root
sys.path.insert(0, str(R))
import harness.driver as drv
from harness.driver import Game, sh, G, WORK, WINE, ENV, DISPLAY, \
    UNIT_PAINT, VIEW_COLS, VIEW_ROWS, SEL_ARMY, SEL_FLEET
from state import sav

ART = R / "artifacts/run-exp-unit-map-selection"
ART.mkdir(parents=True, exist_ok=True)

STAMP = time.strftime("%Y%m%d-%H%M%S")
CASE = "sel"
LOG = R / f"runs/experiments/data/run-exp-unit-map-selection/sel_capture-{STAMP}.log"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log(step, **kw):
    kw.update(step=step, t=time.strftime("%H:%M:%S"))
    print(json.dumps(kw, default=str), flush=True)
    with LOG.open("a") as f:
        f.write(json.dumps(kw, default=str) + "\n")


def _hash_line(dst):
    p = R / "runs/experiments/data/run-exp-unit-map-selection/SAVES.sha256"
    with p.open("a") as f:
        f.write(f"{sha(dst)}  {dst.relative_to(R)}\n")


def keep(src_path, name):
    """Copy src_path to ART with a unique stamped name, hash it, return its name."""
    dst = ART / f"{CASE}_{STAMP}_{name}"
    if dst.exists():
        raise SystemExit(f"{dst} exists: names must be unique")
    shutil.copy2(src_path, dst)
    _hash_line(dst)
    return dst.name


def bring_tile(g, x, y):
    """Bring tile (x,y) into the unit map; return its screen centre (cx, cy)."""
    ox, oy = g.view_origin()
    if not (ox <= x < ox + VIEW_COLS and oy <= y < oy + VIEW_ROWS - 1):
        g.reset_ui()
        g.click(6 + x, 126 + y, pause=0.8)
        ox, oy = g.view_origin()
    c, r = x - ox, y - oy
    if not (0 <= c < VIEW_COLS and 0 <= r < VIEW_ROWS):
        raise RuntimeError(f"tile {x},{y} not visible from origin {ox},{oy}")
    cx = UNIT_PAINT[0] + 32 * c + 16
    cy = UNIT_PAINT[1] + 30 + 32 * r + 16
    return cx, cy


def run_case(name, x, y, select_fn):
    """Run one selection case (army / fleet / town). Returns mem_state dict."""
    log("case_start", case=name, tile=(x, y))

    # Use Game.load: handles seed (None = keep save's RNG), start, open
    save_path = str(R / "saves/fleet-port-antium-0734.SAV")
    g = Game()
    texts = g.load(save_path, seed=None)   # None: loading does not reseed
    if texts:
        log("load_popups", case=name, texts=texts)

    try:
        # bring tile into unit map (no click-to-select yet)
        cx, cy = bring_tile(g, x, y)
        log("tile_visible", case=name, tile=(x, y), screen_centre=(cx, cy))

        # park mouse on neutral point
        nx, ny = g.neutral_point()
        sh("xdotool", "mousemove", str(nx), str(ny))
        time.sleep(1.0)

        # --- unselected screenshot ---
        p_unsel = ART / f"{CASE}_{STAMP}_{name}_unselected.png"
        if p_unsel.exists():
            raise SystemExit(f"{p_unsel} exists")
        g.shot(str(p_unsel))
        _hash_line(p_unsel)
        log("screenshot", case=name, type="unselected", file=p_unsel.name)

        # select the unit
        sel = select_fn(g, cx, cy)
        time.sleep(0.5)

        # --- selected screenshot ---
        p_sel = ART / f"{CASE}_{STAMP}_{name}_selected.png"
        if p_sel.exists():
            raise SystemExit(f"{p_sel} exists")
        g.shot(str(p_sel))
        _hash_line(p_sel)
        log("screenshot", case=name, type="selected", file=p_sel.name)

        # --- blink frames 300 ms apart ---
        time.sleep(0.3)
        p_f2 = ART / f"{CASE}_{STAMP}_{name}_frame2.png"
        if p_f2.exists():
            raise SystemExit(f"{p_f2} exists")
        g.shot(str(p_f2))
        _hash_line(p_f2)
        log("screenshot", case=name, type="frame2", file=p_f2.name)

        time.sleep(0.3)
        p_f3 = ART / f"{CASE}_{STAMP}_{name}_frame3.png"
        if p_f3.exists():
            raise SystemExit(f"{p_f3} exists")
        g.shot(str(p_f3))
        _hash_line(p_f3)
        log("screenshot", case=name, type="frame3", file=p_f3.name)

        # --- save with selection active ---
        save_name = f"SEL_{name.upper()}_{STAMP}.SAV"
        saved = g.save_as(save_name)
        kept_save = keep(saved, save_name)
        log("save_kept", case=name, kept=kept_save, sha256=sha(saved))

        mem_state = {
            "case": name,
            "tile_xy": [x, y],
            "screen_centre": [cx, cy],
            "selected_index": sel,
            "calendar": g.calendar(),
            "turn": g.turn_number(),
            "neutral_point": [nx, ny],
            "files": {
                "unselected": p_unsel.name,
                "selected": p_sel.name,
                "frame2": p_f2.name,
                "frame3": p_f3.name,
                "save": kept_save,
            }
        }
        log("case_done", **mem_state)
        return mem_state

    finally:
        g.kill()


def main():
    os.environ["DISPLAY"] = DISPLAY
    os.environ["WINEPREFIX"] = str(WORK / "prefix")
    os.environ["WINEDEBUG"] = "-all"
    os.environ["WINEARCH"] = "win32"

    results = {}

    # --- Army 0 at (101, 45) ---
    def select_army(g, cx, cy):
        g.click(cx, cy, pause=0.8)
        for _ in range(3):
            if g.i16(SEL_ARMY) == 0:
                return g.i16(SEL_ARMY)
            g.click(cx, cy, pause=0.5)
        raise RuntimeError(f"Army 0 not selected, SEL_ARMY={g.i16(SEL_ARMY)}")

    results["army"] = run_case("army", 101, 45, select_army)

    # --- Fleet 2 at (101, 46) ---
    def select_fleet(g, cx, cy):
        g.click(cx, cy, pause=0.8)
        for _ in range(3):
            if g.i16(SEL_FLEET) == 2:
                return g.i16(SEL_FLEET)
            g.click(cx, cy, pause=0.5)
        raise RuntimeError(f"Fleet 2 not selected, SEL_FLEET={g.i16(SEL_FLEET)}")

    results["fleet"] = run_case("fleet", 101, 46, select_fleet)

    # --- Antium city at (101, 47) ---
    def select_town(g, cx, cy):
        # Clicking a city tile selects it. No SEL_ARMY/SEL_FLEET change for cities.
        g.click(cx, cy, pause=0.8)
        return -1   # cities don't affect SEL_ARMY

    results["town"] = run_case("town", 101, 47, select_town)

    # write results JSON
    res_path = R / "runs/experiments/data/run-exp-unit-map-selection" / f"sel_results-{STAMP}.json"
    with res_path.open("w") as f:
        json.dump({"results": results, "stamp": STAMP}, f, indent=2)
    log("all_done", results_file=str(res_path.relative_to(R)))
    print(f"\nDone. Log: {LOG}")
    print(f"Results: {res_path}")


if __name__ == "__main__":
    main()
