"""Original side of the differential harness (#229): play actions through `harness/driver.py`.

The game is restarted with the run's seed (RandSeed is read at program start only), the start save is opened,
and after every action the state is saved under a name unique to the run (`<tag>-aNNN.SAV`) and copied to the
run folder as `aNNN.SAV`. Autosaves already in the game folder are moved aside first, never deleted (rule 6).
A progress file records the last finished action, so a stopped run shows where it stopped.
"""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from difftest.actions import checkpoint_names
from harness.driver import (AREA_ORIGIN, BATTLE_TOOLBAR_Y, BATTLE_TOOLS, CUR_NATION, G, SEL_ARMY, UNIT_PAINT, VIEW_COLS,
                            VIEW_ROWS, DriverError, Game, GameOver)
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


RECRUIT_MIN = {"li": 3000, "hi": 1200, "ar": 700, "lc": 1400, "hc": 500}       # battalion / 5
RECRUIT_MAX = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}    # battalion (DAT)


def recruit_exact(g, row, unit_type, troops):
    """Recruit exactly `troops` of `unit_type` at the Recruit list's `row`, by arithmetic, not by reading the field:
    choosing a type sets the amount to battalion / 5 and the arrows step it by 100 and 1,000, clamped to
    [battalion / 5, battalion] (research rules-specification.md, "Amounts" [confirmed]; seen 2026-10-29 in
    probe-recruit-ocr-v1: archers 700, light cavalry 1,400, heavy cavalry 500). From the minimum, a target inside the
    limits is reached without clamping. The intent check on the save confirms the amount. (OCR of the field was
    tried first and misread 700 as 0 and 2,500 as 2,000.)"""
    lo, hi = RECRUIT_MIN[unit_type], RECRUIT_MAX[unit_type]
    if not lo <= troops <= hi or (troops - lo) % 100:
        raise DriverError(f"{troops} {unit_type} cannot be set in the Recruit dialog ({lo}..{hi} in steps of 100 from {lo})")
    g.open_recruit()
    cs = g.controls("Army recruits")
    try:
        g.click_list_row(g.control(cs, cls="TListBox", index=0), row, pause=0.6)
        g.click_control(g.control(cs, text=TYPES[unit_type]), pause=0.6)
        spins = sorted((c for c in cs if c["cls"] == "TUpDown"), key=lambda c: c["x"])      # 100s, 1000s
        for _ in range((troops - lo) // 1000):
            g.click_control(spins[1], fy=0.25, pause=0.2)
        for _ in range((troops - lo) % 1000 // 100):
            g.click_control(spins[0], fy=0.25, pause=0.2)
        g.click_control(g.control(cs, text="Recruit unit"), pause=0.8)
        texts = g.dismiss_popups()
    finally:
        g.close_controls("Army recruits", cs)       # an open dialog would block the checkpoint's File > Save
    return [f"amount {troops}"] + texts


def build_fleet_tens_first(g, ships):
    """driver.build_fleet presses the 1s arrows before the 10s: for 25 ships the game built 34 (#230 fleet-25,
    2026-10-29; the 1s arrow seems to jump to the 10-ship minimum first). The driver's dialog handling (notices
    of fleets in construction, refusals, Cancel after OK), with the 10s arrows pressed first.
    The built size is checked by the intent check on the save."""
    def clicks(n):
        cs = g.controls("Build fleet")
        ups = sorted((c for c in cs if c["cls"] == "TUpDown"), key=lambda c: c["x"])      # 1s, 10s
        for _ in range(n // 10):
            g.click_control(ups[1], fy=0.25, pause=0.2)
        for _ in range(n % 10):
            g.click_control(ups[0], fy=0.25, pause=0.2)

    g.tool("build_fleet")
    for _ in range(40):
        g.wait(lambda: g.find_windows("^Build fleet$") or [w for w in g.popups() if w[1] in ("Information", "Warning", "Error")],
               20, "the Build fleet dialog or its refusal")
        if g.find_windows("^Build fleet$"):
            break
        boxes = [w for w in g.popups() if w[1] in ("Information", "Warning", "Error")]
        texts = [g.read_popup(w) for w in boxes]
        if not texts or not all("ready in" in t for t in texts):
            break
        g.dismiss_popups()
        time.sleep(1.0)
    if not g.find_windows("^Build fleet$"):
        refusal = [g.read_popup(w) for w in g.popups() if w[1] in ("Information", "Warning", "Error")]
        g.dismiss_popups()
        return refusal
    clicks(ships)
    cs = g.controls("Build fleet")
    g.click_control(g.control(cs, text="OK"), pause=1.5)
    texts = g.dismiss_popups()
    for _ in range(3):
        if not g.find_windows("^Build fleet$"):
            break
        g.click_control(g.control(cs, text="Cancel"), pause=1.0)
    if g.find_windows("^Build fleet$"):
        raise DriverError("Build fleet did not close after Cancel")
    return texts


def supply_from_controls(g, army, tons):
    """Supply army with the dialog's own controls. driver.supply clicks fixed points and closes the dialog at
    (239,337), but the OK button now sits at (223..293, 349..374) (measured 2026-10-29), so the dialog stayed
    open and the checkpoint's save timed out (#230 buy-*). The upper arrow pair moves tons from the provider
    (left: 10s, right: 100s; layout of Supply fleet), the provider being the list's default (first) row."""
    g.army_tool(army, "supply", "Supply army")
    cs = g.controls("Supply army")
    ups = [c for c in cs if c["cls"] == "TUpDown"]
    top = min(c["y"] for c in ups)
    tons_pair = sorted((c for c in ups if c["y"] == top), key=lambda c: c["x"])
    try:
        for _ in range(tons // 100):
            g.click_control(tons_pair[1], fy=0.25, pause=0.2)
        for _ in range(tons % 100 // 10):
            g.click_control(tons_pair[0], fy=0.25, pause=0.2)
        texts = g.dismiss_popups()
    finally:
        for _ in range(3):
            if not g.find_windows("^Supply army$"):
                break
            g.click_control(g.control(cs, text="OK"), pause=1.0)
    if g.find_windows("^Supply army$"):
        raise DriverError("Supply army did not close after OK")
    return texts


def move_army(g, i, x, y):
    """Select army i and click (x, y). A target outside the 13 x 13 unit map is first brought into view by a click on
    the area map WITHOUT driver.show()'s reset_ui (its Escape and neutral click may drop the selection); the army
    stays selected (probe-far-move-v1/v2, 2026-10-29). The click on the target is repeated once only if the first
    provably moved nothing (the area map takes the focus, so the first click may only re-activate the unit map;
    a click on sea moves nothing either time)."""
    ax, ay = g.army_pos(i)
    g.select_army(i, ax, ay)
    ox, oy = g.view_origin()
    if not (ox <= x < ox + VIEW_COLS and oy <= y < oy + VIEW_ROWS - 1):
        g.click(AREA_ORIGIN[0] + x, AREA_ORIGIN[1] + y, pause=0.8)
        if g.i16(SEL_ARMY) != i:
            raise DriverError(f"army {i} lost its selection when the map scrolled to {x},{y}")
        ox, oy = g.view_origin()
    c, r = x - ox, y - oy
    if not (0 <= c < VIEW_COLS and 0 <= r < VIEW_ROWS):
        raise DriverError(f"tile {x},{y} not visible from origin {ox},{oy}")
    texts = []
    for _ in range(2):
        g.click(UNIT_PAINT[0] + 32 * c + 16, UNIT_PAINT[1] + 30 + 32 * r + 16, pause=1.2)
        texts += g.dismiss_popups()
        if g.army_pos(i) != (ax, ay) or texts:
            break
    return texts


def perform(g, a, state):
    op = a["op"]
    if op == "set_tax":
        return g.taxation(a["percent"])
    if op == "move":
        return move_army(g, a["army"], a["x"], a["y"])
    if op == "recruit":
        return recruit_exact(g, recruit_row(state, state["current_nation"], a["city"]), a["type"], a["troops"])
    if op == "end_turn":
        line, texts = g.end_turn(peace=bool(a.get("peace", False)))
        return [f"AUTOSAVE {line}"] + texts
    if op == "relation":
        value, texts = g.relation(a["nation"], a["kind"])
        return [f"relation value {value}"] + texts
    if op == "fortify":
        c = state["cities"][a["city"]]
        return g.fortify(c["name"], c["x"], c["y"], a["points"])
    if op == "disband_army":
        return g.disband_army(a["army"])
    if op == "split_army":
        # Each Transfer removes its row from the dialog's list (rows 0 then 1 moved units 0 and 2), and the new army
        # takes the units in transfer order (highest first reversed them; #230 split-army-2units, 2026-10-29). So the
        # units go top to bottom, each row shifted up by the number already moved, as a player clicking down the list.
        return g.split_army(a["army"], tuple(u - k for k, u in enumerate(sorted(a["units"]))))
    if op == "join_armies":
        return g.join(a["army"])
    if op == "buy_supply":
        return supply_from_controls(g, a["army"], a["tons"])
    if op == "build_fleet":
        return build_fleet_tens_first(g, a["ships"])
    if op == "disband_slot":
        nation = state["current_nation"]
        slots = state["nations"][nation]["recruit_slots"]
        slot = slots[a["slot"]]
        unit_row = [x["slot"] for x in slots if x["city"] == slot["city"]].index(slot["slot"])
        return g.disband_unit(recruit_row(state, nation, slot["city"]), unit_row)
    if op == "hire_mercenary":
        army = state["armies"][a["army"]]
        offers = sorted(m["slot"] for m in state["mercenaries"]
                        if max(abs(m["x"] - army["x"]), abs(m["y"] - army["y"])) <= 1 and m["troops"] > 0)
        if a["pool"] not in offers:
            raise DriverError(f"mercenary pool slot {a['pool']} is not adjacent to army {a['army']} (offers {offers})")
        n, texts = g.hire_mercs(a["army"], rows=(offers.index(a["pool"]),))
        return [f"units hired {n}"] + texts
    if op == "move_fleet":
        pos, texts = g.move_fleet(a["fleet"], a["x"], a["y"])
        return texts
    if op == "attack_fleet":
        return g.attack_fleet(a["fleet"], a["target"])
    if op == "besiege":
        c = state["cities"][a["city"]]
        return g.attack(a["army"], c["x"], c["y"])
    if op == "attack_army":
        t = state["armies"][a["target"]]
        return g.attack(a["army"], t["x"], t["y"])
    if op == "embark":
        return g.embark(a["army"], a["fleet"])
    if op == "disembark":
        return g.disembark(a["fleet"], a["x"], a["y"])
    if op == "repair_fleet":
        return g.repair_fleet(a["fleet"], a["points"])
    if op == "supply_fleet":
        return g.supply_fleet(a["fleet"], tons=a["tons"])     # the dialog's default provider (as buy_supply)
    if op == "scuttle_fleet":
        return g.scuttle_fleet(a["fleet"], yes=True)
    if op == "split_fleet":
        return g.split_fleet(a["fleet"], a["ships"])
    if op == "join_fleets":
        return g.join_fleets(a["fleet"])
    if op == "transfer_ships":
        return g.transfer_ships(a["fleet"], a["ships"])
    if op == "mobilize":
        nation = state["current_nation"]
        slots = state["nations"][nation]["recruit_slots"]
        slot = slots[a["slot"]]
        unit_row = [x["slot"] for x in slots if x["city"] == slot["city"]].index(slot["slot"])
        return g.mobilize(recruit_row(state, nation, slot["city"]), [unit_row])
    if op == "disband_unit":
        return g.change_units_disband(a["army"], a["unit"])
    if op == "join_units":
        return g.join_units(a["army"], list(a["units"]))
    if op == "transfer_units":
        return g.transfer_units(a["army"], a["unit"])
    raise ValueError(op)


OBS_BYTE, HUMAN_FLAGS, NATION_STRIDE = 0x565000, 0x474B00, 0x494


def apply_observer(g):
    """Observation mode on a loaded game: OBS = 1 and every nation's human flag = 0 (in memory; the save is unchanged)."""
    g.write_mem(OBS_BYTE, b"\x01")
    for n in range(16):
        g.write_mem(HUMAN_FLAGS + NATION_STRIDE * n, b"\x00")


class OriginalSession:
    """One original game process playing from `start` with startup seed `seed`; every checkpoint is saved as
    `<tag>-<name>.SAV` in the game folder and copied to `out/<name>.SAV`. receipt.jsonl and progress.json are
    written as it goes."""

    def __init__(self, start, out, seed, tag, log=print, resume_randseed=None, start_randseed=None, observer=False):
        """`resume_randseed`: continue an interrupted game (owner 2026-11-04, the 150-turn runs). `start` is then the last
        completed checkpoint and the value is the RandSeed logged right after it (`randseed_after`); loading does not
        reseed, so writing it back continues the original's random stream exactly (findings/2026-11-04-v092-followups.md §4)."""
        self.out, self.tag, self.log = Path(out), tag, log
        self.game_over = None     # the End of Game text once the human is overthrown or conquered (act stops checkpointing)
        self.out.mkdir(parents=True, exist_ok=resume_randseed is not None)
        self.receipt = open(self.out / "receipt.jsonl", "a" if resume_randseed is not None else "w")
        self.observer = observer
        if observer:
            # Observation build (patches/observer_build.py): every nation is played by the original's AI, one round per
            # End turn. Built into the game folder if missing.
            import sys as _sys
            _sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "patches"))
            import observer_build as OB
            if not (G / OB.DST).exists():
                import walk_hook as WH
                bb = bytearray((G / WH.SRC).read_bytes())
                OB.build(bb)
                (G / OB.DST).write_bytes(bytes(bb))
            self.g = Game(exe=OB.DST, log=log)
        else:
            self.g = Game(log=log)
        moved = self.g.move_aside(sorted(G.glob("AUTO*")))
        self.emit(kind="resume" if resume_randseed is not None else "start", start=str(start), seed=seed, tag=tag,
                  moved_aside=str(moved) if moved else None)
        popups = self.g.load(start, seed=seed)
        written = resume_randseed if resume_randseed is not None else start_randseed
        if written is not None:
            import struct
            self.g.write_mem(0x45E030, struct.pack("<I", written))
        if observer:
            apply_observer(self.g)
        self.emit(kind="loaded", seed_line=getattr(self.g, "seed_line", ""), popups=popups, environment=self.g.environment,
                  randseed_written=written)

    def emit(self, **e):
        e["time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.receipt.write(json.dumps(e, default=str) + "\n")
        self.receipt.flush()

    ORDER_DIALOGS = ("Army to army transfer", "Split army", "Change units", "Split unit", "Rename unit", "Army recruits",
                     "Supply army", "Recruit mercenary unit", "Supply fleet", "Repair fleet", "Split fleet",
                     "Fleet to fleet transfer", "Build fleet", "International Relations", "Change tax level", "Fortify .*")

    def close_stray_dialogs(self):
        """Close any order dialog still open before a save: a refusal box can leave its dialog open (Army to army
        transfer into a 20-unit army, #230 transfer-into-20), and an open dialog blocks File > Save. Cancel if the
        dialog has it, else OK. Returns the titles closed."""
        closed = []
        for pattern in self.ORDER_DIALOGS:
            for _ in range(3):
                found = self.g.find_windows("^%s$" % pattern)
                if not found:
                    break
                title = found[0][1]
                self.g.dismiss_popups()
                try:
                    cs = self.g.controls(title)
                    button = next((c for c in cs if c["text"].replace("&", "").strip() in ("Cancel",)), None) \
                        or next((c for c in cs if c["text"].replace("&", "").strip() == "OK"), None)
                    if button is None:
                        break
                    self.g.click_control(button, pause=1.0)
                except DriverError:
                    time.sleep(0.6)
                closed.append(title)
        return closed

    def checkpoint(self, name):
        stray = self.close_stray_dialogs()
        if stray:
            self.emit(kind="closed_stray_dialogs", before=name, titles=stray)
        try:
            saved = self.g.save_as(f"{self.tag}-{name}.SAV")
        except DriverError as e:
            # A window that opened after the End turn's autosave blocked File > Save (seleucid-rulebot1-40t, turn 26,
            # 2026-11-02). Record what was on screen, answer boxes the documented way (a Confirm is answered No),
            # close a leftover Save dialog, and retry once under a new name; a second failure ends the game as before.
            g = self.g
            diag = {"windows": [(w[1], w[2], w[3], w[4], w[5]) for w in g.find_windows(".")],
                    "cur_nation": g.i16(CUR_NATION), "battle_flag": g.in_battle(), "steps": []}
            shot = self.out / f"{name}-save-timeout.png"
            try:
                g.shot(shot)
            except Exception:
                pass
            try:
                diag["steps"].append({"dismiss": g.dismiss_popups(strict=True)})
            except DriverError as c:
                diag["steps"].append({"dismiss": str(c)})
            bw = g.find_windows(" v ")
            if bw:
                # The battle window the human defends (seleucid turn 26: flag 0x4A0B7C reads 0 while it is open, so
                # play_battle does nothing). Raise it, then Computer general and up to 30 End turn clicks, recording each.
                subprocess.run(["xdotool", "windowactivate", "--sync", str(bw[0][0])], check=False)
                time.sleep(1.0)
                try:
                    g.shot(self.out / f"{name}-battle-raised.png")
                except Exception:
                    pass
                bx = g.battle_x or BATTLE_TOOLS
                g.click(bx.get("computer", BATTLE_TOOLS["computer"]), BATTLE_TOOLBAR_Y, pause=2.0)
                diag["steps"].append({"computer_general": True, "flag": g.in_battle(), "open": bool(g.find_windows(" v "))})
                for i in range(30):
                    if not g.find_windows(" v ") or g.find_windows("Battle ended"):
                        break
                    g.click(bx.get("end_turn", BATTLE_TOOLS["end_turn"]), BATTLE_TOOLBAR_Y, pause=2.0)
                    diag["steps"].append({"end_turn_click": i + 1, "flag": g.in_battle(), "open": bool(g.find_windows(" v ")),
                                          "title": (g.find_windows(" v ") or [[0, ""]])[0][1]})
                try:
                    g.shot(self.out / f"{name}-battle-after.png")
                except Exception:
                    pass
                try:
                    diag["steps"].append({"after_battle": g.dismiss_popups(strict=True)})
                except DriverError as c:
                    diag["steps"].append({"after_battle": str(c)})
            if g.find_windows("^Save"):
                g.key("Escape")
                time.sleep(1.0)
            if os.environ.get("IC2_FREEZE_DIAG"):
                diag["freeze_diag"] = self.freeze_diag(name)
            self.emit(kind="save_timeout", before=name, error=str(e), screenshot=shot.name if shot.exists() else None, **diag)
            saved = self.g.save_as(f"{self.tag}-{name}-retry.SAV")
        dst = self.out / f"{name}.SAV"
        shutil.copy(saved, dst)
        if os.environ.get("IC2_LOG_RANDSEED"):
            # RandSeed after the checkpoint: what a resumed game writes back after loading this save.
            import struct
            self.emit(kind="randseed_after", checkpoint=name, value=struct.unpack("<I", self.g.mem(0x45E030, 4))[0])
        (self.out / "progress.json").write_text(json.dumps({"last_checkpoint": name, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}))
        self.state = load(dst)
        return self.state

    def freeze_diag(self, name):
        """At a frozen checkpoint (IC2_FREEZE_DIAG=1; seleucid turn 26, 2026-11-02): per-thread CPU over 3 s and kernel wait
        channel of the game's unix process, the X window tree, and winedbg's process list and backtraces of every thread. Written
        to <name>-freeze-*.txt beside the receipt; returns the file names."""
        from harness.driver import ENV, WINE
        out, files = self.out, []
        def save(tag, text):
            f = out / f"{name}-freeze-{tag}.txt"
            f.write_text(text)
            files.append(f.name)
        pid = self.g.pid
        def ticks():
            r = {}
            for d in Path(f"/proc/{pid}/task").iterdir():
                s = (d / "stat").read_text().rsplit(")", 1)[1].split()
                wchan = (d / "wchan").read_text() if (d / "wchan").exists() else ""
                r[d.name] = (int(s[11]) + int(s[12]), s[0], wchan)
            return r
        try:
            a = ticks(); time.sleep(3); b = ticks()
            save("cpu", "\n".join(f"tid {k} state {b[k][1]} wchan {b[k][2]} cpu_ticks_3s {b[k][0] - a.get(k, (b[k][0],))[0]}"
                                  for k in sorted(b, key=int)) + "\n")
        except Exception as x:
            save("cpu", f"error {x}\n")
        run = lambda args, t=90: subprocess.run(args, env=ENV, capture_output=True, text=True, timeout=t)
        try:
            save("xtree", run(["xwininfo", "-root", "-tree"]).stdout)
        except Exception as x:
            save("xtree", f"error {x}\n")
        try:
            procs = run([WINE, "winedbg", "--command", "info proc"]).stdout
            save("procs", procs)
            wpid = next((l.split()[0].lstrip("=") for l in procs.splitlines() if "Imperial Conquest" in l), None)
            if wpid:
                r1 = run([WINE, "winedbg", "--command", "bt all", "0x" + wpid], 120)
                save("bt-cmd", r1.stdout + "\n--- stderr\n" + r1.stderr)
                script = out / f"{name}-freeze-dbg.cmd"
                script.write_text(f"attach 0x{wpid}\ninfo thread\nbt all\ndetach\nquit\n")
                r2 = run([WINE, "winedbg", "--file", str(script)], 120)
                save("bt-file", r2.stdout + "\n--- stderr\n" + r2.stderr)
        except Exception as x:
            save("bt-error", f"error {x}\n")
        return files

    def act(self, a, name):
        """Perform one action on the current state, then checkpoint `name`. Returns (reply texts, error)."""
        if os.environ.get("IC2_LOG_RANDSEED"):
            # Delphi RandSeed (0x45E030) right before the action: lets one turn be replayed from its save by writing the seed
            # back after loading (seleucid turn-26 repro on native Windows, owner 2026-11-02).
            import struct
            self.emit(kind="randseed", before=name, op=a.get("op"), value=struct.unpack("<I", self.g.mem(0x45E030, 4))[0])
        try:
            texts, error = perform(self.g, a, self.state), None
        except GameOver as e:
            # The human overthrown or conquered: End of Game is modal, so File > Save cannot run. The turn's own autosave
            # (written before the window, when there is one) is the checkpoint; `game_over` tells the caller to stop.
            self.game_over = e.text
            texts, error = ([f"AUTOSAVE {e.autosave.split()[1]}"] if e.autosave else []) + [f"END OF GAME {e.text}"], None
            if e.autosave:
                dst = self.out / f"{name}.SAV"
                shutil.copy(G / e.autosave.split()[1], dst)
                self.state = load(dst)
            self.emit(kind="game_over", after=name, text=e.text, autosave=e.autosave)
            self.emit(kind="action", action=a, reply=texts, error=error, checkpoint=name if e.autosave else None,
                      date=self.state["date"])
            return texts, error
        except Exception as e:      # any failure of one order is recorded (an xdotool click once exited 1 mid-campaign)
            texts, error = [], f"{type(e).__name__}: {e}"
            try:
                # A refusal box shown instead of the expected dialog ("Split army did not open" for a one-unit army,
                # #230 split-one-unit): its text is the game's answer, kept as the reply.
                texts = self.g.dismiss_popups()
            except Exception:
                pass
        self.checkpoint(name)
        self.emit(kind="action", action=a, reply=texts, error=error, checkpoint=name, date=self.state["date"])
        return texts, error

    def close(self):
        self.emit(kind="done")
        self.receipt.close()
        self.g.kill()


def run(actions, start, out, seed, tag, log=print):
    """Play the actions from `start` in the original with startup seed `seed`; checkpoints, receipt.jsonl and
    progress.json go to `out`. `tag` makes the in-game save names unique to this run."""
    names = checkpoint_names(actions)
    s = OriginalSession(start, out, seed, tag, log)
    s.checkpoint(names[0])
    results = []
    for a, name in zip(actions, names[1:]):
        texts, error = s.act(a, name)
        results.append({"action": a, "reply": texts, "error": error})
        log(f"original: {name} {a['op']} -> {s.state['date']}{' ERROR ' + error if error else ''}")
    s.close()
    return results
