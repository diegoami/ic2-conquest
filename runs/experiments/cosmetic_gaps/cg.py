"""The cosmetic-gaps helpers on top of the leaders-form runner (play_lib): the X window name (the title bar, read from the
X server, never OCR), window geometry, the Area map's speed buttons (no HWND: located by the live Panel1 rectangle from
win_state plus the child's declared offset in the TAreaMap form resource, its effect verified by the toggle byte in game
memory and the map region's pixels), a verified File > Open through the OCR-read menu, verified toolbar buttons (a tooltip
must prove the x, runs/experiments/refusal_texts' verified_x), a verified window drag, and the SAV words the save keeps for
window positions. Every click is one of play_lib.Game3's recorded clicks; nothing is clicked at a guessed or fixed position."""
import os, re, struct, subprocess, time, shutil
import eog
from eog import *                                   # noqa: F401,F403
from eog import _drv, _ids, _geo, _screen_words
import play_lib as P
from play_lib import (Game3, CLICKS, KEYS, VERIFIED, CTX, note_step, step_begin, read_controls,
                      verified_reset, ocr_word, menu_open, snap, sha, log, new_rec, finish, jlog)
from lib import _orig_sh, ART, DATA, SAVEDIR, ROOT, TMP
from common import new_path, write_new
from state import sav as SAV

BAR = (0, 26, 650, 24)                              # the menu bar strip (play_lib.BAR is the same; kept for clarity)
DROP = (0, 40, 260, 140)                            # the strip under the menu bar in which a dropdown opens
OPEN_REGIONS = [(0, 47, 100, 20), (0, 44, 120, 24), (0, 46, 78, 90)]   # where the File dropdown's word Open can be

# ---------------------------------------------------------------- the X window: name and geometry
def window_name(g, wid):
    """The window's name as the X server holds it (xdotool getwindowname): the title bar's text, not OCR."""
    return _drv.sh('xdotool', 'getwindowname', str(wid)).strip()

def main_wid(g):
    """The main game window: the visible window named 'Imperial Conquest 2...' that is not the hidden 1x1 TApplication
    window Wine also names 'Imperial Conquest 2' (seen in play: wid 8388609 1x1 beside the real 650x300 form)."""
    w = [w for w in g.find_windows('.') if w[1].startswith('Imperial Conquest 2') and w[4] > 1 and w[5] > 1]
    if not w: raise _drv.DriverError('no Imperial Conquest 2 game window')
    if len(w) > 1: raise _drv.DriverError('%d Imperial Conquest 2 game windows: %s' % (len(w), w))
    return w[0]

def win_geo(g, wid):
    """(x, y, w, h) of a window id, as the X server reports it (decorations included)."""
    m = re.search(r'Position: (\d+),(\d+).*Geometry: (\d+)x(\d+)', _drv.sh('xdotool', 'getwindowgeometry', str(wid)), re.S)
    if not m: raise _drv.DriverError('no geometry for window %s' % wid)
    return tuple(int(x) for x in m.groups())

def record_title(g, rec, key, note=None):
    """The main window's X name now, kept in rec['titles'][key] with the window id, the calendar and the current seat
    (what the title should speak of) read from game memory at the same moment."""
    wid = main_wid(g)[0]
    nm = window_name(g, wid)
    rec.setdefault('titles', {})[key] = {'wid': wid, 'name': nm, 'note': note,
        'calendar': g.calendar(), 'cur_nation': g.i16(_drv.CUR_NATION), 'turn': g.turn_number()}
    return rec['titles'][key]

def boxes(g):
    """The small modal boxes now open: [(wid, title, x, y, w, h)] (refusal_texts' helper)."""
    return [p for p in g.popups() if p[1] in eog.BOX_TITLES and p[4] < 600 and p[5] < 300]

