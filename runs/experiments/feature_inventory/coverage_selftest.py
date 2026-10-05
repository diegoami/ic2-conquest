#!/usr/bin/env python3
"""Self-test of the coverage checker: every bad input must be REJECTED (and the controls accepted). Exit 1 if a bad input passes.
Usage: coverage_selftest.py"""
import sys, os, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_check as cc
ctx = cc.Ctx(); good = cc.load_rows()
base = dict(id='T1', group='File', name='x', what='w', pre='none', evidence='', tag='[confirmed]', need='needed')
res = []
def show(name, ok, detail=''):
    print('%-70s %s  %s' % (name, 'OK' if ok else 'FAILED', str(detail)[:150])); res.append(ok)
def bad(name, ev, tag, expect):
    v = cc.validate_rows({'T1': dict(base, evidence=ev, tag=tag)}, ctx); show('REJECT ' + name, any(expect in x for x in v), v[:1])
def okrow(name, ev, tag):
    v = cc.validate_rows({'T1': dict(base, evidence=ev, tag=tag)}, ctx); show('ACCEPT ' + name, not v, v[:1])
FLEET = "Fleet: move, embark, disembark, supply, repair, split, join, transfer, scuttle"
# --- saves
bad('confirmed with only a report citation', 'F:2026-10-02-unit-map-mouse-orders-and-tax-range.md (a)', '[confirmed]', '[confirmed] without')
bad('confirmed with only a log path', 'explore/b1.log', '[confirmed]', '[confirmed] without')
bad('invented save that no independent artifact names', 'INVENTED_BY_ME.SAV', '[confirmed]', 'no independent artifact')
bad('invented save also on a derived row', 'X:TUnitMap_Fortify; INVENTED_BY_ME.SAV', '[derived]', 'no independent artifact')
own = cc.read('findings/' + cc.OWN_FINDING) + ' ONLY_IN_THE_FINDING.SAV'
show('the inventory finding is not a source of the save index', 'ONLY_IN_THE_FINDING.SAV' not in ctx.saves and 'ONLY_IN_THE_FINDING.SAV' in cc.SAVE_RX.findall(own))
bad('save name that is only a substring of a real one (T_MOV.SAV)', 'T_MOV.SAV', '[confirmed]', 'no independent artifact')
okrow('a real save named in coverage.md (control)', 'T_MOVE.SAV', '[confirmed]')
# --- screenshots
bad('screenshot not in the manifest', 'SS:FI_b9_99_nothing.png', '[confirmed]', 'not in the tracked manifest')
rows = {'T1': dict(base, evidence='FI_b1_11_menu_unit.png'), 'T2': dict(base, id='T2', evidence='FI_b1_14_menu_unit_fleet_submenu.png')}
v = cc.validate_rows(rows, ctx); show('REJECT two different screens with one hash (batch-1 submenu shots)', any('duplicate screenshot hash' in x for x in v), v[:1])
okrow('a unique manifest screenshot (control)', 'SS:FI_b2_02_unit_army_submenu.png', '[confirmed]')
# --- coverage.md citations
bad('wrong-section coverage row (the §1 Fleet row cited as §4)', "C:§4 '%s'" % FLEET, '[confirmed]', 'has no row whose first cell')
bad('substring of a real row (C:§1 Fleet)', "C:§1 'Fleet'", '[confirmed]', 'has no row whose first cell')
bad('ambiguous first cell (C:§3 Attack, several rows)', "C:§3 'Attack'", '[confirmed]', 'ambiguous')
bad('coverage row that is not done (C:§1 Supply army)', "C:§1 'Supply army'", '[confirmed]', 'does not have status')
bad('bare section citation with no row', 'C:§1 Fleet row', '[confirmed]', 'bare C:')
okrow('exact section and row (control)', "C:§1 '%s'" % FLEET, '[confirmed]')
# --- derived targets
bad('X:NO_SUCH_FUNCTION', 'X:NO_SUCH_FUNCTION', '[derived]', 'not in the symbol')
bad('a bare X:', 'X:', '[derived]', 'empty X:')
bad('derived with no target at all', 'SS:FI_b1_01_main.png', '[derived]', '[derived] without')
bad('form citation to an unknown form', 'form TNoSuchForm', '[derived]', 'form citation target')
bad("help topic that does not exist", "H:'No such topic'", '[derived]', 'help topic')
bad('document that does not exist', 'R:no-such-report.md', '[derived]', 'unknown document')
bad('finding that does not exist', 'F:2099-01-01-nothing.md', '[derived]', 'does not exist')
bad('rules-digest section that does not exist', 'docs/rules-digest.md §99', '[derived]', 'no section 99')
bad('rules-digest heading that does not exist', 'docs/rules-digest.md §2 "Nothing like this"', '[derived]', 'no heading')
bad('bad tag word', 'x', '[probable]', 'bad tag')
okrow('real function, form, help topic (control)', "X:TUnitMap_Fortify 0x00448004; form TFortifyCity; H:'Fortify city'", '[derived]')
# --- news
lits = {'0x00449a44': {' forms an alliance with ', ' declares war on '}, '0x004514ec': {'Week  ', ' '}}
def news(name, row, expect_bad=True):
    p = cc.check_news([row], lits); show(('REJECT ' if expect_bad else 'ACCEPT ') + name, bool(p) == expect_bad, p[:1])
