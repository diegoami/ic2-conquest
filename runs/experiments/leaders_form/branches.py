"""Derive the branch arms of a decompiled function from its text (independent of any finding): every `if (...) {` chain yields its arms 'then', each `else if (...) {` ('else-if', identified by the arm's own line), the `else {` ('else', the arm's line) and,
when the chain has no else, the fall-through 'implicit-else' (identified by the head line). A condition may wrap over several lines. Used by claims_audit.py to require, from the code alone, a row for every arm of the form's handlers."""
import re

def norm(s): return re.sub(r'\s+', ' ', s).strip()

def arms(lines):
    """lines: [(line number, text)] of one function, in order. Returns a set of (line number, arm)."""
    L = [(k, norm(t)) for k, t in lines]; n = len(L); out = set()
    def block_end(i):
        depth = 0; started = False
        for j in range(i, n):
            t = L[j][1]; depth += t.count('{') - t.count('}')
            if '{' in t: started = True
            if started and depth <= 0: return j
        return None
    for i in range(n):
        if not re.match(r'if \(', L[i][1]): continue
        h = i
        while h < n and not L[h][1].endswith('{') and not L[h][1].endswith(';'): h += 1
        head = L[i][0]; out.add((head, 'then'))
        if h >= n or not L[h][1].endswith('{'):                    # an unbraced arm (a single statement): no else follows in decompiled code of this program
            out.add((head, 'implicit-else')); continue
        j = block_end(h); has_else = False
        while j is not None:
            k = j + 1; nt = L[k][1] if k < n else ''
            if nt.startswith('else if ('): out.add((L[k][0], 'else-if')); j = block_end(k); continue
            if nt.startswith('else'): out.add((L[k][0], 'else')); has_else = True
            break
        if not has_else: out.add((head, 'implicit-else'))
    return out
