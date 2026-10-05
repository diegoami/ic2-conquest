#!/usr/bin/env python3
"""Print the markdown tables of the finding (windows, after-OK, staging) from the sources, to paste into the finding. The audit (claims_audit.py) reads the
finding and recomputes every cell independently from the saves, the code extract and the tracked readings; this script is only a typing aid."""
import sys, os, json, glob, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ART, DATA, ROOT
import fmt
sys.path.insert(0, ROOT)
S = ART + 'saves/'
W = [  # id, reason, seat, source, screenshot
 ('W1', 'deposed, debt below -20,000 (treasury staged -30,000)', 0, 'AUTO:EOG_debt_b1_AUTO0721.SAV', 'EOG_debt_b1_04_window.png'),
 ('W2', 'deposed, debt below -(wealth div 500) (treasury staged -9,000)', 0, 'AUTO:EOG_debt_wealth_b1_AUTO0721.SAV', 'EOG_debt_wealth_b1_04_window.png'),
 ('W3', 'deposed, unity below 400 (unity staged 100)', 0, 'AUTO:EOG_unity_b1_AUTO0721.SAV', 'EOG_unity_b1_04_window.png'),
 ('W4', '250 BC (calendar staged 251 BC Winter week 11)', 0, 'AUTO:EOG_y250_b1_AUTO1200.SAV', 'EOG_y250_b1_04_window.png'),
 ('W5', 'victory, count word staged 334', 0, 'AUTO:EOG_victory_b1_AUTO0721.SAV', 'EOG_victory_b1_04_window.png'),
 ('W6', 'victory, all 334 cities staged as Rome\'s', 0, 'AUTO:EOG_victory_full_b7_AUTO0721.SAV', 'EOG_victory_full_b7_04_window.png'),
 ('W7', 'unity below 400 and debt together', 0, 'AUTO:EOG_unity_debt_b1_AUTO0721.SAV', 'EOG_unity_debt_b1_04_window.png'),
 ('W8', '250 BC and unity below 400 together', 0, 'AUTO:EOG_y250_unity_b1_AUTO1200.SAV', 'EOG_y250_unity_b1_04_window.png'),
 ('W9', 'victory and 250 BC together', 0, 'AUTO:EOG_victory_y250_b7_AUTO1200.SAV', 'EOG_victory_y250_b7_04_window.png'),
 ('W10', 'two humans: Gaul deposed, debt (treasury staged -30,000)', 6, 'AUTO:EOG2_debt_gaul_b3_AUTO0720.SAV', 'EOG2_debt_gaul_b3_gaul_window.png'),
 ('W11', 'two humans: 250 BC, first window (Rome)', 0, 'MEM:states_b5.jsonl#EOG2_y250_both_b5/first_window_open', 'EOG2_y250_both_b5_first_window.png'),
 ('W12', 'two humans: 250 BC, second window (Gaul)', 6, 'AUTO:EOG2_y250_both_b5_AUTO1200.SAV', 'EOG2_y250_both_b5_second_window.png'),
 ('W13', 'two humans: Gaul conquered by Rome (city count word and Felsina staged)', 6, 'CAPTURE:EOG2_conquest_before_siege.SAV+EOG2_conquest_after_gaul_conquered.SAV#city=Felsina#states_b6.jsonl#EOG2_conquest_b6/gaul_window_open', 'EOG2_conquest_b6_gaul_window.png'),
]
def mem_state(spec, seat):
    f, key = spec.split('#'); tag, step = key.split('/')
    for l in open(DATA + f):
        d = json.loads(l)
        if d['tag'] == tag and d['step'] == step: return d['seats'][str(seat)], d
