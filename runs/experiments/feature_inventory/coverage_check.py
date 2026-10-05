#!/usr/bin/env python3
"""Recompute the coverage check of the feature inventory.

Every source entry (form class, control, menu item, toolbar button, .cnt topic, decoded .hlp topic, message-string function,
news template, exe string literal) is built from the tracked extracts in runs/experiments/data/run-exp-feature-inventory/ and
mapped through coverage_map.cfg / news_templates.cfg to inventory rows (inventory_rows.psv) or to a stated exclusion.
Writes coverage_entries.tsv and coverage_report.txt beside the extracts; exit status 1 if anything is unaccounted for.
Usage: python3 runs/experiments/feature_inventory/coverage_check.py [--check]   (--check: do not write, compare with the tracked output)"""
import csv, re, sys, os, collections
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'run-exp-feature-inventory')
D = os.path.normpath(D)
DUMP = '/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt'

def tsv(name): return list(csv.DictReader(open(os.path.join(D, name), encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))

# ---- rows
rows = {}
for l in open(os.path.join(D, 'inventory_rows.psv'), encoding='utf-8').read().split('\n')[1:]:
    if not l.strip(): continue
    f = l.split('|')
    assert len(f) == 8, l[:60]
    rows[f[0]] = dict(zip(('id', 'group', 'name', 'what', 'pre', 'evidence', 'tag', 'need'), f))

# ---- rules
rules = collections.defaultdict(list)
for n, l in enumerate(open(os.path.join(D, 'coverage_map.cfg'), encoding='utf-8'), 1):
    if l.startswith('#') or not l.strip(): continue
    k, rx, rws, note = [x.strip() for x in l.rstrip('\n').split(' :: ')]
    rules[k].append((n, re.compile(rx), rws, note))

def classify(kind, key):
    for n, rx, rws, note in rules[kind]:
        if rx.search(key):
            return n, rws, note
    return None, None, None

entries = []   # (kind, key)
# forms and controls
ctl = tsv('form_controls.tsv')
for f in sorted({r['form'] for r in ctl}): entries.append(('form', 'form:' + f))
for r in ctl:
    label = r['caption'] or r['hint']
    entries.append(('control', 'control:%s|%s|%s|%s' % (r['form'], r['class'], r['name'], label)))
    if r['class'] == 'TMenuItem' and r['caption'] and r['caption'] != '-':
        entries.append(('menu', 'menu:%s|%s' % (r['name'], r['caption'])))
    if r['class'] == 'TSpeedButton':
        entries.append(('toolbar', 'toolbar:%s|%s|%s' % (r['form'], r['name'], label)))
# help
for r in tsv('help_contents_entries.tsv'):
    entries.append(('help_cnt', 'help_cnt:%s|%s' % (r['path'], r['context'])))
for r in tsv('help_topics.tsv'):
    entries.append(('help_topic', 'help_topic:%s|%s' % (r['order'], r['title'])))
# message functions (game code only: below 0x436000 is the VCL/RTL)
byfn = collections.OrderedDict()
for r in tsv('dump_string_literals.tsv'):
    if int(r['addr'], 16) < 0x436000: continue
    byfn.setdefault((r['addr'], r['symbol'] or r['function']), []).append(r['literal'])
for (a, s), lits in byfn.items():
    entries.append(('msgfn', 'msgfn:%s|%s|%s' % (a, s, ' / '.join(dict.fromkeys(lits))[:200])))
# exe ansistring literals of the game range must each be a literal of a mapped function (or have a string rule)
alllits = {l.replace("\\'", "'") for ls in byfn.values() for l in ls}
for r in tsv('exe_strings.tsv'):
    if r['kind'] == 'ansistring' and int(r['file_offset'], 16) >= 0x36f00 and r['text'] not in alllits:
        entries.append(('string', 'string:' + r['text']))
# news templates
dump_text = open(DUMP, encoding='latin-1').read() if os.path.exists(DUMP) else ''
news = []
for l in open(os.path.join(D, 'news_templates.cfg'), encoding='utf-8'):
    if l.startswith('#') or not l.strip(): continue
    news.append([x.strip() for x in l.rstrip('\n').split(' :: ')])

lines = []; tot = collections.OrderedDict(); problems = []
def add(kind, key, status, rws, note):
    lines.append((kind, key, status, rws, note))
    t = tot.setdefault(kind, collections.Counter()); t['total'] += 1; t[status] += 1
for kind, key in entries:
    n, rws, note = classify(kind, key)
    if n is None:
        add(kind, key, 'UNACCOUNTED', '', ''); continue
    if rws == 'EXCLUDED': add(kind, key, 'excluded', '', 'rule %d: %s' % (n, note)); continue
    ids = [x.strip() for x in rws.split(',')]
    bad = [i for i in ids if i not in rows]
    if bad: problems.append('rule %d names missing rows %s' % (n, bad))
    add(kind, key, 'mapped', ','.join(ids), 'rule %d: %s' % (n, note))
tsvals = {r['literal'].replace("\\'", "'") for r in tsv('dump_string_literals.tsv')}
for nid, tmpl, frag, rws, src in news:
    key = 'news:%s|%s' % (nid, tmpl)
    ids = [x.strip() for x in rws.split(',')]
    bad = [i for i in ids if i not in rows]
    if bad: problems.append('news %s names missing rows %s' % (nid, bad))
    if frag.startswith('SEED'):
        how = 'DAT data (report)'
    else:
        f = frag.strip('"')
        if any(f in t for t in tsvals): how = 'dump_string_literals.tsv'
        elif ('"%s"' % f) in dump_text or (f in dump_text): how = 'Ghidra dump (raw search)'
        else:
            how = 'NOT FOUND'; problems.append('news %s: fragment %r not found as a string literal' % (nid, f))
    add('news', key, 'mapped', ','.join(ids), 'literal found in: ' + how)
# help topics that the .cnt names must resolve to a decoded topic title (information)
topics = {r['title'].strip().lower() for r in tsv('help_topics.tsv')}
unres = []
for r in tsv('help_contents_entries.tsv'):
    if r['context']:
        t = r['title'].strip().lower()
        if t not in topics and t.replace('s', '') not in {x.replace('s', '') for x in topics} and t not in ('area map', 'unit map', 'introduction', 'battle'):
            unres.append(r['path'])
# row sanity: tags earned by their evidence
viol = []
for i, r in rows.items():
    ev = r['evidence']
    if r['tag'] not in ('[confirmed]', '[derived]', '[candidate]'): viol.append('%s: bad tag %s' % (i, r['tag']))
    if r['tag'] == '[confirmed]' and not re.search(r'SS:FI_|\.SAV|C:§|F:20|tests/results\.md|explore/', ev): viol.append('%s: [confirmed] without a save, screenshot or coverage row' % i)
    if r['tag'] == '[derived]' and not re.search(r'X:|form |forms |R:|H:|rules-digest|form_xrefs|help_topics', ev): viol.append('%s: [derived] without a function, form, report or help topic' % i)
    if r['need'] not in ('needed', 'useful', 'cosmetic'): viol.append('%s: bad need %s' % (i, r['need']))
used = set()
for l in lines:
    for i in l[3].split(','):
        if i: used.add(i)
unused = sorted(set(rows) - used)

out = []
out.append('Feature inventory coverage check (battle excluded)')
out.append('inventory rows: %d  (%s)' % (len(rows), ', '.join('%s %d' % (k, v) for k, v in sorted(collections.Counter(r['tag'] for r in rows.values()).items()))))
out.append('')
out.append('%-12s %6s %7s %9s %11s' % ('kind', 'total', 'mapped', 'excluded', 'UNACCOUNTED'))
g = collections.Counter()
for k, t in tot.items():
    out.append('%-12s %6d %7d %9d %11d' % (k, t['total'], t['mapped'], t['excluded'], t['UNACCOUNTED']))
    g.update(t)
out.append('%-12s %6d %7d %9d %11d' % ('ALL', g['total'], g['mapped'], g['excluded'], g['UNACCOUNTED']))
out.append('')
out.append('help_cnt entries whose title is not a decoded topic title (information only): %d %s' % (len(unres), unres))
out.append('rows referenced by no entry: %s' % unused)
out.append('rule problems: %s' % (problems or 'none'))
out.append('tag/evidence violations: %s' % (viol or 'none'))
report = '\n'.join(out) + '\n'
ent = 'kind\tkey\tstatus\trows\tnote\n' + ''.join('\t'.join(x) + '\n' for x in lines)
if '--check' in sys.argv:
    same = open(os.path.join(D, 'coverage_report.txt')).read() == report and open(os.path.join(D, 'coverage_entries.tsv')).read() == ent
    print('tracked output identical' if same else 'tracked output DIFFERS'); print(report)
else:
    open(os.path.join(D, 'coverage_report.txt'), 'w').write(report)
    open(os.path.join(D, 'coverage_entries.tsv'), 'w').write(ent)
    print(report)
sys.exit(1 if (g['UNACCOUNTED'] or problems or viol) else 0)