news('news literal only a substring of a real literal', ('x', 't', '" declares"', '0x00449a44', 'L03', 's'))
news('news literal in the wrong function', ('x', 't', '" declares war on "', '0x004514ec', 'L03', 's'))
news('news literal that exists nowhere', ('x', 't', '"never written"', '0x00449a44', 'L03', 's'))
news('exact literal in its function (control)', ('x', 't', '" declares war on "', '0x00449a44', 'L03', 's'), expect_bad=False)
# --- exclusions and unaccounted entries (run on the real source entries)
cfg = open(os.path.join(cc.DATA, 'coverage_map.cfg'), encoding='utf-8').read()
rep, ent, clean = cc.run(good, ctx, cfg_text='form :: ^form:TAboutIC$ :: EXCLUDED ::\n' + cfg)
show('REJECT an EXCLUDED rule with an empty reason on a real source entry', (not clean) and 'empty reason' in rep, [l for l in rep.split('\n') if 'rule problems' in l][0][:120])
rep, ent, clean = cc.run(good, ctx, cfg_text='form :: ^form:TAboutIC$ :: EXCLUDED ::    \n' + cfg)
show('REJECT an EXCLUDED rule with a whitespace-only reason', (not clean) and 'empty reason' in rep)
cfg2 = '\n'.join(l for l in cfg.split('\n') if not l.startswith('form :: ^form:TAboutIC$'))
rep, ent, clean = cc.run(good, ctx, cfg_text=cfg2)
show('REJECT a real source entry (form TAboutIC) with no rule: unaccounted', (not clean) and 'form:TAboutIC' in ent and 'UNACCOUNTED' in ent.split('form:TAboutIC')[1].split('\n')[0])
rows2 = copy.deepcopy(good); del rows2['L03']
rep, ent, clean = cc.run(rows2, ctx); show('REJECT rules naming a row that no longer exists', (not clean) and 'missing rows' in rep)
# --- audit
aud = cc.load_audit()
a2 = aud + [dict(row='E12', source='docs/rules-digest.md', line='1', quote='x', key='a condition the row never states')]
show('REJECT an audited condition missing from its row', any('missing from the row' in p for p in cc.check_audit(good, a2)))
a3 = aud + [dict(row='E12', source='docs/rules-digest.md', line='1', quote='not on line one', key='.')]
show('REJECT an audit quote that is not on its source line', any('not on' in p for p in cc.check_audit(good, a3)))
r3 = copy.deepcopy(good); r3['E12']['pre'] = r3['E12']['pre']; r3['E12']['what'] = r3['E12']['what'].replace('only if the treasury is above 0', '')
show('REJECT the E12 row with its treasury gate dropped (the review\'s R1 case)', bool(cc.check_audit(r3, aud)))
# --- controls
rep, ent, clean = cc.run(good, ctx); show('ACCEPT the real inventory (control)', clean)
print('\nKnown residual bypasses (semantic, not checkable from tracked files): a cited research-report SECTION is not verified (only the file exists);')
print('a real function, help topic, save or screenshot cited for a claim it does not support; a finding that exists but does not say what is cited;')
print('audit keys are regexes written by the author. These are covered by the row_source_audit conditions and by human review.')
print('\n%d of %d checks behaved as required' % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
