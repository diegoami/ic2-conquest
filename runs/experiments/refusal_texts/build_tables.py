"""Render the finding's tables (markdown, each preceded by <!-- table: NAME -->) from the tracked data. usage: build_tables.py > tables.md"""
import os, re, sys, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tables import *
import savefacts as SF
import play_meta
ART = os.environ.get('IC2_ARTIFACTS', os.path.join(ROOT, 'artifacts', 'run-exp-refusal-texts')).rstrip('/') + '/'

def md_table(name, header, rows):
    out = ['<!-- table: %s -->' % name, '| ' + ' | '.join(header) + ' |', '|' + '|'.join('---' for _ in header) + '|']
    for r in rows: out.append('| ' + ' | '.join(esc_cell(str(c)) for c in r) + ' |')
    return '\n'.join(out) + '\n'

def play_ev(P, ids):
    cells = []
    for pid in ids:
        if pid not in P: cells.append('%s (not played)' % pid); continue
        r = P[pid][-1]
        bx = r['boxes'][-1]
        cells.append('%s: box "%s", ctl %s, after %s, %s' % (pid, bx['title'], r['control'], r['after'], r['png_summary'] if 'png_summary' in r else ''))
    return '; '.join(cells)

def render(data=DATA):
    S = read_sites(data); X = read_extract(data); P = read_plays(data)
    out = []
    refusals = [r for r in CS.ROWS if r['kind'] == 'refusal']
    OC = order_cells(S, X)
    rows = []
    for r in refusals:
        s = S[r['line']]
        pcell = ''
        if r['plays']:
            pl = []
            for pid in r['plays']:
                if pid in P:
                    q = P[pid][-1]; b = q['boxes'][-1]
                    shot = b['png']
                    pl.append('%s `%s` `%s` `%s`' % (pid, shot, q['control'], q['after']))
                else: pl.append('%s (not played)' % pid)
            pcell = '[confirmed] ' + '; '.join(pl)
        else: pcell = '-'
        rows.append([r['id'], OC[r['id']], row_literal_cell(r, S, X), '%s:%d' % (s['function'], s['line']), '%s [%s]' % (s['dlg'].split(' ')[1], s['buttons'].replace('+', '+')), r['cond'], r['effect'], pcell])
    cat = md_table('catalogue', ['id', 'test order', 'literal', 'function:call line', 'box [buttons]', 'condition [derived]', 'effect [derived]', 'play [confirmed]'], rows)
    rows = []
    for r in [r for r in CS.ROWS if r['kind'] == 'prompt']:
        s = S[r['line']]
        pc = '-'
        if r['plays']:
            pc = '[confirmed] ' + '; '.join(r['plays'])
        rows.append([r['id'], row_literal_cell(r, S, X), '%s:%d' % (s['function'], s['line']), '%s [%s]' % (s['dlg'].split(' ')[1], s['buttons']), r['cond'], r['effect'], pc])
    pr = md_table('prompts', ['id', 'literal', 'function:call line', 'box [buttons]', 'raised when [derived]', 'answers [derived]', 'play [confirmed]'], rows)
    rows = []
    for r in [r for r in CS.ROWS if r['kind'] in ('notice', 'excluded')]:
        s = S[r['line']]
        rows.append([r['id'], r['kind'], row_literal_cell(r, S, X), '%s:%d' % (s['function'], s['line']), '%s [%s]' % (s['dlg'].split(' ')[1], s['buttons']), r['cond'], r['effect']])
    no = md_table('notices', ['id', 'kind', 'literal', 'function:call line', 'box [buttons]', 'raised when', 'note'], rows)
    return cat, pr, no

def ids_of_function(S):
    by = {}
    for r in CS.ROWS:
        by.setdefault(S[r['line']]['function'], []).append(r)
    return by

CLONE = [  # (the clone's line as issue #721 gives it, row id of the original's line, issue row)
 ("Army '<id>' has fewer than 2 units and cannot be split.", 'R01', 'UA04'),
 ('There are more than 20 units in these armies combined.', 'R03', 'UA05'),
 ("... troops ... (the issue abbreviates the clone's second join line with an ellipsis: JoinArmiesCommandHandler.cs:70)", 'R04', 'UA05'),
 ('Neither fleet may carry an army to join.', 'R16', 'UF05'),
 ("the clone's own wording (T107 split-unit handler)", 'R41', 'D05/D06 (inventory D06: Split unit)'),
 ("the clone's own wording (T107 rename-unit handler)", 'R36', 'D05/D06 (inventory D05: Rename unit)'),
 ("the clone's own wording (T107 rename-unit handler)", 'R37', 'D05/D06 (inventory D05: Rename unit)'),
]
# NB: the clone's third join line, '... troops ...', is given in the issue only as an ellipsis; the issue's wording is kept in the finding text, not audited here.

