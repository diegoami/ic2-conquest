"""The number formatting and the End of Game text selection, rebuilt from the tracked code extract (code_extract_end_of_game*.txt): class Code reads the string
literals, thresholds and formatter constants FROM THE EXTRACT FILE it is given (`use(path)` selects it; the audit passes the one under its --data)."""
import re, os, struct
from paths import DATA

from common import latest
EXTRACT = latest(os.path.join(DATA, 'code_extract_end_of_game.txt'))        # the newest version of the tracked extract (older ones are kept)

def extract_lines(path=EXTRACT):
    """{ghidra line number: text} of the tracked code extract."""
    d = {}
    for l in open(path, encoding='utf-8'):
        m = re.match(r'(\d+)\t(.*)$', l.rstrip('\n'))
        if m: d[int(m.group(1))] = m.group(2)
    return d

ROLES = ['r1_a', 'r1_b', 'r1_c', 'year_end_text', 'unity_text', 'debt_text', 'conq_a', 'conq_b', 'victory_text', 'chg_a', 'chg_years', 'chg_short', 'chg_b', 'chg_c',
         'nat1_b', 'pop_w', 'cities_w', 'money_w', 'talents', 'nat2_in', 'nat2_bc', 'pop_w2', 'cities_w2', 'money_w2', 'talents2']

class Code:
    """What the code extract says: the string literals of THumanFalls_InitializeForm in the order they are written (mapped to roles by position, the count
    checked), the thresholds of its tests and of FUN_00452034, and the constants of the number formatter FUN_00448e74. All READ from the extract file; nothing
    about the window's text or limits is typed in here except the role names and the branch structure that mirrors the decompiled control flow."""
    def __init__(self, path):
        self.path = path; X = extract_lines(path); self.X = X
        def body(name):
            starts = [n for n, t in X.items() if t.startswith('// ==== ')]
            s = next(n for n in starts if name in X[n]); e = min([n for n in starts if n > s] + [max(X) + 1])
            return [(n, X[n]) for n in sorted(X) if s <= n < e]
        ini = body('THumanFalls_InitializeForm')
        lits = []
        for n, t in ini:
            if t.startswith('//'): continue
            lits += re.findall(r'"((?:[^"\\]|\\.)*)"', t)
        if len(lits) != len(ROLES): raise ValueError('InitializeForm has %d literals, expected %d' % (len(lits), len(ROLES)))
        self.lit = dict(zip(ROLES, lits))
        txt = '\n'.join(t for _, t in ini)
        num_ = lambda m: int(m, 0)
        self.year_end = num_(re.search(r'DAT_004a0332 == (0x[0-9a-f]+|\d+)', txt).group(1))
        self.cities_win = num_(re.search(r'DAT_00474ab6\)\[iVar3 \* 0x24a\] < (0x[0-9a-f]+|\d+)', txt).group(1))
        self.unity_min = num_(re.search(r'DAT_00474ab0\)\[iVar3 \* 0x24a\] < (\d+)', txt).group(1))
        self.short_year = num_(re.search(r'DAT_004a0332 < (0x[0-9a-f]+|\d+)', txt).group(1))
        self.years_base = num_(re.search(r'(0x[0-9a-f]+|\d+) - \(int\)DAT_004a0332', txt).group(1))
        ts = '\n'.join(t for _, t in body('FUN_00452034'))
        self.t_year = num_(re.search(r'DAT_004a0332 == (0x[0-9a-f]+|\d+)', ts).group(1))
        self.t_cities = num_(re.search(r'(0x[0-9a-f]+|\d+) < \(short\)\(&DAT_00474ab6', ts).group(1))
        self.t_unity = num_(re.search(r'DAT_00474ab0\)\[iVar1 \* 0x24a\] < (\d+)', ts).group(1))
        self.t_debt_div = int(re.search(r'/ (-\d+)', ts).group(1))
        self.t_debt_abs = int(re.search(r'< (-\d+)\)', ts).group(1))
        fl = '\n'.join(t for _, t in body('FUN_0044c8f0'))
        m = re.search(r'(0x[0-9a-f]+)\),CONCAT22\(uVar7,sVar6 \+ (0x[0-9a-f]+)\)', fl)
        self.fall_unity_cap, self.fall_unity_inc = num_(m.group(1)), num_(m.group(2))
        self.fall_money_bonus = int(re.search(r'DAT_00474aa8\)\[iVar2 \* 0x125\] \+ (\d+);', fl).group(1))
        cap = '\n'.join(t for _, t in body('FUN_0044bb18'))
        self.capture_wealth_mult = int(re.search(r'\* -(\d+);', cap).group(1))
        self.conquest_below = int(re.search(r'DAT_00474ab6\)\[sVar1 \* 0x24a\] < (\d+)', cap).group(1))
        fb = body('FUN_00448e74'); ft = '\n'.join(t for _, t in fb)
        self.fmt_width = len(re.search(r'FUN_00405b00\(param_2,"( +)"\)', ft).group(1))
        self.fmt_sign = int(re.search(r"param_2\[(\d+)\] = '-'", ft).group(1))
        self.fmt_start = int(re.search(r'sVar3 = (\d+);', ft).group(1))
        self.fmt_group = int(re.search(r'% (\d+) == 0', ft).group(1))
        self.fmt_comma = re.search(r"= '(,)'", ft).group(1)

    def e74(self, v):
        """FUN_00448e74: `fmt_width` spaces, the digits from index `fmt_start` with a comma before each group of `fmt_group`, the sign at index `fmt_sign`."""
        s = [' '] * self.fmt_width
        if v < 0: s[self.fmt_sign] = '-'
        d = str(abs(v)); i = self.fmt_start
        for k, ch in enumerate(d, 1):
            s[i] = ch; i += 1
            if (len(d) - k) % self.fmt_group == 0 and k < len(d): s[i] = self.fmt_comma; i += 1
        return ''.join(s)

    def f18(self, v):
        """FUN_00448f18: e74 with the trailing spaces cut."""
        return self.e74(v).rstrip(' ')

    def fires(self, wealth, treasury, unity, cities, year):
        """The conditions of FUN_00452034 that hold (the turn-start test), using the thresholds read from the extract. C division truncates toward zero."""
        q = int(wealth / self.t_debt_div)
        out = []
        if year == self.t_year: out.append('year')
        if cities > self.t_cities: out.append('cities')
        if unity < self.t_unity: out.append('unity')
        if treasury < q: out.append('debt_wealth')
        if treasury < self.t_debt_abs: out.append('debt_abs')
        return out

    def window_texts(self, nation, leader, year, pop_start, cities_start, money_start, pop_now, cities_now, money_now, conqueror_name, conquered_by, unity):
        """The eleven label captions of THumanFalls_InitializeForm as the code builds them (literals from the extract), from the nation fields it reads."""
        L = self.lit
        t = {'lbl_result1': L['r1_a'] + leader + L['r1_b'] + nation + L['r1_c']}
        if cities_now < self.cities_win:
            if year == self.year_end: t['lbl_result2'] = L['year_end_text']
            elif conquered_by < 0: t['lbl_result2'] = L['unity_text'] if unity < self.unity_min else L['debt_text']
            else: t['lbl_result2'] = L['conq_a'] + conqueror_name + L['conq_b']
        else: t['lbl_result2'] = L['victory_text']
        mid = ('%d' % (self.years_base - year) + L['chg_years']) if year < self.short_year else L['chg_short']
        t['lbl_changes'] = L['chg_a'] + mid + L['chg_b'] + nation + L['chg_c']
        t['lbl_nat1'] = nation + L['nat1_b']
        t['lbl_pop1'] = L['pop_w'] + self.f18(pop_start)
        t['lbl_cities1'] = L['cities_w'] + '%d' % cities_start
        t['lbl_money1'] = L['money_w'] + self.f18(money_start) + L['talents']
        t['lbl_nat2'] = nation + L['nat2_in'] + '%d' % year + L['nat2_bc']
        t['lbl_pop2'] = L['pop_w2'] + self.e74(pop_now)
        t['lbl_cities2'] = L['cities_w2'] + '%d' % cities_now
        t['lbl_money2'] = L['money_w2'] + self.f18(money_now) + L['talents2']
        return t

