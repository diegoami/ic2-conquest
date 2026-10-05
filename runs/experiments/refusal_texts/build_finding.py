#!/usr/bin/env python3
"""Compose findings/2026-10-05-refusal-texts-and-conditions.md from finding_template.md (prose) and the tables rendered from the tracked data
(build_tables.py). The audit (claims_audit.py) re-reads the written finding; nothing in it is trusted."""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tables import *
import build_tables as BT

def counts(data=DATA):
    S = read_sites(data); X = read_extract(data)
    cat = BT.render(data)
    lit_sites = sum(1 for s in S.values() if s['kind'] == 'literal')
    kinds = {}
    for r in CS.ROWS: kinds[r['kind']] = kinds.get(r['kind'], 0) + 1
    cats = {}
    for l in open(latest(os.path.join(data, 'literals_in_scope.tsv')), encoding='utf-8').read().splitlines()[1:]:
        f = l.split('\t'); cats[f[3]] = cats.get(f[3], 0) + 1
    lits_cat = sum(1 for r in CS.ROWS if not r['tmpl'])
    rows = [['message-box call sites', len(S)], ['refusals catalogued', kinds['refusal']], ['prompts catalogued', kinds['prompt']], ['notices catalogued', kinds['notice']],
            ['excluded (battle screen)', kinds['excluded']], ['call sites with a literal text', lit_sites], ['call sites with a built text', len(S) - lit_sites],
            ['literals found at call sites', lit_sites], ['literals catalogued', lits_cat],
            ['message-box literals in the scan of the T*_* functions', cats['message-box literal']], ['fragments of built messages (not boxes of their own)', cats['fragment of a built message']],
            ['other strings (captions, panel labels, names)', cats['other']]]
    return BT.md_table('counts', ['count', 'value'], rows)

def classes(data=DATA):
    rows = []
    for l in open(latest(os.path.join(data, 'class_sites.tsv')), encoding='utf-8').read().splitlines()[1:]:
        rows.append(l.split('\t'))
    return BT.md_table('classes', ['class', 'methods named in delphi_symbols.tsv', 'message-box calls'], rows)

def clone(data=DATA):
    S = read_sites(data); X = read_extract(data); byid = {r['id']: r for r in CS.ROWS}
    rows = []
    for (cl, rid, issue) in BT.CLONE:
        rows.append([issue, cl, rid, row_literal_cell(byid[rid], S, X)])
    return BT.md_table('clone', ['issue row', "the clone's line", 'row', "the original's line"], rows)

def main():
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finding_template.md'), encoding='utf-8').read()
    cat, pr, no = BT.render(); ordt, plt = BT.render_more()
    tabs = {'counts': counts(), 'classes': classes(), 'catalogue': cat, 'prompts': pr, 'notices': no, 'orderings': ordt, 'plays': plt, 'clone': clone()}
    out = re.sub(r'\{\{TABLE:(\w+)\}\}', lambda m: tabs[m.group(1)], tpl)
    p = os.path.join(ROOT, 'findings', '2026-10-05-refusal-texts-and-conditions.md')
    open(p, 'w', encoding='utf-8').write(out); print(p, len(out))
if __name__ == '__main__': main()
