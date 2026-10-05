#!/usr/bin/env python3
"""Offline tests of the battle orders `harness/battle_orders.py` (battles plan B7): a FAKE battle (no Wine, no X) that simulates the click handling of the
tactical screen [R-code: the research repo's decompiled battle module, section 3 "Human actions"] and can be made to misbehave. Run:
    python3 -m tests.test_battle_orders      (exit 1 on a failure)

Each order is tested for: the right effect (passes, with the block read-back in the record); a WRONG CELL (the fake's click lands one tile off) -> the order fails
with OrderFailed("wrong") and is not retried; a SILENT NO-OP (the fake ignores the clicks) -> OrderFailed("noop") after exactly 1 + `retries` attempts, never more;
a first click that only activates the window -> the retry succeeds (attempts == 2); preconditions (not adjacent, out of range, no moves, not placement phase)
raise DriverError with NO click made; End turn: one click, proof from the half-round counter, and with no proof DriverError and still exactly one click;
Surrender: "no" leaves the block byte-identical, "yes" ends the battle, anything else raises before any click, and Cancel is never pressed.
"""
import copy
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import harness.driver as D  # noqa: E402
from harness import battle_orders as BO  # noqa: E402
from state import battle_block as BB  # noqa: E402

WIN = (7, "Rome  v  Gaul          Rome to move units.", 5, 99, 448, 414)


def make_block(rome, gaul, y1=1):
    b = BB.synthetic_block(rome, gaul, half_round=3)
    b["y1"] = y1
    for s in b["slots"]:
        if s["alive"]:
            s["state"] = {"li": 4, "hi": 2, "ar": 4, "lc": 6, "hc": 5}[s["type"]]
    return b


