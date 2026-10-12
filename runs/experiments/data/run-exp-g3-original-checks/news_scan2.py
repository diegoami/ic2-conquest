#!/usr/bin/env python3
"""Check 3 (L05/L06), scan v2 (review round 1, R2/R4). Read-only over the saves; writes only NEW files beside this script
(versioned.write_new: news_scan.v2.txt style names, never an existing output; the v1 news_scan.txt is untouched).

For every .sav under the given folders: SHA-256 of the file, then its news lines. A treaty block = a header "<P> sues <W> for peace and;"
plus the directly following indented lines (the block ends at the first line that does not start with a space). A "destroys" line =
"<W2> destroys army of <L2>." It is MATCHED to a treaty block when {W2, L2} == {P, W} (the winner W destroyed an army of the proposer P).
For every matched pair: position of the destroys line relative to the whole block: 'destroys BEFORE block' (index < header), 'destroys AFTER block'
(index > last block line). Matched pairs found at ANY distance, not only adjacent ones. Also counted: treaty blocks with no matching destroys
line in the same 40-line news list (unmatched; e.g. the destroys line was already pushed out), and the number of destroys lines of other nations.
Output 1 (per file): <path>\t<sha256>\t<date>\tblocks=...\tpairs=...    Output 2 (summary): the dedup by SHA-256 and the totals.
Usage: python3 news_scan2.py <outprefix-dir> <folder> ...   (writes <dir>/news_scan.v2.txt and news_scan_summary.v2.txt as the next free versions)."""
import hashlib, re, sys, collections
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R)); sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import sav
from versioned import write_new

DES = re.compile(r"^(.+?) destroys army of (.+?)\.$")
SUE = re.compile(r"^(.+?) sues (.+?) for peace and;$")


def scan(news):
    blocks = []
    for i, t in enumerate(news):
        m = SUE.match(t.strip() if False else t)
        if m:
            e = i
            while e + 1 < len(news) and news[e + 1].startswith(" ") and news[e + 1].strip():
                e += 1
            blocks.append((i, e, m.group(1), m.group(2)))
    des = [(i, m.group(1), m.group(2)) for i, t in enumerate(news) if (m := DES.match(t))]
    pairs, unmatched = [], []
    for (h, e, p, w) in blocks:
        found = [(i, "destroys BEFORE block" if i < h else "destroys AFTER block") for (i, a, b) in des if {a, b} == {p, w} and (a, b) == (w, p)]
        if found: pairs += [(h, e, p, w, i, k) for i, k in found]
        else: unmatched.append((h, e, p, w))
    return blocks, des, pairs, unmatched


if __name__ == "__main__":
    outdir = Path(sys.argv[1]); lines = []; seen = {}
    tot = collections.Counter()
    for root in sys.argv[2:]:
        for p in sorted(Path(root).expanduser().rglob("*")):
            if p.suffix.lower() != ".sav" or not p.is_file(): continue
            tot["sav_files"] += 1
            raw = p.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
            try: s = sav.parse(raw)
            except Exception as e: tot["unparsable"] += 1; continue
            blocks, des, pairs, unmatched = scan(s["news"])
            if not (blocks and des): continue
            tot["files_with_both"] += 1
            lines.append(f"{p}\t{sha}\t{s['date']}\tblocks={[(h, e, f'{a} sues {b}') for h, e, a, b in blocks]}\tdestroys={[(i, a, b) for i, a, b in des]}\tpairs={[(h, e, p_, w, i, k) for h, e, p_, w, i, k in pairs]}\tunmatched_blocks={unmatched}")
            first = sha not in seen; seen.setdefault(sha, []).append(str(p))
            if first:
                tot["distinct_sha"] += 1
                for (_, _, _, _, _, k) in pairs: tot[k] += 1
                tot["unmatched_blocks_distinct"] += len(unmatched)
                tot["blocks_distinct"] += len(blocks)
    a = write_new(outdir / "news_scan.txt", "\n".join(lines) + "\n")
    summ = [f"inputs: {sys.argv[2:]}", f"all .sav files read: {tot['sav_files']} (unparsable {tot['unparsable']})",
            f"files holding both a destroys line and a treaty block: {tot['files_with_both']}",
            f"distinct by SHA-256 among them (first occurrence counted below): {tot['distinct_sha']}",
            f"treaty blocks in the distinct files: {tot['blocks_distinct']}; matched to a destroys line of the same nations (any distance): {tot['destroys BEFORE block'] + tot['destroys AFTER block']} pairs",
            f"  destroys BEFORE the block (normal order): {tot['destroys BEFORE block']}", f"  destroys AFTER the block (reverse order): {tot['destroys AFTER block']}",
            f"treaty blocks without a matching destroys line in the same 40-line list: {tot['unmatched_blocks_distinct']}",
            f"per-file hash list: {a.name}; duplicates (same SHA-256, several paths): " + str(sum(1 for v in seen.values() if len(v) > 1)) + " hashes shared by " + str(sum(len(v) for v in seen.values() if len(v) > 1)) + " files"]
    b = write_new(outdir / "news_scan_summary.txt", "\n".join(summ) + "\n")
    print(a, b); print("\n".join(summ))
