#!/usr/bin/env python3
"""Predicate audit of the refusal-texts catalogue (issue #58).

Two parts.
 1. TABLE: the predicate table (predicates-vN.json, written by predicates_def.py from the code) is checked against the code extract:
    every test it names exists, has the outcome it claims on the path to the box (or to the flag's set line, or the callee's line),
    and the tests it lists for a line are exactly the tests the control flow puts on that line's path; each atom's code is in the
    condition, with the operator and constant the table gives; flags are set where it says; short-circuit operands, gotos and
    preceding ifs behave as it says; context tests have no box on their other branch; 'drop' effects do nothing else in the box's
    branch and the acting line is on another branch (or the box returns first); 'clamp' effects follow a loop that acts; prompt answers
    act on the branch the table gives. Every guard and atom carries a citation that resolves. Any failure here is a TABLE error.
 2. CATALOGUE: each row of the finding's catalogue, prompts and notices tables is compared with its predicates:
    - unresolved citation: an `L<line> «quote»` whose line is not in the extract (or the dump, when given) or whose quote is not in it;
    - missing citation: a decisive test of the row that its condition (or raised-when) cell does not cite and that is not the test of
      an earlier box of the same function (the 'test order' column); a cell with no citation; a prompt's answer test not cited;
    - branch direction: a cited test line whose marker ('the else of', 'the pass test is', 'not (', 'fails' = the test is false;
      none = true) disagrees with the outcome the box needs;
    - condition: a deciding test whose comparison (constant and direction, or the named state) the cell does not state;
    - effect: the effect cell's kind (dropped / clamped; the notices' note) against the code's;
    - answer: the answer cell's Yes number, the Yes effects and the effects that happen whatever the answer, against the code.
usage: predicate_audit.py [--finding F] [--predicates P] [--extract X] [--dump D] [--out FILE]
Exit status 0 only with 0 table errors and 0 catalogue mismatches. Standard library only."""
import argparse, hashlib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cflow
from common import latest, write_new

ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
DATA = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-refusal-audit58')
EXTRACT = os.path.join(ROOT, 'runs', 'experiments', 'data', 'run-exp-refusal-texts', 'code_extract_refusals.v2.txt')
FINDING = os.path.join(ROOT, 'findings', '2026-10-05-refusal-texts-and-conditions.md')
LAYOUT = os.path.join(ROOT, 'docs', 'sav-layout-notes.md')

norm = lambda s: re.sub(r'\s+', ' ', s).strip()
CITE = re.compile(r'L(\d+) «([^»]*)»')
NEG_BEFORE = re.compile(r'(the else of|else-branch of|the pass test is|not \(|fails)\s*$', re.I)
NEG_AFTER = re.compile(r'^\)?\s*(fails|is false)\b', re.I)