def compact_ops(ops):
    out = []
    for op in ops:
        k = op[0]
        if k == 'units':
            us = op[2]; groups = []
            for u in us:
                key = (u[0], u[1], u[3] if len(u) > 3 else 0)
                if groups and groups[-1][0] == key: groups[-1][1] += 1
                else: groups.append([key, 1])
            out.append('army %d units = %s' % (op[1], ' + '.join('%d x %s %s%s' % (n, key[0], format(key[1], ','), ' (mercenary label %d)' % key[2] if key[2] else '') for key, n in groups)))
        elif k == 'fleet': out.append('fleet %d %s = %d' % (op[1], op[2], op[3]))
        elif k == 'nation': out.append('nation %d +0x%x = %d' % (op[1], op[2], op[3]))
        elif k == 'city': out.append('city %d %s' % (op[1], ', '.join('%s = %d' % kv for kv in op[2].items())))
        elif k == 'relation': out.append('relation %d-%d = %d' % (op[1], op[2], op[3]))
        else: out.append('army %d %s = %d' % (op[1], op[0], op[2]))
    return '; '.join(out)

def render_more(data=DATA, art=ART):
    S = read_sites(data); X = read_extract(data); P = read_plays(data); RE = read_reread(data)
    byfn = {}
    for r in CS.ROWS:
        if r['kind'] == 'refusal': byfn.setdefault(S[r['line']]['function'], []).append(r)
    rows = []
    for fn, rs in byfn.items():
        if len(rs) < 2 or any(r['order'].startswith('alternative') for r in rs): continue
        ranks = CON.rank_in_function(X, [r['line'] for r in rs])
        rows.append([fn, ' > '.join(r['id'] for r in sorted(rs, key=lambda r: ranks[r['line']]))])
    comb = {'TUnitMap_JoinArmies': ('UA05c', 'R03'), 'TUnitMap_JoinFleets': ('UF05c', 'R15')}
    rows2 = []
    for fn, ids in rows:
        pc, shown = comb.get(fn, ('-', '-'))
        rows2.append([fn, ids, pc, shown])
    ordt = md_table('orderings', ['function', 'refusals in the order the code tests them', 'combined case played', 'row whose line appeared'], rows2)
    # plays
    prow = []
    rowsof = {}
    for r in CS.ROWS:
        for pid in r['plays']: rowsof.setdefault(pid, []).append(r['id'])
    for pid in sorted(P, key=lambda x: (re.sub(r'\d+.*', '', x), x)):
        q = P[pid][-1]
        ctl = art + 'saves/' + q['control']; aft = art + 'saves/' + q['after']
        facts = '; '.join(SF.fact(ctl, sp) for sp in play_meta.W.get(pid, [])) if os.path.exists(ctl) else '(save not fetched)'
        d = SF.diff_text(ctl, aft) if os.path.exists(ctl) and os.path.exists(aft) else '?'
        facts2 = '; '.join(SF.fact(aft, sp) for sp in play_meta.W.get(pid, [])) if os.path.exists(aft) else '(save not fetched)'
        bxs = ' / '.join('%s: %s' % (b['title'], shown_text(b, RE)) for b in q['boxes'])
        staged = ('STAGED: %s' % compact_ops(q['ops'])) if q['staged'] else 'fixture, unedited'
        prow.append([pid, ','.join(rowsof.get(pid, [])), q['src'], staged.replace('|', '/'), q['note'].replace('|', '/'), facts, bxs, facts2, d, ' '.join('`%s`' % x for x in ([q['boxes'][-1]['png']] if q['boxes'] else []) + [q['control'], q['after']])])
    plt = md_table('plays', ['play', 'rows', 'source save', 'edit', 'order issued', 'state in the control save [recomputed]', 'box title: OCR of the message', 'state in the after save [recomputed]', 'after vs control [recomputed]', 'files'], prow)
    return ordt, plt

if __name__ == '__main__':
    for t in list(render()) + list(render_more()): print(t)
