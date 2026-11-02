"""Seleucid turn 26 on NATIVE Windows (owner 2026-11-02, the targeted repro). Windows Python, ctypes only.

    python.exe repro_windows.py FOLDER SAVE_NAME RANDSEED [SECONDS]

FOLDER holds "Imperial Conquest 2 fast rollingsave seed.exe" (the same bytes as the Wine run), "Imperial Conquest 2.dat",
SEED.TXT and SAVE_NAME (the campaign's t26-a00 checkpoint). The script:
  1. starts the exe in FOLDER and waits for the main form (the visible window with a menu);
  2. File > Open through the form's own menu (WM_COMMAND with the item's id, not mouse clicks), types the save's full path
     into the Open dialog and presses OK; information boxes are closed with OK, a Confirm box is answered No (as the Wine driver);
  3. writes RANDSEED into Delphi RandSeed 0x45E030 (WriteProcessMemory) and checks it;
  4. Game > End turn through the menu, then watches SECONDS (default 150) s: boxes are answered as above and logged, a battle
     window ("<A>  v  <B> ...") is NOT played, only recorded;
  5. records every top-level window of the process (title, class, visible, enabled, rect), the battle flag 0x4A0B7C, the seat
     0x4A0320, RandSeed, whether the main form answers messages (SendMessageTimeout) and IsHungAppWindow, AUTOSAVE.LOG,
     a screenshot (PowerShell CopyFromScreen) -> FOLDER/result.json, FOLDER/after.png. The game is left running for a look.
"""
import ctypes
import ctypes.wintypes as W
import json
import os
import struct
import subprocess
import sys
import time

u32 = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
EXE = "Imperial Conquest 2 fast rollingsave seed.exe"
RAND_SEED, BATTLE_FLAG, CUR_NATION = 0x45E030, 0x4A0B7C, 0x4A0320
WM_COMMAND, WM_SETTEXT, WM_GETTEXT, WM_GETTEXTLENGTH, BM_CLICK, WM_NULL = 0x111, 0x0C, 0x0D, 0x0E, 0xF5, 0
SMTO_ABORTIFHUNG = 2
EnumProc = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
u32.SendMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
u32.SendMessageW.restype = ctypes.c_ssize_t
u32.PostMessageW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM]
u32.SendMessageTimeoutW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM, W.UINT, W.UINT, ctypes.POINTER(ctypes.c_size_t)]
u32.GetMenuItemID.restype = W.UINT
log = []


def say(*a):
    s = " ".join(str(x) for x in a)
    log.append(s)
    print(s, flush=True)


def text(h):
    n = u32.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(n + 1)
    u32.GetWindowTextW(h, b, n + 1)
    return b.value


def ctrl_text(h):
    n = u32.SendMessageW(h, WM_GETTEXTLENGTH, 0, 0)
    b = ctypes.create_unicode_buffer(n + 1)
    u32.SendMessageW(h, WM_GETTEXT, n + 1, ctypes.addressof(b))
    return b.value


def cls(h):
    b = ctypes.create_unicode_buffer(256)
    u32.GetClassNameW(h, b, 256)
    return b.value


def rect(h):
    r = W.RECT()
    u32.GetWindowRect(h, ctypes.byref(r))
    return [r.left, r.top, r.right - r.left, r.bottom - r.top]


def windows(pid):
    out = []

    def cb(h, _):
        p = W.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid:
            out.append(h)
        return True
    u32.EnumWindows(EnumProc(cb), 0)
    return out


def children(h):
    out = []

    def cb(c, _):
        out.append(c)
        return True
    u32.EnumChildWindows(h, EnumProc(cb), 0)
    return out


def describe(pid):
    return [{"title": text(h), "class": cls(h), "visible": bool(u32.IsWindowVisible(h)),
             "enabled": bool(u32.IsWindowEnabled(h)), "rect": rect(h)} for h in windows(pid)]


def main_form(pid):
    for h in windows(pid):
        if u32.IsWindowVisible(h) and u32.GetMenu(h):
            return h
    return None


