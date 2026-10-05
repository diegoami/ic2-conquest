#!/usr/bin/env python3
"""B11 offline test of the exchange replay (`runs/experiments/battles/b11_exchange.py`) on hand-computed cases: one melee, one shot, one rout with draws.
No game and no emulator. The numbers in the comments are worked out by hand from the report's formulas (§4 shot, §5 melee, §6 rout).

    python3 -m tests.test_battle_exchange          # also runnable with pytest
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("IC2_WORK", str(Path.home() / "ic2-work"))
os.environ.setdefault("DISPLAY_IC2", ":577")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs" / "experiments" / "battles"))
import b11_exchange as X  # noqa: E402
from state import battle_block as BB  # noqa: E402


def rec(seq, kind, site, eax=0, edx=0, result=0, counter=3):
    return {"seq": seq, "kind": kind, "site": site, "eax": eax, "edx": edx, "ecx": 0, "seed_before": 0, "seed_after": 0, "result": result, "counter": counter,
            "side": 0, "flag": 1, "ebp": 0}


def block(att, dfn):
    b = BB.synthetic_block([(t, n, q, 0, "a%d" % i) for i, (t, n, q) in enumerate(att)], [(t, n, q, 0, "d%d" % i) for i, (t, n, q) in enumerate(dfn)])
    for s in b["slots"]:
        s["morale"] = 70 if s["alive"] else 0
    return b


def test_one_melee_by_hand():
    # attacker HI 6000 q6 m70 (slot 0) hits defender HI 6000 q6 m70 (slot 20), f = 1:
    # A = D = 5*6000*(6*10+70)//2000 + 12 = 1950 + 12 = 1962; nA = (6000*1962//1962)//12 + 1 = 501; nD = (6000*1962//1962)//10 + 1 = 601
    # draws 100, 50 (attacker) and 200, 150 (defender): la = min(30000, 150*(5-1)//5 = 120) -> min(120, 2400) + 1 = 121; ld = 350*(2+5)//5 = 490 -> 491
    # morale: 6000//491 = 12 < 6000//121 = 49: attacker +2, defender -3. Troops 5879 and 5509; both stay (morale > 39 and troops >= floor): no rout draws.
    b = block([("hi", 6000, 6)], [("hi", 6000, 6)])
    b["slots"][0]["target"] = 20
    st = X.State(b)
    recs = [rec(0, "marker", X.MARK_MELEE),
            rec(1, "random", 0x439557, eax=501, result=100), rec(2, "random", 0x43955F, eax=501, result=50),
            rec(3, "random", 0x4395CE, eax=601, result=200), rec(4, "random", 0x4395D8, eax=601, result=150),
            rec(5, "marker", X.MARK_ROUT, eax=0), rec(6, "marker", X.MARK_ROUT, eax=20)]
    rp = X.Replay(recs, st, 3, None)
    rp.melee(0)
    assert not rp.miss, rp.miss
    (row,) = rp.ex
    assert (row["A"], row["D"], row["nA_pred"], row["nD_pred"], row["f"]) == (1962, 1962, 501, 601, 1)
    assert (row["loss_actor"], row["loss_target"], row["n_ok"], row["morale_winner"]) == (121, 491, True, "actor")
    assert (st.tr[0], st.tr[20], st.m[0], st.m[20]) == (5879, 5509, 72, 67)


def test_one_shot_by_hand():
    # archers slot 0: 3500 troops q6 m70 shoot at HI slot 20 (6000): base = 3500*6*70*2 // (3500*5 + 150000) = 2940000 // 167500 = 17;
    # cap = min(3500//3 = 1166, 6000//2 = 3000) = 1166; n = 18 (not doubled); an adjacent archer would draw with n = min(34, 1166) + 1 = 35.
    # draws 7 and 9: loss 16; morale -min(3, 16*35 // 6001 = 0) = 0; troops 5984; Rout(20) draws nothing (morale 70 > 39, troops >= floor)
    b = block([("ar", 3500, 6)], [("hi", 6000, 6)])
    st = X.State(b)
    recs = [rec(0, "marker", X.MARK_SHOT, eax=0, edx=20),
            rec(1, "random", 0x439188, eax=18, result=7), rec(2, "random", 0x439191, eax=18, result=9),
            rec(3, "marker", X.MARK_ROUT, eax=20)]
    rp = X.Replay(recs, st, 4, None)
    rp.moves()
    assert not rp.miss, rp.miss
    (row,) = rp.ex
    assert (row["n_pred"], row["n_pred_doubled"], row["n_ok"], row["loss"], row["morale_delta_target"]) == (18, 35, True, 16, 0)
    assert st.tr[20] == 5984 and st.shots[0] == 24
    # the same shot at point-blank range is recognised by n = 35 (archers only)
    b2 = block([("ar", 3500, 6)], [("hi", 6000, 6)])
    st2 = X.State(b2)
    rp2 = X.Replay([rec(0, "marker", X.MARK_SHOT, eax=0, edx=20), rec(1, "random", 0x439188, eax=35, result=7), rec(2, "random", 0x439191, eax=35, result=9),
                    rec(3, "marker", X.MARK_ROUT, eax=20)], st2, 4, None)
    rp2.moves()
    assert rp2.ex[0]["n_ok"] and rp2.ex[0]["doubled"] and not rp2.miss
    # a wrong observed n is reported, not accepted
    st3 = X.State(block([("ar", 3500, 6)], [("hi", 6000, 6)]))
    rp3 = X.Replay([rec(0, "marker", X.MARK_SHOT, eax=0, edx=20), rec(1, "random", 0x439188, eax=19, result=7), rec(2, "random", 0x439191, eax=19, result=9),
                    rec(3, "marker", X.MARK_ROUT, eax=20)], st3, 4, None)
    rp3.moves()
    assert rp3.miss and not rp3.ex[0]["n_ok"]


def test_rout_with_draws_and_cascade():
    # a unit with morale 30 (20 < m <= 39) and troops above the floor draws Random(30) twice: 10 + 12 = 22 <= 29: it is removed.
    # Its friend (morale 70) gets -6; the enemy gets +5 (and its target is cleared).
    b = block([("hi", 6000, 6), ("hi", 6000, 6)], [("hi", 6000, 6)])
    b["slots"][0]["morale"] = 30
    b["slots"][20]["target"] = 0
    st = X.State(b)
    rp = X.Replay([rec(0, "marker", X.MARK_ROUT, eax=0), rec(1, "random", 0x438FFB, eax=30, result=10), rec(2, "random", 0x439006, eax=30, result=12)], st, 3, None)
    rp.take()
    row = rp.rout(0, "test")
    assert not rp.miss, rp.miss
    assert row["pred_draws"] == 2 and row["removed"] is True
    assert st.tr[0] == 0 and st.m[1] == 64 and st.m[20] == 75 and st.tg[20] == -1
    # sum above 29: stays
    st = X.State(b)
    rp = X.Replay([rec(0, "marker", X.MARK_ROUT, eax=0), rec(1, "random", 0x438FFB, eax=30, result=20), rec(2, "random", 0x439006, eax=30, result=15)], st, 3, None)
    rp.take()
    row = rp.rout(0, "test")
    assert row["removed"] is False and st.tr[0] == 6000
    # a unit below the floor (HI floor = 240) is removed with no draw
    st = X.State(b)
    st.tr[0] = 100
    rp = X.Replay([rec(0, "marker", X.MARK_ROUT, eax=0)], st, 3, None)
    rp.take()
    row = rp.rout(0, "test")
    assert row["pred_draws"] == 0 and row["removed"] is True


def main():
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("ok   ", name)
            except Exception as e:      # noqa: BLE001
                fails += 1
                print("FAIL ", name, type(e).__name__, e)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
