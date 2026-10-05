"""Shared readers of the tracked data (call sites, code extract, plays) and the table renderers of the finding. Used by build_finding.py and by claims_audit.py (which
re-reads the sources itself and compares them with what the finding says)."""
import os, re, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import latest, versions
from paths import DATA, ROOT
import catalogue_spec as CS

def read_sites(data=DATA):
    rows = {}
    p = latest(os.path.join(data, 'call_sites.tsv'))
    for l in open(p, encoding='utf-8'):
        if l.startswith('#') or l.startswith('seq\t'): continue
        f = l.rstrip('\n').split('\t')
        rows[int(f[2])] = dict(seq=int(f[0]), function=f[1], line=int(f[2]), kind=f[3], literal=f[4].replace('\\n', '\n'), dlg=f[5], button_arg=f[6], word=f[7], buttons=f[8], headers=f[9] if len(f) > 9 else '')
    return rows

def read_extract(data=DATA):
    X = {}
    for l in open(latest(os.path.join(data, 'code_extract_refusals.txt')), encoding='utf-8', errors='replace'):
        m = re.match(r'(\d+)\t(.*)', l.rstrip('\n'))
        if m: X[int(m.group(1))] = m.group(2)
    return X

def norm(s): return re.sub(r'\s+', ' ', s).strip()

def lit_on_line(X, line):
    """the first string literal on an extract line, unescaped"""
    m = re.search(r'"((?:[^"\\]|\\.)*)"', X[line])
    return unesc(m.group(1))

def unesc(s):
    return re.sub(r'\\(x[0-9a-fA-F]{2}|.)', lambda m: {'n': '\n', 't': '\t', "'": "'", '"': '"', '\\': '\\'}.get(m.group(1)) or chr(int(m.group(1)[1:], 16)), s)

def row_literal_cell(r, S, X):
    """The literal of a catalogue row as the finding prints it: code spans joined by ' + '; built messages show their variable parts as <...>"""
    if r['tmpl']:
        parts = []
        for k, v in r['tmpl']:
            parts.append('`<%s>`' % v if k == 'var' else '`%s`' % lit_on_line(X, v))
        return ' + '.join(parts)
    return '`%s`' % S[r['line']]['literal']

def esc_cell(s): return s.replace('|', '\\|')
def unesc_cell(s): return s.replace('\\|', '|')

def read_plays(data=DATA):
    out = {}
    for f in sorted(glob.glob(os.path.join(data, 'plays_*.jsonl'))):
        for l in open(f, encoding='utf-8'):
            r = json.loads(l); out.setdefault(r['play'], []).append(r)
    return out

def last_play(P, pid): return P[pid][-1]