class FakeBattle(BO.BattleGame):
    """The click handling of TBattleMap, simplified, over a real parsed block. Faults: `ignore_first` (that many clicks of the first order are swallowed:
    the window activation), `offset` (every map click lands this many tiles off), `dead` (all map clicks ignored), `end_noop` (End turn does nothing)."""
    CHANGE_TIMEOUT, SETTLE, CLICK_PAUSE = 0.05, 0.0, 0.0

    def __init__(self, block, ignore_first=0, offset=(0, 0), dead=False, end_noop=False, confirm=True):
        self.log = lambda *a: None
        self.pid = 1
        self.b = block
        self.sel = None
        self.clicks = []
        self.ignore = ignore_first
        self.offset, self.dead, self.end_noop = offset, dead, end_noop
        self.over = False
        self.confirm = confirm
        self.boxes = []
        self.pressed = []

    # --- the game side ---
    def in_battle(self):
        return not self.over

    def battle_state(self):
        if self.over:
            raise D.DriverError("battle_state: no battle pending")
        return copy.deepcopy(self.b)

    def half_round_counter(self):
        return None if self.over else self.b["half_round"]

    def find_windows(self, pattern=".", visible=True):
        import re
        wins = [] if self.over else [WIN]
        wins += self.boxes
        if self.over:
            wins.append((9, "Battle ended", 13, 94, 450, 445))
        return [w for w in wins if re.search(pattern, w[1])]

    def battle_focus(self):
        pass

    def read_popup(self, w):
        return "Are you sure you want to surrender ? Yes No Cancel"

    def controls(self, title):
        return [{"cls": "TButton", "text": t, "x": 500 + 80 * i, "y": 520, "w": 70, "h": 25} for i, t in enumerate(["Cancel", "&No", "&Yes"])]

    def end_turn_proven(self, click, timeout=8):
        before = self.b["half_round"]
        click()
        if self.over or self.b["half_round"] != before:
            return
        raise D.DriverError("battle End turn: no sign the battle advanced; not clicking again")

    def sleep_free(self):
        pass

    # --- click handling ---
    def _tile(self, x, y):
        w = WIN
        tx, ty = (x - w[2]) // 32, (y - w[3] - BO.MAP_DY) // 32
        return (tx + self.offset[0], ty + self.offset[1]) if 0 <= ty < 12 and 0 <= tx < 14 else None

    def _at(self, tx, ty):
        for s in self.b["slots"]:
            if s["alive"] and (s["x"], s["y"]) == (tx, ty):
                return s
        return None

    def click(self, x, y, pause=0.4):
        self.clicks.append(("L", x, y))
        if y == WIN[3] + BO.BUTTON_DY:
            return self._button(x)
        self._map_click(x, y, right=False)

    def rclick(self, x, y, pause=0.4):
        self.clicks.append(("R", x, y))
        self._map_click(x, y, right=True)

    def click_control(self, c, fx=0.5, fy=0.5, pause=0.6):
        self.pressed.append(c["text"].replace("&", ""))
        self.boxes = []
        if self.pressed[-1] == "Yes":
            self.over = True

    def _button(self, x):
        names = {v[0] + WIN[2]: k for k, v in BO.BUTTONS.items()}
        name = names.get(x)
        if name == "end_turn" and not self.end_noop:
            self.b["half_round"] += 2
            for s in self.b["slots"]:
                if s["alive"] and s["side"] == 0:
                    s["state"] = {"li": 4, "hi": 2, "ar": 4, "lc": 6, "hc": 5}[s["type"]]
        elif name == "surrender" and self.confirm:
            self.boxes = [(11, "Confirm", 510, 477, 261, 97)]

    def _map_click(self, x, y, right):
        if self.ignore > 0:
            self.ignore -= 1
            return
        if self.dead:
            return
        t = self._tile(x, y)
        if t is None:
            return
        here = self._at(*t)
        if not right:
            if here is not None and here["side"] == 0:
                self.sel = here["slot"]
            elif here is None and self.sel is not None:
                self._place_or_move(self.b["slots"][self.sel], t)
            elif here is not None and here["side"] == 1 and self.sel is not None:
                u = self.b["slots"][self.sel]
                if BO.cheb((u["x"], u["y"]), t) == 1 and u["state"] >= 1:
                    u["target"] = here["slot"]
        elif here is not None and here["side"] == 1 and self.sel is not None:
            u = self.b["slots"][self.sel]
            if u["ammo"] > 0 and u["state"] > 0 and BO.cheb((u["x"], u["y"]), t) <= BO.RANGE.get(u["type"], 0):
                u["ammo"] -= 1
                u["state"] -= 1
                u["target"] = -1
                here["troops"] -= 10

    def _place_or_move(self, u, t):
        if self.b["y1"] == 0:
            if t[1] < 3:
                u["x"], u["y"] = t
            return
        while u["state"] > 0 and (u["x"], u["y"]) != t:
            nx = u["x"] + (t[0] > u["x"]) - (t[0] < u["x"])
            ny = u["y"] + (t[1] > u["y"]) - (t[1] < u["y"])
            if self._at(nx, ny) is not None and (nx, ny) != t:
                break
            if self._at(nx, ny) is not None:
                break
            u["x"], u["y"] = nx, ny
            u["state"] -= 1
        u["target"] = -1


def rome_gaul():
    rome = [("hi", 2000, 6, 0, "h"), ("ar", 3000, 6, 0, "a"), ("lc", 4000, 6, 0, "c")]
    gaul = [("li", 5000, 6, 0, "l"), ("hi", 3000, 6, 0, "g")]
    b = make_block(rome, gaul)
    # Rome on row 2: slots 0,1,2 at x 0,1,2; Gaul: slot 20 at (0,3) (adjacent to slot 0 and 1), slot 21 at (5,9)
    for k in range(3):
        b["slots"][k].update(x=k, y=2)
    b["slots"][20].update(x=0, y=3)
    b["slots"][21].update(x=5, y=9)
    return b


TESTS = []


def test(f):
    TESTS.append(f)
    return f


