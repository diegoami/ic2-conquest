#!/usr/bin/env python3
"""Claims audit of findings/2026-10-05-end-of-game-screens.md.

Every claimed value in the finding's tables (marked `<!-- table: NAME -->`) is read from the finding and compared with a value RECOMPUTED from the sources:
the raw saves (artifacts folder, fetched from the release by fetch_archive.py), the tracked code extract (thresholds, literals and cited lines), the tracked
memory readings (states_*.jsonl, ocr_*.jsonl) and the tracked per-label OCR (ocr_labels.jsonl). Nothing the finding claims is typed in here.

  python3 claims_audit.py [--finding F] [--artifacts DIR] [--data DIR] [--out FILE]

Exit status 0 only with 0 mismatches. The output is written to a new versioned file beside the other tracked outputs (never overwritten)."""
import sys, os, re, json, glob, hashlib, difflib, struct, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
ROOT = paths.ROOT
sys.path.insert(0, ROOT)

ap = argparse.ArgumentParser()
ap.add_argument('--finding', default=os.path.join(ROOT, 'findings', '2026-10-05-end-of-game-screens.md'))
ap.add_argument('--artifacts', default=paths.ART)
ap.add_argument('--data', default=paths.DATA)
ap.add_argument('--out', default=None)
ap.add_argument('--quiet', action='store_true')
args = ap.parse_args()
ART = args.artifacts.rstrip('/') + '/'
DATA = args.data.rstrip('/') + '/'
SAVES = ART + 'saves/'
import fmt                                       # noqa: E402  (after paths)
from common import versions, latest, write_new    # noqa: E402
CODE = fmt.use(latest(os.path.join(DATA, 'code_extract_end_of_game.txt')))     # literals, thresholds and formatter constants come from the extract under --data
from harness.driver import NATIONS              # noqa: E402  (the nation records' address in memory: the code's DAT_ addresses are checked against it)
HUMAN_OFF = fmt.NATION_FIELDS['human'][0]

checks = 0; bad = []
def check(name, cond, detail=''):
    global checks
    checks += 1
    if not cond: bad.append('%s: %s' % (name, detail))
    return cond

sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

# ------------------------------------------------------------------ the finding's tables
def tables(path):
    out = {}; lines = open(path, encoding='utf-8').read().splitlines(); i = 0
    while i < len(lines):
        m = re.match(r'<!-- table: (\w+) -->', lines[i])
        if m:
            name = m.group(1); i += 1
            while i < len(lines) and not lines[i].startswith('|'): i += 1
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip().replace('`', '') for c in lines[i].strip().strip('|').split('|')]); i += 1
            hdr = rows[0]; body = [r for r in rows[2:]]
            out[name] = [dict(zip(hdr, r)) for r in body]
            for r in body: check('table %s row width' % name, len(r) == len(hdr), str(r)[:80])
        else: i += 1
    return out

def num(s):
    """'2,577,000' -> 2577000, '- 30,000' -> -30000"""
    return int(s.replace(',', '').replace(' ', ''))

T = tables(args.finding)
for need in ('rerun', 'windows', 'after_state', 'after_game', 'staging', 'start', 'code', 'counts'):
    check('table present: ' + need, need in T and T[need], need)

# ------------------------------------------------------------------ the code extract
X = fmt.extract_lines(latest(os.path.join(DATA, 'code_extract_end_of_game.txt')))
for r in T.get('code', []):
    line = int(r['line']); q = fmt.norm(r['quote'])
    check('code line %d quotes %r' % (line, q), line in X and q in fmt.norm(X[line]), X.get(line, '<no such line>'))

def code_const(pat, line):
    m = re.search(pat, X[line]); return m
