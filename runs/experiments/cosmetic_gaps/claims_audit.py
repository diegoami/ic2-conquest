#!/usr/bin/env python3
"""Claims audit of findings/2026-10-06-cosmetic-gaps.md.

Every literal, number and play attribution in the finding is compared with a value RECOMPUTED from the sources; nothing the finding
says is taken as its own truth:
 * the tracked code extract (code_extract_cosmetic.v3.txt — v1/v2's CALLSITES function column is known-broken and not used): the
   SetTurnTitle format literals, the MakeSound case table (every cited `line: case` re-read from the extract, with its enclosing
   function recomputed as the last `// ====` header before the line), the StoreFormPositions offsets, the toggle's XOR + paint,
   CityOrFleet's SetVisible groups, FindProviders' relation-3 skip, TAFSupply_OK's flag and the two CM_ messages;
 * the form resource dump (dfm_TAFSupply.v2.txt, parsed into objects/properties): the caption, the client size, btn_buy and btn_ok
   (caption, rectangle, OnClick);
 * the recordings (plays_*.jsonl, every batch, tags unique): the titles T1/T2 read, the toggle words and hashes of T3, the SAV
   words of T4, the dialog control lists of U1/U2/U2B (open or not, which buttons, at which rectangle), the staged save's record;
 * the WAV harvests (wav_opens_*.txt): the SOUND<N>.WAV each cited sound play opened;
 * the artifacts: every screenshot the finding names is hashed against SAVES.sha256.
The finding's own claims are read from its text (the two evidence tables and the title strings) and must EQUAL the recomputed
values.   usage: claims_audit.py [--finding F] [--data D] [--artifacts A] [--out FILE]
Exit status 0 only with 0 mismatches."""
import sys, os, re, json, glob, hashlib, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from common import latest, write_new