# ------------------------------------------------------------------ phrase lexicon: what a cell must say for a state
# concept: (regex when the atom is TRUE, regex when it is FALSE); the atom names its concept as 'concept:<name>'
CONCEPTS = {
    'slot1_empty': (r'second unit slot is empty|has one unit|only 1 unit', r'2 or more units|two or more units'),
    'aboard': (r'(?<!not )(?<!no )aboard|on a fleet', r'not aboard|neither .{0,20}aboard'),
    'no_own_city': (r'no own city|no city|not near', r'near (?:an? |its |one of your )?(?:own )?cit|own city (?:is )?(?:next|near|within)|next to (?:an? |its )?(?:own )?city|city is near'),
    'no_owner_city': (r'not (?:docked|next to a city)', r'next to a city of its owner|(?:next to|near|docked at) (?:a |its )?(?:own )?city'),
    'no_moves': (r'no moves|without moves', r'with (?:\w+ )?moves|1 or more moves|has moves'),
    'fleet_no_army': (r'carries no army|no army aboard|not carrying', r'(?<!no )carr(?:ies|ying) an army|(?<!no )army aboard'),
    'fleet_has_army': (r'(?<!no )carr(?:ies|ying) an army|(?<!no )army aboard', r'carries no army|no army aboard|not carrying'),
    'slot19_free': (r'fewer than 20 units|slot is free', r'20th slot is occupied|already has 20'),
    'war': (r'(?<!not )(?<!not already )at war', r'not (?:already )?at war'),
    'not_aboard_fleet': (r'not aboard', r'(?<!not )aboard a fleet'),
    'aboard_fleet': (r'(?<!not )aboard a fleet', r'not aboard'),
    'no_new_fleet': (r'new fleet index at -1|no free fleet slot', r'a new fleet'),
    'not_besieged': (r'not under siege', r'(?<!not )under siege|enemy army is next'),
    'regular': (r'regular', r'not 0|mercenar|non-zero'),
    'types_differ': (r'not all of one type|not .{0,20}same type|different type', r'all of one type|same type'),
    'slot39_free': (r'40th recruitment slot is free', r'40th recruitment slot is occupied|limit of 40'),
    'all_cities': (r'(?<!not )"All cities"', r'not "All cities"'),
    'capital': (r'(?<!not )the capital', r'not the capital'),
    'no_place': (r'neither an army to join nor room|no place', r'found a place'),
    'computer': (r'computer', r'human'),
    'relation_negative': (r'(?<!not )negative', r'not negative'),
    'relation_nonneg': (r'not negative', r'(?<!not )negative'),
    'pending_war': (r'pending war', r'no pending war'),
    'pending_alliance': (r'pending alliance', r'no pending alliance'),
    'ally_at_war': (r'with a nation at war', r'not at war'),
    'not_at_war_any': (r'not at war with anyone', r'(?<!not )at war with anyone'),
    'no_coastal': (r'no (?:own city is a )?free coastal city|no free coastal', r'a free coastal city exists'),
    'none_building': (r'no own fleet is under construction', r'(?:at least one|an) own fleet is under construction'),
    'human_exists': (r'human', r'no human'),
    'own_fleet': (r'own fleet', r'another nation'),
    'under_construction': (r'under construction', r'launched'),
    'proposal': (r'proposed', r'no proposal'),
    'not_granted': (r'has not got it|not got', r'got it'),
}
ANSWER_CONCEPTS = {
    'treasury': r'treasury', 'city_supplies': r'supplies', 'army_deleted': r'disband|delet|remov', 'fleet_deleted': r'delet|scuttl|remov',
    'war': r'\bwar\b', 'attack': r'attack|siege', 'deselect': r'deselect|selection', 'units_removed': r'remov|disband|delet',
    'mobilisation': r'mobili[sz]ation', 'queue_deleted': r'delet|remov', 'new_game_form': r'new[- ]game', 'quit': r'quit',
    'seat_to_computer': r'computer|seat|abdicat',
}
WORDS = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 10: 'ten', 20: 'twenty', 40: 'forty', 100: 'hundred'}
LT_WORDS = r'fewer than|less than|below|smaller than|under'
GT_WORDS = r'more than|exceeds?|above|over|larger than|greater than'


def num_forms(n):
    f = [str(n)]
    if abs(n) >= 1000: f.append('{:,}'.format(n))
    if n in WORDS: f.append(WORDS[n])
    return f


def NUM(n): return r'(?<![0-9,])(?:%s)(?![0-9])' % '|'.join(re.escape(x) for x in num_forms(n))


def const_left(code):
    return bool(re.match(r'\s*\(?\s*-?(?:0x[0-9a-fA-F]+|\d+)\s*(<=|>=|<|>|==|!=)', code))


FLIP = {'<': '>', '>': '<', '<=': '>=', '>=': '<=', '==': '==', '!=': '!='}
NEG = {'<': '>=', '>=': '<', '>': '<=', '<=': '>', '==': '!=', '!=': '=='}


def refusal_comparison(atom):
    """(op, c) the box needs, normalised to <, >=, ==, != on integers: from the atom's operator, constant, side and value"""
    op = atom['op']; c = atom['const']
    if const_left(atom['code']): op = FLIP[op]
    if not atom['value']: op = NEG[op]
    if op == '<=': op, c = '<', c + 1
    if op == '>': op, c = '>=', c + 1
    return op, c


def number_regex(op, c):
    if op == '>=':
        return r'(?:%s or\b|at least %s|(?:%s) %s)' % (NUM(c), NUM(c), GT_WORDS, NUM(c - 1))
    if op == '<':
        return r'(?:(?:%s) %s|at most %s|%s or (?:less|fewer))' % (LT_WORDS, NUM(c), NUM(c - 1), NUM(c - 1))
    if op == '==':
        return r'(?<!not )(?<!other than )\b%s' % NUM(c)
    if op == '!=':
        return r'(?:not|other than) %s' % NUM(c) + ('|non-zero' if c == 0 else '')
    raise ValueError(op)


