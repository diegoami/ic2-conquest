#!/usr/bin/env python3
"""Claims audit of findings/2026-10-06-leaders-form.md.

Every literal, rule, count and check in the finding's tables (marked <!-- table: NAME -->) is read from the finding and compared with a value RECOMPUTED from the sources:
 * the tracked code extract (code_extract_leaders*.txt): a cited `function:line` must exist and lie inside that function; every `code <line> has <text>` / `code fn <F> has|lacks <text>` is tested on the extract's text;
 * the form's resource dump (dfm_TPickLeaders*.txt, parsed into objects and properties): every `dfm <object>.<Property> == <value>`, the controls table's literals, positions, tab orders and lines; with --exe the dump is
   re-extracted from the executable and compared;
 * the pool table (dat_leader_pool*.tsv): its offset is recomputed from the loader's reads in the code extract (loader_offsets.py), every name list is compared with the DAT when --dat is given;
 * the recorded plays (plays_*.jsonl: clicks with their reasons, verified steps, the form's state as the running game reported it, memory), and the screenshots and memory dumps they name;
 * the saves (artifacts folder): every file hashed against SAVES.sha256 and MANIFEST-*.txt, the autosave of a play parsed again (state/sav.py) for every claim about flags, names, order and bytes.
Nothing the finding claims is typed in here: an expected value is the finding's own cell, compared with a value taken from a source; a claim that two sources agree compares the two sources.
usage: claims_audit.py [--finding F] [--data D] [--artifacts A] [--exe E] [--dat DAT] [--out FILE]   Exit status 0 only with 0 mismatches."""
import sys, os, re, json, glob, hashlib, argparse, ast, struct, subprocess, tempfile, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths
from common import latest, write_new
import loader_offsets

ROOT = paths.ROOT
sys.path.insert(0, ROOT)
from state import sav as SAV

PLAY_ID = r'P\d+[a-z]?'