def menu_id(form, top, item):
    """The command id of item `item` (0-based) of top-level menu `top` (0-based)."""
    m = u32.GetMenu(form)
    sub = u32.GetSubMenu(m, top)
    return u32.GetMenuItemID(sub, item)


def menu_index(form, name):
    m = u32.GetMenu(form)
    for i in range(u32.GetMenuItemCount(m)):
        b = ctypes.create_unicode_buffer(64)
        u32.GetMenuStringW(m, i, b, 64, 0x400)   # MF_BYPOSITION
        if b.value.replace("&", "").lower() == name:
            return i
    raise SystemExit(f"menu {name!r} not found")


def answer_boxes(pid, events):
    """Close message boxes (#32770) of the game: OK for information, No for Confirm. Returns True if one was answered."""
    done = False
    for h in windows(pid):
        if cls(h) != "#32770" or not u32.IsWindowVisible(h):
            continue
        title = text(h)
        kids = children(h)
        if any(cls(c) == "Edit" for c in kids):     # a file dialog, not a message box
            continue
        body = " | ".join(ctrl_text(c) for c in kids if cls(c) == "Static" and ctrl_text(c))
        buttons = {ctrl_text(c).replace("&", ""): c for c in kids if cls(c) == "Button"}
        pick = buttons.get("No") or buttons.get("OK") or buttons.get("Cancel")
        events.append({"t": round(time.time(), 1), "box": title, "text": body, "buttons": list(buttons), "pressed":
                       next((k for k, v in buttons.items() if v == pick), None)})
        say("box", title, body[:200], "->", events[-1]["pressed"])
        if pick:
            u32.SendMessageW(pick, BM_CLICK, 0, 0)
            done = True
            time.sleep(1.0)
    return done


class Proc:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0038 | 0x0400, False, pid)   # VM_OPERATION|VM_READ|VM_WRITE|QUERY_INFORMATION
        if not self.h:
            raise SystemExit(f"OpenProcess failed {ctypes.get_last_error()}")

    def read(self, addr, n):
        b = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t()
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(addr), b, n, ctypes.byref(got)):
            raise SystemExit(f"ReadProcessMemory failed {ctypes.get_last_error()}")
        return b.raw

    def write(self, addr, data):
        got = ctypes.c_size_t()
        if not k32.WriteProcessMemory(self.h, ctypes.c_void_p(addr), data, len(data), ctypes.byref(got)):
            raise SystemExit(f"WriteProcessMemory failed {ctypes.get_last_error()}")


def wait(cond, secs, what):
    t = time.time()
    while time.time() - t < secs:
        v = cond()
        if v:
            return v
        time.sleep(0.25)
    raise SystemExit("timeout: " + what)


