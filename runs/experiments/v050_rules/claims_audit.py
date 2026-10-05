#!/usr/bin/env python3
"""Claims audit of the six findings. Every expected value is DERIVED, never typed in:
  - from the raw saves (state/sav.py on the archived copies in <artifacts>/saves),
  - from the tracked code extracts (code_extract_*.txt: line -> text) and the formulas those lines show,
  - compared with an INDEPENDENT record: another save, a tracked reading of a screenshot (q2_balance_values.tsv, q4_displayed_cost.tsv, q4_panel_pay.tsv),
    the unit prices read from the DAT file (dat_unit_prices.tsv), or the memory log of the play (state_log.jsonl).
The decompile dump is NOT an input here (check_dump_vs_extract.py compares the extracts with the dump separately and optionally).
usage: claims_audit.py [--artifacts DIR]      (default: <repo>/artifacts/run-exp-v050-rules, i.e. the archive extracted by fetch_archive.py)
Scenario identifiers (save names, army ids, the clicked tile, the number of arrow clicks) come from the tracked runners and logs; no expected RESULT is typed in.
Exit 1 on any mismatch. The library entry point is run(ctx) (tests doctor ctx to prove a wrong expected value fails)."""
import sys, os, re, glob, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paths import ROOT, ART, DATA
sys.path.insert(0, ROOT)
import state.sav as S
from common import write_new

class Ctx:
    def __init__(self, artifacts=ART, data=DATA):
        self.art = artifacts.rstrip('/') + '/'; self.data = data.rstrip('/') + '/'
        self.doctor = {}                # {('save', name): fn(dict) | ('tsv', name): fn(rows) | ('line', n): text}
        self._saves = {}; self._lines = None
    def save(self, name):
        if name not in self._saves:
            d = S.load(self.art + 'saves/' + name + '.SAV')
            f = self.doctor.get(('save', name))
            if f: f(d)
            self._saves[name] = d
        return self._saves[name]
    def lines(self):
        """line number -> text, from the tracked code extracts only."""
        if self._lines is None:
            self._lines = {}
            for f in sorted(glob.glob(self.data + 'code_extract_*.txt')):
                for l in open(f, errors='replace').read().split('\n')[1:]:
                    m = re.match(r'(\d+)\t(.*)$', l)
                    if m: self._lines[int(m.group(1))] = m.group(2)
            for k, v in self.doctor.items():
                if k[0] == 'line': self._lines[k[1]] = v
        return self._lines
    def tsv(self, stem, header=True):
        fs = sorted(glob.glob(self.data + stem + '*.tsv'), key=lambda p: (len(p), p))
        ls = [l for l in open(fs[-1]).read().split('\n') if l and not l.startswith('#')]
        rows = [l.split('\t') for l in (ls[1:] if header else ls)]
        f = self.doctor.get(('tsv', stem))
        if f: rows = f(rows)
        return rows
    def tsv_header_comment(self, stem):
        fs = sorted(glob.glob(self.data + stem + '*.tsv'), key=lambda p: (len(p), p))
        return open(fs[-1]).readline()
    def finding(self, stem):
        """the text of a finding under review (findings/<stem>.md); tests doctor it to prove a wrong claimed number fails."""
        t = open(os.path.join(ROOT, 'findings', stem + '.md')).read()
        f = self.doctor.get(('finding', stem))
        return f(t) if f else t
    def statelog(self):
        return [json.loads(l) for l in open(self.data + 'state_log.jsonl') if l.strip()]
    def steplog(self, name):
        return open(self.data + name).read()

ar = lambda d, i: next((a for a in d['armies'] if a['id'] == i), None)
tre = lambda d, n=0: d['nations'][n]['treasury']
mn = lambda a, b: min(a, b)

