"""The plays of the cosmetic-gaps experiment (docs/tasks/cosmetic-gaps.md). One function per play id; each gets (g, tag, rec).
Every step is a verified helper of play_lib / cg (no click at a guessed position). The window title is always read from the X
server (xdotool getwindowname), never OCR; the sound plays run under strace (IC2_STRACE) so the WAV each event opens is the
evidence; the Area map's speed buttons are located from the live Panel1 rectangle plus the form resource's declared offsets
and verified by the toggle byte in game memory."""
import os, shutil, time
from play_lib import *
from eog import _screen_words, _drv
import play_lib as P
import eog
import cg
from cg import (record_title, file_open, boxes, end_turn, area_window, area_panel, sb_rect, click_sb, toggle_byte,
                snap_win, move_window, win_geo, sav_window_words, main_wid, window_name, army_button, fleet_button)
from lib import fixture, SAVEDIR, DATA, ART

FIX_START = 'run0-start-AUTO0720-seed12345.SAV'        # Rome human, army 0 at (100,37) adjacent Arretium (99,36), owner Rome
FIX_FELSINA = 'siege-felsina-failed-0721.SAV'          # army 0 at (99,32) adjacent Felsina (98,31), owner 6 (foreign)
FIX_FLEET = 'fleet-port-antium-0734.SAV'               # fleet 2, 30 ships at (101,46)

def load_fixture(g, rec, name, key):
    """Copy a repo fixture into MY game folder (hashed) and open it through cg.file_open (the toolbar Open button proved by
    its tooltip; the dialog proved by OCR before anything is typed). Records the boxes the load raised."""
    src = fixture(name); dst = _drv.G / name
    if not dst.exists(): shutil.copy(src, dst)
    rec.setdefault('loads', {})[key] = {'fixture': name, 'sha': sha(src)}
    return file_open(g, name)

def mark(g, rec, key):
    """The strace log's size now: the WAV opens after this offset belong to the step named `key`."""
    if os.environ.get('IC2_STRACE'):
        rec.setdefault('strace_marks', {})[key] = os.path.getsize(os.environ['IC2_STRACE'])

def harvest_wavs(tag, rec):
    """Every WAV open in this play's strace log, with the step marks (log byte offsets) it falls between, into a tracked
    file (rule 6). strace prefixes each line with the write offset only with -yy/-qq; instead the log is read in order and
    each match is attributed to the step whose marked offset the file pointer has passed."""
    logp = os.environ.get('IC2_STRACE')
    if not logp: return None
    marks = sorted(rec.get('strace_marks', {}).items(), key=lambda kv: kv[1])
    out = ['# WAV opens of %s (strace -f -e trace=openat,open; each line is preceded by the play step whose mark the read had passed)' % tag]
    step = 'before_load'
    pos = 0
    with open(logp, errors='replace') as f:
        for l in f:
            pos += len(l.encode('utf-8', 'replace'))
            while marks and pos >= marks[0][1]:
                step = marks.pop(0)[0]
            if '.WAV' in l.upper() and 'SOUND' in l.upper():
                out.append('[%s] %s' % (step, l.rstrip()))
    out.append('# marks: ' + repr(rec.get('strace_marks', {})))
    p = write_new(os.path.join(DATA, 'wav_opens_%s.txt' % tag), '\n'.join(out) + '\n')
    rec['wav_opens'] = os.path.basename(p)
    return p

# ---- T1: the title at process start, with the form open, at the first human turn with an EMPTY leader name, after End turn
def t1(g, tag, rec):
    record_title(g, rec, 'at_start', 'process start, no game yet')
    open_form(g, tag, rec)
    record_title(g, rec, 'form_open', 'the leaders form is open, no game started yet')
    fs = need_form(g)
    if not fs['rows'][0]['cb']['check']: set_tick(g, 0, True)
    edit_text(g, 0, '')                                  # Rome human with an EMPTY leader name
    press_button(g, 'OK'); rec['humans_ticked'] = [0]
    after_ok(g, tag, rec, [0])
    record_title(g, rec, 'after_ok', 'first human turn, empty leader name')
    snap_rec(g, rec, 'after_ok', '%s_after_ok.png' % tag)
    rec['end_turn_boxes'] = end_turn(g)
    record_title(g, rec, 'after_end_turn', 'back at the Rome turn after the computer nations played')
    capture(g, tag, rec, 'state', 'after_end_turn'); snap_rec(g, rec, 'after_end_turn', '%s_after_end_turn.png' % tag)