def phrase_ok(atom, text):
    """(ok, what was required) for one atom's check against a cell"""
    chk = atom.get('check')
    t = text
    if not chk: return True, None
    if chk == NUMBER_CHECK:
        op, c = refusal_comparison(atom)
        rx = number_regex(op, c)
        return bool(re.search(rx, t, re.I)), '%s %s %s' % (atom['var'], op, c)
    if chk.startswith('concept:'):
        name = chk.split(':', 1)[1]; rx = CONCEPTS[name][0 if atom['value'] else 1]
        return bool(re.search(rx, t, re.I)), '%s is %s (/%s/)' % (name, atom['value'], rx)
    if chk == 'rel':
        lhs, op, rhs = atom['rel']
        words = LT_WORDS if op == '<' else GT_WORDS
        ok = bool(re.search(words, t, re.I)) and all(re.search(x, t, re.I) for x in atom.get('tokens', []))
        return ok, '%s %s %s' % (lhs, op, rhs)
    raise ValueError(chk)


NUMBER_CHECK = 'number'


# ------------------------------------------------------------------ the finding's tables
def finding_tables(path):
    out = {}; lines = open(path, encoding='utf-8').read().splitlines(); i = 0
    while i < len(lines):
        m = re.match(r'<!-- table: (\w+) -->', lines[i])
        if m:
            name = m.group(1); i += 1
            while i < len(lines) and not lines[i].startswith('|'): i += 1
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', lines[i].strip())[1:-1]]); i += 1
            hdr = rows[0]; out[name] = [dict(zip(hdr, r)) for r in rows[2:]]
        else: i += 1
    return out


def catalogue(path):
    T = finding_tables(path); CAT = {}
    for tname in ('catalogue', 'prompts', 'notices'):
        for r in T.get(tname, []):
            CAT[r['id']] = dict(r, table=tname)
    return CAT


def cond_col(row):
    for c in ('condition [derived]', 'raised when [derived]', 'raised when'):
        if c in row: return c
    return None


def citations(text):
    """[(line, quote, polarity)] polarity False = the cell marks the cited test as false"""
    out = []; prev = 0
    for m in CITE.finditer(text):
        before = text[max(prev, m.start() - 40):m.start()]; after = text[m.end():m.end() + 20]
        neg = bool(NEG_BEFORE.search(before)) or bool(NEG_AFTER.search(after))
        out.append((int(m.group(1)), m.group(2), not neg)); prev = m.end()
    return out


# ------------------------------------------------------------------ part 1: the table against the code
class Code:
    def __init__(self, extract, dump=None):
        self.X = cflow.read_extract(extract); self.fns = cflow.functions(self.X)
        self.D = None
        if dump and os.path.exists(dump):
            self.D = open(dump, encoding='utf-8', errors='replace').read().split('\n')

    def line(self, n):
        if n in self.X: return self.X[n]
        if self.D is not None and 0 < n <= len(self.D): return self.D[n - 1]
        return None

    def fn(self, name): return cflow.fn(self.X, name, self.fns)


ALLOW = [r'^FUN_0042d750\(', r'^iVar\d+ = FUN_0042d750\(', r'^FUN_00405b00\(', r'^FUN_00405bc8\(', r'^FUN_00403458\(', r'^FUN_004028c4\(', r'^FUN_00402978\(',
         r'^return;', r'^goto \w+;', r'^\*(?:param_3|local_8|local_c) = 0;', r'^(?:iVar|uVar|sVar)\d+ = (?:extraout_\w+|0|DAT_004a0328);',
         r'^puStack_\w+ = ', r'^uVar\d+ = FUN_00449cd8\(', r'^cStack_5 = ', r'^iVar\d+ = 0;']


def allowed(stmt): return any(re.match(p, norm(stmt)) for p in ALLOW)


def guard_lines(code, g):
    f = code.fn(g['fn']); s = set(g.get('cite') or [])
    if g['line'] is not None:
        s.add(g['line'])
        if g['line'] in f.tests: s |= set(f.tests[g['line']]['span'])
    if g.get('flag'): s.add(g['flag']['set'])
    return s