def row(w):
    wid, reason, seat, src, png = w
    if src.startswith('AUTO:'):
        b = open(S + src[5:], 'rb').read(); c = fmt.nation_fields(b, seat); names = c['names']
        pop_now, money_now, cities_now = c['wealth'], c['treasury'], c['cities']
    elif src.startswith('MEM:'):
        st, d = mem_state(src[4:], seat); c = dict(st); c['year'] = d['calendar']['year_bc']; names = None
        pop_now, money_now, cities_now = st['wealth'], st['treasury'], st['cities']
        c['humans'] = d['humans']
    else:
        files, _city, spec1, spec2 = src[8:].split('#'); bf, af = files.split('+')
        st, d = mem_state(spec1 + '#' + spec2, seat); c = dict(st); c['year'] = d['calendar']['year_bc']
        pop_now, money_now, cities_now = st['wealth'], st['treasury'], st['cities']; names = None
    conq_name = '' if c['conquered_by'] < 0 else None
    if c['conquered_by'] >= 0 or src.startswith('CAPTURE'): conq_name = 'Rome'
    if src.startswith('CAPTURE'):
        c['conquered_by'] = 0
    t = fmt.window_texts(c['name'], c['leader'], c['year'], c['wealth_start'], c['cities_start'], c['treasury_start'], pop_now, cities_now, money_now, conq_name, c['conquered_by'], c['unity'])
    sha = hashlib.sha256(open(ART + png, 'rb').read()).hexdigest()[:12]
    return '| %s | %s | %d | `%s` | %s | %s | %s | %s | %d | %d | %s | %s | `%s` (%s) | `%s` |' % (wid, reason, seat, src, t['lbl_result2'], t['lbl_changes'],
        fmt.f18(c['wealth_start']).strip(), fmt.e74(pop_now).strip(), c['cities_start'], cities_now, fmt.f18(c['treasury_start']).strip(), fmt.f18(money_now).strip(), png, sha, 'EOG_2h_base_AUTO0720.SAV' if wid in ('W10','W11','W12','W13') else 'run0-start-AUTO0720-seed12345.SAV')
print('| id | reason | seat | source | lbl_result2 | lbl_changes | pop start | pop now | cities start | cities now | treasury start | treasury now | screenshot (sha256 prefix) | base save |')
print('|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|---|')
for w in W: print(row(w))

print()
# ---- staging rows from the staging log
import re as _re
print('| staged input | source save | operation | old | new | changed bytes |')
print('|---|---|---|---:|---:|---:|')
from state import sav as SAV
for l in open(DATA + 'staging_log.tsv'):
    ts, tag, src, srcsha, dst, dstsha, al = l.rstrip('\n').split('\t')
    if not (dst.endswith('_staged.SAV') or dst.endswith('_staged.v2.SAV')) : continue
    if any(x in dst for x in ('abdicate_b1', 'abdicate_b2_staged.SAV', 'debt_gaul_b2', 'y250_both_b3', 'y250_both_b4')): continue
    ranges, ops = al.split(' ops=', 1); ops = json.loads(ops)
    a = open(S + 'inputs/' + src if os.path.exists(S + 'inputs/' + src) else os.path.join(ROOT, 'saves', src), 'rb').read(); b = open(S + 'inputs/' + dst, 'rb').read()
    n = sum(1 for i in range(len(a)) if a[i] != b[i]); n0a, n0b = fmt.nation0(a), fmt.nation0(b)
    ta, tb = SAV.parse(a), SAV.parse(b)
    if not ops: print('| %s | %s | (no operation: byte-identical copy) | - | - | %d |' % (dst, src, n)); continue
    for op in ops:
        k = op[0]
        if k in ('treasury', 'unity', 'ncities'):
            off, f = {'treasury': (0x438, 'i'), 'unity': (0x440, 'h'), 'ncities': (0x446, 'h')}[k]
            import struct
            va = struct.unpack_from('<' + f, a, n0a + op[1] * SAV.NATION_LEN + off)[0]; vb = struct.unpack_from('<' + f, b, n0b + op[1] * SAV.NATION_LEN + off)[0]
            print('| %s | %s | %s[%d] | %d | %d | %d |' % (dst, src, k, op[1], va, vb, n))
        elif k == 'calendar':
            key = {'year': 'year_bc'}.get(op[1], op[1]); print('| %s | %s | calendar.%s | %d | %d | %d |' % (dst, src, op[1], ta[key], tb[key], n))
        elif k == 'city':
            ca = [x for x in ta['cities'] if x['id'] == op[1]][0]; cb = [x for x in tb['cities'] if x['id'] == op[1]][0]
            for f in op[2]: print('| %s | %s | city[%d].%s | %d | %d | %d |' % (dst, src, op[1], f, ca[f], cb[f], n))
        elif k == 'own_all':
            print('| %s | %s | own_all[%d] | - | - | %d |' % (dst, src, op[1], n))
