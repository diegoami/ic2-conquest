"""Claims audit: recompute every captured panel line from the code model (panel_model.py: the decompile + the DAT tables) and compare it with the
OCR of the screenshot recorded in captures*.tsv; then build the band-sample table (expected vs seen word per staged value) from the captures.

    python3 audit.py [--write]     without --write nothing is written (development runs); with it, versioned outputs under DATA

Reads DATA/captures*.tsv and the staged saves in artifacts/run-exp-info-window/saves/ (or the fixtures). Exit 1 on any mismatch.
Lines whose staged value makes the game read memory outside the word tables (relation >= 6, nation population >= 10**9, unity index >= 11)
are not modelled: they are listed as BEYOND-TABLE with the OCR text, never as OK."""
import sys, os, csv, json, re, difflib, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, ART, write_new
import panel_model as M
from state import sav

def norm(t): return re.sub(r'\s+', ' ', t).strip()
def lines_of(ocr): return [norm(x) for x in ocr.split(' | ') if norm(x)]
def expect(L): return [norm(c + ' ' + v) for c, v in L if norm(c + v)]
def find_save(name):
    for d in (ART + 'saves/', '/home/diego/ic2-work/fixtures/'):
        if os.path.exists(d + name): return d + name
    raise FileNotFoundError(name)

def beyond(kind, line, raw, tg):
    """Is this expected line one whose game text comes from memory outside the loaded word tables?"""
    if kind == 'nation':
        nt = raw.p['nations'][tg]
        if line.startswith('Population ') and abs(nt['wealth']) >= 10 ** 9: return True
        for name in M.NAMES:
            if line == name and nt['relations'].get(name, 0) >= 6: return True
        if line.startswith('Unity') and M.cdiv(nt['unity'], 100) >= 11: return True
    return False

def seen(ocr, caption):
    for l in lines_of(ocr):
        if l == caption or l.startswith(caption + ' '): return l[len(caption):].strip()
    return None