def check_table(T, code):
    errs = []; n = [0]
    def ok(cond, row, msg):
        n[0] += 1
        if not cond: errs.append('%s: %s' % (row, msg))
        return cond
    # fields: each cited layout line says what the table says it does
    layout = open(LAYOUT, encoding='utf-8').read().split('\n') if os.path.exists(LAYOUT) else None
    for fd in T.get('fields', []):
        if layout is not None:
            ok(norm(fd['doc_quote']) in norm(layout[fd['doc_line'] - 1]), 'fields', '%s: docs/sav-layout-notes.md L%d does not say %r' % (fd['address'], fd['doc_line'], fd['doc_quote']))
    for r in T['rows']:
        rid = r['id']; f = code.fn(r['function']); call = r['call']
        ok('FUN_0042d750(' in (code.line(call) or ''), rid, 'the call line %d is a message-box call' % call)
        ok(cflow.function_of(code.X, call, code.fns) == r['function'], rid, 'the call line %d is in %s' % (call, r['function']))
        for k, alt in enumerate(r['paths']):
            tag = '%s path %d' % (rid, k + 1)
            by_reached = {}
            for g in alt:
                gf = code.fn(g['fn']); reached = g['reached'] or (call if g['fn'] == r['function'] else None)
                cites = g.get('cite') or []
                ok(len(cites) >= 1, tag, 'guard %s has a citation' % g['line'])
                for c in cites:
                    ok(code.line(c) is not None and norm(code.line(c)) != '', tag, 'citation L%s resolves' % c)
                if g['kind'] == 'dataflow':
                    for a in g['atoms']:
                        ok(norm(a['code']) in norm(code.line(g['line']) or ''), tag, 'dataflow atom %r is on L%s' % (a['code'], g['line']))
                    continue
                if g['kind'] == 'sc':
                    t = gf.test_of(call)
                    if not ok(t is not None and t == g['line'], tag, 'short-circuit guard: the call is in the condition of the test at %s (found %s)' % (g['line'], t)): continue
                    cond = norm(gf.tests[t]['cond'])
                    for a in g['atoms']:
                        p = cond.find(norm(a['code'])); q = cond.find('FUN_0042d750(')
                        if not ok(0 <= p < q, tag, 'sc atom %r precedes the call in the condition of L%s' % (a['code'], t)): continue
                        between = cond[p + len(norm(a['code'])):q]
                        mm = re.search(r'&&|\|\|', between)
                        need = (mm.group(0) == '&&') if mm else None
                        ok(need is not None and need == a['value'], tag, 'sc atom %r must be %s to reach the call (operator %s)' % (a['code'], need, mm.group(0) if mm else None))
                        check_atom(ok, tag, a, cond)
                    continue
                t = g['line']
                if not ok(t in gf.tests, tag, 'L%s is an if-test of %s' % (t, g['fn'])): continue
                cond = norm(gf.tests[t]['cond'])
                for a in g['atoms']: check_atom(ok, tag, a, cond)
                if g.get('flag'):
                    fl = g['flag']; st = norm(code.line(fl['set']) or '')
                    ok(re.match(r'^%s = %s;' % (re.escape(fl['name']), re.escape(fl['value'])), st), tag, 'flag %s is set to %s at L%s (%r)' % (fl['name'], fl['value'], fl['set'], st))
                    if g['kind'] != 'goto':
                        ok(re.search(r'\b%s\b' % re.escape(fl['name']), cond), tag, 'the test at L%s reads flag %s' % (t, fl['name']))
                if g['kind'] == 'goto':
                    th = gf.tests[t]['then']; gotos = [(l, lab) for l, lab in gf.gotos if th[0] <= l <= th[1]]
                    if not ok(len(gotos) == 1, tag, 'the then-branch of L%s is a goto' % t): continue
                    lab = gotos[0][1]; lab_line = gf.labels.get(lab)
                    if g.get('flag'):
                        ok(g['out'] is True and lab_line is not None and 0 <= g['flag']['set'] - lab_line <= 1, tag, 'goto %s at L%s lands on the set line of %s' % (lab, t, g['flag']['name']))
                    else:
                        ok(lab_line is not None and lab_line > call and g['out'] is False, tag, 'goto %s at L%s jumps over the box (label L%s), so the box needs the test false' % (lab, t, lab_line))
                    ctx_t = gf.ctx.get(t, ())
                    continue
                if g['kind'] == 'pre':
                    ok(gf.ctx.get(t, ()) == gf.ctx.get(call, ()) and t < call, tag, 'L%s is an if-statement before the box in the same block' % t)
                    continue
                by_reached.setdefault((g['fn'], reached), {})[t] = g['out']
                if g['role'] == 'context':
                    other = [c for c in all_calls(code, g['fn']) if code.fn(g['fn']).path(c).get(t) == (not g['out'])]
                    ok(not other, tag, 'context test L%s: its other branch has no box (found %s)' % (t, other))
            for (fname, reached), got in by_reached.items():
                if reached is None: continue
                want = code.fn(fname).path(reached)
                if reached != call:   # the tests the box's own path shares with this line are listed once, with the box
                    got = dict(got); got.update({t: o for t, o in by_reached.get((r['function'], call), {}).items() if t in want and fname == r['function']})
                ok(got == want, tag, 'the tests on the path to L%s are %s; the table lists %s' % (reached, want, got))
            if not any(g['kind'] == 'if' and (g['reached'] or call) == call for g in alt):
                ok(code.fn(r['function']).path(call) == {}, tag, 'no test is listed for the box but the code has %s' % code.fn(r['function']).path(call))
            ok(any(g.get('deciding') for g in alt) or r['table'] == 'prompts' and not alt, tag, 'a deciding test is named')
        # effects
        e = r.get('effect')
        if e:
            check_effect(ok, rid, code, r, e)
        a = r.get('answers')
        if a:
            check_answers(ok, rid, code, r, a)
    return n[0], errs


