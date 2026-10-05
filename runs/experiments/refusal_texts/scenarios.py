"""Scenario table of the refusal-text plays. Each: src (a save in the private game folder or the repo's saves/), ops (staged edits, [] = a fixture used as it is),
act(g) (issues the one order without dismissing boxes), note."""
import os
from play_lib import *
from eog import _drv
from lib import _region_hash
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

SC['C01'] = dict(src=TB, ops=[('city', 82, {'fort': 100})], act=lambda g: city_button(g, 99, 42), note='Fortify Caere with fortification 100')
SC['C02'] = dict(src=TB, ops=[('city', 82, {'fort': 172})], act=lambda g: city_button(g, 99, 42), note='Fortify Caere with a fortification order pending (stored 172)')

SC['S01'] = dict(src=TT, act=lambda g: army_button(g, 0, 'disband'), note='Disband army 0 at (103,36) (no own city within one tile)')
def tr_act(army, row):
    def act(g):
        army_button(g, army, 'transfer'); open_dialog_tracked(g, 'Army to army transfer', lambda: None, tries=1)
        cs = g.controls('Army to army transfer')
        lists = sorted((c for c in cs if c['cls'] == 'TListBox'), key=lambda c: c['x'])
        click_row(g, lists[0], row)
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

# ---------------------------------------------------------------- batch b3: embark, relations, recruitment
SC['E01'] = dict(src=TE, act=lambda g: (g.select_army(0, *g.army_pos(0)), g.click_tile(*g.fleet_pos(2), pause=1.5)), note='embark army 0 (10,700 troops, 3 moves) on fleet 2 (20 ships): the click on the fleet')
SC['A01'] = dict(src=GF('T_EMBARK.SAV'), ops=[('moves', 12, 3)], act=lambda g: army_button(g, 12, 'join'),
                 note='Join armies from army 12 (moves staged to 3) next to army 0, which is aboard fleet 2')

def rel_act(nation, col):
    def act(g):
        main_tool(g, 'relations')
        if not g.find_windows('^International Relations$'): main_tool(g, 'relations')
        w = g.find_windows('^International Relations$')
        if not w: raise _drv.DriverError('International Relations did not open')
        g.raise_window(w[0][0])
        cs = None
        for _ in range(8):
            try: cs = g.controls('International Relations'); break
            except _drv.DriverError: time.sleep(1)
        radios = sorted((c for c in cs if c['cls'] == 'TRadioButton'), key=lambda c: (c['y'], c['x']))
        if len(radios) != 64: raise _drv.DriverError('expected 64 radio buttons, found %d' % len(radios))
        tgt = radios[nation * 4 + col]
        for attempt in range(3):                          # the refusal box appears at the click of the radio (the callee fails and the radio goes back): that box, or a change of the radio's pixels, proves the click
            before = _region_hash(g, tgt); g.click_control(tgt, pause=1.2)
            if boxes(g): break
            if _region_hash(g, tgt) != before: break
        else: raise _drv.DriverError('relations radio nation %d column %d: neither a box nor a change after 3 clicks' % (nation, col))
        if not boxes(g): raise _drv.DriverError('the radio changed and no refusal box appeared (the order would be accepted): not a refusal play')
    return act
rel_post = lambda g: close_dialog_cancel(g, 'International Relations')
SC['RL01'] = dict(src=TB, act=rel_act(6, 0), post=rel_post, note='International relations: peace with Gaul (6), at war with Rome (relation 3)')
SC['RL02'] = dict(src=TB, ops=[('relation', 0, 1, 1), ('relation', 0, 2, 1)], act=rel_act(7, 1), post=rel_post, note='International relations: trade with Greece (7) while Rome trades with Illyria, Carthage and Seleucid (3 partners; the two staged)')
SC['RL03'] = dict(src=TB, act=rel_act(4, 1), post=rel_post, note='International relations: trade with Macedonia (4), relation -8 (cooldown)')
SC['RL04'] = dict(src=TB, act=rel_act(6, 1), post=rel_post, note='International relations: trade with Gaul (6), at war (relation 3)')
SC['RL05'] = dict(src=TB, act=rel_act(1, 2), post=rel_post, note='International relations: alliance with Carthage (1) while Rome is at war with Gaul')