# the thresholds are READ from the extract (fmt.Code); the window's tests and the turn-start tests must agree with each other
check('thresholds: 250 BC is the same year in the window and in the turn-start test', CODE.year_end == CODE.t_year, '%s %s' % (CODE.year_end, CODE.t_year))
check('thresholds: victory below %d in the window, above %d at turn start' % (CODE.cities_win, CODE.t_cities), CODE.cities_win == CODE.t_cities + 1)
check('thresholds: unity below the same value in the window and at turn start', CODE.unity_min == CODE.t_unity)
check('thresholds: years in power = %d - year, short time from year %d' % (CODE.years_base, CODE.short_year), CODE.years_base == CODE.short_year + 1)

# ------------------------------------------------------------------ raw readings
def jsonl(pattern, newest=False):
    rows = []
    for f in sorted(glob.glob(DATA + pattern)):
        for l in open(f): rows.append(json.loads(l))
    return rows
STATES = {}
for f in sorted(glob.glob(DATA + 'states_*.jsonl')):
    STATES[os.path.basename(f)] = [json.loads(l) for l in open(f)]
OCRR = jsonl('ocr_b*.jsonl')
OCRL = {}
for f in sorted(glob.glob(DATA + 'ocr_labels*.jsonl')):
    for l in open(f):
        o = json.loads(l); OCRL[o['png']] = o            # the newest file wins (names sort v2 after the base file)

def state_of(spec):
    """MEM:states_bN.jsonl#tag/step -> the recorded state dict"""
    f, key = spec[4:].split('#'); tag, step = key.split('/')
    for d in STATES[f]:
        if d['tag'] == tag and d['step'] == step: return d
    raise KeyError(spec)

def save_fields(name, seat):
    p = SAVES + name if os.path.exists(SAVES + name) else SAVES + 'inputs/' + name
    if not os.path.exists(p): p = os.path.join(ROOT, 'saves', name)
    return fmt.nation_fields(open(p, 'rb').read(), seat)

def window_inputs(src, seat):
    """The numbers THumanFalls_InitializeForm reads, from the cited source -> dict (names as fmt.window_texts)."""
    if src.startswith('AUTO:'):
        c = save_fields(src[5:], seat)
        check('autosave of %s is the fallen seat\'s turn start' % src, c['current_nation'] == seat, str(c['current_nation']))
        return dict(nation=c['name'], leader=c['leader'], year=c['year'], pop_start=c['wealth_start'], cities_start=c['cities_start'], money_start=c['treasury_start'],
                    pop_now=c['wealth'], cities_now=c['cities'], money_now=c['treasury'], conquered_by=c['conquered_by'], unity=c['unity'], names=c['names'])
    if src.startswith('MEM:'):
        d = state_of(src); st = d['seats'][str(seat)]
        return dict(nation=st['name'], leader=st['leader'], year=d['calendar']['year_bc'], pop_start=st['wealth_start'], cities_start=st['cities_start'],
                    money_start=st['treasury_start'], pop_now=st['wealth'], cities_now=st['cities'], money_now=st['treasury'], conquered_by=st['conquered_by'],
                    unity=st['unity'], names=None)
    if src.startswith('CAPTURE:'):
        files, cityspec, memspec = src[8:].split('#', 2)
        bf, af = files.split('+'); cname = cityspec.split('=')[1]
        b = save_fields(bf, seat); a = save_fields(af, seat)
        pb = open(SAVES + bf, 'rb').read(); pa = open(SAVES + af, 'rb').read()
        from state import sav as SAV
        cb = [c for c in SAV.parse(pb)['cities'] if c['name'] == cname][0]; ca = [c for c in SAV.parse(pa)['cities'] if c['name'] == cname][0]
        check('capture: %s changed owner from %d' % (cname, seat), cb['owner'] == seat and ca['owner'] == a['conquered_by'] and a['conquered_by'] != seat, '%s %s' % (cb['owner'], ca['owner']))
        # FUN_0044bb18 (:50183-50185): loser wealth -= pop x 3000, loser city count -= 1; both before FUN_0044c528 annexes the rest
        pop_now = b['wealth'] - ca['pop'] * CODE.capture_wealth_mult; cities_now = b['cities'] - 1
        mem = state_of('MEM:' + memspec)['seats'][str(seat)]
        check('capture: wealth %d - %d x %d = %d equals the memory reading %d' % (b['wealth'], ca['pop'], CODE.capture_wealth_mult, pop_now, mem['wealth']), pop_now == mem['wealth'])
        check('capture: city count %d - 1 = %d equals the memory reading %d' % (b['cities'], cities_now, mem['cities']), cities_now == mem['cities'])
        check('capture: treasury unchanged %d == memory %d' % (b['treasury'], mem['treasury']), b['treasury'] == mem['treasury'])
        check('capture: the loser is left with %d cities, below the conquest threshold %d read from the extract' % (cities_now, CODE.conquest_below), cities_now < CODE.conquest_below)
        check('capture: the loser now carries conquered_by in the after save', a['conquered_by'] == 0)
        return dict(nation=b['name'], leader=b['leader'], year=b['year'], pop_start=b['wealth_start'], cities_start=b['cities_start'], money_start=b['treasury_start'],
                    pop_now=pop_now, cities_now=cities_now, money_now=b['treasury'], conquered_by=a['conquered_by'], unity=b['unity'], names=b['names'])
    raise ValueError(src)