def check_atom(ok, tag, a, cond):
    c = norm(a['code'])
    if not ok(c in cond, tag, 'atom %r is in the condition %r' % (a['code'], cond[:120])): return
    if a['op']:
        ok(re.search(r'(?<![<>=!])%s(?![<>=])' % re.escape(a['op']), c) is not None, tag, 'atom %r has operator %s' % (a['code'], a['op']))
    if a['const'] is not None:
        lits = []
        for m in re.finditer(r"(?<![\w.])-?0x[0-9a-fA-F]+|(?<![\w.])-?\d+|'\\0'|'\\x01'", c):
            s = m.group(0)
            lits.append(0 if s == "'\\0'" else 1 if s == "'\\x01'" else int(s, 16) if '0x' in s.lower() else int(s))
        ok(a['const'] in lits, tag, 'atom %r compares with %s (literals %s)' % (a['code'], a['const'], lits))


def all_calls(code, fname):
    a, b = code.fns[fname]
    return [l for l in range(a, b + 1) if 'FUN_0042d750(' in code.X.get(l, '') and not code.X[l].lstrip().startswith(('void', 'undefined'))]


def exclusive(f, l1, l2):
    p1, p2 = f.path(l1), f.path(l2)
    return any(t in p2 and p2[t] != o for t, o in p1.items())


def block_of(f, line):
    """(first, last) lines of the innermost then/else block holding `line`"""
    ifs = [c for c in f.ctx.get(line, ()) if c[0] == 'if']
    if not ifs: return f.first, f.last
    t, o = ifs[-1][1], ifs[-1][2]
    return f.tests[t]['then' if o else 'else']


def check_effect(ok, rid, code, r, e):
    f = code.fn(r['function']); call = r['call']
    a, b = block_of(f, call)
    if e['kind'] == 'drop':
        for st in f.stmts_in(a, b):
            ok(allowed(st[2]), rid, 'drop: the box branch (L%d-L%d) only shows the box: %r' % (a, b, norm(st[2])[:90]))
        returns = any(norm(st[2]) == 'return;' and st[0] > call for st in f.stmts_in(a, b))
        for l in e['action']:
            ok(exclusive(f, call, l) or (returns and l > call), rid, 'drop: the acting line L%d is on another branch than the box (or the box returns first)' % l)
        if e.get('reports_failure'):
            ok(a <= e['reports_failure'] <= b and re.match(r'^\*(?:param_3|local_8|local_c) = 0;', norm(code.line(e['reports_failure']))), rid, 'drop: L%s reports the failure to the caller in the box branch' % e['reports_failure'])
    elif e['kind'] == 'clamp':
        L = e['loop']; ok(L in f.loops(e['flag_set']), rid, 'clamp: the flag set line L%s is in the loop at L%s' % (e['flag_set'], L))
        for l in e['action']: ok(L in f.loops(l), rid, 'clamp: the acting line L%d is in the loop at L%s' % (l, L))
        ok(L not in f.loops(call) and call > max(e['action'] + [e['flag_set']]), rid, 'clamp: the box comes after the loop')
    elif e['kind'] == 'notice_after_action':
        for l in e['action']:
            ok(l < call and all(f.path(call).get(t) == o for t, o in f.path(l).items()), rid, 'notice: L%d acts before the box on its path' % l)
    elif e['kind'] == 'info':
        for st in f.stmts_in(a, b):
            if st[0] > call: ok(allowed(st[2]), rid, 'info: after the box only reporting: %r' % norm(st[2])[:90])
    else:
        ok(False, rid, 'unknown effect kind %s' % e['kind'])


