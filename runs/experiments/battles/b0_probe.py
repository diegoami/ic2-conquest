#!/usr/bin/env python3
"""B0 probe (docs/proposals/battles.md §4 B0): one battle end to end, on the normal seed build and on the battle-lab build.

    python3 runs/experiments/battles/b0_probe.py normal            # item 1: nothing auto-answered, every step logged
    python3 runs/experiments/battles/b0_probe.py savein [exe]      # item 2: File > Save As and the toolbar Save inside a battle
    python3 runs/experiments/battles/b0_probe.py lab SEED TAG      # item 3: one lab battle, BATTLEnn series kept
    python3 runs/experiments/battles/b0_probe.py gate              # 5 lab battles in a row + a repeat + seed 2
    python3 runs/experiments/battles/b0_probe.py resume            # item 4: File > Open of BATTLE05.SAV (lab)

Start save: `1_rome_270_winter_11.sav` (release run-1-rome of diegoami/imp_conquest_fixtures): Rome's army 0 (37,081) is 7 tiles
from Gaul's army 10 (46,700); it is walked to (86,28) and attacks (85,28). Every output goes to `artifacts/run-exp-battle-probe/`
(text outputs are archived under runs/experiments/data/run-exp-battle-probe/ by scripts/archive_measurements.py). Nothing is ever
deleted or overwritten: a re-run writes new files (a timestamp suffix).
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import harness.driver as D  # noqa: E402
from harness.driver import (BATTLE_FLAG, FILE_ITEMS, G, SEL_ARMY, DriverError, Game, sh)  # noqa: E402
from state.sav import live_armies, load  # noqa: E402

OUT = ROOT / "artifacts" / "run-exp-battle-probe"
START = OUT / "1_rome_270_winter_11.sav"
NORMAL_EXE = "Imperial Conquest 2 fast rollingsave seed.exe"
LAB_EXE = "Imperial Conquest 2 lab s%d.exe"
ROME_ARMY, GAUL_TILE, STAGE_TILE = 0, (85, 28), (86, 28)
LEGS = [(90, 25), (87, 27), STAGE_TILE]       # straight legs of the 6-move path (planner.path.path_adjacent)
SEED = 12345
TOOLBAR_Y = 112
# The research save opens with a unit map of 29 x 27 tiles in view (window 1143 x 903), not the driver's 13 x 13.
D.VIEW_COLS, D.VIEW_ROWS = 29, 27
# ... and its window covers the driver's NEUTRAL click point (1000, 900): with an army selected, reset_ui's click there ORDERS A MOVE
# (found in B0: Save As moved army 0 from (86,28) to (86,30)). Use a point below the unit map (screen bottom strip, bare root).
D.NEUTRAL = (700, 1005)
STAMP = time.strftime("%Y%m%d-%H%M%S")


class Log:
    """Timestamped events to a text log and a jsonl file (new files per run, never overwritten)."""

    def __init__(self, tag):
        OUT.mkdir(parents=True, exist_ok=True)
        self.tag, self.t0 = tag, time.time()
        self.txt = OUT / f"{tag}-{STAMP}.log"
        self.jl = OUT / f"{tag}-{STAMP}.jsonl"

    def __call__(self, event, **kw):
        t = round(time.time() - self.t0, 2)
        rec = {"t": t, "event": event, **kw}
        with open(self.jl, "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        line = f"[{t:7.2f}] {event} " + " ".join(f"{k}={v!r}" for k, v in kw.items())
        with open(self.txt, "a") as f:
            f.write(line + "\n")
        print(line, flush=True)

    def shot(self, g, name, window="root"):
        p = OUT / f"{self.tag}-{STAMP}-{name}.png"
        g.shot(p, window=window)
        self("shot", file=p.name)
        return p


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def win_list(g):
    return [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows()]


def start_game(g, log, exe, seed=None):
    """Fresh process, the research save opened. `seed` (normal build only) goes to SEED.TXT; the lab exe has its seed baked in.
    File > Open is done here, not by Game.open, because this save opens with a modal box ("Bithynia wants to trade with Rome."),
    and with a box open the main window's title never gets 'turn' in it, so Game.open's wait would time out."""
    g.exe = exe
    if seed is not None:
        g.set_seed(seed)
    n = g.seedlog_lines()
    t0 = time.time()
    g.start()
    log("process_started", exe=exe, seconds=round(time.time() - t0, 1), pid=g.pid)
    if seed is not None:
        g.wait(lambda: g.seedlog_lines() > n, 20, "SEED.LOG line at start")
        log("seed_line", line=(G / "SEED.LOG").read_text().splitlines()[-1].strip())
    shutil.copy(START, G / START.name)
    log("start_save", file=START.name, sha256=sha(START))
    t1 = time.time()
    g.menu("file", FILE_ITEMS["open"])
    g.click(636, 450)
    g.replace_field(START.name)
    g.key("Return")
    g.wait(lambda: g.find_windows("^Unit map$") and g.find_windows("^Area map$"), 30, "map windows after load")
    time.sleep(3)
    texts = g.dismiss_popups()
    log("loaded", seconds=round(time.time() - t1, 1), popups=texts, calendar=g.calendar(), windows=win_list(g))
    return texts


def stage(g, log):
    """Walk army 0 to (86,28), next to Gaul's army 10 at (85,28)."""
    for leg in LEGS:
        pos, texts = g.move(ROME_ARMY, *leg)
        log("move", to=leg, now=pos, popups=texts)
    if tuple(g.army_pos(ROME_ARMY)) != STAGE_TILE:
        raise DriverError("army 0 is at %s, not %s" % (g.army_pos(ROME_ARMY), STAGE_TILE))


