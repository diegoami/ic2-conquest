"""Recompute, from the tracked code extract only (a dict line number -> text), (1) the full construction of a message built at run time at a message-box call site
(fragment order, variable placement, conditional pieces, either/or pieces) and (2) the order in which the tests of a function are evaluated on the path to each call site.
Used by tables.py (to write the finding) and by claims_audit.py (to check it)."""
import re

COND, OR = '⟨if⟩', '⟨or⟩'          # markers inside a code span: a conditional piece, and the separator of alternatives

def unesc(s):
    return re.sub(r'\\(x[0-9a-fA-F]{2}|.)', lambda m: {'n': '\n', 't': '\t', "'": "'", '"': '"', '\\': '\\'}.get(m.group(1)) or chr(int(m.group(1)[1:], 16)), s)

def indent(t): return len(t) - len(t.lstrip(' '))

def func_range(X, line):
    """(first, last) line numbers of the function holding `line` (the extract keeps '// ==== name @ addr ====' headers)"""
    starts = sorted(k for k, v in X.items() if v.startswith('// ===='))
    first = max(s for s in starts if s <= line)
    nxt = [s for s in starts if s > first]
    return first, (min(nxt) - 1 if nxt else max(X))

def stmt(X, line, last):
    """the statement starting at `line`: (text, last line of it)"""
    k = line; t = X[k].strip()
    while not re.search(r'[;{}]\s*$', X[k]) and k + 1 <= last and k + 1 in X: k += 1; t += ' ' + X[k].strip()
    return t, k

def stmt_start(X, j, first):
    """first line of the statement that ends on line j (a condition may continue over several lines)"""
    k = j
    while k - 1 > first and not re.search(r'[;{}]\s*$', X.get(k - 1, ';')): k -= 1
    return k

def header_lines(X, line, first):
    """line numbers of the block headers enclosing `line` (outermost first): the first line of a statement that ends in `{` and starts at lower indent"""
    out = []; cur = indent(X[line]); j = line - 1
    while j > first and cur > 2:
        t = X.get(j, '')
        if t.strip() and re.search(r'\{\s*$', t):
            k = stmt_start(X, j, first)
            if indent(X[k]) < cur:
                out.append(k); cur = indent(X[k])
        j -= 1
    return out[::-1]

def call_statement(X, line):
    first, last = func_range(X, line)
    # the call may start on an earlier line than `line` only if `line` is its first line: sites are keyed by their first line
    return stmt(X, line, last)

def split_args(txt, name):
    j = txt.index(name + '(') + len(name) + 1; depth = 0; args = []; cur = ''; instr = False; esc = False
    for ch in txt[j:]:
        if instr:
            cur += ch
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': instr = False
            continue
        if ch == '"': instr = True; cur += ch; continue
        if ch in '([': depth += 1
        if ch in ')]':
            if depth == 0: args.append(cur.strip()); break
            depth -= 1
        if ch == ',' and depth == 0: args.append(cur.strip()); cur = ''; continue
        cur += ch
    return args

def category(arg):
    if re.search(r'&DAT_00474670\b', arg): return 'nation name'
    if re.search(r'&DAT_00479590\b', arg): return 'city name'
    return None

def build_ops(X, buf, upto, first, call_headers):
    """the string operations on buffer `buf` that lead to the call at `upto`: starting at the last assignment (FUN_00405b00) whose block encloses the call"""
    ops = []
    for ln in range(first, upto):
        t = X.get(ln, '')
        if re.search(r'FUN_00405b00\(\s*%s\s*,|FUN_00405bc8\(\s*%s\s*,' % (re.escape(buf), re.escape(buf)), t):
            s, _ = stmt(X, ln, upto)
            kind = 'assign' if 'FUN_00405b00(' in s else 'append'
            args = split_args(s, 'FUN_00405b00' if kind == 'assign' else 'FUN_00405bc8')
            ops.append((ln, kind, args[1], set(header_lines(X, ln, first))))
    # last assign whose headers are all headers of the call
    ch = set(call_headers)
    ai = [i for i, o in enumerate(ops) if o[1] == 'assign' and o[3] <= ch]
    if not ai: raise ValueError('no assignment to %s encloses the call' % buf)
    return ops[ai[-1]:], ch