def check_answers(ok, rid, code, r, an):
    f = code.fn(r['function']); call = r['call']
    t = an['test'] if an['test'] in f.tests else f.test_of(an['test'])
    if not ok(t is not None, rid, 'answers: L%s is (in) a test' % an['test']): return
    cond = norm(f.tests[t]['cond'])
    ok(re.search(r'\w+ %s %d\b' % (re.escape(an['op']), an['yes']), cond) is not None, rid, 'answers: the test L%s compares the result %s %d' % (t, an['op'], an['yes']))
    then = f.tests[t]['then']
    if an['yes_kind'] == 'then':
        ok(an['op'] == '==', rid, 'answers: a then-branch Yes needs ==')
        for x in an['yes_actions']: ok(f.path(x['line']).get(t) is True, rid, 'answers: Yes action L%d is in the then-branch of L%d' % (x['line'], t))
        for x in an['other_actions']: ok(f.path(x['line']).get(t) is False, rid, 'answers: other action L%d is in the else-branch of L%d' % (x['line'], t))
    else:
        ok(an['op'] == '!=', rid, 'answers: after_return needs !=')
        leaves = [st for st in f.stmts_in(then[0], then[1]) if norm(st[2]).startswith(('return', 'goto'))]
        for x in an['yes_actions']:
            skipped = any(norm(st[2]) == 'return;' or (f.labels.get(norm(st[2])[5:-1].strip(), 0) > x['line']) for st in leaves)
            ok(x['line'] > max(f.tests[t]['span']) and t not in f.path(x['line']) and skipped, rid, 'answers: Yes action L%d comes after L%d, whose not-Yes branch leaves first' % (x['line'], t))
        for x in an['other_actions']: ok(f.path(x['line']).get(t) is True, rid, 'answers: other action L%d is in the not-Yes branch of L%d' % (x['line'], t))
    for x in an['after']:
        ok(x['line'] > max(f.tests[t]['span']) and t not in f.path(x['line']), rid, 'answers: L%d runs whatever the answer' % x['line'])
    ok(f.test_of(call) == t or f.path(an['test']) is not None, rid, 'answers: the test reads the box result')


# ------------------------------------------------------------------ part 2: the catalogue against the table
def rank(row):
    m = re.match(r'(\d+) of (\d+)', row.get('test order', ''))
    return int(m.group(1)) if m else None