def attack_open(g, log, shots=True):
    """Select army 0, click Gaul's tile, and watch (every 0.5 s) until the battle window is up. Nothing is answered."""
    g.select_army(ROME_ARMY, *STAGE_TILE)
    t0 = time.time()
    g.click_tile(*GAUL_TILE, pause=0.0)
    log("attack_clicked", selected=g.i16(SEL_ARMY))
    seen = []
    while time.time() - t0 < 40:
        ws = g.find_windows(" v ")
        if g.in_battle() and ws:
            break
        names = [w[1] for w in g.popups()]
        if names and names != seen:
            log("popup_before_battle", names=names, texts=[g.read_popup(p) for p in g.popups()])
            seen = names
        time.sleep(0.5)
    else:
        raise DriverError("battle window did not open in 40 s")
    dt = round(time.time() - t0, 2)
    w = g.find_windows(" v ")[0]
    log("battle_open", seconds_from_click=dt, in_battle=g.in_battle(), title=w[1], geometry=w[2:], windows=win_list(g),
        flag=g.mem(BATTLE_FLAG, 1)[0])
    return dt


def toolbar_scan(g, log, step=3):
    """Hover the whole battle toolbar width (x 5..455) and record every tooltip (named X windows) that appears."""
    base = {w[1] for w in g.find_windows(".")}
    seen = {}
    for x in range(5, 456, step):
        sh("xdotool", "mousemove", str(x), str(TOOLBAR_Y))
        time.sleep(0.7)
        names = {w[1] for w in g.find_windows(".")} - base
        for n in names:
            seen.setdefault(n, []).append(x)
    res = {n: [min(v), max(v)] for n, v in seen.items()}
    log("toolbar_tooltips", x_ranges=res)
    return res


def dump_controls(g, log, title, label):
    try:
        cs = g.controls(title)
    except DriverError as e:
        log("controls", label=label, error=str(e))
        return []
    log("controls", label=label, title=title, controls=cs)
    return cs


def ocr(path):
    return " ".join(subprocess.run(["tesseract", str(path), "-", "--psm", "6"], capture_output=True, text=True).stdout.split())


def post_save(g, log, name):
    t0 = time.time()
    p = g.save_as(name)
    log("save_as", file=name, seconds=round(time.time() - t0, 1), sha256=sha(p))
    return p


def describe_save(path, log, label):
    from state.sav import load as ld
    s = ld(path)
    arm = {a["id"]: (a["owner"], a["troops"]) for a in live_armies(s) if a["owner"] in (0, 6)}
    log("save_state", label=label, file=Path(path).name, size=Path(path).stat().st_size, battle_flag=s["battle_flag"], turn=s["turn"],
        armies=arm, last_news=s["news"][-4:])
    return s


def keep(p, tag=None):
    """Copy a file of the game folder into the artifacts folder under a name that does not exist yet."""
    p = Path(p)
    dst = OUT / ((tag + "_" if tag else "") + p.name)
    if dst.exists() and sha(dst) != sha(p):
        dst = dst.with_name(f"{dst.stem}-{STAMP}{dst.suffix}")
    shutil.copy(p, dst)
    return dst


