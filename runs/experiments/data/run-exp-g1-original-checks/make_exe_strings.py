#!/usr/bin/env python3
"""Byte-exact literals of the original exe that the g1 finding cites: every occurrence's file offset and the hex of the bytes, for
`Imperial Conquest 2.exe` (SHA-256 recorded in the output). Writes exe_strings_g1.txt beside this script (next free version, rule 6)."""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from versioned import write_new
EXE = Path.home() / "ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.exe"
data = EXE.read_bytes()
LIT = ["You can only trade with 3 nations.", " does not want to trade with you.", "You cannot trade with ", "You cannot mobilise a unit at this time.",
       "Are you sure you want to quit ?", "Are you sure you want to start a new game ?", "This city's fortification has fallen below 75%.",
       "Your army have deposed you because they have not been paid.", "Your unpopularity has forced the army to overthrow you.", "All cities", "all cities",
       "Week  ", "Create unit at ", "Units at ", "Mercenary units", "Expenditure", "Regular units"]
out = [f"# Literals of {EXE.name}, SHA-256 {hashlib.sha256(data).hexdigest()}", "# offset (hex file offset)\ttext\thex of the bytes"]
for s in LIT:
    b = s.encode("latin1"); pos, hits = 0, []
    while True:
        i = data.find(b, pos)
        if i < 0: break
        hits.append(i); pos = i + 1
    out.append(f"{s!r}\t{'  '.join('0x%x' % h for h in hits) or 'NOT FOUND'}\t{b.hex()}")
print(write_new(Path(__file__).resolve().parent / "exe_strings_g1.txt", "\n".join(out) + "\n"))