def compare(T, CAT, code):
    mm = []
    def bad(kind, rid, msg): mm.append((kind, rid, msg))
    rows = {r['id']: r for r in T['rows']}
    n = [0]
    for rid, r in rows.items():
        if rid not in CAT:
            bad('missing row', rid, 'the catalogue has no row %s' % rid); continue
        c = CAT[rid]; col = cond_col(c); text = c.get(col, '') if col else ''
        f = code.fn(r['function'])
        fn_line = c.get('function:call line', '')
        n[0] += 1
        if fn_line != '%s:%d' % (r['function'], r['call']): bad('row', rid, 'function:call line %s vs %s:%d' % (fn_line, r['function'], r['call']))
        cites = citations(text)
        cols = [col] + [x for x in ('effect [derived]', 'answers [derived]', 'note') if x in c]
        # unresolved citations (all columns)
        for cc in cols:
            for ln, q, pol in citations(c.get(cc, '')):
                n[0] += 1
                L = code.line(ln)
                if L is None: bad('unresolved citation', rid, '%s: L%d is not in the extract%s' % (cc, ln, '' if code.D is None else ' or the dump'))
                elif norm(q) not in norm(L): bad('unresolved citation', rid, '%s: L%d does not read %r (it reads %r)' % (cc, ln, q[:60], norm(L)[:80]))
        guards = [g for alt in r['paths'] for g in alt]
        has_guards = any(g['role'] in ('decisive',) for g in guards)
        if has_guards:
            n[0] += 1
            if not cites: bad('missing citation', rid, '%s cites no line' % col)
        # missing citations of decisive tests
        k = rank(c); seen = set()
        for alt in r['paths']:
            for g in alt:
                if g['role'] != 'decisive' or g['kind'] in ('dataflow', 'pre') or g['line'] in seen: continue
                seen.add(g['line']); n[0] += 1
                lines = guard_lines(code, g) | ({g['reached']} if g['reached'] and g['reached'] != r['call'] else set())
                if g.get('flag'):   # a flag test is cited by citing a test that sets the flag
                    sets = {g['flag']['set'], g['flag'].get('via')} - {None}
                    for g2 in alt:
                        if g2['reached'] is not None and g2['reached'] in sets and g2 is not g: lines |= guard_lines(code, g2)
                if any(l in lines for l, _, _ in cites): continue
                covered = False
                if k is not None and not g.get('deciding'):
                    for r2 in rows.values():
                        k2 = rank(CAT.get(r2['id'], {}))
                        if r2['function'] == r['function'] and k2 is not None and k2 < k:
                            if any(g2['line'] == g['line'] and g2['role'] == 'decisive' and g2['out'] is not None and g2['out'] != g['out'] for a2 in r2['paths'] for g2 in a2):
                                covered = True
                if not covered:
                    bad('missing citation', rid, '%s does not cite the test L%s (%s, %s on the way to the box%s)' % (
                        col, g['line'], g['means'] or '; '.join(a['var'] for a in g['atoms']), 'true' if g['out'] else 'false',
                        '' if k is None else '; not the test of an earlier box'))
        # branch direction of each cited test
        for ln, q, pol in cites:
            exp = set()
            for g in guards:
                if g['role'] == 'structure' or g['kind'] == 'pre': continue
                gl = guard_lines(code, g)
                reached_cite = g['reached'] and ln == g['reached'] and ln != r['call']
                flag_cite = g.get('flag') and ln == g['flag']['set']
                if flag_cite or reached_cite: exp.add(True); continue
                if ln not in gl or g['out'] is None: continue
                on_line = [a for a in g['atoms'] if a.get('code') and norm(a['code']) in norm(code.line(ln) or '')]
                vals = set(a['value'] for a in on_line)
                exp.add(vals.pop() if len(vals) == 1 else g['out'])
            if not exp: continue
            n[0] += 1
            if pol not in exp:
                bad('branch direction', rid, 'L%d «%s» is cited as %s but the box needs it %s' % (
                    ln, q[:60], 'holding' if pol else 'failing (else / pass test / not)', ' or '.join('true' if x else 'false' for x in sorted(exp))))
        # condition: the deciding tests' comparisons are stated
        for ai, alt in enumerate(r['paths']):
            for g in alt:
                if not g.get('deciding'): continue
                checked = [a for a in g['atoms'] if a.get('check')]
                if not checked: continue
                anyone = (g['combine'] == 'or' and g['out']) or (g['combine'] == 'and' and g['out'] is False)
                res = [phrase_ok(a, text) for a in checked]
                n[0] += 1
                if anyone and not any(x[0] for x in res) or not anyone and not all(x[0] for x in res):
                    bad('condition', rid, '%s does not state %s (test L%s)' % (col, (' or ' if anyone else ' and ').join(w for okk, w in res if not okk), g['line']))
        # effect
        e = r.get('effect')
        if e and c['table'] == 'catalogue':
            n[0] += 1; cell = c.get('effect [derived]', '')
            kind = 'drop' if re.match(r'dropped', cell) else 'clamp' if re.match(r'clamped', cell) else None
            if kind != e['kind']: bad('effect', rid, 'the effect cell says %s, the code %s (%s)' % (kind, e['kind'], cell[:60]))
            if e.get('reports_failure'):
                n[0] += 1
                if '*param_3 = 0' not in cell: bad('effect', rid, 'the callee reports failure (L%s) but the cell does not say so' % e['reports_failure'])
        if e and c['table'] == 'notices':
            n[0] += 1; cell = c.get('note', '')
            kind = 'notice_after_action' if re.search(r'accepted', cell) else 'info' if re.search(r'information only', cell) else None
            if kind != e['kind']: bad('effect', rid, 'the note says %s, the code %s' % (kind, e['kind']))
        # answers
        an = r.get('answers')
        if an:
            cell = c.get('answers [derived]', '')
            n[0] += 1
            m = re.search(r'Yes \((?:result )?(\d+)\)', cell)
            if not m or int(m.group(1)) != an['yes']: bad('answer', rid, 'the cell does not say Yes (%d) acts (%s)' % (an['yes'], cell[:60]))
            n[0] += 1
            tl = set(f.tests[f.test_of(an['test']) or an['test']]['span']) if (f.test_of(an['test']) or an['test']) in f.tests else {an['test']}
            if not any(l in tl for l, _, _ in citations(cell)): bad('missing citation', rid, 'answers [derived] does not cite the answer test L%d' % an['test'])
            for x in an['yes_actions'] + an['after']:
                if not x.get('concept'): continue
                n[0] += 1
                rx = r'\b%s\b' % x['concept'][5:] if x['concept'].startswith('cite:') else ANSWER_CONCEPTS[x['concept']]
                if not re.search(rx, cell, re.I):
                    bad('answer', rid, '%s: the cell does not say %s (L%d: %s)' % ('Yes' if x in an['yes_actions'] else 'whatever the answer', x['concept'], x['line'], x['what']))
            if an['after'] and any(x.get('concept') for x in an['after']):
                n[0] += 1
                if re.search(r'No or Cancel: nothing happens', cell): bad('answer', rid, 'No or Cancel: the cell says nothing happens; the code does %s' % '; '.join('L%d %s' % (x['line'], x['what']) for x in an['after']))
    return n[0], mm


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def run(finding, predicates, extract, dump=None):
    T = json.load(open(predicates, encoding='utf-8'))
    code = Code(extract, dump)
    n1, errs = check_table(T, code)
    CAT = catalogue(finding)
    n2, mm = compare(T, CAT, code)
    return {'table_checks': n1, 'table_errors': errs, 'catalogue_checks': n2, 'mismatches': mm, 'rows': len(T['rows']), 'T': T}


