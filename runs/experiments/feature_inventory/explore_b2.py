"""EXPLORE batch 2 (rework of PR #44): submenus opened and PROVEN open before the screenshot, Show hints toggle, and distinct key tests.
New file names FI_b2_*; every screenshot goes to a new path (rule 6)."""
from explore_lib import *
xvfb()
B = 'b2'
g = Game()
g.load('/home/diego/ic2-work-inv/fixtures/BASE.SAV', seed=12345)
log(B, 'loaded BASE.SAV seed 12345 (%s)' % g.seed_line)
def open_unit_menu():
    g.reset_ui(); g.click(259, 36, pause=1.0)
def word_pos(path, word, region=None):
    for t, x, y in ocr_words(path):
        if t.lower().startswith(word.lower()): return x, y
    return None
# --- 1. Unit map menu and its three submenus
open_unit_menu(); pp, ph = snap(g, 'FI_b2_01_unit_menu_parent.png', '480x300+0+26'); log(B, 'parent menu hash %s' % ph[:12])
parent_words = [t for t, x, y in ocr_words(pp)]
log(B, 'parent OCR: %s' % parent_words)
proven = {}
for sub, expect in (('Army', ('Supply', 'Disband')), ('Fleet', ('Scuttle', 'Repair')), ('City', ('Fortify',))):
    ok = False
    for attempt in range(4):
        open_unit_menu()
        # the parent menu is re-read each time: locate the item by OCR, then hover it
        p0, h0 = snap(g, 'FI_b2_tmp_%s_%d.png' % (sub, attempt), '480x300+0+26')
        pos = word_pos(p0, sub)
        if not pos: log(B, '%s: item not found by OCR (attempt %d)' % (sub, attempt)); continue
        x, y = pos[0] + 0, pos[1] + 26
        sh('xdotool', 'mousemove', str(x), str(y)); time.sleep(0.4); sh('xdotool', 'mousemove', str(x + 25), str(y + 1)); time.sleep(1.2)
        p1, h1 = snap(g, 'FI_b2_02_unit_%s_submenu.png' % sub.lower(), '700x300+0+26')
        words = [t for t, xx, yy in ocr_words(p1)]
        hit = [w for w in expect if any(t.lower().startswith(w.lower()) for t in words)]
        log(B, '%s attempt %d: hash %s expect %s found %s' % (sub, attempt, h1[:12], expect, hit))
        if hit and h1 != ph: ok = True; proven[sub] = (p1, h1); break
    log(B, '%s submenu proven open: %s' % (sub, ok))
    g.reset_ui()
log(B, 'distinct hashes: %s' % (len({h for p, h in proven.values()}) == len(proven)))
# --- 2. Show hints toggle: tooltip over the first nation button
def tooltip(tag):
    g.reset_ui(); sh('xdotool', 'mousemove', '236', '62'); time.sleep(0.4); sh('xdotool', 'mousemove', '240', '59'); time.sleep(2.5)
    return snap(g, 'FI_b2_03_hint_%s.png' % tag, '260x80+180+40')
def toggle_hints():
    g.reset_ui(); g.click(304, 36, pause=1.0); g.click(348, 83, pause=1.0); g.reset_ui()
pa, ha = tooltip('on_before'); log(B, 'hints on: crop hash %s words %s' % (ha[:12], [t for t, x, y in ocr_words(pa)]))
toggle_hints()
pb, hb = tooltip('after_toggle'); log(B, 'after one toggle: crop hash %s words %s' % (hb[:12], [t for t, x, y in ocr_words(pb)]))
g.reset_ui(); g.click(304, 36, pause=1.0); pm, hm = snap(g, 'FI_b2_04_help_menu_after_toggle.png', '480x130+280+26'); g.reset_ui()
toggle_hints()
pc, hc = tooltip('on_again'); log(B, 'toggled back: crop hash %s' % hc[:12])
# --- 3. Keys with another nation viewed: Shift+P draws the VIEWED nation's capital, Ctrl+Q the LEADER's
def clear(): g.click(20, 110, pause=0.8); g.click(20, 110, pause=0.8)
def key(k): sh('xdotool', 'mousemove', '520', '45'); time.sleep(0.3); sh('xdotool', 'key', k); time.sleep(1.5)
g.menu('nations', 1); time.sleep(1.5)   # view Carthage
sh('xdotool', 'mousemove', '600', '45')
res = {}
for k in ('shift+p', 'ctrl+q', 'shift+c', 'ctrl+c'):
    clear(); p, h = snap(g, 'FI_b2_05_carthage_viewed_%s.png' % k.replace('+', '_'), '328x142+2+126'); res[k] = h
    # the crop above is the cleared map; now the key
    key(k); p, h = snap(g, 'FI_b2_05_carthage_viewed_%s_after.png' % k.replace('+', '_'), '328x142+2+126'); res[k + '_after'] = h
    log(B, 'viewing Carthage, key %s: cleared %s -> %s' % (k, res[k][:12], h[:12]))
log(B, 'shift+p vs ctrl+q differ: %s ; shift+c vs ctrl+c differ: %s' % (res['shift+p_after'] != res['ctrl+q_after'], res['shift+c_after'] != res['ctrl+c_after']))
g.click(240, 59, pause=1.0)   # back to Rome
snap(g, 'FI_b2_06_final_state.png'); wins(g, B, 'final')