# ---------------------------------------------------------------------------------------------------------------------------
def cmd_normal(g):
    log = Log("b0-normal")
    t_all = time.time()
    start_game(g, log, NORMAL_EXE, SEED)
    log.shot(g, "01-loaded")
    stage(g, log)
    pre = post_save(g, log, "NB_pre_attack.SAV")
    keep(pre)
    describe_save(pre, log, "pre-attack")
    dt = attack_open(g, log)
    log.shot(g, "02-battle-placement")
    log("stacking", order=sh("xdotool", "search", "--onlyvisible", "--name", ".").split(),
        note="bottom-to-top order is not given by xdotool search; geometry only")
    dump_controls(g, log, g.find_windows(" v ")[0][1], "battle window")
    toolbar_scan(g, log)
    # Computer general, then End turn until the result box (count the clicks, record the title after each)
    tc = time.time()
    g.click(D.BATTLE_TOOLS["computer"], TOOLBAR_Y, pause=1.5)
    log("computer_general_clicked", title=[w[1] for w in g.find_windows(" v ")], in_battle=g.in_battle())
    log.shot(g, "03-after-computer-general")
    clicks = 0
    while clicks < 5 and g.in_battle() and not g.find_windows("Battle ended"):
        g.click(D.BATTLE_TOOLS["end_turn"], TOOLBAR_Y, pause=1.5)
        clicks += 1
        log("end_turn_clicked", n=clicks, in_battle=g.in_battle(), windows=[w[1] for w in g.find_windows()])
    g.wait(lambda: g.find_windows("Battle ended"), 20, "Battle ended box")
    log("battle_ended", end_turn_clicks=clicks, seconds_from_computer_general=round(time.time() - tc, 1),
        seconds_from_attack_click=round(time.time() - tc + dt, 1), in_battle=g.in_battle())
    time.sleep(1)
    p = log.shot(g, "04-battle-ended")
    be = g.find_windows("Battle ended")[0]
    pw = log.shot(g, "04b-battle-ended-window", window=str(be[0]))
    log("ocr_battle_ended", text=ocr(pw), geometry=be[2:])
    dump_controls(g, log, "Battle ended", "battle ended")
    g.click_control(g.control(g.controls("Battle ended"), text="OK"), pause=0.5)
    t_ok = time.time()
    for _ in range(12):
        time.sleep(1)
        log("after_ok", s=round(time.time() - t_ok, 1), in_battle=g.in_battle(), windows=win_list(g))
    log.shot(g, "05-after-ok-open")
    extra = [w for w in g.popups()]
    log("after_ok_popups", popups=extra)
    # If anything opened, it is left open and captured here, then answered No.
    for w in extra:
        log("after_ok_text", name=w[1], text=g.read_popup(w))
        dump_controls(g, log, w[1], "after OK: " + w[1])
        if w[1] == "Confirm":
            g.answer("Confirm", yes=False)
    post = post_save(g, log, "NB_post_battle.SAV")
    keep(post)
    s = describe_save(post, log, "post-battle")
    log("done", total_seconds=round(time.time() - t_all, 1))


def play_out(g, log, max_clicks=5):
    """Computer general on, End turn until the "Battle ended" box (counting the clicks), OK, wait for the map. Nothing else is answered."""
    t0 = time.time()
    g.click(D.BATTLE_TOOLS["computer"], TOOLBAR_Y, pause=1.5)
    log("computer_general_clicked", title=[w[1] for w in g.find_windows(" v ")], in_battle=g.in_battle())
    clicks = 0
    while clicks < max_clicks and g.in_battle() and not g.find_windows("Battle ended"):
        g.click(D.BATTLE_TOOLS["end_turn"], TOOLBAR_Y, pause=1.5)
        clicks += 1
        log("end_turn_clicked", n=clicks, in_battle=g.in_battle(), windows=[w[1] for w in g.find_windows()])
    g.wait(lambda: g.find_windows("Battle ended"), 30, "Battle ended box")
    time.sleep(1)
    be = g.find_windows("Battle ended")[0]
    pw = log.shot(g, "battle-ended-window", window=str(be[0]))
    log("battle_ended", end_turn_clicks=clicks, seconds=round(time.time() - t0, 1), in_battle=g.in_battle(), ocr=ocr(pw))
    g.click_control(g.control(g.controls("Battle ended"), text="OK"), pause=0.5)
    try:
        g.wait(lambda: g.find_windows("^Unit map$") and not g.find_windows("Battle ended"), 20, "map after OK")
    except DriverError:      # something is open after OK: leave it open, record it, the caller reads it
        log("after_ok_map_not_back", windows=win_list(g), popups=g.popups())
    time.sleep(2)
    peace = g.find_windows("^Offer of peace$")
    if peace:        # TBattlePols: left open and captured (screenshot, OCR, controls), then answered No, verified closed (waits up to 8 s)
        log("offer_of_peace_open", geometry=peace[0][2:], windows=win_list(g))
        pw = log.shot(g, "offer-of-peace-window", window=str(peace[0][0]))
        log("offer_of_peace_ocr", text=ocr(pw))
        cs = dump_controls(g, log, "Offer of peace", "offer of peace")
        log.shot(g, "offer-of-peace-root")
        g.click_control(g.control(cs, text="No"), pause=0.5)
        for _ in range(16):
            if not g.find_windows("^Offer of peace$"):
                break
            time.sleep(0.5)
        log("offer_of_peace_answered_no", closed=not g.find_windows("^Offer of peace$"), windows=win_list(g))
        time.sleep(2)
    extra = g.popups()
    log("after_ok", popups=extra, windows=win_list(g))
    return clicks