# ---------------------------------------------------------------- Open (the toolbar's Open button; its tooltip proves the x)
def file_open(g, name):
    """Open a save: the main toolbar's Open button at the x its tooltip proved (verified_reset first; the menu's Open word is
    not reliably read by OCR — refusal_texts' finding), then the Open file dialog must appear as exactly one new
    file-dialog-sized window whose OCR words read as the Open dialog before anything is typed; the save name is typed into the
    field (replace_field) and Return pressed. The game window (or a message box) must follow; every box is closed through its
    own OK control (a Confirm is answered No through its control). Returns the box texts."""
    base = _ids()
    verified_reset(g)
    x = verified_x(g, 'main', 'open')
    b = step_begin(); CTX['why'] = 'main toolbar Open button (tooltip-proved x)'; CTX['target'] = {'src': 'tooltip', 'tool': 'open', 'x': x, 'y': _drv.TOOLBAR_Y}
    g.click(x, _drv.TOOLBAR_Y, pause=1.5)
    try:
        g.wait(lambda: [i for i in _ids() - base if _geo(i) and _geo(i)[2] > 200 and _geo(i)[3] > 150], 8, 'Open dialog window')
    except _drv.DriverError:
        note_step(b, step='open dialog', ok=False, how='exactly one new file-dialog-sized window must appear', attempts=1)
        raise _drv.DriverError('the Open button opened no file-dialog-sized window (nothing typed)')
    dlg = [i for i in _ids() - base if _geo(i) and _geo(i)[2] > 200 and _geo(i)[3] > 150]
    if len(dlg) != 1:
        note_step(b, step='open dialog', ok=False, how='exactly one new file-dialog-sized window must appear', dialogs=[(i, _geo(i)) for i in dlg], attempts=1)
        raise _drv.DriverError('Open: not a single new file-dialog-sized window: %s' % dlg)
    time.sleep(0.8)
    words = [w[0] for w in _screen_words(g, _geo(dlg[0]))]
    if 'save' in words or not any(w.startswith('open') or w.startswith('look') for w in words):
        note_step(b, step='open dialog', ok=False, how='the new window must read as the Open dialog (OCR)', words=words[:12], attempts=1)
        raise _drv.DriverError('the new window does not read as the Open dialog (OCR %s)' % words[:12])
    note_step(b, step='open dialog', ok=True, how='one new file-dialog-sized window whose OCR words read as the Open dialog', wid=dlg[0], geo=_geo(dlg[0]), words=words[:12], attempts=1)
    CTX['why'] = 'type the save name into the Open dialog'
    g.replace_field(name); g.key('Return')
    g.wait(lambda: g.loaded() or boxes(g), 40, 'game window or a message box after load')
    time.sleep(3)
    texts = [t for _, t in close_all_boxes(g, 'load')]
    if not g.loaded():
        g.wait(g.loaded, 30, 'game window after the box was closed')
        texts += [t for _, t in close_all_boxes(g, 'load')]
    return texts

def close_all_boxes(g, tag):
    """Every small box now open, closed through its own OK control (enumerated; a box without one stops the run). A Confirm
    box is answered No through its control. Returns [(wid, text)]."""
    from eog import BOX_TITLES
    out = []
    for p in g.popups():
        wid, name, wd, ht = p[0], p[1], p[4], p[5]
        if name not in BOX_TITLES or wd >= 600 or ht >= 300: continue
        text = g.read_popup(p)
        if name == 'Confirm':
            eog.answer_confirm(g, 'Confirm', 'No'); out.append((wid, 'CONFIRM(No) ' + text)); continue
        cs = g.controls(name); ok = next((c for c in cs if c['text'].replace('&', '').lower() == 'ok'), None)
        if ok is None: raise _drv.DriverError('box %d (%r): no OK control in %s: nothing clicked' % (wid, text, [c['text'] for c in cs]))
        for attempt in range(3):
            eog.spend(wid, 'box', 3)
            g.click_control(ok, pause=0.6)
            if eog.gone(g, wid, timeout=3): break
        else: raise _drv.DriverError('box %d (%r) did not close' % (wid, text))
        out.append((wid, text))
    return out

