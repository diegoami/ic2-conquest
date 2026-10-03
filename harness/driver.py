"""Order driver: runs the original game headless (Wine + Xvfb) and issues orders.

Every order goes through the game's own UI (xdotool clicks on a 1280x1024
Xvfb screen). The driver *reads* the running game's memory through
/proc/<pid>/mem to aim clicks and to check that an order took effect; it
never writes game memory. The layouts it relies on are recorded in
coverage.md ("Dialog layouts").

    from harness.driver import Game
    g = Game(); g.start(); g.open("BASE.SAV", seed=12345)
    g.recruit("Rome", "hi", 3200); g.move(3, 104, 40); g.end_turn()
"""
import json
import os
import re
import shutil
import struct
import subprocess
import time
from pathlib import Path

WORK = Path(os.environ.get("IC2_WORK", Path.home() / "ic2-work"))
PREFIX = WORK / "prefix"
G = PREFIX / "drive_c" / "IC2"
WINE = "/usr/lib/wine/wine"
EXE = os.environ.get("IC2_EXE", "Imperial Conquest 2 fast rollingsave seed.exe")
DISPLAY = os.environ.get("DISPLAY_IC2", ":99")
ENV = dict(os.environ, DISPLAY=DISPLAY, WINEPREFIX=str(PREFIX), WINEDEBUG="-all", WINEARCH="win32")

# --- game memory (Delphi globals; same layouts as the save's tables) ---------
RAND_SEED = 0x45E030
MAP = 0x45E870                  # u16[320][140], column-major: cell(x, y) = MAP + (x*140 + y)*2
NATIONS = 0x474670              # 16 x 1172, the save's nation records
NATION_LEN = 1172
VIEW_Y, VIEW_X = 0x486, 0x488   # nation record: unit-map origin (top-left tile)
ARMIES = 0x47C1EC               # army records, 656 bytes each (the save's army table)
ARMY_LEN = 656
FLEETS = 0x49C26C               # fleet records, 26 bytes each (the save's fleet table, docs/sav-layout-notes.md §4)
FLEET_LEN = 0x1A
CUR_NATION = 0x4A0320
SEL_ARMY, SEL_FLEET = 0x4A0328, 0x4A032A
SEASON, WEEK, YEAR_BC = 0x4A032E, 0x4A0330, 0x4A0332
BATTLE_FLAG = 0x4A0B7C

# --- screen layout (1280x1024, the default window layout of a new game) ------
MENU = {"file": 14, "game": 45, "strategy": 97, "nations": 148, "area": 202, "unit": 259}
MENU_ITEM_Y = lambda i: 56 + 16 * i          # first item at y=56, 16 px apart
FILE_ITEMS = {"new": 0, "open": 1, "save": 2, "save_as": 3, "close": 4}
GAME_ITEMS = {"end_turn": 0, "new_player": 1, "new_nation": 2, "abdicate": 3}
STRATEGY_ITEMS = {"news": 0, "relations": 1, "taxation": 2, "balance": 3, "recruit": 4, "build_fleet": 5}
TOOLBAR = {"open": 12, "save": 35, "end_turn": 57, "news": 84, "relations": 107, "taxation": 129,
           "balance": 151, "recruit": 174, "build_fleet": 196}        # y = 58; nation icons follow
TOOLBAR_Y = 58
# The buttons are wider under some Wine builds, so the x above drifts and a
# click lands on the neighbour (a `recruit` click opens Balance sheet). Each
# button's tooltip is a named X window, so the positions are derived at run time
# by hovering the bar and reading the tooltip; see Game.calibrate_toolbar.
TOOLBAR_LABELS = {"open": "Open saved game", "save": "Save game position",
                  "end_turn": "End player's turn", "news": "News",
                  "relations": "International relations", "taxation": "Taxation",
                  "balance": "Balance sheet", "recruit": "Recruit unit",
                  "build_fleet": "Build fleet"}
TOOLBAR_CACHE = WORK / "toolbar.json"     # derived positions, per environment
# The army toolbar, in the unit map's top strip, visible only while an army is
# selected. Same drift, same tooltip derivation.
ARMY_TOOLBAR_LABELS = {"supply": "Supply army", "mercs": "Recruit mercenaries",
                       "transfer": "Transfer units", "split": "Split army",
                       "join": "Join armies", "change": "Change units",
                       "disband": "Disband army", "cancel": "Cancel selection"}
ARMY_TOOLBAR_Y = 108
# The fleet toolbar (same strip, y = 108), visible while a fleet is selected. Same derivation by tooltip.
FLEET_TOOLBAR_LABELS = {"supply": "Supply fleet", "repair": "Repair fleet", "transfer": "Transfer ships",
                        "split": "Split fleet", "join": "Join fleets", "scuttle": "Scuttle fleet",
                        "cancel": "Cancel selection"}
FLEET_TOOLS = {"supply": 346, "repair": 367, "transfer": 391, "split": 415, "join": 439, "scuttle": 463, "cancel": 493}
FLEET_TOOLBAR_CACHE = WORK / "fleet_toolbar.json"
ARMY_TOOLBAR_CACHE = WORK / "army_toolbar.json"
# The tactical battle's toolbar, in the battle window's top strip (y = 112).
BATTLE_TOOLBAR_LABELS = {"end_turn": "End turn", "computer": "Computer general on"}
BATTLE_TOOLBAR_Y = 112                                 # the toolbar row, window at (5,103)
BATTLE_TOOLS = {"end_turn": 114, "computer": 165}      # measured here; coverage.md had 110/158
BATTLE_TOOLBAR_CACHE = WORK / "battle_toolbar.json"
AREA_ORIGIN = (6, 126)          # area map: 1 px per tile; a click there puts that tile at view col 6, row 7
UNIT_PAINT = (337, 96)          # unit map paint box: tile (ox+c, oy+r) spans x0+32c.., y0+30+32r..
VIEW_COLS, VIEW_ROWS = 13, 13
NEUTRAL = (1000, 900)           # bare root window: a click there resets menu state harmlessly


class DriverError(RuntimeError):
    pass


def sh(*args, check=True):
    return subprocess.run(args, env=ENV, capture_output=True, text=True, check=check).stdout