# ------------------------------------------------------------------ windows
LABELS = ['lbl_result1', 'lbl_result2', 'lbl_changes', 'lbl_nat1', 'lbl_pop1', 'lbl_cities1', 'lbl_money1', 'lbl_nat2', 'lbl_pop2', 'lbl_cities2', 'lbl_money2']
shots_seen = set(); FULL_SEEN = []
for r in T.get('windows', []):
    wid = r['id']; seat = int(r['seat']); src = r['source']
    w = window_inputs(src, seat)
    conq_name = None
    if w['conquered_by'] >= 0:
        names = w['names'] or save_fields('EOG_2h_base_AUTO0720.SAV', 0)['names']
        conq_name = names[w['conquered_by']]
    t = fmt.window_texts(w['nation'], w['leader'], w['year'], w['pop_start'], w['cities_start'], w['money_start'], w['pop_now'], w['cities_now'], w['money_now'],
                         conq_name, w['conquered_by'], w['unity'])
    # claimed cells against the recomputed texts
    check('%s lbl_result2 (exact)' % wid, r['lbl_result2'] == t['lbl_result2'], '%r vs %r' % (r['lbl_result2'], t['lbl_result2']))
    check('%s lbl_changes (exact, spacing included)' % wid, r['lbl_changes'] == t['lbl_changes'], '%r vs %r' % (r['lbl_changes'], t['lbl_changes']))
    if src.startswith(('AUTO:', 'MEM:')):          # the state the window shows satisfies at least one turn-start condition (thresholds read from the extract)
        fired = CODE.fires(w['pop_now'], w['money_now'], w['unity'], w['cities_now'], w['year'])
        check('%s a turn-start condition holds: %s' % (wid, fired), bool(fired))
    for col, key, tgt in (('pop start', 'pop_start', 'lbl_pop1'), ('pop now', 'pop_now', 'lbl_pop2'), ('treasury start', 'money_start', 'lbl_money1'), ('treasury now', 'money_now', 'lbl_money2')):
        check('%s %s' % (wid, col), num(r[col]) == w[key], '%s vs %s' % (r[col], w[key]))
    check('%s cities start' % wid, int(r['cities start']) == w['cities_start'], '%s vs %s' % (r['cities start'], w['cities_start']))
    check('%s cities now' % wid, int(r['cities now']) == w['cities_now'], '%s vs %s' % (r['cities now'], w['cities_now']))
    # start values: recorded at New Game and frozen: they equal the base save's
    base = r['base save']; bw = save_fields(base, seat)
    check('%s start values equal the base save %s' % (wid, base), (bw['wealth_start'], bw['treasury_start'], bw['cities_start']) == (w['pop_start'], w['money_start'], w['cities_start']),
          str((bw['wealth_start'], bw['treasury_start'], bw['cities_start'])))
    # the screenshot: file hash, per-label OCR
    png, pre = re.match(r'(\S+) \((\w+)\)', r['screenshot (sha256 prefix)']).groups()
    shots_seen.add(png)
    if check('%s screenshot exists' % wid, os.path.exists(ART + png), png):
        check('%s screenshot hash prefix' % wid, sha(ART + png).startswith(pre), pre)
    o = OCRL.get(png)
    if check('%s per-label OCR present for %s' % (wid, png), o is not None):
        check('%s OCR reading is of this very file' % wid, os.path.exists(ART + png) and o['sha256'] == sha(ART + png))
        for lab in LABELS:
            got, want = fmt.norm(o['labels'][lab]), fmt.norm(t[lab])
            if lab == 'lbl_result2' and got != want:                        # the label is clipped on screen (394 px): tesseract sees the visible part
                check('%s OCR %s (clipped on screen)' % (wid, lab), difflib.SequenceMatcher(None, got, want).ratio() >= 0.85 and want.startswith(got[:30]), '%r vs %r' % (got, want))
            else:
                check('%s OCR %s' % (wid, lab), got == want, '%r vs %r' % (got, want))
    # the label texts as the game holds them in memory
    mem = [x for x in OCRR if x.get('png') == png]
    if check('%s memory strings recorded' % wid, bool(mem)):
        ms = mem[-1]['memory_strings']; allm = {s.rstrip() for v in ms.values() for s in v}
        for lab in ('lbl_result1', 'lbl_result2', 'lbl_pop1', 'lbl_cities1', 'lbl_money1', 'lbl_pop2', 'lbl_cities2', 'lbl_money2'):
            check('%s memory string %s' % (wid, lab), t[lab].rstrip() in allm, repr(t[lab]))
        check('%s memory string lbl_changes tail' % wid, any(t['lbl_changes'].endswith(s) for s in ms['in power in']), str(ms['in power in']))
        full = ms.get('FULL:in power in')
        if full is not None:         # runs captured since review round 1: the whole caption, so the spacing of the prefix is read from memory
            check('%s memory string lbl_changes (complete, exact)' % wid, t['lbl_changes'] in full, '%r not in %s' % (t['lbl_changes'], full))
            FULL_SEEN.append(wid)
        # the string that is on screen is the one the code's decision picks, and no other result string was built for this window
        reasons = [s for k in ('You have reached the end', 'Your unpopularity', 'Your army have', 'Your nation has been', 'You have conquerred') for s in ms[k]]
        check('%s exactly one result2 string in memory' % wid, [s.rstrip() for s in reasons] == [t['lbl_result2']], str(reasons))

