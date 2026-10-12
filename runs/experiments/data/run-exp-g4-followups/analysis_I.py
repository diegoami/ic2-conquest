#!/usr/bin/env python3
"""Check I, offline: the quarterly treasury of every nation recomputed from the decompile (FUN_00451b40, lines 54741-54889 of the pinned dump) and compared with the observed change.
Before = the staged week-11 save (its path in the `quarter_round` log line), after = the kept autosave (Rome's next turn start). Prediction for a nation with unity > 0:
  T' = T - 3 x ships of its finished fleets (countdown -1) - sum over its armies' regular units (troops div 200) x price(type) - sum over its recruit queue (troops div 200) x price(type)
  T'' = tax_base x tax div 100 + T' + tax_base div 4 - 7 x cities - wealth div 20000 + trade, trade = sum over k with relation 1 or 2 of tax_base[k] div 12 (FUN_004499ec)
with tax_base, wealth, cities, tax and the units, queues and fleets read from the AFTER state, and the relation row of the trade line from the BEFORE state for seats 0-10 (they play after the tick) and the AFTER state for seats 12-15 (the city loop rebuilds tax base and wealth before the nation loop; the AI seats that play
between the tick and Rome's next turn can change units, queue and treasury: such nations are flagged `moved` when their queue, armies or fleets differ between before and after).
Unity: min(990, max(300, unity + 25 - tax div 2 - mobilisation' div 5)), mobilisation' = max(0, mobilisation - 3) (mobilisation read before; after the tick a seat can change it).
Also the deposed set from the news. Output analysis_I.txt (next free version)."""
import json, struct, sys
from pathlib import Path
D = Path(__file__).resolve().parent; R = D.parents[3]; sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "runs/experiments/battles")); sys.path.insert(0, str(D))
from state import sav
import stage
from versioned import write_new
ART = R / "artifacts/run-exp-g4-followups"
tdiv = lambda a, b: int(a / b)


def raw(b):
    """per nation: dict of the words the formulas need, plus queue, armies (regular units), finished-fleet ships"""
    na = struct.unpack_from("<h", b, sav.ARMY_OFF)[0]
    armies = [b[sav.ARMY_OFF + 2 + i * sav.ARMY_LEN: sav.ARMY_OFF + 2 + (i + 1) * sav.ARMY_LEN] for i in range(na)]
    nf = struct.unpack_from("<h", b, sav.ARMY_OFF + 2 + na * sav.ARMY_LEN)[0]
    f0 = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN + 2
    fleets = [struct.unpack_from("<13h", b, f0 + i * sav.FLEET_LEN) for i in range(nf)]
    out = []
    for n in range(16):
        o = stage._nation(bytearray(b), n); nb = b[o:o + sav.NATION_LEN]
        i16 = lambda k: struct.unpack_from("<h", nb, k)[0]; i32 = lambda k: struct.unpack_from("<i", nb, k)[0]
        out.append({"n": n, "treasury": i32(0x438), "wealth": i32(0x430), "tax": i16(0x44a), "tax_base": i16(0x44c), "cities": i16(0x446), "unity": i16(0x440), "mob": i16(0x442),
                    "rel": [i16(0x26 + 2 * k) for k in range(16)], "human": nb[0x490],
                    "queue": [struct.unpack_from("<4h", nb, 0x2e4 + 8 * k) for k in range(40) if i16(0x2e8 + 8 * k) > 0],
                    "units": [(struct.unpack_from("<h", a, 4)[0] == n, tuple(struct.unpack_from("<4h", a, 16 + 32 * k))) for a in armies if struct.unpack_from("<h", a, 4)[0] == n for k in range(20) if struct.unpack_from("<h", a, 16 + 32 * k + 4)[0] > 0],
                    "purse": sum(struct.unpack_from("<h", a, 12)[0] for a in armies if struct.unpack_from("<h", a, 4)[0] == n),
                    "ships": sum(f[9] for f in fleets if f[4] == n and f[5] == -1),
                    "building": [(i, f[9]) for i, f in enumerate(fleets) if f[4] == n and f[5] >= 0]})
    return out, fleets


def predict(a, b, price):
    n = b["n"]; up = 3 * b["ships"]
    up += sum(tdiv(tr, 200) * price[t] for _, (lab, t, tr, q) in b["units"] if lab == 0)
    up += sum(tdiv(sl[2], 200) * price[sl[1]] for sl in b["queue"])
    relrow = a["rel"] if n < 11 else b["rel"]       # seats 0-10 play after the tick (their relation changes come later): the BEFORE row is the row at the tick; seats 12-15 played before it: the AFTER row (Rome, seat 11, never changes its own)
    trade = sum(tdiv(a_["tax_base"], 12) for k, a_ in enumerate(b["_all"]) if relrow[k] in (1, 2))
    t2 = tdiv(b["tax_base"] * b["tax"], 100) + (a["treasury"] - up) + tdiv(b["tax_base"], 4) - 7 * b["cities"] - tdiv(b["wealth"], 20000) + trade
    mob = max(0, a["mob"] - 3); un = min(990, max(300, a["unity"] + 25 - tdiv(b["tax"], 2) - tdiv(mob, 5)))
    return t2, un, up, trade


