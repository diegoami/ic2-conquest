#!/usr/bin/env python3
"""Line-numbered extract of every decompiled function that findings/2026-10-12-g4-followups.md cites, from the pinned all_app_functions.txt
(SHA-256 checked by harness.decompile.check(); first column = that file's line number). Writes code_extract_g4.txt beside this script (next free version)."""
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
    ("FUN_00452034", "C/K: the human seat's turn start: the offer roll (trade / alliance) and the four deposition disjuncts (year 250, cities > 333, unity < 400, treasury below the debt line)"),
    ("FUN_0044c8f0", "C: deposition of a leader (news line for an AI nation, HumanLeaderFalls for a human; unity, treasury, cooldown reset)"),
    ("TPremierForm_HumanLeaderFalls", "C: opens the End of Game form and ends the human's turn"),
    ("FUN_00449078", "C: the leader's nation loses the human flag; the game goes on with the AI seats"),
    ("FUN_00449050", "F/C: true when any nation has the human flag"),
    ("TPolitics_MakeTrade", "B: the trade refusals (3 own partners, cooldown, target full or relation above 1, the pending-offer exemption)"),
    ("FUN_004499c0", "B/K: number of trade partners (relation 1) of a nation"),
    ("FUN_00449b40", "B/J: the relation setter (a 0 on a relation 1 / 2 / 3 writes the cooldown -8 / -24 / -18)"),
    ("FUN_00449cd8", "K: a nation has a war relation"),
    ("FUN_00449a44", "J: news line of a new alliance or war"),
    ("TArmyRecruits_MobilizeUnits", "D: Mobilize button: state > 15 units, FUN_0044a4e0, the refusal box"),
    ("FUN_0044a4e0", "D: mobilise one queued unit into an army (or a new one)"),
    ("FUN_0044a120", "D: choose the army that takes the unit: distance 1, or < 6 for a nation without the human flag; the last qualifying army wins; capacity afterwards"),
    ("FUN_00449f08", "D: create a new army at a free tile (needs a tile and fewer than 198 armies); writes the marker nation + 200"),
    ("FUN_004492c0", "D: the last map word of the 3 x 3 around a city in 2..11 (land) or 0..1 (sea)"),
    ("FUN_0044a66c", "D: highest used slot + 1 of an army"),
    ("FUN_0044a698", "D: total troops of an army"),
    ("FUN_00449018", "D/H: Chebyshev distance"),
    ("FUN_00448fd0", "min of two shorts"), ("FUN_00448fd8", "max of two shorts"),
    ("FUN_004504f4", "D: AI mobilisation: state-24 units, only when an own army is within distance < 6 of a ready unit's city or four units are ready"),
    ("FUN_0044ffbc", "D/J: the AI seat's strength/threat balance: FUN_004504f4 is called only when the threat exceeds the strength"),
    ("FUN_0044a8cc", "D: strength of an army"),
    ("TPremierForm_NewGame", "F: File > New: Confirm, data loader, the initialiser that clears the flag, the leaders form"),
    ("TPremierForm_OpenGameFile", "F: File > Open sets the flag"),
    ("TPremierForm_SaveGameFile", "F: File > Save writes silently only when the flag is set"),
    ("TPremierForm_SaveGameFileAs", "F: File > Save as sets the flag"),
    ("TPremierForm_InitialiseForm", "F: form create: calls the initialiser at start"),
    ("TPremierForm_CheckQuit", "E: the quit prompt"),
    ("FUN_00451b40", "I/J: the quarterly tick"),
    ("FUN_004514ec", "G/L: the weekly block: storm pass, weather call, quarter call, news header"),
    ("FUN_004499ec", "I: trade income of a nation (tax base of partners and allies / 12)"),
    ("FUN_004498b0", "I: a city's tribute contribution"),
    ("FUN_004494e4", "G: id of an own city marker in the 3 x 3 around a position, -1 when none"),
    ("FUN_00451304", "L: weather: clears and paints the rough-sea overlay around 20 fixed centres, zeroes every fleet's covered cell"),
    ("FUN_004511bc", "L: paints one overlay cell"),
    ("FUN_0044c204", "H: rebellion of one city"),
    ("FUN_0044c360", "J: rebirth of a dead nation (resets its relation row to 0, then -8 with each moved city's owner)"),
    ("FUN_0044bed8", "J/H: transfer of one city (a nation left without a city: its relations are reset through the setter)"),
    ("FUN_0044c528", "J: a nation conquered (all its relations through the setter with 0)"),
    ("FUN_0044fb7c", "J: the AI seat's diplomacy: new trades, wars, alliances and the last loop that drops a weaker trade partner (setter with 0: cooldown -8)"),
    ("FUN_0044faa0", "J: strength helper of the AI diplomacy"),
    ("FUN_0044fb50", "J: helper of the AI alliance rule"),
    ("FUN_0044fa20", "turn sequencing: the seat loop that calls the weekly block when the seat index wraps to 0"),
    ("FUN_00451fdc", "turn sequencing: the round: AI seats and the human seat's start of turn"),
]
out = ["# Code extract for findings/2026-10-12-g4-original-checks.md",
       f"# Provenance: {dump.name}, SHA-256 {sha} (pinned in harness/decompile.py PINS and verified by decompile.check() when this was written).",
       "# First column = line number in that file. Functions are whole. Index:"]
for name, why in WHY:
    a, b = rng[name]; out.append(f"#   {name}: lines {a + 1}-{b + 1}  ({why})")
for name, why in WHY:
    a, b = rng[name]; out.append(f"\n# ===== {name} (lines {a + 1}-{b + 1}) =====")
    out += [f"{j + 1}\t{L[j]}" for j in range(a, b + 1)]
print(write_new(Path(__file__).resolve().parent / "code_extract_g4.txt", "\n".join(out) + "\n"))
