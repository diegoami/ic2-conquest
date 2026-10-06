#!/usr/bin/env python3
"""Claims audit of findings/2026-10-06-leaders-form.md.

Every literal, rule, count and check in the finding's tables (marked <!-- table: NAME -->) is compared with a value RECOMPUTED from a source; nothing the finding says is taken as its own truth:
 * the tracked code extract (code_extract_leaders*.txt): a cited `function:line` must exist, lie inside that function and be read by a check of its row; `code <line> has <text>`, `code <a>-<b> seq <t1> ~~ <t2>` (the texts in order
   in the lines, whitespace normalised) and `code fn <F> has|lacks|seq ...` test the extract's text, so the operation a rule describes (a maximum, an offset, a flag, a stride) is checked as the code's own operation;
 * the form's resource dump (dfm_TPickLeaders*.txt, parsed into objects and properties): every object of the resource must have a row of the controls table, and the row's caption, position, tab order, line and every other
   property are compared with the resource; with --exe the dump is re-extracted from the executable and compared; a requested --exe or --dat that does not exist FAILS the audit;
 * the pool table (dat_leader_pool*.tsv): its offset is recomputed from the loader's reads in the code extract (loader_offsets.py), every name list is compared with the DAT when --dat is given;
 * EVERY recorded play (plays_*.jsonl, each recording kept and audited by its unique tag, earlier runner versions included): files and hashes, and for the pointer-verified runner (runner 2) every click's pointer read back from the
   X server, its target (the helper's verbatim line of the control, the OCR word or the root window) and the step it belongs to (clicks and keys partition into verified steps whose postconditions are recomputed here);
 * the saves (artifacts folder): every file hashed against SAVES.sha256 and MANIFEST-*.txt, the autosave of a play parsed again (state/sav.py) for every claim about flags, names, order and bytes.
A [confirmed] row's evidence is resolved by the TAG of the files it cites (one recording per play id), may cite only recordings of runner 2, must cite exactly the files its checks read (the screenshot of the step a check reads, the
save for a save check, the memory dump for a memory check) and exactly the plays its checks use. Every number in a rule's prose must be bound to a passing check of the row; every object of the resource, every handler named in the task,
every required play of the task's Done-when and the claims those plays make must be in the finding, from sources other than the finding.
usage: claims_audit.py [--finding F] [--data D] [--artifacts A] [--exe E] [--dat DAT] [--task T] [--out FILE]   Exit status 0 only with 0 mismatches."""
import sys, os, re, json, glob, hashlib, argparse, ast, struct, subprocess, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths
from common import latest, write_new
import loader_offsets, play_plans, branches

ROOT = paths.ROOT
sys.path.insert(0, ROOT)
from state import sav as SAV

PLAY_ID = r'P\d+[a-z]?'
SCENARIOS = os.path.join(HERE, 'scenarios.py')                                       # the play definitions: the expected action sequence of a play comes from here, never from its recording
OBS = r'(LF_P\d+[a-z]?_b\d+):(.+)'                                                   # an observation token of a [confirmed] row's evidence: <tag>:<path in the recording>
NUM_RE = re.compile(r'(?<![\w])(0x[0-9a-fA-F]+|\d{1,3}(?:,\d{3})+|\d+)(?![\w])')

def numbers(text):
    """The numbers in a piece of text, each with its SPELLING: ('d', n) for a decimal (thousands commas allowed), ('x', n) for a hexadecimal or the address in DAT_xxxxxxxx; so a prose "26" is not bound by a check that says
    0x1a. Identifiers such as F31, P06 or AUTO0720 and array indices `[3]` are not numbers."""
    text = re.sub(r'\[(?:\*|-?\d+)\]', '', text)
    text = re.sub(r'DAT_([0-9a-fA-F]{8})', r' 0x\1 ', text)
    out = set()
    for m in NUM_RE.finditer(text):
        t = m.group(1).replace(',', '')
        try: out.add(('x', int(t, 16)) if t.lower().startswith('0x') else ('d', int(t)))
        except ValueError: pass
    return out

