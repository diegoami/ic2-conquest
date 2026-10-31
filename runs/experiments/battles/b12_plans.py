"""The three scripted plans of B12 (docs/tasks/battles-b7-b12.md), played by the bot as Rome (side 0, the attacker) against Computer general (Gaul, side 1).

The definitions were approved by the player on 2026-10-05; this file is their implementation and states every choice the definitions leave open (the bot's
choices, not the best ones). Every order goes through `harness/battle_orders.py` (verified on the block, <= 2 retries, no blind End turn).

**Placement (all three plans, identical):** every Rome unit goes to row y = 2 (the front home row), in slot order, centred: x = (14 - n) // 2 + i. (Computer general
places by a random formation, `Random(5)`; a human side that places draws nothing from the random stream: that is the first point where a played battle and
the Computer general battle of its pair can differ, and the hook log shows it.)

**P-HOLD:** nobody advances. An archer (`ar`) with shots shoots the nearest enemy within range 2 (ties: fewest troops, then the lowest slot) until it is out of moves, shots or
targets. Every other unit, and an archer that has moves left and an adjacent enemy, sets its melee target on the adjacent enemy with the fewest troops (ties: lowest slot).
LI and LC have shots but P-HOLD does not use them ("archers shoot").

**P-FOCUS:** one target T per half-round: among the enemies nearest to any Rome unit (smallest Chebyshev distance to a Rome unit), the one with the fewest troops (ties: lowest slot);
kept until it is gone (routed or destroyed), then the same rule again. Archers first: in range 2 of T they shoot T until out of moves, shots or T; otherwise they move to the free
cell nearest to them that is at distance 2 from T (else 1) and shoot with what is left. Every other unit adjacent to T sets its melee target on T; one that is not walks (all its
moves) to the free cell adjacent to T that is nearest to it and, if it still has a move and now is adjacent, sets the melee target. Units that cannot reach T this half-round
advance towards it; they attack when they get there. The plan's focus factor f = 4 (attacker loss x1/5, defender x13/5 [D]) is the game's, not set by the bot.

**P-CAV:** LC and HC go round a flank and attack enemy archers first, then the nearest enemy; every other unit does what P-HOLD does. A cavalry unit's target is the nearest enemy archer
(Chebyshev distance from the unit; ties fewest troops, lowest slot), else the nearest enemy (same ties). If it is adjacent to the target it sets the melee target. Otherwise it goes
by the flank: the flank column is fx = 0 when the target stands at x <= 6, else 13; leg 1 is along the unit's own row to (fx, y) (then, with moves left, leg 2 is along column fx
down to the row of the target), leg 3 is the free cell adjacent to the target nearest to the unit; the first leg not yet done is the one ordered, and the unit ends the
half-round with a melee target if it stands next to the target with a move left.

Every order raises on an unverified effect (`OrderFailed`); the plan catches only `OrderFailed("noop")` for MOVES (a blocked path), counts it in `blocked`, and goes on; any other
error ends the trial as an error (it is recorded, never retried silently).
"""
from harness.battle_orders import OrderFailed, cheb
from harness.driver import DriverError

MAX_HALF_ROUNDS = 80                # Rome half-rounds before the trial gives up (the game has no limit [R-code]; a stalemate is an error row, not a result)


def own(st):
    return [s for s in st["slots"][:20] if s["alive"]]


def foes(st):
    return [s for s in st["slots"][20:] if s["alive"]]


def pos(s):
    return (s["x"], s["y"])


def occupied(st):
    return {pos(s) for s in st["slots"] if s["alive"]}


def free_cells_adjacent(st, t, radius=1):
    occ = occupied(st)
    out = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            c = (t["x"] + dx, t["y"] + dy)
            if max(abs(dx), abs(dy)) == radius and 0 <= c[0] < 14 and 0 <= c[1] < 12 and c not in occ:
                out.append(c)
    return out


def nearest_free(st, u, t, radius):
    """The free cell at distance `radius` from T that is nearest to u (ties: smaller x, then y), or None."""
    cs = free_cells_adjacent(st, t, radius)
    return min(cs, key=lambda c: (cheb(pos(u), c), c)) if cs else None


