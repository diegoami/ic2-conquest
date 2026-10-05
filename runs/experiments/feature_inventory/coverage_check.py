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

class Ctx:
    """Everything the validators need, from tracked files."""
    def __init__(self):
        self.manifest = {}                      # screenshot name -> sha256, from SAVES.sha256 and MANIFEST-batch*.txt
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
        self.save_text = read('coverage.md') + read('tests/results.md') + read('saves/README.md') + ''.join(open(x, encoding='utf-8').read() for x in glob.glob(os.path.join(ROOT, 'findings', '*.md'))) + ' '.join(os.listdir(os.path.join(ROOT, 'saves')))
        self.cov_rows = []                      # (first column, status) of coverage.md tables
        for l in read('coverage.md').split('\n'):
            if l.startswith('|') and not l.startswith('|---'):
                c = [x.strip() for x in l.strip('|').split('|')]
                st = '✅' if '✅' in l else ''
                self.cov_rows.append((c[0], st, l))

def validate_rows(rows, ctx):
    """Strict tag validation. Returns a list of violation strings."""
    viol = []; hashes = collections.defaultdict(list)
    for i, r in rows.items():
        ev = r['evidence']; tag = r['tag']
        if tag not in ('[confirmed]', '[derived]', '[candidate]'): viol.append('%s: bad tag %r' % (i, tag)); continue
        if r['need'] not in ('needed', 'useful', 'cosmetic'): viol.append('%s: bad need %r' % (i, r['need']))
        shots = re.findall(r'FI_b\d_[A-Za-z0-9_]+\.png', ev)
        good_shot = False
        for s in shots:
            if s not in ctx.manifest: viol.append('%s: screenshot %s is not in the tracked manifest' % (i, s)); continue
            hashes[ctx.manifest[s]].append((i, s)); good_shot = True
        sav = [t for t in re.findall(r'[A-Za-z0-9_\-]+\.SAV', ev) if t in ctx.save_text]
        cov = False
        for m in re.finditer(r"C:§\d+ '([^']+)'", ev):
            name = m.group(1)
            if any(name.lower() in c[0].lower() and c[1] for c in ctx.cov_rows): cov = True
            else: viol.append("%s: coverage.md row %r not found with status ✅" % (i, name))
        if tag == '[confirmed]' and not (good_shot or sav or cov):
            viol.append('%s: [confirmed] without a manifest screenshot, a named save or a ✅ coverage.md row (a report or log citation is not confirmation)' % i)
        if tag == '[derived]' and not re.search(r'X:|form |forms |R:|H:|rules-digest|form_xrefs|help_topics', ev):
            viol.append('%s: [derived] without a function, form, report or help topic' % i)
        if tag == '[candidate]' and not ev.strip(): viol.append('%s: [candidate] with no evidence note' % i)
    for h, users in hashes.items():
        files = {s for i, s in users}
        if len(files) > 1 and not files <= ctx.same:
            viol.append('duplicate screenshot hash %s... cited as different screens: %s' % (h[:10], sorted(files)))
        names = {s for i, s in users}
        rowsets = {i for i, s in users}
        if len(rowsets) > 1 and len(names) == 1 and not names <= ctx.same:
            pass
    return viol

def check_news(news, lits):
    """news: [(id, template, literal, addrs, rows, src)]. lits: {addr: set(exact literals)}. Exact match against the named function only."""
    problems = []
    for nid, tmpl, lit, addrs, rws, src in news:
        if lit.startswith('SEED'): continue
        f = lit[1:-1] if lit.startswith('"') and lit.endswith('"') else lit
        ok = [a for a in addrs.split(',') if a.strip() and f in lits.get(a.strip(), set())]
        if not ok: problems.append('news %s: exact literal %r is not a literal of function(s) %s' % (nid, f, addrs))
    return problems

def run(rows=None, ctx=None, verbose=True):
    rows = rows if rows is not None else load_rows(); ctx = ctx or Ctx()
    rules = collections.defaultdict(list)
    for n, l in enumerate(open(os.path.join(DATA, 'coverage_map.cfg'), encoding='utf-8'), 1):
        if l.startswith('#') or not l.strip(): continue
        k, rx, rws, note = [x.strip() for x in l.rstrip('\n').split(' :: ')]
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
    news = []
    for l in open(os.path.join(DATA, 'news_templates.cfg'), encoding='utf-8'):
        if l.startswith('#') or not l.strip(): continue
        news.append([x.strip() for x in l.rstrip('\n').split(' :: ')])
    lines = []; tot = collections.OrderedDict(); problems = []
    def add(kind, key, status, rws, note):
        lines.append((kind, key, status, rws, note)); t = tot.setdefault(kind, collections.Counter()); t['total'] += 1; t[status] += 1
    for kind, key in entries:
        hit = next(((n, rws, note) for n, rx, rws, note in rules[kind] if rx.search(key)), None)
        if not hit: add(kind, key, 'UNACCOUNTED', '', ''); continue
        n, rws, note = hit
        if rws == 'EXCLUDED': add(kind, key, 'excluded', '', 'rule %d: %s' % (n, note)); continue
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
    used = {i for l in lines for i in l[3].split(',') if i}
    unused = sorted(set(rows) - used)
    g = collections.Counter()
    out = ['Feature inventory coverage check (battle excluded)',
           'inventory rows: %d  (%s)' % (len(rows), ', '.join('%s %d' % kv for kv in sorted(collections.Counter(r['tag'] for r in rows.values()).items()))), '',
           '%-12s %6s %7s %9s %11s' % ('kind', 'total', 'mapped', 'excluded', 'UNACCOUNTED')]
    for k, t in tot.items():
        out.append('%-12s %6d %7d %9d %11d' % (k, t['total'], t['mapped'], t['excluded'], t['UNACCOUNTED'])); g.update(t)
    out.append('%-12s %6d %7d %9d %11d' % ('ALL', g['total'], g['mapped'], g['excluded'], g['UNACCOUNTED']))
    out += ['', 'rows referenced by no entry (their evidence is a screenshot, a save or a report, not an extracted entry): %s' % unused,
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