# ------------------------------------------------------------------ the after-OK state of the fallen seat
def seat_after(spec, seat):
    if spec.startswith('MEM:'):
        d = state_of(spec); st = d['seats'][str(seat)]
        return dict(leader=st['leader'], unity=st['unity'], money=st['treasury'], human=st['human'], humans=d['humans'], cur=d['cur_nation'], cities=st['cities'])
    c = save_fields(spec[5:], seat)
    return dict(leader=c['leader'], unity=c['unity'], money=c['treasury'], human=c['human'], humans=c['humans'], cur=c['current_nation'], cities=c['cities'], conq=c['conquered_by'])

for r in T.get('after_state', []):
    sid = r['id']; seat = int(r['seat']); b = seat_after(r['before source'], seat); a = seat_after(r['after source'], seat)
    check('%s leader before/after' % sid, (b['leader'], a['leader']) == (r['leader before'], r['leader after']), '%s %s' % (b['leader'], a['leader']))
    check('%s unity before/after' % sid, (b['unity'], a['unity']) == (int(r['unity before']), int(r['unity after'])), '%s %s' % (b['unity'], a['unity']))
    check('%s treasury before/after' % sid, (b['money'], a['money']) == (num(r['treasury before']), num(r['treasury after'])), '%s %s' % (b['money'], a['money']))
    # FUN_00449078 :47789 writes the cleared value at the nation record's human byte; the address is checked against the record layout (NATIONS + 0x490)
    check('%s human flag before/after (cleared to %d by the hand-over at nation +0x%x)' % (sid, CODE.human_cleared, CODE.human_flag_addr - NATIONS), CODE.human_flag_addr - NATIONS == HUMAN_OFF and b['human'] != CODE.human_cleared and a['human'] == CODE.human_cleared, '%s %s' % (b['human'], a['human']))
    rule = r['rule']
    if rule == 'fall':            # FUN_0044c8f0 :50796-50805: unity = max(unity, min(550, unity + 150)); treasury = 0 if negative else + 1000; leader replaced
        check('%s unity rule (fall)' % sid, a['unity'] == max(b['unity'], min(CODE.fall_unity_cap, b['unity'] + CODE.fall_unity_inc)))
        check('%s treasury rule (fall)' % sid, a['money'] == (0 if b['money'] < 0 else b['money'] + CODE.fall_money_bonus))
    elif rule == 'conquered':     # the same routine, then FUN_0044c528 zeroes unity (:50800 order: it runs after) and records the conqueror
        check('%s unity rule (conquered)' % sid, a['unity'] == 0)
        check('%s treasury rule (conquered)' % sid, a['money'] == (0 if b['money'] < 0 else b['money'] + CODE.fall_money_bonus))
        check('%s conquered_by recorded' % sid, a.get('conq') == int(r['conquered by after']))
    elif rule == 'abdicate':      # TPremierForm_Abdicate calls FUN_00449078 only: the flag is cleared; unity and treasury are untouched
        check('%s unity and treasury untouched' % sid, (a['unity'], a['money']) == (b['unity'], b['money']))
    else: check('%s known rule' % sid, False, rule)