def recruit_act(g):
    main_tool(g, 'recruit'); g.wait(lambda: g.find_windows('^Army recruits$'), 10, 'Army recruits dialog'); cs = g.controls('Army recruits')
    cities = g.control(cs, cls='TListBox', index=0)
    click_row(g, cities, 0)
    g.click_control(g.control(cs, text='Light infantry'), pause=0.6)
    g.click_control(g.control(cs, text='Recruit unit'), pause=1.2)
recruit_post = lambda g: close_dialog_cancel(g, 'Army recruits', button='OK')
SC['RC01'] = dict(src=TB, ops=[('nation', 0, 0x420, 1)], act=recruit_act, post=recruit_post, note='Recruit unit with the 40th recruitment slot occupied (nation 0 +0x420 staged to 1)')
SC['RC02'] = dict(src=TB, ops=[('nation', 0, 0x442, 100)], act=recruit_act, post=recruit_post, note='Recruit unit with the mobilisation rate at 100 (nation 0 +0x442 staged)')

def sail_pre(fleet, x, y):
    def pre(g):
        g.select_fleet(fleet); g.click_tile(x, y, pause=1.5)
        p = g.fleet_pos(fleet)
        if tuple(p) != (x, y): raise _drv.DriverError('fleet %d is at %s, not at (%d,%d) after the move order' % (fleet, tuple(p), x, y))
    return pre
SC['F03b'] = dict(src=TE, pre=sail_pre(2, 97, 48), act=lambda g: fleet_button(g, 2, 'repair'), note='Repair fleet 2 after a normal sail order to (97,48), five tiles from any city')
SC['F04b'] = dict(src=TE, pre=sail_pre(2, 97, 48), act=lambda g: fleet_button(g, 2, 'scuttle'), note='Scuttle fleet 2 after a normal sail order to (97,48)')

def sel_act(g):
    ax, ay = g.army_pos(0); g.select_army(0, ax, ay)
SC['SEL01'] = dict(src=GF('T_BASE.SAV'), act=sel_act, note='control for the UI bytes: army 0 only SELECTED (no order, no box), then the after save')

# ---------------------------------------------------------------- batch b4: more rows
SC['M04'] = dict(src=TB, ops=[('city', 120, {'owner': 6})], act=lambda g: army_button(g, 1, 'mercs'),
                 note='Recruit mercenaries, army 1 next to Heraclea (120) whose owner is staged to Gaul (6), at war with Rome')
SC['C03'] = dict(src=TB, ops=[('city', 73, {'owner': 0})], act=lambda g: city_button(g, 94, 27),
                 note='Fortify Brixia (73), owner staged to Rome, with the Gaulish army 9 (at war) one tile away')
def merc_act(g):
    army_button(g, 1, 'mercs'); open_dialog_tracked(g, 'Recruit mercenary unit', lambda: None, tries=1)
    cs = g.controls('Recruit mercenary unit'); lst = g.control(cs, cls='TListBox', index=0)
    click_row(g, lst, 0)
    g.click_control(g.control(cs, text='Recruit unit'), pause=1.5)
def merc_post(g):
    cs = g.controls('Recruit mercenary unit')
    names = [c['text'] for c in cs]
    close_dialog_cancel(g, 'Recruit mercenary unit', button='Cancel' if 'Cancel' in names else 'OK')
SC['MM01'] = dict(src=TB, ops=[('money', 1, 0)], act=merc_act, post=merc_post, note='Recruit mercenary unit dialog: first offer, army 1 with 0 in its purse')
SC['MM02'] = dict(src=TB, ops=[('money', 1, 1000), ('units', 1, named([U('li', 11000)] * 9))], act=merc_act, post=merc_post, note='Recruit mercenary unit dialog: first offer, army 1 of 9 x 11,000 = 99,000 troops with 1,000 in its purse')

SC['S02'] = dict(src=TB, act=lambda g: army_button(g, 0, 'disband'), note='Disband army 0 at (100,37), next to Arretium: the prompt (answered No)')
SC['BF01'] = dict(src=GF('S10_Dacia_AUTO0720.SAV'), act=lambda g: main_tool(g, 'build_fleet'),
                  note='Build fleet as Dacia (no coastal city); the save is S10_Dacia_AUTO0720.SAV of release run-exp-civ-sweep (a natural new-game autosave), used unedited',
                  fixture_note='from release run-exp-civ-sweep')
