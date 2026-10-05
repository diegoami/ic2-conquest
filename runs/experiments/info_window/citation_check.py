"""[O]-citation sweep (PR #46 R5/R-D): every screenshot cited as observation in the findings must, in the audit's row table (claims_audit3_rows*), contain the row
the claim is about, matched exactly (status OK, OK-ordinal or CORRECTED, never a clipped row). Two lists: ROW_CHECK (one regex per table row id, applied to the
capture cited in findings_rows.py) and PROSE (the citations in the findings' prose and band notes). Also: every *.png token of the findings must be in captures.tsv or in
the explicit NOT_IN_CAPTURES list (labelled in the text). Exit 1 on any failure.   python3 citation_check.py [--write]"""
import sys, os, re, csv, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iw_lib import DATA, ROOT, write_new
import findings_rows as FR
OKS = ('OK', 'OK-ordinal', 'CORRECTED-OCR')
ROW_CHECK = {
 'N01': r'^Nation \w', 'N02': r'^Leader \w', 'N03': r'^Capital \w', 'N04': r'^Cities \d', 'N05': r'^Population \d{1,3}(,\d{3})+$', 'N06': r'^Unity (very low|low|normal|high|very high|excellent)$',
 'N07': r'^Tax rate \d+%$', 'N08': r'^Mobilized \d+%$', 'N09': r'^Treasury -? ?[\d,]+ talents$', 'N10': r'^INTERNATIONAL RELATIONS$', 'N11': r'^\w+ (trade|ally|war)$', 'N12': r'conquerred by',
 'C01': r'^City \w', 'C02': r'^Controlled by \w', 'C03': r'^Allegiance to \w', 'C04': r'^Population [\d,]+ \(\d+%\)$', 'C05': r'^Loyalty (very low|low|normal|high|very high|excellent)$',
 'C06': r'^Fortification \d+%( \(under construction\))?', 'C07': r'^Fortification \d+%.* \([\d,]+\)$', 'C08': r'^Tribute \d+ talents$', 'C09': r'^Tribute (poor|moderate|rich|very rich)$', 'C10': r'^Supply \d+ tons$',
 'A01': r'^Army of \w', 'A02': r'^Moves \d+$', 'A03': r'^Supply \d+ tons \(\d+%\)$', 'A04': r'^Morale (very low|low|normal|high|very high|excellent)$', 'A05': r'^Money \d+ talents$', 'A06': r'^Terrain \w',
 'A07': r'^Light infantry [\d,]+$', 'A08': r'^Total troops [\d,]+$', 'A09': r'^No\. of units \d+$', 'A10': r'^Regulars cost \d+ talents per quarter$', 'A11': r'^Mercenary pay [1-9]\d* talents per quarter$',
 'F01': r'^Fleet of \w', 'F02': r'^Moves \d+$', 'F03': r'^Ships \d+$', 'F04': r'^Repair \d+%$', 'F05': r'^Supply \d+ tons \(\d+%\)$', 'F06': r'^Money \d+ talents$', 'F07': r'^Capacity [\d,]+ troops$',
 'F08': r'^Sea (calm|rough)$', 'F09': r'^Army$', 'U1': r'^Mercenaries at \w', 'U2': r'(not ready|very poor|poor|average|good|very good|elite)$', 'U3': r'Battalion .* (average|good|very good|poor|elite)',
}
# (png, [regexes that must each match an OK row], [regexes that must match NO row], what the prose claims)
PROSE = [
 ('A1_city_071_Pisae.png', [r'^Loyalty ite$'], [], 'loyalty -10 prints ite'),
 ('A1_city_080_Tarquinii.png', [r'^Loyalty very low$'], [], 'loyalty -9 prints very low'),
 ('A4_army_00_left.png', [r'^Morale very low$'], [], 'morale 50 very low'),
 ('A4_army_13_left.png', [r'^Morale$'], [r'^Morale \w'], 'morale 75 blank'),
 ('A6_army0_right_scrolled.png', [r'^Test unit 10 Light infantry 2,000$', r'^Test unit 11 Heavy infantry 2,100$', r'^Test unit 9 Heavy cavalry 1,900 elite$'], [], 'quality 10 and 11 blank, 9 elite'),
 ('A2_city_026_Helice.png', [r'^Tribute 10001$'], [], 'tribute 10001 prints the number'),
 ('A2_city_030_Akra Leuke.png', [r'^Tribute 20000$'], [], 'tribute 20000'),
 ('A2_city_033_Icosium.png', [r'^Tribute -25536$'], [], 'tribute 40000 prints -25536'),
 ('A2_city_035_Cissa.png', [r'^Tribute -1$'], [], 'tribute 65535 prints -1'),
 ('A1_city_082_Caere.png', [r'^Fortification 100%$'], [r'under construction'], 'fortification 100 prints 100%'),
 ('A1_city_101_Neapolis.png', [r'^Fortification 1% \(under construction\)$'], [], 'fortification 101 prints 1% under construction'),
 ('A2_city_090_Alba Fucens.png', [r'^Fortification 61% \(3,000\)$'], [], 'state 0 + state 24 = (3,000)'),
 ('A7b_nation00_treasury1.png', [r'^Mobilized 100%$', r'^Treasury 0 talents$'], [], 'own nation panel has Mobilized and Treasury'),
 ('A8_cur1_nation00.png', [r'^Population 2,577,000$'], [r'^Mobilized', r'^Treasury'], 'Rome (foreign, current Carthage): Population 2,577,000, no Mobilized/Treasury'),
 ('A8_cur1_nation01.png', [r'^Population 4,821,000$', r'^Mobilized 12%$', r'^Treasury 7,777 talents$'], [], 'Carthage as current nation: Population 4,821,000, Mobilized 12%, Treasury 7,777'),
 ('A7_nation00_treasury0.png', [r'^Treasury - ?1,500 talents$'], [], 'negative treasury: minus, blank, digits'),
 ('A3_nation_08_Celtiberia.v2.png', [r'^Population 5,000$'], [], 'population -5000 prints without its sign'),
 ('A3_nation_13_Armenia.v2.png', [r'^Unity$'], [r'^Unity \w'], 'unity 1000 blank'),
 ('A3_nation_14_Media.v2.png', [r'^Unity$'], [r'^Unity \w'], 'unity 1100 blank'),
 ('A5_foreign_army2_left.png', [r'^Moves$', r'^Supply$', r'^Morale$', r'^Money$', r'^Terrain \w', r'^Total troops [\d,]+$'], [r'^No\. of units', r'^Regulars cost', r'^Mercenary pay'], 'foreign army: captions only, composition, no cost lines'),
 ('A5_foreign_army2_right.png', [r'^Total troops [\d,]+$'], [r'^Army of Carthage .*Battalion'], 'right click on a foreign army prints nothing new'),
 ('A5_f5a_fleet0_left.png', [r'^Fleet of Carthage$', r'^Moves$', r'^Ships 90$', r'^Repair$', r'^Supply$', r'^Money$', r'^Capacity 45,000 troops$', r'^Sea rough$'], [], 'foreign fleet'),
 ('A5_f5b_fleet1_left.png', [r'^Fleet of Ptolemaic$', r'^Sea calm$'], [], 'foreign fleet calm'),
 ('A5_f5c_fleet0_left.png', [r'^Army$', r'^Light infantry 4,800$', r'^Supply$', r'^Morale$'], [r'^No\. of units'], 'foreign fleet carrying an army: composition only'),
 ('A5_f5a_fleet2_left.png', [r'^Sea calm$'], [], 'sea 0 calm'),
 ('A5_f5a_fleet1_left.png', [r'^Sea rough$'], [], 'sea -1 rough'),
 ('A5_f5b_fleet0_left.png', [r'^Sea rough$'], [], 'sea 2 rough'),
]
NOT_IN_CAPTURES = {'t4_menu.png': 'menu screenshot (Thracia item greyed): in the release manifest, checked by eye, not a panel capture'}
def main(write=False):
    rows = {}
    for f in glob.glob(DATA + 'claims_audit3_rows*.tsv'): pass
    f = sorted(glob.glob(DATA + 'claims_audit3_rows*.tsv'), key=lambda p: (len(p), p))[-1]
    for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'):
        if r['status'] in OKS: rows.setdefault(r['png'], []).append(r['expected'])
    caps = set()
    for g in glob.glob(DATA + 'captures*.tsv'): caps |= {r['png'] for r in csv.DictReader(open(g, encoding='utf-8'), delimiter='\t')}
    res = []; bad = 0
    for r in FR.ROWS:
        if r['id'] == 'H1': continue
        png = r['seen']; ok = png in rows and any(re.search(ROW_CHECK[r['id']], x) for x in rows[png])
        res.append(('row', r['id'], png, 'OK' if ok else 'FAIL')); bad += not ok
    for png, must, mustnot, claim in PROSE:
        rs = rows.get(png, [])
        ok = bool(rs) and all(any(re.search(m, x) for x in rs) for m in must) and not any(re.search(m, x) for m in mustnot for x in rs)
        res.append(('prose', claim, png, 'OK' if ok else 'FAIL')); bad += not ok
    doc = open(ROOT + '/findings/2026-10-05-information-window-fields-and-bands.md', encoding='utf-8').read()
    for png in sorted(set(re.findall(r'`([^`]+\.png)`', doc))):
        if png not in caps and png not in NOT_IN_CAPTURES: res.append(('png-token', png, '', 'NOT IN captures.tsv')); bad += 1
    print('citations checked %d; failures %d' % (len(res), bad))
    for x in res:
        if x[3] != 'OK': print(x)
    if write: print(write_new(DATA + 'citation_check.tsv', 'kind\tclaim\tpng\tstatus\n' + ''.join('\t'.join(x) + '\n' for x in res)))
    return 1 if bad else 0
if __name__ == '__main__': sys.exit(main('--write' in sys.argv))