# ------------------------------------------------------------------ what the game does next
def win_label(ws):
    names = [w[0] if isinstance(w, (list, tuple)) else w for w in ws]
    if names == ['Imperial Conquest 2']: return 'caption only'
    if 'Unit map' in names and 'Area map' in names and 'Information' in names: return 'game windows'
    return 'other: ' + ','.join(names)

for r in T.get('after_game', []):
    gid = r['id']
    b = state_of(r['before source']); a = state_of(r['after source'])
    check('%s humans before' % gid, str(b['humans']) == r['humans before'], str(b['humans']))
    check('%s humans after' % gid, str(a['humans']) == r['humans after'], str(a['humans']))
    check('%s current seat after' % gid, str(a['cur_nation']) == r['current seat after'], str(a['cur_nation']))
    check('%s windows after' % gid, win_label(a['windows']) == r['windows after'], win_label(a['windows']))
    check('%s main window title after' % gid, (a['title'] and a['title'][-1] if r['windows after'] == 'caption only' else True) and True)
    check('%s process alive' % gid, a['alive'] is True and r['program'] == 'keeps running')
    check('%s calendar year' % gid, str(a['calendar']['year_bc']) == r['year after'], str(a['calendar']))

# ------------------------------------------------------------------ staging
LOG = [l.rstrip('\n').split('\t') for l in open(DATA + 'staging_log.tsv')]
for r in T.get('staging', []):
    f = r['staged input']; p = SAVES + 'inputs/' + f
    check('staged input exists: ' + f, os.path.exists(p))
    rows = [l for l in LOG if l[4] == f]
    if not check('staging log has %s' % f, len(rows) == 1, str(len(rows))): continue
    ts, tag, srcname, srcsha, dstname, dstsha, allowed = rows[0]
    allowed_ranges, ops = allowed.split(' ops=', 1)
    ranges = [(o, ln) for o, ln, _ in json.loads(allowed_ranges)]
    srcp = (SAVES + 'inputs/' + srcname) if os.path.exists(SAVES + 'inputs/' + srcname) else os.path.join(ROOT, 'saves', srcname)
    check('%s source save hash' % f, os.path.exists(srcp) and sha(srcp) == srcsha)
    check('%s staged save hash' % f, sha(p) == dstsha)
    check('%s source named in finding' % f, srcname == r['source save'])
    a = open(srcp, 'rb').read(); b = open(p, 'rb').read()
    check('%s same length' % f, len(a) == len(b))
    diff = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    check('%s changed bytes (claimed %s)' % (f, r['changed bytes']), len(diff) == int(r['changed bytes']), str(len(diff)))
    check('%s every changed byte is inside a declared field' % f, all(any(o <= i < o + ln for o, ln in ranges) for i in diff))
    # the operation's old and new value, read from the two files
    from state import sav as SAV
    n0a, n0b = fmt.nation0(a), fmt.nation0(b)
    op = r['operation']
    m = re.fullmatch(r'(treasury|unity|ncities)\[(\d+)\]', op)
    if m:
        off, fm = {'treasury': (0x438, 'i'), 'unity': (0x440, 'h'), 'ncities': (0x446, 'h')}[m.group(1)]; n = int(m.group(2))
        va = struct.unpack_from('<' + fm, a, n0a + n * SAV.NATION_LEN + off)[0]; vb = struct.unpack_from('<' + fm, b, n0b + n * SAV.NATION_LEN + off)[0]
        check('%s %s old/new' % (f, op), (va, vb) == (num(r['old']), num(r['new'])), '%s %s' % (va, vb))
    m = re.fullmatch(r'calendar\.(year|week|season)', op)
    if m:
        ta, tb = SAV.parse(a), SAV.parse(b); key = {'year': 'year_bc'}.get(m.group(1), m.group(1))
        check('%s %s old/new' % (f, op), (ta[key], tb[key]) == (int(r['old']), int(r['new'])), '%s %s' % (ta[key], tb[key]))
    m = re.fullmatch(r'city\[(\d+)\]\.(\w+)', op)
    if m:
        c = int(m.group(1)); fld = m.group(2)
        ca = [x for x in SAV.parse(a)['cities'] if x['id'] == c][0]; cb = [x for x in SAV.parse(b)['cities'] if x['id'] == c][0]
        check('%s %s old/new' % (f, op), (ca[fld], cb[fld]) == (int(r['old']), int(r['new'])), '%s %s' % (ca[fld], cb[fld]))
    m = re.fullmatch(r'own_all\[(\d+)\]', op)
    if m:
        n = int(m.group(1)); sb = SAV.parse(b)
        check('%s own_all: every city owned by nation %d' % (f, n), all(c['owner'] == n for c in sb['cities']))
        check('%s own_all: nation %d lists %d cities' % (f, n, 334), sb['nations'][n]['cities_count'] == 334 and len(sb['nations'][n]['city_list']) == 334)
        check('%s own_all: the other nations have 0 cities and unity 0' % f, all(x['cities_count'] == 0 and x['unity'] == 0 and not x['city_list'] for x in sb['nations'] if x['id'] != n))
    # the operation is among the log's operations
    if op.startswith('(no operation'): check('%s: no operation is byte-identical and logged with no operation' % f, ops == '[]' and not diff)
    else: check('%s operation present in the staging log' % f, op.split('[')[0].split('.')[0] in ops)