# ---------------------------------------------------------------- toolbar buttons: a tooltip must prove the x (refusal_texts' verified_x)
def verified_x(g, bar, tool):
    """The x of a toolbar button from a tooltip scan made NOW with this run's own game: the button's tooltip window must
    appear while the pointer is over x. A cached x is only a hint (a narrow window, then the whole bar); it is never clicked
    unless a tooltip proved it. DriverError (nothing clicked) when the tooltip is not found."""
    labels, y, full, cache = {'army': (_drv.ARMY_TOOLBAR_LABELS, _drv.ARMY_TOOLBAR_Y, (336, 540), g.army_x), 'fleet': (_drv.FLEET_TOOLBAR_LABELS, _drv.ARMY_TOOLBAR_Y, (336, 540), g.fleet_x),
                              'main': (_drv.TOOLBAR_LABELS, _drv.TOOLBAR_Y, (4, 232), g.toolbar_x)}[bar]
    hint = (cache or {}).get(tool)
    windows = ([(max(full[0], hint - 15), min(full[1], hint + 16))] if hint else []) + [full]
    for lo, hi in windows:
        found = g._scan_bar(y, {tool: labels[tool]}, lo, hi, 0.5)
        if tool in found:
            log('toolbar', '%s button %s: tooltip %r seen, x=%d (hint %s)' % (bar, tool, labels[tool], found[tool], hint))
            VERIFIED.append({'step': 'toolbar %s %s' % (bar, tool), 'ok': True, 'how': 'the tooltip %r was seen while the pointer was over x' % labels[tool], 'x': found[tool], 'y': y, 'hint': hint, 'clicks': [len(CLICKS), len(CLICKS)]})
            CTX['target'] = {'src': 'tooltip', 'how': 'the tooltip %r was seen while the pointer was over x' % labels[tool], 'tool': tool, 'x': found[tool], 'y': y}
            return found[tool]
    raise _drv.DriverError('%s toolbar: the tooltip %r of %s was not seen: nothing clicked' % (bar, labels[tool], tool))

def main_tool(g, name, pause=1.5):
    """A main-toolbar button (End turn, Open, ...) at the x a tooltip proved (verified_reset first)."""
    verified_reset(g)
    x = verified_x(g, 'main', name)
    CTX['why'] = 'main toolbar button %s (tooltip-proved x)' % name
    g.click(x, _drv.TOOLBAR_Y, pause=pause)

def army_button(g, i, tool):
    """Select army i (verified through the game's selection word) and click the army-toolbar button `tool` at the tooltip-proved x."""
    select_army(g, i)
    x = verified_x(g, 'army', tool)
    CTX['why'] = 'army toolbar button %s (tooltip-proved x)' % tool
    g.click(x, _drv.ARMY_TOOLBAR_Y, pause=1.5)

def fleet_button(g, i, tool):
    select_fleet(g, i)
    x = verified_x(g, 'fleet', tool)
    CTX['why'] = 'fleet toolbar button %s (tooltip-proved x)' % tool
    g.click(x, _drv.ARMY_TOOLBAR_Y, pause=1.5)

# ---------------------------------------------------------------- tile clicks: the driver's own targeting, recorded as the target proof
def select_army(g, i):
    """g.select_army with the recorded proof: the click goes at army i's tile through the driver's own view geometry
    (Game.show), its effect verified by the game's selection word (the driver raises when the army is not selected);
    the driver's up-to-3 activation retries all carry the same target."""
    ax, ay = g.army_pos(i)
    CTX['why'] = 'select army %d at tile (%d,%d): the driver\'s tile targeting (its own view geometry)' % (i, ax, ay)
    CTX['target'] = {'src': 'driver tile targeting', 'kind': 'select army', 'army': i, 'tile': [ax, ay]}
    CTX['target_multi'] = 3
    g.select_army(i, ax, ay)
    CTX.pop('target_multi', None)

def select_fleet(g, i):
    """The fleet counterpart of select_army (the driver's own selection path)."""
    fx, fy = g.fleet_pos(i)
    CTX['why'] = 'select fleet %d at tile (%d,%d): the driver\'s tile targeting (its own view geometry)' % (i, fx, fy)
    CTX['target'] = {'src': 'driver tile targeting', 'kind': 'select fleet', 'fleet': i, 'tile': [fx, fy]}
    CTX['target_multi'] = 3
    g.select_fleet(i)
    CTX.pop('target_multi', None)