def battle_series(tag):
    """Move the game folder's BATTLEnn.SAV into the artifacts folder as <tag>_BATTLEnn.SAV; return the file names."""
    names = []
    for f in sorted(G.glob("BATTLE*.SAV")):
        dst = OUT / f"{tag}_{f.name}"
        if dst.exists():
            dst = dst.with_name(f"{dst.stem}-{STAMP}{dst.suffix}")
        shutil.copy(f, dst)
        f.unlink()
        names.append(dst.name)
    return names


def run_battle(g, log, exe, seed, tag, pre=False):
    """One whole trial from a fresh process; returns the timing record. `tag` names the kept files."""
    for f in G.glob("BATTLE*.SAV"):     # leftovers of an earlier run were copied out by battle_series; a stray one is kept, not lost
        shutil.copy(f, OUT / f"stray_{f.name}")
        f.unlink()
    t0 = time.time()
    start_game(g, log, exe, seed)
    t_loaded = time.time() - t0
    stage(g, log)
    if pre:
        keep(post_save(g, log, f"{tag}_pre.SAV"))
    t_stage = time.time() - t0
    dt = attack_open(g, log)
    t_open = time.time() - t0
    clicks = play_out(g, log)
    t_over = time.time() - t0
    post = post_save(g, log, f"{tag}_post.SAV")
    t_saved = time.time() - t0
    kept = keep(post)
    series = battle_series(tag)
    s = describe_save(kept, log, "post-battle " + tag)
    rec = {"tag": tag, "exe": exe, "seed": seed, "seconds_process_start_to_post_save": round(t_saved, 1),
           "seconds_loaded": round(t_loaded, 1), "seconds_staged": round(t_stage, 1), "seconds_click_to_battle_window": dt,
           "seconds_battle_open_to_over": round(t_over - t_open, 1), "seconds_post_save": round(t_saved - t_over, 1),
           "end_turn_clicks": clicks, "half_round_saves": len(series), "series": series, "post_sha256": sha(kept),
           "rome_after": [a for a in live_armies(s) if a["owner"] == 0 and a["id"] == ROME_ARMY],
           "gaul_after": [(a["id"], a["troops"]) for a in live_armies(s) if a["owner"] == 6]}
    log("trial", **{k: v for k, v in rec.items() if k != "rome_after"}, rome_army0_alive=bool(rec["rome_after"]))
    with open(OUT / "trials.jsonl", "a") as f:        # append-only, one line per trial
        f.write(json.dumps({**rec, "stamp": STAMP}, default=str) + "\n")
    return rec


def series_equal(a, b):
    """Byte-for-byte comparison of two kept BATTLEnn series (lists of file names in OUT)."""
    if len(a) != len(b):
        return {"equal": False, "why": f"{len(a)} v {len(b)} saves"}
    diff = [(x, y) for x, y in zip(a, b) if (OUT / x).read_bytes() != (OUT / y).read_bytes()]
    return {"equal": not diff, "n": len(a), "differing": diff[:5], "differing_count": len(diff)}