# ------------------------------------------------------------------ start values: recorded at New Game
for r in T.get('start', []):
    p = os.path.join(ROOT, 'saves', r['save']) if os.path.exists(os.path.join(ROOT, 'saves', r['save'])) else SAVES + 'inputs/' + r['save']
    b = open(p, 'rb').read()
    from state import sav as SAV
    st = SAV.parse(b); eq = lambda f: sum(1 for n in range(16) if f(fmt.nation_fields(b, n), st['nations'][n]))
    check('start %s: pop start == pop now' % r['save'], eq(lambda c, s: c['wealth_start'] == c['wealth']) == int(r['pop equal']))
    check('start %s: treasury start == treasury now' % r['save'], eq(lambda c, s: c['treasury_start'] == c['treasury']) == int(r['treasury equal']))
    check('start %s: cities start == count' % r['save'], eq(lambda c, s: c['cities_start'] == c['cities']) == int(r['cities equal']))
    check('start %s: count == city list length' % r['save'], eq(lambda c, s: c['cities'] == len(s['city_list'])) == int(r['count = list']))
    check('start %s: calendar' % r['save'], (st['year_bc'], st['season'], st['week']) == (270, 0, 1))

# ------------------------------------------------------------------ re-runs reproduce the first runs
WIN = {r['id']: r for r in T.get('windows', [])}
for r in T.get('rerun', []):
    f1, f2 = ART + r['first run'], ART + r['re-run']
    if check('%s both screenshots exist' % r['id'], os.path.exists(f1) and os.path.exists(f2)):
        check('%s re-run screenshot is byte-identical to the first run' % r['id'], sha(f1) == sha(f2))
        check('%s sha256 prefix' % r['id'], sha(f2).startswith(r['screenshot sha256 prefix']))
    check('%s the windows table cites the re-run screenshot' % r['id'], r['id'] in WIN and WIN[r['id']]['screenshot (sha256 prefix)'].startswith(r['re-run']))
    check('%s complete caption read from memory' % r['id'], (r['id'] in FULL_SEEN) == (r['memory has the complete caption'] == 'yes'), str(FULL_SEEN))

