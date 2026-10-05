"""Row-by-row comparison of a panel's OCR text with the model's rows (PR #46 rounds 1-2). The only automatic tolerances are:
  spacing           runs of blanks collapse; the OCR sometimes drops a blank inside a row ('Lightinfantry'): compared on the space-free text of a row;
  ordinal glyph     a leading 'l' for '1' in an ordinal ('lst' for '1st'), anywhere in a row; never changes a number field;
  clipping          ONLY for a row whose pixel extent is individually evidenced to touch the window edge (`evidence[i]` = 'right' or 'left', from row_extents.tsv):
                    the visible text must be a STRICTLY shorter exact prefix (right) / suffix (left) of the expected row, space-free; the last (first) visible glyph
                    may be a half-cut mis-read only where the expected glyph there is a letter. Short rows, headers and fully visible rows must match exactly:
                    a full-length word that differs is a MISMATCH.
Anything else (a changed digit or word, a missing or extra row) is a MISMATCH unless a tracked, individually justified entry covers it (OCR corrections, game-output
differences): those have their own statuses.
Statuses returned: OK, OK-ordinal, CLIPPED-right, CLIPPED-left, CORRECTED-OCR, NOT-MODELLED-OUTPUT, SCROLLBAR-ARTIFACT, MISMATCH, MISSING, EXTRA."""
import re
STATUSES = ('OK', 'OK-ordinal', 'CLIPPED-right', 'CLIPPED-left', 'CORRECTED-OCR', 'NOT-MODELLED-OUTPUT', 'SCROLLBAR-ARTIFACT', 'MISMATCH', 'MISSING', 'EXTRA')
FAILING = ('MISMATCH', 'MISSING', 'EXTRA')
def norm(t): return re.sub(r'\s+', ' ', t).strip()
def nospace(t): return re.sub(r'\s+', '', t)
def drop_header(got):
    got = [norm(g) for g in got if norm(g)]
    if got and re.fullmatch(r'\W*[Ii]nformation\W*', got[0]): got = got[1:]
    return got
MIN_CLIP_CHARS = 25     # a row that fills a 320 px window holds far more than this many glyphs: a short visible text can never be a clipped row, whatever the evidence
ORD = re.compile(r'\b[l1](st|nd|rd|th)\b')
def _ord(t): return ORD.sub(r'1\1', t)
def compare_row(e, g, evidence=None):
    if norm(e) == norm(g) or nospace(e) == nospace(g): return 'OK'
    e, g = _ord(norm(e)), _ord(norm(g))
    en, gn = nospace(e), nospace(g)
    if en == gn: return 'OK-ordinal'
    if evidence == 'right' and MIN_CLIP_CHARS <= len(gn) < len(en):
        if en.startswith(gn) or (en.startswith(gn[:-1]) and en[len(gn) - 1].isalpha()): return 'CLIPPED-right'
    if evidence == 'left' and MIN_CLIP_CHARS <= len(gn) < len(en):
        if en.endswith(gn) or (en.endswith(gn[1:]) and en[len(en) - len(gn)].isalpha()): return 'CLIPPED-left'
    return 'MISMATCH'
def compare(expected, got, evidence=None, ocr_corr=(), game_diff=()):
    """expected: rows; got: OCR rows; evidence: {expected_row_index: 'right'|'left'} (pixel-evidenced clipping); ocr_corr / game_diff: [(expected_row, seen_row)]."""
    exp = [norm(e) for e in expected if norm(e)]; got = drop_header(got); evidence = evidence or {}
    out = []
    while len(got) > len(exp) and re.fullmatch(r'[\W_ij]{1,10}', got[-1]) and not re.search(r'[A-Za-z0-9]{2}', got[-1]):
        out.append(('SCROLLBAR-ARTIFACT', '', got.pop()))
    for i in range(max(len(exp), len(got))):
        e = exp[i] if i < len(exp) else None; g = got[i] if i < len(got) else None
        if e is None: out.append(('EXTRA', '', g)); continue
        if g is None: out.append(('MISSING', e, '')); continue
        st = compare_row(e, g, evidence.get(i))
        if st == 'MISMATCH':
            if (e, g) in set(ocr_corr): st = 'CORRECTED-OCR'
            elif (e, g) in set(game_diff): st = 'NOT-MODELLED-OUTPUT'
        out.append((st, e, g))
    return out