class Plan:
    name = "plan"

    def __init__(self, g, log=None):
        self.g = g
        self.log = log or (lambda *a, **k: None)
        self.orders = []            # every order record, with the half-round it belongs to
        self.blocked = 0
        self.half = 0

    # ---- bookkeeping
    def do(self, fn, *a, **k):
        r = fn(*a, **k)
        r = dict(r)
        r["rome_half_round"] = self.half
        self.orders.append(r)
        return r

    def alive(self):
        return self.g.in_battle() and not self.g.find_windows("Battle ended")

    def st(self):
        return self.g.battle_state()

    def move(self, slot, dest):
        """A move that may legitimately find its path blocked: that one case (OrderFailed noop) is counted and skipped."""
        try:
            return self.do(self.g.battle_move, slot, dest[0], dest[1], partial=True, retries=1)
        except OrderFailed as e:
            if e.kind == "noop":
                self.blocked += 1
                rec = dict(e.record or {}, order="move", slot=slot, to=dest, ok=False, blocked=True, rome_half_round=self.half)
                self.orders.append(rec)
                return None
            raise

    # ---- placement
    def place(self):
        st = self.st()
        mine = own(st)
        x0 = (14 - len(mine)) // 2
        for i, u in enumerate(mine):
            self.do(self.g.battle_place, u["slot"], x0 + i, 2)

    # ---- shared pieces
    def shoot_nearest(self, slot):
        """An archer: shoot the nearest enemy in range 2 until out of moves, shots or targets. Returns False when the battle ended."""
        for _ in range(8):
            st = self.st()
            u = st["slots"][slot]
            if not (u["alive"] and u["type"] == "ar" and u["ammo"] > 0 and u["state"] > 0):
                break
            cand = [e for e in foes(st) if cheb(pos(u), pos(e)) <= 2]
            if not cand:
                break
            t = min(cand, key=lambda e: (cheb(pos(u), pos(e)), e["troops"], e["slot"]))
            r = self.do(self.g.battle_shoot, slot, t["slot"])
            if r.get("ended") or not self.alive():
                return False
        return True

    def melee_adjacent(self, slot):
        st = self.st()
        u = st["slots"][slot]
        if not u["alive"] or u["state"] < 1:
            return
        adj = [e for e in foes(st) if cheb(pos(u), pos(e)) == 1]
        if adj:
            t = min(adj, key=lambda e: (e["troops"], e["slot"]))
            self.do(self.g.battle_attack, slot, t["slot"])

    def hold_unit(self, slot):
        st = self.st()
        if st["slots"][slot]["type"] == "ar":
            if not self.shoot_nearest(slot):
                return False
        self.melee_adjacent(slot)
        return self.alive()

    def half_round(self):
        raise NotImplementedError

    # ---- the loop
    def play(self):
        """Place, then half-rounds until the battle is over; returns the list of order records. Raises DriverError when MAX_HALF_ROUNDS pass."""
        self.half = 0
        self.place()
        self.do(self.g.battle_end_turn)             # ends Rome's placement half-round (counter 2 -> 3); Rome then moves first
        for self.half in range(1, MAX_HALF_ROUNDS + 1):
            if not self.alive():
                break
            self.half_round()
            if not self.alive():
                break
            r = self.do(self.g.battle_end_turn)
            self.log("half_round", n=self.half, orders=len(self.orders), end=r)
            if r.get("ended"):
                break
        else:
            raise DriverError("%s: the battle is not over after %d Rome half-rounds" % (self.name, MAX_HALF_ROUNDS))
        return self.orders


class Hold(Plan):
    name = "p-hold"

    def half_round(self):
        for u in own(self.st()):
            if not self.alive() or not self.hold_unit(u["slot"]):
                return


