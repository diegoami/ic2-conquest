"""The human order set of the tactical battle screen (battles plan B7): place, move, melee, shoot, end turn, surrender.

`BattleGame(Game)` adds six orders to the driver without touching `harness/driver.py` (another branch edits `play_battle` there):

    battle_place(slot, x, y)        placement phase: select own unit, click an empty cell of the home rows (attacker y < 3, defender y > 8)
    battle_move(slot, x, y)         select own unit, click an empty cell: the unit walks up to its moves left (Bresenham path)
    battle_attack(slot, target)     select own unit, left-click an ADJACENT enemy: sets the melee target (word 9); costs no move
    battle_shoot(slot, target)      select own unit, RIGHT-click an enemy in range: one shot (word 8 and moves fall)
    battle_end_turn()               ONE End turn click, proven by the half-round counter / flag; never repeated
    battle_surrender(answer)        the Surrender button, then the "Are you sure you want to surrender ?" box answered "no" or "yes" (never Cancel)

UI facts used [R-code: research repo `docs/reports/2026-10-04-decompiled-tactical-battle-rules.md` section 3 "Human actions", read only; the live
checks are `runs/experiments/data/run-exp-battle-orders/`]. Screen geometry [O]: the battle window is 448 x 414 at the screen position
`find_windows(" v ")` reports; tile (x, y), x 0..13, y 0..11, has its centre at (win_x + 32 x + 16, win_y + 30 + 32 y + 16); the toolbar row is
at win_y + 13 (y = 112 for a window at y = 99).

**Verification (the task's forbidden results).** Every order reads the battle block from game memory (`battle_state`) before and after and
accepts the order ONLY when the block shows its effect (position, target word 9, shots word 8 and moves word 7, header counter). An order that
changed nothing at all (the block is byte-identical: the first click into an inactive window may only activate it, or the click missed) is
retried, at most `retries` (default 2) times; an order that changed the block in any other way than the expected one raises
`OrderFailed` at once (no retry: the state moved, a retry could spend a second move). End turn is never retried: with no proof the click
advanced the battle `DriverError` propagates ("not clicking again").
"""
import re
import struct
import subprocess
import time

from harness import driver as D
from harness.driver import DriverError, Game, sh
from state import battle_block as BB

MAP_DY = 30                      # window top to the top of tile row 0
BUTTON_DY = 13                   # window top to the toolbar row centre
# toolbar button centres relative to the window's left edge (screenshot of the window at x = 5: icons at 19, 44, 68, 94, 119, 146, 171, 198) and
# the tooltip each one shows (B8's tooltip scan, `b8-layout-*.jsonl`)
BUTTONS = {"unit_moves": (14, "Unit moves"), "friendly": (39, "Friendly units"), "enemy": (63, "Enemy units"), "cancel": (89, "Cancel selection"),
           "end_turn": (114, "End turn"), "pauses": (141, "Change pauses"), "computer": (166, "Computer general on"), "surrender": (193, "Surrender")}
RANGE = {"li": 1, "ar": 2, "lc": 1}          # shooting range by type [R-code]; hi and hc have no shots
HOME = {0: lambda y: y < 3, 1: lambda y: y > 8}


class OrderFailed(DriverError):
    """An order whose effect the block does not show. `kind`: "noop" (block unchanged after every attempt) or "wrong" (changed, not as ordered)."""

    def __init__(self, msg, kind, record=None):
        super().__init__(msg)
        self.kind, self.record = kind, record


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