class Game:
    def __init__(self, exe=EXE, log=print):
        self.exe, self.log, self.pid = exe, log, None
        self.toolbar_x = self._load_cache(TOOLBAR_CACHE)
        self.army_x = self._load_cache(ARMY_TOOLBAR_CACHE)
        self.battle_x = self._load_cache(BATTLE_TOOLBAR_CACHE)
        self.fleet_x = self._load_cache(FLEET_TOOLBAR_CACHE)

    # ---- process ---------------------------------------------------------
    def ensure_xvfb(self):
        if subprocess.run(["pgrep", "-x", "Xvfb"], capture_output=True).returncode:
            Path("/tmp/.X99-lock").unlink(missing_ok=True)
            subprocess.Popen(["setsid", "Xvfb", DISPLAY, "-screen", "0", "1280x1024x24"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)

    def kill(self):
        subprocess.run(["/usr/lib/wine/wineserver", "-k"], env=ENV, capture_output=True)
        time.sleep(1)
        self.pid = None

    def start(self):
        self.ensure_xvfb()
        self.kill()
        subprocess.Popen(["setsid", WINE, self.exe], cwd=G, env=ENV,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.wait(lambda: self.find_windows("^Imperial Conquest 2$"), 40, "main window")
        time.sleep(3)
        self.pid = int(subprocess.check_output(["pgrep", "-f", "^Imperial Conquest"]).split()[0])

    def wait(self, cond, timeout, what, step=0.5):
        t = time.time()
        while time.time() - t < timeout:
            r = cond()
            if r:
                return r
            time.sleep(step)
        raise DriverError("timeout waiting for " + what)

    # ---- memory (read only) ---------------------------------------------
    def mem(self, addr, n):
        with open(f"/proc/{self.pid}/mem", "rb") as f:
            f.seek(addr)
            return f.read(n)

    def i16(self, addr):
        return struct.unpack("<h", self.mem(addr, 2))[0]

    def in_battle(self):
        """The game's battle flag (byte 0x4A0B7C): 1 while a tactical battle is
        pending. A stale '<A> v <B>' window can linger after the battle is over,
        so this is the reliable signal."""
        return self.mem(BATTLE_FLAG, 1)[0] != 0

    def calendar(self):
        return {"season": self.i16(SEASON), "week": self.i16(WEEK), "year_bc": self.i16(YEAR_BC)}

    def turn_number(self):
        c = self.calendar()
        return (300 - c["year_bc"]) * 24 + c["season"] * 6 + (c["week"] - 1) // 2

    def nation_rec(self, n):
        return self.mem(NATIONS + n * NATION_LEN, NATION_LEN)

    def army_rec(self, i):
        return self.mem(ARMIES + i * ARMY_LEN, ARMY_LEN)

    def view_origin(self):
        n = self.i16(CUR_NATION)
        rec = self.nation_rec(n)
        return struct.unpack_from("<h", rec, VIEW_X)[0], struct.unpack_from("<h", rec, VIEW_Y)[0]

    def cell(self, x, y):
        return struct.unpack("<H", self.mem(MAP + (x * 140 + y) * 2, 2))[0]

    # ---- X ----------------------------------------------------------------
    def find_windows(self, pattern=".", visible=True):
        args = ["xdotool", "search"] + (["--onlyvisible"] if visible else []) + ["--name", pattern]
        out = []
        for w in sh(*args, check=False).split():
            name = sh("xdotool", "getwindowname", w, check=False).strip()
            geo = sh("xdotool", "getwindowgeometry", w, check=False)
            m = re.search(r"Position: (\d+),(\d+).*Geometry: (\d+)x(\d+)", geo, re.S)
            if m:
                out.append((int(w), name, *map(int, m.groups())))
        return out

    def click(self, x, y, pause=0.4):
        # hover first: menu items ignore a click that arrives with the move
        sh("xdotool", "mousemove", str(x), str(y))
        time.sleep(0.25)
        sh("xdotool", "click", "1")
        time.sleep(pause)

    def key(self, *keys):
        sh("xdotool", "key", *keys)
        time.sleep(0.3)

    def type(self, text):
        sh("xdotool", "type", "--delay", "30", text)

    def replace_field(self, text):
        # file dialogs pre-fill the last name with the caret at the start
        self.key("End")
        self.key("shift+Home")
        self.key("BackSpace")
        self.type(text)

    def shot(self, path, window="root"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        sh("import", "-window", window, str(path))

    def reset_ui(self):
        # close any open menu and leave menu-bar mode: a click on the menu
        # bar while it is armed would close the menu instead of opening it
        self.key("Escape")
        self.key("Escape")
        self.click(*NEUTRAL, pause=0.2)

    def _load_cache(self, path):
        try:
            return {k: int(v) for k, v in json.loads(path.read_text()).items()}
        except (OSError, ValueError):
            return {}

    def _save_cache(self, path, found, what, missed=()):
        """Cache a calibration only if every button was seen: a missed one carries
        the recorded fallback x, which must not be frozen into the cache."""
        if missed:
            self.log(f"{what}: not seen {list(missed)}, using recorded x, cache not written")
            return
        try:
            path.write_text(json.dumps(found, indent=1))
        except OSError:
            pass
        self.log(f"{what} calibrated: {found}")

    def _scan_bar(self, y, labels, x0, x1, pause):
        """Hover across a toolbar and return {name: centre x} from the tooltips,
        which Wine exposes as named X windows. A button the scan misses gets no
        entry, so the caller falls back to its recorded x."""
        seen = {label: [] for label in labels.values()}
        for x in range(x0, x1, 3):
            sh("xdotool", "mousemove", str(x), str(y))
            time.sleep(pause)
            names = {w[1] for w in self.find_windows(".")}
            for label in seen:
                if label in names:
                    seen[label].append(x)
        out = {}
        for name, label in labels.items():
            xs = seen[label]
            if xs:
                out[name] = (min(xs) + max(xs)) // 2
        return out

    def calibrate_toolbar(self, force=False):
        """The main toolbar's button x, derived from the tooltips (see _scan_bar)
        and cached in WORK/toolbar.json. The buttons are wider under some Wine
        builds, so the x in TOOLBAR (from coverage.md) drifts and a click lands on
        the neighbour. Falls back to TOOLBAR for a missed one."""
        if self.toolbar_x and not force:
            return self.toolbar_x
        found = self._scan_bar(TOOLBAR_Y, TOOLBAR_LABELS, 4, 232, 0.6)
        missed = [n for n in TOOLBAR_LABELS if n not in found]
        for name in missed:
            found[name] = TOOLBAR[name]
        self.toolbar_x = found
        self._save_cache(TOOLBAR_CACHE, found, "toolbar", missed)
        return found

    def calibrate_army_toolbar(self, force=False):
        """The army toolbar's button x, derived from the tooltips and cached in
        WORK/army_toolbar.json. Call it with an army selected, or the bar is not
        there to hover."""
        if self.army_x and not force:
            return self.army_x
        found = self._scan_bar(ARMY_TOOLBAR_Y, ARMY_TOOLBAR_LABELS, 336, 540, 0.5)
        missed = [n for n in ARMY_TOOLBAR_LABELS if n not in found]
        for name in missed:
            found[name] = self.ARMY_TOOLS[name]
        self.army_x = found
        self._save_cache(ARMY_TOOLBAR_CACHE, found, "army toolbar", missed)
        return found

    def calibrate_fleet_toolbar(self, force=False):
        """The fleet toolbar's button x, derived from the tooltips and cached in WORK/fleet_toolbar.json. Call it with
        a fleet selected. If a button was missed, the recorded x is used for it in memory and the disk cache is NOT written."""
        if self.fleet_x and not force:
            return self.fleet_x
        found = self._scan_bar(ARMY_TOOLBAR_Y, FLEET_TOOLBAR_LABELS, 336, 540, 0.5)
        missed = [n for n in FLEET_TOOLBAR_LABELS if n not in found]
        for name in missed:
            found[name] = FLEET_TOOLS[name]
        self.fleet_x = found
        self._save_cache(FLEET_TOOLBAR_CACHE, found, "fleet toolbar", missed)
        return found

    def calibrate_battle_toolbar(self, force=False):
        """The battle toolbar's button x, derived from the tooltips and cached in
        WORK/battle_toolbar.json. The battle window is raised and focused first so
        its tooltips win over the main window's."""
        if self.battle_x and not force:
            return self.battle_x
        w = self.find_windows(" v ")
        if w:
            sh("xdotool", "windowraise", str(w[0][0]), check=False)
            sh("xdotool", "windowfocus", str(w[0][0]), check=False)
            time.sleep(0.3)
        found = self._scan_bar(BATTLE_TOOLBAR_Y, BATTLE_TOOLBAR_LABELS, 5, 250, 0.6)
        missed = [n for n in BATTLE_TOOLBAR_LABELS if n not in found]
        for name in missed:
            found[name] = BATTLE_TOOLS[name]
        self.battle_x = found
        self._save_cache(BATTLE_TOOLBAR_CACHE, found, "battle toolbar", missed)
        return found

    def tool(self, name, pause=1.0):
        """Toolbar button: more reliable than the menus, which under Wine without a
        window manager sometimes ignore the item click after a dialog closed. The
        x is the one derived by calibrate_toolbar, falling back to coverage.md."""
        if not self.toolbar_x:
            self.calibrate_toolbar()
        self.reset_ui()
        self.click(self.toolbar_x.get(name, TOOLBAR[name]), TOOLBAR_Y, pause=pause)

    # ---- dialog controls (read from the running game) -----------------------
    def controls(self, title):
        """A dialog's controls as [{'cls','text','x','y','w','h'}, ...] in screen
        coordinates. Wine draws a dialog's controls itself (they are not X
        windows) and their positions depend on the font and DPI, so they are read
        from the running game with the win_controls helper, not hardcoded."""
        exe = WORK / "win_controls.exe"
        if not exe.exists():
            self.build_win_controls(exe)
        out = sh(WINE, str(exe), title, check=False)
        cs = []
        for line in out.splitlines():
            p = line.split("\t")
            if len(p) == 6:
                cls, text, x, y, w, h = p
                cs.append({"cls": cls, "text": text, "x": int(x), "y": int(y), "w": int(w), "h": int(h)})
        if not cs:
            raise DriverError("no controls found for window %r" % title)
        return cs

    def build_win_controls(self, exe):
        src = Path(__file__).resolve().parent / "win_controls.c"
        try:
            subprocess.run(["i686-w64-mingw32-gcc", "-O2", "-o", str(exe), str(src)], check=True)
        except (OSError, subprocess.CalledProcessError) as e:
            raise DriverError("win_controls.exe is missing and could not be built "
                              "(install gcc-mingw-w64-i686): %s" % e)

    def control(self, cs, text=None, cls=None, index=0):
        got = [c for c in cs if (text is None or c["text"] == text)
               and (cls is None or c["cls"] == cls)]
        if len(got) <= index:
            raise DriverError("control not found: text=%r class=%r" % (text, cls))
        return got[index]

    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        self.click(c["x"] + int(c["w"] * fx), c["y"] + int(c["h"] * fy), pause=pause)

    def close_controls(self, title, cs, text="OK", pause=1.0):
        self.click_control(self.control(cs, text=text), pause=pause)
        self.wait(lambda: not self.find_windows("^%s$" % re.escape(title)), 10, title + " closed")

    def menu(self, name, item):
        self.reset_ui()
        self.click(MENU[name], 36, pause=0.8)
        self.click(MENU[name] + 20, MENU_ITEM_Y(item), pause=1.2)

    # ---- dialogs ------------------------------------------------------------
    def popups(self):
        """Small modal message boxes (news, offers, refusals): anything that is not
        one of the four permanent windows."""
        keep = {"Area map", "Unit map"}
        out = []
        for w in self.find_windows():
            wid, name, x, y, wd, ht = w
            if name in keep or name.startswith("Imperial Conquest 2") or wd <= 1:
                continue
            if name == "Information" and ht > 600:      # the permanent Information panel
                continue
            out.append(w)
        return out

    def read_popup(self, w):
        wid, name, x, y, wd, ht = w
        png = WORK / "shots" / "_popup.png"
        self.shot(png, window=str(wid))
        txt = subprocess.run(["tesseract", str(png), "-", "--psm", "6"], capture_output=True, text=True).stdout
        return " ".join(txt.split())

    def answer(self, title, yes=True):
        """Press Yes (or No) on a <title> confirmation dialog. Its buttons are
        Yes / No / Cancel, not the bottom-centre OK that dismiss_popups clicks."""
        cs = self.controls(title)
        want = "yes" if yes else "no"
        c = next((c for c in cs if want in c["text"].lower()), None)
        if c is None and yes:              # a refusal ("The army is too large for this fleet ?") has OK only; OK
            c = next((c for c in cs if c["text"].replace("&", "").lower() == "ok"), None)   # is never "No"
        if c is None:
            raise DriverError("%s: no %s button" % (title, want))
        self.click_control(c, pause=0.8)
        return True

    def _refuse_confirm(self):
        """Strict mode: if a Confirm box is open, answer it No and raise (dismiss_popups(strict=True) does both); other boxes are left alone."""
        if any(p[1] == "Confirm" and p[4] < 600 and p[5] < 300 for p in self.popups()):      # the box set dismiss_popups acts on
            self.dismiss_popups(strict=True)

    def dismiss_popups(self, max_n=10, strict=False):
        """Press OK on message boxes; return their texts (OCR). A Confirm box is
        a Yes/No/Cancel dialog and is answered Yes (the driver only calls this
        after the action it asked for). With `strict` a Confirm box is answered No instead, checked to be
        closed, and DriverError("end turn: unexpected Confirm: <text>") is raised (used by `end_turn(strict_confirm=True)`)."""
        texts = []
        for _ in range(max_n):
            ps = [p for p in self.popups() if p[1] in ("Information", "Confirm", "Warning", "Error", "")
                  and p[4] < 600 and p[5] < 300]
            if not ps:
                break
            wid, name = ps[0][0], ps[0][1]
            texts.append(self.read_popup(ps[0]))
            if name == "Confirm" and strict:
                for _ in range(3):      # the first click into an inactive window may only activate it
                    try:
                        self.answer("Confirm", yes=False)
                    except DriverError:     # an OK-only box has no No button: say so in the documented message, never press OK
                        raise DriverError("end turn: unexpected Confirm: " + texts[-1] + " (no No button)")
                    if wid not in [p[0] for p in self.popups()]:
                        break
                if wid in [p[0] for p in self.popups()]:
                    raise DriverError("end turn: unexpected Confirm: " + texts[-1] + " (still open after No)")
                raise DriverError("end turn: unexpected Confirm: " + texts[-1])
            if name == "Confirm":
                self.answer("Confirm", yes=True)
                if wid in [p[0] for p in self.popups()]:
                    self.answer("Confirm", yes=True)
            else:
                x, y, wd, ht = ps[0][2], ps[0][3], ps[0][4], ps[0][5]
                for _ in range(3):  # no window manager: the first click only activates the box
                    self.click(x + wd // 2, y + ht - 24, pause=0.6)     # OK, bottom centre
                    if wid not in [p[0] for p in self.popups()]:
                        break
        return texts

    def close_dialog(self, title, ok_xy, tries=3):
        """Press a dialog's OK until its window is gone (the first click into an
        inactive window may only activate it)."""
        for _ in range(tries):
            w = self.find_windows("^%s$" % re.escape(title))
            if not w:
                return True
            self.raise_window(w[0][0])
            self.click(*ok_xy, pause=1.0)
        if self.find_windows("^%s$" % re.escape(title)):
            raise DriverError(title + " did not close")
        return True

    def raise_window(self, wid):
        # no window manager: a click on the main window can bury a modal dialog
        sh("xdotool", "windowraise", str(wid), check=False)
        time.sleep(0.3)

    def open_dialog(self, title, xy, tries=3):
        for _ in range(tries):
            self.click(*xy, pause=1.2)
            if self.find_windows("^%s$" % re.escape(title)):
                return
        raise DriverError(title + " did not open")

    # ---- file -------------------------------------------------------------
    def set_seed(self, seed):
        seedfile = G / "SEED.TXT"
        if seed is None:
            seedfile.unlink(missing_ok=True)
        else:
            seedfile.write_text(str(seed))

    def load(self, save, seed=None):
        """Restart the game with RandSeed = seed (None: the clock), then open the
        save. The seed is read at program start only: File > Open does not
        reseed, so a fresh process is what makes a turn repeatable."""
        self.set_seed(seed)
        n = self.seedlog_lines()
        self.start()
        self.wait(lambda: self.seedlog_lines() > n, 20, "SEED.LOG line at start")
        self.seed_line = (G / "SEED.LOG").read_text().splitlines()[-1].strip()
        return self.open(save)

    NEWGAME_TICK = (117, 117, 21.67)     # x, y of Rome's "human" checkbox, row pitch (measured on the 16-row form)

    def new_game(self, row=0, seed=None, rows=None):
        """File > New with the given human nation(s). `row` is a row of the nation list (0 = Rome ... 15 = Thracia); `rows`
        (or a list passed as `row`) is a list of rows for several human seats (not tested in this branch; the
        T0 spike in `runs/experiments/two-humans` uses it and checks the autosave's human flags). The form has 16 rows 21.67 px
        apart: the old `(109, 114 + 20 * row)` was off by 8 px in x and, by Thracia (row 15), about 28 px in y (414 against 442).
        The autosave hook fires at new-game start: returns `(path of AUTO0720.SAV, popup texts)`."""
        self.set_seed(seed)
        for f in G.glob("AUTO*"):
            f.unlink()
        self.start()
        self.seed_line = (G / "SEED.LOG").read_text().splitlines()[-1].strip() if (G / "SEED.LOG").exists() else ""
        self.menu("file", FILE_ITEMS["new"])
        self.wait(lambda: self.find_windows("^Imperial Conquest 2$"), 10, "new game form")
        x0, y0, pitch = self.NEWGAME_TICK
        for r in (list(rows) if rows is not None else [row] if isinstance(row, int) else list(row)):
            self.click(x0, round(y0 + pitch * r), pause=0.5)       # the nation's "human" tick
        self.click(344, 194)                                  # OK
        self.wait(lambda: (G / "AUTOSAVE.LOG").exists(), 120, "new-game autosave")
        time.sleep(3)
        texts = self.dismiss_popups()
        line = (G / "AUTOSAVE.LOG").read_text().splitlines()[-1]
        return G / line.split()[1], texts

    def open(self, save):
        """File > Open (the save is copied into the game folder first)."""
        src = Path(save)
        if src.parent.resolve() != G.resolve():
            shutil.copy(src, G / src.name)
        self.menu("file", FILE_ITEMS["open"])
        self.click(636, 450)
        self.replace_field(src.name)
        self.key("Return")
        self.wait(lambda: self.find_windows("turn"), 30, "game window after load")
        time.sleep(3)
        return self.dismiss_popups()

    def seedlog_lines(self):
        p = G / "SEED.LOG"
        return len(p.read_text().splitlines()) if p.exists() else 0

    def save_as(self, name):
        target = G / name
        target.unlink(missing_ok=True)
        self.menu("file", FILE_ITEMS["save_as"])
        self.replace_field(name)
        self.key("Return")
        self.wait(lambda: target.exists() and target.stat().st_size > 100000, 20, "save " + name)
        time.sleep(0.5)
        return target

    # ---- map targeting ------------------------------------------------------
    def show(self, x, y):
        """Bring tile (x, y) into the unit map; return its screen centre."""
        ox, oy = self.view_origin()
        if not (ox <= x < ox + VIEW_COLS and oy <= y < oy + VIEW_ROWS - 1):
            self.reset_ui()
            self.click(AREA_ORIGIN[0] + x, AREA_ORIGIN[1] + y, pause=0.8)
            ox, oy = self.view_origin()
        c, r = x - ox, y - oy
        if not (0 <= c < VIEW_COLS and 0 <= r < VIEW_ROWS):
            raise DriverError(f"tile {x},{y} not visible from origin {ox},{oy}")
        return UNIT_PAINT[0] + 32 * c + 16, UNIT_PAINT[1] + 30 + 32 * r + 16

    def click_tile(self, x, y, pause=0.8):
        self.click(*self.show(x, y), pause=pause)

    # ---- orders -------------------------------------------------------------
    def select_army(self, i, x, y):
        for _ in range(3):       # the first click into an inactive window may only activate it
            self.click_tile(x, y)
            if self.i16(SEL_ARMY) == i:
                break
        if self.i16(SEL_ARMY) != i:
            raise DriverError(f"army {i} at {x},{y} not selected (selected {self.i16(SEL_ARMY)})")

    def army_pos(self, i):
        return struct.unpack_from("<2h", self.army_rec(i), 0)

    def fleet_rec(self, i):
        return self.mem(FLEETS + i * FLEET_LEN, FLEET_LEN)

    def fleet_pos(self, i):
        return struct.unpack_from("<2h", self.fleet_rec(i), 0)

    def fleet_state(self, i):
        """A fleet record read from the game's memory (the save's 26 bytes: x, y, owner +8, countdown +10, moves +12,
        supplies +14, money +16, ships +18, condition +20, carried army +22). An owner of -1 is a destroyed fleet."""
        r = self.fleet_rec(i)
        x, y = struct.unpack_from("<2h", r, 0)
        owner, countdown, moves, supplies, money, ships, cond, army = struct.unpack_from("<8h", r, 8)
        return {"id": i, "x": x, "y": y, "owner": owner, "moves": moves, "supplies": supplies, "money": money,
                "ships": ships, "condition": cond, "army": army}

    def fleet_moves(self, i):
        return struct.unpack_from("<h", self.fleet_rec(i), 12)[0]

    def select_fleet(self, i, x=None, y=None):
        """Select fleet i by clicking its marker (`SEL_FLEET` = i; fleets are markers 300-347 on the unit map)."""
        if x is None:
            x, y = self.fleet_pos(i)
        for _ in range(3):       # the first click into an inactive window may only activate it
            self.click_tile(x, y)
            if self.i16(SEL_FLEET) == i:
                return
        raise DriverError(f"fleet {i} at {x},{y} not selected (selected {self.i16(SEL_FLEET)})")

    def move_fleet(self, i, x, y):
        """Select fleet i and click a sea tile (a click on sea with a fleet selected is a fleet move)."""
        self.select_fleet(i)
        self.click_tile(x, y, pause=1.2)
        texts = self.dismiss_popups()
        return self.fleet_pos(i), texts

    def move(self, i, x, y):
        """Select army i and click the destination tile (one click issues the whole
        Bresenham walk). Returns (new position, popup texts)."""
        ax, ay = self.army_pos(i)
        self.select_army(i, ax, ay)
        self.click_tile(x, y, pause=1.0)
        texts = self.dismiss_popups()
        return self.army_pos(i), texts

    def attack(self, i, x, y):
        """Select army i, then click an adjacent enemy army or city at (x, y). A
        city is a siege (no screen); an army opens the tactical battle, which is
        played with Computer general."""
        ax, ay = self.army_pos(i)
        if max(abs(ax - x), abs(ay - y)) != 1:
            raise DriverError(f"target {x},{y} not adjacent to army {i} at {ax},{ay}")
        self.select_army(i, ax, ay)
        self.click_tile(x, y, pause=1.5)
        texts = self.dismiss_popups()
        # The battle window takes a few seconds to open after the click, and the
        # Computer general toggle must be on during placement, so wait for it.
        for _ in range(30):
            if self.in_battle() and self.find_windows(" v "):
                break
            time.sleep(0.5)
        if self.in_battle() and self.find_windows(" v "):
            texts.append("BATTLE " + self.find_windows(" v ")[0][1])
            self.play_battle()
            texts += self.dismiss_popups()
        return texts

    def open_recruit(self):
        self.tool("recruit")
        self.wait(lambda: self.find_windows("^Army recruits$"), 10, "Army recruits dialog")

    def recruit(self, city_row, unit_type, thousands=0, hundreds=0):
        """Recruit dialog: pick the city (row in its list), the type, then press the
        1000s/100s arrows. The controls are read from the dialog, so the clicks do
        not depend on the environment's font metrics. The size is checked on the
        save diff."""
        TYPES = {"li": "Light infantry", "hi": "Heavy infantry", "ar": "Archers",
                 "lc": "Light cavalry", "hc": "Heavy cavalry"}
        self.open_recruit()
        cs = self.controls("Army recruits")
        cities = self.control(cs, cls="TListBox", index=0)
        self.click(cities["x"] + cities["w"] // 2, cities["y"] + 12 + 12 * city_row, pause=0.6)
        self.click_control(self.control(cs, text=TYPES[unit_type]), pause=0.6)
        spins = sorted((c for c in cs if c["cls"] == "TUpDown"), key=lambda c: c["x"])
        for _ in range(hundreds):
            self.click_control(spins[0], fy=0.25, pause=0.2)
        for _ in range(thousands):
            self.click_control(spins[-1], fy=0.25, pause=0.2)
        self.click_control(self.control(cs, text="Recruit unit"), pause=0.8)
        texts = self.dismiss_popups()
        self.close_controls("Army recruits", cs)
        return texts

    def disband_unit(self, city_row, unit_row):
        """Army recruits: pick the city, select a queued unit, Disband. Controls
        are read from the dialog."""
        self.open_recruit()
        cs = self.controls("Army recruits")
        cities = self.control(cs, cls="TListBox", index=0)
        units = self.control(cs, cls="TListBox", index=1)
        self.click(cities["x"] + cities["w"] // 2, cities["y"] + 12 + 12 * city_row, pause=0.6)
        self.click(units["x"] + units["w"] // 2, units["y"] + 12 + 12 * unit_row, pause=0.4)
        self.click_control(self.control(cs, text="Disband"), pause=1.0)
        texts = self.dismiss_popups()
        self.close_controls("Army recruits", cs)
        return texts

    # ---- army toolbar (appears in the unit map's top strip, y = 108) ---------
    ARMY_TOOLS = {"supply": 349, "mercs": 372, "transfer": 397, "split": 421, "join": 445,
                  "change": 468, "disband": 493, "cancel": 519}
    CITY_TOOLS = {"fortify": 349, "cancel": 372}

    def army_tool(self, i, tool, title):
        ax, ay = self.army_pos(i)
        self.select_army(i, ax, ay)
        if not self.army_x:
            self.calibrate_army_toolbar()
        self.open_dialog(title, (self.army_x.get(tool, self.ARMY_TOOLS[tool]), ARMY_TOOLBAR_Y))
        w = self.find_windows("^%s$" % re.escape(title))[0]
        self.raise_window(w[0])
        return w

    def join(self, i):
        """Select army i and press Join armies, combining it with an adjacent
        friendly army. The game keeps one of the two; the save diff shows which,
        and the combined units."""
        ax, ay = self.army_pos(i)
        self.select_army(i, ax, ay)
        if not self.army_x:
            self.calibrate_army_toolbar()
        self.click(self.army_x.get("join", self.ARMY_TOOLS["join"]), ARMY_TOOLBAR_Y, pause=1.5)
        return self.dismiss_popups()

    def disband_army(self, i):
        """Select army i and press Disband army, answering the Confirm. The army
        must be near one of its own cities."""
        ax, ay = self.army_pos(i)
        self.select_army(i, ax, ay)
        if not self.army_x:
            self.calibrate_army_toolbar()
        self.click(self.army_x.get("disband", self.ARMY_TOOLS["disband"]), ARMY_TOOLBAR_Y, pause=1.5)
        return self.dismiss_popups()

    def split_army(self, i, unit_rows=(0,)):
        """Select army i and split the given unit rows (indices in its unit list)
        into a new army. One observation (from (100,37)): the new army appeared at (101,38),
        diagonally adjacent, not on the same tile; the rule is not established
        (findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md)."""
        ax, ay = self.army_pos(i)
        self.select_army(i, ax, ay)
        if not self.army_x:
            self.calibrate_army_toolbar()
        self.open_dialog("Split army", (self.army_x["split"], ARMY_TOOLBAR_Y))
        cs = self.controls("Split army")
        left = self.control(cs, cls="TListBox", index=0)
        transfer = sorted((c for c in cs if c["text"] == "Transfer"), key=lambda c: c["x"])[0]
        for r in unit_rows:
            self.click(left["x"] + left["w"] // 2, left["y"] + 12 + 12 * r, pause=0.4)
            self.click_control(transfer, pause=0.6)
        self.click_control(self.control(cs, text="OK"), pause=1.5)
        return self.dismiss_popups()

    def transfer_units(self, i, unit_row):
        """Transfer a unit from army i to an adjacent friendly army. Opens the
        Army to army transfer dialog (same layout as Split army)."""
        ax, ay = self.army_pos(i)
        self.select_army(i, ax, ay)
        if not self.army_x:
            self.calibrate_army_toolbar()
        self.open_dialog("Army to army transfer", (self.army_x["transfer"], ARMY_TOOLBAR_Y))
        cs = self.controls("Army to army transfer")
        src = sorted((c for c in cs if c["cls"] == "TListBox"), key=lambda c: c["x"])[0]
        transfer = sorted((c for c in cs if c["text"] == "Transfer"), key=lambda c: c["x"])[0]
        self.click(src["x"] + src["w"] // 2, src["y"] + 12 + 12 * unit_row, pause=0.4)
        self.click_control(transfer, pause=0.6)
        self.click_control(self.control(cs, text="OK"), pause=1.5)
        return self.dismiss_popups()

    def change_units_disband(self, i, unit_row):
        """Change units: select a unit in army i and Disband it."""
        ax, ay = self.army_pos(i)
        self.select_army(i, ax, ay)
        if not self.army_x:
            self.calibrate_army_toolbar()
        self.open_dialog("Change units", (self.army_x["change"], ARMY_TOOLBAR_Y))
        cs = self.controls("Change units")
        lst = self.control(cs, cls="TListBox")
        self.click(lst["x"] + lst["w"] // 2, lst["y"] + 12 + 12 * unit_row, pause=0.5)
        self.click_control(self.control(cs, text="Disband"), pause=0.8)
        texts = self.dismiss_popups()
        self._close_change_units(cs)
        return texts

    def _change_units(self, i, unit_rows, button):
        """Open Change units for army i, select the unit rows (ctrl for more than
        one) and press `button`. Returns the dialog's controls."""
        ax, ay = self.army_pos(i)
        self.select_army(i, ax, ay)
        if not self.army_x:
            self.calibrate_army_toolbar()
        self.open_dialog("Change units", (self.army_x["change"], ARMY_TOOLBAR_Y))
        cs = self.controls("Change units")
        lst = self.control(cs, cls="TListBox")
        for k, r in enumerate(unit_rows):
            if k:
                sh("xdotool", "keydown", "ctrl")
            self.click(lst["x"] + lst["w"] // 2, lst["y"] + 12 + 12 * r, pause=0.4)
            if k:
                sh("xdotool", "keyup", "ctrl")
        self.click_control(self.control(cs, text=button), pause=1.2)
        return cs

    def _ok_until_closed(self, title, cs, pause=1.2):
        """Press OK until the `title` dialog is gone. A click into an inactive
        window may only activate it, so try, then retry twice; raise if it stays."""
        for _ in range(3):
            self.click_control(self.control(cs, text="OK"), pause=pause)
            if not self.find_windows("^%s$" % re.escape(title)):
                return
        raise DriverError("%s did not close after OK" % title)

    def _close_change_units(self, cs):
        self._ok_until_closed("Change units", cs, pause=1.5)

    def rename_unit(self, i, unit_row, name):
        """Change units: select a unit in army i, Rename unit, type the name."""
        cs = self._change_units(i, [unit_row], "Rename unit")
        rc = self.controls("Rename unit")
        edit = self.control(rc, cls="TEdit")
        self.click_control(edit, pause=0.4)
        self.key("End")                 # the box is pre-filled and ctrl+a does not select it
        sh("xdotool", "key", "--repeat", "30", "BackSpace")
        sh("xdotool", "type", "--delay", "60", name)
        self._ok_until_closed("Rename unit", rc)
        texts = self.dismiss_popups()
        self._close_change_units(cs)
        return texts

    def split_unit(self, i, unit_row, hundreds=0):
        """Change units: split a unit (the game refuses a small one: "too small
        to split"). The dialog starts at half and half; each 100s arrow press
        moves 100 troops from the new unit to the original (negative presses
        down), so the new unit ends at half - 100*hundreds."""
        cs = self._change_units(i, [unit_row], "Split unit")
        texts = self.dismiss_popups() if not self.find_windows("^Split unit$") else []
        if not texts and not self.find_windows("^Split unit$"):
            raise DriverError("Split unit: neither the dialog nor a refusal appeared")
        if self.find_windows("^Split unit$"):
            sc = self.controls("Split unit")
            spin = sorted((c for c in sc if c["cls"] == "TUpDown"), key=lambda c: c["x"])[0]
            for _ in range(abs(hundreds)):
                self.click_control(spin, fy=0.25 if hundreds > 0 else 0.75, pause=0.2)
            self._ok_until_closed("Split unit", sc)
            texts += self.dismiss_popups()
        self._close_change_units(cs)
        return texts

    def join_units(self, i, unit_rows):
        """Change units: select two or more units of the same type (ctrl-click)
        and Join units."""
        cs = self._change_units(i, unit_rows, "Join units")
        texts = self.dismiss_popups()
        self._close_change_units(cs)
        return texts

    # ---- fleets (the fleet toolbar appears in the same strip as the army's, y = 108) ----------------------
    def embark(self, army, fleet):
        """Select the army and click the adjacent own fleet: the army goes aboard (its cell becomes -1 and the fleet's
        carried-army field its index) and both units' moves become 0. Refused ("The army is too large for this
        fleet ?") when troops > ships x 500; the refusal box has OK only and the click selects the fleet."""
        ax, ay = self.army_pos(army)
        fx, fy = self.fleet_pos(fleet)
        if max(abs(ax - fx), abs(ay - fy)) != 1:
            raise DriverError(f"fleet {fleet} at {fx},{fy} not adjacent to army {army} at {ax},{ay}")
        self.select_army(army, ax, ay)
        self.click_tile(fx, fy, pause=1.5)
        return self.dismiss_popups()

    def attack_fleet(self, own, enemy, answer=None):
        """Select own fleet, click the adjacent enemy fleet. AT WAR (the tested case: 50 battles) the battle is instant, with no
        window and no box; its effect is verified from the two fleet records (a destroyed fleet has owner -1 and a winner's
        ships or condition fall) and the click is retried at most twice if nothing changed; the news line ("X sinks fleet of
        Y.") is in the next autosave. AT PEACE (tested on trade terms, `findings/2026-10-03-fleet-peace-prompt.md`) the click asks "Are you sure you want to attack this
        fleet ?" (Yes, No, Cancel; No and Cancel change nothing; Yes declares war on the target and its ally and the battle follows at
        once); with `answer` None a box is only read and left open, with True/False it is answered. Returns the texts of any box seen."""
        ox, oy = self.fleet_pos(own)
        ex, ey = self.fleet_pos(enemy)
        if max(abs(ox - ex), abs(oy - ey)) != 1:
            raise DriverError(f"fleet {enemy} at {ex},{ey} not adjacent to fleet {own} at {ox},{oy}")
        self.dismiss_popups()       # a stale news/offer box would be mistaken for the click's effect below
        before = (self.fleet_state(own), self.fleet_state(enemy))
        texts = []
        for _ in range(3):          # verify the click's effect; retry at most twice
            self.select_fleet(own, ox, oy)
            self.click_tile(ex, ey, pause=1.5)
            if self.in_battle() or self.find_windows(" v "):
                # A tactical screen (not seen for fleets at war: the battle is instant): play it as Game.attack does, and stop.
                self.play_battle()
                return [self.read_popup(w) for w in self.popups()] + ["BATTLE screen played (Computer general)"]
            texts = [self.read_popup(w) for w in self.popups() if w[1] in ("Confirm", "Information", "Warning", "Error")]
            if texts:               # a box (the untested peace prompt, or a refusal) is the effect: do not click again
                break
            time.sleep(1.0)
            if (self.fleet_state(own), self.fleet_state(enemy)) != before:
                break
        else:
            raise DriverError(f"attacking fleet {enemy} with fleet {own} changed nothing (no box, both fleet records unchanged)")
        if answer is not None and self.find_windows("^Confirm$"):
            self.answer("Confirm", yes=answer)
            time.sleep(1.5)
            texts += self.dismiss_popups()
        elif answer is not None:
            texts += self.dismiss_popups()
        return texts

    def disembark(self, fleet, x, y):
        """Select the fleet and click an adjacent land tile: the carried army lands there. Needs moves on both."""
        fx, fy = self.fleet_pos(fleet)
        if max(abs(fx - x), abs(fy - y)) != 1:
            raise DriverError(f"tile {x},{y} not adjacent to fleet {fleet} at {fx},{fy}")
        self.select_fleet(fleet)
        self.click_tile(x, y, pause=1.5)
        return self.dismiss_popups()

    def fleet_tool(self, i, tool, title=None):
        """Select fleet i and press a fleet-toolbar button (x derived from the tooltips). With a title, wait for
        that dialog and return its window; a button with nothing to act on shows a message or nothing."""
        self.select_fleet(i)
        if not self.fleet_x:
            self.calibrate_fleet_toolbar()
        x = self.fleet_x.get(tool, FLEET_TOOLS[tool])
        if title is None:
            self.click(x, ARMY_TOOLBAR_Y, pause=1.5)
            return None
        self.open_dialog(title, (x, ARMY_TOOLBAR_Y))
        w = self.find_windows("^%s$" % re.escape(title))[0]
        self.raise_window(w[0])
        return w

    def _spin(self, ups, presses, fy=0.25):
        for _ in range(presses):
            self.click_control(ups, fy=fy, pause=0.2)

    def supply_fleet(self, i, tons=0, money=0):
        """Supply fleet (an own city or fleet next to it is the provider): the 10s/100s arrows move tons from the
        provider, the lower pair moves money from the treasury. Capped by the provider's stock."""
        self.fleet_tool(i, "supply", "Supply fleet")
        cs = self.controls("Supply fleet")
        ups = [c for c in cs if c["cls"] == "TUpDown"]
        mid = (min(c["y"] for c in ups) + max(c["y"] for c in ups)) / 2     # the tons pair above, the money pair below
        top = sorted((c for c in ups if c["y"] < mid), key=lambda c: c["x"])
        bottom = sorted((c for c in ups if c["y"] >= mid), key=lambda c: c["x"])
        self._spin(top[1], tons // 100)
        self._spin(top[0], (tons % 100) // 10)
        self._spin(bottom[1], money // 100)
        self._spin(bottom[0], (money % 100) // 10)
        self._ok_until_closed("Supply fleet", cs)
        return self.dismiss_popups()

    def repair_fleet(self, i, points):
        """Repair fleet (only at one of your own cities; the fleet's moves become 0): 1s/10s arrows raise the state of
        repair; the cost is ships x points / 5 talents."""
        self.fleet_tool(i, "repair", "Repair fleet")
        cs = self.controls("Repair fleet")
        ups = sorted((c for c in cs if c["cls"] == "TUpDown"), key=lambda c: c["x"])
        self._spin(ups[1], points // 10)
        self._spin(ups[0], points % 10)
        self._ok_until_closed("Repair fleet", cs)
        return self.dismiss_popups()

    def scuttle_fleet(self, i, yes=True):
        """Scuttle fleet: next to one of your cities, not carrying an army; answered through its Confirm."""
        self.fleet_tool(i, "scuttle")
        texts = []
        if self.find_windows("^Confirm$"):
            texts.append(self.read_popup(self.find_windows("^Confirm$")[0]))
            self.answer("Confirm", yes=yes)
        return texts + self.dismiss_popups()

    def split_fleet(self, i, ships):
        """Split fleet (at least 20 ships, no army aboard): the DOWN arrows (1s/10s) move ships from the first fleet to
        the second (30/0 -> 20/10); the up arrows move them back. Supply and money rows are left at 0."""
        self.fleet_tool(i, "split", "Split fleet")
        cs = self.controls("Split fleet")
        ups = [c for c in cs if c["cls"] == "TUpDown"]
        row = sorted((c for c in ups if c["y"] == min(u["y"] for u in ups) or abs(c["y"] - min(u["y"] for u in ups)) < 10),
                     key=lambda c: c["x"])
        self._spin(row[1], ships // 10, fy=0.75)       # the DOWN arrows move ships to the second fleet
        self._spin(row[0], ships % 10, fy=0.75)
        self._ok_until_closed("Split fleet", cs)
        return self.dismiss_popups()

    def join_fleets(self, i):
        """Join fleets: no dialog; fleet i and the adjacent own fleet become one (ships add up, fewer than 100 combined,
        neither carrying an army) and the joined fleet's moves become 0."""
        self.fleet_tool(i, "join")
        return self.dismiss_popups()

    def transfer_ships(self, i, ships):
        """Transfer ships ("Fleet to fleet transfer", the layout of Split fleet) between fleet i and the adjacent own
        fleet: a positive `ships` moves that many from the first to the second (down arrows), a negative one back."""
        self.fleet_tool(i, "transfer", "Fleet to fleet transfer")
        cs = self.controls("Fleet to fleet transfer")
        ups = [c for c in cs if c["cls"] == "TUpDown"]
        top = min(u["y"] for u in ups)
        row = sorted((c for c in ups if abs(c["y"] - top) < 10), key=lambda c: c["x"])
        n, fy = abs(ships), (0.75 if ships > 0 else 0.25)
        self._spin(row[1], n // 10, fy=fy)
        self._spin(row[0], n % 10, fy=fy)
        self._ok_until_closed("Fleet to fleet transfer", cs)
        return self.dismiss_popups()

    def supply(self, i, tons=None, money_100s=0):
        """Supply army dialog (window 470x335 at 23,49): the 10s arrows move
        supplies from the adjacent provider (city) to the army, capped by the
        game at troops div 100 + 1 and the city's stock; the money arrows move
        talents between the treasury and the army's purse (100s: +/-100)."""
        rec = self.army_rec(i)
        troops = sum(struct.unpack_from("<h", rec, 16 + 32 * k + 4)[0] for k in range(20)
                     if struct.unpack_from("<h", rec, 16 + 32 * k + 4)[0] > 0)
        have = struct.unpack_from("<h", rec, 10)[0]
        want = troops // 100 + 1 - have if tons is None else tons
        self.army_tool(i, "supply", "Supply army")
        for _ in range(max(0, (want + 9) // 10)):
            self.click(169, 94, pause=0.15)             # 10s up: city -> army
        for _ in range(abs(money_100s)):
            self.click(261, 272 if money_100s > 0 else 290, pause=0.15)
        texts = self.dismiss_popups()
        self.close_dialog("Supply army", (239, 337))
        return struct.unpack_from("<h", self.army_rec(i), 10)[0] - have, texts

    def hire_mercs(self, i, rows=(0,)):
        """Recruit mercenary unit dialog (490x165 at 23,49): the offers of the
        adjacent city; pick a row, Recruit unit, OK. The button does nothing (no
        dialog) when no live offer is adjacent."""
        before = len([k for k in range(20) if struct.unpack_from("<h", self.army_rec(i), 16 + 32 * k + 4)[0] > 0])
        try:
            self.army_tool(i, "mercs", "Recruit mercenary unit")
        except DriverError:
            return 0, ["no mercenary offer adjacent"]
        texts = []
        for r in sorted(rows, reverse=True):          # hired rows leave the list: go bottom-up
            self.click(103, 86 + 12 * r, pause=0.5)
            self.click(410, 104, pause=1.0)
            texts += [t for t in self.dismiss_popups()]
        self.close_dialog("Recruit mercenary unit", (248, 174))
        after = len([k for k in range(20) if struct.unpack_from("<h", self.army_rec(i), 16 + 32 * k + 4)[0] > 0])
        return after - before, texts

    def fortify(self, city, x, y, points):
        """Select an own city, city toolbar Fortify, 1s ▲ points times, OK
        (dialog "Fortify <city>", 365x125 at 23,49)."""
        self.reset_ui()
        self.click(self.ARMY_TOOLS["cancel"], 108, pause=0.5)
        self.click_tile(x, y, pause=1.0)
        title = "Fortify " + city
        self.open_dialog(title, (self.CITY_TOOLS["fortify"], 108))
        self.raise_window(self.find_windows("^%s$" % re.escape(title))[0][0])
        for _ in range(points % 10):
            self.click(136, 86, pause=0.15)
        for _ in range(points // 10):
            self.click(168, 86, pause=0.15)
        texts = self.dismiss_popups()
        self.close_dialog(title, (123, 143))
        return texts

    def mobilize(self, city_row, unit_rows):
        """Army recruits: pick the city, click each unit row (ctrl for more than
        one), Mobilize. The controls are read from the dialog."""
        self.open_recruit()
        cs = self.controls("Army recruits")
        cities = self.control(cs, cls="TListBox", index=0)
        units = self.control(cs, cls="TListBox", index=1)
        self.click(cities["x"] + cities["w"] // 2, cities["y"] + 12 + 12 * city_row, pause=0.6)
        for k, r in enumerate(unit_rows):
            if k:
                sh("xdotool", "keydown", "ctrl")
            self.click(units["x"] + units["w"] // 2, units["y"] + 12 + 12 * r, pause=0.4)
            if k:
                sh("xdotool", "keyup", "ctrl")
        self.click_control(self.control(cs, text="Mobilize"), pause=1.5)
        texts = self.dismiss_popups()
        self.close_controls("Army recruits", cs)
        return texts


    RELATION_COLUMN = {"peace": 0, "trade": 1, "ally": 2, "war": 3}
    RELATION_VALUE = {"trade": 1, "ally": 2, "war": 3}          # what memory must hold after the order (peace may be <= 0: a cooldown)

    def relation(self, nation, kind):
        """International Relations: one row per nation (all 16; each row has four radios, peace, trade, ally, war, and the
        current nation's own row has none selected: 64 radios in all), OK / Cancel. The radios and the buttons are read from
        the running dialog (they drifted from the recorded layout, so a hardcoded OK missed), not hardcoded. OK is clicked up
        to three times; a refusal box stops the whole OK (set one relation per call) and is returned in the texts; if the
        dialog stays open with no box, or the value is not the requested one, it raises instead of reporting success.
        Returns (the current nation's value in memory, box texts)."""
        self.dismiss_popups()       # a stale news/offer box would block the dialog and be mistaken for a refusal below
        self.tool("relations", pause=1.5)
        if not self.find_windows("^International Relations$"):
            self.tool("relations", pause=1.5)
        w = self.find_windows("^International Relations$")
        self.raise_window(w[0][0])
        for _ in range(8):          # the controls are not always enumerable the instant the window appears
            try:
                cs = self.controls("International Relations")
                break
            except DriverError:
                time.sleep(1)
        else:
            raise DriverError("International Relations: its controls could not be read")
        radios = sorted((c for c in cs if c["cls"] == "TRadioButton"), key=lambda c: (c["y"], c["x"]))
        if len(radios) != 64:
            raise DriverError("International Relations: expected 64 radio buttons (16 rows x 4), found %d" % len(radios))
        target = radios[nation * 4 + self.RELATION_COLUMN[kind]]
        for _ in range(2):          # a radio click is idempotent; the first may only activate the window
            self.click_control(target, pause=0.5)
        self.shot(WORK / "shots" / "_relations.png", window=str(w[0][0]))
        texts = []
        for _ in range(3):          # a click into an inactive window may only activate it: try, then retry twice
            self.click_control(self.control(cs, text="OK"), pause=1.5)
            texts += self.dismiss_popups()
            if texts or not self.find_windows("^International Relations$"):
                break
        if self.find_windows("^International Relations$"):
            if not texts:
                raise DriverError("International Relations did not close after OK (and no refusal box)")
            self.click_control(self.control(cs, text="Cancel"), pause=1.0)       # refused: the box stopped the OK
        me = self.i16(CUR_NATION)
        value = self.i16(NATIONS + me * NATION_LEN + 0x26 + 2 * nation)
        want = self.RELATION_VALUE.get(kind)
        if not texts and ((want is not None and value != want) or (want is None and value > 0)):
            raise DriverError("relation with nation %d is %d, not %s as ordered" % (nation, value, kind))
        return value, texts

    def build_fleet(self, ships):
        """Build a fleet of <ships> at the free coastal city the game picks. The
        Build fleet dialog has a 1s and a 10s spinner; OK starts construction."""
        self.tool("build_fleet")
        # Either the dialog opens, or a box refuses ("Only nations with coastal cities can build fleets", seen for Dacia,
        # Galatia and Media; coverage.md also lists "You do not have a free coastal city at this time."): wait for one of them.
        self.wait(lambda: self.find_windows("^Build fleet$") or [w for w in self.popups() if w[1] in ("Information", "Warning", "Error")],
                  8, "the Build fleet dialog or its refusal")
        if not self.find_windows("^Build fleet$"):
            refusal = [self.read_popup(w) for w in self.popups() if w[1] in ("Information", "Warning", "Error")]
            self.dismiss_popups()
            return refusal
        cs = self.controls("Build fleet")
        ups = sorted((c for c in cs if c["cls"] == "TUpDown"), key=lambda c: c["x"])
        for _ in range(ships % 10):
            self.click_control(ups[0], fy=0.25, pause=0.2)
        for _ in range(ships // 10):
            self.click_control(ups[1], fy=0.25, pause=0.2)
        self.click_control(self.control(cs, text="OK"), pause=1.5)
        texts = self.dismiss_popups()
        # The fleet is ordered at once ("The fleet will be built at <city>"), but the dialog STAYS OPEN, and a
        # second OK would order a second fleet. Close it with Cancel (it also swallowed the next End turn click).
        for _ in range(3):
            if not self.find_windows("^Build fleet$"):
                break
            self.click_control(self.control(cs, text="Cancel"), pause=1.0)
        if self.find_windows("^Build fleet$"):
            raise DriverError("Build fleet did not close after Cancel")
        return texts

    def taxation(self, percent):
        """Set the tax level (0..40). The slider is keyboard-driven: focus it,
        Home to 0, then Right once per percent (its LineSize is 1), then OK."""
        self.tool("taxation")
        cs = self.controls("Change tax level")
        tb = self.control(cs, cls="TTrackBar")
        self.click(tb["x"] + tb["w"] // 2, tb["y"] + tb["h"] // 2, pause=0.5)
        self.key("Home")
        if percent:
            sh("xdotool", "key", "--repeat", str(percent), "Right", check=False)
        self.click_control(self.control(cs, text="OK"), pause=1.5)
        return self.dismiss_popups()

    def end_turn(self, timeout=300, battle_shot=None, reclick=True, strict_confirm=False):
        """Game > End turn (it runs at once, unless an army needs supplies: then an
        "End turn ?" box asks, and is answered End turn), then
        play out any battle with Computer general and dismiss the AI's news and
        offer boxes until the autosave line appears.

        `reclick` (default True, the historical behaviour): click End turn a second time when no sign of the turn starting
        appears within 8 s. With `reclick=False` that case raises DriverError("end turn: no sign of the turn starting")
        after the single click (the first click may have registered: the caller must not click again).
        `strict_confirm` (default False): a Confirm box other than "End turn ?" is answered No, never Yes, on every path
        (the wait loop, inside `play_battle`, after the autosave line), and DriverError("end turn: unexpected Confirm: ...") is raised."""
        log = G / "AUTOSAVE.LOG"
        n = len(log.read_text().splitlines()) if log.exists() else 0
        cal, me = self.calendar(), self.i16(CUR_NATION)
        started = lambda: (self.i16(CUR_NATION) != me or self.calendar() != cal
                           or (log.exists() and len(log.read_text().splitlines()) > n)
                           or self.popups() or self.in_battle())
        self.tool("end_turn")
        texts, t0 = [], time.time()
        # EndTurn moves the seat on at once. Click again only after 8 s with no
        # sign of the turn starting: a click queued while the AI seats run would
        # end the next turn as well.
        try:
            self.wait(started, 8, "turn start", step=0.25)
        except DriverError:
            if not reclick:
                raise DriverError("end turn: no sign of the turn starting")
            self.log("end_turn: first click swallowed, clicking again")
            self.tool("end_turn")
        while time.time() - t0 < timeout:
            if log.exists() and len(log.read_text().splitlines()) > n:
                break
            if self.in_battle() and self.find_windows(" v "):   # battle screen "<A> v <B>"
                texts.append("BATTLE " + self.find_windows(" v ")[0][1])
                self.play_battle(battle_shot, strict=strict_confirm)
                continue
            if self.find_windows(r"^End turn \?$"):
                # "An army of yours needs supplies. ... MAKE MORE MOVES / END TURN": the game asks
                # before ending a turn when an army is out of supplies; we are finished, so End turn.
                texts.append("CONFIRM " + self.read_popup(self.find_windows(r"^End turn \?$")[0]))
                cs = self.controls("End turn ?")
                self.click_control(self.control(cs, text="End turn"), pause=1.5)
                continue
            texts += self.dismiss_popups(strict=strict_confirm)
            time.sleep(1)
        else:
            raise DriverError("end turn timed out")
        time.sleep(3)
        texts += self.dismiss_popups(strict=strict_confirm)
        line = log.read_text().splitlines()[-1]
        if not line.rstrip().endswith("OK"):
            raise DriverError("autosave: " + line)
        return line.split()[1], texts

    def play_battle(self, shot=None, strict=False):
        """Play an open battle with Computer general, then dismiss the result.

        The battle toolbar's button x is derived from the tooltips like the
        others. Turning Computer general on and then End turn once runs the whole
        battle, so the two clicks happen immediately, while the battle window is
        still on top; it can end up below the game's other windows later, and a
        click then lands behind it."""
        time.sleep(2)
        if not self.find_windows(" v "):
            return
        if not self.battle_x:
            self.calibrate_battle_toolbar()
        self.click(self.battle_x.get("computer", BATTLE_TOOLS["computer"]), BATTLE_TOOLBAR_Y, pause=1.5)
        for _ in range(120):
            if strict:
                self._refuse_confirm()
            if not self.in_battle() or self.find_windows("Battle ended"):
                break
            self.click(self.battle_x.get("end_turn", BATTLE_TOOLS["end_turn"]), BATTLE_TOOLBAR_Y, pause=1.5)
        w = self.find_windows("Battle ended")
        if w and shot:
            self.shot(shot, window=str(w[0][0]))
        # Dismiss the result dialog: its OK by control, else the default button,
        # else the recorded coordinate.
        try:
            self.click_control(self.control(self.controls("Battle ended"), text="OK"), pause=1.5)
        except DriverError:
            if strict:
                self._refuse_confirm()      # Return (below) could accept an unexpected Confirm box: decline it first
            self.key("Return")
            time.sleep(1.5)
            if strict:
                self._refuse_confirm()
            if self.popups():
                self.click(220, 478, pause=1.5)
        self.dismiss_popups(strict=strict)
