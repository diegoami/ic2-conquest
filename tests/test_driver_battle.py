#!/usr/bin/env python3
"""Offline tests of the driver fixes found by B0 (battles plan §3.5 and the B0 findings), with a scripted Game (no Wine, no X).
Run: python3 -m tests.test_driver_battle   (exit 1 on a failure).

  - `neutral_point` / `reset_ui`: the NEUTRAL click point is used when no window covers it; when an oversized unit map covers it, a point
    outside every window is derived from the screen geometry; none free -> DriverError (no click).
  - `Game.open` with a save that opens with a modal box: the box's text is returned and OK closes it; a Confirm box is answered No and raises.
  - `play_battle`: End turn only after proof of the previous click; no proof -> DriverError and no second click; a battle that ended at the
    Computer general click gets no End turn click; `on_dialog` capture / no / yes / strict on the "Offer of peace" box; None = historical.
"""
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import harness.driver as D  # noqa: E402

MAP = (1, "Unit map", 334, 65, 1143, 903)
AREA = (2, "Area map", 13, 65, 328, 196)
INFO = (3, "Information", 12, 265, 328, 698)


class Fake(D.Game):
    def __init__(self, wins, **kw):
        self.log = lambda *a: None
        self.pid = 1
        self.wins = list(wins)
        self.clicks = []
        self.answers = []
        self.battle = False
        self.cg = False
        self.advance = True           # does an End turn click end the battle?
        self.peace = False            # does OK of "Battle ended" open an "Offer of peace" box?
        self.battle_x = {"computer": 165, "end_turn": 114}
        self.__dict__.update(kw)

    def find_windows(self, pattern=".", visible=True):
        return [w for w in self.wins if re.search(pattern, w[1])]

    def in_battle(self):
        return self.battle

    def screen_size(self):
        return (1280, 1024)

    def click(self, x, y, pause=0.4):
        self.clicks.append((x, y))
        if y == D.BATTLE_TOOLBAR_Y and self.battle:
            if x == 165:
                self.cg = True
            elif x == 114 and self.advance:
                self.end_battle()
            return
        for w in list(self.wins):          # an OK click at the bottom centre of a small box closes it
            if w[1] in D.Game.BOX_TITLES and abs(x - (w[2] + w[4] // 2)) < 5 and abs(y - (w[3] + w[5] - 24)) < 5:
                self.wins.remove(w)
                self.after_box_closed()

    def end_battle(self):
        self.battle = False
        self.wins = [w for w in self.wins if " v " not in w[1]]
        self.wins.append((9, "Battle ended", 13, 94, 450, 445))

    def after_box_closed(self):
        pass

    def read_popup(self, w):
        return "text of " + w[1]

    def shot(self, path, window="root"):
        pass

    def controls(self, title):
        if title == "Battle ended":
            return [{"cls": "TButton", "text": "OK", "x": 203, "y": 499, "w": 70, "h": 25, "title": title}]
        if title == "Offer of peace":
            return [{"cls": "TButton", "text": "Yes", "x": 94, "y": 414, "w": 70, "h": 25, "title": title},
                    {"cls": "TButton", "text": "No", "x": 269, "y": 414, "w": 70, "h": 25, "title": title}]
        if title == "Confirm":
            return [{"cls": "TButton", "text": t, "x": 10, "y": 10, "w": 50, "h": 20, "title": title} for t in ("Yes", "No", "Cancel")]
        raise D.DriverError("no controls")

    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        self.answers.append((c["title"], c["text"]))
        if c["title"] == "Battle ended":
            self.wins = [w for w in self.wins if w[1] != "Battle ended"]
            if self.peace:
                self.wins.append((10, "Offer of peace", 13, 94, 406, 360))
        else:
            self.wins = [w for w in self.wins if w[1] != c["title"]]

    def answer(self, title, yes=True):
        c = next(c for c in self.controls(title) if c["text"].lower() == ("yes" if yes else "no"))
        self.click_control(c)
        return True


class Clock:
    def __enter__(self):
        self.t = 0.0
        self.old = (D.time.sleep, D.time.time, D.G)
        D.time.sleep = lambda s: setattr(self, "t", self.t + s)
        D.time.time = lambda: self.t
        D.G = Path(tempfile.mkdtemp())
        return self

    def __exit__(self, *a):
        D.time.sleep, D.time.time, D.G = self.old


# ---- neutral point -----------------------------------------------------------------------------------------------------------
def test_neutral_is_used_when_free():
    g = Fake([AREA, INFO])
    assert g.neutral_point() == D.NEUTRAL


def test_neutral_moves_off_an_oversized_unit_map():
    g = Fake([MAP, AREA, INFO])
    x, y = g.neutral_point()
    assert (x, y) != D.NEUTRAL and not (MAP[2] <= x < MAP[2] + MAP[4] and MAP[3] <= y < MAP[3] + MAP[5]), (x, y)
    assert 0 <= x < 1280 and 0 <= y < 1024


def test_reset_ui_clicks_the_derived_point():
    with Clock():
        g = Fake([MAP, AREA, INFO])
        g.key = lambda *k: None
        g.reset_ui()
        assert g.clicks == [g.neutral_point()] and g.clicks[0] != D.NEUTRAL, g.clicks


def test_neutral_none_free_raises_without_clicking():
    g = Fake([(5, "Big", 0, 0, 1280, 1024)])
    try:
        g.neutral_point()
    except D.DriverError as e:
        assert "free of windows" in str(e)
    else:
        raise AssertionError("no error")


# ---- Game.open with a modal box ------------------------------------------------------------------------------------------------
class OpenFake(Fake):
    def __init__(self, box):
        super().__init__([(7, "Imperial Conquest 2", 640, 512, 1, 1), AREA, MAP], box=box)

    def open_file_dialog(self, name):
        self.wins.append((20, self.box, 400, 300, 300, 150))      # the box opens; the title never gets "turn" while it is up

    def after_box_closed(self):
        self.wins.append((7, "Imperial Conquest 2 - Rome turn 0743", 640, 512, 1, 1))


def test_open_reports_and_closes_a_modal_box():
    with Clock():
        src = D.G.parent / "x.sav"
        src.write_bytes(b"x")
        g = OpenFake("Information")
        texts = g.open(src)
        assert texts == ["text of Information"], texts
        assert g.find_windows("turn") and not g.message_boxes()


def test_open_confirm_is_answered_no_and_raises():
    with Clock():
        src = D.G.parent / "x.sav"
        src.write_bytes(b"x")
        g = OpenFake("Confirm")
        try:
            g.open(src)
        except D.DriverError as e:
            assert "unexpected Confirm" in str(e), e
        else:
            raise AssertionError("no error")
        assert ("Confirm", "No") in g.answers and ("Confirm", "Yes") not in g.answers, g.answers


# ---- play_battle ----------------------------------------------------------------------------------------------------------------
def battle(**kw):
    g = Fake([AREA, MAP, INFO, (4, "Rome  v  Gaul          Rome to place units.", 5, 99, 448, 414)], **kw)
    g.battle = True
    return g


def run(g, **kw):
    with Clock():
        try:
            return g.play_battle(**kw), None
        except D.DriverError as e:
            return None, str(e)


def test_one_end_turn_click_when_it_advances():
    g = battle()
    r, err = run(g, on_dialog="capture")
    assert err is None and r["end_turn_clicks"] == 1 and g.clicks.count((114, 112)) == 1, (r, err, g.clicks)
    assert r["battle_ended_text"] == "text of Battle ended" and r["dialogs"] == []


def test_no_proof_no_second_click():
    g = battle(advance=False)
    r, err = run(g)
    assert err and "not clicking again" in err and g.clicks.count((114, 112)) == 1, (err, g.clicks)


def test_ended_at_the_computer_general_click_gets_no_end_turn():
    g = battle()
    orig = g.click

    def click(x, y, pause=0.4):
        orig(x, y, pause)
        if x == 165:
            g.end_battle()
    g.click = click
    r, err = run(g, on_dialog="capture")
    assert err is None and r["end_turn_clicks"] == 0 and (114, 112) not in g.clicks, (r, err, g.clicks)


def test_capture_declines_the_offer_of_peace():
    g = battle(peace=True)
    r, err = run(g, on_dialog="capture")
    assert err is None and [d["title"] for d in r["dialogs"]] == ["Offer of peace"], (r, err)
    d = r["dialogs"][0]
    assert d["answer"] == "No" and d["text"] == "text of Offer of peace" and d["shot"] and [c["text"] for c in d["controls"]] == ["Yes", "No"], d
    assert ("Offer of peace", "Yes") not in g.answers and not g.find_windows("Offer of peace")


def test_no_mode_declines_without_artifacts():
    g = battle(peace=True)
    r, err = run(g, on_dialog="no")
    d = r["dialogs"][0]
    assert d["answer"] == "No" and d["shot"] is None and d["controls"] is None and d["text"], d


def test_yes_mode_answers_yes():
    g = battle(peace=True)
    r, err = run(g, on_dialog="yes")
    assert r["dialogs"][0]["answer"] == "Yes" and ("Offer of peace", "Yes") in g.answers, (r, g.answers)


def test_strict_declines_and_raises():
    g = battle(peace=True)
    r, err = run(g, on_dialog="strict")
    assert err == "battle: unexpected dialog: text of Offer of peace" and ("Offer of peace", "No") in g.answers, (err, g.answers)


def test_no_dialog_means_empty_list():
    g = battle(peace=False)
    r, err = run(g, on_dialog="capture")
    assert err is None and r["dialogs"] == [], (r, err)


def test_default_is_the_historical_dismissal():
    g = battle(peace=True)
    r, err = run(g)
    assert err is None and r["dialogs"] == [] and g.find_windows("Offer of peace"), "default must not answer the Offer of peace"


def test_battle_state_reads_memory_like_the_block():
    import struct
    from state import battle_block as BB
    blk = BB.synthetic_block([("hi", 6000, 6, 0, "1st Guards  Battalion"), ("li", 5000, 6, 11, "Gallic")], [("ar", 3000, 6, 0, "2nd Bowmen  Battalion")], 0, 10, half_round=7)
    blk["x2"], blk["y1"] = 1, 1
    raw = BB.encode_block(blk)
    img = {}
    for a, data in ((D.BATTLE_SLOTS, raw[BB.HEADER_LEN:]), (D.BATTLE_HEADER["attacker_army"], struct.pack("<hhhh", 0, 10, 1, 7)),
                    (D.BATTLE_HEADER["y1"], bytes([1])), (D.BATTLE_FLAG, bytes([1]))):
        for i, byte in enumerate(data):
            img[a + i] = byte
    g = Fake([AREA])
    g.battle = True
    g.mem = lambda addr, n: bytes(img.get(addr + i, 0) for i in range(n))
    st = g.battle_state()
    assert BB.encode_block(st) == raw and st["half_round"] == 7 and st["defender_army"] == 10 and st["x2"] == 1 and st["y1"] == 1
    g.battle = False
    try:
        g.battle_state()
    except D.DriverError as e:
        assert "no battle pending" in str(e)
    else:
        raise AssertionError("read a stale block")


def test_common_battle_end_turn_never_retries():
    sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
    import common as C
    C.D.sh = lambda *a, **k: ""
    g = battle(advance=False)
    with Clock():
        try:
            C.battle_end_turn(g, 4)
        except D.DriverError as e:
            assert "not clicking again" in str(e)
        else:
            raise AssertionError("no error without progress")
    assert g.clicks.count((114, 112)) == 1, g.clicks
    g = battle()
    with Clock():
        C.battle_end_turn(g, 4)
    assert g.clicks.count((114, 112)) == 1


def test_bad_mode_rejected():
    try:
        battle().play_battle(on_dialog="maybe")
    except D.DriverError:
        return
    raise AssertionError("accepted")


def test_synthetic_block_refuses_more_units_than_the_grid_holds():
    from state import battle_block as BB
    u = ("hi", 6000, 6, 0, "x")
    BB.synthetic_block([u] * 13, [u] * 12)         # the largest that fits: attacker x 0..12, defender x 1..12
    for att, dfn in (([u] * 14, [u]), ([u], [u] * 13)):
        try:
            BB.synthetic_block(att, dfn)
        except ValueError:
            continue
        raise AssertionError("accepted %d v %d units" % (len(att), len(dfn)))


def test_log_files_are_never_reused_in_the_same_second():
    sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
    import common as C
    d = Path(tempfile.mkdtemp())
    a, b = C.Log("x", d), C.Log("x", d)
    a("e", n=1)
    b("e", n=2)
    assert a.jl != b.jl and a.txt != b.txt and len(list(d.iterdir())) == 4
    assert len(a.jl.read_text().splitlines()) == 1 and len(b.jl.read_text().splitlines()) == 1
    q = C.write_new(d, "x.tar.gz", b"1")
    assert C.write_new(d, "x.tar.gz", b"2") != q and q.read_bytes() == b"1"


class CounterBattle(Fake):
    """A battle in which an End turn click advances the half-round counter only 2 s (fake time) AFTER the click, with no new BATTLEnn.SAV, the flag
    still up and the title unchanged: the only sign is the half-round counter. `stuck` = the click never advances anything."""

    def __init__(self, wins, **kw):
        super().__init__(wins, **kw)
        self.battle, self.hr, self.pending, self.stuck, self.seen = True, 2, [], False, []

    def half_round_counter(self):
        now = D.time.time()
        done = [t for t in self.pending if now - t >= 2]
        self.pending = [t for t in self.pending if now - t < 2]
        self.hr += len(done)
        if self.hr >= 4:
            self.end_battle()
        return self.hr

    def click(self, x, y, pause=0.4):
        if (x, y) == (D.BATTLE_TOOLS["end_turn"], D.BATTLE_TOOLBAR_Y) and self.battle:
            self.seen.append(self.half_round_counter())     # the counter at the moment of THIS click
            self.clicks.append((x, y))
            if not self.stuck:
                self.pending.append(D.time.time())
            return
        super().click(x, y, pause)


def _probe():
    sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
    import b0_probe
    return b0_probe


def test_end_turn_until_over_waits_for_the_half_round_counter():
    """Behavioural: each End turn click is made only after the counter moved on since the previous click (it is the only sign of progress here); with
    the proof comparison deleted from `end_turn_until_over` the second click comes before the counter advanced and this fails."""
    b0 = _probe()
    g = CounterBattle([(5, "Rome  v  Gaul          Rome to move units.", 5, 99, 448, 414)])
    with Clock():
        n = b0.end_turn_until_over(g, lambda *a, **k: None, max_clicks=5)
    assert n == 2 and len(g.clicks) == 2, (n, g.clicks)
    assert g.seen == [2, 3], g.seen          # click 2 only after the counter went 2 -> 3 (a blind second click would see 2 again)


def test_end_turn_until_over_never_clicks_twice_without_a_sign():
    b0 = _probe()
    g = CounterBattle([(5, "Rome  v  Gaul          Rome to move units.", 5, 99, 448, 414)])
    g.stuck = True
    with Clock():
        try:
            b0.end_turn_until_over(g, lambda *a, **k: None, max_clicks=5)
        except D.DriverError as e:
            assert "not clicking again" in str(e)
        else:
            raise AssertionError("no error without a sign of progress")
    assert len(g.clicks) == 1, g.clicks


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as e:      # noqa: BLE001
                fails += 1
                print("FAIL", name, type(e).__name__, e)
    sys.exit(1 if fails else 0)
