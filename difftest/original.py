"""Original side of the differential harness (#229): play actions through `harness/driver.py`.

The game is restarted with the run's seed (RandSeed is read at program start only), the start save is opened,
and after every action the state is saved under a name unique to the run (`<tag>-aNNN.SAV`) and copied to the
run folder as `aNNN.SAV`. Autosaves already in the game folder are moved aside first, never deleted (rule 6).
A progress file records the last finished action, so a stopped run shows where it stopped.
"""
import json
import shutil
import time
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


def perform(g, a, state):
    op = a["op"]
    if op == "set_tax":
        return g.taxation(a["percent"])
    if op == "move":
        pos, texts = g.move(a["army"], a["x"], a["y"])
        return texts
    if op == "recruit":
        nation = state["current_nation"]
        t = a["troops"]
        return g.recruit(recruit_row(state, nation, a["city"]), a["type"], thousands=t // 1000, hundreds=t % 1000 // 100)
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
