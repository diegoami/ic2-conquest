"""Tests of the runner's click discipline: a box without an OK control raises and NOTHING is clicked (play_lib.close_all, which is also the only way the runner's own load path clears boxes,
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
if __name__ == '__main__': unittest.main()