# ---- T2: the title after loading a save with a named leader, and after End turn in that game
def t2(g, tag, rec):
    rec['load_boxes'] = load_fixture(g, rec, FIX_START, 'start')
    record_title(g, rec, 'after_load', 'the turn of the nation the save holds')
    snap_rec(g, rec, 'after_load', '%s_after_load.png' % tag)
    capture(g, tag, rec, 'state', 'after_load')
    rec['end_turn_boxes'] = end_turn(g)
    record_title(g, rec, 'after_end_turn', 'after End turn in the loaded game')
    capture(g, tag, rec, 'state_after', 'after_end_turn'); snap_rec(g, rec, 'after_end_turn', '%s_after_end_turn.png' % tag)

# ---- T3: the Area map colour toggle: byte, panel, button rect, region hash and screenshot before / after one / after two clicks
def t3(g, tag, rec):
    rec['load_boxes'] = load_fixture(g, rec, FIX_START, 'start')
    aw = area_window(g)
    if not aw: raise _drv.DriverError('no Area map window after the load')
    wid = aw[0]; rec['area_wid'] = wid; rec['area_geo'] = win_geo(g, wid)
    rec['panel'] = {k: area_panel(g)[k] for k in ('cls', 'text', 'x', 'y', 'w', 'h', 'line')}
    rec['sb_rect'] = {'sb_areatog': sb_rect(g, 'sb_areatog'), 'sb_areaarms': sb_rect(g, 'sb_areaarms')}
    x, y, w, h = rec['area_geo']
    maprect = (x + 8, y + 34, w - 16, h - 44)            # the map face below the button panel
    n0, b0 = toggle_byte(g); rec['toggle_before'] = {'nation': n0, 'byte': b0}
    rec['hash_before'] = cg.region_hash(g, maprect)
    snap_win(g, rec, 'before', wid, '%s_area_before.png' % tag)
    rec['hint_seen_1'] = click_sb(g, 'sb_areatog', 'toggle colour (first click)')
    n1, b1 = toggle_byte(g); rec['toggle_after_one'] = {'nation': n1, 'byte': b1}
    rec['hash_after_one'] = cg.region_hash(g, maprect)
    snap_win(g, rec, 'after_one', wid, '%s_area_after_one.png' % tag)
    if b1 == b0: raise _drv.DriverError('the toggle byte did not change after one click: %d' % b1)
    rec['hint_seen_2'] = click_sb(g, 'sb_areatog', 'toggle colour (second click)')
    n2, b2 = toggle_byte(g); rec['toggle_after_two'] = {'nation': n2, 'byte': b2}
    rec['hash_after_two'] = cg.region_hash(g, maprect)
    snap_win(g, rec, 'after_two', wid, '%s_area_after_two.png' % tag)
    if b2 != b0: raise _drv.DriverError('the toggle byte did not return to %d after two clicks: %d' % (b0, b2))
    capture(g, tag, rec, 'state', 'after_two_clicks')

# ---- T4: window positions: move the Area map, End turn (autosave), read the SAV's words, restart and load: position restored
def t4(g, tag, rec):
    rec['load_boxes'] = load_fixture(g, rec, FIX_START, 'start')
    aw = area_window(g)
    if not aw: raise _drv.DriverError('no Area map window after the load')
    wid = aw[0]
    geo0 = win_geo(g, wid); rec['geo_loaded'] = list(geo0)
    uw = [w for w in g.find_windows('^Unit map$')]; rec['unit_geo_loaded'] = list(win_geo(g, uw[0][0])) if uw else None
    geo1 = move_window(g, wid, 40, 30); rec['geo_moved'] = list(geo1)
    time.sleep(1.0)
    rec['end_turn_boxes'] = end_turn(g)
    kept = eog.harvest(tag); rec['autosaves'] = kept
    if not kept: raise _drv.DriverError('no autosave was written after End turn')
    savp = SAVEDIR + kept[-1]
    rec['sav_words'] = {'file': kept[-1], 'sha': sha(savp), 'words': sav_window_words(savp)}
    # keep a loadable copy under a name clear_autos will not remove, then restart and load it
    dst = _drv.G / 'T4MOVED.SAV'; shutil.copy(savp, dst)
    g.kill(); time.sleep(2)
    g2 = P.Game3(); g2.start(); eog._ATTEMPTS.clear()
    rec['reload_boxes'] = file_open(g2, 'T4MOVED.SAV')
    aw2 = area_window(g2)
    if not aw2: raise _drv.DriverError('no Area map window after the reload')
    geo2 = win_geo(g2, aw2[0]); rec['geo_restored'] = list(geo2)
    uw2 = [w for w in g2.find_windows('^Unit map$')]; rec['unit_geo_restored'] = list(win_geo(g2, uw2[0][0])) if uw2 else None
    snap_rec(g2, rec, 'after_reload', '%s_after_reload.png' % tag)
    capture(g2, tag, rec, 'state', 'after_reload')
    g2.kill()