SPELL_VAL = {w: i for i, w in enumerate('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split())}
SPELL_VAL.update({'dozen': 12, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'hundred': 100})
ONE_COUNTS = r'one(?= (?:human|flag|byte|character|panel|row|tick|leader|box)(?:s|es)?\b)'                  # "one" is a number only before a counted noun; elsewhere it is a pronoun ("one OK", "when one matches")
SPELLED = re.compile(r'\b(%s|%s)\b' % (ONE_COUNTS, '|'.join(sorted((w for w in SPELL_VAL if w != 'one'), key=len, reverse=True))), re.I)

def spelled(text):
    """the spelled numbers (zero ... twenty, a dozen, thirty ... hundred) of a piece of text, as ('d', n)"""
    return {('d', SPELL_VAL[m.group(1).lower()]) for m in SPELLED.finditer(text)}

def item_numbers(item):
    """the numbers a check item states: its addressing (`code 56939-56941`, `code fn F`) is not a claim"""
    out = numbers(re.sub(r'^code (?:fn \w+ |(?:nl:)?\d+(?:-(?:nl:)?\d+)? )', 'code ', item.strip()))
    for m in re.finditer(r'turn_order\[(\d+)\]', item): out.add(('d', int(m.group(1))))              # a position in the turn order is a claim of the row
    return out

def fmtn(t):
    """a number as it was spelled"""
    return ('0x%x' % t[1]) if t[0] == 'x' else str(t[1])

def norm(s): return re.sub(r'\s+', ' ', s).strip()

def in_order(body, txt, exact=False):
    """every part of `txt` (separated by ' ~~ ') occurs in `body`, in that order (whitespace normalised); with `exact` (a seq over a range of lines) nothing but braces may lie before the first part, between two parts and after the last:
    every statement of the range must be among the parts, so a statement added to the range fails"""
    pos = 0; first = True
    for part in [norm(x) for x in txt.split(' ~~ ')]:
        i = body.find(part, pos)
        if i < 0: return False
        if exact and re.sub(r'[\s{}]', '', body[pos:i]): return False
        pos = i + len(part); first = False
    if exact and re.sub(r'[\s{}]', '', body[pos:]): return False
    return True

def run(finding, data, art, exe=None, dat=None, quiet=True, task=None):
    """the audit; an exception inside it (a source so damaged that a check cannot even be read) is itself a mismatch, never a crash and never a pass"""
    import traceback
    try: return _run(finding, data, art, exe, dat, quiet, task)
    except Exception as e_: return 0, ['the audit could not complete (a damaged or missing source): %s' % traceback.format_exc().strip().splitlines()[-1]]

def _run(finding, data, art, exe=None, dat=None, quiet=True, task=None):
    data = data.rstrip('/') + '/'; art = art.rstrip('/') + '/'
    task = task or os.path.join(ROOT, 'docs', 'tasks', 'leaders-form.md')
    checks = [0]; bad = []
    def check(name, cond, detail=''):
        checks[0] += 1
        if not cond: bad.append('%s: %s' % (name, detail))
        return bool(cond)
    sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
    # ------------------------------------------------------------ the code extract
    EXT = {}; FNOF = {}; FNLINES = collections.defaultdict(list)       # (file, line) -> text ; (file, line) -> function ; function -> [(file, line)]
    ext_path = latest(data + 'code_extract_leaders.txt'); cur_file = None; cur_fn = None
    for l in open(ext_path, encoding='utf-8', errors='replace'):
        l = l.rstrip('\n')
        m = re.match(r'# FILE (\S+)', l)
        if m: cur_file = m.group(1); cur_fn = None; continue
        m = re.match(r'(\d+)\t(.*)', l)
        if not m or cur_file is None: continue
        ln = int(m.group(1)); txt = m.group(2)
        h = re.match(r'// (?:==== (\S+) @ ([0-9a-f]{8}) ====|FUNCTION (\S+) @ ([0-9a-f]{8}))', txt)
        if h: cur_fn = h.group(1) or h.group(3)
        key = ('nl' if cur_file == 'news_log_decomp.txt' else 'all', ln)
        EXT[key] = txt; FNOF[key] = cur_fn; FNLINES[cur_fn].append(key)
    check('code extract is not empty', len(EXT) > 500, str(len(EXT)))
    def code_key(tok):
        m = re.fullmatch(r'(nl:)?(\d+)', tok)
        return ('nl' if m.group(1) else 'all', int(m.group(2)))
    def code_text(a=None, b=None, fn=None):
        """The extract's text of one line, of a range of lines (whitespace normalised, joined by one space), or of a whole function"""
        if fn is not None: return norm(' '.join(EXT[k] for k in FNLINES.get(fn, [])))
        ka = code_key(a); kb = code_key(b) if b else ka
        return norm(' '.join(EXT[(ka[0], i)] for i in range(ka[1], kb[1] + 1) if (ka[0], i) in EXT))
    # ------------------------------------------------------------ the form resource
    DFM = {}; dfm_lines = []
    dfm_path = latest(data + 'dfm_TPickLeaders.txt')
    stack = []
    for i, l in enumerate(open(dfm_path, encoding='utf-8').read().split('\n'), 1):
        dfm_lines.append(l)
        m = re.match(r'(\s*)object (\w+): (\w+)$', l)
        if m:
            o = {'name': m.group(2), 'class': m.group(3), 'props': {}, 'raw': {}, 'children': [], 'line': i, 'proplines': {}}
            if stack: stack[-1]['children'].append(o)
            DFM[o['name']] = o; stack.append(o); continue
        m = re.match(r'\s*end$', l)
        if m and stack: stack.pop(); continue
        m = re.match(r'\s+([\w.]+) = (.*)$', l)
        if m and stack:
            try: stack[-1]['props'][m.group(1)] = ast.literal_eval(m.group(2))
            except Exception: stack[-1]['props'][m.group(1)] = m.group(2)
            stack[-1]['raw'][m.group(1)] = m.group(2)
            stack[-1]['proplines'][m.group(1)] = i
    form = DFM.get('PickLeaders')
    check('dfm: the form object PickLeaders exists', form is not None)
    panels = [c for c in form['children'] if c['class'] == 'TPanel'] if form else []
    DFM_ORDER = [p['props'].get('Caption', '').strip() for p in panels]
    allobjs = list(DFM.values())
    if exe is not None:
        if check('requested --exe exists: %s' % exe, os.path.exists(exe), 'the executable named on the command line is not there: the independent comparison cannot be made'):
            import dump_dfm_check
            fresh = dump_dfm_check.dump(exe)
            mine = [l for l in open(dfm_path, encoding='utf-8').read().split('\n') if not l.startswith('#')]
            check('dfm dump equals a fresh read of the executable', fresh == [l for l in mine if l != ''] or fresh == mine, 'the tracked dump differs from the exe')
    # ------------------------------------------------------------ the pool
    POOL = collections.OrderedDict(); pool_hdr = ''
    for l in open(latest(data + 'dat_leader_pool.tsv'), encoding='utf-8'):
        l = l.rstrip('\n')
        if l.startswith('# '): pool_hdr = l; continue
        if l.startswith('nation_index'): continue
        n, nat, k, name = l.split('\t'); POOL.setdefault(nat, []).append(name)
    off_claim = int(re.search(r'file offset (0x[0-9a-f]+)', pool_hdr).group(1), 16)
    off_calc, pool_len, pool_dst = loader_offsets.pool_read(ext_path)
    check('pool offset in the table header equals the offset recomputed from the loader reads in the code extract', off_claim == off_calc, '%#x vs %#x' % (off_claim, off_calc))
    check('pool size is 16 nations x 12 names x 26 bytes = the length of the loader read', pool_len == 16 * 12 * 26, str(pool_len))
    check('pool has 16 nations of 12 names', len(POOL) == 16 and all(len(v) == 12 for v in POOL.values()), str({k: len(v) for k, v in POOL.items()}))
    if dat is not None:
        if check('requested --dat exists: %s' % dat, os.path.exists(dat), 'the DAT named on the command line is not there: the independent comparison cannot be made'):
            d = open(dat, 'rb').read()
            check('pool table equals the bytes of the DAT at the recomputed offset', all(d[off_calc + n * 312 + k * 26: off_calc + n * 312 + (k + 1) * 26].split(b'\0')[0].decode('latin1') == nm for n, (nat, names) in enumerate(POOL.items()) for k, nm in enumerate(names)))
            check('pool table header carries the DAT hash', hashlib.sha256(d).hexdigest() in pool_hdr)
    DUPS = collections.OrderedDict(); seen = collections.OrderedDict()
    for nat, names in POOL.items():
        for nm in names: seen.setdefault(nm, []).append(nat)
    for nm, nats in seen.items():
        if len(nats) > 1: DUPS[nm] = nats
    dups_text = '; '.join('%s: %s' % (nm, ', '.join(nats)) for nm, nats in DUPS.items())
    # ------------------------------------------------------------ hashes
    HASH = collections.defaultdict(set)
    for l in open(latest(data + 'SAVES.sha256')):
        p = l.split()
        if len(p) == 2: HASH[p[1]].add(p[0])
    MAN = {}
    for m in sorted(glob.glob(data + 'MANIFEST-*.txt')):
        for l in open(m):
            p = l.split()
            if len(p) == 2 and p[1].startswith('member:'): MAN[p[1][7:]] = p[0]
    def art_path(name):
        for d in (art + 'saves/', art):
            if os.path.exists(d + name): return d + name
        return None
    def file_ok(name, what, want_sha=None):
        p = art_path(name)
        if not check('%s: file %s exists in the artifacts' % (what, name), p is not None, name): return None
        h = sha(p)
        check('%s: %s SHA-256 is recorded in SAVES.sha256' % (what, name), h in HASH.get(name, ()), '%s %s' % (h[:12], sorted(x[:12] for x in HASH.get(name, ()))))
        rel = os.path.relpath(p, art)
        if MAN: check('%s: %s matches its manifest hash' % (what, name), MAN.get(rel) == h, '%s %s' % (rel, MAN.get(rel)))
        if want_sha is not None: check('%s: %s equals the hash the play recorded when it took it' % (what, name), h == want_sha, '%s vs %s' % (h[:12], str(want_sha)[:12]))
        return p
    # ------------------------------------------------------------ the recordings: every record kept by its unique tag
    REC = collections.OrderedDict(); ALL = []
    for f in sorted(glob.glob(data + 'plays_*.jsonl')):
        for l in open(f):
            if not l.strip(): continue
            r = json.loads(l); ALL.append(r)
            r['_tag'] = r.get('tag') or 'LF_%s_%s' % (r['play'], r['batch'])
            if not check('recording tag %s is unique (a recording is never replaced by a later one)' % r['_tag'], r['_tag'] not in REC, f): continue
            REC[r['_tag']] = r
    check('the plays files hold %d recordings, all kept by tag' % len(ALL), len(REC) == len(ALL), '%d vs %d' % (len(REC), len(ALL)))
    OKREC = [r for r in REC.values() if r['status'] == 'ok']; FAILED = [r for r in REC.values() if r['status'] != 'ok']
    check('every recording has a status ok or FAILED', all(r['status'] in ('ok', 'FAILED') for r in REC.values()))
    EVID = {t: r for t, r in REC.items() if r['status'] == 'ok' and r.get('runner') == 3 and 'autosave_seen' in r}      # what a rule may cite: runner 3 with the raw outputs, the memory dumps and the autosave listing (batch b8)
    PIDS_OK = sorted({r['play'] for r in OKREC})
    cstr = lambda b: b.split(b'\0')[0].decode('latin1')
    def parse_raw(raw):
        """the helper's output (win_state.exe, one line of 14 tab-separated fields per control) parsed by the audit itself"""
        cs = []
        for line in raw.splitlines():
            p = line.split('\t')
            if len(p) == 14: cs.append({'cls': p[0], 'text': p[1], 'x': int(p[2]), 'y': int(p[3]), 'w': int(p[4]), 'h': int(p[5]), 'enabled': int(p[6]), 'visible': int(p[7]), 'check': int(p[8]), 'limit': int(p[9]), 'sel0': int(p[10]), 'sel1': int(p[11]), 'focus': int(p[12]), 'line': line})
        return cs
    def rows_of(cs, names):
        rows = {}
        for p in [c for c in cs if c['cls'] == 'TPanel']:
            nm = p['text'].strip()
            inside = lambda c: p['x'] <= c['x'] and c['x'] + c['w'] <= p['x'] + p['w'] and p['y'] <= c['y'] and c['y'] + c['h'] <= p['y'] + p['h'] + 4
            cb = [c for c in cs if c['cls'] == 'TCheckBox' and inside(c)]; ed = [c for c in cs if c['cls'] == 'TEdit' and inside(c)]
            if nm in names and len(cb) == 1 and len(ed) == 1: rows[names.index(nm)] = {'nation': nm, 'cb': cb[0], 'ed': ed[0]}
        return rows
    def summary_of(rows): return [[rows[i]['nation'], rows[i]['cb']['check'], rows[i]['cb']['enabled'], rows[i]['ed']['text'], rows[i]['ed']['enabled'], rows[i]['ed']['limit']] for i in sorted(rows)]
    def post_of(cs, rows, n):
        r = rows[n]; e = r['ed']
        return {'check': r['cb']['check'], 'cb_enabled': r['cb']['enabled'], 'cb_focus': r['cb']['focus'], 'edit_enabled': e['enabled'], 'edit_focus': e['focus'], 'sel0': e['sel0'], 'sel1': e['sel1'], 'text': e['text'], 'textlen': len(e['text']), 'focus': [c['cls'] + ':' + c['text'] for c in cs if c['focus']]}
    def decode_nations(b):
        out = []
        for n in range(16):
            r = b[n * 1172:(n + 1) * 1172]
            out.append({'n': n, 'name': cstr(r[:11]), 'leader': cstr(r[0x0B:0x0B + 26]), 'leader_hex': r[0x0B:0x0B + 26].hex(), 'human': r[0x490], 'score_0x440': struct.unpack_from('<h', r, 0x440)[0], 'treasury_0x438': struct.unpack_from('<i', r, 0x438)[0],
                        'view_0x486': struct.unpack_from('<h', r, 0x486)[0], 'view_0x488': struct.unpack_from('<h', r, 0x488)[0], 'sha': hashlib.sha256(r).hexdigest()})
        return out
    SAVE = {}
    def default_view():
        d = {}
        for (k, ln), txt in EXT.items():
            if k == 'nl' and FNOF[(k, ln)] == 'FUN_00448aa4':
                m = re.search(r'\(puStack_20 \+ (0x486|0x488)\) = (0x[0-9a-f]+);', txt)
                if m: d[m.group(1)] = int(m.group(2), 16)
        return d
    DEF = default_view()
    check('the setup code gives the default map view of a nation (words 0x486 and 0x488)', set(DEF) == {'0x486', '0x488'}, str(DEF))
    NAT = DFM_ORDER
    def save_view(tag):
        if tag in SAVE: return SAVE[tag]
        r = REC[tag]
        if not r.get('autosave'): SAVE[tag] = None; return None
        p = art_path(r['autosave']); b = open(p, 'rb').read(); s = SAV.parse(b)
        na = struct.unpack_from('<h', b, SAV.ARMY_OFF)[0]; o = SAV.ARMY_OFF + 2 + na * SAV.ARMY_LEN
        nf = struct.unpack_from('<h', b, o)[0]; o += 2 + nf * SAV.FLEET_LEN
        for n in range(16):
            rec = b[o + n * SAV.NATION_LEN: o + (n + 1) * SAV.NATION_LEN]
            s['nations'][n]['leader_raw_hex'] = rec[0x0B:0x0B + 26].hex()
            s['nations'][n]['leader'] = cstr(rec[0x0B:0x0B + 26]); s['nations'][n]['name'] = cstr(rec[:11])
            s['nations'][n]['view_differs_from_default'] = (s['nations'][n]['view'] != [DEF['0x488'], DEF['0x486']]); s['nations'][n]['view_default'] = [DEF['0x488'], DEF['0x486']]
        s['humans'] = [n['id'] for n in s['nations'] if n['human']]
        names = [n['leader'] for n in s['nations'] if len(n['leader'].strip()) >= 3]
        s['news_naming_a_leader'] = [x for x in s['news'] if any(nm in x for nm in names)]
        SAVE[tag] = s; return s
    def form_view(tag):
        r = REC[tag]; out = {}
        for step, f in r['forms'].items():
            cs = parse_raw(f['raw']); rr = rows_of(cs, NAT)
            rows = summary_of(rr) if tag in EVID else f['rows']                                                      # evidence: the rows are the audit's own parse of the retained helper output
            d = {'titles': [w[0] for w in f['windows']], 'focus': [c['cls'] + ':' + c['text'] for c in cs if c['focus']] if tag in EVID else f['focus'], 'seed': f.get('seed')}
            for row in rows: d[row[0]] = {'check': row[1], 'cb_enabled': row[2], 'text': row[3], 'edit_enabled': row[4], 'limit': row[5]}
            by = {row[0]: row for row in rows}
            d['names'] = [by[n][3] for n in NAT]; d['checks'] = [by[n][1] for n in NAT]; d['edit_enabled'] = [by[n][4] for n in NAT]; d['cb_enabled'] = [by[n][2] for n in NAT]; d['limits'] = [by[n][5] for n in NAT]
            d['names_in_pool'] = all(by[n][3] in POOL.get(n, []) for n in NAT)
            ys = []
            for line in f['raw'].splitlines():
                p = line.split('\t')
                if len(p) == 14 and p[0] == 'TPanel': ys.append((int(p[3]), p[1].strip()))
            d['order'] = [n for _, n in sorted(ys)]
            mem = mem_view(tag)
            if mem: d['rows_match_nations'] = all(by[n][3] == mem['nations'][i]['leader'] and n == mem['nations'][i]['name'] for i, n in enumerate(NAT))
            out[step] = d
        return out
    DS = {}
    def dump_state(tag, key):
        """The game state `key` of a recording as DECODED FROM ITS RAW DUMPS (the 16 nation records, 1,172 bytes each, and the globals words), the file hashes checked; the title bars are the one JSON field (their evidence is the screenshot)."""
        if (tag, key) in DS: return DS[(tag, key)]
        r = REC[tag]; d = r['dumps'][key]; js = r[key]
        pn = art_path(d['nations_bin']); pg = art_path(d['globals_bin'])
        b = open(pn, 'rb').read() if pn else b'\0' * (16 * 1172); gb = open(pg, 'rb').read() if pg else b'\0' * 42          # a missing dump decodes to zeros: every claim fails and the file check names the missing file
        nations = decode_nations(b); to = list(struct.unpack('<16h', gb[:32])); cur, seat, season, week, year = struct.unpack('<5h', gb[32:42])
        st = {'nations': nations, 'turn_order': to, 'cur_nation': cur, 'seat_0x4a032c': seat, 'calendar': {'season': season, 'week': week, 'year_bc': year}, 'windows': js['windows'],
              'nations_bin_leader': [n_['leader'] for n_ in nations]}
        DS[(tag, key)] = st; return st
    def mem_view(tag):
        r = REC[tag]
        if 'dumps' in r:
            return dump_state(tag, 'state') if 'state' in r['dumps'] else None
        s = r.get('state')
        if s is None: return None
        s = json.loads(json.dumps(s))
        if r.get('nations_bin'):
            p = art_path(r['nations_bin'])
            if p:
                b = open(p, 'rb').read()
                s['nations_bin_leader'] = [cstr(b[n * 1172 + 0x0B: n * 1172 + 0x0B + 26]) for n in range(16)]
        return s
    def step_view(tag, v):
        """A verified step with its form states recomputed from the retained raw helper output (never the recorded summaries)"""
        v = json.loads(json.dumps(v)); lab = v['step']
        m = re.match(r'(?:tick|name|space on tick|greyed name box|tab to) (\w+)', lab)
        if 'raw_after' in v:
            cs = parse_raw(v['raw_after']); rr = rows_of(cs, NAT); v['rows_after'] = summary_of(rr)
            if m and m.group(1) in NAT:
                n = NAT.index(m.group(1)); v['post'] = post_of(cs, rr, n)
                if lab.startswith('name '): v['read'] = rr[n]['ed']['text']
        if 'raw_before' in v: v['rows_before'] = summary_of(rows_of(parse_raw(v['raw_before']), NAT))
        for k, st in v.get('stages', {}).items():
            if 'raw' in st and m and m.group(1) in NAT:
                cs = parse_raw(st['raw']); st.update(post_of(cs, rows_of(cs, NAT), NAT.index(m.group(1))))
        if 'rows_before' in v and 'rows_after' in v and m and m.group(1) in NAT:
            n = NAT.index(m.group(1)); v['others_unchanged'] = all(v['rows_before'][i] == v['rows_after'][i] for i in range(16) if i != n)
            v['unchanged'] = v['rows_before'] == v['rows_after']
        return v
    def rec_view(tag):
        r = REC[tag]
        if 'dumps' not in r or tag not in EVID: return r
        out = dict(r)
        for key in r['dumps']: out[key] = dump_state(tag, key)
        out['verified'] = [step_view(tag, v) for v in r['verified']]
        return out
    def view_of(tag):
        r = REC[tag]; v = {}
        if 'tab_walk' in r:
            ys = [w[0][2] for w in r['tab_walk'][1:] if w and w[0][0] == 'TCheckBox']
            v['tab_ticks_increase'] = len(ys) == len(r['tab_walk']) - 1 and all(a < b for a, b in zip(ys, ys[1:]))
        return v
    # ------------------------------------------------------------ paths and checks
    CUR = {'res': {}}                                              # the row being checked: play id -> the tag of the recording its evidence names
    def derived_keys(o, key):
        if isinstance(o, dict) and key not in o and 'nations' in o:
            if key == 'nation_shas': return [n['sha'] for n in o['nations']]
            if key == 'nation_names': return [n['name'] for n in o['nations']]
        raise KeyError(key)
    ALLV = type('ALL', (list,), {})
    def walk(o, path):
        toks = re.findall(r'\.?([A-Za-z_][A-Za-z_0-9]*)|\[(\*|-?\d+)\]|\{([^}=]+)=([^}]*)\}', path)
        cur = o
        for key, idx, sk, sv in toks:
            vals = cur if isinstance(cur, ALLV) else [cur]
            res = []
            for v in vals:
                if key:
                    if isinstance(v, dict) and key in v: res.append(v[key])
                    else: res.append(derived_keys(v, key))
                elif idx:
                    if idx == '*': res.extend(v)
                    else: res.append(v[int(idx)])
                else:
                    hit = [x for x in v if isinstance(x, dict) and str(x.get(sk)) == sv]
                    if not hit: raise KeyError('{%s=%s}' % (sk, sv))
                    res.append(hit[0])
            star = isinstance(cur, ALLV) or idx == '*'
            cur = ALLV(res) if star else res[0]
        return cur
    def root(pid, name):
        if pid not in CUR['res']: raise KeyError('play %s has no cited recording in this row' % pid)
        tag = CUR['res'][pid]
        if name == 'rec': return rec_view(tag)
        if name == 'mem': return mem_view(tag)
        if name == 'save': return save_view(tag)
        if name == 'form': return form_view(tag)
        if name == 'view': return view_of(tag)
        raise KeyError(name)
    def evaluate(pid, path):
        head, _, rest = path.partition('.')
        try:
            base = root(pid, head)
            return True, walk(base, '.' + rest) if rest else base
        except (KeyError, IndexError, TypeError) as e:
            return False, e
    def parse_value(tok, lit):
        tok = tok.strip()
        if tok == '@literal': return lit
        if tok == '@dfmorder': return list(DFM_ORDER)
        if tok == '@limits': return [int(lit)] * 16
        if tok == '@duplicates': return dups_text
        m = re.fullmatch(r'(%s) ((?:[^\s{]|\{[^}]*\})+)' % PLAY_ID, tok)
        if m:
            ok, v = evaluate(m.group(1), m.group(2))
            if not ok: raise KeyError('rhs %s' % tok)
            return v
        return json.loads(tok)
    DRAW_PLAYS = []                                                # filled from the draws table: (play id, tag, step)
    def scan(kind, what):
        """a statement about every recording of runner 2 (a `scan` check of the facts table): the values are read from the records, never from the finding"""
        recs = list(EVID.values())
        ds = lambda r, k: dump_state(r['_tag'], k) if k in r.get('dumps', {}) else None
        if kind == 'score':
            vals = sorted((n['score_0x440'], n['name']) for r in recs for st in [ds(r, 'state'), ds(r, 'state_after_cancel'), ds(r, 'state_first_game'), ds(r, 'state_before_new')] if st for n in st['nations'])
            if not vals: return False, 'no states'
            ma = re.fullmatch(r'min_above_(\d+)', what)
            if ma: return True, vals[0][0] > int(ma.group(1))
            return True, {'min': vals[0][0], 'max': vals[-1][0], 'min_nation': vals[0][1], 'max_nation': vals[-1][1], 'count': len(vals)}[what]
        if kind == 'turn_order':
            by = collections.defaultdict(set)
            for r in recs:
                st = ds(r, 'state')
                if st: by[r['new_games'][-1]['seed']].add(tuple(st['turn_order']))      # the seed of the New Game that drew the state
            if not by: return False, 'no states'
            return True, {'one_per_seed': all(len(v) == 1 for v in by.values()), 'differs_between_seeds': len({next(iter(v)) for v in by.values()}) == len(by), 'seeds': len(by)}[what]
        if kind == 'initial_nation':                                 # every state read where no turn has started: the current nation is the first entry of the order
            sts = [ds(r, 'state') for r in recs if ds(r, 'state') and not r.get('autosave')]
            if not sts: return False, 'no states'
            return True, {'is_first_in_order': all(st['cur_nation'] == st['turn_order'][0] for st in sts), 'states': len(sts)}[what]
        if kind == 'default_forms':                                  # the form of every recording that opened it, before any edit
            fvs = [f for r in recs for step, f in form_view(r['_tag']).items() if step == 'default']
            fvs0 = [f for r in recs if not r.get('autosave') for step, f in form_view(r['_tag']).items() if step == 'default']          # no human started afterwards: the records still hold the drawn names
            if not fvs: return False, 'no forms'
            return True, {'count': len(fvs), 'count_unedited': len(fvs0), 'rows_match': bool(fvs0) and all(f.get('rows_match_nations') is True for f in fvs0), 'all_unticked': all(not any(f['checks']) for f in fvs),
                          'all_greyed': all(not any(f['edit_enabled']) for f in fvs), 'in_pool': all(f['names_in_pool'] for f in fvs), 'all_ticks_enabled': all(all(f['cb_enabled']) for f in fvs)}[what]
        return False, 'unknown scan %s' % kind
    PCHECKS = []                                                   # every passing play check of the current row: (pid, path, op, want); the play paths on the right of a comparison are listed too (op 'rhs')
    PLAY_PATH = r'(%s) ((?:[^\s{]|\{[^}]*\})+)' % PLAY_ID
    unsays = lambda it: re.sub(r'^says "[^"]*" :: ', '', it.strip())
    def reads_line(items, k, fn, strict=False):
        items = [unsays(x) for x in items]
        """a check of the row reads the extract's line k (a `code` check naming it or a range holding it, or a `code fn` check of its function)"""
        for it in items:
            m = re.match(r'code ((?:nl:)?\d+)(?:-((?:nl:)?\d+))? (?:has|seq) ', it)
            if m:
                a = code_key(m.group(1)); b = code_key(m.group(2)) if m.group(2) else a
                if a[0] == k[0] and a[1] <= k[1] <= b[1]: return True
            if not strict and re.match(r'code fn %s ' % re.escape(FNOF.get(k) or '-'), it): return True
        return False
    def _core(rid, item, lit, row):
        item = item.strip()
        name = '%s check [%s]' % (rid, item[:110])
        m = re.fullmatch(r'code fn (\w+) count (\w+) == (\d+)', item)
        if m:
            fn, word, n_ = m.groups()
            if not check(name + ' function in the extract', fn in FNLINES, fn): return
            got = len(re.findall(r'\b%s\b' % re.escape(word), code_text(fn=fn))); check(name, got == int(n_), 'function %s has %d' % (fn, got)); return
        m = re.fullmatch(r'code fn (\w+) (has|lacks|seq) (.+)', item)
        if m:
            fn, op, txt = m.groups()
            if not check(name + ' function in the extract', fn in FNLINES, fn): return
            body = code_text(fn=fn)
            if op == 'seq': good, why = in_order(body, txt), 'function %s lacks the operations in order: %r' % (fn, txt)
            else:
                has = (norm(txt) in body); good = has if op == 'has' else not has; why = 'function %s %s %r' % (fn, 'lacks' if has else 'has', txt)
            check(name, good, why); return
        m = re.fullmatch(r'code ((?:nl:)?\d+)(?:-((?:nl:)?\d+))? (has|seq) (.+)', item)
        if m:
            a, b, op, txt = m.groups(); txt = lit if txt == '@literal' else txt
            if not check(name + ' line exists', code_key(a) in EXT and (b is None or code_key(b) in EXT), '%s-%s' % (a, b)): return
            body = code_text(a, b)
            good = (norm(txt) in body) if op == 'has' else in_order(body, txt, exact=True)
            check(name, good, 'lines %s%s are %r' % (a, '-' + b if b else '', body[:200])); return
        m = re.fullmatch(r'dfm (\w+)\.(\w+(?:\.\w+)?) (==|absent) ?(.*)', item)
        if m and m.group(1) in DFM:
            o, prop, op, rhs = m.groups()[0], m.group(2), m.group(3), m.group(4)
            if op == 'absent': check(name, prop not in DFM[o]['props'], str(DFM[o]['props'].get(prop))); return
            want = lit if rhs == '@literal' else json.loads(rhs)
            check(name, prop in DFM[o]['props'] and DFM[o]['props'][prop] == want, 'resource has %r' % (DFM[o]['props'].get(prop),)); return
        m = re.fullmatch(r'dfm order == (%s) (\S+)' % PLAY_ID, item)
        if m:
            ok, v = evaluate(m.group(1), m.group(2))
            if check(name, ok and v == DFM_ORDER, 'resource order %s vs memory %s' % (DFM_ORDER, v)): PCHECKS.append((m.group(1), m.group(2), 'rhs', None))
            return
        m = re.fullmatch(r'dfm count (\w+) == (\d+)', item)
        if m: check(name, sum(1 for o in allobjs if o['class'] == m.group(1)) == int(m.group(2)), str(sum(1 for o in allobjs if o['class'] == m.group(1)))); return
        m = re.fullmatch(r'dfm all (\w+) (\w+) == (.+)', item)
        if m:
            want = json.loads(m.group(3)); objs = [o for o in allobjs if o['class'] == m.group(1)]
            check(name, objs and all(o['props'].get(m.group(2)) == want for o in objs), '%d objects, values %s' % (len(objs), sorted({str(o['props'].get(m.group(2))) for o in objs}))); return
        m = re.fullmatch(r'dfm all (\w+) lacks (.+)', item)
        if m:
            objs = [o for o in allobjs if o['class'] == m.group(1)]; props = m.group(2).split()
            check(name, objs and not any(p in o['props'] for o in objs for p in props), 'found'); return
        m = re.fullmatch(r'pool (size|nations|bytes_per_name|read_length|offset|duplicates_across_nations|duplicate_names|max_nations_per_duplicate|(\w+) len) == (.+)', item)
        if m:
            what, nat, rhs = m.groups(); got = {'size': sum(len(v) for v in POOL.values()), 'nations': len(POOL), 'bytes_per_name': pool_len // (len(POOL) * 12) if POOL else None, 'read_length': pool_len, 'offset': off_calc,
                                                 'duplicates_across_nations': dups_text, 'duplicate_names': len(DUPS), 'max_nations_per_duplicate': max([len(v) for v in DUPS.values()] or [0])}.get(what, len(POOL.get(nat, [])) if nat else None)
            want = lit if rhs == '@literal' else int(rhs); check(name, got == want, 'recomputed %r' % (got,)); return
        m = re.fullmatch(r'sav (\w+) == (\d+)', item)
        if m: check(name, getattr(SAV, m.group(1), None) == int(m.group(2)), 'state/sav.py has %r' % getattr(SAV, m.group(1), None)); return
        m = re.fullmatch(r'scan (\w+) (\w+) == (.+)', item)
        if m:
            kind, what, rhs = m.groups(); ok, got = scan(kind, what)
            if not check(name + ' scanned', ok, str(got)): return
            check(name, got == json.loads(rhs), 'the recordings give %r' % (got,)); return
        m = re.fullmatch(r'draws count == (\d+)', item)
        if m: check(name, len(DRAW_PLAYS) == int(m.group(1)), 'the draws table has %d rows with a recording' % len(DRAW_PLAYS)); return
        m = re.fullmatch(r'draws (all_in_pool|pairwise_different) == true', item)
        if m:
            lists = []
            for pid, tag, step in DRAW_PLAYS:
                f = form_view(tag)[step]; lists.append(tuple(f['names']))
            if m.group(1) == 'all_in_pool': check(name, DRAW_PLAYS and all(form_view(tag)[step]['names_in_pool'] for pid, tag, step in DRAW_PLAYS), 'a name is not in its nation pool')
            else: check(name, len(set(lists)) == len(lists) and len(lists) >= 3, '%d draws, %d distinct' % (len(lists), len(set(lists))))
            return
        m = re.fullmatch(r'(%s) png (\S+) grey (file|game) (\d) == (true|false)' % PLAY_ID, item)
        if m:
            pid, fn, menu, idx, want = m.groups(); p = art_path(fn)
            if not check(name + ' file', p is not None, fn): return
            x0 = 10 if menu == 'file' else 41; y0 = 51 + 17 * int(idx)
            v = subprocess.run(['convert', p, '-crop', '70x12+%d+%d' % (x0, y0), '+repage', '-colorspace', 'Gray', '-format', '%[fx:minima*255]', 'info:'], capture_output=True, text=True).stdout
            check(name, (float(v) > 100) == (want == 'true'), 'darkest pixel %s' % v); return
        m = re.fullmatch(r'(%s) ((?:[^\s{]|\{[^}]*\})+) ?(==|!=|has|startswith|absent|len==|list==|list!=|before|after)? ?(.*)' % PLAY_ID, item)
        if m:
            pid, path, op, rhs = m.groups()
            if not check(name + ' play is cited by tag in this row', pid in CUR['res'], pid): return
            ok, v = evaluate(pid, path)
            if op == 'absent':
                if check(name, not ok, 'the path exists'): PCHECKS.append((pid, path, 'absent', None))
                return
            if not check(name + ' path exists', ok, str(v)): return
            try: want = rhs if op in ('before', 'after') else parse_value(rhs, lit)
            except Exception as e: check(name + ' value parses', False, '%r: %r' % (rhs, e)); return
            vals = list(v) if isinstance(v, ALLV) else [v]
            if op == '==': good = all(x == want for x in vals)
            elif op == '!=': good = all(x != want for x in vals)
            elif op == 'has': good = all((want in x) for x in vals)
            elif op == 'startswith': good = all(isinstance(x, str) and x.startswith(want) for x in vals)
            elif op == 'len==': good = all(hasattr(x, '__len__') and len(x) == want for x in vals)
            elif op == 'list==': good = list(vals) == want
            elif op == 'list!=': good = list(vals) != want
            elif op in ('before', 'after'):
                a_b = re.fullmatch(r'(\d+) (\d+)', rhs.strip()); lst = list(v)
                good = bool(a_b) and int(a_b.group(1)) in lst and int(a_b.group(2)) in lst and ((lst.index(int(a_b.group(1))) < lst.index(int(a_b.group(2)))) == (op == 'before'))
                if good: LAST['nums'] = {('d', lst.index(int(a_b.group(1)))), ('d', lst.index(int(a_b.group(2)))), ('d', int(a_b.group(1))), ('d', int(a_b.group(2)))}; LAST['kind'] = 'order'
            else: good = False
            if check(name, good, 'source has %r, claim %r' % (v if len(repr(v)) < 160 else repr(v)[:160], want)):
                PCHECKS.append((pid, path, op, want)); m3 = re.fullmatch(PLAY_PATH, rhs.strip())
                if m3: PCHECKS.append((m3.group(1), m3.group(2), 'rhs', None))
            return
        check(name + ' parses', False, 'unknown check form')
    # ------------------------------------------------------------ typed claims: a prose claim is bound, with its operation and its operands, to a check that DERIVES them from a source
    LAST = {'kind': None, 'nums': set()}                           # what the check that ran last derived: its kind and the numbers it vouches for (spelled as the source spells them)
    SAYS = collections.defaultdict(list)                           # row id -> [{phrase, ok, kind, nums}]
    BRANCH_CLAIMS = collections.defaultdict(list)                  # (function, line, arm) -> [row id]
    ROWITEMS = {}                                                  # row id -> the check items of the row (for the checks that look at their own row)
    LEX = [(r'\bat least\b', {'floor'}), (r'\blarger\b|\bgreater\b|\bhigher\b|\bmaximum\b|\braised\b', {'floor', 'maxfn'}), (r'\bat most\b', {'getlimit'}), (r'\bsmaller\b|\blower\b|\bminimum\b|\bless\b|\bfewer\b', {'minfn'}),
           (r'\blowest\b', {'scanmin'}), (r'\bhighest\b', {'scanmax'}), (r'\bsame\b', {'same'}), (r'\bdiffer\w*\b|\bdifferent\b', {'differ'}), (r'\bbefore\b|\bafter\b', {'seq', 'order'}), (r'\bthen\b', {'seq', 'order'}), (r'\bnegative\b', {'lt0'}), (r'\bEscape\b|\bReturn\b', {'same', 'value'})]
    def plain(prose, lit=None):
        """the prose as the phrases are matched against it: a quoted literal (a backtick span with letters and a space) blanked, markup removed"""
        def span(m):
            c = m.group(1)
            return ' ' * len(m.group(0)) if (re.search(r'[A-Za-z]{3,}', c) and ' ' in c and not re.search(r'[+=]|0x', c)) else c
        t = re.sub(r'`([^`]*)`', span, prose)
        return t.replace('**', '')
    def fn_semantics(fn):
        """what a two-argument decompiled function does, DERIVED from its text: `if ((short)a <= (short)b) { a = b; } return a;` returns the larger of its arguments ('max'), `>=` the smaller ('min')"""
        body = code_text(fn=fn)
        m = re.search(r'if \(\(short\)(\w+) (<=|>=) \(short\)(\w+)\) \{ \1 = \3; \} return \1;', body)
        return None if not m else ('max' if m.group(2) == '<=' else 'min')
    def spell(v): return {('d', v), ('x', v)}
    def typed(rid, item, lit, row, name):
        """the typed checks; returns True when handled"""
        m = re.fullmatch(r'code fn (\w+) semantics (max|min)', item)
        if m:
            fn, want = m.groups()
            if not check(name + ' function in the extract', fn in FNLINES, fn): return True
            check(name, fn_semantics(fn) == want, 'derived from the code: %s' % fn_semantics(fn)); LAST.update(kind='maxfn' if want == 'max' else 'minfn', nums=set()); return True
        m = re.fullmatch(r'code floor ((?:nl:)?\d+)-((?:nl:)?\d+) field (0x[0-9a-fA-F]+) min (0x[0-9a-fA-F]+|\d+) fn (\w+)', item)
        if m:
            a, b, field, mn, fn = m.groups()
            if not check(name + ' lines exist', code_key(a) in EXT and code_key(b) in EXT, item): return True
            body = code_text(a, b)
            mm = re.search(r'(\w+) = %s\(CONCAT22\(.*?,(0x[0-9a-fA-F]+|\d+)\), CONCAT22\(\w+,\*\(undefined2 \*\)\((\w+) \+ (0x[0-9a-fA-F]+)\)\)\); \*\(short \*\)\(\3 \+ (0x[0-9a-fA-F]+)\) = \(short\)\1;' % re.escape(fn), body)
            if not check(name + ' the lines call %s with a constant and the field\'s old value and store the result back into the same field' % fn, mm is not None, body[:200]): return True
            k_ = int(mm.group(2), 0); off_r, off_w = int(mm.group(4), 0), int(mm.group(5), 0)
            good = off_r == off_w == int(field, 0) and k_ == int(mn, 0) and fn_semantics(fn) == 'max'
            check(name, good, 'the code floors field %#x at %d (read at %#x, written at %#x) with a function that is a %s; the claim is field %s min %s' % (off_w, k_, off_r, off_w, fn_semantics(fn), field, mn))
            LAST.update(kind='floor', nums=spell(k_) | {('x', off_w)}, roles={'field': {('x', off_w)}, 'min': spell(k_)}); return True            # the field address is a hexadecimal after a plus; the minimum is any other number
        m = re.fullmatch(r'code getlimit ((?:nl:)?\d+) fn (\w+) max (0x[0-9a-fA-F]+|\d+)', item)
        if m:
            a, fn, mx = m.groups()
            if not check(name + ' line exists', code_key(a) in EXT, a): return True
            mm = re.search(r'%s\(\w+,[^,]+,(0x[0-9a-fA-F]+|\d+)\);' % re.escape(fn), code_text(a))
            body = code_text(fn=fn); passes = re.search(r'FUN_004133c0\(param_1,0xd,param_3,param_2\);', body) is not None            # message 0xd (WM_GETTEXT) with the third parameter as its count
            good = mm is not None and passes and int(mm.group(1), 0) == int(mx, 0)
            check(name, good, 'the call passes %s as the count; the function sends WM_GETTEXT with its third parameter: %s' % (mm.group(1) if mm else None, passes))
            LAST.update(kind='getlimit', nums=spell(int(mx, 0))); return True
        m = re.fullmatch(r'code order ((?:nl:)?\d+) < ((?:nl:)?\d+)', item)
        if m:
            ka, kb = code_key(m.group(1)), code_key(m.group(2))
            check(name, ka in EXT and kb in EXT and ka[0] == kb[0] and ka[1] < kb[1] and FNOF.get(ka) == FNOF.get(kb), 'the lines %s and %s must be in one function, the first before the second' % (m.group(1), m.group(2))); LAST.update(kind='order', nums=set()); return True
        m = re.fullmatch(r'dfm (\w+) (\w+) < (\w+)', item)
        if m:
            prop, a, b = m.groups()
            good = a in DFM and b in DFM and isinstance(DFM[a]['props'].get(prop), int) and isinstance(DFM[b]['props'].get(prop), int) and DFM[a]['props'][prop] < DFM[b]['props'][prop]
            check(name, good, 'resource: %s.%s=%s, %s.%s=%s' % (a, prop, DFM.get(a, {}).get('props', {}).get(prop), b, prop, DFM.get(b, {}).get('props', {}).get(prop))); LAST.update(kind='order', nums=set()); return True
        m = re.fullmatch(r'branch (\w+):(\d+) (then|else-if|else|implicit-else)', item)
        if m:
            fn, ln, arm = m.groups()
            if not check(name + ' function in the extract', fn in FNLINES, fn): return True
            arms_ = branches.arms([(k[1], EXT[k]) for k in FNLINES[fn]])
            ok_ = (int(ln), arm) in arms_
            check(name + ' the code has this branch arm (derived from the function\'s text)', ok_, 'arms: %s' % sorted(arms_))
            kk = [k for k in FNLINES[fn] if k[1] == int(ln)]
            if ok_: BRANCH_CLAIMS[(fn, int(ln), arm)].append(rid)
            check(name + ' the row reads the line of the arm with a code check', bool(kk) and reads_line(ROWITEMS[rid], kk[0], fn, strict=True), 'the arm line is not read by a code check of the row')
            LAST.update(kind='branch', nums=set()); return True
        m = re.fullmatch(r'calc (.+) == (0x[0-9a-fA-F]+|\d+)', item)
        if m:
            expr, rhs = m.groups()
            toks = re.findall(r'\{(0x[0-9a-fA-F]+|\d+)@([^}]+)\}', expr)
            if not check(name + ' has a sourced operand (a calc of bare numbers is a check against nothing)', len(toks) >= 1, expr): return True
            nums_ = set()
            for val, src in toks:
                v_ = int(val, 0); sp = ('x', v_) if val.lower().startswith('0x') else ('d', v_)
                if re.fullmatch(r'(?:nl:)?\d+', src):
                    kk = code_key(src); good = kk in EXT and sp in numbers(EXT[kk])
                elif src.startswith('pool.'): good = v_ == {'nations': len(POOL), 'names_per_nation': (len(next(iter(POOL.values()))) if POOL else None), 'bytes_per_name': pool_len // (len(POOL) * 12) if POOL else None, 'read_length': pool_len}.get(src[5:])
                elif src.startswith('dfm.count.'): good = v_ == sum(1 for o in allobjs if o['class'] == src[10:])
                elif src.startswith('sav.'): good = getattr(SAV, src[4:], None) == v_
                else: good = False
                check(name + ' operand %s is found in its source %s' % (val, src), good, 'the source does not have %s' % val)
                nums_.add(sp)
            e2 = re.sub(r'\{(0x[0-9a-fA-F]+|\d+)@[^}]+\}', lambda mm: str(int(mm.group(1), 0)), expr)
            bare = re.findall(r'(?<![\w.])(0x[0-9a-fA-F]+|\d+)(?![\w.])', re.sub(r'\{(0x[0-9a-fA-F]+|\d+)@[^}]+\}', ' ', expr))
            check(name + ' bare numbers are only the structural constants 1 and 2 (an element size, the NUL)', all(int(x, 0) in (1, 2) for x in bare), str(bare))
            try: got = eval(e2, {'__builtins__': {}}, {})
            except Exception as e_: got = repr(e_)
            check(name, got == int(rhs, 0), 'the expression is %r' % (got,))
            rhs_sp = ('x', int(rhs, 0)) if rhs.lower().startswith('0x') else ('d', int(rhs, 0))
            if not re.fullmatch(r'\s*\{[^}]+\}\s*', expr): nums_ = set()               # an expression with an operator: a phrase states its RESULT, never one of its operands (0x1a - 1 == 25 vouches for "25", not for "0x1a")
            nums_.add(rhs_sp)
            LAST.update(kind='calc', nums=nums_); return True
        return False
    def default_kind(item):
        if item.startswith('code'):
            if ' < 0)' in item: return 'lt0'
            return 'seq' if re.match(r'code (?:fn \w+ |(?:nl:)?\d+(?:-(?:nl:)?\d+)? )seq ', item) else 'code'
        for pre in ('dfm', 'pool', 'scan', 'sav', 'draws'):
            if item.startswith(pre + ' '):
                if pre == 'scan':
                    mm = re.fullmatch(r'scan (\w+) (min|max) == .*', item)
                    if mm: return 'scan' + mm.group(2)
                    if re.fullmatch(r'scan \w+ one_per_seed == .*', item): return 'same'
                    if re.fullmatch(r'scan \w+ differs_between_seeds == .*', item): return 'differ'
                if pre == 'draws' and 'pairwise_different' in item: return 'differ'
                return pre
        mm = re.fullmatch(r'%s ((?:[^\s{]|\{[^}]*\})+) ?(==|!=|has|startswith|absent|len==|list==|list!=|before|after)? ?(.*)' % PLAY_ID, item)
        if mm:
            op, rhs = mm.group(2), mm.group(3)
            if op in ('==', 'list==') and re.match(PLAY_ID + r' ', rhs.strip()): return 'same'
            if op in ('!=', 'list!=') and re.match(PLAY_ID + r' ', rhs.strip()): return 'differ'
            return 'value'
        return 'other'
    def run_check(rid, item, lit, row):
        item = item.strip(); name = '%s check [%s]' % (rid, item[:110])
        m = re.fullmatch(r'says "([^"]+)" :: (.+)', item)
        if m:
            phrase, inner = m.groups(); n0 = len(bad)
            prose = row.get('rule', row.get('statement', ''))
            check(name + ' the phrase is in the prose of the row', plain(prose).lower().find(phrase.lower()) >= 0, 'phrase %r not found in %r' % (phrase, plain(prose)[:120]))
            run_check(rid, inner, lit, row)
            kind, nums, roles = LAST['kind'], set(LAST['nums']), LAST.pop('roles', None)
            pn = numbers(phrase) | spelled(phrase); wrong = sorted(fmtn(x) for x in pn if x not in nums)
            check(name + ' every number of the phrase is vouched for by the source its check derives (%s)' % sorted(fmtn(x) for x in nums)[:12], not wrong, 'not derived: %s' % wrong)
            if kind == 'floor' and roles:                                    # operand roles: a number after '+' is the field address, every other number is the minimum, never the other way round
                for mm in NUM_RE.finditer(phrase):
                    t = mm.group(1).replace(',', ''); sp = ('x', int(t, 16)) if t.lower().startswith('0x') else ('d', int(t))
                    role = 'field' if phrase[:mm.start()].rstrip().endswith('+') else 'min'
                    check(name + ' the number %s of the phrase is in the role %s of the floor (field %s, minimum %s)' % (mm.group(1), role, sorted(fmtn(x) for x in roles['field']), sorted(fmtn(x) for x in roles['min'])), sp in roles[role])
            for rx, kinds in LEX:
                if re.search(rx, phrase, re.I): check(name + ' the word %r says an operation: the check must be one of %s (it is a %s check)' % (rx, sorted(kinds), kind), kind in kinds)
            SAYS[rid].append({'phrase': phrase, 'ok': len(bad) == n0, 'kind': kind, 'nums': nums})
            return
        LAST.update(kind=default_kind(item), nums=item_numbers(item))
        if typed(rid, item, lit, row, name): return
        _core(rid, item, lit, row)
        if LAST['kind'] in ('same', 'differ', 'value'):
            for p_, path_, op_, wnt_ in PCHECKS[-1:]:
                if isinstance(wnt_, (int, list, str)) and not isinstance(wnt_, bool) and op_ not in ('before', 'after'): LAST['nums'] = LAST['nums'] | numbers(json.dumps(wnt_))
    # ------------------------------------------------------------ the finding's tables
    def tables(path):
        out = {}; lines = open(path, encoding='utf-8').read().splitlines(); i = 0
        while i < len(lines):
            m = re.match(r'<!-- table: (\w+) -->', lines[i])
            if m:
                name = m.group(1); i += 1
                while i < len(lines) and not lines[i].startswith('|'): i += 1
                rows = []
                while i < len(lines) and lines[i].startswith('|'):
                    cells = [c.strip().replace('\\|', '|') for c in re.split(r'(?<!\\)\|', lines[i].strip())[1:-1]]
                    rows.append(cells); i += 1
                hdr = rows[0]
                for r in rows[2:]: check('table %s row width' % name, len(r) == len(hdr), str(r)[:60])
                out[name] = [dict(zip(hdr, r)) for r in rows[2:]]
            else: i += 1
        return out
    TEXT = open(finding, encoding='utf-8').read()
    T = tables(finding)
    for need in ('controls', 'rules', 'draws', 'clone', 'plays', 'counts', 'facts'):
        check('table present: ' + need, need in T and T[need], need)
    spans = lambda cell: re.findall(r'`([^`]*)`', cell)
    # ---- controls: every object of the resource has a row; every property of it is compared
    SKIP_PROPS = ('Left', 'Top', 'Caption', 'TabOrder')
    for r in T.get('controls', []):
        rid = r['id']; o = DFM.get(r['object'])
        if not check('%s object %s is in the resource' % (rid, r['object']), o is not None): continue
        check('%s class' % rid, o['class'] == r['class'], '%s vs %s' % (o['class'], r['class']))
        sp = spans(r['literal'])
        if r['literal'].startswith('('): check('%s has no caption in the resource' % rid, 'Caption' not in o['props'], str(o['props'].get('Caption')))
        else:
            check('%s literal is one piece' % rid, len(sp) == 1, str(sp))
            check('%s literal byte for byte: finding %r vs resource %r' % (rid, sp[0] if sp else None, o['props'].get('Caption')), sp and sp[0] == o['props'].get('Caption'))
        check('%s left' % rid, o['props'].get('Left') == int(r['left']), '%s vs %s' % (o['props'].get('Left'), r['left']))
        check('%s top' % rid, o['props'].get('Top') == int(r['top']), '%s vs %s' % (o['props'].get('Top'), r['top']))
        if r['tab'] == '-': check('%s has no tab order' % rid, 'TabOrder' not in o['props'])
        else: check('%s tab order' % rid, o['props'].get('TabOrder') == int(r['tab']), '%s vs %s' % (o['props'].get('TabOrder'), r['tab']))
        check('%s resource line' % rid, o['line'] == int(r['dfm line']) or (o['class'] == 'TPickLeaders' and o['proplines'].get('Caption') == int(r['dfm line'])), '%d vs %s' % (o['line'], r['dfm line']))
        want = {k: v for k, v in o['raw'].items() if k not in SKIP_PROPS and not k.startswith('Font.') and k not in ('ParentFont', 'PixelsPerInch', 'TextHeight')}
        got = {}
        for kv in [x.strip() for x in r['props'].split(';') if x.strip() and x.strip() != '-']:
            k, _, v = kv.partition('='); got[k.strip()] = v.strip()
        check('%s properties equal the resource\'s (every one listed, none invented): finding %s vs resource %s' % (rid, sorted(got.items()), sorted(want.items())), got == want)
    ids = [r['id'] for r in T.get('controls', [])]
    check('controls ids are unique', len(ids) == len(set(ids)))
    listed = {r['object'] for r in T.get('controls', [])}
    for name_, o in DFM.items():
        check('the resource object %s (%s) has a row in the controls table (no control of the resource is left out)' % (name_, o['class']), name_ in listed)
    check('the resource has 16 panels, each holding one TCheckBox then one TEdit (the rows are panel children)', len(panels) == 16 and all([c['class'] for c in p['children']] == ['TCheckBox', 'TEdit'] for p in panels))
    for p in panels: check('panel %s caption is two spaces and the nation name' % p['name'], p['props'].get('Caption', '').startswith('  ') and p['props']['Caption'].strip() in NAT)
    # ---- the draws table: which recording and form each row reads (needed by the `draws` checks of the rules)
    for r in T.get('draws', []):
        cand = [t for t, x in EVID.items() if x['play'] == r['play']]
        if cand: DRAW_PLAYS.append((r['play'], cand[-1], 'default' if 'default' in REC[cand[-1]]['forms'] else 'second_default'))
    # ---- rules
    RULE = {}; ROW_OBL = {}; SUGGEST = {}
    def coverage(label, text, sayslist, derived=True, words=True):
        """every number and every operation word (LEX) of `text` lies inside an occurrence of a phrase of a passing `says` item (in `sayslist`) whose check derives that number, or is of the kind the word requires"""
        pt = plain(text); spans_ = []
        for sy in sayslist:
            if not sy['ok']: continue
            for mm in re.finditer(re.escape(sy['phrase']), pt, re.I): spans_.append((mm.start(), mm.end(), sy))
        for mm in NUM_RE.finditer(pt):
            t = mm.group(1).replace(',', ''); sp = ('x', int(t, 16)) if t.lower().startswith('0x') else ('d', int(t))
            if re.match(r'\[', pt[max(0, mm.start() - 1):mm.start()]) or re.match(r'\]', pt[mm.end():mm.end() + 1]): continue          # an array index
            cov = [sy for sa, sb, sy in spans_ if sa <= mm.start() and mm.end() <= sb]
            check('%s: the number %s ("...%s...") lies in a phrase of a passing says check that derives it' % (label, mm.group(1), pt[max(0, mm.start() - 18):mm.end() + 12]), any(sp in sy['nums'] for sy in cov), 'phrases covering it: %s' % [sy['phrase'] for sy in cov])
        for mm in SPELLED.finditer(pt):
            sp = ('d', SPELL_VAL[mm.group(1).lower()])
            cov = [sy for sa, sb, sy in spans_ if sa <= mm.start() and mm.end() <= sb]
            check('%s: the spelled number "%s" ("...%s...") lies in a phrase of a passing says check that derives it' % (label, mm.group(1), pt[max(0, mm.start() - 18):mm.end() + 12]), any(sp in sy['nums'] for sy in cov), 'phrases covering it: %s' % [sy['phrase'] for sy in cov])
        for rx, kinds in (LEX if words else []):
            if (rx.startswith(r'\bbefore') or rx.startswith(r'\bthen')) and not derived: continue
            for mm in re.finditer(rx, pt, re.I):
                cov = [sy for sa, sb, sy in spans_ if sa <= mm.start() and mm.end() <= sb]
                check('%s: the word %r ("...%s...") lies in a phrase of a passing says check of kind %s' % (label, mm.group(0), pt[max(0, mm.start() - 18):mm.end() + 18], sorted(kinds)), any(sy['kind'] in kinds for sy in cov), 'phrases covering it: %s' % [(sy['phrase'], sy['kind']) for sy in cov])
    def resolve_row(rid, r, items):
        """play id -> tag from the files the row cites; every play id the checks use must be cited, and every cited play id must be used"""
        ev = [e.strip() for e in r['evidence'].split(';') if e.strip()]
        pl = [e for e in ev if re.fullmatch(PLAY_ID, e)]; fl = [e for e in ev if e not in pl]
        res = {}
        for pid in pl:
            tags = {re.match(r'(LF_%s_b\d+)[_:]' % pid, f).group(1) for f in fl if re.match(r'LF_%s_b\d+[_:]' % pid, f)}
            if not check('%s evidence: play %s is cited with files of exactly one recording (tags %s)' % (rid, pid, sorted(tags)), len(tags) == 1): continue
            tag = tags.pop()
            if not check('%s evidence: recording %s exists, is ok and was made by the pointer-verified runner (runner 2): earlier recordings are kept but are not evidence' % (rid, tag), tag in EVID, 'recorded: %s' % (REC[tag].get('runner') if tag in REC else 'absent')): continue
            check('%s evidence: recording %s is a recording of play %s' % (rid, tag, pid), REC[tag]['play'] == pid)
            res[pid] = tag
        for f in fl:
            mm = re.match(r'LF_(%s)_b\d+[_:]' % PLAY_ID, f)
            check('%s evidence: file %s belongs to a cited play' % (rid, f), bool(mm) and mm.group(1) in pl, f)
        used = {re.match(r'(%s) ' % PLAY_ID, it).group(1) for it in items if re.match(r'(%s) ' % PLAY_ID, it)}
        used |= {m2 for it in items for m2 in re.findall(r'(?:== |!= )(%s) \S' % PLAY_ID, it)}
        used |= {m2.group(1) for it in items for m2 in [re.match(r'dfm order == (%s) ' % PLAY_ID, it)] if m2}
        check('%s evidence: the plays cited (%s) are exactly the plays the checks use (%s)' % (rid, sorted(pl), sorted(used)), set(pl) == used)
        return res, fl
    STATEKEYS = {'state': ('after_ok', 'after_cancel', 'after_escape'), 'state_after_cancel': ('after_cancel',), 'state_after_no': ('after_no',), 'state_first_game': (), 'state_before_new': ()}
    def needs(tag, path):
        """what a check path reads, as the evidence tokens a [confirmed] row must cite: the artifact files (the screenshot of the form step, the autosave, the raw memory dumps of the state read, the screenshot taken with a window title) and the
        OBSERVATION of the recording the check reads (`<tag>:forms.<step>` = the retained helper output of that form read, `<tag>:verified.<step label>`, `<tag>:autosave_seen.<state>`, ...)"""
        r = REC[tag]; out = set(); head = re.split(r'[.\[{]', path)[0]; sub = path.split('.')
        dumpfiles = lambda key: {r['dumps'][key]['nations_bin'], r['dumps'][key]['globals_bin']}
        screen = lambda keys: {r['screens'][k]['png'] for k in keys if k in r.get('screens', {})}
        if head == 'form': out |= {r['forms'][sub[1]]['png'], '%s:forms.%s' % (tag, sub[1])}
        elif head == 'save': out.add(r['autosave'])
        elif head == 'mem':
            out |= dumpfiles('state')
            if 'windows' in path: out |= screen(STATEKEYS['state'])
        elif head == 'rec':
            s1 = re.split(r'[\[{]', sub[1])[0] if len(sub) > 1 else ''
            if s1 == 'forms': out |= {r['forms'][sub[2]]['png'], '%s:forms.%s' % (tag, sub[2])}
            elif s1 in STATEKEYS:
                out |= dumpfiles(s1)
                if 'windows' in path: out |= screen(STATEKEYS[s1])
            elif s1 == 'verified':
                m2 = re.search(r'\{step=([^}]*)\}', path)
                if m2:
                    out.add('%s:verified.%s' % (tag, m2.group(1)))
                    st = [v for v in r['verified'] if v['step'] == m2.group(1)]
                    if st and st[0].get('post_png') and '.post' in path: out.add(st[0]['post_png'])
            elif s1 == 'autosave_seen': out.add('%s:autosave_seen.%s' % (tag, sub[2]))
            elif s1: out.add('%s:%s' % (tag, s1))
        return {x for x in out if x}
    def obs_exists(tag, token):
        r = REC[tag]; p = token.split('.')
        if p[0] == 'forms': return len(p) == 2 and p[1] in r['forms']
        if p[0] == 'verified': return any(v['step'] == '.'.join(p[1:]) for v in r['verified'])
        if p[0] == 'autosave_seen': return len(p) == 2 and p[1] in r.get('autosave_seen', {})
        return len(p) == 1 and p[0] in r
    for r in T.get('rules', []):
        rid = r['id']; check('rule id unique %s' % rid, rid not in RULE, rid); RULE[rid] = r
        tag = r['tag']; check('%s tag is [derived] or [confirmed]' % rid, tag in ('[derived]', '[confirmed]'), tag)
        sp = spans(r['literal']); lit = sp[0] if sp else None
        if r['literal'] != '-': check('%s literal is one piece' % rid, len(sp) == 1, str(sp))
        items_raw = [x for x in r['check'].split(' ;; ') if x.strip()]; items = [unsays(x) for x in items_raw]; ROWITEMS[rid] = items
        check('%s has checks' % rid, bool(items))
        PCHECKS[:] = []; CUR['res'] = {}; res, fl = {}, []
        if tag == '[derived]':
            check('%s derived rows cite no play' % rid, r['evidence'] == '-', r['evidence'])
            srcs = [s.strip() for s in r['source'].split(', ') if s.strip()]
            check('%s derived rows cite a source' % rid, srcs and srcs != ['-'], r['source'])
            for s in srcs:
                m = re.fullmatch(r'(nl:)?(\w+):(\d+)', s)
                if m and m.group(2) != 'dfm':
                    k = ('nl' if m.group(1) else 'all', int(m.group(3)))
                    if check('%s source %s: line is in the extract' % (rid, s), k in EXT):
                        check('%s source %s: line %d is in function %s (the extract says %s)' % (rid, s, k[1], m.group(2), FNOF.get(k)), FNOF.get(k) == m.group(2))
                        check('%s source %s is read by a check of the row (a citation no check tests is not a claim)' % (rid, s), reads_line(items, k, m.group(2)), s)
                    continue
                m = re.fullmatch(r'dfm:(\d+)', s)
                if m:
                    ln = int(m.group(1)); check('%s source %s: line is in the resource dump' % (rid, s), 1 <= ln <= len(dfm_lines))
                    pm = re.match(r'\s+([\w.]+) = ', dfm_lines[ln - 1]) if ln <= len(dfm_lines) else None
                    if pm: check('%s source %s: the line\'s property %s is one the row checks' % (rid, s, pm.group(1)), any(re.search(r'dfm [\w]+\.%s\b|dfm all \w+ %s\b' % (pm.group(1), pm.group(1)), it) or (pm.group(1) in it and it.startswith('dfm all')) for it in items), pm.group(1))
                    continue
                if s == 'dat:pool': continue
                check('%s source %s is understood' % (rid, s), False)
            check('%s derived rows have a code or resource or pool check' % rid, any(it.startswith(('code', 'dfm', 'pool')) for it in items))
            check('%s derived rows read no play' % rid, not any(re.match(PLAY_ID + ' ', it) for it in items))
        else:
            check('%s confirmed rows cite no code line' % rid, r['source'] == '-', r['source'])
            if os.environ.get('AUDIT_SUGGEST'):            # developer aid: the evidence the checks of this row read (to be reviewed and pasted by hand); never used by the audit's own verdict
                sug_ = set(); pls_ = set()
                for it in items:
                    for mm in re.finditer(r'(%s) ((?:[^\s{]|\{[^}]*\})+)' % PLAY_ID, it):
                        tg_ = [t_ for t_, x_ in EVID.items() if x_['play'] == mm.group(1)]
                        if tg_:
                            pls_.add(mm.group(1))
                            try: sug_ |= needs(tg_[-1], mm.group(2))
                            except (KeyError, IndexError): pass
                    gm = re.match(r'(%s) png (\S+) grey' % PLAY_ID, it)
                    if gm: sug_.add(gm.group(2)); pls_.add(gm.group(1))
                SUGGEST[rid] = '; '.join(sum([[p_] + sorted(x for x in sug_ if re.match(r'LF_%s_b\d+[_:]' % p_, x)) for p_ in sorted(pls_)], []))
            res, fl = resolve_row(rid, r, items); CUR['res'] = res
            check('%s confirmed rows cite a play' % rid, bool(res))
            for f in fl:
                mo = re.fullmatch(OBS, f)
                if mo: check('%s evidence: observation %s exists in the recording' % (rid, f), mo.group(1) in REC and obs_exists(mo.group(1), mo.group(2)))
                elif re.match(r'LF_%s_b\d+_' % PLAY_ID, f): file_ok(f, rid)
            check('%s confirmed rows cite a screenshot' % rid, any(f.endswith('.png') for f in fl), r['evidence'])
            check('%s confirmed rows cite state evidence the task requires: a save or a memory dump' % rid, any(f.endswith(('.SAV', '.bin')) for f in fl), r['evidence'])
            check('%s confirmed rows have a play check' % rid, any(re.match(PLAY_ID + ' ', it) for it in items))
        for it in items_raw: run_check(rid, it, lit, r)
        if tag == '[confirmed]':
            want_files = set()
            for pid, path, op, wnt in PCHECKS:
                try: want_files |= needs(res[pid], path)
                except (KeyError, IndexError): check('%s check %s %s reads a state that has no artifact' % (rid, pid, path), False)
            for it in items:
                m2 = re.match(r'(%s) png (\S+) grey' % PLAY_ID, it)
                if m2: want_files.add(m2.group(2))
            check('%s evidence files are exactly the files the checks read: cited %s, read %s' % (rid, sorted(fl), sorted(want_files)), set(fl) == want_files, 'missing %s, unused %s' % (sorted(want_files - set(fl)), sorted(set(fl) - want_files)))
        ROW_OBL[rid] = list(PCHECKS)
        coverage('%s prose' % rid, r['rule'], SAYS[rid], derived=(tag == '[derived]'))
    # ---- the claims every recorded play makes must be in the rules (obligations from the recordings and the task, not from the finding)
    allp = [(rid, p) for rid, pcs in ROW_OBL.items() for p in pcs if RULE[rid]['tag'] == '[confirmed]']
    task_text = open(task, encoding='utf-8').read().lower() if os.path.exists(task) else ''
    def obliged(name, tag, regex, want=None, op='==', phrase=None, in_task=True):
        """the finding must have a passing check `<play> <path> <op> <value>` of this play whose path matches `regex` and whose value is `want` (None: any); with `phrase` (a phrase of the task's own questions) the check
        must be in a [confirmed] row whose rule text contains that phrase, so a claim cannot be carried only by an aggregate row after its own row is removed"""
        if phrase is not None and in_task: check('the task asks about "%s" (the phrase is in %s)' % (phrase, os.path.basename(task)), phrase in task_text)
        ok = False
        for rid, (pid, path, op2, w) in allp:
            if REC[tag]['play'] != pid or not re.fullmatch(regex, path) or op2 != op: continue
            if phrase is not None and phrase not in RULE[rid]['rule'].lower(): continue
            if want is None or w == want: ok = True
        check('required claim in the finding: ' + name + ' (a passing check of play %s: %s %s %r%s)' % (REC[tag]['play'], regex, op, want, ' in a row whose rule says "%s"' % phrase if phrase else ''), ok)
    def newest(pred):
        c = [t for t, r in EVID.items() if pred(r)]
        return c[-1] if c else None
    def forms_text(r, step='before_ok'): return r['forms'].get(step, {}).get('rows', [])
    def hum(r): return r.get('humans_ticked')
    def verified(r, step): return any(v['step'] == step for v in r['verified'])
    def need(label, tag):
        check('required play exists (task Done-when): ' + label, tag is not None); return tag
    t0h = need('0 humans ticked, OK', newest(lambda r: hum(r) == [] and verified(r, 'press OK') and r.get('dumps')))
    if t0h: obliged('0 humans ticked, OK: no human flag in the records', t0h, r'mem\.nations\[\*\]\.human', 0); obliged('0 humans ticked, OK: no autosave file seen', t0h, r'rec\.autosave_seen\.state\.files', [], '==')
    for n_ in (1, 2, 16):
        t = need('%d human(s) ticked, OK' % n_, newest(lambda r: hum(r) is not None and len(hum(r)) == n_ and r.get('autosave') and (verified(r, 'press OK') or verified(r, 'key Return'))))
        if t: obliged('%d human(s) ticked: the flags in the save are the ticked nations' % n_, t, r'save\.humans', sorted(hum(REC[t])))
    tp = need('an empty name ticked and accepted', newest(lambda r: r.get('autosave') and any(row[1] == 1 and row[3] == '' for row in forms_text(r))))
    if tp:
        for i, row in enumerate(forms_text(REC[tp])):
            if row[1] == 1 and row[3] == '': obliged('an empty name is saved as typed (nation %d)' % i, tp, r'save\.nations\[%d\]\.leader' % i, '', phrase='empty name')
    tp = need('a name of spaces ticked and accepted', newest(lambda r: r.get('autosave') and any(row[1] == 1 and row[3] != '' and row[3].strip() == '' for row in forms_text(r))))
    if tp:
        for i, row in enumerate(forms_text(REC[tp])):
            if row[1] == 1 and row[3] != '' and row[3].strip() == '': obliged('a name of spaces is saved as typed (nation %d)' % i, tp, r'save\.nations\[%d\]\.leader' % i, row[3], phrase='name of spaces')
    tp = need('a duplicate name ticked and accepted', newest(lambda r: r.get('autosave') and len([row[3] for row in forms_text(r) if row[1] == 1 and row[3]]) != len({row[3] for row in forms_text(r) if row[1] == 1 and row[3]})))
    if tp:
        names_ = [row[3] for row in forms_text(REC[tp]) if row[1] == 1 and row[3]]
        for i, row in enumerate(forms_text(REC[tp])):
            if row[1] == 1 and row[3] and names_.count(row[3]) > 1: obliged('a duplicate name is saved as typed (nation %d)' % i, tp, r'save\.nations\[%d\]\.leader' % i, row[3], phrase='duplicate name')
    tp = need('an over-long name typed', newest(lambda r: r.get('autosave') and any(v['step'].startswith('name ') and len(v.get('typed', '')) > 25 for v in r['verified'])))
    if tp:
        for v in REC[tp]['verified']:
            if v['step'].startswith('name ') and len(v.get('typed', '')) > 25:
                i = NAT.index(v['step'][5:]); obliged('the over-long text typed is on record (%s)' % v['step'], tp, r'rec\.verified\{step=%s\}\.typed' % re.escape(v['step']), v['typed'], phrase='long'); obliged('the over-long name is saved cut to the limit (%s)' % v['step'], tp, r'save\.nations\[%d\]\.leader' % i, v['typed'][:25], phrase='long')
    tp = need('a name edited and kept by OK', newest(lambda r: r['play'] == 'P04' and r.get('autosave') and any(v['step'].startswith('name ') and 0 < len(v.get('typed', '')) <= 25 for v in r['verified'])))
    check('the task asks where the name lands (memory and save)', 'where the name lands' in task_text)
    if tp:
        for v in REC[tp]['verified']:
            if v['step'].startswith('name ') and 0 < len(v.get('typed', '')) <= 25:
                i = NAT.index(v['step'][5:]); obliged('the name lands in the nation record in game memory (%s)' % v['step'], tp, r'mem\.nations\[%d\]\.leader' % i, v['typed'], phrase='name lands', in_task=False); obliged('the name lands in the saved nation record (%s)' % v['step'], tp, r'save\.nations\[%d\]\.leader' % i, v['typed'], phrase='name lands', in_task=False)
    check('the task asks for the defaults when the form opens from New Game', 'defaults when it opens from new game' in task_text)
    tp = need('the form as it opens (the default form)', newest(lambda r: 'default' in r['forms'] and r['play'] == 'P01'))
    if tp:
        obliged('the default form has every tick clear', tp, r'form\.default\.checks', [0] * 16, phrase='ticks clear', in_task=False); obliged('the default form has every name box greyed', tp, r'form\.default\.edit_enabled', [0] * 16, phrase='greyed', in_task=False)
    tp = need('an edit attempted on a computer nation\'s box', newest(lambda r: 'greyed_edit' in r))
    if tp:
        for v in REC[tp]['verified']:
            if v['step'].startswith('greyed name box'): obliged('the greyed computer box refuses typing (%s)' % v['step'], tp, r'rec\.verified\{step=%s\}\.unchanged' % re.escape(v['step']), True, phrase='computer')
    tp = need('a name edited then the nation unticked', newest(lambda r: any(v['step'].startswith('tick ') and v['step'].endswith(' off') for v in r['verified'])))
    if tp:
        for v in REC[tp]['verified']:
            if v['step'].startswith('tick ') and v['step'].endswith(' off'): obliged('an untick restores the drawn leader (%s)' % v['step'], tp, r'rec\.verified\{step=%s\}\.post\.text' % re.escape(v['step']), v['stored'])
    tp = need('Cancel pressed with a tick and an edit made', newest(lambda r: verified(r, 'press Cancel') and any(v['step'].startswith('tick ') for v in r['verified']) and any(v['step'].startswith('name ') for v in r['verified'])))
    if tp: obliged('Cancel after ticks and an edit: no human flag in the records', tp, r'mem\.nations\[\*\]\.human', 0)
    tp = need('Cancel pressed on the untouched form', newest(lambda r: verified(r, 'press Cancel') and not any(v['step'].startswith('tick ') for v in r['verified'])))
    if tp: obliged('Cancel on the untouched form: the drawn names are the nation records\'', tp, r'form\.default\.rows_match_nations', True)
    te = need('the form closed by the Escape key', newest(lambda r: verified(r, 'key Escape'))); tr = need('the form closed by the Return key', newest(lambda r: verified(r, 'key Return')))
    if te: obliged('Escape discards the ticks', te, r'mem\.nations\[\*\]\.human', 0)
    if tr: obliged('Return acts as OK', tr, r'save\.humans', sorted(hum(REC[tr])))
    seeds = {r['seed'] for r in EVID.values()}; check('required (task Done-when): three or more seeds', len(seeds) >= 3, str(seeds))
    tn = need('a second New Game with another seed in one process', newest(lambda r: len({ng['seed'] for ng in r.get('new_games', [])}) >= 2))
    if tn: obliged('a second New Game draws again', tn, r'form\.first_default\.names', None, '!=')
    # ---- the functions of the handlers named in the task are each cited by a derived rule (the handlers come from the task file, not from the finding)
    try: handlers = sorted(set(re.findall(r'TPickLeaders_\w+', open(task, encoding='utf-8').read())))
    except OSError: handlers = []
    check('the task names the four handlers of the form', len(handlers) >= 4, str(handlers))
    cited_fns = set()
    for r in T.get('rules', []):
        if r['tag'] == '[derived]':
            for s in r['source'].split(','):
                m = re.fullmatch(r'(?:nl:)?(\w+):\d+', s.strip())
                if m: cited_fns.add(m.group(1))
    for h in handlers: check('handler %s of the task is read by a derived rule' % h, h in cited_fns)
    for fnn in ('TPremierForm_NewGame', 'TPremierForm_NewPlayer', 'TPremierForm_NewNation', 'FUN_00448aa4', 'FUN_004481a0', 'FUN_00449078'):
        check('function %s (caller or callee the method names) is read by a derived rule' % fnn, fnn in cited_fns and fnn in FNLINES)
    # ---- obligations DERIVED FROM THE CODE: every branch arm of the functions that decide a rule of the form must be claimed by a derived row (`branch` check, the arm's line read by the row), and every statement line of them must be read by a line-addressed code check
    OBLIGED = ['TPickLeaders_InitializeForm', 'TPickLeaders_HumanOrComputer', 'TPickLeaders_OK', 'TPickLeaders_Cancel', 'FUN_00448fd8', 'FUN_00449050', 'FUN_00449078', 'TPremierForm_NewGame']       # every statement and every arm
    ARMS_ONLY = ['TPremierForm_NewPlayer', 'TPremierForm_NewNation']                                                                                                                      # every arm (the statements are the callers' glue)
    derived_items = [it for rr in T.get('rules', []) if rr['tag'] == '[derived]' for it in ROWITEMS.get(rr['id'], [])]
    boiler = re.compile(r'^(?:[{}]|else \{|do \{|\} while.*|return;|void \w+\(.*|undefined.*|char .*;|int .*;|short .*;|uint .*;|byte .*;|\w+ \*?\w+;|\*in_FS_OFFSET = &?\w+;|\w+ = &stack0x.*|\w+ = &UNK_\w+;|\w+ = &DAT_\w+;|puStack_\w+ = .*|uStack_\w+ = .*|/\*.*|FUN_004032fc\(.*\);|[\w ]+ \*?\w+\([^;]*\)|\w+ = \w+ \+ -?1;|\w+ = \w+ \+ 0x[0-9a-f]+;|[a-z]Var\d = (?:0|0x10);|)$')
    for fn in OBLIGED + ARMS_ONLY:
        if not check('obliged function %s is in the extract' % fn, fn in FNLINES): continue
        arms_ = branches.arms([(k[1], EXT[k]) for k in FNLINES[fn]])
        for ln, arm in sorted(arms_): check('branch arm %s:%d %s of the code has a derived row that claims it (a `branch` check whose line the row reads)' % (fn, ln, arm), (fn, ln, arm) in BRANCH_CLAIMS)
        for k in (FNLINES[fn] if fn in OBLIGED else []):
            t = norm(EXT[k])
            if boiler.match(t) or t.startswith('//') or k[1] == FNLINES[fn][0][1]: continue
            if k[0] == 'nl' and re.match(r'^\d+$', t): continue
            check('statement line %s:%d of %s (%s) is read by a line-addressed code check of a derived row' % (fn, k[1], fn, t[:50]), any(reads_line([it], k, fn, strict=True) for it in derived_items))
    # ---- every ok recording of runner 2 is covered by a rule row, every earlier recording is audited but not cited
    cited_tags = set()
    for r in T.get('rules', []):
        for e in r['evidence'].split(';'):
            mm = re.match(r'(LF_%s_b\d+)[_:]' % PLAY_ID, e.strip())
            if mm: cited_tags.add(mm.group(1))
    for pid in sorted({r['play'] for r in EVID.values()}): check('play %s: a recording of runner 2 is cited by a rule row' % pid, any(REC[t]['play'] == pid for t in cited_tags))
    # ---- every recording: its files, its clicks, its steps
    def kind_of(step):
        """the kind of a verified step; None for a label that is not one of the runner's step kinds (an unknown label is refused: it would carry no postcondition)"""
        for k in ('tick ', 'name ', 'greyed name box', 'press ', 'key ', 'space on tick', 'tab to', 'tab walk', 'reset', 'menu open', 'menu close', 'menu item', 'confirm ', 'close start boxes'):
            if step.startswith(k): return k
        return None
    for tag, r in REC.items():
        if r['status'] != 'ok': continue
        what = 'recording %s (play %s)' % (tag, r['play']); v2 = r.get('runner') in (2, 3)
        check('%s has a form record or a recorded New Game' % what, bool(r['forms']) or bool(r.get('new_games')) or any(v['step'] == 'File > New' for v in r['verified']), '')
        for step, f in r['forms'].items():
            file_ok(f['png'] if v2 else '%s_%s_form.png' % (tag, step), what, f.get('png_sha') if v2 else None)
            if tag in EVID:
                cs_ = parse_raw(f['raw']); rr_ = rows_of(cs_, NAT)
                check('%s: form %s: the recorded rows and focus equal the audit\'s own parse of the retained helper output (16 rows found)' % (what, step), len(rr_) == 16 and f['rows'] == summary_of(rr_) and f['focus'] == [c['cls'] + ':' + c['text'] for c in cs_ if c['focus']], 'recorded summary differs from the raw output')
        for key, sc in r.get('screens', {}).items(): file_ok(sc['png'], what, sc['png_sha'])
        if r.get('autosave'):
            p = file_ok(r['autosave'], what)
            if p: check('%s autosave hash equals the one in the record' % what, sha(p) == r['autosave_sha'])
            s = save_view(tag); mem = dump_state(tag, 'state') if tag in EVID else r['state']
            if s and len(r.get('new_games', [])) == 1: check('%s: the save and the game memory agree on every human flag and leader (the state is of the one game that wrote the autosave)' % what, [(n['leader'], bool(n['human'])) for n in s['nations']] == [(n['leader'], bool(n['human'])) for n in mem['nations']], 'save vs memory')
            if s and tag in EVID and len(r.get('new_games', [])) == 1: check('%s: the save and the game memory hold the same 26 bytes of every leader field (extracted independently from the autosave and from the raw dump, past the NUL as well)' % what, [n['leader_raw_hex'] for n in s['nations']] == [n['leader_hex'] for n in mem['nations']], 'save vs memory bytes')
        if r.get('dumps'):
            for key, d in r['dumps'].items():
                for fk in ('nations_bin', 'globals_bin'):
                    p = file_ok(d[fk], what)
                    if p: check('%s: dump %s %s hash equals the one in the record' % (what, key, d[fk]), sha(p) == d[fk + '_sha'])
                st = dump_state(tag, key) if tag in EVID else None
                if st:
                    js = r[key]
                    check('%s: state %s: the recorded JSON equals what the raw dumps decode to (every nation field, the turn order, the current nation, the calendar)' % (what, key),
                          js['nations'] == st['nations'] and js['turn_order'] == st['turn_order'] and js['cur_nation'] == st['cur_nation'] and js['seat_0x4a032c'] == st['seat_0x4a032c'] and js['calendar'] == st['calendar'], 'JSON vs dump')
            if tag in EVID: check('%s: an autosave listing is recorded for the state reads (the first-game and before-new states are aliases of the dump kept by after_ok)' % what, 'state' in r['autosave_seen'] and set(r['autosave_seen']) <= set(r['dumps']), '%s vs %s' % (sorted(r['autosave_seen']), sorted(r['dumps'])))
        if r.get('nations_bin'):
            p = file_ok(r['nations_bin'], what)
            if p: check('%s memory dump hash equals the one in the record' % what, sha(p) == r['nations_bin_sha'])
            if not v2:
                m = re.match(r'%s_(after_\w+)_nations\.bin' % re.escape(tag), r['nations_bin'])
                if m: file_ok('%s_%s_screen.png' % (tag, m.group(1)), what)
            b = open(art_path(r['nations_bin']), 'rb').read() if art_path(r['nations_bin']) else b''
            if b: check('%s memory dump equals the nation hashes of the record' % what, [hashlib.sha256(b[n * 1172:(n + 1) * 1172]).hexdigest() for n in range(16)] == [n['sha'] for n in r['state']['nations']])
        cl = r['clicks']; ver = r['verified']; ks = r['keys']
        if v2: check('%s: every click has a recorded reason' % what, all(c.get('why') for c in cl), str([c for c in cl if not c.get('why')]))
        if not v2:
            for c in cl:
                m = re.match(r"control (\w+) '.*' at (\d+),(\d+) (\d+)x(\d+)$", c['why'] or '')
                if m: check('%s: click %s,%s lies inside the control its reason names (%s; an earlier runner: the rectangle is in the reason only, no pointer record)' % (what, c['x'], c['y'], c['why'][:40]), int(m.group(2)) <= c['x'] < int(m.group(2)) + int(m.group(4)) and int(m.group(3)) <= c['y'] < int(m.group(3)) + int(m.group(5)))
            continue
        # ---- runner 2: pointer, target and step of every click; postconditions recomputed from the recorded states
        for i, c in enumerate(cl):
            nm = '%s: click %d' % (what, i)
            try:
                if not check(nm + ' records the pointer read back from the X server and a target', isinstance(c.get('pointer'), dict) and isinstance(c.get('target'), dict), str(sorted(c))): continue
                check(nm + ' went where the pointer was read (%s,%s)' % (c['x'], c['y']), (c['pointer'].get('x'), c['pointer'].get('y')) == (c['x'], c['y']), str(c['pointer']))
                t = c['target']
                if t.get('src') in ('win_state', 'win_controls'):
                    f = t['line'].split('\t'); n_f = 14 if t['src'] == 'win_state' else 6
                    if not check(nm + ' target line has %d fields' % n_f, len(f) == n_f, str(f[:3])): continue
                    cls_, x_, y_, w_, h_ = f[0], int(f[2]), int(f[3]), int(f[4]), int(f[5])
                    check(nm + ' lies inside the rectangle of the helper\'s own line for the control (%d,%d %dx%d)' % (x_, y_, w_, h_), x_ <= c['x'] < x_ + w_ and y_ <= c['y'] < y_ + h_, t['line'][:60])
                    check(nm + ' target geometry equals the helper\'s line', (t['cls'], t['x'], t['y'], t['w'], t['h']) == (cls_, x_, y_, w_, h_))
                    mm = re.match(r"control (\w+) '.*' at (\d+),(\d+) (\d+)x(\d+)$", c['why'] or '')
                    check(nm + ' reason names the same control as the helper\'s line', bool(mm) and (mm.group(1), int(mm.group(2)), int(mm.group(3)), int(mm.group(4)), int(mm.group(5))) == (cls_, x_, y_, w_, h_), c['why'][:60])
                elif t.get('src') == 'ocr': check(nm + ' is the OCR word %r at the hit' % t.get('word'), (t['x'], t['y']) == (c['x'], c['y']) and t.get('word') in ('file', 'new', 'game'), str(t)[:80])
                elif t.get('src') == 'xdotool getmouselocation': check(nm + ' is a click on the bare root window: the pointer window is the root id', t.get('pointer', {}).get('window') == t.get('root') == c['pointer'].get('window'), str(t)[:80])
                else: check(nm + ' has a known target source', False, str(t)[:80])
            except (KeyError, IndexError, TypeError, ValueError) as e_:
                check(nm + ' is well-formed (its record lacks a field the audit reads)', False, repr(e_))
        covered_c = []; covered_k = []
        for i, v0 in enumerate(ver):
            nm = '%s: step %d (%s)' % (what, i, v0.get('step'))
            try:
                v = step_view(tag, v0) if tag in EVID else v0                       # evidence: the form states of a step are recomputed from the retained raw helper output
                if not check(nm + ' records ok, attempts and its clicks and keys', all(k in v for k in ('ok', 'attempts', 'clicks', 'keys')), str(sorted(v))): continue
                if not check(nm + ' is one of the runner\'s step kinds (an unknown label is refused)', kind_of(v['step']) is not None, v['step']): continue
                if tag in EVID and kind_of(v['step']) in ('tick ', 'name ', 'space on tick', 'greyed name box'):
                    if not check(nm + ' retains the raw helper output before and after the step', all(isinstance(v0.get(k_), str) and len(rows_of(parse_raw(v0[k_]), NAT)) == 16 for k_ in ('raw_before', 'raw_after')), 'raw_before/raw_after missing'): continue
                    for k_ in ('rows_before', 'rows_after', 'post', 'others_unchanged', 'unchanged', 'read'):
                        if k_ in v0: check(nm + ' recorded %s equals what the raw helper output gives' % k_, v0[k_] == v[k_], '%s vs %s' % (str(v0[k_])[:80], str(v[k_])[:80]))
                c0, c1 = v['clicks']; k0, k1 = v['keys']
                covered_c += list(range(c0, c1)); covered_k += list(range(k0, k1))
                kd = kind_of(v['step']); sc = cl[c0:c1]; sk = ks[k0:k1]
                if kd in ('tab walk', 'tab to'): check(nm + ' attempts is the number of Tab keys sent (and the walk is bounded)', v['attempts'] == len([k for k in sk if k.get('keys') == ['Tab']]) and v['attempts'] <= 24 and not sc, '%s vs %d keys' % (v['attempts'], len(sk)))
                else: check(nm + ' attempts is a bounded integer', isinstance(v['attempts'], int) and 0 <= v['attempts'] <= 3, str(v['attempts']))
                if kd in ('tick ', 'press ', 'greyed name box', 'name '):
                    want_cls = {'tick ': 'TCheckBox', 'press ': 'TButton', 'greyed name box': 'TEdit', 'name ': 'TEdit'}[kd]
                    check(nm + ' every click is a click on a %s' % want_cls, len(sc) >= 1 and all(c['target'].get('cls') == want_cls for c in sc), str([c['target'].get('cls') for c in sc]))
                if kd in ('tick ', 'press ', 'name '): check(nm + ' clicks equal the attempts', len(sc) == v['attempts'], '%d clicks, %d attempts' % (len(sc), v['attempts']))
                if kd == 'reset': check(nm + ' is one click and Escape, Escape', len(sc) == 1 and [k.get('keys') for k in sk] == [['Escape'], ['Escape']], str(len(sc)))
                if kd in ('tick ', 'name ', 'space on tick'): check(nm + ' the other 15 rows are unchanged (recomputed from the rows before and after)' if tag in EVID else nm + ' records that the other 15 rows are unchanged', v.get('others_unchanged') is True, str(v.get('others_unchanged')))
                if kd == 'greyed name box' and tag in EVID: check(nm + ' all 16 rows are the same before and after (recomputed)', v['unchanged'] is True, 'rows differ')
                if kd in ('tick ',) and tag in EVID: check(nm + ' the tick box changed state (before %s, after %s)' % (v['rows_before'][NAT.index(v['step'].split()[1])][1], v['rows_after'][NAT.index(v['step'].split()[1])][1]), v['rows_before'][NAT.index(v['step'].split()[1])][1] != v['rows_after'][NAT.index(v['step'].split()[1])][1])
                if not v['ok']: check(nm + ' is a failed attempt of a retried transition (only menu transitions may retry)', kd in ('menu open', 'menu item', 'menu close'), kd)
                if kd == 'tick ' and v['step'].endswith(' on'):
                    p = v['post']; check(nm + ' name box woke at once: enabled, focused, whole text selected (selection 0 to its length %d)' % len(p['text']), (p['check'], p['edit_enabled'], p['edit_focus'], p['sel0'], p['sel1']) == (1, 1, 1, 0, len(p['text'])) and p['textlen'] == len(p['text']), str(p))
                    file_ok(v['post_png'], what, v['post_png_sha'])
                if kd == 'tick ' and v['step'].endswith(' off'):
                    p = v['post']; check(nm + ' name box greyed, unfocused, the stored leader back', (p['check'], p['edit_enabled'], p['edit_focus']) == (0, 0, 0) and p['text'] == v['stored'], str(p))
                    file_ok(v['post_png'], what, v['post_png_sha'])
                if kd == 'name ':
                    st = v['stages']; check(nm + ' focus, whole text selected, deleted, typed: each read back', st['focus']['edit_focus'] == 1 and st['selected']['sel0'] == 0 and st['selected']['sel1'] == len(st['focus']['text']) and st['deleted']['text'] == '' and v['read'] == v['typed'][:25], str(st)[:200])
                if kd == 'space on tick': check(nm + ' recorded the name box state after the key', 'post' in v and v['before'][1] != v['after'][1], str(v.get('post')))
                if kd == 'menu open': check(nm + ' one click on the bar word and the dropdown word seen (or a failed attempt without it)', (v['hit'] is not None) == bool(v['ok']) and len(sc) <= 1, str(v.get('hit')))
                if kd == 'menu item': check(nm + ' is one click on the dropdown word', len(sc) == 1 and sc[0]['target'].get('word') == 'new', str(len(sc)))

            except (KeyError, IndexError, TypeError, ValueError) as e_:
                check(nm + ' is well-formed (its record lacks a field the audit reads)', False, repr(e_))
        for i, v in enumerate(ver):                      # order of the transitions: a reset before every menu opening, the dropdown seen before the item is clicked, the reset's point bare
            try:
                if kind_of(v['step']) == 'menu open': check('%s: step %d (%s) is directly preceded by a verified reset' % (what, i, v['step']), i > 0 and ver[i - 1]['step'] == 'reset' and ver[i - 1]['ok'] is True, str(ver[i - 1]['step'] if i else None))
                if kind_of(v['step']) == 'menu item': check('%s: step %d (%s) follows an opened menu' % (what, i, v['step']), i > 0 and ver[i - 1]['step'] == 'menu open file' and ver[i - 1]['ok'] is True, str(ver[i - 1]['step'] if i else None))
                if v['step'] == 'reset':
                    px, py = v['point']; check('%s: step %d (reset) clicked a point no window covers (%d,%d)' % (what, i, px, py), not any(w[2] <= px < w[2] + w[4] and w[3] <= py < w[3] + w[5] for w in v['windows']) and v['pointer']['window'] == v['root'] and [px, py] == [v['pointer']['x'], v['pointer']['y']], str(v['windows'])[:100])
            except (KeyError, IndexError, TypeError, ValueError) as e_:
                check('%s: step %d is well-formed for the order checks' % (what, i), False, repr(e_))
        if tag in EVID:
            try:
                pl = play_plans.plan_of(SCENARIOS, r['play'])
                got = [v['step'] for v in ver if v['ok']]
                check('%s: the successful steps are exactly the steps the play definition (scenarios.py) prescribes, in order' % what, got == pl.steps, '%s vs %s' % (got, pl.steps))
                check('%s: the New Games it started have the seeds the play definition prescribes %s' % (what, pl.seeds), [g_['seed'] for g_ in r['new_games']] == pl.seeds, str([g_['seed'] for g_ in r['new_games']]))
                check('%s: the Confirm answers (%d) are the ones the play definition prescribes' % (what, pl.confirms), sum(1 for v in ver if v['step'].startswith('confirm ')) == pl.confirms)
            except KeyError as e_: check('%s: the play is defined in scenarios.py' % what, False, repr(e_))
        check('%s: every click belongs to exactly one verified step' % what, sorted(covered_c) == list(range(len(cl))), '%s vs %d clicks' % (covered_c, len(cl)))
        check('%s: every key and typed text belongs to exactly one verified step' % what, sorted(covered_k) == list(range(len(ks))), '%s vs %d keys' % (covered_k, len(ks)))
        failed_menu = collections.Counter(kind_of(v['step']) for v in ver if not v['ok'])
        check('%s: failed menu attempts are bounded (at most 2 of each kind)' % what, all(n <= 2 for n in failed_menu.values()), str(failed_menu))
        yn = sum(1 for c in cl if re.match(r"control TButton '&(Yes|No)'", c['why'] or '')); check('%s: the Confirm answers clicked (%d) are one per Confirm box recorded' % (what, yn), yn == (1 if r.get('confirm_text') else 0), '')
        check('%s: the New Games it started each record their seed, equal to the seed of the forms they opened' % what, len(r['new_games']) >= 1 and all(isinstance(g_.get('seed'), int) for g_ in r['new_games']) and all(f['seed'] == r['new_games'][f['new_game']]['seed'] for f in r['forms'].values()), str(r['new_games']))
        check('%s: the first New Game used the seed the play declares' % what, r['new_games'][0]['seed'] == r['seed'], '%s vs %s' % (r['new_games'][0]['seed'], r['seed']))
    check('failed recordings are kept, not cited: %d recorded' % len(FAILED), all(f['status'] == 'FAILED' for f in FAILED))
    for f in FAILED:
        for fn in glob.glob(art + '%s_*' % f['_tag']) + glob.glob(art + 'saves/%s_*' % f['_tag']): file_ok(os.path.basename(fn), 'failed recording %s' % f['_tag'])
    # ---- remaining tables
    ruleids = set(RULE) | {r['id'] for r in T.get('controls', [])} | {r['id'] for r in T.get('facts', [])}
    def frag(t):
        """text as fragments are compared: markup removed, lower case, one space between words, no outer punctuation"""
        t = t.replace('**', '').replace('`', '').replace('*', '').lower(); t = re.sub(r'\s+', ' ', t); return t.strip(' .,;:')
    for r in T.get('clone', []):
        cites = [s.strip() for s in r['rules'].split(',') if s.strip()]
        for x in cites: check('clone row %s cites rule %s that exists' % (r['id'], x), x in ruleids)
        check('clone row %s names the original' % r['id'], bool(r['the original']))
        src_ = ' || '.join(frag(RULE[x]['rule'] + ' ' + RULE[x]['literal']) for x in cites if x in RULE)
        for fr_ in [f_.strip() for f_ in r['the original'].split(';') if f_.strip()]:
            if fr_ == '(not stated)': continue
            check('clone row %s: the fragment "%s" is a verbatim piece of a rule it cites (at least 3 words)' % (r['id'], fr_[:60]), len(fr_.split()) >= 3 and frag(fr_) in src_, 'not found in %s' % cites)
        coverage('clone row %s' % r['id'], r['the original'], [sy for x in cites for sy in SAYS.get(x, [])], derived=False)
    ps = {r['play']: r for r in T.get('plays', [])}
    check('plays table lists exactly the play ids recorded ok', set(ps) == set(PIDS_OK), '%s' % sorted(set(ps) ^ set(PIDS_OK)))
    nm_ = '|'.join(NAT)
    def explain(pid, cell, rec):
        """the `what` of a play, phrase by phrase: each phrase is understood (a known form) and TRUE of the recording's verified steps and resulting state; the labels of the steps it describes are consumed; every action step of the recording must be consumed by some phrase (nothing recorded is left unsaid, nothing said is unrecorded)"""
        okl = [v['step'] for v in rec['verified'] if v['ok']]
        pool = collections.Counter(l for l in okl if kind_of(l) in ('tick ', 'name ', 'greyed name box', 'press ', 'key ', 'space on tick', 'tab to', 'tab walk', 'confirm '))
        humans = set()
        for l in okl:
            mm = re.fullmatch(r'tick (\w+) (on|off)', l)
            if mm: (humans.add if mm.group(2) == 'on' else humans.discard)(NAT.index(mm.group(1)))
            mm = re.fullmatch(r'space on tick (\w+)', l)
            if mm: humans ^= {NAT.index(mm.group(1))}
        typed = [v['typed'] for v in rec['verified'] if v['ok'] and v['step'].startswith('name ')]
        st = dump_state(rec['_tag'], 'state'); ng = rec['new_games']
        st_ok = dump_state(rec['_tag'], 'state_first_game') if 'state_first_game' in rec['dumps'] else st          # the state a game left after OK (P09: its first game)
        closers = [l for l in okl if l in ('press OK', 'key Return')]
        W = {'one': 1, 'two': 2, 'six': 6, 'all sixteen': 16}
        def take(*lbls):
            for l in lbls:
                if pool[l] <= 0: return False
                pool[l] -= 1
            return True
        ph = [(r'the form as it opens', lambda m: bool(rec['forms'].get('default') or rec['forms'].get('first_default'))),
              (r'the draw', lambda m: bool(rec['forms'].get('default'))),
              (r'tab order of the first (\d+) presses', lambda m: any(v['step'] == 'tab walk' and v['attempts'] == int(m.group(1)) for v in rec['verified']) and take('tab walk')),
              (r'zero humans|nothing ticked', lambda m: not humans and all(n_['human'] == 0 for n_ in st['nations'])),
              (r'(one|two|six|all sixteen) humans?(?: \(([^)]*)\))?', lambda m: len(humans) == W[m.group(1)] and (m.group(2) is None or m.group(2).split(', ') == [NAT[i] for i in sorted(humans)])
                                                                                  and all(((n_['human'] == 1) == (i in humans)) for i, n_ in enumerate(st['nations'])) and take(*['tick %s on' % NAT[i] for i in sorted(humans)])),
              (r'tick (%s)(?: and (%s))?' % (nm_, nm_), lambda m: take(*['tick %s on' % x for x in m.groups() if x])),
              (r'(%s) ticked, edited and unticked' % nm_, lambda m: take('tick %s on' % m.group(1), 'name %s' % m.group(1), 'tick %s off' % m.group(1))),
              (r'rename (%s)|(%s) renamed' % (nm_, nm_), lambda m: take('name %s' % (m.group(1) or m.group(2)))),
              (r'an empty, a spaces-only, two equal, an over-long and an odd-character name', lambda m: sorted(len(t) for t in typed) == sorted([0, 3, 4, 4, 42, len('ünal-ö "Q" |;,')]) and '' in typed and '   ' in typed and len(typed) - len(set(typed)) == 1 and any(len(t) > 25 for t in typed) and any(not t.isascii() for t in typed) and take(*['name %s' % NAT[i] for i in range(6)])),
              (r'typing into the greyed (%s) box' % nm_, lambda m: take('greyed name box %s refuses typing' % m.group(1))),
              (r'Tab to the (%s) tick box' % nm_, lambda m: take('tab to %s tick box' % m.group(1))),
              (r'space on the (%s) tick box' % nm_, lambda m: take('space on tick %s' % m.group(1))),
              (r'OK', lambda m: take('press OK') and all(((n_['human'] == 1) == (i in humans)) for i, n_ in enumerate(st_ok['nations']))),
              (r'Cancel', lambda m: take('press Cancel') and all(n_['human'] == 0 for n_ in st['nations'])), (r'Escape', lambda m: take('key Escape') and all(n_['human'] == 0 for n_ in st['nations'])),
              (r'Return', lambda m: take('key Return') and all(((n_['human'] == 1) == (i in humans)) for i, n_ in enumerate(st_ok['nations']))),
              (r'File > New with a game running', lambda m: bool(rec.get('confirm_text')) and any(l == 'press OK' for l in okl)),
              (r'Confirm answered (Yes|No)', lambda m: take('confirm %s' % m.group(1))),
              (r'a second New Game with another seed after a game with a human', lambda m: len(ng) >= 2 and ng[1]['seed'] != ng[0]['seed'] and 'press OK' in okl and take('confirm Yes')),
              (r'New Game again', lambda m: len(ng) == 3 and ng[2]['seed'] == ng[1]['seed'])]
        for phrase in [x.strip() for x in cell.split(';') if x.strip()]:
            hit = [(rx, fn) for rx, fn in ph if re.fullmatch(rx, phrase)]
            if not check('plays table: %s "%s" is a phrase the audit understands' % (pid, phrase), len(hit) == 1, 'matches %d forms' % len(hit)): continue
            rx, fn = hit[0]; mm = re.fullmatch(rx, phrase)
            check('plays table: %s "%s" is true of the recording (its verified steps and the state it left)' % (pid, phrase), bool(fn(mm)), 'false for the recording')
        left = +pool
        check('plays table: %s says everything the recording did: steps left unsaid %s' % (pid, sorted(left)), not left)
    for pid, r in ps.items():
        recs = [x for x in EVID.values() if x['play'] == pid]
        if check('plays table: %s has a recording of the evidence runner' % pid, bool(recs)):
            pl_ = play_plans.plan_of(SCENARIOS, pid); seeds_ = []
            for sd in pl_.seeds:
                if not seeds_ or seeds_[-1] != sd: seeds_.append(sd)
            check('plays table: %s seed(s) "%s" equal the seeds the play definition (scenarios.py) prescribes %s' % (pid, r['seed'], seeds_), r['seed'] == ' then '.join(str(x) for x in seeds_), '%s vs %s' % (r['seed'], seeds_))
            check('plays table: %s outcome' % pid, r['outcome'] == 'ok' and recs[-1]['status'] == 'ok')
            explain(pid, r['what'], recs[-1])
    drawn_seeds = set()
    for r in T.get('draws', []):
        pid = r['play']; names = [x.strip() for x in spans(r['names (nation order)'])[0].split(';')]; slots = [int(x) for x in spans(r['slots'])[0].split(';')]
        cand = [t for t, x in EVID.items() if x['play'] == pid]
        if not check('draws row %s: a recording of runner 2 exists' % pid, bool(cand)): continue
        tg = cand[-1]; step = 'default' if 'default' in REC[tg]['forms'] else 'second_default'
        f = form_view(tg)[step]; drawn_seeds.add(str(f['seed']))
        check('draws row %s: the 16 names equal the names the form showed' % pid, names == f['names'], '%s vs %s' % (names[:3], f['names'][:3]))
        check('draws row %s: the seed %s is the seed the New Game that opened that form recorded (%s)' % (pid, r['seed'], f['seed']), str(f['seed']) == r['seed'], '%s vs %s' % (f['seed'], r['seed']))
        calc = [POOL[NAT[i]].index(n) if n in POOL[NAT[i]] else None for i, n in enumerate(names)]
        check('draws row %s: every name is in its nation\'s pool and its slot is the one recomputed' % pid, calc == slots, '%s vs %s' % (calc, slots))
    seen_seeds = {str(f['seed']) for r in EVID.values() for stp, f in form_view(r['_tag']).items() if stp in ('default', 'second_default')}
    check('the draws table covers every seed of which a recording of runner 2 opened a default form', drawn_seeds == seen_seeds, '%s vs %s' % (sorted(drawn_seeds), sorted(seen_seeds)))
    # ---- facts: every universal or numeric statement the finding makes about the records, each recomputed from the records
    for r in T.get('facts', []):
        rid = r['id']; items = [x for x in r['check'].split(' ;; ') if x.strip()]; check('%s has checks' % rid, bool(items))
        PCHECKS[:] = []; CUR['res'] = {}; ROWITEMS[rid] = items
        for it in items: run_check(rid, it, None, r)
        coverage('%s statement' % rid, r['statement'], SAYS[rid])
    # ---- counts (each recomputed from a source, never from the finding)
    cnt = {r['item']: r for r in T.get('counts', [])}
    def count_check(item, value):
        r = [v for k, v in cnt.items() if k.startswith(item)]
        if check('counts row present: ' + item, bool(r)): check('count %s: finding %s vs sources %s' % (item, r[0]['count'], value), int(r[0]['count']) == value)
    count_check('unique play ids recorded ok', len(PIDS_OK)); count_check('successful recordings (all runners)', len(OKREC)); count_check('successful recordings by the evidence runner', len(EVID))
    count_check('failed recordings', len(FAILED)); count_check('recordings in all', len(REC)); count_check('pool names', sum(len(v) for v in POOL.values()))
    count_check('form controls', sum(1 for o in allobjs if o['class'] in ('TPanel', 'TCheckBox', 'TEdit'))); count_check('objects of the resource', len(allobjs))
    # ---- every number and operation word of the Answer and of "What this does not establish" lies in a phrase that a row the item CITES derives from a source (not in the union of the numbers of those rows); a cited id that does not exist fails
    def section(title):
        m = re.search(r'^## %s\n(.*?)(?=^## |\Z)' % re.escape(title), TEXT, re.S | re.M); return m.group(1) if m else ''
    ALLIDS = set(RULE) | {r['id'] for r in T.get('controls', [])} | {r['id'] for r in T.get('facts', [])} | {r['id'] for r in T.get('clone', [])} | set(ps)
    def cited_ids(text):
        """the row ids a paragraph cites: single ids and ranges such as H01-H04 (a range expands to every id between its ends, each of which must exist)"""
        out = []
        for m in re.finditer(r'\b([A-Z])(\d{2})(?:-(?:([A-Z])?(\d{2})))?\b', text):
            a_, n0, b_, n1 = m.groups()
            if n1: out += ['%s%02d' % (a_, k) for k in range(int(n0), int(n1) + 1)]
            else: out.append(a_ + n0)
        return out
    for sec, item_re in (('Answer', r'^\d+\. '), ('What this does not establish', r'^- ')):
        items_ = []
        for l in section(sec).split('\n'):
            if re.match(item_re, l): items_.append(l)
            elif l.strip() and items_: items_[-1] += ' ' + l
        check('section "%s" has items' % sec, bool(items_))
        for it in items_:
            ids_ = sorted(set(cited_ids(it)))
            for i_ in ids_: check('section "%s", item "%s...": the cited id %s exists in a table of the finding' % (sec, it[:30], i_), i_ in ALLIDS)
            txt = re.sub(r'\([A-Z]\d{2}[^)]*\)', '', it); txt = re.sub(r'`?\b[A-Z]{1,3}\d{2}\b`?', '', txt); txt = re.sub(r'^\d+\. ', '', txt)
            coverage('section "%s", item "%s..."' % (sec, txt.strip()[:40]), txt, [sy for i_ in ids_ for sy in SAYS.get(i_, [])], derived=False, words=(sec == 'Answer'))
    # ---- lost qualifications (round-3 R4): a summary line (an Answer item, a rule, a fact, a clone row) that states a rule which has a branch in OK's human-to-computer arm must name that arm (O02) or the New Game scope
    QUAL = [(r'\bunticked row\b', r'\bO02\b', 'a statement about an unticked row names the human-to-computer branch of OK (O02)'),
            (r'\bdo(?:es)? not draw\b|\bnever draws\b', r'\bO02\b|human back into a computer', 'a "does not draw" statement names OK\'s human-to-computer branch (O02)'),
            (r'leave the same world', r'in a New Game', 'a "same world" statement is scoped to a New Game'),
            (r'\bOK with no tick\b', r'\bNew Game\b|\bO0[12]\b|\bT0[12]\b|\bC03\b|\bX0[28]\b', 'a statement about OK with no tick is scoped to a New Game')]
    for ln_ in open(finding, encoding='utf-8').read().split('\n'):
        if not (ln_.startswith('|') or re.match(r'\d+\. ', ln_)) or ln_.startswith('| id ') or ln_.startswith('|---'): continue
        for rx, req, why in QUAL:
            if re.search(rx, ln_, re.I): check('qualification: %s (line "%s...")' % (why, re.sub(r'\s+', ' ', ln_)[:50]), re.search(req, ln_) is not None, 'the line says %r but not %r' % (re.search(rx, ln_, re.I).group(0), req))
    if os.environ.get('AUDIT_SUGGEST'): json.dump(SUGGEST, open(os.environ['AUDIT_SUGGEST'], 'w'), indent=1)
    return checks[0], bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--finding', default=os.path.join(paths.ROOT, 'findings', '2026-10-06-leaders-form.md'))
    ap.add_argument('--data', default=paths.DATA); ap.add_argument('--artifacts', default=paths.ART)
    ap.add_argument('--exe'); ap.add_argument('--dat'); ap.add_argument('--task'); ap.add_argument('--out')
    a = ap.parse_args()
    n, bad = run(a.finding, a.data, a.artifacts, a.exe, a.dat, task=a.task)
    lines = ['claims audit of %s' % os.path.basename(a.finding), '%d checks, %d mismatches' % (n, len(bad)), 'requested --exe: %s; requested --dat: %s' % (a.exe, a.dat)] + ['MISMATCH ' + b for b in bad]
    print('\n'.join(lines))
    if a.out: print('written', write_new(a.out, '\n'.join(lines) + '\n'))
    sys.exit(0 if not bad else 1)

if __name__ == '__main__': main()
