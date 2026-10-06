"""Tests of the runner's click discipline and of its verified transitions (R2: an intermediate selection or an order whose expected effect does not show fails closed; R3: no guessed-coordinate path): a box without an OK control raises and NOTHING is clicked (play_lib.close_all, which is also the only way the runner's own load path clears boxes,
and eog.close_boxes). usage: python3 -m unittest test_runner   (no display needed: the game object is a fake)"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import play_lib, eog
from eog import _drv

class FakeG:
    def __init__(self, controls): self._controls = controls; self.clicks = []
    def popups(self): return [(8388700, 'Information', 500, 480, 296, 96)]
    def controls(self, title): return self._controls
    def click(self, *a, **k): self.clicks.append(('click', a))
    def click_control(self, *a, **k): self.clicks.append(('click_control', a))
    def read_popup(self, w): return 'a box'
    def find_windows(self, *a, **k): return [(8388700, 'Information', 500, 480, 296, 96)]

class T(unittest.TestCase):
    def setUp(self): eog._ATTEMPTS.clear()
    def test_close_all_without_ok_control_raises_and_clicks_nothing(self):
        g = FakeG([{'cls': 'TButton', 'text': 'Cancel', 'x': 1, 'y': 1, 'w': 5, 'h': 5}])
        with self.assertRaises(_drv.DriverError): play_lib.close_all(g, 'test')
        self.assertEqual(g.clicks, [])
    def test_close_all_with_no_controls_at_all_raises_and_clicks_nothing(self):
        class G2(FakeG):
            def controls(self, title): raise _drv.DriverError('no controls found')
        g = G2([])
        with self.assertRaises(Exception): play_lib.close_all(g, 'test')
        self.assertEqual(g.clicks, [])
    def test_eog_close_boxes_without_ok_control_raises_and_clicks_nothing(self):
        g = FakeG([])
        with self.assertRaises(_drv.DriverError): eog.close_boxes(g)
        self.assertEqual(g.clicks, [])
    def test_no_geometric_fallback_in_the_runner_sources(self):
        import re
        here = os.path.dirname(os.path.abspath(__file__))
        for f in ('play_lib.py', 'scenarios.py', 'eog.py', 'run_play.py'):
            src = open(os.path.join(here, f)).read()
            self.assertIsNone(re.search(r'g\.click\(x \+ w|click\(x \+ wd|y \+ h - 24|y \+ ht - 24|dismiss_popups\(', src), f)

class FakeDlg:
    """a game whose dialog `D` has one button; `plan` says what a click does: 'nothing', 'change' (the dialog pixels change) or 'box' (a message box appears)"""
    def __init__(self, plan, controls=None):
        self.plan = list(plan); self.clicks = 0; self.hash = 0; self.box = False
        self._controls = controls or [{'cls': 'TButton', 'text': 'Go', 'x': 10, 'y': 10, 'w': 50, 'h': 20}]
    def find_windows(self, pat, visible=True): return [(1, 'D', 0, 0, 300, 200)]
    def controls(self, title): return self._controls
    def control(self, cs, text=None, cls=None, index=0):
        return [c for c in cs if text is None or c['text'] == text][index]
    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        self.clicks += 1
        what = self.plan.pop(0) if self.plan else 'nothing'
        if what == 'change': self.hash += 1
        elif what == 'box': self.box = True

class Patched(unittest.TestCase):
    def setUp(self):
        eog._ATTEMPTS.clear(); play_lib.VERIFIED[:] = []
        self._o = (play_lib._region_hash, play_lib.boxes, play_lib.time.sleep)
        self.g = None
        play_lib._region_hash = lambda g, rect: g.hash
        play_lib.boxes = lambda g: [(2, 'Information', 0, 0, 200, 100)] if getattr(g, 'box', False) else []
        play_lib.time.sleep = lambda s: setattr(self, '_slept', getattr(self, '_slept', 0) + s) or None
        self._real_time = play_lib.time.time; self._t = [0.0]
        play_lib.time.time = lambda: self._t.__setitem__(0, self._t[0] + 0.5) or self._t[0]       # every poll advances a fake clock: no real waiting
    def tearDown(self):
        play_lib._region_hash, play_lib.boxes, play_lib.time.sleep = self._o; play_lib.time.time = self._real_time

class TransitionTests(Patched):
    def test_press_box_appears(self):
        g = FakeDlg(['box']); self.assertEqual(play_lib.press(g, 'D', 'Go'), 'box'); self.assertEqual(g.clicks, 1)
    def test_press_click_that_does_not_register_is_retried_then_fails_closed(self):
        g = FakeDlg([])
        with self.assertRaises(_drv.DriverError): play_lib.press(g, 'D', 'Go')
        self.assertEqual(g.clicks, 3)                        # bounded: exactly three clicks, never more
    def test_press_first_click_only_activates_second_registers(self):
        g = FakeDlg(['nothing', 'box']); self.assertEqual(play_lib.press(g, 'D', 'Go'), 'box'); self.assertEqual(g.clicks, 2)
    def test_press_change_without_box_when_a_box_is_expected_fails_at_once(self):
        g = FakeDlg(['change'])
        with self.assertRaises(_drv.DriverError) as e: play_lib.press(g, 'D', 'Go')
        self.assertEqual(g.clicks, 1); self.assertIn('accepted', str(e.exception))
    def test_press_box_or_change_accepts_a_change(self):
        g = FakeDlg(['change']); c = g.controls('D')[0]
        self.assertEqual(play_lib.press_control(g, 'D', c, 'x', expect='box_or_change'), 'change')
        self.assertEqual(play_lib.VERIFIED[-1]['how'], 'change')
    def test_press_box_or_change_nothing_fails_closed(self):
        g = FakeDlg([]); c = g.controls('D')[0]
        with self.assertRaises(_drv.DriverError): play_lib.press_control(g, 'D', c, 'x', expect='box_or_change')
        self.assertEqual(g.clicks, 3)
    def test_press_missing_control_raises_without_clicking(self):
        g = FakeDlg(['box'])
        with self.assertRaises(IndexError): play_lib.press(g, 'D', 'Missing')
        self.assertEqual(g.clicks, 0)
    def test_select_verified_registers(self):
        g = FakeDlg([]); states = iter([False, False, True])
        self.assertEqual(play_lib.select_verified(g, 'D', 'Go', lambda g_: None, lambda o: next(states), 'radio'), 2); self.assertEqual(g.clicks, 2)
    def test_select_verified_unregistered_selection_fails_closed_after_three_clicks(self):
        g = FakeDlg([])
        with self.assertRaises(_drv.DriverError): play_lib.select_verified(g, 'D', 'Go', lambda g_: None, lambda o: False, 'radio')
        self.assertEqual(g.clicks, 3)
    def test_select_verified_already_selected_before_proves_nothing_and_clicks_nothing(self):
        g = FakeDlg([])
        with self.assertRaises(_drv.DriverError): play_lib.select_verified(g, 'D', 'Go', lambda g_: ['litinf'], lambda o: 'litinf' in o, 'radio')
        self.assertEqual(g.clicks, 0)
    def test_expectations(self):
        ce = play_lib.check_expectation
        ce('box', True); ce('nobox', False); ce('state', False, 1, 2)
        for args in (('box', False), ('nobox', True), ('state', True, 1, 2), ('state', False, 1, 1), ('state', False, None, 2)):
            with self.assertRaises(_drv.DriverError, msg=str(args)): ce(*args)
    def test_scenarios_declare_the_no_box_plays(self):
        import scenarios
        nobox = sorted(k for k, v in scenarios.SC.items() if v.get('expect', 'box') != 'box')
        self.assertEqual(nobox, ['A01', 'SEL01', 'TR3'])
        self.assertTrue(callable(scenarios.SC['A01']['watch']))

class GuessedCoordinateTests(unittest.TestCase):
    """R3: no runner path may click an inherited guessed or fixed coordinate (Game.save_as, Game.tool, dismiss_popups ...), and every click site of the runner is accounted for"""
    HERE = os.path.dirname(os.path.abspath(__file__))
    FORBID = {'save_as', 'tool', 'dismiss_popups', 'calibrate_toolbar', 'calibrate_army_toolbar', 'calibrate_fleet_toolbar', 'calibrate_battle_toolbar', 'open_dialog', 'close_dialog',
              'new_game', 'army_tool', 'fleet_tool', 'menu', 'recruit', 'hire_mercs', 'end_turn', 'end_turn_proven', 'play_battle', 'split_army', 'disband_army', 'embark', 'press_end_turn_once',
              'keep_save', 'open_tool'}
    def sources(self):
        import ast, glob
        for p in sorted(glob.glob(os.path.join(self.HERE, '*.py'))):
            if os.path.basename(p).startswith('test_'): continue
            yield os.path.basename(p), ast.parse(open(p).read())
    @staticmethod
    def constant(a, consts):
        import ast
        return (isinstance(a, ast.Constant) and isinstance(a.value, (int, float))) or (isinstance(a, ast.Name) and a.id in consts)
    @staticmethod
    def constant_names(tree):
        """Names bound anywhere in the file to a number literal (x = 640; x, y = 640, 500; x: int = 640): a click through such a name is a click at a constant coordinate"""
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
        out = []
        consts = self.constant_names(tree)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in self.FORBID: out.append('%s:%d calls .%s(): an inherited path with guessed or fixed coordinates' % (name, n.lineno, n.func.attr))
            if isinstance(n, ast.FunctionDef) and n.name in ('keep_save', 'open_tool', 'press_end_turn_once'): out.append('%s:%d defines %s: an unused helper that clicks inherited coordinates' % (name, n.lineno, n.name))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'Game' and n.func.attr in ('open', 'load', 'save_as') and name != 'play_lib.py':
                out.append('%s:%d calls Game.%s directly' % (name, n.lineno, n.func.attr))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('click', 'click_control', 'click_tile', 'mousemove') and any(self.constant(a, consts) for a in n.args[:2]):
                out.append('%s:%d: a click at a constant coordinate' % (name, n.lineno))
        return out
    def test_no_forbidden_driver_call_and_no_unsafe_helper(self):
        for name, tree in self.sources(): self.assertEqual(self.violations(name, tree), [])
    def test_the_guard_catches_each_way_back(self):
        import ast
        for snippet in ('g.save_as("x")', 'g.tool("end_turn")', 'g.dismiss_popups()', 'g.click(640, 500)', 'g.click_control(c); g.click(10, y)', 'Game.open(self, s)', 'g.calibrate_army_toolbar()',
                        'def keep_save(g, n): pass', 'def open_tool(g): pass', 'def press_end_turn_once(g): pass',
                        'x = 640; y = 500; g.click(x, y)', 'x, y = 640, 500; g.click(x, y)', 'def f(g):\n    y = 500\n    g.click(xx, y)'):
            self.assertTrue(self.violations('snippet.py', ast.parse(snippet)), snippet)
        self.assertEqual(self.violations('snippet.py', ast.parse('g.click(x, ARMY_Y)')), [])
    def test_every_click_site_is_accounted_for_and_none_has_a_constant_coordinate(self):
        import ast
        sites = set()
        for name, tree in self.sources():
            for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
                for n in ast.walk(fn):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('click', 'click_control', 'click_tile', 'mousemove'):
                        self.assertFalse(any(isinstance(a, ast.Constant) and isinstance(a.value, (int, float)) for a in n.args[:2]), '%s:%d: a click at a constant coordinate' % (name, n.lineno))
                        sites.add((name, fn.name, n.func.attr, ', '.join(ast.unparse(a) for a in n.args if not isinstance(a, ast.Constant))))
        # each site below was read: its coordinates come from a control enumerated by Game.controls, a tooltip scan made in this run (verified_x), an OCR word of this run, or a tile position
        # computed by the driver from game memory; a NEW click site must be added here by a reviewer, or this test fails
        self.assertEqual(sorted(sites), sorted(self.EXPECTED), sorted(sites ^ set(self.EXPECTED)))
    EXPECTED = [
        ('eog.py', 'answer_confirm', 'click_control', 'c'),
        ('eog.py', 'click_ok', 'click_control', "g.control(cs, text='OK')"),
        ('eog.py', 'close_boxes', 'click_control', 'ok'),
        ('eog.py', 'menu_pick', 'click', 'bar[0][1], bar[0][2]'),
        ('eog.py', 'menu_pick', 'click', 'hit[0][1], hit[0][2]'),
        ('lib.py', 'menu_step', 'click', 'hit[0][1], hit[0][2]'),
        ('play_lib.py', 'army_button', 'click', 'x, ARMY_Y'),
        ('play_lib.py', 'city_button', 'click', "found['fortify'], ARMY_Y"),
        ('play_lib.py', 'city_button', 'click_tile', 'x, y'),
        ('play_lib.py', 'click_control', 'click_control', 'self, c, fx, fy, pause'),
        ('play_lib.py', 'click_row', 'click', "lst['x'] + lst['w'] // 2, lst['y'] + 12 + 12 * r"),
        ('play_lib.py', 'click_verified', 'click_control', 'c'),
        ('play_lib.py', 'close_all', 'click_control', 'c'),
        ('play_lib.py', 'close_dialog_cancel', 'click_control', 'g.control(cs, text=button)'),
        ('play_lib.py', 'fleet_button', 'click', 'x, ARMY_Y'),
        ('play_lib.py', 'main_tool', 'click', 'x, _drv.TOOLBAR_Y'),
        ('play_lib.py', 'open_file_dialog', 'click', 'x, _drv.TOOLBAR_Y'),
        ('play_lib.py', 'press_control', 'click_control', 'c'),
        ('play_lib.py', 'select_verified', 'click_control', 'c'),
        ('scenarios.py', 'act', 'click_control', 'tgt'),
        ('scenarios.py', 'e01_act', 'click_tile', '*g.fleet_pos(2)'),
        ('scenarios.py', 'embark_pre', 'click_tile', 'fx, fy'),
        ('scenarios.py', 'pre', 'click_tile', 'fx, fy'),
        ('scenarios.py', 'pre', 'click_tile', 'x, y'),
        ('scenarios.py', 'rel_act', 'click_control', 'tgt'),
        ('scenarios.py', 'sail_pre', 'click_tile', 'x, y'),
    ]

if __name__ == '__main__': unittest.main()