CODE = None
def use(path=None):
    """Select the code extract every function below reads (default: the newest tracked one)."""
    global CODE
    CODE = Code(path or EXTRACT); return CODE
def e74(v): return CODE.e74(v)
def f18(v): return CODE.f18(v)
def window_texts(*a, **k): return CODE.window_texts(*a, **k)
use()

def norm(s):
    return ' '.join(s.split())

# ---- the save fields the window reads (offsets in the nation record; docs/sav-layout-notes.md, confirmed by the memory reads of the experiment) ----
NATION_FIELDS = {'wealth': (0x430, 'i'), 'wealth_start': (0x434, 'i'), 'treasury': (0x438, 'i'), 'treasury_start': (0x43C, 'i'), 'unity': (0x440, 'h'),
                 'cities': (0x446, 'h'), 'cities_start': (0x448, 'h'), 'conquered_by': (0x44E, 'h'), 'human': (0x490, 'B')}

def nation0(b):
    """Offset of nation record 0 in a save (the army table, then the fleet table, then the 16 nation records: state/sav.py)."""
    from state import sav as SAV
    na = SAV.i16(b, SAV.ARMY_OFF); off_f = SAV.ARMY_OFF + 2 + na * SAV.ARMY_LEN; nf = SAV.i16(b, off_f)
    return off_f + 2 + nf * SAV.FLEET_LEN

def nation_fields(save_bytes, n):
    """The window's inputs for nation n read raw from a save, plus names, the calendar and the human flags."""
    from state import sav as SAV
    t = SAV.parse(bytes(save_bytes)); n0 = nation0(save_bytes)
    cs = lambda m, o, ln: save_bytes[n0 + m * SAV.NATION_LEN + o:n0 + m * SAV.NATION_LEN + o + ln].split(b'\0')[0].decode('latin1')
    d = {k: struct.unpack_from('<' + f, save_bytes, n0 + n * SAV.NATION_LEN + o)[0] for k, (o, f) in NATION_FIELDS.items()}
    d['name'] = cs(n, 0, 11); d['leader'] = cs(n, 0x0B, 27)
    d['year'] = t['year_bc']; d['week'] = t['week']; d['season'] = t['season']; d['current_nation'] = t['current_nation']
    d['humans'] = [m for m in range(16) if save_bytes[n0 + m * SAV.NATION_LEN + 0x490]]
    d['names'] = [cs(m, 0, 11) for m in range(16)]
    return d