def cmd_lab(g):
    seed, tag = int(sys.argv[2]), sys.argv[3]
    run_battle(g, Log("b0-lab-" + tag), LAB_EXE % seed, None, f"lab{seed}_{tag}")


def cmd_gate(g):
    """Gate: 5 lab battles in a row on seed 1 (same battle), then seed 2 once; compares the BATTLEnn series byte for byte."""
    log = Log("b0-gate")
    recs = []
    for i in "abcde":
        recs.append(run_battle(g, log, LAB_EXE % 1, None, f"lab1_{i}"))
    recs.append(run_battle(g, log, LAB_EXE % 2, None, "lab2_a"))
    cmp = {}
    for i in "bcde":
        cmp["lab1_a v lab1_" + i] = series_equal(recs[0]["series"], recs["abcde".index(i)]["series"])
    cmp["lab1_a v lab2_a"] = series_equal(recs[0]["series"], recs[5]["series"])
    cmp["post-battle saves identical (lab1 a..e)"] = len({r["post_sha256"] for r in recs[:5]}) == 1
    times = [r["seconds_process_start_to_post_save"] for r in recs]
    log("gate_summary", comparisons=cmp, times=times, mean_lab1=round(sum(times[:5]) / 5, 1))
    (OUT / f"gate-summary-{STAMP}.json").write_text(json.dumps({"comparisons": cmp, "times": times, "records": recs}, indent=1, default=str))


def cmd_win(g):
    """A human VICTORY on the normal build (what opens after the OK of a won battle?): from NB_post_battle.SAV (the item-1 battle, Rome
    lost army 0) Rome's army 13 (38,455) walks to (86,28) and attacks Gaul's army 10 (17,239) at (85,28); nothing is auto-answered."""
    global START, ROME_ARMY, LEGS
    START, ROME_ARMY = OUT / "NB_post_battle.SAV", 13
    LEGS = [(91, 28), (90, 27), (89, 27), (88, 26), (87, 27), STAGE_TILE]
    log = Log("b0-win")
    start_game(g, log, NORMAL_EXE, SEED)
    stage(g, log)
    attack_open(g, log)
    log.shot(g, "01-placement")
    play_out(g, log)
    log.shot(g, "02-after-ok")
    for w in g.popups():
        log("after_ok_text", name=w[1], text=g.read_popup(w))
        dump_controls(g, log, w[1], "after OK (win): " + w[1])
    post = post_save(g, log, "WIN_post_battle.SAV")
    describe_save(keep(post), log, "post-battle win")


def block12(path):
    """(battle flag, bytes after the 55-byte trailer) of a save: 2,105 bytes when the battle block is present."""
    b = Path(path).read_bytes()
    from state.sav import parse
    t = parse(b)["tail_off"]
    return b[t + 54], len(b) - (t + 55)


def state_now(g):
    ws = g.find_windows(".")
    return {"in_battle": g.in_battle(), "sel_army": g.i16(SEL_ARMY), "battle_titles": [w[1] for w in g.find_windows(" v ")],
            "windows": [(w[1], w[2], w[3], w[4], w[5]) for w in ws if w[4] > 1]}


def try_save(g, log, label, name, via):
    """Inside a battle: File > Save As (via='menu') or the toolbar Save icon (via='toolbar'); everything is recorded, nothing assumed."""
    before = state_now(g)
    log("save_try_before", label=label, via=via, **before)
    mt = {f.name: (f.stat().st_mtime_ns, sha(f)) for f in G.glob("*.sav") if f.name.startswith("1_rome")}
    target = G / name
    target.unlink(missing_ok=True)
    if via in ("menu", "menu-noreset"):
        if via == "menu":
            g.menu("file", FILE_ITEMS["save_as"])
        else:       # g.menu's reset_ui presses Escape twice first; in a battle Escape may act on the battle, so this does not
            g.click(D.MENU["file"], 36, pause=0.8)
            g.click(D.MENU["file"] + 20, D.MENU_ITEM_Y(FILE_ITEMS["save_as"]), pause=1.2)
        time.sleep(1.0)
        log("save_try_after_menu", label=label, **state_now(g))
        log.shot(g, f"{label}-after-menu")
        if not g.in_battle() and "move" in label:      # the battle was gone before the dialog: do not type into the map
            log("save_try_abort", label=label, why="battle already over, no dialog")
            return {"label": label, "via": via, "file_written": False, "aborted": "battle over before the dialog"}
        g.replace_field(name)
        g.key("Return")
    else:
        g.reset_ui()
        g.click(D.TOOLBAR["save"], D.TOOLBAR_Y, pause=1.5)
        log("save_try_after_toolbar_click", label=label, **state_now(g))
        log.shot(g, f"{label}-after-toolbar")
    t0 = time.time()
    while time.time() - t0 < 15 and not (via != "toolbar" and target.exists() and target.stat().st_size > 100000):
        time.sleep(0.5)
        if via == "toolbar" and time.time() - t0 > 4:
            break
    time.sleep(1.0)
    res = {"label": label, "via": via, "file_written": target.exists()}
    if target.exists():
        res.update(size=target.stat().st_size, sha256=sha(target), block12=block12(target))
        res["kept"] = keep(target).name
    for f in G.glob("*.sav"):
        if f.name.startswith("1_rome") and (f.stat().st_mtime_ns, sha(f)) != mt.get(f.name):
            res["start_copy_rewritten"] = f.name
            res["start_copy_block12"] = block12(f)
            res["kept_start_copy"] = keep(f, label).name
    res["after"] = state_now(g)
    log("save_try_result", **res)
    return res


