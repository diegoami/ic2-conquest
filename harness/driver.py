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

    def tool(self, name, pause=1.0):
        """Toolbar button: more reliable than the menus, which under Wine without a
        window manager sometimes ignore the item click after a dialog closed."""
        self.reset_ui()
        self.click(TOOLBAR[name], TOOLBAR_Y, pause=pause)

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
        """Select army i, then click an adjacent enemy army or city at (x, y)."""
        ax, ay = self.army_pos(i)
        if max(abs(ax - x), abs(ay - y)) != 1:
            raise DriverError(f"target {x},{y} not adjacent to army {i} at {ax},{ay}")
        self.select_army(i, ax, ay)
        self.click_tile(x, y, pause=1.5)
        return self.dismiss_popups()

    RECRUIT = {  # "Army recruits" dialog (window at 23,49, 560x360)
        "types": {"li": (93, 96), "hi": (93, 128), "ar": (93, 161), "lc": (93, 193), "hc": (93, 225)},
        "up100": (183, 102), "down100": (183, 120), "up1000": (230, 102), "down1000": (230, 120),
        "recruit": (93, 279), "ok": (155, 345), "mobilize": (350, 352), "disband": (461, 352),
        "cities": (365, 75),        # first row of the city list; rows 12 px apart
    }

    def open_recruit(self):
        self.tool("recruit")
        self.wait(lambda: self.find_windows("^Army recruits$"), 10, "Army recruits dialog")

    def recruit(self, city_row, unit_type, thousands=0, hundreds=0):
        """Recruit dialog: pick the city (row in its list), the type, then press the
        1000s/100s arrows. The resulting size is checked from the save diff."""
        L = self.RECRUIT
        self.open_recruit()
        self.click(L["cities"][0], L["cities"][1] + 12 * city_row)
        self.click(*L["types"][unit_type])
        for _ in range(thousands):
            self.click(*L["up1000"], pause=0.2)
        for _ in range(hundreds):
            self.click(*L["up100"], pause=0.2)
        self.click(*L["recruit"], pause=0.8)
        texts = self.dismiss_popups()
        self.click(*L["ok"], pause=0.8)
        self.wait(lambda: not self.find_windows("^Army recruits$"), 10, "Army recruits closed")
        return texts

    def end_turn(self, timeout=300, battle_shot=None):
        """Game > End turn (it runs at once: there is no confirmation box), then
        play out any battle with Computer general and dismiss the AI's news and
        offer boxes until the autosave line appears."""
        log = G / "AUTOSAVE.LOG"
        n = len(log.read_text().splitlines()) if log.exists() else 0
        cal, me = self.calendar(), self.i16(CUR_NATION)
        started = lambda: (self.i16(CUR_NATION) != me or self.calendar() != cal
                           or (log.exists() and len(log.read_text().splitlines()) > n)
                           or self.popups() or self.find_windows(" v "))
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
            if self.find_windows(" v "):                   # battle screen "<A> v <B>"
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
        time.sleep(2)
        self.click(158, 112, pause=1.0)                    # Computer general on
        for _ in range(90):
            if self.find_windows("Battle ended"):
                break
            self.click(110, 112, pause=2.0)                # End turn (battle)
        w = self.find_windows("Battle ended")
        if w and shot:
            self.shot(shot, window=str(w[0][0]))
        self.click(220, 478, pause=1.5)                    # OK on the result