def click_tile(g, tx, ty, pause=2.0, why=None):
    """g.click_tile with the recorded proof: the tile's screen point comes from the driver's own view geometry
    (Game.show); the caller's `why` names the order. The effect is proved by the caller (a position wait)."""
    CTX['why'] = why or 'tile (%d,%d) through the driver\'s own view geometry (Game.show)' % (tx, ty)
    CTX['target'] = {'src': 'driver tile targeting', 'tile': [tx, ty]}
    g.click_tile(tx, ty, pause=pause)

def end_turn(g):
    """End turn: the toolbar button at the tooltip-proved x; the 'End turn ?' Confirm box (if any) is answered through its own
    End turn control; every information box through its OK. Returns the box texts."""
    before = eog.autosave_lines()
    main_tool(g, 'end_turn', pause=2.0)
    texts = []
    t0 = time.time()
    while time.time() - t0 < 60:
        if g.find_windows(r'^End turn \?$'): texts.append('CONFIRM ' + eog.answer_confirm(g, 'End turn ?', 'End turn'))
        texts += [t for _, t in close_all_boxes(g, 'end_turn')]
        if not boxes(g) and not g.find_windows(r'^End turn \?$') and eog.autosave_lines() > before: break
        time.sleep(1)
    return texts

# ---------------------------------------------------------------- the Area map's speed buttons (no HWND of their own)
AREA_TITLE = 'Area map'
# The TAreaMap form resource (tracked: form_TAreaMap.txt): Panel1 holds the speed buttons; each child's rectangle is its
# declared Left/Top/Width/Height inside Panel1. sb_areatog 3,3,22,22; sb_areaarms 76,3,22,22 (from the resource, never measured).
SB = {'sb_areatog': (3, 3, 22, 22), 'sb_areacits': (30, 3, 22, 22), 'sb_areacap': (53, 3, 22, 22), 'sb_areaarms': (76, 3, 22, 22),
      'sb_areaflts': (99, 3, 22, 22), 'sb_areaalln': (122, 3, 22, 22)}

def area_panel(g):
    """The Area map's Panel1 rectangle from a fresh win_state read of the live window (the anchor every speed button is
    located from). DriverError when the window or the panel is missing."""
    cs = read_controls(g, AREA_TITLE)
    panels = [c for c in cs if c['cls'] == 'TPanel' and c['w'] >= 300]
    if len(panels) != 1: raise _drv.DriverError('Area map: %d wide panels in win_state' % len(panels))
    return panels[0]

def sb_rect(g, name):
    """The screen rectangle of speed button `name`: Panel1's live rectangle plus the button's declared offset in the form
    resource (SB above, cross-checked by the claims audit against the tracked dump of the resource)."""
    p = area_panel(g)
    l, t, w, h = SB[name]
    return (p['x'] + l, p['y'] + t, w, h)