def run(finding, data, art, quiet=True):
    data = data.rstrip('/') + '/'; art = art.rstrip('/') + '/'
    checks = [0]; bad = []
    hashes = {}
    for l in open(data + 'SAVES.sha256'):
        p = l.split()
        if len(p) == 2: hashes[p[1]] = p[0]
    def check(name, cond, detail=''):
        checks[0] += 1
        if not cond: bad.append('%s: %s' % (name, detail))
        return cond
    sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()

    # ------------------------------------------------------------ sources: the code extract
    # The extract has two parts: FUNCS (whole function bodies, in the script's list order) and CALLSITES (each call
    # with three lines of context, prefixed '---- in <function> ----', the enclosing function recomputed from the
    # dump by make_extract's fixed last-header rule). Lines can appear in BOTH parts, so the two are parsed apart and
    # the site table comes only from CALLSITES' own markers - never from a header that merely precedes them in the file.
    X = {}; FN = {}; cur = None; SITES = []; CALLS_IN = {}; ALLNUM = set()
    incalls = False; sitefn = None
    for l in open(latest(data + 'code_extract_cosmetic.txt'), encoding='utf-8', errors='replace'):
        l = l.rstrip('\n')
        m = re.match(r'---- in (\S+) ----', l)
        if m: sitefn = m.group(1); continue
        if l.startswith('# CALLSITES'): incalls = True; continue
        m = re.match(r'(\d+)\t(.*)', l)
        if not m: continue
        ln = int(m.group(1)); ALLNUM.add(ln)
        if incalls:
            mm = re.search(r'TPremierForm_MakeSound\((?:\(int\))?DAT_004a0bd0,\s*(\d+)\)', m.group(2))
            if mm and not m.group(2).startswith('void'):
                SITES.append((ln, int(mm.group(1)), sitefn))
            mm = re.search(r'TPremierForm_(SetTurnTitle|StoreFormPositions)\(', m.group(2))
            if mm and not m.group(2).startswith('void'):
                CALLS_IN.setdefault(mm.group(1), []).append((ln, sitefn))
        else:
            X[ln] = m.group(2)
            mm = re.match(r'// ==== (\S+) @ ([0-9a-f]+) ====', m.group(2))
            if mm: cur = mm.group(1)
            FN[ln] = cur
    ALLX = ALLNUM          # a cited line may be a function body line OR a CALLSITES context line
    def fnbody(name):
        ks = [n for n, f in FN.items() if f == name]
        return '\n'.join(X[n] for n in sorted(ks))
    def text(a, b):
        return ' '.join(X[n] for n in sorted(X) if a <= n <= b)

    # M04: the title format, from SetTurnTitle's own lines (raw: the spacing is the claim)
    body = fnbody('TPremierForm_SetTurnTitle'); raw_st = body
    for lit in ('"Imperial Conquest 2    "', "\"\\'s turn\"", '"   ("', '")"'):
        check('m04 literal %r in SetTurnTitle' % lit, lit in raw_st, raw_st[:120])
    check('m04 truncation 91 (0x5b)', '0x5b' in body, body[:120])
    # when set: the three call sites
    st_calls = dict(CALLS_IN.get('SetTurnTitle', []))
    for line, fn in ((53216, 'FUN_0044fa20'), (58091, 'TPremierForm_OpenGameFile'), (58201, 'TPremierForm_StartTurn')):
        check('m04 callsite %d in %s' % (line, fn), st_calls.get(line) == fn, 'CALLSITES says %r' % (st_calls.get(line),))

    # M06: the case table recomputed from the extract's CALLSITES
    sites = SITES
    finding_cases = {}
    fm = open(finding, encoding='utf-8').read()
    for row in re.finditer(r'^\| (\d+) \| Sound(\d+) \|.*\|$', fm, re.M):
        for m in re.finditer(r'(\d+) in `([^`]+)`', row.group(0)):
            finding_cases.setdefault(int(m.group(1)), set()).add((int(row.group(1)), m.group(2)))
    for line, case, fn in sites:
        check('m06 site %d: case %d in %s' % (line, case, fn),
              (case, fn) in finding_cases.get(line, set()),
              'recomputed (%d, %s) vs finding %s' % (case, fn, finding_cases.get(line)))
    check('m06 all 16 sites are in the finding', set(finding_cases) == {n for n, _, _ in sites},
          'finding-only %s extract-only %s' % (sorted(set(finding_cases) - {n for n, _, _ in sites}), sorted({n for n, _, _ in sites} - set(finding_cases))))
    mkbody = fnbody('TPremierForm_MakeSound')
    for case in range(1, 11):
        check('m06 case %d -> Sound%d' % (case, case), '"Sound%d"' % case in mkbody, mkbody[:100])
    check('m06 .WAV suffix', '".WAV"' in mkbody and 'PlaySoundA' in mkbody, mkbody[:100])

    # M05: the offsets StoreFormPositions writes - the dump spells them as absolute addresses of nation 0's record
    # (&DAT_<0x474670+off> + nation*0x494), so each offset the finding claims is bound by its address
    spbody = fnbody('TPremierForm_StoreFormPositions')
    m05para = re.search(r'### 5\. Window positions.*?(?=\n### |\n## )', fm, re.S).group(0)
    offclaims = [int(x, 16) for x in re.findall(r'\+0x4[678][0-9a-fA-F]', m05para)]
    check('m05 some offsets claimed', len(offclaims) >= 12, offclaims)
    for off in offclaims:
        check('m05 offset +0x%x as DAT_%x in StoreFormPositions' % (off, 0x474670 + off), ('dat_%08x' % (0x474670 + off)) in spbody.lower(), 'looking for DAT_%08x' % (0x474670 + off))
    check('m05 nation stride 0x494', '0x494' in spbody, spbody[:200])
    # R3: the H/W ASSIGNMENT - the finding's per-window offsets must match the getter->address pairing in the code
    # (FUN_00412880 = client Width reads the RECT word at +8; FUN_004128c4 = client Height at +12: see their bodies)
    assigns = {}
    cur_getter = None
    for l in spbody.split('\n'):
        m = re.search(r'uVar2 = (FUN_004128(?:80|c4))\(DAT_(0045e7(?:18|40|0c))\)', l)
        if m: cur_getter = (m.group(1), m.group(2)); continue
        m = re.search(r'&DAT_(00474[0-9a-f]{3}) \+ iVar1\) = \(short\)uVar2', l)
        if m and cur_getter:
            assigns[cur_getter[1]] = assigns.get(cur_getter[1], {}); assigns[cur_getter[1]][cur_getter[0]] = int(m.group(1), 16) - 0x474670
            cur_getter = None
    winaddr = {'0045e718': ('area', 0x46E), '0045e740': ('unit', 0x476), '0045e70c': ('information', 0x47E)}
    for g, fname in (('FUN_00412880', 'W'), ('FUN_004128c4', 'H')):
        gb = fnbody(g)
        check('m05 %s is client %s (RECT word at %s)' % (g, 'Width' if fname == 'W' else 'Height', '+8' if fname == 'W' else '+12'),
              ('+ 8)' if fname == 'W' else '+ 0xc)') in gb.replace('0xc)', '+ 0xc)') or (('auStack_14 [8]' if fname == 'W' else 'auStack_14 [12]') in gb), gb[:160])
    for form, (wname, lbase) in winaddr.items():
        got = assigns.get(form, {})
        for g, fname in (('FUN_00412880', 'W'), ('FUN_004128c4', 'H')):
            want_off = lbase + (4 if fname == 'H' else 6)   # four shorts: L+0 T+2 H+4 W+6
            check('m05 %s %s at +0x%x (the code writes %s there)' % (wname, fname, want_off, g),
                  got.get(g) == want_off, 'code says %r (want +0x%x)' % (got, want_off))
            letter = fname.lower()
            check('m05 finding claims %s %s at +0x%x (spelled %s+0x%x)' % (wname, fname, want_off, letter, want_off),
                  ('%s+0x%x' % (letter, want_off)) in fm.lower(),
                  'the finding does not spell %s+0x%x' % (letter, want_off))
    sp_calls = dict(CALLS_IN.get('StoreFormPositions', []))
    for line, fn in ((58108, 'TPremierForm_SaveGameFile'), (58127, 'TPremierForm_SaveGameFileAs'), (58786, 'TPremierForm_CloseAllForms')):
        check('m05 callsite %d in %s' % (line, fn), sp_calls.get(line) == fn, 'CALLSITES says %r' % (sp_calls.get(line),))

    # A01: the toggle
    tgbody = fnbody('TAreaMap_ToggleMap')
    check('a01 toggle XORs the +0x46C byte (address 0x474adc)', '0x474adc' in tgbody.lower() and '^ 1' in tgbody, tgbody[:200])
    check('a01 toggle resets the selected-cell word', '+ 0x2b8) = 0xffff' in tgbody, tgbody[:200])
    check('a01 toggle repaints', 'TAreaMap_PaintForm' in tgbody, tgbody)

    # UA01: CityOrFleet groups, SetVisible, FindProviders, OK/CM_RELEASE, CM_VISIBLECHANGED
    cobody = fnbody('TAFSupply_CityOrFleet')
    check('ua01 CityOrFleet flag +0x27d', '0x27d' in cobody, cobody[:120])
    check('ua01 CityOrFleet fleet slot +0x288', '0x288' in cobody, cobody[:200])
    check('ua01 CityOrFleet uses SetVisible (FUN_00412c08)', 'FUN_00412c08' in cobody, cobody[:200])
    fpbody = fnbody('TAFSupply_FindProviders')
    check('ua01 FindProviders skips relation 3', '!= 3' in fpbody, fpbody[:400])
    okbody = fnbody('TAFSupply_OK')
    check('ua01 OK sets flag 0x4a', '0x4a] = 1' in okbody, okbody)
    cmrbody = fnbody('FUN_0042313c')
    check('ua01 OK posts CM_RELEASE 0xb021', '0xb021' in cmrbody, cmrbody)
    svbody = fnbody('FUN_00412c08')
    check('ua01 FUN_00412c08 posts CM_VISIBLECHANGED 0xb00b', '0xb00b' in svbody, svbody)

    # ------------------------------------------------------------ sources: the form resource (the exact version the finding names: v1's root header is garbled)
    mdfm = re.search(r'(dfm_TAFSupply(?:\.v\d+)?\.txt)', fm)
    dfm_path = data + (mdfm.group(1) if mdfm else 'dfm_TAFSupply.v2.txt')
    dfm = parse_dfm(dfm_path)
    top = dfm.get('AFSupply', {}).get('props', {})
    check('dfm source is the finding\'s own file', 'v2' in dfm_path, dfm_path)
    check('dfm AFSupply caption', top.get('Caption') == "'Supply army'", top.get('Caption'))
    check('dfm client 470x335', top.get('ClientWidth') == '470' and top.get('ClientHeight') == '335', (top.get('ClientWidth'), top.get('ClientHeight')))
    buy = dfm.get('btn_buy', {}).get('props', {})
    check('dfm btn_buy caption', buy.get('Caption') == "'Buy supplies'", buy.get('Caption'))
    check('dfm btn_buy rect 320,136,100,26', (buy.get('Left'), buy.get('Top'), buy.get('Width'), buy.get('Height')) == ('320', '136', '100', '26'), buy)
    check('dfm btn_buy OnClick TransferSupply', 'TransferSupply' in buy.get('OnClick', ''), buy.get('OnClick'))
    bok = dfm.get('btn_ok', {}).get('props', {})
    check('dfm btn_ok caption OK', bok.get('Caption') == "'OK'", bok.get('Caption'))
    check('dfm btn_ok OnClick OK', bok.get('OnClick', '').strip("{'ident '}") == 'OK' or 'OK' in bok.get('OnClick', ''), bok.get('OnClick'))

    # ------------------------------------------------------------ sources: the recordings
    plays = {}
    for f in sorted(glob.glob(data + 'plays_*.jsonl')):
        partial = 'partial' in os.path.basename(f)      # the restored b2 partial: historical, never canonical (its tags' canonical recordings are checked below)
        for l in open(f):
            if not l.strip(): continue
            r = json.loads(l); tag = r.get('tag') or 'CG_%s_%s' % (r['play'], r['batch'])
            if partial:
                check('partial tag %s has a canonical recording' % tag, tag in plays or True, '')   # order-independent: checked again after the loop
                continue
            check('tag %s unique' % tag, tag not in plays, 'also recorded earlier')
            plays[tag] = r
    for f in sorted(glob.glob(data + 'plays_*partial*.jsonl')):
        for l in open(f):
            if l.strip():
                tag = json.loads(l).get('tag')
                check('partial tag %s has a canonical recording' % tag, tag in plays, 'the partial records a play no canonical file holds')
    def P(tag):
        check('play %s recorded' % tag, tag in plays, 'not in any plays_*.jsonl')
        return plays.get(tag, {})

    # every recording's clicks: the pointer read back must sit where the click went
    for tag, r in plays.items():
        for c in r.get('clicks', []):
            if (c['x'], c['y']) != (c['pointer']['x'], c['pointer']['y']):
                check('%s click %s,%s pointer' % (tag, c['x'], c['y']), False, 'pointer at %s,%s' % (c['pointer']['x'], c['pointer']['y']))
    checks[0] += len(plays)          # the loop above only counts failures; count the invariant per play

    # R2: a sound row's case must match its WAV name, and the play it cites must have opened exactly that WAV
    for row in re.finditer(r'^\| (\d+) \| Sound(\d+) \|.*\|$', fm, re.M):
        case = int(row.group(1))
        check('m06 row case %d names Sound%d' % (case, case), case == int(row.group(2)), row.group(0)[:80])
        for tag in re.findall(r'(CG_S\d+_b\d+)', row.group(0)):
            r = plays.get(tag)
            check('m06 row case %d cites %s (ok)' % (case, tag), r is not None and r.get('status') == 'ok', 'status %s' % (r or {}).get('status'))
            if r and r.get('wav_opens'):
                check('m06 %s opened Sound%d.WAV' % (tag, case), ('SOUND%d.WAV' % case) in open(data + r['wav_opens'], errors='replace').read(), r['wav_opens'])

    # M04 plays
    t1 = P('CG_T1_b1b')['titles']
    check('t1 at_start bare', t1.get('at_start', {}).get('name') == 'Imperial Conquest 2', t1.get('at_start'))
    check('t1 form_open bare', t1.get('form_open', {}).get('name') == 'Imperial Conquest 2', t1.get('form_open'))
    check('t1 after_ok empty leader', t1.get('after_ok', {}).get('name') == "Imperial Conquest 2    Rome's turn   ()", repr(t1.get('after_ok', {}).get('name')))
    t2 = P('CG_T2_b1c')['titles']
    check('t2 after_load leader', t2.get('after_load', {}).get('name') == "Imperial Conquest 2    Rome's turn   (Appius Claudius)", repr(t2.get('after_load', {}).get('name')))

    # A01 play
    t3 = P('CG_T3_b1c')
    check('t3 toggle 1->0->1', (t3.get('toggle_before', {}).get('byte'), t3.get('toggle_after_one', {}).get('byte'), t3.get('toggle_after_two', {}).get('byte')) == (1, 0, 1),
          (t3.get('toggle_before'), t3.get('toggle_after_one'), t3.get('toggle_after_two')))
    check('t3 hashes in the finding', set(re.findall(r'\d+\.\d{3}', fm)) >= {str(t3.get('hash_before')), str(t3.get('hash_after_one')), str(t3.get('hash_after_two'))},
          (t3.get('hash_before'), t3.get('hash_after_one'), t3.get('hash_after_two')))
    check('t3 tooltips seen', t3.get('hint_seen_1') and t3.get('hint_seen_2'), (t3.get('hint_seen_1'), t3.get('hint_seen_2')))

    # M05 play
    t4 = P('CG_T4_b1c')
    w = t4.get('sav_words', {}).get('words', {})
    check('t4 nation0 area words', w.get('nations', {}).get('0', {}).get('area') == [42, 104, 170, 320], w.get('nations', {}).get('0', {}).get('area'))
    check('t4 main words', w.get('main') == [-4, -4, 281, 650], w.get('main'))
    check('t4 moved == restored', t4.get('geo_moved') == t4.get('geo_restored') == [42, 104, 328, 196], (t4.get('geo_moved'), t4.get('geo_restored')))

    # M06 plays: the WAV each opened
    for tag, wav in (('CG_S1_b2', 'SOUND1.WAV'), ('CG_S2_b2', 'SOUND2.WAV'), ('CG_S3_b3', 'SOUND8.WAV'), ('CG_S4_b3', 'SOUND9.WAV')):
        r = P(tag)
        p = data + r.get('wav_opens', '')
        okk = r.get('wav_opens') and os.path.exists(p) and wav in open(p, errors='replace').read()
        check('%s opened %s' % (tag, wav), okk, p)

    # UA01 plays
    u1 = P('CG_U1_b6').get('dialog', {}).get('own_city', {})
    check('u1 dialog open', u1.get('open') is True, u1.get('open'))
    check('u1 no buy button', u1.get('buy_button') is None, u1.get('buy_button'))
    check('u1 buttons only OK', [b['text'] for b in u1.get('buttons', [])] == ['OK'], u1.get('buttons'))
    u2 = P('CG_U2_b4').get('dialog', {}).get('hostile_city', {})
    check('u2 hostile: no dialog', u2.get('open') is False, u2.get('open'))
    u2b = P('CG_U2B_b6')
    d = u2b.get('dialog', {}).get('staged_neutral_city', {})
    check('u2b staged record', 'STAGED' in (u2b.get('staged') or {}).get('note', ''), u2b.get('staged'))
    check('u2b buy visible enabled', (d.get('buy_button') or {}).get('text') == 'Buy supplies' and (d.get('buy_button') or {}).get('enabled') == 1 and (d.get('buy_button') or {}).get('visible') == 1, d.get('buy_button'))
    check('u2b buy at dfm rect', [d.get('buy_button', {}).get(k) for k in ('x', 'y', 'w', 'h')] == [343, 185, 100, 26], d.get('buy_button'))


    # R9: every dump line the finding cites must exist in the extract the finding names (its version string)
    mv = re.search(r'(code_extract_cosmetic(?:\.v\d+)?\.txt)', fm)
    check('finding names its extract version', bool(mv), 'no code_extract_cosmetic*.txt cited')
    for ln in sorted(set(int(x) for x in re.findall(r'\b(\d{5})\b', fm))):
        check('cited line %d exists in the extract' % ln, ln in ALLX, 'not in code_extract_cosmetic*.txt')

    # every play tag the finding cites must be a recording (and the audit reads its claims from those tags)
    for tag in sorted(set(re.findall(r'`(CG_[A-Z0-9]+_b\d+[a-z]?)`', fm))):
        check('cited tag %s is recorded' % tag, tag in plays, 'not in any plays_*.jsonl')

    # ------------------------------------------------------------ the finding's OWN quoted values, bound to the same sources
    recorded_titles = set()
    for r in plays.values():
        for t in (r.get('titles') or {}).values(): recorded_titles.add(t.get('name'))
    for q in sorted(set(re.findall(r'`(Imperial Conquest 2(?:[^`]*turn\s+\([^`]*\))?)`', fm))):
        check('m04 quoted title %r is a recorded title' % q, q in recorded_titles, 'not among the recordings')
    mt = re.search(r'byte `(\d) → (\d) → (\d)`', fm)
    if check('a01 finding quotes the toggle triple', bool(mt), 'pattern missing'):
        check('a01 quoted triple equals the recording', [int(mt.group(i)) for i in (1, 2, 3)] ==
              [t3.get('toggle_before', {}).get('byte'), t3.get('toggle_after_one', {}).get('byte'), t3.get('toggle_after_two', {}).get('byte')], mt.group(0))
    mc = re.search(r"Caption = '(Buy supplies)'", fm)
    if check('ua01 finding quotes the buy caption', bool(mc), 'pattern missing'):
        check('ua01 quoted caption equals the resource', mc.group(1) == 'Buy supplies' and dfm['btn_buy']['props']['Caption'] == "'%s'" % mc.group(1), mc.group(1))
    m05p = re.search(r'### 5\. Window positions.*?(?=\n## )', fm, re.S)
    if m05p:
        allowed = {tuple(v) for v in (w.get('nations', {}).get('0', {}).get('area'), w.get('main'),
                                      P('CG_T4_b1c').get('geo_moved'), P('CG_T4_b1c').get('geo_restored'), P('CG_T4_b1c').get('geo_loaded')) if v}
        for q in re.findall(r'\[(-?\d+, -?\d+, -?\d+, -?\d+)\]', m05p.group(0)):
            check('m05 quoted words [%s] is a recorded words/geometries value' % q, tuple(int(x) for x in q.split(',')) in allowed, sorted(allowed))

    # ------------------------------------------------------------ the artifacts the finding names
    for name in set(re.findall(r'`([A-Za-z0-9_.]+\.(?:png|SAV))`', fm)):
        hits = [os.path.join(r, f) for r, _, fs in os.walk(art) for f in fs if f == name]
        check('artifact %s hashed' % name, hits and hashes.get(name) == sha(hits[0]), 'found %d copies' % len(hits))
    return checks[0], bad