def raises(exc, f, *a, **k):
    try:
        f(*a, **k)
    except exc as e:
        return e
    raise AssertionError("%s did not raise %s" % (f.__name__, exc.__name__))


@test
def place_ok():
    b = rome_gaul()
    b["y1"] = 0
    g = FakeBattle(b)
    r = g.battle_place(0, 7, 1)
    assert r["ok"] and r["attempts"] == 1 and (g.b["slots"][0]["x"], g.b["slots"][0]["y"]) == (7, 1), r
    assert len(g.clicks) == 2           # select, destination


@test
def place_wrong_cell_fails_and_is_not_retried():
    b = rome_gaul()
    b["y1"] = 0
    g = FakeBattle(b, offset=(1, 0))      # the click lands one tile to the right of the aimed cell: the unit stands at (8, 1) not (7, 1)... after a select that also misses
    g.b["slots"][0].update(x=0, y=0)
    g.offset = (0, 0)
    # select works (offset 0), then the destination click is misplaced: emulate by an offset applied only to empty-cell clicks
    orig = g._tile
    state = {"n": 0}

    def tile(x, y):
        t = orig(x, y)
        state["n"] += 1
        return (t[0] + (1 if state["n"] % 2 == 0 else 0), t[1]) if t else t
    g._tile = tile
    e = raises(BO.OrderFailed, g.battle_place, 0, 7, 1)
    assert e.kind == "wrong", e.kind
    assert e.record["attempts"] == 1 and len(g.clicks) == 2, (e.record, g.clicks)      # not retried: the state moved


@test
def place_noop_gives_up_after_three_attempts():
    b = rome_gaul()
    b["y1"] = 0
    g = FakeBattle(b, dead=True)
    e = raises(BO.OrderFailed, g.battle_place, 0, 7, 1)
    assert e.kind == "noop" and e.record["attempts"] == 3 and len(g.clicks) == 6, (e.record, len(g.clicks))


@test
def retries_are_capped_by_the_argument():
    b = rome_gaul()
    b["y1"] = 0
    g = FakeBattle(b, dead=True)
    e = raises(BO.OrderFailed, g.battle_place, 0, 7, 1, retries=0)
    assert e.record["attempts"] == 1 and len(g.clicks) == 2


@test
def first_click_only_activates_the_window():
    b = rome_gaul()
    b["y1"] = 0
    g = FakeBattle(b, ignore_first=2)     # both clicks of the first attempt swallowed
    r = g.battle_place(0, 7, 1)
    assert r["ok"] and r["attempts"] == 2 and r["noop_attempts"] == 1, r


@test
def place_preconditions_click_nothing():
    b = rome_gaul()
    g = FakeBattle(b)                       # y1 = 1: the placement is over
    raises(D.DriverError, g.battle_place, 0, 7, 1)
    b2 = rome_gaul()
    b2["y1"] = 0
    g2 = FakeBattle(b2)
    raises(D.DriverError, g2.battle_place, 0, 7, 5)      # not a home row
    raises(D.DriverError, g2.battle_place, 0, 1, 2)      # occupied by slot 1
    raises(D.DriverError, g2.battle_place, 20, 7, 1)     # an enemy unit (side to move is 0)
    assert g.clicks == [] and g2.clicks == []


@test
def move_arrives():
    g = FakeBattle(rome_gaul())
    r = g.battle_move(2, 2, 6)
    s = g.b["slots"][2]
    assert r["ok"] and (s["x"], s["y"]) == (2, 6) and s["state"] == 6 - 4, (r, s)


@test
def move_partial_needs_the_flag():
    g = FakeBattle(rome_gaul())
    e = raises(BO.OrderFailed, g.battle_move, 0, 0, 8)      # HI: 2 moves, 6 needed: stops at (0, 4)... wait (0,3) is occupied by Gaul: it never moves
    assert e.kind in ("noop", "wrong")
    g2 = FakeBattle(rome_gaul())
    e2 = raises(BO.OrderFailed, g2.battle_move, 2, 2, 11)    # LC: 6 moves, 9 needed, ends at (2, 8) with moves 0: not the destination
    assert e2.kind == "wrong" and len(g2.clicks) == 2, e2.record
    g3 = FakeBattle(rome_gaul())
    r = g3.battle_move(2, 2, 11, partial=True)
    assert r["ok"] and (g3.b["slots"][2]["x"], g3.b["slots"][2]["y"]) == (2, 8), r


