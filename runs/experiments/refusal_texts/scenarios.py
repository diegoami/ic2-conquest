"""Scenario table of the refusal-text plays. Each: src (a save in the private game folder or the repo's saves/), ops (staged edits, [] = a fixture used as it is),
act(g) (issues the one order without dismissing boxes), note."""
import os
from play_lib import *
from eog import _drv
GF = lambda n: str(_drv.G / n)                 # a save of the private game folder (copied from ~/ic2-work; the T_* saves are the earlier sessions' play states)
def named(units):
    """explicit names for every unit (the slots' old bytes can hold residue longer than the 23 characters set_units allows)"""
    out = []; cnt = {}
    for (t, n, q, lab) in units:
        cnt[t] = cnt.get(t, 0) + 1
        nm = '%s %s  Battalion' % (STAGE._ordinal(cnt[t]), STAGE.KIND[t]) if not lab else 'Hired %s %d' % (STAGE.KIND[t], cnt[t])
        out.append((t, n, q, lab, nm))
    return out
def U(t, n, q=6, lab=0): return (t, n, q, lab)
SC = {}
SC['UA04'] = dict(src=GF('T_JOIN_FLEETS.SAV'), note='split army 13 (one unit)', act=lambda g: army_button(g, 13, 'split'),
                  fixture_note='T_JOIN_FLEETS.SAV army 13 has one unit (an earlier play state, unedited)')

def join_ops(n, size, typ='li'):
    return [('units', 0, named([U(typ, size)] * n)), ('units', 1, named([U(typ, size)] * n))]
JOIN = lambda g: army_button(g, 0, 'join')
SC['UA05a'] = dict(src=GF('T_TRANSFER.SAV'), ops=join_ops(11, 3000), act=JOIN, note='join armies 0+1: 22 units, 66,000 troops (over 20 units only)')
SC['UA05b'] = dict(src=GF('T_TRANSFER.SAV'), ops=join_ops(8, 7000, 'hi'), act=JOIN, note='join armies 0+1: 16 units, 112,000 troops (over 100,000 only)')
SC['UA05c'] = dict(src=GF('T_TRANSFER.SAV'), ops=join_ops(11, 5000), act=JOIN, note='join armies 0+1: 22 units AND 110,000 troops (combined case)')

def embark_pre(army, fleet):
    def pre(g):
        ax, ay = g.army_pos(army); fx, fy = g.fleet_pos(fleet)
        g.select_army(army, ax, ay); g.click_tile(fx, fy, pause=1.5)
        if g.fleet_state(fleet)['army'] != army: raise _drv.DriverError('embark of army %d on fleet %d not verified: %s' % (army, fleet, g.fleet_state(fleet)))
    return pre
SC['UF05'] = dict(src=GF('T_EMBARK_REFUSED.SAV'), ops=[('fleet', 2, 'ships', 25), ('fleet', 5, 'ships', 5)], pre=embark_pre(0, 2), act=lambda g: fleet_button(g, 5, 'join'),
                  note='fleets 2 (25 ships) and 5 (5 ships) staged; army 0 embarked on fleet 2 by a normal embark order before the control save; Join fleets from fleet 5 (30 ships, one carries an army)')
SC['UF05b'] = dict(src=GF('T_EMBARK_REFUSED.SAV'), ops=[('fleet', 2, 'ships', 60), ('fleet', 5, 'ships', 50)], act=lambda g: fleet_button(g, 5, 'join'),
                  note='Join fleets 5+2: 110 ships, neither carries an army')
SC['UF05c'] = dict(src=GF('T_EMBARK_REFUSED.SAV'), ops=[('fleet', 2, 'ships', 60), ('fleet', 5, 'ships', 50)], pre=embark_pre(0, 2), act=lambda g: fleet_button(g, 5, 'join'),
                  note='combined case: 110 ships AND fleet 2 carries army 0 (embarked by a normal order before the control save)')

