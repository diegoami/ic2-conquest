"""L11 20-units in the Army to army transfer dialog (TArmyToArmy_Army1Transfer :44113-44165 / Army2Transfer, R28 / R31).
FLEET_PORT: army 0 (Rome, (101,45)) is selected -> left list; the right list is the adjacent own army (armies 12 at (102,45)
and 13 at (102,44) are both adjacent; both get the same layout, unit names show which one the dialog used).
Every unit: regular heavy infantry, 1,000 men, quality 7, named "S<army>-<slot>". Steps: select rows of one list (ctrl for
more), press that list's Transfer, collect boxes, then OK or Cancel.
python3 probe_transfer20.py <out_dir> [case ...]"""
import json, shutil, struct, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
from tests.test_orders import fresh_save, load
from harness.driver import ARMY_TOOLBAR_Y, DriverError, sh

FLEET_PORT = (Path(__file__).resolve().parents[4] / "saves/fleet-port-antium-0734.SAV")
CASES = {   # case: (army 0 slots, partner slots, list moved from ("left"=army 0 / "right"=partner), rows selected, finish)
    "c1_18_plus_3_left": (list(range(3)), list(range(18)), "left", [0, 1, 2], "OK"),
    "c2_target_only_slot19": ([0], [19], "left", [0], "OK"),
    "c3_target_gap_0_9": (list(range(2)), [0, 9], "left", [0, 1], "OK"),
    "c4_18_plus_3_right": (list(range(18)), list(range(3)), "right", [0, 1, 2], "OK"),
    "c5_18_plus_3_cancel": (list(range(3)), list(range(18)), "left", [0, 1, 2], "Cancel"),
    "c2b_target_only_slot19_cancel": ([0], [19], "left", [0], "Cancel"),
    "c6_target_gap_0_2": ([0], [0, 2], "left", [0], "OK"),       # landing at the unit COUNT (2) would hit the occupied slot 2
}
TITLES = ("Army to army transfer", "Split army")   # attempt 3: with the partner's slot 19 occupied the same dialog is captioned "Split army"
def dialog():
    for t in TITLES:
        w = g.find_windows("^%s$" % t)
        if w: return t, w[0]
    return None, None
ARMY_COUNT_OFF, ARMY_LEN = 100956, 656
out = Path(sys.argv[1])

def army_off(data, x, y):
    na = struct.unpack_from("<h", data, ARMY_COUNT_OFF)[0]
    return next(ARMY_COUNT_OFF + 2 + i * ARMY_LEN for i in range(na)
                if struct.unpack_from("<3h", data, ARMY_COUNT_OFF + 2 + i * ARMY_LEN) == (x, y, 0))

def make_pre(a0, partner):
    data = bytearray(FLEET_PORT.read_bytes())
    for (x, y, aid), slots in (((101, 45, 0), a0), ((102, 45, 12), partner), ((102, 44, 13), partner)):
        off = army_off(data, x, y)
        for k in range(20):
            so = off + 16 + 32 * k
            data[so:so + 32] = bytes(32)
            if k in slots:
                struct.pack_into("<4h", data, so, 0, 1, 1000, 7)
                data[so + 8:so + 8 + len(f"S{aid}-{k}")] = f"S{aid}-{k}".encode()
    fd, name = tempfile.mkstemp(suffix=".SAV", prefix="tmp_tr20_"); p = Path(name); p.write_bytes(bytes(data))
    return p

def armies(s):
    return {a["id"]: {"troops": a["troops"], "slots": {u["slot"]: u["name"] for u in a["units"]}}
            for a in s["armies"] if a["owner"] == 0 and a["id"] in (0, 12, 13)}

def army_bytes(path):
    d = path.read_bytes(); na = struct.unpack_from("<h", d, ARMY_COUNT_OFF)[0]
    return d[ARMY_COUNT_OFF:ARMY_COUNT_OFF + 2 + na * ARMY_LEN]

