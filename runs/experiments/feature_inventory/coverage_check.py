#!/usr/bin/env python3
"""Recompute the coverage check of the feature inventory from TRACKED inputs only (no Ghidra dump, no game files, no research repo).

Entries: form classes, controls, menu items, toolbar buttons, .cnt topics, decoded .hlp topics, message-string functions, news templates,
stray exe strings, and the rules family (docs/rules-digest.md headings, coverage.md section 4 mechanics, research report titles).
Each is mapped through coverage_map.cfg / news_templates.cfg to inventory rows or to a stated exclusion. Rows are validated strictly.
Outputs are versioned (rule 6): a changed result is written as coverage_report.vN.txt / coverage_entries.vN.tsv, never over an old one.
Usage: coverage_check.py            compute; write a new version if the result changed
       coverage_check.py --check    compute and compare with the newest tracked version (exit 1 if different or not clean)"""
import csv, re, sys, os, collections, hashlib, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, latest, write_new
ROOT = os.path.normpath(os.path.join(DATA, '..', '..', '..', '..'))

def tsv(name):
    return list(csv.DictReader(open(latest(os.path.join(DATA, name)), encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))

def load_rows(path=None):
    rows = {}
    for l in open(path or os.path.join(DATA, 'inventory_rows.psv'), encoding='utf-8').read().split('\n')[1:]:
        if l.strip():
            f = l.split('|'); assert len(f) == 8, l[:60]
            rows[f[0]] = dict(zip(('id', 'group', 'name', 'what', 'pre', 'evidence', 'tag', 'need'), f))
    return rows

def read(p): return open(os.path.join(ROOT, p), encoding='utf-8', errors='replace').read()

SAVE_RX = re.compile(r'(?<![A-Za-z0-9_\-*])[A-Za-z0-9_\-]+\.SAV\b')
OWN_FINDING = '2026-10-05-player-facing-feature-inventory.md'

class Ctx:
    """Everything the validators need, from tracked files. The save index is built from artifacts independent of this inventory:
    saves/README.md and saves/, coverage.md, tests/results.md, other runs' SAVES.sha256, and findings other than this inventory's own."""
    def __init__(self):
        self.manifest = {}
        for l in open(os.path.join(DATA, 'SAVES.sha256')):
            f = l.split()
            if len(f) == 2 and f[1].endswith('.png'): self.manifest[f[1]] = f[0]
        for m in glob.glob(os.path.join(DATA, 'MANIFEST-batch*.txt')):
            for l in open(m):
                f = l.split()
                if len(f) == 2 and f[1].endswith('.png') and len(f[0]) == 64: self.manifest[f[1]] = f[0]
        self.same = set()
        for l in open(os.path.join(DATA, 'same_screen.cfg')):
            if l[0] != '#' and l.strip(): self.same.update(x.strip() for x in l.split(' :: ')[:2])
        src = [read('coverage.md'), read('tests/results.md'), read('saves/README.md'), ' '.join(os.listdir(os.path.join(ROOT, 'saves')))]
        for x in glob.glob(os.path.join(ROOT, 'findings', '*.md')):
            if os.path.basename(x) != OWN_FINDING: src.append(open(x, encoding='utf-8').read())
        for x in glob.glob(os.path.join(ROOT, 'runs', 'experiments', 'data', '*', 'SAVES.sha256')):
            if os.path.basename(os.path.dirname(x)) != 'run-exp-feature-inventory': src.append(open(x).read())
        self.saves = set(SAVE_RX.findall(' '.join(src)))
        self.cov = collections.defaultdict(list)   # (section, first cell) -> [has done status]
        sec = 0
        for l in read('coverage.md').split('\n'):
            m = re.match(r'## (\d+)\.', l)
            if m: sec = int(m.group(1))
            if l.startswith('|') and not l.startswith('|---'):
                c = [x.strip() for x in l.strip('|').split('|')]
                self.cov[(sec, c[0])].append('✅' in '|'.join(c[1:]))
        self.syms = {'entry'}
        for r in tsv('function_list.tsv'): self.syms.update((r['name'], r['symbol'], r['addr'])); 
        for l in open(latest(os.path.join(DATA, 'delphi_symbols.tsv'))):
            f = l.rstrip('\n').split('\t')
            if len(f) >= 2: self.syms.update((f[0], f[1]))
        self.syms.discard('')
        ctl = tsv('form_controls.tsv')
        self.forms = set()
        for r in ctl:
            self.forms.update((r['form'], r['name'])); self.forms.update(r['path'].split('/'))
        self.help = {r['title'].strip().lower() for r in tsv('help_topics.tsv')} | {r['title'].strip().lower() for r in tsv('help_contents_entries.tsv')}
        self.docs = {r['file'] for r in tsv('report_titles.tsv')}
        for d in ('findings', 'docs'):
            for x in glob.glob(os.path.join(ROOT, d, '*.md')):
                if os.path.basename(x) != OWN_FINDING: self.docs.add(os.path.basename(x))
        self.docs.update(('coverage.md', 'README.md', 'results.md'))
        self.findings = {os.path.basename(x) for x in glob.glob(os.path.join(ROOT, 'findings', '*.md')) if os.path.basename(x) != OWN_FINDING}
        rd = read('docs/rules-digest.md').split('\n')
        self.rd_head = [re.sub(r'^#+\s*', '', l) for l in rd if l.startswith('##')]

def clauses(ev):
    return [c.strip() for c in ev.split(';') if c.strip()]

def validate_rows(rows, ctx):
    """Strict validation of every citation kind. Returns violation strings."""
    viol = []; hashes = collections.defaultdict(list)
    for i, r in rows.items():
        ev = r['evidence']; tag = r['tag']
        if tag not in ('[confirmed]', '[derived]', '[candidate]'): viol.append('%s: bad tag %r' % (i, tag)); continue
        if r['need'] not in ('needed', 'useful', 'cosmetic'): viol.append('%s: bad need %r' % (i, r['need']))
        good_shot = False; good_sav = False; good_cov = False; resolved = 0
        for s in re.findall(r'FI_b\d_[A-Za-z0-9_]+\.png', ev):
            if s not in ctx.manifest: viol.append('%s: screenshot %s is not in the tracked manifest' % (i, s)); continue
            hashes[ctx.manifest[s]].append((i, s)); good_shot = True
        for t in SAVE_RX.findall(ev):
            if t in ctx.saves: good_sav = True
            else: viol.append('%s: save %s is in no independent artifact (saves/, coverage.md, tests/results.md, other runs\' hash lists, other findings)' % (i, t))
        for m in re.finditer(r"C:§(\d+) '([^']*)'", ev):
            sec, name = int(m.group(1)), m.group(2)
            hit = ctx.cov.get((sec, name))
            if not hit: viol.append("%s: coverage.md §%d has no row whose first cell is exactly %r" % (i, sec, name))
            elif len(hit) > 1: viol.append("%s: coverage.md §%d first cell %r is not unique (ambiguous)" % (i, sec, name))
            elif not hit[0]: viol.append("%s: coverage.md §%d row %r does not have status ✅" % (i, sec, name))
            else: good_cov = True
        if re.search(r'C:§\d+(?! \')', ev) and not re.search(r"C:§\d+ '", ev): viol.append('%s: bare C:§ citation (cite section and the exact first cell)' % i)
        for c in clauses(ev):
            if c.startswith('X:'):
                body = re.sub(r'\([^)]*\)', ' ', c[2:])
                items = [x for x in re.split(r'[,\s]+', body) if x and not x.startswith('0x') and x.lower() not in ('and', 'or')]
                if not items: viol.append('%s: empty X: citation' % i); continue
                bad = [x for x in items if x not in ctx.syms]
                if bad: viol.append('%s: X: target(s) not in the symbol/function lists: %s' % (i, bad))
                else: resolved += 1
            elif c.startswith('form ') or c.startswith('forms '):
                body = re.sub(r'\([^)]*\)', ' ', c.split(' ', 1)[1])
                toks = [x for x in re.split(r'[,\s]+', body) if x]
                first = [t for t in re.split(r'/', toks[0]) if t] if toks else []
                bad = [t for t in first if t not in ctx.forms]
                if c.startswith('forms '): bad += [t for t in toks if t not in ctx.forms]
                if not toks or bad: viol.append('%s: form citation target(s) unknown: %s' % (i, bad or 'none given'))
                else: resolved += 1
            elif c.startswith('H:'):
                qs = re.findall(r"'([^']+)'", c)
                bad = [q for q in qs if q.strip().lower() not in ctx.help]
                if not qs or bad: viol.append('%s: help topic(s) unknown: %s' % (i, bad or 'none quoted'))
                else: resolved += 1
        for t in re.findall(r'[A-Za-z0-9_\-]+\.md', ev):
            if t not in ctx.docs: viol.append('%s: unknown document %s' % (i, t))
            elif t != 'coverage.md': resolved += 1
        for m in re.finditer(r'rules-digest\.md §(\d+)(?: "([^"]+)")?', ev):
            if not any(h.startswith('%s.' % m.group(1)) for h in ctx.rd_head): viol.append('%s: rules-digest has no section %s' % (i, m.group(1)))
            if m.group(2) and not any(m.group(2).lower() in h.lower() for h in ctx.rd_head): viol.append('%s: rules-digest has no heading %r' % (i, m.group(2)))
        for m in re.finditer(r'F:(\d{4}-[A-Za-z0-9\-]+\.md)', ev):
            if m.group(1) not in ctx.findings: viol.append('%s: finding %s does not exist' % (i, m.group(1)))
        if tag == '[confirmed]' and not (good_shot or good_sav or good_cov):
            viol.append('%s: [confirmed] without a manifest screenshot, an independently indexed save or a ✅ coverage.md row (a report or log citation is not confirmation)' % i)
        if tag == '[derived]' and not resolved:
            viol.append('%s: [derived] without a resolvable function, form, help topic or document' % i)
        if tag == '[candidate]' and not ev.strip(): viol.append('%s: [candidate] with no evidence note' % i)
    for h, users in hashes.items():
        files = {s for i, s in users}
        if len(files) > 1 and not files <= ctx.same:
            viol.append('duplicate screenshot hash %s... cited as different screens: %s' % (h[:10], sorted(files)))
    return viol

def load_audit():
    """row_source_audit (newest version): row, source, line, quote, key. Returns list of dicts."""
    out = []
    for l in open(latest(os.path.join(DATA, 'row_source_audit.tsv')), encoding='utf-8').read().split('\n')[1:]:
        if l.strip():
            f = l.split('\t'); out.append(dict(zip(('row', 'source', 'line', 'quote', 'key'), f)))
    return out

def check_audit(rows, audit):
    """Every audited condition: the quote is on the stated line of a tracked file, and the row text carries the key."""
    prob = []
    for a in audit:
        r = rows.get(a['row'])
        if not r: prob.append('audit names missing row %s' % a['row']); continue
        if not a['source'].startswith('R:'):
            try: line = read(a['source']).split('\n')[int(a['line']) - 1]
            except Exception as e: prob.append('audit %s: cannot read %s:%s' % (a['row'], a['source'], a['line'])); continue
            if a['quote'] not in line: prob.append('audit %s: quote %r not on %s:%s' % (a['row'], a['quote'], a['source'], a['line']))
        if not re.search(a['key'], r['what'] + ' ' + r['pre'], re.I): prob.append('audit %s: condition %r (key %r) is missing from the row' % (a['row'], a['quote'], a['key']))
    return prob

def check_news(news, lits):
    """news: [(id, template, literal, addrs, rows, src)]. lits: {addr: set(exact literals)}. Exact match against the named function only."""
    problems = []
    for nid, tmpl, lit, addrs, rws, src in news:
        if lit.startswith('SEED'): continue
        f = lit[1:-1] if lit.startswith('"') and lit.endswith('"') else lit
        ok = [a for a in addrs.split(',') if a.strip() and f in lits.get(a.strip(), set())]
        if not ok: problems.append('news %s: exact literal %r is not a literal of function(s) %s' % (nid, f, addrs))
    return problems

def run(rows=None, ctx=None, cfg_text=None, audit=None, extra_entries=()):
    rows = rows if rows is not None else load_rows(); ctx = ctx or Ctx()
    rules = collections.defaultdict(list); problems = []
    cfg = cfg_text if cfg_text is not None else open(os.path.join(DATA, 'coverage_map.cfg'), encoding='utf-8').read()
    for n, l in enumerate(cfg.split('\n'), 1):
        if l.startswith('#') or not l.strip(): continue
        parts = [x.strip() for x in re.split(r'\s::\s|\s::$', l.rstrip('\n'))]   # tolerates a trailing empty field
        if len(parts) < 4: parts += [''] * (4 - len(parts))
        k, rx, rws, note = parts[:4]
        if not note.strip(): problems.append('cfg line %d: empty reason (every rule, and every exclusion, needs a stated reason)' % n)
        rules[k].append((n, re.compile(rx), rws, note))
    ctl = tsv('form_controls.tsv'); entries = []
    for f in sorted({r['form'] for r in ctl}): entries.append(('form', 'form:' + f))
    for r in ctl:
        label = r['caption'] or r['hint']
        entries.append(('control', 'control:%s|%s|%s|%s' % (r['form'], r['class'], r['name'], label)))
        if r['class'] == 'TMenuItem' and r['caption'] and r['caption'] != '-': entries.append(('menu', 'menu:%s|%s' % (r['name'], r['caption'])))
        if r['class'] == 'TSpeedButton': entries.append(('toolbar', 'toolbar:%s|%s|%s' % (r['form'], r['name'], label)))
    for r in tsv('help_contents_entries.tsv'): entries.append(('help_cnt', 'help_cnt:%s|%s' % (r['path'], r['context'])))
    for r in tsv('help_topics.tsv'): entries.append(('help_topic', 'help_topic:%s|%s' % (r['order'], r['title'])))
    byfn = collections.OrderedDict(); lits = collections.defaultdict(set)
    for r in tsv('dump_string_literals.tsv'):
        lit = r['literal'].replace("\\'", "'")
        lits[r['addr']].add(lit)
        if int(r['addr'], 16) < 0x436000: continue
        if re.search('[A-Za-z]', lit): byfn.setdefault((r['addr'], r['symbol'] or r['function']), []).append(r['literal'])
    for (a, s), ls in byfn.items(): entries.append(('msgfn', 'msgfn:%s|%s|%s' % (a, s, ' / '.join(dict.fromkeys(ls))[:200])))
    alllits = {l.replace("\\'", "'") for ls in byfn.values() for l in ls}
    for r in tsv('exe_strings.tsv'):
        if r['kind'] == 'ansistring' and int(r['file_offset'], 16) >= 0x36f00 and r['text'] not in alllits: entries.append(('string', 'string:' + r['text']))
    for l in read('docs/rules-digest.md').split('\n'):
        m = re.match(r'#{2,3} (.*)', l)
        if m: entries.append(('rule_head', 'rule_head:' + m.group(1).strip()))
    sec = False
    for l in read('coverage.md').split('\n'):
        if l.startswith('## 4'): sec = True; continue
        if l.startswith('## ') and sec: break
        if sec and l.startswith('|') and not l.startswith('|---') and not l.startswith('| Mechanic'):
            entries.append(('mechanic', 'mechanic:' + l.strip('|').split('|')[0].strip()))
    for r in tsv('report_titles.tsv'): entries.append(('report', 'report:%s|%s' % (r['file'], r['title'])))
    entries += list(extra_entries)
    news = []
    for l in open(os.path.join(DATA, 'news_templates.cfg'), encoding='utf-8'):
        if l.startswith('#') or not l.strip(): continue
        news.append([x.strip() for x in l.rstrip('\n').split(' :: ')])
    lines = []; tot = collections.OrderedDict()
    def add(kind, key, status, rws, note):
        lines.append((kind, key, status, rws, note)); t = tot.setdefault(kind, collections.Counter()); t['total'] += 1; t[status] += 1
    for kind, key in entries:
        hit = next(((n, rws, note) for n, rx, rws, note in rules[kind] if rx.search(key)), None)
        if not hit: add(kind, key, 'UNACCOUNTED', '', ''); continue
        n, rws, note = hit
        if rws == 'EXCLUDED':
            if not note.strip(): problems.append('entry %s excluded with an empty reason (rule %d)' % (key[:60], n))
            add(kind, key, 'excluded', '', 'rule %d: %s' % (n, note)); continue
        ids = [x.strip() for x in rws.split(',')]
        bad = [i for i in ids if i not in rows]
        if bad: problems.append('rule %d names missing rows %s' % (n, bad))
        add(kind, key, 'mapped', ','.join(ids), 'rule %d: %s' % (n, note))
    problems += check_news(news, lits)
    for nid, tmpl, lit, addrs, rws, src in news:
        ids = [x.strip() for x in rws.split(',')]
        bad = [i for i in ids if i not in rows]
        if bad: problems.append('news %s names missing rows %s' % (nid, bad))
        add('news', 'news:%s|%s' % (nid, tmpl), 'mapped', ','.join(ids), 'exact literal in function ' + addrs)
    viol = validate_rows(rows, ctx)
    aud = load_audit() if audit is None else audit
    problems += check_audit(rows, aud)
    used = {i for l in lines for i in l[3].split(',') if i}
    unused = sorted(set(rows) - used)
    g = collections.Counter()
    out = ['Feature inventory coverage check (battle excluded)',
           'inventory rows: %d  (%s)' % (len(rows), ', '.join('%s %d' % kv for kv in sorted(collections.Counter(r['tag'] for r in rows.values()).items()))), '',
           '%-12s %6s %7s %9s %11s' % ('kind', 'total', 'mapped', 'excluded', 'UNACCOUNTED')]
    for k, t in tot.items():
        out.append('%-12s %6d %7d %9d %11d' % (k, t['total'], t['mapped'], t['excluded'], t['UNACCOUNTED'])); g.update(t)
    out.append('%-12s %6d %7d %9d %11d' % ('ALL', g['total'], g['mapped'], g['excluded'], g['UNACCOUNTED']))
    out += ['', 'audited conditions: %d over %d rows (each quote is on its source line and each key is in the row)' % (len(aud), len({a['row'] for a in aud})), 'rows referenced by no entry (their evidence is a screenshot, a save or a report, not an extracted entry): %s' % unused,
            'rule problems: %s' % (problems or 'none'), 'tag/evidence violations: %s' % (viol or 'none')]
    report = '\n'.join(out) + '\n'
    ent = 'kind\tkey\tstatus\trows\tnote\n' + ''.join('\t'.join(x) + '\n' for x in lines)
    clean = not (g['UNACCOUNTED'] or problems or viol)
    return report, ent, clean

if __name__ == '__main__':
    report, ent, clean = run()
    rp, ep = os.path.join(DATA, 'coverage_report.txt'), os.path.join(DATA, 'coverage_entries.tsv')
    try: same = open(latest(rp)).read() == report and open(latest(ep)).read() == ent
    except FileNotFoundError: same = False
    if '--check' in sys.argv:
        print('tracked output identical' if same else 'tracked output DIFFERS'); print(report); sys.exit(0 if (same and clean) else 1)
    if not same:
        print('wrote', write_new(rp, report), write_new(ep, ent))
    else: print('unchanged (newest tracked version identical)')
    print(report); sys.exit(0 if clean else 1)
