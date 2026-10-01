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
ARMY_TOOLBAR_CACHE = WORK / "army_toolbar.json"
# The tactical battle's toolbar, in the battle window's top strip (y = 112).
BATTLE_TOOLBAR_LABELS = {"end_turn": "End turn", "computer": "Computer general on"}
BATTLE_TOOLBAR_Y = 112
BATTLE_TOOLBAR_CACHE = WORK / "battle_toolbar.json"
BATTLE_TOOLS = {"end_turn": 110, "computer": 158}      # coverage.md's fallback
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

    def _save_cache(self, path, found, what):
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
        for name in TOOLBAR_LABELS:
            found.setdefault(name, TOOLBAR[name])
        self.toolbar_x = found
        self._save_cache(TOOLBAR_CACHE, found, "toolbar")
        return found

    def calibrate_army_toolbar(self, force=False):
        """The army toolbar's button x, derived from the tooltips and cached in
        WORK/army_toolbar.json. Call it with an army selected, or the bar is not
        there to hover."""
        if self.army_x and not force:
            return self.army_x
        found = self._scan_bar(ARMY_TOOLBAR_Y, ARMY_TOOLBAR_LABELS, 336, 540, 0.5)
        for name in ARMY_TOOLBAR_LABELS:
            found.setdefault(name, self.ARMY_TOOLS[name])
        self.army_x = found
        self._save_cache(ARMY_TOOLBAR_CACHE, found, "army toolbar")
        return found

    def calibrate_battle_toolbar(self, force=False):
        """The tactical battle's toolbar x, derived from the tooltips and cached
        in WORK/battle_toolbar.json. Call it with the battle window open; it is
        raised and focused first, or the main window's tooltips win."""
        if self.battle_x and not force:
            return self.battle_x
        w = self.find_windows(" v ")
        if w:
            sh("xdotool", "windowraise", str(w[0][0]), check=False)
            sh("xdotool", "windowfocus", str(w[0][0]), check=False)
            time.sleep(0.3)
        found = self._scan_bar(BATTLE_TOOLBAR_Y, BATTLE_TOOLBAR_LABELS, 5, 250, 0.6)
        for name in BATTLE_TOOLBAR_LABELS:
            found.setdefault(name, BATTLE_TOOLS[name])
        self.battle_x = found
        self._save_cache(BATTLE_TOOLBAR_CACHE, found, "battle toolbar")
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

    def dismiss_popups(self, max_n=10):
        """Press OK on message boxes; return their texts (OCR)."""
        texts = []
        for _ in range(max_n):
            ps = [p for p in self.popups() if p[1] in ("Information", "Confirm", "Warning", "Error", "")
                  and p[4] < 600 and p[5] < 300]
            if not ps:
                break
            wid, name, x, y, wd, ht = ps[0]
            texts.append(self.read_popup(ps[0]))
            for _ in range(3):      # no window manager: the first click only activates the box
                self.click(x + wd // 2, y + ht - 24, pause=0.6)     # the OK button, bottom centre
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

    def new_game(self, row=0, seed=None):
        """File > New with one human nation (row in the nation list, 0 = Rome).
        The autosave hook fires at new-game start: returns AUTO0720.SAV's path."""
        self.set_seed(seed)
        for f in G.glob("AUTO*"):
            f.unlink()
        self.start()
        self.seed_line = (G / "SEED.LOG").read_text().splitlines()[-1].strip() if (G / "SEED.LOG").exists() else ""
        self.menu("file", FILE_ITEMS["new"])
        self.wait(lambda: self.find_windows("^Imperial Conquest 2$"), 10, "new game form")
        self.click(109, 114 + 20 * row, pause=0.5)          # the nation's "human" tick
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

    RELATIONS = {"peace": 94, "trade": 134, "ally": 176, "war": 218}

    def relation(self, nation, kind):
        """International Relations (352x436 at 23,49): one radio per nation row
        (Rome is row 0), OK at (308,217). A refusal box stops the whole OK, so
        set one relation per call. Returns (new value in memory, box texts)."""
        self.tool("relations", pause=1.5)
        w = self.find_windows("^International Relations$")
        if not w:
            self.tool("relations", pause=1.5)
            w = self.find_windows("^International Relations$")
        self.raise_window(w[0][0])
        for _ in range(2):          # a radio click is idempotent; the first may only activate
            self.click(23 + self.RELATIONS[kind], 49 + 25 + round(23.55 * nation), pause=0.5)
        self.shot(WORK / "shots" / "_relations.png", window=str(w[0][0]))
        self.click(308, 217, pause=1.5)
        texts = self.dismiss_popups()
        if self.find_windows("^International Relations$"):
            self.close_dialog("International Relations", (308, 283))      # Cancel
        me = self.i16(CUR_NATION)
        return self.i16(NATIONS + me * NATION_LEN + 0x26 + 2 * nation), texts

    def end_turn(self, timeout=300, battle_shot=None):
        """Game > End turn (it runs at once: there is no confirmation box), then
        play out any battle with Computer general and dismiss the AI's news and
        offer boxes until the autosave line appears."""
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
            self.log("end_turn: first click swallowed, clicking again")
            self.tool("end_turn")
        while time.time() - t0 < timeout:
            if log.exists() and len(log.read_text().splitlines()) > n:
                break
            if self.in_battle() and self.find_windows(" v "):   # battle screen "<A> v <B>"
                texts.append("BATTLE " + self.find_windows(" v ")[0][1])
                self.play_battle(battle_shot)
                continue
            texts += self.dismiss_popups()
            time.sleep(1)
        else:
            raise DriverError("end turn timed out")
        time.sleep(3)
        texts += self.dismiss_popups()
        line = log.read_text().splitlines()[-1]
        if not line.rstrip().endswith("OK"):
            raise DriverError("autosave: " + line)
        return line.split()[1], texts

    def play_battle(self, shot=None):
        """Play an open battle with Computer general, then dismiss the result.
        The battle toolbar's x is derived the same way as the others."""
        time.sleep(2)
        w = self.find_windows(" v ")
        if w:
            sh("xdotool", "windowraise", str(w[0][0]), check=False)
            sh("xdotool", "windowfocus", str(w[0][0]), check=False)
            time.sleep(0.3)
        if not self.battle_x:
            self.calibrate_battle_toolbar()
        self.click(self.battle_x.get("computer", BATTLE_TOOLS["computer"]), BATTLE_TOOLBAR_Y, pause=1.5)
        for _ in range(120):
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
            self.key("Return")
            time.sleep(1.5)
            if self.popups():
                self.click(220, 478, pause=1.5)
        self.dismiss_popups()