class BattleGame(Game):
    CHANGE_TIMEOUT = 2.5         # s to wait for the block to change after an order's clicks (a no-op attempt costs this much)
    SETTLE = 0.15                # s between the first sign of change and the read-back
    CLICK_PAUSE = 0.2            # s after each of an order's clicks (the click itself hovers 0.25 s first)

    # ---- geometry --------------------------------------------------------------
    def battle_window(self):
        w = self.find_windows(" v ")
        if not w:
            raise DriverError("no battle window (title '<A>  v  <B>')")
        return w[0]

    def battle_xy(self, x, y):
        """Screen centre of battle tile (x, y)."""
        if not (0 <= x < BB.GRID_W and 0 <= y < BB.GRID_H):
            raise DriverError("battle tile (%s, %s) is outside the %d x %d grid" % (x, y, BB.GRID_W, BB.GRID_H))
        w = self.battle_window()
        return (w[2] + 32 * x + 16, w[3] + MAP_DY + 32 * y + 16)

    def battle_button_xy(self, name):
        w = self.battle_window()
        return (w[2] + BUTTONS[name][0], w[3] + BUTTON_DY)

    def rclick(self, x, y, pause=0.4):
        sh("xdotool", "mousemove", str(x), str(y))
        time.sleep(0.25)
        sh("xdotool", "click", "3")
        time.sleep(pause)

    def battle_focus(self):
        """Raise and focus the battle window (it can end up below the game's other windows, e.g. after a File > Save As)."""
        w = self.battle_window()
        sh("xdotool", "windowraise", str(w[0]), check=False)
        sh("xdotool", "windowfocus", str(w[0]), check=False)
        time.sleep(0.2)

    # ---- the generic verified order ---------------------------------------------
    @staticmethod
    def _raw(b):
        return BB.encode_block(b)

    def _wait_change(self, before_raw, timeout=None, step=0.1):
        """Poll the block until it differs from `before_raw` (or the battle ended / the timeout passes); returns the block or None when the battle is over."""
        timeout = self.CHANGE_TIMEOUT if timeout is None else timeout
        t0 = time.time()
        while True:
            try:
                now = self.battle_state()
            except DriverError:
                return None
            if self._raw(now) != before_raw or time.time() - t0 > timeout:
                return now
            time.sleep(step)

    def _verified(self, name, clicks, check, retries=2):
        """Run `clicks()` (the order's mouse clicks), then require `check(before, after)` -> (ok, why). A block that did not change at all is a no-op: the
        order is retried up to `retries` times, then OrderFailed("noop"); a block that changed but fails the check raises OrderFailed("wrong") at once."""
        before = self.battle_state()
        raw0 = self._raw(before)
        rec = {"order": name, "attempts": 0}
        for attempt in range(1, retries + 2):
            rec["attempts"] = attempt
            clicks()
            after = self._wait_change(raw0)
            if after is None:               # the battle ended on this order
                rec.update(ok=True, ended=True)
                return rec, before, None
            time.sleep(self.SETTLE)
            after = self.battle_state()
            if self._raw(after) == raw0:
                rec["noop_attempts"] = attempt
                continue
            ok, why = check(before, after)
            rec.update(ok=bool(ok), why=why)
            if ok:
                return rec, before, after
            raise OrderFailed("%s: the block does not show the order's effect: %s" % (name, why), "wrong", rec)
        raise OrderFailed("%s: no effect on the block after %d attempt(s) (a silent no-op)" % (name, rec["attempts"]), "noop", rec)

    def _own(self, b, slot, side=None):
        side = b["x2"] if side is None else side        # header x2 = the side to move [O: B5]
        if not 0 <= slot < BB.N_SLOTS or b["slots"][slot]["side"] != side:
            raise DriverError("slot %s is not a unit of the side to move (side %s)" % (slot, side))
        s = b["slots"][slot]
        if not s["alive"]:
            raise DriverError("slot %s is not alive" % slot)
        return s

    def _select_click(self, s):
        self.click(*self.battle_xy(s["x"], s["y"]), pause=self.CLICK_PAUSE)

    # ---- the orders ---------------------------------------------------------------
    def battle_place(self, slot, x, y, retries=2):
        """Placement: put own unit `slot` on the empty cell (x, y) of the home rows. Verified: the slot stands at (x, y) afterwards."""
        b = self.battle_state()
        s = self._own(b, slot)
        if b["y1"] != 0:
            raise DriverError("battle_place: the placement phase is over (y1 = %d)" % b["y1"])
        if not HOME[s["side"]](y):
            raise DriverError("battle_place: row %d is not a home row of side %d" % (y, s["side"]))
        if (s["x"], s["y"]) == (x, y):
            return {"order": "place", "slot": slot, "attempts": 0, "ok": True, "why": "already there"}
        if any(o["alive"] and (o["x"], o["y"]) == (x, y) for o in b["slots"]):
            raise DriverError("battle_place: cell (%d, %d) is occupied" % (x, y))

        def check(be, af):
            n = af["slots"][slot]
            return (n["x"], n["y"]) == (x, y), "slot %d at (%d,%d), wanted (%d,%d)" % (slot, n["x"], n["y"], x, y)

        rec, _, _ = self._verified("place", lambda: (self._select_click(s), self.click(*self.battle_xy(x, y), pause=self.CLICK_PAUSE)), check, retries)
        rec.update(slot=slot, to=(x, y))
        return rec

    def battle_move(self, slot, x, y, partial=False, retries=2):
        """Move own unit `slot` towards the empty cell (x, y). Verified: the unit stands at (x, y) and its moves word fell; with `partial=True` a unit that
        ended no farther from the target, having paid at least one move per cell travelled (a blocked path stops the walk early), also passes. A path blocked from the first step changes nothing: OrderFailed("noop")."""
        b = self.battle_state()
        s = self._own(b, slot)
        if b["y1"] != 1:
            raise DriverError("battle_move: not in the move phase (y1 = %d)" % b["y1"])
        if s["state"] < 1:
            raise DriverError("battle_move: slot %d has no moves left" % slot)
        if (s["x"], s["y"]) == (x, y):
            return {"order": "move", "slot": slot, "attempts": 0, "ok": True, "why": "already there"}
        if any(o["alive"] and (o["x"], o["y"]) == (x, y) for o in b["slots"]):
            raise DriverError("battle_move: cell (%d, %d) is occupied" % (x, y))

        def check(be, af):
            n, o = af["slots"][slot], be["slots"][slot]
            pos = (n["x"], n["y"])
            if n["state"] >= o["state"] or pos == (o["x"], o["y"]):
                return False, "slot %d moves %d -> %d, position %s -> %s" % (slot, o["state"], n["state"], (o["x"], o["y"]), pos)
            if pos == (x, y):
                return True, "arrived, moves %d -> %d" % (o["state"], n["state"])
            steps = cheb(pos, (o["x"], o["y"]))
            if partial and cheb(pos, (x, y)) <= cheb((o["x"], o["y"]), (x, y)) and o["state"] - n["state"] >= steps:
                # moved, no farther from the destination (a detour around a blocked cell can be sideways), and paid at least one move per cell travelled;
                # the walk stops early when the path is blocked, so moves may be left over
                return True, "partial: %s -> %s (distance %d -> %d), moves %d -> %d" % ((o["x"], o["y"]), pos, cheb((o["x"], o["y"]), (x, y)), cheb(pos, (x, y)), o["state"], n["state"])
            return False, "slot %d stands at %s, wanted %s (partial=%s)" % (slot, pos, (x, y), partial)

        rec, _, _ = self._verified("move", lambda: (self._select_click(s), self.click(*self.battle_xy(x, y), pause=self.CLICK_PAUSE)), check, retries)
        rec.update(slot=slot, to=(x, y))
        return rec

    def battle_attack(self, slot, target, retries=2):
        """Melee order: own unit `slot` attacks the ADJACENT enemy `target` (a slot). Verified: word 9 of `slot` equals `target`."""
        b = self.battle_state()
        s = self._own(b, slot)
        t = b["slots"][target] if 0 <= target < BB.N_SLOTS else None
        if t is None or t["side"] == s["side"] or not t["alive"]:
            raise DriverError("battle_attack: slot %s is not a live enemy" % target)
        if s["state"] < 1:
            raise DriverError("battle_attack: slot %d has no moves left" % slot)
        if cheb((s["x"], s["y"]), (t["x"], t["y"])) != 1:
            raise DriverError("battle_attack: slot %d at %s is not adjacent to slot %d at %s" % (slot, (s["x"], s["y"]), target, (t["x"], t["y"])))
        if s["target"] == target:
            return {"order": "attack", "slot": slot, "target": target, "attempts": 0, "ok": True, "why": "already targeting"}

        def check(be, af):
            return af["slots"][slot]["target"] == target, "slot %d target word %d -> %d, wanted %d" % (slot, be["slots"][slot]["target"], af["slots"][slot]["target"], target)

        rec, _, _ = self._verified("attack", lambda: (self._select_click(s), self.click(*self.battle_xy(t["x"], t["y"]), pause=self.CLICK_PAUSE)), check, retries)
        rec.update(slot=slot, target=target)
        return rec

    def battle_shoot(self, slot, target, retries=2):
        """Shoot: own unit `slot` (LI, archers or LC with shots left) RIGHT-clicks the enemy `target` within range. Verified: shots word 8 fell and the
        moves word fell (one shot costs one of each). The loss is reported in the record (it can be 0: Random(n) + Random(n))."""
        b = self.battle_state()
        s = self._own(b, slot)
        t = b["slots"][target] if 0 <= target < BB.N_SLOTS else None
        if t is None or t["side"] == s["side"] or not t["alive"]:
            raise DriverError("battle_shoot: slot %s is not a live enemy" % target)
        rng = RANGE.get(s["type"], 0)
        if rng == 0 or s["ammo"] < 1 or s["state"] < 1:
            raise DriverError("battle_shoot: slot %d (%s) cannot shoot (shots %d, moves %d)" % (slot, s["type"], s["ammo"], s["state"]))
        if cheb((s["x"], s["y"]), (t["x"], t["y"])) > rng:
            raise DriverError("battle_shoot: slot %d at %s is out of range %d of slot %d at %s" % (slot, (s["x"], s["y"]), rng, target, (t["x"], t["y"])))

        def check(be, af):
            o, n = be["slots"][slot], af["slots"][slot]
            return (n["ammo"] < o["ammo"] and n["state"] < o["state"]), "slot %d shots %d -> %d, moves %d -> %d" % (slot, o["ammo"], n["ammo"], o["state"], n["state"])

        rec, before, after = self._verified("shoot", lambda: (self._select_click(s), self.rclick(*self.battle_xy(t["x"], t["y"]), pause=self.CLICK_PAUSE)), check, retries)
        rec.update(slot=slot, target=target)
        if after is not None:
            rec["target_troops"] = (before["slots"][target]["troops"], after["slots"][target]["troops"])
        return rec

    def battle_end_turn(self):
        """ONE End turn click with proof it advanced (`end_turn_proven`: flag, title, BATTLEnn count or half-round counter moves within 8 s). The window is raised
        and focused first (not a retry). No retry of any kind: with no proof DriverError propagates (the click may still be queued). Returns the record with
        the counters before and after, `ended` True when the battle is over."""
        self.battle_focus()
        h0 = self.half_round_counter()
        self.end_turn_proven(lambda: self.click(*self.battle_button_xy("end_turn"), pause=1.0))
        time.sleep(0.5)
        ended = (not self.in_battle()) or bool(self.find_windows("Battle ended"))
        return {"order": "end_turn", "attempts": 1, "ok": True, "half_round_before": h0, "half_round_after": None if ended else self.half_round_counter(), "ended": ended}

    def battle_surrender(self, answer):
        """The Surrender button, then the Confirm box "Are you sure you want to surrender ?" is answered `answer` ("no" or "yes"; Cancel is never pressed).
        Returns what was captured: the box's windows, texts and controls, whether the battle is still on and whether the block changed. "no": verified that the
        box closed and the block is byte-identical. "yes": the box closed; what follows (Battle ended, flag) is read and returned, not assumed."""
        if answer not in ("no", "yes"):
            raise DriverError("battle_surrender: answer must be 'no' or 'yes', not %r" % (answer,))
        before = self._raw(self.battle_state())
        self.battle_focus()
        self.click(*self.battle_button_xy("surrender"), pause=1.5)
        box = self.wait(lambda: [p for p in self.find_windows("^Confirm$")], 8, "the surrender Confirm box")[0]
        text = self.read_popup(box)
        cs = self.controls("Confirm")
        rec = {"order": "surrender", "answer": answer, "box_text": text, "box_controls": [c["text"] for c in cs], "box_geometry": list(box[2:])}
        if "surrender" not in text.lower():
            raise DriverError("battle_surrender: the Confirm box is not the surrender box: %r (nothing pressed)" % text)
        want = next((c for c in cs if c["text"].replace("&", "").strip().lower() == answer), None)
        if want is None:
            raise DriverError("battle_surrender: no %r control among %s (nothing pressed)" % (answer, [c["text"] for c in cs]))
        for attempt in range(1, 4):          # the first click into an inactive window may only activate it; the box closing is the proof
            self.click_control(want, pause=1.2)
            if not self.find_windows("^Confirm$"):
                break
        rec["attempts"] = attempt
        if self.find_windows("^Confirm$"):
            raise OrderFailed("battle_surrender: the box is still open after %d answers %r" % (attempt, answer), "noop", rec)
        time.sleep(1.0)
        rec["in_battle"] = self.in_battle()
        rec["battle_ended_box"] = bool(self.find_windows("Battle ended"))
        if rec["in_battle"]:
            rec["block_unchanged"] = self._raw(self.battle_state()) == before
        if answer == "no" and (not rec["in_battle"] or not rec["block_unchanged"]):
            raise OrderFailed("battle_surrender(no): the battle changed (in_battle=%s, block_unchanged=%s)" % (rec["in_battle"], rec.get("block_unchanged")), "wrong", rec)
        rec["ok"] = True
        return rec

    def battle_finish(self, shot=None, on_dialog="no"):
        """After the last End turn: the "Battle ended" box (screenshot to `shot`), its OK, then every box that follows (Offer of peace: `on_dialog` "no" declines;
        "capture" also screenshots, "strict" raises). Same tail as `play_battle` but without turning Computer general on. Returns {"battle_ended_text", "dialogs"}."""
        if on_dialog not in ("capture", "no", "strict"):
            raise DriverError("battle_finish: on_dialog must be 'capture', 'no' or 'strict' (never 'yes')")
        res = {"battle_ended_text": None, "dialogs": []}
        w = self.find_windows("Battle ended") or self.wait(lambda: self.find_windows("Battle ended"), 30, "Battle ended box")
        if shot:
            self.shot(shot, window=str(w[0][0]))
        res["battle_ended_text"] = self.read_popup(w[0])
        try:
            self.click_control(self.control(self.controls("Battle ended"), text="OK"), pause=1.5)
        except DriverError:
            self.key("Return")
            time.sleep(1.5)
            if self.popups():
                self.click(220, 478, pause=1.5)
        try:
            self.wait(lambda: self._post_battle_windows() or (self.find_windows("^Unit map$") and not self.find_windows("Battle ended")), 60,
                      "map or a dialog after the Battle ended box")
        except DriverError:
            pass
        time.sleep(2)
        for _ in range(6):
            boxes = self._post_battle_windows()
            if not boxes:
                break
            res["dialogs"].append(self._answer_post_battle(boxes[0], on_dialog))
            if on_dialog == "strict":
                raise DriverError("battle: unexpected dialog: " + res["dialogs"][-1]["text"])
            time.sleep(1.5)
        return res