def receipt(res, finding, predicates, extract, dump):
    kinds = {}
    for k, rid, msg in res['mismatches']: kinds[k] = kinds.get(k, 0) + 1
    out = ['predicate audit (issue #58) of %s' % os.path.relpath(finding, ROOT),
           'predicates %s sha256 %s' % (os.path.relpath(predicates, ROOT), sha(predicates)),
           'extract %s sha256 %s' % (os.path.relpath(extract, ROOT), sha(extract)),
           'finding sha256 %s' % sha(finding),
           'dump %s' % ('%s sha256 %s' % (os.path.basename(dump), sha(dump)) if dump and os.path.exists(dump) else 'not given (citations outside the extract are reported unresolved)'),
           'rows audited: %d (%s)' % (res['rows'], ', '.join('%s %d' % (t, sum(1 for r in res['T']['rows'] if r['table'] == t)) for t in ('catalogue', 'prompts', 'notices'))),
           'table checks: %d, table errors: %d' % (res['table_checks'], len(res['table_errors'])),
           'catalogue checks: %d, mismatches: %d' % (res['catalogue_checks'], len(res['mismatches'])),
           'mismatches by kind: ' + (', '.join('%s %d' % (k, v) for k, v in sorted(kinds.items())) or 'none'), '']
    out += ['TABLE %s' % e for e in res['table_errors']]
    out += ['MISMATCH [%s] %s: %s' % (k, rid, msg) for k, rid, msg in res['mismatches']]
    return '\n'.join(out).rstrip('\n') + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--finding', default=FINDING)
    ap.add_argument('--predicates', default=None)
    ap.add_argument('--extract', default=EXTRACT)
    ap.add_argument('--dump', default=os.environ.get('IC2_DUMP'))
    ap.add_argument('--out', default=os.path.join(DATA, 'predicate_audit_receipt.txt'))
    ap.add_argument('--stdout', action='store_true', help='print only; write no receipt')
    a = ap.parse_args()
    pred = a.predicates or latest(os.path.join(DATA, 'predicates.json'))
    res = run(a.finding, pred, a.extract, a.dump)
    text = receipt(res, a.finding, pred, a.extract, a.dump)
    sys.stdout.write(text)
    if not a.stdout:
        print('receipt:', os.path.relpath(write_new(a.out, text), ROOT))
    sys.exit(1 if res['table_errors'] or res['mismatches'] else 0)


if __name__ == '__main__':
    main()
