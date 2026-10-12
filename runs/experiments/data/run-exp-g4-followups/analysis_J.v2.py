#!/usr/bin/env python3
"""Check J, v2 (reviewer R4 + R5 round-2): relation changes of one round and the swap-rule explanation.

R4: a nation is "before the tick" iff its SEAT (index in the staged save's `turn_order`) is >= 12, not iff the nation ID is >= 12. Rome is nation 0 but seat 11 in the start save. Seats 12-15 play BEFORE the tick and their trade-partner swap runs in their own seat; the AFTER-state row is what the quarterly tick reads. Seats 0-10 play AFTER the tick and their relations are unchanged at the tick.

R5: the analysis walks every ordered pair (x, y), not just x < y. The old walk skipped pairs where only the (y, x) direction changed; rebirth leaves the matrix asymmetric (Greece's own row reset to 0, the partners' rows keep 1) and exactly that asymmetry is the case the reviewer cites. The new walk also reports the asymmetric pairs explicitly.

(swap)  the AI seat's partner swap, FUN_0044fb7c lines 53423-53444: nation x (human flag 0) holds a trade with y (relation 1) and a candidate c with relation 0 has a higher
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


def rel_tax(b, turn_order=None):
    """per nation: relation matrix, tax base, unity, human flag, plus the seat (R4: index in the staged save's turn_order)."""
    rel, tb, un, hu, seat = [], [], [], [], []
    for n in range(16):
        o = stage._nation(bytearray(b), n); nb = b[o:o + sav.NATION_LEN]
        rel.append([struct.unpack_from("<h", nb, 0x26 + 2 * k)[0] for k in range(16)])
        tb.append(struct.unpack_from("<h", nb, 0x44c)[0])
        un.append(struct.unpack_from("<h", nb, 0x440)[0])
        hu.append(nb[0x490])
        seat.append(turn_order.index(n) if (turn_order and n in turn_order) else -1)
    return rel, tb, un, hu, seat


def selftest():
    """R4: seat lookup. The start save's turn_order puts Rome (nation 0) at seat 11 and Carthage (nation 1) at seat 13 — a >= 12 check
    on nation ID would have flagged Rome as before the tick (wrong) and missed Carthage (also wrong)."""
    to = [9, 5, 3, 12, 2, 15, 7, 10, 4, 14, 13, 0, 11, 1, 6, 8]
    cases = []
    for n, expected_seat in [(0, 11), (1, 13), (7, 6), (15, 5)]:
        got = to.index(n)
        cases.append(f"{sav.NATIONS[n]} nation {n} seat {got} (expected {expected_seat}) [{'OK' if got == expected_seat else 'FAIL'}]")
    return ["selftest seat_from_turn_order: " + " | ".join(cases)]


def main(files):
    L = ["# analysis_J v2 (R4+R5): relation changes per round, seat from turn_order, all ordered pairs (see the docstring)"]; L += selftest(); tot = {"swap": 0, "rebirth": 0, "thaw": 0, "formed": 0, "unexplained": 0}; asym = 0
    for f in files:
        opened = {}
        for line in open(f):
            d = json.loads(line)
            if d.get("step") == "round_open":
                # R4: parse the staged save's turn_order so we can derive each nation's seat for the "before the tick" check
                opened[d["tag"]] = (d["save"], sav.parse((ART / d["save"]).read_bytes()).get("turn_order"))
            if d.get("step") != "round_done" or not d.get("kept"): continue
            tag = d["tag"]; staged_name, turn_order = opened[tag]
            a, tb0, un0, hu0, seat0 = rel_tax((ART / staged_name).read_bytes(), turn_order=turn_order)
            b, tb, un, hu, seat = rel_tax((ART / d["kept"]).read_bytes(), turn_order=turn_order)
            news = d["autosave_news"]; defects = [t for t in news if " defects from " in t]
            L.append(f"-- {f.name} {tag}: staged {staged_name} kept {d['kept']}; turn_order {turn_order}; unity before/after Greece {un0[7]} -> {un[7]}; defect lines {len(defects)}")
            for x in range(16):
                for y in range(16):                                                    # R5: walk every ordered pair (x, y), not just x < y
                    if x == y: continue
                    if a[x][y] == b[x][y] and a[y][x] == b[y][x]: continue            # both directions unchanged: skip
                    # R5: report asymmetric pairs explicitly. The matrix is asymmetric when a[x][y] != a[y][x] or b[x][y] != b[y][x].
                    if a[x][y] != a[y][x] or b[x][y] != b[y][x]:
                        asym += 1
                    why = None
                    if a[x][y] == 0 and b[x][y] == 1: why = "formed: a new trade (FUN_0044fb7c 53395-53404 / 53408-53420: setter(x, y, 1))"
                    elif b[x][y] < 0 and a[x][y] >= 0:                       # a new cooldown
                        # R4: the "before the tick" check uses the SEAT of the acting nation (x, the seat that owns the swap), not its nation ID.
                        # In the start save Rome is nation 0 but seat 11; the old `who >= 12` flagged Rome as before the tick (wrong).
                        for who, other in ((x, y), (y, x)):
                            if hu[who]: continue
                            cands = [c for c in range(16) if c not in (who, other) and b[who][c] == 1 and a[who][c] != 1 and tb[other] < tb[c]]
                            if b[x][y] == -8 and cands and a[x][y] in (0, 1): why = f"swap: {sav.NATIONS[who]} (seat {seat[who]}) dropped {sav.NATIONS[other]} (tax base {tb[other]}) for {[ (sav.NATIONS[c], tb[c]) for c in cands]}"; break
                            if -8 < b[x][y] < 0 and cands and seat[who] >= 12 and a[x][y] in (0, 1): why = f"swap by a seat that plays BEFORE the tick (seat {seat[who]}): {sav.NATIONS[who]} dropped {sav.NATIONS[other]} (tax base {tb[other]}) for {[ (sav.NATIONS[c], tb[c]) for c in cands]}"; break
                        if why is None and any(sav.NATIONS[x] in t.split(" to ")[-1] or sav.NATIONS[y] in t.split(" to ")[-1] for t in defects): why = "rebirth/transfer cooldown (defect lines present)"
                    elif b[x][y] < 0 and a[x][y] < 0 and b[x][y] > a[x][y]: why = "thaw"
                    kind = (why or "unexplained").split(":")[0].split(" ")[0]
                    tot[{"swap": "swap", "rebirth/transfer": "rebirth", "thaw": "thaw", "formed": "formed"}.get(kind, "unexplained")] += 1
                    # R5: when both directions of the same unordered pair changed, also list the (y, x) row together
                    pair_note = f"   {sav.NATIONS[x]:10s} - {sav.NATIONS[y]:10s} {a[x][y]:>4} -> {b[x][y]:>4}  {why or 'UNEXPLAINED'}"
                    if a[y][x] != a[x][y] or b[y][x] != b[x][y]:
                        pair_note += f"   | reverse {sav.NATIONS[y]:10s} - {sav.NATIONS[x]:10s} {a[y][x]:>4} -> {b[y][x]:>4}  (asymmetric)"
                    L.append(pair_note)
    L.append(f"totals: {tot}")
    L.append(f"asymmetric pairs reported: {asym} (R5: the old walk x<y skipped these; the new walk makes them visible)")
    return L


if __name__ == "__main__":
    print(write_new(D / "analysis_J.txt", "\n".join(main(sorted(D.glob("g4_checks-J-*.jsonl")))) + "\n"))
