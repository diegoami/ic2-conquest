#!/usr/bin/env python3
"""Line-numbered extract of every decompiled function that findings/2026-10-11-g1-original-checks.md cites, from the pinned all_app_functions.txt
(SHA-256 checked by harness.decompile.check(); first column = that file's line number). Writes code_extract_g1.txt beside this script (next free version)."""
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
    ("TBalanceSheet_PaintBalance", "G2: every Balance sheet figure; Expenditure Total sums administration, fleets, queue, regular and mercenary units; Debt limit rounding"),
    ("FUN_00452034", "G2/G3: human start of turn: offers, then the deposition test (treasury < wealth / -500 or < -20000, unrounded)"),
    ("FUN_0044c8f0", "G2: deposition: human branch calls TPremierForm_HumanLeaderFalls"),
    ("THumanFalls_InitializeForm", "G2: the game-over texts"),
    ("TPolitics_ChangeIR", "G3: radio click handler, calls MakeTrade"),
    ("TPolitics_MakeTrade", "G3: trade proposal refusals: 3 own partners, target at 3 partners, does not want to trade"),
    ("FUN_004499c0", "G3: count of a nation's trade partners"),
    ("FUN_00449050", "G6: true when any nation has the human flag (+0x490): the quit/new confirmations depend on it"),
    ("TPremierForm_CheckQuit", "G6: 'Are you sure you want to quit ?'"),
    ("TPremierForm_NewGame", "G5/G6: New game confirmation, then the new game"),
    ("TPremierForm_OpenGameFile", "G5: Open stores the file name (DAT_0045e7a8) and sets the 'has a name' flag (0x4a0334)"),
    ("TPremierForm_SaveGameFile", "G5: Save writes silently when the flag is set, else Save as"),
    ("TPremierForm_SaveGameFileAs", "G5: Save as"),
    ("TArmyRecruits_SetCityRecruits", "G8: list of queued units, 'Units at all cities'"),
    ("TArmyRecruits_RecruitUnit", "G8: the 75% refusal and the 'All cities' entry"),
    ("TArmyRecruits_MobilizeUnits", "G9: refusal text"),
    ("FUN_0044a4e0", "G9: mobilise one unit: finds or creates the army, flag 0 when none"),
    ("FUN_0044a120", "G9: own army within distance 1 with room"),
    ("FUN_00449f08", "G9: new army: refused at 198 armies (0xc6) or when no free tile"),
    ("FUN_00449018", "G9: distance between two positions (the army-to-city test in FUN_0044a120: 1, or under 6 for a nation whose flag at 0x474b00 is 0)"),
    ("FUN_00448fd0", "G9: min of two shorts (clamp helper of FUN_004492c0)"),
    ("FUN_00448fd8", "G9: max of two shorts (FUN_00449018 = max(|dx|, |dy|), the Chebyshev distance)"),
    ("FUN_0044a66c", "G9: number of units in an army (compared with 0x14 = 20 in FUN_0044a120)"),
    ("FUN_0044a698", "G9: total troops in an army (plus the incoming unit's troops must be under 0x186a1 = 100,001)"),
    ("FUN_004492c0", "G9: find a free tile near a position for a new army (negative when none), called by FUN_00449f08"),
    ("FUN_004514ec", "G10: weekly block; the news header built at 54679-54692: Week + two spaces + week + 6 spaces + season + 6 spaces + year + BC"),
    ("FUN_00449240", "G10: news line store (61-byte Pascal strings at 0x49f994, 40 lines)"),
    ("FUN_004028c4", "G10: Str(x:0)"),
    ("FUN_00402978", "G10: Pascal string to C string"),
]
out = ["# Code extract for findings/2026-10-11-g1-original-checks.md",
       f"# Provenance: {dump.name}, SHA-256 {sha} (pinned in harness/decompile.py PINS and verified by decompile.check() when this was written).",
       "# First column = line number in that file. Functions are whole. Index:"]
for name, why in WHY:
    a, b = rng[name]; out.append(f"#   {name}: lines {a + 1}-{b + 1}  ({why})")
for name, why in WHY:
    a, b = rng[name]; out.append(f"\n# ===== {name} (lines {a + 1}-{b + 1}) =====")
    out += [f"{j + 1}\t{L[j]}" for j in range(a, b + 1)]
print(write_new(Path(__file__).resolve().parent / "code_extract_g1.txt", "\n".join(out) + "\n"))