print()
# ---- start table
print('| save | pop equal | treasury equal | cities equal | count = list |')
print('|---|---:|---:|---:|---:|')
for sv in ('run0-start-AUTO0720-seed12345.SAV', 'EOG_2h_base_AUTO0720.SAV'):
    p = os.path.join(ROOT, 'saves', sv) if os.path.exists(os.path.join(ROOT, 'saves', sv)) else S + 'inputs/' + sv
    b = open(p, 'rb').read(); st = SAV.parse(b)
    e = lambda f: sum(1 for n in range(16) if f(fmt.nation_fields(b, n), st['nations'][n]))
    print('| %s | %d | %d | %d | %d |' % (sv, e(lambda c, s: c['wealth_start'] == c['wealth']), e(lambda c, s: c['treasury_start'] == c['treasury']), e(lambda c, s: c['cities_start'] == c['cities']), e(lambda c, s: c['cities'] == len(s['city_list']))))

# ---- after_state and after_game rows
STATES = {}
for f in glob.glob(DATA + 'states_*.jsonl'):
    STATES[os.path.basename(f)] = [json.loads(l) for l in open(f)]
def st(spec):
    f, key = spec[4:].split('#'); tag, step = key.split('/')
    return [d for d in STATES[f] if d['tag'] == tag and d['step'] == step][0]
def sa(spec, seat):
    if spec.startswith('MEM:'):
        d = st(spec); s_ = d['seats'][str(seat)]; return dict(leader=s_['leader'], unity=s_['unity'], money=s_['treasury'])
    c = fmt.nation_fields(open(S + spec[5:], 'rb').read(), seat); return dict(leader=c['leader'], unity=c['unity'], money=c['treasury'], conq=c['conquered_by'])
AS = [
 ('S1', 'W1 debt below -20,000', 0, 'fall', 'MEM:states_b1.jsonl#EOG_debt_b1/window_open', 'MEM:states_b1.jsonl#EOG_debt_b1/after_ok'),
 ('S2', 'W2 debt below -(wealth div 500)', 0, 'fall', 'MEM:states_b1.jsonl#EOG_debt_wealth_b1/window_open', 'MEM:states_b1.jsonl#EOG_debt_wealth_b1/after_ok'),
 ('S3', 'W3 unity below 400', 0, 'fall', 'MEM:states_b1.jsonl#EOG_unity_b1/window_open', 'MEM:states_b1.jsonl#EOG_unity_b1/after_ok'),
 ('S4', 'W4 250 BC', 0, 'fall', 'MEM:states_b1.jsonl#EOG_y250_b1/window_open', 'MEM:states_b1.jsonl#EOG_y250_b1/after_ok'),
 ('S5', 'W5 victory (count word)', 0, 'fall', 'MEM:states_b1.jsonl#EOG_victory_b1/window_open', 'MEM:states_b1.jsonl#EOG_victory_b1/after_ok'),
 ('S6', 'W6 victory (all cities)', 0, 'fall', 'MEM:states_b7.jsonl#EOG_victory_full_b7/window_open', 'MEM:states_b7.jsonl#EOG_victory_full_b7/after_ok'),
 ('S7', 'W7 unity and debt', 0, 'fall', 'MEM:states_b1.jsonl#EOG_unity_debt_b1/window_open', 'MEM:states_b1.jsonl#EOG_unity_debt_b1/after_ok'),
 ('S8', 'W8 250 BC and unity', 0, 'fall', 'MEM:states_b1.jsonl#EOG_y250_unity_b1/window_open', 'MEM:states_b1.jsonl#EOG_y250_unity_b1/after_ok'),
 ('S9', 'W9 victory and 250 BC', 0, 'fall', 'MEM:states_b7.jsonl#EOG_victory_y250_b7/window_open', 'MEM:states_b7.jsonl#EOG_victory_y250_b7/after_ok'),
 ('S10', 'W10 two humans, Gaul debt', 6, 'fall', 'MEM:states_b3.jsonl#EOG2_debt_gaul_b3/gaul_window_open', 'SAVE:EOG2_debt_gaul_after_gaul_falls.SAV'),
 ('S11', 'W12 two humans, 250 BC, Gaul', 6, 'fall', 'MEM:states_b5.jsonl#EOG2_y250_both_b5/second_window_open', 'MEM:states_b5.jsonl#EOG2_y250_both_b5/after_both'),
 ('S12', 'W13 two humans, Gaul conquered', 6, 'conquered', 'MEM:states_b6.jsonl#EOG2_conquest_b6/gaul_window_open', 'SAVE:EOG2_conquest_after_gaul_conquered.SAV'),
 ('S13', 'Abdicate, one human', 0, 'abdicate', 'MEM:states_b2.jsonl#EOG_abdicate_b2/confirm_open', 'MEM:states_b2.jsonl#EOG_abdicate_b2/after_yes_t16'),
 ('S14', 'Abdicate, two humans (Rome)', 0, 'abdicate', 'MEM:states_b3.jsonl#EOG2_abdicate_rome_b3/loaded', 'SAVE:EOG2_abdicate_rome_after.SAV'),
]
print()
print('| id | scenario | seat | rule | leader before | leader after | unity before | unity after | treasury before | treasury after | conquered by after | before source | after source |')
print('|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---|---|')
for i, sc, seat, rule, b, a in AS:
    x, y = sa(b, seat), sa(a, seat)
    print('| %s | %s | %d | %s | %s | %s | %d | %d | %s | %s | %s | `%s` | `%s` |' % (i, sc, seat, rule, x['leader'], y['leader'], x['unity'], y['unity'], fmt.f18(x['money']).strip(), fmt.f18(y['money']).strip(), y.get('conq', '-') if rule == 'conquered' else '-', b, a))