def cu_open(g, army):
    army_button(g, army, 'change')
    open_dialog_tracked(g, 'Change units', lambda: None, tries=1)
def cu_act(army, rows, button):
    def act(g):
        cu_open(g, army); select_rows(g, 'Change units', rows); press(g, 'Change units', button)
    return act
cu_post = lambda g: close_dialog_cancel(g, 'Change units')
SC['D06'] = dict(src=GF('T_BASE.SAV'), ops=[('units', 0, named([U('hi', 5000, 7), U('hi', 100, 6)]))], act=cu_act(0, [1], 'Split unit'), post=cu_post,
                 note='Change units: Split unit on a 100-troop heavy-infantry unit')
SC['D05a'] = dict(src=GF('T_BASE.SAV'), ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6)]))], act=cu_act(0, [0, 1], 'Rename unit'), post=cu_post,
                  note='Change units: Rename unit with two units selected')
SC['D05b'] = dict(src=GF('T_BASE.SAV'), ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6, 11)]))], act=cu_act(0, [1], 'Rename unit'), post=cu_post,
                  note='Change units: Rename unit on a mercenary unit (label 11)')

# ---------------------------------------------------------------- batch b2: the other refusals the staged saves allow
TB = GF('T_BASE.SAV'); TE = GF('T_EMBARK_REFUSED.SAV'); TT = GF('T_TRANSFER.SAV')
SC['S01'] = dict(src=TB, act=lambda g: army_button(g, 1, 'disband'), note='Disband army 1 at (120,53) (not near a city?)')
SC['M01'] = dict(src=TB, ops=[('supplies', 1, 0)], act=lambda g: army_button(g, 1, 'mercs'), note='Recruit mercenaries, army 1 with 0 supplies (next to the Heraclea offer)')
SC['M02'] = dict(src=TB, ops=[('units', 1, named([U('li', 15000)] * 7))], act=lambda g: army_button(g, 1, 'mercs'), note='Recruit mercenaries, army 1 with 7 x 15,000 = 105,000 troops')
SC['M03'] = dict(src=TB, ops=[('units', 1, named([U('li', 1000)] * 20))], act=lambda g: army_button(g, 1, 'mercs'), note='Recruit mercenaries, army 1 with 20 units')
SC['F01'] = dict(src=TE, act=lambda g: fleet_button(g, 5, 'split'), note='Split fleet 5 (10 ships)')
SC['F02'] = dict(src=TE, ops=[('fleet', 2, 'ships', 25)], pre=embark_pre(0, 2), act=lambda g: fleet_button(g, 2, 'split'), note='Split fleet 2 (25 ships) carrying army 0')
SC['F03'] = dict(src=TE, act=lambda g: fleet_button(g, 2, 'repair'), note='Repair fleet 2 at (101,46)')
SC['F04'] = dict(src=TE, act=lambda g: fleet_button(g, 2, 'scuttle'), note='Scuttle fleet 2 at (101,46)')
SC['F05'] = dict(src=TE, ops=[('fleet', 2, 'ships', 25)], pre=embark_pre(0, 2), act=lambda g: fleet_button(g, 2, 'scuttle'), note='Scuttle fleet 2 carrying army 0')
SC['F06'] = dict(src=TE, ops=[('fleet', 2, 'ships', 25)], pre=embark_pre(0, 2), act=lambda g: fleet_button(g, 2, 'repair'), note='Repair fleet 2 carrying army 0')

def city_button(g, x, y, tool_label='Fortify city'):
    g.reset_ui(); g.click_tile(x, y, pause=1.0)
    found = g._scan_bar(ARMY_Y, {'fortify': tool_label}, 336, 420, 0.5)
    if 'fortify' not in found: raise _drv.DriverError('city toolbar: no %s tooltip' % tool_label)
    g.click(found['fortify'], ARMY_Y, pause=1.5)