@test
def move_blocked_is_a_noop_failure():
    b = rome_gaul()
    g = FakeBattle(b)
    e = raises(BO.OrderFailed, g.battle_move, 0, 0, 6)     # slot 0 at (0,2), enemy at (0,3) directly in the way: the fake does not move it
    assert e.kind == "noop" and e.record["attempts"] == 3


@test
def move_wrong_cell():
    g = FakeBattle(rome_gaul())
    orig = g._tile
    n = {"i": 0}

    def tile(x, y):
        t = orig(x, y)
        n["i"] += 1
        return (t[0] + (1 if n["i"] % 2 == 0 else 0), t[1]) if t else t
    g._tile = tile
    e = raises(BO.OrderFailed, g.battle_move, 2, 2, 6)
    assert e.kind == "wrong" and len(g.clicks) == 2


@test
def move_preconditions():
    b = rome_gaul()
    b["slots"][2]["state"] = 0
    g = FakeBattle(b)
    raises(D.DriverError, g.battle_move, 2, 2, 6)          # no moves left
    raises(D.DriverError, g.battle_move, 20, 3, 5)         # enemy unit
    raises(D.DriverError, g.battle_move, 1, 0, 3)          # occupied destination
    assert g.clicks == []


@test
def attack_sets_word_9():
    g = FakeBattle(rome_gaul())
    r = g.battle_attack(0, 20)
    assert r["ok"] and g.b["slots"][0]["target"] == 20, r


@test
def attack_not_adjacent_or_no_moves_clicks_nothing():
    g = FakeBattle(rome_gaul())
    raises(D.DriverError, g.battle_attack, 2, 20)           # slot 2 at (2,2), enemy (0,3): distance 2
    raises(D.DriverError, g.battle_attack, 0, 21)           # far
    raises(D.DriverError, g.battle_attack, 0, 1)            # own unit
    b = rome_gaul()
    b["slots"][0]["state"] = 0
    g2 = FakeBattle(b)
    raises(D.DriverError, g2.battle_attack, 0, 20)
    assert g.clicks == [] and g2.clicks == []


@test
def attack_wrong_target_fails():
    b = rome_gaul()
    b["slots"][21].update(x=1, y=3)                          # a second enemy next to slot 0 / 1
    g = FakeBattle(b)
    g.offset = (0, 0)
    orig = g._tile
    n = {"i": 0}

    def tile(x, y):
        t = orig(x, y)
        n["i"] += 1
        return (t[0] + (1 if n["i"] % 2 == 0 else 0), t[1]) if t else t      # the second click lands on slot 21's tile instead of slot 20's
    g._tile = tile
    e = raises(BO.OrderFailed, g.battle_attack, 0, 20)
    assert e.kind == "wrong" and g.b["slots"][0]["target"] == 21, (e.kind, g.b["slots"][0]["target"])


@test
def attack_noop():
    g = FakeBattle(rome_gaul(), dead=True)
    e = raises(BO.OrderFailed, g.battle_attack, 0, 20)
    assert e.kind == "noop" and e.record["attempts"] == 3


@test
def shoot_spends_a_shot_and_a_move():
    g = FakeBattle(rome_gaul())
    g.b["slots"][1].update(x=2, y=4)                         # archer 2 tiles from (0,3)? cheb((2,4),(0,3)) = 2: in range
    r = g.battle_shoot(1, 20)
    s = g.b["slots"][1]
    assert r["ok"] and s["ammo"] == 24 and s["state"] == 3 and r["target_troops"] == (5000, 4990), (r, s)
    assert g.clicks[-1][0] == "R"                            # the shot is a RIGHT click


