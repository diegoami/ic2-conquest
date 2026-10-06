#!/usr/bin/env python3
"""Claims audit of findings/2026-10-05-refusal-texts-and-conditions.md.

Every claim in the finding's tables (marked <!-- table: NAME -->) is read from the finding and compared with a value RECOMPUTED from the sources:
 * the tracked code extract (code_extract_refusals*.txt): the call-site lines (the literal is parsed from the call text and compared with the finding's literal BYTE FOR BYTE),
   the box type (the CONCAT31 argument), the cited condition lines (every `L<line> «quote»` must be a substring of that line), the function each line belongs to;
 * the executable (if present): the literal as a NUL-delimited string, and the button-set word at the address the call names;
 * the tracked readings (ocr_*.jsonl, plays_*.jsonl): the box title and the OCR of the message must match the literal of the row the play is cited for (and the combined-case plays must
   match the row the finding says appeared better than the other row);
 * the saves (artifacts folder): SHA-256 against SAVES.sha256 and the manifests, the state facts of the control save, and the difference between control and after saves.
Nothing the finding claims is typed in here.   usage: claims_audit.py [--finding F] [--data D] [--artifacts A] [--exe E] [--out FILE]
Exit status 0 only with 0 mismatches."""
import sys, os, re, json, glob, hashlib, difflib, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from common import latest, write_new
import savefacts as SF
import construct as C

