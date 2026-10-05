"""Row-by-row comparison of a panel's OCR text with the model's rows. The only automatic tolerances are:
  spacing           runs of blanks collapse; the OCR sometimes drops a blank inside a row ('Lightinfantry'): compared on the space-free text of a row;
  ordinal glyph     a leading 'l' for '1' in an ordinal ('lst' for '1st') of a unit name, never in a number field;
  clipping (lists)  a list row wider than the 328 px window is cut on the right (unscrolled) or left (scrolled 96 px): the visible text must be an exact
                    prefix / suffix (space-free) of the expected row; a clipped last/first word may be partial only if the expected word is alphabetic.
Anything else (a changed digit, a changed word, a missing or an extra row) is a MISMATCH unless a tracked individually justified correction covers it.
Returns [(status, expected_row, got_row)] with status in OK, OK-ordinal, CLIPPED-right, CLIPPED-left, CORRECTED, MISMATCH, MISSING, EXTRA."""
import re

def norm(t): return re.sub(r'\s+', ' ', t).strip()
def nospace(t): return re.sub(r'\s+', '', t)
def drop_header(got):
    got = [norm(g) for g in got if norm(g)]
    if got and re.fullmatch(r'\W*[Ii]nformation\W*', got[0]): got = got[1:]
    return got
ORD = re.compile(r'\b[l1](st|nd|rd|th)\b')
def _ord(t): return ORD.sub(r'1\1', t)          # the OCR reads the digit 1 of an ordinal ('1st') as the letter l
def compare_row(e, g, clip=None):
    if norm(e) == norm(g): return 'OK'
    if nospace(e) == nospace(g): return 'OK'
    e, g = _ord(norm(e)), _ord(norm(g))
    en, gn = nospace(e), nospace(g)
    if en == gn: return 'OK-ordinal'
    if clip in ('right', 'any') and 3 < len(gn) <= len(en):
        if en.startswith(gn) and len(gn) < len(en): return 'CLIPPED-right'
        # the last visible glyph may be a half-cut letter mis-read: allowed only where the expected glyph at that place is a letter
        if en.startswith(gn[:-1]) and en[len(gn) - 1].isalpha(): return 'CLIPPED-right'
    if clip in ('left', 'any') and 3 < len(gn) <= len(en):
        if en.endswith(gn) and len(gn) < len(en): return 'CLIPPED-left'
        if en.endswith(gn[1:]) and en[len(en) - len(gn)].isalpha(): return 'CLIPPED-left'
    return 'MISMATCH'
def compare(expected, got, clip=None, corrections=()):
    """expected: list of rows; got: OCR rows (header dropped). corrections: [(expected_row, got_row)] individually justified (tracked file)."""
    exp = [norm(e) for e in expected if norm(e)]; got = drop_header(got)
    out = []
    # trailing rows made only of scroll-bar arrow glyphs (the crop includes the horizontal scroll bar when a list is wider than the window) are not panel content
    while len(got) > len(exp) and re.fullmatch(r'[\W_ij]{1,10}', got[-1]) and not re.search(r'[A-Za-z0-9]{2}', got[-1]):
        out.append(('SCROLLBAR-ARTIFACT', '', got.pop()))
    for i in range(max(len(exp), len(got))):
        e = exp[i] if i < len(exp) else None; g = got[i] if i < len(got) else None
        if e is None: out.append(('EXTRA', '', g)); continue
        if g is None: out.append(('MISSING', e, '')); continue
        st = compare_row(e, g, clip)
        if st == 'MISMATCH' and (e, g) in set(corrections): st = 'CORRECTED'
        out.append((st, e, g))
    return out
