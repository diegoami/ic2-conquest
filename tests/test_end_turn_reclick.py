#!/usr/bin/env python3
"""Offline tests of `Game.end_turn(reclick=..., strict_confirm=...)` and `dismiss_popups(strict=...)` with a scripted Game (no game, no Wine,
no X): the clicks, boxes and the autosave line are scripted. Run: python3 -m tests.test_end_turn_reclick   (exit 1 on a failure).

What is checked: the default behaviour is unchanged (a second click when no sign of the turn starting appears; a Confirm answered Yes);
`reclick=False` clicks exactly once and raises; `strict_confirm=True` answers an unknown Confirm No (never Yes), checks that it closed and
raises, on each path of end_turn (the wait loop, after the autosave line, inside play_battle), and still answers "End turn ?" End turn.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import harness.driver as D  # noqa: E402


class Scripted(D.Game):
    """A Game whose window and memory access is scripted. `boxes` is a list of (id, title) shown by popups()/find_windows();
    `answer` removes the box it answers and records the answer; `tool('end_turn')` counts clicks and optionally writes the autosave line."""

    def __init__(self, log_dir, sign=True, boxes_after_line=None, boxes_during=None, battle=False, defer_line=False):
        self.log = lambda *a: None
        self.dir = log_dir
        self.sign = sign                  # does the first click produce a sign of the turn starting?
        self.clicks = 0
        self.answers = []
        self.boxes = list(boxes_during or [])
        self.boxes_after_line = list(boxes_after_line or [])
        self.cal = 1
        self.battle = battle
        self.line_written = False
        self.defer_line = defer_line      # the autosave line only appears after the End turn box is answered / the battle played

    # --- what end_turn touches ---
    def calendar(self):
        return self.cal

    def i16(self, addr):
        return 1

    def wait(self, cond, timeout, what, step=0.5):
        if cond():
            return True
        raise D.DriverError("timeout waiting for " + what)

    def tool(self, name, pause=1.0):
        assert name == "end_turn"
        self.clicks += 1
        if self.sign or self.clicks > 1:
            self.cal += 1                  # the calendar moves: a sign of the turn starting
            if not self.defer_line:
                self._line()

    def _line(self):
        (self.dir / "AUTOSAVE.LOG").write_text("0721 AUTO0721.SAV OK\n")
        self.line_written = True
        self.boxes += self.boxes_after_line
        self.boxes_after_line = []

    def popups(self):
        return [(i, t, 100, 100, 300, 120) for i, t in self.boxes]

    def find_windows(self, pattern=None):
        import re
        return [w for w in self.popups() if pattern is None or re.search(pattern, w[1])]

    def in_battle(self):
        return self.battle

    def read_popup(self, w):
        return f"text of {w[1]} {w[0]}"

    def controls(self, title):
        return [{"text": "End turn"}]

    def control(self, cs, text=None, **kw):
        return cs[0]

    def click_control(self, c, **kw):
        self.answers.append(("click", c["text"]))
        self.boxes = [b for b in self.boxes if b[1] != "End turn ?"]
        if self.defer_line:
            self._line()

    def answer(self, title, yes=True):
        self.answers.append((title, yes))
        self.boxes = [b for b in self.boxes if b[1] != title]
        return True

    def click(self, x, y, pause=0.5):
        self.boxes = [b for b in self.boxes if b[1] == "Confirm"]      # an OK click dismisses information boxes, not a Confirm

    def play_battle(self, shot=None, strict=False):
        self.played = strict
        self.battle = False
        self.boxes.append((77, "Confirm"))
        try:
            self.dismiss_popups(strict=strict)
        finally:
            self._line()


def run(**kw):
    with tempfile.TemporaryFile() as _:
        pass
    d = Path(tempfile.mkdtemp())
    old = D.G
    D.G = d
    D.time.sleep = lambda s: None
    try:
        reclick = kw.pop("reclick", True)
        strict = kw.pop("strict", False)
        g = Scripted(d, **kw)
        try:
            out = g.end_turn(timeout=5, reclick=reclick, strict_confirm=strict)
            err = None
        except D.DriverError as e:
            out, err = None, str(e)
        return g, out, err
    finally:
        D.G = old


def test_default_reclicks_without_a_sign():
    g, out, err = run(sign=False)
    assert err is None and g.clicks == 2, (g.clicks, err)


def test_default_single_click_with_a_sign():
    g, out, err = run(sign=True)
    assert err is None and g.clicks == 1 and out[0] == "AUTO0721.SAV", (g.clicks, err, out)


def test_reclick_false_clicks_once_and_raises():
    g, out, err = run(sign=False, reclick=False)
    assert g.clicks == 1 and err == "end turn: no sign of the turn starting", (g.clicks, err)


def test_default_answers_an_unknown_confirm_yes():
    g, out, err = run(sign=True, boxes_after_line=[(5, "Confirm")])
    assert err is None and ("Confirm", True) in g.answers, (err, g.answers)


def test_strict_answers_an_unknown_confirm_no_after_the_line():
    g, out, err = run(sign=True, boxes_after_line=[(5, "Confirm")], strict=True)
    assert err and "unexpected Confirm" in err and ("Confirm", False) in g.answers and ("Confirm", True) not in g.answers, (err, g.answers)
    assert not g.popups(), "the Confirm box must be closed"


def test_strict_answers_an_unknown_confirm_no_in_the_wait_loop():
    # a box present before the autosave line appears: `sign` False and reclick False would raise earlier, so the box is there from the start
    g, out, err = run(sign=True, boxes_during=[(6, "Confirm")], strict=True)
    assert err and "unexpected Confirm" in err and ("Confirm", False) in g.answers and ("Confirm", True) not in g.answers, (err, g.answers)


def test_strict_still_answers_end_turn_box():
    g, out, err = run(sign=True, boxes_during=[(8, "End turn ?")], strict=True, defer_line=True)
    assert err is None and ("click", "End turn") in g.answers and ("Confirm", False) not in g.answers, (err, g.answers)


def test_strict_reaches_play_battle_and_its_dismissal():
    g, out, err = run(sign=True, battle=True, boxes_during=[(9, "Battle v Battle")], strict=True, defer_line=True)
    assert getattr(g, "played", None) is True, "play_battle must get strict=True"
    assert err and "unexpected Confirm" in err and ("Confirm", False) in g.answers, (err, g.answers)


def test_strict_information_boxes_are_still_dismissed():
    g, out, err = run(sign=True, boxes_after_line=[(10, "Information")], strict=True)
    assert err is None and not g.popups(), (err, g.popups())


def test_real_play_battle_passes_strict_to_its_final_dismissal():
    """The scripted `play_battle` above only shows end_turn passes `strict`; the real method's final `dismiss_popups` must use it
    (its other clicks are on an OK-only 'Battle ended' result box). A source check, since the real method needs a battle window."""
    import inspect
    src = inspect.getsource(D.Game.play_battle)
    assert "self.dismiss_popups(strict=strict)" in src and "def play_battle(self, shot=None, strict=False)" in src
    assert src.count("dismiss_popups") == 1, "every dismissal inside play_battle must be the strict-aware one"


TESTS = [n for n in sorted(globals()) if n.startswith("test_")]

if __name__ == "__main__":
    bad = 0
    for n in TESTS:
        try:
            globals()[n]()
            print("PASS", n)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print("FAIL", n, type(e).__name__, e)
    sys.exit(1 if bad else 0)
