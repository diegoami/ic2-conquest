"""Control flow of one decompiled function, for the predicate audit (issue #58).

Independent of construct.py: a small recursive-descent reader of Ghidra's C output that records, for every line, the chain of
enclosing tests and the branch taken to reach it (an `if` test and `True` for its then-block, `False` for its else-block; an
`else if` is the `if` of the enclosing else-block), and the loops around it. A test is named by the line its `if` keyword is on;
`span` gives every line its condition covers, so a citation of a continuation line maps to its test.

X: {line number: text} (one function or more; the first column of code_extract_refusals*.txt). Standard library only."""
import re

IDENT = re.compile(r'[A-Za-z_]\w*')


class Fn:
    """parse(X, first, last) of one function: .ctx[line] = tuple of ('if', test_line, outcome) and ('loop', line) from the
    outside in; .tests[test_line] = {'cond': text, 'span': [lines], 'then': (a, b), 'else': (a, b) or None};
    .labels[name] = line; .gotos = [(line, label)]."""

    def __init__(self, X, first, last):
        self.X = X; self.first = first; self.last = last
        chars = []; lines = []
        for ln in range(first, last + 1):
            t = X.get(ln, '')
            if t.lstrip().startswith('//'): t = ''
            for ch in t + '\n':
                chars.append(ch); lines.append(ln)
        self.s = ''.join(chars); self.L = lines
        self.ctx = {}; self.tests = {}; self.labels = {}; self.gotos = []; self.stmts = []
        i = self.s.find('\n{')
        if i < 0: raise ValueError('no function body between lines %d and %d' % (first, last))
        self._block(i + 2, ())

    # ---------------------------------------------------------------- lexing helpers
    def _ws(self, i):
        s = self.s
        while i < len(s):
            if s[i].isspace(): i += 1
            elif s.startswith('/*', i): i = s.index('*/', i) + 2
            else: break
        return i

    def _match(self, i, open_='(', close=')'):
        """index of the bracket closing the one at i (strings and char literals skipped)"""
        s = self.s; depth = 0; j = i
        while j < len(s):
            c = s[j]
            if c in '"\'':
                q = c; j += 1
                while s[j] != q:
                    j += 2 if s[j] == '\\' else 1
            elif c == open_: depth += 1
            elif c == close:
                depth -= 1
                if depth == 0: return j
            j += 1
        raise ValueError('unbalanced %s at line %d' % (open_, self.L[i]))

    def _word(self, i):
        m = IDENT.match(self.s, i)
        return m.group(0) if m else None

    def _mark(self, a, b, ctx):
        for k in range(a, min(b + 1, len(self.L))):
            self.ctx.setdefault(self.L[k], ctx)

    # ---------------------------------------------------------------- statements
    def _block(self, i, ctx):
        """s[i-1] == '{'; returns the index after the matching '}'"""
        while True:
            i = self._ws(i)
            if self.s[i] == '}': return i + 1
            i = self._stmt(i, ctx)

    def _body(self, i, ctx):
        i = self._ws(i)
        if self.s[i] == '{':
            self._mark(i, i, ctx)
            return self._block(i + 1, ctx)
        return self._stmt(i, ctx)

    def _stmt(self, i, ctx):
        s = self.s; i = self._ws(i); w = self._word(i)
        if w == 'if':
            j = s.index('(', i); k = self._match(j)
            line = self.L[i]
            span = sorted(set(self.L[i:k + 1]))
            self._mark(i, k, ctx)
            t = {'cond': s[j + 1:k], 'span': span, 'line': line}
            self.tests[line] = t
            a = self._ws(k + 1); b = self._body(a, ctx + (('if', line, True),)); t['then'] = (self.L[a], self.L[b - 1])
            e = self._ws(b)
            if self._word(e) == 'else':
                a2 = self._ws(e + 4); b2 = self._body(a2, ctx + (('if', line, False),)); t['else'] = (self.L[a2], self.L[b2 - 1])
                return b2
            t['else'] = None
            return b
        if w == 'do':
            line = self.L[i]
            b = self._body(i + 2, ctx + (('loop', line),))
            b = self._ws(b)
            assert self._word(b) == 'while', 'do without while at line %d' % line
            j = s.index('(', b); k = self._match(j)
            self._mark(b, s.index(';', k), ctx + (('loop', line),))
            return s.index(';', k) + 1
        if w in ('while', 'for', 'switch'):
            line = self.L[i]
            j = s.index('(', i); k = self._match(j)
            self._mark(i, k, ctx + (('loop', line),))
            return self._body(k + 1, ctx + (('loop', line),))
        if s[i] == '{':
            return self._block(i + 1, ctx)
        if w and s[i + len(w):i + len(w) + 1] == ':' and s[i + len(w):i + len(w) + 2] != '::' and w not in ('default', 'case'):
            self.labels[w] = self.L[i]; self._mark(i, i + len(w), ctx)
            return i + len(w) + 1
        # a plain statement: up to ';' at bracket depth 0
        j = i; depth = 0
        while True:
            c = s[j]
            if c in '"\'':
                q = c; j += 1
                while s[j] != q:
                    j += 2 if s[j] == '\\' else 1
            elif c in '([{': depth += 1
            elif c in ')]}': depth -= 1
            elif c == ';' and depth == 0: break
            j += 1
        self._mark(i, j, ctx)
        text = s[i:j + 1]
        self.stmts.append((self.L[i], self.L[j], text))
        m = re.match(r'goto\s+(\w+)', text)
        if m: self.gotos.append((self.L[i], m.group(1)))
        return j + 1

    # ---------------------------------------------------------------- queries
    def test_of(self, line):
        """the test whose condition covers `line` (its `if` line), or None"""
        for t, d in self.tests.items():
            if line in d['span']: return t
        return None

    def path(self, line):
        """{test line: outcome} of the enclosing tests on the way to `line` (a line inside a test's own condition is not under it)"""
        return {c[1]: c[2] for c in self.ctx.get(line, ()) if c[0] == 'if'}

    def loops(self, line):
        return [c[1] for c in self.ctx.get(line, ()) if c[0] == 'loop']

    def stmts_in(self, a, b):
        """plain statements whose first line lies in [a, b]"""
        return [st for st in self.stmts if a <= st[0] <= b]


def functions(X):
    """{name: (first line, last line)} from the `// ==== NAME @ addr ====` headers of an extract"""
    heads = sorted((ln, m.group(1)) for ln, t in X.items() for m in [re.match(r'// ==== (\S+) @ [0-9a-f]+ ====', t)] if m)
    out = {}
    for k, (ln, name) in enumerate(heads):
        nxt = heads[k + 1][0] if k + 1 < len(heads) else max(X) + 1
        body = [l for l in X if ln < l < nxt]
        end = max([l for l in body if X[l].rstrip() == '}'] or [nxt - 1])
        out[name] = (ln, end)
    return out


def function_of(X, line, fns=None):
    fns = fns or functions(X)
    for name, (a, b) in fns.items():
        if a <= line <= b: return name
    return None


_cache = {}
def fn(X, name, fns=None):
    key = (id(X), name)
    if key not in _cache:
        a, b = (fns or functions(X))[name]
        _cache[key] = Fn(X, a, b)
    return _cache[key]


def read_extract(path):
    X = {}
    for l in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'(\d+)\t(.*)', l.rstrip('\n'))
        if m: X[int(m.group(1))] = m.group(2)
    return X
