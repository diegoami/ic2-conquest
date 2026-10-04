#!/usr/bin/env python3
"""B11 exchange log: rebuild every shot, melee and rout of a hooked battle from the lab snapshots plus the hook's records, and check the research report's
formulas (docs/reports/2026-10-04-decompiled-tactical-battle-rules.md §4 shooting, §5 melee, §6 rout: all [R-code]) against what the game did.

    python3 runs/experiments/battles/b11_exchange.py TRIAL...       # TRIAL = e.g. hi-hi-one_s1_r2_hook (its BATTLEnn saves are in artifacts/, its hooklog in the data folder)

Method. The lab snapshot BATTLEnn is taken at the entry of the half-round end (FUN_00439C20), i.e. AFTER the side's moves and shots and BEFORE its melee [R-code,
re-checked in `check_semantics`]. The hook's records carry the half-round counter, so the records with counter k are: the moves phase of half-round k (shots,
rout tests, flank draws), then the melee marker, then the melee phase of half-round k. For k = 1.. the state S_k is read from BATTLEnn; the melee of k is replayed
on S_k with the recorded draws (the game's Random results are facts, the formulas turn them into losses), giving the state at the start of half-round k+1; the
moves phase of k+1 (shots and routs, in record order) is replayed on it and the result must equal S_{k+1} in every slot's troops, morale and presence.
Nothing is assumed: each prediction (the range `n` of every draw, which draws exist, each loss) is compared with the record, and each miss is listed.
Where the board lacks information (movement), only the draws and the snapshots are used. Actor and target of a shot are the marker's EAX and EDX; of a melee the
slot order of the report; both are CHECKED by the predicted `n` of the draws.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from state import battle_block as BB  # noqa: E402

TYPES = ("li", "hi", "ar", "lc", "hc")
STD = {"li": 15000, "hi": 6000, "ar": 3500, "lc": 7000, "hc": 2500}
FLOOR = {t: STD[t] // 25 for t in TYPES}                       # the rout floor: standard battalion div 25
VULN = {"li": 18, "hi": 2, "ar": 18, "lc": 15, "hc": 4}        # stat +0x20
RANGE = {"li": 1, "hi": 0, "ar": 2, "lc": 1, "hc": 0}
SHOTS0 = {"li": 7, "hi": 0, "ar": 25, "lc": 9, "hc": 0}
M = {"li": [15, 4, 20, 5, 3], "hi": [60, 5, 65, 15, 8], "ar": [10, 3, 18, 5, 3], "lc": [25, 8, 28, 15, 8], "hc": [18, 12, 20, 12, 8]}   # M[a][d], DAT 0x1F7A6
MARK_SHOT, MARK_MELEE, MARK_ROUT = 0x43910C, 0x4393EC, 0x438FB0
S_SHOT, S_MELEE, S_ROUT = (0x439188, 0x439191), (0x439557, 0x43955F, 0x4395CE, 0x4395D8), (0x438FFB, 0x439006)
S_COPY, S_PLACE, S_FLANK, S_POST = (0x43801A, 0x43812F), 0x43820D, 0x43AA88, (0x4592BD, 0x45951C)


def i32(x):
    x &= 0xFFFFFFFF
    return x - (1 << 32) if x & 0x80000000 else x


def idiv(a, b):
    """Delphi `div` on 32-bit integers: truncates toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def load_log(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append({"seq": int(r["seq"]), "kind": r["kind"], "site": int(r["site"], 16), "eax": int(r["eax"]), "edx": int(r["edx"]), "ecx": int(r["ecx"]),
                         "seed_before": int(r["seed_before"]), "seed_after": int(r["seed_after"]), "result": int(r["result"]), "counter": int(r["counter"]),
                         "side": int(r["side"]), "flag": int(r["flag"]), "ebp": int(r["ebp"], 16)})
    return rows


def sx16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def load_series(art, tag):
    files = sorted(Path(art).glob("%s_BATTLE[0-9][0-9].SAV" % tag))
    return [BB.from_save(f) for f in files], [f.name for f in files]


class State:
    """Mutable copy of the fields the rules touch: troops, morale, target, plus the fixed type and quality, per slot 0..39."""

    def __init__(self, block):
        self.t = [TYPES.index(s["type"]) if isinstance(s["type"], str) else s["type"] for s in block["slots"]]
        self.tr = [s["troops"] for s in block["slots"]]
        self.q = [s["quality"] for s in block["slots"]]
        self.m = [s["morale"] for s in block["slots"]]
        self.tg = [s["target"] for s in block["slots"]]
        self.shots = [s["ammo"] for s in block["slots"]]

    def copy(self):
        o = State.__new__(State)
        o.t, o.tr, o.q, o.m, o.tg, o.shots = self.t[:], self.tr[:], self.q[:], self.m[:], self.tg[:], self.shots[:]
        return o

    def typ(self, u):
        return TYPES[self.t[u]]

    def live(self, u):
        return self.tr[u] > 0

    def side_of(self, u):
        return 0 if u < 20 else 1

    def side_live(self, side):
        return [u for u in range(side * 20, side * 20 + 20) if self.tr[u] > 0]


class Replay:
    """Replays record groups on a State and keeps the exchanges and every miss."""

    def __init__(self, recs, st, hr, log):
        self.recs, self.i, self.st, self.hr, self.log = recs, 0, st, hr, log
        self.ex, self.miss = [], []

    def peek(self):
        return self.recs[self.i] if self.i < len(self.recs) else None

    def take(self):
        r = self.recs[self.i]
        self.i += 1
        return r

    def note(self, why, **kw):
        self.miss.append({"half_round": self.hr, "why": why, **kw})

    # -- Rout(u) (FUN_00438FB0) -------------------------------------------------
    def rout(self, u, ctx):
        """Replays the Rout marker at self.i (already consumed by the caller) for slot u. Returns the exchange row."""
        st = self.st
        row = {"half_round": self.hr, "kind": "rout_test", "unit": u, "ctx": ctx, "troops": st.tr[u], "morale": st.m[u], "type": st.typ(u)}
        if not st.live(u):
            row["pred_draws"] = 0
            row["note"] = "unit already removed"
            draws = self.draws(S_ROUT)
            row["draws"] = [d["result"] for d in draws]
            if draws:
                self.note("rout draws for an already removed unit", unit=u)
            return row
        floor = FLOOR[st.typ(u)]
        test = st.tr[u] >= floor and st.m[u] > 19
        if test and st.m[u] > 39:
            test = False       # returns without drawing
            pred_draws, removed = 0, False
        elif test:
            pred_draws = 2
        else:
            pred_draws, removed = 0, True
        draws = self.draws(S_ROUT)
        row["draws"] = [d["result"] for d in draws]
        row["ranges"] = [d["eax"] for d in draws]
        row["pred_draws"] = pred_draws
        if len(draws) != pred_draws:
            self.note("rout: number of draws differs from the report's rule", unit=u, predicted=pred_draws, observed=len(draws), troops=st.tr[u], morale=st.m[u], floor=floor)
            removed = None
            if len(draws) == 2:
                removed = sum(d["result"] for d in draws) <= 29
        elif pred_draws == 2:
            if any(d["eax"] != st.m[u] for d in draws):
                self.note("rout: Random range is not the unit's morale", unit=u, ranges=row["ranges"], morale=st.m[u])
            removed = sum(d["result"] for d in draws) <= 29
        row["removed"] = removed
        if removed:
            self.remove(u)
        return row

    def remove(self, u):
        st = self.st
        side = st.side_of(u)
        st.tr[u] = 0
        for f in st.side_live(side):
            st.m[f] -= 6
            if st.m[f] < 30:
                st.tr[f] = 0                          # cascade: removed, no further cascade
        for e in st.side_live(1 - side):
            st.m[e] = min(99, st.m[e] + 5)
            if st.tg[e] == u:
                st.tg[e] = -1

    def draws(self, sites):
        """Consume the random records that directly follow, whose site is in `sites`."""
        out = []
        while True:
            r = self.peek()
            if r is None or r["kind"] != "random" or r["site"] not in sites:
                return out
            out.append(self.take())

    # -- one shot (FUN_0043910C) ------------------------------------------------
    def shot(self, marker):
        st = self.st
        s, t = sx16(marker["eax"]), sx16(marker["edx"])
        row = {"half_round": self.hr, "kind": "shot", "actor": s, "target": t, "seq": marker["seq"]}
        draws = self.draws(S_SHOT)
        row["draws"] = [d["result"] for d in draws]
        row["ranges"] = [d["eax"] for d in draws]
        if not (0 <= s < 40 and 0 <= t < 40):
            self.note("shot marker slots out of range", marker=(s, t))
            return row
        ts, tt = st.typ(s), st.typ(t)
        row["actor_type"], row["target_type"] = ts, tt
        row["troops_before"] = (st.tr[s], st.tr[t])
        if len(draws) != 2:
            self.note("shot: not two draws", actor=s, target=t, draws=len(draws))
            return row
        base = idiv(i32(st.tr[s] * st.q[s] * st.m[s] * VULN[tt]), st.tr[s] * 5 + 150000)
        cap = min(st.tr[s] // 3, st.tr[t] // 2)
        n1 = min(base, cap) + 1
        n2 = min(base * 2, cap) + 1
        n_obs = draws[0]["eax"]
        row["n_observed"], row["n_pred"], row["n_pred_doubled"] = n_obs, n1, n2
        if draws[0]["eax"] != draws[1]["eax"]:
            self.note("shot: the two draws have different ranges", actor=s, target=t, ranges=row["ranges"])
        if n_obs == n1:
            row["n_ok"], row["doubled"] = True, False
        elif n_obs == n2 and ts == "ar":
            row["n_ok"], row["doubled"] = True, True
        else:
            row["n_ok"] = False
            self.note("shot: observed n not predicted", actor=s, target=t, observed=n_obs, predicted=n1, predicted_doubled=n2, actor_type=ts, target_type=tt,
                      s_state=(st.tr[s], st.q[s], st.m[s]), t_troops=st.tr[t])
        loss = draws[0]["result"] + draws[1]["result"]
        row["loss"] = loss
        dm = min(3, (loss * 35) // (st.tr[t] + 1))
        row["morale_delta_target"] = -dm
        st.shots[s] -= 1
        st.m[t] -= dm
        st.tr[t] -= loss
        # Rout(target) follows
        r = self.peek()
        if r is not None and r["kind"] == "marker" and r["site"] == MARK_ROUT:
            self.take()
            row["rout"] = self.rout(sx16(r["eax"]), "after_shot")
            if sx16(r["eax"]) != t:
                self.note("rout after a shot is not for the shot's target", target=t, rout=sx16(r["eax"]))
        else:
            self.note("no Rout marker after a shot", actor=s, target=t)
        return row

    # -- the moves phase --------------------------------------------------------
    def moves(self):
        for _ in range(100000):
            r = self.peek()
            if r is None:
                return
            if r["kind"] == "marker" and r["site"] == MARK_MELEE:
                return
            self.take()
            if r["kind"] == "marker" and r["site"] == MARK_SHOT:
                self.ex.append(self.shot(r))
            elif r["kind"] == "marker" and r["site"] == MARK_ROUT:
                self.ex.append(self.rout(sx16(r["eax"]), "moves_phase"))
                self.note("a Rout call in the moves phase that did not follow a shot", unit=sx16(r["eax"]))
            elif r["kind"] == "random" and r["site"] == S_FLANK:
                self.ex.append({"half_round": self.hr, "kind": "flank_draw", "range": r["eax"], "result": r["result"], "seq": r["seq"]})
            elif r["kind"] == "random" and r["site"] == S_PLACE:
                self.ex.append({"half_round": self.hr, "kind": "placement_draw", "range": r["eax"], "result": r["result"], "seq": r["seq"]})
            else:
                self.note("unexpected record in the moves phase", seq=r["seq"], kind=r["kind"], site=hex(r["site"]))

    # -- the melee phase of the side `mover` -------------------------------------
    def melee(self, mover):
        st = self.st
        mk = self.peek()
        if mk is None or mk["kind"] != "marker" or mk["site"] != MARK_MELEE:
            self.note("no melee marker")
            return
        self.take()
        for a in range(mover * 20, mover * 20 + 20):
            d = st.tg[a]
            if not (st.tr[a] > 0 and d >= 0 and st.tr[d] > 0):
                continue
            row = {"half_round": self.hr, "kind": "melee", "actor": a, "target": d, "actor_type": st.typ(a), "target_type": st.typ(d)}
            draws = self.draws(S_MELEE)
            row["draws"] = [x["result"] for x in draws]
            row["ranges"] = [x["eax"] for x in draws]
            if len(draws) != 4:
                self.note("melee: not four draws for a qualifying pair", actor=a, target=d, draws=len(draws))
                self.ex.append(row)
                return
            ta, td = st.typ(a), st.typ(d)
            f = max(1, min(4, sum(1 for u in range(mover * 20, mover * 20 + 20) if st.tg[u] == d)))
            A = idiv(M[ta][TYPES.index(td)] * st.tr[a] * (st.q[a] * 10 + st.m[a]), 2000) + 12
            D = idiv(M[td][TYPES.index(ta)] * st.tr[d] * (st.q[d] * 10 + st.m[d]), 2000) + 12
            nA = idiv(idiv(i32(st.tr[a] * D), A), 12) + 1
            nD = idiv(idiv(i32(st.tr[d] * A), D), 10) + 1
            row.update({"f": f, "A": A, "D": D, "nA_pred": nA, "nD_pred": nD, "troops_before": (st.tr[a], st.tr[d]), "morale_before": (st.m[a], st.m[d])})
            rg = row["ranges"]
            row["n_ok"] = rg == [nA, nA, nD, nD]
            if not row["n_ok"]:
                self.note("melee: observed ranges differ from the report's nA, nD", actor=a, target=d, observed=rg, predicted=[nA, nA, nD, nD], f=f, A=A, D=D,
                          troops=(st.tr[a], st.tr[d]), q=(st.q[a], st.q[d]), m=(st.m[a], st.m[d]), types=(ta, td))
            r1, r2, r3, r4 = (x["result"] for x in draws)
            la = min(30000, idiv((r1 + r2) * (5 - f), 5))
            la = min(la, idiv(st.tr[a] * 4, 10)) + 1
            ld = min(30000, idiv((r3 + r4) * (2 * f + 5), 5))
            ld = min(ld, idiv(st.tr[d] * 4, 10)) + 1
            row["loss_actor"], row["loss_target"] = la, ld
            if idiv(st.tr[d], ld) < idiv(st.tr[a], la):
                st.m[a] = min(99, st.m[a] + 2)
                st.m[d] = min(99, st.m[d] - 3)
                row["morale_winner"] = "actor"
            else:
                st.m[a] = min(99, st.m[a] - 3)
                st.m[d] = min(99, st.m[d] + 2)
                row["morale_winner"] = "target"
            st.tr[a] -= la
            st.tr[d] -= ld
            row["rout"] = []
            for who in (a, d):
                r = self.peek()
                if r is not None and r["kind"] == "marker" and r["site"] == MARK_ROUT:
                    self.take()
                    if sx16(r["eax"]) != who:
                        self.note("rout after a melee is not for the expected unit", expected=who, got=sx16(r["eax"]))
                    row["rout"].append(self.rout(sx16(r["eax"]), "after_melee"))
                else:
                    self.note("no Rout marker after a melee", unit=who)
            self.ex.append(row)
        extra = [x for x in self.recs[self.i:] if x["kind"] in ("random", "marker")]
        if extra:
            self.note("records left over after the melee phase", count=len(extra), first=(extra[0]["kind"], hex(extra[0]["site"])))


def compare_states(tracked, block, hr):
    """Slot by slot: troops, morale (alive slots), presence. Returns the list of differences."""
    diffs = []
    for u in range(40):
        s = block["slots"][u]
        if tracked.tr[u] != s["troops"] and not (tracked.tr[u] <= 0 and s["troops"] <= 0):
            diffs.append({"half_round": hr, "slot": u, "field": "troops", "predicted": tracked.tr[u], "snapshot": s["troops"]})
        elif s["troops"] > 0 and tracked.m[u] != s["morale"]:
            diffs.append({"half_round": hr, "slot": u, "field": "morale", "predicted": tracked.m[u], "snapshot": s["morale"]})
        if s["troops"] > 0 and tracked.shots[u] != s["ammo"]:        # word 8: the shots the markers counted must be the drop in the snapshot
            diffs.append({"half_round": hr, "slot": u, "field": "shots", "predicted": tracked.shots[u], "snapshot": s["ammo"]})
    return diffs


def copy_in_check(S1, recs):
    """Copy-in (FUN_00437DE4): Random(q*4) per live slot, attackers 0..19 first (site 0x43801A) then defenders (0x43812F), in slot order; the morale of the slot is
    clamp(draw + base, 60, 90) with base the army's morale (+3 for a computer-controlled side): the base is INFERRED per side as the value that reproduces every slot
    (it is 65 for both armies in the staged cells; for the natural research start save it is the saved one)."""
    out = {}
    pre = [r for r in recs if r["kind"] == "random" and r["counter"] == 0 and r["site"] in S_COPY]
    for side, site in ((0, S_COPY[0]), (1, S_COPY[1])):
        slots = [u for u in range(side * 20, side * 20 + 20) if S1["slots"][u]["troops"] > 0]
        dr = [r for r in pre if r["site"] == site]
        row = {"live_slots": len(slots), "draws": len(dr), "count_ok": len(dr) == len(slots),
               "ranges_ok": [r["eax"] for r in dr] == [S1["slots"][u]["quality"] * 4 for u in slots]}
        if row["count_ok"]:
            bases = [b for b in range(0, 130) if all(max(60, min(90, r["result"] + b)) == S1["slots"][u]["morale"] for r, u in zip(dr, slots))]
            row["base_candidates"] = bases if len(bases) < 8 else [bases[0], "...", bases[-1]]
            row["morale_rule_ok"] = bool(bases)
        out["attacker" if side == 0 else "defender"] = row
    return out


def post_check(final, recs, dialog):
    """After the battle (TBattleOver_OK): Random(4) per surviving winner unit (site 0x4592BD), then the peace Random(5) (0x45951C) when the peace test is reached."""
    clear = next((r for r in recs if r["kind"] == "flag_clear"), None)
    post = [r for r in recs if clear is not None and r["seq"] > clear["seq"] and r["kind"] == "random"]
    surv = [u for u in range(40) if final.tr[u] > 0]
    winner = {s_ for s_ in (final.side_of(u) for u in surv)}
    prom = [r for r in post if r["site"] == S_POST[0]]
    peace = [r for r in post if r["site"] == S_POST[1]]
    return {"survivors": len(surv), "winner_sides": sorted(winner), "promotion_draws": len(prom), "promotion_draws_equal_survivors": len(prom) == len(surv),
            "promotion_ranges_all_4": all(r["eax"] == 4 for r in prom), "promotions": sum(1 for r in prom if r["result"] == 0), "peace_draws": len(peace),
            "peace_range_5": all(r["eax"] == 5 for r in peace), "peace_results": [r["result"] for r in peace], "dialog_after_battle": dialog,
            "offer_iff_draw_below_2": (bool(dialog) and "peace" in dialog.lower()) == any(r["result"] < 2 for r in peace) if peace else None}


def reconstruct(blocks, recs):
    """Returns (exchange rows, summary). `blocks` = [S_1 ...], `recs` = the hook records of the battle."""
    by_hr = {}
    for r in recs:
        if r["kind"] in ("random", "marker"):
            by_hr.setdefault(r["counter"], []).append(r)
    clear = next((r for r in recs if r["kind"] == "flag_clear"), None)
    if clear is not None:                                          # records after the battle is over are post-battle draws, not part of a half-round
        post = [r for r in recs if r["seq"] > clear["seq"] and r["kind"] == "random"]
        for k in by_hr:
            by_hr[k] = [r for r in by_hr[k] if clear is None or r["seq"] < clear["seq"]]
    else:
        post = []
    rows, miss, diffs, per_hr = [], [], [], []
    n_hr = len(blocks)
    tracked = None
    for k in range(1, n_hr + 1):
        S = blocks[k - 1]
        grp = by_hr.get(k, [])
        ok_idx = S["half_round"] == k
        rp = Replay(grp, tracked.copy() if tracked is not None else State(S), k, None)
        d = []
        if tracked is not None:
            rp.moves()
            d = compare_states(rp.st, S, k)
        else:
            rp.moves()           # half-round 1: placement, no shots expected
        rows += rp.ex
        miss += rp.miss
        diffs += d
        # authoritative state from here
        st = State(S)
        rp2 = Replay(grp[rp.i:], st, k, None)
        mover = S["x2"]
        rp2.melee(mover)
        rows += rp2.ex
        miss += rp2.miss
        per_hr.append({"half_round": k, "header_ok": ok_idx, "mover": mover, "moves_exchanges": sum(1 for x in rp.ex if x["kind"] in ("shot",)),
                       "melee_exchanges": sum(1 for x in rp2.ex if x["kind"] == "melee"), "state_diffs": len(d), "misses": len(rp.miss) + len(rp2.miss)})
        tracked = st
    # the loss rows of the B2 diff (a slot whose troops fell between two consecutive snapshots) and how many the replay explains exactly: a loss row (window ending
    # at snapshot k, slot u) is explained when the replay's troops for u at S_k equal the snapshot (no troops difference listed for (k, u))
    bad = {(d["half_round"], d["slot"]) for d in diffs if d["field"] == "troops"}
    loss_pairs = [(k, u) for k in range(2, n_hr + 1) for u in range(40)
                  if blocks[k - 2]["slots"][u]["troops"] > 0 and blocks[k - 1]["slots"][u]["troops"] < blocks[k - 2]["slots"][u]["troops"]]
    exact = [p for p in loss_pairs if p not in bad]
    return rows, {"half_rounds": n_hr, "per_half_round": per_hr, "misses": miss, "state_diffs": diffs, "post_battle_draws": [(r["site"], r["eax"], r["result"]) for r in post],
                  "final_state": tracked, "copy_in": copy_in_check(blocks[0], recs),
                  "loss_rows": len(loss_pairs), "loss_rows_exact": len(exact), "loss_rows_not_exact": [p for p in loss_pairs if p in bad]}


def summarize(rows, summ):
    shots = [r for r in rows if r["kind"] == "shot"]
    melees = [r for r in rows if r["kind"] == "melee"]
    routs = []
    for r in rows:
        if r["kind"] == "rout_test":
            routs.append(r)
        if r["kind"] == "shot" and "rout" in r:
            routs.append(r["rout"])
        if r["kind"] == "melee":
            routs += r["rout"]
    return {"shots": len(shots), "shots_n_ok": sum(1 for r in shots if r.get("n_ok")), "melee": len(melees), "melee_n_ok": sum(1 for r in melees if r.get("n_ok")),
            "rout_tests": len(routs), "rout_with_draws": sum(1 for r in routs if r.get("pred_draws") == 2),
            "rout_draw_count_ok": sum(1 for r in routs if len(r.get("draws", [])) == r.get("pred_draws")), "rout_removed": sum(1 for r in routs if r.get("removed")),
            "state_diffs": len(summ["state_diffs"]), "misses": len(summ["misses"]), "loss_rows": summ["loss_rows"], "loss_rows_exact": summ["loss_rows_exact"],
            "flank_draws": sum(1 for r in rows if r["kind"] == "flank_draw"), "placement_draws": sum(1 for r in rows if r["kind"] == "placement_draw")}


def main():
    import b11_common as B
    C = B.C
    args = sys.argv[1:]
    outdir = C.DATA
    if "--out" in args:                       # a scratch folder for development runs (the default is the tracked data folder: never overwritten, versioned)
        i = args.index("--out")
        outdir = Path(args[i + 1])
        del args[i:i + 2]
    for tag in args:
        blocks, names = load_series(C.ART, tag)
        recs = load_log(C.DATA / ("hooklog-%s.csv" % tag))
        rows, summ = reconstruct(blocks, recs)
        out = summarize(rows, summ)
        dialog = None
        for t in (json.loads(x) for x in (C.DATA / "trials-b11.jsonl").read_text().splitlines() if x.strip()):
            if t.get("trial") == tag and t.get("status") == "ok":
                dialog = t.get("dialog")
        out.update({"trial": tag, "series": names, "per_half_round": summ["per_half_round"], "miss_list": summ["misses"], "state_diff_list": summ["state_diffs"],
                    "loss_rows_not_exact": summ["loss_rows_not_exact"], "copy_in": summ["copy_in"], "post_battle": post_check(summ["final_state"], recs, dialog)})
        C.write_new(outdir, "exchanges-%s.jsonl" % tag, "\n".join(json.dumps(r) for r in rows) + "\n")
        p = C.write_new(outdir, "exchange-check-%s.json" % tag, json.dumps(out, indent=1))
        print(tag, {k: v for k, v in out.items() if k not in ("series", "per_half_round", "miss_list", "state_diff_list")}, p.name)


if __name__ == "__main__":
    main()
