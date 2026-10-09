"""Original-side check 1 of the v0.5.0 gap analysis (rows_g1.md NEW-g1-2): what the original's International Relations dialog does when
the Peace radio is set on a nation the player trades with, or is allied with, and whether Cancel discards a change.
Start: saves/run0-start-AUTO0720-seed12345.SAV, Rome human (Rome trades with Illyria, relation 1). Seed 12345, the seed exe. One fresh
process per phase:
  A  Peace on Illyria (trade partner) -> OK; read Rome->Illyria and Illyria->Rome from memory, the boxes, File > Save As; End turn; the
     next autosave's news.
  B  Cancel: open the dialog, click Peace on Illyria, Cancel; the relation must be unchanged; Save As.
  C  Ally: try Alliance with Illyria, then other nations, until one accepts (boxes recorded); Save As; then Peace on the ally -> OK; read
     both sides, the boxes; Save As; End turn; the autosave's news. (At this start all 15 refused: no natural ally.)
  D  Staged ally (L1, labelled): the start save with Rome-Illyria set to 2 (allied) both ways (runs/experiments/battles/stage.py
     `relation` op), then Peace on Illyria -> OK; both sides, boxes; Save As; End turn; news.
Saves are copied to artifacts/run-exp-peace-radio/ (never overwritten); one JSON line per step to peace_radio-<stamp>.jsonl (tracked).
python3 peace_radio.py A|B|C|D"""
import hashlib, json, shutil, sys, time
from pathlib import Path
R = Path("/home/diego/projects/ic2-conquest"); sys.path.insert(0, str(R))
import harness.driver as drv
from harness.driver import Game, G, DriverError
from state import sav
START = R / "saves/run0-start-AUTO0720-seed12345.SAV"
ART = R / "artifacts/run-exp-peace-radio"; ART.mkdir(parents=True, exist_ok=True)
D = R / "runs/experiments/data/run-exp-peace-radio"
STAMP = time.strftime("%Y%m%d-%H%M%S"); phase = sys.argv[1]
LOG = D / f"peace_radio-{phase}-{STAMP}.jsonl"
NAMES = ["Rome", "Carthage", "Seleucid", "Ptolemaic", "Macedonia", "Numidia", "Gaul", "Greece", "Celtiberia", "Illyria", "Dacia",
         "Bithynia", "Galatia", "Armenia", "Media", "Thracia"]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def log(step, **kw):
    kw.update(step=step, t=time.strftime("%H:%M:%S")); print(kw, flush=True)
    with LOG.open("a") as f: f.write(json.dumps(kw, default=str) + "\n")
def rel(g, a, b):
    return g.i16(drv.NATIONS + a * drv.NATION_LEN + 0x26 + 2 * b)
def both(g, n):
    return {"rome_to": rel(g, 0, n), "to_rome": rel(g, n, 0)}
def keep(src, name):
    dst = ART / f"{phase}_{STAMP}_{name}"; shutil.copy2(src, dst)
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")
    return dst.name
def save(g, name):
    return keep(g.save_as(name), name)
def end_turn_news(g):
    name, texts = g.end_turn(timeout=400)
    k = keep(G / name, name)
    s = sav.load(str(ART / k))
    return {"autosave": k, "texts": texts, "news": s["news"]}

if phase == "D":
    sys.path.insert(0, str(R / "runs/experiments/battles")); import stage
    staged = ART / f"D_{STAMP}_start_rome_illyria_allied.SAV"
    stage.edit(START, staged, [("relation", 0, 9, 2)])
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(staged)}  {staged.name}\n")
    START = staged
g = Game()
g.load(START, seed=12345)
log("loaded", seed_line=g.seed_line, illyria=both(g, 9))
if phase == "A":
    before = save(g, "A_before.SAV")
    v, texts = g.relation(9, "peace")
    log("peace_on_trade_partner", target="Illyria", value=v, boxes=texts, both=both(g, 9), before_save=before)
    log("saved_after", file=save(g, "A_after.SAV"))
    r = end_turn_news(g); log("end_turn", **r, both=both(g, 9))
elif phase == "B":
    g.dismiss_popups(); g.tool("relations", pause=1.5)
    if not g.find_windows("^International Relations$"): g.tool("relations", pause=1.5)
    w = g.find_windows("^International Relations$"); g.raise_window(w[0][0])
    cs = None
    for _ in range(8):
        try: cs = g.controls("International Relations"); break
        except DriverError: time.sleep(1)
    radios = sorted((c for c in cs if c["cls"] == "TRadioButton"), key=lambda c: (c["y"], c["x"]))
    for _ in range(2): g.click_control(radios[9 * 4 + 0], pause=0.5)
    shot = ART / f"B_{STAMP}_peace_clicked.png"; g.shot(shot, window=str(w[0][0]))
    clicks = 0
    for _ in range(3):              # a click into an inactive window may only activate it (CLAUDE.md, driver pitfalls)
        g.click_control(g.control(cs, text="Cancel"), pause=1.5); clicks += 1
        if not g.find_windows("^International Relations$"): break
    log("cancel", cancel_clicks=clicks, still_open=bool(g.find_windows("^International Relations$")), both=both(g, 9), shot=shot.name, shot_sha256=sha(shot))
    log("saved_after", file=save(g, "B_after_cancel.SAV"))
elif phase == "C":
    ally = None
    for n in [9] + [k for k in range(1, 16) if k not in (9, 6)]:
        try:
            v, texts = g.relation(n, "ally")
        except DriverError as e:
            log("ally_try", nation=NAMES[n], error=str(e), both=both(g, n)); continue
        log("ally_try", nation=NAMES[n], value=v, boxes=texts, both=both(g, n))
        if v == 2: ally = n; break
    if ally is None:
        log("no_ally"); g.kill(); sys.exit(0)
    log("saved_ally", file=save(g, "C_ally.SAV"))
    v, texts = g.relation(ally, "peace")
    log("peace_on_ally", target=NAMES[ally], value=v, boxes=texts, both=both(g, ally))
    log("saved_after", file=save(g, "C_after.SAV"))
    r = end_turn_news(g); log("end_turn", **r, both=both(g, ally))
elif phase == "D":
    log("staged", start=START.name, both=both(g, 9))
    v, texts = g.relation(9, "peace")
    log("peace_on_ally", target="Illyria", value=v, boxes=texts, both=both(g, 9))
    log("saved_after", file=save(g, "D_after.SAV"))
    r = end_turn_news(g); log("end_turn", **r, both=both(g, 9))
g.kill(); log("done")
