"""Claims audit v2 (rework of PR #46 R1/R2): every captured panel is compared ROW BY ROW, exactly, with the code model (panel_model.py), see rowcompare.py for the
only automatic tolerances (spacing, ordinal glyph, explicit clipping of list rows). No whole-line similarity. Unexpected, missing and extra rows fail.
A row that differs for another reason must be listed in the tracked `visual_corrections.tsv` (png, row, expected, seen, reason; each checked by eye), else MISMATCH.
A capture that does not show its staged subject (mis-click, stale panel) must be listed in `capture_exclusions.tsv`; nothing is excluded silently.

    python3 audit.py [--write]     without --write nothing is written; with it, versioned outputs under DATA (claims_audit2_*)
Exit 1 on any MISMATCH / MISSING / EXTRA or unlisted wrong subject."""
import sys, os, csv, json, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, ART, write_new
import panel_model as M
import rowcompare as RC
from state import sav

def find_save(name):
    for d in (ART + 'saves/', '/home/diego/ic2-work/fixtures/'):
        if os.path.exists(d + name): return d + name
    raise FileNotFoundError(name)
def tsv(path):
    return list(csv.DictReader(open(path, encoding='utf-8'), delimiter='\t')) if os.path.exists(path) else []
LINES = []
def rows_of(pairs, glue=' '):
    """Non-blank rows; the panel line number of each is kept in LINES (blank lines still occupy a line)."""
    LINES[:] = [i for i, (c, v) in enumerate(pairs) if RC.norm(c + v)]
    return [RC.norm(c + glue + v) for c, v in pairs if RC.norm(c + v)]
def merc_rows(raw, cx, cy):
    return [RC.norm(n + ' ' + r) for n, r in M.merc_list(raw, cx, cy)]

def expected_for(raw, kind, tg, cur):
    """-> (expected rows, clip mode) or None when the kind is not modelled."""
    p = raw.p
    if kind == 'nation': return rows_of(M.nation_panel(p, tg, cur)), None
    if kind in ('city_own', 'city_foreign', 'city'): return rows_of(M.city_panel(p, tg, cur)), None
    if kind in ('army_left', 'army_foreign_left', 'army_foreign_right'): return rows_of(M.army_lines(raw, tg, cur)), None
    if kind == 'fleet_left': return rows_of(M.fleet_full(raw, tg, cur)), None
    if kind in ('army_right', 'army_right_scrolled'):
        L = M.army_units_list(raw, tg, cur)
        return (rows_of(L), 'right' if kind == 'army_right' else 'any') if L else (rows_of(M.army_lines(raw, tg, cur)), None)
    if kind == 'fleet_right':
        L, army = M.fleet_lines(raw, tg, cur)
        if army >= 0 and L[0][1] == M.NAMES[cur]: return rows_of(M.army_units_list(raw, army, cur)), 'right'
        return rows_of(M.fleet_full(raw, tg, cur)), None
    if kind in ('merc_list', 'merc_list_scrolled'):
        c = p['cities'][tg]; m = merc_rows(raw, c['x'], c['y'])
        return [('Mercenaries at ' if m else 'There are no mercenaries at ') + c['name']] + m, 'right' if kind == 'merc_list' else 'any'
    return None

def seen_after(got, caption):
    for l in got:
        if l == caption or l.startswith(caption + ' '): return l[len(caption):].strip()
    return None

