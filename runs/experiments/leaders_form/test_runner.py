"""Tests of the leaders-form runner's click discipline: every intermediate click (a tick, a name edit, a button, a menu word) is verified, retried at most twice, and fails closed (DriverError) when its effect
does not show; a control that is missing or greyed stops the run with nothing clicked; no runner path clicks an inherited guessed or fixed coordinate (an AST guard over every source of this folder).
usage: python3 -m unittest test_runner   (no display needed: the game object is a fake)"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import play_lib as P, eog
from eog import _drv

def make_fs(checks=None, texts=None, enabled=None):
    checks = checks or [0] * 16; texts = texts or ['n%d' % i for i in range(16)]; enabled = enabled if enabled is not None else [c for c in checks]
    rows = {}
    for i in range(16):
        rows[i] = {'nation': P.NATIONS[i], 'panel': {}, 'cb': {'cls': 'TCheckBox', 'text': '', 'x': 111, 'y': 100 + 20 * i, 'w': 17, 'h': 14, 'enabled': 1, 'check': checks[i], 'focus': 0},
                   'ed': {'cls': 'TEdit', 'text': texts[i], 'x': 171, 'y': 100 + 20 * i, 'w': 148, 'h': 16, 'enabled': enabled[i], 'check': -1, 'limit': 25, 'focus': 0}}
    return {'rows': rows, 'buttons': {'OK': {'cls': 'TButton', 'text': 'OK', 'x': 342, 'y': 193, 'w': 61, 'h': 22}, 'Cancel': {'cls': 'TButton', 'text': 'Cancel', 'x': 342, 'y': 345, 'w': 61, 'h': 21}}, 'cs': [{'raw': '', 'focus': 0, 'cls': 'TPanel'}], 'complete': True}

class FakeG:
    """A game whose form is a list of states; `script` says what each click_control does to it"""
    def __init__(self, fs, on_click=None): self.fs = fs; self.clicks = []; self.keys = []; self.typed = []; self.on_click = on_click
    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        self.clicks.append((c['cls'], c.get('text'), c['x'], c['y']))
        if self.on_click: self.on_click(self, c)
    def click(self, x, y, pause=0.4): self.clicks.append(('click', x, y))
    def key(self, *k): self.keys.append(k)
    def type(self, t): self.typed.append(t)

class Base(unittest.TestCase):
    def setUp(self):
        eog._ATTEMPTS.clear(); P.VERIFIED[:] = []
        self._o = (P.form_state, P.settle_state, P.time.sleep, P.form_wid, eog.gone)
        P.time.sleep = lambda s: None
        P.form_state = lambda g: g.fs
        def settle(g, cond, timeout=3.0):
            fs = g.fs
            for _ in range(2):
                if cond(fs): return fs, True
            return fs, False
        P.settle_state = settle
    def tearDown(self): P.form_state, P.settle_state, P.time.sleep, P.form_wid, eog.gone = self._o

class TickTests(Base):
    def test_tick_registers_first_click(self):
        def on(g, c): g.fs = make_fs(checks=[0, 1] + [0] * 14)
        g = FakeG(make_fs(), on); P.set_tick(g, 1, True); self.assertEqual(len(g.clicks), 1); self.assertEqual(P.VERIFIED[-1]['attempts'], 1)
    def test_tick_first_click_only_activates_second_registers(self):
        n = [0]
        def on(g, c):
            n[0] += 1
            if n[0] == 2: g.fs = make_fs(checks=[0, 1] + [0] * 14)
        g = FakeG(make_fs(), on); P.set_tick(g, 1, True); self.assertEqual(len(g.clicks), 2); self.assertEqual(P.VERIFIED[-1]['attempts'], 2)
    def test_tick_that_never_registers_fails_closed_after_three_clicks(self):
        g = FakeG(make_fs())
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
        self.assertEqual(len(g.clicks), 3)
    def test_tick_already_in_the_wanted_state_proves_nothing_and_clicks_nothing(self):
        g = FakeG(make_fs(checks=[0, 1] + [0] * 14))
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
        self.assertEqual(g.clicks, [])
    def test_tick_that_changes_another_row_is_an_error(self):
        def on(g, c): g.fs = make_fs(checks=[1, 1] + [0] * 14)
        g = FakeG(make_fs(), on)
        with self.assertRaises(_drv.DriverError): P.set_tick(g, 1, True)
    def test_untick(self):
        def on(g, c): g.fs = make_fs(checks=[0] * 16)
        g = FakeG(make_fs(checks=[0, 1] + [0] * 14), on); P.set_tick(g, 1, False); self.assertEqual(len(g.clicks), 1)

class EditTests(Base):
    def test_edit_of_a_greyed_box_clicks_nothing(self):
        g = FakeG(make_fs())
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
        self.assertEqual(g.clicks, [])
    def test_edit_cut_to_the_limit_is_the_expected_text(self):
        def on(g, c):
            g.fs = make_fs(checks=[0, 1] + [0] * 14, texts=['n0', 'ABCDEFGHIJKLMNOPQRSTUVWXY'] + ['n%d' % i for i in range(2, 16)]); g.fs['rows'][1]['ed']['focus'] = 1
        g = FakeG(make_fs(checks=[0, 1] + [0] * 14), on)
        P.edit_text(g, 1, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        self.assertEqual(P.VERIFIED[-1]['read'], 'ABCDEFGHIJKLMNOPQRSTUVWXY')
    def test_edit_whose_text_never_matches_fails_closed_after_three_rounds(self):
        def on(g, c): g.fs['rows'][1]['ed']['focus'] = 1
        g = FakeG(make_fs(checks=[0, 1] + [0] * 14), on)
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
        self.assertEqual(len(g.clicks), 3)
    def test_edit_without_focus_is_retried_then_fails_closed(self):
        g = FakeG(make_fs(checks=[0, 1] + [0] * 14))
        with self.assertRaises(_drv.DriverError): P.edit_text(g, 1, 'Zed')
        self.assertEqual(len(g.clicks), 3); self.assertEqual(g.typed, [])        # nothing was typed into a box that never took the focus
    def test_typing_into_a_greyed_box_that_changes_is_an_error(self):
        def typ(g, t): g.fs = make_fs(texts=['XYZ'] + ['n%d' % i for i in range(1, 16)])
        g = FakeG(make_fs()); g.type = lambda t: typ(g, t)
        with self.assertRaises(_drv.DriverError): P.try_edit_disabled(g, 0, 'XYZ')

class ButtonTests(Base):
    def test_button_missing_clicks_nothing(self):
        fs = make_fs(); del fs['buttons']['OK']; g = FakeG(fs); P.form_wid = lambda g_: 77
        with self.assertRaises(_drv.DriverError): P.press_button(g, 'OK')
        self.assertEqual(g.clicks, [])
    def test_button_that_never_closes_the_form_fails_closed_after_three_clicks(self):
        g = FakeG(make_fs()); P.form_wid = lambda g_: 77; eog.gone = lambda g_, w, timeout=5: False
        with self.assertRaises(_drv.DriverError): P.press_button(g, 'OK')
        self.assertEqual(len(g.clicks), 3)
    def test_button_closes_second_click(self):
        g = FakeG(make_fs()); P.form_wid = lambda g_: 77; res = iter([False, True]); eog.gone = lambda g_, w, timeout=5: next(res)
        self.assertEqual(P.press_button(g, 'Cancel'), 2); self.assertEqual(len(g.clicks), 2)
    def test_no_form_means_no_click(self):
        g = FakeG(make_fs()); P.form_wid = lambda g_: None
        with self.assertRaises(_drv.DriverError): P.press_button(g, 'OK')
        self.assertEqual(g.clicks, [])
    def test_key_close_bounded_and_fails_closed(self):
        g = FakeG(make_fs()); P.form_wid = lambda g_: 77; eog.gone = lambda g_, w, timeout=5: False
        with self.assertRaises(_drv.DriverError): P.press_key_close(g, 'Escape')
        self.assertEqual(len(g.keys), 2)

class KeyboardTests(Base):
    def test_tab_walk_is_bounded(self):
        g = FakeG(make_fs())
        with self.assertRaises(_drv.DriverError): P.focus_checkbox_by_tab(g, 1, max_tabs=5)
        self.assertEqual(len(g.keys), 5)
    def test_space_that_changes_nothing_fails_closed_after_two_presses(self):
        g = FakeG(make_fs())
        with self.assertRaises(_drv.DriverError): P.key_toggle(g, 1)
        self.assertEqual(len(g.keys), 2)

class MenuTests(Base):
    def test_menu_new_without_words_clicks_only_the_reset(self):
        class G(FakeG):
            def reset_ui(self): self.clicks.append('reset')
        g = G(make_fs()); o = P.ocr_word; P.ocr_word = lambda g_, r, w, tries=3: None
        try:
            with self.assertRaises(_drv.DriverError): P.menu_new(g)
        finally: P.ocr_word = o
        self.assertEqual([c for c in g.clicks if c != 'reset'], [])
    def test_form_text_is_read_as_latin1_not_utf8(self):
        import subprocess
        line = 'TEdit\t\xfcnal\t1\t2\t3\t4\t1\t1\t-1\t25\t0\t0\t0\t540100c0\r\n'.encode('latin1')
        o = subprocess.run; subprocess.run = lambda *a, **k: type('R', (), {'stdout': line})()
        try: cs = P.read_controls(None)
        finally: subprocess.run = o
        self.assertEqual(cs[0]['text'], '\xfcnal')

class GuessedCoordinateTests(unittest.TestCase):
    """no runner path may click an inherited guessed or fixed coordinate (Game.new_game, Game.menu, dismiss_popups ...), and every click site of the runner is accounted for"""
    HERE = os.path.dirname(os.path.abspath(__file__))
    FORBID = {'save_as', 'tool', 'dismiss_popups', 'calibrate_toolbar', 'calibrate_army_toolbar', 'calibrate_fleet_toolbar', 'calibrate_battle_toolbar', 'open_dialog', 'close_dialog',
              'new_game', 'army_tool', 'fleet_tool', 'menu', 'recruit', 'hire_mercs', 'end_turn', 'end_turn_proven', 'play_battle', 'split_army', 'disband_army', 'embark', 'NEWGAME_TICK'}
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
            if isinstance(n, ast.Attribute) and n.attr == 'NEWGAME_TICK': out.append('%s:%d uses the driver\'s fixed tick-box layout' % (name, n.lineno))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('click', 'click_control', 'click_tile', 'mousemove') and any(self.constant(a, consts) for a in n.args[:2]):
                out.append('%s:%d: a click at a constant coordinate' % (name, n.lineno))
        return out
    def test_no_forbidden_driver_call_and_no_constant_coordinate(self):
        for name, tree in self.sources(): self.assertEqual(self.violations(name, tree), [])
    def test_the_guard_catches_each_way_back(self):
        import ast
        for snippet in ('g.new_game(rows=[1])', 'g.menu("file", 0)', 'g.dismiss_popups()', 'g.click(640, 500)', 'g.click_control(c); g.click(10, y)', 'g.calibrate_army_toolbar()', 'g.NEWGAME_TICK',
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
        ('eog.py', 'click_ok', 'click_control', "g.control(cs, text='OK')"),
        ('eog.py', 'close_boxes', 'click_control', 'ok'),
        ('eog.py', 'menu_pick', 'click', 'bar[0][1], bar[0][2]'),
        ('eog.py', 'menu_pick', 'click', 'hit[0][1], hit[0][2]'),
        ('lib.py', 'menu_step', 'click', 'hit[0][1], hit[0][2]'),
        ('play_lib.py', 'click', 'click', 'self, x, y, pause'),
        ('play_lib.py', 'click_control', 'click_control', 'self, c, fx, fy, pause'),
        ('play_lib.py', 'edit_text', 'click_control', 'c'),
        ('play_lib.py', 'menu_new', 'click', 'f[0], f[1]'),
        ('play_lib.py', 'menu_new', 'click', 'n[0], n[1]'),
        ('play_lib.py', 'press_button', 'click_control', 'b'),
        ('play_lib.py', 'set_tick', 'click_control', 'c'),
        ("play_lib.py", 'try_edit_disabled', 'click_control', "row['ed']"),
        ('scenarios.py', 'menu_probe', 'click', 'f[0], f[1]'),
    ]

if __name__ == '__main__': unittest.main()