@test
def shoot_preconditions_click_nothing():
    g = FakeBattle(rome_gaul())
    raises(D.DriverError, g.battle_shoot, 0, 20)             # HI has no shots
    raises(D.DriverError, g.battle_shoot, 1, 21)             # out of range
    b = rome_gaul()
    b["slots"][1].update(x=2, y=4, state=0)
    raises(D.DriverError, FakeBattle(b).battle_shoot, 1, 20)  # no moves
    b = rome_gaul()
    b["slots"][1].update(x=2, y=4, ammo=0)
    raises(D.DriverError, FakeBattle(b).battle_shoot, 1, 20)  # no shots
    assert g.clicks == []


@test
def shoot_noop():
    g = FakeBattle(rome_gaul(), dead=True)
    g.b["slots"][1].update(x=2, y=4)
    e = raises(BO.OrderFailed, g.battle_shoot, 1, 20)
    assert e.kind == "noop" and e.record["attempts"] == 3 and all(c[0] in "LR" for c in g.clicks)


@test
def end_turn_one_click_proven():
    g = FakeBattle(rome_gaul())
    r = g.battle_end_turn()
    assert r["ok"] and r["half_round_before"] == 3 and r["half_round_after"] == 5 and not r["ended"], r
    assert len(g.clicks) == 1


@test
def end_turn_without_proof_is_never_repeated():
    g = FakeBattle(rome_gaul(), end_noop=True)
    e = raises(D.DriverError, g.battle_end_turn)
    assert "not clicking again" in str(e) and len(g.clicks) == 1, (str(e), g.clicks)


@test
def surrender_no_leaves_the_block_identical():
    g = FakeBattle(rome_gaul())
    raw = BB.encode_block(g.b)
    r = g.battle_surrender("no")
    assert r["ok"] and r["in_battle"] and r["block_unchanged"] and g.pressed == ["No"], (r, g.pressed)
    assert BB.encode_block(g.b) == raw


@test
def surrender_yes_ends_the_battle():
    g = FakeBattle(rome_gaul())
    r = g.battle_surrender("yes")
    assert r["ok"] and not r["in_battle"] and r["battle_ended_box"] and g.pressed == ["Yes"], (r, g.pressed)


@test
def surrender_bad_answer_or_missing_box_presses_nothing():
    g = FakeBattle(rome_gaul())
    raises(D.DriverError, g.battle_surrender, "cancel")
    assert g.clicks == [] and g.pressed == []
    g2 = FakeBattle(rome_gaul(), confirm=False)               # the button opens no box: nothing to answer
    g2.wait = lambda cond, timeout, what, step=0.5: (_ for _ in ()).throw(D.DriverError("timeout waiting for " + what))
    raises(D.DriverError, g2.battle_surrender, "yes")
    assert g2.pressed == []


@test
def surrender_never_presses_cancel():
    g = FakeBattle(rome_gaul())
    g.battle_surrender("no")
    g2 = FakeBattle(rome_gaul())
    g2.battle_surrender("yes")
    assert "Cancel" not in g.pressed + g2.pressed


@test
def tile_geometry():
    g = FakeBattle(rome_gaul())
    assert g.battle_xy(0, 0) == (21, 145) and g.battle_xy(13, 11) == (437, 497), (g.battle_xy(0, 0), g.battle_xy(13, 11))
    raises(D.DriverError, g.battle_xy, 14, 0)
    raises(D.DriverError, g.battle_xy, 0, 12)
    assert g.battle_button_xy("end_turn") == (119, 112)


def main():
    fails = 0
    for t in TESTS:
        try:
            t()
            print("ok   ", t.__name__)
        except Exception:      # noqa: BLE001
            fails += 1
            print("FAIL ", t.__name__)
            traceback.print_exc()
    print("%d tests, %d failed" % (len(TESTS), fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