class Focus(Plan):
    name = "p-focus"

    def target(self, st, current=None):
        fs = foes(st)
        if not fs:
            return None
        if current is not None and st["slots"][current]["alive"]:
            return st["slots"][current]
        ms = own(st)
        dist = {e["slot"]: min(cheb(pos(e), pos(u)) for u in ms) for e in fs}
        dmin = min(dist.values())
        return min((e for e in fs if dist[e["slot"]] == dmin), key=lambda e: (e["troops"], e["slot"]))

    def half_round(self):
        T = None
        order = sorted(own(self.st()), key=lambda u: (u["type"] != "ar", u["slot"]))      # archers first, then slot order
        for u0 in order:
            if not self.alive():
                return
            st = self.st()
            u = st["slots"][u0["slot"]]
            if not u["alive"]:
                continue
            T = self.target(st, None if T is None else T["slot"])
            if T is None:
                return
            if u["type"] == "ar":
                if u["ammo"] > 0 and u["state"] > 0:
                    if cheb(pos(u), pos(T)) > 2:
                        dest = nearest_free(st, u, T, 2) or nearest_free(st, u, T, 1)
                        if dest is not None:
                            self.move(u["slot"], dest)
                    st = self.st()
                    u = st["slots"][u["slot"]]
                    # shoot T while it is in range; otherwise the nearest in range (shoot_nearest) so that a spent move is not wasted
                    for _ in range(8):
                        st = self.st()
                        u = st["slots"][u0["slot"]]
                        if not (u["alive"] and u["ammo"] > 0 and u["state"] > 0 and st["slots"][T["slot"]]["alive"] and cheb(pos(u), pos(T)) <= 2):
                            break
                        r = self.do(self.g.battle_shoot, u["slot"], T["slot"])
                        if r.get("ended") or not self.alive():
                            return
                st = self.st()
                u = st["slots"][u0["slot"]]
                T = self.target(st, T["slot"] if st["slots"][T["slot"]]["alive"] else None)
                if T is not None and u["alive"] and u["state"] >= 1 and cheb(pos(u), pos(T)) == 1:
                    self.do(self.g.battle_attack, u["slot"], T["slot"])
                continue
            if cheb(pos(u), pos(T)) != 1:
                dest = nearest_free(st, u, T, 1)
                if dest is not None and u["state"] >= 1:
                    self.move(u["slot"], dest)
                st = self.st()
                u = st["slots"][u0["slot"]]
                T = self.target(st, T["slot"] if st["slots"][T["slot"]]["alive"] else None)
            if T is not None and u["alive"] and u["state"] >= 1 and cheb(pos(u), pos(T)) == 1:
                self.do(self.g.battle_attack, u["slot"], T["slot"])


class Cav(Plan):
    name = "p-cav"

    def cav_target(self, st, u):
        fs = foes(st)
        if not fs:
            return None
        ars = [e for e in fs if e["type"] == "ar"]
        pool = ars or fs
        return min(pool, key=lambda e: (cheb(pos(u), pos(e)), e["troops"], e["slot"]))

    def cav_unit(self, slot):
        st = self.st()
        u = st["slots"][slot]
        T = self.cav_target(st, u)
        if T is None or not u["alive"]:
            return
        for _ in range(3):                                   # at most three legs per half-round
            st = self.st()
            u = st["slots"][slot]
            T = self.cav_target(st, u)
            if T is None or not u["alive"] or u["state"] < 1:
                return
            if cheb(pos(u), pos(T)) == 1:
                self.do(self.g.battle_attack, slot, T["slot"])
                return
            fx = 0 if T["x"] <= 6 else 13
            occ = occupied(st)
            if u["x"] != fx and (fx, u["y"]) not in occ:
                dest = (fx, u["y"])                          # leg 1: along the unit's own row to the flank column
            elif u["y"] < T["y"] - 1 and (fx, T["y"]) not in occ and u["x"] == fx:
                dest = (fx, T["y"])                          # leg 2: down the flank column to the target's row
            else:
                dest = nearest_free(st, u, T, 1)             # leg 3: the free cell next to the target
            if dest is None or dest == pos(u):
                return
            if self.move(slot, dest) is None:
                return

    def half_round(self):
        for u in sorted(own(self.st()), key=lambda u: u["slot"]):
            if not self.alive():
                return
            if u["type"] in ("lc", "hc"):
                self.cav_unit(u["slot"])
            elif not self.hold_unit(u["slot"]):
                return


PLANS = {"p-hold": Hold, "p-focus": Focus, "p-cav": Cav}
