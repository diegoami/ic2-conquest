"""Original side of the differential harness (#229): play actions through `harness/driver.py`.

The game is restarted with the run's seed (RandSeed is read at program start only), the start save is opened,
and after every action the state is saved under a name unique to the run (`<tag>-aNNN.SAV`) and copied to the
run folder as `aNNN.SAV`. Autosaves already in the game folder are moved aside first, never deleted (rule 6).
A progress file records the last finished action, so a stopped run shows where it stopped.
"""
import json
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path

from difftest.actions import checkpoint_names
from harness.driver import G, DriverError, Game
from state.sav import can_recruit_at, load


def recruit_row(state, nation, city):
    """Row of `city` in the Recruit dialog: the nation's city list filtered to the cities that may recruit
    (findings/2026-09-29-recruiting-cities-need-fortification-75.md; Rome's start list reads Luceria, ROME)."""
    s = state
    rows = [c for c in s["nations"][nation]["city_list"] if can_recruit_at(s, nation, s["cities"][c])]
    if city not in rows:
        raise DriverError(f"city {city} is not in the Recruit list {rows}")
    return rows.index(city)


TYPES = {"li": "Light infantry", "hi": "Heavy infantry", "ar": "Archers", "lc": "Light cavalry", "hc": "Heavy cavalry"}


def read_amount(g, spin100):
    """The troop amount in the Recruit dialog's "New unit" field, by OCR of its digits (the field is not a
    control). Its digits sit 39 px right of and 98 px below the 100s arrows (measured 2026-10-28, run-exp-diff084-tooling).
    Read at three scales; the majority wins, and no majority raises."""
    with tempfile.TemporaryDirectory() as d:
        shot = Path(d) / "root.png"
        g.shot(str(shot))
        reads = []
        for scale in (300, 400, 500):
            img = Path(d) / f"{scale}.png"
            subprocess.run(["convert", str(shot), "-crop", f"50x21+{spin100['x'] + 39}+{spin100['y'] + 98}", "-colorspace", "Gray",
                            "-scale", f"{scale}%", "-threshold", "60%", "-bordercolor", "white", "-border", "20", str(img)], check=True)
            text = subprocess.run(["tesseract", str(img), "-", "--psm", "7", "-c", "tessedit_char_whitelist=0123456789,"],
                                  capture_output=True, text=True).stdout.strip().replace(",", "")
            reads.append(int(text) if text.isdigit() else None)
    value, n = Counter(reads).most_common(1)[0]
    if value is None or n < 2:
        raise DriverError(f"Recruit amount unreadable: {reads}")
    return value


def recruit_exact(g, row, unit_type, troops):
    """Recruit exactly `troops` of `unit_type` at the Recruit list's `row`. The dialog starts each type at a
    default amount (1,200 at Rome, 270 BC) and the arrows step it by 100 and 1,000, so the amount is read, stepped
    to the target and read again before "Recruit unit" (driver.recruit only adds clicks to the default)."""
    g.open_recruit()
    cs = g.controls("Army recruits")
    g.click_list_row(g.control(cs, cls="TListBox", index=0), row, pause=0.6)
    g.click_control(g.control(cs, text=TYPES[unit_type]), pause=0.6)
    spins = sorted((c for c in cs if c["cls"] == "TUpDown"), key=lambda c: c["x"])      # 100s, 1000s
    texts = []
    for attempt in range(4):
        have = read_amount(g, spins[0])
        if have == troops:
            break
        if attempt == 3:
            continue
        diff = troops - have
        thousands, hundreds = abs(diff) // 1000, abs(diff) % 1000 // 100
        fy = 0.25 if diff > 0 else 0.75
        for _ in range(thousands):
            g.click_control(spins[1], fy=fy, pause=0.2)
        for _ in range(hundreds):
            g.click_control(spins[0], fy=fy, pause=0.2)
        time.sleep(0.3)
    else:
        g.close_controls("Army recruits", cs)
        raise DriverError(f"Recruit amount stuck at {have}, wanted {troops}")
    g.click_control(g.control(cs, text="Recruit unit"), pause=0.8)
    texts += g.dismiss_popups()
    g.close_controls("Army recruits", cs)
    return [f"amount {troops}"] + texts


def perform(g, a, state):
    op = a["op"]
    if op == "set_tax":
        return g.taxation(a["percent"])
    if op == "move":
        pos, texts = g.move(a["army"], a["x"], a["y"])
        return texts
    if op == "recruit":
        return recruit_exact(g, recruit_row(state, state["current_nation"], a["city"]), a["type"], a["troops"])
    if op == "end_turn":
        line, texts = g.end_turn(peace=False)
        return [f"AUTOSAVE {line}"] + texts
    raise ValueError(op)


def run(actions, start, out, seed, tag, log=print):
    """Play the actions from `start` in the original with startup seed `seed`; checkpoints, receipt.jsonl and
    progress.json go to `out`. `tag` makes the in-game save names unique to this run."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    names = checkpoint_names(actions)
    receipt = open(out / "receipt.jsonl", "w")

    def emit(**e):
        e["time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        receipt.write(json.dumps(e) + "\n")
        receipt.flush()

    def checkpoint(name):
        saved = g.save_as(f"{tag}-{name}.SAV")
        dst = out / f"{name}.SAV"
        shutil.copy(saved, dst)
        (out / "progress.json").write_text(json.dumps({"last_checkpoint": name, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}))
        return load(dst)

    g = Game(log=log)
    moved = g.move_aside(sorted(G.glob("AUTO*")))
    emit(kind="start", start=str(start), seed=seed, tag=tag, moved_aside=str(moved) if moved else None)
    popups = g.load(start, seed=seed)
    emit(kind="loaded", seed_line=getattr(g, "seed_line", ""), popups=popups, environment=g.environment)
    state = checkpoint(names[0])
    results = []
    for k, (a, name) in enumerate(zip(actions, names[1:])):
        try:
            texts = perform(g, a, state)
            error = None
        except DriverError as e:
            texts, error = [], f"{type(e).__name__}: {e}"
            g.dismiss_popups()
        state = checkpoint(name)
        results.append({"action": a, "reply": texts, "error": error})
        emit(kind="action", step=k, action=a, reply=texts, error=error, checkpoint=name, date=state["date"])
        log(f"original: {name} {a['op']} -> {state['date']}{' ERROR ' + error if error else ''}")
    emit(kind="done", steps=len(actions))
    receipt.close()
    g.kill()
    return results