SC['A01b'] = dict(src=GF('T_EMBARK.SAV'), ops=[('moves', 12, 3), ('owner', 13, 1)], act=lambda g: army_button(g, 12, 'join'),
                  note='Join armies from army 12 (moves staged to 3) next to army 0, aboard fleet 2; army 13, the other own army next to army 12 and the partner the game would pick first (the last in index order), is staged to nation 1 so that army 0 is the partner')

def td_act(side):
    def act(g):
        army_button(g, 0, 'transfer'); open_dialog_tracked(g, 'Army to army transfer', lambda: None, tries=1)
        cs = g.controls('Army to army transfer')
        lists = sorted((c for c in cs if c['cls'] == 'TListBox'), key=lambda c: c['x'])
        click_row(g, lists[side], 0)
        db = sorted((c for c in cs if c['text'] == 'Disband'), key=lambda c: c['x'])
        if len(db) != 2: raise _drv.DriverError('expected two Disband buttons, found %d' % len(db))
        g.click_control(db[side], pause=1.2)
        confirm_step(g, 'Yes')
    return act
SC['TD01'] = dict(src=TT, ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6)])), ('units', 1, named([U('hi', 3000, 7), U('li', 2000, 6)]))], act=td_act(0), post=tr_post,
                  note='Army to army transfer dialog: Disband (left button) the first unit of army 0 at (103,36), far from a city; Confirm answered Yes')
SC['TD02'] = dict(src=TT, ops=[('units', 0, named([U('hi', 5000, 7), U('li', 4000, 6)])), ('units', 1, named([U('hi', 3000, 7), U('li', 2000, 6)]))], act=td_act(1), post=tr_post,
                  note='Army to army transfer dialog: Disband (right button) the first unit of army 1, far from a city; Confirm answered Yes')
SC['TR3'] = dict(src=GF('T_EMBARK.SAV'), ops=[('moves', 12, 3), ('owner', 13, 1), ('units', 12, named([U('li', 6000), U('li', 1100)]))], act=tr_act(12, 0), post=tr_post,
                 note='Army to army transfer from army 12 (moves staged to 3; units staged to 6,000 + 1,100) into army 0, aboard fleet 2 (30 ships, 15,000 troops of room; army 0 holds 10,700); army 13 is staged to nation 1 so that army 0 is the partner')
SC['TR3b'] = dict(src=GF('T_EMBARK.SAV'), ops=[('moves', 12, 3), ('owner', 13, 1), ('units', 12, named([U('li', 6000), U('li', 6000)]))], act=tr_act(12, 0), post=tr_post,
                  note='Army to army transfer from army 12 (moves staged to 3; units staged to 6,000 + 6,000) into army 0, aboard fleet 2 (30 ships = room for 15,000 troops; army 0 holds 10,700); army 13 is staged to nation 1 so that army 0 is the partner')

def tr_act_side(army, row, side):
    """like tr_act, but the unit is picked in the list `side` (0 left, 1 right) and that side's Transfer button is pressed"""
    def act(g):
        army_button(g, army, 'transfer'); open_dialog_tracked(g, 'Army to army transfer', lambda: None, tries=1)
        cs = g.controls('Army to army transfer')
        lists = sorted((c for c in cs if c['cls'] == 'TListBox'), key=lambda c: c['x'])
        click_row(g, lists[side], row)
        tb = sorted((c for c in cs if c['text'] == 'Transfer'), key=lambda c: c['x'])[side]
        g.click_control(tb, pause=1.5)
    return act
SC['T01r'] = dict(src=TT, ops=[('units', 0, named([U('li', 1000)] * 20)), ('units', 1, named([U('li', 3000)] * 3))], act=tr_act_side(0, 0, 1), post=tr_post,
                  note='Army to army transfer, RIGHT Transfer button: one unit of army 1 (3 units) into army 0 (20 units)')
SC['T02r'] = dict(src=TT, ops=[('units', 0, named([U('hi', 12000)] * 8)), ('units', 1, named([U('hi', 6000)] * 2))], act=tr_act_side(0, 0, 1), post=tr_post,
                  note='Army to army transfer, RIGHT Transfer button: a 6,000 unit of army 1 into army 0 (8 x 12,000 = 96,000 troops)')
