#!/usr/bin/env python3
"""Check J, offline: the relation changes of one round (staged week-11 save -> kept autosave, Rome's next turn start) and whether each cooldown value is explained by
  (swap)  the AI seat's partner swap, FUN_0044fb7c lines 53423-53444 of the pinned dump: nation x (human flag 0) holds a trade with y (relation 1) and a candidate c with relation 0 has a higher
          tax base than y: the setter is called with 0 for (x,y) (a trade 1 becomes the cooldown -8) and with 1 for (x,c). A pair that goes 0 -> -8 in one round is a trade formed earlier in the
          same seat's turn (FUN_0044fb7c 53395-53404, `setter(x,p,1)`) and dropped by the swap; the test needs  tax_base_after[y] < tax_base_after[c]  for a candidate c whose relation with x
          went 0 -> 1 (or stayed 1 with y dropped).
  (rebirth) a -8 or a thawed value from FUN_0044c360's loop (setter(x, owner of a moved city, -8)); recognised by the news line 'City defects from <owner> to <x>'
  (thaw)  a value between -7 and -1 that was negative before (FUN_00451b40 54905-54925 raises negatives by 1, and by up to 3 with probability 1/3, once per matrix entry in each direction)
Everything else is listed as unexplained. Output analysis_J.txt (next free version)."""
import json, struct, sys
from pathlib import Path
D = Path(__file__).resolve().parent; R = D.parents[3]; sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "runs/experiments/battles")); sys.path.insert(0, str(D))
from state import sav
import stage
from versioned import write_new
ART = R / "artifacts/run-exp-g4-followups"


def rel_tax(b):
    rel, tb, un, hu = [], [], [], []
    for n in range(16):
        o = stage._nation(bytearray(b), n); nb = b[o:o + sav.NATION_LEN]
        rel.append([struct.unpack_from("<h", nb, 0x26 + 2 * k)[0] for k in range(16)]); tb.append(struct.unpack_from("<h", nb, 0x44c)[0]); un.append(struct.unpack_from("<h", nb, 0x440)[0]); hu.append(nb[0x490])
    return rel, tb, un, hu


def main(files):
    L = ["# analysis_J: relation changes per round and the swap-rule explanation (see the docstring)"]; tot = {"swap": 0, "rebirth": 0, "thaw": 0, "formed": 0, "unexplained": 0}
    for f in files:
        opened = {}
        for line in open(f):
            d = json.loads(line)
            if d.get("step") == "round_open": opened[d["tag"]] = d["save"]
            if d.get("step") != "round_done" or not d.get("kept"): continue
            tag = d["tag"]; a, tb0, un0, hu0 = rel_tax((ART / opened[tag]).read_bytes()); b, tb, un, hu = rel_tax((ART / d["kept"]).read_bytes())
            news = d["autosave_news"]; defects = [t for t in news if " defects from " in t]
            L.append(f"-- {f.name} {tag}: staged {opened[tag]} kept {d['kept']}; unity before/after Greece {un0[7]} -> {un[7]}; defect lines {len(defects)}")
            for x in range(16):
                for y in range(x + 1, 16):
                    if a[x][y] == b[x][y]: continue
                    why = None
                    if a[x][y] == 0 and b[x][y] == 1: why = "formed: a new trade (FUN_0044fb7c 53395-53404 / 53408-53420: setter(x, y, 1))"
                    elif b[x][y] < 0 and a[x][y] >= 0:                       # a new cooldown
                        for who, other in ((x, y), (y, x)):
                            if hu[who]: continue
                            cands = [c for c in range(16) if c not in (who, other) and b[who][c] == 1 and a[who][c] != 1 and tb[other] < tb[c]]
                            if b[x][y] == -8 and cands and a[x][y] in (0, 1): why = f"swap: {sav.NATIONS[who]} dropped {sav.NATIONS[other]} (tax base {tb[other]}) for {[ (sav.NATIONS[c], tb[c]) for c in cands]}"; break
                            if -8 < b[x][y] < 0 and cands and who >= 12 and a[x][y] in (0, 1): why = f"swap by a seat that plays BEFORE the tick (seat {who}), then thawed by the tick: {sav.NATIONS[who]} dropped {sav.NATIONS[other]} (tax base {tb[other]}) for {[ (sav.NATIONS[c], tb[c]) for c in cands]}"; break
                        if why is None and any(sav.NATIONS[x] in t.split(" to ")[-1] or sav.NATIONS[y] in t.split(" to ")[-1] for t in defects): why = "rebirth/transfer cooldown (defect lines present)"
                    elif b[x][y] < 0 and a[x][y] < 0 and b[x][y] > a[x][y]: why = "thaw"
                    kind = (why or "unexplained").split(":")[0].split(" ")[0]
                    tot[{"swap": "swap", "rebirth/transfer": "rebirth", "thaw": "thaw", "formed": "formed"}.get(kind, "unexplained")] += 1
                    L.append(f"   {sav.NATIONS[x]:10s} - {sav.NATIONS[y]:10s} {a[x][y]:>4} -> {b[x][y]:>4}  {why or 'UNEXPLAINED'}")
    L.append(f"totals: {tot}")
    return L


if __name__ == "__main__":
    print(write_new(D / "analysis_J.txt", "\n".join(main(sorted(D.glob("g4_checks-J-*.jsonl")))) + "\n"))