def norm_ws(s): return re.sub(r'\s+', ' ', s).strip()

def parse_dfm(path):
    """The TPF0 text dump into {object name: {'cls': class, 'props': {name: value}}}: a property belongs to the most
    recently declared object at any depth (children no longer leak their properties into the parent)."""
    dfm = {}; obj = None
    for l in open(path, encoding='utf-8'):
        m = re.match(r'\s*object (\w+): (\w+)', l)
        if m:
            obj = m.group(1); dfm[obj] = {'cls': m.group(2), 'props': {}}
            continue
        m = re.match(r'\s+(\w+) = (.*)$', l)
        if obj and m and not l.lstrip().startswith('end'):
            dfm[obj]['props'][m.group(1)] = m.group(2).rstrip()
    return dfm

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--finding', default=os.path.join(paths.ROOT, 'findings', '2026-10-06-cosmetic-gaps.md'))
    ap.add_argument('--data', default=os.path.join(paths.ROOT, 'runs', 'experiments', 'data', 'run-exp-cosmetic-gaps'))
    ap.add_argument('--artifacts', default=os.path.join(paths.ROOT, 'runs', 'experiments', 'artifacts', 'run-exp-cosmetic-gaps'))
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    art = a.artifacts if os.path.isdir(a.artifacts) else os.path.join(paths.ROOT, 'artifacts', 'run-exp-cosmetic-gaps')
    n, bad = run(a.finding, a.data, art)
    rep = ['claims audit of %s' % os.path.basename(a.finding), '%d checks, %d mismatches' % (n, len(bad))]
    rep += ['MISMATCH %s' % b for b in bad]
    txt = '\n'.join(rep) + '\n'
    print(txt)
    if a.out: write_new(a.out, txt)
    sys.exit(1 if bad else 0)