def main(write=False):
    rows = []
    for f in sorted(glob.glob(DATA + 'captures*.tsv')): rows += tsv(f)
    excl = {r['png']: r['reason'] for f in sorted(glob.glob(DATA + 'capture_exclusions*.tsv')) for r in tsv(f)}
    corr = {}
    for r in [x for f in sorted(glob.glob(DATA + 'visual_corrections*.tsv')) for x in tsv(f)]: corr.setdefault(r['png'], []).append((r['expected'], r['seen']))
    raws, band, out = {}, [], []
    cnt = {}
    def bump(k): cnt[k] = cnt.get(k, 0) + 1
    for r in rows:
        raw = raws.get(r['save']) or raws.setdefault(r['save'], M.Raw(find_save(r['save'])))
        cur = raw.p['current_nation']; kind, tg = r['kind'], int(r['target'])
        if r['png'] in excl: bump('EXCLUDED-listed'); out.append((r['png'], kind, tg, 'EXCLUDED-listed', '', excl[r['png']], '')); continue
        ex = expected_for(raw, kind, tg, cur)
        if ex is None: bump('NOT-MODELLED'); out.append((r['png'], kind, tg, 'NOT-MODELLED', '', '', '')); continue
        exp, clip = ex
        got = [x for x in r['ocr'].split(' | ')]
        res = RC.compare(exp, got, clip, corr.get(r['png'], ()))
        gotn = RC.drop_header(got)
        lines_ = list(LINES)
        for i, (st, e, g) in enumerate(res):
            bump(st); ln = lines_[exp.index(e)] if (e in exp and exp.index(e) < len(lines_)) else ''
            out.append((r['png'], kind, tg, st, e, g, ln))
        # band samples (only from rows that compared exactly)
        okset = ('OK', 'OK-ordinal', 'CORRECTED')
        status_by_exp = {e: st for st, e, g in res}
        def samp(fld, v, word, caption):
            line = next((e for e in exp if e == caption or e.startswith(caption + ' ')), None)
            if line is None or status_by_exp.get(line) not in okset: return
            band.append((fld, v, word, seen_after(gotn, caption) or '', r['png'], r['save']))
        if kind in ('city_own', 'city_foreign', 'city'):
            c = raw.p['cities'][tg]
            samp('loyalty', c['loyalty'], M.loyalty_word(c['loyalty']), 'Loyalty')
            if c['owner'] != cur:
                w = M.tribute_word(c['tribute'])
                samp('tribute_word_foreign', c['tribute'] & 0xffff, w if w is not None else M.f_plain(M.i16(M.cdiv(c['tribute'] * c['pop'], c['max_pop']))), 'Tribute')
        elif kind == 'nation':
            nt = raw.p['nations'][tg]
            samp('unity', nt['unity'], M.unity_word(nt['unity']), 'Unity')
            for name, v in nt['relations'].items():
                if v < 6 and raw.p['nations'][M.NAMES.index(name)]['unity'] != 0: samp('relation', v, M.relation_word(v).strip(), name)
        elif kind == 'army_left':
            h = raw.army_hdr(tg)
            if h[2] == cur: samp('morale', h[7], M.morale_word(h[7]), 'Morale')
        elif kind == 'fleet_left':
            o = raw.s.fleet0 + tg * sav.FLEET_LEN
            sea = M.i16(int.from_bytes(raw.b[o + 24:o + 26], 'little')); samp('sea', sea, 'calm' if sea == 0 else 'rough', 'Sea')
        elif kind in ('army_right_scrolled', 'merc_list_scrolled'):
            # quality words: the scrolled list rows must be complete (status OK or the left clip that keeps the word) -- use space-free suffix match
            if kind == 'army_right_scrolled':
                rr = [(t, tr, q) for lab, t, tr, q, nm in raw.slots(tg)]; rr = rr[:next((k for k, x in enumerate(rr) if x[1] <= 0), len(rr))]
            else:
                c = raw.p['cities'][tg]; rr = [(typ, tr_, q_) for (x_, y_, lab_, typ, tr_, q_) in raw.merc_rows() if tr_ >= 0 and x_ == c['x'] and y_ == c['y']]
            for t, tr, q in rr:
                pre = RC.nospace(M.unit_name(t) + ' ' + M.f_commas(tr))
                for g in gotn:
                    gn = RC.nospace(g)
                    if pre in gn:
                        seen = gn[gn.index(pre) + len(pre):]; band.append(('quality', q, RC.nospace(M.quality_word(q)), seen, r['png'], r['save'])); break
    brows, bmism = [], 0
    for fld, v, e, s, png, save in band:
        st = 'OK' if s.strip() == e.strip() else 'MISMATCH'
        bmism += st != 'OK'; brows.append((fld, v, e.strip(), s.strip(), st, png, save))
    bad = sum(cnt.get(k, 0) for k in ('MISMATCH', 'MISSING', 'EXTRA'))
    summ = 'captures %d; row statuses: %s; MISMATCH+MISSING+EXTRA %d\nband samples %d; band MISMATCH %d\n' % (
        len(rows), ', '.join('%s %d' % kv for kv in sorted(cnt.items())), bad, len(brows), bmism)
    print(summ)
    if write:
        hdr = 'png\tkind\ttarget\tstatus\texpected\tseen\tpanel_line\n'
        p1 = write_new(DATA + 'claims_audit2_rows.tsv', hdr + ''.join('\t'.join(map(str, o)) + '\n' for o in out))
        p2 = write_new(DATA + 'band_samples2.tsv', 'field\tvalue\texpected_word\tseen_word\tstatus\tpng\tsave\n' + ''.join('\t'.join(map(str, o)) + '\n' for o in brows))
        p3 = write_new(DATA + 'claims_audit2_summary.txt', summ); print(p1, p2, p3)
    for o in out:
        if o[3] in ('MISMATCH', 'MISSING', 'EXTRA'): print(o)
    for b in brows:
        if b[4] != 'OK': print(b)
    return 1 if (bad or bmism) else 0

if __name__ == '__main__': sys.exit(main('--write' in sys.argv))