def main(logs):
    L = ["# analysis_I: AI and human quarter income, recomputed from the code (see the docstring)"]; rows = []
    for f in logs:
        price = None
        for line in open(f):
            d = json.loads(line)
            if d.get("step") == "unit_prices": price = [p[1] for p in d["prices"]]; price_init = [p[0] for p in d["prices"]]; L.append(f"{f.name}: unit prices (regular, 0x478fd4 + 40 t) = {price}")
            if d.get("step") == "quarter_round":
                a, fa = raw((ART / d["staged"]).read_bytes()); b, fb = raw((ART / d["kept"]).read_bytes())
                for x in b: x["_all"] = b
                deposed = [t for t in d["autosave_news"] if "depose their leader" in t]
                L.append(f"-- {f.name} opening {d['opening']} kept {d['kept']} news: {[t for t in d['autosave_news'][-14:] if t.strip()]}")
                for n in range(16):
                    if a[n]["unity"] <= 0: continue
                    t2, un, up, trade = predict(a[n], b[n], price)
                    qk = lambda q: sorted((sl[1], sl[2], sl[3]) for sl in q)          # the queue state counts up every week: compare type, troops, city only
                    newq = [x for x in qk(b[n]["queue"]) if x not in qk(a[n]["queue"])]; goneq = [x for x in qk(a[n]["queue"]) if x not in qk(b[n]["queue"])]
                    newb = [bb for bb in b[n]["building"] if bb[0] >= len(fa) or bb not in a[n]["building"]]
                    uk = lambda u: sorted((lab, t, tr) for _, (lab, t, tr, q) in u)
                    moved = bool(newq or goneq or newb) or uk(a[n]["units"]) != uk(b[n]["units"]) or a[n]["ships"] != b[n]["ships"]
                    mpay = sum(tdiv(tdiv(tr, 200) * price[t] * q, 5) for _, (lab, t, tr, q) in b[n]["units"] if lab != 0)          # mercenary pay taken from the army purse by the tick
                    purse_in = (b[n]["purse"] - a[n]["purse"]) + mpay                                                          # money the AI moved from the treasury into army purses (seat actions)
                    spend = sum(tdiv(tr, 200) * price_init[t] for t, tr, c in newq) + sum(10 * sh for _, sh in newb) + max(0, purse_in)
                    dep = any(sav.NATIONS[n] + " depose" in t for t in deposed)
                    rows.append((f.name, d["opening"], sav.NATIONS[n], a[n]["treasury"], b[n]["treasury"], t2, b[n]["treasury"] - t2, un, b[n]["unity"], moved, dep, up, trade, spend, newq, goneq, newb))
                    L.append(f"   {sav.NATIONS[n]:11s} treasury {a[n]['treasury']:>8} -> {b[n]['treasury']:>8}  predicted {t2:>8}  diff {b[n]['treasury'] - t2:>6}  | unity {a[n]['unity']} -> {b[n]['unity']} predicted {un} | upkeep {up} trade {trade} | AI actions seen (new queue {newq}, gone {goneq}, new fleets {newb}, purse money in {purse_in}, units/ships changed {uk(a[n]['units']) != uk(b[n]['units']) or a[n]['ships'] != b[n]['ships']}) estimated spending {spend} -> diff + spending = {b[n]['treasury'] - t2 + spend} | deposed: {dep}")
    ex = [r for r in rows if r[6] == 0]; unmoved = [r for r in rows if not r[9] and not r[10]]; expl = [r for r in rows if r[6] + r[13] == 0]
    L.append(f"nation-quarters: {len(rows)}; exact treasury match: {len(ex)}; of the {len(unmoved)} without a changed queue/units/fleet and no deposition: exact {sum(1 for r in unmoved if r[6] == 0)}; exact after adding the estimated AI spending (new queue slots at the initial price, new fleets 10 per ship, money moved into army purses = purse change + the tick's mercenary pay): {len(expl)}")
    L.append(f"unity: exact {sum(1 for r in rows if r[7] == r[8])} of {len(rows)} (the after-tick seats can move mobilisation)")
    ai = [r for r in rows if r[2] != "Rome"]; L.append(f"AI only: {len(ai)}; exact treasury {sum(1 for r in ai if r[6] == 0)}; exact among unmoved {sum(1 for r in ai if r[6] == 0 and not r[9] and not r[10])} of {sum(1 for r in ai if not r[9] and not r[10])}; exact after spending {sum(1 for r in ai if r[6] + r[13] == 0)}")
    rest = [(r[2], r[1], r[6] + r[13]) for r in ai if r[6] + r[13] != 0]; L.append(f"AI nation-quarters still not exact after the spending estimate (nation, opening, remaining difference): {rest}")
    return L


if __name__ == "__main__":
    logs = sorted(D.glob("g4_checks-I-*.jsonl"))
    print(write_new(D / "analysis_I.txt", "\n".join(main(logs)) + "\n"))