# ---- S1: an army move (strace on: which WAV opens)
def s1(g, tag, rec):
    rec['load_boxes'] = load_fixture(g, rec, FIX_START, 'start')
    mark(g, rec, 'loaded')
    ax, ay = g.army_pos(0); rec['army0_before'] = [ax, ay]
    g.select_army(0, ax, ay)
    mark(g, rec, 'selected')
    CTX['why'] = 'move army 0 one tile west (the driver\'s tile targeting, its own view geometry)'
    g.click_tile(ax - 1, ay, pause=2.0)
    g.wait(lambda: g.army_pos(0) != (ax, ay), 20, 'army 0 to move west')
    rec['army0_after'] = list(g.army_pos(0))
    mark(g, rec, 'moved')
    snap_rec(g, rec, 'after_move', '%s_after_move.png' % tag)
    harvest_wavs(tag, rec)

# ---- S2: a fleet move (strace on)
def s2(g, tag, rec):
    rec['load_boxes'] = load_fixture(g, rec, FIX_FLEET, 'fleet')
    mark(g, rec, 'loaded')
    fx, fy = g.fleet_pos(2); rec['fleet2_before'] = [fx, fy]
    g.select_fleet(2)
    mark(g, rec, 'selected')
    CTX['why'] = 'move fleet 2 one tile west (the driver\'s tile targeting)'
    g.click_tile(fx - 1, fy, pause=2.0)
    g.wait(lambda: g.fleet_pos(2) != (fx, fy), 20, 'fleet 2 to move west')
    rec['fleet2_after'] = list(g.fleet_pos(2))
    mark(g, rec, 'moved')
    snap_rec(g, rec, 'after_move', '%s_after_move.png' % tag)
    harvest_wavs(tag, rec)

# ---- S3: scuttle a fleet (strace on; the Confirm box is answered through its own Yes control)
def s3(g, tag, rec):
    rec['load_boxes'] = load_fixture(g, rec, FIX_FLEET, 'fleet')
    mark(g, rec, 'loaded')
    fx, fy = g.fleet_pos(2); rec['fleet2_before'] = [fx, fy]
    fleet_button(g, 2, 'scuttle')
    mark(g, rec, 'dialog')
    ws = g.find_windows('^Confirm$')
    if not ws: raise _drv.DriverError('scuttle raised no Confirm box')
    rec['confirm_text'] = g.read_popup(ws[0])
    eog.answer_confirm(g, 'Confirm', 'Yes')
    mark(g, rec, 'confirmed')
    rec['fleet2_after'] = safe_fleet_pos(g, 2)
    snap_rec(g, rec, 'after_scuttle', '%s_after_scuttle.png' % tag)
    harvest_wavs(tag, rec)

def safe_fleet_pos(g, i):
    try: return list(g.fleet_pos(i))
    except Exception as e: return 'gone (%s)' % repr(e)

# ---- S4: End turn in a game with neighbours at war (strace on: the computer nations' events and their WAVs)
def s4(g, tag, rec):
    rec['load_boxes'] = load_fixture(g, rec, FIX_FELSINA, 'felsina')
    mark(g, rec, 'loaded')
    rec['end_turn_boxes'] = end_turn(g)
    mark(g, rec, 'end_turn_done')
    snap_rec(g, rec, 'after_end_turn', '%s_after_end_turn.png' % tag)
    harvest_wavs(tag, rec)