def wl(ws):
    names = [w[0] for w in ws]
    if names == ['Imperial Conquest 2']: return 'caption only'
    if 'Unit map' in names and 'Area map' in names and 'Information' in names: return 'game windows'
    return 'other: ' + ','.join(names)
AG = [('G1', 'debt, one human', 'MEM:states_b1.jsonl#EOG_debt_b1/window_open', 'MEM:states_b1.jsonl#EOG_debt_b1/after_ok'),
 ('G2', 'debt by wealth, one human', 'MEM:states_b1.jsonl#EOG_debt_wealth_b1/window_open', 'MEM:states_b1.jsonl#EOG_debt_wealth_b1/after_ok'),
 ('G3', 'unity, one human', 'MEM:states_b1.jsonl#EOG_unity_b1/window_open', 'MEM:states_b1.jsonl#EOG_unity_b1/after_ok'),
 ('G4', '250 BC, one human', 'MEM:states_b1.jsonl#EOG_y250_b1/window_open', 'MEM:states_b1.jsonl#EOG_y250_b1/after_ok'),
 ('G5', 'victory (count word), one human', 'MEM:states_b1.jsonl#EOG_victory_b1/window_open', 'MEM:states_b1.jsonl#EOG_victory_b1/after_ok'),
 ('G6', 'victory (all cities), one human', 'MEM:states_b7.jsonl#EOG_victory_full_b7/window_open', 'MEM:states_b7.jsonl#EOG_victory_full_b7/after_ok'),
 ('G7', 'Abdicate Yes, one human', 'MEM:states_b2.jsonl#EOG_abdicate_b2/confirm_open', 'MEM:states_b2.jsonl#EOG_abdicate_b2/after_yes_t16'),
 ('G8', 'debt of Gaul, two humans', 'MEM:states_b3.jsonl#EOG2_debt_gaul_b3/gaul_window_open', 'MEM:states_b3.jsonl#EOG2_debt_gaul_b3/after_ok_rome_turn'),
 ('G9', 'Rome abdicates, two humans', 'MEM:states_b3.jsonl#EOG2_abdicate_rome_b3/loaded', 'MEM:states_b3.jsonl#EOG2_abdicate_rome_b3/after_yes_gaul_turn'),
 ('G10', '250 BC for both, two humans', 'MEM:states_b5.jsonl#EOG2_y250_both_b5/first_window_open', 'MEM:states_b5.jsonl#EOG2_y250_both_b5/after_both'),
 ('G11', 'Gaul conquered by Rome, two humans', 'MEM:states_b6.jsonl#EOG2_conquest_b6/gaul_window_open', 'MEM:states_b6.jsonl#EOG2_conquest_b6/after_ok')]
print()
print('| id | scenario | humans before | humans after | current seat after | windows after | program | year after | before source | after source |')
print('|---|---|---|---|---:|---|---|---:|---|---|')
for i, sc, b, a in AG:
    x, y = st(b), st(a)
    print('| %s | %s | %s | %s | %d | %s | %s | %d | `%s` | `%s` |' % (i, sc, x['humans'], y['humans'], y['cur_nation'], wl(y['windows']), 'keeps running' if y['alive'] else 'exited', y['calendar']['year_bc'], b, a))
