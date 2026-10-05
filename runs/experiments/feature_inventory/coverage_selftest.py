#!/usr/bin/env python3
"""Self-test of the coverage checker: feed it bad rows, bad news literals and an unmapped entry; every case must be REJECTED.
Exit status 1 if any bad input is accepted. Usage: coverage_selftest.py"""
import sys, os, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coverage_check as cc
ctx = cc.Ctx(); good = cc.load_rows()
base = dict(id='T1', group='File', name='x', what='w', pre='none', evidence='', tag='[confirmed]', need='needed')
def case(name, ev, tag, expect):
    r = dict(base, evidence=ev, tag=tag); v = cc.validate_rows({'T1': r}, ctx)
    hit = any(expect in x for x in v)
    print('%-62s %s  %s' % (name, 'REJECTED' if hit else 'ACCEPTED (BAD)', v[:1] if v else ''))
    return hit
res = []
res.append(case('confirmed with only a report citation', 'F:2026-10-02-unit-map-mouse-orders-and-tax-range.md (a)', '[confirmed]', '[confirmed] without'))
res.append(case('confirmed with only a log path', 'explore/b1.log', '[confirmed]', '[confirmed] without'))
res.append(case('confirmed with a screenshot not in the manifest', 'SS:FI_nonexistent.png FI_b9_99_nothing.png', '[confirmed]', 'not in the tracked manifest'))
res.append(case('confirmed with a save name that no tracked file mentions', 'NO_SUCH_SAVE_XYZ.SAV', '[confirmed]', '[confirmed] without'))
res.append(case("confirmed citing a coverage row that is not ✅", "C:§1 'Supply army'", '[confirmed]', 'not found with status'))
res.append(case('derived with no function, form, report or help topic', 'SS:FI_b1_01_main.png', '[derived]', '[derived] without'))
res.append(case('bad tag word', 'x', '[probable]', 'bad tag'))
# duplicate screenshot hash cited as two different screens
a, b = 'FI_b1_11_menu_unit.png', 'FI_b1_14_menu_unit_fleet_submenu.png'
rows = {'T1': dict(base, id='T1', evidence=a, tag='[confirmed]'), 'T2': dict(base, id='T2', evidence=b, tag='[confirmed]')}
v = cc.validate_rows(rows, ctx); ok = any('duplicate screenshot hash' in x for x in v)
print('%-62s %s  %s' % ('two different screens with one hash (batch 1 submenu shots)', 'REJECTED' if ok else 'ACCEPTED (BAD)', v[:1])); res.append(ok)
# news
lits = {'0x00449a44': {' forms an alliance with ', ' declares war on '}, '0x004514ec': {'Week  ', ' '}}
def news(name, row, expect_bad=True):
    p = cc.check_news([row], lits); ok = bool(p) == expect_bad
    print('%-62s %s  %s' % (name, 'REJECTED' if p else 'ACCEPTED', p[:1])); return ok
res.append(news('news literal only a substring of a real literal', ('x', 't', '" declares"', '0x00449a44', 'L03', 's')))
res.append(news('news literal in the wrong function', ('x', 't', '" declares war on "', '0x004514ec', 'L03', 's')))
res.append(news('news literal that exists nowhere', ('x', 't', '"never written"', '0x00449a44', 'L03', 's')))
res.append(news('news literal accepted when exact and in its function (control)', ('x', 't', '" declares war on "', '0x00449a44', 'L03', 's'), expect_bad=False))
# a rule naming a missing row, and an unaccounted entry: run the whole check on a copy of the rows with L03 removed
rows2 = copy.deepcopy(good); del rows2['L03']
rep, ent, clean = cc.run(rows2, ctx)
ok = (not clean) and 'rule problems: [' in rep
print('%-62s %s' % ('rules naming a row that no longer exists', 'REJECTED' if ok else 'ACCEPTED (BAD)')); res.append(ok)
rep, ent, clean = cc.run(good, ctx); print('%-62s %s' % ('the real inventory passes (control)', 'PASSES' if clean else 'FAILS')); res.append(clean)
print('\n%d of %d checks behaved as required' % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
