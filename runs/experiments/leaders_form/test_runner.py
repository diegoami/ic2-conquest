"""Tests of the leaders-form runner's discipline: every intermediate step (a tick, a name edit, a button, a key, a reset, a menu transition) is verified against a MODEL of the form that keeps focus, selection, deletion, typing and the
edit limit separately (so deleting a runner step makes a test fail), retried at most twice, and fails closed (DriverError) when its effect does not show; a control that is missing, disabled or an incomplete form stops the run with nothing
clicked; a click is aimed at a located, pointer-verified target; no runner path clicks an inherited guessed or fixed coordinate (an AST guard over every source of this folder, including the inherited reset paths).
usage: python3 -m unittest test_runner   (no display needed: the game object is a fake)"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import play_lib as P, eog
from eog import _drv

DRAWN = ['Drawn%d' % i for i in range(16)]

class FakeForm:
    """A model of the TPickLeaders form as the original behaves: a mouse press on a tick box (HumanOrComputer) ticks it and wakes the name box (enabled, focused, whole text selected), or unticks it, restores the drawn leader,
    greys the box and leaves the focus on the tick box; a click on an enabled name box focuses it and puts the caret at its end; End, shift+Home, BackSpace and typing act on the focused enabled box (selection, deletion, the
    25 character limit); space on the focused tick box ticks it without waking the name box; a click on a greyed box focuses OK. `mode` switches single defects on: 'activate_first' (the first click only activates the window),
    'nowake' (a tick does not enable the box), 'norestore' (an untick keeps the typed text), 'noselect', 'nofocus', 'touch_other' (a tick or a type changes row 0)."""
    def __init__(self, mode=(), checks=None, enabled=None, texts=None, cb_enabled=None, complete=True):
        self.mode = set(mode); self.checks = list(checks or [0] * 16); self.ed_enabled = list(enabled if enabled is not None else self.checks)
        self.texts = list(texts or DRAWN); self.cb_enabled = list(cb_enabled or [1] * 16); self.focus = ('btn', 'OK'); self.sel = [0, 0]; self.limit = 25; self.activated = 'activate_first' not in self.mode; self.complete = complete
    def row_of(self, c):
        for i in range(16):
            if (c['cls'], c['x'], c['y']) == ('TCheckBox', 111, 100 + 20 * i): return 'cb', i
            if (c['cls'], c['x'], c['y']) == ('TEdit', 171, 100 + 20 * i): return 'ed', i
        return 'btn', c['text']
    def press(self, c):
        if not self.activated: self.activated = True; return
        kind, i = self.row_of(c)
        if kind == 'cb' and self.cb_enabled[i]:
            if not self.checks[i]:
                self.checks[i] = 1
                if 'nowake' not in self.mode:
                    self.ed_enabled[i] = 1
                    if 'nofocus' not in self.mode: self.focus = ('ed', i)
                    self.sel = [0, len(self.texts[i])] if 'noselect' not in self.mode else [len(self.texts[i])] * 2
            else:
                self.checks[i] = 0; self.ed_enabled[i] = 0; self.focus = ('cb', i)
                if 'norestore' not in self.mode: self.texts[i] = DRAWN[i]
            if 'touch_other' in self.mode: self.texts[0] = 'changed'
        elif kind == 'ed':
            if self.ed_enabled[i]: self.focus = ('ed', i); self.sel = [len(self.texts[i])] * 2
            else: self.focus = ('btn', 'OK')
        else: self.focus = ('btn', i)
    def key(self, k):
        f, i = self.focus
        if k == 'space' and f == 'cb' and self.cb_enabled[i]:
            self.checks[i] ^= 1
            if 'touch_other' in self.mode: self.texts[0] = 'changed'
        elif f == 'ed' and self.ed_enabled[i]:
            n = len(self.texts[i])
            if k == 'End': self.sel = [n, n]
            elif k == 'shift+Home': self.sel = [0, self.sel[1]]
            elif k == 'BackSpace':
                a, b = self.sel
                if a == b: a = max(0, a - 1)
                self.texts[i] = self.texts[i][:a] + self.texts[i][b:]; self.sel = [a, a]
    def type(self, t):
        f, i = self.focus
        if f == 'ed' and self.ed_enabled[i]:
            a, b = self.sel; s = self.texts[i][:a] + self.texts[i][b:]
            for ch in t:
                if len(s) < self.limit: s = s[:a] + ch + s[a:]; a += 1
            self.texts[i] = s; self.sel = [a, a]
            if 'touch_other' in self.mode: self.texts[0] = 'changed'
    def fs(self):
        rows = {}
        for i in range(16):
            rows[i] = {'nation': P.NATIONS[i], 'panel': {},
                       'cb': {'cls': 'TCheckBox', 'text': '', 'x': 111, 'y': 100 + 20 * i, 'w': 17, 'h': 14, 'enabled': self.cb_enabled[i], 'check': self.checks[i], 'focus': int(self.focus == ('cb', i)), 'sel0': 0, 'sel1': 0},
                       'ed': {'cls': 'TEdit', 'text': self.texts[i], 'x': 171, 'y': 100 + 20 * i, 'w': 148, 'h': 16, 'enabled': self.ed_enabled[i], 'check': -1, 'limit': 25, 'focus': int(self.focus == ('ed', i)),
                              'sel0': self.sel[0] if self.focus == ('ed', i) else 0, 'sel1': self.sel[1] if self.focus == ('ed', i) else 0}}
        if not self.complete: del rows[15]
        cs = [{'raw': '', 'focus': 0, 'cls': 'TPanel', 'text': ''}] + [{'raw': '', 'cls': r['cb']['cls'], 'text': r['cb']['text'], 'focus': r['cb']['focus']} for r in rows.values()] \
             + [{'cls': r['ed']['cls'], 'text': r['ed']['text'], 'focus': r['ed']['focus']} for r in rows.values()]
        btn = lambda t, y: {'cls': 'TButton', 'text': t, 'x': 342, 'y': y, 'w': 61, 'h': 22, 'enabled': 1, 'focus': int(self.focus == ('btn', t))}
        return {'rows': rows, 'buttons': {'OK': btn('OK', 193), 'Cancel': btn('Cancel', 345)}, 'cs': cs, 'complete': self.complete}

class FakeG:
    """The game as the runner sees it: clicks and keys act on the FakeForm; `drop` names a key or the typing the fake loses (a runner step deleted, an input lost)"""
    def __init__(self, form, drop=()):
        self.form = form; self.clicks = []; self.keys = []; self.typed = []; self.drop = set(drop)
    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        self.clicks.append((c['cls'], c.get('text'), c['x'], c['y'])); self.form.press(c)
    def click(self, x, y, pause=0.4): self.clicks.append(('click', x, y))
    def key(self, *k):
        self.keys.append(k)
        for x in k:
            if x not in self.drop: self.form.key(x)
    def type(self, t):
        self.typed.append(t)
        if 'type' not in self.drop: self.form.type(t)
    def nation_rec(self, n): return b'\0' * 11 + DRAWN[n].encode('latin1') + b'\0' * 100

class Base(unittest.TestCase):
    def setUp(self):
        eog._ATTEMPTS.clear(); P.VERIFIED[:] = []; P.CLICKS[:] = []; P.KEYS[:] = []
        self._o = (P.form_state, P.time.sleep, P.form_wid, eog.gone, P.snap, P.sha, P.CTX.copy())
        P.time.sleep = lambda s: None
        self._time = P.time.time; self._clock = [0.0]
        def clock(): self._clock[0] += 0.5; return self._clock[0]
        P.time.time = clock                                    # a fake clock: every wait loop of the runner times out quickly
        self.g = None
        P.form_state = lambda g: g.form.fs()
        P.snap = lambda g, name: '/nonexistent/' + name; P.sha = lambda p: 'x'
    def tearDown(self):
        P.form_state, P.time.sleep, P.form_wid, eog.gone, P.snap, P.sha = self._o[:6]; P.time.time = self._time; P.CTX.clear(); P.CTX.update(self._o[6])
    def G(self, **kw):
        drop = kw.pop('drop', ()); return FakeG(FakeForm(**kw), drop)
    def step(self, name): return [v for v in P.VERIFIED if v['step'] == name][-1]

class TickTests(Base):
    def test_tick_registers_first_click_and_records_the_state_right_after(self):
        g = self.G(); P.set_tick(g, 1, True); self.assertEqual(len(g.clicks), 1)
        v = self.step('tick Carthage on'); self.assertEqual(v['attempts'], 1)
        self.assertEqual((v['post']['check'], v['post']['edit_enabled'], v['post']['edit_focus'], v['post']['sel0'], v['post']['sel1'], v['post']['textlen']), (1, 1, 1, 0, len(DRAWN[1]), len(DRAWN[1])))
        self.assertTrue(v['others_unchanged']); self.assertEqual(v['post_png'], 'LF_tick_Carthage_on_post.png')
    def test_first_click_only_activates_second_registers(self):
        g = self.G(mode=['activate_first']); P.set_tick(g, 1, True); self.assertEqual(len(g.clicks), 2); self.assertEqual(self.step('tick Carthage on')['attempts'], 2)
    def test_tick_that_never_registers_fails_closed_after_three_clicks(self):
        g = self.G(mode=['activate_first']); g.form.press = lambda c: None
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
        self.assertEqual(len(g.clicks), 3)
    def test_tick_already_in_the_wanted_state_proves_nothing_and_clicks_nothing(self):
        g = self.G(checks=[0, 1] + [0] * 14, enabled=[0, 1] + [0] * 14)
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
        self.assertEqual(g.clicks, [])
    def test_a_disabled_tick_box_is_refused_before_any_click(self):
        g = self.G(cb_enabled=[1, 0] + [1] * 14)
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
        self.assertEqual(g.clicks, [])
    def test_an_incomplete_form_is_refused_before_any_click(self):
        g = self.G(complete=False)
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
        self.assertEqual(g.clicks, [])
    def test_tick_that_changes_another_row_raises_at_once(self):
        g = self.G(mode=['touch_other'])
        with self.assertRaises(_drv.DriverError) as e: P.set_tick(g, 1, True)
        self.assertIn('another row', str(e.exception)); self.assertEqual(len(g.clicks), 1)
    def test_a_tick_that_does_not_wake_the_name_box_is_not_accepted(self):
        g = self.G(mode=['nowake'])
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
        self.assertLessEqual(len(g.clicks), 3); self.assertEqual([v for v in P.VERIFIED if v['step'].startswith('tick')], [])
    def test_a_tick_without_focus_on_the_name_box_is_not_accepted(self):
        g = self.G(mode=['nofocus'])
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
    def test_a_tick_without_the_whole_text_selected_is_not_accepted(self):
        g = self.G(mode=['noselect'])
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
    def test_untick_restores_the_drawn_leader_and_greys_the_box(self):
        g = self.G(); P.set_tick(g, 1, True); P.edit_text(g, 1, 'Zed'); P.set_tick(g, 1, False)
        v = self.step('tick Carthage off'); self.assertEqual((v['post']['text'], v['post']['edit_enabled'], v['post']['edit_focus']), (DRAWN[1], 0, 0)); self.assertEqual(v['stored'], DRAWN[1])
    def test_an_untick_that_keeps_the_typed_text_is_not_accepted(self):
        g = self.G(mode=['norestore']); P.set_tick(g, 1, True); P.edit_text(g, 1, 'Zed')
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, False)

class EditTests(Base):
    def test_edit_of_a_greyed_box_clicks_nothing(self):
        g = self.G()
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
        self.assertEqual(g.clicks, [])
    def test_edit_sends_select_delete_and_the_typed_text_and_the_box_reads_it_back(self):
        g = self.G(); P.set_tick(g, 1, True); P.edit_text(g, 1, 'Zed')
        self.assertEqual([k for k in g.keys if k[0] in ('End', 'shift+Home', 'BackSpace')], [('End',), ('shift+Home',), ('BackSpace',)]); self.assertEqual(g.typed, ['Zed'])
        v = self.step('name Carthage'); self.assertEqual(v['read'], 'Zed'); self.assertEqual(g.form.texts[1], 'Zed')
        self.assertEqual((v['stages']['selected']['sel0'], v['stages']['selected']['sel1']), (0, len(DRAWN[1]))); self.assertEqual(v['stages']['deleted']['text'], '')
    def test_edit_cut_to_the_limit_is_the_expected_text(self):
        g = self.G(); P.set_tick(g, 1, True); P.edit_text(g, 1, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        self.assertEqual(self.step('name Carthage')['read'], 'ABCDEFGHIJKLMNOPQRSTUVWXY'); self.assertEqual(g.form.texts[1], 'ABCDEFGHIJKLMNOPQRSTUVWXY')
    def test_an_empty_name_is_typed_as_nothing(self):
        g = self.G(); P.set_tick(g, 1, True); P.edit_text(g, 1, ''); self.assertEqual(g.typed, []); self.assertEqual(g.form.texts[1], '')
    def test_deleting_the_select_step_makes_the_edit_fail(self):
        g = self.G(drop=['shift+Home']); P.set_tick(g, 1, True)
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
    def test_deleting_the_backspace_makes_the_edit_fail(self):
        g = self.G(drop=['BackSpace']); P.set_tick(g, 1, True)
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
        self.assertNotEqual(g.form.texts[1], 'Zed')
    def test_deleting_the_typing_makes_the_edit_fail(self):
        g = self.G(drop=['type']); P.set_tick(g, 1, True)
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
    def test_edit_without_focus_is_retried_then_fails_closed_and_nothing_is_typed(self):
        g = self.G(); P.set_tick(g, 1, True); g.form.press = lambda c: None      # the click never focuses the box
        g.form.focus = ('btn', 'OK'); n0 = len(g.clicks)
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
        self.assertEqual(len(g.clicks) - n0, 3); self.assertEqual(g.typed, [])
    def test_typing_that_changes_another_row_raises_at_once(self):
        g = self.G(); P.set_tick(g, 1, True); g.form.mode.add('touch_other')
        with self.assertRaises(_drv.DriverError) as e: P.edit_text(g, 1, 'Zed')
        self.assertIn('another row', str(e.exception)); self.assertEqual(len(g.clicks) - 1, 1)
    def test_an_incomplete_form_is_refused_by_the_edit(self):
        g = self.G(complete=False, checks=[0, 1] + [0] * 14)
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
        self.assertEqual(g.clicks, [])
    def test_typing_into_a_greyed_box_that_changes_is_an_error(self):
        g = self.G(); g.form.type = lambda t: g.form.texts.__setitem__(0, 'XYZ')
        with self.assertRaises(_drv.DriverError): P.try_edit_disabled(g, 0, 'XYZ')
    def test_typing_into_a_greyed_box_that_does_not_change_is_recorded(self):
        g = self.G(); P.try_edit_disabled(g, 0, 'XYZ'); self.assertTrue(self.step('greyed name box Rome refuses typing')['unchanged'])
    def test_try_edit_disabled_refuses_an_enabled_box(self):
        g = self.G(checks=[1] + [0] * 15)
        with self.assertRaises(_drv.DriverError): P.try_edit_disabled(g, 0, 'XYZ')
        self.assertEqual(g.clicks, [])

class ButtonTests(Base):
    def test_button_missing_clicks_nothing(self):
        g = self.G(); P.form_wid = lambda g_: 77; g.form.fs = (lambda f: (lambda: {**f(), 'buttons': {}})) (g.form.fs)
        with self.assertRaises(_drv.DriverError): P.press_button(g, 'OK')
        self.assertEqual(g.clicks, [])
    def test_disabled_button_clicks_nothing(self):
        g = self.G(); P.form_wid = lambda g_: 77
        def fs():
            d = FakeForm.fs(g.form); d['buttons']['OK']['enabled'] = 0; return d
        g.form.fs = fs
        with self.assertRaises(_drv.DriverError): P.press_button(g, 'OK')
        self.assertEqual(g.clicks, [])
    def test_button_that_never_closes_the_form_fails_closed_after_three_clicks(self):
        g = self.G(); P.form_wid = lambda g_: 77; eog.gone = lambda g_, w, timeout=5: False
        with self.assertRaises(_drv.DriverError): P.press_button(g, 'OK')
        self.assertEqual(len(g.clicks), 3)
    def test_button_closes_second_click(self):
        g = self.G(); P.form_wid = lambda g_: 77; res = iter([False, True]); eog.gone = lambda g_, w, timeout=5: next(res)
        self.assertEqual(P.press_button(g, 'Cancel'), 2); self.assertEqual(len(g.clicks), 2)
    def test_no_form_means_no_click(self):
        g = self.G(); P.form_wid = lambda g_: None
        with self.assertRaises(_drv.DriverError): P.press_button(g, 'OK')
        self.assertEqual(g.clicks, [])
    def test_key_close_bounded_and_fails_closed(self):
        g = self.G(); P.form_wid = lambda g_: 77; eog.gone = lambda g_, w, timeout=5: False
        with self.assertRaises(_drv.DriverError): P.press_key_close(g, 'Escape')
        self.assertEqual(len(g.keys), 2)

class KeyboardTests(Base):
    def test_tab_walk_is_bounded(self):
        g = self.G()
        with self.assertRaises(_drv.DriverError): P.focus_checkbox_by_tab(g, 1, max_tabs=5)
        self.assertEqual(len(g.keys), 5)
    def test_space_without_focus_on_the_tick_box_sends_nothing(self):
        g = self.G()
        with self.assertRaises(_drv.DriverError): P.key_toggle(g, 1)
        self.assertEqual(g.keys, [])
    def test_space_on_the_focused_tick_box_ticks_it_and_leaves_the_name_box_as_it_is(self):
        g = self.G(); g.form.focus = ('cb', 1); P.key_toggle(g, 1); v = self.step('space on tick Carthage')
        self.assertEqual((v['post']['check'], v['post']['edit_enabled']), (1, 0)); self.assertEqual(len(g.keys), 1)
    def test_space_that_changes_nothing_fails_closed_after_two_presses(self):
        g = self.G(drop=['space']); g.form.focus = ('cb', 1)
        with self.assertRaises(_drv.DriverError): P.key_toggle(g, 1)
        self.assertEqual(len(g.keys), 2)
    def test_space_that_changes_another_row_raises_at_once(self):
        g = self.G(mode=['touch_other']); g.form.focus = ('cb', 1)
        with self.assertRaises(_drv.DriverError): P.key_toggle(g, 1)
        self.assertEqual(len(g.keys), 1)
    def test_form_text_is_read_as_latin1_not_utf8(self):
        import subprocess
        line = 'TEdit\t\xfcnal\t1\t2\t3\t4\t1\t1\t-1\t25\t0\t0\t0\t540100c0\r\n'.encode('latin1')
        o = subprocess.run; subprocess.run = lambda *a, **k: type('R', (), {'stdout': line})()
        try: cs = P.read_controls(None)
        finally: subprocess.run = o
        self.assertEqual(cs[0]['text'], '\xfcnal')

class MenuG:
    """the game as the menu helpers see it: keys and clicks recorded, a screen of 1280 x 1024 with one window"""
    def __init__(self): self.clicks = []; self.keys = []
    def key(self, *k): self.keys.append(k); P.KEYS.append({'keys': list(k)})
    def click(self, x, y, pause=0.4): self.clicks.append((x, y)); P.CLICKS.append({'x': x, 'y': y})
    def screen_size(self): return 1280, 1024
    def find_windows(self, pat='.', visible=True): return [(5, 'Imperial Conquest 2', 0, 0, 1143, 903)]

class ResetAndMenuTests(Base):
    def setUp(self):
        Base.setUp(self)
        self._m = (P.pointer_at, P.root_window_id, P.ocr_word, P.form_wid)
        P.root_window_id = lambda: 99
        P.pointer_at = lambda x, y: {'x': x, 'y': y, 'window': 99 if (x > 1143 or y > 903) else 5}
    def tearDown(self): P.pointer_at, P.root_window_id, P.ocr_word, P.form_wid = self._m; Base.tearDown(self)
    def test_reset_clicks_a_located_point_whose_pointer_window_is_the_root(self):
        g = MenuG(); P.verified_reset(g); (x, y), = g.clicks
        self.assertNotEqual((x, y), (1000, 900)); v = self.step('reset'); self.assertEqual(v['pointer']['window'], v['root']); self.assertEqual(g.keys, [('Escape',), ('Escape',)])
        self.assertEqual(v['clicks'], [0, 1]); self.assertEqual(v['keys'], [0, 2])
    def test_reset_with_no_bare_point_clicks_nothing(self):
        g = MenuG(); P.pointer_at = lambda x, y: {'x': x, 'y': y, 'window': 5}
        with self.assertRaises(_drv.DriverError): P.verified_reset(g)
        self.assertEqual(g.clicks, [])
    def test_reset_skips_a_candidate_a_window_covers(self):
        g = MenuG(); g.find_windows = lambda pat='.', visible=True: [(5, 'big', 0, 0, 1280, 1000)]
        P.verified_reset(g); (x, y), = g.clicks; self.assertGreaterEqual(y, 1000)
    def test_menu_open_that_never_opens_fails_after_three_attempts_with_bounded_clicks(self):
        g = MenuG(); P.ocr_word = lambda g_, regions, word, tries=3: (15, 37, 11) if word == 'file' else None
        with self.assertRaises(_drv.DriverError): P.menu_open(g, 'file', 'new', P.NEW_REGIONS)
        self.assertEqual(len(g.clicks), 6)                       # 3 x (a located reset point + the bar word)
        self.assertEqual([v['ok'] for v in P.VERIFIED if v['step'] == 'menu open file'], [False] * 3)
    def test_menu_open_activation_only_first_click_is_retried_and_both_attempts_are_recorded(self):
        g = MenuG(); n = [0]
        def ocr(g_, regions, word, tries=3):
            if word == 'file': return (15, 37, 11)
            n[0] += 1; return (30, 57, 11) if n[0] == 2 else None
        P.ocr_word = ocr; hit, attempts = P.menu_open(g, 'file', 'new', P.NEW_REGIONS)
        self.assertEqual(attempts, 2); self.assertEqual([v['ok'] for v in P.VERIFIED if v['step'] == 'menu open file'], [False, True])
    def test_menu_open_with_the_bar_word_missing_clicks_no_bar_word(self):
        g = MenuG(); P.ocr_word = lambda g_, regions, word, tries=3: None
        with self.assertRaises(_drv.DriverError): P.menu_open(g, 'file', 'new', P.NEW_REGIONS)
        self.assertNotIn((15, 37), g.clicks); self.assertEqual(len(g.clicks), 3)                  # only the three resets
    def test_menu_new_requires_the_form_after_the_item_click(self):
        g = MenuG(); P.ocr_word = lambda g_, regions, word, tries=3: (15, 37, 11) if word == 'file' else (30, 57, 11)
        P.form_wid = lambda g_: None; g.find_windows = lambda pat='.', visible=True: [(5, 'Imperial Conquest 2', 0, 0, 1143, 903)] if pat == '.' else []
        with self.assertRaises(_drv.DriverError): P.menu_new(g, tries=2)
        self.assertEqual([v['ok'] for v in P.VERIFIED if v['step'] == 'menu item New'], [False, False])
    def test_menu_new_succeeds_when_the_form_appears(self):
        g = MenuG(); P.ocr_word = lambda g_, regions, word, tries=3: (15, 37, 11) if word == 'file' else (30, 57, 11); P.form_wid = lambda g_: 8388618
        self.assertEqual(P.menu_new(g), 8388618); self.assertEqual([v['step'] for v in P.VERIFIED], ['reset', 'menu open file', 'menu item New'])
    def test_menu_close_that_leaves_the_dropdown_open_fails(self):
        g = MenuG(); P.ocr_word = lambda g_, regions, word, tries=3: (1, 1, 11)
        with self.assertRaises(_drv.DriverError): P.menu_close(g, 'file', 'save', [P.DROP])

class Game3Tests(Base):
    """the click of the real Game3: the pointer is read back from the X server and must be where the click goes; a control click needs a fresh read of the control"""
    def setUp(self):
        Base.setUp(self); self._p = (P.pointer_at, P.MyGame.click, P.read_controls)
        self.sent = []; P.MyGame.click = lambda self_, x, y, pause=0.4: self.sent.append((x, y))
        self.g = P.Game3.__new__(P.Game3)
    def tearDown(self): P.pointer_at, P.MyGame.click, P.read_controls = self._p; Base.tearDown(self)
    def test_a_click_whose_pointer_is_elsewhere_is_not_sent(self):
        P.pointer_at = lambda x, y: {'x': x + 3, 'y': y, 'window': 5}
        with self.assertRaises(_drv.DriverError): self.g.click(10, 10)
        self.assertEqual(self.sent, []); self.assertEqual(P.CLICKS, [])
    def test_a_click_is_recorded_with_the_pointer_read_back(self):
        P.pointer_at = lambda x, y: {'x': x, 'y': y, 'window': 5}; P.CTX['why'] = 'reason'; self.g.click(10, 12)
        self.assertEqual(P.CLICKS[-1]['pointer'], {'x': 10, 'y': 12, 'window': 5}); self.assertEqual(self.sent, [(10, 12)])
    def test_a_control_that_is_not_in_a_fresh_read_is_not_clicked(self):
        P.form_wid = lambda g_: 77; P.read_controls = lambda g_, title=P.TITLE: [{'cls': 'TButton', 'text': 'OK', 'x': 1, 'y': 1, 'w': 5, 'h': 5, 'line': 'l'}]
        P.pointer_at = lambda x, y: {'x': x, 'y': y, 'window': 5}
        with self.assertRaises(_drv.DriverError): self.g.click_control({'cls': 'TButton', 'text': 'OK', 'x': 2, 'y': 1, 'w': 5, 'h': 5})
        self.assertEqual(self.sent, [])
    def test_a_control_in_a_fresh_read_is_clicked_with_its_verbatim_line_recorded(self):
        P.form_wid = lambda g_: 77; P.read_controls = lambda g_, title=P.TITLE: [{'cls': 'TButton', 'text': 'OK', 'x': 1, 'y': 1, 'w': 6, 'h': 4, 'line': 'TButton\tOK\t1\t1\t6\t4'}]
        P.pointer_at = lambda x, y: {'x': x, 'y': y, 'window': 5}; self.g.click_control({'cls': 'TButton', 'text': 'OK', 'x': 1, 'y': 1, 'w': 6, 'h': 4})
        self.assertEqual(self.sent, [(4, 3)]); self.assertEqual(P.CLICKS[-1]['target']['line'], 'TButton\tOK\t1\t1\t6\t4')

class GuessedCoordinateTests(unittest.TestCase):
    """no runner path may click an inherited guessed or fixed coordinate (Game.new_game, Game.menu, dismiss_popups ...), and every click site of the runner is accounted for"""
    HERE = os.path.dirname(os.path.abspath(__file__))
    FORBID = {'save_as', 'tool', 'dismiss_popups', 'calibrate_toolbar', 'calibrate_army_toolbar', 'calibrate_fleet_toolbar', 'calibrate_battle_toolbar', 'open_dialog', 'close_dialog',
              'reset_ui', 'neutral_point', 'new_game', 'army_tool', 'fleet_tool', 'menu', 'recruit', 'hire_mercs', 'end_turn', 'end_turn_proven', 'play_battle', 'split_army', 'disband_army', 'embark', 'NEWGAME_TICK'}
    def sources(self):
        import ast, glob
        for p in sorted(glob.glob(os.path.join(self.HERE, '*.py'))):
            if os.path.basename(p).startswith('test_'): continue
            yield os.path.basename(p), ast.parse(open(p).read(), p)
    @staticmethod
    def constant(a, consts):
        import ast
        return (isinstance(a, ast.Constant) and isinstance(a.value, (int, float))) or (isinstance(a, ast.Name) and a.id in consts)
    @staticmethod
    def constant_names(tree):
        import ast
        names = set()
        for n in ast.walk(tree):
            pairs = []
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Tuple) and isinstance(n.value, ast.Tuple): pairs += list(zip(t.elts, n.value.elts))
                    else: pairs.append((t, n.value))
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and n.value is not None: pairs.append((n.target, n.value))
            for t, v in pairs:
                if isinstance(t, ast.Name) and isinstance(v, ast.Constant) and isinstance(v.value, (int, float)) and not isinstance(v.value, bool): names.add(t.id)
        return names
    def violations(self, name, tree):
        import ast
        out = []; consts = self.constant_names(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in self.FORBID: out.append('%s:%d calls .%s(): an inherited path with guessed or fixed coordinates' % (name, n.lineno, n.func.attr))
            if isinstance(n, ast.Name) and n.id == 'NEUTRAL' or isinstance(n, ast.Attribute) and n.attr == 'NEUTRAL': out.append('%s:%d uses the driver\'s fixed neutral point' % (name, n.lineno))
            if isinstance(n, ast.Attribute) and n.attr == 'NEWGAME_TICK': out.append('%s:%d uses the driver\'s fixed tick-box layout' % (name, n.lineno))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('click', 'click_control', 'click_tile', 'mousemove') and any(self.constant(a, consts) for a in n.args[:2]):
                out.append('%s:%d: a click at a constant coordinate' % (name, n.lineno))
        return out
    def test_no_forbidden_driver_call_and_no_constant_coordinate(self):
        for name, tree in self.sources(): self.assertEqual(self.violations(name, tree), [])
    def test_the_guard_catches_each_way_back(self):
        import ast
        for snippet in ('g.new_game(rows=[1])', 'g.menu("file", 0)', 'g.dismiss_popups()', 'g.click(640, 500)', 'g.click_control(c); g.click(10, y)', 'g.calibrate_army_toolbar()', 'g.NEWGAME_TICK', 'g.reset_ui()', 'g.neutral_point()', 'from harness.driver import NEUTRAL\ng.click(*NEUTRAL)', 'self.reset_ui()',
                        'x = 640; y = 500; g.click(x, y)', 'x, y = 640, 500; g.click(x, y)', 'def f(g):\n    y = 500\n    g.click(xx, y)'):
            self.assertTrue(self.violations('snippet.py', ast.parse(snippet)), snippet)
        self.assertEqual(self.violations('snippet.py', ast.parse('g.click(x, ARMY_Y)')), [])
    def test_every_click_site_is_accounted_for(self):
        import ast
        sites = set()
        for name, tree in self.sources():
            for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
                for n in ast.walk(fn):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('click', 'click_control', 'click_tile', 'mousemove'):
                        sites.add((name, fn.name, n.func.attr, ', '.join(ast.unparse(a) for a in n.args if not isinstance(a, ast.Constant))))
        # each site below was read: its coordinates come from a control enumerated by the running form (win_state.exe / Game.controls), or an OCR word of this run; a NEW click site must be added here by a reviewer
        self.assertEqual(sorted(sites), sorted(self.EXPECTED), sorted(sites ^ set(self.EXPECTED)))
    EXPECTED = [
        ('eog.py', 'answer_confirm', 'click_control', 'c'),
        ('eog.py', 'close_boxes', 'click_control', 'ok'),
        ('play_lib.py', 'click', 'click', 'self, x, y, pause'),
        ('play_lib.py', 'click_control', 'click_control', 'self, c, fx, fy, pause'),
        ('play_lib.py', 'edit_text', 'click_control', 'c'),
        ('play_lib.py', 'menu_new', 'click', 'n[0], n[1]'),
        ('play_lib.py', 'menu_open', 'click', 'f[0], f[1]'),
        ('play_lib.py', 'press_button', 'click_control', 'btn'),
        ('play_lib.py', 'set_tick', 'click_control', 'c'),
        ("play_lib.py", 'try_edit_disabled', 'click_control', "row['ed']"),
        ('play_lib.py', 'verified_reset', 'click', 'x, y'),
    ]

if __name__ == '__main__': unittest.main()