def number_vars(X, first, upto):
    """identifiers that hold a decimal number: the second argument of the int-to-string pair FUN_004028c4 / FUN_00402978"""
    out = set()
    for ln in range(first, upto):
        m = re.search(r'FUN_00402978\(\s*\w+\s*,\s*(?:\(char \*\))?(\w+)\)', X.get(ln, ''))
        if m: out.add(m.group(1))
    return out

def alternatives(X, name, first, upto):
    """a buffer assigned a different literal in each branch: [(literal, header lines)]"""
    alts = []
    for ln in range(first, upto):
        m = re.search(r'FUN_00405b00\(\s*%s\s*,\s*"((?:[^"\\]|\\.)*)"\)' % re.escape(name), X.get(ln, ''))
        if m: alts.append((unesc(m.group(1)), ln))
    return alts

def construction(X, line):
    """the items of the message built at the call whose first line is `line`: ('lit', s) | ('var', category) | ('cond', s) | ('alt', [s, ...]); raises if the call has a literal text"""
    txt, _ = call_statement(X, line)
    arg0 = split_args(txt, 'FUN_0042d750')[0]
    if arg0.startswith('(uint *)"'): return None
    first, last = func_range(X, line)
    mm = None
    for ln in range(line - 1, first, -1):
        m = re.search(r'FUN_00403458\(\s*\(int \*\)&%s\s*,\s*(\w+)\s*,' % re.escape(arg0), X.get(ln, ''))
        if m: mm = m; break
    if not mm: raise ValueError('no copy of a buffer into %s before line %d' % (arg0, line))
    buf = mm.group(1)
    call_headers = header_lines(X, line, first)
    ops, ch = build_ops(X, buf, ln, first, call_headers)
    nums = number_vars(X, first, ln)
    items = []
    for (oln, kind, arg, hdrs) in ops:
        cond = not (hdrs <= ch)
        m = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', arg)
        if m: item = ('cond' if cond else 'lit', unesc(m.group(1)))
        elif re.fullmatch(r'(?:\(char \*\))?(\w+)', arg) and re.sub(r'\(char \*\)', '', arg) in nums: item = ('var', 'number')
        elif category(arg): item = ('var', category(arg))
        elif re.fullmatch(r'\w+', arg) and alternatives(X, arg, first, ln):
            item = ('alt', [a for a, _ in alternatives(X, arg, first, ln)])
        else: raise ValueError('unrecognised piece %r at line %d' % (arg, oln))
        items.append(item)
    return items

def span(item):
    k, v = item
    if k == 'lit': return '`%s`' % v
    if k == 'var': return '`<%s>`' % v
    if k == 'cond': return '`%s%s`' % (COND, v)
    if k == 'alt': return '`%s`' % OR.join(v)
    raise ValueError(k)

def spans(X, line):
    items = construction(X, line)
    return None if items is None else [span(i) for i in items]

# ---------------------------------------------------------------- order of tests
def tests_on_path(X, line):
    """line numbers of the if / else-if tests evaluated on the path to `line` (the test of an enclosing if, and every earlier test of the chain an else belongs to)"""
    first, last = func_range(X, line); out = set()
    for h in header_lines(X, line, first):
        t = X[h].strip()
        k = indent(X[h])
        # the start of this header's own statement may be the `} else if (` line itself
        if re.match(r'(\} )?(else )?if\b', t) or re.match(r'\}?\s*else if\b', t): out.add(h)
        if re.match(r'(\} )?else\b', t) or t.startswith('else'):
            j = h - 1
            while j > first:
                u = X.get(j, '')
                if u.strip() and indent(u) == k and re.match(r'(\} )?(else )?if\b', u.strip()):
                    out.add(j)
                    if not re.match(r'(\} )?else\b', u.strip()): break
                elif u.strip() and indent(u) < k: break
                j -= 1
    return out

def last_test(X, line):
    t = tests_on_path(X, line)
    return max(t) if t else 0

def rank_in_function(X, lines):
    """{call line: 1-based position in the order the code evaluates the tests that lead to each box}"""
    order = sorted(lines, key=lambda l: (last_test(X, l), l))
    return {l: i + 1 for i, l in enumerate(order)}