def main():
    folder, save_name, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    secs = int(sys.argv[4]) if len(sys.argv) > 4 else 150
    import hashlib
    res = {"folder": folder, "save": save_name, "randseed": seed, "events": [],
           "exe_sha256": hashlib.sha256(open(os.path.join(folder, EXE), "rb").read()).hexdigest()}
    p = subprocess.Popen([os.path.join(folder, EXE)], cwd=folder)
    pid = p.pid
    say("started pid", pid)
    form = wait(lambda: main_form(pid), 30, "main form")
    time.sleep(2)
    answer_boxes(pid, res["events"])
    res["menus"] = {"file": menu_index(form, "file"), "game": menu_index(form, "game")}
    u32.PostMessageW(form, WM_COMMAND, menu_id(form, res["menus"]["file"], 1), 0)          # File > Open
    dlg = wait(lambda: next((h for h in windows(pid) if cls(h) == "#32770" and u32.IsWindowVisible(h)
                             and any(cls(c) == "Edit" for c in children(h))), None), 15, "Open dialog")
    res["open_dialog_title"] = text(dlg)
    edit = next(c for c in children(dlg) if cls(c) == "Edit")
    path = os.path.join(folder, save_name)
    buf = ctypes.create_unicode_buffer(path)
    u32.SendMessageW(edit, WM_SETTEXT, 0, ctypes.addressof(buf))
    u32.PostMessageW(dlg, WM_COMMAND, 1, 0)                                                 # IDOK
    say("opening", path)
    wait(lambda: not u32.IsWindowVisible(dlg), 15, "Open dialog closed")
    t = time.time()
    while time.time() - t < 8:
        answer_boxes(pid, res["events"])
        time.sleep(0.5)
    pr = Proc(pid)
    res["randseed_after_load"] = struct.unpack("<I", pr.read(RAND_SEED, 4))[0]
    pr.write(RAND_SEED, struct.pack("<I", seed))
    res["randseed_written"] = struct.unpack("<I", pr.read(RAND_SEED, 4))[0]
    say("RandSeed", res["randseed_after_load"], "->", res["randseed_written"])
    log_path = os.path.join(folder, "AUTOSAVE.LOG")
    n0 = len(open(log_path).read().splitlines()) if os.path.exists(log_path) else 0
    u32.PostMessageW(form, WM_COMMAND, menu_id(form, res["menus"]["game"], 0), 0)         # Game > End turn
    say("End turn")
    t, seen = time.time(), set()
    while time.time() - t < secs:
        answer_boxes(pid, res["events"])
        for h in windows(pid):
            ti = text(h)
            if "  v  " in ti and ti not in seen:
                seen.add(ti)
                res["events"].append({"t": round(time.time() - t, 1), "battle_window": ti})
                say("battle window:", ti)
        time.sleep(1.0)
    lines = open(log_path).read().splitlines() if os.path.exists(log_path) else []
    r = ctypes.c_size_t()
    ok = u32.SendMessageTimeoutW(form, WM_NULL, 0, 0, SMTO_ABORTIFHUNG, 5000, ctypes.byref(r))
    res["after"] = {"windows": describe(pid), "battle_flag": pr.read(BATTLE_FLAG, 1)[0],
                    "cur_nation": struct.unpack("<h", pr.read(CUR_NATION, 2))[0],
                    "randseed": struct.unpack("<I", pr.read(RAND_SEED, 4))[0],
                    "responds": bool(ok), "hung": bool(u32.IsHungAppWindow(form)), "autosave_log_new": lines[n0:]}
    res["frozen_like_wine"] = any("Seleucid to move units" in w["title"] for w in res["after"]["windows"]) \
        and not res["after"]["battle_flag"]
    # Only the game's own windows: the bounding box of its visible windows, with the game brought to the front. A full-desktop
    # capture once caught the owner's other windows and went into a public release (2026-11-02); never capture the whole screen.
    u32.SetForegroundWindow(form)
    time.sleep(1.0)
    rs = [rect(h) for h in windows(pid) if u32.IsWindowVisible(h) and rect(h)[2] > 2 and rect(h)[3] > 2]
    x0, y0 = min(r[0] for r in rs), min(r[1] for r in rs)
    x1, y1 = max(r[0] + r[2] for r in rs), max(r[1] + r[3] for r in rs)
    shot = os.path.join(folder, "after.png")
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Add-Type -AssemblyName System.Drawing;"
                    f"$i=New-Object System.Drawing.Bitmap {x1 - x0},{y1 - y0};"
                    f"$g=[System.Drawing.Graphics]::FromImage($i);$g.CopyFromScreen({x0},{y0},0,0,$i.Size);"
                    f"$i.Save('{shot}')"], timeout=60)
    res["shot_box"] = [x0, y0, x1 - x0, y1 - y0]
    res["log"] = log
    with open(os.path.join(folder, "result.json"), "w") as f:
        json.dump(res, f, indent=1)
    say("result:", json.dumps({k: res["after"][k] for k in ("battle_flag", "cur_nation", "responds", "hung")}),
        "frozen_like_wine", res["frozen_like_wine"])


if __name__ == "__main__":
    main()