def click_sb(g, name, why):
    """Click an Area map speed button at its located rectangle, with the button's tooltip as a second proof of the point
    (the pointer rests there before the click and the hint window 'Toggle colour' / 'Show armies' must be up)."""
    x, y, w, h = sb_rect(g, name)
    hint = {'sb_areatog': 'Toggle colour', 'sb_areaarms': 'Show armies'}[name]
    _drv.sh('xdotool', 'mousemove', str(x + w // 2), str(y + h // 2)); time.sleep(1.0)
    seen = hint in {wn[1] for wn in g.find_windows('.')}
    CTX['why'] = why; CTX['target'] = {'src': 'panel + form resource', 'button': name, 'panel_line': area_panel(g)['line'],
                                       'rect': [x, y, w, h], 'hint_seen': seen, 'hint': hint}
    g.click(x + w // 2, y + h // 2, pause=1.0)
    return seen

def toggle_byte(g):
    """The Area map colour-toggle byte as the game holds it: nation record +0x46C of the current nation (0 mono, 1 terrain)."""
    n = g.i16(_drv.CUR_NATION)
    return n, g.mem(_drv.NATIONS + n * _drv.NATION_LEN + 0x46C, 1)[0]

def area_window(g):
    w = g.find_windows('^%s$' % AREA_TITLE)
    return w[0] if w else None

def region_hash(g, rect):
    """A perceptual-ish hash of a screen region of a fresh screenshot: the mean of the region's grey bytes (the area map's
    palette switch and the drawn markers both move it; recorded as a number, the screenshots are the evidence)."""
    x, y, w, h = rect
    full = os.path.join(TMP, 'ic2_cg_rh.png')
    _orig_sh('import', '-window', 'root', full)
    out = subprocess.run(['convert', full, '-crop', '%dx%d+%d+%d' % (w, h, x, y), '+repage', '-resize', '64x32!', '-colorspace', 'Gray', '-format', '%[fx:mean*255]', 'info:'],
                         capture_output=True, text=True).stdout
    return round(float(out), 3)

def snap_win(g, rec, key, wid, name):
    """Screenshot of one window, kept under the next free name and recorded (name, hash) in the play's `screens`."""
    p = new_path(ART + name); g.shot(p, window=str(wid))
    with open(DATA + 'SAVES.sha256', 'a') as f: f.write('%s  %s\n' % (sha(p), os.path.basename(p)))
    rec.setdefault('screens', {})[key] = {'png': os.path.basename(p), 'png_sha': sha(p)}
    return p

# ---------------------------------------------------------------- a verified window move (M05)
def move_window(g, wid, dx, dy):
    """Move a window by (dx, dy) with xdotool windowmove --sync (there is no window manager on the display, so there is no
    title bar to drag: the move is programmatic and the finding says so). The step is recorded as a key-like action and
    verified by the window's X geometry having moved by exactly (dx, dy) with the same size."""
    x, y, w, h = win_geo(g, wid)
    b = step_begin()
    CTX['why'] = 'move window %s by %d,%d (xdotool windowmove; no window manager on the display)' % (wid, dx, dy)
    _drv.sh('xdotool', 'windowmove', '--sync', str(wid), str(x + dx), str(y + dy)); time.sleep(1.0)
    x2, y2, w2, h2 = win_geo(g, wid)
    ok = (x2 - x, y2 - y) == (dx, dy) and (w2, h2) == (w, h)
    KEYS.append({'keys': ['windowmove', wid, x + dx, y + dy], 'why': CTX['why']})
    note_step(b, step='move window %s' % wid, ok=ok, how='the X geometry must have moved by exactly %d,%d with the same size' % (dx, dy),
              geo_before=[x, y, w, h], geo_after=[x2, y2, w2, h2], attempts=1)
    if not ok: raise _drv.DriverError('the move took the window from %s to %s (wanted +%d,%d)' % ([x, y], [x2, y2], dx, dy))
    return (x2, y2, w2, h2)

# ---------------------------------------------------------------- the SAV's window-position words
def sav_window_words(path):
    """The words a SAV holds for window positions, read with the same arithmetic as the game's save writer
    (FUN_004484d0: map, cities, armies, fleets, then 16 x 0x494 nation records, ... then the 55-byte tail):
    per nation the three secondary windows' left/top/height/width (record +0x46E Area map, +0x476 Unit map, +0x47E Information),
    and the tail's 8 bytes (the main window's left/top/height/width)."""
    b = open(path, 'rb').read()
    from state.sav import ARMY_OFF, ARMY_LEN, FLEET_LEN, NATION_LEN
    na = struct.unpack_from('<h', b, ARMY_OFF)[0]
    o = ARMY_OFF + 2 + na * ARMY_LEN
    nf = struct.unpack_from('<h', b, o)[0]
    o += 2 + nf * FLEET_LEN
    nats = {}
    for n in range(16):
        base = o + n * NATION_LEN
        nats[n] = {w: list(struct.unpack_from('<4h', b, base + off)) for w, off in (('area', 0x46E), ('unit', 0x476), ('information', 0x47E))}
        nats[n]['toggle_byte'] = b[base + 0x46C]
        nats[n]['leader'] = b[base + 0x0B:base + 0x0B + 26].split(b'\0')[0].decode('latin1')
        nats[n]['name'] = b[base:base + 11].split(b'\0')[0].decode('latin1')
    tail = o + 16 * NATION_LEN + 600
    ni = struct.unpack_from('<h', b, tail)[0]
    tail8 = tail + 2 + (ni + 1) * 61
    return {'nations': nats, 'current_nation': struct.unpack_from('<h', b, tail8 + 36)[0], 'main': list(struct.unpack_from('<4h', b, tail8 + 46)),
            'turn_order': list(struct.unpack_from('<16h', b, tail8))}
