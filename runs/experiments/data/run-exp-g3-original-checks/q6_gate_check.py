#!/usr/bin/env python3
"""R3: evaluate the two trade-offer gates of FUN_00452034 (extract lines 55002-55015) on the Q6 staged state, from the start save
(saves/run0-start-AUTO0720-seed12345.SAV; the Q6 staging only sets Rome's own relations to 0, nothing about other nations' rows or tax bases).
Rome's trade partners in the staging: none (< 3), so the first gate (55002: sVar7 = 0 < candidate tax base) passes for every alive candidate with tax base > 0.
Second gate (55006-55015): the candidate needs a CURRENT trade partner (its relation row == 1) whose tax base is below Rome's.
Writes the table to the next free q6_gate_check[.vN].txt."""
import sys
from pathlib import Path
D = Path(__file__).resolve().parent; R = D.parents[3]
sys.path.insert(0, str(R)); sys.path.insert(0, str(D))
from state import sav
from versioned import write_new
s = sav.parse((R / "saves/run0-start-AUTO0720-seed12345.SAV").read_bytes())
N = s["nations"]; tb = {n["name"]: n["tax_base"] for n in N}
out = [f"Rome tax base {tb['Rome']}; Rome trade partners in the Q6 staging: none (all 15 relations 0); neighbour mask: {N[0]['neighbours']}"]
ok = 0
for n in N[1:]:
    pr = [k for k, v in n["relations"].items() if v == 1 and k != "Rome"]
    below = [k for k in pr if tb[k] < tb["Rome"]]
    g1 = n["alive"] and n["tax_base"] > 0
    out.append(f"{n['name']}\ttax_base {n['tax_base']}\tgate1 {'pass' if g1 else 'FAIL'}\ttrade partners {pr}\tbelow Rome {below}\tgate2 {'pass' if below else 'FAIL'}")
    if n["name"] not in N[0]["neighbours"] and g1 and below: ok += 1
nn = len([n for n in N[1:] if n["name"] not in N[0]["neighbours"]])
out.append(f"non-neighbour candidates passing both gates: {ok} of {nn}; conditional expectation of trade offers in 120 turn starts, ONLY if these {ok} start-save-eligible non-neighbours stay the eligible set at every roll (not verified: AI seats change trade relations before the rolls): 120 x {ok}/16 x 1/3 = {120 * ok / 16 / 3:.1f}; gate-independent upper bound (without the second gate): 120 x {nn}/16 x 1/3 = {120 * nn / 16 / 3:.1f}")
print(write_new(D / "q6_gate_check.txt", "\n".join(out) + "\n")); print(out[-1])
