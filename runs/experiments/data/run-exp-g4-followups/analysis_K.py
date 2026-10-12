#!/usr/bin/env python3
"""Check K, offline: for every round of g4_checks-K-<stamp>.jsonl (kept autosave = the state at the offer roll of FUN_00452034, lines 54975-55030 of the pinned dump),
recompute which proposer p could give which offer and compare with the observed pending offer (+16/+17 words of the autosave tail).
Rule (human seat = Rome, nation 0): p = Random(16); needs relation(Rome,p) == 0 and unity[p] > 0; then Random(3) == 0 and p without the human flag; then
  trade: n = Rome's trade partners; threshold = 0 when n < 3, else the lowest tax base among Rome's partners; needs threshold < tax_base[p] and some k with relation(p,k) == 1 and tax_base[k] < tax_base[Rome];
  alliance (overrides trade): p in Rome's neighbour mask and Rome has no war relation.
Expected offers per round = (eligible proposers) / 48 (16 x 3). Output analysis_K.txt (next free version). Reads the kept autosaves under artifacts/run-exp-g4-followups/."""
import json, random, sys
from pathlib import Path
D = Path(__file__).resolve().parent; R = D.parents[3]; sys.path.insert(0, str(R)); sys.path.insert(0, str(D))
from state import sav
from versioned import write_new
ART = R / "artifacts/run-exp-g4-followups"


def eligible(s):
    N = s["nations"]; rome = N[0]; rel = lambda a, b: N[a]["relations"].get(sav.NATIONS[b], 0)
    partners = [k for k in range(16) if k != 0 and rel(0, k) == 1]
    thr = 0 if len(partners) < 3 else min(N[k]["tax_base"] for k in partners)
    war = any(rel(0, k) == 3 for k in range(1, 16)); out = {}
    for p in range(1, 16):
        if rel(0, p) != 0 or N[p]["unity"] <= 0 or N[p]["human"]: continue
        kind = None
        if thr < N[p]["tax_base"] and any(rel(p, k) == 1 and N[k]["tax_base"] < rome["tax_base"] for k in range(16) if k != p): kind = 1
        if sav.NATIONS[p] in rome["neighbours"] and not war: kind = 2
        if kind: out[p] = kind
    return out


def run(files):
    L = ["# analysis_K: offer eligibility per roll (see the docstring of analysis_K.py)"]; rounds = []
    for f in files:
        for line in open(f):
            d = json.loads(line)
            if d.get("step") == "light_round" and d.get("kept") and (ART / d["kept"]).exists():
                s = sav.parse((ART / d["kept"]).read_bytes()); rounds.append((f.name, d["tag"], d["kept"], s, s["pending_offer"]))
    L.append(f"files: {[Path(f).name for f in files]}; rounds read: {len(rounds)}")
    viol, exp_sum, obs = 0, 0.0, {1: 0, 2: 0}; table = []
    for fn, tag, kept, s, off in rounds:
        el = eligible(s); exp_sum += len(el) / 48
        frm, typ = off["from"], off["type"]
        has = 0 <= frm < 16
        ok = (not has) or (el.get(frm) == typ)
        if has: obs[typ] = obs.get(typ, 0) + 1
        if not ok: viol += 1
        table.append((tag, kept, "offer from %s type %s" % (sav.NATIONS[frm] if has else None, typ if has else None), "eligible " + str({sav.NATIONS[p]: t for p, t in el.items()}), "OK" if ok else "VIOLATION"))
    for t in table: L.append("  " + " | ".join(map(str, t)))
    n_off = sum(1 for r in rounds if 0 <= r[4]["from"] < 16)
    L.append(f"observed offers: {n_off} of {len(rounds)} rounds (trade {obs.get(1, 0)}, alliance {obs.get(2, 0)}); violations (observed proposer/type not in the eligible set at that roll): {viol}")
    L.append(f"expected offers if the rule is exactly this: {exp_sum:.1f} of {len(rounds)} rounds (sum over rounds of eligible/48; the eligible set is read from each autosave)")
    # self-test: the check must be able to fail. Shuffle the observed proposers among the rounds (positive control of the detector).
    rnd = random.Random(1); bad = 0; tot = 0
    ob = [(r[4]["from"], r[4]["type"]) for r in rounds if 0 <= r[4]["from"] < 16]
    for _ in range(200):
        rnd.shuffle(ob); k = 0
        for r in rounds:
            if 0 <= r[4]["from"] < 16:
                frm, typ = ob[k]; k += 1; tot += 1
                if eligible(r[3]).get(frm) != typ: bad += 1
    L.append(f"detector self-test: with the proposers shuffled among rounds, {bad} of {tot} shuffled offer checks fail (a check that never failed would show 0)")
    return L


if __name__ == "__main__":
    files = sorted(D.glob("g4_checks-K-*.jsonl"))
    print(write_new(D / "analysis_K.txt", "\n".join(run(files)) + "\n"))