def cmd_savein(g):
    """Item 2 on the normal build. Control: toolbar Save on the strategic map. In the battle: Save As (menu) and the toolbar Save at the
    placement phase, then Save As again with Computer general on ("to move units"), opened WITHOUT reset_ui's Escape presses (the
    first attempt, b0-savein-20261004-081536, ended the battle there); then the battle is played out."""
    lab = len(sys.argv) > 2 and sys.argv[2] == "lab"       # `savein lab`: the same on the lab build (seed 1)
    log = Log("b0-savein-lab" if lab else "b0-savein")
    start_game(g, log, LAB_EXE % 1 if lab else NORMAL_EXE, None if lab else SEED)
    stage(g, log)
    # control: the toolbar Save outside a battle (army 0 is selected and stays so)
    before = {f.name: (f.stat().st_mtime_ns, sha(f)) for f in G.glob("*.sav")}
    g.reset_ui()
    g.select_army(ROME_ARMY, *STAGE_TILE)
    g.click(D.TOOLBAR["save"], D.TOOLBAR_Y, pause=2.0)
    time.sleep(2)
    changed = [f.name for f in G.glob("*.sav") if (f.stat().st_mtime_ns, sha(f)) != before.get(f.name)]
    log("control_toolbar_save_on_map", files_changed=changed, windows=win_list(g), sel_army=g.i16(SEL_ARMY))
    attack_open(g, log)
    log.shot(g, "01-placement")
    try_save(g, log, "placement-menu", "SI_lab_placement_menu.SAV" if lab else "SI_placement_menu.SAV", "menu")
    log("check_battle_window_still_open", **state_now(g))
    try_save(g, log, "placement-toolbar", "SI_lab_placement_toolbar.SAV" if lab else "SI_placement_toolbar.SAV", "toolbar")
    log("check_battle_window_still_open", **state_now(g))
    # Computer general stays OFF: End turn at the placement phase, then the phases pass with Rome idle and Gaul (AI) playing, so the
    # battle is mid-way and nothing runs while the dialog is open (the first two attempts, 081536 and 081801, toggled Computer general
    # first and the battle ran to its end at the next input event, before any dialog opened).
    for k in (1, 2, 3):
        g.click(D.BATTLE_TOOLS["end_turn"], TOOLBAR_Y, pause=2.5)
        log("end_turn_clicked_human", n=k, **state_now(g))
        log.shot(g, f"02-after-end-turn-{k}")
        if k == 2:
            break
    try_save(g, log, "mid-menu", "SI_lab_mid_menu.SAV" if lab else "SI_mid_menu.SAV", "menu")
    log("check_battle_window_still_open", **state_now(g))
    g.click(D.BATTLE_TOOLS["end_turn"], TOOLBAR_Y, pause=2.5)
    log("end_turn_clicked_human", n=3, **state_now(g))
    try_save(g, log, "mid2-menu", "SI_lab_mid2_menu.SAV" if lab else "SI_mid2_menu.SAV", "menu")
    log("check_battle_window_still_open", **state_now(g))
    if g.in_battle():
        play_out(g, log)
    elif g.find_windows("Battle ended"):
        g.click_control(g.control(g.controls("Battle ended"), text="OK"), pause=1.5)
    post = post_save(g, log, "SI_lab_post_battle.SAV" if lab else "SI_post_battle.SAV")
    describe_save(keep(post), log, "post-battle after saves in battle")
    if lab:
        log("lab_series", files=battle_series("silab"))


