"""Coverage check: every string literal, every called helper and every data symbol of the seven TInformation_Show* functions (ReTools/all_app_functions.txt)
must be covered by a row of findings_rows.py (a table row of the findings draft) or excluded here with a reason. Prints and (with --write) writes a versioned report.
    python3 coverage_check.py [--write] [--selftest]     exit 1 when anything is unaccounted"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, write_new
import findings_rows as FR
DUMP = '/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt'
FUNCS = ['TInformation_ShowNationStatus', 'TInformation_ShowCityDetails', 'TInformation_ShowArmyDetails', 'TInformation_ShowFleetDetails',
         'TInformation_ShowCityUnits', 'TInformation_ShowArmyUnits', 'TInformation_ShowFleetUnits']
# exclusions: (kind, regex on the item) -> reason
EXCL = [('dat', r'DAT_0049f(00c|049|086|0c3|100|13d|17a|1b7|1f4|231|26e|2ab)', 'the 61-byte display-line buffer: the line index of each row is in the tables (line = (address - 0x0049F00C) / 0x3D)'),
        ('dat', r'DAT_004a031c', 'the panel line count handed to PrintInfo (last line index): in the tables as the "last line" notes'),
        ('dat', r'DAT_004a0320', 'the current nation (the "own" test): in every condition column'),
        ('dat', r'DAT_00474670', 'the nation record table base (name at +0): N01, C01, A01, F01, U2')]
NON_HELPER = {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'do', 'else', 'case'}      # C control-flow keywords that are followed by '(' : not calls
TYPE_WORDS = {'int', 'short', 'char', 'byte', 'uint', 'ushort', 'uchar', 'long', 'ulong', 'float', 'double', 'bool', 'void', 'code', 'longlong', 'ulonglong',
              'undefined', 'undefined1', 'undefined2', 'undefined3', 'undefined4', 'undefined8', 'int3', 'uint3', 'int5', 'dword', 'word', 'DWORD', 'WORD', 'LONG', 'BOOL',
              'HANDLE', 'LPVOID', 'ULONG', 'LPCSTR', 'LPSTR', 'const', 'unsigned', 'signed', 'struct'}
def _is_cast(inner):
    toks = re.findall(r'[A-Za-z_]\w*|\*|\[\s*\d*\s*\]', inner)
    return bool(toks) and re.fullmatch(r'\s*(?:[A-Za-z_]\w*|\*|\[\s*\d*\s*\])(?:\s*(?:[A-Za-z_]\w*|\*|\[\s*\d*\s*\]))*\s*', inner) is not None and \
        all(t in TYPE_WORDS or t == '*' or t.startswith('[') for t in toks)
def calls_of(body, own):
    """Every call expression of a function body, found structurally whatever the arguments (empty, numeric, parenthesized, ...):
      identifier  <blanks>  '('                      -> the identifier (a named call, any naming scheme),
      ')' <blanks> '('  and  ']' <blanks> '('        -> an indirect call, '<indirect call>', unless the group before it is a C cast `(type *)` or follows a keyword
                                                       such as `if`/`while` (those are explicit non-helper constructs),
    after string literals and comments are removed. The function's own signature name is not a call."""
    b = re.sub(r'"(?:[^"\\]|\\.)*"', '""', body)
    b = re.sub(r'/\*.*?\*/', ' ', b, flags=re.S)
    b = re.sub(r'//[^\n]*', ' ', b)
    names = {m.group(1) for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\(', b)} - NON_HELPER - {own}
    stack = []
    for k, ch in enumerate(b):
        if ch == '(': stack.append(k)
        elif ch == ')' and stack:
            j = stack.pop()
            m = re.match(r'\s*\(', b[k + 1:])
            if not m: continue
            inner = b[j + 1:k]
            before = re.search(r'([A-Za-z_]\w*)\s*$', b[:j])
            if before and before.group(1) in NON_HELPER: continue
            if before and before.group(1) not in NON_HELPER and False: continue
            if _is_cast(inner): continue
            names.add('<indirect call>')
        elif ch == ']':
            if re.match(r'\s*\(', b[k + 1:]): names.add('<indirect call>')
    return names
def load():
    t = open(DUMP, encoding='latin-1').read()
    out = {}
    for n in FUNCS:
        m = re.search(r'// ==== %s @ ([0-9a-f]+) ====\n(.*?)(?=\n// ==== |\Z)' % n, t, re.S)
        b = m.group(2)
        out[n] = {'addr': m.group(1),
                  'lit': set(re.findall(r'"((?:[^"\\]|\\.)*)"', b)),
                  'call': calls_of(b, n),
                  'dat': set(re.findall(r'DAT_[0-9a-f]{8}', b))}
    return out
def check(rows=None):
    rows = FR.ROWS if rows is None else rows
    D = load(); res = []; bad = 0
    for n in FUNCS:
        cov = {}
        for r in rows:
            if r['fn'] != n: continue
            for k, v in r['covers']: cov.setdefault((k, v), []).append(r['id'])
        for c in FR.SHARED.get(n, []): cov.setdefault(('call', c), []).append('H1')
        for kind in ('lit', 'call', 'dat'):
            for item in sorted(D[n][kind]):
                if (kind, item) in cov: res.append((n, kind, item, 'row', ','.join(sorted(set(cov[(kind, item)])))))
                else:
                    ex = [why for k, rx, why in EXCL if k == kind and re.fullmatch(rx, item)]
                    if ex: res.append((n, kind, item, 'excluded', ex[0]))
                    else: res.append((n, kind, item, 'UNACCOUNTED', '')); bad += 1
    return res, bad, D
def main():
    res, bad, D = check()
    ids = {r['id'] for r in FR.ROWS}
    for _, _, _, st, why in res:
        if st == 'row': assert all(i in ids or i == 'H1' for i in why.split(',')), why
    n_row = sum(1 for r in res if r[3] == 'row'); n_ex = sum(1 for r in res if r[3] == 'excluded')
    summ = 'functions %d; items %d (literals %d, helpers %d, data symbols %d); mapped to a row %d; excluded with a reason %d; UNACCOUNTED %d\n' % (
        len(FUNCS), len(res), sum(len(D[n]['lit']) for n in FUNCS), sum(len(D[n]['call']) for n in FUNCS), sum(len(D[n]['dat']) for n in FUNCS), n_row, n_ex, bad)
    print(summ)
    for r in res:
        if r[3] == 'UNACCOUNTED': print(r)
    if '--selftest' in sys.argv:
        # self-test: drop row N06 and C05: the check must then report the unity/loyalty items as unaccounted
        res2, bad2, _ = check([r for r in FR.ROWS if r['id'] not in ('N06', 'C05')])
        print('selftest: without N06 and C05 the check reports %d unaccounted (must be > 0): %s' % (bad2, 'PASS' if bad2 > 0 else 'FAIL'))
        summ += 'selftest (rows N06, C05 removed): %d unaccounted -> %s\n' % (bad2, 'PASS' if bad2 > 0 else 'FAIL')
        if bad2 == 0: return 1
    if '--write' in sys.argv:
        body = 'function\tkind\titem\tstatus\trow_or_reason\n' + ''.join('\t'.join(map(str, r)) + '\n' for r in res)
        print(write_new(DATA + 'coverage_report.tsv', body)); print(write_new(DATA + 'coverage_summary.txt', summ))
    return 1 if bad else 0
if __name__ == '__main__': sys.exit(main())
