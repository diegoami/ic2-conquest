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
import loader_offsets

ROOT = paths.ROOT
sys.path.insert(0, ROOT)
from state import sav as SAV

PLAY_ID = r'P\d+[a-z]?'
NUM_RE = re.compile(r'(?<![\w])(0x[0-9a-fA-F]+|\d[\d,]*)(?![\w])')

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

def item_numbers(item):
    """the numbers a check item states: its addressing (`code 56939-56941`, `code fn F`) is not a claim"""
    return numbers(re.sub(r'^code (?:fn \w+ |(?:nl:)?\d+(?:-(?:nl:)?\d+)? )', 'code ', item.strip()))

def fmtn(t):
    """a number as it was spelled"""
    return ('0x%x' % t[1]) if t[0] == 'x' else str(t[1])

def norm(s): return re.sub(r'\s+', ' ', s).strip()

def in_order(body, txt):
    """every part of `txt` (separated by ' ~~ ') occurs in `body`, in that order (whitespace normalised)"""
    pos = 0
    for part in [norm(x) for x in txt.split(' ~~ ')]:
        i = body.find(part, pos)
        if i < 0: return False
        pos = i + len(part)
    return True

def run(finding, data, art, exe=None, dat=None, quiet=True, task=None):
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
    EVID = {t: r for t, r in REC.items() if r['status'] == 'ok' and r.get('runner') == 2}      # what a rule may cite
    PIDS_OK = sorted({r['play'] for r in OKREC})
    cstr = lambda b: b.split(b'\0')[0].decode('latin1')
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
            s['nations'][n]['view_differs_from_default'] = (s['nations'][n]['view'] != [DEF['0x488'], DEF['0x486']])
        s['humans'] = [n['id'] for n in s['nations'] if n['human']]
        names = [n['leader'] for n in s['nations'] if len(n['leader'].strip()) >= 3]
        s['news_naming_a_leader'] = [x for x in s['news'] if any(nm in x for nm in names)]
        SAVE[tag] = s; return s
    def form_view(tag):
        r = REC[tag]; out = {}
        for step, f in r['forms'].items():
            rows = f['rows']; d = {'titles': [w[0] for w in f['windows']], 'focus': f['focus'], 'seed': f.get('seed')}
            for row in rows: d[row[0]] = {'check': row[1], 'cb_enabled': row[2], 'text': row[3], 'edit_enabled': row[4], 'limit': row[5]}
            by = {row[0]: row for row in rows}
            d['names'] = [by[n][3] for n in NAT]; d['checks'] = [by[n][1] for n in NAT]; d['edit_enabled'] = [by[n][4] for n in NAT]; d['cb_enabled'] = [by[n][2] for n in NAT]; d['limits'] = [by[n][5] for n in NAT]
            d['names_in_pool'] = all(by[n][3] in POOL.get(n, []) for n in NAT)
            ys = []
            for line in f['raw'].splitlines():
                p = line.split('\t')
                if len(p) == 14 and p[0] == 'TPanel': ys.append((int(p[3]), p[1].strip()))
            d['order'] = [n for _, n in sorted(ys)]
            mem = r.get('state')
            if mem: d['rows_match_nations'] = all(by[n][3] == mem['nations'][i]['leader'] and n == mem['nations'][i]['name'] for i, n in enumerate(NAT))
            out[step] = d
        return out
    def mem_view(tag):
        r = REC[tag]; s = r.get('state')
        if s is None: return None
        s = json.loads(json.dumps(s))
        if r.get('nations_bin'):
            p = art_path(r['nations_bin'])
            if p:
                b = open(p, 'rb').read()
                s['nations_bin_leader'] = [cstr(b[n * 1172 + 0x0B: n * 1172 + 0x0B + 26]) for n in range(16)]
        return s
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
        if name == 'rec': return REC[tag]
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
        if kind == 'score':
            vals = sorted((n['score_0x440'], n['name']) for r in recs for st in [r.get('state'), r.get('state_after_cancel'), r.get('state_first_game'), r.get('state_before_new')] if st for n in st['nations'])
            if not vals: return False, 'no states'
            return True, {'min': vals[0][0], 'max': vals[-1][0], 'min_nation': vals[0][1], 'max_nation': vals[-1][1], 'count': len(vals)}[what]
        if kind == 'turn_order':
            by = collections.defaultdict(set)
            for r in recs:
                st = r.get('state')
                if st: by[r['new_games'][-1]['seed']].add(tuple(st['turn_order']))      # the seed of the New Game that drew the state
            if not by: return False, 'no states'
            return True, {'one_per_seed': all(len(v) == 1 for v in by.values()), 'differs_between_seeds': len({next(iter(v)) for v in by.values()}) == len(by), 'seeds': len(by)}[what]
        if kind == 'initial_nation':                                 # every state read where no turn has started: the current nation is the first entry of the order
            sts = [r['state'] for r in recs if r.get('state') and not r.get('autosave') and r['state']['calendar']['season'] is not None]
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
    def reads_line(items, k, fn):
        """a check of the row reads the extract's line k (a `code` check naming it or a range holding it, or a `code fn` check of its function)"""
        for it in items:
            m = re.match(r'code ((?:nl:)?\d+)(?:-((?:nl:)?\d+))? (?:has|seq) ', it)
            if m:
                a = code_key(m.group(1)); b = code_key(m.group(2)) if m.group(2) else a
                if a[0] == k[0] and a[1] <= k[1] <= b[1]: return True
            if re.match(r'code fn %s ' % re.escape(FNOF.get(k) or '-'), it): return True
        return False
    def run_check(rid, item, lit, row):
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
            good = (norm(txt) in body) if op == 'has' else in_order(body, txt)
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
        m = re.fullmatch(r'pool (size|nations|bytes_per_name|read_length|offset|duplicates_across_nations|(\w+) len) == (.+)', item)
        if m:
            what, nat, rhs = m.groups(); got = {'size': sum(len(v) for v in POOL.values()), 'nations': len(POOL), 'bytes_per_name': pool_len // (len(POOL) * 12) if POOL else None, 'read_length': pool_len, 'offset': off_calc,
                                                 'duplicates_across_nations': dups_text}.get(what, len(POOL.get(nat, [])) if nat else None)
            want = lit if rhs == '@literal' else int(rhs); check(name, got == want, 'recomputed %r' % (got,)); return
        m = re.fullmatch(r'calc ([0-9a-fA-Fx +*()-]+) == (0x[0-9a-fA-F]+|\d+)', item)
        if m:
            try: got = eval(m.group(1), {'__builtins__': {}}, {})
            except Exception as e: got = repr(e)
            check(name, got == int(m.group(2), 0), 'the expression is %r' % (got,)); return
        m = re.fullmatch(r'sav (\w+) == (\d+)', item)
        if m: check(name, getattr(SAV, m.group(1), None) == int(m.group(2)), 'state/sav.py has %r' % getattr(SAV, m.group(1), None)); return
        m = re.fullmatch(r'scan (\w+) (\w+) == (.+)', item)
        if m:
            kind, what, rhs = m.groups(); ok, got = scan(kind, what)
            if not check(name + ' scanned', ok, str(got)): return
            check(name, got == json.loads(rhs), 'the recordings give %r' % (got,)); return
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
        m = re.fullmatch(r'(%s) ((?:[^\s{]|\{[^}]*\})+) ?(==|!=|has|startswith|absent|len==|list==|list!=)? ?(.*)' % PLAY_ID, item)
        if m:
            pid, path, op, rhs = m.groups()
            if not check(name + ' play is cited by tag in this row', pid in CUR['res'], pid): return
            ok, v = evaluate(pid, path)
            if op == 'absent':
                if check(name, not ok, 'the path exists'): PCHECKS.append((pid, path, 'absent', None))
                return
            if not check(name + ' path exists', ok, str(v)): return
            try: want = parse_value(rhs, lit)
            except Exception as e: check(name + ' value parses', False, '%r: %r' % (rhs, e)); return
            vals = list(v) if isinstance(v, ALLV) else [v]
            if op == '==': good = all(x == want for x in vals)
            elif op == '!=': good = all(x != want for x in vals)
            elif op == 'has': good = all((want in x) for x in vals)
            elif op == 'startswith': good = all(isinstance(x, str) and x.startswith(want) for x in vals)
            elif op == 'len==': good = all(hasattr(x, '__len__') and len(x) == want for x in vals)
            elif op == 'list==': good = list(vals) == want
            elif op == 'list!=': good = list(vals) != want
            else: good = False
            if check(name, good, 'source has %r, claim %r' % (v if len(repr(v)) < 160 else repr(v)[:160], want)):
                PCHECKS.append((pid, path, op, want)); m3 = re.fullmatch(PLAY_PATH, rhs.strip())
                if m3: PCHECKS.append((m3.group(1), m3.group(2), 'rhs', None))
            return
        check(name + ' parses', False, 'unknown check form')
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
    BOUND = set()                                                  # every number a claim of the finding is bound to by a passing check
    ROWBOUND = {}                                                  # row id -> the numbers that row's checks bind
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
        BOUND |= numbers(' '.join([r['left'], r['top'], r['tab'], r['props'], r['literal']])); ROWBOUND[rid] = numbers(' '.join([r['left'], r['top'], r['tab'], r['props'], r['literal']]))
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
    RULE = {}; ROW_OBL = {}
    LEX = (('at least', 'FUN_00448fd8'), ('raised', 'FUN_00448fd8'), ('maximum', 'FUN_00448fd8'))       # a word that claims an operation: the row must check that operation in the code
    def resolve_row(rid, r, items):
        """play id -> tag from the files the row cites; every play id the checks use must be cited, and every cited play id must be used"""
        ev = [e.strip() for e in r['evidence'].split(';') if e.strip()]
        pl = [e for e in ev if re.fullmatch(PLAY_ID, e)]; fl = [e for e in ev if e not in pl]
        res = {}
        for pid in pl:
            tags = {re.match(r'(LF_%s_b\d+)_' % pid, f).group(1) for f in fl if re.match(r'LF_%s_b\d+_' % pid, f)}
            if not check('%s evidence: play %s is cited with files of exactly one recording (tags %s)' % (rid, pid, sorted(tags)), len(tags) == 1): continue
            tag = tags.pop()
            if not check('%s evidence: recording %s exists, is ok and was made by the pointer-verified runner (runner 2): earlier recordings are kept but are not evidence' % (rid, tag), tag in EVID, 'recorded: %s' % (REC[tag].get('runner') if tag in REC else 'absent')): continue
            check('%s evidence: recording %s is a recording of play %s' % (rid, tag, pid), REC[tag]['play'] == pid)
            res[pid] = tag
        for f in fl:
            mm = re.match(r'LF_(%s)_b\d+_' % PLAY_ID, f)
            check('%s evidence: file %s belongs to a cited play' % (rid, f), bool(mm) and mm.group(1) in pl, f)
        used = {re.match(r'(%s) ' % PLAY_ID, it).group(1) for it in items if re.match(r'(%s) ' % PLAY_ID, it)}
        used |= {m2 for it in items for m2 in re.findall(r'(?:== |!= )(%s) \S' % PLAY_ID, it)}
        used |= {m2.group(1) for it in items for m2 in [re.match(r'dfm order == (%s) ' % PLAY_ID, it)] if m2}
        check('%s evidence: the plays cited (%s) are exactly the plays the checks use (%s)' % (rid, sorted(pl), sorted(used)), set(pl) == used)
        return res, fl
    def needs(tag, path):
        """the artifact files of recording `tag` that a check path reads: the screenshot of the form step, the autosave, the memory dump (and the screen taken with it for a window title), the step's immediate screenshot"""
        r = REC[tag]; out = set(); head = re.split(r'[.\[{]', path)[0]
        sub = re.split(r'[.]', path)
        if head == 'form': out.add(r['forms'][sub[1]]['png'])
        elif head == 'save': out.add(r['autosave'])
        elif head == 'mem':
            if r.get('nations_bin'): out.add(r['nations_bin'])
            if 'windows' in path:
                for k in ('after_ok', 'after_cancel', 'after_escape'):
                    if k in r.get('screens', {}): out.add(r['screens'][k]['png'])
        elif head == 'rec':
            s1 = re.split(r'[\[{]', sub[1])[0] if len(sub) > 1 else ''
            if s1 == 'forms': out.add(r['forms'][sub[2]]['png'])
            elif s1 in ('state', 'state_after_cancel', 'state_after_no', 'state_first_game', 'state_before_new'):
                screen = {'state': ('after_ok', 'after_cancel', 'after_escape'), 'state_after_cancel': ('after_cancel',), 'state_after_no': ('after_no',), 'state_first_game': (), 'state_before_new': ()}[s1]
                if s1 in ('state', 'state_after_cancel') and r.get('nations_bin'): out.add(r['nations_bin'])
                if 'windows' in path:
                    for k in screen:
                        if k in r.get('screens', {}): out.add(r['screens'][k]['png'])
            elif s1 == 'verified':
                m2 = re.search(r'\{step=([^}]*)\}', path)
                if m2:
                    st = [v for v in r['verified'] if v['step'] == m2.group(1)]
                    if st and st[0].get('post_png'): out.add(st[0]['post_png'])
            elif s1 == 'tab_walk': out.add(r['forms']['after_tabs']['png'])
        elif head == 'view': out.add(r['forms']['after_tabs']['png'])
        return {x for x in out if x}
    for r in T.get('rules', []):
        rid = r['id']; check('rule id unique %s' % rid, rid not in RULE, rid); RULE[rid] = r
        tag = r['tag']; check('%s tag is [derived] or [confirmed]' % rid, tag in ('[derived]', '[confirmed]'), tag)
        sp = spans(r['literal']); lit = sp[0] if sp else None
        if r['literal'] != '-': check('%s literal is one piece' % rid, len(sp) == 1, str(sp))
        items = [x for x in r['check'].split(' ;; ') if x.strip()]
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
            res, fl = resolve_row(rid, r, items); CUR['res'] = res
            check('%s confirmed rows cite a play' % rid, bool(res))
            for f in fl:
                if re.match(r'LF_%s_b\d+_' % PLAY_ID, f): file_ok(f, rid)
            check('%s confirmed rows cite a screenshot' % rid, any(f.endswith('.png') for f in fl), r['evidence'])
            check('%s confirmed rows have a play check' % rid, any(re.match(PLAY_ID + ' ', it) for it in items))
        for it in items: run_check(rid, it, lit, r)
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
        # ---- every number of the prose is bound to a passing check of the row (or to the row's literal); an operation a word claims is checked in the code
        bound = set().union(*[item_numbers(it) for it in items]) | numbers(r['literal'] if r['literal'] != '-' else '')
        for p_, path_, op_, wnt_ in PCHECKS:
            if isinstance(wnt_, (int, list)) and not isinstance(wnt_, bool): bound |= numbers(json.dumps(wnt_))
        BOUND |= bound; ROWBOUND[rid] = bound
        for nmb in sorted(numbers(re.sub(r'`[^`]*[A-Za-z]{3,}[^`]* [^`]*`', '', r['rule']))):          # a literal quoted in the prose (a caption, a name) is checked byte for byte by the literal's own check
            check('%s prose number %s is bound to a check of the row (the checks mention %s)' % (rid, fmtn(nmb), [fmtn(x) for x in sorted(bound)][:14]), nmb in bound)
        for word, fn in LEX:
            if word in r['rule'].lower(): check('%s prose says %r: the row must check the operation of %s in the code' % (rid, word, fn), any(it.startswith('code fn %s seq' % fn) for it in items))
    # ---- the claims every recorded play makes must be in the rules (obligations from the recordings and the task, not from the finding)
    allp = [(rid, p) for rid, pcs in ROW_OBL.items() for p in pcs if RULE[rid]['tag'] == '[confirmed]']
    task_text = open(task, encoding='utf-8').read().lower() if os.path.exists(task) else ''
    def obliged(name, tag, regex, want=None, op='==', phrase=None):
        """the finding must have a passing check `<play> <path> <op> <value>` of this play whose path matches `regex` and whose value is `want` (None: any); with `phrase` (a phrase of the task's own questions) the check
        must be in a [confirmed] row whose rule text contains that phrase, so a claim cannot be carried only by an aggregate row after its own row is removed"""
        if phrase is not None: check('the task asks about "%s" (the phrase is in %s)' % (phrase, os.path.basename(task)), phrase in task_text)
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
    t0h = need('0 humans ticked, OK', newest(lambda r: hum(r) == [] and verified(r, 'press OK') and r.get('nations_bin')))
    if t0h: obliged('0 humans ticked, OK: no human flag in the records', t0h, r'mem\.nations\[\*\]\.human', 0); obliged('0 humans ticked, OK: no autosave', t0h, r'rec\.autosave', None, 'absent')
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
    # ---- every ok recording of runner 2 is covered by a rule row, every earlier recording is audited but not cited
    cited_tags = set()
    for r in T.get('rules', []):
        for e in r['evidence'].split(';'):
            mm = re.match(r'(LF_%s_b\d+)_' % PLAY_ID, e.strip())
            if mm: cited_tags.add(mm.group(1))
    for pid in sorted({r['play'] for r in EVID.values()}): check('play %s: a recording of runner 2 is cited by a rule row' % pid, any(REC[t]['play'] == pid for t in cited_tags))
    # ---- every recording: its files, its clicks, its steps
    def kind_of(step):
        for k in ('tick ', 'name ', 'greyed name box', 'press ', 'key ', 'space on tick', 'tab to', 'tab walk', 'reset', 'menu open', 'menu close', 'menu item', 'confirm ', 'close start boxes'):
            if step.startswith(k): return k
        return step
    for tag, r in REC.items():
        if r['status'] != 'ok': continue
        what = 'recording %s (play %s)' % (tag, r['play']); v2 = r.get('runner') == 2
        check('%s has a form record' % what, bool(r['forms']) or r['play'] in ('P10',), '')
        for step, f in r['forms'].items(): file_ok(f['png'] if v2 else '%s_%s_form.png' % (tag, step), what, f.get('png_sha') if v2 else None)
        for key, sc in r.get('screens', {}).items(): file_ok(sc['png'], what, sc['png_sha'])
        if r.get('autosave'):
            p = file_ok(r['autosave'], what)
            if p: check('%s autosave hash equals the one in the record' % what, sha(p) == r['autosave_sha'])
            s = save_view(tag); mem = r['state']
            if s and r['play'] not in ('P09', 'P10'): check('%s: the save and the game memory agree on every human flag and leader' % what, [(n['leader'], bool(n['human'])) for n in s['nations']] == [(n['leader'], bool(n['human'])) for n in mem['nations']], 'save vs memory')
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
        for i, v in enumerate(ver):
            nm = '%s: step %d (%s)' % (what, i, v.get('step'))
            try:
                if not check(nm + ' records ok, attempts and its clicks and keys', all(k in v for k in ('ok', 'attempts', 'clicks', 'keys')), str(sorted(v))): continue
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
                if kd in ('tick ', 'name ', 'space on tick'): check(nm + ' records that the other 15 rows are unchanged', v.get('others_unchanged') is True, str(v.get('others_unchanged')))
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
    ruleids = set(RULE) | {r['id'] for r in T.get('controls', [])}
    for r in T.get('clone', []):
        cites = [s.strip() for s in r['rules'].split(',') if s.strip()]
        for x in cites: check('clone row %s cites rule %s that exists' % (r['id'], x), x in ruleids)
        check('clone row %s names the original' % r['id'], bool(r['the original']))
        cb_ = set()
        for x in cites:
            if x in RULE: cb_ |= numbers(RULE[x]['rule'] + ' ' + RULE[x]['check'] + ' ' + RULE[x]['literal'])
        for nmb in sorted(numbers(r['the original'])): check('clone row %s: the number %s in "the original" is in a rule it cites' % (r['id'], fmtn(nmb)), nmb in cb_)
    ps = {r['play']: r for r in T.get('plays', [])}
    check('plays table lists exactly the play ids recorded ok', set(ps) == set(PIDS_OK), '%s' % sorted(set(ps) ^ set(PIDS_OK)))
    for pid, r in ps.items():
        recs = [x for x in EVID.values() if x['play'] == pid]
        if check('plays table: %s has a recording of runner 2' % pid, bool(recs)):
            seeds_ = []
            for g_ in recs[-1]['new_games']:
                if not seeds_ or seeds_[-1] != g_['seed']: seeds_.append(g_['seed'])
            check('plays table: %s seed(s) "%s" equal the seeds the New Games of its newest recording recorded %s' % (pid, r['seed'], seeds_), r['seed'] == ' then '.join(str(s) for s in seeds_), '%s vs %s' % (r['seed'], seeds_))
            check('plays table: %s outcome' % pid, r['outcome'] == 'ok')
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
        PCHECKS[:] = []; CUR['res'] = {}
        for it in items: run_check(rid, it, None, r)
        bound = set().union(*[item_numbers(it) for it in items]); BOUND |= bound; ROWBOUND[rid] = bound
        for nmb in sorted(numbers(r['statement'])): check('%s statement number %s is bound to a check of the row' % (rid, fmtn(nmb)), nmb in bound)
    # ---- counts (each recomputed from a source, never from the finding)
    cnt = {r['item']: r for r in T.get('counts', [])}
    def count_check(item, value):
        r = [v for k, v in cnt.items() if k.startswith(item)]
        if check('counts row present: ' + item, bool(r)): check('count %s: finding %s vs sources %s' % (item, r[0]['count'], value), int(r[0]['count']) == value)
    count_check('unique play ids recorded ok', len(PIDS_OK)); count_check('successful recordings (all runners)', len(OKREC)); count_check('successful recordings by the pointer-verified runner', len(EVID))
    count_check('failed recordings', len(FAILED)); count_check('recordings in all', len(REC)); count_check('pool names', sum(len(v) for v in POOL.values()))
    count_check('form controls', sum(1 for o in allobjs if o['class'] in ('TPanel', 'TCheckBox', 'TEdit'))); count_check('objects of the resource', len(allobjs))
    # ---- every number of the Answer and of "What this does not establish" is bound to a claim of the tables
    def section(title):
        m = re.search(r'^## %s\n(.*?)(?=^## |\Z)' % re.escape(title), TEXT, re.S | re.M); return m.group(1) if m else ''
    BOUND |= numbers(' '.join(r['seed'] for r in T.get('draws', [])) + ' ' + ' '.join(r['seed'] for r in T.get('plays', [])))
    for r in T.get('counts', []): BOUND |= numbers(r['count'])
    def expand(text):
        """the row ids a paragraph cites: single ids and ranges such as H01-H04"""
        out = set()
        for m in re.finditer(r'\b([A-Z])(\d{2})(?:-(?:([A-Z])?(\d{2})))?\b', text):
            a_, n0, b_, n1 = m.groups()
            if n1: out |= {'%s%02d' % (a_, k) for k in range(int(n0), int(n1) + 1)}
            else: out.add(a_ + n0)
        return {i for i in out if i in ROWBOUND}
    for sec, item_re in (('Answer', r'^\d+\. '), ('What this does not establish', r'^- ')):
        items_ = []
        for l in section(sec).split('\n'):
            if re.match(item_re, l): items_.append(l)
            elif l.strip() and items_: items_[-1] += ' ' + l
        for it in items_:
            ids_ = expand(it); allowed = set().union(*[ROWBOUND[i] for i in ids_]) if ids_ else set()
            txt = re.sub(r'\([A-Z]\d{2}[^)]*\)', '', it); txt = re.sub(r'`?\b[A-Z]{1,3}\d{2}\b`?', '', txt); txt = re.sub(r'^\d+\. ', '', txt)
            for nmb in sorted(numbers(txt)): check('section "%s", item "%s...": the number %s is bound by a row the item cites (%s)' % (sec, txt.strip()[:40], fmtn(nmb), sorted(ids_)), nmb in allowed)
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