def run(finding, data, art, exe=None, dump=None, quiet=True):
    data = data.rstrip('/') + '/'; art = art.rstrip('/') + '/'
    checks = [0]; bad = []
    def check(name, cond, detail=''):
        checks[0] += 1
        if not cond: bad.append('%s: %s' % (name, detail))
        return cond
    sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
    # ------------------------------------------------------------ sources
    X = {}; FN = {}; cur = None
    for l in open(latest(data + 'code_extract_refusals.txt'), encoding='utf-8', errors='replace'):
        l = l.rstrip('\n'); m = re.match(r'(\d+)\t(.*)', l)
        if not m: continue
        ln = int(m.group(1)); X[ln] = m.group(2); mm = re.match(r'// ==== (\S+) @ ([0-9a-f]+) ====', m.group(2))
        if mm: cur = mm.group(1)
        FN[ln] = cur
    norm = lambda s: re.sub(r'\s+', ' ', s).strip()
    def unesc(s): return re.sub(r'\\(x[0-9a-fA-F]{2}|.)', lambda m: {'n': '\n', 't': '\t', "'": "'", '"': '"', '\\': '\\'}.get(m.group(1)) or chr(int(m.group(1)[1:], 16)), s)
    def call_text(line):
        k = line; t = X[k].strip()
        while not re.search(r';\s*$', X[k]) and k + 1 in X: k += 1; t += ' ' + X[k].strip()
        return t
    def parse_args(txt):
        j = txt.index('FUN_0042d750(') + len('FUN_0042d750('); depth = 0; args = []; cur_ = ''; instr = False; esc = False
        for ch in txt[j:]:
            if instr:
                cur_ += ch
                if esc: esc = False
                elif ch == '\\': esc = True
                elif ch == '"': instr = False
                continue
            if ch == '"': instr = True; cur_ += ch; continue
            if ch in '([': depth += 1
            if ch in ')]':
                if depth == 0: args.append(cur_.strip()); break
                depth -= 1
            if ch == ',' and depth == 0: args.append(cur_.strip()); cur_ = ''; continue
            cur_ += ch
        return args
    DLG = {0: 'mtWarning', 1: 'mtError', 2: 'mtInformation', 3: 'mtConfirmation'}
    TITLE = {'mtInformation': 'Information', 'mtConfirmation': 'Confirm', 'mtWarning': 'Warning', 'mtError': 'Error'}
    BTN = ['mbYes', 'mbNo', 'mbOK', 'mbCancel', 'mbAbort', 'mbRetry', 'mbIgnore', 'mbAll', 'mbNoToAll', 'mbYesToAll', 'mbHelp']
    EXE = None
    if exe and os.path.exists(exe):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import sites as _sites
        EXE = _sites.Exe(exe)
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
    for need in ('catalogue', 'prompts', 'notices', 'orderings', 'plays', 'counts', 'clone'):
        check('table present: ' + need, need in T and T[need], need)
    # ------------------------------------------------------------ call-site rows
    spans = lambda cell: re.findall(r'`([^`]*)`', cell)
    site_of = {}                                  # call line -> (literal or None, dlg name, button word or None)
    def site(line):
        if line in site_of: return site_of[line]
        a = parse_args(call_text(line)); m = re.fullmatch(r'\(uint \*\)"((?:[^"\\]|\\.)*)"', a[0])
        lit = unesc(m.group(1)) if m else None
        c = re.search(r'CONCAT31\(.*,\s*(\d)\)$', a[1], re.S); dlg = DLG.get(int(c.group(1))) if c else None
        mb = re.fullmatch(r'(?:_UNK|DAT)_([0-9a-f]{8})', a[2]); word = None
        if mb and EXE:
            raw = EXE.rd(int(mb.group(1), 16), 2); word = int.from_bytes(raw, 'little')
        site_of[line] = (lit, dlg, word); return site_of[line]
    def box_cell(cell):
        m = re.fullmatch(r'(mt\w+) \[([\w+]*)\]', cell); return (m.group(1), m.group(2)) if m else (None, None)
    CAT = {}                                        # id -> row dict (all three call-site tables)
    for tname in ('catalogue', 'prompts', 'notices'):
        for r in T.get(tname, []):
            check('%s id unique %s' % (tname, r['id']), r['id'] not in CAT, r['id']); CAT[r['id']] = dict(r, table=tname)
            fl = r['function:call line']; m = re.fullmatch(r'(\w+):(\d+)', fl)
            if not check('%s function:line form' % r['id'], bool(m), fl): continue
            fn, line = m.group(1), int(m.group(2))
            if not check('%s call line %d exists in the extract' % (r['id'], line), line in X): continue
            check('%s call line %d is in function %s (the extract says %s)' % (r['id'], line, fn, FN.get(line)), FN.get(line) == fn)
            check('%s call line %d calls the message-box function' % (r['id'], line), 'FUN_0042d750(' in X[line])
            lit, dlg, word = site(line)
            sp = spans(r['literal'])
            if lit is not None and not any(s.startswith('<') and s.endswith('>') for s in sp):
                check('%s literal is one piece' % r['id'], len(sp) == 1, str(sp))
                check('%s literal byte for byte: finding %r vs call site %r' % (r['id'], sp[0] if sp else None, lit), sp and sp[0] == lit)
                if EXE:
                    check('%s literal is a NUL-delimited string of the executable' % r['id'], EXE.d.find(b'\0' + lit.encode('latin1') + b'\0') >= 0)
            else:                                    # a message built at run time: its whole construction is recomputed from the extract (order, variables, conditional and either/or pieces)
                check('%s built message: the call passes no literal' % r['id'], lit is None, str(lit))
                try: derived = C.spans(X, line)
                except Exception as e: derived = ['<cannot derive: %s>' % e]
                check('%s built message: finding %r vs construction recomputed from %s: %r' % (r['id'], r['literal'], fn, ' + '.join(derived or [])), r['literal'] == ' + '.join(derived or []))
            # every cited line must lie in the row's own function, or in a function the condition names
            for col in ('condition [derived]', 'raised when [derived]', 'raised when'):
                for ln, q in re.findall(r'L(\d+) «([^»]*)»', r.get(col, '')):
                    f2 = FN.get(int(ln))
                    check('%s cited line %s is in %s or a function the condition names (it is in %s)' % (r['id'], ln, fn, f2), f2 == fn or (f2 is not None and f2 in r.get(col, '')))
            bt, bb = box_cell(r['box [buttons]'])
            check('%s box type: finding %s vs code %s' % (r['id'], bt, dlg), bt == dlg)
            if tname == 'prompts': check('%s is in the prompts table: its button set must be Yes+No+Cancel (finding %s)' % (r['id'], bb), bb == 'mbYes+mbNo+mbCancel')
            if tname == 'catalogue': check('%s is in the refusals table: its button set must have no Yes/No (finding %s)' % (r['id'], bb), 'mbYes' not in bb and 'mbNo' not in bb)
            if tname == 'notices': check('%s is in the notices table: %s must be OK-only, or the battle screen' % (r['id'], bb), (r.get('kind') == 'excluded' and fn.startswith('TBattleMap_')) or (r.get('kind') == 'notice' and bb == 'mbOK'))
            if word is not None:
                want = '+'.join(BTN[k] for k in range(11) if word >> k & 1)
                check('%s buttons: finding %s vs executable %s' % (r['id'], bb, want), bb == want)
            # cited condition lines
            for col in ('condition [derived]', 'raised when [derived]', 'raised when', 'effect [derived]', 'note'):
                for ln, q in re.findall(r'L(\d+) «([^»]*)»', r.get(col, '')):
                    ln = int(ln)
                    check('%s cited line %d quotes %r' % (r['id'], ln, q[:50]), ln in X and norm(q) in norm(X[ln]), X.get(ln, '<no such line>')[:80])
    # ------------------------------------------------------------ counts
    n_sites = len(set(int(re.fullmatch(r'\w+:(\d+)', r['function:call line']).group(1)) for r in CAT.values()))
    all_call_lines = sorted(ln for ln in X if 'FUN_0042d750(' in X[ln] and not X[ln].startswith('void ') and FN.get(ln) != 'FUN_0042d750')
    for r in T.get('counts', []):
        k, v = r['count'], r['value']
    cnt = {r['count']: r['value'] for r in T.get('counts', [])}
    def num(k):
        v = cnt.get(k); return int(v.replace(',', '')) if v and v.replace(',', '').isdigit() else None
    check('every call line of the extract is catalogued exactly once (%d lines, %d catalogue rows)' % (len(all_call_lines), len(CAT)),
          sorted(int(re.fullmatch(r'\w+:(\d+)', r['function:call line']).group(1)) for r in CAT.values()) == all_call_lines)
    kinds = {}
    for r in CAT.values(): kinds[r['table'] if r['table'] != 'notices' else r.get('kind', 'notice')] = kinds.get(r['table'] if r['table'] != 'notices' else r.get('kind', 'notice'), 0) + 1
    check('count: message-box call sites = %s' % cnt.get('message-box call sites'), num('message-box call sites') == len(all_call_lines), str(len(all_call_lines)))
    check('count: refusal rows', num('refusals catalogued') == kinds.get('catalogue'), str(kinds))
    check('count: prompt rows', num('prompts catalogued') == kinds.get('prompts'), str(kinds))
    check('count: notice rows', num('notices catalogued') == kinds.get('notice'), str(kinds))
    check('count: excluded rows', num('excluded (battle screen)') == kinds.get('excluded'), str(kinds))
    check('count: the rows recounted from the tables sum to the sites recomputed from the extract', sum(kinds.values()) == len(all_call_lines), str(kinds))
    lit_sites = sum(1 for ln in all_call_lines if site(ln)[0] is not None)
    check('count: call sites whose text is a literal', num('call sites with a literal text') == lit_sites, str(lit_sites))
    check('count: call sites whose text is built at run time', num('call sites with a built text') == len(all_call_lines) - lit_sites, str(len(all_call_lines) - lit_sites))
    check('count: literals found at call sites (recomputed)', num('literals found at call sites') == lit_sites, str(lit_sites))
    lits_cat = sum(1 for r in CAT.values() if not any(s.startswith('<') for s in spans(r['literal'])))
    check('count: literals catalogued = literals found, both recomputed', lits_cat == lit_sites, '%d vs %d' % (lits_cat, lit_sites))
    check('count: literals catalogued recomputed', num('literals catalogued') == lits_cat, str(lits_cat))
    lt = latest(data + 'literals_in_scope.tsv'); cats = {}
    for l in open(lt, encoding='utf-8').read().splitlines()[1:]:
        f = l.split('\t'); cats[f[3]] = cats.get(f[3], 0) + 1
    check('count: message-box literals in the scan of the T* functions', num('message-box literals in the scan of the T*_* functions') == cats.get('message-box literal'), str(cats))
    check('count: message-box literals in the scan (recomputed) = literals found (recomputed)', cats.get('message-box literal') == lit_sites, '%s vs %s' % (cats, lit_sites))
    check('count: fragments of built messages in the scan', num('fragments of built messages (not boxes of their own)') == cats.get('fragment of a built message'), str(cats))
    check('count: other strings in the scan', num('other strings (captions, panel labels, names)') == cats.get('other'), str(cats))
    cls = [l.split('\t') for l in open(latest(data + 'class_sites.tsv'), encoding='utf-8').read().splitlines()[1:]]
    check('classes table equals class_sites.tsv', [[c.strip() for c in r.values()] for r in T.get('classes', [])] == [[c.strip() for c in r] for r in cls])
    check('classes table: the calls of all classes sum to the call lines recomputed from the extract', sum(int(r[2]) for r in cls) == len(all_call_lines))
    by_cls = {}
    for ln in all_call_lines: by_cls[FN[ln].split('_')[0] if re.match(r'T[A-Z]\w*_', FN[ln]) else '(unnamed)'] = by_cls.get(FN[ln].split('_')[0] if re.match(r'T[A-Z]\w*_', FN[ln]) else '(unnamed)', 0) + 1
    check('classes table: the calls per class equal those recomputed from the extract', all(by_cls.get(r[0], 0) == int(r[2]) for r in cls), str(by_cls))
    if dump and os.path.exists(dump):
        n = sum(1 for l in open(dump, errors='replace') if 'FUN_0042d750(' in l and not l.startswith('void '))
        check('dump check: call sites in all_app_functions.txt (+ the definition line of the wrapper excluded) = %d' % len(all_call_lines), n == len(all_call_lines), str(n))
    fn_of_cell = lambda c: c['function:call line'].split(':')[0]
    # ------------------------------------------------------------ plays
    PL = {}
    for f in sorted(glob.glob(data + 'plays_*.jsonl')):
        for l in open(f, encoding='utf-8'): r = json.loads(l); PL.setdefault(r['play'], []).append(r)
    RE = {}
    for f in sorted(glob.glob(data + 'ocr_reread*.jsonl')):
        for l in open(f, encoding='utf-8'): r = json.loads(l); RE[r['png']] = r
    def texts_of(b):
        c = [b.get('text', ''), b.get('text_crop', '')]
        if b['png'] in RE: c += [RE[b['png']]['psm6'], RE[b['png']]['psm4']]
        return [norm(x).lower() for x in c if x]
    def partial(lit, t):
        lit = norm(lit).lower(); best = 0.0; n = len(lit)
        for i in range(0, max(1, len(t) - n + 4)):
            for w in (n - 2, n - 1, n, n + 1, n + 2):
                if w > 0: best = max(best, difflib.SequenceMatcher(None, lit, t[i:i + w]).ratio())
        return best
    def best_ratio(lit, q):
        return max((partial(lit, t) for b in q['boxes'] for t in texts_of(b)), default=0.0)
    def expected_text(r):
        """the texts the box may show for a row: its pieces joined, a number as 1 or 2 (the conditional `s` only for 2), an either/or piece as each alternative, a name as empty"""
        import itertools
        sp = spans(r['literal']); out = []
        for n in (1, 2):
            for alt in itertools.product(*[([a_ for a_ in x.split(C.OR)] if C.OR in x else [x]) for x in sp]):
                t = ''
                for x, a_ in zip(sp, alt):
                    if x.startswith(C.COND):
                        if n == 2: t += x[len(C.COND):]
                    elif x.startswith('<') and x.endswith('>'): t += str(n) if 'number' in x else ''
                    else: t += a_
                if t not in out: out.append(t)
        return out
    THR = 0.85
    for rid, r in CAT.items():
        cell = r.get('play [confirmed]', '-')
        if cell == '-' or not cell: continue
        check('%s play cell starts with [confirmed]' % rid, cell.startswith('[confirmed]'), cell[:30])
        for entry in cell[len('[confirmed]'):].split(';'):
            toks = entry.strip().split(' ')
            pid = toks[0]
            if pid not in PL: check('%s play %s exists in plays_*.jsonl' % (rid, pid), False); continue
            q = PL[pid][-1]
            exp = expected_text(r)
            ratio = max(best_ratio(e, q) for e in exp)
            check('%s play %s: OCR of a box matches the literal %r (ratio %.2f >= %.2f)' % (rid, pid, exp[0][:40], ratio, THR), ratio >= THR)
            _, dlg, _ = site(int(re.fullmatch(r'\w+:(\d+)', r['function:call line']).group(1)))
            titles = [b['title'] for b in q['boxes']]
            check('%s play %s: a box titled %s (type %s)' % (rid, pid, TITLE.get(dlg), dlg), TITLE.get(dlg) in titles, str(titles))
            for fn_ in toks[1:]:
                fn_ = fn_.strip('`')
                if fn_.endswith('.png'): check('%s play %s: screenshot %s named in the record' % (rid, pid, fn_), any(b['png'] == fn_ for b in q['boxes']))
                if fn_.endswith('.SAV'): check('%s play %s: save %s named in the record' % (rid, pid, fn_), fn_ in (q['control'], q['after']))
    # play table rows: files, hashes, state facts, difference
    hashes = {}
    for l in open(data + 'SAVES.sha256'): p = l.split(); hashes[p[1]] = p[0]
    mem = {}
    for m in sorted(glob.glob(data + 'MANIFEST-*.txt')):
        for l in open(m):
            p = l.split()
            if len(p) == 2 and p[1].startswith('member:'): mem[os.path.basename(p[1][7:])] = p[0]
    # the order a play issued, as recorded at play time (play_lib.CLICKS), mapped to the handler it reaches (used by the per-play checks and by the required-confirmation checks)
    def handlers_of(q):
        TOOL = {('army', 'split'): 'TUnitMap_SplitArmy', ('army', 'join'): 'TUnitMap_JoinArmies', ('army', 'mercs'): 'TUnitMap_RecruitMercenaries', ('army', 'disband'): 'TUnitMap_DisbandArmy',
                ('fleet', 'repair'): 'TUnitMap_RepairFlt', ('fleet', 'split'): 'TUnitMap_SplitFleet', ('fleet', 'join'): 'TUnitMap_JoinFleets', ('fleet', 'scuttle'): 'TUnitMap_ScuttleFleet',
                ('city', 'fortify'): 'TUnitMap_Fortify', ('main', 'build_fleet'): 'TPremierForm_BuildNewFleet'}
        DLG = {('Change units', 'Rename unit'): 'TChangeArmyUnits_RenameUnit', ('Change units', 'Split unit'): 'TChangeArmyUnits_SplitUnit', ('Change units', 'Join units'): 'TChangeArmyUnits_JoinUnits',
               ('Change units', 'Disband'): 'TChangeArmyUnits_Disband', ('Recruit mercenary unit', 'Recruit unit'): 'TRecruitMercs_RecruitMercUnit', ('Army recruits', 'Recruit unit'): 'TArmyRecruits_RecruitUnit'}
        RADIO = {0: 'TPolitics_MakePeace', 1: 'TPolitics_MakeTrade', 2: 'TPolitics_MakeAlliance'}
        def src_offset(fnname):                      # the dialog copy a transfer / disband handler takes its units from, read from its call of MoveUnit / RemoveUnit
            for ln in X:
                if FN.get(ln) == fnname:
                    m = re.search(r'TArmyToArmy_(?:MoveUnit|RemoveUnit)\(param_1,param_1 \+ (0x[0-9a-f]+)', X[ln])
                    if m: return int(m.group(1), 16)
        def side_handler(kind, side):                # the first army's list is the left one (caption "Units in first army"); its handler is the one whose source copy is the lower offset
            hs = sorted([('TArmyToArmy_Army1' + kind, src_offset('TArmyToArmy_Army1' + kind)), ('TArmyToArmy_Army2' + kind, src_offset('TArmyToArmy_Army2' + kind))], key=lambda h: h[1])
            return hs[0][0] if side == 'left' else hs[1][0]
        handlers = set(); xfer = None
        for c in q.get('clicks', []):
            if c['kind'] == 'toolbar' and (c['bar'], c['tool']) in TOOL: handlers.add(TOOL[(c['bar'], c['tool'])])
            elif c['kind'] == 'control' and (c['dialog'], c['text']) in DLG: handlers.add(DLG[(c['dialog'], c['text'])])
            elif c['kind'] == 'radio': handlers.add(RADIO[c['column']])
            elif c['kind'] == 'tile': handlers.add('TUnitMap_SelectUnit')
            elif c['kind'] == 'transfer-dialog':
                handlers.add(side_handler('Transfer' if c['button'] == 'Transfer' else 'Disband', c['side']))
                if c['button'] == 'Transfer': xfer = c
        return handlers, xfer
    for r in T.get('plays', []):
        pid = r['play']
        if not check('play %s has a record' % pid, pid in PL): continue
        q = PL[pid][-1]
        check('%s: source save column %r vs record %r' % (pid, r['source save'], q['src']), r['source save'] == q['src'])
        check('%s: order-issued column vs the record' % pid, r['order issued'] == q['note'], '%r vs %r' % (r['order issued'], q['note']))
        citing = sorted(c['id'] for c in CAT.values() if pid in re.findall(r'(?:^|; |\[confirmed\] )(\w+)', c.get('play [confirmed]', '')))
        check('%s: rows column %r vs the rows whose play cell names it %r' % (pid, r['rows'], citing), sorted([x for x in r['rows'].split(',') if x]) == citing)
        handlers, xfer = handlers_of(q)
        cited_rows = [c for c in CAT.values() if pid in re.findall(r'(?:^|; |\[confirmed\] )(\w+)', c.get('play [confirmed]', ''))]
        for c in cited_rows:
            check('%s: row %s (%s) belongs to a handler the play\'s recorded clicks reach %s' % (pid, c['id'], fn_of_cell(c), sorted(handlers)), fn_of_cell(c) in handlers)
        if cited_rows: check('%s: the record has the clicks of the order (a play cited by rows needs them)' % pid, bool(q.get('clicks')))
        if xfer and os.path.exists(art + 'saves/' + q['control']):    # a transfer: recompute from the control save that the cited refusal's own condition held at the TARGET of the clicked side
            ctl_ = art + 'saves/' + q['control']; ents = __import__('play_meta').W.get(pid, [])
            army_ids = [int(e.split(':')[1]) for e in ents if e.startswith('army:')]; first = xfer['first_army']; other = [a_ for a_ in army_ids if a_ != first][0]
            srcA, tgtA = (first, other) if xfer['side'] == 'left' else (other, first)
            unit = SF.slot_troops(ctl_, srcA, xfer['row']); tu, tt, tab = SF.army_numbers(ctl_, tgtA)
            fl = [SF.fleet_numbers(ctl_, int(e.split(':')[1])) for e in ents if e.startswith('fleet:')]
            for c in cited_rows:
                lit = spans(c['literal'])[0]
                if 'already has 20 units' in lit: ok_ = tu >= 20
                elif 'more than 100,000 troops' in lit: ok_ = tt + unit >= 100001
                elif 'can not carry any more troops' in lit: ok_ = tab and any(f[1] == tgtA and (tt + unit) // 500 > f[0] for f in fl)
                else: continue
                check('%s: the %s side was clicked (source army %d, target army %d): the condition of %s held in the control save' % (pid, xfer['side'], srcA, tgtA, c['id']), ok_)
        check('%s: files column vs the record' % pid, spans(r['files']) == ([q['boxes'][-1]['png']] if q['boxes'] else []) + [q['control'], q['after']], r['files'])
        stg = [l.rstrip('\n').split('\t') for l in open(data + 'staging_log.tsv')]
        logged = [x for x in stg if x[4] == q['input']]
        if r['edit'].startswith('STAGED'):
            check('%s: the finding says STAGED, so the record must be staged (staged=%s)' % (pid, q['staged']), q['staged'] is True and bool(q['ops']))
            check('%s: the finding says STAGED, so the staging log has the input %s' % (pid, q['input']), len(logged) >= 1)
            if logged:
                check('%s: the staging log hash and operations equal the record\'s' % pid, logged[-1][5] == q['input_sha'] and logged[-1][6].split(' ops=', 1)[1] == json.dumps(q['ops']), logged[-1][6][-80:])
                check('%s: the staging log source %s equals the record\'s source and hash' % (pid, logged[-1][2]), logged[-1][2] == q['src'] and logged[-1][3] == q['src_sha'])
            import build_tables as _BT
            check('%s: the edit column equals the declared edits of the record: %r' % (pid, r['edit']), r['edit'] == 'STAGED: ' + _BT.compact_ops(q['ops']), r['edit'][:80])
        else:
            check('%s: the finding says %r, so the record must be unedited and absent from the staging log' % (pid, r['edit']), r['edit'] == 'fixture, unedited' and q['staged'] is False and not q['ops'] and not logged and q['src_sha'] == q['input_sha'])
        for fn_ in spans(r['files']):
            h = hashes.get(fn_)
            check('%s: %s has a hash in SAVES.sha256' % (pid, fn_), h is not None)
            check('%s: %s is in a manifest with the same hash' % (pid, fn_), mem.get(fn_) == h, '%s vs %s' % (mem.get(fn_), h))
            p = art + ('saves/' if fn_.endswith('.SAV') else '') + fn_
            if os.path.exists(p): check('%s: %s file hash equals SAVES.sha256' % (pid, fn_), sha(p) == h)
        ctl = art + 'saves/' + q['control']; aft = art + 'saves/' + q['after']
        if os.path.exists(ctl) and os.path.exists(aft):
            check('%s: control save hash equals the record (%s)' % (pid, q['control']), sha(ctl) == q['control_sha'])
            check('%s: after save hash equals the record (%s)' % (pid, q['after']), sha(aft) == q['after_sha'])
            facts = '; '.join(SF.fact(ctl, sp) for sp in __import__('play_meta').W.get(pid, []))
            check('%s: state facts in the control save: finding %r vs recomputed %r' % (pid, r['state in the control save [recomputed]'], facts), r['state in the control save [recomputed]'] == facts)
            d = SF.diff_text(ctl, aft)
            check('%s: after vs control: finding %r vs recomputed %r' % (pid, r['after vs control [recomputed]'], d), r['after vs control [recomputed]'] == d)
            shown = ' / '.join('%s: %s' % (b['title'], (RE[b['png']]['psm6'] if b['png'] in RE and RE[b['png']]['psm6'] else (b.get('text_crop') or b.get('text', '')))) for b in q['boxes'])
            check('%s: the OCR reading in the finding is the recorded one' % pid, r['box title: OCR of the message'] == shown, '%r vs %r' % (r['box title: OCR of the message'], shown))
            facts2 = '; '.join(SF.fact(aft, sp) for sp in __import__('play_meta').W.get(pid, []))
            check('%s: state facts in the after save: finding %r vs recomputed %r' % (pid, r['state in the after save [recomputed]'], facts2), r['state in the after save [recomputed]'] == facts2)
            cited = [c for c in CAT.values() if pid in re.findall(r'(?:^|; |\[confirmed\] )(\w+)', c.get('play [confirmed]', ''))]
            def has_loop(fnname):
                return any(re.match(r'\s*(do|while|for)\b', X[ln]) for ln in X if FN.get(ln) == fnname)
            allowed = []
            for c in cited:
                if c['table'] != 'catalogue': continue
                f_ = c['function:call line'].split(':')[0]
                if c['effect [derived]'].startswith('clamped'):
                    check('%s: %s says clamped, which needs a loop in %s' % (pid, c['id'], f_), has_loop(f_))
                    allowed.append(c['id'])
            if d != 'identical' and cited and not allowed: check('%s: no cited row is a clamping one, so every differing byte must be in the nation record UI block' % pid, SF.ui_only(ctl, aft), d)
        else: check('%s: saves present in %s' % (pid, art), False, 'fetch them with fetch_archive.py')
        ip = art + 'saves/inputs/' + q['input']
        if os.path.exists(ip): check('%s: the input save %s hashes as recorded' % (pid, q['input']), sha(ip) == q['input_sha'])
        check('%s: the input save is in SAVES.sha256' % pid, hashes.get(q['input']) == q['input_sha'])
    # ------------------------------------------------------------ the plays table is complete against the recorded plays
    tbl = [r['play'] for r in T.get('plays', [])]
    check('plays table: no play listed twice', len(tbl) == len(set(tbl)), str(sorted(x for x in set(tbl) if tbl.count(x) > 1)))
    check('plays table: every recorded play (plays_*.jsonl) is listed: missing %s' % sorted(set(PL) - set(tbl)), set(PL) <= set(tbl))
    check('plays table: every listed play has a record: unknown %s' % sorted(set(tbl) - set(PL)), set(tbl) <= set(PL))
    # ------------------------------------------------------------ required confirmations: enforced from the TASK (docs/tasks/refusal-texts.md) and the recorded plays, not from the finding's own cells
    TASK = open(os.path.join(paths.ROOT, 'docs', 'tasks', 'refusal-texts.md'), encoding='utf-8').read()
    REQUIRED = [('UA04 split of a one-unit army', 'TUnitMap_SplitArmy', 'only 1 unit'),
                ('UA05 join over 20 units and over 100,000 troops', 'TUnitMap_JoinArmies', 'more than 20 units'),
                ('UA05 join over 20 units and over 100,000 troops', 'TUnitMap_JoinArmies', 'more than 100,000 troops'),
                ('UF05 join fleets while one carries an army', 'TUnitMap_JoinFleets', 'carrying an army'),
                ('D05 a unit too small to split', 'TChangeArmyUnits_SplitUnit', 'too small to split'),
                ('D06 rename more than one unit or a mercenary unit', 'TChangeArmyUnits_RenameUnit', 'rename 1 unit'),
                ('D06 rename more than one unit or a mercenary unit', 'TChangeArmyUnits_RenameUnit', 'regular units')]
    row_at = {int(re.fullmatch(r'\w+:(\d+)', r_['function:call line']).group(1)): rid_ for rid_, r_ in CAT.items()}
    for phrase, fn_req, kw in REQUIRED:
        check('required: the task names %r' % phrase, phrase in TASK)
        lines_ = [ln for ln in all_call_lines if FN.get(ln) == fn_req and kw in (site(ln)[0] or '')]
        if not check('required %s / %r: exactly one call site of %s in the extract has that literal (found %s)' % (phrase[:4], kw, fn_req, lines_), len(lines_) == 1): continue
        rid_ = row_at.get(lines_[0])
        if not check('required %s / %r: the call site (line %d) is catalogued' % (phrase[:4], kw, lines_[0]), rid_ is not None): continue
        ev = []                                          # the recorded plays that reached this handler and whose box reads as this row's literal
        for pid_, qs in PL.items():
            q_ = qs[-1]
            if fn_req in handlers_of(q_)[0] and TITLE.get(site(lines_[0])[1]) in [b['title'] for b in q_['boxes']] and max(best_ratio(e, q_) for e in expected_text(CAT[rid_])) >= THR: ev.append(pid_)
        if not check('required %s: row %s has a recorded play whose clicks reach %s and whose box reads as it (%s)' % (phrase[:4], rid_, fn_req, ev), bool(ev)): continue
        cell_ = CAT[rid_].get('play [confirmed]', '-')
        check('required %s: row %s is confirmed in the catalogue by a recorded play of %s (cell %r)' % (phrase[:4], rid_, ev, cell_[:40]), cell_.startswith('[confirmed]') and any(p_ in re.findall(r'(?:^|; |\[confirmed\] )(\w+)', cell_) for p_ in ev))
        check('required %s: the plays table lists a play of %s with row %s' % (phrase[:4], ev, rid_), any(r_['play'] in ev and rid_ in r_['rows'].split(',') for r_ in T.get('plays', [])))
    combined = sorted(pid_ for pid_, qs in PL.items() if 'combined case' in qs[-1]['note'])
    check('required: the task asks for a combined case (play one combined case)', 'play one combined case' in TASK)
    check('required: at least one combined-case play is recorded (%s)' % combined, bool(combined))
    for pid_ in combined:
        hs = handlers_of(PL[pid_][-1])[0]
        check('required: combined play %s (handlers %s) is listed in the orderings table with the row whose line appeared' % (pid_, sorted(hs)),
              any(o_['function'] in hs and o_['combined case played'] == pid_ and o_['row whose line appeared'] != '-' for o_ in T.get('orderings', [])))
    # ------------------------------------------------------------ every screenshot of every box of a recorded play exists and matches its record, SAVES.sha256 and the manifest (a missing file is a mismatch)
    OCRREC = {}
    for f_ in sorted(glob.glob(data + 'ocr_b*.jsonl')):
        for l_ in open(f_, encoding='utf-8'): r_ = json.loads(l_); OCRREC.setdefault(r_['png'], []).append(r_)
    for r in T.get('plays', []):
        pid = r['play']
        if pid not in PL: continue
        q = PL[pid][-1]; tag_ = 'REF_%s_%s' % (pid, q['batch'])
        shots = []
        for b in q['boxes']:
            png = b['png']; shots.append(png)
            recs_ = [x for x in OCRREC.get(png, []) if x['play'] == pid and x['wid'] == b['wid']]
            check('%s: box screenshot %s has its OCR record (ocr_b*.jsonl) with the same box text' % (pid, png), any(x['text'] == b['text'] for x in recs_))
            m_ = re.search(r'_(box|confirm)_box\d+', png)
            if m_: shots += sorted(n for n in hashes if re.fullmatch(re.escape('%s_%s_screen' % (tag_, m_.group(1))) + r'(\.v\d+)?\.png', n))
        for png in dict.fromkeys(shots):
            p = art + png
            if not check('%s: screenshot %s exists in the artifacts' % (pid, png), os.path.exists(p), 'missing: a cited screenshot is evidence'): continue
            check('%s: screenshot %s has a hash in SAVES.sha256 and in a manifest, and the file matches both' % (pid, png), hashes.get(png) is not None and mem.get(png) == hashes[png] and sha(p) == hashes[png], '%s / %s / %s' % (hashes.get(png), mem.get(png), sha(p)))
    # ------------------------------------------------------------ order of tests: recomputed from the control flow of the extract
    refus = [r for r in CAT.values() if r['table'] == 'catalogue']
    line_of = lambda r: int(re.fullmatch(r'\w+:(\d+)', r['function:call line']).group(1))
    fn_of = lambda r: r['function:call line'].split(':')[0]
    fns = {}
    for r in refus: fns.setdefault(fn_of(r), []).append(r)
    DERIVED = {}
    for fn, rs in fns.items():
        ranks = C.rank_in_function(X, [line_of(r) for r in rs])
        DERIVED[fn] = [r['id'] for r in sorted(rs, key=lambda r: ranks[line_of(r)])]
        for r in rs:
            cell = r['test order']; m = re.match(r'(\d+) of (\d+)\b', cell)
            if cell.startswith('alternative'):
                others = [o for o in rs if o is not r]
                indep = all(not (C.last_test(X, line_of(r)) in C.tests_on_path(X, line_of(o)) or C.last_test(X, line_of(o)) in C.tests_on_path(X, line_of(r))) for o in others)
                check('%s: said to be an alternative of the other refusals of %s: none lies on the path of another' % (r['id'], fn), indep)
            else:
                check('%s test order %r: recomputed %d of %d from the control flow of %s' % (r['id'], cell, ranks[line_of(r)], len(rs), fn), bool(m) and int(m.group(1)) == ranks[line_of(r)] and int(m.group(2)) == len(rs))
    ordrows = {r['function']: [x.strip() for x in r['refusals in the order the code tests them'].split('>')] for r in T.get('orderings', [])}
    want = {fn: ids for fn, ids in DERIVED.items() if len(ids) >= 2 and not any(CAT[i]['test order'].startswith('alternative') for i in ids)}
    check('orderings table lists exactly the functions with two or more ordered refusals (%s)' % sorted(want), sorted(ordrows) == sorted(want), sorted(ordrows))
    for fn, ids in want.items():
        check('ordering %s: finding %s vs recomputed %s' % (fn, ordrows.get(fn), ids), ordrows.get(fn) == ids)
    # combined cases: both conditions must have held in the control save, and the box must be the one the code order predicts
    def numbers(pid, q):
        ctl = art + 'saves/' + q['control']
        ents = __import__('play_meta').W.get(pid, [])
        armies = [SF.army_numbers(ctl, int(e.split(':')[1])) for e in ents if e.startswith('army:')]
        fleets = [SF.fleet_numbers(ctl, int(e.split(':')[1])) for e in ents if e.startswith('fleet:')]
        return armies, fleets
    def threshold(row):
        for col in ('condition [derived]',):
            for ln, q in re.findall(r'L(\d+) «([^»]*)»', row.get(col, '')):
                m = re.search(r'< (0x[0-9a-f]+)', q)
                if m: return int(m.group(1), 16)
        return None
    for r in T.get('orderings', []):
        if r['combined case played'] == '-': continue
        pid, shown, fn = r['combined case played'], r['row whose line appeared'], r['function']
        if not check('combined play %s exists and its control save is present' % pid, pid in PL and os.path.exists(art + 'saves/' + PL[pid][-1]['control'])): continue
        q = PL[pid][-1]; armies, fleets = numbers(pid, q); preds = {}
        for i in DERIVED[fn]:
            lit = spans(CAT[i]['literal'])[0]; th = threshold(CAT[i])
            if 'on a fleet' in lit and armies: preds[i] = any(a[2] for a in armies)
            elif 'more than 20 units' in lit and th and armies: preds[i] = sum(a[0] for a in armies) >= th
            elif 'troops' in lit and th and armies: preds[i] = sum(a[1] for a in armies) >= th
            elif 'more than 100 ships' in lit and th and fleets: preds[i] = sum(f[0] for f in fleets) >= th
            elif 'carrying an army' in lit and fleets: preds[i] = any(f[1] >= 0 for f in fleets)
        check('combined case %s: every refusal of %s has a predicate recomputed from the control save (%s)' % (pid, fn, preds), set(preds) == set(DERIVED[fn]))
        true = [i for i in DERIVED[fn] if preds.get(i)]
        check('combined case %s: at least two refusal conditions hold in the control save (holding: %s)' % (pid, true), len(true) >= 2)
        check('combined case %s: the box the code order predicts is %s; the finding says %s' % (pid, true[0] if true else None, shown), bool(true) and true[0] == shown)
        others = [i for i in DERIVED[fn] if i != shown]
        rs = max(best_ratio(e, q) for e in expected_text(CAT[shown]))
        ro = max(best_ratio(e, q) for o in others for e in expected_text(CAT[o]))
        check('combined case %s: the play\'s box reads as %s (%.2f) and not as the others (%.2f)' % (pid, shown, rs, ro), rs >= THR and rs > ro + 0.1)
    # ------------------------------------------------------------ the clone table: the original's line is recomputed from the extract, not read from another table
    def row_spans(rid):
        line = line_of(CAT[rid]); lit = site(line)[0]
        return [lit] if lit is not None else spans(' + '.join(C.spans(X, line)))
    for r in T.get('clone', []):
        rid = r['row']
        if check('clone row %s is catalogued' % rid, rid in CAT):
            check('clone table: the original\'s line of %s: finding %r vs the call site in the extract %r' % (rid, r["the original's line"], row_spans(rid)), spans(r["the original's line"]) == row_spans(rid))
    return checks[0], bad

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--finding', default=os.path.join(paths.ROOT, 'findings', '2026-10-05-refusal-texts-and-conditions.md'))
    ap.add_argument('--data', default=paths.DATA); ap.add_argument('--artifacts', default=paths.ART)
    ap.add_argument('--exe', default=os.environ.get('IC2_ORIG_EXE', os.path.expanduser('~/ic2-work/build/Imperial Conquest 2.exe')))
    ap.add_argument('--dump', default=os.environ.get('IC2_DUMP', '/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt'))
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    n, bad = run(a.finding, a.data, a.artifacts, a.exe, a.dump)
    msg = 'claims audit of %s: %d checks, %d mismatches\n' % (os.path.relpath(a.finding, paths.ROOT), n, len(bad)) + ''.join('MISMATCH %s\n' % b for b in bad)
    print(msg, end='')
    out = a.out or os.path.join(a.data, 'claims_audit_output.txt')
    if a.out != '-': print(write_new(out, msg))
    sys.exit(1 if bad else 0)