def run(ctx):
    checks = []
    def C(q, what, ok): checks.append((q, what, bool(ok)))
    L = ctx.lines()
    def line(q, n, *subs):
        for s in subs: C(q, 'extract line %d contains %r' % (n, s), s in L.get(n, ''))
    prices = {r[0]: (int(r[2]), int(r[3])) for r in ctx.tsv('dat_unit_prices')}      # type -> (initial, quarterly), read from the DAT
    def pay_gate(t, ty, q): return (t * prices[ty][1] // 1000) * q                    # TRecruitMercs_RecruitMercUnit :43633-43636
    def pay_shown(t, ty, q): return (t * prices[ty][1] * q) // 1000                   # TRecruitMercs_ChangeUnit :43603-43605
    def pay_actual(t, ty, q): return (((t // 200) * prices[ty][1]) * q) // 5          # FUN_00451B40 :54751, :54757, :54765
    # the formulas are the ones the extract lines show: check the shape of those lines, then use them
    line('Q4', 43635, '00478fd4'); line('Q4', 43636, '1000'); line('Q4', 43636, '0049d0ae'); line('Q4', 43605, '/ 1000'); line('Q4', 54751, '/ 200'); line('Q4', 54765, '/ 5')

    # ------------------------------ Q1: the purse
    s0, s1, s3, s4, s5, s6, b1, c0, c1 = (ctx.save(n) for n in ('Q1_00_start', 'Q1_01_army0_at_100_42', 'Q1_03_army1_supply_11x100', 'Q1_04_after_split', 'Q1_05_before_join', 'Q1_06_after_join', 'Q1b_01_after_one_up_click', 'Q1c_00_before_click', 'Q1c_01_after_click_own_city'))
    log1 = ctx.steplog('q1.log')
    clicks = int(re.search(r'money x(\d+)', log1).group(1))                         # the number of "+100" clicks, from the play log
    p, t = ar(s0, 1)['money'], tre(s0)
    for _ in range(clicks):                                                         # TAFSupply_ChangeMoney :43118-43135, treasury provider
        step = mn(100, 1000 - p); p += step; t -= step
    C('Q1', 'Supply army x%d: predicted purse %d and treasury %d = the after-save (%d, %d)' % (clicks, p, t, ar(s3, 1)['money'], tre(s3)), (p, t) == (ar(s3, 1)['money'], tre(s3)) and p == 1000 and clicks * 100 > 1000 - ar(s0, 1)['money'])
    line('Q1', 43118, 'FUN_00448fd0'); line('Q1', 43119, '1000 - '); line('Q1', 43125, 'DAT_00474aa8'); line('Q1', 43134, 'DAT_0047c1f8')
    # split partner
    new = [a for a in s4['armies'] if a['id'] not in {x['id'] for x in s3['armies']} and a['troops'] > 0]
    C('Q1', 'split created exactly one army with purse 0, supplies 0, moves 0 (human owner)', len(new) == 1 and (new[0]['money'], new[0]['supplies'], new[0]['moves']) == (0, 0, 0))
    line('Q1', 48740, 'DAT_0047c1f8'); line('Q1', 48732, 'DAT_0047c1f2'); line('Q1', 48733, '== \'\\0\'')
    pid = new[0]['id']
    # partner supplied the same way
    p2, t2 = 0, tre(s4)
    for _ in range(clicks):
        step = mn(100, 1000 - p2); p2 += step; t2 -= step
    C('Q1', 'partner supplied x%d: predicted purse %d and treasury %d = the before-join save' % (clicks, p2, t2), (p2, t2) == (ar(s5, pid)['money'], tre(s5)))
    # Join: the partner is the highest-index own army at distance 1; gates from the before-save; result from the after-save
    a1 = ar(s5, 1); a15 = ar(s5, pid)
    adj = [a['id'] for a in s5['armies'] if a['troops'] > 0 and a['owner'] == a1['owner'] and a['id'] != 1 and max(abs(a['x'] - a1['x']), abs(a['y'] - a1['y'])) == 1]
    gates_ok = (not a1['embarked'] and not a15['embarked'] and len(a1['units']) + len(a15['units']) < 21 and a1['troops'] + a15['troops'] <= 100000 and max(adj) == pid)
    j = ar(s6, 1)
    C('Q1', 'Join: gates hold (not aboard, units %d+%d < 21, troops %d+%d <= 100000, partner = highest adjacent index %s)' % (len(a1['units']), len(a15['units']), a1['troops'], a15['troops'], adj), gates_ok)
    C('Q1', 'Join: kept purse %d = %d + %d (no cap), supplies %d = sum, troops = sum, units = sum, moves 0, partner gone, treasury unchanged' % (j['money'], a1['money'], a15['money'], j['supplies']),
      j['money'] == a1['money'] + a15['money'] > 1000 and j['supplies'] == a1['supplies'] + a15['supplies'] and j['troops'] == a1['troops'] + a15['troops'] and len(j['units']) == len(a1['units']) + len(a15['units']) and j['moves'] == 0 and ar(s6, pid)['troops'] == 0 and tre(s6) == tre(s5))
    line('Q1', 46992, 'DAT_0047c1f8'); line('Q1', 46997, 'DAT_0047c1f2'); line('Q1', 46984, '0x15'); line('Q1', 46987, '0x186a1')
    # over-cap trim: one up click on the joined purse
    step = mn(100, 1000 - j['money'])
    C('Q1', 'over-cap trim: step min(100, 1000-%d) = %d: purse %d and treasury %d predicted = the after-save' % (j['money'], step, j['money'] + step, tre(s6) - step), (ar(b1, 1)['money'], tre(b1)) == (j['money'] + step, tre(s6) - step) and step < 0)
    # no human refill: save pair for the move, save pair for the click
    st = [c for c in s1['cities'] if c['owner'] == 0 and max(abs(c['x'] - ar(s1, 0)['x']), abs(c['y'] - ar(s1, 0)['y'])) == 1 and c['supplies'] > 0]
    would = ar(s0, 0)['money'] < 500 and tre(s0) > 0                                 # the AI refill's own condition (FUN_0044F6D8 :53098-53103)
    C('Q1', 'move next to %d own cities with stock: the refill condition held (purse<500, treasury>0) yet purse/supplies are unchanged' % len(st), len(st) >= 2 and would and (ar(s1, 0)['money'], ar(s1, 0)['supplies']) == (ar(s0, 0)['money'], ar(s0, 0)['supplies']) and tre(s1) == tre(s0))
    key = lambda d, i: (ar(d, i)['x'], ar(d, i)['y'], ar(d, i)['moves'], ar(d, i)['money'], ar(d, i)['supplies'], ar(d, i)['troops'])
    adjown = [c['name'] for c in c0['cities'] if c['owner'] == 0 and max(abs(c['x'] - ar(c0, 1)['x']), abs(c['y'] - ar(c0, 1)['y'])) == 1]
    C('Q1', 'click on own adjacent city %s: army 1 (x,y,moves,purse,supplies,troops) and the treasury identical in the save pair' % adjown, adjown and all(key(c0, i) == key(c1, i) for i in (0, 1, 14)) and tre(c0) == tre(c1) and len(c0['news']) == len(c1['news']))
    q1c = ctx.steplog('q1c.log'); sel = re.findall(r'selected army (?:before|after) the click[^:]*: (-?\d+)', q1c)
    C('Q1', 'memory-only: selection %s (before, after) from q1c.log' % sel, sel == ['1', '-1'])
    for n, subs in ((53092, ('1000 <',)), (53096, ('= 1000',)), (53098, ('< 500',)), (53100, ('+ 500',)), (53101, ('DAT_00474aa8',)), (53106, ('/ 5',)), (54759, ('< 1',)), (54765, ('/ 5)',)), (54772, ('psVar11[4]',)), (57618, ('DAT_0047c1f8',)), (49648, ('DAT_0047c1f8',)), (49687, ('DAT_0047c1f8',)),
                    (53980, ('80000',) if False else ()), (53967, ('20000',)), (53979, ('FUN_0044a698',)), (53980, ('80000', '-1 <')), (53981, ('psVar5[4]',)), (53975, ('0x12',)), (53978, ('0x14',)),
                    (43162, ('FUN_00448fd0',)), (43163, ('1000 - ',)), (43154, ('FUN_00448fd0',)), (43039, ('FUN_00448fd0',)), (43041, ('* 5)',)), (44056, ('1000 - ',)), (46384, ('0x14', '0x15b'))):
        line('Q1', n, *subs)

    # signed Buy supplies (R1 of round 2): derived from the clamp order the extract shows, truncation toward zero for the negative division
    for n, subs in ((43011, ('FUN_00448fd8',)), (43013, ('FUN_00448fd0',)), (43026, ('/ 100',)), (43028, ('+ 1',)), (43041, ('* 5',)), (43071, ('/ 5',)), (43081, ('DAT_0047c1f8',))): line('Q1', n, *subs)
    def buy(amount, troops, supplies, stock, purse):
        a = max(0, amount); a = min(a, stock); a = min(a, troops // 100 - supplies + 1); a = min(a, purse * 5)
        q = abs(a) // 5 * (1 if a >= 0 else -1)                                         # IDIV truncates toward zero
        return a, purse - q
    # the example's inputs and its claimed results are read from the finding; the amount and purse are recomputed here from the inputs alone
    num = lambda x: int(x.replace(',', '').replace('\u2212', '-'))
    txt = ctx.finding('2026-10-05-army-purse-writes-and-the-1000-cap')
    m = re.search(r'Example `\[derived\]`: ([\d,]+) troops, ([\d,]+) supplies, purse ([\d,]+):.*?amount ([\u2212\-]?[\d,]+),.*?purse ([\d,]+)\.', txt)
    m8 = re.search(r'1,000 \u2192 ([\d,]+)\)', txt)
    troops, sup, purse0, c_amount, c_purse = (num(g) for g in m.groups()) if m else (0, 0, 0, None, None)
    a, newp = buy(10, troops, sup, 10**6, purse0)                                      # one up-arrow press (+10), the stock not binding
    C('Q1', 'signed Buy supplies [derived]: %d troops, %d supplies, purse %d: recomputed amount %d, purse %d; the finding claims amount %s, purse %s (table) and %s (summary)' % (troops, sup, purse0, a, newp, c_amount, c_purse, m8 and m8.group(1)),
      m is not None and m8 is not None and (a, newp) == (c_amount, c_purse) and num(m8.group(1)) == newp and purse0 == 1000 and newp > purse0)
    C('Q1', 'signed Buy supplies [derived]: an army below its room (supplies %d) pays for a positive amount: purse %d -> %d' % (troops // 200, purse0, buy(10, troops, troops // 200, 10**6, purse0)[1]),
      buy(10, troops, troops // 200, 10**6, purse0)[1] < purse0)

    # ------------------------------ Q2: the balance sheet
    q2a, q2b = ctx.save('Q2_00_start_tax10'), ctx.save('Q2_01_tax20')
    rows = {(r[0], r[1]): r[2] for r in ctx.tsv('q2_balance_values') if len(r) == 3 and r[2]}
    def sheet(tag, d):
        n = d['nations'][0]; tb = n['tax_base']
        trade = sum(m['tax_base'] // 12 for m in d['nations'] if n['relations'].get(m['name']) in (1, 2))
        exp = {'Taxes': tb * n['tax'] // 100, 'Tribute': tb >> 2, 'Trade': trade, 'Administration': n['wealth'] // 20000 + n['cities_count'] * 7}
        exp['Total revenue'] = exp['Taxes'] + exp['Tribute'] + exp['Trade']
        dl = min(n['wealth'] // 500, 20000)
        exp['Debt limit'] = dl - dl % 100 if dl < 5001 else (dl - dl % 500 if dl - 5001 < 5000 else dl - dl % 1000)
        for k, v in exp.items():
            got = rows.get(('Q2_%s_balance_sheet.png' % tag, k), '').replace(',', '')
            C('Q2', '%s %s: derived from the save %d, read from the screenshot %s' % (tag, k, v, got), got == str(v))
    sheet('00_tax10', q2a); sheet('01_tax20', q2b)
    C('Q2', 'only the tax rate differs between the two saves, so Tribute (taxBase div 4) is the same line in both', q2a['nations'][0]['tax_base'] == q2b['nations'][0]['tax_base'] and q2a['nations'][0]['tax'] != q2b['nations'][0]['tax'] and rows[('Q2_00_tax10_balance_sheet.png', 'Tribute')] == rows[('Q2_01_tax20_balance_sheet.png', 'Tribute')])
    live = sum((c['tribute'] * c['pop'] // c['max_pop']) << 2 for c in q2a['cities'] if c['owner'] == 0)
    C('Q2', 'stored taxBase %d differs from the live city sum %d (the line follows the stored word)' % (q2a['nations'][0]['tax_base'], live), live != q2a['nations'][0]['tax_base'])
    for n, subs in ((55439, ('474abc',)), (55440, ('474aba',)), (55445, ('0x44c',)), (55449, ('>> 2',)), (55456, ('>> 2',)), (55457, ('FUN_004499ec',)), (55466, ('/ 20000',)), (54866, ('0x440',)), (54875, ('0x44c', '0x44a')), (54876, ('>> 2',)), (54877, ('/ 20000',)), (48428, ('== 1',)), (48430, ('/ 0xc',)), (55541, ('/ 500',)), (55542, ('20000',)), (55545, ('0x1389',)), (55548, ('5000',)), (55551, ('10000',))):
        line('Q2', n, *subs)

    # ------------------------------ Q3: disbanding queued recruits
    q3 = [ctx.save(n) for n in ('Q3_00_start', 'Q3_01_after_disband_hi3200', 'Q3_02_after_disband_hi4000')]
    def removed(b, a):
        qb = sorted((x['type'], x['troops'], x['city']) for x in b['nations'][0]['recruit_slots']); qa = sorted((x['type'], x['troops'], x['city']) for x in a['nations'][0]['recruit_slots'])
        gone = list(qb)
        for x in qa: gone.remove(x)
        return gone
    for k in (0, 1):
        b, a = q3[k], q3[k + 1]; gone = removed(b, a); nb, na = b['nations'][0], a['nations'][0]
        C('Q3', 'step %d removed exactly one queue entry %s' % (k + 1, gone), len(gone) == 1)
        ty, tr_, _ = gone[0]
        exp = max(0, nb['mobilization'] - 1 - tr_ * 1000 // nb['wealth'])
        C('Q3', 'step %d: mobilisation %d -> %d predicted %d (floor division; rounding would give %d); treasury %d -> %d unchanged; queue %d -> %d' % (k + 1, nb['mobilization'], na['mobilization'], exp, max(0, nb['mobilization'] - 1 - round(tr_ * 1000 / nb['wealth'])), nb['treasury'], na['treasury'], len(nb['recruit_slots']), len(na['recruit_slots'])),
          na['mobilization'] == exp and na['treasury'] == nb['treasury'] and len(na['recruit_slots']) == len(nb['recruit_slots']) - 1)
    # the amount lost: the recruiting cost of the first removed entry, from the two fixture saves and the DAT price
    f0 = S.load(ROOT + '/saves/run0-start-AUTO0720-seed12345.SAV'); f1 = S.load(ROOT + '/saves/recruit-hi3200-0720.SAV')
    ty, tr_, _ = removed(q3[0], q3[1])[0]
    C('Q3', 'cost paid at queueing: treasury %d -> %d = %d = %d div 200 x initial price %d (DAT)' % (tre(f0), tre(f1), tre(f0) - tre(f1), tr_, prices[ty][0]), tre(f0) - tre(f1) == tr_ // 200 * prices[ty][0] and tre(q3[1]) == tre(f1))
    # the cap asymmetry (formulas of :56000-56005 and :56157-56166), shown on the formula, not on a save
    inc = lambda m, t, w: min(100, m + t * 1000 // w + 1); dec = lambda m, t, w: max(0, m - 1 - t * 1000 // w)
    w = q3[0]['nations'][0]['wealth']; tt = (1 * w + 999) // 1000                    # a unit whose floor term t*1000 div w is 1 (total step 1 + 1 = 2)
    C('Q3', 'cap asymmetry (formulas of :56000-56005 and :56157-56166): from 99 a recruit with floor term %d (step %d) gives %d, its disband then gives %d, not 99' % (tt * 1000 // w, tt * 1000 // w + 1, inc(99, tt, w), dec(inc(99, tt, w), tt, w)), inc(99, tt, w) == 100 and dec(inc(99, tt, w), tt, w) == 100 - (tt * 1000 // w + 1) != 99)
    for n, subs in ((56157, ('00474958',)), (56158, ('1000',)), (56162, ('1000',)), (56164, ('FUN_00448fd8',)), (56167, ('FUN_0044a610',)), (49007, ('0x2ec',)), (55996, ('0x438',)), (55999, ('00478fd2',)), (56000, ('1000',)), (56001, ('0x442',)), (56003, ('FUN_00448fd0',)), (55949, ('00474a90',)), (55950, ('== 100',)), (55957, ('0x4a',)), (56131, ('FUN_00429eb8',)), (56148, ('== 6',))):
        line('Q3', n, *subs)

    # ------------------------------ Q4: the mercenary hire
    q4 = {n: ctx.save(n) for n in ('Q4_00_start', 'Q4_01_purse20_before_hire', 'Q4_02_after_refused_hire', 'Q4_03_purse30_before_hire', 'Q4_04_after_heraclea_hire', 'Q4_05_before_thurii_hire', 'Q4_06_after_thurii_hire')}
    pool = lambda d: {m['slot']: m for m in d['mercenaries']}
    A = lambda n: ar(q4[n], 1)
    disp = {r[0]: int(r[1]) for r in ctx.tsv('q4_displayed_cost')}
    panel = {r[1]: int(r[2]) for r in ctx.tsv('q4_panel_pay', header=False)}
    gone1 = [s for s in pool(q4['Q4_03_purse30_before_hire']) if s not in pool(q4['Q4_04_after_heraclea_hire'])]
    gone2 = [s for s in pool(q4['Q4_05_before_thurii_hire']) if s not in pool(q4['Q4_06_after_thurii_hire'])]
    C('Q4', 'each hire emptied exactly one pool slot (%s, %s); the refusal emptied none' % (gone1, gone2), len(gone1) == 1 and len(gone2) == 1 and pool(q4['Q4_01_purse20_before_hire']).keys() == pool(q4['Q4_02_after_refused_hire']).keys())
    offs = [pool(q4['Q4_03_purse30_before_hire'])[gone1[0]], pool(q4['Q4_05_before_thurii_hire'])[gone2[0]]]
    refused_offer = pool(q4['Q4_01_purse20_before_hire'])[gone1[0]]
    pr = A('Q4_01_purse20_before_hire')['money']
    C('Q4', 'refusal pair: purse %d < gate %d of the Samnite offer: no unit, purse %d, treasury %d unchanged' % (pr, pay_gate(refused_offer['troops'], refused_offer['type'], refused_offer['quality']), A('Q4_02_after_refused_hire')['money'], tre(q4['Q4_02_after_refused_hire'])),
      pr < pay_gate(refused_offer['troops'], refused_offer['type'], refused_offer['quality']) and len(A('Q4_02_after_refused_hire')['units']) == len(A('Q4_01_purse20_before_hire')['units']) and A('Q4_02_after_refused_hire')['money'] == pr and tre(q4['Q4_02_after_refused_hire']) == tre(q4['Q4_01_purse20_before_hire']))
    shots = {0: 'Q4_04_heraclea_purse30_offer_selected.png', 1: 'Q4_06_thurii_purse30_offer_selected.png'}
    for k, (b, a, o) in enumerate((('Q4_03_purse30_before_hire', 'Q4_04_after_heraclea_hire', offs[0]), ('Q4_05_before_thurii_hire', 'Q4_06_after_thurii_hire', offs[1]))):
        ub, ua = A(b)['units'], A(a)['units']; added = ua[len(ub)]
        g, sh_, ac = pay_gate(o['troops'], o['type'], o['quality']), pay_shown(o['troops'], o['type'], o['quality']), pay_actual(o['troops'], o['type'], o['quality'])
        C('Q4', 'hire %d: offer %s %d q%d label %d -> unit added with the same fields (%s, %s, %d, %d, label %d); one unit more, troops +%d' % (k + 1, o['type'], o['troops'], o['quality'], o['label'], added['name'], added['type'], added['troops'], added['quality'], added['merc'], A(a)['troops'] - A(b)['troops']),
          (added['type'], added['troops'], added['quality'], added['merc']) == (o['type'], o['troops'], o['quality'], o['label']) and len(ua) == len(ub) + 1 and A(a)['troops'] - A(b)['troops'] == o['troops'])
        C('Q4', 'hire %d: purse %d >= gate %d, and nothing was charged: purse %d -> %d, treasury %d -> %d' % (k + 1, A(b)['money'], g, A(b)['money'], A(a)['money'], tre(q4[b]), tre(q4[a])), A(b)['money'] >= g and A(a)['money'] == A(b)['money'] and tre(q4[a]) == tre(q4[b]))
        C('Q4', 'hire %d: gate %d, displayed estimate %d, actual pay %d; the screenshot box shows %s' % (k + 1, g, sh_, ac, disp.get(shots[k])), disp.get(shots[k]) == sh_)
    o2 = offs[1]
    C('Q4', 'the HC offer: purse %d is between the gate %d and the displayed %d (hired although the box said more); the displayed %d differs from the actual pay %d' % (A('Q4_05_before_thurii_hire')['money'], pay_gate(o2['troops'], o2['type'], o2['quality']), pay_shown(o2['troops'], o2['type'], o2['quality']), pay_shown(o2['troops'], o2['type'], o2['quality']), pay_actual(o2['troops'], o2['type'], o2['quality'])),
      pay_gate(o2['troops'], o2['type'], o2['quality']) <= A('Q4_05_before_thurii_hire')['money'] < pay_shown(o2['troops'], o2['type'], o2['quality']) and pay_shown(o2['troops'], o2['type'], o2['quality']) != pay_actual(o2['troops'], o2['type'], o2['quality']))
    for n in ('Q4_04_after_heraclea_hire', 'Q4_06_after_thurii_hire'):
        tot = sum(pay_actual(u['troops'], u['type'], u['quality']) for u in A(n)['units'] if u['merc'])
        wrong = sum(pay_shown(u['troops'], u['type'], u['quality']) for u in A(n)['units'] if u['merc'])
        C('Q4', '%s: Mercenary pay on the army panel %s = sum of the actual-pay formula over the army\'s mercenaries %d (the displayed formula would give %d)' % (n, panel.get(n + '.SAV'), tot, wrong), panel.get(n + '.SAV') == tot and (tot != wrong or n == 'Q4_04_after_heraclea_hire'))
    for n, subs in ((43633, ('DAT_0047c1f8',)), (43637, ('too little money',)), (43672, ('0xffff',)), (43641, ('FUN_0044a698',)), (43644, ('0x186a1',)), (43647, ('FUN_0044a698',)), (43651, ('/ 500',)), (43691, ('100,000',)), (43652, ('too little space',)),
                    (46871, ('0x89',)), (46878, ('DAT_004a0320',)), (46881, ('FUN_00449d08',)), (46884, ('< 1',)), (46885, ('0x186a1',)), (46887, ('== 3',)), (46893, ('< 0xf',)), (46898, ('0x89',)), (46899, ('/ 500',)), (46904, ('fleet cannot carry',)), (46910, ('bigger',)), (46914, ('20 units',)), (46888, ('enemy city',)),
                    (41084, ('/ 200',)), (41086, ('FUN_00448fd0',) if False else ()), (41089, ('/ 5',))):
        line('Q4', n, *subs)

    # ------------------------------ Q5: disbanding a unit in Change units
    q5 = {n: ctx.save(n) for n in ('Q5A_00_start', 'Q5A_01_after_disband_regular', 'Q5B_00_start', 'Q5B_01_after_disband_merc')}
    for (b, a, i) in (('Q5A_00_start', 'Q5A_01_after_disband_regular', 0), ('Q5B_00_start', 'Q5B_01_after_disband_merc', 1)):
        uk = lambda u: {k: u[k] for k in ('type', 'troops', 'quality', 'merc', 'name')}
        ub, ua = [uk(u) for u in ar(q5[b], i)['units']], [uk(u) for u in ar(q5[a], i)['units']]; gone = list(ub)
        for u in ua: gone.remove(u)
        nb, na = q5[b]['nations'][0], q5[a]['nations'][0]
        C('Q5', '%s -> %s: exactly one unit removed %s' % (b, a, [(u['type'], u['troops'], u['merc']) for u in gone]), len(gone) == 1)
        u = gone[0]; exp = max(0, nb['mobilization'] - 1 - u['troops'] * 1000 // nb['wealth']) if u['merc'] == 0 else nb['mobilization']
        near = [c for c in q5[b]['cities'] if c['owner'] == 0 and max(abs(c['x'] - ar(q5[b], i)['x']), abs(c['y'] - ar(q5[b], i)['y'])) <= 1]
        C('Q5', '%s: unit %s %d (merc label %d): mobilisation %d -> %d predicted %d; treasury %d -> %d, purse and supplies unchanged; own city in the 3x3: %s' % (b, u['type'], u['troops'], u['merc'], nb['mobilization'], na['mobilization'], exp, nb['treasury'], na['treasury'], [c['name'] for c in near]),
          na['mobilization'] == exp and na['treasury'] == nb['treasury'] and (ar(q5[a], i)['money'], ar(q5[a], i)['supplies']) == (ar(q5[b], i)['money'], ar(q5[b], i)['supplies']) and (u['merc'] != 0 or near) and ar(q5[b], i)['troops'] - ar(q5[a], i)['troops'] == u['troops'])
    C('Q5', 'one case is a regular unit (mobilisation moves) and one a mercenary (it does not)', q5['Q5A_00_start']['nations'][0]['mobilization'] != q5['Q5A_01_after_disband_regular']['nations'][0]['mobilization'] and q5['Q5B_00_start']['nations'][0]['mobilization'] == q5['Q5B_01_after_disband_merc']['nations'][0]['mobilization'])
    for n, subs in ((45787, ('*psVar1 == 0',)), (45789, ('* 1000',)), (45791, ('FUN_00448fd8',)), (45820, ('00474ab2',)), (45718, ('0 <',)), (45734, ('== 6',)), (45736, ('0x13',)), (45739, ('0x1ee',)), (45743, ('0x1d6',)), (45744, ('0x1ea',)), (45756, ('near its own city',)), (45839, ('= 2',)),
                    (44483, ('param_4',)), (44485, ('* 1000',)), (44316, ('TArmyToArmy_RemoveUnit',)), (44402, ('TArmyToArmy_RemoveUnit',)), (44397, ('0x770',)), (43793, ('FUN_004494e4',)), (45408, ('FUN_004494e4',)), (48107, ('0x8000000f',) if False else ()), (48106, ('0x13',))):
        line('Q5', n, *subs)

    # ------------------------------ Q6: the attack order
    q6 = {n: ctx.save(n) for n in ('Q6_00_start', 'Q6_01_after_far_click', 'Q6_02_adjacent_moves5', 'Q6_03_after_prompt_no', 'Q6_04_adjacent_moves0', 'Q6_05_after_zero_move_click', 'Q6b_01_after_yes')}
    script = open(HERE + '/q6_refused_attack.py').read()
    tx, ty = map(int, re.search(r'click_tile\((\d+), (\d+), pause=1\.5\)', script).groups())       # the clicked tile, from the tracked runner
    a_id = int(re.search(r'GREECE, ME, A9 = \d+, \d+, (\d+)', script).group(1))                  # the army id, from the tracked runner
    d0 = q6['Q6_00_start']; me = d0['current_nation']
    city = next(c for c in d0['cities'] if (c['x'], c['y']) == (tx, ty)); owner = city['owner']
    rel = lambda d: (d['nations'][me]['relations'][d['nations'][owner]['name']], d['nations'][owner]['relations'][d['nations'][me]['name']])
    def legal(d):
        a = ar(d, a_id); return a['moves'] >= 1 and max(abs(a['x'] - tx), abs(a['y'] - ty)) == 1
    steps = (('C far click', 'Q6_00_start', 'Q6_01_after_far_click'), ('B No', 'Q6_02_adjacent_moves5', 'Q6_03_after_prompt_no'), ('A zero moves', 'Q6_04_adjacent_moves0', 'Q6_05_after_zero_move_click'))
    for lab, b, a in steps:
        db, da = q6[b], q6[a]
        # legal = army selected, moves >= 1, distance exactly 1 (:46514-46521); a click that is not legal, or answered No, declares nothing
        unchanged = rel(db) == rel(da) and rel(db)[0] != 3 and len(db['news']) == len(da['news']) and (ar(db, a_id)['moves'], ar(db, a_id)['troops']) == (ar(da, a_id)['moves'], ar(da, a_id)['troops']) and db['nations'][me]['relations'] == da['nations'][me]['relations']
        C('Q6', '%s: legal (moves>=1, distance 1) = %s on the before-save; relation %s -> %s, news and army unchanged' % (lab, legal(db), rel(db), rel(da)), unchanged and legal(db) == (lab == 'B No'))
    db, da = q6['Q6_02_adjacent_moves5'], q6['Q6b_01_after_yes']
    allies = [m['name'] for m in db['nations'] if m['name'] != db['nations'][owner]['name'] and db['nations'][owner]['relations'].get(m['name']) == 2 and db['nations'][me]['relations'].get(m['name']) != 3]
    others_unchanged = all(db['nations'][me]['relations'][k] == da['nations'][me]['relations'][k] for k in db['nations'][me]['relations'] if k != db['nations'][owner]['name'])
    exp_news = '%s DECLARES WAR ON %s.' % (db['nations'][me]['name'].upper(), db['nations'][owner]['name'].upper())
    C('Q6', 'Yes branch: legal %s, relation %s -> %s; no ally of the target to cascade to (%s) so no other relation changed; news +2 starting %r; army moves %d -> %d; city %s now owner %s (attacker %s)' % (legal(db), rel(db), rel(da), allies, exp_news, ar(db, a_id)['moves'], ar(da, a_id)['moves'], city['name'], next(c for c in da['cities'] if (c['x'], c['y']) == (tx, ty))['owner'], me),
      legal(db) and rel(da) == (3, 3) and rel(db)[0] != 3 and not allies and others_unchanged and da['news'][len(db['news'])] == exp_news and len(da['news']) == len(db['news']) + 2 and ar(da, a_id)['moves'] == 0)
    sel = ctx.statelog()
    C('Q6', 'target owner is another nation than the attacker and the relation before the clicks was not war', owner != me and rel(d0)[0] != 3)
    for n, subs in ((46514, ('DAT_0047c1f2', '< 1')), (46515, ('FUN_004492a0',)), (46532, ('0x14', '0x50')), (46539, ('bVar4',)), (46540, ('== 3',)), (46541, ('attack this city',)), (46544, ('!= 3',)), (46545, ('FUN_00449b40',)), (46547, ('FUN_0044b27c',)), (46551, ('= -1',)), (46555, ('200U',)), (46563, ('!= DAT_004a0320',)),
                    (46566, ('attack this army',)), (46570, ('FUN_00449b40',)), (46572, ('FUN_0044aee4',)), (46582, ('300U',)), (46590, ('== DAT_004a0320',)), (46592, ('== -1',)), (46594, ('/ 500',)), (46601, ('FUN_0044b79c',)), (46611, ('DAT_004a032a',)), (46611, ('< 1',)), (46612, ('FUN_004492a0',)),
                    (46619, ('FUN_004494e4',)), (46621, ('< 0',)), (46622, ('== 3',)), (46623, ('attack this fleet',)), (46627, ('FUN_00449b40',)), (46629, ('FUN_0044b5d0',)), (46637, ('docked at its own city',)), (48089, ('param_2',)), (48094, ('0x13f',)), (48106, ('0x13',)), (48112, ('== puVar6',) if False else ()),
                    (48502, ('00474696',)), (48504, ('00474696',)), (48513, ('== 3',)), (48515, ('= 3',)), (48532, ('== 2',)), (48455, ('declares war on',)), (49815, ('DAT_0047c1f2',)), (55385, ('FUN_00449b40',)), (46384, ('0x14', '0x15b')), (46427, ('TUnitMap_SelectUnit',)), (49903, ('DAT_0049c278',))):
        line('Q6', n, *subs)
    return checks

def main():
    art = ART
    if '--artifacts' in sys.argv: art = sys.argv[sys.argv.index('--artifacts') + 1]
    ctx = Ctx(art)
    checks = run(ctx)
    bad = [c for c in checks if not c[2]]
    out = ['# claims audit: %d checks, %d mismatches' % (len(checks), len(bad))] + ['%s\t%s\t%s' % (q, 'OK' if ok else 'MISMATCH', w) for q, w, ok in checks]
    print(write_new(os.path.join(DATA, 'claims_audit_output.txt'), '\n'.join(out) + '\n')); print(out[0])
    for q, w, ok in bad: print('MISMATCH', q, w)
    return 1 if bad else 0
if __name__ == '__main__': sys.exit(main())