results = {}
for case in (sys.argv[2:] or CASES):
    a0, partner, side, rows, finish = CASES[case]
    pre = make_pre(a0, partner); shutil.copy(pre, out / f"{case}_PRE.SAV")
    g = fresh_save(pre)
    p0 = g.save_as(f"{case.upper()}_BEFORE.SAV"); shutil.copy(p0, out / f"{case}_BEFORE.SAV")
    ax, ay = g.army_pos(0); g.select_army(0, ax, ay)
    if not g.army_x: g.calibrate_army_toolbar()
    try:
        # not open_dialog(): the dialog can take longer than its 3 x 1.2 s (attempt 1, c2: it opened after the driver gave up)
        for _ in range(2):
            g.click(g.army_x["transfer"], ARMY_TOOLBAR_Y, pause=0.5)
            try:
                g.wait(lambda: dialog()[0], 6, "Army to army transfer / Split army"); break
            except DriverError:
                pass
        else:
            raise DriverError("Army to army transfer did not open")
    except DriverError as e:
        g.shot(out / f"{case}_no_dialog.png")
        texts = g.dismiss_popups()
        p1 = g.save_as(f"{case.upper()}_AFTER.SAV"); shutil.copy(p1, out / f"{case}_AFTER.SAV")
        results[case] = {"open_error": str(e), "popups": texts,
                         "army_table_identical": army_bytes(out / f"{case}_BEFORE.SAV") == army_bytes(out / f"{case}_AFTER.SAV")}
        print(case, json.dumps(results[case]), flush=True); pre.unlink(missing_ok=True); continue
    title, _w = dialog()
    count_open = g.i16(0x4A0324)
    cs = g.controls(title)
    lists = sorted((c for c in cs if c["cls"] == "TListBox"), key=lambda c: c["x"])
    buttons = sorted((c for c in cs if c["text"] == "Transfer"), key=lambda c: c["x"])
    k_side = 0 if side == "left" else 1
    lst = lists[k_side]
    # activate the dialog first: the first click into an inactive window may only activate it (attempt 1, c1: row 0 was not selected)
    g.click(lst["x"] + lst["w"] // 2, lst["y"] - 8, pause=0.6)
    # rows are 10 px high in this dialog (attempt 2/3: a 12 px step hit the row 0/1 boundary, then rows 2, 3); ctrl-click every row
    sh("xdotool", "keydown", "ctrl")
    for r in rows:
        g.click(lst["x"] + lst["w"] // 2, lst["y"] + 6 + 10 * r, pause=0.4)
    sh("xdotool", "keyup", "ctrl")
    g.shot(out / f"{case}_selection.png")
    g.click_control(buttons[k_side], pause=1.5)
    g.shot(out / f"{case}_after_transfer.png")
    seen = [(w[1], w[4], w[5]) for w in g.find_windows(".")]
    texts = g.dismiss_popups()
    g.click_control(g.control(cs, text=finish), pause=1.5)
    texts += g.dismiss_popups()
    still_open = (not g._popup_gone(dialog()[1][0])) if dialog()[0] else False
    p1 = g.save_as(f"{case.upper()}_AFTER.SAV"); shutil.copy(p1, out / f"{case}_AFTER.SAV")
    b, a = armies(load(out / f"{case}_BEFORE.SAV")), armies(load(out / f"{case}_AFTER.SAV"))
    r = {"dialog_title": title, "army_count_dialog_open": count_open, "army_count_after": g.i16(0x4A0324), "windows_after_transfer": seen, "army0_slots": a0, "partner_slots": partner, "side": side, "rows": rows, "finish": finish,
         "popups": texts, "dialog_still_open": still_open, "before": b, "after": a,
         "army_table_identical": army_bytes(out / f"{case}_BEFORE.SAV") == army_bytes(out / f"{case}_AFTER.SAV")}
    results[case] = r
    print(case, json.dumps({k: r[k] for k in ("dialog_title", "army_count_dialog_open", "army_count_after", "popups", "dialog_still_open", "after", "army_table_identical")}), flush=True)
    pre.unlink(missing_ok=True)
(out / ("probe_transfer20_" + "_".join(results) + ".json")).write_text(json.dumps(results, indent=1))
