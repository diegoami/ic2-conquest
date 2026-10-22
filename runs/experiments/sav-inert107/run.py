#!/usr/bin/env python3
"""run-exp-sav-inert107: native checks of two static claims of issue #107.

    python3 runs/experiments/sav-inert107/run.py T1|T2|T3

T1  INERT bytes: load the start save and its marked copy (seed 12345), Save As,
    End turn; then File > New (Rome) in the marked process.
T2  Fleet waypoint: load fleet-split-antium-0734 and its route_y-sentinel copy
    (seed 12345), End turn.
T3  The INERT round trip (load, Save As) with the unpatched original EXE.

Every step is appended to runs/experiments/data/run-exp-sav-inert107/<test>-<stamp>.jsonl
(tracked); saves are copied to artifacts/run-exp-sav-inert107/<stamp>/ with unique names and
are never deleted (CLAUDE.md rule 6). Analysis: analyse.py.
"""
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness import driver  # noqa: E402

STAMP = time.strftime("%Y%m%d-%H%M%S")
DATA = ROOT / "runs/experiments/data/run-exp-sav-inert107"
ART = ROOT / "artifacts/run-exp-sav-inert107" / STAMP
INPUTS = ROOT / "artifacts/run-exp-sav-inert107/inputs"
SEED = 12345


class Log:
    def __init__(self, test):
        DATA.mkdir(parents=True, exist_ok=True)
        ART.mkdir(parents=True, exist_ok=True)
        self.path = DATA / f"{test}-{STAMP}.jsonl"
        self.fh = open(self.path, "x")

    def __call__(self, step, **kw):
        rec = dict(t=time.strftime("%H:%M:%S"), step=step, **kw)
        self.fh.write(json.dumps(rec) + "\n")
        self.fh.flush()
        print(json.dumps(rec), flush=True)

    def keep(self, src, name):
        """Copy a game-folder file to the artifacts with a unique name; log its hash."""
        dst = ART / name
        shutil.copyfile(src, dst)
        h = hashlib.sha256(dst.read_bytes()).hexdigest()
        self("kept", file=name, sha256=h, size=dst.stat().st_size)
        return dst


def last_autosave():
    line = (driver.G / "AUTOSAVE.LOG").read_text().splitlines()[-1]
    return driver.G / line.split()[1]


def load_and_turn(g, log, save, tag):
    g.load(save, seed=SEED)
    log("loaded", save=Path(save).name, tag=tag, seed_line=g.seed_line)
    log.keep(g.save_as(f"{tag}_{STAMP}_saveas.SAV"), f"{tag}_saveas.SAV")
    texts = g.end_turn(strict_confirm=True)
    log("end_turn", tag=tag, texts=texts if isinstance(texts, list) else str(texts))
    return log.keep(last_autosave(), f"{tag}_autosave_after_end_turn.SAV")


def new_game_same_process(g, log, tag):
    """File > New (Rome human) without restarting the process: the point of the check."""
    moved = g.supersede_autosaves()
    log("autosaves_superseded", folder=str(moved.name) if moved else None)
    g.menu("file", driver.FILE_ITEMS["new"])
    # a loaded game first asks "Are you sure you want to start a new game ?"
    g.wait(lambda: g.message_boxes(), 10, "new-game Confirm box")
    log("confirm", texts=[g.read_popup(p) for p in g.message_boxes()] if hasattr(g, "read_popup") else None)
    g.answer("Confirm", yes=True)
    time.sleep(1.5)
    g.wait(lambda: g.find_windows("^Imperial Conquest 2$") and not g.message_boxes(), 10, "new game form")
    x0, y0, pitch = g.NEWGAME_TICK
    g.click(x0, round(y0), pause=0.5)          # Rome's human tick
    g.click(344, 194)                          # OK
    g.wait(lambda: (driver.G / "AUTOSAVE.LOG").exists(), 120, "new-game autosave")
    time.sleep(3)
    texts = g.dismiss_popups()
    log("new_game", tag=tag, texts=texts)
    return log.keep(last_autosave(), f"{tag}_new_game_autosave.SAV")


def main():
    test = sys.argv[1]
    log = Log(test)
    log("start", test=test, exe=driver.EXE if test != "T3" else "Imperial Conquest 2.exe", stamp=STAMP)
    if test == "T1":
        g = driver.Game(log=lambda *a: None)
        load_and_turn(g, log, ROOT / "saves/run0-start-AUTO0720-seed12345.SAV", "T1A_plain")
        load_and_turn(g, log, INPUTS / "T1M_0720_inert_marked.SAV", "T1B_marked")
        new_game_same_process(g, log, "T1B_marked")
    elif test == "T2":
        g = driver.Game(log=lambda *a: None)
        load_and_turn(g, log, ROOT / "saves/fleet-split-antium-0734.SAV", "T2A_plain")
        load_and_turn(g, log, INPUTS / "T2M_0734_route_y_sentinel.SAV", "T2B_sentinel")
    elif test == "T3":
        g = driver.Game(exe="Imperial Conquest 2.exe", log=lambda *a: None)
        g.start()
        texts = g.open(INPUTS / "T1M_0720_inert_marked.SAV")
        log("loaded", save="T1M_0720_inert_marked.SAV", tag="T3_original", texts=texts)
        log.keep(g.save_as(f"T3_original_{STAMP}_saveas.SAV"), "T3_original_saveas.SAV")
    g.kill()
    log("done")


if __name__ == "__main__":
    main()
