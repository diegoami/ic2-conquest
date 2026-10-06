"""Recompute, from the tracked code extract of FUN_004481a0 (the DAT loader), the file offset at which each read starts: the reads are `(**(code **)*piVar2)(piVar2,<dest>,<length>)` in order, a do/while loop
counted by `sStack_6 = N;` repeats the reads inside it N times. Returns the offset of the read into the given destination."""
import re

def function_lines(extract_path, fname, addr):
    lines = []; infile = False; infn = False
    for l in open(extract_path, encoding='utf-8', errors='replace'):
        l = l.rstrip('\n')
        if l.startswith('# FILE '): infile = (l[7:] == fname); infn = False; continue
        if not infile: continue
        m = re.match(r'(\d+)\t(.*)', l)
        if not m: continue
        if re.search(r'FUNCTION \S+ @ %s|==== \S+ @ %s ====' % (addr, addr), m.group(2)): infn = True; lines.append((int(m.group(1)), m.group(2))); continue
        if infn and re.search(r'FUNCTION \S+ @ [0-9a-f]{8}|==== \S+ @ [0-9a-f]{8} ====', m.group(2)): break
        if infn: lines.append((int(m.group(1)), m.group(2)))
    return lines

def reads(extract_path):
    """[(dest, length, multiplier, line)] in file order"""
    L = function_lines(extract_path, 'news_log_decomp.txt', '004481a0')
    out = []; mult = [1]; pending = None
    for ln, t in L:
        m = re.search(r'sStack_6 = (0x[0-9a-f]+|\d+);', t)
        if m: pending = int(m.group(1), 0); continue
        if re.search(r'\bdo \{', t): mult.append(mult[-1] * (pending if pending else 1)); pending = None; continue
        if re.search(r'\} while \(sStack_6 != 0\);', t): mult.pop(); continue
        m = re.search(r'\(\*\*\(code \*\*\)\*piVar2\)\(piVar2,([^,]+),(0x[0-9a-f]+|\d+)\);', t)
        if m: out.append((m.group(1).strip(), int(m.group(2), 0), mult[-1], ln))
    return out

def pool_read(extract_path, dest='&DAT_0049dc68'):
    off = 0
    for d, n, mult, ln in reads(extract_path):
        if d == dest: return off, n, d
        off += n * mult
    raise ValueError('no read into ' + dest)
