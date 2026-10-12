#!/usr/bin/env python3
"""R4 positive control for news_scan2.scan: a synthetic news list with the treaty block FIRST (header four lines before the destroys line's end)
must be classified 'destroys AFTER block'; an unrelated destroys line next to a block must not be paired."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from news_scan2 import scan
blk = ["B sues A for peace and;", "    B ends all current trading agreements.", "    B  ends all current alliances.", "    B pays reparations of 1 talents."]
rev = ["x"] + blk + ["A destroys army of B."]
fwd = ["x", "A destroys army of B."] + blk
oth = ["x", "C destroys army of D."] + blk
for name, n in (("reverse", rev), ("forward", fwd), ("unrelated", oth)):
    b, d, p, u = scan(n); print(name, [x[-1] for x in p], "unmatched", u)
assert [x[-1] for x in scan(rev)[2]] == ["destroys AFTER block"] and [x[-1] for x in scan(fwd)[2]] == ["destroys BEFORE block"] and scan(oth)[2] == [] and len(scan(oth)[3]) == 1
print("OK")
