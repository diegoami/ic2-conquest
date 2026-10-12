#!/usr/bin/env python3
"""Line-numbered extract of every decompiled function that findings/2026-10-12-g3-original-checks.md cites, from the pinned all_app_functions.txt
(SHA-256 checked by harness.decompile.check(); first column = that file's line number). Writes code_extract_g3.txt beside this script (next free version)."""
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import decompile
from versioned import write_new
decompile.check()
dump = Path(decompile.DUMP); sha = decompile.PINS[dump.name]
L = dump.read_text(errors="replace").split("\n")
heads = [(i, L[i].split()[2]) for i in range(len(L)) if L[i].startswith("// ==== ")]
rng = {}
for k, (i, name) in enumerate(heads):
    end = (heads[k + 1][0] - 1) if k + 1 < len(heads) else len(L) - 1
    while end > i and not L[end].strip(): end -= 1
    rng[name] = (i, end)
WHY = [
    ("FUN_00451b40", "Q1/Q2: the quarterly tick: ship, army (mercenary pay or desertion) and city-unit upkeep; city loop (population growth, loyalty draws, rebellion call at loyalty < 30); nation loop (income, unity, mobilisation, AI deposition 1 in 9)"),
    ("FUN_004514ec", "Q1e/Q5/Q2: the weekly block: city stock and winter famine loyalty (Random(3), season 3), army supply and morale, fleet storm pass (x3 when the covered cell is 1), weather call, quarter call, news header"),
    ("FUN_0044c204", "Q1a/b/c: rebellion of one city: (a) rebirth when the allegiance nation is dead, (b) back to the allegiance nation, (c) last war army within 10 tiles, (d) best neighbour"),
    ("FUN_0044c360", "Q1c: rebirth of a dead nation: count of allegiance cities under loyalty 40 must exceed 7, resets, capital choice"),
    ("FUN_0044bed8", "Q1a/b/c: transfer of one city (unity, wealth, treasury, slots, loyalty formula, news line 'defects from')"),
    ("FUN_0044c8f0", "Q1f: deposition of a leader: news line, new name, unity, treasury, cooldowns"),
    ("FUN_0044b8d0", "Q1: true when the city is the capital of any nation (such a city never rebels)"),
    ("FUN_004497cc", "Q1e: besieged test (enemy army adjacent at war) used for the stock growth"),
    ("FUN_00451304", "Q5: weather: clears and paints the rough-sea overlay, zeroes every fleet's covered cell"),
    ("FUN_004511bc", "Q5: paints one overlay cell (needs code 0 and no city marker in its 3x3; sets a fleet's covered cell to 1 when the cell holds a fleet marker)"),
    ("FUN_00451fdc", "Q3/Q6: the round: AI seats and the human seat's start of turn (FUN_00452034)"),
    ("FUN_00452034", "Q6: the offer roll at a human seat's turn start (trade or alliance, shown by TPremierForm_StartTurn)"),
    ("TPremierForm_StartTurn", "Q6: shows the offer box 'X wants to trade with Y.' / 'X wants to form an alliance with Y.'"),
    ("FUN_0044ac3c", "Q1d: remove one unit from an army (mercenary desertion)"),
    ("FUN_00449240", "Q3: news line store (61-byte strings at 0x49f994, 40 lines)"),
    ("FUN_00449018", "Q1: distance between two positions (Chebyshev)"),
    ("FUN_00448fd0", "min of two shorts"),
    ("FUN_00448fd8", "max of two shorts"),
    ("FUN_00449b40", "Q1c/Q1f: relation setter (cooldown writes of rebirth and deposition)"),
    ("FUN_004499ec", "Q2: trade income of a nation (the Balance sheet's Trade line)"),
    ("FUN_004498b0", "Q1/Q2: a city's tribute contribution (tax base share)"),
    ("FUN_004494e4", "Q5: id of an own city marker in the 3x3 around a position, -1 when none (the storm roll is halved next to an own city, doubled + 1 otherwise)"),
    ("FUN_0044fa20", "Turn sequencing (review round 1, R7): the seat loop that calls the weekly block when the seat index wraps to 0 (lines 53208-53236)"),
    ("FUN_0044a98c", "Q1c: city strength used by the rebirth to choose the new capital"),
]
out = ["# Code extract for findings/2026-10-11-g3-original-checks.md",
       f"# Provenance: {dump.name}, SHA-256 {sha} (pinned in harness/decompile.py PINS and verified by decompile.check() when this was written).",
       "# First column = line number in that file. Functions are whole. Index:"]
for name, why in WHY:
    a, b = rng[name]; out.append(f"#   {name}: lines {a + 1}-{b + 1}  ({why})")
for name, why in WHY:
    a, b = rng[name]; out.append(f"\n# ===== {name} (lines {a + 1}-{b + 1}) =====")
    out += [f"{j + 1}\t{L[j]}" for j in range(a, b + 1)]
print(write_new(Path(__file__).resolve().parent / "code_extract_g3.txt", "\n".join(out) + "\n"))