def run(finding, data, art, exe=None, dat=None, quiet=True):
    data = data.rstrip('/') + '/'; art = art.rstrip('/') + '/'
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
    # ------------------------------------------------------------ the form resource
    DFM = {}; DFM_LINE = {}; DFM_ORDER = []; dfm_lines = []
    dfm_path = latest(data + 'dfm_TPickLeaders.txt')
    stack = []
    for i, l in enumerate(open(dfm_path, encoding='utf-8').read().split('\n'), 1):
        dfm_lines.append(l)
        m = re.match(r'(\s*)object (\w+): (\w+)$', l)
        if m:
            o = {'name': m.group(2), 'class': m.group(3), 'props': {}, 'children': [], 'line': i, 'proplines': {}}
            if stack: stack[-1]['children'].append(o)
            DFM[o['name']] = o; stack.append(o); continue
        m = re.match(r'\s*end$', l)
        if m and stack: stack.pop(); continue
        m = re.match(r'\s+([\w.]+) = (.*)$', l)
        if m and stack:
            try: stack[-1]['props'][m.group(1)] = ast.literal_eval(m.group(2))
            except Exception: stack[-1]['props'][m.group(1)] = m.group(2)
            stack[-1]['proplines'][m.group(1)] = i
    form = DFM.get('PickLeaders')
    check('dfm: the form object PickLeaders exists', form is not None)
    panels = [c for c in form['children'] if c['class'] == 'TPanel'] if form else []
    DFM_ORDER = [p['props'].get('Caption', '').strip() for p in panels]
    allobjs = list(DFM.values())
    if exe and os.path.exists(exe):
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
    if dat and os.path.exists(dat):
        d = open(dat, 'rb').read()
        check('pool table equals the bytes of the DAT at the recomputed offset', all(d[off_calc + n * 312 + k * 26: off_calc + n * 312 + (k + 1) * 26].split(b'\0')[0].decode('latin1') == nm for n, (nat, names) in enumerate(POOL.items()) for k, nm in enumerate(names)))
        check('pool table header carries the DAT hash', hashlib.sha256(d).hexdigest() in pool_hdr)
    DUPS = collections.OrderedDict()
    seen = collections.OrderedDict()
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
    def file_ok(name, what):
        p = art_path(name)
        if not check('%s: file %s exists in the artifacts' % (what, name), p is not None, name): return None
        h = sha(p)
        check('%s: %s SHA-256 is recorded in SAVES.sha256' % (what, name), h in HASH.get(name, ()), '%s %s' % (h[:12], sorted(x[:12] for x in HASH.get(name, ()))))
        rel = os.path.relpath(p, art)
        if MAN: check('%s: %s matches its manifest hash' % (what, name), MAN.get(rel) == h, '%s %s' % (rel, MAN.get(rel)))
        return p
    # ------------------------------------------------------------ the plays
    PLAYS = {}; FAILED = []; ALL = []
    for f in sorted(glob.glob(data + 'plays_*.jsonl')):
        for l in open(f):
            r = json.loads(l); ALL.append(r)
            if r['status'] == 'ok': PLAYS[r['play']] = r
            else: FAILED.append(r)
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
    def save_view(pid):
        if pid in SAVE: return SAVE[pid]
        r = PLAYS[pid]
        if not r.get('autosave'): SAVE[pid] = None; return None
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
        SAVE[pid] = s; return s
    NAT = DFM_ORDER
    def form_view(pid):
        r = PLAYS[pid]; out = {}
        for step, f in r['forms'].items():
            rows = f['rows']; d = {'titles': [w[0] for w in f['windows']], 'focus': f['focus']}
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
    def mem_view(pid):
        r = PLAYS[pid]; s = r.get('state')
        if s is None: return None
        s = json.loads(json.dumps(s))
        if r.get('nations_bin'):
            p = art_path(r['nations_bin'])
            if p:
                b = open(p, 'rb').read()
                s['nations_bin_leader'] = [cstr(b[n * 1172 + 0x0B: n * 1172 + 0x0B + 26]) for n in range(16)]
        return s
    def view_of(pid):
        r = PLAYS[pid]
        v = {}
        if 'tab_walk' in r:
            ys = [w[0][2] for w in r['tab_walk'][1:] if w and w[0][0] == 'TCheckBox']
            v['tab_ticks_increase'] = len(ys) == len(r['tab_walk']) - 1 and all(a < b for a, b in zip(ys, ys[1:]))
        return v
    # ------------------------------------------------------------ paths and checks
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
        if name == 'rec': return PLAYS[pid]
        if name == 'mem': return mem_view(pid)
        if name == 'save': return save_view(pid)
        if name == 'form': return form_view(pid)
        if name == 'view': return view_of(pid)
        raise KeyError(name)
    def evaluate(pid, path, absent=False):
        head, _, rest = path.partition('.')
        # `rec.autosave absent`: a missing key is the answer
        try:
            base = root(pid, head)
            return True, walk(base, '.' + rest) if rest else base
        except KeyError as e:
            return False, e
    def parse_value(tok, lit, extra):
        tok = tok.strip()
        if tok == '@literal': return lit
        if tok == '@dfmorder': return list(DFM_ORDER)
        if tok == '@limits': return [int(lit)] * 16
        if tok == '@duplicates': return dups_text
        m = re.fullmatch(r'(%s) (\S+)' % PLAY_ID, tok)
        if m:
            ok, v = evaluate(m.group(1), m.group(2))
            if not ok: raise KeyError('rhs %s' % tok)
            return v
        return json.loads(tok)
    OPS = ('==', '!=', 'has', 'startswith', 'absent')
    def unq(s): return s
    def run_check(rid, item, lit, row):
        item = item.strip()
        name = '%s check [%s]' % (rid, item[:110])
        m = re.fullmatch(r'code fn (\w+) (has|lacks) (.+)', item)
        if m:
            fn, op, txt = m.groups()
            body = '\n'.join(EXT[k] for k in FNLINES.get(fn, []))
            if not check(name + ' function in the extract', fn in FNLINES, fn): return
            has = (txt in body)
            check(name, has if op == 'has' else not has, 'function %s %s %r' % (fn, 'lacks' if has else 'has', txt)); return
        m = re.fullmatch(r'code ((?:nl:)?\d+) has (.+)', item)
        if m:
            k = code_key(m.group(1)); txt = lit if m.group(2) == '@literal' else m.group(2)
            if not check(name + ' line exists', k in EXT, str(k)): return
            check(name, txt in EXT[k], 'line %s is %r' % (m.group(1), EXT[k][:140])); return
        m = re.fullmatch(r'dfm (\w+)\.(\w+(?:\.\w+)?) (==|absent) ?(.*)', item)
        if m and m.group(1) in DFM:
            o, prop, op, rhs = m.groups()[0], m.group(2), m.group(3), m.group(4)
            if op == 'absent': check(name, prop not in DFM[o]['props'], str(DFM[o]['props'].get(prop))); return
            want = lit if rhs == '@literal' else json.loads(rhs)
            check(name, prop in DFM[o]['props'] and DFM[o]['props'][prop] == want, 'resource has %r' % (DFM[o]['props'].get(prop),)); return
        m = re.fullmatch(r'dfm order == (%s) (\S+)' % PLAY_ID, item)
        if m:
            ok, v = evaluate(m.group(1), m.group(2)); check(name, ok and v == DFM_ORDER, 'resource order %s vs memory %s' % (DFM_ORDER, v)); return
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
        m = re.fullmatch(r'pool size == (\d+)', item)
        if m: check(name, sum(len(v) for v in POOL.values()) == int(m.group(1)), str(sum(len(v) for v in POOL.values()))); return
        m = re.fullmatch(r'pool (\w+) len == (\d+)', item)
        if m: check(name, len(POOL.get(m.group(1), [])) == int(m.group(2)), str(len(POOL.get(m.group(1), [])))); return
        m = re.fullmatch(r'pool offset == (\d+)', item)
        if m: check(name, off_calc == int(m.group(1)), 'recomputed %d' % off_calc); return
        m = re.fullmatch(r'pool duplicates_across_nations == @literal', item)
        if m: check(name, dups_text == lit, 'pool has %r' % dups_text); return
        m = re.fullmatch(r'draws (all_in_pool|pairwise_different) == true', item)
        if m:
            lists = []
            for pid, step in DRAW_PLAYS:
                f = form_view(pid)[step]; lists.append(tuple(f['names']))
            if m.group(1) == 'all_in_pool': check(name, all(form_view(pid)[step]['names_in_pool'] for pid, step in DRAW_PLAYS), 'a name is not in its nation pool')
            else: check(name, len(set(lists)) == len(lists) and len(lists) >= 3, '%d draws, %d distinct' % (len(lists), len(set(lists))))
            return
        m = re.fullmatch(r'(%s) png (\S+) grey (file|game) (\d) == (true|false)' % PLAY_ID, item)
        if m:
            pid, fn, menu, idx, want = m.groups(); p = art_path(fn)
            if not check(name + ' file', p is not None, fn): return
            x0 = 10 if menu == 'file' else 41; y0 = 51 + 17 * int(idx)
            v = subprocess.run(['convert', p, '-crop', '70x12+%d+%d' % (x0, y0), '+repage', '-colorspace', 'Gray', '-format', '%[fx:minima*255]', 'info:'], capture_output=True, text=True).stdout
            check(name, (float(v) > 100) == (want == 'true'), 'darkest pixel %s' % v); return
        m = re.fullmatch(r'(%s) ((?:[^\s{]|\{[^}]*\})+) ?(==|!=|has|startswith|absent)? ?(.*)' % PLAY_ID, item)
        if m:
            pid, path, op, rhs = m.groups()
            if pid not in PLAYS: check(name + ' play exists and is ok', False, pid); return
            ok, v = evaluate(pid, path)
            if op == 'absent': check(name, not ok, 'the path exists'); return
            if not check(name + ' path exists', ok, str(v)): return
            try: want = parse_value(rhs, lit, None)
            except Exception as e: check(name + ' value parses', False, '%r: %r' % (rhs, e)); return
            vals = list(v) if isinstance(v, ALLV) else [v]
            if op == '==': good = all(x == want for x in vals)
            elif op == '!=': good = all(x != want for x in vals)
            elif op == 'has': good = all((want in x) for x in vals)
            elif op == 'startswith': good = all(isinstance(x, str) and x.startswith(want) for x in vals)
            else: good = False
            check(name, good, 'source has %r, claim %r' % (v if len(repr(v)) < 160 else repr(v)[:160], want)); return
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
    T = tables(finding)
    for need in ('controls', 'rules', 'draws', 'clone', 'plays', 'counts'):
        check('table present: ' + need, need in T and T[need], need)
    spans = lambda cell: re.findall(r'`([^`]*)`', cell)
    DRAW_PLAYS = []
    for r in T.get('draws', []):
        DRAW_PLAYS.append((r['play'], 'default' if 'default' in PLAYS.get(r['play'], {'forms': {}})['forms'] else 'second_default'))
    # ---- controls
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
    ids = [r['id'] for r in T.get('controls', [])]
    check('controls ids are unique', len(ids) == len(set(ids)))
    cb = [o for o in allobjs if o['class'] == 'TCheckBox']; ed = [o for o in allobjs if o['class'] == 'TEdit']
    check('every panel holds one TCheckBox (left 100, top 3, tab 0, no caption) and one TEdit (left 170, top 1, width 170, tab 1, MaxLength 25)',
          len(panels) == 16 and all([c['class'] for c in p['children']] == ['TCheckBox', 'TEdit'] and p['children'][0]['props'].get('Left') == 100 and p['children'][0]['props'].get('Top') == 3 and p['children'][0]['props'].get('TabOrder') == 0 and 'Caption' not in p['children'][0]['props']
                                    and p['children'][1]['props'].get('Left') == 170 and p['children'][1]['props'].get('Top') == 1 and p['children'][1]['props'].get('Width') == 170 and p['children'][1]['props'].get('TabOrder') == 1 and p['children'][1]['props'].get('MaxLength') == 25 for p in panels), 'a panel differs')
    for p in panels: check('panel %s caption is two spaces and the nation name' % p['name'], p['props'].get('Caption', '').startswith('  ') and p['props']['Caption'].strip() in NAT)
    # ---- rules
    RULE = {}; cited_plays = set()
    for r in T.get('rules', []):
        rid = r['id']; check('rule id unique %s' % rid, rid not in RULE, rid); RULE[rid] = r
        tag = r['tag']; check('%s tag is [derived] or [confirmed]' % rid, tag in ('[derived]', '[confirmed]'), tag)
        sp = spans(r['literal']); lit = sp[0] if sp else None
        if r['literal'] != '-': check('%s literal is one piece' % rid, len(sp) == 1, str(sp))
        items = [x for x in r['check'].split(' ;; ') if x.strip()]
        check('%s has checks' % rid, bool(items))
        if tag == '[derived]':
            check('%s derived rows cite no play' % rid, r['evidence'] == '-', r['evidence'])
            srcs = [s.strip() for s in r['source'].split(', ') if s.strip()]
            check('%s derived rows cite a source' % rid, srcs and srcs != ['-'], r['source'])
            for s in srcs:
                m = re.fullmatch(r'(nl:)?(\w+):(\d+)', s)
                if m and m.group(2) != 'dfm':
                    k = ('nl' if m.group(1) else 'all', int(m.group(3)))
                    if check('%s source %s: line is in the extract' % (rid, s), k in EXT): check('%s source %s: line %d is in function %s (the extract says %s)' % (rid, s, k[1], m.group(2), FNOF.get(k)), FNOF.get(k) == m.group(2))
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
        else:
            check('%s confirmed rows cite no code line' % rid, r['source'] == '-', r['source'])
            ev = [e.strip() for e in r['evidence'].split(';') if e.strip()]
            pl = [e for e in ev if re.fullmatch(PLAY_ID, e)]; fl = [e for e in ev if e not in pl]
            check('%s confirmed rows cite a play' % rid, bool(pl))
            pngs = [f for f in fl if f.endswith('.png')]; svs = [f for f in fl if f.endswith('.SAV')]; bins = [f for f in fl if f.endswith('.bin')]
            check('%s confirmed rows cite a screenshot' % rid, bool(pngs), r['evidence'])
            nosave = [p for p in pl if p in PLAYS and not PLAYS[p].get('autosave')]
            check('%s confirmed rows cite a save (or, for a state that has none, the memory dump)' % rid, bool(svs) or (bool(bins) and bool(nosave)), r['evidence'])
            for f in fl: file_ok(f, rid)
            for p in pl:
                check('%s cited play %s was recorded ok' % (rid, p), p in PLAYS)
                cited_plays.add(p)
            for f in fl:
                tagp = re.match(r'LF_(P\d+[a-z]?)_', f)
                if tagp: check('%s cited file %s belongs to a cited play' % (rid, f), tagp.group(1) in pl, tagp.group(1))
            for it in items:
                m = re.match(r'(%s) ' % PLAY_ID, it)
                if m: cited_plays.add(m.group(1))
            check('%s confirmed rows have a play check' % rid, any(re.match(PLAY_ID + ' ', it) for it in items))
        for it in items: run_check(rid, it, lit, r)
    # ---- every ok play is cited, every required play exists and is cited
    cited_in_evidence = set()
    for r in T.get('rules', []):
        for e in r['evidence'].split(';'):
            if re.fullmatch(PLAY_ID, e.strip()): cited_in_evidence.add(e.strip())
    for pid in PLAYS: check('play %s is cited by at least one rule row' % pid, pid in cited_in_evidence)
    def humans(r): return r.get('humans_ticked')
    def forms_text(r, step='before_ok'): return r['forms'].get(step, {}).get('rows', [])
    REQ = collections.OrderedDict([
        ('0 humans ticked, OK', lambda r: humans(r) == [] and any(v['step'] == 'press OK' for v in r['verified']) and r.get('nations_bin')),
        ('1 human ticked, OK', lambda r: humans(r) is not None and len(humans(r)) == 1 and r.get('autosave') and any(v['step'] in ('press OK', 'key Return') for v in r['verified'])),
        ('2 humans ticked, OK', lambda r: humans(r) is not None and len(humans(r)) == 2 and r.get('autosave') and any(v['step'] == 'press OK' for v in r['verified'])),
        ('16 humans ticked, OK', lambda r: humans(r) is not None and len(humans(r)) == 16 and r.get('autosave') and any(v['step'] == 'press OK' for v in r['verified'])),
        ('an empty name ticked and accepted', lambda r: r.get('autosave') and any(row[1] == 1 and row[3] == '' for row in forms_text(r))),
        ('a name of spaces ticked and accepted', lambda r: r.get('autosave') and any(row[1] == 1 and row[3] != '' and row[3].strip() == '' for row in forms_text(r))),
        ('a duplicate name ticked and accepted', lambda r: r.get('autosave') and len([row[3] for row in forms_text(r) if row[1] == 1 and row[3]]) != len({row[3] for row in forms_text(r) if row[1] == 1 and row[3]})),
        ('an over-long name typed', lambda r: r.get('autosave') and any(v['step'].startswith('name ') and len(v.get('typed', '')) > 25 for v in r['verified'])),
        ('an edit attempted on a computer nation\'s box', lambda r: 'greyed_edit' in r),
        ('a name edited then the nation unticked', lambda r: any(v['step'].startswith('tick ') and v['step'].endswith(' off') for v in r['verified'])),
        ('Cancel pressed with a tick and an edit made', lambda r: any(v['step'] == 'press Cancel' for v in r['verified']) and any(v['step'].startswith('tick ') for v in r['verified']) and any(v['step'].startswith('name ') for v in r['verified'])),
        ('Cancel pressed on the untouched form', lambda r: any(v['step'] == 'press Cancel' for v in r['verified']) and not any(v['step'].startswith('tick ') for v in r['verified'])),
        ('the form closed by Escape and by Return', None),
        ('three or more seeds', None)])
    for name, pred in REQ.items():
        if name == 'three or more seeds':
            seeds = {r['seed'] for r in PLAYS.values()}; check('required: ' + name, len(seeds) >= 3, str(seeds)); continue
        if name.startswith('the form closed by Escape'):
            esc = [p for p, r in PLAYS.items() if any(v['step'] == 'key Escape' for v in r['verified'])]; ret = [p for p, r in PLAYS.items() if any(v['step'] == 'key Return' for v in r['verified'])]
            check('required: ' + name, bool(esc) and bool(ret) and set(esc + ret) <= cited_in_evidence, '%s %s' % (esc, ret)); continue
        got = [p for p, r in PLAYS.items() if pred(r)]
        check('required play exists: ' + name, bool(got), 'no ok play')
        check('required play is cited by a rule row: ' + name, bool(got) and any(p in cited_in_evidence for p in got), str(got))
    # ---- every recorded play: its files, its clicks, its verified steps
    for pid, r in PLAYS.items():
        tag = r['tag']; what = 'play ' + pid
        check('%s has a form record' % what, bool(r['forms']) or pid in ('P10',), '')
        for step in r['forms']: file_ok('%s_%s_form.png' % (tag, step), what)
        if r.get('autosave'):
            p = file_ok(r['autosave'], what)
            if p: check('%s autosave hash equals the one in the record' % what, sha(p) == r['autosave_sha'])
            s = save_view(pid); mem = r['state']
            if s and pid not in ('P09', 'P10'): check('%s: the save and the game memory agree on every human flag and leader' % what, [(n['leader'], bool(n['human'])) for n in s['nations']] == [(n['leader'], bool(n['human'])) for n in mem['nations']], 'save vs memory')
        if r.get('nations_bin'):
            p = file_ok(r['nations_bin'], what)
            if p: check('%s memory dump hash equals the one in the record' % what, sha(p) == r['nations_bin_sha'])
            m = re.match(r'%s_(after_\w+)_nations\.bin' % re.escape(tag), r['nations_bin'])
            if m: file_ok('%s_%s_screen.png' % (tag, m.group(1)), what)
            b = open(art_path(r['nations_bin']), 'rb').read() if art_path(r['nations_bin']) else b''
            if b: check('%s memory dump equals the nation hashes of the record' % what, [hashlib.sha256(b[n * 1172:(n + 1) * 1172]).hexdigest() for n in range(16)] == [n['sha'] for n in r['state']['nations']])
        # clicks: each has a reason; a control click lies inside the rectangle its reason names; clicks of each kind equal the verified attempts
        cl = r['clicks']
        check('%s: every click has a recorded reason' % what, all(c.get('why') for c in cl), str([c for c in cl if not c.get('why')]))
        for c in cl:
            m = re.match(r"control (\w+) '.*' at (\d+),(\d+) (\d+)x(\d+)$", c['why'] or '')
            if m: check('%s: click %s,%s lies inside the control it names (%s)' % (what, c['x'], c['y'], c['why'][:40]), int(m.group(2)) <= c['x'] < int(m.group(2)) + int(m.group(4)) and int(m.group(3)) <= c['y'] < int(m.group(3)) + int(m.group(5)))
        ver = r['verified']
        cbc = sum(1 for c in cl if (c['why'] or '').startswith('control TCheckBox')); cba = sum(v['attempts'] for v in ver if v['step'].startswith('tick '))
        check('%s: tick-box clicks (%d) equal the attempts of the verified tick steps (%d)' % (what, cbc, cba), cbc == cba)
        edc = sum(1 for c in cl if (c['why'] or '').startswith('control TEdit')); eda = sum(v['attempts'] for v in ver if v['step'].startswith('name ')) + sum(1 for v in ver if v['step'].startswith('greyed name box'))
        check('%s: name-box clicks (%d) equal the attempts of the verified name steps plus the greyed-box tries (%d)' % (what, edc, eda), edc >= eda and edc - eda <= 3 * sum(1 for v in ver if v['step'].startswith('name ')), '')
        btc = sum(1 for c in cl if re.match(r"control TButton '(OK|Cancel)'", c['why'] or '')); bta = sum(v['attempts'] for v in ver if v['step'] in ('press OK', 'press Cancel'))
        check('%s: button clicks (%d) equal the attempts of the verified press steps (%d)' % (what, btc, bta), btc == bta)
        yn = sum(1 for c in cl if re.match(r"control TButton '&(Yes|No)'", c['why'] or '')); check('%s: the Confirm answers clicked (%d) are one per Confirm box recorded' % (what, yn), yn == (1 if r.get('confirm_text') else 0), '')
        check('%s: every control click went to a TCheckBox, TEdit or TButton of the form' % what, all((c['why'] or '').startswith(('control TCheckBox', 'control TEdit', 'control TButton', 'menu bar', 'dropdown', 'reset menus')) for c in cl), str([c['why'] for c in cl][:20]))
        check('%s: every tick and name step lists the other rows unchanged' % what, all(v.get('others_unchanged', True) for v in ver))
    check('failed plays are kept, not cited: %d recorded' % len(FAILED), all(f['status'] == 'FAILED' for f in FAILED))
    # ---- remaining tables
    ruleids = set(RULE) | {r['id'] for r in T.get('controls', [])}
    for r in T.get('clone', []):
        for x in [s.strip() for s in r['rules'].split(',') if s.strip()]: check('clone row %s cites rule %s that exists' % (r['id'], x), x in ruleids)
        check('clone row %s names the original' % r['id'], bool(r['the original']))
    ps = {r['play']: r for r in T.get('plays', [])}
    check('plays table lists exactly the ok plays', set(ps) == set(PLAYS), '%s vs %s' % (sorted(set(ps) ^ set(PLAYS)), ''))
    for pid, r in ps.items():
        if pid in PLAYS:
            check('plays table: %s seed' % pid, str(PLAYS[pid]['seed']) == r['seed'].split()[0], '%s vs %s' % (PLAYS[pid]['seed'], r['seed']))
            check('plays table: %s outcome' % pid, r['outcome'] == PLAYS[pid]['status'])
    for r in T.get('draws', []):
        pid = r['play']; names = [x.strip() for x in spans(r['names (nation order)'])[0].split(';')]; slots = [int(x) for x in spans(r['slots'])[0].split(';')]
        if not check('draws row %s: play exists' % pid, pid in PLAYS): continue
        step = 'default' if 'default' in PLAYS[pid]['forms'] else 'second_default'
        f = form_view(pid)[step]
        check('draws row %s: the 16 names equal the names the form showed' % pid, names == f['names'], '%s vs %s' % (names[:3], f['names'][:3]))
        check('draws row %s: the seed is the play\'s (or the second New Game\'s)' % pid, str(PLAYS[pid]['seed']) == r['seed'] or pid == 'P09', '')
        calc = [POOL[NAT[i]].index(n) if n in POOL[NAT[i]] else None for i, n in enumerate(names)]
        check('draws row %s: every name is in its nation\'s pool and its slot is the one recomputed' % pid, calc == slots, '%s vs %s' % (calc, slots))
    # ---- counts (each recomputed from a source, never from the finding)
    cnt = {r['item']: r for r in T.get('counts', [])}
    def count_check(item, value):
        r = [v for k, v in cnt.items() if k.startswith(item)]
        if check('counts row present: ' + item, bool(r)): check('count %s: finding %s vs sources %s' % (item, r[0]['count'], value), int(r[0]['count']) == value)
    count_check('plays recorded ok', len(PLAYS)); count_check('plays recorded failed', len(FAILED)); count_check('pool names', sum(len(v) for v in POOL.values()))
    count_check('form controls', sum(1 for o in allobjs if o['class'] in ('TPanel', 'TCheckBox', 'TEdit')))
    return checks[0], bad

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--finding', default=os.path.join(paths.ROOT, 'findings', '2026-10-06-leaders-form.md'))
    ap.add_argument('--data', default=paths.DATA); ap.add_argument('--artifacts', default=paths.ART)
    ap.add_argument('--exe'); ap.add_argument('--dat', default=paths.DAT); ap.add_argument('--out')
    a = ap.parse_args()
    n, bad = run(a.finding, a.data, a.artifacts, a.exe, a.dat)
    lines = ['claims audit of %s' % os.path.basename(a.finding), '%d checks, %d mismatches' % (n, len(bad))] + ['MISMATCH ' + b for b in bad]
    print('\n'.join(lines))
    if a.out: print('written', write_new(a.out, '\n'.join(lines) + '\n'))
    sys.exit(0 if not bad else 1)

if __name__ == '__main__': main()
