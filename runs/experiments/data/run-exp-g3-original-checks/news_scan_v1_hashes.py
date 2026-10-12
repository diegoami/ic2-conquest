#!/usr/bin/env python3
"""R4: the dedup behind "870 distinct by SHA-256": hashes every path listed in the (untouched) v1 news_scan.txt and writes the list + count
to the next free news_scan_v1_hashes[.vN].txt (it was run once, result news_scan_v1_hashes.txt: 1195 paths, 0 missing, 870 distinct)."""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from versioned import write_new
D = Path(__file__).resolve().parent
out = []; seen = {}; miss = 0
for l in open(D / 'news_scan.txt'):
    p = Path(l.split('\t')[0])
    if not p.exists(): miss += 1; out.append(f"MISSING\t{p}"); continue
    h = hashlib.sha256(p.read_bytes()).hexdigest(); seen.setdefault(h, []).append(str(p)); out.append(f"{h}\t{p}")
out.append(f"# paths in news_scan.txt: {sum(1 for _ in open(D / 'news_scan.txt'))}; missing now: {miss}; distinct SHA-256: {len(seen)}")
print(write_new(D / 'news_scan_v1_hashes.txt', "\n".join(out) + "\n"))