SC['C01'] = dict(src=TB, ops=[('city', 82, {'fort': 100})], act=lambda g: city_button(g, 99, 42), note='Fortify Caere with fortification 100')
SC['C02'] = dict(src=TB, ops=[('city', 82, {'fort': 172})], act=lambda g: city_button(g, 99, 42), note='Fortify Caere with a fortification order pending (stored 172)')

SC['S01'] = dict(src=TT, act=lambda g: army_button(g, 0, 'disband'), note='Disband army 0 at (103,36) (no own city within one tile)')
def tr_act(army, row):
    def act(g):
        army_button(g, army, 'transfer'); open_dialog_tracked(g, 'Army to army transfer', lambda: None, tries=1)
        cs = g.controls('Army to army transfer')
        lists = sorted((c for c in cs if c['cls'] == 'TListBox'), key=lambda c: c['x'])
        g.click(lists[0]['x'] + lists[0]['w'] // 2, lists[0]['y'] + 12 + 12 * row, pause=0.5)
        tb = sorted((c for c in cs if c['text'] == 'Transfer'), key=lambda c: c['x'])[0]
        g.click_control(tb, pause=1.5)
    return act
tr_post = lambda g: close_dialog_cancel(g, 'Army to army transfer')
SC['T01'] = dict(src=TT, ops=[('units', 0, named([U('li', 3000)] * 3)), ('units', 1, named([U('li', 1000)] * 20))], act=tr_act(0, 0), post=tr_post,
                 note='Army to army transfer: one unit of army 0 (3 units) into army 1 (20 units)')
SC['T02'] = dict(src=TT, ops=[('units', 0, named([U('hi', 6000)] * 2)), ('units', 1, named([U('hi', 12000)] * 8))], act=tr_act(0, 0), post=tr_post,
                 note='Army to army transfer: a 6,000 unit of army 0 into army 1 (8 x 12,000 = 96,000 troops)')
SC['CU01'] = dict(src=TB, ops=[('units', 0, named([U('li', 4000)] * 20))], act=cu_act(0, [0], 'Split unit'), post=cu_post, note='Change units: Split unit in an army of 20 units')
SC['CU02'] = dict(src=TB, ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6, 11)]))], act=cu_act(0, [1], 'Split unit'), post=cu_post, note='Change units: Split unit on a mercenary unit')
SC['CU03'] = dict(src=TB, ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6)]))], act=cu_act(0, [0, 1], 'Split unit'), post=cu_post, note='Change units: Split unit with two units selected')
SC['CU04'] = dict(src=TB, ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6, 11)]))], act=cu_act(0, [0, 1], 'Join units'), post=cu_post, note='Change units: Join units, one regular and one mercenary')
SC['CU05'] = dict(src=TB, ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6)]))], act=cu_act(0, [0, 1], 'Join units'), post=cu_post, note='Change units: Join units of two types')
SC['CU06'] = dict(src=TB, ops=[('units', 0, named([U('hi', 20000, 7), U('hi', 20000, 6)]))], act=cu_act(0, [0, 1], 'Join units'), post=cu_post, note='Change units: Join units, two heavy infantry of 20,000')
def cu_disband_act(g):
    cu_open(g, 0); select_rows(g, 'Change units', [0]); press(g, 'Change units', 'Disband'); confirm_step(g, 'Yes')
SC['CU07'] = dict(src=TT, ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6, 11)]))], act=cu_disband_act, post=cu_post, note='Change units: Disband the regular unit 0 of army 0 at (103,36), far from a city (Confirm answered Yes)')
SC['CU08'] = dict(src=TT, ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6, 11)]))], act=lambda g: (cu_open(g, 0), select_rows(g, 'Change units', [0, 1]), press(g, 'Change units', 'Disband'), confirm_step(g, 'Yes')), post=cu_post,
                  note='Change units: Disband a regular and a mercenary unit at (103,36) (Confirm Yes)')
