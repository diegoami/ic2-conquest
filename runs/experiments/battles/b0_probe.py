#!/usr/bin/env python3
"""B0 probe (docs/proposals/battles.md §4 B0): one battle end to end, on the normal seed build and on the battle-lab build.

    python3 runs/experiments/battles/b0_probe.py normal            # item 1: nothing auto-answered, every step logged
    python3 runs/experiments/battles/b0_probe.py savein [lab]      # item 2: File > Save As and the toolbar Save inside a battle (`lab`: on the lab seed-1 exe)
    python3 runs/experiments/battles/b0_probe.py escape            # does Escape act on a battle?
    python3 runs/experiments/battles/b0_probe.py lab SEED TAG      # item 3: one lab battle, BATTLEnn series kept (the first trial, lab1_t0, was `lab 1 t0`)
    python3 runs/experiments/battles/b0_probe.py gate              # SIX lab seed-1 battles in a row (gate2_a..f) + seed 2 twice (gate2_s2a, s2b);
                                                                   #   writes gate-summary-<stamp>.json with every series/post comparison (lab1_t0 as an extra)
    python3 runs/experiments/battles/b0_probe.py report TAG...     # compare kept series with the first (series_equal) -> series-report-<stamp>.json
    python3 runs/experiments/battles/b0_probe.py resume SEED TAG NN [SFX]   # item 4: File > Open of <TAG>_BATTLE<NN>.SAV on lab exe SEED, played out
    python3 runs/experiments/battles/b0_probe.py resumecmp ORIG RES OFFSET [RES2]  # resume v original (RES file i = ORIG file i+OFFSET) and v a second resume
    python3 runs/experiments/battles/b0_probe.py compare A B       # closest file of series A for each file of series B, with the differing byte count
    python3 runs/experiments/battles/b0_probe.py win               # a human victory

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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402  (write_new: the one never-overwrite writer)
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
# (and its window covers the old NEUTRAL click point (1000, 900): reset_ui ORDERED A MOVE there; `Game.neutral_point` now derives a point off every window)
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


def window_ids():
    """Every visible top-level window id, named or not (the Wine file dialog has an EMPTY name, so find_windows(".") never sees it)."""
    return set(sh("xdotool", "search", "--onlyvisible", "--name", "").split())


def open_dialog(g, name):
    """File > Open and type the name. No click at a fixed point (the old driver click (636, 450) could land in the map): the dialog is
    proven open by a new, unnamed top-level window (420 x 267 at (430,270) here), which has the focus with the name field as in Save As;
    if none appears, DriverError and nothing is typed."""
    before = window_ids()
    g.menu("file", FILE_ITEMS["open"])
    try:
        g.wait(lambda: window_ids() - before, 8, "Open dialog window")
    except DriverError:
        raise DriverError("File > Open: no dialog window appeared (nothing typed)")
    time.sleep(0.5)
    g.replace_field(name)
    g.key("Return")


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
    open_dialog(g, START.name)
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
    base, n = dst, 0
    while dst.exists() and sha(dst) != sha(p):           # never overwrite (rule 6): loop until a free or identical name
        n += 1
        dst = base.with_name(f"{base.stem}-{STAMP}{'' if n == 1 else '-%d' % n}{base.suffix}")
    if not dst.exists():
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
    computer_general_on(g, log)
    log.shot(g, "03-after-computer-general")
    clicks = end_turn_until_over(g, log, 5)
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


def count_battle_saves():
    return len(list(G.glob("BATTLE*.SAV")))


def computer_general_on(g, log):
    """Click Computer general ONCE and verify it took effect (the title becomes "... to move units.", or the battle is already over / the
    "Battle ended" box is up). The toggle is stateful: no second click, DriverError if there is no sign within 8 s."""
    g.click(D.BATTLE_TOOLS["computer"], TOOLBAR_Y, pause=1.5)
    try:
        g.wait(lambda: not g.in_battle() or g.find_windows("Battle ended") or any("to move units" in w[1] for w in g.find_windows(" v ")),
               8, "Computer general to take effect (title 'to move units' or the battle over)", step=0.25)
    except DriverError:
        raise DriverError("Computer general click: no sign it took effect (title %s); not clicking again" % [w[1] for w in g.find_windows(" v ")])
    log("computer_general_clicked", title=[w[1] for w in g.find_windows(" v ")], in_battle=g.in_battle())


def end_turn_until_over(g, log, max_clicks=3):
    """End turn until the "Battle ended" box. Each click is made only after the previous one is PROVEN to have advanced the battle (in_battle
    fell, a Battle ended box appeared, the title changed or a new BATTLEnn.SAV was written, within 8 s); with no proof DriverError, never a
    blind second click. Returns the number of End turn clicks (0 if the Computer general click alone ended the battle)."""
    clicks = 0
    while g.in_battle() and not g.find_windows("Battle ended"):
        if clicks >= max_clicks:
            raise DriverError("battle not over after %d End turn clicks" % clicks)
        before = ([w[1] for w in g.find_windows(" v ")], count_battle_saves())
        g.click(D.BATTLE_TOOLS["end_turn"], TOOLBAR_Y, pause=1.0)
        clicks += 1
        proof = lambda: (not g.in_battle() or g.find_windows("Battle ended")
                         or ([w[1] for w in g.find_windows(" v ")], count_battle_saves()) != before)
        try:
            g.wait(proof, 8, "proof that End turn click %d advanced the battle" % clicks, step=0.25)
        except DriverError:
            raise DriverError("End turn click %d: no sign the battle advanced; not clicking again" % clicks)
        log("end_turn_clicked", n=clicks, in_battle=g.in_battle(), windows=[w[1] for w in g.find_windows()])
    return clicks


def play_out(g, log, max_clicks=3):
    """Computer general on, then End turn until the "Battle ended" box; OK; wait for the map OR an "Offer of peace" box (answered No, never Yes).
    Each End turn click is made only after the previous one is PROVEN to have advanced the battle (in_battle fell, a Battle ended box
    appeared, the title changed or a new BATTLEnn.SAV was written, within 8 s); with no proof DriverError, never a blind second click."""
    t0 = time.time()
    computer_general_on(g, log)
    clicks = end_turn_until_over(g, log, max_clicks)
    g.wait(lambda: g.find_windows("Battle ended"), 30, "Battle ended box")
    time.sleep(1)
    be = g.find_windows("Battle ended")[0]
    pw = log.shot(g, "battle-ended-window", window=str(be[0]))
    log("battle_ended", end_turn_clicks=clicks, seconds=round(time.time() - t0, 1), in_battle=g.in_battle(), ocr=ocr(pw))
    g.click_control(g.control(g.controls("Battle ended"), text="OK"), pause=0.5)
    t_ok = time.time()
    # the map is back, or the Offer of peace box is up (it blocks the map: the first gate run waited for the map only and aborted there)
    try:
        g.wait(lambda: g.find_windows("^Offer of peace$") or (g.find_windows("^Unit map$") and not g.find_windows("Battle ended")),
               60, "map or Offer of peace after OK")
    except DriverError:
        log("after_ok_nothing", windows=win_list(g), popups=g.popups())
    log("after_ok_wait", seconds=round(time.time() - t_ok, 1))
    time.sleep(2)
    peace = g.find_windows("^Offer of peace$")
    if peace:        # TBattlePols: left open and captured (screenshot, OCR, controls), then answered No, verified closed (waits up to 12 s)
        log("offer_of_peace_open", seconds_after_ok=round(time.time() - t_ok, 1), geometry=peace[0][2:], windows=win_list(g))
        pw = log.shot(g, "offer-of-peace-window", window=str(peace[0][0]))
        log("offer_of_peace_ocr", text=ocr(pw))
        cs = dump_controls(g, log, "Offer of peace", "offer of peace")
        log.shot(g, "offer-of-peace-root")
        g.click_control(g.control(cs, text="No"), pause=0.5)
        for _ in range(24):
            if not g.find_windows("^Offer of peace$"):
                break
            time.sleep(0.5)
        log("offer_of_peace_answered_no", closed=not g.find_windows("^Offer of peace$"), windows=win_list(g))
        g.wait(lambda: g.find_windows("^Unit map$"), 30, "map after the peace offer")
        time.sleep(2)
    extra = g.popups()
    log("after_ok", popups=extra, windows=win_list(g))
    return clicks


def battle_series(tag):
    """Move the game folder's BATTLEnn.SAV into the artifacts folder as <tag>_BATTLEnn.SAV (through keep(): an existing file with other
    content gets a -<stamp> suffix, never overwritten); return the kept file names in order."""
    names = []
    for f in sorted(G.glob("BATTLE*.SAV")):
        names.append(keep(f, tag).name)
        f.unlink()
    return names


def run_battle(g, log, exe, seed, tag, pre=False):
    """One whole trial from a fresh process; returns the timing record. `tag` names the kept files."""
    for f in G.glob("BATTLE*.SAV"):     # leftovers of an earlier run were copied out by battle_series; a stray one is kept, not lost
        keep(f, "stray")
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


def series_names(tag):
    """The kept files of series <tag>, one per half-round number nn: the NEWEST version when a re-run kept a `-<stamp>` copy beside the old
    one (the plain glob matched only the first run's files)."""
    best = {}
    for p in OUT.glob(f"{tag}_BATTLE[0-9][0-9]*.SAV"):
        nn = p.name[len(tag) + 7:len(tag) + 9]
        if nn not in best or p.stat().st_mtime_ns > best[nn].stat().st_mtime_ns:
            best[nn] = p
    return [best[k].name for k in sorted(best)]


def series_report(tags, ref=None):
    """Byte comparison of kept series, every tag against `ref` (default the first), plus the post-battle saves' hashes."""
    ref = ref or tags[0]
    res = {"reference": ref, "series_files": {t: len(series_names(t)) for t in tags}, "vs_reference": {}}
    for t in tags:
        res["vs_reference"][t] = series_equal(series_names(ref), series_names(t))
    res["post_sha256"] = {t: sha(OUT / f"{t}_post.SAV")[:16] for t in tags if (OUT / f"{t}_post.SAV").exists()}
    return res


def cmd_gate(g):
    """Gate: six lab seed-1 battles in a row (gate2_a..f, one process each), then seed 2 twice (gate2_s2a, gate2_s2b). The byte comparison
    of every series and of the post-battle saves, with lab1_t0 (made earlier by `lab 1 t0`) as an extra, is written to
    gate-summary-<stamp>.json together with the per-trial times (the mean is over the six seed-1 gate trials)."""
    log = Log("b0-gate")
    s1 = [run_battle(g, log, LAB_EXE % 1, None, f"gate2_{i}") for i in "abcdef"]
    s2 = [run_battle(g, log, LAB_EXE % 2, None, f"gate2_s2{i}") for i in "ab"]
    t1 = [r["seconds_process_start_to_post_save"] for r in s1]
    tags1 = [f"gate2_{i}" for i in "abcdef"] + (["lab1_t0"] if series_names("lab1_t0") else [])
    summary = {"seed1": series_report(tags1), "seed2": series_report(["gate2_s2a", "gate2_s2b"]),
               "seed1_v_seed2": series_equal(series_names("gate2_a"), series_names("gate2_s2a")),
               "times_seed1_s": t1, "mean_seed1_s": round(sum(t1) / len(t1), 1),
               "times_seed2_s": [r["seconds_process_start_to_post_save"] for r in s2], "records": s1 + s2}
    log("gate_summary", **{k: v for k, v in summary.items() if k != "records"})
    C.write_new(OUT, f"gate-summary-{STAMP}.json", json.dumps(summary, indent=1, default=str))


def cmd_report(g=None):
    res = series_report(sys.argv[2:])
    C.write_new(OUT, f"series-report-{STAMP}.json", json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def cmd_resumecmp(g=None):
    """resumecmp ORIG RES OFFSET [RES2]: file i of RES (a resume of ORIG's BATTLE<OFFSET>) against ORIG's file i+OFFSET, and against RES2."""
    orig, res, off = sys.argv[2], sys.argv[3], int(sys.argv[4])
    res2 = sys.argv[5] if len(sys.argv) > 5 else None
    A, R = series_names(orig), series_names(res)
    rd = lambda n: (OUT / n).read_bytes()
    rows = []
    for i, r in enumerate(R):
        row = {"resumed": r}
        if i + off < len(A):
            a = rd(A[i + off])
            row.update(original=A[i + off], differing_bytes=sum(x != y for x, y in zip(a, rd(r))) + abs(len(a) - len(rd(r))))
        rows.append(row)
    aligned = [r for r in rows if "differing_bytes" in r]
    out = {"original": orig, "resumed": res, "offset": off, "rows": rows, "aligned_rows": len(aligned),
           "all_identical_to_original": bool(aligned) and all(r["differing_bytes"] == 0 for r in aligned)}   # never vacuously true
    if res2:
        out["resume_v_resume"] = series_equal(R, series_names(res2))
    C.write_new(OUT, f"resume-comparison-{res}-{STAMP}.json", json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


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
        C.battle_end_turn(g)       # proven (half-round counter / title / flag), no blind click, no retry
        time.sleep(1.5)
        log("end_turn_clicked_human", n=k, **state_now(g))
        log.shot(g, f"02-after-end-turn-{k}")
        if k == 2:
            break
    try_save(g, log, "mid-menu", "SI_lab_mid_menu.SAV" if lab else "SI_mid_menu.SAV", "menu")
    log("check_battle_window_still_open", **state_now(g))
    C.battle_end_turn(g)
    time.sleep(1.5)
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
    open_dialog(g, name)
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
    sfx = sys.argv[5] if len(sys.argv) > 5 else ""        # optional suffix of the kept names (a second resume of the same save)
    log = Log(f"b0-resume-{tag}-{nn}{sfx}")
    src = f"{tag}_BATTLE{nn}.SAV"
    for f in G.glob("BATTLE*.SAV"):
        keep(f, "stray")
        f.unlink()
    g.exe = LAB_EXE % seed
    g.start()
    log("process_started", exe=g.exe)
    # the save is opened under a name that is not BATTLEnn.SAV, so the new series cannot overwrite it
    name = f"RESUME_{nn}_{tag}{sfx}.SAV"
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
    post = post_save(g, log, f"resume_{nn}_{tag}{sfx}_post.SAV")
    describe_save(keep(post), log, "post-battle after resume")
    series = battle_series(f"resume{nn}_{tag}{sfx}")
    log("resumed_series", files=series)


def cmd_compare(g=None):
    """Compare two kept series: for each file of B, which file of A (if any) is byte-identical; else the nearest by differing bytes."""
    a_tag, b_tag = sys.argv[2], sys.argv[3]
    A = [OUT / n for n in series_names(a_tag)]       # newest version per half-round (a re-run keeps a -<stamp> copy beside the old file)
    B = [OUT / n for n in series_names(b_tag)]
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
    C.write_new(OUT, f"compare-{a_tag}-{b_tag}-{STAMP}.json", json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    g = Game()
    try:
        {"normal": cmd_normal, "lab": cmd_lab, "gate": cmd_gate, "savein": cmd_savein, "win": cmd_win, "escape": cmd_escape, "resume": cmd_resume, "compare": cmd_compare, "report": cmd_report, "resumecmp": cmd_resumecmp}[cmd](g)
    except KeyError:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
