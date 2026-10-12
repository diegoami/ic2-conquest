"""Check 3 (L05/L06): in every save under the given folders whose news holds both a "<A> destroys army of <B>." line and a treaty block
("... sues ... for peace and;" followed by the indented lines), print the index of each, so the order in the news log is read from the saves themselves.
Usage: python3 news_scan.py <folder> ... > news_scan.txt   (read-only; the saves are not copied)."""
import re, sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R))
from state import sav
for root in sys.argv[1:]:
    for p in sorted(Path(root).expanduser().rglob("*")):
        if p.suffix.lower() != ".sav": continue
        try: s = sav.parse(p.read_bytes())
        except Exception as e: continue
        news = s["news"]
        d = [i for i, t in enumerate(news) if re.search(r" destroys army of ", t)]
        sue = [i for i, t in enumerate(news) if re.search(r" sues .* for peace and;", t)]
        if d and sue:
            pairs = [(i, j, "destroys FIRST" if i < j else "treaty FIRST") for i in d for j in sue if abs(i - j) <= 1]
            print(f"{p}\t{s['date']}\tdestroys@{d}\tsues@{sue}\tadjacent:{pairs}")
            for i in range(min(d + sue) - 1, min(max(d + sue) + 6, len(news))): print(f"    [{i}] {news[i]!r}")