def cmd_escape(g):
    """Does Escape (reset_ui presses it twice before every menu) act on a battle? Computer general on, then one Escape, state after 3 s."""
    log = Log("b0-escape")
    start_game(g, log, NORMAL_EXE, SEED)
    stage(g, log)
    attack_open(g, log)
    g.key("Escape")
    time.sleep(2)
    log("escape_at_placement", **state_now(g))
    g.click(D.BATTLE_TOOLS["computer"], TOOLBAR_Y, pause=1.5)
    log("computer_general_clicked", **state_now(g))
    for i in range(8):
        time.sleep(1)
        log("idle_after_cg", s=i + 1, **state_now(g))
        if not g.in_battle():
            break
    if g.in_battle():
        g.key("Escape")
        for i in range(6):
            time.sleep(1)
            log("after_escape", s=i + 1, **state_now(g))
            if not g.in_battle():
                break
    log.shot(g, "end")


def open_file(g, log, name):
    shutil.copy(OUT / name, G / name) if (OUT / name).exists() else None
    g.menu("file", FILE_ITEMS["open"])
    g.click(636, 450)
    g.replace_field(name)
    g.key("Return")
    t0 = time.time()
    for _ in range(30):
        time.sleep(1)
        log("after_open", s=round(time.time() - t0, 1), **state_now(g))
        if g.in_battle() and g.find_windows(" v "):
            break
    return time.time() - t0


def cmd_resume(g):
    """Item 4: lab exe (seed given), File > Open of <tag>_BATTLE<nn>.SAV, Computer general, End turn, the rest of the series."""
    seed, tag, nn = int(sys.argv[2]), sys.argv[3], sys.argv[4]
    log = Log(f"b0-resume-{tag}-{nn}")
    src = f"{tag}_BATTLE{nn}.SAV"
    for f in G.glob("BATTLE*.SAV"):
        shutil.copy(f, OUT / f"stray_{f.name}")
        f.unlink()
    g.exe = LAB_EXE % seed
    g.start()
    log("process_started", exe=g.exe)
    # the save is opened under a name that is not BATTLEnn.SAV, so the new series cannot overwrite it
    name = f"RESUME_{nn}_{tag}.SAV"
    shutil.copy(OUT / src, OUT / name) if not (OUT / name).exists() else None
    log("source", file=src, sha256=sha(OUT / src), block12=block12(OUT / src))
    dt = open_file(g, log, name)
    log("resumed_window", seconds=round(dt, 1), **state_now(g))
    log.shot(g, "01-resumed")
    for w in g.find_windows(" v "):
        dump_controls(g, log, w[1], "resumed battle")
    for p in g.popups():
        log("popup", name=p[1], text=g.read_popup(p))
    play_out(g, log)
    post = post_save(g, log, f"resume_{nn}_{tag}_post.SAV")
    describe_save(keep(post), log, "post-battle after resume")
    series = battle_series(f"resume{nn}_{tag}")
    log("resumed_series", files=series)


def cmd_compare(g=None):
    """Compare two kept series: for each file of B, which file of A (if any) is byte-identical; else the nearest by differing bytes."""
    a_tag, b_tag = sys.argv[2], sys.argv[3]
    A = sorted(OUT.glob(f"{a_tag}_BATTLE*.SAV"))
    B = sorted(OUT.glob(f"{b_tag}_BATTLE*.SAV"))
    out = []
    for fb in B:
        db = fb.read_bytes()
        best = None
        for fa in A:
            da = fa.read_bytes()
            n = sum(x != y for x, y in zip(da, db)) + abs(len(da) - len(db))
            if best is None or n < best[1]:
                best = (fa.name, n)
        out.append({"b": fb.name, "closest_a": best[0], "differing_bytes": best[1], "identical": best[1] == 0})
    res = {"a": a_tag, "b": b_tag, "a_files": [f.name for f in A], "rows": out}
    (OUT / f"compare-{a_tag}-{b_tag}-{STAMP}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    g = Game()
    try:
        {"normal": cmd_normal, "lab": cmd_lab, "gate": cmd_gate, "savein": cmd_savein, "win": cmd_win, "escape": cmd_escape, "resume": cmd_resume, "compare": cmd_compare}[cmd](g)
    except KeyError:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