def main(write=False):
    rows = []
    for f in sorted(glob.glob(DATA + 'captures*.tsv')):
        rows += list(csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'))
    excl_file = DATA + 'capture_exclusions.tsv'
    exclusions = {}
    if os.path.exists(excl_file):
        for l in open(excl_file, encoding='utf-8').read().splitlines()[1:]:
            if l.strip(): k, v = l.split('\t', 1); exclusions[k] = v
    out, mism, ok, excl, fuzzy, bey = [], 0, 0, 0, 0, 0
    raws, band = {}, []
    for r in rows:
        raw = raws.get(r['save']) or raws.setdefault(r['save'], M.Raw(find_save(r['save'])))
        cur = raw.p['current_nation']
        got = lines_of(r['ocr'])
        if r['png'] in exclusions:
            excl += 1; out.append((r['png'], r['kind'], int(r['target']), 'EXCLUDED-listed', exclusions[r['png']])); continue
        kind, tg = r['kind'], int(r['target'])
        exp = None
        if kind == 'nation': exp = expect(M.nation_panel(raw.p, tg, cur))
        elif kind in ('city_own', 'city_foreign', 'city'): exp = expect(M.city_panel(raw.p, tg, cur))
        elif kind == 'army_left': exp = expect(M.army_lines(raw, tg, cur))
        elif kind == 'army_right':
            L = M.army_units_list(raw, tg, cur); exp = expect(L) if L else expect(M.army_lines(raw, tg, cur))
        elif kind == 'fleet_left': exp = expect(M.fleet_full(raw, tg, cur))
        elif kind == 'fleet_right':
            L, army = M.fleet_lines(raw, tg, cur)
            exp = expect(M.army_units_list(raw, army, cur)) if (army >= 0 and L[0][1] == M.NAMES[cur]) else expect(M.fleet_full(raw, tg, cur))
        elif kind in ('army_foreign_left', 'army_foreign_right'): exp = expect(M.army_lines(raw, tg, cur))
        elif kind == 'merc_list':
            c = raw.p['cities'][tg]; rows_ = M.merc_list(raw, c['x'], c['y'])
            exp = [('Mercenaries at ' if rows_ else 'There are no mercenaries at ') + c['name']]
        elif kind in ('army_right_scrolled', 'merc_list_scrolled'):
            # the window is scrolled 96 px right: only the tail of each row is visible (type, troops, quality); the OCR keeps a clipped name stub in front
            if kind == 'army_right_scrolled':
                rows_ = [(t, tr, q) for lab, t, tr, q, nm in raw.slots(tg)]
                rows_ = rows_[:next((k for k, x in enumerate(rows_) if x[1] <= 0), len(rows_))]       # ShowArmyUnits stops at the first empty slot
            else:
                c = raw.p['cities'][tg]
                rows_ = [(typ, tr_, q_) for (x_, y_, lab_, typ, tr_, q_) in raw.merc_rows() if tr_ >= 0 and x_ == c['x'] and y_ == c['y']]
            for t, tr, q in rows_:
                pre = norm(M.unit_name(t) + ' ' + M.f_commas(tr))
                tail = norm(pre + ' ' + M.quality_word(q))
                hit = [g for g in got if g.endswith(tail)]
                seen_w = None
                pre_ns = pre.replace(' ', '')
                for g in got:
                    gn = g.replace(' ', '')          # the OCR sometimes drops a space inside a row ('Lightinfantry'): match on the space-free text
                    if pre_ns in gn: seen_w = g_rest = gn[gn.index(pre_ns) + len(pre_ns):]; break
                if hit: ok += 1; out.append((r['png'], kind, tg, 'OK', tail))
                else:
                    best = max(got, key=lambda g: difflib.SequenceMatcher(None, tail, g[-len(tail) - 3:]).ratio()) if got else ''
                    if difflib.SequenceMatcher(None, tail, best[-len(tail) - 3:]).ratio() >= 0.9: fuzzy += 1; out.append((r['png'], kind, tg, 'OK-OCR-fuzzy', '%r ~ %r' % (tail, best)))
                    else: mism += 1; out.append((r['png'], kind, tg, 'MISMATCH', '%r not at the end of any OCR line; lines %r' % (tail, got[:8])))
                band.append(('quality', q, M.quality_word(q).replace(' ', ''), seen_w, r['png'], r['save']))   # compared space-free (OCR)
            continue
        if exp is None:
            out.append((r['png'], kind, tg, 'NOT-MODELLED', '')); continue
        if exp[0] not in got and not any(difflib.SequenceMatcher(None, exp[0], g).ratio() > 0.85 for g in got):
            excl += 1
            out.append((r['png'], kind, tg, 'EXCLUDED-wrong-subject', 'expected first line %r, the panel shows %r (the click landed on another object)' % (exp[0], got[:2])))
            continue
        for e in exp:
            if e in got: ok += 1; out.append((r['png'], kind, tg, 'OK', e)); continue
            if beyond(kind, e, raw, tg):
                bey += 1
                out.append((r['png'], kind, tg, 'BEYOND-TABLE', '%r (memory past the word table); OCR lines %r' % (e, [g for g in got if g.split(' ')[0] == e.split(' ')[0]])))
                continue
            best = max(got, key=lambda g: difflib.SequenceMatcher(None, e, g).ratio()) if got else ''
            ratio = difflib.SequenceMatcher(None, e, best).ratio()
            if ratio >= 0.9: fuzzy += 1; out.append((r['png'], kind, tg, 'OK-OCR-fuzzy', '%r ~ %r' % (e, best)))
            else: mism += 1; out.append((r['png'], kind, tg, 'MISMATCH', '%r not in OCR; closest %r' % (e, best)))
        # ---- band samples: (field, value, expected word, seen word, png, save)
        if kind in ('city_own', 'city_foreign', 'city'):
            c = raw.p['cities'][tg]
            band.append(('loyalty', c['loyalty'], M.loyalty_word(c['loyalty']), seen(r['ocr'], 'Loyalty'), r['png'], r['save']))
            if c['owner'] != cur:
                w = M.tribute_word(c['tribute'])
                exp_w = w if w is not None else M.f_plain(M.i16(M.cdiv(c['tribute'] * c['pop'], c['max_pop'])))
                band.append(('tribute_word_foreign', c['tribute'] & 0xffff, exp_w, seen(r['ocr'], 'Tribute'), r['png'], r['save']))
        elif kind == 'nation':
            nt = raw.p['nations'][tg]
            band.append(('unity', nt['unity'], M.unity_word(nt['unity']), seen(r['ocr'], 'Unity'), r['png'], r['save']))
            for name, v in nt['relations'].items():
                if v < 6 and raw.p['nations'][M.NAMES.index(name)]['unity'] != 0:
                    band.append(('relation', v, M.relation_word(v), seen(r['ocr'], name) or '', r['png'], r['save']))
        elif kind == 'army_left':
            h = raw.army_hdr(tg)
            if h[2] == cur: band.append(('morale', h[7], M.morale_word(h[7]), seen(r['ocr'], 'Morale'), r['png'], r['save']))
        elif kind == 'fleet_left':
            sea = M.i16(int.from_bytes(raw.b[raw.s.fleet0 + tg * sav.FLEET_LEN + 24:raw.s.fleet0 + tg * sav.FLEET_LEN + 26], 'little'))
            band.append(('sea', sea, 'calm' if sea == 0 else 'rough', seen(r['ocr'], 'Sea'), r['png'], r['save']))
    brows, bmism = [], 0
    for fld, v, exp_w, seen_w, png, save in band:
        s = (seen_w or '').strip(); e = (exp_w or '').strip()
        st = 'OK' if s == e else 'MISMATCH'
        if st != 'OK': bmism += 1
        brows.append((fld, v, e, s, st, png, save))
    summ = ('captures %d; panel lines OK %d; OCR-fuzzy %d; BEYOND-TABLE (not modelled) %d; MISMATCH %d; excluded (wrong subject) %d; not modelled %d\n'
            'band samples %d; band MISMATCH %d\n') % (len(rows), ok, fuzzy, bey, mism, excl, sum(1 for o in out if o[3] == 'NOT-MODELLED'), len(brows), bmism)
    print(summ)
    if write:
        p1 = write_new(DATA + 'claims_audit_lines.tsv', 'png\tkind\ttarget\tstatus\tdetail\n' + ''.join('\t'.join(map(str, o)) + '\n' for o in out))
        p2 = write_new(DATA + 'band_samples.tsv', 'field\tvalue\texpected_word\tseen_word\tstatus\tpng\tsave\n' + ''.join('\t'.join(map(str, o)) + '\n' for o in brows))
        p3 = write_new(DATA + 'claims_audit_summary.txt', summ)
        print(p1, p2, p3)
    for o in out:
        if o[3] in ('MISMATCH', 'NOT-MODELLED'): print(o)
    for b in brows:
        if b[4] != 'OK': print(b)
    return 1 if (mism or bmism) else 0

if __name__ == '__main__': sys.exit(main('--write' in sys.argv))