# ---- U1 / U2: the Supply army dialog at an own city and at a foreign city
def supply_dialog(g, tag, rec, fix, city_note):
    rec['load_boxes'] = load_fixture(g, rec, fix, 'fix')
    ax, ay = g.army_pos(0); rec['army0'] = [ax, ay]
    army_button(g, 0, 'supply')
    ws = g.find_windows('^Supply army$')
    if not ws: raise _drv.DriverError('the Supply army dialog did not open (%s)' % city_note)
    wid = ws[0][0]; rec.setdefault('dialog', {})[city_note] = {'wid': wid, 'geo': list(win_geo(g, wid))}
    cs = read_controls(g, 'Supply army')
    rec['dialog'][city_note]['controls'] = [{k: c[k] for k in ('cls', 'text', 'x', 'y', 'w', 'h', 'enabled', 'visible', 'line')} for c in cs]
    btn = next((c for c in cs if c['cls'] == 'TButton'), None)
    rec['dialog'][city_note]['buy_button'] = {k: btn[k] for k in ('cls', 'text', 'x', 'y', 'w', 'h', 'enabled')} if btn else None
    snap_win(g, rec, 'dialog_' + city_note, wid, '%s_supply_%s.png' % (tag, city_note))
    cancel = next((c for c in cs if c['text'].replace('&', '').lower() in ('cancel', 'done', 'ok')), None)
    if cancel: click_cancel(g, cancel, wid)
    capture(g, tag, rec, 'state', 'after_' + city_note)

def click_cancel(g, c, wid):
    b = step_begin()
    CTX['why'] = 'close the Supply army dialog with its own %s control' % c['text']
    for k in range(3):
        eog.spend(wid, 'Supply army dialog', 3)
        g.click_control(c, pause=0.8)
        if eog.gone(g, wid, timeout=3): break
    else: raise _drv.DriverError('the Supply army dialog did not close')
    note_step(b, step='close supply dialog', ok=True, how='dialog window (X id %d) gone' % wid, attempts=k + 1)

def u1(g, tag, rec):
    supply_dialog(g, tag, rec, FIX_START, 'own_city')

def u2(g, tag, rec):
    supply_dialog(g, tag, rec, FIX_FELSINA, 'foreign_city')

SC = {'T1': dict(seed=12345, fn=t1, note='title at start / form open / first turn with an empty leader / after End turn'),
      'T2': dict(seed=12345, fn=t2, note='title after loading a save with a named leader, and after End turn'),
      'T3': dict(seed=12345, fn=t3, note='Area map colour toggle: byte, hashes and screenshots before / one / two clicks'),
      'T4': dict(seed=12345, fn=t4, note='move the Area map, End turn, the SAV words, reload: position restored'),
      'S1': dict(seed=12345, fn=s1, note='army move under strace', strace=True),
      'S2': dict(seed=12345, fn=s2, note='fleet move under strace', strace=True),
      'S3': dict(seed=12345, fn=s3, note='scuttle a fleet under strace', strace=True),
      'S4': dict(seed=12345, fn=s4, note='End turn under strace (computer nations\' events)', strace=True),
      'U1': dict(seed=12345, fn=u1, note='Supply army dialog at an own city'),
      'U2': dict(seed=12345, fn=u2, note='Supply army dialog at a foreign city')}

def run(pid, batch):
    sc = SC[pid]; tag = 'CG_%s_%s' % (pid, batch)
    import glob, json as _json
    for f in glob.glob(DATA + 'plays_*.jsonl'):          # a recording is never replaced: a tag already recorded is refused (a re-run uses a new batch name)
        for l in open(f):
            if l.strip() and (_json.loads(l).get('tag') or 'CG_%s_%s' % (_json.loads(l)['play'], _json.loads(l)['batch'])) == tag:
                raise _drv.DriverError('the tag %s is already recorded in %s: use a new batch name' % (tag, f))
    eog._ATTEMPTS.clear(); del CLICKS[:]; del KEYS[:]; del VERIFIED[:]
    if sc.get('strace'):
        os.environ['IC2_STRACE'] = ART + 'strace_%s.strace' % tag   # .strace: raw log kept in artifacts and the release tar, never copied into git by archive_measurements
    else:
        os.environ.pop('IC2_STRACE', None)
    g = start_game(sc['seed']); rec = new_rec(pid, batch, sc['seed'], sc['note']); rec['tag'] = tag
    if sc.get('strace'): rec['strace_log'] = os.path.basename(os.environ['IC2_STRACE'])
    CTX.update(tag=tag, why=None, target=None)
    try:
        sc['fn'](g, tag, rec); rec['status'] = 'ok'
    except Exception as e:
        rec['status'] = 'FAILED'; rec['error'] = repr(e)
        try: snap(g, '%s_failure.png' % tag)
        except Exception: pass
        raise
    finally:
        finish(rec, g, batch)
        os.environ.pop('IC2_STRACE', None)
    return rec