# ------------------------------------------------------------------ counts
count_src = {'windows captured (rows of the windows table)': len(T.get('windows', [])),
             'screenshots read per label': len(shots_seen),
             'distinct reasons that produced a window': len({r['lbl_result2'] for r in T.get('windows', [])}),
             'staged inputs (rows of the staging table, distinct files)': len({r['staged input'] for r in T.get('staging', [])}),
             'two-human scenarios (rows of after_game with two humans before)': len([r for r in T.get('after_game', []) if r['humans before'].count(',') == 1])}
for r in T.get('counts', []):
    check('count: ' + r['item'], r['item'] in count_src and count_src[r['item']] == int(r['value']), '%s vs %s' % (r['value'], count_src.get(r['item'])))

# ------------------------------------------------------------------ integrity of the released artifacts
for m in sorted(glob.glob(DATA + 'MANIFEST-*.txt')):
    for l in open(m):
        p = l.split()
        if len(p) == 2 and p[1].startswith('member:'):
            f = ART + p[1][7:]
            if os.path.exists(f): check('manifest member hash %s' % p[1][7:], sha(f) == p[0])
            else: check('manifest member present %s' % p[1][7:], False, 'missing (run fetch_archive.py)')
hashes = {}
for l in open(DATA + 'SAVES.sha256'):
    p = l.split()
    if len(p) == 2: hashes.setdefault(p[1], set()).add(p[0])
for name, hs in hashes.items():
    cand = [x for x in (SAVES + name, SAVES + 'inputs/' + name, ART + name) if os.path.exists(x)]
    if cand: check('SAVES.sha256 %s' % name, sha(cand[0]) in hs)

summary = 'claims audit of %s: %d checks, %d mismatches' % (os.path.basename(args.finding), checks, len(bad))
text = '\n'.join(['MISMATCH ' + b for b in bad] + [summary]) + '\n'
if args.out != 'none':
    p = write_new(args.out or os.path.join(DATA, 'claims_audit_output.txt'), text)
    print('written', p)
print(text if not args.quiet or bad else summary)
sys.exit(1 if bad else 0)
