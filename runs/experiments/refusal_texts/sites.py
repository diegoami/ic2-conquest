#!/usr/bin/env python3
"""Find every message box call (FUN_0042d750 = MessageDlg(Msg, DlgType, Buttons, HelpCtx), through FUN_0042d770 -> FUN_0042d2f4 CreateMessageDialog) in the
decompile and write one row per call site: enclosing function, call line, the first argument (a string literal, byte for byte as the decompile prints it, or the
expression), the dialog type (last argument of CONCAT31: 0 Warning, 1 Error, 2 Information, 3 Confirmation), the button-set word read from the executable at
the address the call names, and the lines of the enclosing blocks (the `if`/`else` headers, for the condition). Output: a new versioned
runs/experiments/data/run-exp-refusal-texts/call_sites.tsv (never overwrites).
usage: sites.py [--exe PATH]"""
import re, os, sys, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import write_new, DATA
DUMP = os.environ.get('IC2_DUMP', '/mnt/c/Users/diego/AppData/Local/ReTools/all_app_functions.txt')
EXE = os.environ.get('IC2_ORIG_EXE', os.path.expanduser('~/ic2-work/build/Imperial Conquest 2.exe'))
WRAP = 'FUN_0042d750'
DLG = {0: 'mtWarning', 1: 'mtError', 2: 'mtInformation', 3: 'mtConfirmation', 4: 'mtCustom'}
BTN = ['mbYes', 'mbNo', 'mbOK', 'mbCancel', 'mbAbort', 'mbRetry', 'mbIgnore', 'mbAll', 'mbNoToAll', 'mbYesToAll', 'mbHelp']

class Exe:
    def __init__(self, path):
        self.d = open(path, 'rb').read(); d = self.d
        pe = struct.unpack_from('<I', d, 0x3c)[0]; n = struct.unpack_from('<H', d, pe + 6)[0]; opt = struct.unpack_from('<H', d, pe + 20)[0]
        self.base = struct.unpack_from('<I', d, pe + 24 + 28)[0]; self.secs = []
        for i in range(n):
            o = pe + 24 + opt + 40 * i; vs, va, rs, ro = struct.unpack_from('<IIII', d, o + 8); self.secs.append((va, vs, ro, rs))
        self.sha = hashlib.sha256(d).hexdigest()
    def rd(self, a, n):
        for va, vs, ro, rs in self.secs:
            if va <= a - self.base < va + max(vs, rs): o = ro + a - self.base - va; return self.d[o:o + n]
        return None

def unescape(s):
    """C string escapes of the decompile -> the bytes of the literal"""
    return re.sub(r'\\(x[0-9a-fA-F]{2}|.)', lambda m: {'n': '\n', 't': '\t', "'": "'", '"': '"', '\\': '\\'}.get(m.group(1)) or chr(int(m.group(1)[1:], 16)), s)

def load(dump=DUMP):
    return open(dump, errors='replace').read().split('\n')

def functions(L):
    cur = None; out = {}
    for i, l in enumerate(L):
        m = re.match(r'// ==== (\S+) @ ([0-9a-f]+) ====', l)
        if m: cur = m.group(1); out[cur] = [i, m.group(2)]
        if cur: out[cur].append(i)
    return out

def indent(l): return len(l) - len(l.lstrip(' '))

def headers(L, i, fstart):
    """Enclosing block headers of line i (0-based): [(lineno, text)] outermost first. A header is the first line of a statement at lower indent that ends in `{`
    (a multi-line condition is joined); an `else` header carries the line of the `if` it negates."""
    out = []; cur = indent(L[i]); j = i - 1
    while j > fstart and cur > 2:
        l = L[j]
        if l.strip() and indent(l) < cur and re.search(r'\{\s*$', l):
            k = j
            while k > fstart and not re.match(r'\s*(\} )?(if|else|while|for|do|switch)\b', L[k]) and not re.match(r'\s*\}?\s*else', L[k]): k -= 1
            txt = ' '.join(x.strip() for x in L[k:j + 1])
            out.append((k + 1, txt, indent(l)))
            cur = indent(l)
        j -= 1
    return out[::-1]

def sites(L):
    fn = functions(L); res = []
    for name, v in fn.items():
        start = v[0]; end = v[-1]
        for i in range(start, end + 1):
            if WRAP + '(' in L[i] and not L[i].startswith('void ') and name != WRAP:
                k = i; txt = L[i].strip()
                while not re.search(r';\s*$', L[k]) and k < end: k += 1; txt += ' ' + L[k].strip()
                res.append((name, i, k, txt))
    return res

def parse_call(txt):
    j = txt.index(WRAP + '(') + len(WRAP) + 1
    # split top level args
    depth = 0; args = []; cur = ''; instr = False; esc = False
    for ch in txt[j:]:
        if instr:
            cur += ch
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': instr = False
            continue
        if ch == '"': instr = True; cur += ch; continue
        if ch in '([': depth += 1
        if ch in ')]':
            if depth == 0: args.append(cur.strip()); break
            depth -= 1
        if ch == ',' and depth == 0: args.append(cur.strip()); cur = ''; continue
        cur += ch
    return args

def main():
    exe = Exe(sys.argv[sys.argv.index('--exe') + 1] if '--exe' in sys.argv else EXE)
    L = load(); rows = []
    rows.append('# message box call sites of %s (sha256 of the dump %s), buttons read from %s (sha256 %s)' % (os.path.basename(DUMP), hashlib.sha256('\n'.join(L).encode('utf-8', 'replace')).hexdigest()[:16], os.path.basename(EXE), exe.sha))
    rows.append('seq\tfunction\tcall_line\tfirst_arg_kind\tliteral\tdlg_type\tbutton_arg\tbutton_word\tbuttons\tenclosing_headers')
    for n, (name, i, k, txt) in enumerate(sites(L), 1):
        a = parse_call(txt)
        m = re.fullmatch(r'\(uint \*\)"((?:[^"\\]|\\.)*)"', a[0])
        kind, lit = ('literal', unescape(m.group(1))) if m else ('expr', a[0])
        c = re.search(r'CONCAT31\(.*,\s*(\d)\)$', a[1], re.S); dt = int(c.group(1)) if c else -1
        b = a[2]; mb = re.fullmatch(r'(?:_UNK|DAT)_([0-9a-f]{8})', b)
        if mb:
            raw = exe.rd(int(mb.group(1), 16), 2); w = struct.unpack('<H', raw)[0]
        else: w = None
        bt = '+'.join(BTN[x] for x in range(11) if w is not None and w >> x & 1) if w is not None else '?'
        fn_start = functions(L)[name][0]
        hs = ' || '.join('%d: %s' % (ln, t) for ln, t, _ in headers(L, i, fn_start))
        rows.append('\t'.join([str(n), name, str(i + 1), kind, lit.replace('\n', '\\n'), '%d %s' % (dt, DLG.get(dt, '?')), b, '0x%04x' % w if w is not None else '?', bt, hs]))
    print(write_new(os.path.join(DATA, 'call_sites.tsv'), '\n'.join(rows) + '\n'))
if __name__ == '__main__': main()
